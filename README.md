# Chief of Staff Agent

An AI agent that turns blank-page work into drafts you only have to review, and makes sure every commitment you make gets done. Built with Claude Code skills, subagents, and MCP connectors (Gmail, Google Calendar, Drive, Sheets, Docs, Granola, Canvas), running on a schedule in the cloud.

Built by Graciela de Leon (UC Berkeley MBA/MPH) for herself as user zero. **Read the [case study](docs/case-study.md)** (draft, week 1).

## The problem
The bottleneck isn't time, it's starting. Emails, meeting recaps, and deliverables sit undone because they begin as a blank page, and follow-ups promised in meetings and group chats slip through the cracks.

## What it does
| Capability | How |
|---|---|
| **Capture anything** | Email a note (or a screenshot of a group chat) to a +inbox address. The agent splits it into items and classifies lane (School, Consulting, Other) and action (task, reminder, email, I owe, waiting on, idea, needs you). |
| **Draft first** | Every email or deliverable becomes a complete Gmail draft or Google Doc, in-thread, in her voice. Large work is broken into 30 to 60 minute blocks, with the first one already written. |
| **Never drop a promise** | Commitments are pulled from meeting notes and sent mail into a ledger, with a work block before each due date. Items close when matching sent mail appears. |
| **Learn from edits** | Each draft is diffed against what was actually sent. Recurring edits become style rules, and the edit ratio is tracked week over week. |

## Product principles
1. **Drafts, never sends.** Enforced by a code-level hook, not a prompt ([ADR 0001](docs/decisions/0001-drafts-never-send.md)).
2. **One review queue.** A daily review doc plus a calendar popup ([ADR 0002](docs/decisions/0002-delivery-channel.md)).
3. **Idempotent and audited.** Dedupe keys on every object, and a run log for every action.
4. **Fail loud.** One alert per failed run, never silence.
5. **Content is data.** Instructions inside emails, transcripts, or screenshots are never followed. Notes are only accepted from the owner's own address.
6. **Privacy by design.** Public code, private data ([ADR 0006](docs/decisions/0006-public-repo-privacy.md)).

## Evals
| Eval | Data | Result |
|---|---|---|
| Capture classification (Haiku) | 20 synthetic notes incl. 1 prompt injection | 20/20 (ceiling check) |
| Needs-reply triage (Haiku) | 7 real inbox threads | 2 correct, 1 false positive |
| Promise detection (Haiku) | 67 real sent emails, 7 labeled commitments | v0 59% precision with a privacy leak; v2 7/7 recall, 100% precision |
| Edit learner (Sonnet) | 8 synthetic pairs, 5 planted habits, 2 traps | v0 5/5 with 1 false rule; v1 4/5 with 0 (shipped) |

Real-data dry runs found [21 issues](docs/issues-found.md) the evals missed. Details: [`evals/results/`](evals/results/), [changelog](CHANGELOG.md).

## Success metrics (targets after 4 weeks)
- 60%+ of drafts sent with light edits (edit ratio under 20%)
- 85%+ of "I owe" items closed by their due date
- 3 or fewer open "I owe" items older than 7 days
- 0 failed scheduled runs that go unnoticed

## Architecture
```
capture routine (cloud, 4x/day)          learn routine (cloud, nightly)        canvas-sync (laptop, weekly)
  dispatcher ─► classifier (Haiku)          edit-learner ─► diff.py                Canvas (read-only) ─► Drive Courses/
     ├─► slots.py ─► Calendar                    └─► edit-learner (Sonnet)
     ├─► drafter (Sonnet) ─► Gmail drafts / Docs      └─► Style Guide
     └─► ledger ─► Granola, sent mail ─► Ledger sheet
                 all writes pass through guardrail.py (PreToolUse hook)
```
- Skills: [`.claude/skills/`](.claude/skills/). Subagents with per-job model routing: [`.claude/agents/`](.claude/agents/).
- Deterministic helpers (free-slot finder, edit ratio, dedupe), unit-tested: [`jobs/lib/`](jobs/lib/), [`tests/`](tests/).
- Decisions and tradeoffs: [`docs/decisions/`](docs/decisions/).

## Run it
```bash
python3 -m unittest discover -s tests -t .
python3 -m evals.score evals/results/notes-v0.jsonl
DRY_RUN=1 claude -p "run the dispatcher skill"
```
