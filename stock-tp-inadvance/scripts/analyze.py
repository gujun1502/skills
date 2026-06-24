#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze.py —— 四块聚合 + 可追溯加权决策引擎

把四个研究块的数据聚合，计算【确定性、可追溯】的因子子分与加权综合分，
给出技术买卖点位与初步操作建议，输出一个 JSON 数据包。

设计原则——决策过程"可视、可追溯、权重可调"：
  * 5 个因子子分（0-100）：消息面 / 情绪面 / 基本面 / 技术面 / 资金面
  * 权重默认见 DEFAULT_WEIGHTS，可用环境变量 W_NEWS / W_SENTIMENT / W_FUND /
    W_TECH / W_CAPITAL 覆盖；脚本会把每个因子的"得分 × 权重 = 贡献"全部列出。
  * 消息面子分需要语义判断：脚本留 news_score=None（占位 50），交给 Claude 依据
    references/prompts.md 的"拆解预言"流程评分后回填，再重算综合分（complete_decision()）。

用法：
  python analyze.py 600519
  python analyze.py AAPL --days 250
  python analyze.py 600519 --news-score 72   # 回填消息面分后重算
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import common as C
import fetch_market
import fetch_fundamentals
import fetch_capital_flow
import sentiment as sent
import anspire_search

DEFAULT_WEIGHTS = {
    "news": 0.22,       # 信息/消息/新闻面
    "sentiment": 0.13,  # 情绪面
    "fundamental": 0.25,  # 财报/行业/盈利点
    "technical": 0.22,  # 技术面（量价）
    "capital": 0.18,    # 资金面（主力/筹码）
}
WEIGHT_ENV = {"news": "W_NEWS", "sentiment": "W_SENTIMENT", "fundamental": "W_FUND",
              "technical": "W_TECH", "capital": "W_CAPITAL"}
FACTOR_CN = {"news": "消息面", "sentiment": "情绪面", "fundamental": "基本面",
             "technical": "技术面", "capital": "资金面"}


def load_weights() -> dict:
    w = dict(DEFAULT_WEIGHTS)
    for k, env in WEIGHT_ENV.items():
        v = C.safe_float(C.get(env))
        if v is not None:
            w[k] = v
    s = sum(w.values()) or 1.0
    return {k: round(v / s, 4) for k, v in w.items()}  # 归一化


# ---------------------------------------------------------------------------
# 因子子分
# ---------------------------------------------------------------------------
def technical_score(ind: dict) -> tuple[float, list[str]]:
    if not ind:
        return 50.0, ["无技术指标，取中性 50"]
    s, notes = 50.0, []
    align = ind.get("ma_alignment")
    if align == "多头排列":
        s += 12; notes.append("均线多头排列 +12")
    elif align == "空头排列":
        s -= 12; notes.append("均线空头排列 -12")
    macd = (ind.get("macd") or {}).get("signal")
    if macd == "金叉":
        s += 8; notes.append("MACD 金叉 +8")
    elif macd == "死叉":
        s -= 8; notes.append("MACD 死叉 -8")
    rsi = ind.get("rsi14")
    if rsi is not None:
        if rsi > 75: s -= 7; notes.append(f"RSI {rsi} 超买 -7")
        elif rsi < 28: s += 7; notes.append(f"RSI {rsi} 超卖(反弹预期) +7")
        elif 45 <= rsi <= 62: s += 3; notes.append(f"RSI {rsi} 健康 +3")
    j = (ind.get("kdj") or {}).get("j")
    if j is not None:
        if j > 100: s -= 4; notes.append(f"KDJ J={j} 高位 -4")
        elif j < 0: s += 4; notes.append(f"KDJ J={j} 低位 +4")
    close, ma20 = ind.get("close"), ind.get("ma20")
    if close and ma20:
        if close > ma20: s += 5; notes.append("收盘站上 MA20 +5")
        else: s -= 5; notes.append("收盘跌破 MA20 -5")
    ch = ind.get("chg_20d")
    if ch is not None:
        s += max(-8, min(8, ch * 0.4))
        notes.append(f"20日动量 {ch:+.1f}% ({max(-8, min(8, ch*0.4)):+.1f})")
    return max(0, min(100, round(s, 1))), notes


def capital_score(cap_block: dict) -> tuple[float, list[str], bool]:
    """返回 (分, 说明, 是否适用)。不适用时中性且权重将被重分配。"""
    st = cap_block.get("status")
    if st == "not_supported":
        return 50.0, ["该市场不支持资金流，权重重分配到其它因子"], False
    if st != "ok":
        return 50.0, [f"资金流取数失败({cap_block.get('note','')[:40]})，取中性"], True
    summ = (cap_block.get("data") or {}).get("summary", {})
    direction, streak = summ.get("direction"), summ.get("streak_days") or 0
    s, notes = 50.0, []
    if direction == "净流入":
        s += min(18, streak * 4); notes.append(f"主力连续{streak}日净流入 +{min(18, streak*4)}")
    elif direction == "净流出":
        s -= min(18, streak * 4); notes.append(f"主力连续{streak}日净流出 -{min(18, streak*4)}")
    latest = summ.get("latest_main_net")
    if latest is not None:
        notes.append(f"最新主力净额 {latest/1e8:+.2f}亿" if abs(latest) > 1e6 else f"最新主力净额 {latest:+.0f}")
    return max(0, min(100, round(s, 1))), notes, True


def technical_levels(ind: dict, quote: dict) -> dict:
    price = (quote.get("data") or {}).get("price") if quote else None
    price = price or ind.get("close")
    if not price:
        return {}
    boll = ind.get("boll") or {}
    supports, resistances = [], []
    for k in ("ma20", "ma60", "ma120"):
        v = ind.get(k)
        if v and v < price: supports.append(round(v, 3))
    if boll.get("lower") and boll["lower"] < price: supports.append(round(boll["lower"], 3))
    if ind.get("low_250"): supports.append(round(ind["low_250"], 3))
    for k in ("ma20", "ma60"):
        v = ind.get(k)
        if v and v > price: resistances.append(round(v, 3))
    if boll.get("upper") and boll["upper"] > price: resistances.append(round(boll["upper"], 3))
    if ind.get("high_250") and ind["high_250"] > price: resistances.append(round(ind["high_250"], 3))
    atr = ind.get("atr14")
    return {
        "price": round(price, 3),
        "supports": sorted(set(supports), reverse=True)[:3],
        "resistances": sorted(set(resistances))[:3],
        "atr14": atr,
        "suggested_stop": round(price - 2 * atr, 3) if atr else None,
        "note": "支撑取均线/布林下轨/年内低；止损 = 现价 - 2×ATR（可按风险偏好调整）",
    }


# ---------------------------------------------------------------------------
# 综合决策
# ---------------------------------------------------------------------------
def compose(scores: dict, weights: dict, capital_applicable: bool) -> dict:
    w = dict(weights)
    if not capital_applicable:
        # 资金面不适用：把其权重按比例分给其余因子
        cw = w.pop("capital")
        rest = sum(w.values()) or 1.0
        w = {k: v + cw * v / rest for k, v in w.items()}
        w["capital"] = 0.0
    breakdown = []
    composite = 0.0
    for k in ("news", "sentiment", "fundamental", "technical", "capital"):
        sc = scores.get(k, 50.0)
        wt = round(w.get(k, 0.0), 4)
        contrib = round(sc * wt, 2)
        composite += contrib
        breakdown.append({"factor": FACTOR_CN[k], "key": k, "score": sc,
                          "weight": wt, "contribution": contrib})
    composite = round(composite, 1)
    action, stance = _action(composite)
    return {"composite": composite, "action": action, "stance": stance,
            "weights_used": {k: round(v, 4) for k, v in w.items()},
            "breakdown": breakdown}


def _action(c: float) -> tuple[str, str]:
    if c >= 68: return "买入 / 增持", "偏多"
    if c >= 56: return "逢低买入 / 持有偏多", "中性偏多"
    if c >= 45: return "持有 / 观望", "中性"
    if c >= 33: return "减持 / 逢高减仓", "中性偏空"
    return "卖出 / 回避", "偏空"


def gather(symbol: str, days: int, with_news: bool = True) -> dict:
    meta = C.detect_market(symbol)
    mk = fetch_market.fetch(symbol, days)
    fd = fetch_fundamentals.fetch(symbol)
    cp = fetch_capital_flow.fetch(symbol)
    se = sent.fetch(symbol)
    name = ((fd.get("fundamentals", {}) or {}).get("data") or {}).get("name") or meta["code"]

    news = {"status": "skipped"}
    if with_news:
        news = anspire_search.fetch(name, meta["code"], meta["market"])

    ind = (mk.get("indicators", {}) or {}).get("data") or {}
    quote = mk.get("quote", {})
    p0 = (fd.get("p0", {}) or {}).get("data") or {}
    senti = (se.get("sentiment", {}) or {}).get("data") or {}

    t_sc, t_notes = technical_score(ind)
    c_sc, c_notes, c_appl = capital_score(cp.get("capital_flow", {}))
    f_sc = p0.get("score", 50.0)
    s_sc = senti.get("temperature", 50.0)
    n_sc = None  # 待 Claude 回填

    scores = {"technical": t_sc, "capital": c_sc, "fundamental": f_sc,
              "sentiment": s_sc, "news": n_sc if n_sc is not None else 50.0}
    weights = load_weights()
    decision = compose(scores, weights, c_appl)

    bundle = {
        "schema": "stock-tp/v1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "symbol": symbol, "name": name, "meta": meta,
        "market_data": mk, "fundamentals": fd, "capital": cp, "sentiment": se,
        "news": news,
        "factor_scores": {
            "technical": {"score": t_sc, "notes": t_notes},
            "capital": {"score": c_sc, "notes": c_notes, "applicable": c_appl},
            "fundamental": {"score": f_sc, "grade": p0.get("grade"), "flags": p0.get("flags", [])},
            "sentiment": {"score": s_sc, "label": senti.get("label"), "drivers": senti.get("drivers", [])},
            "news": {"score": n_sc, "status": "待Claude依据 references/prompts.md 拆解预言后回填"},
        },
        "technical_levels": technical_levels(ind, quote),
        "weights": weights,
        "decision_preliminary": decision,
        "next_step": "Claude 阅读本数据包 → 对 news.groups 拆解预言、对 news 评分(0-100) → "
                     "用 --news-score 重算或在报告中手动重算综合分 → 套用 templates/report-template.md 产出最终决策报告",
    }
    return bundle


def complete_decision(bundle: dict, news_score: float) -> dict:
    """回填消息面分后重算综合分。"""
    fs = bundle["factor_scores"]
    fs["news"]["score"] = news_score
    fs["news"]["status"] = "已回填"
    scores = {k: bundle["factor_scores"][k]["score"] for k in
              ("technical", "capital", "fundamental", "sentiment", "news")}
    c_appl = bundle["factor_scores"]["capital"]["applicable"]
    bundle["decision_final"] = compose(scores, bundle["weights"], c_appl)
    return bundle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--days", type=int, default=250)
    ap.add_argument("--no-news", action="store_true")
    ap.add_argument("--news-score", type=float, default=None)
    ap.add_argument("--save", action="store_true", help="写入 reports/ 目录")
    a = ap.parse_args()
    bundle = gather(a.symbol, a.days, with_news=not a.no_news)
    if a.news_score is not None:
        bundle = complete_decision(bundle, a.news_score)
    if a.save:
        meta = bundle["meta"]
        fn = C.OUTPUT_DIR / f"{meta['code']}_{dt.date.today().isoformat()}_data.json"
        Path(fn).write_text(C.to_json(bundle), encoding="utf-8")
        bundle["_saved"] = str(fn)
    C.print_json(bundle)


if __name__ == "__main__":
    main()
