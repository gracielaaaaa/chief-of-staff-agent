---
name: edit-learner
description: F5 learn from edits. Matches drafts to what was actually sent, computes edit ratios, proposes scoped style rules, activates rules after 2 sightings, and records metrics. The nightly `learn` routine.
---
# Edit learner

Follow `run-common` Start.

1. **Match.** For each `_State` `drafts` row with `status=open` created more than 1 hour ago: find a sent message in the same `thread_id` after `created`, else one to the same recipients with a similar subject within 7 days. Check the draft still exists (`get_draft`).
2. **Score.** For each match run `python3 -m jobs.lib.diff '{"draft": ..., "sent": ...}'`. Update the row: `status=sent`, `edit_ratio`, `matched_message_id`.
3. **Reject.** Open drafts older than `draft_rejected_after_days` with no match: `status=rejected`. If she wrote something else in the thread, note the probable reason in one line.
4. **Learn.** Send all newly scored pairs with `edit_ratio > 0.05` to the `edit-learner` subagent in one batch, with the current Style Guide rules.
5. **Rules.** For each candidate rule, find an existing `observations` row with the same meaning and scope. If found, increment `evidence_count` and update `last_seen`, else add it as `candidate`. When `evidence_count >= style_rule_activation_count`, set `status=active` and add it to the Style Guide under `Active rules` as `- <rule> (scope: <scope>, seen <n>x)`. If it `contradicts` an active rule, move the old rule to `Retired`.
6. **Metrics.** Append to `Run Log` `metrics` for the current ISO week: `drafts_scored`, `avg_edit_ratio`, `light_edit_share` (ratio < 0.20), `rejected`, plus Ledger `i_owe_closed_on_time` and `i_owe_open_over_7d`. Aggregates only.

Weekly (Sunday run): consolidate the Style Guide (merge duplicates, retire contradicted rules) and write the top 3 changes in the review doc.

Finish with `run-common` Finish (no popup unless a rule was activated or something failed).
