#!/usr/bin/env python3
"""PreToolUse guardrail: enforces "drafts, never sends" in code, not prompts.

Connector tool names carry an environment-specific server prefix
(mcp__<server-id>__<tool>), so rules match on the tool suffix.

Exit 0 = allow, exit 2 = block (stderr is shown to the model).
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from jobs.lib.sensitive import find_secrets  # noqa: E402

# Allow list, not block list: any connector tool not named here is blocked,
# so newly attached connectors (or new tools on old ones) can't act by default.
# Spec section 4, principle 1: drafts, never sends.
READ = re.compile(r"^(get_.*|list_.*|search_.*|read_.*|query_.*|check_.*)$")

# Attachments and file downloads are where statements, tax forms, and offer letters live.
NEVER_READ = re.compile(r".*(attachment|download).*")

# Writes the agent needs. Blocked in dry-run and when paused.
WRITE = {
    "create_draft", "update_draft",                       # Gmail drafts, never sends
    "create_label", "label_message", "label_thread",      # Gmail labels (Agent/*)
    "unlabel_message", "unlabel_thread",
    "create_event", "update_event",                       # Calendar, primary only
    "create_file", "update_file",                         # Drive create, rename, move
    "append_values", "update_values", "update_formulas",  # Sheets
    "update_spreadsheet", "insert_dimension",
    "update_doc",                                         # Docs
}

# Harness and session tools, not data connectors. Not used by scheduled jobs.
HARNESS_SERVERS = re.compile(
    r"^mcp__(ccd_[a-z_]+|mcp-registry|visualize|Claude_Browser|Claude_Code_iOS_Simulator|terminal|scheduled-tasks)__"
)


# Structural deletes inside otherwise-allowed batch edits (Sheets/Docs).
# Ledger rows are never removed; they get status=dropped instead.
DESTRUCTIVE_REQUESTS = re.compile(r'"(deleteSheet|deleteDimension|deleteDocumentTab|deleteTab)"')


def tool_suffix(name: str) -> str:
    if name.startswith("mcp__"):
        return name.split("__", 2)[-1]
    return name


def load_config() -> dict:
    try:
        return json.loads((ROOT / "config.json").read_text())
    except (OSError, ValueError):
        return {}


def truthy(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes"}


def decide(tool_name: str, env: dict, config: dict, tool_input=None) -> tuple[bool, str]:
    if not tool_name.startswith("mcp__"):
        return True, ""
    if HARNESS_SERVERS.match(tool_name):
        return True, ""
    suffix = tool_suffix(tool_name)
    if NEVER_READ.match(suffix):
        return False, (
            f"BLOCKED by guardrail: '{suffix}' reads attachments or downloads files, which this "
            "agent never does (financial and personal documents live there)."
        )
    if not READ.match(suffix) and suffix not in WRITE:
        return False, (
            f"BLOCKED by guardrail: '{suffix}' is not on the allow list. This agent only "
            "reads, creates drafts, events, and files in its own folder. Record the intended "
            "action in the review doc for Graciela instead."
        )
    if DESTRUCTIVE_REQUESTS.search(json.dumps(tool_input or {})):
        return False, (
            "BLOCKED by guardrail: deleting sheets, rows, columns, or tabs is never allowed. "
            "Mark ledger items status=dropped instead."
        )
    if suffix in WRITE:
        secrets = find_secrets(json.dumps(tool_input or {}, ensure_ascii=False))
        if secrets:
            return False, (
                f"BLOCKED by guardrail: this write contains what looks like a {', '.join(secrets)}. "
                "Financial details and login credentials never go into drafts, sheets, docs, or events. "
                "Skip that content, log 'skipped: sensitive', and continue."
            )
        if truthy(env.get("DRY_RUN")) or config.get("dry_run"):
            return False, (
                f"DRY RUN: '{suffix}' was not executed. Print the intended action "
                "(tool, arguments, dedupe key) and continue."
            )
        if truthy(env.get("PAUSED")) or config.get("paused"):
            return False, "PAUSED: kill switch is on. Stop the run without writing anything."
    return True, ""


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        print("guardrail: unreadable hook input, blocking to be safe", file=sys.stderr)
        return 2
    ok, reason = decide(event.get("tool_name", ""), dict(os.environ), load_config(), event.get("tool_input"))
    if ok:
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
