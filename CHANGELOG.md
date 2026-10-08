# Changelog

## v0.1.0 (2026-10-07): Phase 0 scaffold
- Guardrail hook: blocks send, forward, reply, delete, trash, share, invite responses, Canvas writes, and structural Sheet/Doc deletes. Blocks all writes in dry-run and paused modes. 17 unit tests.
- Deterministic helpers: free-slot finder (working hours, protected calendar colors, office hours), edit ratio (quoted history stripped), dedupe keys.
- Skills: setup, dispatcher, drafter, ledger, edit-learner, canvas-sync, lane rules, shared run protocol.
- Subagents: classifier (Haiku), drafter and edit-learner (Sonnet).
- Eval v0: capture classification 20/20 on the synthetic set, including a prompt-injection note correctly routed to "needs you".
- ADRs 0001 to 0006.
