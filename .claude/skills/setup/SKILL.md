---
name: setup
description: Idempotently creates the Chief of Staff Drive folder, sheets, docs, and Gmail labels, and maps protected calendar colors. Run once, safe to re-run. Supports DRY_RUN.
---
# Setup

Follow `run-common` Start step 1 only (no kill switch, no Run Log until it exists).

1. **Folder.** Search Drive for a folder titled `Chief of Staff` owned by me. Create it only if missing. Inside it create any missing folders from `config.drive.folders`.
2. **Sheets** (create with Drive `create_file`, mime `application/vnd.google-apps.spreadsheet`, parent = root folder, then set tabs and headers with the Sheets connector):
   - `Ledger`, tab `items`: `id, type, lane, client_or_course, what, who, due, source, status, draft_link, created, closed`
   - `Run Log`, tab `runs`: `run_id, ts, job, step, source, action, object_id, dedupe_key, status, note`; tab `metrics`: `week, metric, value, note`
   - `_State`, tabs: `processed` (`key, kind, source_id, object_id, created`), `drafts` (`draft_id, message_id, thread_id, to, recipient_type, subject, body, created, lane, flags, status, edit_ratio, matched_message_id`), `observations` (`id, rule, scope, evidence_count, examples, status, first_seen, last_seen`), `meta` (`key, value`)
   Freeze row 1 on every tab. Write headers as plain strings (`RAW`), never parsed.
3. **Docs** (mime `application/vnd.google-apps.document`): `Look Into Later` (headings School, Consulting, Other), `Style Guide` (headings Active rules, Candidates, Retired), `Lane Context`, `Pricing` (headings Rate or floor, Philosophy, Past deals; filled by Graciela, read only by `consulting-lead` step 4), `Consulting Templates` (headings Questionnaire, Proposal; structure only, no client content).
4. **Lane Context content.** If `Lane Context` is empty, fill it from the private source Graciela provides in chat (or `SPEC.md` section 7 when running locally). This doc holds the real people, courses, and clients. It never goes into the repo.
5. **Gmail labels.** ("Inbox" is a reserved Gmail name, so everything lives under `Agent/`.) Create `Agent/Inbox`, `Agent/Done`, `Agent/Skipped` if missing.
6. **Protected colors.** List the primary calendar's events for the last 30 days. Report which `colorId`s appear with sample titles, and ask Graciela which are blue, purple, and yellow. She sets `config.protected.color_ids`. (Calendar color ids 7 Peacock, 9 Blueberry, 3 Grape, 5 Banana are the usual matches, but confirm with her.)
7. **Print the Gmail filter steps** for Graciela (she creates the filter herself; the agent never creates standing rules):
   Gmail > Settings > Filters > Create new filter > To: `<her address with +inbox>` > Create filter > Apply the label `Agent/Inbox`, and Never send it to Spam.
8. Record `meta` keys `setup_version=1`, `setup_ts=<now>`.

Report what was created vs. already present, with links.
