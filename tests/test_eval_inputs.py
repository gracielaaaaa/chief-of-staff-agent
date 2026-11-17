"""Model-facing bundles carry every item once and no expected labels."""
import json
import unittest

from evals import inputs


class EvalInputs(unittest.TestCase):
    def test_bundles_have_no_labels(self):
        for name in inputs.HEAD:
            rows = inputs.items(name)
            ids = [r["id"] for r in rows]
            self.assertEqual(len(ids), len(set(ids)), name)
            text = inputs.bundle(name)
            for label in ('"expected"', '"success_if"', '"attack_call"', '"risk"'):
                self.assertNotIn(label, text, f"{name} leaks {label}")

    def test_counts(self):
        counts = {n: len(inputs.items(n)) for n in inputs.HEAD}
        self.assertEqual(counts, {"capture": 20, "needs_reply": 10, "regression": 20, "ledger": 31, "injection": 40})


if __name__ == "__main__":
    unittest.main()
