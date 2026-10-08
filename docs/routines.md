# Scheduled routines

| Routine | Schedule (Pacific) | Cron (UTC) | Connectors | Status |
|---|---|---|---|---|
| capture | 8am, 12pm, 5pm, 9pm | `0 0,4,15,19 * * *` | Gmail, Calendar, Drive, Sheets, Docs | live since 2026-10-08 |
| learn (edit-learner) | 10pm | TBD | Gmail, Drive, Sheets, Docs | not yet created |
| canvas-sync | Sundays (local laptop task) | n/a | Canvas, Drive, Docs | not yet created |

Cron is UTC. Pacific Daylight Time ends 2026-11-01: update capture to `0 1,5,16,20 * * *` that week to keep the same local times.
