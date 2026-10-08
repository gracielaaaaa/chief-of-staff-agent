import importlib.util
import unittest
from pathlib import Path

from jobs.lib import dedupe, diff, slots

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("guardrail", ROOT / ".claude/hooks/guardrail.py")
guardrail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guardrail)

GMAIL = "mcp__946aec6a__"
CFG = {
    "timezone": "America/Los_Angeles",
    "working_hours": {"start": "08:00", "end": "21:00"},
    "protected": {"color_ids": ["9"], "weekly_blocks": [{"day": "TUE", "start": "14:30", "end": "15:30"}]},
}


class Guardrail(unittest.TestCase):
    def check(self, tool, env=None, cfg=None):
        return guardrail.decide(tool, env or {}, cfg or {})[0]

    def test_never_sends_or_deletes(self):
        for t in ["send_message", "forward", "reply", "trash_thread", "delete_draft",
                  "delete_event", "respond_to_event", "share_file", "trash_file",
                  "send_conversation", "post_discussion_entry", "bulk_grade_submissions", "delete"]:
            self.assertFalse(self.check(GMAIL + t), t)

    def test_drafts_and_reads_allowed(self):
        for t in ["create_draft", "update_draft", "create_event", "search_threads",
                  "get_meetings", "label_message", "list_events", "get_my_upcoming_assignments"]:
            self.assertTrue(self.check(GMAIL + t), t)

    def test_dry_run_blocks_writes_not_reads(self):
        self.assertFalse(self.check(GMAIL + "create_draft", {"DRY_RUN": "1"}))
        self.assertFalse(self.check(GMAIL + "label_thread", cfg={"dry_run": True}))
        self.assertTrue(self.check(GMAIL + "search_threads", {"DRY_RUN": "1"}))

    def test_paused_blocks_writes(self):
        self.assertFalse(self.check(GMAIL + "create_event", cfg={"paused": True}))
        self.assertTrue(self.check(GMAIL + "list_events", cfg={"paused": True}))

    def test_structural_deletes_blocked(self):
        req = {"requests": [{"deleteDimension": {"range": {"sheetId": 0}}}]}
        self.assertFalse(guardrail.decide(GMAIL + "update_spreadsheet", {}, {}, req)[0])
        ok = {"requests": [{"appendCells": {"sheetId": 0}}]}
        self.assertTrue(guardrail.decide(GMAIL + "update_spreadsheet", {}, {}, ok)[0])

    def test_non_mcp_tools_pass(self):
        self.assertTrue(self.check("Bash"))


class Diff(unittest.TestCase):
    def test_identical_is_zero(self):
        self.assertEqual(diff.edit_ratio("Hi Priya,\n\nAttached.", "Hi Priya,\n\nAttached."), 0.0)

    def test_quoted_history_ignored(self):
        sent = "Hi Priya,\n\nAttached.\n\nOn Mon, Oct 5, 2026 at 9:00 AM Priya wrote:\n> old stuff"
        self.assertEqual(diff.edit_ratio("Hi Priya,\n\nAttached.", sent), 0.0)

    def test_heavy_rewrite_is_high(self):
        self.assertGreater(diff.edit_ratio("I hope this finds you well. Here is the doc.", "Doc attached."), 0.5)

    def test_light_edit_threshold(self):
        draft = ("Hi Priya,\n\nThanks so much for the call today. I will send the revised "
                 "landscape doc by Friday and flag the two open fact-checks.\n\nBest,\nG")
        r = diff.edit_ratio(draft, draft.replace("Thanks so much for", "Thanks for"))
        self.assertTrue(diff.light_edit(r))


class Slots(unittest.TestCase):
    def test_skips_busy_and_finds_next(self):
        ev = [{"start": "2026-10-08T09:00:00-07:00", "end": "2026-10-08T10:00:00-07:00"}]
        s = slots.find_slot("2026-10-08T09:05:00-07:00", "2026-10-09T17:00:00-07:00", 60, ev, CFG)
        self.assertEqual(s["start"], "2026-10-08T10:00:00-07:00")

    def test_respects_working_hours(self):
        s = slots.find_slot("2026-10-08T20:30:00-07:00", "2026-10-10T00:00:00-07:00", 60, [], CFG)
        self.assertEqual(s["start"], "2026-10-09T08:00:00-07:00")

    def test_protected_color_blocks_even_if_free(self):
        ev = [{"start": "2026-10-08T08:00:00-07:00", "end": "2026-10-08T12:00:00-07:00",
               "colorId": "9", "transparency": "transparent"}]
        s = slots.find_slot("2026-10-08T08:00:00-07:00", "2026-10-09T00:00:00-07:00", 30, ev, CFG)
        self.assertEqual(s["start"], "2026-10-08T12:00:00-07:00")

    def test_transparent_unprotected_ignored(self):
        ev = [{"start": "2026-10-08T08:00:00-07:00", "end": "2026-10-08T12:00:00-07:00", "transparency": "transparent"}]
        s = slots.find_slot("2026-10-08T08:00:00-07:00", "2026-10-09T00:00:00-07:00", 30, ev, CFG)
        self.assertEqual(s["start"], "2026-10-08T08:00:00-07:00")

    def test_office_hours_protected(self):
        # 2026-10-13 is a Tuesday
        s = slots.find_slot("2026-10-13T14:30:00-07:00", "2026-10-14T00:00:00-07:00", 30, [], CFG)
        self.assertEqual(s["start"], "2026-10-13T15:30:00-07:00")

    def test_no_slot_before_deadline(self):
        self.assertIsNone(slots.find_slot("2026-10-08T20:45:00-07:00", "2026-10-08T23:00:00-07:00", 60, [], CFG))


class Dedupe(unittest.TestCase):
    def test_stable_and_whitespace_insensitive(self):
        self.assertEqual(dedupe.key("task", "m1", "Send  deck"), dedupe.key("task", "m1", "send deck"))
        self.assertNotEqual(dedupe.key("task", "m1", "a"), dedupe.key("task", "m2", "a"))


if __name__ == "__main__":
    unittest.main()
