#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""盘中实时监测引擎（akshare）。输出 JSON 到 stdout。

用法:
  python engine.py --symbol 600519
  python engine.py --movers --by speed|volume|turnover --top 20
  python engine.py --sectors --top 15
  python engine.py --fundflow 600519
  python engine.py --zt

数据源容错（2026-06 起）：
  东财实时推送主机 push2.eastmoney.com 偶发整体不可用（502/断连）。
  实时快照/分时已加新浪兜底；但"主力资金流/板块资金流"在免费源中无等价替代，
  该主机不可用时这两类返回空并附 note。
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime

import pandas as pd


def _eprint(*a):
    print(*a, file=sys.stderr)


def _retry(fn, tries=3, sleep=1.2):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa
            last = e
            _eprint(f"[retry {i+1}/{tries}] {e}")
            time.sleep(sleep)
    raise last


def _trading_now():
    n = datetime.now()
    if n.weekday() >= 5:
        return False
    hm = n.hour * 60 + n.minute
    return (570 <= hm <= 690) or (780 <= hm <= 900)  # 9:30-11:30, 13:00-15:00


def _norm_code(s):
    return re.sub(r"^(sh|sz|bj)", "", str(s).strip().lower())


# 全市场实时快照：优先东财，失败回退新浪；进程内缓存避免重复拉取。
_SPOT = {}


def _spot(ak):
    if "df" in _SPOT:
        return _SPOT["df"]
    try:
        df = _retry(lambda: ak.stock_zh_a_spot_em(), tries=2)
        _SPOT["src"] = "eastmoney"
    except Exception as e:  # noqa
        _eprint(f"[spot_em 不可用，回退新浪] {e}")
        # 新浪为 ~70 页分页抓取，偶发断页；多重试几次提高整体成功率
        df = _retry(lambda: ak.stock_zh_a_spot(), tries=4, sleep=2.0)
        if "代码" in df.columns:
            df = df.copy()
            df["代码"] = df["代码"].map(_norm_code)
        _SPOT["src"] = "sina"
    _SPOT["df"] = df
    return df


def _src_note():
    if _SPOT.get("src") == "sina":
        return ("实时快照来自新浪兜底源（东财 push2 当前不可用）；"
                "缺量比/换手率/涨速/总市值等东财专有字段。")
    return None


def _mins(symbol, ak):
    """当日分时：优先东财，失败回退新浪分钟线。"""
    try:
        md = _retry(lambda: ak.stock_zh_a_hist_min_em(
            symbol=symbol, period="1", adjust=""), tries=2)
        return md.fillna("").astype(str).tail(15).to_dict(orient="records")
    except Exception as e:  # noqa
        _eprint(f"[min_em 回退新浪] {e}")
    try:
        pre = "sh" if symbol.startswith(("6", "9")) else (
            "bj" if symbol.startswith(("4", "8")) else "sz")
        md = _retry(lambda: ak.stock_zh_a_minute(
            symbol=pre + symbol, period="1", adjust=""), tries=2)
        return md.fillna("").astype(str).tail(15).to_dict(orient="records")
    except Exception as e:  # noqa
        _eprint(f"[min sina 失败] {e}")
        return []


def snapshot(symbol, ak):
    df = _spot(ak)
    m = df[df["代码"].astype(str) == symbol]
    snap = {}
    if not m.empty:
        snap = m.fillna("").astype(str).iloc[0].to_dict()
    return {"snapshot": snap, "recent_minutes": _mins(symbol, ak)}


def movers(by, top, ak):
    df = _spot(ak)
    by_map = {"speed": "涨跌幅", "volume": "量比", "turnover": "换手率"}
    col = by_map.get(by, "涨跌幅")
    if col not in df.columns:  # 新浪兜底源无 量比/换手率，回退按涨跌幅
        col = "涨跌幅"
    df = df.copy()
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values(col, ascending=False).head(top)
    keep = [c for c in ["代码", "名称", "最新价", "涨跌幅", "涨速", "量比",
                        "换手率", "成交额"] if c in df.columns]
    return df[keep].fillna("").astype(str).to_dict(orient="records")


def sectors(top, ak):
    df = _retry(lambda: ak.stock_sector_fund_flow_rank(
        indicator="今日", sector_type="行业资金流"))
    return df.head(top).fillna("").astype(str).to_dict(orient="records")


def fundflow(symbol, ak):
    market = "sh" if symbol.startswith(("6", "9")) else "sz"
    if symbol.startswith(("4", "8")):
        market = "bj"
    df = _retry(lambda: ak.stock_individual_fund_flow(
        stock=symbol, market=market))
    return df.tail(10).fillna("").astype(str).to_dict(orient="records")


def zt(ak):
    date = datetime.now().strftime("%Y%m%d")
    df = _retry(lambda: ak.stock_zt_pool_em(date=date))
    keep = [c for c in ["代码", "名称", "最新价", "涨跌幅", "成交额",
                        "流通市值", "换手率", "连板数", "所属行业"]
            if c in df.columns]
    return df[keep].fillna("").astype(str).to_dict(orient="records")


_FF_UNAVAIL = ("资金流接口依赖东财实时主机 push2.eastmoney.com，"
               "当前不可用且无免费等价替代源；其余价格类数据已用新浪兜底。")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol")
    p.add_argument("--movers", action="store_true")
    p.add_argument("--by", default="speed")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--sectors", action="store_true")
    p.add_argument("--fundflow")
    p.add_argument("--zt", action="store_true")
    args = p.parse_args()
    if args.symbol:
        args.symbol = args.symbol.strip().zfill(6)
    if args.fundflow:
        args.fundflow = args.fundflow.strip().zfill(6)

    try:
        import akshare as ak
    except ImportError:
        _eprint("缺少 akshare，请先: pip install akshare")
        sys.exit(2)

    base = {"trading_now": _trading_now(),
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    if args.symbol:
        base.update({"mode": "snapshot", **snapshot(args.symbol, ak)})
    elif args.movers:
        base.update({"mode": "movers", "by": args.by,
                     "records": movers(args.by, args.top, ak)})
    elif args.sectors:
        try:
            base.update({"mode": "sectors", "records": sectors(args.top, ak)})
        except Exception as e:  # noqa
            base.update({"mode": "sectors", "records": [],
                         "note": f"{_FF_UNAVAIL}（{e}）"})
    elif args.fundflow:
        try:
            base.update({"mode": "fundflow", "symbol": args.fundflow,
                         "records": fundflow(args.fundflow, ak)})
        except Exception as e:  # noqa
            base.update({"mode": "fundflow", "symbol": args.fundflow,
                         "records": [], "note": f"{_FF_UNAVAIL}（{e}）"})
    elif args.zt:
        base.update({"mode": "zt", "records": zt(ak)})
    else:
        _eprint("需指定 --symbol / --movers / --sectors / --fundflow / --zt")
        sys.exit(1)

    note = _src_note()
    if note:
        base["data_source_note"] = note

    print(json.dumps(base, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
