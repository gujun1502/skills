#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_overnight.py —— 模块①宏观风险预警（隔夜 + 亚太早盘 + 汇率利率）

为 A 股 9:30 开盘前提供"外部环境锚定"：
  - 美股隔夜：标普/纳指/费半 + 个股专属隔夜代理(如 SOXX/NVDA/AAPL)
  - 亚太早盘：日经/韩综指(北京时间 9 点已开盘约 1 小时)/恒生
  - 汇率利率：美元兑人民币 / 美10年期 / 美元指数
全部走 yfinance（全球通），不依赖 akshare。每个标的给出涨跌幅与方向，
再合成一个 0~100 的"宏观偏向分(macro_tilt)"：>50 利多 A 股，<50 利空。

用法：
  python fetch_overnight.py                 # 仅全局宏观
  python fetch_overnight.py --code 002156   # 叠加该股的隔夜代理(读 linkage.json)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import common as C

SKILL_ROOT = Path(__file__).resolve().parent.parent
LINKAGE_FILE = SKILL_ROOT / "linkage.json"


def _load_linkage() -> dict:
    try:
        return json.loads(LINKAGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _chg(symbol: str) -> dict:
    """取最近一根 vs 前一根日线涨跌幅。对亚太=当日早盘相对昨收；对美股=隔夜收盘。"""
    try:
        import yfinance as yf
        h = yf.Ticker(symbol).history(period="6d", auto_adjust=True)
        if h is None or h.empty or len(h) < 2:
            return {"symbol": symbol, "status": "empty"}
        close = h["Close"].astype(float)
        last, prev = float(close.iloc[-1]), float(close.iloc[-2])
        chg = (last - prev) / prev * 100 if prev else None
        return {
            "symbol": symbol,
            "status": "ok",
            "last": round(last, 4),
            "prev": round(prev, 4),
            "chg_pct": round(chg, 3) if chg is not None else None,
            "asof": str(h.index[-1].date()),
        }
    except Exception as e:
        return {"symbol": symbol, "status": "error", "note": f"{type(e).__name__}"}


def _label(chg: float | None, bullish_when: str = "up") -> str:
    if chg is None:
        return "—"
    if bullish_when == "down":  # 利率/汇率：下跌才利多
        chg = -chg
    if chg >= 1.5:
        return "强多"
    if chg >= 0.3:
        return "偏多"
    if chg > -0.3:
        return "中性"
    if chg > -1.5:
        return "偏空"
    return "强空"


def _tilt_from(items: list[dict]) -> float | None:
    """把一组 {chg_pct, weight, bullish_when} 映射成 0~100 偏向分。"""
    num = den = 0.0
    for it in items:
        chg = it.get("chg_pct")
        if chg is None:
            continue
        w = float(it.get("weight", 1.0))
        sign = -1.0 if it.get("bullish_when") == "down" else 1.0
        signed = sign * chg
        # 单标的贡献：±2% 饱和到 ±50 分，叠加到 50 基准
        contrib = max(-50.0, min(50.0, signed / 2.0 * 50.0))
        num += w * contrib
        den += w
    if den == 0:
        return None
    return round(50.0 + num / den, 1)


def fetch(code: str = "") -> dict:
    lk = _load_linkage()
    gm = lk.get("_global_macro", {})

    def _resolve(group):
        out = []
        for spec in group:
            r = _chg(spec["symbol"])
            r["name"] = spec.get("name", spec["symbol"])
            r["bullish_when"] = spec.get("bullish_when", "up")
            r["label"] = _label(r.get("chg_pct"), r["bullish_when"])
            out.append(r)
        return out

    us = _resolve(gm.get("us_overnight", []))
    asia = _resolve(gm.get("asia_morning", []))
    ratesfx = _resolve(gm.get("rates_fx", []))

    # 个股专属隔夜代理
    proxies = []
    proxy_specs = []
    if code:
        rec = lk.get(code) or lk.get("_default", {})
        proxy_specs = rec.get("overnight_proxies", [])
        proxies = _resolve(proxy_specs)
        for p, spec in zip(proxies, proxy_specs):
            p["weight"] = spec.get("weight", 1.0)

    # 合成宏观偏向分：美股隔夜 0.40 / 亚太早盘 0.30 / 汇率利率 0.30
    sub = {
        "us": _tilt_from([{**x, "weight": 1.0} for x in us]),
        "asia": _tilt_from([{**x, "weight": 1.0} for x in asia]),
        "rates_fx": _tilt_from([{**x, "weight": 1.0} for x in ratesfx]),
    }
    parts = [(sub["us"], 0.40), (sub["asia"], 0.30), (sub["rates_fx"], 0.30)]
    num = den = 0.0
    for v, w in parts:
        if v is not None:
            num += v * w
            den += w
    macro_tilt = round(num / den, 1) if den else None

    # 个股专属代理偏向(仅作模块④联动的隔夜部分参考，单独给出)
    proxy_tilt = _tilt_from(proxies) if proxies else None

    return {
        "block": "overnight",
        "status": "ok" if macro_tilt is not None else "error",
        "macro_tilt": macro_tilt,
        "macro_tilt_sub": sub,
        "proxy_tilt": proxy_tilt,
        "us_overnight": us,
        "asia_morning": asia,
        "rates_fx": ratesfx,
        "stock_proxies": proxies,
        "note": "macro_tilt>50 利多A股 / <50 利空；±2% 单标的饱和。汇率利率取'下跌为多'。",
        "source": "yfinance",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default="", help="叠加该股隔夜代理(读 linkage.json)")
    a = ap.parse_args()
    C.print_json(fetch(a.code))


if __name__ == "__main__":
    main()
