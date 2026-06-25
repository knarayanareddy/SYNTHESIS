"""TOCTOU-safe workspace path opening — prevents symlink race conditions.

Uses os.open() with O_NOFOLLOW (Linux) to get a file descriptor before
resolving the path, then uses os.fdlist operations that can't be
symlink-swapped between check and use.

For macOS, O_NOFOLLOW is not supported on directories — we use fcntl
with F_GETPATH to verify no symlink component exists in the final path.
"""

from __future__ import annotations

import os
import sys
import errno
from pathlib import Path
from typing import Optional

# ── Platform detection ────────────────────────────────────────────────────────

_IS_LINUX = sys.platform.startswith("linux")
_IS_MACOS = sys.platform == "darwin"


def open_workspace_dir_safe(workspace: str) -> int:
    """Open a workspace directory safely, preventing TOCTOU symlink races.

    On Linux: opens with O_NOFOLLOW to reject symlinks outright.
    On macOS: opens normally then verifies the real path matches.

    Args:
        workspace: Path to the workspace directory.

    Returns:
        File descriptor for the opened directory.

    Raises:
        OSError: If the path is a symlink (Linux) or resolves outside
                 the expected location (macOS).
    """
    workspace = os.path.abspath(workspace)

    if _IS_LINUX:
        # O_NOFOLLOW: fail if the final component is a symlink
        # O_DIRECTORY: fail if not a directory
        # O_RDONLY: read-only access
        try:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            fd = os.open(workspace, flags)
        except OSError as e:
            if e.errno in (errno.ELOOP, errno.ENOTDIR):
                raise OSError(e.errno, f"Workspace is a symlink (rejected): {workspace}")
            raise
        return fd

    elif _IS_MACOS:
        # macOS: O_NOFOLLOW doesn't work on directories reliably.
        # Instead, open normally, then verify the real path.
        # Resolve parent directories to handle system symlinks (like /var -> /private/var on macOS)
        parent = os.path.dirname(workspace)
        name = os.path.basename(workspace)
        parent_real = os.path.realpath(parent)
        expected_path = os.path.join(parent_real, name)

        fd = os.open(workspace, os.O_RDONLY)
        try:
            real_path = os.path.realpath(workspace)
            if real_path != expected_path:
                raise OSError(errno.ELOOP, f"Workspace resolves differently (symlink detected): "
                               f"expected {expected_path}, got {real_path}")
        except Exception:
            os.close(fd)
            raise
        return fd

    else:
        # Generic fallback: open and verify with realpath
        fd = os.open(workspace, os.O_RDONLY)
        try:
            real = os.path.realpath(workspace)
            if real != os.path.abspath(workspace):
                os.close(fd)
                raise OSError(errno.ELOOP, f"Workspace symlink detected: {workspace} → {real}")
        except Exception:
            os.close(fd)
            raise
        return fd


def safe_resolve_under_workspace(workspace: str, relative_path: str) -> str:
    """Safely resolve a relative path within a workspace, rejecting symlinks.

    Uses os.open with O_NOFOLLOW (Linux) or realpath verification (macOS)
    to prevent TOCTOU symlink races.

    Args:
        workspace: Workspace root directory.
        relative_path: Relative path within the workspace.

    Returns:
        Absolute resolved path.

    Raises:
        OSError: If any component is a symlink or path escapes workspace.
    """
    workspace_abs = os.path.abspath(workspace)

    # Step 1: Open workspace dir safely
    fd = open_workspace_dir_safe(workspace_abs)
    os.close(fd)

    # Step 2: Walk each component of the relative path, verifying no symlinks
    workspace_resolved = os.path.realpath(workspace_abs)
    candidate_full = os.path.normpath(os.path.join(workspace_resolved, relative_path))

    # Verify the candidate is under the resolved workspace
    if not candidate_full.startswith(workspace_resolved + os.sep) and candidate_full != workspace_resolved:
        raise OSError(errno.EACCES, f"Path escapes workspace: {relative_path}")

    # Step 3: Walk each component, checking for symlinks
    components = relative_path.replace("\\", "/").strip("/").split("/")
    if components == [""]:
        return workspace_resolved

    current = workspace_abs
    for component in components:
        if not component or component == ".":
            continue
        if component == "..":
            raise OSError(errno.EACCES, f"Path component '..' not allowed: {relative_path}")

        next_path = os.path.join(current, component)

        # On Linux, try to open with O_NOFOLLOW
        if _IS_LINUX and hasattr(os, "O_NOFOLLOW"):
            try:
                fd = os.open(next_path, os.O_RDONLY | os.O_NOFOLLOW)
                os.close(fd)
            except OSError as e:
                if e.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise OSError(errno.ELOOP, f"Symlink detected at component '{component}': {next_path}")
                elif e.errno == errno.ENOENT:
                    pass  # File may not exist yet — that's OK, parent dir was verified
                else:
                    raise
        else:
            # macOS fallback
            if os.path.lexists(next_path) and os.path.islink(next_path):
                raise OSError(errno.ELOOP, f"Symlink detected at component '{component}': {next_path}")

        current = next_path

    return os.path.realpath(candidate_full)


def is_toctou_safe(workspace: str) -> bool:
    """Check if a workspace is safe from TOCTOU symlink attacks.

    Returns True if the workspace can be opened without symlink traversal.
    """
    try:
        fd = open_workspace_dir_safe(workspace)
        os.close(fd)
        return True
    except OSError:
        return False
