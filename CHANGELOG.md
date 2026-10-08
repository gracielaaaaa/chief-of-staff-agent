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
