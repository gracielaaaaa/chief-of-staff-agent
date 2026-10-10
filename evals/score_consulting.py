"""Score the consulting workforce against the synthetic golden case (ADR 0008).

  python3 -m evals.score_consulting                       # check the checks: before fails, golden passes
  python3 -m evals.score_consulting --questions q.json --proposal p.md --cover c.txt

Model outputs are scored with the same code gates the skill uses, plus a few
rules the gates cannot see (one batch of questions, no fee in a default, the
cover email leads with the relationship).
"""
import argparse
import json
import re
from pathlib import Path

from datetime import datetime

from jobs.lib import confidential, facts, pricing, slots

ROOT = Path(__file__).resolve().parent
CASE = ROOT / "consulting"
FEE_WORDS = re.compile(r"\b(fee|price|pricing|investment|charge)\b", re.I)
RELATIONSHIP = re.compile(r"\b(thank|call|conversation|talk|great to|enjoyed|patience)\b", re.I)
STARTING_POINT = re.compile(r"\b(starting point|first pass|pre-read|to react to|draft|conversation)\b", re.I)


def load_case():
    return json.loads((CASE / "case.json").read_text())


def score_gate(text, case, resolved=True):
    return facts.gate(text, case["resolved_facts" if resolved else "facts"], case["other_client_terms"])


def score_questions(qs, case):
    qs = qs.get("questions", qs)
    text = [f"{q.get('q', '')} {q.get('why', '')}" for q in qs]
    fee_qs = [q for q in qs if FEE_WORDS.search(q.get("q", "")) and "per cohort" not in q.get("q", "")]
    return {
        "one_batch": len(qs) <= 12,
        "conflict_asked": any("4,500" in t and "1,500" in t for t in text),
        "overlap_asked": any(re.search(r"overlap|northwind", t, re.I) for t in text),
        "fee_asked": bool(fee_qs),
        "no_fee_in_defaults": all("$" not in (q.get("default") or q.get("recommended") or "") for q in fee_qs),
    }


def score_cover(text, case):
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith(("REVIEW", "Subject"))]
    opening = " ".join(lines[1:3])  # after the greeting
    want = [s["start"] for s in slots.find_slots(case["calendar"]["now"], case["calendar"]["deadline"], 30,
                                                 case["calendar"]["events"], json.loads((ROOT.parent / "config.json").read_text()),
                                                 3, {"start": "09:00", "end": "17:00"})]
    return {
        "flagged": text.startswith("REVIEW BEFORE SENDING"),
        "opens_with_relationship": bool(RELATIONSHIP.search(opening)) and "proposal" not in opening.lower(),
        "doc_as_starting_point": bool(STARTING_POINT.search(text)),
        "no_fee_in_email": "$" not in text,
        "three_free_call_times": len(re.findall(r"^\s*[-*] .*\d", text, re.M)) == 3 and len(want) == 3
                                 and all(datetime.fromisoformat(w).strftime("%b %-d") in text for w in want),
        "no_cross_client": not confidential.scan(text, case["other_client_terms"]),
        "no_em_dash": chr(0x2014) not in text,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions")
    ap.add_argument("--proposal", default=str(CASE / "golden_proposal.md"))
    ap.add_argument("--cover", default=str(CASE / "golden_cover.txt"))
    a = ap.parse_args()
    case = load_case()

    before = score_gate((CASE / "before_proposal.md").read_text(), case, resolved=False)
    after = score_gate(Path(a.proposal).read_text(), case)
    frame = pricing.frame(case["pricing_input"])
    out = {
        "conflicts_found": [(c["key"], c["ratio"]) for c in facts.conflicts(case["facts"])],
        "before_blocked": {"ready": before["ready"], "check_markers": before["check_markers"],
                           "untraced": before["untraced_numbers"], "cross_client": [h["term"] for h in before["cross_client"]]},
        "proposal_gate": after,
        "pricing_frame_has_no_fee": "fee" not in frame and all("fee" not in o for o in frame["options"]),
        "cover": score_cover(Path(a.cover).read_text(), case),
    }
    if a.questions:
        out["questions"] = score_questions(json.loads(Path(a.questions).read_text()), case)
    checks = [
        out["conflicts_found"] == [("Peer Coach price", 3.0)],
        not before["ready"] and before["check_markers"] >= 10 and before["cross_client"],
        after["ready"],
        out["pricing_frame_has_no_fee"],
        all(out["cover"].values()),
        all(out.get("questions", {}).values()),
    ]
    out["pass"] = all(checks)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
