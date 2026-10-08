"""Deterministic helpers for Canvas data (used by canvas-sync and the course-deadline step).

Canvas returns due dates in UTC. "2026-10-13T06:59:00Z" is Monday Oct 12, 11:59pm Pacific,
so every date must be converted before it is shown or scheduled.

Usage:
  python -m jobs.lib.canvas due '2026-10-13T06:59:00Z'
  python -m jobs.lib.canvas text '<html>'
"""
import html
import json
import re
import sys
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Los_Angeles")
_DROP_BLOCKS = re.compile(r"<(script|style)\b.*?</\1>|<link\b[^>]*>|<img\b[^>]*>", re.S | re.I)
_BOILERPLATE = re.compile(r"When replying to peers, we encourage you to use the @ feature.*", re.S | re.I)
_UNTRUSTED = re.compile(r"<<<(?:END )?UNTRUSTED CANVAS CONTENT[^>]*>>>")


def due_local(utc_iso: str) -> datetime:
    return datetime.fromisoformat(utc_iso.replace("Z", "+00:00")).astimezone(TZ)


def reminder_at(utc_iso: str, hours_before: int = 48, at: time = time(9, 0)) -> datetime:
    """The 48 h reminder lands at 9:00am Pacific on the day that is `hours_before` earlier,
    never at 11:59pm."""
    target = due_local(utc_iso) - timedelta(hours=hours_before)
    return datetime.combine(target.date(), at, TZ)


def html_to_text(raw: str, limit: int = 3000) -> str:
    s = _UNTRUSTED.sub("", raw or "")
    s = _DROP_BLOCKS.sub("", s)
    s = re.sub(r"<li[^>]*>", "\n- ", s, flags=re.I)
    s = re.sub(r"<(br|/p|/div|/li|hr)[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = _BOILERPLATE.sub("", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n\s*\n+", "\n", s).strip()
    return s[:limit]


if __name__ == "__main__":
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "due":
        d = due_local(arg)
        print(json.dumps({"due_local": d.isoformat(), "display": d.strftime("%a %b %-d, %-I:%M%p"),
                          "reminder_48h": reminder_at(arg).isoformat()}))
    elif cmd == "text":
        print(html_to_text(arg))


def daily_digests(items, hours_before: int = 48, at: time = time(9, 0)):
    """Group not-submitted graded items into one reminder per day.

    items: dicts with title, course, due_utc, status, link (rows of Courses/Upcoming).
    Returns [{"at": iso, "items": [...]}] sorted by time, one entry per day.
    """
    days = {}
    for it in items:
        if it.get("status") == "submitted":
            continue
        when = reminder_at(it["due_utc"], hours_before, at)
        days.setdefault(when, []).append(it)
    return [{"at": k.isoformat(), "items": sorted(v, key=lambda i: i["due_utc"])} for k, v in sorted(days.items())]
