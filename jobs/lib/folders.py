"""Drive folders the agent may create files in (enforced by the guardrail hook).

The ids are never in the repo (public). `run-common` Start resolves the
`Chief of Staff` folder and its subfolders by name and writes them here each
run; skills add a folder right after creating one (e.g. Consulting/<Client>).
The hook also accepts a comma-separated `COS_ALLOWED_FOLDERS` env var.

Usage:
  python3 -m jobs.lib.folders set <id> [<id> ...]
  python3 -m jobs.lib.folders add <id>
  python3 -m jobs.lib.folders show
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_FILE = ROOT / "state" / "allowed_folders.json"


def load(env: dict | None = None, path: Path | None = None) -> set[str]:
    path = path or ALLOWED_FILE
    ids = {i.strip() for i in (env or {}).get("COS_ALLOWED_FOLDERS", "").split(",") if i.strip()}
    try:
        ids |= set(json.loads(path.read_text()).get("folders", []))
    except (OSError, ValueError):
        pass
    return ids


def save(ids, path: Path | None = None) -> None:
    path = path or ALLOWED_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"folders": sorted(set(ids))}, indent=2) + "\n")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "set":
        save(args)
    elif cmd == "add":
        save(load() | set(args))
    elif cmd != "show":
        sys.exit(f"unknown command {cmd}")
    print(json.dumps(sorted(load())))
