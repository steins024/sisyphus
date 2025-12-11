"""Tool formatter for Anthropic API integration.

This module provides utilities to format tool definitions from the
registry into the format expected by the Anthropic Messages API.
"""

from typing import Any

from sisyphus.registry.tool_registry import ToolRegistry


def format_tools_for_anthropic(registry: ToolRegistry) -> list[dict[str, Any]]:
    """Convert registered tools to Anthropic tool format.

    Takes all tools from the registry and formats them into the structure
    required by the Anthropic Messages API tools parameter.

    Args:
        registry: ToolRegistry containing registered tools

    Returns:
        List of tool definitions in Anthropic format:
        [
            {
                "name": "tool_name",
                "description": "Tool description",
                "input_schema": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            },
            ...
        ]
    """
    tools: list[dict[str, Any]] = []

    for tool_name in registry.list():
        definition = registry.get_definition(tool_name)
        if definition:
            tools.append({
                "name": definition.name,
                "description": definition.description,
                "input_schema": definition.parameters,
            })

    return tools


def get_tool_descriptions(registry: ToolRegistry) -> str:
    """Get a human-readable summary of available tools.

    Useful for system prompts or help messages.

    Args:
        registry: ToolRegistry containing registered tools

    Returns:
        Formatted string describing all available tools
    """
    if not registry.list():
        return "No tools available."

    descriptions = []
    for tool_name in registry.list():
        definition = registry.get_definition(tool_name)
        if definition:
            descriptions.append(f"- **{definition.name}**: {definition.description}")

    return "\n".join(descriptions)
