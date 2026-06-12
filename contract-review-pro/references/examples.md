# Contract Review Examples

## Quick Start

```python
# -*- coding: utf-8 -*-
from scripts.workflow import ContractReviewWorkflow

comments = [
    {
        "search": "Total Price",
        "comment": """[Issue Type] Payment Terms
[Risk Reason] The total amount is stated as USD 100,000 in Section 3.2, but the payment clause lists USD 1,000,000 in Section 5.1.
[Revision Suggestion] Align the total amount across clauses and clarify tax inclusion.""",
        "risk_level": "High",
    }
]

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(comments, "Contract_Reviewed.docx")
```

## Forward-Looking Risk Comments (Layer 4)

Layer 4 comments use the same structure as other layers; the issue type names the risk family, the risk reason states the trigger + who bears it + the quantified exposure, and the suggestion is a clause-level fix. See **[forward-risk.md](forward-risk.md)**.

```python
# -*- coding: utf-8 -*-
comments = [
    {
        "search": "Party A may request revisions",
        "comment": """[Issue Type] Scope Creep
[Risk Reason] Section 4 lets the counterparty request revisions "until satisfied" with no cap on rounds and no objective acceptance standard. As performance proceeds, this is an open door to unlimited unpaid rework — each extra review round is ~N person-days absorbed entirely by our side, and the completion date becomes unknowable.
[Revision Suggestion] Cap included revisions (e.g., 2 rounds); bill further rounds at an agreed day rate via a written change-order; replace "to Party A's satisfaction" with objective, testable acceptance criteria; deem the deliverable accepted if no written objection within N business days.""",
        "risk_level": "High",
    },
    {
        "search": "delivery within 30 days",
        "comment": """[Issue Type] Schedule Risk
[Risk Reason] Our 30-day delivery deadline is fixed and carries liquidated damages, but it depends on the counterparty's data hand-off and site access, which carry no date and no penalty. If their input slips, our clock keeps running and we pay delay damages for a delay we did not cause.
[Revision Suggestion] Add an extension-of-time clause granting day-for-day relief for counterparty delay, scope change, and force majeure; start our clock only after the counterparty's inputs are delivered; cap total liquidated damages.""",
        "risk_level": "High",
    },
    {
        "search": "fixed price",
        "comment": """[Issue Type] Future Contingency
[Risk Reason] The price is fixed for a 3-year term with no adjustment mechanism, leaving us fully exposed to raw-material, labor, and FX movement plus any change in tax or regulation over that period.
[Revision Suggestion] Add an annual price-review / index-linked adjustment clause and a change-in-law / change-in-tax reopener; allocate FX and withholding exposure explicitly.""",
        "risk_level": "Medium",
    },
]
```

## Contract Summary (English)

```python
# -*- coding: utf-8 -*-
summary_text = """I. Basic Contract Information
Item\tContent
Contract Name\tNot specified
Contract Type\tNot specified
Parties\tParty A: Not specified
Party B: Not specified
Signing Date\tNot specified
Term\tNot specified
Contract Amount\tNot specified
II. Business Model Overview
Brief description: Not specified
III. Key Clause Elements
3.1 Transaction Elements
Element\tDetails
Subject Matter/Services\tNot specified
Quantity/Specs\tNot specified
Pricing Structure\tNot specified
Payment Terms\tNot specified
Delivery Terms\tNot specified
3.2 Rights and Obligations
Party A main rights/obligations:
Not specified
Party B main rights/obligations:
Not specified
3.3 Performance Safeguards
Clause Type\tDetails
Liability/Default\tNot specified
Guarantees/Security\tNot specified
Acceptance Standards\tNot specified
Quality Warranty\tNot specified
3.4 Risk Allocation & Special Terms
Risk Allocation:
Not specified
Special Terms:
Not specified
3.5 Dispute Resolution & Termination
Item\tDetails
Dispute Resolution\tNot specified
Amendment\tNot specified
Termination\tNot specified
Governing Law\tNot specified
IV. Key Timeline Milestones
Not specified
"""

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(
    comments,
    "Contract_Reviewed.docx",
    summary_text=summary_text,
    summary_filename="Contract_Summary.docx",
    summary_font="Times New Roman",
)
```

## Consolidated Opinion (English)

```python
# -*- coding: utf-8 -*-
opinion_text = """This agreement is a goods sales contract under which our side purchases specific devices from the counterparty for a total amount of USD 100,000, payable as a 30% prepayment and 70% balance after acceptance, with delivery and acceptance milestones defined in the contract.

After review, the following key risks require attention: 1. Product model names are inconsistent across clauses, which may cause delivery disputes; 2. The prepayment amount does not match the stated percentage, potentially causing payment execution issues; 3. Delivery timing is stated as “reasonable time,” which is ambiguous and may lead to delay disputes."""

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(
    comments,
    "Contract_reviewed.docx",
    opinion_text=opinion_text,
    opinion_filename="Consolidated_Opinion.docx",
    opinion_font="Times New Roman",
)
```

## Business Flowchart (Mermaid)

```python
# -*- coding: utf-8 -*-
flowchart_mermaid = """flowchart TD
    A[Contract Signed] -->|?| B[Performance]
"""

workflow = ContractReviewWorkflow("Contract.docx", "Reviewer")
workflow.run_full_workflow(
    comments,
    "Contract_reviewed.docx",
    flowchart_mermaid=flowchart_mermaid,
)
```

## Full Workflow Example

```python
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sys
from pathlib import Path

skill_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skill_dir))

from scripts.workflow import ContractReviewWorkflow

contract_path = "path/to/contract.docx"
output_path = "contract_reviewed.docx"
report_path = "review_report.txt"
reviewer = "Reviewer"

comments = [
    {
        "search": "Total Price",
        "comment": """[Issue Type] Payment Terms
[Risk Reason] Amount mismatch between pricing and payment clauses.
[Revision Suggestion] Align total amount and clarify tax.""",
        "risk_level": "High"
    }
]

summary_text = """I. Basic Contract Information
Item\tContent
Contract Name\tNot specified
Contract Type\tNot specified
Parties\tParty A: Not specified
Party B: Not specified
Signing Date\tNot specified
Term\tNot specified
Contract Amount\tNot specified
"""

opinion_text = """This agreement is a services contract between our side and the counterparty with defined scope, pricing, and milestones.

After review, the following key risks require attention: 1. Payment timing is unclear; 2. Acceptance criteria are missing."""

flowchart_mermaid = """flowchart TD
    A[Contract Signed] -->|?| B[Performance]
"""

workflow = ContractReviewWorkflow(
    contract_path=contract_path,
    reviewer_name=reviewer,
    enable_smart_keyword_expansion=False,
)

workflow.run_full_workflow(
    comments=comments,
    output_docx_filename=output_path,
    report_filename=report_path,
    summary_text=summary_text,
    summary_filename="Contract_Summary.docx",
    summary_font="Times New Roman",
    opinion_text=opinion_text,
    opinion_filename="Consolidated_Opinion.docx",
    opinion_font="Times New Roman",
    flowchart_mermaid=flowchart_mermaid,
    render_flowchart=True,
    parallel_outputs=True,
)

print(f"✓ Added comments: {len(workflow.comments_added)}")
print(f"✗ Failed comments: {len(workflow.comments_failed)}")
```

## Language Notes

- Output must follow the contract’s language.
- For Chinese contracts, use the Chinese labels in **[language.md](language.md)** and set `summary_font` / `opinion_font` to Fangsong (仿宋).
