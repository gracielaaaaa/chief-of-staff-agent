# Changelog

## v0.1.0 (2026-10-07): Phase 0 scaffold
- Guardrail hook: blocks send, forward, reply, delete, trash, share, invite responses, Canvas writes, and structural Sheet/Doc deletes. Blocks all writes in dry-run and paused modes. 17 unit tests.
- Deterministic helpers: free-slot finder (working hours, protected calendar colors, office hours), edit ratio (quoted history stripped), dedupe keys.
- Skills: setup, dispatcher, drafter, ledger, edit-learner, canvas-sync, lane rules, shared run protocol.
- Subagents: classifier (Haiku), drafter and edit-learner (Sonnet).
- Eval v0: capture classification 20/20 on the synthetic set, including a prompt-injection note correctly routed to "needs you".
- ADRs 0001 to 0006.

## v0.1.1 (2026-10-08): setup run, guardrail allow list
- Guardrail switched from a block list to an allow list: only reads and 17 named write tools pass. New connectors (or new tools on existing ones) are blocked by default. Found because attaching the Sheets connector added `batch_clear_values`, which the block list missed. 18 unit tests.
- Setup ran for real: Drive folder, Ledger, Run Log, _State (4 tabs), Style Guide, Lane Context, Look Into Later, Gmail labels.
- Capture label renamed to `Agent/Inbox` (Gmail reserves "Inbox"). Skills resolve label ids before searching.

## v0.1.2 (2026-10-08): first real-note dry run
Ran the dispatcher dry-run on a real phone note (3 items: an errand, a fitness class, a restaurant follow-up). Classification was correct on all 3. Found and fixed 4 issues the synthetic evals missed:
- **Sender allowlist.** The note came from the phone's personal mail, so "self only" would have skipped it. Notes are now accepted from a private list of the owner's addresses.
- **Duplicate events.** The class was already on the calendar under a different title. Dispatcher now checks nearby events before booking.
- **Same-run collisions.** Two tasks were booked into the same 8:00am slot. Slots booked in a run now feed the next search (new test).
- **Business hours.** Calls and errands were scheduled before businesses open. Slot finder takes a time window (new test). 20 unit tests.

## v0.1.3 (2026-10-08): cloud verified, first live booking
- Cloud routine connector check passed: Gmail, Calendar, Drive, Sheets, Docs, Granola all reachable; 20/20 tests; guardrail hook active in the cloud (blocked `send_message`, exit 2). Cloud tool prefixes (`mcp__Gmail__...`) differ from local ones, which the suffix-based guardrail handles.
- First live run on a real note: 2 events booked, 1 skipped as already on calendar, note labeled done, all actions in the Run Log with dedupe keys.

## v0.2.0 (2026-10-08): inbox triage (needs-reply drafts)
Pulled forward from Phase 2 at the owner's request: the agent scans the inbox and drafts replies to real people who are waiting on her.
- First live run: 9 threads, 7 after code filters, 3 flagged by Haiku as needing a reply, 2 drafted (student accommodation question, instructor follow-up), 1 skipped as a probable false positive ("let's discuss after class").
- Fixes from the run: Gmail ignores `-label:` with ids in search, so filters run in code; wrapped "On ... wrote:" attributions are now stripped (a 40KB thread became 3 lines); accommodation and health requests get a dedicated never-decide rule; student names are redacted in the learning log.
- New eval set `evals/needs_reply.jsonl` (10 cases, synthetic, includes the false-positive pattern).
- Step flags in config: course deadlines and ledger stay off until their own dry runs pass.

## v0.3.0 (2026-10-08): Canvas sync
- Weekly local sync (Sundays 4pm, laptop) of the next 14 days of her own student coursework into `Courses/Upcoming`. Teaching and TA courses are excluded: no rosters, submissions, or grades leave Canvas.
- Tested helpers: Canvas UTC to Pacific (Oct 13 06:59Z is Mon Oct 12 11:59pm; DST-aware), prompt HTML cleanup, and daily digest grouping. 26 unit tests.
- **Product decision:** graded coursework gets outlines and work blocks, never full drafts (academic integrity; course AI policies vary). Diverges from the original spec on purpose.
- **Product decision:** one 9am digest popup per day instead of one popup per deadline (the spec rule would have meant 4 popups on one Saturday).
- First sync: 11 items across 4 courses, 10 not submitted.
- Per-course AI policy (kept in the private Lane Context doc): AI courses get full drafts, all other graded work gets outlines. Large technical projects are routed to a dedicated build session instead of the scheduled agent.
- Course step turned on for cloud runs after the first live run: 5 digest popups, 1 outline, 2 work blocks.

## v0.4.0 (2026-10-08): learn routine
- Edit ratio ignores the agent's own `REVIEW BEFORE SENDING` line (deleting it was being counted as an edit).
- Tested helpers for weekly metrics, 7-day rejection, and rule activation (2+ sightings or owner confirmation). 30 unit tests.
- Edit-learner eval on 8 synthetic pairs: v0 found 5/5 planted habits but invented 1 false rule and 12 rules total; v1 (prompt excludes placeholder fills and fact fixes, one idea per rule) found 4/5 with 0 false rules. Shipped v1: precision over recall for rules that change every future draft.

## v0.5.0 (2026-10-08): ledger dry run on real meetings and sent mail
- Promise detection: v0 59% precision with a student-name leak; v2 7/7 recall, 100% precision, no leaks (see `evals/results/promises.score.md`).
- Code prefilter drops automated sent mail (18 of 67 messages) before any model call; code backstop redacts student names; first-run backlog limited to 7 days with past-due items turned into one confirmation question.
- Found that Granola participant lists can be incomplete (a client retreat listed only the owner), so the meeting filter also reads the notes.
- Ledger live: 8 rows from the first run (6 open, 2 auto-closed because the matching sent mail already existed), 4 work blocks, 1 reminder, 1 flagged student draft.
- Scheduling fixes found while booking: earliest-fit packed four tasks into one morning (now searches a 3-day lead window before each deadline), and Google marks focus time as "free" (her focus blocks now count as busy). 37 unit tests.

## v0.5.1 (2026-10-08): first scheduled cloud run
- 8am run succeeded in 63 seconds: kill switch, Drive and label lookup, inbox scan; one recruiting blast correctly dropped (not on To/CC).
- The agent flagged a conflict on its own: the routine prompt still said two steps were off while `config.json` had them on. Fixed by making the prompt defer to config.
- Cursors now advance on quiet runs; timestamps come from the system clock, not the model (one was off by an hour).

## v0.5.2 (2026-10-08): review doc renderer
- The daily review doc is rendered by tested code (`jobs/lib/review.py`): fixed section order, flagged drafts first, HTML escaped, em dashes rejected. 40 unit tests.
- Needs-reply eval: 10/10 on the synthetic set (a regression check after the real-mail false-positive fix, not an unbiased estimate).

## v0.5.3 (2026-10-08): recap fact-check
- Recap acceptance test (5 past client meetings, offline): the drafter reported 30/30 action items covered. An independent fact-checker, confirmed by hand, found 1 open question listed as a task, 1 finding listed as a decision, 1 owner assigned without support, 1 date pulled from another meeting, 1 inferred time, and 1 attendee left off the To line. Self-reported coverage overstated quality.
- Drafter now has explicit recap accuracy rules for each of those error types. Owner grading pending.

## v0.6.0 (2026-10-08): financial and credential boundary
- Owner's rule: receipts and invoices are fine; banking, investments, loans (plus tax and payroll, which carry SSNs) are never read. ADR 0007.
- Four layers: Gmail search exclusions, metadata-only skip of sensitive senders and subjects, attachments and downloads blocked by the hook, and a secrets scan on every write (card numbers with Luhn check, SSNs, bank details, one-time codes, passwords).
- False-positive checks: the write scan passes everything the agent has written so far (review doc, recaps, Canvas rows) and common phrases like "bank account details" or "dress code for Oct 2026". 45 unit tests.

## v0.6.1 (2026-10-08): noon run fixes
- First full capture run with every step on: 3 notes (1 skipped as sensitive), 4 events, Forum 8 outline, 2 reply drafts, 1 waiting-on item, review doc, popup.
- Fixed: label searches use names (ids silently return nothing); review doc is appended to, never read back. 46 unit tests.
- Watching: the run ended before finishing the Granola and sent-mail scans (it left those cursors in place, so the next run retries).

## v0.6.2 (2026-10-08): financial errands are tasks
- Owner feedback: a to-do about calling Vanguard and logging in to an HSA was skipped as sensitive. The boundary is account data, not the topic. Errands are booked; only notes containing account data (secrets scan) or forwarded financial emails are skipped. 47 unit tests.
