#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
premarket.py —— A股早盘决策一键聚合 + 当日/三日预测引擎（可追溯）

把五个板块的数据聚合，算出【确定性、可追溯】的因子子分与加权早盘分，
并给出：
  · 今日 9:30-15:00 的预测开盘缺口、最高/最低点(ATR模型 + 技术位校准)
  · 未来三天趋势标签 + 理论高低价位(支撑压力 / 波浪位置)
  · 持仓分析(输入买入价+股数 → 浮盈亏/套牢/解套位/今日操作建议)
五因子：技术面 / 资金面 / 宏观隔夜 / 板块联动 / 情绪面（权重可用 W_PM_* 覆盖）。
消息/政策的语义解读交给 Claude（见 references/premarket-framework.md）。

用法：
  python premarket.py 002156 --save
  python premarket.py 002156 --buy-price 26.8 --shares 1000 --save
  python premarket.py 002156 --review        # 看昨日预测，待回填实际值做复盘学习
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import common as C
import fetch_market as FM
import fetch_capital_flow as CF
import sentiment as SE
import fetch_overnight as OV
import fetch_linkage as LK
import fetch_orderbook as OB
import analyze as A  # 复用 technical_score / capital_score / technical_levels

JOURNAL = C.OUTPUT_DIR / "premarket_journal.jsonl"

DEFAULT_PM_WEIGHTS = {
    "technical": 0.25,   # 个股量价结构/动量
    "capital": 0.22,     # 主力资金(前一日/连续)
    "overnight": 0.20,   # 宏观隔夜 + 亚太早盘 + 汇率利率
    "linkage": 0.18,     # 板块同业/ETF 合力
    "sentiment": 0.15,   # 市场情绪温度
}
PM_ENV = {"technical": "W_PM_TECH", "capital": "W_PM_CAPITAL",
          "overnight": "W_PM_OVERNIGHT", "linkage": "W_PM_LINKAGE",
          "sentiment": "W_PM_SENTIMENT"}
PM_CN = {"technical": "技术面", "capital": "资金面", "overnight": "宏观隔夜",
         "linkage": "板块联动", "sentiment": "情绪面"}


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def load_pm_weights() -> dict:
    w = dict(DEFAULT_PM_WEIGHTS)
    for k, env in PM_ENV.items():
        v = C.safe_float(C.get(env))
        if v is not None:
            w[k] = v
    s = sum(w.values()) or 1.0
    return {k: round(v / s, 4) for k, v in w.items()}


def compose_pm(scores: dict, applicable: dict, weights: dict) -> dict:
    """不适用的因子(取 50)把权重按比例摊给其余因子，保证可追溯。"""
    w = {k: weights[k] for k in DEFAULT_PM_WEIGHTS}
    dead = [k for k in w if not applicable.get(k, True)]
    if dead:
        freed = sum(w[k] for k in dead)
        live = {k: v for k, v in w.items() if k not in dead}
        rest = sum(live.values()) or 1.0
        for k in live:
            w[k] = live[k] + freed * live[k] / rest
        for k in dead:
            w[k] = 0.0
    breakdown, composite = [], 0.0
    for k in DEFAULT_PM_WEIGHTS:
        sc = scores.get(k, 50.0)
        wt = round(w[k], 4)
        contrib = round(sc * wt, 2)
        composite += contrib
        breakdown.append({"factor": PM_CN[k], "key": k, "score": sc,
                          "weight": wt, "contribution": contrib,
                          "applicable": applicable.get(k, True)})
    composite = round(composite, 1)
    return {"premarket_score": composite, "weights_used": {k: round(w[k], 4) for k in w},
            "breakdown": breakdown}


def _action(c: float) -> tuple[str, str]:
    if c >= 66: return "积极参与 / 低吸为主", "偏多"
    if c >= 56: return "谨慎偏多 / 逢回踩介入", "中性偏多"
    if c >= 45: return "观望为主 / 不追高", "中性"
    if c >= 34: return "防守 / 反弹减仓", "中性偏空"
    return "回避 / 反弹了结", "偏空"


# ---------------------------------------------------------------------------
# 预测：今日高低点 + 三日趋势
# ---------------------------------------------------------------------------
def predict(ind: dict, prev_close: float, levels: dict,
            bias: float, ext_bias: float, trend_bias: float) -> dict:
    atr = ind.get("atr14")
    if not prev_close:
        return {"status": "no_price"}
    # ---- 今日 ----
    gap_pct = _clamp(ext_bias * 1.5, -3.0, 3.0)              # 外部环境主导跳空
    pred_open = prev_close * (1 + gap_pct / 100)
    rng = (atr if atr else prev_close * 0.025) * (0.9 + 0.4 * abs(bias))
    up_share = _clamp(0.5 + 0.35 * bias, 0.2, 0.8)
    pred_high = pred_open + rng * up_share
    pred_low = pred_open - rng * (1 - up_share)

    res = levels.get("resistances") or []
    sup = levels.get("supports") or []
    near_res = next((r for r in sorted(res) if r >= pred_open), (res and min(res)) or None)
    near_sup = next((s for s in sorted(sup, reverse=True) if s <= pred_open), (sup and max(sup)) or None)
    # 用技术位校准：高点不轻易穿越最近压力(除非强多)，低点获最近支撑托底
    high_ref = pred_high
    if near_res and bias < 0.5:
        high_ref = min(pred_high, near_res * 1.005)
    low_ref = pred_low
    if near_sup and bias > -0.5:
        low_ref = max(pred_low, near_sup * 0.995)

    # ---- 三日 ----
    rng3 = (atr if atr else prev_close * 0.025) * (3 ** 0.5) * (0.9 + 0.4 * abs(trend_bias))
    up3 = _clamp(0.5 + 0.35 * trend_bias, 0.2, 0.8)
    d3_high = prev_close + rng3 * up3
    d3_low = prev_close - rng3 * (1 - up3)
    # 三日理论位向更高级别支撑压力靠拢
    big_res = [ind.get("ma60"), ind.get("ma120"), ind.get("high_250")]
    big_res = sorted([x for x in big_res if x and x > prev_close])
    big_sup = [ind.get("ma60"), ind.get("ma120"), ind.get("low_250")]
    big_sup = sorted([x for x in big_sup if x and x < prev_close], reverse=True)
    d3_high_theory = big_res[0] if (big_res and trend_bias > 0.2 and big_res[0] < d3_high * 1.05) else round(d3_high, 2)
    d3_low_theory = big_sup[0] if (big_sup and trend_bias < -0.2 and big_sup[0] > d3_low * 0.95) else round(d3_low, 2)

    trend_label = ("偏强上行" if trend_bias > 0.35 else "震荡偏多" if trend_bias > 0.12 else
                   "震荡整理" if trend_bias > -0.12 else "震荡偏弱" if trend_bias > -0.35 else "偏弱下行")

    pos = ind.get("pos_in_range_pct")
    wave_hint = "—"
    if pos is not None:
        wave_hint = ("处年内高位区，warning 追高风险/防回落" if pos > 80 else
                     "处年内中高位，趋势中继需放量确认" if pos > 55 else
                     "处年内中位区，方向待选择" if pos > 35 else
                     "处年内低位区，关注是否波段底部/反弹弹性大" )

    dec = lambda v: round(v, 2)
    return {
        "status": "ok",
        "today": {
            "prev_close": dec(prev_close),
            "gap_pct": round(gap_pct, 2),
            "predicted_open": dec(pred_open),
            "predicted_high": dec(pred_high),
            "predicted_low": dec(pred_low),
            "high_ref": dec(high_ref),
            "low_ref": dec(low_ref),
            "expected_range_pct": round(rng / prev_close * 100, 2),
            "nearest_resistance": near_res,
            "nearest_support": near_sup,
            "atr14": atr,
        },
        "three_day": {
            "trend_label": trend_label,
            "trend_bias": round(trend_bias, 3),
            "high_theory": d3_high_theory,
            "low_theory": d3_low_theory,
            "high_atr_model": dec(d3_high),
            "low_atr_model": dec(d3_low),
            "wave_position": wave_hint,
        },
        "model_note": "高低点 = 预测开盘 ± ATR×波动系数(按多空偏向劈分)，再用最近支撑/压力位校准；"
                      "三日用 ATR×√3 放大并向中级别均线/年内高低靠拢。属概率区间，非精确点位。",
    }


def position_analysis(buy_price: float, shares: float, prev_close: float,
                      pred: dict, trend_bias: float, levels: dict) -> dict:
    if not buy_price or not prev_close:
        return {"status": "skipped", "note": "未提供买入价，跳过持仓分析"}
    cost = buy_price * shares if shares else None
    cur = prev_close * shares if shares else None
    pnl = (cur - cost) if (cost is not None and cur is not None) else None
    pnl_pct = (prev_close - buy_price) / buy_price * 100
    locked = prev_close < buy_price
    breakeven = buy_price
    dist_be = (buy_price - prev_close) / prev_close * 100
    today = pred.get("today", {})
    can_breakeven_today = bool(today.get("predicted_high") and today["predicted_high"] >= buy_price)

    # 建议
    advice = []
    if locked:
        advice.append(f"当前浮亏 {pnl_pct:.1f}%，处于套牢状态，解套位(成本价) {breakeven}。")
        if can_breakeven_today:
            advice.append(f"今日预测高点 {today.get('predicted_high')} 可能触及成本价，"
                          f"若趋势偏弱可借反弹至 {today.get('high_ref')} 附近减仓降低风险。")
        else:
            advice.append(f"今日预测高点 {today.get('predicted_high')} 难及成本价 {breakeven}，"
                          f"短线解套概率低；")
        if trend_bias > 0.12:
            advice.append("三日趋势偏多，可持有等反弹，但反弹至成本价附近留意抛压。")
        elif trend_bias < -0.12:
            advice.append("三日趋势偏弱，反弹即是减仓/止损机会，控制仓位优先，避免越套越深。")
        else:
            advice.append("三日震荡，建议高抛低吸降低成本，不宜重仓死扛。")
    else:
        advice.append(f"当前浮盈 {pnl_pct:.1f}%。")
        if trend_bias > 0.12:
            advice.append(f"趋势偏多，持有为主，回踩 {today.get('low_ref')} / 支撑 "
                          f"{(levels.get('supports') or ['—'])[0]} 可考虑加仓。")
        elif trend_bias < -0.12:
            advice.append(f"趋势转弱，逢高(预测高点 {today.get('predicted_high')})兑现部分利润，落袋为安。")
        else:
            advice.append("趋势震荡，持盈守正，跌破支撑再考虑减仓。")
    advice.append("提示：避免在高位听消息追买——以预测高低区间与支撑压力为锚，分批操作。")

    return {
        "status": "ok",
        "buy_price": buy_price, "shares": shares,
        "cost": round(cost, 2) if cost is not None else None,
        "market_value": round(cur, 2) if cur is not None else None,
        "pnl": round(pnl, 2) if pnl is not None else None,
        "pnl_pct": round(pnl_pct, 2),
        "locked": locked,
        "breakeven": breakeven,
        "distance_to_breakeven_pct": round(dist_be, 2),
        "can_breakeven_today": can_breakeven_today,
        "advice": advice,
    }


def gather(symbol: str, buy_price: float = None, shares: float = None,
           with_news: bool = False) -> dict:
    meta = C.detect_market(symbol)
    mk = FM.fetch(symbol, days=120)
    cp = CF.fetch(symbol)
    se = SE.fetch(symbol)
    ov = OV.fetch(meta["code"] if meta["market"] == "A" else "")
    lk = LK.fetch(symbol) if meta["market"] == "A" else {"status": "not_supported", "linkage_tilt": None}
    ob = OB.fetch(symbol)

    ind = (mk.get("indicators", {}) or {}).get("data") or {}
    quote = mk.get("quote", {})
    prev_close = (quote.get("data") or {}).get("price") or ind.get("close")
    senti = (se.get("sentiment", {}) or {}).get("data") or {}

    # ---- 因子子分 ----
    t_sc, t_notes = A.technical_score(ind)
    c_sc, c_notes, c_appl = A.capital_score(cp.get("capital_flow", {}))
    s_sc = senti.get("temperature", 50.0)
    macro = ov.get("macro_tilt")
    proxy = ov.get("proxy_tilt")
    if macro is None:
        o_sc, o_appl = 50.0, False
    else:
        o_sc = round(0.45 * macro + 0.55 * proxy, 1) if proxy is not None else macro
        o_appl = True
    link_tilt = lk.get("linkage_tilt")
    if link_tilt is None:
        l_sc, l_appl = 50.0, False
    else:
        l_sc, l_appl = link_tilt, True

    scores = {"technical": t_sc, "capital": c_sc, "overnight": o_sc,
              "linkage": l_sc, "sentiment": s_sc}
    applicable = {"technical": True, "capital": c_appl, "overnight": o_appl,
                  "linkage": l_appl, "sentiment": True}
    weights = load_pm_weights()
    decision = compose_pm(scores, applicable, weights)
    score = decision["premarket_score"]

    # ---- 偏向 ----
    bias = _clamp((score - 50) / 50, -1, 1)
    ext_bias = _clamp(((o_sc + l_sc) / 2 - 50) / 50, -1, 1)          # 外部(隔夜+联动)主导跳空
    trend_bias = _clamp(((t_sc + c_sc + l_sc) / 3 - 50) / 50, -1, 1)  # 慢变量主导三日

    levels = A.technical_levels(ind, quote)
    pred = predict(ind, prev_close, levels, bias, ext_bias, trend_bias)
    pos = position_analysis(buy_price, shares, prev_close, pred, trend_bias, levels)
    action, stance = _action(score)

    # ---- 因子一致性 → 置信度 ----
    signs = []
    for k in ("technical", "capital", "overnight", "linkage", "sentiment"):
        if applicable[k]:
            signs.append(1 if scores[k] > 52 else -1 if scores[k] < 48 else 0)
    nz = [x for x in signs if x != 0]
    agree = (max(nz.count(1), nz.count(-1)) / len(nz)) if nz else 0.5
    confidence = "高" if agree >= 0.8 and abs(bias) > 0.2 else "中" if agree >= 0.6 else "低"

    news = {"status": "skipped"}
    if with_news:
        try:
            import anspire_search
            name = lk.get("peers") and meta["code"] or meta["code"]
            news = anspire_search.fetch(meta["code"], meta["code"], meta["market"])
        except Exception as e:
            news = {"status": "error", "note": type(e).__name__}

    return {
        "schema": "stock-tp-premarket/v1",
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "symbol": symbol, "meta": meta,
        "blocks": {"market": mk, "capital": cp, "sentiment": se,
                   "overnight": ov, "linkage": lk, "orderbook": ob, "news": news},
        "factor_scores": {
            "technical": {"score": t_sc, "notes": t_notes},
            "capital": {"score": c_sc, "notes": c_notes, "applicable": c_appl},
            "overnight": {"score": o_sc, "macro_tilt": macro, "proxy_tilt": proxy, "applicable": o_appl},
            "linkage": {"score": l_sc, "tilt": link_tilt, "applicable": l_appl,
                        "peer_consensus": lk.get("peer_consensus")},
            "sentiment": {"score": s_sc, "label": senti.get("label")},
        },
        "weights": weights,
        "decision": {**decision, "action": action, "stance": stance, "confidence": confidence,
                     "bias": round(bias, 3), "factor_agreement": round(agree, 2)},
        "prediction": pred,
        "position": pos,
        "technical_levels": levels,
        "next_step": "Claude 读本包 → 结合 overnight/linkage/news 做信息面语义解读 → 校正预测与建议 → "
                     "套 templates/premarket-report.md 出《今日作战图》。收盘后用 --review 回填实际值复盘。",
    }


def journal_append(bundle: dict):
    today = (bundle.get("prediction") or {}).get("today") or {}
    td3 = (bundle.get("prediction") or {}).get("three_day") or {}
    rec = {
        "date": dt.date.today().isoformat(),
        "code": bundle["meta"]["code"],
        "premarket_score": bundle["decision"]["premarket_score"],
        "bias": bundle["decision"]["bias"],
        "pred_open": today.get("predicted_open"),
        "pred_high": today.get("predicted_high"),
        "pred_low": today.get("predicted_low"),
        "trend_label": td3.get("trend_label"),
        "weights": bundle["weights"],
        # 复盘时回填：
        "actual_open": None, "actual_high": None, "actual_low": None, "actual_close": None,
        "hit_high_err_pct": None, "hit_low_err_pct": None, "reviewed": False,
    }
    try:
        with JOURNAL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


def review(code: str):
    """打印该股历史预测记录，供 Claude 对照实际表现做复盘学习。"""
    if not JOURNAL.exists():
        return {"status": "empty", "note": "尚无预测日志"}
    rows = []
    for line in JOURNAL.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
            if not code or r.get("code") == code:
                rows.append(r)
        except Exception:
            pass
    return {"status": "ok", "code": code, "count": len(rows), "records": rows[-20:],
            "note": "回填 actual_* 后，Claude 按 references/premarket-learning.md 统计命中率并微调 W_PM_*。"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--buy-price", type=float, default=None)
    ap.add_argument("--shares", type=float, default=None)
    ap.add_argument("--news", action="store_true", help="叠加 Anspire 新闻检索(需Key)")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--review", action="store_true", help="查看历史预测日志(复盘)")
    a = ap.parse_args()

    if a.review:
        C.print_json(review(C.detect_market(a.symbol)["code"]))
        return

    bundle = gather(a.symbol, a.buy_price, a.shares, with_news=a.news)
    journal_append(bundle)
    if a.save:
        meta = bundle["meta"]
        fn = C.OUTPUT_DIR / f"{meta['code']}_{dt.date.today().isoformat()}_premarket.json"
        Path(fn).write_text(C.to_json(bundle), encoding="utf-8")
        bundle["_saved"] = str(fn)
    C.print_json(bundle)


if __name__ == "__main__":
    main()
