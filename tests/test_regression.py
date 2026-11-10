"""Regression tests: one per failure that real-data dry runs found (docs/issues-found.md).

Each test replays the original failing situation on synthetic data (persona in
evals/persona/). Model-behavior issues are scored separately in
evals/regression/model_cases.jsonl. Coverage per issue: evals/regression/coverage.md.
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

from jobs.lib import diff, filters, promises, review, sensitive, slots

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("guardrail", ROOT / ".claude/hooks/guardrail.py")
guardrail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guardrail)

MCP = "mcp__0000__"
AT = "@"
CONFIG = json.loads((ROOT / "config.json").read_text())
CFG = {
    "timezone": "America/Los_Angeles",
    "working_hours": {"start": "08:00", "end": "21:00"},
    "protected": {"color_ids": ["9"], "weekly_blocks": []},
}
# Gmail system labels a user label cannot reuse (case-insensitive).
GMAIL_RESERVED = {"inbox", "sent", "draft", "drafts", "spam", "trash", "starred", "important",
                  "unread", "chat", "chats", "all mail", "scheduled", "snoozed"}


def read(rel):
    return (ROOT / rel).read_text()


def allowed(tool, tool_input=None):
    return guardrail.decide(MCP + tool, {}, {}, tool_input)[0]


class RealDataRegressions(unittest.TestCase):
    def test_issue_01_labels_avoid_gmail_reserved_names(self):
        cap = CONFIG["capture"]
        for name in (cap["label"], cap["done_label"]):
            self.assertTrue(name.startswith("Agent/"), name)
            self.assertNotIn(name.lower(), GMAIL_RESERVED)
            self.assertNotIn(name.split("/")[-1].lower(), GMAIL_RESERVED - {"inbox"},
                             "leaf may be 'Inbox' only under the Agent/ parent")

    def test_issue_02_sheets_and_docs_edit_tools_allowed(self):
        # The fix routes edits through Sheets and Docs connectors; the hook must let them through.
        for t in ["append_values", "update_values", "update_doc", "update_spreadsheet"]:
            self.assertTrue(allowed(t, {"requests": [{"appendCells": {}}]}), t)

    def test_issue_03_unknown_destructive_tools_blocked(self):
        # A new connector tool must be blocked by default, whatever its name.
        for t in ["clear_all_values", "batch_clear_values", "clear_values", "wipe_sheet",
                  "delete_rows", "remove_file", "archive_thread", "some_future_tool"]:
            self.assertFalse(allowed(t), t)

    def test_issue_04_skills_search_by_label_name(self):
        # Connector behavior (ids vs names) is not reproducible offline. What we can pin is
        # the written rule, so a prompt edit cannot silently revert it (see issue 25).
        text = (ROOT / ".claude/skills/run-common/SKILL.md").read_text()
        self.assertRegex(text, r"use label NAMES")
        disp = (ROOT / ".claude/skills/dispatcher/SKILL.md").read_text()
        self.assertIn("label:Agent/Inbox", disp)

    def test_issue_05_phone_address_accepted_strangers_not(self):
        mine = ["maya" + AT + "example.edu", "maya.ortiz.phone" + AT + "example.com"]
        self.assertTrue(filters.accepted_sender("Maya Ortiz <maya.ortiz.phone" + AT + "example.com>", mine))
        self.assertTrue(filters.accepted_sender("MAYA" + AT + "EXAMPLE.EDU", mine))
        for bad in ["Maya Ortiz <maya" + AT + "example.edu.evil.test>",
                    "maya" + AT + "example.edu <attacker" + AT + "evil.test>",
                    "Lena Park <lena" + AT + "northwind.example.com>", "", "Maya Ortiz"]:
            self.assertFalse(filters.accepted_sender(bad, mine), bad)

    def test_issue_07_two_tasks_one_run_never_share_a_slot(self):
        booked = []
        for _ in range(3):
            s = slots.find_slot("2026-10-08T08:00:00-07:00", "2026-10-09T00:00:00-07:00", 30, booked, CFG)
            booked.append(s)
        starts = [b["start"] for b in booked]
        self.assertEqual(len(starts), len(set(starts)))

    def test_issue_08_call_waits_for_business_hours(self):
        # Booked late at night: the call must land after opening, not at 8:00.
        s = slots.find_slot("2026-10-07T22:25:00-07:00", "2026-10-09T17:00:00-07:00", 15, [], CFG,
                            {"start": "11:00", "end": "17:00"})
        self.assertTrue(s["start"].endswith("T11:00:00-07:00"), s)

    def test_issue_09_labeled_thread_dropped_even_if_search_returned_it(self):
        done = "Label_done"
        thread = {"messages": [{"labelIds": ["INBOX"]}, {"labelIds": ["INBOX", done]}]}
        self.assertTrue(filters.has_any_label(thread, [done, "Label_inbox"]))
        self.assertFalse(filters.has_any_label({"messages": [{"labelIds": ["INBOX"]}]}, [done]))
        self.assertFalse(filters.has_any_label({"messages": [{}]}, [done]))

    def test_issue_10_wrapped_attribution_and_huge_history_stripped(self):
        history = "\n".join("> line %d of an old thread" % i for i in range(2000))
        sent = ("Sounds good, see you Thursday.\n\nOn Tue, Oct 6, 2026 at 11:33 PM Prof. Ruth\n"
                "Alder <ralder" + AT + "example.edu> wrote:\n\n" + history)
        self.assertGreater(len(sent), 40_000)
        self.assertEqual(diff.strip_quoted(sent), "Sounds good, see you Thursday.")

    def test_issue_11_deleting_review_flag_is_not_an_edit(self):
        draft = "REVIEW BEFORE SENDING (student). Delete this line.\n\nHi,\n\nYes, that works.\n\nMaya"
        self.assertEqual(diff.edit_ratio(draft, "Hi,\n\nYes, that works.\n\nMaya"), 0.0)

    def test_issue_12_student_name_never_reaches_ledger(self):
        for what in ["Share the exam with DSP before Friday", "Send attendance makeup options",
                     "Check the quiz extension request"]:
            item = promises.redact_who({"who": "Jamie Student", "who_type": "other", "what": what})
            self.assertEqual(item["who"], "student", what)


class RealDataRegressions15to28(unittest.TestCase):
    def test_issue_15_first_run_stale_items_become_one_question(self):
        stale = [{"due": "2026-09-%02d" % d} for d in range(10, 30, 3)]
        self.assertTrue(all(promises.triage(i, "2026-10-08") == "confirm" for i in stale))
        self.assertEqual(promises.triage({"due": "2026-10-12"}, "2026-10-08"), "open")

    def test_issue_17_four_deadlines_do_not_pack_one_morning(self):
        now, booked = "2026-10-05T08:00:00-07:00", []
        for due in ["2026-10-09", "2026-10-12", "2026-10-14", "2026-10-16"]:
            deadline = due + "T21:00:00-07:00"
            s = slots.find_slot(slots.planning_start(now, deadline), deadline, 60, booked, CFG)
            booked.append(s)
        days = {b["start"][:10] for b in booked}
        self.assertGreaterEqual(len(days), 3, booked)

    def test_issue_18_focus_time_marked_free_still_blocks(self):
        focus = {"start": "2026-10-08T08:00:00-07:00", "end": "2026-10-08T11:00:00-07:00",
                 "transparency": "transparent", "eventType": "FOCUS_TIME"}
        s = slots.find_slot("2026-10-08T08:00:00-07:00", "2026-10-09T00:00:00-07:00", 60, [focus], CFG)
        self.assertGreaterEqual(s["start"], "2026-10-08T11:00:00-07:00")

    def test_issue_26_review_block_is_plain_text_for_append(self):
        txt = review.render_text("17:00", {"needs_you": [{"text": "Confirm the reader meeting time"}]})
        self.assertNotIn("<", txt)
        self.assertTrue(txt.startswith("\nRun 17:00\n"))

    def test_issue_27_financial_errand_is_a_task_not_a_secret(self):
        for note in ["call the bank about my 401(k) rollover, 30 min",
                     "log in to my HSA and download nothing, just check the claim status",
                     "book 20 min to move my IRA to the new provider"]:
            self.assertEqual(sensitive.find_secrets(note), [], note)
        self.assertNotEqual(sensitive.find_secrets("my routing number is 121000248"), [])

    def test_issue_28_attachments_blocked_drive_images_readable(self):
        for t in ["get_message_attachment", "get_meeting_attachment", "download_file_content",
                  "download_course_file"]:
            self.assertFalse(allowed(t), t)
        self.assertTrue(allowed("read_file_content"))


class SkillTextBackstops(unittest.TestCase):
    """Rules whose fix is prompt text: pin the text so a later edit cannot drop them."""

    def test_issue_13_and_14_promise_rules_present(self):
        text = (ROOT / ".claude/agents/classifier.md").read_text()
        self.assertTrue(re.search(r"same-day logistics", text, re.I), "issue 13 exclusion missing")
        self.assertTrue(re.search(r"I need to", text), "issue 14 obligation rule missing")

    def test_issue_15_first_run_lookback_rule(self):
        self.assertIn("First run (no cursor): look back 7 days only", read(".claude/skills/ledger/SKILL.md"))

    def test_issue_16_meeting_filter_reads_notes(self):
        self.assertIn("also keep meetings whose notes name other people or a client",
                      read(".claude/skills/ledger/SKILL.md"))

    def test_issue_19_config_is_source_of_truth(self):
        self.assertIn("It is the source of truth", read(".claude/skills/run-common/SKILL.md"))

    def test_issue_20_cursors_and_clock(self):
        text = read(".claude/skills/run-common/SKILL.md")
        self.assertIn("Advance cursors on quiet runs too", text)
        self.assertIn("date -u +%Y-%m-%dT%H:%M:%SZ", text)

    def test_issue_21_capture_routine_lists_granola(self):
        row = next(l for l in read("docs/routines.md").splitlines() if l.startswith("| capture"))
        for connector in ["Gmail", "Calendar", "Drive", "Sheets", "Docs", "Granola"]:
            self.assertIn(connector, row)

    def test_issue_25_names_in_search_ids_only_for_labeling(self):
        text = read(".claude/skills/run-common/SKILL.md")
        self.assertIn("searching by label id silently returns nothing", text)
        self.assertIn("Label ids are only for", text)

    def test_issue_26_review_doc_never_read_back(self):
        self.assertIn("NEVER read it back", read(".claude/skills/run-common/SKILL.md"))

    def test_issue_27_errands_are_tasks(self):
        self.assertIn("Financial **errands**", read(".claude/skills/dispatcher/SKILL.md"))

    def test_issue_05_and_09_skills_call_the_code_filters(self):
        disp = (ROOT / ".claude/skills/dispatcher/SKILL.md").read_text()
        triage = (ROOT / ".claude/skills/inbox-triage/SKILL.md").read_text()
        self.assertIn("jobs.lib.filters.accepted_sender", disp)
        self.assertIn("jobs.lib.filters.has_any_label", disp)
        self.assertIn("jobs.lib.filters.has_any_label", triage)


if __name__ == "__main__":
    unittest.main()
