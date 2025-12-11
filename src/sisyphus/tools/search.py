"""Search tool for finding patterns in files and code.

This module provides a tool for searching file contents using patterns.
"""

import fnmatch
import os
import re
from dataclasses import dataclass
from pathlib import Path

from sisyphus.core.tool import ToolResult


@dataclass
class SearchMatch:
    """A single search match result."""

    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int


def search(
    pattern: str,
    path: str = ".",
    file_pattern: str | None = None,
    case_sensitive: bool = True,
    max_results: int = 100,
) -> ToolResult:
    """Search for patterns in files.

    Recursively searches through files in a directory tree for lines matching
    a pattern. Supports regex patterns, file filtering, and case sensitivity.

    Args:
        pattern: The search pattern (regex supported)
        path: Directory or file to search in (default: current directory)
        file_pattern: File name pattern to filter (e.g., "*.py", "test_*.py")
        case_sensitive: Whether the search is case-sensitive (default: True)
        max_results: Maximum number of results to return (default: 100)

    Returns:
        ToolResult with:
        - success: data = list of matches, metadata = {matches_found, files_searched}
        - error: error_message describing the failure

    Error cases:
        - Path does not exist
        - Permission denied
        - Invalid regex pattern
        - No matches found (not an error, returns empty list)
    """
    try:
        # Convert to Path for better handling
        search_path = Path(path).expanduser().resolve()

        # Check if path exists
        if not search_path.exists():
            return ToolResult.error(f"Path does not exist: {path}")

        # Check if path is accessible
        if not os.access(search_path, os.R_OK):
            return ToolResult.error(f"Permission denied: {path}")

        # Compile regex pattern
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            return ToolResult.error(f"Invalid regex pattern: {pattern} - {e}")

        # Collect files to search
        files_to_search: list[Path] = []

        if search_path.is_file():
            # Single file search
            if file_pattern is None or fnmatch.fnmatch(search_path.name, file_pattern):
                files_to_search.append(search_path)
        else:
            # Directory search
            for root, _, files in os.walk(search_path):
                for file_name in files:
                    # Skip hidden files and directories
                    if file_name.startswith("."):
                        continue

                    # Apply file pattern filter
                    if file_pattern and not fnmatch.fnmatch(file_name, file_pattern):
                        continue

                    file_path = Path(root) / file_name

                    # Skip files we can't read
                    if not os.access(file_path, os.R_OK):
                        continue

                    files_to_search.append(file_path)

        # Search through files
        matches: list[SearchMatch] = []
        files_searched = 0

        for file_path in files_to_search:
            # Stop if we've reached max results
            if len(matches) >= max_results:
                break

            try:
                # Try to read as text file
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        # Search for pattern in line
                        match = regex.search(line)
                        if match:
                            matches.append(
                                SearchMatch(
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    line_content=line.rstrip("\n"),
                                    match_start=match.start(),
                                    match_end=match.end(),
                                )
                            )

                            # Check if we've hit max results
                            if len(matches) >= max_results:
                                break

                files_searched += 1

            except (UnicodeDecodeError, OSError):
                # Skip binary files or files we can't read
                continue

        # Format results for output
        result_data = [
            {
                "file": match.file_path,
                "line": match.line_number,
                "content": match.line_content,
                "match_start": match.match_start,
                "match_end": match.match_end,
            }
            for match in matches
        ]

        return ToolResult.success(
            data=result_data,
            matches_found=len(matches),
            files_searched=files_searched,
            pattern=pattern,
            truncated=len(matches) >= max_results,
        )

    except Exception as e:
        return ToolResult.error(f"Unexpected error during search: {e}")
