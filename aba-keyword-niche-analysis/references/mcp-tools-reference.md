# 卖家精灵 (SellerSprite) MCP 工具参考

> 本文件供 `aba-keyword-niche-analysis` Skill 的 Phase 3（数据验证）使用。
> Agent 在调用前应先用 `ToolSearch` 加载对应 MCP 工具的真实 schema，再按实际参数名调用。
> 下表为**语义参考**：字段名以实际 MCP 返回为准；若某字段缺失，按"数据不可用"处理而非编造。

---

## 工具总览

| 工具 | 用途 | 何时调用 |
|------|------|----------|
| `keyword_research` | 关键词市场评估 | 验证每个候选细分词的市场规模、转化、利润 |
| `keyword_miner` | 关键词竞争分析 | 评估进入难度（SPR / 标题密度 / 广告竞品） |
| `asin_detail` | ASIN 商品详情 | 拉取 Top ASIN 的售价 / 评分 / BSR / 上架时间 |
| `aba_research_weekly` | ABA 周度趋势 | 验证关键词的周度搜索排名走势 |
| `traffic_keyword` | ASIN 流量词分析 | 反查竞品 ASIN 的来源关键词、拓词 |
| `google_trend` | Google 趋势验证 | 跨平台验证需求的真实性与季节性 |

---

## 1. keyword_research —— 关键词市场评估

**用途**：对单个关键词做市场体量与商业价值评估。

**输入（语义）**：`keyword`（关键词，英文）、`market`/`marketplace`（默认 `US` 北美站）。

**返回字段（语义）**：
- `monthly_search_volume` 月搜索量 → 评分维度【市场规模】
- `monthly_purchase_volume` 月购买量
- `purchase_rate` 购买率（购买量 / 搜索量） → 评分维度【转化潜力】
- `supply_demand_ratio` 供需比（商品数 / 搜索量，越高越蓝海） → 评分维度【竞争难度】
- `ppc_bid` / `ppc_cpc` PPC 竞价 → 评分维度【利润空间】
- `click_concentration` 点击集中度（Top3 点击份额） → 评分维度【竞争难度】
- `avg_price` 平均售价 → 评分维度【利润空间】
- `product_count` 在售商品数
- `search_growth` / `search_trend` 搜索增长率（同比/环比） → 评分维度【成长性】

**调用建议**：对 Phase 2 聚类后的"代表词"逐个调用；控制频率，失败重试 1 次后跳过并标注 `data_unavailable`。

---

## 2. keyword_miner —— 关键词竞争分析

**用途**：评估关键词的进入难度与竞争格局，配合 keyword_research 形成"市场 × 竞争"二维判断。

**返回字段（语义）**：
- `spr`（SellerSprite PPC Rank / 上首页所需销量估算）越低越易进入 → 评分维度【竞争难度】
- `title_density` 标题密度（标题精确含该词的竞品占比）越高越红海
- `ad_competitor_count` 广告竞品数
- `supply_demand_ratio` 供需比
- 关联拓展词列表（可用于丰富某个 niche 的词簇）

---

## 3. asin_detail —— ASIN 商品详情

**用途**：拉取竞品/Top ASIN 的核心商品数据，用于 ASIN 排行 Sheet 与利润空间估算。

**输入**：`asin`、`market`（默认 `US`）。

**返回字段（语义）**：
- `price` 售价
- `rating` 评分、`reviews_count` 评论数
- `bsr` Best Seller Rank（含类目）
- `category_path` 类目路径
- `listing_date` / `first_available` 上架时间（判断新品机会）
- `brand` 品牌、`title` 标题、`main_image` 主图 URL

---

## 4. aba_research_weekly —— ABA 周度趋势

**用途**：验证关键词的 ABA 搜索排名周度走势，识别上升/下降/季节性。

**输入**：`keyword`、可选周范围。

**返回字段（语义）**：周度 `search_frequency_rank` 序列、环比变化 → 用于校正【成长性】评分。

---

## 5. traffic_keyword —— ASIN 流量词分析

**用途**：对一个竞品 ASIN 反查其自然/广告流量来源关键词，用于发现 ABA 未直接暴露的长尾词、丰富 niche 词簇。

**输入**：`asin`、`market`。

**返回字段（语义）**：流量词列表，每词含搜索量、排名、流量占比、自然/广告标记。

---

## 6. google_trend —— Google 趋势验证

**用途**：跨平台验证需求真实性与季节性（避免只看 Amazon 站内数据导致的幸存者偏差）。

**输入**：`keyword`、`geo`（默认 `US`）、时间范围。

**返回字段（语义）**：相对热度时间序列、季节性峰谷、相关上升查询（rising queries）。

---

## 调用纪律（重要）

1. **先 ToolSearch 后调用**：MCP 工具 schema 是延迟加载的，调用前用 `ToolSearch` 拿到真实参数名。
2. **节流**：聚类后每个 niche 只验证 3-5 个代表词 + Top 3 ASIN，避免海量调用。
3. **容错**：单次调用失败重试 1 次；仍失败则该字段记 `null` 并在报告中标注"数据缺失"，对应评分维度取保守中位分（5 分）并注明。
4. **不编造**：MCP 未返回的数值一律为 `null`，绝不臆造月搜索量 / 售价等关键数字。
5. **市场固定北美**：所有调用 `market`/`geo` 默认 `US`，与独立站目标市场一致。
