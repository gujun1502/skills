# 每日迭代与自校准（loop）

需求："/loop 每天对这个 skills 模型进行迭代、分析、总结、归纳，以期更准确反映市场。"
做法是把"预测 → 实际 → 复盘 → 调参"闭环固化，让权重和打分口径越用越准。

---

## 1. 复盘日志

每次出报告后，向 `reports/journal.jsonl` 追加一行（JSON）：

```json
{"date":"2026-06-21","symbol":"600519","action":"逢低买入","composite":61.2,
 "entry":1620,"target":1750,"stop":1560,
 "factor_scores":{"news":70,"sentiment":77,"fundamental":67,"technical":36,"capital":50},
 "thesis":"AI+业绩高增长；待Q3财报验证","catalyst_date":"2026-10-下旬"}
```

收盘后/次日，回填实际表现：

```json
{"date":"2026-06-21","symbol":"600519","realized":{"d1_chg":1.2,"d5_chg":-0.8,
 "hit_target":false,"hit_stop":false},"verdict":"方向对、幅度高估"}
```

## 2. 每日 loop 任务清单（可被 /loop 或 schedule 驱动）

1. 对 `STOCK_LIST` 批量跑 `analyze.py`，生成/更新各标的数据包。
2. 对持仓与关注标的，用 prompts.md 流程更新消息面分与结论。
3. 回填昨日预测的实际表现到 journal。
4. **统计校准**（见下），输出当日"模型体检"小结。
5. 把当日新发现的有效规律/失效规律写入 `references/lessons.md`（自建，增量积累）。

## 3. 统计校准指标（周/月滚动）

- **命中率**：action=买入/增持 后 N 日上涨比例；卖出/减持后下跌比例。
- **方向准确度 vs 幅度误差**：常见"方向对、幅度偏"，据此校准点位与情景概率。
- **因子有效性**：分因子做 IC（子分与未来收益的相关性）。某因子长期 IC≈0 → 降权；
  显著为正 → 适度升权。调整落到 `W_*` 环境变量，并在 journal 记录调参原因与日期。
- **过拟合护栏**：单次样本不调参；权重单次调整幅度 ≤ 0.03；保留默认权重作对照。

## 4. 调参纪律

- 只有在 ≥20 个样本、跨不同行情(涨/跌/震荡)下仍稳定的信号，才固化为口径变更。
- 每次调参写明：依据(统计结果) → 改动(哪个 W_/阈值) → 预期 → 回看验证日期。
- 记录失败案例与"本可避免"的清单，比记录成功更重要（对应买方 memo 的真正价值）。

## 5. 与 Codex 金融 Skill 思路对齐（借鉴）

- serenity-alpha / Bayesian 估值 / GF-DMA 健康度 / TAM-adjusted PEG / 买方研报 memo：
  共同点是把研究拆成**「需求变化 → 财报传导 → 弹性 → 验证」可追溯链条**。
- 本 skill 已将该链条嵌入 decision-framework.md §7 与 prompts.md A 步；loop 阶段持续
  用"验证路径是否兑现"反向打分 thesis 质量，淘汰常错的逻辑模板。
