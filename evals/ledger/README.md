# Ledger eval: commitment extraction and auto-close

`cases.jsonl` is synthetic, built on the persona in `evals/persona/`. Relative dates resolve from each case's `date` (Mon 2026-11-16).

- **Extraction (25 cases, 20 commitments):** sent-mail snippets and meeting notes. Positives cover the phrasings that failed on real data: "I need to..." obligations (issue 14), "let me check and get back to you", promised outcomes ("you'll receive credit"), two commitments in one email, items she is owed (`WAITING_ON`), and a meeting whose participant list showed only her (issue 16). The 8 negatives are same-day logistics (issue 13), a decision already made, a pleasantry, someone else's promise inside quoted text, something already done, an in-person errand, solo reading notes, and a decisions-only meeting. Partial negatives sit inside positive cases: teammates' tasks in a group meeting, and a vague "think about" item.
- **Auto-close (6 cases):** an open item plus a later sent message. Closes on delivery. Stays open for a holding note ("coming Thursday"), a different thread, or a hand-off ("can someone else book it?").

Scoring (`score.py`): precision, recall, and F1 over items (type plus key phrases); due-date accuracy on matched items; student-name leaks (a student item whose `who` is a name); and auto-close accuracy. The scorecard reports F1 as the headline. Target: precision and recall of 0.9 or more, 0 leaks.
