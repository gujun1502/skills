# Contract Review Checklist

## Layer 0: Entity Verification (Subject Authenticity)

### 1. Entity Extraction
- [ ] All contracting parties are identified (full legal names)
- [ ] Unified Social Credit Code (统一社会信用代码) is extracted if present
- [ ] Legal representative names are noted if stated
- [ ] Entity type is identified (company, individual business, natural person, etc.)

### 2. Name Accuracy
- [ ] Registered name matches exactly (no typos, missing/extra characters)
- [ ] Entity type suffix is correct (有限公司 vs 有限责任公司, etc.)
- [ ] If trade name differs from registered name, both are verified

### 3. Authenticity & Status
- [ ] Entity exists in business registration records
- [ ] Entity is not in revoked/cancelled/abnormal status
- [ ] Business scope covers the contract's subject matter (if verifiable)

### 4. Verification Method
- [ ] Use MCP business lookup tool (企业详情查询) if available
- [ ] Fall back to Web Search if MCP tool is unavailable
- [ ] Record verification source in comment

**Risk level guidance:**
- 🔴 High: entity does not exist, or name significantly wrong, or revoked/cancelled
- 🟡 Medium: minor name discrepancy, or status could not be fully verified
- 🔵 Low: minor formatting difference in name (e.g., punctuation)

---

## Layer 1: Basic Review (Text Quality)

### 1. Text Accuracy
- [ ] Key terms and spellings are correct
- [ ] Numbers, amounts, and ratios are accurate
- [ ] Amounts in words match numerals
- [ ] Dates are precise (avoid vague terms like “soon”)

### 2. Formatting Consistency
- [ ] Punctuation is correct
- [ ] Clause numbering is sequential
- [ ] No duplicate numbering
- [ ] Layout is clean
- [ ] Signature blocks have enough space

### 3. Clarity of Expression
- [ ] No grammar errors
- [ ] No unclear statements
- [ ] No ambiguity in time/quantity/quality
- [ ] Terminology is used correctly

### 4. Internal Consistency
- [ ] Same concept uses consistent naming
- [ ] Cross‑references are correct
- [ ] No logical conflicts across clauses
- [ ] Attachments match the main text

**Risk level guidance:**
- 🔴 High: ambiguity in core terms (price, subject matter, rights/obligations)
- 🟡 Medium: ambiguity in non‑core terms
- 🔵 Low: minimal practical impact

---

## Layer 2: Business Terms

### 1. Purpose & Term
- [ ] Purpose is clear
- [ ] Background is stated
- [ ] Start/end dates are clear
- [ ] Renewal terms are clear (if any)

### 2. Subject Matter
- [ ] Quantity is specific
- [ ] Category/brand/model/specs are clear
- [ ] Quality standards are clear
- [ ] Acceptance terms are operable
- [ ] Legality/ownership status is clear

### 3. Price & Payment
- [ ] Price structure is clear
- [ ] Pricing method is clear
- [ ] Currency is clear
- [ ] Tax separation is clear
- [ ] Tax responsibility is clear
- [ ] Payment method is clear
- [ ] Payment milestones align with performance
- [ ] Payment conditions are operable
- [ ] Invoice/receipt terms are clear

### 4. Performance
- [ ] Performance timeline is specific
- [ ] Performance location is specific
- [ ] Performance method is detailed
- [ ] Performance process is structured
- [ ] Title transfer point is clear
- [ ] Risk transfer point is clear
- [ ] Notice obligations are clear

### 5. Rights & Obligations
- [ ] Main rights are complete
- [ ] No implied waiver
- [ ] Exemption clauses are reasonable
- [ ] Main obligations are complete
- [ ] Standards for obligations are clear
- [ ] Obligations are feasible
- [ ] Post‑contract obligations are clear
- [ ] Ancillary rights/obligations are clear

### 6. Intellectual Property
- [ ] Existing IP ownership is clear
- [ ] IP created during performance is clear
- [ ] Scope/purpose/term of IP use is clear
- [ ] IP transfer/license terms are clear
- [ ] Protection responsibilities are clear
- [ ] Confidentiality/competition limits are reasonable

**Risk level guidance:**
- 🔴 High: core business cannot proceed due to contradictions/ambiguity/gaps
- 🟡 Medium: material dispute risk but business can still proceed
- 🔵 Low: minimal impact on business

---

## Layer 3: Legal Terms

### 1. Effectiveness
- [ ] Formation vs. effectiveness is distinguished
- [ ] Effectiveness conditions are clear
- [ ] Feasibility of conditions is considered
- [ ] Pre‑effect legal responsibility is addressed

### 2. Liability/Default
- [ ] Default types are clearly defined
- [ ] Remedies are clear
- [ ] Penalty ratio is reasonable
- [ ] Liability is balanced
- [ ] Calculation method is clear

### 3. Amendment/Termination
- [ ] Amendment conditions are clear
- [ ] Amendment procedure is clear
- [ ] Termination conditions are reasonable
- [ ] Termination procedure is operable
- [ ] End‑of‑term conditions are clear
- [ ] Survival clauses are reasonable
- [ ] Post‑termination duties are clear

### 4. Governing Law
- [ ] Governing law is specified
- [ ] Choice of law is reasonable
- [ ] No conflict with mandatory rules
- [ ] Enforceability is considered

### 5. Confidentiality
- [ ] Confidential info is defined
- [ ] Confidentiality term is clear
- [ ] Exceptions are limited and reasonable
- [ ] Breach liability is clear

### 6. Force Majeure
- [ ] Events are defined reasonably
- [ ] Notice duty is clear
- [ ] Exemption conditions are fair
- [ ] Follow‑up measures are clear

### 7. Dispute Resolution
- [ ] Dispute method is clear
- [ ] Jurisdiction/arbitration body is clear
- [ ] No conflict between arbitration/litigation
- [ ] Governing law matches dispute forum

### 8. Notice
- [ ] Notice method is clear
- [ ] Address/contact is complete
- [ ] Effective time/conditions are clear
- [ ] Change‑of‑address notice duty is clear

### 9. Authorization
- [ ] Authorized persons are clear
- [ ] Scope/authority is clear
- [ ] Term is reasonable
- [ ] Revocation/change mechanism is clear

### 10. Other Legal Terms
- [ ] Interpretation rules are clear
- [ ] Signing time/place is clear
- [ ] Severability is clear

**Risk level guidance:**
- 🔴 High: missing legal terms or unreasonable liability
- 🟡 Medium: other material issues
- 🔵 Low: minor issues

---

## Layer 4: Forward-Looking Risk (Dynamic / Adversarial)

Layers 0–3 check the contract *as written today*. Layer 4 checks how it behaves *as it is performed over time, under changing conditions, read by an adversarial counterparty*. Apply the four stress-test questions (Time / Workload / Future conditions / Adversarial reading) to **every material obligation, milestone, and payment trigger**. Methodology and fix language: **[forward-risk.md](forward-risk.md)**.

**Principle: cautious judgment.** Treat silence on risk allocation as a red flag; read open-ended wording in its broadest sense against us; when unsure of severity, flag up.

### A. Schedule / Time Risk (工期风险)
- [ ] Our deadlines and the counterparty's input deadlines are symmetrical (both dated, both enforced)
- [ ] An extension-of-time mechanism exists for counterparty delay, scope change, and force majeure
- [ ] Liquidated / delay damages are capped and apply only to fault attributable to us
- [ ] Acceptance/approval loops have a round limit AND a time limit (or deemed acceptance after inaction)
- [ ] The performance clock starts on satisfaction of conditions precedent, not merely on signing
- [ ] "Time is of the essence" is not combined with uncontrolled dependence on others

### B. Scope / Workload Creep (工作量蔓延)
- [ ] Scope is itemized and bounded; explicit exclusions are stated
- [ ] Acceptance criteria are objective and measurable (not "to satisfaction")
- [ ] Revisions / iterations / re-tests are capped; extra rounds are billable
- [ ] A written change-order procedure (quote → approval → invoice) is the only route for added scope
- [ ] Warranty/support is limited to defects against spec, not open-ended new work
- [ ] Obligations to coordinate with / integrate uncontrolled third parties are bounded

### C. Future Contingencies (未来不确定因素)
- [ ] Long or volatile fixed-price terms carry a price-adjustment / index / review clause
- [ ] A change-in-law / change-in-tax reopener exists
- [ ] Currency, FX, and withholding exposure is allocated
- [ ] Long-term exclusivity / minimum-volume commitments have an exit or review point
- [ ] Named third-party / supply-chain dependencies carry pass-through or relief
- [ ] Renewal and termination notice rights are symmetrical (no one-sided auto-renewal / convenience exit)

### D. Hidden Traps & Asymmetry (隐性陷阱)
- [ ] Penalties, default interest, and remedies are symmetrical between parties
- [ ] Liability is capped (aggregate) and excludes indirect/consequential loss; indemnities are bilateral and fault-scoped
- [ ] No uncontrolled joint-and-several liability or guarantee of others' performance
- [ ] No cross-default or one-way set-off against money owed to us
- [ ] Surviving obligations (confidentiality, non-compete, exclusivity) have end dates and reasonable scope
- [ ] IP assignment is limited to the agreed deliverable (no background IP / tools / know-how)
- [ ] Our payment triggers are objective and time-bound (not "upon counterparty confirmation" with no deadline)
- [ ] Retention/holdback has a defined release condition and date
- [ ] No unilateral amendment / "as updated from time to time" incorporating changeable external policies
- [ ] Notice-and-cure before termination is mutual

**Risk level guidance:**
- 🔴 High: open-ended / uncapped exposure on a core dimension (uncapped scope or liability, no EOT against penalties on the critical path, fixed price on a long volatile term)
- 🟡 Medium: real but bounded or lower-probability exposure
- 🔵 Low: minor asymmetry or low-likelihood contingency

---

## Usage Notes

### Review Process
1. Review in order: Layer 0 → Layer 1 → Layer 2 → Layer 3 → Layer 4
2. Evaluate each checklist item
3. For Layer 4, run the four stress-test questions against every material obligation
4. Record findings and risk levels
5. Add structured comments to the document

### Comment Format
Each comment must include:
- **Issue type** (matches checklist)
- **Risk reason** (impact and reasoning)
- **Revision suggestion** (actionable fix)

Risk level is encoded by reviewer name; **do not** add a “risk level” line inside the comment body.

### Priority
- **High**: address first
- **Medium**: address next
- **Low**: optional cleanup
