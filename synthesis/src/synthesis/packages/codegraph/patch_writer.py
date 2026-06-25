"""Deterministic patch writer — applies single-line replacements to source files.

Only supports exact-line-match replacements. No model-generated patches.
All writes are sandbox-validated against workspace."""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass


@dataclass
class PatchResult:
    success: bool
    file_path: str
    old_line: str
    new_line: str
    lines_matched: int = 0
    error: str = ""

    def to_payload(self) -> dict:
        return {
            "success": self.success,
            "file_path": self.file_path,
            "old_line": self.old_line,
            "new_line": self.new_line,
            "lines_matched": self.lines_matched,
            "error": self.error,
        }


def apply_patch(
    workspace: str,
    file_path: str,
    old_line_stripped: str,
    new_line_stripped: str,
) -> PatchResult:
    """Replace exactly one line (whitespace-insensitive match) in a file.

    Args:
        workspace: Sandbox workspace root (path confinement).
        file_path: Relative path to the file within workspace.
        old_line_stripped: The line to find (matched after strip()).
        new_line_stripped: The replacement line (inserted with original indentation).

    Returns:
        PatchResult with success status and match count.
    """
    from synthesis.packages.sandbox.runner import canonicalize_workspace_path

    try:
        full_path = canonicalize_workspace_path(workspace, file_path)
    except Exception as e:
        return PatchResult(False, file_path, old_line_stripped, new_line_stripped, 0, str(e))

    path = Path(full_path)
    if not path.exists():
        return PatchResult(False, file_path, old_line_stripped, new_line_stripped, 0,
                           f"File not found: {full_path}")
    if not path.is_file():
        return PatchResult(False, file_path, old_line_stripped, new_line_stripped, 0,
                           f"Not a file: {full_path}")

    try:
        lines = path.read_text().splitlines(keepends=True)
    except Exception as e:
        return PatchResult(False, file_path, old_line_stripped, new_line_stripped, 0,
                           f"Read error: {e}")

    matches = []
    for i, line in enumerate(lines):
        if line.strip() == old_line_stripped:
            matches.append(i)

    if len(matches) == 0:
        return PatchResult(False, file_path, old_line_stripped, new_line_stripped, 0,
                           "No matching line found")
    if len(matches) > 1:
        return PatchResult(False, file_path, old_line_stripped, new_line_stripped,
                           len(matches),
                           f"Multiple matches ({len(matches)}) — ambiguous patch")

    # Single match: replace preserving original indentation
    idx = matches[0]
    original_indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
    lines[idx] = original_indent + new_line_stripped + "\n"

    try:
        path.write_text("".join(lines))
    except Exception as e:
        return PatchResult(False, file_path, old_line_stripped, new_line_stripped, 1,
                           f"Write error: {e}")

    return PatchResult(True, file_path, old_line_stripped, new_line_stripped, 1)
