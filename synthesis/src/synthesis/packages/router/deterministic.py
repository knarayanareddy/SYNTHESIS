"""Deterministic local-first router."""

from dataclasses import dataclass, field
from typing import Optional

SELECTABLE_MATURITY = {"full"}
SELECTABLE_LIFECYCLE = {"serving", "warm"}


@dataclass
class TaskSpec:
    task_type: str
    agent_role: str = "worker"
    required_capability: str = "chat"
    trace_id: str = ""


@dataclass
class RoutingResult:
    selected_model: Optional[str] = None
    selected_backend: Optional[str] = None
    locality: Optional[str] = None
    score: float = 0.0
    candidates_considered: int = 0
    rejection_reasons: list[dict] = field(default_factory=list)
    cloud_gate_result: str = "not_allowed"
    no_model_available: bool = False

    def to_dict(self) -> dict:
        return {
            "selected_model": self.selected_model,
            "selected_backend": self.selected_backend,
            "locality": self.locality,
            "score": self.score,
            "candidates_considered": self.candidates_considered,
            "rejection_reasons": self.rejection_reasons,
            "cloud_gate_result": self.cloud_gate_result,
            "no_model_available": self.no_model_available,
        }


def select_model(
    model_pool: dict,
    task: TaskSpec,
    ledger=None,
) -> RoutingResult:
    """Select the best local model using deterministic local-first routing."""
    result = RoutingResult()

    candidates = []
    for backend in model_pool.get("backends", []):
        for model in backend.get("models", []):
            result.candidates_considered += 1

            # Reject non-local
            if model.get("locality") != "local":
                result.rejection_reasons.append({
                    "model": model.get("name"),
                    "reason": "non_local_candidate_rejected_by_default",
                })
                continue

            # Reject partial/discovery adapters
            if model.get("adapter_maturity") not in SELECTABLE_MATURITY:
                result.rejection_reasons.append({
                    "model": model.get("name"),
                    "reason": "adapter_maturity_not_selectable_for_chat",
                })
                continue

            # Reject non-serving
            if model.get("lifecycle_state") not in SELECTABLE_LIFECYCLE:
                result.rejection_reasons.append({
                    "model": model.get("name"),
                    "reason": "model_not_serving",
                })
                continue

            # Reject missing capability
            if task.required_capability == "chat" and not model.get("supports_chat", False):
                result.rejection_reasons.append({
                    "model": model.get("name"),
                    "reason": "chat_not_supported",
                })
                continue
            if task.required_capability == "embedding" and not model.get("supports_embeddings", False):
                result.rejection_reasons.append({
                    "model": model.get("name"),
                    "reason": "embedding_not_supported",
                })
                continue

            candidates.append((model, 0.5))  # Placeholder score

    if not candidates:
        result.no_model_available = True
        if ledger:
            ledger.append("route_decision", task.trace_id, result.to_dict())
            ledger.append("route_outcome", task.trace_id, {
                "task_success": False,
                "tests_passed": False,
                "escalated": False,
                "failure_reason": "no_model_available",
                "decision_kind": "model_selection",
            })
        return result

    # Select best score
    model, score = max(candidates, key=lambda x: x[1])
    result.selected_model = model.get("name")
    result.selected_backend = model.get("backend")
    result.locality = model.get("locality")
    result.score = score

    if ledger:
        ledger.append("route_decision", task.trace_id, result.to_dict())

    return result
