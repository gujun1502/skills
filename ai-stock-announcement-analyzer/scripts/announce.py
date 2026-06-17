#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""盘前公告抓取（akshare）。输出 JSON 到 stdout，供 Claude 解读。

用法:
  python announce.py --symbol 600519 [--start 20260601]
  python announce.py --market --date 20260617
  python announce.py --resolve 贵州茅台

数据源容错（2026-06 起）：
  - resolve 的官方代码表含北交所站点(www.bse.cn)，偶发 SSL 失败；失败时回退新浪行情列表。
  - 个股公告(巨潮 cninfo)偶发返回空，akshare 对空结果未保护会抛错；此处已捕获并返回空集。
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta


def _eprint(*a):
    print(*a, file=sys.stderr)


def _retry(fn, tries=3, sleep=1.5):
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


def resolve(name, ak):
    """名称->代码：优先官方代码表；失败(常因北交所站点)回退新浪行情列表。"""
    src = "official"
    try:
        df = _retry(lambda: ak.stock_info_a_code_name(), tries=2)
        cols = {c.lower(): c for c in df.columns}
        code_c = cols.get("code") or list(df.columns)[0]
        name_c = cols.get("name") or list(df.columns)[1]
    except Exception as e:  # noqa
        _eprint(f"[code_name 回退新浪] {e}")
        df = _retry(lambda: ak.stock_zh_a_spot())  # 新浪，含 代码/名称，较慢
        df = df.copy()
        df["代码"] = df["代码"].map(_norm_code)
        code_c, name_c, src = "代码", "名称", "sina"
    hit = df[df[name_c].astype(str).str.contains(name, na=False)]
    matches = [
        {"code": str(r[code_c]), "name": str(r[name_c])}
        for _, r in hit.head(20).iterrows()
    ]
    return matches, src


def individual(symbol, start, ak):
    """个股公告：巨潮(cninfo)披露接口。空结果/源异常时返回空集，不崩溃。"""
    end = datetime.now().strftime("%Y%m%d")
    if not start:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    s = f"{start[:4]}-{start[4:6]}-{start[6:]}"
    e = f"{end[:4]}-{end[4:6]}-{end[6:]}"
    try:
        df = _retry(lambda: ak.stock_zh_a_disclosure_report_cninfo(
            symbol=symbol, market="沪深京", start_date=s, end_date=e), tries=3)
        return df.fillna("").astype(str).to_dict(orient="records"), None
    except Exception as e:  # noqa
        _eprint(f"[cninfo individual] {e}")
        return [], ("巨潮披露接口本次未返回数据（区间内无公告，或源暂时限流/不可用）。"
                    "可稍后重试或缩小日期区间。")


def market(date, ak):
    """全市场某日公告概览（东财公告，数据中心主机，通常可用但较慢）。"""
    out = []
    note = None
    for typ in ["全部"]:
        try:
            df = _retry(lambda: ak.stock_notice_report(symbol=typ, date=date))
            out.extend(df.fillna("").astype(str).to_dict(orient="records"))
        except Exception as e:  # noqa
            _eprint(f"[market {typ}] {e}")
            note = f"东财公告接口本次不可用：{e}"
    return out, note


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol")
    p.add_argument("--start")
    p.add_argument("--market", action="store_true")
    p.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    p.add_argument("--resolve")
    args = p.parse_args()
    if args.symbol:
        args.symbol = args.symbol.strip().zfill(6)

    try:
        import akshare as ak
    except ImportError:
        _eprint("缺少 akshare，请先: pip install akshare")
        sys.exit(2)

    if args.resolve:
        matches, src = resolve(args.resolve, ak)
        data = {"mode": "resolve", "query": args.resolve,
                "matches": matches, "source": src}
    elif args.symbol:
        records, note = individual(args.symbol, args.start, ak)
        data = {"mode": "individual", "symbol": args.symbol,
                "records": records}
        if note:
            data["note"] = note
    elif args.market:
        records, note = market(args.date, ak)
        data = {"mode": "market", "date": args.date, "records": records}
        if note:
            data["note"] = note
    else:
        _eprint("需指定 --symbol / --market / --resolve 之一")
        sys.exit(1)

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
