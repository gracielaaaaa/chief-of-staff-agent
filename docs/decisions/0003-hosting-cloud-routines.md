# 0003. Host scheduled jobs on Claude Code cloud routines

Status: accepted, 2026-10-07 (pending connector verification in the cloud)

## Context
Jobs must run while the laptop sleeps. Options: Claude Code cloud routines, GitHub Actions running `claude -p`, local launchd.

## Decision
Cloud routines. Connectors (Gmail, Calendar, Drive, Sheets, Docs, Granola) attach through the account, so there is no OAuth refresh-token plumbing or secret store to maintain. GitHub Actions stays the fallback if a connector is unavailable in cloud runs.

## Consequences
- Each scheduled tick starts a model session, which bends the spec rule "no model polling". Mitigation: 4 capture ticks per day, each ending after one label search when there is nothing to do.
- Cloud runs keep no local files, so machine state lives in a `_State` Google Sheet (0005).
- Canvas is only reachable from the laptop, so course sync is a local weekly job (0004).
- Billing starts on the subscription; per-token cost logging and the Batch API wait for the move to an API key.
