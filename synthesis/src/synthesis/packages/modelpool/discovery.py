"""Model pool discovery — probe all local backends."""

from typing import Optional

from synthesis.packages.modelpool.adapters.ollama import OllamaAdapter
from synthesis.packages.modelpool.adapters.lm_studio import LMStudioAdapter
from synthesis.packages.modelpool.adapters.jan import JanAdapter
from synthesis.packages.modelpool.adapters.mlx import MLXAdapter
from synthesis.packages.modelpool.adapters.base import ModelBackendAdapter


def discover_model_pool(ledger=None) -> dict:
    """Discover all local backends and return ModelPool state."""
    adapters: list[ModelBackendAdapter] = [
        OllamaAdapter(),
        LMStudioAdapter(),
        JanAdapter(),
        MLXAdapter(),
    ]
    backends = []
    degraded_notes = []

    for adapter in adapters:
        health = adapter.health()
        models = adapter.list_models() if health.get("reachable") else []
        backends.append({
            "name": getattr(adapter, "name", "unknown"),
            "adapter_maturity": getattr(adapter, "adapter_maturity", "partial"),
            "health": health,
            "models": models,
        })
        if not health.get("reachable"):
            degraded_notes.append(f"{getattr(adapter, 'name', 'unknown')} not reachable")

    return {
        "backends": backends,
        "cloud_enabled": False,
        "local_first": True,
        "degraded_notes": degraded_notes,
    }
