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
