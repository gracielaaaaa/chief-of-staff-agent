# Case study: an AI chief of staff that never hits Send

*Graciela de Leon, UC Berkeley MBA/MPH. Draft, week 1 of 4. Outcome metrics marked "pending" fill in as real usage accumulates.*

## TL;DR
I built an agent that turns my blank-page work into drafts I only have to review, and makes sure every commitment I make gets done. It runs four times a day in the cloud against my real Gmail, Calendar, Drive, Granola meeting notes, and Canvas. In week 1 it went from spec to running in the cloud within about a day. The most useful finding: **synthetic evals passed at 100% while real-data dry runs found [21 issues](issues-found.md) they missed**, from a student's name leaking into a log to tasks booked before stores open.

## The problem (user zero: me)
I'm a dual-degree student, a teaching assistant for two courses, and an independent consultant. My bottleneck isn't time, it's starting. Emails, meeting recaps, and course work sit undone because they begin as a blank page. What slips through: follow-ups I promised in meetings and group chats.

So the job isn't "an assistant that does tasks." It's **"never let me face a blank page, and never let a promise go untracked,"** without ever acting on my behalf where a mistake costs trust.

## What it does
| Capability | How it works |
|---|---|
| Capture | I email a note (or a screenshot of a group chat) to a +inbox address. A small model splits it into items, classifies each by lane and action, and books it into free time on my calendar. |
| Draft first | Emails waiting on me get an in-thread draft in my voice. Large work becomes 30 to 60 minute blocks with the first one prepared. |
| Never drop a promise | Commitments are extracted from meeting notes and my sent mail into a ledger, with a work block before each deadline. Items close when matching sent mail appears. |
| Course deadlines | A weekly sync pulls my coursework from Canvas; one 9am digest per day lists what's due within 48 hours. |
| Learn from edits | Each draft is diffed against what I actually sent. Repeated edits become style rules. |

Architecture: Claude Code skills and subagents, scheduled as cloud routines, connected through MCP to Google Workspace, Granola, and Canvas. Classification runs on a small model (Haiku); drafting and learning on a mid-size model (Sonnet). Anything deterministic (time zones, free-slot search, edit ratios, dedupe keys, metrics) is plain, unit-tested Python, never left to the model.

## Product decisions and trade-offs
Each is a one-page decision record in [`docs/decisions/`](decisions/).

1. **Drafts, never sends, enforced in code.** A pre-tool hook blocks send, forward, reply, delete, and share no matter what the prompt says. I first wrote it as a block list; attaching one new connector added a "clear all values" tool the block list missed. It is now an **allow list**: anything not explicitly approved is blocked, including tools on connectors added later.
2. **Delivery through Calendar, not email to myself.** Sending to myself would need an exception to "never send." A calendar popup with a link to a review doc is free, reaches my phone, and keeps the rule absolute.
3. **Outlines, not drafts, for graded coursework, set per course.** The spec said "fully draft discussion posts." That's an academic integrity risk where AI use isn't allowed. The agent now reads a per-course AI policy: full drafts in AI courses, outlines and work blocks everywhere else. Emails and client work are always fully drafted.
4. **One digest per day instead of one reminder per deadline.** Following the spec literally meant four popups on one Saturday.
5. **Pulled inbox triage forward from phase 2.** In my first session as a user I asked, "can it draft replies to emails I get, not just notes I send it?" That was the real job, so it moved up.
6. **Public code, private data.** Real names, courses, and clients live in a private Drive doc loaded at runtime. A pre-commit check blocks real names and IDs; it caught a real colleague's name I had put in a test.

## How I evaluated it
| Eval | Data | Result |
|---|---|---|
| Capture classification | 20 synthetic notes, incl. a prompt injection | 20/20; injection routed to "needs you." A ceiling, since I wrote the set. |
| Needs-reply triage | 7 real inbox threads | 3 flagged, 2 correct, 1 false positive ("let's discuss after class") |
| Promise detection | 67 real sent emails, 7 hand-labeled commitments | v0: 7/7 recall, ~59% precision, 1 student name leaked. v2: 7/7 recall, 100% precision, no leaks. |
| Edit learner | 8 synthetic draft/sent pairs with 5 planted habits and 2 traps | v0: 5/5 habits, 1 false rule. v1: 4/5, 0 false rules. Shipped v1. |

Two things I'd tell another PM:

- **Precision versus recall depends on what a mistake costs.** For promise detection, a miss costs a broken commitment, so recall matters: v1 had perfect precision but missed the single most important deadline (sharing an exam with disability services), because I wrote "I need to" instead of "I'll." For style rules, a false rule silently changes every future draft, so I shipped the version with lower recall and zero false rules.
- **Real-data dry runs beat synthetic evals.** Every capability ran in dry-run mode on my real data before it could write anything. Those runs found [21 issues](issues-found.md) the evals didn't, including: a note sent from my phone's personal account would have been ignored; a fitness class already on my calendar would have been booked twice; two tasks landed in the same 8am slot; calls to a restaurant were scheduled before it opened; Google labels my focus blocks "free," so the agent booked over them; and the first scheduled cloud run followed a stale line in my own prompt over the config file (it flagged the conflict itself).

## Trust and safety
- **Prompt injection:** email, documents, transcripts, and Canvas pages are data. Notes are only accepted from my own addresses, so a public capture address can't be used to instruct the agent.
- **Student privacy (FERPA):** student names and grades never reach the ledger, logs, or review docs. The model is told this, and code enforces it anyway: a redaction backstop rewrites any coursework recipient who isn't staff to "student."
- **Accommodation requests** get a dedicated rule: the agent never interprets or decides them; it drafts a warm "I'm confirming with the instructor" and flags it.
- **Kill switch:** an email with the subject PAUSE AGENT stops every run.

## Results so far
| Metric | Target (4 weeks) | Now |
|---|---|---|
| Drafts sent with light edits (under 20% changed) | 60%+ | pending (first drafts created day 1) |
| Average edit ratio | trending down weekly | pending |
| Promises closed by due date | 85%+ | pending (8 tracked, 2 auto-closed on day 1) |
| Unnoticed failed runs | 0 | 0 |

## What I'd do next
- Pre-meeting briefs 30 minutes before client and group meetings (phase 2).
- A harder classification eval built from my real notes, since the synthetic set is saturated.
- Wednesday risk check: compare free hours against estimated work through Sunday, and draft the "can we move this" email when it doesn't fit.

## What I learned
[pending: written at the end of week 4]
