"""Unit tests for ledger append, redaction, verification, and corruption detection."""

import os
import json
import tempfile
import pytest
from synthesis.packages.observability.ledger import JsonlLedger, LedgerContext, LedgerVerificationResult


class TestLedger:
    def test_ledger_append_and_verify(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = JsonlLedger(path)

            event = ledger.append("request_started", "trace-001", {"task": "bug_fix"})
            assert event["event_type"] == "request_started"
            assert event["hash_self"] != ""
            assert event["redaction_applied"] is True

            verification = ledger.verify()
            assert verification.valid
            assert verification.total_events > 0

    def test_ledger_detects_corruption(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = JsonlLedger(path)

            ledger.append("request_started", "trace-001", {"task": "bug_fix"})

            # Corrupt the ledger
            with open(path, "a") as f:
                f.write("this is not valid json\n")

            verification = ledger.verify()
            assert not verification.valid

    def test_ledger_rejects_unknown_event_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = JsonlLedger(path)

            with pytest.raises(ValueError, match="Unknown event type"):
                ledger.append("nonexistent_event", "trace-001", {})

    def test_ledger_redaction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = JsonlLedger(path)

            # Redact secrets in payload
            event = ledger.append("policy_check", "trace-001", {
                "api_key": "sk-123456789012345678901234567890",
                "safe_field": "ok",
            })
            assert event["payload"]["api_key"] == "***REDACTED***"
            assert event["payload"]["safe_field"] == "ok"

    def test_ledger_hash_chain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = JsonlLedger(path)

            e1 = ledger.append("request_started", "trace-001", {"step": 1})
            e2 = ledger.append("policy_check", "trace-001", {"step": 2})

            assert e2["hash_prev"] == e1["hash_self"]

            verification = ledger.verify()
            assert verification.valid

    def test_ledger_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = JsonlLedger(path)
            ctx = LedgerContext(ledger, "trace-001")

            e1 = ctx.append("request_started", {"task": "test"})
            e2 = ctx.append("policy_check", {"approved": True})

            assert e1["trace_id"] == "trace-001"
            assert e2["trace_id"] == "trace-001"
            verification = ledger.verify()
            assert verification.valid

    def test_ledger_secret_detection(self):
        from synthesis.packages.observability.redaction import redact_payload, assert_no_secrets

        payload = {"password": "secret123", "normal": "ok"}
        redacted, changed = redact_payload(payload)
        assert changed
        assert redacted["password"] == "***REDACTED***"

        # Assert no secrets should pass for redacted payload
        assert_no_secrets(redacted)
