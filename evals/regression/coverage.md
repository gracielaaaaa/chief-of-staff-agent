# Regression coverage of real-data issues

Source: `docs/issues-found.md`, which lists the failures found by real-data dry runs. The synthetic evals caught none of them. This table records how each issue can now be caught offline.

Layers: **code** = deterministic test in `tests/test_regression.py`. **model** = scored case in `model_cases.jsonl` (needs a model run; scored by `evals/regression/score.py`). **text** = a test that pins the prompt rule, so an edit cannot silently drop it. **connector** = depends on live Gmail, Drive, or Calendar behavior and cannot be reproduced offline.

| # | Issue (short) | Status | Layers | Notes |
|---|---|---|---|---|
| 1 | "Inbox" label reserved | covered | code | Config labels checked against Gmail's reserved names |
| 2 | Drive connector could not edit after create | partly | code, connector | Hook allows the Sheets and Docs edit tools; the connector limit itself is live-only |
| 3 | Block list missed "clear all values" | covered | code | Unknown and destructive tool names blocked by default |
| 4 | Gmail search needs ids, not names | partly | text, connector | Live behavior; later reversed by issue 25. The written rule is pinned |
| 5 | Phone address skipped as non-self | covered | code, text | New `jobs.lib.filters.accepted_sender`; skills now call it. Lookalike senders rejected |
| 6 | Class already on calendar booked again | model only | model | Matching is a judgment call ("arrive at Hele's" = "pilates with Helena"); 4 cases |
| 7 | Two tasks in the same slot | covered | code | Three bookings in one run never share a start |
| 8 | Call booked before the business opened | covered | code | Business-hours window |
| 9 | `-label:` exclusion ignored by Gmail | covered | code, text | New `jobs.lib.filters.has_any_label`; skills now call it |
| 10 | Wrapped "On ... wrote:" not stripped | covered | code | Wrapped attribution plus a 40 KB history |
| 11 | Deleting the review flag counted as an edit | covered | code | Edit ratio 0 when only the flag is removed |
| 12 | Student name in a ledger row | covered | code, model | Code backstop `redact_who` plus 2 model cases |
| 13 | Same-day logistics counted as promises | covered | model, text | 4 negatives, including quoted text and decisions already made |
| 14 | "I need to" obligations lost | covered | model, text | 4 positives, including the exam deadline |
| 15 to 28 | | pending | | Block 4 (Nov 10) |

## Summary so far (issues 1 to 14)
- Covered: 11 (issues 13 and 14 need a model run to score). Partly covered: 2 (issues 2 and 4, whose connector half cannot be reproduced offline). Model only: 1 (issue 6).
- Finding: 2 of the fixes (issues 5 and 9) existed only as prose in a skill, with no code a test could check. They are now code. That is the pattern this study looks for: rules enforced only by prompt are the ones a synthetic eval cannot catch regressing.
