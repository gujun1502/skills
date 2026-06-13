# findings JSON 模板（Agent 搜索后填充）

> Agent 在全网搜索、提取痛点原句后，把结果整理成下面这个 JSON，保存为 `findings.json`，
> 再交给 `scripts/synthesize_candidates.py` 生成候选关键词。

```json
{
  "category": "electronics",
  "market": "US",
  "search_date": "2026-06-13",
  "pain_points": [
    {
      "id": "pain_1",
      "summary": "想要不打孔、磁吸够强、不挡出风口的车载手机支架（一句话中文概括）",
      "product_noun": "car phone mount",
      "desired_features": ["no drill", "strong magnet", "one hand"],
      "negative_signals": ["falls off", "blocks vent", "weak magnet"],
      "audiences": ["commuters", "delivery drivers"],
      "scenarios": ["car", "truck"],
      "mention_count": 7,
      "sources": [
        {"platform": "reddit", "url": "https://www.reddit.com/r/gadgets/...", "quote": "i wish there was a car mount that doesn't block the vent", "date": "2026-03"},
        {"platform": "amazon", "url": "https://www.amazon.com/...", "quote": "magnet too weak, phone falls off on bumps", "date": "2025-12"},
        {"platform": "youtube", "url": "https://www.youtube.com/watch?v=...", "quote": "the no-drill mounts are way better now", "date": "2026-01"}
      ]
    }
  ]
}
```

## 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `category` | 是 | 与查询计划一致（jewelry/daily/electronics/consumer-electronics/custom） |
| `market` | 是 | 默认 `US`（北美） |
| `pain_points[].product_noun` | 是 | 核心品类英文名词；候选词生成的 base |
| `pain_points[].desired_features` | 建议 | 想要的功能/卖点（英文，亚马逊搜索风格的修饰词） |
| `pain_points[].negative_signals` | 建议 | 被吐槽的缺点（用于差异化卖点，不直接进关键词） |
| `pain_points[].audiences` / `scenarios` | 建议 | 用于生成 `for car` / `women` 等长尾词 |
| `pain_points[].mention_count` | 建议 | 去重后被多少独立来源提及；缺省则按 sources 数量计 |
| `pain_points[].sources[]` | 是 | 每条含 `platform`/`url`/`quote`/`date`，date 含年份以参与新鲜度打分 |

## 质量要求

- **不编造**：每个 quote 必须来自真实抓到的网页；找不到来源的痛点不要写。
- **去重**：同一句被多平台转载只算一次，但跨平台独立提及计入 `mention_count`。
- **英文 product_noun / features**：因为下游要对接 Amazon ABA（英文搜索词）。
- 痛点数量建议 8-20 个；少于 3 个时脚本会告警，说明搜索覆盖不足。
