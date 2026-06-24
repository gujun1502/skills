# stock-tp-inadvance · A股早盘决策 & 当日/三日预测 Skill

开盘前（约 9:00）给你一张**今日作战图**：聚合五个板块，用可追溯五因子模型预测
**今日 9:30–15:00 高低点**与**未来三天趋势/理论高低位**，并结合你的持仓给到价位的操作建议。

> 姊妹 skill `stock-tp` 偏中长期价值研究；本 skill 偏当日/三日择时。二者协作、互不改动。

## 五个板块
1. **宏观风险预警** — 美股隔夜 / 日韩亚太早盘联动 / 汇率·利率·政策（yfinance）
2. **资金流** — 前一日/前一周主力超大单大单流入流出、小单承接（akshare）
3. **个股盘口** — 五档/委比/内外盘主动买盘/量能 + 你的持仓浮盈亏与套牢解套（akshare）
4. **板块联动与信息面** — 同业/ETF合力 + 苹果链/先进封装/存储/A50 等主题（`linkage.json` 可配）
5. **学习进化** — 每日复盘命中率、按纪律微调权重、刻画你的风险偏好

## 快速开始
```bash
pip install -r requirements.txt
cp config.example.env config.env          # 可选：ANSPIRE_API_KEYS(新闻)、W_PM_*(权重)
cd scripts && python premarket.py 002156 --buy-price 26.8 --shares 1000 --save
```
然后在 Claude Code 里直接说「看下 002156 今天早盘怎么操作 / 我 26.8 买的 1000 股套了怎么办」即可触发。

## 结构
```
SKILL.md                  早盘主流程（Claude 读这个）
linkage.json              板块联动/隔夜代理/主题配置（含 002156 示例）
scripts/
  premarket.py            ★五板块聚合 + 当日/三日预测 + 持仓分析 + 学习日志
  fetch_overnight.py      ①宏观隔夜/亚太/汇率利率（yfinance）
  fetch_capital_flow.py   ②资金流·筹码·龙虎榜（沿用）
  fetch_orderbook.py      ③实时盘口·委比·内外盘
  fetch_linkage.py        ④板块同业/ETF 合力
  fetch_market.py / sentiment.py / fetch_fundamentals.py / anspire_search.py / md_to_pdf.py  （沿用）
references/
  premarket-framework.md  预测口径与决策逻辑
  premarket-learning.md   复盘与调参纪律（模块⑤）
templates/premarket-report.md  《今日作战图》报告模板
reports/                  数据包、报告、预测日志 premarket_journal.jsonl
```

## 预测怎么来（不黑箱）
- **今日高低点** = 预测开盘(隔夜+联动定缺口) ± ATR×波动系数(按多空偏向劈分)，再用最近支撑/压力校准。
- **三日趋势** = 技术/资金/联动慢变量定方向，ATR×√3 放大并向中级别均线/年内高低靠拢。
- 全程**可追溯**：每个结论复述「因子×权重=贡献」，并指出胜负手因子。

## 数据源
- 全球指数/汇率/利率/隔夜：yfinance（必装）
- A股资金流/盘口/板块：akshare（东财→新浪兜底）
- 新闻舆情（可选）：Anspire AI Search

> 仅供研究与教育用途，非投资建议；预测为概率区间，请独立核实、自负盈亏。
