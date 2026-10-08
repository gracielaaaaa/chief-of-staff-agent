"""Cheap code filters before promise detection (spec F3). Calendar receipts, emoji
reactions, and invites are never promises, so they never reach the model."""
import re

_AUTOMATED = re.compile(
    r"^(This event has been updated|Booked by |.{0,80}has (accepted|declined|tentatively accepted) this invitation"
    r"|👍 .{0,60}reacted via Gmail|.{0,80}is inviting you to a scheduled Zoom meeting"
    r"|.{0,80}You have been invited by|Invitation:|Updated invitation)",
    re.S,
)


def is_automated(snippet: str) -> bool:
    return bool(_AUTOMATED.match((snippet or "").strip()))


def excluded(recipients: list[str], snippet: str, domains: list[str], keywords: list[str]) -> bool:
    """config.exclusions: employer mail stays out of the system."""
    if any(r.lower().endswith("@" + d) for r in recipients for d in domains):
        return True
    return any(k.lower() in (snippet or "").lower() for k in keywords)


_STUDENT_SIGNALS = re.compile(r"\b(DSP|accommodation|exam|quiz|grade|graded|credit|attendance|absence|section|InQuizitive|office hours|extension|deduction)", re.I)
_STAFF_TYPES = {"instructor", "teammate", "client"}


def redact_who(item: dict) -> dict:
    """Privacy backstop: if the model did not call a coursework recipient a student,
    code does. Only instructors, teammates, and clients keep a name."""
    text = " ".join(str(item.get(k, "")) for k in ("what", "quote"))
    if item.get("who_type") not in _STAFF_TYPES and _STUDENT_SIGNALS.search(text):
        item = {**item, "who": "student", "who_type": "student"}
    return item


def triage(item: dict, today: str) -> str:
    """'open' for future work, 'confirm' for past-due items on a first run (ask her once
    instead of flooding the ledger)."""
    due = (item.get("due") or "")[:10]
    return "confirm" if due and due < today else "open"
