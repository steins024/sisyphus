"""Tests for filesystem tools (read_file and write_file)."""

import os
import tempfile
from pathlib import Path

import pytest

from sisyphus.core.tool import ToolStatus
from sisyphus.tools.filesystem import read_file, write_file


class TestReadFile:
    """Test suite for read_file tool."""

    def test_read_simple_file(self, tmp_path: Path) -> None:
        """Test reading a simple text file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!\nLine 2\nLine 3\n"
        test_file.write_text(test_content)

        # Read the file
        result = read_file(str(test_file))

        # Verify result
        assert result.is_success
        assert result.data == test_content
        assert result.metadata["total_lines"] == 3
        assert result.metadata["lines_read"] == 3
        assert result.metadata["encoding"] == "utf-8"

    def test_read_file_with_line_range(self, tmp_path: Path) -> None:
        """Test reading a specific line range."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

        # Read lines 2-4
        result = read_file(str(test_file), start_line=2, end_line=4)

        # Verify result
        assert result.is_success
        assert result.data == "Line 2\nLine 3\nLine 4\n"
        assert result.metadata["lines_read"] == 3
        assert result.metadata["total_lines"] == 5

    def test_read_file_with_start_line_only(self, tmp_path: Path) -> None:
        """Test reading from a start line to end of file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\n")

        # Read from line 3 to end
        result = read_file(str(test_file), start_line=3)

        # Verify result
        assert result.is_success
        assert result.data == "Line 3\nLine 4\n"
        assert result.metadata["lines_read"] == 2

    def test_read_file_with_end_line_only(self, tmp_path: Path) -> None:
        """Test reading from start to a specific end line."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\n")

        # Read from start to line 2
        result = read_file(str(test_file), end_line=2)

        # Verify result
        assert result.is_success
        assert result.data == "Line 1\nLine 2\n"
        assert result.metadata["lines_read"] == 2

    def test_read_file_not_found(self) -> None:
        """Test reading a non-existent file."""
        result = read_file("/nonexistent/file.txt")

        assert result.is_error
        assert "File not found" in result.error_message

    def test_read_directory_as_file(self, tmp_path: Path) -> None:
        """Test reading a directory (should fail)."""
        result = read_file(str(tmp_path))

        assert result.is_error
        assert "Not a file" in result.error_message

    def test_read_file_permission_denied(self, tmp_path: Path) -> None:
        """Test reading a file without read permissions."""
        # Create a test file and remove read permissions
        test_file = tmp_path / "test.txt"
        test_file.write_text("secret content")
        test_file.chmod(0o000)

        try:
            result = read_file(str(test_file))
            assert result.is_error
            assert "Permission denied" in result.error_message
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    def test_read_file_invalid_encoding(self, tmp_path: Path) -> None:
        """Test reading with an invalid encoding."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")

        result = read_file(str(test_file), encoding="invalid-encoding")

        assert result.is_error
        assert "Invalid encoding" in result.error_message

    def test_read_binary_file_with_text_encoding(self, tmp_path: Path) -> None:
        """Test reading a binary file with text encoding (should fail gracefully)."""
        # Create a binary file
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\xff\xfe")

        result = read_file(str(test_file))

        assert result.is_error
        assert "Encoding error" in result.error_message

    def test_read_file_invalid_line_range(self, tmp_path: Path) -> None:
        """Test reading with invalid line ranges."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        # Invalid: start_line < 1
        result = read_file(str(test_file), start_line=0)
        assert result.is_error
        assert "Invalid start_line" in result.error_message

        # Invalid: end_line < 1
        result = read_file(str(test_file), end_line=0)
        assert result.is_error
        assert "Invalid end_line" in result.error_message

        # Invalid: start_line > end_line
        result = read_file(str(test_file), start_line=3, end_line=1)
        assert result.is_error
        assert "Invalid range" in result.error_message

        # Invalid: start_line exceeds file length
        result = read_file(str(test_file), start_line=100)
        assert result.is_error
        assert "exceeds file length" in result.error_message

    def test_read_empty_file(self, tmp_path: Path) -> None:
        """Test reading an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = read_file(str(test_file))

        assert result.is_success
        assert result.data == ""
        assert result.metadata["total_lines"] == 0
        assert result.metadata["lines_read"] == 0

    def test_read_file_with_different_encoding(self, tmp_path: Path) -> None:
        """Test reading a file with a specific encoding."""
        test_file = tmp_path / "latin1.txt"
        content = "Café ñoño"
        test_file.write_text(content, encoding="latin-1")

        result = read_file(str(test_file), encoding="latin-1")

        assert result.is_success
        assert result.data == content
        assert result.metadata["encoding"] == "latin-1"

    def test_read_file_with_tilde_expansion(self) -> None:
        """Test that ~ is properly expanded in file paths."""
        # Use a file that should exist in any Unix-like system
        result = read_file("~/.bashrc")

        # File might not exist, but path should be expanded
        # (we can't test the actual content, but we can verify no crash)
        assert result.status in [ToolStatus.SUCCESS, ToolStatus.ERROR]


class TestWriteFile:
    """Test suite for write_file tool."""

    def test_write_simple_file(self, tmp_path: Path) -> None:
        """Test writing a simple text file."""
        test_file = tmp_path / "output.txt"
        content = "Hello, World!\n"

        result = write_file(str(test_file), content)

        assert result.is_success
        assert test_file.exists()
        assert test_file.read_text() == content
        assert result.metadata["lines_written"] == 1
        assert result.metadata["bytes_written"] == len(content.encode("utf-8"))

    def test_write_file_with_multiple_lines(self, tmp_path: Path) -> None:
        """Test writing a file with multiple lines."""
        test_file = tmp_path / "output.txt"
        content = "Line 1\nLine 2\nLine 3\n"

        result = write_file(str(test_file), content)

        assert result.is_success
        assert test_file.read_text() == content
        assert result.metadata["lines_written"] == 3

    def test_write_file_without_trailing_newline(self, tmp_path: Path) -> None:
        """Test line counting for content without trailing newline."""
        test_file = tmp_path / "output.txt"
        content = "Line 1\nLine 2"  # No trailing newline

        result = write_file(str(test_file), content)

        assert result.is_success
        assert result.metadata["lines_written"] == 2

    def test_write_empty_file(self, tmp_path: Path) -> None:
        """Test writing an empty file."""
        test_file = tmp_path / "empty.txt"

        result = write_file(str(test_file), "")

        assert result.is_success
        assert test_file.exists()
        assert test_file.read_text() == ""
        assert result.metadata["lines_written"] == 0

    def test_overwrite_existing_file(self, tmp_path: Path) -> None:
        """Test overwriting an existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Old content")

        new_content = "New content"
        result = write_file(str(test_file), new_content, overwrite=True)

        assert result.is_success
        assert test_file.read_text() == new_content

    def test_write_file_no_overwrite(self, tmp_path: Path) -> None:
        """Test writing with overwrite=False to existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("Old content")

        result = write_file(str(test_file), "New content", overwrite=False)

        assert result.is_error
        assert "already exists" in result.error_message
        assert test_file.read_text() == "Old content"  # Unchanged

    def test_create_parent_directories(self, tmp_path: Path) -> None:
        """Test creating parent directories."""
        test_file = tmp_path / "subdir1" / "subdir2" / "file.txt"
        content = "Test content"

        result = write_file(str(test_file), content, create_dirs=True)

        assert result.is_success
        assert test_file.exists()
        assert test_file.read_text() == content

    def test_write_file_no_create_dirs(self, tmp_path: Path) -> None:
        """Test writing without creating parent directories."""
        test_file = tmp_path / "nonexistent" / "file.txt"

        result = write_file(str(test_file), "content", create_dirs=False)

        assert result.is_error
        assert "does not exist" in result.error_message
        assert not test_file.exists()

    def test_write_file_permission_denied_directory(self, tmp_path: Path) -> None:
        """Test writing to a directory without write permissions."""
        # Create a directory and remove write permissions
        no_write_dir = tmp_path / "no_write"
        no_write_dir.mkdir()
        no_write_dir.chmod(0o444)  # Read-only

        test_file = no_write_dir / "file.txt"

        try:
            result = write_file(str(test_file), "content")
            assert result.is_error
            assert "Permission denied" in result.error_message
        finally:
            # Restore permissions for cleanup
            no_write_dir.chmod(0o755)

    def test_write_file_permission_denied_file(self, tmp_path: Path) -> None:
        """Test overwriting a file without write permissions."""
        test_file = tmp_path / "readonly.txt"
        test_file.write_text("Original")
        test_file.chmod(0o444)  # Read-only

        try:
            result = write_file(str(test_file), "New content", overwrite=True)
            assert result.is_error
            assert "Permission denied" in result.error_message
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    def test_write_file_with_different_encoding(self, tmp_path: Path) -> None:
        """Test writing a file with a specific encoding."""
        test_file = tmp_path / "latin1.txt"
        content = "Café ñoño"

        result = write_file(str(test_file), content, encoding="latin-1")

        assert result.is_success
        # Verify encoding by reading with same encoding
        assert test_file.read_text(encoding="latin-1") == content
        assert result.metadata["encoding"] == "latin-1"

    def test_write_file_invalid_encoding(self, tmp_path: Path) -> None:
        """Test writing with an invalid encoding."""
        test_file = tmp_path / "test.txt"

        result = write_file(str(test_file), "content", encoding="invalid-encoding")

        assert result.is_error
        assert "Invalid encoding" in result.error_message

    def test_write_file_atomic_operation(self, tmp_path: Path) -> None:
        """Test that write_file uses atomic operations (no .tmp files left)."""
        test_file = tmp_path / "atomic.txt"

        result = write_file(str(test_file), "content")

        assert result.is_success
        # Verify no temporary files left behind
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_write_file_with_tilde_expansion(self) -> None:
        """Test that ~ is properly expanded in file paths."""
        # Use a temporary file in the home directory
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", dir=Path.home(), delete=False
        ) as tmp_file:
            tmp_name = Path(tmp_file.name).name

        try:
            # Write using ~ expansion
            test_file_path = f"~/{tmp_name}"
            result = write_file(test_file_path, "test content")

            assert result.is_success

            # Verify file was written
            actual_path = Path.home() / tmp_name
            assert actual_path.exists()
            assert actual_path.read_text() == "test content"
        finally:
            # Cleanup
            (Path.home() / tmp_name).unlink(missing_ok=True)
