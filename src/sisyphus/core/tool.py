"""Tool protocol and type definitions for the Sisyphus agent system.

This module defines the core abstractions for tools that can be used by
agents, subagents, and skills. Tools provide a unified interface for
executing actions like file operations, API calls, and system commands.

Design Principles:
- Protocol-based: Use typing.Protocol for flexible implementations
- Async-first: Support both sync and async execution patterns
- Type-safe: Strict typing with pydantic validation
- Reusable: Designed for use across agents, subagents, and skills
- Maintainable: Clear separation of concerns and extensibility
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Tool Execution Result Types
# ============================================================================


class ToolStatus(str, Enum):
    """Status of a tool execution."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    """Result of a tool execution.

    Provides a standardized way to return results from tool executions,
    including success/failure status, data payload, and error information.

    Attributes:
        status: Execution status (success, error, timeout, cancelled)
        data: The result data (arbitrary type, tool-specific)
        error_message: Error message if status is not SUCCESS
        metadata: Optional metadata about the execution (timing, etc.)
    """

    status: ToolStatus
    data: Any = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=lambda: {})

    @property
    def is_success(self) -> bool:
        """Check if the execution was successful."""
        return self.status == ToolStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if the execution resulted in an error."""
        return self.status == ToolStatus.ERROR

    @classmethod
    def success(cls, data: Any = None, **metadata: Any) -> "ToolResult":
        """Create a successful result.

        Args:
            data: The result data
            **metadata: Optional metadata about the execution

        Returns:
            A ToolResult with SUCCESS status
        """
        return cls(status=ToolStatus.SUCCESS, data=data, metadata=metadata)

    @classmethod
    def error(cls, error: str, **metadata: Any) -> "ToolResult":
        """Create an error result.

        Args:
            error: Error message describing what went wrong
            **metadata: Optional metadata about the execution

        Returns:
            A ToolResult with ERROR status
        """
        return cls(status=ToolStatus.ERROR, error_message=error, metadata=metadata)

    @classmethod
    def timeout(cls, error: str, **metadata: Any) -> "ToolResult":
        """Create a timeout result.

        Args:
            error: Error message describing the timeout
            **metadata: Optional metadata about the execution

        Returns:
            A ToolResult with TIMEOUT status
        """
        return cls(status=ToolStatus.TIMEOUT, error_message=error, metadata=metadata)

    @classmethod
    def cancelled(cls, error: str, **metadata: Any) -> "ToolResult":
        """Create a cancelled result.

        Args:
            error: Error message describing the cancellation
            **metadata: Optional metadata about the execution

        Returns:
            A ToolResult with CANCELLED status
        """
        return cls(
            status=ToolStatus.CANCELLED, error_message=error, metadata=metadata
        )


# ============================================================================
# Tool Exceptions
# ============================================================================


class ToolExecutionError(Exception):
    """Base exception for tool execution errors."""

    def __init__(self, message: str, tool_name: str | None = None) -> None:
        super().__init__(message)
        self.tool_name = tool_name


class ToolValidationError(ToolExecutionError):
    """Raised when tool parameter validation fails."""


class ToolTimeoutError(ToolExecutionError):
    """Raised when tool execution exceeds timeout."""


class ToolNotFoundError(ToolExecutionError):
    """Raised when a requested tool is not registered."""


class ToolRegistrationError(ToolExecutionError):
    """Raised when tool registration fails."""


# ============================================================================
# Tool Definition Schema (for YAML parsing)
# ============================================================================


class ToolDefinition(BaseModel):
    """Definition of a tool loaded from YAML configuration.

    This model is used to parse and validate tool definition files.
    It provides the metadata needed to register and execute tools.

    Example YAML:
        name: read_file
        description: Read the contents of a file from the filesystem
        parameters:
          type: object
          properties:
            file_path:
              type: string
              description: The absolute path to the file to read
          required:
            - file_path
        handler: sisyphus.tools.filesystem.read_file
        timeout: 30.0
        async: false
    """

    name: str = Field(
        description="Unique identifier for the tool (e.g., 'read_file')",
        min_length=1,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    description: str = Field(
        description="Human-readable description of what the tool does",
        min_length=1,
    )

    parameters: dict[str, Any] = Field(
        description="JSON Schema object defining the tool's parameters",
    )

    handler: str = Field(
        description=(
            "Module path to the handler function (e.g., 'tools.filesystem.read_file')"
        ),
        min_length=1,
    )

    timeout: float | None = Field(
        default=None,
        description="Optional timeout in seconds for tool execution",
        gt=0,
    )

    async_handler: bool = Field(
        default=False,
        description="Whether the handler is an async function",
        alias="async",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for tool-specific configuration",
    )

    @field_validator("parameters")
    @classmethod
    def validate_parameters_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that parameters follow JSON Schema object format."""
        # Basic JSON Schema validation
        if "type" not in v:
            raise ValueError("parameters must have a 'type' field")

        if v["type"] != "object":
            raise ValueError("parameters type must be 'object'")

        if "properties" not in v:
            raise ValueError("parameters must have a 'properties' field")

        if not isinstance(v.get("properties"), dict):
            raise ValueError("parameters.properties must be a dict")

        return v

    @field_validator("handler")
    @classmethod
    def validate_handler_path(cls, v: str) -> str:
        """Validate that handler path looks like a valid module path."""
        if not v or "." not in v:
            raise ValueError(
                "handler must be a valid module path (e.g., 'module.function')"
            )
        return v


# ============================================================================
# Tool Protocol Interface
# ============================================================================


@runtime_checkable
class Tool(Protocol):
    """Protocol defining the interface for all tools.

    Tools are executable actions that can be invoked by agents, subagents,
    and skills. This protocol defines the minimum interface that all tools
    must implement.

    Design rationale:
    - Protocol-based for maximum flexibility (no inheritance required)
    - Supports both sync and async execution
    - Provides introspection via name, description, parameters
    - Returns standardized ToolResult for consistent error handling
    """

    @property
    def name(self) -> str:
        """Unique identifier for this tool.

        Returns:
            Tool name (e.g., 'read_file', 'search', 'terminal')
        """
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what this tool does.

        Returns:
            Description text for LLM context and documentation
        """
        ...

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema describing the tool's parameters.

        Returns:
            JSON Schema object with type, properties, required fields, etc.
        """
        ...

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool synchronously.

        Args:
            **kwargs: Tool-specific parameters matching the JSON Schema

        Returns:
            ToolResult with execution status and data/error

        Raises:
            ToolValidationError: If parameters don't match schema
            ToolExecutionError: If execution fails
            ToolTimeoutError: If execution exceeds timeout
        """
        ...


@runtime_checkable
class AsyncTool(Protocol):
    """Protocol for tools that support async execution.

    Tools implementing this protocol can be executed asynchronously,
    which is important for I/O-bound operations like API calls,
    file operations, and long-running processes.
    """

    @property
    def name(self) -> str:
        """Unique identifier for this tool."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        ...

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema describing the tool's parameters."""
        ...

    async def execute_async(self, **kwargs: Any) -> ToolResult:
        """Execute the tool asynchronously.

        Args:
            **kwargs: Tool-specific parameters matching the JSON Schema

        Returns:
            ToolResult with execution status and data/error

        Raises:
            ToolValidationError: If parameters don't match schema
            ToolExecutionError: If execution fails
            ToolTimeoutError: If execution exceeds timeout
        """
        ...


# ============================================================================
# Type Aliases for Handler Functions
# ============================================================================

# Handler function signatures
SyncToolHandler = Callable[..., ToolResult]
AsyncToolHandler = Callable[..., Awaitable[ToolResult]]
ToolHandler = SyncToolHandler | AsyncToolHandler
