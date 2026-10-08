"""Deterministic parts of edit learning (spec F5). The model proposes rules; code owns
the counting, activation, and metrics so the Sunday numbers are reproducible.

Usage:
  python -m jobs.lib.learn metrics '<json list of _State drafts rows as dicts>'
"""
import json
import sys
from datetime import datetime, timedelta, timezone

LIGHT_EDIT = 0.20


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso_week(ts: str) -> str:
    y, w, _ = _ts(ts).isocalendar()
    return f"{y}-W{w:02d}"


def is_rejected(draft: dict, now: str, after_days: int = 7) -> bool:
    """Open drafts with no matching sent mail after `after_days` count as rejected."""
    return draft.get("status") == "open" and _ts(now) - _ts(draft["created"]) >= timedelta(days=after_days)


def weekly_metrics(drafts: list[dict]) -> dict:
    """Aggregate by the ISO week the draft was created. Only sent drafts have a ratio."""
    out = {}
    for d in drafts:
        wk = out.setdefault(iso_week(d["created"]), {"drafts": 0, "sent": 0, "rejected": 0, "ratios": []})
        wk["drafts"] += 1
        if d.get("status") == "sent" and d.get("edit_ratio") not in (None, ""):
            wk["sent"] += 1
            wk["ratios"].append(float(d["edit_ratio"]))
        elif d.get("status") == "rejected":
            wk["rejected"] += 1
    for wk in out.values():
        r = wk.pop("ratios")
        wk["avg_edit_ratio"] = round(sum(r) / len(r), 4) if r else None
        wk["light_edit_share"] = round(sum(x < LIGHT_EDIT for x in r) / len(r), 4) if r else None
    return dict(sorted(out.items()))


def activations(observations: list[dict], threshold: int = 2) -> list[str]:
    """Candidate rules that have reached the evidence threshold (or were confirmed by her)."""
    return [o["id"] for o in observations
            if o.get("status") == "candidate"
            and (int(o.get("evidence_count", 0)) >= threshold or o.get("confirmed") in (True, "TRUE", "yes"))]


if __name__ == "__main__":
    cmd, arg = sys.argv[1], json.loads(sys.argv[2])
    if cmd == "metrics":
        print(json.dumps(weekly_metrics(arg), indent=2))
