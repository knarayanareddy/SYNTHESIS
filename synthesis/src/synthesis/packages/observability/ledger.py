"""Hash-chained JSONL ledger for audit, replay, and trace completeness."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from synthesis.packages.observability.event_registry import ALLOWED_EVENT_TYPES
from synthesis.packages.observability.redaction import redact_payload, assert_no_secrets


@dataclass
class LedgerVerificationResult:
    valid: bool
    total_events: int = 0
    error_event_index: int = -1
    error_message: str = ""


def canonical_json(obj: dict) -> str:
    """Deterministic JSON serialization with sorted keys."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)


def event_hash(obj: dict) -> str:
    """SHA-256 hash of canonical JSON (with blank hash_self)."""
    obj_copy = dict(obj)
    obj_copy["hash_self"] = ""
    return hashlib.sha256(canonical_json(obj_copy).encode("utf-8")).hexdigest()


class JsonlLedger:
    """Append-only hash-chained JSONL ledger."""

    def __init__(self, path: str):
        self.path = path
        self._prev_hash: Optional[str] = None
        self._event_count = 0
        # Load existing events to determine prev_hash
        if os.path.exists(path):
            self._scan_existing()

    def _scan_existing(self) -> None:
        """Scan existing ledger to find last hash."""
        try:
            with open(self.path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    event = json.loads(line)
                    self._prev_hash = event.get("hash_self", "")
                    self._event_count += 1
        except Exception:
            pass

    def append(self, event_type: str, trace_id: str, payload: dict) -> dict:
        """Append a validated, redacted, hash-chained event to the ledger.

        Raises ValueError for unregistered event types or secret values.
        """
        if event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unknown event type: {event_type}")

        # Redact payload
        redacted, _ = redact_payload(payload)
        assert_no_secrets(redacted)

        event = {
            "schema_version": "1.0",
            "event_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": redacted,
            "redaction_applied": True,
            "hash_prev": self._prev_hash,
            "hash_self": "",
        }
        event["hash_self"] = event_hash(event)

        # Append
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a") as f:
            f.write(canonical_json(event) + "\n")

        self._prev_hash = event["hash_self"]
        self._event_count += 1
        return event

    def verify(self) -> LedgerVerificationResult:
        """Verify the entire ledger's hash chain and JSON validity."""
        if not os.path.exists(self.path):
            return LedgerVerificationResult(True, 0)

        try:
            with open(self.path, "r") as f:
                lines = f.readlines()
        except Exception as e:
            return LedgerVerificationResult(False, 0, 0, f"Read error: {e}")

        prev_hash: Optional[str] = None
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as e:
                return LedgerVerificationResult(False, i, i, f"JSON error at line {i}: {e}")

            # Check hash_prev
            if event.get("hash_prev") != prev_hash:
                return LedgerVerificationResult(
                    False, i, i,
                    f"hash_prev mismatch at event {i}: expected {prev_hash}, got {event.get('hash_prev')}"
                )

            # Check hash_self
            expected_hash = event_hash(event)
            if event.get("hash_self") != expected_hash:
                return LedgerVerificationResult(
                    False, i, i,
                    f"hash_self mismatch at event {i}: expected {expected_hash}, got {event.get('hash_self')}"
                )

            prev_hash = event["hash_self"]

        return LedgerVerificationResult(True, len(lines))


# ── LedgerContext ──

class LedgerContext:
    """Request-scoped helper around JsonlLedger."""

    def __init__(self, ledger: JsonlLedger, trace_id: str):
        self.ledger = ledger
        self.trace_id = trace_id

    def append(self, event_type: str, payload: dict) -> dict:
        return self.ledger.append(event_type, self.trace_id, payload)
