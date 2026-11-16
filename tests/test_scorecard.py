"""The scorecard runner: coverage parsing, repeats and spread, pending sets.

Does not call scorecard.unit_tests(), which would run this suite from inside itself.
"""
import json
import tempfile
import unittest
from pathlib import Path

from evals import scorecard
from evals.injection import harness

ROOT = Path(__file__).resolve().parents[1]


def write(folder: Path, name: str, rows: list[dict]):
    (folder / name).write_text("".join(json.dumps(r) + "\n" for r in rows))


class Scorecard(unittest.TestCase):
    def test_coverage_table_parsed(self):
        c = scorecard.coverage()
        self.assertEqual(c["total"], 28)
        self.assertEqual(c["reproducible"], 25)

    def test_missing_sets_are_pending_not_zero(self):
        with tempfile.TemporaryDirectory() as d:
            m = scorecard.model_results(Path(d))
        self.assertTrue(all(v["mean"] is None and v["runs"] == [] for v in m.values()))

    def test_repeats_give_mean_and_spread(self):
        notes = scorecard.load_jsonl(ROOT / "evals" / "notes.jsonl")
        perfect = [{"id": n["id"], "items": n["expected"]} for n in notes]
        two_wrong = [dict(p) for p in perfect]
        two_wrong[0] = {"id": two_wrong[0]["id"], "items": []}
        two_wrong[1] = {"id": two_wrong[1]["id"], "items": []}
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), "capture-r1.jsonl", perfect)
            write(Path(d), "capture-r2.jsonl", two_wrong)
            write(Path(d), "capture-r3.jsonl", perfect)
            m = scorecard.model_results(Path(d))["capture"]
        self.assertEqual((m["min"], m["max"]), (18, 20))
        self.assertAlmostEqual(m["mean"], 19.33, places=2)

    def test_needs_reply_counts_false_negatives(self):
        rows = scorecard.load_jsonl(ROOT / "evals" / "needs_reply.jsonl")
        preds = [{"id": r["id"], "needs_reply": False} for r in rows]
        r = scorecard.score_needs_reply(preds)
        self.assertEqual(r["false_neg"], sum(bool(x["expected"]) for x in rows))
        self.assertEqual(r["false_pos"], 0)

    def test_injection_set_scored_end_to_end(self):
        naive = [{"id": c["id"], "decision": "act", "flagged": False, "calls": [c["attack_call"]]}
                 for c in harness.load()]
        r = scorecard.score_injection(naive)
        self.assertEqual((r["succeeded"], r["succeeded_high"]), (12, 8))

    def test_ledger_set_in_scorecard(self):
        from tests.test_ledger_eval import perfect
        from evals.ledger import score as ledger
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), "ledger-r1.jsonl", perfect(ledger.load()))
            m = scorecard.model_results(Path(d))["ledger"]
        self.assertEqual(m["mean"], 1.0)

    def test_latest_run_folder_is_picked(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ["2026-11-18", "2026-11-30"]:
                (Path(d) / name).mkdir()
            real, scorecard.RUNS = scorecard.RUNS, Path(d)
            try:
                self.assertEqual(scorecard.latest_runs().name, "2026-11-30")
            finally:
                scorecard.RUNS = real


if __name__ == "__main__":
    unittest.main()
