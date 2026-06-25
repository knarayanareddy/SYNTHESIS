"""Sandbox runner — argv-only execution with workspace path confinement.

Now integrated with TOCTOU-safe path resolution from toctou.py.
Path validation uses safe_resolve_under_workspace() to prevent
symlink race conditions between check and use.
"""
from __future__ import annotations

import os
import subprocess
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("synthesis.sandbox")

# ── Allow/Deny lists ──────────────────────────────────────────────────────────

COMMAND_ALLOWLIST: set[str] = {
    "pytest", "python", "python3", "pip", "git", "ls", "cat", "echo",
    "grep", "find", "wc", "head", "tail", "sort", "uniq", "diff",
    "touch", "mkdir", "rm", "cp", "mv", "chmod", "true", "false",
    "ruff", "mypy", "black", "isort", "sleep",
}

COMMAND_DENYLIST: set[str] = {
    "sh", "bash", "zsh", "dash", "ksh", "curl", "wget", "nc",
    "ncat", "telnet", "ssh", "scp", "sftp", "su", "sudo", "chown",
    "mount", "umount", "systemctl", "service", "docker", "kubectl",
}

SHELL_METACHARACTERS: set[str] = {";", "|", "&", "`", "$", ">", "<"}


# ── Import TOCTOU-safe path resolution ────────────────────────────────────────

try:
    from synthesis.packages.sandbox.toctou import safe_resolve_under_workspace
    _TOCTOU_AVAILABLE = True
except ImportError:
    _TOCTOU_AVAILABLE = False


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class SandboxDecision:
    """Represents an allow/deny decision for a sandbox operation."""
    allowed: bool
    command: str
    argv: list[str]
    reason: str = ""
    workspace: str = ""

    def to_event_payload(self) -> dict:
        return {
            "allowed": self.allowed,
            "command": self.command,
            "argv": self.argv,
            "reason": self.reason,
            "workspace": self.workspace,
        }


@dataclass
class SandboxResult:
    """Result of a sandboxed command execution."""
    command: str
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    workspace: str = ""


class SandboxViolation(Exception):
    """Raised when a sandbox rule is violated."""
    def __init__(self, decision: SandboxDecision):
        self.decision = decision
        super().__init__(f"Sandbox violation: {decision.reason}")


# ── Path validation ───────────────────────────────────────────────────────────

def _resolve_workspace_safe(workspace: str) -> str:
    """Resolve workspace path using TOCTOU-safe method if available."""
    workspace = os.path.abspath(workspace)
    if _TOCTOU_AVAILABLE:
        try:
            return safe_resolve_under_workspace(workspace, ".")
        except OSError as e:
            raise SandboxViolation(SandboxDecision(
                allowed=False, command="", argv=[],
                reason=f"TOCTOU check failed for workspace {workspace}: {e}",
                workspace=workspace,
            ))
    # Fallback to Path.resolve() — log warning
    logger.warning(
        "TOCTOU protection unavailable — using Path.resolve() fallback. "
        "For production use with untrusted repos, ensure the toctou module "
        "is importable (check synthesis.packages.sandbox.toctou)."
    )
    return str(Path(workspace).resolve(strict=True))


def canonicalize_workspace_path(workspace: str, candidate: str) -> str:
    """Resolve a candidate path under workspace, raising if it escapes.

    Uses TOCTOU-safe resolution when available; falls back to Path.resolve().
    """
    if _TOCTOU_AVAILABLE:
        try:
            resolved = safe_resolve_under_workspace(workspace, candidate)
        except OSError as e:
            raise SandboxViolation(SandboxDecision(
                allowed=False, command="", argv=[],
                reason=f"Path rejected by TOCTOU check: {candidate} — {e}",
                workspace=workspace,
            ))
    else:
        workspace_resolved = Path(workspace).resolve(strict=True)
        candidate_path = (workspace_resolved / candidate).resolve()
        if not str(candidate_path).startswith(str(workspace_resolved) + os.sep) \
           and str(candidate_path) != str(workspace_resolved):
            raise SandboxViolation(SandboxDecision(
                allowed=False, command="", argv=[],
                reason=f"Path escape: {candidate} resolves to {candidate_path} outside {workspace_resolved}",
                workspace=workspace,
            ))
        resolved = str(candidate_path)

    ws_root = _resolve_workspace_safe(workspace)
    if not resolved.startswith(ws_root + os.sep) and resolved != ws_root:
        raise SandboxViolation(SandboxDecision(
            allowed=False, command="", argv=[],
            reason=f"Path escape: {candidate} resolves to {resolved} outside {ws_root}",
            workspace=workspace,
        ))
    return resolved


def _contains_shell_metacharacters(argv: list[str]) -> bool:
    for arg in argv:
        for ch in arg:
            if ch in SHELL_METACHARACTERS:
                return True
    return False


def validate_argv(argv: list[str], workspace: str, cwd: Optional[str] = None) -> SandboxDecision:
    if not argv:
        return SandboxDecision(False, "", argv, "Empty argv denied", workspace)
    command = argv[0]
    command_basename = os.path.basename(command)
    if command_basename in COMMAND_DENYLIST:
        return SandboxDecision(False, command, argv,
                               f"Command '{command_basename}' is denylisted", workspace)
    if command_basename not in COMMAND_ALLOWLIST:
        return SandboxDecision(False, command, argv,
                               f"Command '{command_basename}' not in allowlist", workspace)
    if _contains_shell_metacharacters(argv):
        return SandboxDecision(False, command, argv,
                               "Shell metacharacters denied in argv", workspace)
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        try:
            canonicalize_workspace_path(workspace, arg)
        except SandboxViolation as e:
            return SandboxDecision(False, command, argv, e.decision.reason, workspace)
    if cwd is not None:
        try:
            canonicalize_workspace_path(workspace, cwd)
        except SandboxViolation as e:
            return SandboxDecision(False, command, argv, e.decision.reason, workspace)
    return SandboxDecision(True, command, argv, "ok", workspace)


def run_argv(
    argv: list[str], workspace: str, cwd: Optional[str] = None,
    timeout_sec: int = 60,
) -> SandboxResult:
    decision = validate_argv(argv, workspace, cwd)
    if not decision.allowed:
        raise SandboxViolation(decision)
    resolved_cwd = _resolve_workspace_safe(workspace)
    if cwd is not None:
        resolved_cwd = canonicalize_workspace_path(workspace, cwd)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": workspace}
    try:
        result = subprocess.run(
            argv, cwd=resolved_cwd, env=env, timeout=timeout_sec,
            capture_output=True, text=True, shell=False,
        )
        return SandboxResult(command=argv[0], argv=argv,
                             returncode=result.returncode, stdout=result.stdout,
                             stderr=result.stderr, timed_out=False, workspace=workspace)
    except subprocess.TimeoutExpired:
        return SandboxResult(command=argv[0], argv=argv,
                             returncode=-1, stdout="", stderr="Command timed out",
                             timed_out=True, workspace=workspace)


def parse_shell_string_forbidden(command: str) -> None:
    raise SandboxViolation(SandboxDecision(
        False, "", [],
        "Shell string execution is forbidden. Use argv arrays only.", "",
    ))
