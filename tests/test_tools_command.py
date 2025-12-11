"""Tests for the /tools command in the CLI."""

from pathlib import Path

from sisyphus.core import Conversation
from sisyphus.registry.tool_registry import ToolRegistry
from sisyphus.ui.cli import handle_special_command


def test_tools_command_with_registry():
    """Test /tools command displays registered tools."""
    # Create a registry and register tools
    registry = ToolRegistry.get_instance()
    registry.clear()

    tools_dir = Path(__file__).parent.parent / "config" / "tools"
    if tools_dir.exists():
        registry.register_from_yaml_directory(str(tools_dir))

    # Create a conversation
    conversation = Conversation()

    # Handle /tools command
    result = handle_special_command("/tools", conversation, registry)

    # Should return True (command was handled)
    assert result is True

    # Verify tools are registered
    assert registry.has("read_file")
    assert registry.has("write_file")
    assert registry.has("search")
    assert registry.has("terminal")

    # Cleanup
    registry.clear()


def test_tools_command_without_registry():
    """Test /tools command when registry is None."""
    conversation = Conversation()

    # Handle /tools command without registry
    result = handle_special_command("/tools", conversation, None)

    # Should return True (command was handled)
    assert result is True


def test_tools_command_with_empty_registry():
    """Test /tools command with empty registry."""
    registry = ToolRegistry.get_instance()
    registry.clear()

    conversation = Conversation()

    # Handle /tools command with empty registry
    result = handle_special_command("/tools", conversation, registry)

    # Should return True (command was handled)
    assert result is True

    # Cleanup
    registry.clear()
