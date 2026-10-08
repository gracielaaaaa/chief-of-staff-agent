"""Find a free calendar slot for a TASK before its deadline (spec F1).

Plain code, no model: the skill passes in events from the primary calendar
and gets back a slot or null.

Usage:
  python -m jobs.lib.slots '{"now": "...", "deadline": "...", "duration_min": 60,
                             "events": [{"start": "...", "end": "...",
                                         "colorId": "9", "transparency": "opaque"}]}'
"""
import json
import sys
from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STEP = timedelta(minutes=15)
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _parse(ts: str, tz: ZoneInfo) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _hm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def _round_up(dt: datetime) -> datetime:
    dt = dt.replace(second=0, microsecond=0)
    extra = dt.minute % 15
    return dt + timedelta(minutes=(15 - extra) % 15)


def busy_intervals(events, protected_colors, tz):
    """Opaque events block time. Protected colors block time even if marked free.
    All-day events (date only) are ignored unless protected."""
    out = []
    for ev in events:
        color = str(ev.get("colorId") or "")
        protected = color in protected_colors
        if ev.get("transparency") == "transparent" and not protected:
            continue
        start, end = ev.get("start"), ev.get("end")
        if not start or not end:
            continue
        if len(start) == 10 and not protected:  # all-day, e.g. "2026-10-08"
            continue
        out.append((_parse(start, tz), _parse(end, tz)))
    return out


def weekly_intervals(blocks, day_start: datetime, tz):
    out = []
    for b in blocks:
        if DAYS[day_start.weekday()] != b["day"]:
            continue
        d = day_start.date()
        out.append((datetime.combine(d, _hm(b["start"]), tz), datetime.combine(d, _hm(b["end"]), tz)))
    return out


def find_slot(now, deadline, duration_min, events, config):
    tz = ZoneInfo(config.get("timezone", "America/Los_Angeles"))
    now, deadline = _parse(now, tz), _parse(deadline, tz)
    dur = timedelta(minutes=int(duration_min))
    hours = config.get("working_hours", {"start": "08:00", "end": "21:00"})
    prot = config.get("protected", {})
    busy = busy_intervals(events, {str(c) for c in prot.get("color_ids", [])}, tz)

    cursor = _round_up(now)
    while cursor + dur <= deadline:
        day_open = datetime.combine(cursor.date(), _hm(hours["start"]), tz)
        day_close = datetime.combine(cursor.date(), _hm(hours["end"]), tz)
        if cursor < day_open:
            cursor = day_open
            continue
        if cursor + dur > day_close:
            cursor = datetime.combine(cursor.date() + timedelta(days=1), _hm(hours["start"]), tz)
            continue
        end = cursor + dur
        blocked = busy + weekly_intervals(prot.get("weekly_blocks", []), cursor, tz)
        clash = [b for b in blocked if b[0] < end and cursor < b[1]]
        if not clash:
            return {"start": cursor.isoformat(), "end": end.isoformat()}
        cursor = _round_up(max(b[1] for b in clash))
    return None


if __name__ == "__main__":
    args = json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read())
    cfg = json.loads((ROOT / "config.json").read_text())
    print(json.dumps(find_slot(args["now"], args["deadline"], args["duration_min"], args.get("events", []), cfg)))
