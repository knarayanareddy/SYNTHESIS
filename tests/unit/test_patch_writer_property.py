"""Property-based tests for the deterministic patch writer."""

import os
import tempfile
import pytest
from synthesis.packages.codegraph.patch_writer import apply_patch


class TestPatchWriterProperties:
    """Test patch_writer behavior across varied inputs."""

    def test_patch_preserves_other_lines(self):
        """Patching one line should not change any other line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            original = "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
            with open(filepath, "w") as f:
                f.write(original)

            apply_patch(tmpdir, "test.py", "return 1", "return 42")

            with open(filepath) as f:
                result = f.read()

            lines = result.splitlines()
            assert any("return 42" in l for l in lines)
            assert any("return 2" in l for l in lines)
            assert any("def foo():" in l for l in lines)
            assert any("def bar():" in l for l in lines)

    def test_patch_preserves_indentation(self):
        """Patching should preserve the original line's indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            original = "def foo():\n    return 1\n"
            with open(filepath, "w") as f:
                f.write(original)

            apply_patch(tmpdir, "test.py", "return 1", "return 2")

            with open(filepath) as f:
                result = f.read()

            assert "    return 2" in result

    def test_patch_with_trailing_whitespace_in_original(self):
        """Matching strips whitespace, so trailing spaces don't prevent match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            original = "return 1   \n"
            with open(filepath, "w") as f:
                f.write(original)

            result = apply_patch(tmpdir, "test.py", "return 1", "return 2")
            assert result.success

    def test_patch_empty_file(self):
        """Patching an empty file should fail gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            with open(filepath, "w") as f:
                f.write("")

            result = apply_patch(tmpdir, "test.py", "return 1", "return 2")
            assert not result.success
            assert "No matching" in result.error

    def test_patch_file_not_found(self):
        """Patching a nonexistent file should fail gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = apply_patch(tmpdir, "nonexistent.py", "x", "y")
            assert not result.success

    def test_patch_binary_file(self):
        """Patching a non-text file should fail gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.bin")
            with open(filepath, "wb") as f:
                f.write(b"\x00\x01\x02\x03")

            result = apply_patch(tmpdir, "test.bin", "x", "y")
            assert not result.success

    def test_patch_long_line(self):
        """Patching a very long line should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            long_line = "x" * 10000
            original = f"{long_line}\n"
            with open(filepath, "w") as f:
                f.write(original)

            result = apply_patch(tmpdir, "test.py", long_line, "replaced")
            assert result.success

    def test_patch_with_special_characters(self):
        """Patching lines with special characters should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            original = 'print("hello\\nworld")\n'
            with open(filepath, "w") as f:
                f.write(original)

            result = apply_patch(tmpdir, "test.py", 'print("hello\\nworld")', 'pass')
            assert result.success

    def test_patch_idempotent(self):
        """Applying the same patch twice should fail on second attempt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            with open(filepath, "w") as f:
                f.write("return 1\n")

            r1 = apply_patch(tmpdir, "test.py", "return 1", "return 2")
            assert r1.success

            r2 = apply_patch(tmpdir, "test.py", "return 1", "return 2")
            assert not r2.success  # Line no longer exists
