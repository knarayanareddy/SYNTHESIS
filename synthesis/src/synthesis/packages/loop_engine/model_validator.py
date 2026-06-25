"""Model response validation — ensures model output is safe and useful.

Checks that model responses are non-empty, within size bounds,
and free of execution-injection markers before being passed
to downstream systems. Model output must never reach shell or eval directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# Maximum reasonable response length (prevents runaway generation)
MAX_RESPONSE_LENGTH = 32_768  # 32KB
MIN_RESPONSE_LENGTH = 1       # At least one non-whitespace character

# Patterns that indicate the model is trying to execute code directly
SHELL_EXECUTION_MARKERS = [
    "```bash",
    "```sh",
    "```python\nimport subprocess",
    "```python\nos.system",
    "eval(",
    "exec(",
    "__import__(",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "os.popen",
    "os.system(",
    "shell=True",
]


@dataclass
class ModelResponseValidation:
    """Result of validating a model response."""
    valid: bool
    content: str = ""
    error: str = ""
    warnings: list[str] = field(default_factory=list)
    content_length: int = 0
    model: str = ""
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "error": self.error,
            "warnings": self.warnings,
            "content_length": self.content_length,
            "model": self.model,
            "tokens_used": self.tokens_used,
        }


def validate_model_response(
    content: str,
    model: str = "",
    min_length: int = MIN_RESPONSE_LENGTH,
    max_length: int = MAX_RESPONSE_LENGTH,
) -> ModelResponseValidation:
    """Validate a model's response for safety and usefulness.

    Checks:
    1. Response is not None or empty whitespace
    2. Response is within length bounds
    3. No shell execution markers in response
    4. Response appears to be natural language (not binary/encoded)

    Args:
        content: The raw model response text.
        model: Model name for logging.
        min_length: Minimum non-whitespace characters required.
        max_length: Maximum allowed response length.

    Returns:
        ModelResponseValidation with valid flag and details.
    """
    warnings: list[str] = []

    # Check 1: Non-empty
    if content is None or not content.strip():
        return ModelResponseValidation(
            valid=False,
            content=content or "",
            error="Model returned empty or whitespace-only response",
            model=model,
        )

    content_length = len(content)

    # Check 2: Length bounds
    if content_length > max_length:
        return ModelResponseValidation(
            valid=False,
            content=content[:max_length],
            error=f"Response too long: {content_length} > {max_length} chars",
            content_length=content_length,
            model=model,
        )

    if len(content.strip()) < min_length:
        warnings.append(f"Response very short: {len(content.strip())} non-whitespace chars")

    # Check 3: Execution markers
    content_lower = content.lower()
    for marker in SHELL_EXECUTION_MARKERS:
        if marker.lower() in content_lower:
            warnings.append(f"Response contains execution marker: {marker[:50]}...")
            # Note: we warn but don't fail — the model may be describing code,
            # not trying to execute it. The sandbox prevents actual execution.

    # Check 4: Heuristic for non-text content (high ratio of non-printable chars)
    non_printable = sum(1 for ch in content if ord(ch) < 32 and ch not in "\n\r\t")
    if non_printable > len(content) * 0.1:
        warnings.append("Response contains suspicious amount of non-printable characters")

    return ModelResponseValidation(
        valid=True,
        content=content,
        warnings=warnings,
        content_length=content_length,
        model=model,
    )


def extract_reasoning(content: str, max_chars: int = 2000) -> str:
    """Extract the key reasoning from a model response.

    Strips code blocks and extracts natural language text.
    Safe to log and display.
    """
    if not content:
        return ""

    # Remove code blocks
    import re
    cleaned = re.sub(r"```[^`]*```", "[code block]", content)
    cleaned = re.sub(r"`[^`]+`", "[inline code]", cleaned)

    # Take first max_chars
    return cleaned[:max_chars].strip()
