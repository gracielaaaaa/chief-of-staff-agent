"""Render the daily review doc (spec principle 2: one review queue).

The model gathers items; code renders them, so the doc looks the same every day
and never contains student names (callers pass `student`, this module checks).

Usage:
  python -m jobs.lib.review '<json>'   # prints HTML for Drive create_file (text/html)
"""
import html
import json
import sys

SECTIONS = [
    ("needs_you", "Needs you"),
    ("drafts", "Drafts to review"),
    ("booked", "Booked"),
    ("ledger", "Ledger changes"),
    ("skipped", "Skipped"),
]


def _li(item: dict) -> str:
    text = html.escape(item["text"])
    if item.get("link"):
        text = f'<a href="{html.escape(item["link"], quote=True)}">{text}</a>'
    if item.get("flag"):
        text = f"<b>REVIEW BEFORE SENDING</b> ({html.escape(item['flag'])}): {text}"
    return f"<li>{text}</li>"


def render(date: str, sections: dict, summary: str = "") -> str:
    """sections: {"drafts": [{"text": ..., "link": ..., "flag": ...}], ...}
    Flagged drafts are listed first. Empty sections are omitted."""
    out = [f"<h1>Review {html.escape(date)}</h1>"]
    if summary:
        out.append(f"<p>{html.escape(summary)}</p>")
    for key, title in SECTIONS:
        items = list(sections.get(key) or [])
        if not items:
            continue
        if key == "drafts":
            items.sort(key=lambda i: not i.get("flag"))
        out.append(f"<h2>{title}</h2><ul>{''.join(_li(i) for i in items)}</ul>")
    doc = "".join(out)
    if "—" in doc:
        raise ValueError("em dash in review doc")
    return doc


def render_text(run_label: str, sections: dict) -> str:
    """Plain-text block appended to the end of an existing review doc (no read-back needed)."""
    lines = ["", f"Run {run_label}"]
    for key, title in SECTIONS:
        items = list(sections.get(key) or [])
        if not items:
            continue
        if key == "drafts":
            items.sort(key=lambda i: not i.get("flag"))
        lines.append(title)
        for i in items:
            flag = f"REVIEW BEFORE SENDING ({i['flag']}): " if i.get("flag") else ""
            link = f" {i['link']}" if i.get("link") else ""
            lines.append(f"- {flag}{i['text']}{link}")
    text = "\n".join(lines) + "\n"
    if "\u2014" in text:
        raise ValueError("em dash in review doc")
    return text


def counts(sections: dict) -> str:
    """Popup title, e.g. '[Agent] 3 drafts, 2 booked, 1 question'."""
    n = {k: len(sections.get(k) or []) for k, _ in SECTIONS}
    q = n["needs_you"]
    return f"[Agent] {n['drafts']} drafts, {n['booked']} booked, {q} question{'s' if q != 1 else ''}"


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--text":
        a = json.loads(sys.argv[2])
        print(render_text(a["run"], a["sections"]), end="")
    else:
        a = json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read())
        print(render(a["date"], a["sections"], a.get("summary", "")))
