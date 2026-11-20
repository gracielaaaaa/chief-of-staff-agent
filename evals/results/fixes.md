# Fix log (work blocks 11 to 13)

Each fix names the baseline failure it targets, what changed, and a spot check. Spot checks are informal; the official rerun (block 14) re-scores every set with 3 repeats.

## Fix 1: capture action and lane rules (block 11, 2026-11-20)

Targets the baseline capture failures in `baseline-2026-11-17.md`: n16 (forum reply classed EMAIL), n14 (rates proposal sent to NEEDS_YOU), n11 (lane inferred from topic).

Changes, all in `.claude/agents/classifier.md` capture mode:
- "reply/write to X" is EMAIL only when the reply is an email. A forum, discussion board, or Canvas reply is a TASK.
- Review topics (rates, contracts, scope, extensions, grades) add a review flag but do not change the action.
- Lane is School or Consulting only when the note names a course, project, or client. No inferring from the topic.

Pinned by `tests/test_regression.py::test_baseline_capture_rules` (text pins: a prompt edit that drops a rule fails the test).

Spot check (`runs/2026-11-20-capture-spot/`, 3 fresh Haiku runs, labels with the n19 relabel):

| | Baseline (relabeled) | After fix 1 |
|---|---|---|
| Capture, mean (min to max) | 17.7 of 20 (17 to 18) | 19.7 of 20 (19 to 20) |
| n14 rates proposal | NEEDS_YOU in 1 of 3 | TASK in 3 of 3 |
| n11 article lane | School in 3 of 3 | Other in 3 of 3 |
| n16 forum reply | EMAIL in 3 of 3 | TASK in 2 of 3 |

Read: the lane and review-topic rules held in every run. The forum-reply rule helped but is not reliable yet: one run still classed "reply to two classmates on the PH 220 forum" as EMAIL. A possible next step is a deterministic check (an item that mentions a forum, discussion, or Canvas cannot be EMAIL), the same pattern the regression suite uses elsewhere. Not done in this block; recorded for the rerun.

Not scored but noticed: due dates for "by Friday" on a Friday varied (Nov 20 vs Nov 27) across runs (n05, n15). The capture scorer reads lane and action only.
