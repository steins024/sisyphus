"""Tests for the tool registry."""

# ruff: noqa: RUF012

import tempfile
from pathlib import Path
from typing import Any

import pytest

from sisyphus.core.tool import (
    Tool,
    ToolDefinition,
    ToolNotFoundError,
    ToolRegistrationError,
    ToolResult,
)
from sisyphus.registry import ToolRegistry

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def registry() -> ToolRegistry:
    """Get a fresh registry instance for each test."""
    ToolRegistry.reset_instance()
    return ToolRegistry.get_instance()


@pytest.fixture
def sample_tool() -> Tool:
    """Create a sample tool for testing."""

    class SampleTool:
        @property
        def name(self) -> str:
            return "sample_tool"

        @property
        def description(self) -> str:
            return "A sample tool for testing"

        @property
        def parameters(self) -> dict[str, Any]:
            return {"type": "object", "properties": {}}

        def execute(self, **_kwargs: Any) -> ToolResult:
            return ToolResult.success(data="executed")

    return SampleTool()  # type: ignore[return-value]


@pytest.fixture
def temp_yaml_dir() -> Path:
    """Create a temporary directory for YAML files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Test ToolRegistry Singleton
# ============================================================================


class TestToolRegistrySingleton:
    """Tests for singleton pattern."""

    def test_get_instance_returns_same_instance(self) -> None:
        """Test that get_instance returns the same instance."""
        ToolRegistry.reset_instance()
        registry1 = ToolRegistry.get_instance()
        registry2 = ToolRegistry.get_instance()
        assert registry1 is registry2

    def test_reset_instance(self) -> None:
        """Test that reset_instance creates a new instance."""
        registry1 = ToolRegistry.get_instance()
        ToolRegistry.reset_instance()
        registry2 = ToolRegistry.get_instance()
        assert registry1 is not registry2


# ============================================================================
# Test Tool Registration
# ============================================================================


class TestToolRegistration:
    """Tests for tool registration."""

    def test_register_tool(self, registry: ToolRegistry, sample_tool: Tool) -> None:
        """Test registering a tool."""
        registry.register(sample_tool)
        assert registry.has("sample_tool")
        assert registry.get("sample_tool") is sample_tool

    def test_register_duplicate_tool_raises_error(
        self, registry: ToolRegistry, sample_tool: Tool
    ) -> None:
        """Test that registering duplicate tool raises error."""
        registry.register(sample_tool)
        with pytest.raises(
            ToolRegistrationError, match="already registered"
        ):
            registry.register(sample_tool)

    def test_register_duplicate_tool_with_override(
        self, registry: ToolRegistry, sample_tool: Tool
    ) -> None:
        """Test that allow_override permits duplicate registration."""
        registry.register(sample_tool)
        registry.register(sample_tool, allow_override=True)
        assert registry.has("sample_tool")

    def test_register_multiple_tools(self, registry: ToolRegistry) -> None:
        """Test registering multiple tools."""

        class Tool1:
            name = "tool1"
            description = "Tool 1"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.success()

        class Tool2:
            name = "tool2"
            description = "Tool 2"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.success()

        registry.register(Tool1())  # type: ignore[arg-type]
        registry.register(Tool2())  # type: ignore[arg-type]

        assert registry.has("tool1")
        assert registry.has("tool2")
        assert len(registry.list()) == 2


# ============================================================================
# Test Tool Retrieval
# ============================================================================


class TestToolRetrieval:
    """Tests for tool retrieval."""

    def test_get_tool(self, registry: ToolRegistry, sample_tool: Tool) -> None:
        """Test getting a registered tool."""
        registry.register(sample_tool)
        tool = registry.get("sample_tool")
        assert tool is sample_tool

    def test_get_nonexistent_tool_raises_error(
        self, registry: ToolRegistry
    ) -> None:
        """Test that getting nonexistent tool raises error."""
        with pytest.raises(ToolNotFoundError, match="not registered"):
            registry.get("nonexistent_tool")

    def test_has_tool(self, registry: ToolRegistry, sample_tool: Tool) -> None:
        """Test checking if tool exists."""
        assert not registry.has("sample_tool")
        registry.register(sample_tool)
        assert registry.has("sample_tool")

    def test_list_tools(self, registry: ToolRegistry) -> None:
        """Test listing all registered tools."""

        class ToolA:
            name = "tool_a"
            description = "Tool A"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.success()

        class ToolB:
            name = "tool_b"
            description = "Tool B"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.success()

        registry.register(ToolB())  # type: ignore[arg-type]
        registry.register(ToolA())  # type: ignore[arg-type]

        # Should be sorted alphabetically
        assert registry.list() == ["tool_a", "tool_b"]

    def test_list_tool_instances(self, registry: ToolRegistry) -> None:
        """Test listing all tool instances."""

        class Tool1:
            name = "tool1"
            description = "Tool 1"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.success()

        tool = Tool1()
        registry.register(tool)  # type: ignore[arg-type]

        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0] is tool

    def test_items_list(self, registry: ToolRegistry) -> None:
        """Test getting all tool names and instances."""

        class Tool1:
            name = "tool1"
            description = "Tool 1"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **_kwargs: Any) -> ToolResult:
                return ToolResult.success()

        tool = Tool1()
        registry.register(tool)  # type: ignore[arg-type]

        items = registry.items()
        assert len(items) == 1
        assert items[0][0] == "tool1"
        assert items[0][1] is tool


# ============================================================================
# Test Tool Unregistration
# ============================================================================


class TestToolUnregistration:
    """Tests for tool unregistration."""

    def test_unregister_tool(
        self, registry: ToolRegistry, sample_tool: Tool
    ) -> None:
        """Test unregistering a tool."""
        registry.register(sample_tool)
        assert registry.has("sample_tool")

        registry.unregister("sample_tool")
        assert not registry.has("sample_tool")

    def test_unregister_nonexistent_tool_raises_error(
        self, registry: ToolRegistry
    ) -> None:
        """Test that unregistering nonexistent tool raises error."""
        with pytest.raises(ToolNotFoundError, match="not registered"):
            registry.unregister("nonexistent_tool")

    def test_clear_all_tools(
        self, registry: ToolRegistry, sample_tool: Tool
    ) -> None:
        """Test clearing all tools."""
        registry.register(sample_tool)
        assert len(registry.list()) == 1

        registry.clear()
        assert len(registry.list()) == 0


# ============================================================================
# Test YAML Loading
# ============================================================================


class TestYAMLLoading:
    """Tests for loading tools from YAML."""

    def test_register_from_yaml_with_valid_file(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test loading tool from valid YAML file."""
        yaml_file = temp_yaml_dir / "test_tool.yaml"
        yaml_content = """
name: test_tool
description: A test tool
parameters:
  type: object
  properties:
    message:
      type: string
handler: sisyphus.tools.test_tool.execute
"""
        yaml_file.write_text(yaml_content)

        # This will fail to import the handler, which is expected
        # We're testing the YAML parsing part
        with pytest.raises(ToolRegistrationError, match="Failed to register"):
            registry.register_from_yaml(yaml_file)

    def test_register_from_yaml_with_invalid_yaml(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test that invalid YAML raises error."""
        yaml_file = temp_yaml_dir / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content:")

        with pytest.raises(ToolRegistrationError):
            registry.register_from_yaml(yaml_file)

    def test_register_from_yaml_with_missing_fields(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test that YAML with missing required fields raises error."""
        yaml_file = temp_yaml_dir / "incomplete.yaml"
        yaml_content = """
name: incomplete_tool
# Missing description, parameters, and handler
"""
        yaml_file.write_text(yaml_content)

        with pytest.raises(ToolRegistrationError):
            registry.register_from_yaml(yaml_file)

    def test_register_from_nonexistent_yaml(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test that loading from nonexistent file raises error."""
        yaml_file = temp_yaml_dir / "nonexistent.yaml"

        with pytest.raises(ToolRegistrationError):
            registry.register_from_yaml(yaml_file)


# ============================================================================
# Test Definition Registration
# ============================================================================


class TestDefinitionRegistration:
    """Tests for registering tools from definitions."""

    def test_register_from_definition(self, registry: ToolRegistry) -> None:
        """Test registering tool from definition."""
        definition = ToolDefinition(
            name="test_tool",
            description="Test tool",
            parameters={"type": "object", "properties": {}},
            handler="builtins.len",  # Use a real function for testing
        )

        registry.register_from_definition(definition)
        assert registry.has("test_tool")

    def test_get_definition(self, registry: ToolRegistry) -> None:
        """Test getting tool definition."""
        definition = ToolDefinition(
            name="test_tool",
            description="Test tool",
            parameters={"type": "object", "properties": {}},
            handler="builtins.len",
        )

        registry.register_from_definition(definition)
        retrieved = registry.get_definition("test_tool")

        assert retrieved is not None
        assert retrieved.name == "test_tool"
        assert retrieved.description == "Test tool"

    def test_get_definition_for_nonexistent_tool(
        self, registry: ToolRegistry
    ) -> None:
        """Test that getting definition for nonexistent tool returns None."""
        assert registry.get_definition("nonexistent") is None

    def test_register_from_definition_with_invalid_handler(
        self, registry: ToolRegistry
    ) -> None:
        """Test that invalid handler raises error."""
        definition = ToolDefinition(
            name="test_tool",
            description="Test tool",
            parameters={"type": "object", "properties": {}},
            handler="nonexistent.module.function",
        )

        with pytest.raises(ToolRegistrationError, match="Failed to register"):
            registry.register_from_definition(definition)


# ============================================================================
# Test Directory Loading
# ============================================================================


class TestDirectoryLoading:
    """Tests for loading tools from directories."""

    def test_register_from_empty_directory(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test loading from empty directory."""
        registered = registry.register_from_yaml_directory(temp_yaml_dir)
        assert registered == []

    def test_register_from_nonexistent_directory(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test that loading from nonexistent directory raises error."""
        nonexistent_dir = temp_yaml_dir / "nonexistent"

        with pytest.raises(ToolRegistrationError, match="does not exist"):
            registry.register_from_yaml_directory(nonexistent_dir)

    def test_register_from_directory_with_valid_files(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test loading multiple tools from directory."""
        # Create valid YAML files (they will fail on handler import)
        for i in range(3):
            yaml_file = temp_yaml_dir / f"tool_{i}.yaml"
            yaml_content = f"""
name: tool_{i}
description: Tool {i}
parameters:
  type: object
  properties: {{}}
handler: builtins.len
"""
            yaml_file.write_text(yaml_content)

        # Should successfully register all tools
        registered = registry.register_from_yaml_directory(temp_yaml_dir)
        assert len(registered) == 3
        assert "tool_0" in registered
        assert "tool_1" in registered
        assert "tool_2" in registered

    def test_register_from_directory_with_custom_pattern(
        self, registry: ToolRegistry, temp_yaml_dir: Path
    ) -> None:
        """Test loading with custom file pattern."""
        # Create files with different extensions
        (temp_yaml_dir / "tool1.yaml").write_text(
            """
name: tool1
description: Tool 1
parameters:
  type: object
  properties: {}
handler: builtins.len
"""
        )

        (temp_yaml_dir / "tool2.yml").write_text(
            """
name: tool2
description: Tool 2
parameters:
  type: object
  properties: {}
handler: builtins.len
"""
        )

        # Load only .yml files
        registered = registry.register_from_yaml_directory(
            temp_yaml_dir, pattern="*.yml"
        )
        assert len(registered) == 1
        assert "tool2" in registered


# ============================================================================
# Test Thread Safety
# ============================================================================


class TestThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_registration(self, registry: ToolRegistry) -> None:
        """Test that concurrent registrations are thread-safe."""
        import threading

        results: list[bool] = []

        def register_tool(i: int) -> None:
            class TestTool:
                name = f"tool_{i}"
                description = f"Tool {i}"
                parameters = {"type": "object", "properties": {}}

                def execute(self, **_kwargs: Any) -> ToolResult:
                    return ToolResult.success()

            try:
                registry.register(TestTool())  # type: ignore[arg-type]
                results.append(True)
            except Exception:
                results.append(False)

        threads = [threading.Thread(target=register_tool, args=(i,)) for i in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All registrations should succeed
        assert all(results)
        assert len(registry.list()) == 10
