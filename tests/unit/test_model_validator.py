"""Tests for model response validation."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))

from synthesis.packages.loop_engine.model_validator import (
    validate_model_response,
    extract_reasoning,
    ModelResponseValidation,
    MAX_RESPONSE_LENGTH,
)


class TestModelValidator:
    """Tests for model response validation."""

    def test_valid_response(self):
        """A normal response should be valid."""
        result = validate_model_response("The function should strip whitespace.", model="test-model")
        assert result.valid
        assert len(result.warnings) == 0

    def test_empty_response(self):
        """Empty response should be invalid."""
        result = validate_model_response("", model="test-model")
        assert not result.valid
        assert "empty" in result.error.lower()

    def test_none_response(self):
        """None response should be invalid."""
        result = validate_model_response(None, model="test-model")
        assert not result.valid

    def test_whitespace_only_response(self):
        """Whitespace-only response should be invalid."""
        result = validate_model_response("   \n\t  ", model="test-model")
        assert not result.valid

    def test_too_long_response(self):
        """Overly long response should be invalid."""
        long_text = "x" * (MAX_RESPONSE_LENGTH + 100)
        result = validate_model_response(long_text, model="test-model")
        assert not result.valid
        assert "too long" in result.error.lower()

    def test_execution_marker_warning(self):
        """Response with shell execution markers should warn."""
        result = validate_model_response(
            "You should run subprocess.run(['rm', '-rf', '/'])", model="test-model"
        )
        assert result.valid  # Should still be valid (warns, doesn't fail)
        assert len(result.warnings) > 0
        assert any("subprocess" in w.lower() for w in result.warnings)

    def test_eval_marker_warning(self):
        """Response with eval() should warn."""
        result = validate_model_response(
            "Use eval() to evaluate the expression", model="test-model"
        )
        assert result.valid
        assert any("eval" in w.lower() for w in result.warnings)

    def test_code_block_in_response(self):
        """Response describing code (not executing) should be valid."""
        result = validate_model_response(
            "Here is the fix:\n```python\nreturn token.strip().lower()\n```",
            model="test-model"
        )
        assert result.valid

    def test_short_response_warns(self):
        """Very short response should warn but be valid."""
        result = validate_model_response("x", model="test-model", min_length=2)
        assert result.valid
        assert len(result.warnings) > 0

    def test_extract_reasoning_strips_code_blocks(self):
        """extract_reasoning should strip code blocks."""
        text = "The bug is:\n```python\nx = 1\n```\nYou should fix it."
        result = extract_reasoning(text)
        assert "```python" not in result
        assert "[code block]" in result

    def test_to_dict(self):
        """to_dict should serialize correctly."""
        result = validate_model_response("Test response.", model="test-model")
        d = result.to_dict()
        assert d["valid"] is True
        assert d["model"] == "test-model"
        assert d["content_length"] == 14
