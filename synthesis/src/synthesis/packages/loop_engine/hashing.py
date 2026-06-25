"""Deterministic loop state hashing for repeated-state detection."""

import hashlib
import json

HASH_INCLUDED_FIELDS = [
    "task_type",
    "success_criteria",
    "changed_file_digests",
    "failed_gates",
    "last_error_class",
    "crg_digest",
    "world_divergence_bucket",
]


def stable_state_hash(state: dict) -> str:
    """Deterministic SHA-256 hash of selected nondeterministic-safe fields."""
    subset = {}
    for field in HASH_INCLUDED_FIELDS:
        if field in state:
            subset[field] = state[field]
    canonical = json.dumps(subset, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
