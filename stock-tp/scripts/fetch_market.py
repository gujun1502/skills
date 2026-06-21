#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_market.py —— 行情 + K线 + 技术指标

引擎：
  A股/ETF  -> akshare (stock_zh_a_hist / fund_etf_hist_em)
  港股      -> akshare (stock_hk_hist) 兜底 yfinance
  美/日/韩  -> yfinance

技术指标全部本地计算（MA/EMA/MACD/RSI/KDJ/BOLL/ATR/量比），不依赖 TA-Lib。

用法：
  python fetch_market.py 600519
  python fetch_market.py AAPL --days 250
"""
from __future__ import annotations

import argparse
import datetime as dt
from typing import Optional

import common as C

try:
    import pandas as pd
except Exception:
    pd = None


# ---------------------------------------------------------------------------
# 指标计算（输入：按时间升序的 DataFrame，列 open/high/low/close/volume）
# ---------------------------------------------------------------------------
def _ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def compute_indicators(df) -> dict:
    if df is None or len(df) < 2:
        return {}
    c = df["close"].astype(float)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    v = df["volume"].astype(float)
    out: dict = {}

    last = lambda s: C.safe_float(s.iloc[-1])

    # 均线
    for n in (5, 10, 20, 30, 60, 120, 250):
        if len(c) >= n:
            out[f"ma{n}"] = round(c.tail(n).mean(), 4)
    out["close"] = last(c)

    # 均线多空排列
    arr = [out.get(f"ma{n}") for n in (5, 10, 20, 60) if out.get(f"ma{n}") is not None]
    if len(arr) >= 3:
        out["ma_alignment"] = ("多头排列" if arr == sorted(arr, reverse=True)
                               else "空头排列" if arr == sorted(arr)
                               else "纠缠")

    # MACD
    if len(c) >= 26:
        dif = _ema(c, 12) - _ema(c, 26)
        dea = _ema(dif, 9)
        macd = (dif - dea) * 2
        out["macd"] = {"dif": round(last(dif), 4), "dea": round(last(dea), 4),
                       "hist": round(last(macd), 4),
                       "signal": "金叉" if last(dif) > last(dea) else "死叉"}

    # RSI(14)
    if len(c) >= 15:
        delta = c.diff()
        up = delta.clip(lower=0).rolling(14).mean()
        dn = (-delta.clip(upper=0)).rolling(14).mean()
        rs = up / dn.replace(0, 1e-9)
        rsi = 100 - 100 / (1 + rs)
        out["rsi14"] = round(last(rsi), 2)

    # KDJ(9,3,3)
    if len(c) >= 9:
        low9 = l.rolling(9).min()
        high9 = h.rolling(9).max()
        rsv = (c - low9) / (high9 - low9).replace(0, 1e-9) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        j = 3 * k - 2 * d
        out["kdj"] = {"k": round(last(k), 2), "d": round(last(d), 2), "j": round(last(j), 2)}

    # BOLL(20,2)
    if len(c) >= 20:
        mid = c.rolling(20).mean()
        std = c.rolling(20).std()
        out["boll"] = {"upper": round(last(mid + 2 * std), 4),
                       "mid": round(last(mid), 4),
                       "lower": round(last(mid - 2 * std), 4)}

    # ATR(14) 波动
    if len(c) >= 15:
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        out["atr14"] = round(last(tr.rolling(14).mean()), 4)

    # 量比（今量 / 过去5日均量）
    if len(v) >= 6:
        out["volume_ratio"] = round(last(v) / v.tail(6).head(5).mean(), 2) if v.tail(6).head(5).mean() else None

    # 区间涨跌
    for n, label in ((5, "chg_5d"), (20, "chg_20d"), (60, "chg_60d")):
        if len(c) > n:
            out[label] = C.pct(c.iloc[-1], c.iloc[-1 - n])
    out["chg_1d"] = C.pct(c.iloc[-1], c.iloc[-2]) if len(c) >= 2 else None

    # 52周高低位置
    if len(c) >= 60:
        hi, lo = c.tail(250).max(), c.tail(250).min()
        out["pos_in_range_pct"] = C.pct(c.iloc[-1], lo) and round(
            (c.iloc[-1] - lo) / (hi - lo) * 100, 1) if hi > lo else None
        out["high_250"] = round(hi, 4)
        out["low_250"] = round(lo, 4)
    return out


# ---------------------------------------------------------------------------
# 取数
# ---------------------------------------------------------------------------
def _akshare_cn_kline(meta, days):
    """A股/ETF：东方财富(stock_zh_a_hist)主源，失败时切新浪(stock_zh_a_daily)兜底。"""
    import akshare as ak
    end = dt.date.today()
    start = end - dt.timedelta(days=int(days * 1.8) + 40)
    sd, ed = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    code = meta["code"]
    is_etf = code[:2] in ("51", "15", "56", "58", "16", "50") and meta["market"] == "A"

    # 主源：东方财富
    try:
        if is_etf:
            df = ak.fund_etf_hist_em(symbol=code, period="daily",
                                     start_date=sd, end_date=ed, adjust="qfq")
        else:
            df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                    start_date=sd, end_date=ed, adjust="qfq")
        if df is not None and not df.empty:
            return df.rename(columns={"日期": "date", "开盘": "open", "收盘": "close",
                                      "最高": "high", "最低": "low", "成交量": "volume",
                                      "成交额": "amount", "换手率": "turnover"})
    except Exception:
        pass

    # 兜底：新浪（需要 sh/sz 前缀）
    prefix = {"SH": "sh", "SZ": "sz", "BJ": "bj"}.get(meta["board"], "sh")
    sina_sym = f"{prefix}{code}"
    df = ak.stock_zh_a_daily(symbol=sina_sym, start_date=sd, end_date=ed, adjust="qfq")
    return df.rename(columns={"date": "date", "open": "open", "close": "close",
                              "high": "high", "low": "low", "volume": "volume",
                              "amount": "amount"})


def _akshare_hk_kline(meta, days):
    import akshare as ak
    end = dt.date.today()
    start = end - dt.timedelta(days=int(days * 1.8) + 40)
    df = ak.stock_hk_hist(symbol=meta["code"], period="daily",
                          start_date=start.strftime("%Y%m%d"),
                          end_date=end.strftime("%Y%m%d"), adjust="qfq")
    df = df.rename(columns={"日期": "date", "开盘": "open", "收盘": "close",
                            "最高": "high", "最低": "low", "成交量": "volume",
                            "成交额": "amount"})
    return df


def _yf_kline(meta, days):
    import yfinance as yf
    period = "2y" if days > 250 else "1y"
    t = yf.Ticker(meta["yf_symbol"])
    df = t.history(period=period, auto_adjust=True)
    if df is None or df.empty:
        return None
    df = df.reset_index().rename(columns={
        "Date": "date", "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume"})
    return df


def fetch(symbol: str, days: int = 250) -> dict:
    meta = C.detect_market(symbol)
    ck = f"{meta['engine']}:{meta['code']}:{days}"
    cached = C.cache_get("market", ck, ttl_hours=2.0)
    if cached:
        return cached

    kline = None
    err = ""
    try:
        if meta["engine"] == "akshare_cn":
            kline = _akshare_cn_kline(meta, days)
        elif meta["engine"] == "akshare_hk":
            try:
                kline = _akshare_hk_kline(meta, days)
            except Exception:
                kline = _yf_kline(meta, days)
        else:
            kline = _yf_kline(meta, days)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"

    result = {"meta": meta}
    if kline is None or (hasattr(kline, "empty") and kline.empty):
        result["quote"] = C.block_result("error", None, err or "无K线数据")
        result["indicators"] = C.block_result("empty")
        result["kline_tail"] = C.block_result("empty")
    else:
        for col in ("open", "high", "low", "close", "volume"):
            if col in kline:
                kline[col] = pd.to_numeric(kline[col], errors="coerce")
        kline = kline.dropna(subset=["close"]).reset_index(drop=True)
        ind = compute_indicators(kline)
        tail = kline.tail(20)[["date", "open", "high", "low", "close", "volume"]]
        tail = tail.copy()
        tail["date"] = tail["date"].astype(str)
        last = kline.iloc[-1]
        result["quote"] = C.block_result("ok", {
            "date": str(last.get("date", "")),
            "price": C.safe_float(last["close"]),
            "open": C.safe_float(last["open"]),
            "high": C.safe_float(last["high"]),
            "low": C.safe_float(last["low"]),
            "volume": C.safe_float(last["volume"]),
            "chg_pct": ind.get("chg_1d"),
            "currency": meta["currency"],
        }, source=meta["engine"])
        result["indicators"] = C.block_result("ok", ind, source="本地计算")
        result["kline_tail"] = C.block_result("ok", tail.to_dict("records"))
    C.cache_set("market", ck, result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--days", type=int, default=250)
    a = ap.parse_args()
    C.print_json(fetch(a.symbol, a.days))


if __name__ == "__main__":
    main()
