#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_fundamentals.py —— 基本面 / 财报 / 估值

A股/港股 -> akshare（个股信息、财务摘要、估值指标）
美/日/韩 -> yfinance（info + 三大报表关键科目）

输出统一字段（尽量补齐，缺失为 None）：
  name, industry, market_cap, pe_ttm, pe_forward, pb, ps, dividend_yield,
  revenue, revenue_yoy, net_profit, net_profit_yoy, gross_margin,
  net_margin, roe, eps, debt_to_equity, current_ratio, report_period
并给出 P0 语义解读（强/中/弱）。
"""
from __future__ import annotations

import argparse
import common as C


def _akshare_cn(meta) -> dict:
    import akshare as ak
    code = meta["code"]
    out: dict = {}

    # 个股基础信息（名称、行业、总市值）
    try:
        info = ak.stock_individual_info_em(symbol=code)
        kv = dict(zip(info["item"], info["value"]))
        out["name"] = kv.get("股票简称")
        out["industry"] = kv.get("行业")
        out["market_cap"] = C.safe_float(kv.get("总市值"))
        out["float_cap"] = C.safe_float(kv.get("流通市值"))
    except Exception:
        pass

    # 估值（乐咕：PE/PB/股息率），取最新一行
    try:
        val = ak.stock_a_indicator_lg(symbol=code)
        if val is not None and not val.empty:
            r = val.iloc[-1]
            out["pe_ttm"] = C.safe_float(r.get("pe_ttm"))
            out["pb"] = C.safe_float(r.get("pb"))
            out["ps"] = C.safe_float(r.get("ps_ttm"))
            out["dividend_yield"] = C.safe_float(r.get("dv_ttm"))
    except Exception:
        pass

    # 财务摘要（营收、净利、同比）
    try:
        abs = ak.stock_financial_abstract(symbol=code)
        # 宽表：列为报告期，行为指标
        if abs is not None and not abs.empty:
            idx = abs.set_index(abs.columns[0])
            cols = [c for c in idx.columns if str(c)[:2] in ("20", "19")]
            cols = sorted(cols)[-1:] if cols else []
            if cols:
                latest = cols[-1]
                out["report_period"] = str(latest)
                def g(keys):
                    for k in keys:
                        for ridx in idx.index:
                            if any(s in str(ridx) for s in keys):
                                return C.safe_float(idx.loc[ridx, latest])
                    return None
                out["revenue"] = g(["营业总收入", "营业收入"])
                out["net_profit"] = g(["归母净利润", "净利润"])
    except Exception:
        pass

    # 财务分析指标（ROE/毛利率/负债率/EPS）
    try:
        fa = ak.stock_financial_analysis_indicator(symbol=code, start_year="2022")
        if fa is not None and not fa.empty:
            r = fa.iloc[0]  # 最新
            for src, dst in [("净资产收益率(%)", "roe"),
                             ("销售毛利率(%)", "gross_margin"),
                             ("资产负债率(%)", "debt_ratio"),
                             ("摊薄每股收益(元)", "eps"),
                             ("主营业务收入增长率(%)", "revenue_yoy"),
                             ("净利润增长率(%)", "net_profit_yoy")]:
                if src in fa.columns:
                    out.setdefault(dst, C.safe_float(r.get(src)))
    except Exception:
        pass
    return out


def _yfinance(meta) -> dict:
    import yfinance as yf
    t = yf.Ticker(meta["yf_symbol"])
    out: dict = {}
    try:
        info = t.info or {}
    except Exception:
        info = {}
    g = info.get
    out["name"] = g("shortName") or g("longName")
    out["industry"] = g("industry") or g("sector")
    out["market_cap"] = C.safe_float(g("marketCap"))
    out["pe_ttm"] = C.safe_float(g("trailingPE"))
    out["pe_forward"] = C.safe_float(g("forwardPE"))
    out["pb"] = C.safe_float(g("priceToBook"))
    out["ps"] = C.safe_float(g("priceToSalesTrailing12Months"))
    dy = C.safe_float(g("dividendYield"))
    out["dividend_yield"] = round(dy * 100, 2) if dy and dy < 1 else dy
    out["revenue"] = C.safe_float(g("totalRevenue"))
    out["revenue_yoy"] = C.safe_float(g("revenueGrowth"))
    if out["revenue_yoy"] is not None:
        out["revenue_yoy"] = round(out["revenue_yoy"] * 100, 2)
    out["net_profit"] = C.safe_float(g("netIncomeToCommon"))
    eg = C.safe_float(g("earningsGrowth"))
    out["net_profit_yoy"] = round(eg * 100, 2) if eg is not None else None
    gm = C.safe_float(g("grossMargins"))
    out["gross_margin"] = round(gm * 100, 2) if gm is not None else None
    nm = C.safe_float(g("profitMargins"))
    out["net_margin"] = round(nm * 100, 2) if nm is not None else None
    roe = C.safe_float(g("returnOnEquity"))
    out["roe"] = round(roe * 100, 2) if roe is not None else None
    out["eps"] = C.safe_float(g("trailingEps"))
    out["debt_to_equity"] = C.safe_float(g("debtToEquity"))
    out["current_ratio"] = C.safe_float(g("currentRatio"))
    out["beta"] = C.safe_float(g("beta"))
    out["target_mean"] = C.safe_float(g("targetMeanPrice"))
    out["recommendation"] = g("recommendationKey")
    return out


def _p0_semantic(f: dict) -> dict:
    """基本面 P0 语义：把关键指标翻成强/中/弱信号，供评分与报告引用。"""
    flags = []
    score = 50.0  # 0-100
    ry = f.get("revenue_yoy")
    ny = f.get("net_profit_yoy")
    roe = f.get("roe")
    gm = f.get("gross_margin")
    pe = f.get("pe_ttm")

    if ny is not None:
        if ny > 30: score += 12; flags.append(f"净利同比 +{ny}%（高增长）")
        elif ny > 0: score += 5; flags.append(f"净利同比 +{ny}%（正增长）")
        else: score -= 12; flags.append(f"净利同比 {ny}%（下滑）")
    if ry is not None:
        if ry > 20: score += 8; flags.append(f"营收同比 +{ry}%（扩张）")
        elif ry < 0: score -= 6; flags.append(f"营收同比 {ry}%（收缩）")
    if roe is not None:
        if roe > 15: score += 8; flags.append(f"ROE {roe}%（优秀）")
        elif roe < 5: score -= 5; flags.append(f"ROE {roe}%（偏低）")
    if gm is not None and gm > 40:
        score += 4; flags.append(f"毛利率 {gm}%（高壁垒）")
    if pe is not None:
        if pe < 0: score -= 8; flags.append("PE 为负（亏损）")
        elif pe > 80: score -= 6; flags.append(f"PE {pe}（估值偏高）")
        elif pe < 15: score += 4; flags.append(f"PE {pe}（估值较低）")
    score = max(0, min(100, round(score, 1)))
    grade = "强" if score >= 65 else "中" if score >= 45 else "弱"
    return {"score": score, "grade": grade, "flags": flags}


def fetch(symbol: str) -> dict:
    meta = C.detect_market(symbol)
    ck = f"{meta['engine']}:{meta['code']}"
    cached = C.cache_get("fundamental", ck, ttl_hours=24.0)
    if cached:
        return cached
    f, err = {}, ""
    try:
        if meta["engine"] == "akshare_cn":
            f = _akshare_cn(meta)
        elif meta["engine"] == "akshare_hk":
            try:
                f = _yfinance(meta)
            except Exception:
                f = {}
        else:
            f = _yfinance(meta)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"

    if not f:
        result = {"meta": meta, "fundamentals": C.block_result("error", None, err or "无基本面数据")}
    else:
        result = {"meta": meta,
                  "fundamentals": C.block_result("ok", f, source=meta["engine"]),
                  "p0": C.block_result("ok", _p0_semantic(f))}
    C.cache_set("fundamental", ck, result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    a = ap.parse_args()
    C.print_json(fetch(a.symbol))


if __name__ == "__main__":
    main()
