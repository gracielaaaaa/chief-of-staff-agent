"""Pricing frame: the math behind the fee question, never the fee (ADR 0008).

Plain code, no model. The rate comes from the private Pricing doc at runtime;
there is no default, so a missing rate is a question, not a guess.

Input:
  {"rate": 150,
   "options": [{"name": "Pilot", "hours_low": 20, "hours_high": 30}],
   "anchors": [{"label": "their current program price", "value": 4500, "source": "questionnaire Q7"}],
   "budget": {"low": 5000, "high": 8000, "source": "call notes"},
   "levers": [{"name": "drop the second workshop", "hours_delta": -6}]}

Usage:
  python -m jobs.lib.pricing '<json>'
"""
import json
import sys

ROUND = 50


def _r(x: float) -> int:
    return int(round(x / ROUND) * ROUND)


def frame(args: dict) -> dict:
    rate = args.get("rate")
    if not rate:
        return {"error": "no rate in the Pricing doc", "question": "What hourly rate (or floor) should this be built on?"}
    budget = args.get("budget") or {}
    out = []
    for o in args.get("options", []):
        low, high = _r(rate * o["hours_low"]), _r(rate * o["hours_high"])
        row = {"name": o["name"], "hours": [o["hours_low"], o["hours_high"]], "cost_basis": [low, high]}
        if budget.get("high"):
            row["vs_budget"] = ("under" if high <= budget["high"] and low >= budget.get("low", 0)
                                else "over" if low > budget["high"] else "overlaps")
        out.append(row)
    levers = [{"name": l["name"], "hours_delta": l["hours_delta"], "fee_delta": _r(rate * l["hours_delta"])}
              for l in args.get("levers", [])]
    return {
        "rate": rate,
        "options": out,
        "anchors": args.get("anchors", []),
        "budget": budget or None,
        "levers": levers,
        "decision": "Graciela picks the fee. These are cost-basis ranges, not quotes.",
    }


if __name__ == "__main__":
    print(json.dumps(frame(json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()))))
