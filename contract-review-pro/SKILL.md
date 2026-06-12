---
name: contract-review-pro
description: "Professional-grade contract review skill that adds comment-based issue annotations without changing original text. Enforces a five-layer review — entity verification, basic, business, legal, and forward-looking risk (schedule slippage, scope/workload creep, future contingencies, and hidden traps, judged adversarially and cautiously). Writes structured comments (issue type, risk reason, revision suggestion) with risk level encoded via reviewer name, and generates a contract summary, consolidated opinion, and Mermaid business flowchart (with rendered image). Output language must follow the contract’s language."
---

# Contract Review Skill

## Overview

This skill performs contract reviews by **adding comments only** (no edits to the original text). It follows a five-layer review (entity verification, basic, business, legal, and **forward-looking risk**) and generates:

- Annotated contract (.docx)
- Contract summary (.docx)
- Consolidated review opinion (.docx)
- Business flowchart (Mermaid + rendered image)

**Language rule:** detect the contract’s dominant language and output all generated content (comments, summary, opinion, flowchart text) in that language. Use the guidance in **[references/language.md](references/language.md)**.

## Workflow

1. Unpack the contract (.docx) for XML operations
2. Read contract text (pandoc or XML)
3. Extract and verify contracting parties (Layer 0)
4. Execute static clause review (Layers 1–3: basic, business, legal)
5. Execute forward-looking risk review (Layer 4: run the four stress-test questions over every material obligation)
6. Add comments to the document
7. Generate contract summary
8. Generate consolidated opinion
9. Generate business flowchart and render image
10. Repack to .docx

## Output Naming

- Output directory: `审核结果：{ContractName}` for Chinese or `Review_Result_{ContractName}` for English
- Reviewed contract: `{ContractName}_审核版.docx` for Chinese or `{ContractName}_Reviewed.docx` for English
- Review report: `审核报告.txt` for Chinese or `Review_Report.txt` for English

## Comment Principles

- **Comments only**: do not modify the original text or formatting
- **Precise anchoring**: comment should target specific clauses/paragraphs
- **Structured content**: each comment includes issue type, risk reason, and revision suggestion
- **Risk level**: carried by reviewer name; do **not** include a “risk level” line in comment body
- **Output language**: use labels in the contract’s language (see `references/language.md`)

**Comment example (English):**
```
[Issue Type] Payment Terms
[Risk Reason] The total amount is stated as USD 100,000 in Section 3.2, but the payment clause lists USD 1,000,000 in Section 5.1. This inconsistency may cause disputes.
[Revision Suggestion] Align the total amount across clauses and clarify whether tax is included.
```

## Review Standards

Use the five-layer review model and the detailed checklist in **[references/checklist.md](references/checklist.md)**. Layers 0–3 are **static** (is each clause present, clear, consistent as written?); Layer 4 is **dynamic and adversarial** (as the contract is performed over time and conditions change, where does our side get squeezed?).

### Layer 0: Entity verification (subject authenticity)
- Extract all contracting parties (full legal names, credit codes, legal representatives)
- Verify each entity's registered name accuracy and business registration status
- **Verification tool priority:**
  1. If an MCP tool for business registration lookup is available in the current environment (e.g., enterprise info query, company lookup, 企业查询, 工商查询), use it to query each party's name or Unified Social Credit Code.
  2. If no such MCP tool is available, use Web Search to look up "[entity name] 工商登记信息" or "[entity name] business registration".
  3. Record the verification source (MCP tool name / Web Search) in the comment.

### Layer 1: Basic (text quality)
- Accuracy of numbers, dates, terms
- Consistent numbering and references
- Clarity and lack of ambiguity
- Formatting and punctuation quality

### Layer 2: Business terms
- Scope, deliverables, quantity/specs
- Pricing and payment schedule
- Delivery/acceptance procedures
- Rights/obligations and performance guarantees

### Layer 3: Legal terms
- Effectiveness and term/termination
- Liability/penalties and remedies
- Dispute resolution and governing law
- Confidentiality, force majeure, IP, notice, authorization

### Layer 4: Forward-looking risk (dynamic / adversarial)
Static review (Layers 1–3) asks whether each clause is clear and complete *today*. Layer 4 asks how the contract behaves *over time, under changing conditions, read literally by an adversarial counterparty*. Full methodology, trap catalog, and fix language: **[references/forward-risk.md](references/forward-risk.md)**.

Apply the **four stress-test questions** to every material obligation, milestone, and payment trigger:
1. **Time** — if this is delayed, who bears it? Are our deadlines firm while our dependencies stay open-ended, with no extension-of-time relief?
2. **Workload** — if this is more work than expected, who pays? Is scope bounded, are revisions capped, does extra work route through a paid change-order?
3. **Future conditions** — if prices, rates, law, supply, or technology change, does the deal still hold and stay fair to us?
4. **Adversarial reading** — if the counterparty reads the clause in its most literal, self-serving way, what is the worst outcome, and is it capped/survivable?

The four risk families to surface: **Schedule risk (工期风险)**, **Scope creep (工作量蔓延)**, **Future contingencies (未来不确定性)**, **Hidden traps & asymmetry (隐性陷阱)**.

**Principle — cautious judgment (谨慎判断):** treat silence on risk allocation as a red flag (the default burden falls on the performing party); read open-ended wording in its broadest sense against us; when unsure of severity, flag **up**; quantify exposure where possible.

**Risk levels (encoded in reviewer name):**
- 🔴 High: core business ambiguity (price, scope, rights/obligations)
- 🟡 Medium: material but non-core ambiguity
- 🔵 Low: minimal practical impact

## Contract Summary

Generate a structured, objective summary in the contract’s language.
- See **[references/summary.md](references/summary.md)** (English template)
- Use **[references/language.md](references/language.md)** for language selection and Chinese labels

Output file: `合同概要.docx` for Chinese or `Contract_Summary.docx` for English (default font: 仿宋; adjust if language requires)

## Consolidated Opinion

Generate a concise, two-paragraph response for the business team in the contract’s language.
- See **[references/opinion.md](references/opinion.md)**

Output file: `综合审核意见.docx` for Chinese or `Consolidated_Opinion.docx` for English (default font: 仿宋; adjust if language requires)

## Business Flowchart (Mermaid)

Generate Mermaid flowchart per requirements and render to image.
- See **[references/flowchart.md](references/flowchart.md)**

Outputs:
- `business_flowchart.mmd`
- `business_flowchart.png`

## Technical Notes

Core workflow:
1. Unpack → 2. Entity verification → 3. Static review (L1–3) → 4. Forward-looking risk (L4) → 5. Add comments → 6. Summary → 7. Opinion → 8. Flowchart → 9. Repack

API & implementation details:
- **[references/technical.md](references/technical.md)**

## Dependencies

- Python 3.9+ (3.10+ recommended)
- pandoc (system install)
- defusedxml
- Mermaid CLI (`mmdc`) for rendering
- python-docx for rich text output

## Troubleshooting (Short)

- **Comments missing in Word**: run `doc.verify_comments()` and re-save
- **find_paragraph fails**: shorten search text; confirm actual paragraph text
- **Mermaid render fails**: ensure `mmdc` installed; use Chrome path or Puppeteer config

## Examples

See **[references/examples.md](references/examples.md)** for a full workflow example.

## Important Rules

1. Never alter original contract text
2. Entity verification (Layer 0) must complete before clause review (Layers 1–4)
3. Review all five layers, do not skip items; Layer 4 is mandatory, not optional
4. Run the four stress-test questions over every material obligation; treat silence on risk allocation as a red flag and flag up when severity is uncertain
5. Ensure risk level is accurate and consistent
6. Keep comments precise, professional, and actionable; Layer 4 fixes must be clause-level (an EOT trigger, a revision cap, a change-order, a liability cap), never a generic "clarify this"
7. Flowchart must come strictly from the contract text
8. Summary is objective only; no risk analysis
9. Opinion only reflects findings already identified, and leads with Layer 4 High risks

## License

SPDX-License-Identifier: Apache-2.0

Copyright (c) 2026 JiCheng

Licensed under the Apache License, Version 2.0. See repository root `LICENSE`.
