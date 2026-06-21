---
name: stock-tp
description: A股/美股(含港股、日股、韩股、ETF)个股研究与买卖决策。从四个维度——①信息/消息/新闻面(政策、领导人讲话、公告、舆情，拆解其中的"预言")②情绪面(市场情绪温度作决策因子)③财报/行业趋势/盈利点(估值、成长、邻近标的比选、未来事件影响)④综合分析与预测——聚合多市场数据(行情、K线、技术指标、资金流、筹码、龙虎榜、基本面、新闻)，用可视化、可追溯、可调权重的五因子模型给出买入/卖出/持有结论、评分、买卖点位、风险警报、催化剂日历与操作清单。当用户要分析某只股票、问"该买/卖/持有吗"、做个股研究/盘前盘后复盘/选股比选/舆情消息面解读/估值与财报分析、或提到股票代码(如600519、AAPL、hk00700、7203.T)寻求投资决策时使用。
---

# stock-tp：A股 / 美股个股研究与决策

把一只股票的研究拆成四块，聚合数据后给出**可追溯**的买卖结论。Claude 负责消息面
拆解与最终综合（你就是大模型）；Python 脚本负责取数与确定性打分。

> ⚠️ 输出始终声明"研究分析、非投资建议"。不编造数据：取数失败就如实标注并降级。

## 0. 准备（首次或报错时）

```bash
cd <skill目录>
pip install -r requirements.txt          # akshare / yfinance / pandas
cp config.example.env config.env         # 填 ANSPIRE_API_KEYS（新闻必需）；STOCK_LIST 可选
```
- 新闻/舆情走 **Anspire AI Search**（`ANSPIRE_API_KEYS`）。无 Key 时消息面降级为 Claude 用 `WebSearch`/`WebFetch` 兜底。
- 交互式分析**无需**配置 LLM 端点；`anspire_llm.py` 仅供无人值守 loop。
- 所有脚本在 `scripts/` 下运行（`cd scripts` 或 `python scripts/xxx.py`），输出 UTF-8 JSON。

## 1. 标准分析流程（单只股票）

**第一步——一键聚合**（行情+指标+基本面+资金流+情绪+新闻 → 含可追溯权重的决策包）：
```bash
cd scripts && python analyze.py <代码> --save
# 例：python analyze.py 600519 --save  /  python analyze.py AAPL --save
```
读取它打印的 JSON（也存到 `reports/<代码>_<日期>_data.json`）。它已算好：
`factor_scores`（技术/资金/基本面/情绪 四个子分）、`technical_levels`（买卖点/止损）、
`weights`、`decision_preliminary`（消息面用占位 50）。

**第二步——消息面拆解（你来做）**：按 `references/prompts.md` 的"拆解预言四步法"，
对决策包里 `news.groups` 的每条做：信源核验 → 提取可证伪的"预言"(方向/传导链/弹性/
确定性/兑现时点) → 政策与领导人讲话专项 → 合成**消息面分数 0–100**。
> 若 `news.status != ok`（无 Key/失败），改用 `WebSearch` 搜「公司名+消息/政策/业绩/研报」，同法拆解。

**第三步——回填重算**：
```bash
python analyze.py <代码> --news-score <你给的分> --save
```
得到 `decision_final`（含完整 `breakdown`：因子×权重=贡献）。

**第四步——综合与预测（你来做）**：按 `prompts.md` 的 C 步 + `decision-framework.md`，
检查**风险否决**（命中则下调结论并红字警报），做三情景预测、催化剂日历、操作清单。

**第五步——出报告**：套 `templates/report-template.md`，产出中文 Markdown 决策报告。
如用户要存档：写到 `reports/<代码>_<日期>.md`。

**导出 PDF**（用户要 PDF 时）：`python scripts/md_to_pdf.py reports/<代码>_<日期>.md`。
Windows 友好（markdown→HTML→系统 Edge/Chrome headless 打印，内嵌微软雅黑/宋体，A4），
不依赖 weasyprint/GTK。注意输出路径用绝对路径（脚本已自动 resolve）。

## 2. 单脚本（按需取某一块）

| 块 | 命令 | 产出 |
|----|------|------|
| 行情/K线/指标 | `python fetch_market.py <代码> --days 250` | 报价、20根K线、MA/MACD/RSI/KDJ/BOLL/ATR/量比 |
| 基本面/财报/估值 | `python fetch_fundamentals.py <代码>` | PE/PB/ROE/增速… + P0 语义分 |
| 资金流/筹码/龙虎榜 | `python fetch_capital_flow.py <代码>` | 主力净额序列+尾盘趋势、筹码、龙虎榜(A股) |
| 情绪面 | `python sentiment.py <代码>` | 市场情绪温度0-100 + 标签 |
| 新闻/政策/舆情 | `python anspire_search.py --name <名> --code <码> --market <A/US/...>` | 三组检索结果 |
| 自定义检索 | `python anspire_search.py --query "<关键词>" --top_k 8` | 单查询结果 |

## 3. 邻近标的比选 / 选股

对 2–4 只同业各跑 `analyze.py`，按 `prompts.md` B 步列对比表，从估值性价比/增速弹性/
确定性/催化临近度/拥挤度排序，回答"同样的钱为什么买这只"。批量可遍历 `STOCK_LIST`。

## 4. 决策模型要点（细节见 references/）

- **五因子加权**：消息0.22 / 情绪0.13 / 基本面0.25 / 技术0.22 / 资金0.18（`W_*` 可覆盖，自动归一化）。
- **市场降级**：美/日/韩无资金流→该因子权重按比例摊给其余（报告 `weights_used` 体现）。
- **综合分映射**：≥68 买入｜56–68 逢低买/持有偏多｜45–56 持有｜33–45 减持｜<33 卖出。
- **风险否决**优先于综合分（财务雷/黑天鹅/政策反转/技术破位/拥挤交易）。
- **量价口诀**：尾盘资金、红绿黑成交、竞价规则见 `references/auction-rules.md`，用于人工校正技术/资金子分。
- **可追溯**：报告必须复述 `breakdown` 的"因子×权重=贡献"并做敏感性分析（胜负手因子）。

## 5. 参考文件

- `references/decision-framework.md` — 评分口径、权重、决策映射、风险否决、弹性/验证链。
- `references/prompts.md` — 拆解预言四步法、比选、综合分析、无人值守 LLM 提示词。
- `references/auction-rules.md` — A股/美股竞价、尾盘资金、红绿黑成交口诀。
- `references/market-support.md` — 各市场数据边界与代码格式。
- `references/loop-iteration.md` — 每日 /loop 复盘、统计校准、调参纪律（让模型越用越准）。
- `templates/report-template.md` — 决策报告模板。

## 6. 每日迭代（可选 /loop）

用 `/loop` 或 schedule 每日：批量分析 `STOCK_LIST` → 更新消息面与结论 → 回填昨日预测的实际
表现到 `reports/journal.jsonl` → 统计命中率与因子 IC → 按 `loop-iteration.md` 的纪律微调
`W_*` 与口径。单次不调参、单次幅度≤0.03、保留默认权重对照，避免过拟合。

## 7. 免责声明

输出仅为研究与教育用途，不构成投资建议；数据可能延迟或有误，结论含主观判断。
用户应独立核实并自负盈亏。
