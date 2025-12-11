"""Tool registry for managing tool definitions and instances.

This module provides a singleton registry for tools that can be used by
agents, subagents, and skills. It supports both programmatic registration
and loading from YAML configuration files.
"""

import importlib
import threading
from pathlib import Path
from typing import Any

import yaml

from sisyphus.core.tool import (
    AsyncTool,
    AsyncToolHandler,
    SyncToolHandler,
    Tool,
    ToolDefinition,
    ToolHandler,
    ToolNotFoundError,
    ToolRegistrationError,
)


class ToolRegistry:
    """Singleton registry for managing tools.

    The ToolRegistry maintains a central repository of all available tools
    in the system. It supports:
    - Programmatic registration of tool instances
    - Loading tool definitions from YAML files
    - Dynamic handler resolution and instantiation
    - Thread-safe operations

    Usage:
        registry = ToolRegistry.get_instance()
        registry.register(my_tool)
        tool = registry.get("tool_name")
        all_tools = registry.list()
    """

    _instance: "ToolRegistry | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the tool registry.

        Note: Use get_instance() instead of calling this directly.
        """
        self._tools: dict[str, Tool | AsyncTool] = {}
        self._definitions: dict[str, ToolDefinition] = {}
        self._lock_instance = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """Get the singleton instance of the tool registry.

        Returns:
            The singleton ToolRegistry instance

        Thread-safe: Yes
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance.

        This is primarily useful for testing to ensure a clean state.

        Warning: This should not be called in production code.
        """
        with cls._lock:
            cls._instance = None

    def register(
        self,
        tool: Tool | AsyncTool,
        *,
        allow_override: bool = False,
    ) -> None:
        """Register a tool instance.

        Args:
            tool: The tool instance to register
            allow_override: If True, allow overriding existing tools

        Raises:
            ToolRegistrationError: If tool name is already registered
                and allow_override is False
        """
        with self._lock_instance:
            if not allow_override and tool.name in self._tools:
                raise ToolRegistrationError(
                    f"Tool '{tool.name}' is already registered. "
                    f"Use allow_override=True to replace it.",
                    tool_name=tool.name,
                )

            self._tools[tool.name] = tool

    def register_from_definition(
        self,
        definition: ToolDefinition,
        *,
        allow_override: bool = False,
    ) -> None:
        """Register a tool from a definition by resolving its handler.

        Args:
            definition: The tool definition with handler path
            allow_override: If True, allow overriding existing tools

        Raises:
            ToolRegistrationError: If handler cannot be resolved or
                instantiation fails
        """
        with self._lock_instance:
            if not allow_override and definition.name in self._definitions:
                raise ToolRegistrationError(
                    f"Tool definition '{definition.name}' is already registered. "
                    f"Use allow_override=True to replace it.",
                    tool_name=definition.name,
                )

            # Store the definition
            self._definitions[definition.name] = definition

            # Resolve and instantiate the handler
            try:
                handler = self._resolve_handler(definition.handler)
                tool_instance = self._create_tool_from_handler(definition, handler)
                self._tools[definition.name] = tool_instance
            except Exception as e:
                raise ToolRegistrationError(
                    f"Failed to register tool '{definition.name}' from handler "
                    f"'{definition.handler}': {e}",
                    tool_name=definition.name,
                ) from e

    def register_from_yaml(
        self,
        yaml_path: Path | str,
        *,
        allow_override: bool = False,
    ) -> None:
        """Register a tool from a YAML definition file.

        Args:
            yaml_path: Path to the YAML file containing tool definition
            allow_override: If True, allow overriding existing tools

        Raises:
            ToolRegistrationError: If YAML is invalid or registration fails
        """
        try:
            yaml_path = Path(yaml_path)
            with yaml_path.open("r") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ValueError("YAML must contain a dictionary")

            # yaml.safe_load returns dict[Any, Any], cast to dict[str, Any]
            definition = ToolDefinition(**data)  # type: ignore[arg-type]
            self.register_from_definition(definition, allow_override=allow_override)

        except Exception as e:
            raise ToolRegistrationError(
                f"Failed to load tool from YAML '{yaml_path}': {e}",
            ) from e

    def register_from_yaml_directory(
        self,
        directory: Path | str,
        *,
        pattern: str = "*.yaml",
        allow_override: bool = False,
    ) -> list[str]:
        """Register all tools from YAML files in a directory.

        Args:
            directory: Path to directory containing YAML files
            pattern: Glob pattern for YAML files (default: "*.yaml")
            allow_override: If True, allow overriding existing tools

        Returns:
            List of registered tool names

        Raises:
            ToolRegistrationError: If any registration fails
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise ToolRegistrationError(
                f"Directory '{directory}' does not exist or is not a directory"
            )

        registered_tools: list[str] = []
        errors: list[tuple[Path, Exception]] = []

        for yaml_file in directory.glob(pattern):
            if yaml_file.is_file():
                try:
                    self.register_from_yaml(yaml_file, allow_override=allow_override)
                    # Get the tool name from the file (we know it was just registered)
                    with yaml_file.open("r") as f:
                        data = yaml.safe_load(f)
                        if isinstance(data, dict) and "name" in data:
                            tool_name: Any = data["name"]  # type: ignore[misc]
                            if isinstance(tool_name, str):
                                registered_tools.append(tool_name)
                except Exception as e:
                    errors.append((yaml_file, e))

        if errors:
            error_messages = [
                f"{path}: {error}" for path, error in errors
            ]
            raise ToolRegistrationError(
                f"Failed to register {len(errors)} tool(s):\n"
                + "\n".join(error_messages)
            )

        return registered_tools

    def get(self, name: str) -> Tool | AsyncTool:
        """Get a registered tool by name.

        Args:
            name: The tool name

        Returns:
            The tool instance

        Raises:
            ToolNotFoundError: If tool is not registered
        """
        with self._lock_instance:
            if name not in self._tools:
                raise ToolNotFoundError(
                    f"Tool '{name}' is not registered", tool_name=name
                )
            return self._tools[name]

    def get_definition(self, name: str) -> ToolDefinition | None:
        """Get the definition for a registered tool.

        Args:
            name: The tool name

        Returns:
            The tool definition if available, None otherwise
        """
        with self._lock_instance:
            return self._definitions.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: The tool name

        Returns:
            True if tool is registered, False otherwise
        """
        with self._lock_instance:
            return name in self._tools

    def list(self) -> list[str]:  # type: ignore[misc]
        """List all registered tool names.

        Returns:
            List of tool names in alphabetical order
        """
        with self._lock_instance:
            # Use explicit list comprehension to satisfy type checker
            return sorted([name for name in self._tools])

    def list_tools(self) -> list[Tool | AsyncTool]:  # type: ignore[misc]
        """List all registered tool instances.

        Returns:
            List of tool instances
        """
        with self._lock_instance:
            # Use explicit list comprehension to satisfy type checker
            return [tool for tool in self._tools.values()]

    def items(self) -> list[tuple[str, Tool | AsyncTool]]:  # type: ignore[misc]
        """Get all tool names and instances.

        Returns:
            List of tuples (tool_name, tool_instance)
        """
        with self._lock_instance:
            return list(self._tools.items())

    def unregister(self, name: str) -> None:
        """Unregister a tool.

        Args:
            name: The tool name

        Raises:
            ToolNotFoundError: If tool is not registered
        """
        with self._lock_instance:
            if name not in self._tools:
                raise ToolNotFoundError(
                    f"Tool '{name}' is not registered", tool_name=name
                )
            del self._tools[name]
            if name in self._definitions:
                del self._definitions[name]

    def clear(self) -> None:
        """Clear all registered tools.

        Warning: This removes all tools from the registry.
        Use with caution.
        """
        with self._lock_instance:
            self._tools.clear()
            self._definitions.clear()

    def _resolve_handler(self, handler_path: str) -> ToolHandler:
        """Resolve a handler function from a module path.

        Args:
            handler_path: Module path like "module.submodule.function"

        Returns:
            The handler function

        Raises:
            ImportError: If module or function cannot be found
        """
        parts = handler_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(
                f"Invalid handler path '{handler_path}'. "
                f"Expected format: 'module.function'"
            )

        module_path, function_name = parts

        try:
            module = importlib.import_module(module_path)
            handler = getattr(module, function_name)

            if not callable(handler):
                raise TypeError(
                    f"Handler '{handler_path}' is not callable"
                )

            return handler  # type: ignore[return-value]

        except ImportError as e:
            raise ImportError(
                f"Cannot import module '{module_path}': {e}"
            ) from e
        except AttributeError as e:
            raise ImportError(
                f"Module '{module_path}' has no attribute '{function_name}': {e}"
            ) from e

    def _create_tool_from_handler(
        self,
        definition: ToolDefinition,
        handler: ToolHandler,
    ) -> Tool | AsyncTool:
        """Create a tool instance from a definition and handler.

        Args:
            definition: The tool definition
            handler: The handler function (sync or async)

        Returns:
            A tool instance implementing the Tool or AsyncTool protocol
        """
        # Create a dynamic tool class that wraps the handler
        if definition.async_handler:
            return _AsyncToolWrapper(definition, handler)  # type: ignore[arg-type]
        else:
            return _SyncToolWrapper(definition, handler)  # type: ignore[arg-type]


# ============================================================================
# Internal Tool Wrappers
# ============================================================================


class _SyncToolWrapper:
    """Internal wrapper for synchronous tool handlers."""

    def __init__(self, definition: ToolDefinition, handler: SyncToolHandler) -> None:
        self._definition = definition
        self._handler = handler

    @property
    def name(self) -> str:
        return self._definition.name

    @property
    def description(self) -> str:
        return self._definition.description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._definition.parameters

    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool handler."""
        return self._handler(**kwargs)


class _AsyncToolWrapper:
    """Internal wrapper for asynchronous tool handlers."""

    def __init__(
        self, definition: ToolDefinition, handler: AsyncToolHandler
    ) -> None:
        self._definition = definition
        self._handler = handler

    @property
    def name(self) -> str:
        return self._definition.name

    @property
    def description(self) -> str:
        return self._definition.description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._definition.parameters

    async def execute_async(self, **kwargs: Any) -> Any:
        """Execute the tool handler asynchronously."""
        return await self._handler(**kwargs)
