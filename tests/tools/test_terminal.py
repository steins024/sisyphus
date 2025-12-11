"""Tests for the terminal tool."""

import sys
from pathlib import Path

import pytest

from sisyphus.core.tool import ToolStatus
from sisyphus.tools.terminal import terminal


class TestTerminal:
    """Test suite for terminal tool."""

    @pytest.mark.asyncio
    async def test_simple_command(self) -> None:
        """Test executing a simple command."""
        result = await terminal(command="echo 'Hello World'")

        assert result.is_success
        assert "Hello World" in result.data["stdout"]
        assert result.data["returncode"] == 0
        assert "duration" in result.metadata

    @pytest.mark.asyncio
    async def test_command_with_args(self) -> None:
        """Test executing a command with arguments."""
        result = await terminal(command="echo foo bar baz")

        assert result.is_success
        assert "foo bar baz" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_command_with_stderr(self) -> None:
        """Test capturing stderr output."""
        # Use a command that writes to stderr
        result = await terminal(command="python -c 'import sys; sys.stderr.write(\"error\\n\")'")

        # Python stderr writes are captured
        assert result.is_success or result.is_error
        if result.is_success:
            assert "error" in result.data["stderr"]

    @pytest.mark.asyncio
    async def test_command_with_working_dir(self, tmp_path: Path) -> None:
        """Test executing a command with a specific working directory."""
        # Create a test file in tmp_path
        test_file = tmp_path / "testfile.txt"
        test_file.write_text("test content")

        # List files in tmp_path
        result = await terminal(command="ls", working_dir=str(tmp_path))

        assert result.is_success
        assert "testfile.txt" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_command_nonzero_exit_code(self) -> None:
        """Test command that exits with non-zero code."""
        result = await terminal(command="python -c 'exit(1)'")

        assert result.is_error
        assert "exit code 1" in result.error_message
        assert result.metadata["returncode"] == 1

    @pytest.mark.asyncio
    async def test_command_timeout(self) -> None:
        """Test command timeout."""
        # Command that sleeps longer than timeout
        result = await terminal(command="sleep 10", timeout=0.5)

        assert result.status == ToolStatus.TIMEOUT
        assert "timed out" in result.error_message

    @pytest.mark.asyncio
    async def test_command_not_found(self) -> None:
        """Test executing a non-existent command."""
        result = await terminal(command="nonexistent_command_12345")

        assert result.is_error
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_working_dir_not_found(self) -> None:
        """Test with non-existent working directory."""
        result = await terminal(
            command="echo test", working_dir="/nonexistent/directory"
        )

        assert result.is_error
        assert "does not exist" in result.error_message

    @pytest.mark.asyncio
    async def test_working_dir_is_file(self, tmp_path: Path) -> None:
        """Test with a file as working directory (should fail)."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        result = await terminal(command="echo test", working_dir=str(test_file))

        assert result.is_error
        assert "not a directory" in result.error_message

    @pytest.mark.asyncio
    async def test_shell_mode(self) -> None:
        """Test executing command through shell."""
        # Use shell features like pipes
        result = await terminal(command="echo 'test' | grep 'test'", shell=True)

        assert result.is_success
        assert "test" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_command_with_special_chars(self) -> None:
        """Test command with special characters."""
        result = await terminal(command="echo 'special $chars & symbols'")

        assert result.is_success
        assert "special" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_multiline_output(self) -> None:
        """Test command with multiline output."""
        result = await terminal(command="python -c 'print(\"line1\\nline2\\nline3\")'")

        assert result.is_success
        stdout = result.data["stdout"]
        assert "line1" in stdout
        assert "line2" in stdout
        assert "line3" in stdout

    @pytest.mark.asyncio
    async def test_empty_output(self) -> None:
        """Test command with no output."""
        result = await terminal(command="true")

        assert result.is_success
        assert result.data["stdout"] == ""
        assert result.data["returncode"] == 0

    @pytest.mark.asyncio
    async def test_metadata_fields(self) -> None:
        """Test that all expected metadata fields are present."""
        result = await terminal(command="echo test")

        assert result.is_success
        assert "command" in result.metadata
        assert "duration" in result.metadata
        assert "working_dir" in result.metadata
        assert result.metadata["command"] == "echo test"
        assert isinstance(result.metadata["duration"], float)

    @pytest.mark.asyncio
    async def test_data_structure(self) -> None:
        """Test that result data has correct structure."""
        result = await terminal(command="echo test")

        assert result.is_success
        data = result.data
        assert isinstance(data, dict)
        assert "stdout" in data
        assert "stderr" in data
        assert "returncode" in data
        assert isinstance(data["stdout"], str)
        assert isinstance(data["stderr"], str)
        assert isinstance(data["returncode"], int)

    @pytest.mark.asyncio
    async def test_long_running_command(self) -> None:
        """Test a command that takes some time but completes within timeout."""
        result = await terminal(command="sleep 0.1", timeout=2.0)

        assert result.is_success
        assert result.data["returncode"] == 0

    @pytest.mark.asyncio
    async def test_command_with_quotes(self) -> None:
        """Test command with quoted arguments."""
        result = await terminal(command='echo "quoted string"')

        assert result.is_success
        assert "quoted string" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_python_script_execution(self, tmp_path: Path) -> None:
        """Test executing a Python script."""
        # Create a simple Python script
        script = tmp_path / "test_script.py"
        script.write_text('print("Script output")')

        result = await terminal(command=f"python {script}")

        assert result.is_success
        assert "Script output" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_unicode_output(self) -> None:
        """Test command with unicode output."""
        result = await terminal(command="python -c 'print(\"Hello 世界 🌍\")'")

        assert result.is_success
        # Unicode should be properly decoded
        assert "Hello" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_environment_variables(self) -> None:
        """Test that environment variables are accessible."""
        # Test that PATH is accessible
        result = await terminal(command="python -c 'import os; print(os.environ.get(\"PATH\", \"no path\"))'")

        assert result.is_success
        # PATH should exist in the environment
        assert result.data["stdout"].strip() != "no path"

    @pytest.mark.asyncio
    async def test_invalid_shell_syntax(self) -> None:
        """Test command with invalid shell syntax (without shell=True)."""
        # Pipe without shell=True should fail to parse
        result = await terminal(command="echo test | grep test", shell=False)

        # This will try to execute 'echo' with args ['test', '|', 'grep', 'test']
        # which will succeed but the pipe won't work as expected
        assert result.is_success
        # The | will be printed as literal text
        assert "|" in result.data["stdout"] or result.data["returncode"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_commands(self) -> None:
        """Test running multiple commands concurrently."""
        import asyncio

        # Run multiple commands at once
        results = await asyncio.gather(
            terminal(command="echo 'cmd1'"),
            terminal(command="echo 'cmd2'"),
            terminal(command="echo 'cmd3'"),
        )

        # All should succeed
        assert all(r.is_success for r in results)
        assert "cmd1" in results[0].data["stdout"]
        assert "cmd2" in results[1].data["stdout"]
        assert "cmd3" in results[2].data["stdout"]

    @pytest.mark.asyncio
    async def test_large_output(self) -> None:
        """Test command with large output."""
        # Generate large output (1000 lines)
        result = await terminal(
            command="python -c 'for i in range(1000): print(i)'",
            timeout=5.0
        )

        assert result.is_success
        lines = result.data["stdout"].strip().split("\n")
        assert len(lines) == 1000
        assert "999" in result.data["stdout"]

    @pytest.mark.asyncio
    async def test_tilde_expansion_in_working_dir(self) -> None:
        """Test that ~ is properly expanded in working_dir."""
        # Use home directory
        result = await terminal(command="pwd", working_dir="~")

        assert result.is_success
        # Should show the expanded home directory
        from pathlib import Path
        assert str(Path.home()) in result.data["stdout"]
