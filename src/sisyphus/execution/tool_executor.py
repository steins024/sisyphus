"""Tool execution engine with validation, timeout, and error handling.

This module provides the ToolExecutor class that bridges tool definitions
with actual execution, handling parameter validation, timeouts, cancellation,
and standardized error handling.
"""

import asyncio
import inspect
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from contextlib import contextmanager
from typing import Any

from jsonschema import ValidationError, validate

from sisyphus.core.tool import (
    AsyncTool,
    Tool,
    ToolExecutionError,
    ToolResult,
    ToolTimeoutError,
    ToolValidationError,
)


class ToolExecutor:
    """Execute tools with validation, timeout, and error handling.

    The ToolExecutor provides a safe execution environment for tools with:
    - JSON Schema parameter validation
    - Configurable timeouts for sync and async execution
    - Exception handling and conversion to ToolResult
    - Execution metadata (timing, resource usage)
    - Support for both Tool and AsyncTool protocols

    Usage:
        executor = ToolExecutor()
        result = executor.execute(tool, param1="value1", param2="value2")

    Thread-safety: Each execution is isolated, but executor instance
    should not be shared across threads without synchronization.
    """

    def __init__(
        self,
        *,
        default_timeout: float = 60.0,
        max_workers: int = 4,
    ) -> None:
        """Initialize the tool executor.

        Args:
            default_timeout: Default timeout in seconds for tool execution
            max_workers: Maximum worker threads for sync tool execution
        """
        self.default_timeout = default_timeout
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    def execute(
        self,
        tool: Tool | AsyncTool,
        *,
        timeout: float | None = None,
        validate_params: bool = True,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a tool synchronously.

        This is a synchronous wrapper that handles both sync and async tools.
        For async tools, it will run them in a new event loop.

        Args:
            tool: The tool instance to execute
            timeout: Optional timeout in seconds (overrides default)
            validate_params: Whether to validate parameters (default: True)
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution status and data

        Raises:
            ToolValidationError: If parameter validation fails
            ToolTimeoutError: If execution exceeds timeout
            ToolExecutionError: If execution fails
        """
        # Determine if tool is async
        is_async = self._is_async_tool(tool)

        if is_async:
            # Run async tool in event loop
            return asyncio.run(
                self.execute_async(
                    tool,  # type: ignore[arg-type]
                    timeout=timeout,
                    validate_params=validate_params,
                    **kwargs,
                )
            )
        else:
            return self._execute_sync(
                tool,  # type: ignore[arg-type]
                timeout=timeout,
                validate_params=validate_params,
                **kwargs,
            )

    async def execute_async(
        self,
        tool: AsyncTool,
        *,
        timeout: float | None = None,
        validate_params: bool = True,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute an async tool.

        Args:
            tool: The async tool instance to execute
            timeout: Optional timeout in seconds (overrides default)
            validate_params: Whether to validate parameters (default: True)
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution status and data

        Raises:
            ToolValidationError: If parameter validation fails
            ToolTimeoutError: If execution exceeds timeout
            ToolExecutionError: If execution fails
        """
        start_time = time.time()
        effective_timeout = timeout if timeout is not None else self.default_timeout

        try:
            # Validate parameters
            if validate_params:
                self._validate_parameters(tool, kwargs)

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    tool.execute_async(**kwargs),
                    timeout=effective_timeout,
                )
            except TimeoutError as e:
                execution_time = time.time() - start_time
                raise ToolTimeoutError(
                    f"Tool '{tool.name}' execution exceeded timeout of "
                    f"{effective_timeout}s (ran for {execution_time:.2f}s)",
                    tool_name=tool.name,
                ) from e

            # Add execution metadata
            execution_time = time.time() - start_time
            # Check if result is ToolResult and add metadata
            if isinstance(result, ToolResult):  # type: ignore[misc]
                result.metadata["execution_time"] = execution_time
                result.metadata["tool_name"] = tool.name
                return result
            else:
                # Wrap non-ToolResult returns (for compatibility)
                return ToolResult.success(
                    data=result,
                    execution_time=execution_time,
                    tool_name=tool.name,
                )

        except ToolValidationError:
            raise
        except ToolTimeoutError:
            raise
        except ToolExecutionError:
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult.error(
                error=f"Tool '{tool.name}' execution failed: {type(e).__name__}: {e}",
                execution_time=execution_time,
                tool_name=tool.name,
                exception_type=type(e).__name__,
            )

    def _execute_sync(
        self,
        tool: Tool,
        *,
        timeout: float | None = None,
        validate_params: bool = True,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a synchronous tool with timeout.

        Args:
            tool: The tool instance to execute
            timeout: Optional timeout in seconds (overrides default)
            validate_params: Whether to validate parameters (default: True)
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution status and data
        """
        start_time = time.time()
        effective_timeout = timeout if timeout is not None else self.default_timeout

        try:
            # Validate parameters
            if validate_params:
                self._validate_parameters(tool, kwargs)

            # Execute with timeout using thread pool
            future = self._thread_pool.submit(tool.execute, **kwargs)

            try:
                result = future.result(timeout=effective_timeout)
            except FuturesTimeoutError as e:
                future.cancel()
                execution_time = time.time() - start_time
                raise ToolTimeoutError(
                    f"Tool '{tool.name}' execution exceeded timeout of "
                    f"{effective_timeout}s (ran for {execution_time:.2f}s)",
                    tool_name=tool.name,
                ) from e

            # Add execution metadata
            execution_time = time.time() - start_time
            # Check if result is ToolResult and add metadata
            if isinstance(result, ToolResult):  # type: ignore[misc]
                result.metadata["execution_time"] = execution_time
                result.metadata["tool_name"] = tool.name
                return result
            else:
                # Wrap non-ToolResult returns (for compatibility)
                return ToolResult.success(
                    data=result,
                    execution_time=execution_time,
                    tool_name=tool.name,
                )

        except ToolValidationError:
            raise
        except ToolTimeoutError:
            raise
        except ToolExecutionError:
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult.error(
                error=f"Tool '{tool.name}' execution failed: {type(e).__name__}: {e}",
                execution_time=execution_time,
                tool_name=tool.name,
                exception_type=type(e).__name__,
            )

    def _validate_parameters(
        self,
        tool: Tool | AsyncTool,
        params: dict[str, Any],
    ) -> None:
        """Validate tool parameters against JSON Schema.

        Args:
            tool: The tool instance
            params: Parameters to validate

        Raises:
            ToolValidationError: If validation fails
        """
        try:
            # Get the JSON Schema from the tool
            schema = tool.parameters

            # Validate against schema
            validate(instance=params, schema=schema)

        except ValidationError as e:
            # Convert jsonschema ValidationError to ToolValidationError
            error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            raise ToolValidationError(
                f"Parameter validation failed for tool '{tool.name}' at {error_path}: "
                f"{e.message}",
                tool_name=tool.name,
            ) from e
        except Exception as e:
            raise ToolValidationError(
                f"Parameter validation failed for tool '{tool.name}': {e}",
                tool_name=tool.name,
            ) from e

    def _is_async_tool(self, tool: Tool | AsyncTool) -> bool:
        """Check if a tool is async.

        Args:
            tool: The tool instance

        Returns:
            True if tool has execute_async method, False otherwise
        """
        if not hasattr(tool, "execute_async"):
            return False
        execute_async_method = tool.execute_async  # type: ignore[union-attr]
        return inspect.iscoroutinefunction(execute_async_method)  # type: ignore[arg-type]

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources.

        This should be called when done with the executor to cleanup
        the thread pool.
        """
        self._thread_pool.shutdown(wait=True)

    def __enter__(self) -> "ToolExecutor":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - cleanup resources."""
        self.shutdown()


@contextmanager
def timeout_context(seconds: float):
    """Context manager for timeout using signals (Unix only).

    This is an alternative timeout mechanism for sync functions.
    Note: Only works on Unix systems, not Windows.

    Args:
        seconds: Timeout in seconds

    Raises:
        TimeoutError: If execution exceeds timeout

    Example:
        with timeout_context(5.0):
            # Code that should timeout after 5 seconds
            slow_function()
    """

    def timeout_handler(signum: int, frame: Any) -> None:
        raise TimeoutError("Execution timed out")

    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))

    try:
        yield
    finally:
        # Restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
