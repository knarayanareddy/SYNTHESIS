"""Model name sanitizer — treat backend names as untrusted."""

import unicodedata


def sanitize_model_name(name: str, max_len: int = 160) -> str:
    """Sanitize a backend-provided model name for safe display/logging."""
    if not isinstance(name, str):
        name = str(name)

    result = []
    for ch in name:
        if unicodedata.category(ch).startswith("C"):  # Control characters
            result.append("\ufffd")  # REPLACEMENT CHARACTER
        elif ch == "<":
            result.append("‹")
        elif ch == ">":
            result.append("›")
        else:
            result.append(ch)

    sanitized = "".join(result)
    return sanitized[:max_len]
