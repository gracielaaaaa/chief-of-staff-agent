"""Shape checks for the red-team set, so new cases cannot break the scorer."""
import json
import unittest
from pathlib import Path

CASES = Path(__file__).resolve().parents[1] / "evals" / "injection" / "cases.jsonl"
MODEL = {"ignore", "skip", "act", "needs_you", "no_action"}
DEFENSE = {"hook", "code", "code+hook", "model", "none"}


class InjectionCases(unittest.TestCase):
    def setUp(self):
        self.rows = [json.loads(l) for l in CASES.read_text().splitlines() if l.strip()]

    def test_ids_unique_and_counts(self):
        ids = [r["id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(sum(r["kind"] == "attack" for r in self.rows), 30)
        self.assertGreaterEqual(sum(r["kind"] == "benign" for r in self.rows), 10)

    def test_fields(self):
        for r in self.rows:
            e = r["expected"]
            self.assertIn(e["model"], MODEL, r["id"])
            self.assertIn(e["hook"], {"block", "allow"}, r["id"])
            self.assertIn(e["defense"], DEFENSE, r["id"])
            self.assertTrue(r["attack_call"]["tool"], r["id"])
            self.assertEqual(e["flag"], r["kind"] == "attack", r["id"])
            if e["defense"] == "model":
                self.assertEqual(e["hook"], "allow", r["id"])

    def test_no_em_dashes(self):
        self.assertNotIn("—", CASES.read_text())


if __name__ == "__main__":
    unittest.main()
