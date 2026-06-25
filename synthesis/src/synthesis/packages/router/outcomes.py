"""Route outcome writer."""

from typing import Optional


def write_route_outcome(
    ctx,
    decision,
    task_success: bool,
    verifier_score: Optional[float] = None,
    tests_passed: Optional[bool] = None,
    escalated: bool = False,
    failure_reason: Optional[str] = None,
) -> dict:
    """Write a route_outcome event to the ledger."""
    return ctx.append("route_outcome", {
        "task_success": task_success,
        "verifier_score": verifier_score,
        "tests_passed": tests_passed,
        "escalated": escalated,
        "failure_reason": failure_reason,
        "decision_kind": "model_selection",
    })
