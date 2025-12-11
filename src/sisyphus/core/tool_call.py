"""Tool call data structures for LLM tool use integration.

This module defines the data structures used to represent tool calls
from LLM responses and their results.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    """Represents a tool call request from an LLM response.

    When an LLM wants to use a tool, it returns a tool_use content block
    with this information. This class represents the parsed tool call.

    Attributes:
        id: Unique identifier for this tool call (from LLM)
        name: Name of the tool to call (e.g., 'read_file')
        input: Dictionary of parameters to pass to the tool
    """

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolCallResult:
    """Represents the result of a tool execution to send back to the LLM.

    After executing a tool, this structure is used to format the result
    in a way that the LLM can understand.

    Attributes:
        tool_use_id: The ID from the original ToolCall
        content: String representation of the result (JSON or text)
        is_error: Whether the tool execution resulted in an error
    """

    tool_use_id: str
    content: str
    is_error: bool = False

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic tool_result block format.

        Returns:
            Dictionary in the format expected by the Anthropic API
        """
        return {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "content": self.content,
            "is_error": self.is_error,
        }
