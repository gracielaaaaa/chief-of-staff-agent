"""Score classifier predictions against evals/notes.jsonl.

Predictions file: one JSON object per line, {"id": "n01", "items": [{"lane": ..., "action": ...}, ...]}
  python3 -m evals.score evals/results/notes-<date>.jsonl

A note is correct when its predicted (lane, action) multiset equals the expected one.
Spec F1 acceptance: 18 of 20 notes correct.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(path):
    return {r["id"]: r for r in (json.loads(l) for l in Path(path).read_text().splitlines() if l.strip())}


def pairs(items):
    return Counter((i["lane"], i["action"]) for i in items)


def score(expected, predicted):
    rows, item_hits, item_total = [], 0, 0
    for nid, exp in expected.items():
        e = pairs(exp["expected"])
        p = pairs(predicted.get(nid, {}).get("items", []))
        item_total += sum(e.values())
        item_hits += sum((e & p).values())
        rows.append({"id": nid, "ok": e == p, "expected": sorted(e.elements()), "predicted": sorted(p.elements())})
    notes_ok = sum(r["ok"] for r in rows)
    return {
        "notes_correct": notes_ok,
        "notes_total": len(rows),
        "item_recall": round(item_hits / item_total, 3) if item_total else 0.0,
        "pass": notes_ok >= round(0.9 * len(rows)),
        "failures": [r for r in rows if not r["ok"]],
    }


if __name__ == "__main__":
    result = score(load(ROOT / "notes.jsonl"), load(sys.argv[1]))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["pass"] else 1)
