"""Tests for the tool protocol and type definitions."""

from typing import Any

import pytest

from sisyphus.core.tool import (
    AsyncTool,
    Tool,
    ToolDefinition,
    ToolExecutionError,
    ToolNotFoundError,
    ToolRegistrationError,
    ToolResult,
    ToolStatus,
    ToolTimeoutError,
    ToolValidationError,
)

# ============================================================================
# Test ToolResult
# ============================================================================


class TestToolResult:
    """Tests for ToolResult."""

    def test_success_result(self) -> None:
        """Test creating a success result."""
        result = ToolResult.success(data={"key": "value"}, duration=1.5)
        assert result.status == ToolStatus.SUCCESS
        assert result.data == {"key": "value"}
        assert result.error_message is None
        assert result.metadata == {"duration": 1.5}
        assert result.is_success
        assert not result.is_error

    def test_error_result(self) -> None:
        """Test creating an error result."""
        result = ToolResult.error(error="Something went wrong", code="E001")
        assert result.status == ToolStatus.ERROR
        assert result.data is None
        assert result.error_message == "Something went wrong"
        assert result.metadata == {"code": "E001"}
        assert not result.is_success
        assert result.is_error

    def test_timeout_result(self) -> None:
        """Test creating a timeout result."""
        result = ToolResult.timeout(error="Execution timed out", timeout=30.0)
        assert result.status == ToolStatus.TIMEOUT
        assert result.error_message == "Execution timed out"
        assert result.metadata == {"timeout": 30.0}

    def test_cancelled_result(self) -> None:
        """Test creating a cancelled result."""
        result = ToolResult.cancelled(error="User cancelled", reason="manual")
        assert result.status == ToolStatus.CANCELLED
        assert result.error_message == "User cancelled"
        assert result.metadata == {"reason": "manual"}

    def test_result_with_none_data(self) -> None:
        """Test that None data is allowed."""
        result = ToolResult.success(data=None)
        assert result.status == ToolStatus.SUCCESS
        assert result.data is None

    def test_result_with_complex_data(self) -> None:
        """Test result with complex data types."""
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2),
        }
        result = ToolResult.success(data=complex_data)
        assert result.data == complex_data

    def test_result_metadata_default_empty(self) -> None:
        """Test that metadata defaults to empty dict."""
        result = ToolResult(status=ToolStatus.SUCCESS)
        assert result.metadata == {}


# ============================================================================
# Test Tool Exceptions
# ============================================================================


class TestToolExceptions:
    """Tests for tool exception hierarchy."""

    def test_base_exception(self) -> None:
        """Test ToolExecutionError base exception."""
        error = ToolExecutionError("Test error", tool_name="test_tool")
        assert str(error) == "Test error"
        assert error.tool_name == "test_tool"

    def test_base_exception_without_tool_name(self) -> None:
        """Test ToolExecutionError without tool name."""
        error = ToolExecutionError("Test error")
        assert str(error) == "Test error"
        assert error.tool_name is None

    def test_validation_error_inheritance(self) -> None:
        """Test that ToolValidationError inherits from ToolExecutionError."""
        assert issubclass(ToolValidationError, ToolExecutionError)
        error = ToolValidationError("Invalid params", tool_name="test_tool")
        assert isinstance(error, ToolExecutionError)

    def test_timeout_error_inheritance(self) -> None:
        """Test that ToolTimeoutError inherits from ToolExecutionError."""
        assert issubclass(ToolTimeoutError, ToolExecutionError)
        error = ToolTimeoutError("Timeout", tool_name="test_tool")
        assert isinstance(error, ToolExecutionError)

    def test_not_found_error_inheritance(self) -> None:
        """Test that ToolNotFoundError inherits from ToolExecutionError."""
        assert issubclass(ToolNotFoundError, ToolExecutionError)
        error = ToolNotFoundError("Not found", tool_name="test_tool")
        assert isinstance(error, ToolExecutionError)

    def test_registration_error_inheritance(self) -> None:
        """Test that ToolRegistrationError inherits from ToolExecutionError."""
        assert issubclass(ToolRegistrationError, ToolExecutionError)
        error = ToolRegistrationError("Registration failed", tool_name="test_tool")
        assert isinstance(error, ToolExecutionError)


# ============================================================================
# Test ToolDefinition
# ============================================================================


class TestToolDefinition:
    """Tests for ToolDefinition pydantic model."""

    def test_valid_definition(self) -> None:
        """Test creating a valid tool definition."""
        definition = ToolDefinition(
            name="read_file",
            description="Read a file from the filesystem",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"}
                },
                "required": ["file_path"],
            },
            handler="sisyphus.tools.filesystem.read_file",
        )
        assert definition.name == "read_file"
        assert definition.description == "Read a file from the filesystem"
        assert definition.handler == "sisyphus.tools.filesystem.read_file"
        assert not definition.async_handler
        assert definition.timeout is None
        assert definition.metadata == {}

    def test_definition_with_timeout(self) -> None:
        """Test tool definition with timeout."""
        definition = ToolDefinition(
            name="long_task",
            description="A long running task",
            parameters={"type": "object", "properties": {}},
            handler="tools.tasks.long_task",
            timeout=60.0,
        )
        assert definition.timeout == 60.0

    def test_definition_with_async_handler(self) -> None:
        """Test tool definition with async handler."""
        definition = ToolDefinition(
            name="async_task",
            description="An async task",
            parameters={"type": "object", "properties": {}},
            handler="tools.tasks.async_task",
            **{"async": True},  # Use dict unpacking for reserved keyword
        )
        assert definition.async_handler is True

    def test_definition_with_metadata(self) -> None:
        """Test tool definition with custom metadata."""
        definition = ToolDefinition(
            name="custom_tool",
            description="A tool with metadata",
            parameters={"type": "object", "properties": {}},
            handler="tools.custom.tool",
            metadata={"version": "1.0", "author": "test"},
        )
        assert definition.metadata == {"version": "1.0", "author": "test"}

    def test_invalid_name_pattern(self) -> None:
        """Test that invalid name patterns are rejected."""
        with pytest.raises(ValueError, match="String should match pattern"):
            ToolDefinition(
                name="Read-File",  # Invalid: contains hyphen
                description="Test",
                parameters={"type": "object", "properties": {}},
                handler="tools.test",
            )

        with pytest.raises(ValueError, match="String should match pattern"):
            ToolDefinition(
                name="ReadFile",  # Invalid: starts with uppercase
                description="Test",
                parameters={"type": "object", "properties": {}},
                handler="tools.test",
            )

    def test_empty_name_rejected(self) -> None:
        """Test that empty name is rejected."""
        with pytest.raises(ValueError):
            ToolDefinition(
                name="",
                description="Test",
                parameters={"type": "object", "properties": {}},
                handler="tools.test",
            )

    def test_empty_description_rejected(self) -> None:
        """Test that empty description is rejected."""
        with pytest.raises(ValueError):
            ToolDefinition(
                name="test_tool",
                description="",
                parameters={"type": "object", "properties": {}},
                handler="tools.test",
            )

    def test_parameters_must_be_object(self) -> None:
        """Test that parameters must be object type."""
        with pytest.raises(ValueError, match="parameters type must be 'object'"):
            ToolDefinition(
                name="test_tool",
                description="Test",
                parameters={"type": "string"},  # Invalid: not object
                handler="tools.test",
            )

    def test_parameters_must_have_properties(self) -> None:
        """Test that parameters must have properties field."""
        with pytest.raises(ValueError, match="parameters must have a 'properties'"):
            ToolDefinition(
                name="test_tool",
                description="Test",
                parameters={"type": "object"},  # Missing properties
                handler="tools.test",
            )

    def test_parameters_properties_must_be_dict(self) -> None:
        """Test that parameters.properties must be a dict."""
        with pytest.raises(ValueError, match="properties must be a dict"):
            ToolDefinition(
                name="test_tool",
                description="Test",
                parameters={
                    "type": "object",
                    "properties": "invalid",  # Should be dict
                },
                handler="tools.test",
            )

    def test_invalid_handler_path(self) -> None:
        """Test that invalid handler paths are rejected."""
        with pytest.raises(ValueError, match="valid module path"):
            ToolDefinition(
                name="test_tool",
                description="Test",
                parameters={"type": "object", "properties": {}},
                handler="invalid",  # Missing dot
            )

    def test_negative_timeout_rejected(self) -> None:
        """Test that negative timeout is rejected."""
        with pytest.raises(ValueError):
            ToolDefinition(
                name="test_tool",
                description="Test",
                parameters={"type": "object", "properties": {}},
                handler="tools.test",
                timeout=-1.0,
            )

    def test_zero_timeout_rejected(self) -> None:
        """Test that zero timeout is rejected."""
        with pytest.raises(ValueError):
            ToolDefinition(
                name="test_tool",
                description="Test",
                parameters={"type": "object", "properties": {}},
                handler="tools.test",
                timeout=0.0,
            )


# ============================================================================
# Test Tool Protocol
# ============================================================================


class TestToolProtocol:
    """Tests for Tool protocol compliance."""

    def test_simple_tool_implementation(self) -> None:
        """Test that a simple tool implementation conforms to the protocol."""

        class SimpleTool:
            """A simple test tool."""

            @property
            def name(self) -> str:
                return "simple_tool"

            @property
            def description(self) -> str:
                return "A simple test tool"

            @property
            def parameters(self) -> dict[str, Any]:
                return {"type": "object", "properties": {}}

            def execute(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.success(data="executed")

        tool = SimpleTool()
        assert isinstance(tool, Tool)
        assert tool.name == "simple_tool"
        assert tool.description == "A simple test tool"
        assert tool.parameters == {"type": "object", "properties": {}}

        result = tool.execute()
        assert result.is_success
        assert result.data == "executed"

    def test_tool_with_parameters(self) -> None:
        """Test tool that uses parameters."""

        class EchoTool:
            """Tool that echoes input."""

            @property
            def name(self) -> str:
                return "echo"

            @property
            def description(self) -> str:
                return "Echo the input"

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
                return ToolResult.success(data=message)

        tool = EchoTool()
        assert isinstance(tool, Tool)

        result = tool.execute(message="Hello, World!")
        assert result.is_success
        assert result.data == "Hello, World!"

    def test_tool_with_error(self) -> None:
        """Test tool that returns errors."""

        class ErrorTool:
            """Tool that always errors."""

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
                return ToolResult.error(error="Tool failed")

        tool = ErrorTool()
        result = tool.execute()
        assert result.is_error
        assert result.error_message == "Tool failed"


# ============================================================================
# Test AsyncTool Protocol
# ============================================================================


class TestAsyncToolProtocol:
    """Tests for AsyncTool protocol compliance."""

    @pytest.mark.asyncio
    async def test_async_tool_implementation(self) -> None:
        """Test that an async tool implementation conforms to the protocol."""

        class AsyncEchoTool:
            """An async echo tool."""

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
                }

            async def execute_async(self, **kwargs: Any) -> ToolResult:
                message = kwargs.get("message", "")
                return ToolResult.success(data=f"async: {message}")

        tool = AsyncEchoTool()
        assert isinstance(tool, AsyncTool)
        assert tool.name == "async_echo"

        result = await tool.execute_async(message="Hello")
        assert result.is_success
        assert result.data == "async: Hello"

    @pytest.mark.asyncio
    async def test_async_tool_with_error(self) -> None:
        """Test async tool that returns errors."""

        class AsyncErrorTool:
            """Async tool that errors."""

            @property
            def name(self) -> str:
                return "async_error"

            @property
            def description(self) -> str:
                return "Async error tool"

            @property
            def parameters(self) -> dict[str, Any]:
                return {"type": "object", "properties": {}}

            async def execute_async(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.error(error="Async error")

        tool = AsyncErrorTool()
        result = await tool.execute_async()
        assert result.is_error
        assert result.error_message == "Async error"
