"""Performance measurement — lightweight benchmarking for Phase 3.

Provides wall-clock timing with perf_counter for key operations.
Results are stored in ledger-compatible format for future comparison.
"""

from __future__ import annotations

import time
import statistics
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class PerfSample:
    """A single performance sample."""
    name: str
    duration_sec: float
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_sec": self.duration_sec,
            "duration_ms": self.duration_sec * 1000,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class PerfReport:
    """Aggregated performance report."""
    name: str
    samples: list[PerfSample] = field(default_factory=list)
    count: int = 0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    mean_ms: float = 0.0
    total_sec: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "mean_ms": self.mean_ms,
            "total_sec": self.total_sec,
        }


def time_operation(name: str, fn: Callable, *args, **kwargs) -> tuple:
    """Time a function call and return (result, PerfSample)."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    sample = PerfSample(
        name=name,
        duration_sec=elapsed,
        timestamp=time.time(),
        metadata={"args": str(args)[:100], "kwargs": str(kwargs)[:100]},
    )
    return result, sample


def aggregate_samples(name: str, samples: list[PerfSample]) -> PerfReport:
    """Aggregate multiple samples into a statistical report."""
    if not samples:
        return PerfReport(name=name)

    durations = [s.duration_sec for s in samples]
    sorted_durations = sorted(durations)
    n = len(sorted_durations)

    return PerfReport(
        name=name,
        samples=samples,
        count=n,
        p50_ms=_percentile(sorted_durations, 50) * 1000,
        p95_ms=_percentile(sorted_durations, 95) * 1000,
        p99_ms=_percentile(sorted_durations, 99) * 1000,
        min_ms=min(durations) * 1000,
        max_ms=max(durations) * 1000,
        mean_ms=statistics.mean(durations) * 1000,
        total_sec=sum(durations),
    )


def _percentile(sorted_data: list[float], p: float) -> float:
    """Compute the p-th percentile of sorted data."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * p / 100.0
    f = int(k)
    c = k - f
    if f + 1 < len(sorted_data):
        return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
    return sorted_data[f]


def benchmark_golden_demo(
    repo_root: str,
    runs: int = 5,
    warmup: int = 1,
    ollama_model: str = "qwen2.5-coder:7b",
) -> dict:
    """Benchmark the golden demo across multiple runs.

    Args:
        repo_root: Path to golden demo repo.
        runs: Number of measurement runs.
        warmup: Number of warmup runs (excluded from stats).
        ollama_model: Ollama model to use.

    Returns:
        Dict with phase reports and overall summary.
    """
    from synthesis.packages.observability.ledger import JsonlLedger
    from synthesis.packages.loop_engine.rarv import run_golden_demo_rarv
    import tempfile, os

    all_samples: list[PerfSample] = []
    reason_samples: list[PerfSample] = []
    act_samples: list[PerfSample] = []

    total_runs = warmup + runs

    for i in range(total_runs):
        tmpdir = tempfile.mkdtemp()
        ledger_path = os.path.join(tmpdir, "ledger.jsonl")
        ledger = JsonlLedger(ledger_path)

        import shutil
        run_repo = os.path.join(tmpdir, "repo")
        shutil.copytree(repo_root, run_repo)

        t0 = time.perf_counter()
        result = run_golden_demo_rarv(ledger=ledger, repo_root=run_repo, ollama_model=ollama_model)
        elapsed = time.perf_counter() - t0

        shutil.rmtree(tmpdir, ignore_errors=True)

        if i >= warmup:
            sample = PerfSample(
                name="golden_demo_full",
                duration_sec=elapsed,
                timestamp=time.time(),
                metadata={"run": i, "status": result.status},
            )
            all_samples.append(sample)

    report = aggregate_samples("golden_demo_full", all_samples)

    return {
        "report": report.to_dict(),
        "runs": runs,
        "warmup": warmup,
        "all_samples": [s.to_dict() for s in all_samples],
    }
