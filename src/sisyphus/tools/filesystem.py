"""Filesystem tools for reading and writing files.

This module provides tools for file I/O operations:
- read_file: Read file contents with line range support
- write_file: Write content to files with atomic operations
"""

import os
from pathlib import Path

from sisyphus.core.tool import ToolResult


def read_file(
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
    encoding: str = "utf-8",
) -> ToolResult:
    """Read the contents of a file from the filesystem.

    Supports reading entire files or specific line ranges. Handles various
    encodings and provides clear error messages for common failure modes.

    Args:
        file_path: Absolute or relative path to the file to read
        start_line: Optional starting line number (1-indexed, inclusive)
        end_line: Optional ending line number (1-indexed, inclusive)
        encoding: File encoding (default: utf-8)

    Returns:
        ToolResult with:
        - success: data = file contents (str), metadata = {lines_read,
          total_lines, file_size}
        - error: error_message describing the failure

    Error cases:
        - File not found
        - Permission denied
        - Invalid encoding
        - Binary file with text encoding
        - Invalid line range
    """
    try:
        # Convert to Path for better handling
        path = Path(file_path).expanduser().resolve()

        # Check if file exists
        if not path.exists():
            return ToolResult.error(f"File not found: {file_path}")

        # Check if it's a file (not directory)
        if not path.is_file():
            return ToolResult.error(f"Not a file: {file_path}")

        # Check if file is readable
        if not os.access(path, os.R_OK):
            return ToolResult.error(f"Permission denied: {file_path}")

        # Get file size
        file_size = path.stat().st_size

        # Attempt to read the file
        try:
            with open(path, encoding=encoding) as f:
                lines = f.readlines()
        except UnicodeDecodeError as e:
            return ToolResult.error(
                f"Encoding error (possibly binary file): {file_path} - {e}"
            )
        except LookupError:
            return ToolResult.error(f"Invalid encoding: {encoding}")

        total_lines = len(lines)

        # Handle line range
        if start_line is not None or end_line is not None:
            # Validate line numbers (1-indexed)
            if start_line is not None and start_line < 1:
                return ToolResult.error(
                    f"Invalid start_line: {start_line} (must be >= 1)"
                )

            if end_line is not None and end_line < 1:
                return ToolResult.error(f"Invalid end_line: {end_line} (must be >= 1)")

            if (
                start_line is not None
                and end_line is not None
                and start_line > end_line
            ):
                return ToolResult.error(
                    f"Invalid range: start_line ({start_line}) > end_line ({end_line})"
                )

            # Convert to 0-indexed and slice
            start_idx = (start_line - 1) if start_line is not None else 0
            end_idx = end_line if end_line is not None else total_lines

            # Check bounds
            if start_idx >= total_lines:
                return ToolResult.error(
                    f"start_line ({start_line}) exceeds file length "
                    f"({total_lines} lines)"
                )

            selected_lines = lines[start_idx:end_idx]
            content = "".join(selected_lines)
            lines_read = len(selected_lines)
        else:
            content = "".join(lines)
            lines_read = total_lines

        return ToolResult.success(
            data=content,
            lines_read=lines_read,
            total_lines=total_lines,
            file_size=file_size,
            encoding=encoding,
        )

    except Exception as e:
        return ToolResult.error(f"Unexpected error reading {file_path}: {e}")


def write_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
    overwrite: bool = True,
) -> ToolResult:
    """Write content to a file on the filesystem.

    Supports atomic writes (via temporary file + rename), directory creation,
    and overwrite protection. Provides clear error messages for common failure modes.

    Args:
        file_path: Absolute or relative path to the file to write
        content: Content to write to the file
        encoding: File encoding (default: utf-8)
        create_dirs: Whether to create parent directories if they don't exist
        overwrite: Whether to overwrite existing files (default: True)

    Returns:
        ToolResult with:
        - success: data = None, metadata = {bytes_written, lines_written}
        - error: error_message describing the failure

    Error cases:
        - Permission denied
        - File exists and overwrite=False
        - Parent directory doesn't exist and create_dirs=False
        - Disk full / I/O error
        - Invalid encoding
    """
    try:
        # Convert to Path for better handling
        path = Path(file_path).expanduser().resolve()

        # Check if file exists and overwrite is disabled
        if path.exists() and not overwrite:
            return ToolResult.error(
                f"File already exists and overwrite=False: {file_path}"
            )

        # Create parent directories if needed
        parent_dir = path.parent
        if not parent_dir.exists():
            if create_dirs:
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    return ToolResult.error(
                        f"Failed to create parent directory {parent_dir}: {e}"
                    )
            else:
                return ToolResult.error(
                    f"Parent directory does not exist and "
                    f"create_dirs=False: {parent_dir}"
                )

        # Check if we can write to the directory
        if not os.access(parent_dir, os.W_OK):
            return ToolResult.error(f"Permission denied (directory): {parent_dir}")

        # If file exists, check if we can write to it
        if path.exists() and not os.access(path, os.W_OK):
            return ToolResult.error(f"Permission denied: {file_path}")

        # Perform atomic write using temporary file
        temp_path = path.with_suffix(path.suffix + ".tmp")

        try:
            # Write to temporary file
            with open(temp_path, "w", encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk

            # Atomically rename temp file to target file
            temp_path.replace(path)

        except OSError as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            return ToolResult.error(f"I/O error writing to {file_path}: {e}")

        except LookupError:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            return ToolResult.error(f"Invalid encoding: {encoding}")

        # Get file statistics
        file_size = path.stat().st_size
        line_count = content.count("\n")
        if content and not content.endswith("\n"):
            line_count += 1  # Count last line even if no trailing newline

        return ToolResult.success(
            data=None,
            bytes_written=file_size,
            lines_written=line_count,
            encoding=encoding,
        )

    except Exception as e:
        return ToolResult.error(f"Unexpected error writing to {file_path}: {e}")
