"""Unit tests for sandbox runner."""

import os
import tempfile
import pytest
from synthesis.packages.sandbox.runner import (
    validate_argv, run_argv, parse_shell_string_forbidden,
    canonicalize_workspace_path, SandboxViolation, SandboxDecision,
)


class TestSandbox:
    def test_shell_strings_forbidden(self):
        with pytest.raises(SandboxViolation):
            parse_shell_string_forbidden("pytest tests/test_auth.py")

    def test_path_escape_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            decision = validate_argv(
                ["pytest", "../../etc/passwd"],
                tmpdir,
            )
            assert not decision.allowed

    def test_symlink_escape_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create symlink to /etc/passwd
            link_path = os.path.join(tmpdir, "escape")
            try:
                os.symlink("/etc/passwd", link_path)
            except OSError:
                pytest.skip("Cannot create symlink in this environment")

            decision = validate_argv(
                ["cat", "escape"],
                tmpdir,
            )
            assert not decision.allowed

    def test_shell_metacharacters_denied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            decision = validate_argv(
                ["echo", "hello;", "rm", "-rf", "/"],
                tmpdir,
            )
            assert not decision.allowed
            assert "metacharacter" in decision.reason.lower()

    def test_allowed_argv_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_argv(
                ["echo", "hello"],
                tmpdir,
                timeout_sec=5,
            )
            assert result.returncode == 0
            assert "hello" in result.stdout

    def test_command_not_in_allowlist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            decision = validate_argv(
                ["nano", "file.txt"],
                tmpdir,
            )
            assert not decision.allowed
            assert "allowlist" in decision.reason.lower()

    def test_denylisted_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            decision = validate_argv(
                ["curl", "http://example.com"],
                tmpdir,
            )
            assert not decision.allowed
            assert "denylist" in decision.reason.lower()

    def test_empty_argv_denied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            decision = validate_argv([], tmpdir)
            assert not decision.allowed
            assert "Empty" in decision.reason

    def test_canonicalize_workspace_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            resolved = canonicalize_workspace_path(tmpdir, "subdir/file.txt")
            assert resolved.startswith(os.path.realpath(tmpdir))

    def test_timeout_enforcement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_argv(
                ["sleep", "10"],
                tmpdir,
                timeout_sec=1,
            )
            assert result.timed_out

    def test_sandbox_decision_to_payload(self):
        d = SandboxDecision(True, "echo", ["echo", "hi"], "ok", "/workspace")
        p = d.to_event_payload()
        assert p["allowed"] is True
        assert p["command"] == "echo"
        assert "workspace" in p

    def test_pytest_runs_in_sandbox(self):
        """Verify pytest can run through sandbox."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a passing test
            test_dir = os.path.join(tmpdir, "tests")
            os.makedirs(test_dir, exist_ok=True)
            with open(os.path.join(test_dir, "test_ok.py"), "w") as f:
                f.write("def test_ok():\n    assert True\n")

            result = run_argv(
                ["pytest", "tests/test_ok.py", "-v"],
                tmpdir,
                timeout_sec=30,
            )
            assert result.returncode == 0
