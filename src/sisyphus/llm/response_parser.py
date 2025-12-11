"""Parser for LLM responses with tool use support.

This module provides utilities to parse Anthropic API responses
and extract tool calls from them.
"""

from typing import Any

import anthropic

from sisyphus.core.tool_call import ToolCall


def parse_tool_calls(message: anthropic.types.Message) -> list[ToolCall]:
    """Extract tool calls from an Anthropic message response.

    Args:
        message: Anthropic Message object from API response

    Returns:
        List of ToolCall objects, one for each tool_use block in the message
    """
    tool_calls: list[ToolCall] = []

    for block in message.content:
        if block.type == "tool_use":
            tool_calls.append(
                ToolCall(
                    id=block.id,
                    name=block.name,
                    input=block.input,
                )
            )

    return tool_calls


def has_tool_calls(message: anthropic.types.Message) -> bool:
    """Check if a message contains any tool calls.

    Args:
        message: Anthropic Message object from API response

    Returns:
        True if the message contains tool_use blocks, False otherwise
    """
    return message.stop_reason == "tool_use"


def extract_text_content(message: anthropic.types.Message) -> str:
    """Extract all text content from a message, ignoring tool blocks.

    Args:
        message: Anthropic Message object from API response

    Returns:
        Concatenated text from all text content blocks
    """
    text_parts: list[str] = []

    for block in message.content:
        if block.type == "text":
            text_parts.append(block.text)

    return "".join(text_parts)


def message_to_dict(message: anthropic.types.Message) -> dict[str, Any]:
    """Convert an Anthropic message to a dictionary for conversation history.

    This preserves all content blocks (text and tool_use) in the format
    needed for the Anthropic API.

    Args:
        message: Anthropic Message object from API response

    Returns:
        Dictionary with 'role' and 'content' suitable for conversation history
    """
    content_blocks = []

    for block in message.content:
        if block.type == "text":
            content_blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content_blocks.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })

    return {"role": "assistant", "content": content_blocks}
