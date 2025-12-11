"""Conversation history management."""

from dataclasses import dataclass, field
from typing import Any, Literal


def _empty_message_list() -> "list[Message]":
    """Factory function for empty message list."""
    return []


Role = Literal["user", "assistant"]

# Content can be a string (simple text) or a list of content blocks (structured)
MessageContent = str | list[dict[str, Any]]


@dataclass
class Message:
    """A single message in the conversation.

    Messages can have either simple string content or structured content blocks.
    Structured content is used for tool use and tool results.
    """

    role: Role
    content: MessageContent


@dataclass
class Conversation:
    """Manages conversation history.

    Provides methods to add messages, convert to API format,
    and manage conversation state.
    """

    messages: list[Message] = field(default_factory=_empty_message_list)
    system_prompt: str | None = None

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation.

        Args:
            content: The message content.
        """
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation.

        Args:
            content: The message content.
        """
        self.messages.append(Message(role="assistant", content=content))

    def add_structured_message(
        self, role: Role, content_blocks: list[dict[str, Any]]
    ) -> None:
        """Add a message with structured content blocks.

        Used for tool use and tool results, which require structured content
        rather than simple strings.

        Args:
            role: Message role ('user' or 'assistant')
            content_blocks: List of content block dictionaries
        """
        self.messages.append(Message(role=role, content=content_blocks))

    def add_tool_use_message(self, content_blocks: list[dict[str, Any]]) -> None:
        """Add an assistant message containing tool use blocks.

        Args:
            content_blocks: List of content blocks including tool_use blocks
        """
        self.add_structured_message("assistant", content_blocks)

    def add_tool_result_message(self, tool_results: list[dict[str, Any]]) -> None:
        """Add a user message containing tool result blocks.

        Args:
            tool_results: List of tool_result content blocks
        """
        self.add_structured_message("user", tool_results)

    def to_api_format(self) -> list[dict[str, Any]]:
        """Convert to format expected by LLM API.

        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def clear(self) -> None:
        """Clear conversation history."""
        self.messages.clear()

    def __len__(self) -> int:
        """Return number of messages in conversation."""
        return len(self.messages)

    @property
    def is_empty(self) -> bool:
        """Check if conversation has no messages."""
        return len(self.messages) == 0

    @property
    def last_message(self) -> Message | None:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
