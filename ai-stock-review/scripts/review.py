#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""盘后复盘取数（akshare）。输出 JSON 到 stdout，供 Claude 撰写复盘。

用法:
  python review.py --market
  python review.py --holdings 600519,000001,300750
  python review.py --market --holdings 600519,000001

数据源容错（2026-06 起）：
  东财实时推送主机 push2.eastmoney.com 偶发整体不可用（502/断连）。
  指数/全市场快照已加新浪兜底；涨跌停、个股日K 走可用主机；
  "板块资金流/个股资金流"无免费等价替代，该主机不可用时相应字段缺失。
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta

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


def _norm_code(s):
    return re.sub(r"^(sh|sz|bj)", "", str(s).strip().lower())


# 进程内缓存 + 东财->新浪兜底
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


def _index_spot(ak):
    """主要指数实时：优先东财，失败回退新浪（代码去前缀，新浪无北证50）。"""
    try:
        di = _retry(lambda: ak.stock_zh_index_spot_em(), tries=2)
        return di
    except Exception as e:  # noqa
        _eprint(f"[index_spot_em 回退新浪] {e}")
        di = _retry(lambda: ak.stock_zh_index_spot_sina())
        if "代码" in di.columns:
            di = di.copy()
            di["代码"] = di["代码"].map(_norm_code)
        return di


def _src_note():
    if _SPOT.get("src") == "sina":
        return ("全市场快照来自新浪兜底源（东财 push2 当前不可用）；"
                "缺换手率/量比/总市值等东财专有字段，板块/个股资金流不可用。")
    return None


def market_overview(ak):
    out = {}
    today = datetime.now().strftime("%Y%m%d")

    # 主要指数
    indices = []
    try:
        di = _index_spot(ak)
        want = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指",
                "000688": "科创50", "899050": "北证50"}
        m = di[di["代码"].astype(str).isin(want.keys())]
        indices = m.fillna("").astype(str).to_dict(orient="records")
    except Exception as e:  # noqa
        _eprint(f"[indices] {e}")
    out["indices"] = indices

    # 全市场快照 -> 涨跌停/涨跌家数统计
    try:
        spot = _spot(ak)
        chg = pd.to_numeric(spot["涨跌幅"], errors="coerce")
        up = int((chg > 0).sum())
        down = int((chg < 0).sum())
        flat = int((chg == 0).sum())
        out["breadth"] = {"up": up, "down": down, "flat": flat,
                          "total": int(len(spot))}
    except Exception as e:  # noqa
        _eprint(f"[breadth] {e}")

    # 涨停 / 跌停
    for key, fn in [("zt_count", lambda: ak.stock_zt_pool_em(date=today)),
                    ("dt_count", lambda: ak.stock_zt_pool_dtgc_em(date=today))]:
        try:
            df = _retry(fn)
            out[key] = int(len(df))
            if key == "zt_count" and "连板数" in df.columns:
                try:
                    out["max_limit_streak"] = int(
                        df["连板数"].astype("float").max())
                except Exception:  # noqa
                    pass
        except Exception as e:  # noqa
            _eprint(f"[{key}] {e}")

    # 行业涨跌
    try:
        ind = _retry(lambda: ak.stock_board_industry_name_em())
        if "涨跌幅" in ind.columns:
            ind = ind.copy()
            ind["涨跌幅"] = pd.to_numeric(ind["涨跌幅"], errors="coerce")
            ind = ind.sort_values("涨跌幅", ascending=False)
            keep = [c for c in ["板块名称", "涨跌幅", "总市值", "上涨家数",
                                "下跌家数", "领涨股票"] if c in ind.columns]
            out["industry_top"] = ind[keep].head(5).fillna("").astype(
                str).to_dict(orient="records")
            out["industry_bottom"] = ind[keep].tail(5).fillna("").astype(
                str).to_dict(orient="records")
    except Exception as e:  # noqa
        _eprint(f"[industry] {e}")
        out["industry_note"] = ("行业涨跌依赖东财实时主机，当前不可用。")

    # 板块资金流
    try:
        sf = _retry(lambda: ak.stock_sector_fund_flow_rank(
            indicator="今日", sector_type="行业资金流"))
        out["sector_fundflow_top"] = sf.head(8).fillna("").astype(
            str).to_dict(orient="records")
    except Exception as e:  # noqa
        _eprint(f"[sector_fundflow] {e}")
        out["sector_fundflow_note"] = ("板块资金流依赖东财实时主机 push2，"
                                       "当前不可用且无免费等价替代源。")

    return out


def _hist(code, start, end, ak):
    """个股日K：优先东财push2his；失败回退新浪日K并自算涨跌幅。返回统一列名DataFrame。"""
    try:
        return _retry(lambda: ak.stock_zh_a_hist(
            symbol=code, period="daily", start_date=start,
            end_date=end, adjust="qfq"), tries=2)
    except Exception as e:  # noqa
        _eprint(f"[hist_em 回退新浪 {code}] {e}")
    pre = "sh" if code.startswith(("6", "9")) else (
        "bj" if code.startswith(("4", "8")) else "sz")
    df = _retry(lambda: ak.stock_zh_a_daily(symbol=pre + code, adjust="qfq"))
    df = df.copy()
    df["prev"] = df["close"].shift(1)
    df["涨跌额"] = (df["close"] - df["prev"]).round(3)
    df["涨跌幅"] = ((df["close"] / df["prev"] - 1) * 100).round(3)
    df = df.rename(columns={"date": "日期", "open": "开盘", "close": "收盘",
                            "high": "最高", "low": "最低", "volume": "成交量"})
    keep = [c for c in ["日期", "开盘", "收盘", "最高", "最低", "成交量",
                        "涨跌额", "涨跌幅"] if c in df.columns]
    sd = start[:4] + "-" + start[4:6] + "-" + start[6:]
    out = df[df["日期"].astype(str) >= sd]
    return out[keep] if not out.empty else df[keep].tail(10)


def holdings(codes, ak):
    start = (datetime.now() - timedelta(days=12)).strftime("%Y%m%d")
    end = datetime.now().strftime("%Y%m%d")
    res = []
    # 个股快照直接取自日K最后一行（push2his，稳定可用），
    # 不再依赖全市场实时快照(新浪70页分页易整轮失败)。
    for code in codes:
        item = {"code": code}
        # 近期日K（push2his，失败回退新浪日K）
        try:
            hist = _hist(code, start, end, ak)
            item["recent_kline"] = hist.tail(5).fillna("").astype(
                str).to_dict(orient="records")
            if not hist.empty:
                last = hist.iloc[-1]
                for src, dst in [("收盘", "最新价"), ("涨跌幅", "涨跌幅"),
                                 ("涨跌额", "涨跌额"), ("换手率", "换手率"),
                                 ("成交额", "成交额")]:
                    if src in last:
                        item[dst] = str(last[src])
        except Exception as e:  # noqa
            _eprint(f"[hist {code}] {e}")
            item["hist_note"] = "个股日K接口本次不可用，请稍后重试。"
        # 个股资金流（东财实时主机，可能不可用）
        try:
            mk = "sh" if code.startswith(("6", "9")) else (
                "bj" if code.startswith(("4", "8")) else "sz")
            ff = _retry(lambda: ak.stock_individual_fund_flow(
                stock=code, market=mk), tries=2)
            item["fundflow_today"] = ff.tail(1).fillna("").astype(
                str).to_dict(orient="records")
        except Exception as e:  # noqa
            _eprint(f"[fundflow {code}] {e}")
            item["fundflow_note"] = "个股资金流接口当前不可用(push2)。"
        res.append(item)
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--market", action="store_true")
    p.add_argument("--holdings")
    args = p.parse_args()

    try:
        import akshare as ak
    except ImportError:
        _eprint("缺少 akshare，请先: pip install akshare")
        sys.exit(2)

    if not args.market and not args.holdings:
        _eprint("需指定 --market 和/或 --holdings")
        sys.exit(1)

    data = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    if args.market:
        data["market"] = market_overview(ak)
    if args.holdings:
        codes = [c.strip().zfill(6) for c in args.holdings.split(",")
                 if c.strip()]
        data["holdings"] = holdings(codes, ak)

    note = _src_note()
    if note:
        data["data_source_note"] = note

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
