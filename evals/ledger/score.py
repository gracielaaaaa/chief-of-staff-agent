"""Score the ledger: commitment extraction (precision, recall) and auto-close decisions.

Predictions file: one JSON object per line.
  extract: {"id": "l01", "items": [{"type": "I_OWE", "what": "...", "who": "...", "who_type": "client", "due": "2026-11-19"}]}
  close:   {"id": "l26", "close": true}
  python3 -m evals.ledger.score predictions.jsonl

A predicted item matches an expected one when the types agree and every expected key
phrase appears in its `what` (case-insensitive). Each prediction matches at most one
expected item. Due dates are checked only on matched items that expect one. A student
item leaks when its `who` is anything but "student".
"""
import json
import sys
from pathlib import Path

CASES = Path(__file__).with_name("cases.jsonl")


def load(path=CASES):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def _matches(exp: dict, got: dict) -> bool:
    what = (got.get("what") or "").lower()
    return got.get("type") == exp["type"] and all(k in what for k in exp["keys"])


def score(predictions: list[dict], cases=None) -> dict:
    cases = cases or load()
    pred = {p["id"]: p for p in predictions}
    tp = fp = fn = due_ok = due_total = leaks = 0
    misses, extras, close_wrong = [], [], []
    close_ok = close_total = 0
    for c in cases:
        p = pred.get(c["id"], {})
        if c["task"] == "close":
            close_total += 1
            if bool(p.get("close")) == c["expected"]["close"]:
                close_ok += 1
            else:
                close_wrong.append(c["id"])
            continue
        got = list(p.get("items") or [])
        for exp in c["expected"]:
            hit = next((g for g in got if _matches(exp, g)), None)
            if hit is None:
                fn += 1
                misses.append(f"{c['id']}:{'/'.join(exp['keys'])}")
                continue
            got.remove(hit)
            tp += 1
            if exp.get("due"):
                due_total += 1
                due_ok += (hit.get("due") or "")[:10] == exp["due"]
            if exp.get("who_type") == "student" and (hit.get("who") or "student").lower() != "student":
                leaks += 1
        fp += len(got)
        extras += [f"{c['id']}:{(g.get('what') or '')[:40]}" for g in got]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "true_pos": tp, "false_pos": fp, "false_neg": fn,
            "due_correct": f"{due_ok}/{due_total}", "student_name_leaks": leaks,
            "close_correct": close_ok, "close_total": close_total,
            "misses": misses, "extras": extras, "close_wrong": close_wrong}


if __name__ == "__main__":
    print(json.dumps(score(load(sys.argv[1])), indent=2))
