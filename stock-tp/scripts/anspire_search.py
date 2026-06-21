#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anspire_search.py —— 信息面/消息面/新闻面 检索（Anspire AI Search）

官方接口（已核对）：
  GET https://plugin.anspire.cn/api/ntsearch/search?query=...&top_k=10
  Header: Authorization: Bearer <ANSPIRE_API_KEY>, Accept: application/json
  Resp:   {"results":[{"title","url","content","score","date"}, ...]}

本脚本面向"个股研究"封装多组查询模板：
  - 公司新闻 / 业绩 / 公告
  - 行业政策 / 监管 / 领导人讲话
  - 舆情 / 利好利空 / 催化事件
并对结果做时间排序、去重、可信度粗排，输出结构化条目供 Claude 拆解"预言"。

无 Key 或失败时：status=error，可由 analyze.py 降级到 WebSearch 兜底（由 Claude 执行）。

用法：
  python anspire_search.py --name 贵州茅台 --code 600519 --market A
  python anspire_search.py --query "英伟达 AI 芯片 出口管制" --top_k 8
"""
from __future__ import annotations

import argparse
import urllib.parse
import urllib.request
import json
import common as C

SEARCH_URL = "https://plugin.anspire.cn/api/ntsearch/search"


def _one_search(query: str, top_k: int, key: str, timeout: int = 25) -> list[dict]:
    qs = urllib.parse.urlencode({"query": query, "top_k": str(top_k)})
    req = urllib.request.Request(
        f"{SEARCH_URL}?{qs}",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8", "ignore"))
    results = payload.get("results") or payload.get("data") or []
    out = []
    for it in results:
        out.append({
            "title": it.get("title", ""),
            "url": it.get("url", ""),
            "content": (it.get("content", "") or "")[:1200],
            "score": C.safe_float(it.get("score")),
            "date": it.get("date", ""),
            "query": query,
        })
    return out


def _dedup(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for it in sorted(items, key=lambda x: (x.get("date") or "", x.get("score") or 0), reverse=True):
        key = (it.get("url") or it.get("title", ""))[:120]
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def build_queries(name: str, code: str, market: str) -> dict[str, list[str]]:
    """按四块需求生成查询模板。"""
    n = name or code
    region = {"A": "A股", "HK": "港股", "US": "美股", "JP": "日股", "KR": "韩股"}.get(market, "")
    return {
        "公司新闻业绩": [f"{n} 最新消息", f"{n} 业绩 财报 营收 净利润", f"{n} {code} 公告"],
        "政策监管讲话": [f"{n} 所在行业 政策 监管", f"{region} {n} 行业 国家政策 领导人讲话",
                     f"{n} 行业 补贴 出口 关税 限制"],
        "舆情催化事件": [f"{n} 利好 利空", f"{n} 催化剂 事件 订单 中标 合作",
                     f"{n} 研报 目标价 评级 机构观点"],
    }


def fetch(name: str, code: str, market: str, top_k: int = 6) -> dict:
    keys = C.anspire_keys()
    meta_q = build_queries(name, code, market)
    if not keys:
        return {"status": "error", "note": "未配置 ANSPIRE_API_KEYS，建议由 Claude 用 WebSearch 兜底",
                "queries": meta_q, "groups": {}}

    ck = f"{code}:{market}:{top_k}"
    cached = C.cache_get("news", ck, ttl_hours=4.0)
    if cached:
        return cached

    key = keys[0]
    groups: dict[str, list[dict]] = {}
    errors = []
    for group, queries in meta_q.items():
        items: list[dict] = []
        for q in queries:
            try:
                items.extend(_one_search(q, top_k, key))
            except Exception as e:
                errors.append(f"{q}: {type(e).__name__}")
        groups[group] = _dedup(items)[:max(8, top_k)]

    total = sum(len(v) for v in groups.values())
    result = {
        "status": "ok" if total else "empty",
        "note": "; ".join(errors[:3]) if errors else "",
        "total": total,
        "groups": groups,
        "queries": meta_q,
    }
    if total:
        C.cache_set("news", ck, result)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="")
    ap.add_argument("--code", default="")
    ap.add_argument("--market", default="A")
    ap.add_argument("--query", default="")
    ap.add_argument("--top_k", type=int, default=6)
    a = ap.parse_args()
    if a.query:
        keys = C.anspire_keys()
        if not keys:
            C.print_json({"status": "error", "note": "no ANSPIRE_API_KEYS"})
            return
        try:
            C.print_json({"status": "ok", "items": _dedup(_one_search(a.query, a.top_k, keys[0]))})
        except Exception as e:
            C.print_json({"status": "error", "note": str(e)})
    else:
        C.print_json(fetch(a.name, a.code, a.market, a.top_k))


if __name__ == "__main__":
    main()
