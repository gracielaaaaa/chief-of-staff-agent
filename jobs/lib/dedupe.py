"""Stable dedupe keys so every run is idempotent (spec section 4, principle 3)."""
import hashlib
import re


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def key(kind: str, source_id: str, *parts: str) -> str:
    """Deterministic id for an object derived from a source item.

    kind: what is being created (task, reminder, draft, ledger, recap, ...)
    source_id: Gmail message id, Granola meeting id, Canvas assignment id, ...
    parts: anything that distinguishes items split from the same source
    """
    raw = "|".join([kind, source_id, *(_norm(p) for p in parts)])
    return f"{kind}:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
