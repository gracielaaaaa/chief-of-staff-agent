---
name: canvas-sync
description: Weekly LOCAL job (laptop, desktop app scheduled task). Copies the next 2 weeks of Graciela's own course assignments, discussion prompts, and reading links from Canvas into Drive Courses/ so cloud jobs can use them. Read-only on Canvas.
---
# Canvas sync

Runs locally only, because the Canvas connector lives on the laptop. Canvas tools are read-only for this agent; the guardrail blocks every Canvas write.

Follow `run-common` Start.

1. `get_my_enrollments`, keeping courses where she is a **student**. For courses where she is a TA or teacher, sync only the schedule and assignment due dates, never submissions, rosters, grades, or analytics.
2. For each course: `get_my_upcoming_assignments` (days 14) plus `list_assignments` filtered to due dates in the next 14 days. For discussion assignments, `get_discussion_topic_details` for the prompt text. For readings, the module item titles and links (not file contents).
3. Write one Google Doc per course, `Courses/<course code>/Upcoming`, replacing its body with:
   - first line `synced_at: <ISO timestamp>`
   - one section per item: title, type (assignment | discussion | quiz | group), due (ISO, Pacific), points, `canvas_id`, link, prompt text (discussions only, trimmed to 3,000 chars), group flag and group members' first names only for her own group projects.
4. Run Log row per course: `items=<n>`.

Never copy other students' posts, names, or grades. If a course's page is a TA-view, skip anything student-identifying.
