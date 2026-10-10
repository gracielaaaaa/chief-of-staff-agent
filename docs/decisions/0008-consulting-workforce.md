# 0008. Consulting workforce: one question batch, code gates, client firewall

Status: accepted, 2026-10-09

## Context
The first real pilot proposal (2026-10-09, handled in its own session) showed what a single drafter cannot do well:
- About 12 `[CHECK]` markers spread through the doc. Each one meant reopening the draft.
- The call notes and the client's questionnaire disagreed on a program price by 3x. Nothing caught it.
- Fees had no frame: nothing set her rate times hours next to the client's own prices and budget.
- The prospect's offers overlap with products owned by another client, who made the introduction.
- The proposal was late after a promise, so the cover email mattered as much as the doc.

## Decision
A lead skill (`consulting-lead`) and five subagents, run on demand per client, in two passes.

| Member | Model | Why this tier |
|---|---|---|
| discovery-synthesizer, proposal-architect, pricing-analyst | Sonnet | Drafting and judgment |
| fact-checker, confidentiality-reviewer | Haiku | Narrow checks on top of code |
| cover email | existing `drafter` (Sonnet) | One place for email tone and edit learning |

1. **One batch of questions.** Pass 1 writes a single `<Client> - Questions` doc (at most 12, each with a recommended default; blank means accept). Pass 2 builds the proposal. Gaps found in pass 2 go back to that doc, never into the proposal as `[CHECK]`.
2. **Code gates before model judgment.** `jobs/lib/facts.py` keeps a fact table (`key, value, source`), turns same-key disagreements into questions, and fails any proposal with an untraced number, an open conflict, a `[CHECK` marker, an em dash, or a cross-client term. Models check claims in words; code checks numbers.
3. **The agent never picks a fee.** `jobs/lib/pricing.py` computes cost-basis ranges from her rate (private `Pricing` doc, no default) and estimated hours, next to the client's anchors, budget, and scope levers. The output is a question.
4. **Client firewall.** Other clients' names, people, products, and figures come from the private Lane Context at runtime and are scanned for in every output (`jobs/lib/confidential.py`), plus a Haiku review for paraphrases and positioning. Overlap between clients is always a question.
5. **Relationship first.** The cover email opens with the person and the call, owns a missed date in one line, frames the doc as a starting point, carries no fees, and offers 3 call times from `slots.find_slots` (weekdays, protected blocks respected, nothing booked).
6. **On demand only.** The capture routine flags a returned questionnaire in the review doc; it never starts the workforce.

## Consequences
- Two touches per proposal instead of a dozen: answer the batch, then review the finished doc and draft.
- Pricing, IP and legal terms, and anything about another client cannot reach a draft without her written answer.
- The number extractor only sees money, percents, and counts with a unit. Claims in words rely on the Haiku fact-checker.
- Out of scope for v1: SOWs, contracts, invoices, deliverables. They can reuse the same gates.
- Eval: `evals/consulting/` (synthetic version of the 2026-10-09 case), scored by `python3 -m evals.score_consulting`.
