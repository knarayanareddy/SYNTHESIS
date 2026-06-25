"""Policy constants — circuit breakers, mutation blocklist, command lists."""

RUNTIME_MUTATION_BLOCKLIST = [
    "local_first",
    "cloud_requires_explicit_approval",
    "network_default",
    "max_iterations_by_task",
    "safety_circuit_breakers",
    "routing_weights",
    "prompt_templates",
    "workflow_variants",
    "router_policy",
    "safety_policy",
    "cloud_policy",
    "sandbox_policy",
    "max_cap",
    "audit_policy",
]

# Re-export sandbox allow/deny lists for policy module
from synthesis.packages.sandbox.runner import COMMAND_ALLOWLIST, COMMAND_DENYLIST, SHELL_METACHARACTERS

__all__ = [
    "RUNTIME_MUTATION_BLOCKLIST",
    "COMMAND_ALLOWLIST",
    "COMMAND_DENYLIST",
    "SHELL_METACHARACTERS",
]
