"""Event type registry — allowed event types and non-sampled set."""

ALLOWED_EVENT_TYPES: set[str] = {
    "request_started", "request_completed", "policy_check", "config_snapshot",
    "approval_requested", "approval_approved", "approval_denied",
    "approval_revoked", "approval_expired",
    "model_discovery", "backend_health",
    "model_call_started", "model_call_completed", "model_call_failed",
    "route_decision", "route_outcome", "role_selection",
    "loop_iteration_started", "loop_iteration_completed",
    "loop_gate_result", "loop_terminated",
    "tool_call_started", "tool_call_completed", "tool_call_failed",
    "sandbox_exec", "sandbox_denial",
    "path_escape_blocked", "destructive_command_blocked",
    "network_request_blocked",
    "world_predict", "world_reconcile",
    "codegraph_update", "codegraph_query", "crg_propagate",
    "stale_graph_fallback",
    "memory_retrieve", "memory_commit", "memory_rollback",
    "memory_quarantined",
    "runtime_self_evolution_blocked", "cost_event",
    "ledger_checkpoint", "ledger_corruption_detected",
}

NON_SAMPLED_EVENT_TYPES: set[str] = {
    "approval_requested", "approval_approved", "approval_denied",
    "approval_revoked", "approval_expired",
    "model_call_completed", "model_call_failed",
    "tool_call_started", "tool_call_completed", "tool_call_failed",
    "sandbox_exec", "sandbox_denial",
    "path_escape_blocked", "destructive_command_blocked",
    "network_request_blocked",
    "memory_commit", "memory_rollback", "memory_quarantined",
    "runtime_self_evolution_blocked", "cost_event",
    "ledger_checkpoint", "ledger_corruption_detected",
}
