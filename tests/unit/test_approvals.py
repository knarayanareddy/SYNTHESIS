"""Unit tests for approval system."""

import pytest
from datetime import datetime, timezone, timedelta
from synthesis.packages.approvals.policy import Approval, approval_allows


class TestApprovals:
    def test_approval_exact_task_match(self):
        approval = Approval(
            task_id="task-1",
            requested_action="sandbox_exec",
            status="approved",
            max_uses=1,
        )
        assert approval_allows(approval, "task-1", "sandbox_exec")
        assert not approval_allows(approval, "task-2", "sandbox_exec")
        assert not approval_allows(approval, "task-1", "different_action")

    def test_approval_max_uses(self):
        approval = Approval(
            task_id="task-1",
            requested_action="sandbox_exec",
            status="approved",
            max_uses=2,
            uses=2,
        )
        assert not approval_allows(approval, "task-1", "sandbox_exec")

    def test_approval_expiry(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        approval = Approval(
            task_id="task-1",
            requested_action="sandbox_exec",
            status="approved",
            expires_at=past,
        )
        assert not approval_allows(approval, "task-1", "sandbox_exec")

    def test_approval_not_expired(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        approval = Approval(
            task_id="task-1",
            requested_action="sandbox_exec",
            status="approved",
            expires_at=future,
        )
        assert approval_allows(approval, "task-1", "sandbox_exec")

    def test_approval_immutable_attempt_block(self):
        approval = Approval(
            task_id="task-1",
            requested_action="sandbox_exec",
            status="approved",
            immutable_policy_keys=["local_first"],
        )
        assert not approval_allows(approval, "task-1", "sandbox_exec")

    def test_approval_not_approved_status(self):
        approval = Approval(
            task_id="task-1",
            requested_action="sandbox_exec",
            status="pending",
        )
        assert not approval_allows(approval, "task-1", "sandbox_exec")

    def test_approval_to_dict(self):
        approval = Approval(
            task_id="t1",
            requested_action="a1",
            status="approved",
            max_uses=1,
            uses=0,
        )
        d = approval.to_dict()
        assert d["task_id"] == "t1"
        assert d["status"] == "approved"
        assert d["max_uses"] == 1
