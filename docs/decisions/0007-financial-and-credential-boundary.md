# 0007. Financial and credential boundary

Status: accepted, 2026-10-08

## Context
The Google connectors grant read access to the whole Berkeley account; their scope cannot be narrowed. A metadata-only scan found about 200 finance-related threads in 90 days (mostly receipts). The owner's rule: receipts and work invoices are fine; banking, investments, and loans must never be accessed, and login credentials must be protected.

## Decision
Defense in depth, weakest to strongest:
1. Gmail searches exclude bank, brokerage, loan, payment-app, tax, and payroll senders (`jobs.lib.sensitive.GMAIL_EXCLUDE`).
2. Threads with a sensitive sender or subject (statements, loans, 401(k), verification codes, password resets) are dropped on metadata, before any body is read.
3. Attachments and file downloads are blocked by the hook (statements and tax forms arrive as attachments).
4. The hook scans every write and blocks card numbers (Luhn-checked), SSNs, bank account or routing numbers, one-time codes, and passwords, so nothing sensitive can leave in a draft, sheet, doc, or event even if it was read.

## Consequences
- Layers 1 and 2 are lists and patterns, so a bank with an unlisted domain could get through them. Layers 3 and 4 still hold.
- The agents never hold passwords: connectors use OAuth tokens held by claude.ai, and cloud runs have no browser, password manager, or access to the laptop.
- Tax and payroll mail is excluded too, because W-2s and pay stubs carry SSNs and account numbers.
