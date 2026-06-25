"""Approval system — task-scoped, expiring, one-use approvals."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone, timedelta


@dataclass
class Approval:
    task_id: str
    requested_action: str
    status: str = "pending"  # pending, approved, denied, revoked, expired
    max_uses: int = 1
    uses: int = 0
    expires_at: Optional[str] = None
    immutable_policy_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "requested_action": self.requested_action,
            "status": self.status,
            "max_uses": self.max_uses,
            "uses": self.uses,
            "expires_at": self.expires_at,
            "immutable_policy_keys": self.immutable_policy_keys,
        }


def approval_allows(
    approval: Approval,
    task_id: str,
    requested_action: str,
    now: Optional[datetime] = None,
) -> bool:
    """Check if an approval allows a specific action. Returns True/False."""
    if approval.status != "approved":
        return False
    if approval.task_id != task_id:
        return False
    if approval.requested_action != requested_action:
        return False
    if approval.uses >= approval.max_uses:
        return False

    # Check expiry
    if approval.expires_at and now is None:
        now = datetime.now(timezone.utc)
    if approval.expires_at and now:
        try:
            expires = datetime.fromisoformat(approval.expires_at)
            if now >= expires:
                return False
        except (ValueError, TypeError):
            return False

    # Immutable policy attempt blocked
    if approval.immutable_policy_keys:
        return False

    return True
