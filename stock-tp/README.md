# stock-tp · A股/美股个股研究决策 Skill

把个股研究拆成四块——**消息面 / 情绪面 / 财报行业 / 综合预测**——聚合多市场数据，
用可视、可追溯、可调权重的五因子模型给出**买入/卖出/持有**结论。

## 快速开始
```bash
pip install -r requirements.txt
cp config.example.env config.env      # 填 ANSPIRE_API_KEYS（新闻必需）
cd scripts && python analyze.py 600519 --save
```
然后在 Claude Code 里直接说「分析一下贵州茅台 / 600519 该不该买」即可触发 skill。

## 结构
```
SKILL.md                  主流程（Claude 读这个）
scripts/
  common.py               配置/市场识别/缓存/降级
  fetch_market.py         行情·K线·技术指标(本地计算)
  fetch_fundamentals.py   基本面·估值·P0语义分
  fetch_capital_flow.py   资金流·筹码·龙虎榜(A股)
  sentiment.py            市场情绪温度
  anspire_search.py       新闻/政策/舆情检索(Anspire AI Search)
  anspire_llm.py          可选·无人值守时的LLM综合层(OpenAI兼容)
  analyze.py              四块聚合 + 可追溯加权决策引擎
references/               框架·拆解预言·竞价红绿黑·市场边界·每日校准
templates/report-template.md   决策报告模板
```

## 支持市场
A股 `600519` · 港股 `hk00700` · 美股 `AAPL` · 日股 `7203.T` · 韩股 `005930.KS` · ETF `510300`
（资金流/筹码/龙虎榜为 A 股专属，其余市场自动降级并重分配权重）

## 数据源
- A股/港股：akshare（东财→新浪兜底）
- 美/日/韩：yfinance
- 新闻舆情：Anspire AI Search

> 仅供研究与教育用途，非投资建议。
