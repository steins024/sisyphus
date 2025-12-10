"""Conversation history management."""

from dataclasses import dataclass, field
from typing import Any, Literal


def _empty_message_list() -> "list[Message]":
    """Factory function for empty message list."""
    return []


Role = Literal["user", "assistant"]


@dataclass
class Message:
    """A single message in the conversation."""

    role: Role
    content: str


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
