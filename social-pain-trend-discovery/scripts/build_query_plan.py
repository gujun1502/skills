#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_query_plan.py
===================
为「社媒痛点 / 热词发现」生成一份结构化的全网搜索查询计划（query plan）。

输入一个品类（jewelry / daily / electronics / consumer-electronics / custom）和/或若干
种子产品词，脚本把它们展开成针对不同公开来源（Reddit / Quora / 论坛 / YouTube / TikTok /
Amazon 评论 / 通用网页）的"痛点信号"查询语句，输出 JSON 供 Agent 用 WebSearch/WebFetch 执行。

只用公开网页搜索：所有查询都是可直接喂给 WebSearch 的 google 风格 query，
或可直接 WebFetch 的 Reddit 公开 JSON 端点。不依赖任何需要鉴权的 API。

用法：
    python build_query_plan.py --category electronics --seeds "phone holder,earbuds case" --out query_plan.json
    python build_query_plan.py --category jewelry
    python build_query_plan.py --seeds "neck fan,desk organizer" --category custom
"""

import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# 品类预设：相关 subreddit、论坛、典型种子词
# 北美市场视角；可扩展。
# ---------------------------------------------------------------------------
CATEGORY_PRESETS = {
    "jewelry": {
        "label": "珠宝 / 饰品",
        "subreddits": ["jewelry", "Jewellery", "femalefashionadvice", "TwoXChromosomes",
                       "weddingplanning", "EngagementRings", "BuyItForLife"],
        "seeds": ["necklace", "earrings", "bracelet", "ring", "anklet", "jewelry organizer"],
        "forums": ["quora.com", "thestudentroom.co.uk", "purseforum.com"],
    },
    "daily": {
        "label": "日用品 / 家居",
        "subreddits": ["BuyItForLife", "HomeImprovement", "organization", "declutter",
                       "Frugal", "lifehacks", "amazon", "ProductPorn"],
        "seeds": ["storage box", "organizer", "water bottle", "cleaning brush",
                  "kitchen gadget", "laundry"],
        "forums": ["quora.com", "houzz.com", "thekitchn.com"],
    },
    "electronics": {
        "label": "电子产品",
        "subreddits": ["gadgets", "BuyItForLife", "techsupport", "UsefulCharts",
                       "EDC", "androidapps", "apple", "Android"],
        "seeds": ["phone holder", "charger", "cable", "power bank", "phone case",
                  "screen protector", "earbuds case"],
        "forums": ["quora.com", "tomsguide.com", "xda-developers.com"],
    },
    "consumer-electronics": {
        "label": "消费电子",
        "subreddits": ["gadgets", "headphones", "smarthome", "homeautomation",
                       "wearables", "BudgetAudiophile", "battlestations"],
        "seeds": ["bluetooth speaker", "earbuds", "smart plug", "webcam",
                  "keyboard", "monitor stand", "neck fan"],
        "forums": ["quora.com", "tomsguide.com", "head-fi.org", "rtings.com"],
    },
    "custom": {
        "label": "自定义",
        "subreddits": ["BuyItForLife", "amazon", "ProductPorn", "lifehacks", "gadgets"],
        "seeds": [],
        "forums": ["quora.com", "reddit.com"],
    },
}

# ---------------------------------------------------------------------------
# 痛点信号词库：把"抱怨 / 渴望 / 求推荐 / 找不到"等需求信号编码成查询模板
# {seed} 会被替换为具体产品词。
# ---------------------------------------------------------------------------
PAIN_PATTERNS = [
    # 抱怨型（已有产品不满意 → 改进机会）
    '{seed} problem',
    '{seed} annoying',
    '{seed} "i hate"',
    '{seed} keeps breaking',
    '{seed} "doesn\'t work"',
    '{seed} "fell apart"',
    '{seed} complaints',
    # 渴望型（明确想要某功能 → 蓝海卖点）
    '{seed} "i wish there was"',
    '{seed} "wish it had"',
    '{seed} "is there a" better',
    '{seed} "why is it so hard to find"',
    # 求推荐型（购买意图强 → 关键词价值高）
    '{seed} "any recommendations" reddit',
    '{seed} "looking for" reddit',
    '{seed} "what should i buy" reddit',
    'best {seed} reddit 2026',
    'best {seed} reddit 2025',
    # 替代/对比型
    '{seed} "alternative to"',
    '{seed} vs reddit',
]

# 通用趋势/热点型查询（不带 seed，用于发现品类新兴方向）
TREND_PATTERNS = [
    '{cat} trending products 2026 reddit',
    '{cat} "must have" amazon reddit',
    '{cat} viral tiktok 2026',
    '{cat} "where did you get" reddit',
]

# Reddit 公开 JSON 端点模板（无需鉴权，WebFetch 可直接取；best-effort，可能被限流）
REDDIT_JSON = "https://www.reddit.com/r/{sub}/search.json?q={q}&restrict_sr=1&sort=relevance&t=year&limit=25"


def normalize_seed(s):
    return re.sub(r"\s+", " ", s.strip()).strip()


def url_quote(s):
    # 轻量 url 编码，仅处理空格和引号，供 reddit.json 使用
    return s.replace(" ", "+").replace('"', "%22").replace("'", "%27")


def build_plan(category, seeds, max_seed_queries=8):
    preset = CATEGORY_PRESETS.get(category, CATEGORY_PRESETS["custom"])

    # 合并种子词：用户提供优先，否则用预设
    effective_seeds = [normalize_seed(s) for s in seeds if normalize_seed(s)]
    if not effective_seeds:
        effective_seeds = list(preset["seeds"])
    if not effective_seeds:
        effective_seeds = [preset["label"]]

    cat_label = preset["label"]

    plan = {
        "category": category,
        "category_label": cat_label,
        "market": "US",
        "effective_seeds": effective_seeds,
        "target_subreddits": preset["subreddits"],
        "target_forums": preset["forums"],
        "queries": {
            "websearch_reddit": [],     # site:reddit.com 定向
            "websearch_forums": [],     # quora / 论坛
            "websearch_social": [],     # youtube / tiktok / 通用
            "websearch_amazon": [],     # amazon 评论吐槽
            "websearch_trend": [],      # 品类趋势
            "reddit_json_fetch": [],    # WebFetch 直取 reddit 公开 json
        },
        "notes": (
            "Agent 用 WebSearch 执行 websearch_* 查询；用 WebFetch 直取 reddit_json_fetch。"
            "每条查询取前若干结果，提取含痛点信号的原句，记录 platform/url/quote/date。"
        ),
    }

    # 1) 每个 seed × 痛点模板 → reddit 定向
    for seed in effective_seeds[:max_seed_queries]:
        for pat in PAIN_PATTERNS:
            q = pat.format(seed=seed)
            plan["queries"]["websearch_reddit"].append(f"site:reddit.com {q}")
        # 论坛
        for forum in preset["forums"][:2]:
            plan["queries"]["websearch_forums"].append(
                f'site:{forum} {seed} ("i wish" OR "any recommendations" OR problem)'
            )
        # 社媒 / youtube / tiktok / 通用
        plan["queries"]["websearch_social"].append(
            f'{seed} ("worth it" OR "honest review" OR "don\'t buy") site:youtube.com'
        )
        plan["queries"]["websearch_social"].append(
            f'{seed} tiktok made me buy 2026'
        )
        # amazon 评论吐槽（1-3 星抱怨 → 痛点）
        plan["queries"]["websearch_amazon"].append(
            f'site:amazon.com {seed} review "disappointed" OR "wish" OR "stopped working"'
        )
        # reddit 公开 json 直取（取前 3 个相关 subreddit）
        for sub in preset["subreddits"][:3]:
            plan["queries"]["reddit_json_fetch"].append(
                REDDIT_JSON.format(sub=sub, q=url_quote(seed))
            )

    # 2) 品类趋势型
    for pat in TREND_PATTERNS:
        plan["queries"]["websearch_trend"].append(pat.format(cat=cat_label))
        plan["queries"]["websearch_trend"].append(pat.format(cat=category))

    # 去重
    for k, v in plan["queries"].items():
        seen, dedup = set(), []
        for q in v:
            if q not in seen:
                seen.add(q)
                dedup.append(q)
        plan["queries"][k] = dedup

    plan["total_queries"] = sum(len(v) for v in plan["queries"].values())
    return plan


def print_summary(plan):
    print("=" * 60)
    print(f"全网搜索查询计划  品类={plan['category_label']}  市场={plan['market']}")
    print("=" * 60)
    print(f"种子产品词: {', '.join(plan['effective_seeds'])}")
    print(f"目标 Subreddits: {', '.join(plan['target_subreddits'])}")
    print(f"查询总数: {plan['total_queries']}")
    print("-" * 60)
    for group, qs in plan["queries"].items():
        print(f"[{group}] ({len(qs)} 条)")
        for q in qs[:4]:
            print(f"   - {q}")
        if len(qs) > 4:
            print(f"   ... 另有 {len(qs) - 4} 条")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(description="生成社媒痛点全网搜索查询计划")
    ap.add_argument("--category", default="custom",
                    choices=list(CATEGORY_PRESETS.keys()),
                    help="品类预设")
    ap.add_argument("--seeds", default="", help="逗号分隔的种子产品词（英文，覆盖预设）")
    ap.add_argument("--out", default="query_plan.json", help="输出 JSON 路径")
    ap.add_argument("--max-seeds", type=int, default=8, help="最多展开多少个种子词")
    args = ap.parse_args()

    seeds = [s for s in args.seeds.split(",")] if args.seeds else []
    plan = build_plan(args.category, seeds, max_seed_queries=args.max_seeds)

    try:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[错误] 写入查询计划失败: {e}", file=sys.stderr)
        sys.exit(2)

    print_summary(plan)
    print(f"\n[完成] 查询计划已写入: {os.path.abspath(args.out)}")
    print("[提示] Agent 下一步：用 WebSearch 执行 websearch_* 查询、WebFetch 直取 reddit_json_fetch，")
    print("       提取痛点原句，按 findings 模板整理后交给 synthesize_candidates.py。")


if __name__ == "__main__":
    main()
