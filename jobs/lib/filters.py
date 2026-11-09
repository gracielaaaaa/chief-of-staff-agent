"""Capture and triage screens that used to live only in skill prose (issues 5 and 9).

Plain code, no model, so a regression test can catch them coming back.

Usage:
  python -m jobs.lib.filters accepted '{"sender": "Maya <maya@example.edu>", "addresses": ["maya@example.edu"]}'
  python -m jobs.lib.filters drop '{"thread": {"messages": [{"labelIds": ["L1"]}]}, "label_ids": ["L1"]}'
"""
import json
import re
import sys
from email.utils import parseaddr

_ANGLE = re.compile(r"<([^<>]+)>")


def address(sender: str) -> str:
    """Bare lowercase address from a From header ("Name <name@example.com>" or a bare address)."""
    m = _ANGLE.search(sender or "")
    addr = m.group(1) if m else parseaddr(sender or "")[1]
    return addr.strip().lower()


def accepted_sender(sender: str, addresses: list[str]) -> bool:
    """The prompt-injection boundary: only her own addresses (Lane Context `My addresses`,
    which includes her phone's personal mail) may give the agent instructions. Exact
    match on the bare address, so display names and lookalike domains do not pass."""
    return bool(address(sender)) and address(sender) in {a.strip().lower() for a in addresses}


def has_any_label(thread: dict, label_ids: list[str]) -> bool:
    """Gmail search ignores `-label:` with ids, so the label screen runs here, on every
    message in the thread."""
    wanted = set(label_ids)
    return any(wanted & set(m.get("labelIds") or []) for m in thread.get("messages") or [])


if __name__ == "__main__":
    cmd, args = sys.argv[1], json.loads(sys.argv[2])
    if cmd == "accepted":
        print(json.dumps(accepted_sender(args["sender"], args["addresses"])))
    elif cmd == "drop":
        print(json.dumps(has_any_label(args["thread"], args["label_ids"])))
    else:
        sys.exit(f"unknown command {cmd}")
