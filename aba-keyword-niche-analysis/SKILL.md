---
name: aba-keyword-niche-analysis
description: 分析 Amazon Brand Analytics (ABA) Top Search Terms CSV，从热搜词中挖掘亚马逊细分市场/利基机会，结合卖家精灵 MCP 与 Google Trends 验证数据，按五维评分体系打分，输出一份含细分市场总览、关键词明细、ASIN 排行、进入策略四个 Sheet 的 Excel 选品分析报告。当用户提到 ABA 分析、ABA 热搜词、Top Search Terms、关键词选品、细分市场分析、keyword niche mining、利基挖掘、选品报告时触发。面向销往北美市场的跨境电商独立站经营者（珠宝 / 日用品 / 电子及消费电子等品类）。
---

# ABA 关键词细分市场挖掘 (aba-keyword-niche-analysis)

## 这个 Skill 做什么

把一份 **Amazon Brand Analytics 的 Top Search Terms 周报 CSV** 变成一份**可执行的选品决策报告**：

ABA CSV → 解析与指标计算 → 语义聚类成"细分市场" → MCP/Trends 数据验证 → 五维评分 → Excel 报告

最终回答经营者一个问题：**在北美市场，哪些细分品类/关键词具有"大卖"的潜力，且我现在值得进入。**

## 适用场景（触发条件）

当用户出现以下任一意图时使用本 Skill：
- 提到 "ABA 分析 / ABA 热搜词 / Top Search Terms / Brand Analytics"
- 提到 "关键词选品 / 细分市场分析 / 利基挖掘 / keyword niche mining / 选品报告"
- 提供了一份 ABA Top Search Terms 导出 CSV，希望从中找有潜力的商品方向
- 想用"热词 + 趋势"判断某品类（珠宝/日用品/电子/消费电子）在北美能否大卖

## 前置条件（开始前检查）

1. **ABA CSV**：用户提供 Amazon Brand Analytics → Top Search Terms 导出的 CSV 文件路径。
   - 若用户没提供，**先索要文件**，并说明在卖家后台 `品牌分析 → 亚马逊搜索词` 导出周报。
2. **卖家精灵 MCP**：Phase 3 需要。若未启用，仍可完成 Phase 1/2/4/5，但需在报告中标注"市场数据未经 MCP 验证，仅基于 ABA 站内信号"。
3. **本地 Python 3**：Phase 1 解析脚本需要。Phase 5 生成 Excel 需要 `openpyxl`（缺失时用 `pip install openpyxl` 安装，或降级输出 CSV/Markdown）。

---

## 执行流程（五个 Phase）

### Phase 1 —— 解析 ABA CSV（确定性脚本）

运行解析脚本，得到结构化 JSON + 控制台摘要：

```bash
python scripts/parse_aba_csv.py "<用户的ABA文件.csv>" --out aba_parsed.json --top 30
```

脚本会输出：总关键词数、品牌词/非品牌词数、平均点击份额、平均转化率、高频修饰词、Top 品牌、Top ASIN、Top 非品牌搜索词，并写出 `aba_parsed.json`（含每条词的 Top1/Top3 点击份额、Top3 转化率、品牌标记、类目等）。

**读取 `aba_parsed.json` 进入下一步**，重点关注 `non_brand_keywords` 和 `modifier_words`——它们是利基机会的原料（品牌词通常是大牌护城河，独立站难抢）。

### Phase 2 —— AI 语义聚类（找出"细分市场"）

基于 `non_brand_keywords` 与 `modifier_words` 做语义聚类，把零散关键词归并成有商业意义的 **细分市场（niche）**：

- 按 **共同基础品类词 + 修饰词** 聚类。例如：`magnetic phone holder car`、`phone holder for car dashboard`、`vent phone mount` → 归为「车载磁吸手机支架」。
- 每个 niche 给出：`niche名称`、`代表关键词(3-5个)`、`覆盖搜索词数`、`核心修饰词(场景/人群/材质/功能)`、`推测目标人群`、`推测痛点`。
- 用修饰词区分需求类型：场景词（car/office/travel）、人群词（women/men/kids）、材质词（stainless/silicone）、功能词（waterproof/magnetic）、痛点词（anti-slip/no-drill）。
- 优先标记**新兴/上升修饰词**与**长尾低竞争**词簇——这是独立站最可能突破的位置。

产出 8-15 个候选 niche（数量视数据量调整），并为每个 niche 选 3-5 个**代表词**进入 Phase 3 验证。

### Phase 3 —— 卖家精灵 MCP / Trends 数据验证

参见 `references/mcp-tools-reference.md`。**调用前先用 `ToolSearch` 加载工具真实 schema。**

对每个 niche 的代表词与 Top ASIN 做验证（节流：每 niche 3-5 词 + Top 3 ASIN）：
- `keyword_research`：月搜索量、月购买量、购买率、供需比、PPC 竞价、点击集中度、平均售价、商品数、搜索增长率。
- `keyword_miner`：SPR、标题密度、广告竞品数、供需比（进入难度）。
- `asin_detail`：售价、评分、评论数、BSR、类目路径、上架时间（找新品机会）。
- `aba_research_weekly`：周度排名趋势，校正成长性。
- `traffic_keyword`：竞品 ASIN 反查流量词，补充长尾。
- `google_trend`：跨平台验证需求真实性与季节性。

把每个 niche 的验证数据回填，缺失字段记 `null`（不编造）。

### Phase 4 —— 五维评分

对每个 niche（取代表词的加权/中位指标）按以下体系打分（1-10）：

**① 市场规模（权重 25%）**
| 条件 | 分 |
|---|---|
| 月搜索量 > 50000 且 ABA 排名 < 10000 | 9-10 |
| 月搜索量 20000-50000 | 7-8 |
| 月搜索量 5000-20000 | 5-6 |
| 月搜索量 1000-5000 | 3-4 |
| 月搜索量 < 1000 | 1-2 |

**② 转化潜力（权重 20%）**
| 条件 | 分 |
|---|---|
| 购买率 > 5% 且 ABA 转化率 > 70% | 9-10 |
| 购买率 3%-5%，ABA 转化率 50%-70% | 7-8 |
| 购买率 1.5%-3%，ABA 转化率 30%-50% | 5-6 |
| 购买率 0.5%-1.5% | 3-4 |
| 购买率 < 0.5% | 1-2 |

**③ 竞争难度（权重 25%，分数越高=越难）**
| 条件 | 分 |
|---|---|
| 点击集中度 < 30%，SPR < 10，供需比 > 3 | 1-2 |
| 点击集中度 30%-45%，供需比 1.5-3 | 3-4 |
| 点击集中度 45%-60%，供需比 0.8-1.5 | 5-6 |
| 点击集中度 60%-80% | 7-8 |
| 点击集中度 > 80% | 9-10 |

**④ 成长性（权重 15%）**
| 条件 | 分 |
|---|---|
| 搜索增长率 > 30% | 9-10 |
| 10%-30% | 7-8 |
| 0%-10% | 5-6 |
| -10%-0% | 3-4 |
| < -10% | 1-2 |

**⑤ 利润空间（权重 15%）**
| 条件 | 分 |
|---|---|
| 售价 > $25 且 PPC 竞价 < $1.5 | 9-10 |
| 售价 $15-25，PPC < $2 | 7-8 |
| 售价 $10-15 | 5-6 |
| 售价 $5-10 且 PPC 较高 | 3-4 |
| 售价 < $5 | 1-2 |

**综合分公式（注意竞争难度反向）：**
```
综合分 = 市场规模×0.25 + 转化潜力×0.20 + (10 - 竞争难度)×0.25 + 成长性×0.15 + 利润空间×0.15
```

**推荐等级：**
- 综合分 ≥ 7.5 → **S 级，强烈推荐**
- 6.0-7.4 → **A 级，值得进入**
- 4.5-5.9 → **B 级，谨慎考虑**
- < 4.5 → **C 级，不推荐**

> 若某维度数据缺失（MCP 未启用或调用失败），该维度取保守中位分 5，并在报告备注列标注"数据缺失，估算分"。

### Phase 5 —— 生成 Excel 报告

用 `openpyxl` 生成 `.xlsx`（文件名建议 `ABA选品分析_<日期或周次>.xlsx`），含四个 Sheet：

1. **细分市场总览**：niche 名称、代表词、综合分、推荐等级、五维分、月搜索量、平均售价、一句话结论。按综合分降序，S/A 级高亮。
2. **关键词明细**：每个关键词的 ABA 排名、Top1/Top3 点击份额、Top3 转化率、所属 niche、品牌/非品牌、MCP 月搜索量/购买率/供需比/PPC/增长率。
3. **ASIN 排行**：Top ASIN、出现频次、标题、品牌、售价、评分、评论数、BSR、上架时间、所属 niche。
4. **进入策略建议**：对 S/A 级 niche，给出差异化卖点（基于痛点修饰词）、定价区间、首批选品方向、PPC 预算提示、风险点。

报告头部写明：数据来源（ABA 周次）、市场（北美 US）、生成日期、是否经 MCP 验证。

最后向用户用中文口头总结：Top 3 推荐 niche + 理由，并给出报告文件路径。

---

## 错误处理

- **CSV 格式异常 / 找不到 Search Term 列**：脚本以退出码 3 报错并打印检测到的表头。此时向用户确认文件是否为 ABA Top Search Terms 导出，必要时让用户贴前几行内容，再考虑手动指定列。
- **编码异常**：脚本已尝试 utf-8-sig/utf-8/latin-1/gbk。仍失败则请用户用 Excel 另存为"CSV UTF-8"。
- **关键词数量不足（< 20）**：脚本打印警告。提示用户结论可信度有限，建议合并多周 ABA 数据或扩大导出范围；聚类时减少 niche 数量。
- **MCP 调用失败 / 未启用**：单次失败重试 1 次仍失败则跳过该字段记 `null`，对应维度取中位分 5 并标注；整体降级为"基于 ABA 站内信号 + 可用数据"的报告，并在头部明确标注未完成市场验证。
- **openpyxl 缺失**：先尝试 `pip install openpyxl`；若环境不允许安装，降级输出 Markdown 表格 + CSV，并告知用户。
- **不编造数据**：任何 MCP/Trends 未返回的数值一律为空，绝不臆造月搜索量、售价、增长率等关键指标。

---

## 文件结构

```
aba-keyword-niche-analysis/
├── SKILL.md                          # 本文件：流程与评分规则
├── scripts/
│   └── parse_aba_csv.py              # Phase 1 确定性解析脚本
└── references/
    └── mcp-tools-reference.md        # 卖家精灵 MCP 工具语义参考
```
