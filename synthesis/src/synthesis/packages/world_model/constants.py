"""World model advisory-only prohibitions and thresholds."""

WORLD_MODEL_MAY_NOT = [
    "approve_correctness",
    "bypass_tests",
    "bypass_verifier",
    "bypass_safety",
    "approve_destructive_actions",
    "commit_memory_alone",
]

PER_DOMAIN_THRESHOLDS = {
    "terminal": {"min_transitions": 50, "min_negative": 20},
    "swe": {"min_transitions": 50, "min_negative": 20},
}
