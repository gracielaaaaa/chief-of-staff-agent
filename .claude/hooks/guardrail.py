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
from jobs.lib import folders  # noqa: E402
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

# Kit (newsletter platform) draft-building actions, allowed on the Kit connector only.
# Emails are created and edited unpublished; publishing, sending, and deleting stay
# blocked because they are not on any list. The Kit connector's server id lives in
# state/kit_connector.txt (gitignored) or the KIT_CONNECTOR env var; without it, none of these run.
KIT_DRAFTS = {
    "create_sequence", "create_sequence_email", "create_landing_page",
    "create_custom_field", "bulk_create_custom_fields", "create_tag", "bulk_create_tags",
    "update_sequence_email",   # emails stay unpublished (published: true is blocked)
    "update_landing_page",     # Graciela approved edits to the published signup page
    "create_broadcast", "update_broadcast",  # always drafts; scheduling and sending stay in Kit's UI
}
KIT_FILE = ROOT / "state" / "kit_connector.txt"


def kit_connector(env: dict) -> str:
    if env.get("KIT_CONNECTOR"):
        return env["KIT_CONNECTOR"].strip()
    try:
        return KIT_FILE.read_text().strip()
    except OSError:
        return ""


def kit_block(tool_name: str, suffix: str, env: dict, tool_input) -> str:
    """Reason to block a Kit draft action, or "" if it may run."""
    kit = kit_connector(env)
    server = tool_name.split("__")[1] if tool_name.count("__") >= 2 else ""
    if not kit or server != kit:
        return f"BLOCKED by guardrail: '{suffix}' is only allowed on the Kit connector."
    if (tool_input or {}).get("published") is True:
        return "BLOCKED by guardrail: Kit content is created unpublished. Graciela publishes it in Kit."
    if (tool_input or {}).get("public") is True:
        return "BLOCKED by guardrail: broadcasts stay off the public newsletter site. Graciela publishes in Kit."
    return ""


# WordPress (the consulting client's website), allowed on the WordPress connector only.
# Reads are open. Writes create draft or pending pages and posts, and update only drafts
# this agent created (their ids are recorded after each create in state/wp_drafts.json).
# Publishing, scheduling, editing live pages, section edits, media, menus, settings, and
# deletes are not on any list. Graciela publishes in WordPress.
# The connector's server id lives in state/wp_connector.txt (gitignored) or WP_CONNECTOR.
WP_READ = {
    "wpcom-user-sites", "docs", "wpcom-site-settings", "wpcom-rendered-page-get",
    "wpcom-mcp-pages-list", "wpcom-mcp-pages-get", "wpcom-mcp-posts-list", "wpcom-mcp-posts-get",
    "wpcom-mcp-media-list", "wpcom-mcp-media-get", "wpcom-mcp-content-search", "wpcom-mcp-site-posts-search",
    "wpcom-page-sections-list", "wpcom-post-sections-list", "wpcom-templates-list", "wpcom-templates-get",
    "wpcom-theme-active", "wpcom-global-styles-get",
}
WP_CREATE = {"wpcom-mcp-pages-create", "wpcom-mcp-posts-create"}
WP_UPDATE = {"wpcom-mcp-pages-update", "wpcom-mcp-posts-update"}
WP_DRAFT_STATUS = {"draft", "pending"}
WP_FILE = ROOT / "state" / "wp_connector.txt"
WP_DRAFTS_FILE = ROOT / "state" / "wp_drafts.json"


def wp_connector(env: dict) -> str:
    if env.get("WP_CONNECTOR"):
        return env["WP_CONNECTOR"].strip()
    try:
        return WP_FILE.read_text().strip()
    except OSError:
        return ""


def wp_drafts() -> set:
    try:
        return {int(i) for i in json.loads(WP_DRAFTS_FILE.read_text())}
    except (OSError, ValueError, TypeError):
        return set()


def wp_block(tool_name: str, suffix: str, env: dict, tool_input) -> str:
    """Reason to block a WordPress action, or "" if it may run."""
    wp = wp_connector(env)
    server = tool_name.split("__")[1] if tool_name.count("__") >= 2 else ""
    if not wp or server != wp:
        return f"BLOCKED by guardrail: '{suffix}' is only allowed on the WordPress connector."
    ti = tool_input or {}
    if suffix in WP_CREATE | WP_UPDATE:
        status = ti.get("status")
        if status is not None and status not in WP_DRAFT_STATUS:
            return ("BLOCKED by guardrail: WordPress pages and posts stay drafts (status draft or pending). "
                    "Graciela publishes in WordPress.")
        if ti.get("date"):
            return "BLOCKED by guardrail: setting a date can schedule a post. Leave scheduling to Graciela."
    if suffix in WP_UPDATE:
        try:
            pid = int(ti.get("id"))
        except (TypeError, ValueError):
            pid = None
        if pid not in wp_drafts():
            return ("BLOCKED by guardrail: this agent only edits WordPress drafts it created. "
                    "Live pages change only when Graciela copies the draft in.")
    return ""


def record_wp_draft(event: dict) -> None:
    """PostToolUse: remember the id of a draft this agent just created."""
    suffix = tool_suffix(event.get("tool_name", ""))
    if suffix not in WP_CREATE:
        return
    m = re.search(r'\\?"id\\?"\s*:\s*(\d+)', json.dumps(event.get("tool_response")))
    if not m:
        return
    ids = wp_drafts() | {int(m.group(1))}
    WP_DRAFTS_FILE.parent.mkdir(exist_ok=True)
    WP_DRAFTS_FILE.write_text(json.dumps(sorted(ids)))


# Harness and session tools, not data connectors. Not used by scheduled jobs.
HARNESS_SERVERS = re.compile(
    r"^mcp__(ccd_[a-z_]+|mcp-registry|visualize|Claude_Browser|Claude_Code_iOS_Simulator|terminal|scheduled-tasks)__"
)


# Structural deletes inside otherwise-allowed batch edits (Sheets/Docs).
# Ledger rows are never removed; they get status=dropped instead.
DESTRUCTIVE_REQUESTS = re.compile(r'"(deleteSheet|deleteDimension|deleteDocumentTab|deleteTab)"')


# Drive writes that place a file must name a parent inside the agent's own folder.
PLACES_FILE = {"create_file", "update_file"}
FOLDER_MIME = "application/vnd.google-apps.folder"


def outside_folder(suffix: str, tool_input: dict, env: dict, config: dict) -> str:
    """Reason to block, or "" if the file lands in Chief of Staff (or is the root folder itself)."""
    ti = tool_input or {}
    parents = [v for k, v in ti.items() if "parent" in k.lower() and isinstance(v, str) and v]
    parents += [p for k, v in ti.items() if "parent" in k.lower() and isinstance(v, list) for p in v]
    if suffix == "update_file" and not parents:
        return ""  # rename or content update, nothing moves
    root_name = (config.get("drive") or {}).get("root_folder_name", "Chief of Staff")
    if (suffix == "create_file" and ti.get("title") == root_name
            and FOLDER_MIME in (ti.get("contentMimeType"), ti.get("mimeType"))):
        return ""  # setup creating the root folder
    allowed = folders.load(env)
    if not parents:
        return "names no parent folder"
    if not allowed:
        return "has no list of allowed folders (run-common Start writes it)"
    bad = [p for p in parents if p not in allowed]
    return "targets a folder outside Chief of Staff" if bad else ""


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
    if suffix in KIT_DRAFTS:
        why = kit_block(tool_name, suffix, env, tool_input)
        if why:
            return False, why
    wp_write = suffix in WP_CREATE | WP_UPDATE
    if wp_write or suffix in WP_READ:
        why = wp_block(tool_name, suffix, env, tool_input)
        if why:
            return False, why
    if (not READ.match(suffix) and suffix not in WRITE and suffix not in KIT_DRAFTS
            and suffix not in WP_READ and not wp_write):
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
    if suffix in WRITE or suffix in KIT_DRAFTS or wp_write:
        secrets = find_secrets(json.dumps(tool_input or {}, ensure_ascii=False))
        if secrets:
            return False, (
                f"BLOCKED by guardrail: this write contains what looks like a {', '.join(secrets)}. "
                "Financial details and login credentials never go into drafts, sheets, docs, or events. "
                "Skip that content, log 'skipped: sensitive', and continue."
            )
        if suffix in PLACES_FILE:
            why = outside_folder(suffix, tool_input, env, config)
            if why:
                return False, (
                    f"BLOCKED by guardrail: this '{suffix}' {why}. Files are created only inside the "
                    "Chief of Staff folder. Write the intended file into the review doc instead."
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
    if len(sys.argv) > 1 and sys.argv[1] == "post":
        try:
            record_wp_draft(event)
        except OSError:
            pass
        return 0
    ok, reason = decide(event.get("tool_name", ""), dict(os.environ), load_config(), event.get("tool_input"))
    if ok:
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
