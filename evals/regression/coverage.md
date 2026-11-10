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
| 15 | First run would backfill a month of stale tasks | covered | code, text | Past-due items become one question; 7-day first-run rule pinned |
| 16 | Granola listed only the owner at a client retreat | covered | model, text | Notes-based filter pinned; 3 model cases (2 keep, 1 solo note) |
| 17 | Earliest-fit packed four tasks into one morning | covered | code | Four deadlines spread across at least 3 days |
| 18 | Focus time marked "free" was booked over | covered | code | Focus time blocks even when transparent |
| 19 | Cloud run followed a stale prompt line over config | covered | text | **Gap found:** the fix lived only in the cloud routine prompt, not in the repo. Added "config.json is the source of truth" to run-common and pinned it |
| 20 | Cursors stuck on quiet runs; a timestamp off by an hour | partly | text | Both rules pinned; real cursor writes are live-only |
| 21 | Meeting connector missing from the cloud routine | partly | text, connector | routines.md must list every connector capture needs; the routine's actual attachments are live config |
| 22 | 12-day-old client promise outside the 7-day lookback | open, not fixed | none | No fix exists yet, so there is nothing to test. Candidate for a fix block |
| 23 | Deleted agent event leaves its ledger item open | open, not fixed | none | No fix exists yet. Candidate for a fix block |
| 24 | One chat for every project overloaded it | not testable | none | Process change (one session per workstream), not system behavior |
| 25 | Search by label id silently returned nothing | partly | text, connector | Rule pinned (names in search, ids only for labeling); the Gmail behavior is live-only |
| 26 | Review doc grew past the read limit | covered | code, text | Plain-text append block; "never read it back" pinned |
| 27 | Her own financial errand skipped as "financial details" | covered | code, model, text | Errands pass the secrets scan; 3 model cases. **Bug found:** the scan missed "my routing number is ..." (only "Routing number: ..." matched). Fixed in `jobs/lib/sensitive.py` |
| 28 | Receipt photos arrive as blocked attachments | partly | code | Attachments and downloads stay blocked; Drive file reads allowed. The "save to Drive?" prompt is still a candidate feature |

## Summary (all 28 issues)
| Status | Count | Issues |
|---|---|---|
| Covered | 18 | 1, 3, 5, 7 to 19, 26, 27 (13 to 16 and 27 also need a model run) |
| Partly covered | 6 | 2, 4, 20, 21, 25, 28 (the connector half is live-only) |
| Model only | 1 | 6 |
| Open, no fix yet | 2 | 22, 23 |
| Not testable | 1 | 24 |

That is 25 of 28 reproducible offline, at least in part (target: 20). Every "partly" is partly for the same reason: the failure came from how a live connector behaves, which no offline test can see.

## Findings
1. **Prompt-only fixes regress silently.** Three fixes (issues 5, 9, and 19) existed only as prose, and one (19) was not even in the repo: it lived in the cloud routine's prompt. Issues 5 and 9 are now code with tests. Issue 19 is now versioned text with a test that pins it.
2. **Writing tests found a live bug.** The regression test for issue 27 showed the guardrail's secrets scan missed account numbers written conversationally ("my routing number is ..."). The guardrail hook uses that scan, so a note like that could have been written to a sheet. Fixed and covered.
3. **Connector behavior is the hard limit.** The 6 partly covered issues all trace to live Gmail, Drive, or routine configuration. Closing that gap needs a recorded-response replay or a live smoke test, not more synthetic cases.
