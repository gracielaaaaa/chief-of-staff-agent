# Consulting workforce eval (synthetic golden case, v0)

Case: `evals/consulting/case.json`, a scrubbed and synthetic version of the 2026-10-09 pilot proposal.

| Check | Before (single drafter) | After (golden output) |
|---|---|---|
| `[CHECK]` markers | 12 | 0 |
| Untraced numbers | 3 (30 participants, 2 workshops, 6 months) | 0 |
| Price conflict (3x) surfaced as a question | no, silently used the call-notes figure | yes, resolved by her answer |
| Other client's product named | yes (positioned against it) | no |
| Gate | blocked | ready |
| Pricing frame contains a fee | n/a | no |
| Cover email: relationship first, doc as starting point, no fees, 3 free weekday slots | n/a | all pass |

This version checks the gates and the scorer with hand-written outputs. **Next:** run pass 1 and pass 2 with the subagents on the case, score with `--questions`, `--proposal`, `--cover`, then dry-run pass 1 on the real prospect and compare its question batch with the original 12 `[CHECK]`s.
