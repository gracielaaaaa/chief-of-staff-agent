# 0006. Public repo, private data

Status: accepted, 2026-10-07

## Context
The repo doubles as a portfolio piece, but the system handles student email (FERPA) and confidential client work.

## Decision
- The repo contains no real names, addresses, or Drive ids. People, courses, and clients live in a `Lane Context` Google Doc loaded at runtime.
- Evals, demos, and screenshots use a synthetic persona (`evals/persona/`).
- A pre-commit hook (`scripts/scrub_check.py`) blocks emails, Drive and calendar ids, and a private term list kept outside git.
- Published results are aggregates only.
- Student names and grades are never written to the Ledger, Run Log, or review docs, only to the Gmail draft itself.
- Capture notes are accepted only from her own authenticated address, so a public capture address cannot be used to give the agent instructions.

## Consequences
Two sources of truth for lane context (synthetic in git, real in Drive). The agent prompts are written against the structure, not the names.
