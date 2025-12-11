"""Terminal tool for executing shell commands.

This module provides a tool for running shell commands safely with
timeout support and output capture.
"""

import asyncio
import os
import shlex
from pathlib import Path

from sisyphus.core.tool import ToolResult


async def terminal(
    command: str,
    working_dir: str | None = None,
    timeout: float = 30.0,
    shell: bool = False,
) -> ToolResult:
    """Execute a shell command asynchronously.

    Runs a shell command with timeout support, output capture, and
    configurable working directory. Provides both stdout and stderr
    in the result.

    Args:
        command: The shell command to execute
        working_dir: Working directory for the command (default: current directory)
        timeout: Command timeout in seconds (default: 30.0)
        shell: Whether to execute through shell (default: False for safety)

    Returns:
        ToolResult with:
        - success: data = {stdout, stderr, returncode}, metadata = {command, duration}
        - error: error_message describing the failure

    Error cases:
        - Working directory does not exist
        - Command times out
        - Command fails with non-zero exit code
        - Permission denied
        - Command not found

    Security considerations:
        - By default, shell=False to prevent command injection
        - Commands are not executed through the shell unless explicitly requested
        - Working directory is validated before execution
    """
    import time

    start_time = time.time()

    try:
        # Validate and resolve working directory
        if working_dir:
            work_path = Path(working_dir).expanduser().resolve()
            if not work_path.exists():
                return ToolResult.error(
                    f"Working directory does not exist: {working_dir}"
                )
            if not work_path.is_dir():
                return ToolResult.error(
                    f"Working directory is not a directory: {working_dir}"
                )
            cwd = str(work_path)
        else:
            cwd = None

        # Prepare command for execution
        if shell:
            # Execute through shell (less safe, but more flexible)
            cmd = command
        else:
            # Parse command into arguments (safer)
            try:
                cmd = shlex.split(command)
            except ValueError as e:
                return ToolResult.error(f"Invalid command syntax: {e}")

        # Execute the command
        process = None
        try:
            if shell:
                process = await asyncio.create_subprocess_shell(
                    command,  # Use original command string for shell
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd,  # cmd is already a list here
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )

            # Wait for completion with timeout
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            # Decode output
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            returncode = process.returncode

            duration = time.time() - start_time

            # Check if command succeeded
            if returncode == 0:
                return ToolResult.success(
                    data={
                        "stdout": stdout,
                        "stderr": stderr,
                        "returncode": returncode,
                    },
                    command=command,
                    duration=duration,
                    working_dir=cwd or os.getcwd(),
                )
            else:
                # Non-zero exit code
                return ToolResult.error(
                    f"Command failed with exit code {returncode}\n"
                    f"stdout: {stdout}\n"
                    f"stderr: {stderr}",
                    command=command,
                    duration=duration,
                    returncode=returncode,
                )

        except TimeoutError:
            # Kill the process on timeout
            if process:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

            return ToolResult.timeout(
                f"Command timed out after {timeout} seconds",
                command=command,
                timeout=timeout,
            )

        except FileNotFoundError:
            # Extract command name from the parsed list
            cmd_name = cmd[0] if isinstance(cmd, list) else command.split()[0]
            return ToolResult.error(
                f"Command not found: {cmd_name}",
                command=command,
            )

        except PermissionError:
            return ToolResult.error(
                f"Permission denied executing command: {command}",
                command=command,
            )

    except Exception as e:
        duration = time.time() - start_time
        return ToolResult.error(
            f"Unexpected error executing command: {e}",
            command=command,
            duration=duration,
        )
