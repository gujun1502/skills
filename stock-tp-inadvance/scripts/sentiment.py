#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sentiment.py —— 市场情绪面

产出一个 0-100 的"市场情绪温度"与离散标签（极度恐慌/恐慌/中性/乐观/亢奋），
作为决策因子的环境项（影响仓位与买卖点容忍度）。

A股：东方财富/乐咕的涨跌停家数、上涨下跌家数 → 情绪温度
全球：^VIX（恐慌指数）反向映射 + 标的所在大盘近 20 日趋势

口径写在 references/auction-rules.md（红绿黑成交口诀 + 竞价规则）。
"""
from __future__ import annotations

import argparse
import common as C


def _cn_breadth() -> dict:
    """A股市场宽度：上涨/下跌/涨停/跌停家数。"""
    import akshare as ak
    data = {}
    try:
        act = ak.stock_market_activity_legu()  # item/value 两列
        kv = dict(zip(act["item"], act["value"]))
        data["up"] = C.safe_float(kv.get("上涨"))
        data["down"] = C.safe_float(kv.get("下跌"))
        data["limit_up"] = C.safe_float(kv.get("涨停") or kv.get("真实涨停"))
        data["limit_down"] = C.safe_float(kv.get("跌停") or kv.get("真实跌停"))
        data["activity"] = kv.get("活跃度")
    except Exception as e:
        data["error"] = str(e)
    return data


def _vix() -> float | None:
    import yfinance as yf
    try:
        df = yf.Ticker("^VIX").history(period="5d")
        if df is not None and not df.empty:
            return C.safe_float(df["Close"].iloc[-1])
    except Exception:
        pass
    return None


def _index_trend(meta) -> dict:
    """标的所在大盘近 20 日涨跌幅。"""
    import yfinance as yf
    idx_map = {"A": "000001.SS", "HK": "^HSI", "US": "^GSPC",
               "JP": "^N225", "KR": "^KS11"}
    sym = idx_map.get(meta["market"], "^GSPC")
    try:
        df = yf.Ticker(sym).history(period="2mo")
        if df is None or df.empty:
            return {}
        c = df["Close"]
        return {"index": sym,
                "chg_20d": C.pct(c.iloc[-1], c.iloc[-21]) if len(c) > 21 else None,
                "above_ma20": bool(c.iloc[-1] > c.tail(20).mean())}
    except Exception:
        return {}


def _score(market: str, breadth: dict, vix, idx: dict) -> dict:
    score = 50.0
    drivers = []
    if market == "A" and breadth and "error" not in breadth:
        up, down = breadth.get("up") or 0, breadth.get("down") or 0
        if up + down > 0:
            ratio = up / (up + down)
            score = 30 + ratio * 50  # 30-80 base
            drivers.append(f"上涨/下跌家数 {int(up)}/{int(down)}（{ratio*100:.0f}% 上涨）")
        lu, ld = breadth.get("limit_up") or 0, breadth.get("limit_down") or 0
        if lu + ld > 0:
            score += min(12, (lu - ld) * 0.3)
            drivers.append(f"涨停/跌停 {int(lu)}/{int(ld)}")
    if vix is not None:
        # VIX 12->乐观, 35->恐慌；反向映射叠加
        v_score = max(0, min(100, 100 - (vix - 12) / (40 - 12) * 100))
        if market == "A":
            score = score * 0.7 + v_score * 0.3
        else:
            score = v_score
        drivers.append(f"VIX {vix:.1f}")
    if idx.get("chg_20d") is not None:
        score += max(-8, min(8, idx["chg_20d"] * 0.5))
        drivers.append(f"大盘({idx.get('index')}) 20日 {idx['chg_20d']:+.1f}%，{'站上' if idx.get('above_ma20') else '跌破'}20日线")
    score = max(0, min(100, round(score, 1)))
    label = ("极度恐慌" if score < 20 else "恐慌" if score < 40 else
             "中性" if score < 60 else "乐观" if score < 80 else "亢奋")
    return {"temperature": score, "label": label, "drivers": drivers}


def fetch(symbol: str) -> dict:
    meta = C.detect_market(symbol)
    cached = C.cache_get("sentiment", meta["market"], ttl_hours=3.0)
    if cached:
        cached["meta"] = meta
        return cached
    breadth = _cn_breadth() if meta["market"] == "A" else {}
    vix = _vix()
    idx = _index_trend(meta)
    score = _score(meta["market"], breadth, vix, idx)
    result = {"meta": meta,
              "sentiment": C.block_result("ok", {
                  "market_breadth": breadth, "vix": vix,
                  "index_trend": idx, **score})}
    C.cache_set("sentiment", meta["market"], result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    a = ap.parse_args()
    C.print_json(fetch(a.symbol))


if __name__ == "__main__":
    main()
