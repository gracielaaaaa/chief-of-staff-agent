---
name: inbox-triage
description: Scans Graciela's inbox for emails from real people that need a reply and writes a draft reply in-thread for each, through the drafter. Runs inside the capture routine. Never sends.
---
# Inbox triage (needs-reply drafts)

Runs after the dispatcher in the `capture` routine. Uses `run-common` (already started by the dispatcher).

## 1. Candidates (plain search, no model)
- Cursor `inbox_last_ts` from `_State` `meta`. If missing (first run), use `newer_than:<config.inbox_triage.first_run_lookback>`; otherwise `after:<cursor as epoch seconds>`.
- Gmail search: `config.inbox_triage.query` with label ids filled in, plus the time clause.
- Gmail search does not reliably honor `-label:` with ids, so apply every filter below in code, on each thread's messages.
- Drop a thread if any of these is true:
  - any message carries the `Agent/Inbox`, `Agent/Done`, or `Agent/Skipped` label (capture notes are the dispatcher's job)
  - the newest message is from one of her addresses (`My addresses` in Lane Context): she already answered
  - the sender matches `skip_sender_patterns`, or `config.exclusions`
  - she is not on To or CC (mailing lists, BCC blasts)
  - a draft already exists in the thread (`list_drafts`, match `threadId`): hers or ours
  - `_State` `processed` already has `reply|<thread id>|<newest message id>`
- Archived or answered threads never appear, which is how Graciela opts out.

## 2. Needs a reply? (Haiku)
Send the surviving threads, last 2 messages each with quoted history removed, to the `classifier` subagent in **mode `needs_reply`**, in one batch. Keep only `needs_reply: true`.

## 3. Draft (Sonnet)
Order by urgency, then `config.inbox_triage.priority`. No per-run cap unless `max_drafts_per_run` is set. For each thread, call the `drafter` skill with `kind: email`, `replyToMessageId` = newest message id, `recipient_type`, and lane. The drafter applies the review flags (instructor, students, rates, contracts, scope, extensions, grades).
- **Accommodations, health, or personal circumstances** (DSP, disability, illness, family emergency): never decide or interpret the accommodation. Draft a warm acknowledgment that says she is confirming with the instructor and gives a follow-up date as `[CHECK: date]`, and remind the student to send their DSP letter to the instructor if they have not. Always flagged. Add a `Needs you` line: "Confirm accommodation with instructor".
- Student emails: draft from that thread only. No promises on extensions or grades. Always `REVIEW BEFORE SENDING`. Never write the student's name to any log or review doc (use `student`).
- If the email asks for something only Graciela knows (a decision, a date, an opinion), draft the reply with `[CHECK: ...]` placeholders and list it under `Needs you`.

## 4. Record
- `_State` `drafts`: for students, store `to=student`, `subject=student thread`, and the body with the student's name replaced by `[student]` (apply the same replacement to the sent text before computing the edit ratio).
- `processed`: `reply|<thread id>|<newest message id>`. A new message in the same thread later gets a new key, so it can be drafted again.
- Run Log row per draft: `action=create_draft`, `object_id=<draft id>`, `note=<recipient_type>, <lane>, flagged yes/no`. No subjects for student threads.
- Review doc `Drafts to review`: flagged first, then by urgency. Each line: recipient type, subject (or `student thread`), Gmail link.
- Update `inbox_last_ts` last.
