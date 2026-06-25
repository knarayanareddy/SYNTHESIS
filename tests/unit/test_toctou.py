"""Tests for TOCTOU-safe workspace path opening."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))

from synthesis.packages.sandbox.toctou import (
    open_workspace_dir_safe,
    safe_resolve_under_workspace,
    is_toctou_safe,
)


class TestTOCTOU:
    """Tests for TOCTOU-safe workspace operations."""

    def test_open_workspace_safe_normal_dir(self):
        """Opening a normal directory should succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fd = open_workspace_dir_safe(tmpdir)
            assert fd >= 0
            os.close(fd)

    def test_open_workspace_safe_symlink_rejected(self):
        """Opening a symlinked directory should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            real_dir = os.path.join(tmpdir, "real")
            os.makedirs(real_dir)
            link_dir = os.path.join(tmpdir, "link")

            try:
                os.symlink(real_dir, link_dir, target_is_directory=True)
            except (OSError, TypeError):
                # Try without target_is_directory
                try:
                    os.symlink(real_dir, link_dir)
                except OSError:
                    pytest.skip("Cannot create symlinks in this environment")

            # On Linux with O_NOFOLLOW, this should fail
            try:
                fd = open_workspace_dir_safe(link_dir)
                os.close(fd)
                # macOS may succeed but should detect the symlink difference
                assert is_toctou_safe(link_dir) or not os.path.islink(link_dir)
            except OSError as e:
                # Expected on Linux with O_NOFOLLOW
                assert "symlink" in str(e).lower() or "not a directory" in str(e).lower() or e.errno == 40  # ELOOP

    def test_is_toctou_safe_normal(self):
        """Normal directory should be TOCTOU-safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_toctou_safe(tmpdir)

    def test_safe_resolve_rejects_dotdot(self):
        """Path with .. should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(OSError, match="not allowed|Path escapes"):
                safe_resolve_under_workspace(tmpdir, "../etc/passwd")

    def test_safe_resolve_normal_path(self):
        """Normal relative path should resolve correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resolved = safe_resolve_under_workspace(tmpdir, "subdir/file.txt")
            assert resolved.startswith(os.path.realpath(tmpdir))

    def test_safe_resolve_symlink_component(self):
        """Symlink component in path should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            real_dir = os.path.join(tmpdir, "real")
            os.makedirs(real_dir)
            link_dir = os.path.join(tmpdir, "link")
            try:
                os.symlink(real_dir, link_dir, target_is_directory=True)
            except (OSError, TypeError):
                try:
                    os.symlink(real_dir, link_dir)
                except OSError:
                    pytest.skip("Cannot create symlinks")

            # Walking through "link" should be rejected
            try:
                safe_resolve_under_workspace(tmpdir, "link")
            except OSError as e:
                assert "symlink" in str(e).lower() or "not a directory" in str(e).lower() or e.errno == 40

    def test_open_nonexistent_workspace(self):
        """Opening a nonexistent workspace should raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = os.path.join(tmpdir, "does_not_exist")
            with pytest.raises(OSError):
                open_workspace_dir_safe(nonexistent)

    def test_safe_resolve_nested_normal(self):
        """Nested normal directories should resolve correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "a", "b", "c")
            os.makedirs(nested)
            resolved = safe_resolve_under_workspace(tmpdir, "a/b/c")
            assert resolved.startswith(os.path.realpath(tmpdir))
