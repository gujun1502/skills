---
name: stock-tp-inadvance
description: A股个股【早盘开盘前(约9:00)】的量化决策与当日/三日预测工具。开盘前聚合五个板块——①宏观风险预警(美股隔夜、日韩亚太早盘联动、汇率/利率/政策)②资金流(前一日/前一周主力超大单大单流入流出与小单承接)③个股盘口(五档/委比/内外盘主动买盘/量能，含用户持仓买入价与股数的浮盈亏与套牢解套分析)④板块联动与信息面(同业/行业ETF合力+苹果链/先进封装/存储/A50等主题，按linkage.json可配参数)⑤模型学习进化(每日复盘命中率、按纪律微调权重、刻画用户风险偏好)——用可追溯五因子模型预测今日9:30-15:00的开盘缺口与最高/最低点、未来三天趋势与理论高低价位，并给出到价位的早盘操作清单与套牢应对。当用户在盘前问"今天某只A股怎么走/高低点多少/该不该卖/手里这只套了怎么办"、要早盘研判/开盘前作战图/当日高低点预测/三日趋势/盘口与持仓分析、或提到A股代码(如002156通富微电)寻求当日操作决策时使用。区别于偏中长期价值研究的 stock-tp。
---

# stock-tp-inadvance：A股早盘决策与当日/三日预测

**定位**：每天开盘前（约 9:00）给你一张「今日作战图」——预测今日 9:30–15:00 的高低点、
未来三天趋势与理论高低价位，结合你的持仓成本给到价位的操作建议。
偏中观/微观择时；姊妹 skill `stock-tp` 偏中长期价值研究，二者协作（见 §5）。

> ⚠️ 输出始终声明"研究分析、非投资建议"。预测是**概率区间非精确点位**。取数失败如实标注并降级，不编造。

## 0. 准备（首次或报错时）
```bash
cd <skill目录>
pip install -r requirements.txt          # akshare / yfinance / pandas
cp config.example.env config.env         # ANSPIRE_API_KEYS(可选,新闻用)；W_PM_* 权重可选
```
- 宏观隔夜/亚太/汇率利率走 **yfinance**（全球通，必装）。资金流/盘口/板块联动走 **akshare**（A股）。
- 重点股请在 `linkage.json` 登记其**同业/行业ETF/隔夜代理/主题**（已含 002156 示例，照葫芦画瓢加）。
- 所有脚本在 `scripts/` 下运行，输出 UTF-8 JSON。

## 1. 标准早盘流程（单只股票）

**第一步——一键聚合 + 预测**（五板块 + 当日/三日预测 + 持仓分析）：
```bash
cd scripts && python premarket.py <代码> --buy-price <买入价> --shares <股数> --save
# 例：python premarket.py 002156 --buy-price 26.8 --shares 1000 --save
# 不带持仓也行：python premarket.py 002156 --save
# 叠加新闻检索(需Key)：加 --news
```
读它打印的 JSON（也存 `reports/<代码>_<日期>_premarket.json`）。它已算好：
- `factor_scores`：技术/资金/宏观隔夜/板块联动/情绪 五个子分；
- `decision`：`premarket_score`、`action`、`confidence`、可追溯 `breakdown`(因子×权重=贡献)、`weights_used`；
- `prediction.today`：预测开盘缺口、最高/最低点(ATR模型 + 技术位校准 high_ref/low_ref)、预期振幅；
- `prediction.three_day`：趋势标签、理论高低位、波浪位置提示；
- `position`：浮盈亏、是否套牢、解套位、今日能否解套、操作建议；
- `blocks`：各板块原始数据(overnight/capital/orderbook/linkage/sentiment/market)。

**第二步——信息面与盘口语义解读（你来做，脚本不做）**：按 `references/premarket-framework.md` §4：
- 读 `blocks.overnight`(隔夜板块/个股代理)、`blocks.linkage.themes`(苹果链/先进封装/存储/A50…)、`blocks.news`，判断今天有无针对该股/板块的催化或利空，**手动微调**预测区间与建议（写明理由）；
- 读 `blocks.orderbook.signals`(主动买盘/委比/量能)校正当日强弱；
- **风险否决**：隔夜对应板块大跌 / 人民币急贬 / 美债急升 / 个股放量长上影或主力大幅净流出 / 年内高位+RSI超买（呼应"高位听消息追买被套"）→ 命中则下调结论并红字警报。

**第三步——出报告**：套 `templates/premarket-report.md`，产出中文《今日作战图》。
含三情景、到价位的操作清单、可追溯因子表与胜负手。要存档：写 `reports/<代码>_<日期>_premarket.md`。
要 PDF：`python md_to_pdf.py reports/<代码>_<日期>_premarket.md`。

**第四步——收盘复盘（进化）**：见 §4。

## 2. 单脚本（按需取某一板块）

| 板块 | 命令 | 产出 |
|------|------|------|
| ①宏观隔夜 | `python fetch_overnight.py --code <码>` | 美股隔夜/日韩早盘/汇率利率 + macro_tilt + 个股代理 proxy_tilt |
| ②资金流 | `python fetch_capital_flow.py <码>` | 主力/超大单净流入序列+尾盘趋势、筹码、龙虎榜 |
| ③盘口 | `python fetch_orderbook.py <码>` | 实时五档/委比/内外盘主动买盘/量比 + 派生信号 |
| ④板块联动 | `python fetch_linkage.py <码>` | 同业/ETF前一日合力 linkage_tilt、齐心度、主题 |
| 行情/指标 | `python fetch_market.py <码> --days 120` | K线 + MA/MACD/RSI/KDJ/BOLL/ATR/量比 |
| 情绪面 | `python sentiment.py <码>` | 市场情绪温度0-100 |

## 3. 五因子与预测口径（细节见 references/premarket-framework.md）
- **权重**：技术0.25 / 资金0.22 / 宏观隔夜0.20 / 板块联动0.18 / 情绪0.15（`W_PM_*` 可覆盖，自动归一化）。
- **市场降级**：非A股无资金流/联动→该因子权重摊给其余（`weights_used` 体现）。
- **早盘分映射**：≥66 积极/低吸｜56–66 谨慎偏多｜45–56 观望不追高｜34–45 防守/反弹减仓｜<34 回避。
- **今日高低点**：预测开盘(隔夜+联动定缺口) ± ATR×波动系数(按多空偏向劈分)，再用最近支撑/压力校准。
- **三日**：ATR×√3 放大、向中级别均线/年内高低靠拢，配波浪位置提示。
- **可追溯**：报告必须复述 `breakdown` 并指出胜负手因子。

## 4. 模型学习与进化（模块⑤，详见 references/premarket-learning.md）
每次跑都自动写预测日志 `reports/premarket_journal.jsonl`。收盘后：
```bash
python premarket.py <代码> --review     # 看历史预测，回填实际开高低收
```
Claude 协助：取当日实际值回填 → 算高低点误差与方向命中率 → 定性归因(哪个因子帮了/坑了) →
**有纪律地**微调 `W_PM_*`（一次一项、幅度≤0.03、留默认对照、样本≥10才动）→ 逐步刻画你的
风险偏好（你怕"高位听消息追买被套"，默认更强调不追高、低吸、套牢反弹减仓）与中国股市阶段判断。

## 5. 与 stock-tp（深度研究 skill）协作
本 skill 管"今天/三天怎么操作"；需要判断"这票中长期基本面/估值/消息面预言行不行"时，
引用同目录脚本（`fetch_fundamentals.py` / `anspire_search.py`）或老 skill 的 `analyze.py`，
把中长期结论作为三日趋势偏向的背景修正。二者互不改动、各司其职。

## 6. 免责声明
仅供研究与教育用途，不构成投资建议；数据可能延迟或有误，结论含主观判断与概率预测。
用户应独立核实并自负盈亏。
