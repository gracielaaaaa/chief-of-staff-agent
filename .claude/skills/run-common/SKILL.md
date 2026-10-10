---
name: run-common
description: Shared start and finish steps for every scheduled job (kill switch, dry run, Drive lookup, Run Log, failure alert, review doc). Every job skill follows this first.
---
# Run protocol (every job)

## Start
1. Read `config.json`. Note `DRY_RUN` (env var or `dry_run`). In dry run, never call a write tool; print `WOULD ...` lines instead. The guardrail hook also blocks writes, so a blocked write in dry run is expected, not an error.
2. **Kill switch.** If `paused: true`, stop. Otherwise search Gmail: `from:me subject:"PAUSE AGENT" newer_than:30d` and `from:me subject:"RESUME AGENT" newer_than:30d`. If the newest of these is a PAUSE, stop. When stopping, log `paused` (step 4) and do nothing else.
3. **Resolve Drive objects by name, never hardcode IDs.** Search Drive for the folder titled `drive.root_folder_name` (`mimeType = 'application/vnd.google-apps.folder'`, `owner = 'me'`), then for each file in `drive.files` and each folder in `drive.folders` with `parentId` = that folder. If the root folder is missing, fail with "run the setup skill". Then record where files may be created: `python3 -m jobs.lib.folders set <root id> <each folder id> <each subfolder of Consulting>`. The guardrail blocks any Drive `create_file` (or move) whose parent is not on this list, and blocks all of them if the list is missing.
4. **Gmail labels.** In search queries use label NAMES (`label:Agent/Inbox`); searching by label id silently returns nothing (found 2026-10-08). Label ids are only for `label_thread` / `unlabel_thread`: call `list_labels` once to map names to ids for those calls.
5. **Run id** = `<job>-<UTC timestamp>`. Get every timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`; never write one from memory. Read `_State` tab `meta` for this job's last-run cursors.

## Logging
Append rows to `Run Log` tab `runs` with columns: `run_id, ts, job, step, source, action, object_id, dedupe_key, status, note`. Batch rows and append once per step, not once per call. Do not put student names, grades, or email bodies in `note`.

## Dedupe
Before any create: compute the key (`kind:sha256(kind|source_id|parts)[:16]`; run `python3 -c "from jobs.lib.dedupe import key; print(key('task','<src>','<text>'))"`). Skip if the key exists in `_State` tab `processed`. After a successful create, append `key, kind, source_id, object_id, created_ts` to `processed`.

## Failure
If any connector call fails with an auth, permission, or server error (not a guardrail block):
1. Stop the job. Do not retry more than once.
2. Append a Run Log row `status=error` with the tool and error message (no personal content).
3. Create one calendar event on the primary calendar: title `[Agent] FAILED: <job>: <short reason>`, start = now rounded up to the next 5 min, 5 min long, transparency `transparent`, popup reminder at 0 min. Dedupe key `alert|<job>|<date>` so a job alerts at most once per day.
4. If the failing connector is Calendar itself, write the failure into today's review doc header and end.

## Finish: the review queue
If the run created or found anything Graciela should look at, update today's review doc `Chief of Staff/Review/Review YYYY-MM-DD`. Render it with `python3 -m jobs.lib.review '<json>'` (never hand-write the HTML): if the doc does not exist, create it from that HTML with Drive `create_file` (text/html); if it exists, NEVER read it back with `read_doc` (it grows past the read limit). Instead append this run's block to the end with Docs `update_doc` `insertText` at `endOfSegmentLocation`, using the plain text from `python3 -m jobs.lib.review --text '<json>'` (a heading line with the run time, then the sections). One doc per day, always. The popup title comes from `jobs.lib.review.counts`. Sections, in this order:
- `Needs you` (questions and NEEDS_YOU items)
- `Drafts to review` (link, recipient type, subject, `REVIEW BEFORE SENDING` flags first)
- `Booked` (tasks and reminders with times)
- `Ledger changes` (new, closed)
- `Skipped` (notes from non-self senders, excluded items, with a reason)
Then create or update one calendar popup for the run: title `[Agent] <n> drafts, <n> booked, <n> questions`, 5 min at the next free 5-minute mark within working hours (or 8:00 next morning if outside), transparent, 0 min popup, description = review doc link. Dedupe key `popup|<run_id>`.

Write `meta` cursors last, only after everything else succeeded, so a failed run is retried next time. **Advance cursors on quiet runs too** (nothing new is still a success); otherwise every run re-reads the same threads. Update the existing `meta` row for a key (find its row with `get_values`) instead of appending a duplicate.
