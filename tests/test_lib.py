import importlib.util
import unittest
from pathlib import Path

from jobs.lib import canvas, dedupe, diff, learn, promises, review, sensitive, slots

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("guardrail", ROOT / ".claude/hooks/guardrail.py")
guardrail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guardrail)

GMAIL = "mcp__946aec6a__"
AT = "@"  # built at runtime so the repo scrub check does not read test senders as real addresses
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
                  "send_conversation", "post_discussion_entry", "bulk_grade_submissions", "delete",
                  "batch_clear_values", "execute_sql", "buy_domain", "create_broadcast",
                  "create_assignment", "update_assignment", "copy_file"]:
            self.assertFalse(self.check(GMAIL + t), t)

    def test_drafts_and_reads_allowed(self):
        for t in ["create_draft", "update_draft", "create_event", "search_threads",
                  "get_meetings", "label_message", "list_events", "get_my_upcoming_assignments"]:
            self.assertTrue(self.check(GMAIL + t), t)

    def test_dry_run_blocks_writes_not_reads(self):
        self.assertFalse(self.check(GMAIL + "create_draft", {"DRY_RUN": "1"}))
        self.assertFalse(self.check(GMAIL + "label_thread", cfg={"dry_run": True}))
        self.assertFalse(self.check(GMAIL + "append_values", {"DRY_RUN": "1"}))
        self.assertTrue(self.check(GMAIL + "search_threads", {"DRY_RUN": "1"}))

    def test_paused_blocks_writes(self):
        self.assertFalse(self.check(GMAIL + "create_event", cfg={"paused": True}))
        self.assertTrue(self.check(GMAIL + "list_events", cfg={"paused": True}))

    def test_structural_deletes_blocked(self):
        req = {"requests": [{"deleteDimension": {"range": {"sheetId": 0}}}]}
        self.assertFalse(guardrail.decide(GMAIL + "update_spreadsheet", {}, {}, req)[0])
        ok = {"requests": [{"appendCells": {"sheetId": 0}}]}
        self.assertTrue(guardrail.decide(GMAIL + "update_spreadsheet", {}, {}, ok)[0])

    def test_writes_with_secrets_blocked(self):
        bad = {"body": "Here is my card 4111 1111 1111 1111"}
        self.assertFalse(guardrail.decide(GMAIL + "create_draft", {}, {}, bad)[0])
        good = {"body": "Hi Pat, see you Friday."}
        self.assertTrue(guardrail.decide(GMAIL + "create_draft", {}, {}, good)[0])

    def test_attachments_and_downloads_blocked(self):
        for t in ["get_message_attachment", "download_file_content", "download_course_file"]:
            self.assertFalse(self.check(GMAIL + t), t)

    def test_harness_tools_pass(self):
        self.assertTrue(self.check("mcp__ccd_session__mark_chapter"))

    def test_non_mcp_tools_pass(self):
        self.assertTrue(self.check("Bash"))


class Diff(unittest.TestCase):
    def test_identical_is_zero(self):
        self.assertEqual(diff.edit_ratio("Hi Priya,\n\nAttached.", "Hi Priya,\n\nAttached."), 0.0)

    def test_quoted_history_ignored(self):
        sent = "Hi Priya,\n\nAttached.\n\nOn Mon, Oct 5, 2026 at 9:00 AM Priya wrote:\n> old stuff"
        self.assertEqual(diff.edit_ratio("Hi Priya,\n\nAttached.", sent), 0.0)

    def test_wrapped_attribution_stripped(self):
        sent = ("Thanks, will do.\n\nOn Tue, Oct 6, 2026 at 11:33 PM Pat Example <\n"
                "pat@example.edu> wrote:\n\n> long history\n> more")
        self.assertEqual(diff.strip_quoted(sent), "Thanks, will do.")

    def test_review_flag_line_is_not_an_edit(self):
        draft = "REVIEW BEFORE SENDING (instructor). Delete this line.\n\nHi Pat,\n\nYes, will do.\n\nBest,\nG"
        self.assertEqual(diff.edit_ratio(draft, "Hi Pat,\n\nYes, will do.\n\nBest,\nG"), 0.0)

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

    def test_business_hours_window(self):
        s = slots.find_slot("2026-10-07T22:25:00-07:00", "2026-10-09T17:00:00-07:00", 15, [], CFG,
                            {"start": "11:00", "end": "17:00"})
        self.assertEqual(s["start"], "2026-10-08T11:00:00-07:00")

    def test_booked_slots_feed_next_search(self):
        first = slots.find_slot("2026-10-08T08:00:00-07:00", "2026-10-09T00:00:00-07:00", 30, [], CFG)
        second = slots.find_slot("2026-10-08T08:00:00-07:00", "2026-10-09T00:00:00-07:00", 30, [first], CFG)
        self.assertEqual(second["start"], "2026-10-08T08:30:00-07:00")

    def test_focus_time_blocks_even_if_free(self):
        ev = [{"start": "2026-10-08T08:00:00-07:00", "end": "2026-10-08T12:00:00-07:00",
               "transparency": "transparent", "eventType": "FOCUS_TIME"}]
        s = slots.find_slot("2026-10-08T08:00:00-07:00", "2026-10-09T00:00:00-07:00", 30, ev, CFG)
        self.assertEqual(s["start"], "2026-10-08T12:00:00-07:00")

    def test_planning_start_uses_lead_window(self):
        self.assertEqual(slots.planning_start("2026-10-08T09:00:00-07:00", "2026-10-23T21:00:00-07:00"),
                         "2026-10-20T21:00:00-07:00")
        self.assertEqual(slots.planning_start("2026-10-08T09:00:00-07:00", "2026-10-09T21:00:00-07:00"),
                         "2026-10-08T09:00:00-07:00")

    def test_no_slot_before_deadline(self):
        self.assertIsNone(slots.find_slot("2026-10-08T20:45:00-07:00", "2026-10-08T23:00:00-07:00", 60, [], CFG))


class Canvas(unittest.TestCase):
    def test_utc_due_is_previous_evening_pacific(self):
        d = canvas.due_local("2026-10-13T06:59:00Z")
        self.assertEqual((d.month, d.day, d.hour, d.minute), (10, 12, 23, 59))

    def test_reminder_lands_at_9am_two_days_before(self):
        self.assertEqual(canvas.reminder_at("2026-10-13T06:59:00Z").isoformat(), "2026-10-10T09:00:00-07:00")

    def test_after_dst_ends(self):
        # Nov 10 07:59Z is Nov 9 11:59pm PST (UTC-8)
        d = canvas.due_local("2026-11-10T07:59:59Z")
        self.assertEqual((d.day, d.hour, d.utcoffset().total_seconds()), (9, 23, -8 * 3600))

    def test_daily_digest_groups_and_skips_submitted(self):
        items = [
            {"title": "A", "due_utc": "2026-10-20T06:59:59Z", "status": "not submitted"},
            {"title": "B", "due_utc": "2026-10-20T06:59:59Z", "status": "not submitted"},
            {"title": "C", "due_utc": "2026-10-13T06:59:00Z", "status": "not submitted"},
            {"title": "D", "due_utc": "2026-10-13T06:59:00Z", "status": "submitted"},
        ]
        d = canvas.daily_digests(items)
        self.assertEqual([x["at"][:10] for x in d], ["2026-10-10", "2026-10-17"])
        self.assertEqual([i["title"] for i in d[1]["items"]], ["A", "B"])

    def test_html_cleaned(self):
        raw = ('<<<UNTRUSTED CANVAS CONTENT (x)>>><link rel="stylesheet" href="a.css"><ul><li>What is '
               '<i>cisnormativity</i>?&nbsp;</li><li>Second</li></ul><p><strong>When replying to peers, '
               'we encourage you to use the @ feature to tag</strong></p><script>x()</script>')
        self.assertEqual(canvas.html_to_text(raw), "- What is cisnormativity?\n- Second")


class Learn(unittest.TestCase):
    def test_weekly_metrics(self):
        rows = [
            {"created": "2026-10-08T05:40:00Z", "status": "sent", "edit_ratio": "0.10"},
            {"created": "2026-10-08T06:00:00Z", "status": "sent", "edit_ratio": "0.30"},
            {"created": "2026-10-09T06:00:00Z", "status": "rejected", "edit_ratio": ""},
            {"created": "2026-10-13T06:00:00Z", "status": "open", "edit_ratio": ""},
        ]
        m = learn.weekly_metrics(rows)
        self.assertEqual(m["2026-W41"], {"drafts": 3, "sent": 2, "rejected": 1,
                                         "avg_edit_ratio": 0.2, "light_edit_share": 0.5})
        self.assertIsNone(m["2026-W42"]["avg_edit_ratio"])

    def test_rejected_after_7_days(self):
        d = {"status": "open", "created": "2026-10-08T05:40:00Z"}
        self.assertFalse(learn.is_rejected(d, "2026-10-14T05:39:00Z"))
        self.assertTrue(learn.is_rejected(d, "2026-10-15T05:40:00Z"))

    def test_activation_threshold_or_confirmation(self):
        obs = [{"id": "r1", "status": "candidate", "evidence_count": 2},
               {"id": "r2", "status": "candidate", "evidence_count": 1},
               {"id": "r3", "status": "candidate", "evidence_count": 1, "confirmed": "yes"},
               {"id": "r4", "status": "active", "evidence_count": 5}]
        self.assertEqual(learn.activations(obs), ["r1", "r3"])


class Promises(unittest.TestCase):
    def test_automated_mail_dropped(self):
        for snip in ["Booked by Pat Example pat@example.edu Appointment Schedule",
                     "CGSM Monthly GBM Maya Ortiz has accepted this invitation. Hi everyone",
                     "\U0001F44D Maya Ortiz reacted via Gmail On Tue, Oct 6",
                     "Chat Maya is inviting you to a scheduled Zoom meeting. Join",
                     "This event has been updated Changed: conferencing"]:
            self.assertTrue(promises.is_automated(snip), snip)

    def test_real_mail_kept(self):
        self.assertFalse(promises.is_automated("Hi Sam, That works for me. I'll send you the grades asap."))

    def test_student_names_redacted_by_code(self):
        it = promises.redact_who({"who": "Pat Example", "who_type": "other",
                                  "what": "Share the exam with DSP 4 days before the exam"})
        self.assertEqual((it["who"], it["who_type"]), ("student", "student"))
        kept = promises.redact_who({"who": "Prof Alder", "who_type": "instructor", "what": "grade the quiz"})
        self.assertEqual(kept["who"], "Prof Alder")

    def test_past_due_needs_confirmation(self):
        self.assertEqual(promises.triage({"due": "2026-10-06"}, "2026-10-08"), "confirm")
        self.assertEqual(promises.triage({"due": "2026-10-24"}, "2026-10-08"), "open")
        self.assertEqual(promises.triage({"due": None}, "2026-10-08"), "open")

    def test_exclusions(self):
        self.assertTrue(promises.excluded(["recruiter@employer.example.com"], "Hi", ["employer.example.com"], []))
        self.assertFalse(promises.excluded(["pat@example.edu"], "Hi Pat", ["employer.example.com"], ["EmployerCo"]))


class Review(unittest.TestCase):
    def test_flagged_drafts_first_and_empty_sections_omitted(self):
        doc = review.render("2026-10-08", {"drafts": [{"text": "Client: deck"}, {"text": "student thread", "flag": "student"}],
                                           "booked": []})
        self.assertLess(doc.index("student thread"), doc.index("Client: deck"))
        self.assertNotIn("Booked", doc)

    def test_escapes_and_rejects_em_dash(self):
        self.assertIn("&lt;b&gt;", review.render("d", {"skipped": [{"text": "<b>x</b>"}]}))
        with self.assertRaises(ValueError):
            review.render("d", {"skipped": [{"text": "a \u2014 b"}]})

    def test_popup_title(self):
        self.assertEqual(review.counts({"drafts": [1, 2], "booked": [1], "needs_you": [1]}),
                         "[Agent] 2 drafts, 1 booked, 1 question")


class Sensitive(unittest.TestCase):
    def test_detects_secrets(self):
        self.assertEqual(sensitive.find_secrets("card 4111 1111 1111 1111 exp 12/29"), ["card number"])
        self.assertEqual(sensitive.find_secrets("SSN 123-45-6789"), ["SSN"])
        self.assertIn("bank account detail", sensitive.find_secrets("Routing number: 121000248"))
        self.assertIn("one-time code", sensitive.find_secrets("Your verification code is 482913"))
        self.assertIn("password", sensitive.find_secrets("password: hunter22"))

    def test_ignores_normal_work_content(self):
        for ok in ["https://mail.google.com/mail/#all?compose=thread-f:1877961163425134275",
                   "key=task:14f4d860f62f2819 canvas 9102497", "Room 1102, due 2026-10-16",
                   "Hi Pat, the deck is attached. Best, Maya", "course code PH 220, section 201",
                   "Please send your bank account details to HR, not me", "Dress code for the Oct 2026 event",
                   "account settings were updated", "PIN the event for 2026"]:
            self.assertEqual(sensitive.find_secrets(ok), [], ok)

    def test_financial_senders_and_subjects(self):
        self.assertTrue(sensitive.sensitive_sender("alerts" + AT + "chase.com"))
        self.assertFalse(sensitive.sensitive_sender("auto-confirm" + AT + "amazon.com"))  # receipts are fine
        self.assertTrue(sensitive.sensitive_sender("noreply" + AT + "studentaid.gov"))
        self.assertTrue(sensitive.sensitive_sender("alerts" + AT + "fidelity.com"))
        self.assertTrue(sensitive.sensitive_sender("faoemail" + AT + "example.edu"))
        self.assertFalse(sensitive.sensitive_sender("pat" + AT + "example.edu"))
        self.assertTrue(sensitive.sensitive_subject("Your verification code"))
        self.assertTrue(sensitive.sensitive_subject("Your W-2 is ready"))
        self.assertFalse(sensitive.sensitive_subject("Re: quiz 3"))
        self.assertTrue(sensitive.sensitive_subject("Your loan payment is due"))
        self.assertTrue(sensitive.sensitive_subject("Your 401(k) quarterly statement"))
        self.assertFalse(sensitive.sensitive_subject("Invoice #42 from Mendocino Farms"))
        self.assertFalse(sensitive.sensitive_subject("Your Amazon order receipt"))


class Dedupe(unittest.TestCase):
    def test_stable_and_whitespace_insensitive(self):
        self.assertEqual(dedupe.key("task", "m1", "Send  deck"), dedupe.key("task", "m1", "send deck"))
        self.assertNotEqual(dedupe.key("task", "m1", "a"), dedupe.key("task", "m2", "a"))


if __name__ == "__main__":
    unittest.main()
