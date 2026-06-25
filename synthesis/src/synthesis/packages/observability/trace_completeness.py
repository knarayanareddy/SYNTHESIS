"""Trace completeness scoring — measures whether required events are present."""

import json
import os
from typing import Optional

REQUIRED_EVENTS_BY_TASK: dict[str, set[str]] = {
    "bug_fix": {
        "request_started",
        "policy_check",
        "route_decision",
        "codegraph_update",
        "codegraph_query",
        "crg_propagate",
        "loop_iteration_started",
        "loop_iteration_completed",
        "loop_gate_result",
        "route_outcome",
        "loop_terminated",
        "sandbox_exec",
        "model_call_started",
        "model_call_completed",
        "memory_commit",
    },
    "code_review": {
        "request_started",
        "policy_check",
        "route_decision",
        "codegraph_update",
        "codegraph_query",
        "loop_iteration_started",
        "loop_iteration_completed",
        "route_outcome",
        "loop_terminated",
    },
    "test_generation": {
        "request_started",
        "policy_check",
        "route_decision",
        "loop_iteration_started",
        "loop_iteration_completed",
        "route_outcome",
        "loop_terminated",
        "sandbox_exec",
    },
}


def trace_completeness(
    task_type: str,
    event_types: set[str] | list[str],
) -> dict:
    """Compute trace completeness score for a task.

    Args:
        task_type: The task type (e.g., "bug_fix").
        event_types: The set of event types present in the trace.

    Returns:
        Dict with task_type, required, present, missing, score.
    """
    required = REQUIRED_EVENTS_BY_TASK.get(task_type, set())
    if isinstance(event_types, list):
        event_types = set(event_types)

    present = required & event_types
    missing = required - event_types
    score = len(present) / len(required) if required else 1.0

    return {
        "task_type": task_type,
        "required": sorted(required),
        "present": sorted(present),
        "missing": sorted(missing),
        "score": score,
    }


def trace_completeness_from_ledger(
    path: str,
    task_type: str,
    trace_id: Optional[str] = None,
) -> dict:
    """Compute trace completeness by reading events from a ledger file.

    Args:
        path: Path to the ledger JSONL file.
        task_type: The task type (e.g., "bug_fix").
        trace_id: Optional trace_id filter.

    Returns:
        Completeness dict from trace_completeness().
    """
    if not os.path.exists(path):
        return trace_completeness(task_type, set())

    event_types: set[str] = set()
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if trace_id and event.get("trace_id") != trace_id:
                    continue
                event_types.add(event.get("event_type", ""))
    except Exception:
        pass

    return trace_completeness(task_type, event_types)
