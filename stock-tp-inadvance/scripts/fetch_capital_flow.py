#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_capital_flow.py —— 资金流 / 筹码 / 龙虎榜（A股专属）

按市场边界降级：HK/US/JP/KR 这些块返回 not_supported。

输出：
  capital_flow : 近 N 日主力/超大单净流入序列 + 最新一日（含"尾盘资金"代理信号）
  chips        : 筹码分布（获利比例、平均成本、90/70 成本区间）
  dragon_tiger : 最近龙虎榜上榜记录（若有）
覆盖需求中的"尾盘资金流入走势、前一天尾盘资金流入走势"——用日度主力净额趋势近似，
并标注最近两日方向，配合 references/auction-rules.md 的红绿黑口诀解读。
"""
from __future__ import annotations

import argparse
import common as C


def _market_arg(meta) -> str:
    return {"SH": "sh", "SZ": "sz", "BJ": "bj"}.get(meta["board"], "sh")


def _capital_flow(meta, days=10) -> dict:
    import akshare as ak
    df = ak.stock_individual_fund_flow(stock=meta["code"], market=_market_arg(meta))
    if df is None or df.empty:
        return C.block_result("empty")
    df = df.tail(days).copy()
    rename = {"日期": "date", "主力净流入-净额": "main_net",
              "主力净流入-净占比": "main_net_pct",
              "超大单净流入-净额": "xl_net", "大单净流入-净额": "l_net",
              "收盘价": "close", "涨跌幅": "chg_pct"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "date": str(r.get("date")),
            "main_net": C.safe_float(r.get("main_net")),
            "main_net_pct": C.safe_float(r.get("main_net_pct")),
            "xl_net": C.safe_float(r.get("xl_net")),
            "chg_pct": C.safe_float(r.get("chg_pct")),
        })
    # 趋势判断：近两日主力方向 + 连续流入/流出天数
    nets = [x["main_net"] for x in rows if x["main_net"] is not None]
    streak, direction = 0, "中性"
    for v in reversed(nets):
        if v > 0 and direction in ("中性", "净流入"):
            direction = "净流入"; streak += 1
        elif v < 0 and direction in ("中性", "净流出"):
            direction = "净流出"; streak += 1
        else:
            break
    summary = {
        "latest_main_net": rows[-1]["main_net"] if rows else None,
        "prev_main_net": rows[-2]["main_net"] if len(rows) >= 2 else None,
        "direction": direction,
        "streak_days": streak,
        "note": "日度主力净额近似尾盘资金趋势；连续方向天数越长，资金意图越明确",
    }
    return C.block_result("ok", {"series": rows, "summary": summary}, source="eastmoney")


def _chips(meta) -> dict:
    import akshare as ak
    try:
        df = ak.stock_cyq_em(symbol=meta["code"], adjust="qfq")
    except Exception as e:
        return C.block_result("error", None, str(e))
    if df is None or df.empty:
        return C.block_result("empty")
    r = df.iloc[-1]
    return C.block_result("ok", {
        "date": str(r.get("日期")),
        "profit_ratio": C.safe_float(r.get("获利比例")),
        "avg_cost": C.safe_float(r.get("平均成本")),
        "cost_90_low": C.safe_float(r.get("90成本-低")),
        "cost_90_high": C.safe_float(r.get("90成本-高")),
        "concentration_90": C.safe_float(r.get("90集中度")),
    }, source="eastmoney")


def _dragon_tiger(meta) -> dict:
    import akshare as ak
    import datetime as dt
    try:
        end = dt.date.today()
        start = end - dt.timedelta(days=30)
        df = ak.stock_lhb_detail_em(start_date=start.strftime("%Y%m%d"),
                                    end_date=end.strftime("%Y%m%d"))
        if df is None or df.empty:
            return C.block_result("empty", note="近30日无龙虎榜")
        col = "代码" if "代码" in df.columns else df.columns[0]
        hit = df[df[col].astype(str).str.contains(meta["code"])]
        if hit.empty:
            return C.block_result("empty", note="该股近30日未上龙虎榜")
        recs = hit.head(5).to_dict("records")
        return C.block_result("ok", {"count": len(hit), "records": recs}, source="eastmoney")
    except Exception as e:
        return C.block_result("error", None, str(e))


def fetch(symbol: str) -> dict:
    meta = C.detect_market(symbol)
    result = {"meta": meta}
    if not C.supports(meta, "capital_flow"):
        result["capital_flow"] = C.not_supported(meta["market"], "capital_flow")
        result["chips"] = C.not_supported(meta["market"], "chips")
        result["dragon_tiger"] = C.not_supported(meta["market"], "dragon_tiger")
        return result

    ck = meta["code"]
    cached = C.cache_get("capflow", ck, ttl_hours=4.0)
    if cached:
        return cached
    try:
        result["capital_flow"] = _capital_flow(meta)
    except Exception as e:
        result["capital_flow"] = C.block_result("error", None, str(e))
    try:
        result["chips"] = _chips(meta)
    except Exception as e:
        result["chips"] = C.block_result("error", None, str(e))
    result["dragon_tiger"] = _dragon_tiger(meta)
    C.cache_set("capflow", ck, result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    a = ap.parse_args()
    C.print_json(fetch(a.symbol))


if __name__ == "__main__":
    main()
