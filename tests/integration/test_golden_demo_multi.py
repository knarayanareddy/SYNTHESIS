"""Multi-iteration golden demo tests — exercises loop behavior across iterations."""

import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from synthesis.packages.observability.ledger import JsonlLedger
from synthesis.packages.loop_engine.termination import (
    LoopBudget, LoopCounters, should_stop,
)
from synthesis.packages.loop_engine.gates import make_gate_result
from synthesis.packages.loop_engine.hashing import stable_state_hash


class TestLoopMultiIteration:
    """Tests for loop behavior across multiple iterations."""

    def test_repeated_state_hash_detection(self):
        """Repeated state hash should stop the loop after count >= 2."""
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(repeated_state_hash_count=2)

        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "repeated_state_hash"

    def test_repeated_state_hash_not_triggered_at_1(self):
        """Single repeated hash should not stop the loop."""
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(repeated_state_hash_count=1)

        stop, reason = should_stop(budget, counters)
        assert not stop

    def test_same_failed_gate_detection(self):
        """Same failed gate should stop after count >= 2."""
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(same_failed_gate_count=2)

        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "same_failed_gate"

    def test_wall_clock_limit(self):
        """Wall clock limit should stop the loop."""
        import time
        budget = LoopBudget(task_type="bug_fix", wall_clock_limit_sec=0)
        # Set started time far in the past
        counters = LoopCounters(started_monotonic=time.monotonic() - 10)

        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "wall_clock_limit"

    def test_budget_enforced_before_actions(self):
        """Budget caps must be checked BEFORE incrementing counters (pattern check)."""
        # This test verifies the pattern: check limits, THEN act, THEN increment
        budget = LoopBudget(task_type="bug_fix", max_model_calls=3)

        # Simulate loop pattern: should_stop before each call
        counters = LoopCounters(model_calls=2)
        stop, _ = should_stop(budget, counters)
        assert not stop  # Can proceed

        counters.model_calls += 1  # After call

        stop2, _ = should_stop(budget, counters)
        assert stop2  # At cap

    def test_error_cap_increments_correctly(self):
        """Error count should trigger stop at max_errors."""
        budget = LoopBudget(task_type="bug_fix", max_errors=2)
        counters = LoopCounters(error_count=2)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "error_cap"

    def test_world_sim_cap(self):
        """World simulation cap should stop the loop."""
        budget = LoopBudget(task_type="bug_fix", max_world_sim_calls=1)
        counters = LoopCounters(world_sim_calls=1)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "world_sim_call_cap"


class TestGateBehavior:
    """Additional gate behavior tests."""

    def test_multiple_gates_in_sequence(self):
        """Multiple gates in sequence: all must pass."""
        gates = [
            make_gate_result("intent_gate", "blocking", "pass", reason="ok", trace_id="t1", loop_id="l1", iteration=0),
            make_gate_result("execution_gate", "blocking", "pass", reason="ok", trace_id="t1", loop_id="l1", iteration=0),
        ]
        for gate in gates:
            assert gate.result == "pass"

    def test_blocking_gate_fail(self):
        """A blocking gate that fails should be allowed (pass, fail, escalate are valid)."""
        gate = make_gate_result("safety_gate", "blocking", "fail", reason="unsafe", trace_id="t1", loop_id="l1", iteration=0)
        assert gate.result == "fail"
        assert gate.severity == "blocking"

    def test_blocking_gate_escalate(self):
        """A blocking gate can escalate."""
        gate = make_gate_result("safety_gate", "blocking", "escalate", reason="needs review", trace_id="t1", loop_id="l1", iteration=0)
        assert gate.result == "escalate"

    def test_non_blocking_gate_skip(self):
        """Non-blocking gates can be skipped."""
        gate = make_gate_result("style_gate", "informational", "skip_with_reason", reason="not needed", trace_id="t1", loop_id="l1", iteration=0)
        assert gate.result == "skip_with_reason"
        assert gate.gate_name not in {"safety_gate", "sandbox_gate", "execution_gate", "intent_gate"}


class TestStateHashIterations:
    """State hash behavior across iterations."""

    def test_hash_different_across_iterations(self):
        """State hash should differ when task state changes between iterations."""
        state1 = {
            "task_type": "bug_fix",
            "success_criteria": ["test_pass"],
            "changed_file_digests": [],
            "failed_gates": [],
            "last_error_class": None,
            "crg_digest": "",
            "world_divergence_bucket": 0,
        }
        # Patch was applied — file changed
        state2 = {
            "task_type": "bug_fix",
            "success_criteria": ["test_pass"],
            "changed_file_digests": ["abc123"],
            "failed_gates": [],
            "last_error_class": None,
            "crg_digest": "",
            "world_divergence_bucket": 0,
        }

        assert stable_state_hash(state1) != stable_state_hash(state2)

    def test_hash_same_without_changes(self):
        """Same state (no field changes) => same hash."""
        state = {
            "task_type": "bug_fix",
            "success_criteria": ["test_pass"],
            "changed_file_digests": [],
            "failed_gates": [],
            "last_error_class": None,
            "crg_digest": "",
            "world_divergence_bucket": 0,
        }
        assert stable_state_hash(state) == stable_state_hash(dict(state))
