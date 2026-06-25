"""CLI integration tests."""

import os
import sys
import tempfile
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _setup_golden_repo(tmpdir: str) -> str:
    """Create a golden demo repo in tmpdir."""
    repo = os.path.join(tmpdir, "golden_demo_repo")
    src_dir = os.path.join(repo, "src")
    tests_dir = os.path.join(repo, "tests")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(tests_dir, exist_ok=True)

    with open(os.path.join(src_dir, "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(src_dir, "auth.py"), "w") as f:
        f.write('"""Auth module for golden demo."""\n\n\n')
        f.write('def normalize_token(token: str) -> str:\n')
        f.write('    return token.lower()\n')

    with open(os.path.join(tests_dir, "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(tests_dir, "test_auth.py"), "w") as f:
        f.write('"""Test for normalize_token."""\n')
        f.write('from src.auth import normalize_token\n\n\n')
        f.write('def test_token_normalization_strips_whitespace():\n')
        f.write('    assert normalize_token("  ABC  ") == "abc"\n')

    return repo


class TestCLI:
    """CLI tests for synthesis commands."""

    def test_cli_run_bugfix(self):
        """CLI 'synthesis run --task bugfix --repo <path>' should succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = _setup_golden_repo(tmpdir)

            result = subprocess.run(
                [
                    sys.executable, "-m", "synthesis.apps.cli.main",
                    "run", "--task", "bugfix", "--repo", repo,
                    "--ollama-model", "qwen2.5-coder:7b",
                ],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
            )

            # Should succeed (model call stubbed in CI)
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "success" in result.stdout.lower() or "SUCCESS" in result.stdout

    def test_cli_dry_run_with_json_output(self):
        """CLI with --output should write JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = _setup_golden_repo(tmpdir)
            output_path = os.path.join(tmpdir, "result.json")

            result = subprocess.run(
                [
                    sys.executable, "-m", "synthesis.apps.cli.main",
                    "run", "--task", "bugfix", "--repo", repo,
                    "--output", output_path,
                ],
                capture_output=True, text=True, timeout=60,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
            )

            assert result.returncode == 0
            assert os.path.exists(output_path)

            import json
            with open(output_path) as f:
                data = json.load(f)
            assert data["status"] == "success"
            assert data["trace_completeness"]["score"] == 1.0

    def test_cli_ledger_verify(self):
        """CLI 'synthesis ledger verify' should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = _setup_golden_repo(tmpdir)

            # First run to create ledger
            subprocess.run(
                [sys.executable, "-m", "synthesis.apps.cli.main",
                 "run", "--task", "bugfix", "--repo", repo],
                capture_output=True, timeout=60,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
            )

            ledger_path = os.path.join(repo, ".synthesis", "ledger.jsonl")
            assert os.path.exists(ledger_path)

            result = subprocess.run(
                [sys.executable, "-m", "synthesis.apps.cli.main",
                 "ledger", "verify", "--path", ledger_path],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
            )
            assert result.returncode == 0

    def test_cli_doctor(self):
        """CLI 'synthesis doctor' should run without error."""
        result = subprocess.run(
            [sys.executable, "-m", "synthesis.apps.cli.main", "doctor"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
        )
        assert result.returncode == 0

    def test_cli_dashboard(self):
        """CLI 'synthesis dashboard' should run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = _setup_golden_repo(tmpdir)

            subprocess.run(
                [sys.executable, "-m", "synthesis.apps.cli.main",
                 "run", "--task", "bugfix", "--repo", repo],
                capture_output=True, timeout=60,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
            )

            ledger_path = os.path.join(repo, ".synthesis", "ledger.jsonl")
            result = subprocess.run(
                [sys.executable, "-m", "synthesis.apps.cli.main",
                 "dashboard", "--ledger", ledger_path],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
            )
            assert result.returncode == 0

    def test_cli_rejects_bad_repo(self):
        """CLI should reject a nonexistent repo path."""
        result = subprocess.run(
            [sys.executable, "-m", "synthesis.apps.cli.main",
             "run", "--task", "bugfix", "--repo", "/nonexistent/path"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "..")},
        )
        assert result.returncode != 0
