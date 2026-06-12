# Contract Review Pro / 合同审阅（专业版）

Professional-grade contract review skill. Adds comment-based issue annotations without modifying the original text. Enforces a five-layer review methodology — including a forward-looking, adversarial risk layer that cautiously judges schedule slippage, scope/workload creep, future uncertainties, and hidden traps — and produces a full review deliverable.

专业级合同审阅 skill。只加批注、不改原文；五层方法论审查（含前瞻性、对抗式的风险层，谨慎判断工期拖延、工作量蔓延、未来不确定因素与隐性陷阱），并生成完整的审核交付物。

## What you get / 产出

- **Annotated contract (.docx)** — inline comments anchored to specific clauses
- **Contract summary (.docx)** — key terms, amounts, parties at a glance
- **Consolidated review opinion (.docx)** — prioritized issue list with recommendations
- **Business flowchart** — Mermaid source + rendered image

- **批注版合同（.docx）** — 精准锚定条款的批注
- **合同摘要（.docx）** — 关键条款 / 金额 / 主体一览
- **综合审核意见（.docx）** — 按优先级排序的问题清单与建议
- **业务流程图** — Mermaid 源码 + 渲染图

## Five-layer methodology / 五层方法论

0. **Entity verification** — 主体核验：确认签约方资质
1. **Basic review** — 基础审查：标题、日期、条款编号、引用一致性
2. **Business review** — 业务审查：商业条款合理性与内部一致性
3. **Legal review** — 法务审查：风险条款、责任分配、争议解决
4. **Forward-looking risk** — 前瞻性风险审查（动态、对抗式）：对每一项实质义务做"压力测试"，谨慎判断**工期拖延、工作量蔓延、未来不确定因素、隐性陷阱**——把条款空白视为风险信号，把模糊措辞按对我方最不利的方式解读，吃不准就往高报。

Layers 0–3 are **static** (is each clause clear and consistent *as written*?). Layer 4 is **dynamic and adversarial** (as the contract is performed over time and conditions change, where does our side get squeezed?). See [`references/forward-risk.md`](references/forward-risk.md).

前四层是**静态**审查（条款写得清不清楚、前后一致不一致）；第五层是**动态对抗式**审查（合同履行起来、外部条件一变，我方会在哪里被挤压）。

## Language

Output language follows the contract's dominant language (detected automatically). All comments, summary, opinion, and flowchart labels are generated in the detected language.

输出语言跟随合同主导语言自动适配。

## Install

```bash
npx skills add lovstudio/contract-review-pro-skill --all -g
```

## See also

- [`review-doc`](https://github.com/lovstudio/review-doc-skill) — lightweight daily version for general document review
- [`review-doc`](https://github.com/lovstudio/review-doc-skill) — 日常轻量版，适用于普通文档审阅

## License

MIT — content adapted from jicheng's contract-review methodology.
