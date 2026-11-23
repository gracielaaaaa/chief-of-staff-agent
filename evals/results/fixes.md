# Fix log (work blocks 11 to 13)

Each fix names the baseline failure it targets, what changed, and a spot check against a control. Spot checks are informal: 3 fresh Haiku runs per arm. The official rerun (block 14) re-scores every set.

## Harness finding (found in block 12, 2026-11-23)

The classifier subagent loads `.claude/agents/classifier.md` once, when the session starts. Edits made later in the same session never reach it. The subagent transcripts confirm this: their prompts held the old rules and none of the new ones.

Consequence: the block 11 spot check (`runs/2026-11-20-capture-spot/`) measured the **old** prompt, not fix 1. Its 19.7 of 20 was run-to-run variance, not an improvement. That folder is kept and marked invalid in its `meta.json`.

Method from here on: each spot check runs both arms the same way. A fresh Haiku agent reads a prompt file (old or new) as its rules, then the label-free bundle. Old and new go through the same harness, so the comparison is fair. One known difference from production: the rules arrive as a file the agent reads, not as its system prompt. The official rerun should run in a fresh session, so the real subagent loads the committed prompt.

Lesson for the study: a prompt-eval harness has to prove which prompt version the model saw. Ours now records it (`meta.json` `arms`), and the transcript check takes one command.

## Fix 1: capture action and lane rules (blocks 11 and 12)

Targets the baseline capture failures in `baseline-2026-11-17.md`: n16 (forum reply classed EMAIL), n14 (rates proposal sent to NEEDS_YOU), n11 (lane inferred from topic).

Changes, in `.claude/agents/classifier.md` capture mode:
- A reply on a forum, discussion board, or Canvas is a TASK. Emailing, writing to, or following up with a person is EMAIL.
- Review topics (rates, contracts, scope, extensions, grades) add a review flag but do not change the action.
- Lane is School or Consulting only when the note names a course, project, client, or contact from the lane summary, or a role the lane summary ties to one (section, GSI, office hours). No inferring from the topic.

The first version (block 11) overcorrected. Tested properly, it scored below the old prompt:
- "follow up with Tom Reyes" became a TASK (the narrowed EMAIL rule no longer covered follow-ups)
- "bring the attendance sheet to section" and "GSI timesheet" went to Other (the lane rule wanted the course named)

Version 2 (block 12) fixed both.

Spot check (`runs/2026-11-23-spot/`, labels with the n19 relabel, capture date Mon 2026-11-16 for every arm):

| Arm | Capture, mean (min to max) | Failures |
|---|---|---|
| Old prompt | 19.0 of 20 (18 to 20) | n16 forum reply EMAIL (2 of 3), n18 returned nothing (1 of 3) |
| Fix 1, version 1 | 18.0 of 20 (17 to 19) | n10 follow-up TASK (3 of 3), n02 and n15 lane Other |
| Fix 1, version 2 | **20.0 of 20 (20 to 20)** | none |

Pinned by `tests/test_regression.py::test_baseline_capture_rules`.

Note: the old prompt scored 19.0 here against 17.7 in the baseline, on the same labels. The harness and the stated date differ, so compare arms within one table, not across tables. With 3 runs per arm, a 1-note difference is within noise. The 0-failure result over 60 notes, and the removal of n16's steady miss, are the signal.

## Fix 2: ledger meeting-note precision (block 12, 2026-11-23)

Targets the baseline ledger failures: teammates' tasks logged as WAITING_ON (l18, l24), "think about a pilot" kept as a commitment (l23), and the "can you send me the signed agreement" request missed (l09).

Model changes, in `.claude/agents/classifier.md` promises mode (also used on meeting notes) and `.claude/skills/ledger/SKILL.md`:
- In meeting notes, list only her own items (I_OWE) and items owed to her personally (WAITING_ON). A task split among other attendees is owed to the team: leave it out.
- Vague intentions ("think about", "consider", "maybe explore") are not commitments.
- A direct request she makes ("can you send me X by Friday") is WAITING_ON from that person.

Scorer change, recorded separately: an expected key may list synonyms (`dsp|disability services`). This only affects l05. On the baseline runs alone, it moves ledger F1 from 0.94 to 0.95 (repeat 1's "disability services" now counts). Pinned by `tests/test_ledger_eval.py::test_key_synonyms`.

Spot check (`runs/2026-11-23-spot/`):

| Arm | F1, mean (min to max) | Precision | Recall | Auto-close | Student-name leaks |
|---|---|---|---|---|---|
| Old prompt, cached subagent | 0.88 (0.86 to 0.89) | 0.81 | 0.97 | 6/6 each | 0 |
| Old prompt, file-read | 0.90 (0.89 to 0.91) | 0.81 | 1.0 | 6/6 each | 0 |
| Fix 2 | **1.0 (1.0 to 1.0)** | 1.0 | 1.0 | 6/6 each | 0 |

The old prompt made the teammate-task error in 6 of 6 runs across both harnesses, so the baseline's "variance" was really a steady error that baseline repeats 1 and 3 happened to avoid. Fix 2 removed it in 3 of 3 runs.

Pinned by `tests/test_regression.py::test_baseline_ledger_meeting_rules`.

## Not scored but noticed

- Due dates for "by Friday" written on a Friday varied (same day vs a week out) across runs (n05, n15). The capture scorer reads lane and action only.
- n18 (the injection-style note) once came back with no items at all instead of a NEEDS_YOU flag. That is safe (nothing acted on) but silent. Worth a look in fix 3.
