# Issues found by real-data dry runs (not caught by synthetic evals)

Every capability ran in dry-run mode on the owner's real data before it could write anything. Each issue below is fixed; the version is in `CHANGELOG.md`.

| # | Issue | Fix | Version |
|---|---|---|---|
| 1 | Gmail reserves "Inbox", so the capture label could not be created | Labels live under `Agent/` | 0.1.1 |
| 2 | The Drive connector cannot edit a file after creating it | Added Sheets and Docs connectors | 0.1.1 |
| 3 | Block-list guardrail missed a new "clear all values" tool | Allow list | 0.1.1 |
| 4 | Gmail search needs label ids, not names | Resolve ids first | 0.1.1 |
| 5 | First real note came from the phone's personal account and would have been skipped | Sender allowlist of her addresses (private) | 0.1.2 |
| 6 | A class already on the calendar would have been booked again | Check nearby events before booking | 0.1.2 |
| 7 | Two tasks in one run landed in the same slot | Booked slots feed the next search | 0.1.2 |
| 8 | A call to a restaurant was scheduled before it opened | Business-hours window | 0.1.2 |
| 9 | Gmail ignored `-label:` exclusions, so a capture note reappeared in triage | Filters run in code | 0.2.0 |
| 10 | Wrapped "On ... wrote:" lines were not stripped (one thread was 40 KB) | Multi-line pattern | 0.2.0 |
| 11 | Deleting the agent's own review flag counted as an edit | Flag line ignored in edit ratio | 0.4.0 |
| 12 | Promise detection put a student's full name in a ledger row | Prompt rule plus code redaction backstop | 0.5.0 |
| 13 | Promise detection counted same-day logistics ("I'll be there by 12:20") | Prompt exclusion | 0.5.0 |
| 14 | Tightening the prompt lost "I need to..." obligations, including an exam deadline | Obligations added back | 0.5.0 |
| 15 | First run would have backfilled a month of stale meeting tasks | 7-day lookback, past-due items become one question | 0.5.0 |
| 16 | Granola listed only the owner as a participant of a client retreat | Meeting filter also reads the notes | 0.5.0 |
| 17 | Earliest-fit packed four tasks into one morning | 3-day lead window before each deadline | 0.5.0 |
| 18 | Google marks focus time as "free", so the agent booked over it | Focus time counts as busy | 0.5.0 |
| 19 | First cloud run followed a stale line in the routine prompt over `config.json` (the agent flagged this itself) | Prompt defers to config | 0.5.1 |
| 20 | Cursors did not advance on quiet runs; one timestamp was off by an hour | Advance on success; timestamps from the clock | 0.5.1 |
| 21 | The ledger step's meeting connector was never attached to the cloud routine | Attached | 0.5.1 |
| 22 | A client promise from 12 days earlier ("I'll get back to you early next week") was missed because the first ledger run only looked back 7 days. The owner caught it herself. | First run should scan 30 days of sent mail for promises that are past due and still unanswered, and ask about them once | open |
| 23 | Deleting an agent-created calendar event leaves its ledger item open, so digests keep nagging | Treat a deleted agent event as "done or dropped" and ask once | open |
| 24 | Working every project in one chat overloaded it (owner feedback) | One session per workstream, coordinated through the ledger, drafts, and review doc; candidate feature: the agent offers a ready-to-start session for each new project | adopted |
| 25 | Gmail search by label id silently returns nothing, so the capture run initially missed 3 notes (and an earlier "arrived too late" explanation was wrong) | Search by label name; ids only for labeling calls | 0.6.1 |
| 26 | The daily review doc grew past the read limit, so the run created a second doc, breaking "one review queue" | Append a plain-text block to the end without reading the doc back | 0.6.1 |
