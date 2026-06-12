# Forward-Looking Risk Review (Layer 4)

The first four layers are **static**: they check whether each clause is present, clear, and internally consistent *as written today*. They do not ask what happens once the contract is actually performed — over months or years, by a counterparty who will read every clause literally and in their own favor.

Layer 4 is **dynamic and adversarial**. It assumes performance will *not* go smoothly: time will slip, scope will grow, external conditions will change, and the counterparty will exploit any asymmetry. Its job is to find, before signing, every place where our side silently absorbs that risk.

**Governing principle — cautious judgment (谨慎判断):**
- When a clause is silent on who bears a foreseeable risk, the default allocation almost always falls on the performing party. Treat silence as a red flag, not as neutral.
- When wording is open-ended ("etc.", "including but not limited to", "as reasonably required", "to the other party's satisfaction"), assume it will be read in its broadest sense against us.
- When in doubt about severity, flag **up**, not down. A false alarm costs a sentence; a missed trap costs the project.
- Quantify exposure whenever possible ("each extra review round ≈ N person-days, uncapped" beats "scope may expand").

---

## The four stress-test questions

Apply these to **every material obligation, deliverable, milestone, and payment trigger** in the contract. Each obligation that fails a question becomes a Layer 4 finding.

1. **Time** — *If this is delayed, who bears it?* Is our deadline firm while our dependencies (counterparty inputs, approvals, third parties, permits) are open-ended? Is there relief (extension of time) when the cause is not ours?
2. **Workload** — *If this turns out to be more work than expected, who pays?* Is scope bounded? Are revisions, iterations, re-tests, or re-submissions capped? Does extra work route through a paid change mechanism, or is it swallowed under a vague "as required"?
3. **Future conditions** — *If the world changes — prices, rates, law, supply, technology — does the deal still hold and stay fair to us?* Is a long or fixed commitment exposed to movement it cannot pass through or adjust for?
4. **Adversarial reading** — *If the counterparty reads this clause in the most literal, self-serving way, what is the worst outcome?* Is the worst case survivable (capped, insurable, exitable), or open-ended?

---

## A. Schedule / time risk (工期风险)

- **One-sided deadlines** — our obligations carry fixed dates and penalties; counterparty inputs we depend on (data, approvals, site access, sign-off, prior-phase deliverables) have no date or no penalty.
- **No extension-of-time (EOT) mechanism** — no clause grants us relief when delay is caused by the counterparty, a third party, force majeure, or a change in scope. Liquidated damages then accrue against us regardless of fault.
- **Conditions precedent buried in the timeline** — our clock starts on signing, but real start depends on a deposit, permit, or third-party act that the contract does not time-bound.
- **Open-ended review/approval loops** — "Party A may request revisions until satisfied" with no round limit and no time limit silently makes the end date unknowable.
- **Acceptance by silence vs. acceptance by act** — if acceptance requires the counterparty's active sign-off but they have no deadline to give it, payment and completion can be stalled indefinitely. Prefer deemed-acceptance after N days of inaction.
- **Time is of the essence** combined with our dependence on others is a trap: it hardens our deadline without hardening theirs.
- **Cascading milestones** — a slip in an early counterparty-controlled step compresses every downstream window that *we* are penalized on.

**Suggested fixes to offer:** symmetrical deadlines; explicit EOT triggers (counterparty delay, scope change, force majeure) with day-for-day extension; cap total liquidated damages; deemed acceptance after a fixed inactivity period; start-clock tied to satisfaction of conditions precedent, not signing.

## B. Scope / workload creep (工作量蔓延)

- **Unbounded scope language** — "including but not limited to", "and related work", "等", "such other services as may be reasonably required". Each phrase is an open door to unpaid work.
- **Subjective acceptance criteria** — "to Party A's satisfaction", "industry-leading quality", "as approved" with no objective, measurable standard. The counterparty decides when you are done.
- **Uncapped revisions / iterations** — design, drafts, reports, software builds re-done an unlimited number of times at no extra fee.
- **No change-order mechanism** — there is no clause that says additional or changed work is quoted, agreed, and paid before it proceeds. Without it, every change is free to the counterparty and costly to us.
- **Free maintenance / warranty creep** — "warranty" or "support" defined so broadly it becomes open-ended new development rather than defect repair.
- **Embedded third-party coordination** — obligations to "coordinate with", "integrate", or "obtain sign-off from" other vendors/authorities whose effort and timeline you cannot control but are accountable for.
- **Most-favored / catch-all obligations** — "ensure the project succeeds", "deliver a fully functional system", outcome-guarantees that absorb unlimited effort.

**Suggested fixes to offer:** an exhaustive, itemized scope with explicit exclusions; objective, testable acceptance criteria; a cap on revision rounds (e.g., 2) with extra rounds billed; a written change-order procedure (quote → approval → invoice) as the *only* route for added scope; warranty limited to defects against the agreed spec for a defined period.

## C. Future contingencies (未来不确定因素)

- **Fixed price over a long or volatile term** with no adjustment/index/escalation clause — exposes us to raw-material, labor, currency, and freight movement.
- **No tax / law / policy change clause** — a later change in tax rate, tariff, licensing, or regulation lands entirely on the performing party.
- **Currency and cross-border exposure** — price in one currency, costs in another, no FX mechanism; or payment subject to foreign exchange controls/withholding not allocated.
- **Long-term exclusivity or minimum-volume commitments** — lock us in even if our cost base or the market shifts; check for an exit or review point.
- **Third-party / supply-chain dependency** — performance hinges on a sub-supplier, platform, or license that could fail, raise prices, or disappear, with no pass-through or relief.
- **Technology / standard obsolescence** — multi-year deliverables tied to a spec, platform, or regulation likely to change mid-term.
- **Renewal and termination asymmetry** — auto-renewal that locks us in; long notice period to exit vs. short notice for them; termination-for-convenience available only to the counterparty.

**Suggested fixes to offer:** price-adjustment/index clause or periodic price review; a "change in law / tax" reopener; FX and withholding allocation; hardship/material-adverse-change reopener for long terms; symmetrical renewal/termination notice; pass-through or relief for named third-party dependencies.

## D. Hidden traps & asymmetry (隐性陷阱)

Scan specifically for clauses that look standard but allocate risk asymmetrically or open-endedly:

- **Asymmetric penalties** — liquidated damages or default interest run against us but not against them, or at different rates.
- **Uncapped liability / indemnity** — no aggregate liability cap; indemnities covering "any and all" losses including indirect/consequential; one-way indemnity.
- **Joint and several liability / guarantees** — we guarantee others' performance, or are jointly liable for a consortium we don't control.
- **Cross-default and set-off** — default under one contract triggers default here; the counterparty may set off unrelated claims against money owed to us.
- **Perpetual or unbounded obligations** — confidentiality, non-compete, or exclusivity with no end date or unreasonable scope/geography.
- **Broad IP assignment** — assigns more than the deliverable (background IP, tools, know-how), or grants rights beyond the agreed use.
- **Conditions precedent to *our* payment that are in the counterparty's gift** — payment "upon Party A's confirmation" with no deadline or objective trigger.
- **Retention / holdback** without a defined release date or condition.
- **Unilateral amendment / "as updated from time to time"** incorporating external policies the counterparty can change at will.
- **Entire-agreement + no-oral-modification** that quietly voids prior promises, side letters, or emails relied upon.
- **Notice and cure asymmetry** — they get notice-and-cure before termination; we can be terminated immediately.
- **Most-favored-customer, audit, or step-in rights** granted one way only.

**Suggested fixes to offer:** symmetry as the default test — every right or penalty granted to one party should be examined for a mirror; aggregate liability cap (e.g., contract value) excluding indirect loss; bilateral indemnity scoped to fault; defined end dates and reasonable scope for surviving obligations; objective, time-bound payment triggers; mutual notice-and-cure.

---

## How Layer 4 findings are written

Layer 4 findings use the same comment structure (issue type, risk reason, revision suggestion) and the same reviewer-name risk encoding as Layers 1–3. Specifics:

- **Issue type** uses a Layer 4 label: `Schedule Risk` / `Scope Creep` / `Future Contingency` / `Hidden Trap` (Chinese: `工期风险` / `工作量蔓延` / `未来不确定性` / `隐性陷阱`). See `language.md`.
- **Risk reason** must name (a) the trigger ("if the counterparty delays its data delivery…"), (b) who currently bears it, and (c) the concrete exposure, quantified where possible.
- **Revision suggestion** must be a *specific clause-level fix* (an EOT trigger, a revision cap, a change-order procedure, a liability cap), not a generic "clarify this".

**Risk level guidance (Layer 4):**
- 🔴 High: open-ended, uncapped exposure on a core dimension — uncapped scope/liability, no EOT against penalties on a critical path, fixed price on a long volatile term with no adjustment.
- 🟡 Medium: real but bounded or lower-probability exposure — recoverable through negotiation, or affecting a non-critical obligation.
- 🔵 Low: minor asymmetry or low-likelihood contingency worth noting but not blocking.

Distinguish Layer 4 from Layer 2: Layer 2 asks *"is this business term clear and complete as written?"*; Layer 4 asks *"as this contract is performed over time and conditions change, where does our side get squeezed?"* The same clause may legitimately draw both a Layer 2 and a Layer 4 comment.
