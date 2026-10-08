# Phase 1 acceptance (from the spec)

Phase 2 (pre-meeting briefs, morning/evening/Sunday digests) starts only when every row below is met **and** Phase 1 has had 1 week of real use (live since 2026-10-08, so 2026-10-15 at the earliest).

| Capability | Criterion | Status | Evidence |
|---|---|---|---|
| F1 Capture | 20 test notes: correct lane and action for 18+ | Met on the synthetic set (20/20) | `evals/results/notes-v0.score.json`. Real-note set to follow once 20 real notes exist. |
| F1 Capture | Zero duplicates on re-run | Met by design, verify in week 1 | Dedupe keys in `_State/processed`; check the Run Log after the first repeated note. |
| F2 Drafts | 8 of 10 drafts rated "send with light edits" | Pending | Needs 10 real drafts sent or rated. 3 created on day 1. Edit ratio measured nightly. |
| F3 Ledger | Recaps on 5 past client meetings capture all action items she agrees with | In progress | `evals/real/recaps-v0.md` (private), rated by Graciela |
| F3 Ledger | 2 weeks of sent mail: 80%+ of real commitments, few false positives | Partly met (1 week): 7/7 recall, 100% precision | `evals/results/promises.score.md` |
| F5 Learning | After 2 weeks, average edit ratio lower than week 1 | Pending (earliest 2026-10-22) | `Run Log/metrics` |
| Ops | No unnoticed failed runs | Met so far | Every run writes a Run Log row; failures create a calendar alert. |
