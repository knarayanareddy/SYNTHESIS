"""Model pool types and dataclasses."""

from dataclasses import dataclass


@dataclass
class BackendProbe:
    backend: str
    reachable: bool
    latency_ms: float = 0.0
    model_count: int = 0
    error: str = ""
