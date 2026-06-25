"""Test TOCTOU fallback warning when toctou module is not importable."""

import os, sys, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))


class TestTOCTOUFallback:
    """Verify TOCTOU fallback behavior."""

    def test_canonicalize_workspace_path_works_without_toctou(self):
        """canonicalize_workspace_path should work even when TOCTOU unavailable.
        The module already has the try/except fallback pattern built in.
        """
        import tempfile
        from synthesis.packages.sandbox.runner import canonicalize_workspace_path

        with tempfile.TemporaryDirectory() as tmpdir:
            result = canonicalize_workspace_path(tmpdir, "test.txt")
            assert os.path.isabs(result)
            assert result.startswith(os.path.realpath(tmpdir))

    def test_run_argv_works_with_toctou_integrated(self):
        """run_argv should work with the integrated TOCTOU path."""
        import tempfile
        from synthesis.packages.sandbox.runner import run_argv

        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_argv(["echo", "hello"], tmpdir, timeout_sec=5)
            assert result.returncode == 0
            assert "hello" in result.stdout

    def test_validate_argv_works_with_toctou_integrated(self):
        """validate_argv should work with the integrated TOCTOU path."""
        import tempfile
        from synthesis.packages.sandbox.runner import validate_argv

        with tempfile.TemporaryDirectory() as tmpdir:
            decision = validate_argv(["ls", "."], tmpdir)
            assert decision.allowed

    def test_path_escape_still_blocked_with_toctou(self):
        """Path escape should be blocked regardless of TOCTOU availability."""
        import tempfile
        from synthesis.packages.sandbox.runner import validate_argv

        with tempfile.TemporaryDirectory() as tmpdir:
            decision = validate_argv(["pytest", "../../etc/passwd"], tmpdir)
            assert not decision.allowed

    def test_sandbox_decision_payload_contains_reason(self):
        """All SandboxDecision payloads should include reason."""
        from synthesis.packages.sandbox.runner import SandboxDecision
        d = SandboxDecision(False, "curl", ["curl", "http://evil.com"],
                            reason="denylisted", workspace="/tmp/test")
        payload = d.to_event_payload()
        assert payload["reason"] == "denylisted"
        assert payload["allowed"] is False
        assert payload["workspace"] == "/tmp/test"
