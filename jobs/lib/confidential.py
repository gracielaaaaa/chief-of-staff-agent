"""Client firewall: nothing about one client appears in another client's work (ADR 0008).

Plain code, no model. The term list is built at runtime from the private Lane
Context doc (other clients' names, contacts, product and program names,
internal figures) and is never stored in the repo.

Term: {"client": "Northwind", "term": "Care Navigator Academy"}

Usage:
  python -m jobs.lib.confidential '{"text": "...", "terms": [...], "sources": [...], "allowed_folders": [...]}'
"""
import json
import re
import sys


def scan(text: str, terms: list[dict]) -> list[dict]:
    """Case-insensitive whole-phrase matches, with a short snippet for the review doc."""
    hits = []
    for t in terms:
        phrase = (t.get("term") or "").strip()
        if len(phrase) < 3:
            continue
        for m in re.finditer(rf"(?<!\w){re.escape(phrase)}(?!\w)", text or "", re.I):
            a, b = max(0, m.start() - 40), min(len(text), m.end() + 40)
            hits.append({"client": t.get("client", ""), "term": phrase, "snippet": text[a:b].replace("\n", " ")})
            break
    return hits


def sources_outside(sources: list[str], allowed_folders: list[str]) -> list[str]:
    """Sources (Drive paths or doc titles) that do not belong to this client's folder.
    Every claim the synthesizer makes carries a source; one from another client's
    folder is a leak even if no term matches."""
    allowed = [a.rstrip("/").lower() + "/" for a in allowed_folders]
    return [s for s in sources if not any((s or "").lower().startswith(a) for a in allowed)]


if __name__ == "__main__":
    a = json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read())
    print(json.dumps({
        "hits": scan(a.get("text", ""), a.get("terms", [])),
        "sources_outside": sources_outside(a.get("sources", []), a.get("allowed_folders", [])),
    }))
