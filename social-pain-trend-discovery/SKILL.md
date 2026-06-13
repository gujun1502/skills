---
name: social-pain-trend-discovery
description: 用公开网页搜索（WebSearch + WebFetch）在 Reddit、Quora、论坛、YouTube/TikTok、Amazon 评论上挖掘北美消费者的痛点、抱怨、渴望与新兴热点，归纳成结构化痛点，再合成一批可直接验证的候选 Amazon 搜索关键词，交给 aba-keyword-niche-analysis Skill 做选品评分。当用户提到痛点挖掘、需求发现、社媒选品、Reddit 选品、热点/趋势找品、还不知道做什么品类想找方向、candidate keyword discovery、痛点找词时触发。面向销往北美的跨境电商独立站经营者（珠宝/日用品/电子/消费电子）。仅使用公开网页搜索，不依赖任何需鉴权 API。
---

# 社媒痛点 / 热词发现 (social-pain-trend-discovery)

## 这个 Skill 做什么

在还没有 ABA 数据、甚至还没定品类的阶段，从**真实用户的声音**里找选品方向：

公开网页搜索 → 抓痛点/抱怨/渴望/热点原句 → 归纳成结构化痛点 → 合成候选关键词 → 交接给 `aba-keyword-niche-analysis` 做量化选品

它是 `aba-keyword-niche-analysis` 的**上游**：那个 Skill 负责"验证一个词值不值得做"，本 Skill 负责"该去验证哪些词"。

```
[本 Skill] 社媒痛点发现 → 候选关键词
                ↓ 交接
[aba-keyword-niche-analysis] 拉 ABA + MCP 验证 → 五维评分 → 选品报告
```

## 适用场景（触发条件）

- 提到 "痛点挖掘 / 需求发现 / 社媒选品 / Reddit 选品 / 热点找品 / 趋势找品"
- "还不知道做什么品类 / 想找新方向 / 帮我找有潜力的词"
- 提到 candidate keyword discovery / 痛点找词
- 有了某个品类/种子产品词，想知道用户在抱怨什么、想要什么

## 前置条件

1. **WebSearch / WebFetch 工具**：执行搜索的核心。调用前先用 `ToolSearch` 加载它们的 schema（它们是延迟加载工具）。
2. **本地 Python 3**：两个确定性脚本需要（仅用标准库，无需 pip 安装）。
3. **明确品类或种子词**：若用户没给，先问"主营哪个品类（珠宝/日用品/电子/消费电子）或有没有具体产品词"。市场默认北美 US。

---

## 执行流程（五个 Phase）

### Phase 0 —— 确定品类与种子词

确认 `category`（jewelry / daily / electronics / consumer-electronics / custom）和可选 `seeds`（英文产品词，逗号分隔）。市场固定 `US`。

### Phase 1 —— 生成查询计划（确定性脚本）

```bash
python scripts/build_query_plan.py --category electronics --seeds "phone holder,earbuds case" --out query_plan.json
```

脚本输出 `query_plan.json`，把种子词 × 痛点信号词库展开成针对各来源的查询：
- `websearch_reddit`：`site:reddit.com` 定向痛点查询
- `websearch_forums`：Quora / 垂直论坛
- `websearch_social`：YouTube 测评 / TikTok 热点
- `websearch_amazon`：Amazon 1-3 星差评吐槽
- `websearch_trend`：品类层面新兴趋势
- `reddit_json_fetch`：Reddit 公开 JSON 端点（WebFetch 直取，best-effort）

### Phase 2 —— 执行全网搜索（Agent 用 WebSearch / WebFetch）

参见 `references/source-playbook.md`。**先 `ToolSearch` 加载 WebSearch/WebFetch。**

- 用 `WebSearch` 跑 `websearch_*` 查询；用 `WebFetch` 直取 `reddit_json_fetch`（限流就退回 site: 搜索，不超过 1 次重试）。
- **节流**：先跑高价值组（reddit + amazon 差评 + trend），每条查询取前 5-8 条结果；每个种子词约 8-12 次 WebSearch + 2-3 次 WebFetch 足够。
- 对每条结果，按痛点信号词库（抱怨型/渴望型/求推荐型/替代型/热点型）保留**原句**，记录 `platform / url / quote / date`。
- 丢弃噪声：品牌粉丝吹捧、二手转售、纯技术报错、与购买无关的闲聊。

### Phase 3 —— 归纳结构化痛点（写 findings.json）

参见 `references/findings-schema.md`。把反复出现的诉求归纳成 pain point，抽取：
`product_noun`（英文核心品类词）、`desired_features`、`negative_signals`、`audiences`、`scenarios`、`mention_count`、`sources[]`。

**真信号判据**：一个痛点至少被 2 个独立来源、最好跨 2 个平台提及。把结果存成 `findings.json`。

### Phase 4 —— 合成候选关键词（确定性脚本）

```bash
python scripts/synthesize_candidates.py findings.json --out candidate_keywords.json --top 40
```

脚本会：去重 → 信号打分（volume × 平台多样性 × 新鲜度，0-10）→ 用模板把痛点组合成候选 Amazon 搜索词（`{modifier} {base}`、`{base} for {scenario}`、`{base} {audience}` 等）→ 排序输出 `candidate_keywords.json` + 控制台 Top 痛点 / Top 候选词。

### Phase 5 —— 输出报告并交接

向用户给出中文小结：
1. **Top 痛点**（用户最痛/最想要什么）+ 代表性引语和来源平台。
2. **Top 候选关键词**（大词 vs 长尾），标信号分。
3. **新兴热点/趋势**信号（若 trend 查询有发现）。
4. **差异化卖点提示**：把 `negative_signals` 翻译成"你的产品应该解决的痛点"。
5. **交接说明**：建议把高分候选词带到 Amazon 后台拉 ABA 周报，或用卖家精灵 `keyword_research` MCP 直接验证，然后调用 **`aba-keyword-niche-analysis`** Skill 做五维评分选品。

如果两个 Skill 连用，可在本 Skill 结束后直接接力调用 `aba-keyword-niche-analysis`。

---

## 错误处理

- **WebSearch 无结果 / 被限流**：换用更宽松的查询（去掉过多引号约束），或减少 `site:` 限定；记录"该角度无信号"而非编造。
- **Reddit JSON 取不到（403/非 JSON）**：最多重试 1 次，随后改用 `site:reddit.com` 的 WebSearch 兜底。
- **痛点不足（< 3）**：`synthesize_candidates.py` 会告警。提示用户扩大种子词、换相邻品类或合并多轮搜索结果。
- **候选词过于宽泛**：偏向保留长尾词（≥3 词），它们竞争更低、更适合独立站；在小结里标注大词仅供方向参考。
- **不编造**：每条 quote 必须来自真实抓到的网页；无来源的痛点不写入 findings。
- **脚本只用标准库**：无需联网安装依赖；若 `python` 不在 PATH，提示用户用 `py` 或完整路径。

---

## 文件结构

```
social-pain-trend-discovery/
├── SKILL.md
├── scripts/
│   ├── build_query_plan.py        # Phase 1：品类/种子 → 全网查询计划
│   └── synthesize_candidates.py   # Phase 4：痛点 findings → 候选关键词
└── references/
    ├── source-playbook.md         # 来源、信号词库、节流、衔接
    └── findings-schema.md         # findings.json 模板与字段说明
```
