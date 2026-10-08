# 0001. Drafts, never sends, enforced in code

Status: accepted, 2026-10-07

## Context
The agent writes email for a GSI and a consultant. One wrong send (to a student, an instructor, or a client, about grades or rates) costs far more than the time saved by auto-sending. Prompt instructions alone are not a guarantee: a model can be talked into things by content it reads.

## Decision
The agent can create and update drafts, calendar events, and files in one Drive folder. It cannot send, forward, reply, delete, trash, share, or accept invites. This is enforced by a `PreToolUse` hook (`.claude/hooks/guardrail.py`) that matches tool names by suffix, so it holds across connector instances whose server ids differ between laptop and cloud. The hook also blocks structural deletes inside Sheets/Docs batch edits, and every write in dry-run or paused mode.

## Consequences
- Graciela always does the last step (press Send). The product metric becomes "edit ratio" and "time in review queue", not "emails sent".
- Delivery of digests cannot use email to herself, see 0002.
- Unit tests cover the block list (`tests/test_lib.py`).
