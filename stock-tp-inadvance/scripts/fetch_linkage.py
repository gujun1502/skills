#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_linkage.py —— 模块④板块联动与信息面（当日 A 股部分）

读 linkage.json 里某只股票登记的同业(peers)与行业 ETF，取它们前一交易日的
涨跌幅与近 5 日表现，判断"板块合力"方向，合成 0~100 的 linkage_tilt：
  >50 板块前一日偏强(利多次日) / <50 偏弱。
隔夜代理(overnight_proxies)由 fetch_overnight.py 负责，这里只看 A 股盘内联动。

复用 fetch_market.fetch（带缓存、自动降级），不重复造取数。

用法：
  python fetch_linkage.py 002156
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import common as C
import fetch_market as FM

SKILL_ROOT = Path(__file__).resolve().parent.parent
LINKAGE_FILE = SKILL_ROOT / "linkage.json"


def _load_linkage() -> dict:
    try:
        return json.loads(LINKAGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _quote_chg(code: str) -> dict:
    """取某 A 股/ETF 的前一交易日涨跌幅 + 近5日 + 均线排列。"""
    try:
        r = FM.fetch(code, days=30)
        ind = (r.get("indicators") or {}).get("data") or {}
        q = (r.get("quote") or {}).get("data") or {}
        if not ind and not q:
            return {"code": code, "status": "error"}
        return {
            "code": code,
            "status": "ok",
            "chg_1d": ind.get("chg_1d"),
            "chg_5d": ind.get("chg_5d"),
            "ma_alignment": ind.get("ma_alignment"),
            "price": q.get("price"),
        }
    except Exception as e:
        return {"code": code, "status": "error", "note": type(e).__name__}


def _tilt(items: list[dict], key: str = "chg_1d") -> float | None:
    """一组标的涨跌幅 → 0~100。±3% 单标的饱和到 ±50。"""
    vals = [x.get(key) for x in items if x.get(key) is not None]
    if not vals:
        return None
    contribs = [max(-50.0, min(50.0, v / 3.0 * 50.0)) for v in vals]
    return round(50.0 + sum(contribs) / len(contribs), 1)


def fetch(code: str) -> dict:
    lk = _load_linkage()
    rec = lk.get(code) or lk.get("_default", {})

    peers = []
    for p in rec.get("peers", []):
        r = _quote_chg(p["code"])
        r["name"] = p.get("name", p["code"])
        peers.append(r)
    etfs = []
    for e in rec.get("etfs", []):
        r = _quote_chg(e["code"])
        r["name"] = e.get("name", e["code"])
        etfs.append(r)

    peer_tilt = _tilt(peers)
    etf_tilt = _tilt(etfs)
    # 板块合力：同业 0.6 + ETF 0.4
    parts = [(peer_tilt, 0.6), (etf_tilt, 0.4)]
    num = den = 0.0
    for v, w in parts:
        if v is not None:
            num += v * w
            den += w
    linkage_tilt = round(num / den, 1) if den else None

    # 一致性：同业里多少比例同向（衡量"板块是否齐涨齐跌"）
    chgs = [p.get("chg_1d") for p in peers if p.get("chg_1d") is not None]
    consensus = None
    if chgs:
        up = sum(1 for c in chgs if c > 0)
        consensus = round(max(up, len(chgs) - up) / len(chgs), 2)

    return {
        "block": "linkage",
        "status": "ok" if linkage_tilt is not None else "degraded",
        "linkage_tilt": linkage_tilt,
        "peer_tilt": peer_tilt,
        "etf_tilt": etf_tilt,
        "peer_consensus": consensus,
        "core_sectors": rec.get("core_sectors", []),
        "themes": rec.get("themes", []),
        "notes": rec.get("notes", ""),
        "peers": peers,
        "etfs": etfs,
        "note": "linkage_tilt>50 板块前一日偏强(利多次日)。peer_consensus 越接近1板块越齐心。",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code")
    a = ap.parse_args()
    C.print_json(fetch(a.code))


if __name__ == "__main__":
    main()
