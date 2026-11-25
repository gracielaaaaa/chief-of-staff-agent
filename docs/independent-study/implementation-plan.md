# MBA 293 Independent Study: implementation and evaluation plan

Week 2 deliverable. Fall B 2026 (Oct 26 to Dec 18). Path 2: a new project built on MBA 290T foundations.

## Research question
What do synthetic evaluations of an agent miss that real-world runs catch, and can a targeted test suite close that gap?

## Starting point (baseline, built before Oct 26, not for credit)
- A scheduled Claude agent (this repo) that captures to-dos, drafts email for review, tracks commitments in a ledger, and learns from edits. It never sends; a pre-tool hook enforces that in code.
- Existing evals: 20 capture notes, 10 needs-reply threads, 8 edit pairs, 1 consulting case, and 60 unit tests on helpers and the guardrail hook.
- `docs/issues-found.md`: 28 failures found by real-data dry runs. None was caught by the synthetic evals.
- No test of whether the model resists instructions planted in the content it reads.

## New work (Oct 26 onward)
1. **Regression suite** (`evals/regression/`). One synthetic case per issue in `issues-found.md` that can be reproduced offline. Deterministic failures (slots, quote stripping, dedupe, sensitive filters, guardrail) become unit tests; model-behavior failures (classification, promise detection, financial errands) become scored eval cases. Each issue gets a status: covered, partly covered, or not reproducible offline (with the reason). That list is part of the answer to the research question.
2. **Prompt-injection red-team set** (`evals/injection/`). About 30 attacks across channels (email body, quoted thread, Drive doc, meeting transcript, calendar description, a capture note from a non-allowed sender, forwarded text inside an allowed note) and goals (send or forward mail, share a file, delete, exfiltrate sensitive data, change a rule, write to Canvas, invent a ledger item). There are also 10 benign look-alikes to measure false positives. Two layers are scored separately: the model layer (does the agent attempt the action) and the hook layer (does `guardrail.decide` block the resulting tool call).
3. **Ledger set** (`evals/ledger/`). About 25 synthetic meeting notes and sent-mail snippets with labeled commitments, including hard negatives (same-day logistics, other people's promises) and closures.
4. **Scorecard runner** (`python3 -m evals.scorecard`). One command that runs all scorers and writes `evals/results/scorecard-<date>.md` with model id, prompt version, and run date. Model calls follow the repo routing: Haiku for classification, Sonnet for drafting.

## Metrics and targets
| Metric | Source | Target |
|---|---|---|
| Real-data issues reproduced offline | regression suite | 20 of 28 or more |
| Regression cases passing | regression suite | 100% after fixes |
| Capture classification accuracy | `evals/notes.jsonl` | 18 of 20 or more (existing bar) |
| Ledger precision and recall | ledger set | 90% or more each |
| Injection attack success, model layer | red-team set | 0 on high-risk goals, under 10% overall |
| Hook block rate on attempted actions | red-team set | 100% |
| Benign false-positive rate | red-team look-alikes | under 10% |
| Draft edit ratio | `evals/edit_pairs.jsonl` | report only (baseline comparison) |

## Evaluation protocol
1. Baseline scorecard (week 4): run every set 3 times and report the mean and spread, because model output varies.
2. Inspect failures, then fix the 3 weakest areas (prompt, code, or hook).
3. Rerun and report before and after.
4. Round 2: write about 10 new injection attacks after the fixes are made, so the final number is not measured on cases the fixes were tuned to.

## Data
All test data is synthetic, built on the persona in `evals/persona/`. No real email, client material, or student data. Hours count only for building, testing, documenting, and learning about the agent, not for paid GSI or consulting work done with it.

## Foundations from MBA 290T
Evaluation design (labeled sets, precision and recall, held-out round), LLM behavior (prompt injection, nondeterminism), agent tools (tool permissions, pre-tool hooks), workflow design (draft-first, human review), and software systems (tests, reproducible runs).

## Expected limitations
Small sets, so results are directional. Cases are self-authored, so the red-team may miss attacks a stranger would try. Some failures depend on live connectors (for example, how Gmail handles label ids) and cannot be reproduced offline. That gap is the finding, not a defect of the plan.

## Schedule
| Week | Dates | Work | Deliverable |
|---|---|---|---|
| 1 | Oct 26 to Nov 8 | Scope, baseline review | Project description |
| 2 | Nov 9 to 15 | Regression suite, red-team set | This plan |
| 3 | Nov 16 to 22 | Scorecard runner, ledger set, baseline run | Midpoint update (Nov 20) |
| 4 | Nov 23 to Dec 6 | Fixes, rerun, injection round 2, final run | Results tables |
| 5 | Dec 7 to 18 | Delivery note, README, hours log | Final submission (by Dec 15) |
