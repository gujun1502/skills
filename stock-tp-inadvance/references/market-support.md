# 市场支持边界

不同市场可取的数据块不同。脚本对不支持的块返回 `status: "not_supported"`，
决策引擎会把缺失因子的权重按比例**重分配**给其余因子（见报告 `weights_used`）。

| 数据块 | A股 | 港股 HK | 美股 US | 日股 .T | 韩股 .KS/.KQ |
|--------|:--:|:--:|:--:|:--:|:--:|
| 行情/K线 quote/kline | ✅ akshare | ✅ akshare/yf | ✅ yf | ✅ yf | ✅ yf |
| 技术指标 indicator | ✅ 本地算 | ✅ | ✅ | ✅ | ✅ |
| 基本面 fundamental | ✅ akshare | ⚠️ yf | ✅ yf | ✅ yf | ✅ yf |
| 新闻舆情 news | ✅ Anspire | ✅ | ✅ | ⚠️ | ⚠️ |
| 资金流 capital_flow | ✅ | ❌ not_supported | ❌ | ❌ | ❌ |
| 筹码 chips | ✅ | ❌ | ❌ | ❌ | ❌ |
| 龙虎榜 dragon_tiger | ✅ | ❌ | ❌ | ❌ | ❌ |
| 涨跌停情绪 breadth | ✅ | ❌(用VIX) | ❌(用VIX) | ❌ | ❌ |

图例：✅ 支持 ｜ ⚠️ 部分/质量降级 ｜ ❌ not_supported（降级）

## 代码格式

| 市场 | 输入示例 | 归一化引擎 |
|------|----------|-----------|
| A股沪 | `600519` | akshare_cn (`.SS`) |
| A股深 | `000001` `300750` | akshare_cn (`.SZ`) |
| A股北 | `830799` `430139` | akshare_cn (`.BJ`) |
| ETF | `510300` `159915` | akshare_cn |
| 港股 | `hk00700` `00700.HK` | akshare_hk → yf 兜底 |
| 美股/ETF | `AAPL` `SPY` | yfinance |
| 日股 | `7203.T` | yfinance |
| 韩股 | `005930.KS` `.KQ` | yfinance |

## 网络注意

- A股/港股走 akshare（东方财富/新浪）；个别网络环境下东方财富 TLS 可能不通，
  脚本已内置**东财→新浪**兜底链。
- 美/日/韩走 yfinance（Yahoo）。
- 若结构化取数失败，Claude 应降级到 `WebSearch`/`WebFetch` 获取行情与新闻，
  并在报告中标注"数据来源降级、时效性下降"。
