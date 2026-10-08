---
name: ledger
description: F3 "I owe" ledger. Drafts recaps and records action items from new Granola meetings, detects promises in sent mail, and closes items when matching sent mail appears. Runs inside the capture routine.
---
# Ledger

Cursors in `_State` `meta`: `granola_last_ts`, `sent_last_ts`. **First run (no cursor): look back 7 days only.** Older meetings and mail go into one `Needs you` line ("N older meetings not scanned; ask me to backfill"), never into the ledger.

## A. New meetings (Granola)
1. `list_meetings` since `granola_last_ts`. Keep meetings with at least one attendee outside her own address. Granola's participant list is often incomplete (a client retreat showed only her), so also keep meetings whose notes name other people or a client; skip only clear solo notes.
2. `get_meetings` for those ids (max 10 per call). Extract action items **she owns** and items others owe her.
3. For each: Ledger row (I_OWE or WAITING_ON), key `ledger|<meeting id>|<what>`, due as stated or +3 business days, `source` = Granola note URL. I_OWE items get a TASK before due (dispatcher TASK rules) and, if the deliverable is an email, a draft.
4. Client meetings (Consulting lane): one recap draft via `drafter` (`kind: recap`), key `recap|<meeting id>`.

## B. Sent-mail promises
1. Gmail search `in:sent after:<sent_last_ts>` (cap 50). Drop `jobs.lib.promises.is_automated` messages, `excluded` ones, and any to or from a `jobs.lib.sensitive.sensitive_sender` or with a sensitive subject, before any model call. Strip quoted history (`jobs.lib.diff.strip_quoted` semantics). Skip student threads for promise storage unless the promise is about a non-grade deliverable, and never store the student's name (`who = "student"`).
2. `classifier` subagent, mode `promises`.
3. Pass every item through `jobs.lib.promises.redact_who` (privacy backstop) and `triage` (past-due on first run becomes a `Needs you` confirmation, not a row). New Ledger rows, key `ledger|<message id>|<what>`, `source` = sent message link.
4. Before adding a row, look for a later sent message in the same thread that fulfills it (for example the grades actually sent). If found, add it with `status=done` so the close rate counts it.

## C. Auto-close
For each open I_OWE row: look for sent mail to `who` after `created` whose content matches `what` (same thread as the source, or a subject/body match). If found, set `status=done`, `closed=<ts>`, and list it under `Ledger changes`. If unsure, leave it open and add a one-line question to `Needs you` ("Did you send X to Y?").

## D. Surface
Open I_OWE items due in 48 hours or overdue go into the review doc under `Needs you`, oldest first.

Update `granola_last_ts` and `sent_last_ts` last.
