"""Tests for the search tool."""

from pathlib import Path

import pytest

from sisyphus.tools.search import search


class TestSearch:
    """Test suite for search tool."""

    def test_search_simple_pattern(self, tmp_path: Path) -> None:
        """Test searching for a simple pattern."""
        # Create test files
        (tmp_path / "file1.txt").write_text("Hello World\nGoodbye World\n")
        (tmp_path / "file2.txt").write_text("Hello Python\n")

        result = search(pattern="Hello", path=str(tmp_path))

        assert result.is_success
        assert result.metadata["matches_found"] == 2
        assert result.metadata["files_searched"] == 2
        assert len(result.data) == 2

    def test_search_regex_pattern(self, tmp_path: Path) -> None:
        """Test searching with a regex pattern."""
        # Create test file
        test_file = tmp_path / "code.py"
        test_file.write_text("def foo():\n    pass\ndef bar():\n    pass\n")

        result = search(pattern=r"def \w+\(\):", path=str(tmp_path))

        assert result.is_success
        assert result.metadata["matches_found"] == 2
        assert result.data[0]["content"] == "def foo():"
        assert result.data[1]["content"] == "def bar():"

    def test_search_case_insensitive(self, tmp_path: Path) -> None:
        """Test case-insensitive search."""
        test_file = tmp_path / "text.txt"
        test_file.write_text("Hello\nhello\nHELLO\n")

        result = search(pattern="hello", path=str(tmp_path), case_sensitive=False)

        assert result.is_success
        assert result.metadata["matches_found"] == 3

    def test_search_case_sensitive(self, tmp_path: Path) -> None:
        """Test case-sensitive search."""
        test_file = tmp_path / "text.txt"
        test_file.write_text("Hello\nhello\nHELLO\n")

        result = search(pattern="hello", path=str(tmp_path), case_sensitive=True)

        assert result.is_success
        assert result.metadata["matches_found"] == 1
        assert result.data[0]["content"] == "hello"

    def test_search_with_file_pattern(self, tmp_path: Path) -> None:
        """Test searching with file pattern filter."""
        # Create test files
        (tmp_path / "test.py").write_text("import os\n")
        (tmp_path / "test.txt").write_text("import os\n")
        (tmp_path / "main.py").write_text("import sys\n")

        result = search(
            pattern="import", path=str(tmp_path), file_pattern="*.py"
        )

        assert result.is_success
        assert result.metadata["matches_found"] == 2
        assert result.metadata["files_searched"] == 2
        # Only .py files should be searched
        for match in result.data:
            assert match["file"].endswith(".py")

    def test_search_multiple_file_patterns(self, tmp_path: Path) -> None:
        """Test searching with specific file pattern."""
        # Create test files
        (tmp_path / "test_foo.py").write_text("test\n")
        (tmp_path / "test_bar.py").write_text("test\n")
        (tmp_path / "main.py").write_text("test\n")

        result = search(
            pattern="test", path=str(tmp_path), file_pattern="test_*.py"
        )

        assert result.is_success
        assert result.metadata["matches_found"] == 2

    def test_search_single_file(self, tmp_path: Path) -> None:
        """Test searching a single file."""
        test_file = tmp_path / "single.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        result = search(pattern="Line", path=str(test_file))

        assert result.is_success
        assert result.metadata["matches_found"] == 3
        assert result.metadata["files_searched"] == 1

    def test_search_max_results(self, tmp_path: Path) -> None:
        """Test max_results limit."""
        # Create a file with many matches
        test_file = tmp_path / "many.txt"
        content = "\n".join([f"match {i}" for i in range(200)])
        test_file.write_text(content)

        result = search(pattern="match", path=str(tmp_path), max_results=50)

        assert result.is_success
        assert len(result.data) == 50
        assert result.metadata["truncated"] is True

    def test_search_no_matches(self, tmp_path: Path) -> None:
        """Test search with no matches."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("Nothing here\n")

        result = search(pattern="something", path=str(tmp_path))

        assert result.is_success
        assert result.metadata["matches_found"] == 0
        assert len(result.data) == 0

    def test_search_path_not_found(self) -> None:
        """Test searching a non-existent path."""
        result = search(pattern="test", path="/nonexistent/path")

        assert result.is_error
        assert "does not exist" in result.error_message

    def test_search_invalid_regex(self, tmp_path: Path) -> None:
        """Test search with invalid regex pattern."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test\n")

        result = search(pattern="[invalid(", path=str(tmp_path))

        assert result.is_error
        assert "Invalid regex pattern" in result.error_message

    def test_search_nested_directories(self, tmp_path: Path) -> None:
        """Test searching through nested directories."""
        # Create nested structure
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "dir2").mkdir()
        (tmp_path / "file1.txt").write_text("target\n")
        (tmp_path / "dir1" / "file2.txt").write_text("target\n")
        (tmp_path / "dir1" / "dir2" / "file3.txt").write_text("target\n")

        result = search(pattern="target", path=str(tmp_path))

        assert result.is_success
        assert result.metadata["matches_found"] == 3
        assert result.metadata["files_searched"] == 3

    def test_search_skips_hidden_files(self, tmp_path: Path) -> None:
        """Test that search skips hidden files."""
        # Create regular and hidden files
        (tmp_path / "visible.txt").write_text("test\n")
        (tmp_path / ".hidden.txt").write_text("test\n")

        result = search(pattern="test", path=str(tmp_path))

        assert result.is_success
        assert result.metadata["matches_found"] == 1
        # Only visible file should be found
        assert ".hidden" not in result.data[0]["file"]

    def test_search_skips_binary_files(self, tmp_path: Path) -> None:
        """Test that search gracefully handles binary files."""
        # Create text and binary files
        (tmp_path / "text.txt").write_text("readable\n")
        (tmp_path / "binary.bin").write_bytes(b"\x00\x01\x02\xff\xfe")

        result = search(pattern="readable", path=str(tmp_path))

        # Should successfully search text file, skip binary
        assert result.is_success
        assert result.metadata["matches_found"] == 1

    def test_search_match_positions(self, tmp_path: Path) -> None:
        """Test that match positions are correctly reported."""
        test_file = tmp_path / "positions.txt"
        test_file.write_text("prefix TARGET suffix\n")

        result = search(pattern="TARGET", path=str(tmp_path))

        assert result.is_success
        assert result.data[0]["match_start"] == 7
        assert result.data[0]["match_end"] == 13

    def test_search_line_numbers(self, tmp_path: Path) -> None:
        """Test that line numbers are correctly reported."""
        test_file = tmp_path / "lines.txt"
        test_file.write_text("Line 1\nLine 2 match\nLine 3\nLine 4 match\n")

        result = search(pattern="match", path=str(tmp_path))

        assert result.is_success
        assert result.metadata["matches_found"] == 2
        assert result.data[0]["line"] == 2
        assert result.data[1]["line"] == 4

    def test_search_empty_directory(self, tmp_path: Path) -> None:
        """Test searching an empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = search(pattern="anything", path=str(empty_dir))

        assert result.is_success
        assert result.metadata["matches_found"] == 0
        assert result.metadata["files_searched"] == 0

    def test_search_permission_denied(self, tmp_path: Path) -> None:
        """Test searching a directory without read permissions."""
        no_read_dir = tmp_path / "no_read"
        no_read_dir.mkdir()
        no_read_dir.chmod(0o000)

        try:
            result = search(pattern="test", path=str(no_read_dir))
            assert result.is_error
            assert "Permission denied" in result.error_message
        finally:
            # Restore permissions for cleanup
            no_read_dir.chmod(0o755)

    def test_search_metadata_fields(self, tmp_path: Path) -> None:
        """Test that all expected metadata fields are present."""
        test_file = tmp_path / "meta.txt"
        test_file.write_text("test pattern\n")

        result = search(pattern="pattern", path=str(tmp_path))

        assert result.is_success
        assert "matches_found" in result.metadata
        assert "files_searched" in result.metadata
        assert "pattern" in result.metadata
        assert "truncated" in result.metadata
        assert result.metadata["pattern"] == "pattern"
        assert result.metadata["truncated"] is False

    def test_search_result_data_structure(self, tmp_path: Path) -> None:
        """Test that result data has correct structure."""
        test_file = tmp_path / "struct.txt"
        test_file.write_text("test line\n")

        result = search(pattern="test", path=str(tmp_path))

        assert result.is_success
        assert len(result.data) == 1

        match = result.data[0]
        assert "file" in match
        assert "line" in match
        assert "content" in match
        assert "match_start" in match
        assert "match_end" in match

        assert isinstance(match["line"], int)
        assert isinstance(match["content"], str)
        assert isinstance(match["match_start"], int)
        assert isinstance(match["match_end"], int)
