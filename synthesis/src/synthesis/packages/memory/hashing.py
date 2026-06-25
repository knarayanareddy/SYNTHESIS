"""Deterministic memory commit hash."""

import hashlib
import json


def canonical_memory_json(obj: dict) -> str:
    """Deterministic JSON for memory commits."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)


def memory_commit_hash(obj: dict) -> str:
    """SHA-256 hash of canonical memory JSON."""
    return hashlib.sha256(canonical_memory_json(obj).encode("utf-8")).hexdigest()
