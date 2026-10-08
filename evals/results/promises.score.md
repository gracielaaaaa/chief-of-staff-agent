# Promise detection on real sent mail (7 days, aggregates only)

Input: 67 sent messages. Code prefilter removed 18 automated (calendar receipts, emoji reactions, invites) and 1 excluded (employer domain) before any model call. 41 went to Haiku. Ground truth: 7 real commitments, labeled by hand.

| Version | Items returned | Real | Recall | Precision | Student-name leak |
|---|---|---|---|---|---|
| v0 | 11 | 6.5 | 7/7 | ~59% | 1 |
| v1 | 5 | 5 | 5/7 | 100% | 0 |
| v2 | 6 | 6 (two related commitments merged) | 7/7 | 100% | 0 |

What changed:
- v0 to v1: excluded same-day logistics ("I'll be there by 12:20"), statements of decisions already made, and quoted text. Recall dropped: obligations phrased as "I need to..." were lost, including the most important one (a disability-services exam deadline).
- v1 to v2: added obligations ("I need to", "I have to") and promised outcomes that require later action ("you'll receive credit").
- Code backstop (`jobs/lib/promises.redact_who`): any coursework-related recipient who is not an instructor, teammate, or client is stored as `student`, whatever the model says.
- Code triage: on the first run, past-due items become one "did you do this?" question instead of ledger rows.

Raw predictions stay in `evals/real/` (gitignored).
