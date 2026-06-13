# 全网痛点 / 热词搜索 Playbook（仅公开网页搜索）

> 供 `social-pain-trend-discovery` Skill 的搜索执行阶段使用。
> 所有来源均为公开网页，通过 Agent 的 `WebSearch`（google 风格查询）与 `WebFetch`（直取 URL）访问。
> **调用前先用 `ToolSearch` 加载 `WebSearch` / `WebFetch` 的 schema。** 不使用任何需要鉴权的 API。

---

## 一、来源与访问方式

| 来源 | 怎么访问 | 价值 |
|------|----------|------|
| Reddit（定向搜索） | `WebSearch`: `site:reddit.com <痛点查询>` | 真实用户抱怨/求推荐，购买意图强 |
| Reddit（公开 JSON） | `WebFetch`: `https://www.reddit.com/r/<sub>/search.json?q=<词>&restrict_sr=1&t=year` | 结构化帖子标题+内容，best-effort（可能限流，失败就退回 site: 搜索） |
| Quora / 论坛 | `WebSearch`: `site:quora.com` / `site:tomsguide.com` 等 | 长问答暴露深层痛点与功能诉求 |
| YouTube / TikTok | `WebSearch`: `<词> honest review site:youtube.com` / `<词> tiktok made me buy 2026` | 热点/带货趋势，新兴卖点 |
| Amazon 评论 | `WebSearch`: `site:amazon.com <词> review "disappointed" OR "wish"` | 1-3 星差评 = 最直接的改进机会 |
| 通用网页/Google Trends 页 | `WebSearch`: `<品类> trending products 2026` | 品类层面的新兴方向 |

> Reddit JSON 端点限流或返回非 JSON 时，**不要重试超过 1 次**，直接改用 `site:reddit.com` 的 WebSearch 兜底。

---

## 二、痛点信号词库（识别"需求"而非噪声）

抓取每条结果时，优先保留含以下信号的**原句**（连同 url 和日期）：

- **抱怨型**（已有产品不满意）：`problem`, `annoying`, `i hate`, `keeps breaking`, `doesn't work`, `fell apart`, `cheap quality`, `stopped working`, `disappointed`
- **渴望型**（明确想要某功能）：`i wish there was`, `wish it had`, `is there a … that`, `why is it so hard to find`, `does anyone make`
- **求推荐型**（购买意图）：`any recommendations`, `looking for`, `what should i buy`, `best … for`, `which … is worth it`
- **替代/对比型**：`alternative to`, `… vs …`, `better than`
- **热点/从众型**：`tiktok made me buy`, `viral`, `where did you get`, `must have`

**噪声过滤**：纯品牌粉丝吹捧、转售/二手、纯技术报错、与购买无关的闲聊 → 丢弃。

---

## 三、从原句 → 结构化痛点

对每个反复出现的诉求，归纳成一个 **pain point**，抽取：
- `product_noun`：核心品类名词（英文，亚马逊搜索习惯，如 `car phone mount`）
- `desired_features`：被反复提到的"想要的功能/卖点"（`no drill`, `waterproof`, `strong magnet`）
- `negative_signals`：被反复吐槽的缺点（`falls off`, `blocks vent`, `too bulky`）
- `audiences` / `scenarios`：人群（`women`, `commuters`）、场景（`car`, `office`, `travel`）
- `mention_count`：被多少条独立来源提及（去重后）
- `sources`：每条 `{platform, url, quote, date}`

> 经验法则：**一个痛点至少被 2 个独立来源、且最好跨 2 个平台提及**，才算"真信号"，否则标低权重。

---

## 四、节流与配额

- 不要把查询计划里的全部查询都跑完——**先跑高价值组**（reddit + amazon 差评 + 趋势），每组取前 5-8 条结果即可。
- 每个种子词大约 8-12 次 WebSearch + 2-3 次 WebFetch 足够形成判断。
- 时间优先近 12 个月（`t=year` / 查询里带 `2025`/`2026`），保证趋势新鲜度。

---

## 五、与下游 Skill 的衔接

本 Skill 产出 `candidate_keywords.json` → 交给 `aba-keyword-niche-analysis`：
1. 把高分候选词带到 Amazon 卖家后台拉 ABA Top Search Terms 周报；**或**
2. 直接用卖家精灵 `keyword_research` MCP 对候选词做量化验证。

两条路最终都进入 `aba-keyword-niche-analysis` 的五维评分，形成选品报告。
