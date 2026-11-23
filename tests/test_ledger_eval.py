"""The ledger eval: case shape and the scorer's precision, recall, dates, privacy, and closure."""
import unittest

from evals.ledger import score as ledger


def perfect(cases):
    out = []
    for c in cases:
        if c["task"] == "close":
            out.append({"id": c["id"], "close": c["expected"]["close"]})
        else:
            out.append({"id": c["id"], "items": [
                {"type": e["type"], "what": " ".join(e["keys"]), "due": e.get("due"),
                 "who": "student" if e.get("who_type") == "student" else "Lena Park"}
                for e in c["expected"]]})
    return out


class LedgerEval(unittest.TestCase):
    def setUp(self):
        self.cases = ledger.load()

    def test_case_shape(self):
        ids = [c["id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        extract = [c for c in self.cases if c["task"] == "extract"]
        self.assertGreaterEqual(len(extract), 25)
        self.assertGreaterEqual(sum(not c["expected"] for c in extract), 6, "need hard negatives")
        for c in extract:
            for e in c["expected"]:
                self.assertIn(e["type"], {"I_OWE", "WAITING_ON"}, c["id"])
                self.assertTrue(all(k == k.lower() for k in e["keys"]), c["id"])

    def test_perfect_agent(self):
        r = ledger.score(perfect(self.cases), self.cases)
        self.assertEqual((r["precision"], r["recall"]), (1.0, 1.0))
        self.assertEqual(r["close_correct"], r["close_total"])
        self.assertEqual(r["student_name_leaks"], 0)
        self.assertEqual(r["due_correct"].split("/")[0], r["due_correct"].split("/")[1])

    def test_student_name_leak_counted(self):
        preds = perfect(self.cases)
        for p in preds:
            if p["id"] == "l04":
                p["items"][0]["who"] = "Jamie Student"
        self.assertEqual(ledger.score(preds, self.cases)["student_name_leaks"], 1)

    def test_key_synonyms(self):
        # Scorer change, block 12: "dsp|disability services" accepts either phrase.
        preds = perfect(self.cases)
        for p in preds:
            if p["id"] == "l05":
                p["items"][0]["what"] = "share the midterm with disability services"
        r = ledger.score(preds, self.cases)
        self.assertEqual(r["false_neg"], 0)
        for p in preds:
            if p["id"] == "l05":
                p["items"][0]["what"] = "share the midterm"
        self.assertEqual(ledger.score(preds, self.cases)["false_neg"], 1)

    def test_quoted_promise_is_a_false_positive(self):
        preds = perfect(self.cases)
        for p in preds:
            if p["id"] == "l14":
                p["items"] = [{"type": "I_OWE", "what": "send the pricing sheet"}]
        r = ledger.score(preds, self.cases)
        self.assertEqual(r["false_pos"], 1)
        self.assertLess(r["precision"], 1.0)
        self.assertEqual(r["recall"], 1.0)

    def test_holding_note_closed_by_mistake(self):
        preds = perfect(self.cases)
        for p in preds:
            if p["id"] == "l27":
                p["close"] = True
        self.assertEqual(ledger.score(preds, self.cases)["close_wrong"], ["l27"])

    def test_wrong_type_or_date(self):
        preds = perfect(self.cases)
        for p in preds:
            if p["id"] == "l09":
                p["items"][0]["type"] = "I_OWE"
            if p["id"] == "l01":
                p["items"][0]["due"] = "2026-11-20"
        r = ledger.score(preds, self.cases)
        self.assertIn("l09:agreement", r["misses"])
        self.assertEqual(r["false_pos"], 1)
        due_ok, due_total = map(int, r["due_correct"].split("/"))
        self.assertEqual(due_ok, due_total - 1)


if __name__ == "__main__":
    unittest.main()
