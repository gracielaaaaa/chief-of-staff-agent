# MBA 293 hours log

Target: 45 hours, Oct 26 to Dec 18, 2026. Only work done for the independent study counts. Entries are dated by when the work was done; some blocks were finished ahead of their scheduled dates in `work-schedule.md`.

| Date | Hours | Category | Activity |
|---|---|---|---|
| 2026-11-03 | 1.0 | Project selection and problem definition | Chose the path (new project on MBA 290T foundations), reviewed the baseline system and its 28 real-data issues, drafted the project description |
| 2026-11-03 | 1.5 | Implementation | Built two agent capabilities: escalation of overdue commitments with a holding-note draft, and a multi-agent team (lead plus specialist subagents) for long-form drafting |
| 2026-11-03 | 0.25 | Documentation and submission | Sent the project description to the faculty sponsor (approved) and asked about the certificate steps |
| 2026-11-09 | 3.0 | Implementation | Regression set for real-data issues 1 to 14: 13 regression tests, 14 model-layer cases with a scorer, coverage table; moved two prompt-only screens into tested code |
| 2026-11-09 | 2.75 | Research and design | Reviewed and finalized the implementation and evaluation plan and its email to the faculty sponsor |
| 2026-11-09 | 2.0 | Implementation | Regression set for real-data issues 15 to 28: 14 more tests, 6 model cases, full coverage table (25 of 28 reproducible); found and fixed a secrets-scan gap |
| 2026-11-11 | 2.0 | Testing and evaluation | Prompt-injection red-team set: 32 attacks across 9 channels and 10 benign look-alikes, labeled by which layer should stop each one |
| 2026-11-12 | 2.0 | Testing and evaluation | Red-team harness: end-to-end scoring in the live agent's layer order (sender filter, model, hook), model prompts, over-refusal checks; naive and safe reference agents pinned in tests |
| 2026-11-15 | 2.0 | Testing and evaluation | Scorecard runner: one command for all checks, dated report, mean and spread over repeated model runs, needs-reply scorer; validated against the Oct 7 v0 predictions |
| 2026-11-16 | 2.0 | Testing and evaluation | Ledger eval set: 25 extraction cases (20 commitments, 8 hard negatives) and 6 auto-close cases, scorer for precision, recall, due dates, student-name leaks, and closure; added to the scorecard |
| 2026-11-17 | 2.0 | Testing and evaluation | Baseline scorecard run: label-free input bundles, 3 repeats of each model set, failure inspection, three weakest areas chosen for the fix blocks |

Categories (from the study plan, with planned hours): project selection and problem definition (4), research and design (6), implementation (20), testing and evaluation (10), documentation and submission (5).

**Total so far: 20.5 of 45**
