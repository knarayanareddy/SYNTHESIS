"""Approval transition ledger helpers."""

from synthesis.packages.approvals.policy import Approval


APPROVAL_EVENTS = [
    "approval_requested",
    "approval_approved",
    "approval_denied",
    "approval_revoked",
    "approval_expired",
]


def ledger_approval(ctx, event_type: str, approval: Approval) -> dict:
    """Ledger an approval lifecycle event."""
    if event_type not in APPROVAL_EVENTS:
        raise ValueError(f"Unknown approval event: {event_type}")
    return ctx.append(event_type, approval.to_dict())
