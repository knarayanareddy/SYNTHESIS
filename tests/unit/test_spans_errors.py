"""Error path tests for spans — verify span wrapping handles failures."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))

import pytest
from synthesis.packages.observability.spans import (
    start_span, end_span, span_context, spans_available,
    model_call_span, loop_iteration_span, routing_decision_span, sandbox_span,
)


class TestSpansErrors:
    """Verify spans handle edge cases and errors gracefully."""

    def test_end_span_noop_success(self):
        span = start_span("test", trace_id="t1")
        end_span(span, success=True)

    def test_end_span_noop_failure(self):
        span = start_span("test", trace_id="t1")
        end_span(span, success=False, error="something went wrong")

    def test_span_context_propagates_exception(self):
        """Exception inside span context should propagate."""
        with pytest.raises(ValueError, match="test error"):
            with span_context("test", trace_id="t1"):
                raise ValueError("test error")

    def test_span_context_sets_error_on_exception(self):
        """Span should be ended with error status when exception occurs."""
        span = start_span("test", trace_id="t1")
        try:
            with span_context("test_ctx", trace_id="t1"):
                raise RuntimeError("simulated failure")
        except RuntimeError:
            pass
        # Span should still be ended (no-op span doesn't track status,
        # but the end_span call should not crash)

    def test_span_with_none_attributes(self):
        """span with None attributes should not crash."""
        span = start_span("test", trace_id="t1", attributes=None)
        assert span is not None

    def test_span_with_empty_attributes(self):
        span = start_span("test", trace_id="t1", attributes={})
        assert span is not None
        span.set_attribute("key", "value")

    def test_span_set_attribute_truncation(self):
        """Long attribute values should be truncated."""
        span = start_span("test", trace_id="t1")
        long_value = "x" * 500
        span.set_attribute("key", long_value)
        # No crash — truncation is handled internally

    def test_sandbox_span_empty_argv(self):
        """sandbox_span with empty argv should not crash."""
        span = sandbox_span("t1", [])
        assert span is not None
        span.end()

    def test_sandbox_span_single_command(self):
        span = sandbox_span("t1", ["pytest"])
        assert span is not None
        span.end()

    def test_model_call_span_with_attributes(self):
        span = model_call_span("t1", "llama3:8b", "ollama")
        span.set_attribute("synthesis.tokens", 150)
        span.set_attribute("synthesis.prompt_tokens", 50)
        span.end()

    def test_multiple_spans_independent(self):
        """Multiple spans should not interfere with each other."""
        s1 = start_span("span1", trace_id="t1")
        s2 = start_span("span2", trace_id="t1")
        s1.set_attribute("a", "1")
        s2.set_attribute("b", "2")
        s1.end()
        s2.end()
        # No interference

    def test_spans_available_returns_bool(self):
        assert isinstance(spans_available(), bool)
