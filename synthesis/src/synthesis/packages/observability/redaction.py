"""Redaction-before-persistence — detects and redacts secret values."""

import re
from typing import Any

# Patterns that indicate potential secrets
_SECRET_KEY_PATTERNS = re.compile(
    r'(api[_-]?key|secret|password|token|auth|credential|private[_-]?key)',
    re.IGNORECASE,
)

_SECRET_VALUE_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),       # OpenAI-like
    re.compile(r'sk-ant-[a-zA-Z0-9]{20,}'),    # Anthropic-like
    re.compile(r'AIza[a-zA-Z0-9_\-]{30,}'),    # Google-like
    re.compile(r'sgpa_[a-zA-Z0-9]{20,}'),      # OpenRouter-like
    re.compile(r'[a-zA-Z0-9+/]{40,}={0,2}'),   # Generic base64 tokens
]

REDACTED_PLACEHOLDER = "***REDACTED***"


def _detect_secrets_in_value(value: Any) -> bool:
    """Check if a value looks like a secret."""
    if not isinstance(value, str):
        return False
    for pattern in _SECRET_VALUE_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _detect_secret_keys(payload: dict) -> list[str]:
    """Find keys in payload that look like secret keys."""
    found = []
    for key in payload:
        if isinstance(key, str) and _SECRET_KEY_PATTERNS.search(key):
            found.append(key)
    return found


def redact_payload(payload: dict) -> tuple[dict, bool]:
    """Redact secret values from a payload. Returns (redacted, redacted_any)."""
    redacted_any = False
    result = {}

    for key, value in payload.items():
        if _SECRET_KEY_PATTERNS.search(str(key)):
            result[key] = REDACTED_PLACEHOLDER
            redacted_any = True
        elif _detect_secrets_in_value(value):
            result[key] = REDACTED_PLACEHOLDER
            redacted_any = True
        elif isinstance(value, dict):
            inner, inner_redacted = redact_payload(value)
            result[key] = inner
            if inner_redacted:
                redacted_any = True
        elif isinstance(value, list):
            result[key] = [
                REDACTED_PLACEHOLDER if _detect_secrets_in_value(v)
                else redact_payload(v)[0] if isinstance(v, dict) else v
                for v in value
            ]
        else:
            result[key] = value

    return result, redacted_any


def assert_no_secrets(payload: dict) -> None:
    """Raise ValueError if secrets remain in the payload after redaction."""
    for key, value in payload.items():
        if _detect_secrets_in_value(value):
            raise ValueError(f"Secret value remains in key '{key}' after redaction")
        if _SECRET_KEY_PATTERNS.search(str(key)) and value != REDACTED_PLACEHOLDER:
            raise ValueError(f"Secret key '{key}' not redacted")
