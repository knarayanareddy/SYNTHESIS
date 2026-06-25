"""OpenTelemetry span wrapper for synthesis operations.

Provides lightweight span creation around model calls, loop iterations,
routing decisions, and sandbox executions. Falls back to no-op spans
when OTel SDK or Langfuse is not available.

Designed for Langfuse self-hosted backend via OTLP exporter.
Spans are correlated with ledger events via trace_id.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional

# ── Optional OTel imports ──────────────────────────────────────────────────

try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


# ── Configuration ──────────────────────────────────────────────────────────

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")


def _is_langfuse_configured() -> bool:
    return bool(LANGFUSE_HOST and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)


def _is_otel_configured() -> bool:
    return _is_langfuse_configured() or bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))


_TRACER_PROVIDER_INITIALIZED = False


def _init_tracer_provider():
    global _TRACER_PROVIDER_INITIALIZED
    if _TRACER_PROVIDER_INITIALIZED:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({
            "service.name": "synthesis",
            "service.version": "0.3.0",
        })

        provider = TracerProvider(resource=resource)

        if _is_langfuse_configured():
            import base64
            auth_header = base64.b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()
            headers = {"Authorization": f"Basic {auth_header}"}
            otlp_endpoint = f"{LANGFUSE_HOST.rstrip('/')}/api/public/otlp/v1/traces"
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, headers=headers)
        else:
            exporter = OTLPSpanExporter()

        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _TRACER_PROVIDER_INITIALIZED = True
    except Exception as e:
        import logging
        logging.getLogger("synthesis").warning(f"Failed to initialize OTel TracerProvider: {e}")


# ── Span dataclass for no-op mode ──────────────────────────────────────────

@dataclass
class _NoOpSpan:
    """Minimal span-like object for when OTel is not available."""
    name: str = ""
    trace_id: str = ""
    parent: Optional[_NoOpSpan] = None
    attributes: dict = field(default_factory=dict)
    start_time: float = 0.0

    def set_attribute(self, key: str, value):
        self.attributes[key] = str(value)[:256]

    def set_status(self, status):
        pass

    def end(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.end()


def _get_tracer():
    """Get an OTel tracer if available, otherwise return None."""
    if _OTEL_AVAILABLE:
        try:
            _init_tracer_provider()
            return trace.get_tracer("synthesis", "0.2.0")
        except Exception:
            return None
    return None


# ── Span creation ──────────────────────────────────────────────────────────

def start_span(name: str, trace_id: str = "", kind: str = "INTERNAL",
               attributes: Optional[dict] = None) -> _NoOpSpan:
    """Create and start a span.

    Uses real OTel spans when available, no-op spans otherwise.
    The trace_id links spans to ledger events.
    """
    if _is_otel_configured() and _OTEL_AVAILABLE:
        tracer = _get_tracer()
        if tracer:
            span_kind_map = {
                "CLIENT": SpanKind.CLIENT,
                "SERVER": SpanKind.SERVER,
                "INTERNAL": SpanKind.INTERNAL,
            }
            kind_enum = span_kind_map.get(kind, SpanKind.INTERNAL)
            span = tracer.start_span(name, kind=kind_enum)
            span.set_attribute("synthesis.trace_id", trace_id)
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(f"synthesis.{k}", str(v)[:256])
            return span

    # No-op fallback
    span = _NoOpSpan(name=name, trace_id=trace_id, start_time=time.monotonic())
    if attributes:
        span.attributes = {k: str(v)[:256] for k, v in attributes.items()}
    return span


def end_span(span, success: bool = True, error: str = ""):
    """End a span with status."""
    if hasattr(span, "set_status") and _OTEL_AVAILABLE:
        try:
            from opentelemetry.trace import Status, StatusCode
            if success:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR, error))
        except ImportError:
            pass
    span.end()


@contextmanager
def span_context(name: str, trace_id: str = "", kind: str = "INTERNAL",
                 attributes: Optional[dict] = None):
    """Context manager for a span. Usage:

    with span_context("model_call", trace_id="abc", kind="CLIENT",
                      attributes={"model": "qwen2.5-coder"}) as span:
        # ... do work ...
        span.set_attribute("synthesis.tokens", 150)
    """
    span = start_span(name, trace_id, kind, attributes)
    try:
        yield span
        end_span(span, success=True)
    except Exception as e:
        end_span(span, success=False, error=str(e)[:256])
        raise


# ── Specialized span creators ─────────────────────────────────────────────

def model_call_span(trace_id: str, model: str, backend: str) -> _NoOpSpan:
    """Create a span for a model call."""
    return start_span("model_call", trace_id=trace_id, kind="CLIENT",
                      attributes={
                          "model": model,
                          "backend": backend,
                          "purpose": "reason_about_bug",
                      })


def loop_iteration_span(trace_id: str, loop_id: str, iteration: int,
                        phase: str) -> _NoOpSpan:
    """Create a span for a loop iteration."""
    return start_span(f"loop_iteration.{phase}", trace_id=trace_id,
                      kind="INTERNAL",
                      attributes={
                          "loop_id": loop_id,
                          "iteration": iteration,
                          "phase": phase,
                      })


def routing_decision_span(trace_id: str, candidates: int,
                          selected: str = "") -> _NoOpSpan:
    """Create a span for a routing decision."""
    return start_span("routing_decision", trace_id=trace_id,
                      kind="INTERNAL",
                      attributes={
                          "candidates_considered": candidates,
                          "selected_model": selected,
                      })


def sandbox_span(trace_id: str, argv: list[str]) -> _NoOpSpan:
    """Create a span for sandbox execution."""
    cmd = argv[0] if argv else "unknown"
    return start_span(f"sandbox_exec.{cmd}", trace_id=trace_id,
                      kind="INTERNAL",
                      attributes={
                          "command": cmd,
                          "arg_count": len(argv) - 1,
                      })


# ── Check if spans are available ──────────────────────────────────────────

def spans_available() -> bool:
    """Check if real OTel spans are available."""
    return _OTEL_AVAILABLE and _is_otel_configured()
