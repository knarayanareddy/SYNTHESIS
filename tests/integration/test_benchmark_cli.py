"""Benchmark CLI integration tests."""

import os, sys, subprocess, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))


def _setup_golden_repo(tmpdir: str) -> str:
    repo = os.path.join(tmpdir, "golden_demo_repo")
    os.makedirs(os.path.join(repo, "src"))
    os.makedirs(os.path.join(repo, "tests"))
    with open(os.path.join(repo, "src", "__init__.py"), "w"): pass
    with open(os.path.join(repo, "src", "auth.py"), "w") as f:
        f.write("def normalize_token(token: str) -> str:\n    return token.lower()\n")
    with open(os.path.join(repo, "tests", "__init__.py"), "w"): pass
    with open(os.path.join(repo, "tests", "test_auth.py"), "w") as f:
        f.write("from src.auth import normalize_token\n\n\ndef test_token_normalization_strips_whitespace():\n    assert normalize_token(\"  ABC  \") == \"abc\"\n")
    return repo


class TestBenchmarkCLI:
    def test_benchmark_command_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = _setup_golden_repo(tmpdir)
            result = subprocess.run(
                [sys.executable, "-m", "synthesis.apps.cli.main",
                 "benchmark", "--repo", repo, "--runs", "3", "--warmup", "1"],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src")},
            )
            assert result.returncode == 0, f"Benchmark failed: {result.stderr}"
            assert "P50" in result.stdout
            assert "P95" in result.stdout
            assert "P99" in result.stdout

    def test_benchmark_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = _setup_golden_repo(tmpdir)
            json_path = os.path.join(tmpdir, "bench.json")
            result = subprocess.run(
                [sys.executable, "-m", "synthesis.apps.cli.main",
                 "benchmark", "--repo", repo, "--runs", "3", "--warmup", "1",
                 "--json", json_path],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src")},
            )
            assert result.returncode == 0
            assert os.path.exists(json_path)
            import json
            with open(json_path) as f:
                data = json.load(f)
            assert "report" in data
            assert "p50_ms" in data["report"]

    def test_run_shows_wall_time(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = _setup_golden_repo(tmpdir)
            result = subprocess.run(
                [sys.executable, "-m", "synthesis.apps.cli.main",
                 "run", "--task", "bugfix", "--repo", repo],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src")},
            )
            assert result.returncode == 0
            assert "Wall time" in result.stdout
