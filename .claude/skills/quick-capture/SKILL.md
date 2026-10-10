---
name: quick-capture
description: Interactive version of the capture routine. Graciela types to-dos, ideas, and commitments directly into a chat session instead of emailing +inbox; this skill classifies, books, drafts, and records them with the same rules, keys, and state as the scheduled dispatcher. Also answers "what's on my plate?".
---
# Quick capture (typed to-dos)

Same rules as `.claude/skills/dispatcher/SKILL.md` and CLAUDE.md. The difference: the input is what Graciela types here, and she is present, so show results immediately and ask instead of guessing.

Before the first write in a session, do `run-common` Start step 3 (resolve the Drive folders by name and run `python3 -m jobs.lib.folders set ...`), or the guardrail blocks every Drive file create.

## When she types items
1. Split the message into atomic items. Classify each (lane, action, due, duration) using the `classifier` subagent rules. If an item is ambiguous (lane, date, who), ask ONE short batched question before acting.
2. Act exactly as the dispatcher does:
   - TASK: free slot via `jobs.lib.slots.planning_start` + `find_slot` on her primary calendar (business-hours window for calls and errands; focus time counts as busy; check existing events first so nothing is double-booked).
   - REMINDER: 10 min free event, popup at 0.
   - EMAIL: draft it (drafter rules, flags for students, instructor, rates, contracts, scope).
   - I_OWE / WAITING_ON: Ledger row (Ledger sheet 1jl_WqU2BDo4hRPgzmBLD3gyqJ065of90Y8VT2X3DfWU, tab items).
   - LOOK_INTO_LATER: append under the lane heading in the `Look Into Later` doc.
3. Dedupe: key `kind|chat-<YYYYMMDD>|<item text>` in `_State` `processed` (sheet 1Pm40j1FY9F9Q24pn5--So5fy2q3SZpoE4NCDo-8O2mI). Record each created object there and one row per action in the Run Log (sheet 1ldU4EXkqgBVCfGSLrq3eHh4ErnJvUAK88uLuSEzTzXM, tab runs, job `quick-capture`).
4. Reply with a compact table: item, what was done, when, link. No popup (she is here).
5. Project work that needs real effort (a proposal, an invoice, an application) belongs in its own workstream session: book the block, add the ledger row, and suggest opening that workstream.

## When she asks "what's on my plate?" (or "today", "this week")
Read-only summary: today's and tomorrow's calendar, open Ledger items due within 7 days (oldest first), Gmail drafts waiting for review (with links), and anything in today's review doc under `Needs you`. Keep it to one screen.

## When she marks something done ("sent Shannon", "did the returns")
Find the matching Ledger row or calendar block, set Ledger `status=done` and `closed=<now>`; do not delete events.
