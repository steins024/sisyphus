"""Tests for the conversation module."""

from sisyphus.core import Conversation, Message


class TestMessage:
    """Tests for Message dataclass."""

    def test_create_user_message(self) -> None:
        """Test creating a user message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_create_assistant_message(self) -> None:
        """Test creating an assistant message."""
        msg = Message(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"


class TestConversation:
    """Tests for Conversation class."""

    def test_empty_conversation(self) -> None:
        """Test creating an empty conversation."""
        conv = Conversation()
        assert len(conv) == 0
        assert conv.is_empty
        assert conv.last_message is None

    def test_add_user_message(self) -> None:
        """Test adding a user message."""
        conv = Conversation()
        conv.add_user_message("Hello")
        assert len(conv) == 1
        assert not conv.is_empty
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Hello"

    def test_add_assistant_message(self) -> None:
        """Test adding an assistant message."""
        conv = Conversation()
        conv.add_assistant_message("Hi there!")
        assert len(conv) == 1
        assert conv.messages[0].role == "assistant"
        assert conv.messages[0].content == "Hi there!"

    def test_conversation_flow(self) -> None:
        """Test a typical conversation flow."""
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi! How can I help?")
        conv.add_user_message("What's 2+2?")
        conv.add_assistant_message("2+2 equals 4.")

        assert len(conv) == 4
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[2].role == "user"
        assert conv.messages[3].role == "assistant"

    def test_last_message(self) -> None:
        """Test getting the last message."""
        conv = Conversation()
        conv.add_user_message("First")
        assert conv.last_message is not None
        assert conv.last_message.content == "First"

        conv.add_assistant_message("Second")
        assert conv.last_message is not None
        assert conv.last_message.content == "Second"

    def test_to_api_format(self) -> None:
        """Test converting to API format."""
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi!")

        api_format = conv.to_api_format()
        assert api_format == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]

    def test_to_api_format_empty(self) -> None:
        """Test converting empty conversation to API format."""
        conv = Conversation()
        assert conv.to_api_format() == []

    def test_clear(self) -> None:
        """Test clearing conversation history."""
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi!")
        assert len(conv) == 2

        conv.clear()
        assert len(conv) == 0
        assert conv.is_empty

    def test_system_prompt(self) -> None:
        """Test setting system prompt."""
        conv = Conversation(system_prompt="You are a helpful assistant.")
        assert conv.system_prompt == "You are a helpful assistant."

    def test_system_prompt_default(self) -> None:
        """Test default system prompt is None."""
        conv = Conversation()
        assert conv.system_prompt is None

    def test_independent_instances(self) -> None:
        """Test that conversation instances don't share state."""
        conv1 = Conversation()
        conv2 = Conversation()

        conv1.add_user_message("Hello from conv1")
        assert len(conv1) == 1
        assert len(conv2) == 0
