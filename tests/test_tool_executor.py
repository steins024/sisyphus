"""Tests for the tool executor."""


import asyncio
import time
from typing import Any

import pytest

from sisyphus.core.tool import (
    ToolResult,
    ToolTimeoutError,
    ToolValidationError,
)
from sisyphus.execution import ToolExecutor

# ============================================================================
# Test Fixtures - Mock Tools
# ============================================================================


class SimpleTool:
    """A simple synchronous tool for testing."""

    @property
    def name(self) -> str:
        return "simple_tool"

    @property
    def description(self) -> str:
        return "A simple test tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        message = kwargs.get("message", "")
        return ToolResult.success(data=f"Echo: {message}")


class SlowTool:
    """A tool that sleeps to test timeout."""

    @property
    def name(self) -> str:
        return "slow_tool"

    @property
    def description(self) -> str:
        return "A slow tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        sleep_time = kwargs.get("sleep_time", 5.0)
        time.sleep(sleep_time)
        return ToolResult.success(data="completed")


class ErrorTool:
    """A tool that always raises an exception."""

    @property
    def name(self) -> str:
        return "error_tool"

    @property
    def description(self) -> str:
        return "A tool that errors"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **_kwargs: Any) -> ToolResult:
        raise ValueError("This tool always fails")


class AsyncEchoTool:
    """An async tool for testing."""

    @property
    def name(self) -> str:
        return "async_echo"

    @property
    def description(self) -> str:
        return "Async echo tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        }

    async def execute_async(self, **kwargs: Any) -> ToolResult:
        message = kwargs.get("message", "")
        # Simulate some async work
        await asyncio.sleep(0.1)
        return ToolResult.success(data=f"Async echo: {message}")


class AsyncSlowTool:
    """An async tool that sleeps to test timeout."""

    @property
    def name(self) -> str:
        return "async_slow_tool"

    @property
    def description(self) -> str:
        return "A slow async tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute_async(self, **kwargs: Any) -> ToolResult:
        sleep_time = kwargs.get("sleep_time", 5.0)
        await asyncio.sleep(sleep_time)
        return ToolResult.success(data="completed")


class RawReturnTool:
    """A tool that returns raw data instead of ToolResult."""

    @property
    def name(self) -> str:
        return "raw_return_tool"

    @property
    def description(self) -> str:
        return "Returns raw data"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **_kwargs: Any) -> str:
        return "raw data"  # type: ignore[return-value]


# ============================================================================
# Test ToolExecutor - Basic Execution
# ============================================================================


class TestBasicExecution:
    """Tests for basic tool execution."""

    def test_execute_simple_tool(self) -> None:
        """Test executing a simple synchronous tool."""
        executor = ToolExecutor()
        tool = SimpleTool()

        result = executor.execute(tool, message="Hello, World!")

        assert result.is_success
        assert result.data == "Echo: Hello, World!"
        assert "execution_time" in result.metadata
        assert result.metadata["tool_name"] == "simple_tool"

    def test_execute_with_context_manager(self) -> None:
        """Test executor as context manager."""
        tool = SimpleTool()

        with ToolExecutor() as executor:
            result = executor.execute(tool, message="Test")

        assert result.is_success
        assert result.data == "Echo: Test"

    def test_execute_raw_return_tool(self) -> None:
        """Test tool that returns raw data gets wrapped in ToolResult."""
        executor = ToolExecutor()
        tool = RawReturnTool()

        result = executor.execute(tool)

        assert result.is_success
        assert result.data == "raw data"
        assert "execution_time" in result.metadata

    @pytest.mark.asyncio
    async def test_execute_async_tool(self) -> None:
        """Test executing an async tool."""
        executor = ToolExecutor()
        tool = AsyncEchoTool()

        result = await executor.execute_async(tool, message="Async test")

        assert result.is_success
        assert result.data == "Async echo: Async test"
        assert "execution_time" in result.metadata

    def test_execute_async_tool_sync_wrapper(self) -> None:
        """Test executing async tool via synchronous execute method."""
        executor = ToolExecutor()
        tool = AsyncEchoTool()

        result = executor.execute(tool, message="Sync wrapper")

        assert result.is_success
        assert result.data == "Async echo: Sync wrapper"


# ============================================================================
# Test Parameter Validation
# ============================================================================


class TestParameterValidation:
    """Tests for parameter validation."""

    def test_valid_parameters(self) -> None:
        """Test execution with valid parameters."""
        executor = ToolExecutor()
        tool = SimpleTool()

        result = executor.execute(tool, message="Valid")

        assert result.is_success

    def test_missing_required_parameter(self) -> None:
        """Test that missing required parameter raises validation error."""
        executor = ToolExecutor()
        tool = SimpleTool()

        with pytest.raises(ToolValidationError, match="required"):
            executor.execute(tool)  # Missing 'message' parameter

    def test_wrong_parameter_type(self) -> None:
        """Test that wrong parameter type raises validation error."""
        executor = ToolExecutor()
        tool = SimpleTool()

        with pytest.raises(ToolValidationError):
            executor.execute(tool, message=123)  # Should be string, not int

    def test_validation_disabled(self) -> None:
        """Test that validation can be disabled."""
        executor = ToolExecutor()
        tool = SimpleTool()

        # This would normally fail validation, but we disable it
        result = executor.execute(tool, validate_params=False, wrong_param=123)

        # Tool may handle it differently, but no validation error is raised
        assert isinstance(result, ToolResult)

    @pytest.mark.asyncio
    async def test_async_validation(self) -> None:
        """Test parameter validation for async tools."""
        executor = ToolExecutor()
        tool = AsyncEchoTool()

        with pytest.raises(ToolValidationError):
            await executor.execute_async(tool)  # Missing required parameter


# ============================================================================
# Test Timeout Handling
# ============================================================================


class TestTimeoutHandling:
    """Tests for timeout handling."""

    def test_sync_tool_timeout(self) -> None:
        """Test that slow synchronous tool times out."""
        executor = ToolExecutor(default_timeout=1.0)
        tool = SlowTool()

        with pytest.raises(ToolTimeoutError, match="exceeded timeout"):
            executor.execute(tool, sleep_time=5.0)

    def test_custom_timeout(self) -> None:
        """Test execution with custom timeout."""
        executor = ToolExecutor(default_timeout=10.0)
        tool = SlowTool()

        # Should timeout with custom 0.5s timeout
        with pytest.raises(ToolTimeoutError):
            executor.execute(tool, timeout=0.5, sleep_time=2.0)

    @pytest.mark.asyncio
    async def test_async_tool_timeout(self) -> None:
        """Test that slow async tool times out."""
        executor = ToolExecutor(default_timeout=1.0)
        tool = AsyncSlowTool()

        with pytest.raises(ToolTimeoutError, match="exceeded timeout"):
            await executor.execute_async(tool, sleep_time=5.0)

    def test_fast_tool_no_timeout(self) -> None:
        """Test that fast tool doesn't timeout."""
        executor = ToolExecutor(default_timeout=5.0)
        tool = SlowTool()

        result = executor.execute(tool, sleep_time=0.1)

        assert result.is_success


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_tool_exception_converted_to_result(self) -> None:
        """Test that tool exceptions are converted to error results."""
        executor = ToolExecutor()
        tool = ErrorTool()

        result = executor.execute(tool)

        assert result.is_error
        assert "ValueError" in result.error_message
        assert "This tool always fails" in result.error_message
        assert result.metadata["exception_type"] == "ValueError"

    def test_execution_metadata_on_error(self) -> None:
        """Test that execution metadata is included on errors."""
        executor = ToolExecutor()
        tool = ErrorTool()

        result = executor.execute(tool)

        assert "execution_time" in result.metadata
        assert "tool_name" in result.metadata
        assert result.metadata["tool_name"] == "error_tool"


# ============================================================================
# Test Execution Metadata
# ============================================================================


class TestExecutionMetadata:
    """Tests for execution metadata."""

    def test_execution_time_recorded(self) -> None:
        """Test that execution time is recorded."""
        executor = ToolExecutor()
        tool = SimpleTool()

        result = executor.execute(tool, message="Test")

        assert "execution_time" in result.metadata
        assert isinstance(result.metadata["execution_time"], float)
        assert result.metadata["execution_time"] > 0

    def test_tool_name_in_metadata(self) -> None:
        """Test that tool name is included in metadata."""
        executor = ToolExecutor()
        tool = SimpleTool()

        result = executor.execute(tool, message="Test")

        assert result.metadata["tool_name"] == "simple_tool"

    @pytest.mark.asyncio
    async def test_async_metadata(self) -> None:
        """Test metadata for async tool execution."""
        executor = ToolExecutor()
        tool = AsyncEchoTool()

        result = await executor.execute_async(tool, message="Test")

        assert "execution_time" in result.metadata
        assert "tool_name" in result.metadata
        assert result.metadata["tool_name"] == "async_echo"


# ============================================================================
# Test Tool Type Detection
# ============================================================================


class TestToolTypeDetection:
    """Tests for detecting sync vs async tools."""

    def test_detect_sync_tool(self) -> None:
        """Test detection of synchronous tools."""
        executor = ToolExecutor()
        tool = SimpleTool()

        # Should detect as sync and execute properly
        result = executor.execute(tool, message="Test")

        assert result.is_success

    def test_detect_async_tool(self) -> None:
        """Test detection of async tools."""
        executor = ToolExecutor()
        tool = AsyncEchoTool()

        # Should detect as async and run in event loop
        result = executor.execute(tool, message="Test")

        assert result.is_success


# ============================================================================
# Test Executor Configuration
# ============================================================================


class TestExecutorConfiguration:
    """Tests for executor configuration."""

    def test_custom_default_timeout(self) -> None:
        """Test executor with custom default timeout."""
        executor = ToolExecutor(default_timeout=2.0)
        tool = SlowTool()

        # Should timeout after 2 seconds
        with pytest.raises(ToolTimeoutError):
            executor.execute(tool, sleep_time=5.0)

    def test_custom_max_workers(self) -> None:
        """Test executor with custom max workers."""
        executor = ToolExecutor(max_workers=2)

        # Should be able to execute multiple tools
        tool = SimpleTool()
        result1 = executor.execute(tool, message="Test 1")
        result2 = executor.execute(tool, message="Test 2")

        assert result1.is_success
        assert result2.is_success

    def test_executor_shutdown(self) -> None:
        """Test that executor can be shutdown cleanly."""
        executor = ToolExecutor()
        tool = SimpleTool()

        executor.execute(tool, message="Test")
        executor.shutdown()

        # After shutdown, executor should still exist
        # (but thread pool is cleaned up)
        assert executor is not None
