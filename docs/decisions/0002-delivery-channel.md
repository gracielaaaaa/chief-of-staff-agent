# 0002. Deliver digests as a Drive doc plus a calendar popup

Status: accepted, 2026-10-07

## Options
| Option | Cost | Reliability on phone | Breaks "never send"? |
|---|---|---|---|
| Email to self | free | high | yes, needs an exception |
| Claude app push | free | only with Remote Control connected | no |
| Third-party push (ntfy, Pushover) | free to $5 | high | no, but adds a service and a secret |
| **Drive doc + Calendar popup** | free | high (Calendar already notifies) | no |

## Decision
One review doc per day in `Chief of Staff/Review/`, plus one calendar popup per run that produced something, with the doc link in the description. Failure alerts use the same channel.

## Consequences
No new service, no exception to 0001. Calendar popups are less rich than email; the doc carries the detail.
