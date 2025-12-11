"""Integration tests for built-in tools with YAML registration."""

import asyncio
from pathlib import Path

import pytest

from sisyphus.registry.tool_registry import ToolRegistry


@pytest.fixture
def registry() -> ToolRegistry:
    """Create a fresh registry for each test."""
    registry = ToolRegistry.get_instance()
    registry.clear()
    yield registry
    registry.clear()


class TestToolYAMLRegistration:
    """Test that all built-in tools can be registered from YAML."""

    def test_register_all_tools_from_directory(self, registry: ToolRegistry) -> None:
        """Test registering all tools from the config/tools directory."""
        config_dir = Path(__file__).parent.parent.parent / "config" / "tools"

        # Register all tools from directory
        registered_tools = registry.register_from_yaml_directory(str(config_dir))

        # Should have registered 4 tools
        assert len(registered_tools) == 4

        # Verify all tools are registered
        assert registry.has("read_file")
        assert registry.has("write_file")
        assert registry.has("search")
        assert registry.has("terminal")

    def test_read_file_yaml_registration(self, registry: ToolRegistry) -> None:
        """Test read_file tool can be registered from YAML."""
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "tools" / "read_file.yaml"
        )

        registry.register_from_yaml(str(config_path))

        assert registry.has("read_file")
        definition = registry.get_definition("read_file")
        assert definition.name == "read_file"
        assert definition.async_handler is False
        assert "file_path" in definition.parameters["properties"]

    def test_write_file_yaml_registration(self, registry: ToolRegistry) -> None:
        """Test write_file tool can be registered from YAML."""
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "tools" / "write_file.yaml"
        )

        registry.register_from_yaml(str(config_path))

        assert registry.has("write_file")
        definition = registry.get_definition("write_file")
        assert definition.name == "write_file"
        assert definition.async_handler is False
        assert "file_path" in definition.parameters["properties"]
        assert "content" in definition.parameters["properties"]

    def test_search_yaml_registration(self, registry: ToolRegistry) -> None:
        """Test search tool can be registered from YAML."""
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "tools" / "search.yaml"
        )

        registry.register_from_yaml(str(config_path))

        assert registry.has("search")
        definition = registry.get_definition("search")
        assert definition.name == "search"
        assert definition.async_handler is False
        assert "pattern" in definition.parameters["properties"]

    def test_terminal_yaml_registration(self, registry: ToolRegistry) -> None:
        """Test terminal tool can be registered from YAML."""
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "tools" / "terminal.yaml"
        )

        registry.register_from_yaml(str(config_path))

        assert registry.has("terminal")
        definition = registry.get_definition("terminal")
        assert definition.name == "terminal"
        assert definition.async_handler is True  # Terminal is async
        assert "command" in definition.parameters["properties"]


class TestToolExecution:
    """Test that registered tools can be executed."""

    def test_execute_read_file_tool(
        self, registry: ToolRegistry, tmp_path: Path
    ) -> None:
        """Test executing read_file tool through registry."""
        # Register tool
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "tools" / "read_file.yaml"
        )
        registry.register_from_yaml(str(config_path))

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        # Get and execute tool
        tool = registry.get("read_file")
        result = tool.execute(file_path=str(test_file))

        assert result.is_success
        assert result.data == "Hello World"

    def test_execute_write_file_tool(
        self, registry: ToolRegistry, tmp_path: Path
    ) -> None:
        """Test executing write_file tool through registry."""
        # Register tool
        config_path = (
            Path(__file__).parent.parent.parent
            / "config"
            / "tools"
            / "write_file.yaml"
        )
        registry.register_from_yaml(str(config_path))

        # Get and execute tool
        test_file = tmp_path / "output.txt"
        tool = registry.get("write_file")
        result = tool.execute(file_path=str(test_file), content="Test content")

        assert result.is_success
        assert test_file.exists()
        assert test_file.read_text() == "Test content"

    def test_execute_search_tool(self, registry: ToolRegistry, tmp_path: Path) -> None:
        """Test executing search tool through registry."""
        # Register tool
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "tools" / "search.yaml"
        )
        registry.register_from_yaml(str(config_path))

        # Create test files
        (tmp_path / "file1.txt").write_text("Hello World")
        (tmp_path / "file2.txt").write_text("Goodbye World")

        # Get and execute tool
        tool = registry.get("search")
        result = tool.execute(pattern="Hello", path=str(tmp_path))

        assert result.is_success
        assert result.metadata["matches_found"] == 1

    @pytest.mark.asyncio
    async def test_execute_terminal_tool(self, registry: ToolRegistry) -> None:
        """Test executing terminal tool through registry."""
        # Register tool
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "tools" / "terminal.yaml"
        )
        registry.register_from_yaml(str(config_path))

        # Get and execute tool (terminal is async)
        tool = registry.get("terminal")

        # Terminal tool has execute_async method
        result = await tool.execute_async(command="echo 'test'")

        assert result.is_success
        assert "test" in result.data["stdout"]


class TestToolIntegration:
    """Test that all tools work together in an integrated scenario."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, registry: ToolRegistry, tmp_path: Path) -> None:
        """Test a complete workflow using all four tools."""
        # Register all tools
        config_dir = Path(__file__).parent.parent.parent / "config" / "tools"
        registry.register_from_yaml_directory(str(config_dir))

        # 1. Write a file
        write_tool = registry.get("write_file")
        test_file = tmp_path / "workflow.txt"
        write_result = write_tool.execute(
            file_path=str(test_file), content="Test workflow content\n"
        )
        assert write_result.is_success

        # 2. Read the file
        read_tool = registry.get("read_file")
        read_result = read_tool.execute(file_path=str(test_file))
        assert read_result.is_success
        assert "workflow" in read_result.data

        # 3. Search for content
        search_tool = registry.get("search")
        search_result = search_tool.execute(pattern="workflow", path=str(tmp_path))
        assert search_result.is_success
        assert search_result.metadata["matches_found"] == 1

        # 4. Execute a command
        terminal_tool = registry.get("terminal")
        terminal_result = await terminal_tool.execute_async(
            command=f"cat {test_file}", shell=False
        )
        assert terminal_result.is_success
        assert "workflow" in terminal_result.data["stdout"]

    def test_all_tools_have_correct_metadata(self, registry: ToolRegistry) -> None:
        """Test that all tools have proper metadata in their definitions."""
        config_dir = Path(__file__).parent.parent.parent / "config" / "tools"
        registry.register_from_yaml_directory(str(config_dir))

        for tool_name in ["read_file", "write_file", "search", "terminal"]:
            definition = registry.get_definition(tool_name)

            # All tools should have these fields
            assert definition.name
            assert definition.description
            assert definition.parameters
            assert definition.handler
            assert definition.timeout is not None

            # Parameters should follow JSON Schema format
            assert definition.parameters["type"] == "object"
            assert "properties" in definition.parameters
            assert "required" in definition.parameters
