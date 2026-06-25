"""Route scoring helpers."""

import json
import os
from typing import Optional


def load_routing_weights(weights_path: Optional[str] = None) -> dict:
    """Load routing weights from config file."""
    if weights_path is None:
        weights_path = os.path.join(
            os.path.dirname(__file__), "config", "routing_weights_v1.json"
        )

    try:
        with open(weights_path) as f:
            return json.load(f)
    except Exception:
        return {
            "version": "router-score-v1",
            "weights": {
                "capability_match": 0.25,
                "context_fit": 0.15,
                "role_match": 0.15,
                "lifecycle_health": 0.10,
                "latency_score": 0.10,
                "historical_success_decayed": 0.10,
                "verifier_score_decayed": 0.05,
                "low_world_divergence": 0.05,
                "safety_compatibility": 0.05,
            },
        }


def score_model(model: dict, task_type: str) -> dict:
    """Compute individual score components for a model."""
    return {
        "capability_match": 1.0,
        "context_fit": 0.5,
        "role_match": 0.5,
        "lifecycle_health": 0.5,
        "latency_score": 0.5,
        "historical_success_decayed": 0.5,
        "verifier_score_decayed": 0.5,
        "low_world_divergence": 0.5,
        "safety_compatibility": 0.5,
    }


def weighted_score(components: dict, weights: dict) -> float:
    """Compute weighted score from components and weights."""
    w = weights.get("weights", weights)
    total = 0.0
    for key, weight in w.items():
        total += components.get(key, 0.0) * weight
    return total / sum(w.values()) if w else 0.0
