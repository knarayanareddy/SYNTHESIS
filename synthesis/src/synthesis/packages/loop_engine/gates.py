"""Loop gate system — enforces quality gates with ledgering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal

GateSeverity = Literal["blocking", "warning", "informational"]
GateResultStatus = Literal["pass", "fail", "escalate", "skip_with_reason"]

BLOCKING_GATES: set[str] = {
    "intent_gate",
    "safety_gate",
    "sandbox_gate",
    "execution_gate",
    "termination_gate",
    "cloud_approval_gate",
}

POLICY_ALLOWS_BLOCKING_SKIP = False  # Phase 0: can never skip blocking gates


@dataclass
class GateResult:
    """Result of a loop quality gate evaluation."""
    gate_name: str
    severity: GateSeverity
    result: GateResultStatus
    reason: str = ""
    trace_id: str = ""
    loop_id: str = ""
    iteration: int = 0
    next_action: str = ""
    evidence: dict | None = None
    policy_allows_skip: bool = False

    def to_payload(self) -> dict:
        return {
            "gate_name": self.gate_name,
            "severity": self.severity,
            "result": self.result,
            "reason": self.reason,
            "trace_id": self.trace_id,
            "loop_id": self.loop_id,
            "iteration": self.iteration,
            "next_action": self.next_action,
            "evidence": self.evidence or {},
            "policy_allows_skip": self.policy_allows_skip,
        }


def make_gate_result(
    gate_name: str,
    severity: GateSeverity,
    result: GateResultStatus,
    reason: str = "",
    trace_id: str = "",
    loop_id: str = "",
    iteration: int = 0,
    next_action: str = "",
    evidence: Optional[dict] = None,
) -> GateResult:
    """Create a validated GateResult. Raises ValueError if blocking gate skip is forbidden."""
    if (
        gate_name in BLOCKING_GATES
        and result == "skip_with_reason"
        and not POLICY_ALLOWS_BLOCKING_SKIP
    ):
        raise ValueError(
            f"Blocking gate '{gate_name}' cannot be skipped: "
            f"POLICY_ALLOWS_BLOCKING_SKIP is False"
        )
    return GateResult(
        gate_name=gate_name,
        severity=severity,
        result=result,
        reason=reason,
        trace_id=trace_id,
        loop_id=loop_id,
        iteration=iteration,
        next_action=next_action,
        evidence=evidence,
        policy_allows_skip=(result != "skip_with_reason" or gate_name not in BLOCKING_GATES),
    )


def write_gate(ctx, gate: GateResult) -> dict:
    """Ledger a gate result."""
    return ctx.append("loop_gate_result", gate.to_payload())
