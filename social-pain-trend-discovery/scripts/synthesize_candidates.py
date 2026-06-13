#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synthesize_candidates.py
========================
读取 Agent 在全网搜索后整理出的「痛点发现 findings JSON」，
做去重 + 信号打分 + 关键词候选词生成，输出一份可直接喂给
`aba-keyword-niche-analysis` Skill 的候选关键词清单 JSON + 控制台摘要。

输入 findings JSON 结构（由 Agent 填充，见 references/findings-schema.md）：
{
  "category": "electronics",
  "market": "US",
  "pain_points": [
    {
      "summary": "想要不打孔、不挡出风口、磁吸够强的车载手机支架",
      "product_noun": "car phone mount",
      "desired_features": ["no drill", "strong magnet", "one hand"],
      "audiences": ["commuters"],
      "scenarios": ["car", "truck"],
      "negative_signals": ["falls off", "blocks vent"],
      "mention_count": 7,
      "sources": [
        {"platform": "reddit", "url": "...", "quote": "...", "date": "2026-03"},
        {"platform": "youtube", "url": "...", "quote": "...", "date": "2025-11"}
      ]
    }
  ]
}

用法：
    python synthesize_candidates.py findings.json --out candidate_keywords.json --top 40
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def norm_kw(s):
    s = re.sub(r"\s+", " ", str(s).lower()).strip()
    s = re.sub(r"[^a-z0-9 \-]", "", s)
    return s


def gen_keyword_candidates(pp):
    """
    从单个痛点生成候选 Amazon 搜索词（英文）。
    组合规则：
      base = product_noun
      modifier × base
      base + for + scenario
      base + audience
      modifier + base + for + scenario
    """
    base = norm_kw(pp.get("product_noun", ""))
    if not base:
        return []

    feats = [norm_kw(f) for f in pp.get("desired_features", []) if norm_kw(f)]
    scenes = [norm_kw(s) for s in pp.get("scenarios", []) if norm_kw(s)]
    auds = [norm_kw(a) for a in pp.get("audiences", []) if norm_kw(a)]

    cands = set()
    cands.add(base)
    for f in feats:
        cands.add(f"{f} {base}")
    for sc in scenes:
        cands.add(f"{base} for {sc}")
    for a in auds:
        cands.add(f"{base} {a}")
    # 双修饰组合（modifier + base + 场景），控制数量避免爆炸
    for f in feats[:3]:
        for sc in scenes[:2]:
            cands.add(f"{f} {base} for {sc}")

    # 清洗：去空、去过长（亚马逊搜索词一般 <= 6 词）
    out = []
    for c in cands:
        c = re.sub(r"\s+", " ", c).strip()
        if c and len(c.split()) <= 6:
            out.append(c)
    return out


def signal_score(pp):
    """
    信号强度 0-10：
      volume    : mention_count，封顶 → 0-5
      diversity : 不同平台数，封顶 3 → 0-3
      recency   : 含 2026 来源 +2，否则含 2025 +1，否则 0
    """
    mc = pp.get("mention_count")
    if not isinstance(mc, (int, float)):
        mc = len(pp.get("sources", []))
    volume = min(mc / 2.0, 5.0)

    platforms = set()
    has_2026 = has_2025 = False
    for s in pp.get("sources", []):
        p = (s.get("platform") or "").lower().strip()
        if p:
            platforms.add(p)
        d = str(s.get("date") or "")
        if "2026" in d:
            has_2026 = True
        elif "2025" in d:
            has_2025 = True
    diversity = min(len(platforms), 3) * 1.0
    recency = 2.0 if has_2026 else (1.0 if has_2025 else 0.0)

    score = volume + diversity + recency
    return round(min(score, 10.0), 2), {
        "volume": round(volume, 2),
        "diversity": round(diversity, 2),
        "recency": recency,
        "platforms": sorted(platforms),
        "mention_count": mc,
    }


def main():
    ap = argparse.ArgumentParser(description="把痛点 findings 合成候选关键词清单")
    ap.add_argument("findings", help="findings JSON 路径")
    ap.add_argument("--out", default="candidate_keywords.json", help="输出 JSON")
    ap.add_argument("--top", type=int, default=40, help="保留候选关键词数量")
    args = ap.parse_args()

    if not os.path.isfile(args.findings):
        print(f"[错误] findings 文件不存在: {args.findings}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.findings, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[错误] findings JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(3)

    pps = data.get("pain_points", [])
    if not isinstance(pps, list) or len(pps) == 0:
        print("[错误] findings 中没有 pain_points，或为空。请确认 Agent 已整理痛点。", file=sys.stderr)
        sys.exit(3)

    if len(pps) < 3:
        print(f"[警告] 仅 {len(pps)} 个痛点，样本偏少，候选词覆盖面有限。建议扩大搜索或合并多次结果。",
              file=sys.stderr)

    category = data.get("category", "unknown")
    market = data.get("market", "US")

    # 候选词 -> 聚合信息
    kw_map = defaultdict(lambda: {"keyword": None, "from_pains": [], "score_sum": 0.0,
                                  "platforms": set(), "best_score": 0.0})
    pain_scored = []

    for i, pp in enumerate(pps):
        score, detail = signal_score(pp)
        pp_id = pp.get("id") or f"pain_{i+1}"
        pain_scored.append({
            "id": pp_id,
            "summary": pp.get("summary", ""),
            "product_noun": pp.get("product_noun", ""),
            "signal_score": score,
            "score_detail": detail,
            "negative_signals": pp.get("negative_signals", []),
            "source_count": len(pp.get("sources", [])),
        })
        for kw in gen_keyword_candidates(pp):
            entry = kw_map[kw]
            entry["keyword"] = kw
            entry["from_pains"].append(pp_id)
            entry["score_sum"] += score
            entry["best_score"] = max(entry["best_score"], score)
            for p in detail["platforms"]:
                entry["platforms"].add(p)

    # 候选词最终分：best_score 为主 + 出现在多个痛点的加成
    candidates = []
    for kw, e in kw_map.items():
        multi_pain_bonus = min(len(set(e["from_pains"])) - 1, 2) * 0.5
        final = round(min(e["best_score"] + multi_pain_bonus, 10.0), 2)
        candidates.append({
            "keyword": kw,
            "signal_score": final,
            "from_pains": sorted(set(e["from_pains"])),
            "platforms": sorted(e["platforms"]),
            "word_count": len(kw.split()),
            "type": "head" if len(kw.split()) <= 2 else "long_tail",
        })

    candidates.sort(key=lambda x: (-x["signal_score"], x["keyword"]))
    candidates = candidates[:args.top]

    pain_scored.sort(key=lambda x: -x["signal_score"])

    out = {
        "category": category,
        "market": market,
        "generated_from": os.path.basename(args.findings),
        "pain_points_ranked": pain_scored,
        "candidate_keywords": candidates,
        "feeds_into": "aba-keyword-niche-analysis",
        "next_step": (
            "把这些候选关键词带到 Amazon 卖家后台拉对应 ABA Top Search Terms 周报（或用卖家精灵 "
            "keyword_research MCP 直接验证），再交给 aba-keyword-niche-analysis Skill 做五维评分选品。"
        ),
    }

    try:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[错误] 写入候选词失败: {e}", file=sys.stderr)
        sys.exit(4)

    # 控制台摘要
    print("=" * 60)
    print(f"痛点 → 候选关键词合成   品类={category}  市场={market}")
    print("=" * 60)
    print(f"痛点数: {len(pps)}   生成候选关键词: {len(candidates)}")
    print("-" * 60)
    print("Top 痛点 (按信号强度):")
    for p in pain_scored[:8]:
        print(f"   [{p['signal_score']:>4}] {p['summary'][:46]}  (来源{p['source_count']})")
    print("-" * 60)
    print(f"Top 候选关键词 (前 {min(20, len(candidates))}):")
    for c in candidates[:20]:
        tag = "长尾" if c["type"] == "long_tail" else "大词"
        print(f"   [{c['signal_score']:>4}|{tag}] {c['keyword']}")
    print("=" * 60)
    print(f"[完成] 候选关键词已写入: {os.path.abspath(args.out)}")
    print("[提示] 下一步：用这些词拉 ABA 周报 → 交给 aba-keyword-niche-analysis 做选品评分。")


if __name__ == "__main__":
    main()
