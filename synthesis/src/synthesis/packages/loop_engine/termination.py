"""Loop termination system — ensures no loop runs unbounded."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

MAX_ITERATIONS_BY_TASK: dict[str, int] = {
    "question": 2,
    "terminal": 3,
    "code_review": 3,
    "test_generation": 4,
    "bug_fix": 5,
    "refactor": 5,
}


@dataclass
class LoopBudget:
    """Configuration for loop termination caps."""
    task_type: str
    max_iterations: int | None = None
    max_model_calls: int = 30
    max_tool_calls: int = 40
    max_world_sim_calls: int = 8
    max_errors: int = 2
    wall_clock_limit_sec: int = 900

    def resolved_max_iterations(self) -> int:
        if self.max_iterations is not None:
            return self.max_iterations
        return MAX_ITERATIONS_BY_TASK.get(self.task_type, 5)


@dataclass
class LoopCounters:
    """Runtime counters for loop execution."""
    iteration: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    world_sim_calls: int = 0
    error_count: int = 0
    repeated_state_hash_count: int = 0
    same_failed_gate_count: int = 0
    safety_stop: bool = False
    started_monotonic: float = field(default_factory=time.monotonic)
    goal_achieved: bool = False
    verification_passed: bool = False


def should_stop(budget: LoopBudget, counters: LoopCounters) -> tuple[bool, str]:
    """Evaluate whether the loop should stop. Returns (stop, reason)."""
    if counters.goal_achieved and counters.verification_passed:
        return True, "success"
    if counters.safety_stop:
        return True, "safety_stop"
    if counters.iteration >= budget.resolved_max_iterations():
        return True, "max_iterations"
    if counters.model_calls >= budget.max_model_calls:
        return True, "model_call_cap"
    if counters.tool_calls >= budget.max_tool_calls:
        return True, "tool_call_cap"
    if counters.world_sim_calls >= budget.max_world_sim_calls:
        return True, "world_sim_call_cap"
    if counters.error_count >= budget.max_errors:
        return True, "error_cap"
    if counters.repeated_state_hash_count >= 2:
        return True, "repeated_state_hash"
    if counters.same_failed_gate_count >= 2:
        return True, "same_failed_gate"
    if time.monotonic() - counters.started_monotonic >= budget.wall_clock_limit_sec:
        return True, "wall_clock_limit"
    return False, "continue"
