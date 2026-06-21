#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.py —— stock-tp 公共工具层

职责：
  1. 配置加载（环境变量 / config.env / .env），STOCK_LIST、ANSPIRE_API_KEYS 等
  2. 市场识别：把任意代码归一化到 (market, normalized_symbol, data_engine)
  3. 轻量磁盘缓存（按天），避免重复打网络
  4. 统一的结构化结果容器与 not_supported 降级标记
  5. JSON 安全序列化（pandas / numpy / Timestamp）

所有取数脚本都从这里 import。保持零三方依赖（除 pandas，可选）。
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import hashlib
import datetime as dt
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
SKILL_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = SKILL_ROOT / ".cache"
OUTPUT_DIR = SKILL_ROOT / "reports"
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# 配置加载
# ---------------------------------------------------------------------------
_CONFIG_CACHE: Optional[dict] = None


def _parse_env_file(path: Path) -> dict:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_config() -> dict:
    """优先级：真实环境变量 > config.env > config.example.env(仅占位说明)。"""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    cfg: dict[str, str] = {}
    # 文件兜底（低优先级）
    for fname in ("config.example.env", "config.env"):
        cfg.update(_parse_env_file(SKILL_ROOT / fname))
    # 真实环境变量覆盖
    for k, v in os.environ.items():
        if k in cfg or k.isupper():
            cfg[k] = v
    _CONFIG_CACHE = cfg
    return cfg


def get(key: str, default: str = "") -> str:
    return load_config().get(key, default) or default


def get_list(key: str) -> list[str]:
    raw = get(key)
    return [x.strip() for x in re.split(r"[,\s;]+", raw) if x.strip()]


def anspire_keys() -> list[str]:
    """支持单 Key 或逗号分隔多 Key（用于负载/限流轮换）。"""
    keys = get_list("ANSPIRE_API_KEYS")
    if not keys:
        keys = get_list("ANSPIRE_API_KEY")
    return keys


# ---------------------------------------------------------------------------
# 市场识别
# ---------------------------------------------------------------------------
# data_engine: 'akshare_cn' | 'akshare_hk' | 'yfinance'
def detect_market(symbol: str) -> dict:
    """把用户输入的代码归一化。

    返回 dict:
      raw, market, board, code, yf_symbol, ak_symbol, engine, currency, supports
    market ∈ {A, HK, US, JP, KR, UNKNOWN}
    supports: 该市场支持的高阶数据块集合（用于降级）。
    """
    s = symbol.strip()
    su = s.upper()

    # 日股 7203.T / 韩股 005930.KS / 005930.KQ
    m = re.match(r"^(\d{4,6})\.(T|KS|KQ)$", su)
    if m:
        mkt = "JP" if m.group(2) == "T" else "KR"
        return _mk(s, mkt, "", m.group(1), su, su, "yfinance",
                   "JPY" if mkt == "JP" else "KRW",
                   {"quote", "kline", "indicator", "fundamental"})

    # 港股 hk00700 / 00700.HK / 0700.HK
    m = re.match(r"^(?:HK)?0*(\d{4,5})(?:\.HK)?$", su)
    if m and ("HK" in su or su.endswith(".HK")):
        code = m.group(1).zfill(5)
        return _mk(s, "HK", "", code, f"{code[-4:].zfill(4)}.HK",
                   code, "akshare_hk", "HKD",
                   {"quote", "kline", "indicator", "fundamental", "news"})

    # A 股 6 位数字
    m = re.match(r"^(\d{6})$", su)
    if m:
        code = m.group(1)
        if code[0] == "6":
            board, yf = "SH", f"{code}.SS"
        elif code[:2] in ("00", "30"):
            board, yf = "SZ", f"{code}.SZ"
        elif code[0] in ("8", "4"):
            board, yf = "BJ", f"{code}.BJ"
        else:
            board, yf = "SH", f"{code}.SS"
        return _mk(s, "A", board, code, yf, code, "akshare_cn", "CNY",
                   {"quote", "kline", "indicator", "fundamental", "news",
                    "capital_flow", "dragon_tiger", "chips", "boards", "announcement"})

    # 港股裸 5 位（00700）—— 仅当明确以 0 开头的 5 位，避免与 A 股冲突
    m = re.match(r"^0(\d{4})$", su)
    if m:
        code = su.zfill(5)
        return _mk(s, "HK", "", code, f"{code[-4:]}.HK", code,
                   "akshare_hk", "HKD",
                   {"quote", "kline", "indicator", "fundamental", "news"})

    # 美股 / ETF：字母为主
    if re.match(r"^[A-Z][A-Z0-9.\-]{0,9}$", su):
        return _mk(s, "US", "", su, su, su, "yfinance", "USD",
                   {"quote", "kline", "indicator", "fundamental", "news"})

    return _mk(s, "UNKNOWN", "", su, su, su, "yfinance", "",
               {"quote", "kline"})


def _mk(raw, market, board, code, yf, ak, engine, currency, supports):
    return {
        "raw": raw, "market": market, "board": board, "code": code,
        "yf_symbol": yf, "ak_symbol": ak, "engine": engine,
        "currency": currency, "supports": sorted(supports),
    }


def supports(meta: dict, block: str) -> bool:
    return block in set(meta.get("supports", []))


# ---------------------------------------------------------------------------
# 结果容器 / 降级
# ---------------------------------------------------------------------------
def block_result(status: str, data: Any = None, note: str = "", source: str = "") -> dict:
    """status ∈ ok | not_supported | error | empty"""
    return {"status": status, "data": data, "note": note, "source": source}


def not_supported(market: str, block: str) -> dict:
    return block_result("not_supported", None,
                        f"{market} 市场不支持 {block}（按市场边界降级）")


# ---------------------------------------------------------------------------
# 缓存
# ---------------------------------------------------------------------------
def _today() -> str:
    return dt.date.today().isoformat()


def cache_get(namespace: str, key: str, ttl_hours: float = 6.0) -> Optional[Any]:
    h = hashlib.md5(f"{namespace}:{key}".encode()).hexdigest()[:16]
    p = CACHE_DIR / f"{namespace}_{h}.json"
    if not p.exists():
        return None
    age = time.time() - p.stat().st_mtime
    if age > ttl_hours * 3600:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def cache_set(namespace: str, key: str, value: Any) -> None:
    h = hashlib.md5(f"{namespace}:{key}".encode()).hexdigest()[:16]
    p = CACHE_DIR / f"{namespace}_{h}.json"
    try:
        p.write_text(json.dumps(value, ensure_ascii=False, default=_json_default),
                     encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# JSON 安全
# ---------------------------------------------------------------------------
def _json_default(o):
    try:
        import numpy as np
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return None if math.isnan(float(o)) else float(o)
        if isinstance(o, (np.ndarray,)):
            return o.tolist()
    except Exception:
        pass
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    if hasattr(o, "isoformat"):
        return o.isoformat()
    if isinstance(o, float) and math.isnan(o):
        return None
    return str(o)


def to_json(obj: Any, indent: int = 2) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=indent, default=_json_default)


def print_json(obj: Any) -> None:
    sys.stdout.write(to_json(obj) + "\n")


def safe_float(x, default=None):
    try:
        v = float(x)
        return default if math.isnan(v) else v
    except Exception:
        return default


def pct(a, b):
    """(a-b)/b * 100，安全。"""
    a, b = safe_float(a), safe_float(b)
    if a is None or b is None or b == 0:
        return None
    return round((a - b) / b * 100, 2)


if __name__ == "__main__":
    # 自检：python common.py 600519 AAPL hk00700 7203.T 005930.KS 510300
    tests = sys.argv[1:] or ["600519", "AAPL", "hk00700", "7203.T", "005930.KS", "510300", "00700.HK"]
    for t in tests:
        print_json(detect_market(t))
