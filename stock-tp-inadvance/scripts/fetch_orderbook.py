#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_orderbook.py —— 模块③个股盘口状态（实时五档 / 委比 / 内外盘 / 量比）

抓 A 股实时盘口快照(东财)，刻画"价格结构 + 主动买盘 + 量能"：
  - 五档买卖盘 + 委比/委差(挂单多空力量)
  - 内盘/外盘(主动卖/主动买的成交占比 → 主动买盘强弱)
  - 量比、换手、今开/昨收/最高/最低/涨跌停
盘前(9:15-9:25)可读集合竞价；盘中读实时。akshare 不可用时整体降级，
持仓盈亏与套牢分析改由 premarket.py 用日线昨收兜底。

用法：
  python fetch_orderbook.py 002156
"""
from __future__ import annotations

import argparse
import common as C


_KEYMAP = {
    "最新": "last", "均价": "avg", "涨幅": "chg_pct", "涨跌": "chg",
    "总手": "volume_lots", "金额": "amount", "换手": "turnover", "量比": "volume_ratio",
    "最高": "high", "最低": "low", "今开": "open", "昨收": "prev_close",
    "涨停": "limit_up", "跌停": "limit_down", "外盘": "outer", "内盘": "inner",
    "委比": "order_ratio", "委差": "order_diff",
}


def _spot(meta) -> dict:
    """东财实时盘口；返回标准化 dict 或 None。"""
    import akshare as ak
    df = ak.stock_bid_ask_em(symbol=meta["code"])
    if df is None or df.empty:
        return {}
    kv = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1]))
    out = {}
    for zh, en in _KEYMAP.items():
        if zh in kv:
            out[en] = C.safe_float(kv[zh])
    # 五档（东财字段名形如 买一/买一量、卖一/卖一量）
    bids, asks = [], []
    for name in ["一", "二", "三", "四", "五"]:
        bids.append({"p": C.safe_float(kv.get(f"买{name}")), "v": C.safe_float(kv.get(f"买{name}量"))})
        asks.append({"p": C.safe_float(kv.get(f"卖{name}")), "v": C.safe_float(kv.get(f"卖{name}量"))})
    out["bids"] = bids
    out["asks"] = asks
    return out


def _derive(spot: dict) -> dict:
    """从盘口派生主动买盘强弱、挂单倾向等语义信号。"""
    sig = {}
    inner, outer = spot.get("inner"), spot.get("outer")
    if inner is not None and outer is not None and (inner + outer) > 0:
        ob_ratio = outer / (inner + outer)
        sig["active_buy_ratio"] = round(ob_ratio, 3)
        sig["active_buy_label"] = (
            "主动买盘占优(外盘大)" if ob_ratio > 0.55 else
            "主动卖盘占优(内盘大)" if ob_ratio < 0.45 else "多空均衡")
    orr = spot.get("order_ratio")
    if orr is not None:
        sig["order_book_label"] = (
            "挂单买方占优" if orr > 10 else "挂单卖方占优" if orr < -10 else "挂单均衡")
    vr = spot.get("volume_ratio")
    if vr is not None:
        sig["volume_label"] = (
            "明显放量" if vr > 2.0 else "温和放量" if vr > 1.2 else
            "缩量" if vr < 0.8 else "量能平稳")
    # 价格在当日区间的位置
    last, hi, lo = spot.get("last"), spot.get("high"), spot.get("low")
    if last and hi and lo and hi > lo:
        sig["intraday_pos_pct"] = round((last - lo) / (hi - lo) * 100, 1)
    return sig


def fetch(symbol: str) -> dict:
    meta = C.detect_market(symbol)
    if meta["market"] != "A":
        return {"block": "orderbook", "meta": meta,
                "status": "not_supported",
                "note": "实时五档/内外盘仅 A 股支持，其余市场用日线兜底。"}
    try:
        spot = _spot(meta)
        if not spot:
            return {"block": "orderbook", "meta": meta, "status": "empty"}
        return {"block": "orderbook", "meta": meta, "status": "ok",
                "spot": spot, "signals": _derive(spot), "source": "akshare/eastmoney"}
    except Exception as e:
        return {"block": "orderbook", "meta": meta, "status": "error",
                "note": f"{type(e).__name__}: {str(e)[:80]}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    a = ap.parse_args()
    C.print_json(fetch(a.symbol))


if __name__ == "__main__":
    main()
