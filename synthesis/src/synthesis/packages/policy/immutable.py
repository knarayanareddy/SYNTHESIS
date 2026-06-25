"""Immutable policy key enforcement."""

from synthesis.packages.policy.constants import RUNTIME_MUTATION_BLOCKLIST


IMMUTABLE_KEYS = frozenset(RUNTIME_MUTATION_BLOCKLIST)


def is_immutable(key: str) -> bool:
    """Check if a policy key is immutable at runtime."""
    return key in IMMUTABLE_KEYS


def assert_mutable(key: str) -> None:
    """Raise ValueError if the key is immutable."""
    if is_immutable(key):
        raise ValueError(f"Runtime mutation of '{key}' is blocked (immutable policy key)")


def validate_mutation(updates: dict) -> tuple[bool, list[str]]:
    """Validate a policy mutation dict. Returns (allowed, blocked_keys)."""
    blocked = [k for k in updates if is_immutable(k)]
    return len(blocked) == 0, blocked
