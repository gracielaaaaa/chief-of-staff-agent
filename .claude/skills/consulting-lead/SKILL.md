---
name: consulting-lead
description: Consulting workforce lead. Turns a prospect's or client's discovery (questionnaire, call notes, thread) into one batch of questions, then, after Graciela answers, a send-ready proposal with options, a cover email draft, and 3 call times. On demand only - /consulting-lead <Client>. Never sends, never picks a fee.
---
# Consulting lead

Follow `run-common` Start first (kill switch, dry run, Drive lookup, run id). Load `consulting-lane`. Decisions behind this flow: `docs/decisions/0008-consulting-workforce.md`.

Input: `client` (as named in Lane Context), optional `prospect: true`.

## 0. Where things live
- **Read from:** the client's existing Drive folder (questionnaire, notes), Granola meetings with the client's contacts, the latest Gmail thread with them, the private `Consulting Templates` doc. The private `Pricing` doc is read only in step 4 and its contents go only to the pricing helper and analyst.
- **Write to:** `Chief of Staff/Consulting/<Client>/` only (create the folder if missing). Docs: `<Client> - Questions`, `<Client> - Proposal`. Plus one Gmail draft and the review doc.
- **Firewall list:** from Lane Context Consulting, build `other_client_terms` = every other client's and lead's name, contacts, products, programs, and known figures, as `[{client, term}]`. Note who introduced this client, if anyone. Never write this list anywhere.

## 1. Which pass?
Look for `<Client> - Questions` in the client's agent folder.
- Missing: **pass 1**.
- Present and every fee question has an answer: **pass 2**.
- Present but a fee question is blank: stop, add a `Needs you` line to the review doc ("<Client>: questions doc waiting on N answers"), end.

## Pass 1: one batch of questions
2. **Gather** (trim hard, `defaults.transcript_char_cap`): questionnaire responses, call notes and Granola summaries, the last 3 messages of the thread, and the Ledger rows for this client (promises made, due dates). Label every source (`questionnaire Q7`, `call notes 2026-10-02`, `email 2026-10-05`).
3. **Synthesize.** `discovery-synthesizer` subagent. Then run `python3 -m jobs.lib.facts conflicts '<facts>'`. Every conflict becomes a question showing each value with its source and the ratio ("questionnaire Q7 says $4,500 per cohort, call notes say $1,500, 3x apart: which is right?"), default = the client's written answer.
4. **Pricing frame.** Read the `Pricing` doc. Draft the option outline (scope and levers only, no prose) yourself from the findings and template. `pricing-analyst` subagent estimates hours; run `python3 -m jobs.lib.pricing '<json>'` with her rate, the hours, anchors, budget, and levers; give the result back to the analyst for its question. If the Pricing doc has no rate, the first question is the rate. Never put a fee in a default.
5. **Confidentiality.** `python3 -m jobs.lib.confidential` on the findings with `other_client_terms` and every source path (`allowed_folders` = this client's folders). Then `confidentiality-reviewer` subagent. Any product overlap with another client, or anything about the introducer, becomes a question ("Their offer overlaps with <other client>'s product line. Mention it, stay silent, or decline that scope?"), default = stay silent.
6. **Relationship check.** From the Ledger and sent mail: did she promise this proposal by a date that has passed? Note it for the cover email (no question unless the tone is unclear).
7. **Write `<Client> - Questions`** (one doc, numbered, most important first, at most 12 questions):
   ```
   <Client> - Questions (answer under each, blank = use the recommendation; fee questions need an answer)
   Q1. <question>
   Why: <one line, with sources>
   Recommended: <default>
   Answer:
   ...
   Fact table (key | value | source)
   Findings summary (5 to 8 bullets with sources)
   Options outline (names, scope, hours ranges, no fees)
   ```
   Dedupe key `key('consult_questions', <client>, <questionnaire file id>)`.
8. **Review doc** `Needs you`: "<Client>: N questions before the proposal (link). About 10 minutes." Then `run-common` Finish.

## Pass 2: send-ready proposal
9. **Read answers.** Blank = recommended default. Her answers are facts with source `Graciela`. Add them to the fact table; for each resolved conflict keep only the value she chose.
10. **Draft.** `proposal-architect` subagent with findings, resolved facts, answers, template, lane tone, Style Guide. If it returns `blockers`, append them as new questions to the Questions doc, add a `Needs you` line, and stop.
11. **Gate (code, then models).**
    - `python3 -m jobs.lib.facts gate '{"draft": ..., "facts": ..., "other_client_terms": ...}'` must return `ready: true`.
    - `fact-checker` subagent: `unsupported` and `misquoted` must be empty.
    - `confidentiality-reviewer` subagent: `hits` must be empty.
    On a failure, fix what is a pure wording issue yourself (re-run the gate after). Anything needing a fact or a decision goes back to the Questions doc as a new numbered question; stop. Never ship a doc with a `[CHECK`.
12. **Write `<Client> - Proposal`** (Google Doc, from the architect's markdown). Dedupe key `key('consult_proposal', <client>, <questions doc id>)`; on re-run update the same doc.
13. **Call times.** List primary calendar events for the next `consulting.call_search_business_days` business days, then `python3 -m jobs.lib.slots '{"now": <start of the next business day>, "deadline": ..., "duration_min": <consulting.call_minutes>, "events": [...], "count": <consulting.call_options>, "window": <consulting.call_window>}'` (weekends are skipped, protected colors and office hours are respected, nothing is booked). Offer them in the client's time zone if Lane Context has it, else Pacific with "PT".
14. **Cover email.** `drafter` skill, `kind: consulting_cover`, with: the relationship notes from step 6, the proposal link, the 3 call times, the contact's address from mail history. In-thread if a thread exists. Always `REVIEW BEFORE SENDING` (scope and rates).
15. **Review doc** `Drafts to review`: proposal link, cover draft link, gate result ("0 open checks, 23 numbers traced, 0 cross-client hits"). `Ledger changes`: mark the proposal I_OWE row `drafted` with the draft link (never `done`; she closes it by sending). Then `run-common` Finish.

## Never, without her answer in the Questions doc
A fee, discount, or payment term. IP, liability, or any legal term. Any mention of, comparison with, or information from another client, including the introducer. A timeline commitment she has not stated. Sending anything.

## Dry run
Do all reads and subagent calls; print `WOULD create_file <Client> - Questions key=...`, `WOULD create_draft cover to=<recipient type> key=...`. Print gate results in full.
