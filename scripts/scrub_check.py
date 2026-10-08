#!/usr/bin/env python3
"""Block commits that would publish real people, accounts, or Drive IDs.

The repo is public (portfolio). Real names live in private/scrub_terms.txt
(gitignored), one term per line. Run as a pre-commit hook or by hand:
  python3 scripts/scrub_check.py            # staged files
  python3 scripts/scrub_check.py --all      # every tracked + untracked file
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS_FILE = ROOT / "private" / "scrub_terms.txt"
SKIP = {"scripts/scrub_check.py"}

PATTERNS = {
    "real email address": re.compile(r"[\w.+-]+@(?!([\w-]+\.)*example\.(com|org|edu)\b)[\w-]+\.[\w.]+", re.I),
    "Google Drive/Docs link": re.compile(r"(docs|drive)\.google\.com/\S*/d/[\w-]{20,}"),
    "calendar id": re.compile(r"[\w]{20,}@(group|import)\.calendar\.google\.com"),
}


def files(all_files: bool) -> list[str]:
    if all_files:
        cmd = ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
    else:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f and f not in SKIP]


def terms() -> list[str]:
    if not TERMS_FILE.exists():
        return []
    return [t.strip() for t in TERMS_FILE.read_text().splitlines() if t.strip() and not t.startswith("#")]


def scan(path: str, private_terms: list[str]) -> list[str]:
    try:
        text = (ROOT / path).read_text(errors="ignore")
    except OSError:
        return []
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for label, pat in PATTERNS.items():
            if pat.search(line):
                hits.append(f"{path}:{n}: {label}")
        low = line.lower()
        for t in private_terms:
            if t.lower() in low:
                hits.append(f"{path}:{n}: private term")
    return hits


def main() -> int:
    if not TERMS_FILE.exists():
        print("scrub_check: private/scrub_terms.txt is missing; refusing to pass.", file=sys.stderr)
        return 1
    private_terms = terms()
    hits = [h for f in files("--all" in sys.argv) for h in scan(f, private_terms)]
    if hits:
        print("scrub_check: possible private data, commit blocked:\n  " + "\n  ".join(hits), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
