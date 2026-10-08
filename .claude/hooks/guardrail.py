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

# Never allowed, in any mode. Spec section 4, principle 1.
FORBIDDEN = re.compile(
    r"^(send_.*|forward|reply|delete|reply_to_.*|post_.*|share_file|trash_.*|"
    r"delete_.*|bulk_.*|mark_.*_spam|respond_to_event|grade_.*|assign_.*|"
    r"associate_.*|fix_.*|upload_.*|create_announcement|create_discussion_topic|"
    r"create_assignment|create_rubric.*|create_module|create_page|create_content_migration|"
    r"update_assignment|update_discussion_topic|update_module.*|update_page.*|edit_page_content|"
    r"add_module_item|mark_conversations_read)$"
)

# Writes that are allowed normally but blocked in dry-run or when paused.
WRITE = re.compile(
    r"^(create_.*|update_.*|label_.*|unlabel_.*|untrash_.*|copy_file|"
    r"apply_.*_label|unmark_.*_spam)$"
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
    suffix = tool_suffix(tool_name)
    if FORBIDDEN.match(suffix):
        return False, (
            f"BLOCKED by guardrail: '{suffix}' is never allowed. This agent only "
            "creates drafts, events, and Drive files. Record the intended action "
            "in the review doc for Graciela instead."
        )
    if DESTRUCTIVE_REQUESTS.search(json.dumps(tool_input or {})):
        return False, (
            "BLOCKED by guardrail: deleting sheets, rows, columns, or tabs is never allowed. "
            "Mark ledger items status=dropped instead."
        )
    if WRITE.match(suffix):
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
