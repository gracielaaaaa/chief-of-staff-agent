# 0005. Keep machine state in a Google Sheet, not local files

Status: accepted, 2026-10-07

## Context
The spec suggested local JSON (`drafts.json`, `processed.json`). Cloud routines start from a fresh checkout each run. The Drive connector can create files but cannot edit them, so in-place updates need the Google Sheets and Docs connectors.

## Decision
`_State` sheet with tabs `processed` (dedupe keys), `drafts` (for edit learning), `observations` (style rules), `meta` (cursors). Gmail label `Agent/Done` is the first-line dedupe for captured notes. Cursors are written last, so a failed run is retried and dedupe keys prevent duplicates.

## Consequences
Graciela can inspect state from her phone. Sheets writes are slower than local files, so rows are batched per step.
