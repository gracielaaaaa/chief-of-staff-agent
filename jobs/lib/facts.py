"""Fact table and send-ready gate for consulting docs (ADR 0008).

Plain code, no model. Every number in a proposal must trace to a fact with a
source, two sources that disagree on the same fact become a question, and a
doc with any `[CHECK` marker, untraced number, or cross-client hit is not
ready to send.

Fact: {"key": "pilot price", "value": "$4,500 per cohort", "source": "questionnaire Q7"}

Usage:
  python -m jobs.lib.facts extract '<text>'
  python -m jobs.lib.facts conflicts '<json list of facts>'
  python -m jobs.lib.facts gate '{"draft": "...", "facts": [...], "other_client_terms": [...]}'
"""
import json
import re
import sys

from jobs.lib import confidential

UNITS = (
    "participant|learner|student|member|employee|user|client|customer|"
    "session|workshop|module|cohort|program|course|location|site|"
    "hour|day|week|month|year|call|interview|deliverable"
)
MONEY = re.compile(
    r"\$\s?(\d[\d,]*(?:\.\d+)?)\s?([kKmM])?\b(?:\s*(?:/|per|a|each)\s*(\w+))?"
)
PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s?(?:%|percent\b)")
COUNT = re.compile(rf"\b(\d[\d,]*(?:\.\d+)?)\s?(?:-\s?)?((?:{UNITS})s?|people|staff)\b", re.I)
CHECK = re.compile(r"\[CHECK", re.I)
TOLERANCE = 0.005


def _num(s: str, mult: str = "") -> float:
    v = float(s.replace(",", ""))
    return v * {"k": 1e3, "m": 1e6}.get((mult or "").lower(), 1)


def _unit(u: str) -> str:
    u = (u or "").lower()
    return u[:-1] if u.endswith("s") and len(u) > 3 else u


def extract(text: str) -> list[dict]:
    """Numbers that make a claim: money (with its per-unit), percents, and counts
    with a unit. Bare numbers ("Option 2", "Phase 1") are not claims."""
    out, taken = [], []
    for m in MONEY.finditer(text or ""):
        per = _unit(m.group(3)) if m.group(3) and m.group(3).lower() not in ("and", "or", "to") else ""
        out.append({"kind": "money", "value": _num(m.group(1), m.group(2)), "per": per, "raw": m.group(0).strip()})
        taken.append(m.span())
    for m in PERCENT.finditer(text or ""):
        out.append({"kind": "percent", "value": float(m.group(1)), "per": "", "raw": m.group(0)})
        taken.append(m.span())
    for m in COUNT.finditer(text or ""):
        if any(a <= m.start() < b for a, b in taken):
            continue
        out.append({"kind": "count", "value": _num(m.group(1)), "per": _unit(m.group(2)), "raw": m.group(0)})
    return out


def _same(a: dict, b: dict) -> bool:
    if a["kind"] != b["kind"] or (a["per"] and b["per"] and a["per"] != b["per"]):
        return False
    if a["kind"] == "count" and a["per"] != b["per"]:
        return False
    hi = max(abs(a["value"]), abs(b["value"]), 1e-9)
    return abs(a["value"] - b["value"]) / hi <= TOLERANCE


def _norm_key(k: str) -> str:
    return re.sub(r"\s+", " ", (k or "").strip().lower())


def conflicts(facts: list[dict]) -> list[dict]:
    """Same key, values that do not match. Each conflict lists every value with its
    source, so the question can show them side by side."""
    by_key: dict[str, list[dict]] = {}
    for f in facts:
        by_key.setdefault(_norm_key(f["key"]), []).append(f)
    out = []
    for k, fs in by_key.items():
        nums = [(f, extract(str(f["value"]))) for f in fs]
        nums = [(f, n[0]) for f, n in nums if n]
        if len(nums) < 2:
            continue
        base = nums[0][1]
        if any(not _same(base, n) for _, n in nums[1:]):
            vals = [n["value"] for _, n in nums]
            out.append({
                "key": fs[0]["key"],
                "values": [{"value": f["value"], "source": f.get("source", "")} for f, _ in nums],
                "ratio": round(max(vals) / min(vals), 2) if min(vals) > 0 else None,
            })
    return out


def untraced(draft: str, facts: list[dict], allow: list[str] | None = None) -> list[str]:
    """Numbers in the draft that match no fact. `allow` holds raw strings that are
    fine without a source (her own answers already added as facts are better)."""
    known = [n for f in facts for n in extract(str(f["value"]))]
    allowed = {a.strip().lower() for a in (allow or [])}
    out = []
    for n in extract(draft):
        if n["raw"].lower() in allowed:
            continue
        if not any(_same(n, k) for k in known):
            out.append(n["raw"])
    return out


def check_markers(draft: str) -> int:
    return len(CHECK.findall(draft or ""))


def gate(draft: str, facts: list[dict], other_client_terms: list[dict] | None = None,
         allow: list[str] | None = None) -> dict:
    """Send-ready only when every count is zero."""
    result = {
        "check_markers": check_markers(draft),
        "untraced_numbers": untraced(draft, facts, allow),
        "conflicts": conflicts(facts),
        "cross_client": confidential.scan(draft, other_client_terms or []),
        "em_dashes": (draft or "").count(chr(0x2014)),
    }
    result["ready"] = not any([result["check_markers"], result["untraced_numbers"], result["conflicts"],
                               result["cross_client"], result["em_dashes"]])
    return result


if __name__ == "__main__":
    cmd, arg = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read()
    if cmd == "extract":
        print(json.dumps(extract(arg)))
    elif cmd == "conflicts":
        print(json.dumps(conflicts(json.loads(arg))))
    elif cmd == "gate":
        a = json.loads(arg)
        print(json.dumps(gate(a["draft"], a["facts"], a.get("other_client_terms"), a.get("allow"))))
    else:
        sys.exit(f"unknown command {cmd}")
