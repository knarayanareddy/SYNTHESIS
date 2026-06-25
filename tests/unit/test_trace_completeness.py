"""Unit tests for trace completeness scoring."""

import os
import tempfile
import json
from synthesis.packages.observability.trace_completeness import (
    trace_completeness,
    trace_completeness_from_ledger,
    REQUIRED_EVENTS_BY_TASK,
)


class TestTraceCompleteness:
    def test_bug_fix_full_score(self):
        required = REQUIRED_EVENTS_BY_TASK["bug_fix"]
        result = trace_completeness("bug_fix", required)
        assert result["score"] == 1.0
        assert len(result["missing"]) == 0

    def test_missing_events_reduce_score(self):
        required = REQUIRED_EVENTS_BY_TASK["bug_fix"]
        # Remove one event
        partial = required - {"sandbox_exec"}
        result = trace_completeness("bug_fix", partial)
        assert result["score"] < 1.0
        assert "sandbox_exec" in result["missing"]

    def test_empty_trace_zero_score(self):
        result = trace_completeness("bug_fix", set())
        assert result["score"] == 0.0

    def test_from_ledger_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            # Write synthetic events
            events = [
                {"event_type": "request_started", "trace_id": "t1"},
                {"event_type": "policy_check", "trace_id": "t1"},
                {"event_type": "route_decision", "trace_id": "t1"},
            ]
            with open(ledger_path, "w") as f:
                for e in events:
                    f.write(json.dumps(e) + "\n")

            result = trace_completeness_from_ledger(ledger_path, "bug_fix")
            assert result["score"] > 0.0
            assert result["score"] < 1.0

    def test_from_nonexistent_ledger(self):
        result = trace_completeness_from_ledger("/nonexistent/path.jsonl", "bug_fix")
        assert result["score"] == 0.0

    def test_code_review_events(self):
        required = REQUIRED_EVENTS_BY_TASK["code_review"]
        result = trace_completeness("code_review", required)
        assert result["score"] == 1.0
