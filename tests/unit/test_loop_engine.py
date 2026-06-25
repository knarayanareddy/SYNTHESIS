"""Unit tests for loop engine: termination, gates, hashing."""

import time
import pytest
from synthesis.packages.loop_engine.termination import (
    LoopBudget, LoopCounters, should_stop, MAX_ITERATIONS_BY_TASK,
)
from synthesis.packages.loop_engine.gates import (
    make_gate_result, write_gate, GateResult, BLOCKING_GATES,
    POLICY_ALLOWS_BLOCKING_SKIP,
)
from synthesis.packages.loop_engine.hashing import stable_state_hash, HASH_INCLUDED_FIELDS


class TestTermination:
    def test_should_stop_max_iterations(self):
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(iteration=5)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "max_iterations"

    def test_should_stop_model_call_cap(self):
        budget = LoopBudget(task_type="bug_fix", max_model_calls=5)
        counters = LoopCounters(model_calls=5)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "model_call_cap"

    def test_should_stop_safety(self):
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(safety_stop=True)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "safety_stop"

    def test_should_stop_tool_call_cap(self):
        budget = LoopBudget(task_type="bug_fix", max_tool_calls=5)
        counters = LoopCounters(tool_calls=5)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "tool_call_cap"

    def test_should_stop_error_cap(self):
        budget = LoopBudget(task_type="bug_fix", max_errors=2)
        counters = LoopCounters(error_count=2)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "error_cap"

    def test_should_stop_repeated_state_hash(self):
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(repeated_state_hash_count=2)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "repeated_state_hash"

    def test_should_stop_same_failed_gate(self):
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(same_failed_gate_count=2)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "same_failed_gate"

    def test_should_stop_success(self):
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(goal_achieved=True, verification_passed=True)
        stop, reason = should_stop(budget, counters)
        assert stop
        assert reason == "success"

    def test_should_continue(self):
        budget = LoopBudget(task_type="bug_fix")
        counters = LoopCounters(iteration=0)
        stop, reason = should_stop(budget, counters)
        assert not stop
        assert reason == "continue"

    def test_resolved_max_iterations(self):
        budget = LoopBudget(task_type="bug_fix")
        assert budget.resolved_max_iterations() == 5

        budget2 = LoopBudget(task_type="question")
        assert budget2.resolved_max_iterations() == 2

        budget3 = LoopBudget(task_type="unknown", max_iterations=7)
        assert budget3.resolved_max_iterations() == 7


class TestGates:
    def test_blocking_gate_cannot_skip(self):
        with pytest.raises(ValueError, match="cannot be skipped"):
            make_gate_result("safety_gate", "blocking", "skip_with_reason",
                             reason="testing skip", trace_id="t1", loop_id="l1", iteration=0)

    def test_non_blocking_gate_can_pass(self):
        gate = make_gate_result("style_gate", "informational", "pass",
                                reason="ok", trace_id="t1", loop_id="l1", iteration=0)
        assert gate.result == "pass"
        assert gate.gate_name == "style_gate"

    def test_gate_result_to_payload(self):
        gate = make_gate_result("intent_gate", "blocking", "pass",
                                reason="intent accepted", trace_id="t1", loop_id="l1", iteration=0,
                                next_action="proceed")
        p = gate.to_payload()
        assert p["gate_name"] == "intent_gate"
        assert p["result"] == "pass"
        assert p["reason"] == "intent accepted"

    def test_blocking_gates_set(self):
        assert "safety_gate" in BLOCKING_GATES
        assert "sandbox_gate" in BLOCKING_GATES
        assert "execution_gate" in BLOCKING_GATES
        assert "intent_gate" in BLOCKING_GATES

    def test_policy_allows_blocking_skip_false(self):
        assert POLICY_ALLOWS_BLOCKING_SKIP is False


class TestStateHashing:
    def test_state_hash_ignores_nondeterministic_fields(self):
        state1 = {
            "task_type": "bug_fix",
            "success_criteria": ["test_pass"],
            "changed_file_digests": ["abc"],
            "failed_gates": [],
            "last_error_class": None,
            "crg_digest": "def",
            "world_divergence_bucket": 0,
            "timestamp": "2024-01-01T00:00:00Z",
            "span_id": "span-123",
        }
        state2 = {
            "task_type": "bug_fix",
            "success_criteria": ["test_pass"],
            "changed_file_digests": ["abc"],
            "failed_gates": [],
            "last_error_class": None,
            "crg_digest": "def",
            "world_divergence_bucket": 0,
            "timestamp": "2025-12-31T23:59:59Z",
            "span_id": "span-999",
        }
        h1 = stable_state_hash(state1)
        h2 = stable_state_hash(state2)
        assert h1 == h2, "Hash should be identical despite different timestamps"

    def test_state_hash_changes_with_fields(self):
        state1 = {
            "task_type": "bug_fix",
            "success_criteria": ["test_pass"],
            "changed_file_digests": [],
            "failed_gates": [],
            "last_error_class": None,
            "crg_digest": "",
            "world_divergence_bucket": 0,
        }
        state2 = dict(state1, task_type="refactor")
        h1 = stable_state_hash(state1)
        h2 = stable_state_hash(state2)
        assert h1 != h2

    def test_hash_included_fields(self):
        for field in ["task_type", "success_criteria", "changed_file_digests",
                       "failed_gates", "last_error_class", "crg_digest",
                       "world_divergence_bucket"]:
            assert field in HASH_INCLUDED_FIELDS
