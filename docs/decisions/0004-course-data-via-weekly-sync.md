# 0004. Course data via a weekly local Canvas sync

Status: accepted, 2026-10-07

## Context
Discussion posts and deadlines live in Canvas. The Canvas connector runs on the laptop and is not reachable from cloud jobs.

## Decision
A local scheduled task (Sundays, catches up when the laptop wakes) copies the next 14 days of her own courses' assignments, discussion prompts, and reading links into Drive `Courses/`. Cloud jobs read only Drive. The Canvas connector is read-only for this agent (the guardrail blocks all Canvas writes). For courses where she teaches, only schedule and due dates are synced: no rosters, submissions, or grades.

## Consequences
Data can be up to a week stale; the capture job flags a sync older than 8 days.
