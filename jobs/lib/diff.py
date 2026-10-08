"""Edit ratio between an agent draft and what Graciela actually sent (spec section 3).

edit ratio = character-level edit distance / draft length
"""
import re
import sys
import json
from difflib import SequenceMatcher

_QUOTE_MARKERS = (
    # Gmail wraps long attributions: "On Tue, Oct 6, 2026 at 11:33 PM Name <\nemail> wrote:"
    re.compile(r"^On [^\n]{0,200}(?:\n[^\n]{0,200}){0,2}?wrote:\s*$", re.M),
    re.compile(r"^-+ ?Original Message ?-+", re.M | re.I),
    re.compile(r"^From: .+$", re.M),
)


def strip_quoted(body: str) -> str:
    """Drop the quoted thread history Gmail appends to replies."""
    cut = len(body)
    for pat in _QUOTE_MARKERS:
        m = pat.search(body)
        if m:
            cut = min(cut, m.start())
    lines = [ln for ln in body[:cut].splitlines() if not ln.lstrip().startswith(">")]
    return "\n".join(lines).strip()


def normalize(body: str) -> str:
    body = strip_quoted(body)
    body = body.replace("\r\n", "\n")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def edit_distance(a: str, b: str) -> int:
    """Characters inserted, deleted, or replaced to turn a into b."""
    dist = 0
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            dist += max(i2 - i1, j2 - j1)
    return dist


def edit_ratio(draft: str, sent: str) -> float:
    d, s = normalize(draft), normalize(sent)
    if not d:
        return 1.0 if s else 0.0
    return round(edit_distance(d, s) / len(d), 4)


def light_edit(ratio: float, threshold: float = 0.20) -> bool:
    return ratio < threshold


if __name__ == "__main__":
    # Usage: python -m jobs.lib.diff '{"draft": "...", "sent": "..."}'
    payload = json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read())
    r = edit_ratio(payload["draft"], payload["sent"])
    print(json.dumps({"edit_ratio": r, "light_edit": light_edit(r)}))
