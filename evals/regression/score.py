"""Score model predictions on the model-layer regression cases (issues whose fix was a prompt).

Predictions file: one JSON object per line, {"id": "r13a", "output": {"promise": false, ...}}
  python3 -m evals.regression.score evals/results/regression-<date>.jsonl

A case passes when every expected field matches. who_type is checked only when expected.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

CASES = Path(__file__).with_name("model_cases.jsonl")


def load(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def score(cases, predictions):
    pred = {p["id"]: p.get("output", {}) for p in predictions}
    by_issue, failures = defaultdict(lambda: [0, 0]), []
    for c in cases:
        out = pred.get(c["id"], {})
        ok = all(out.get(k) == v for k, v in c["expected"].items())
        by_issue[c["issue"]][0] += ok
        by_issue[c["issue"]][1] += 1
        if not ok:
            failures.append({"id": c["id"], "issue": c["issue"], "expected": c["expected"], "got": out})
    passed = sum(v[0] for v in by_issue.values())
    return {"passed": passed, "total": len(cases),
            "by_issue": {str(k): f"{v[0]}/{v[1]}" for k, v in sorted(by_issue.items())},
            "failures": failures}


if __name__ == "__main__":
    print(json.dumps(score(load(CASES), load(sys.argv[1])), indent=2))
