"""Tests for the LLM client module."""

from unittest.mock import MagicMock, patch

import anthropic
import pytest

from sisyphus.llm import (
    LLMAPIError,
    LLMClient,
    LLMClientError,
    LLMConfig,
    LLMConnectionError,
)


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = LLMConfig()
        assert config.base_url == "http://localhost:4141"
        assert config.api_key == "dummy"
        assert config.model == "claude-3-sonnet"
        assert config.max_tokens == 4096
        assert config.timeout == 60.0

    def test_custom_values(self) -> None:
        """Test that custom values can be set."""
        config = LLMConfig(
            base_url="http://custom:8080",
            api_key="custom-key",
            model="claude-3-opus",
            max_tokens=2048,
            timeout=30.0,
        )
        assert config.base_url == "http://custom:8080"
        assert config.api_key == "custom-key"
        assert config.model == "claude-3-opus"
        assert config.max_tokens == 2048
        assert config.timeout == 30.0

    def test_env_variable_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables are loaded."""
        monkeypatch.setenv("SISYPHUS_BASE_URL", "http://env:9000")
        monkeypatch.setenv("SISYPHUS_MODEL", "claude-3-haiku")
        config = LLMConfig()
        assert config.base_url == "http://env:9000"
        assert config.model == "claude-3-haiku"

    def test_max_tokens_validation(self) -> None:
        """Test max_tokens has proper validation."""
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=0)
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=-1)

    def test_timeout_validation(self) -> None:
        """Test timeout has proper validation."""
        with pytest.raises(ValueError):
            LLMConfig(timeout=0)
        with pytest.raises(ValueError):
            LLMConfig(timeout=-1)


class TestLLMClientErrors:
    """Tests for LLM client exception hierarchy."""

    def test_error_hierarchy(self) -> None:
        """Test that error classes have correct inheritance."""
        assert issubclass(LLMConnectionError, LLMClientError)
        assert issubclass(LLMAPIError, LLMClientError)

    def test_api_error_status_code(self) -> None:
        """Test that LLMAPIError stores status code."""
        error = LLMAPIError("Test error", status_code=429)
        assert error.status_code == 429
        assert str(error) == "Test error"

    def test_api_error_no_status_code(self) -> None:
        """Test that LLMAPIError works without status code."""
        error = LLMAPIError("Test error")
        assert error.status_code is None


class TestLLMClient:
    """Tests for LLMClient."""

    def test_init_with_default_config(self) -> None:
        """Test client initializes with default config."""
        with patch("sisyphus.llm.client.anthropic.Anthropic"):
            client = LLMClient()
            assert client.config.base_url == "http://localhost:4141"

    def test_init_with_custom_config(self) -> None:
        """Test client initializes with custom config."""
        config = LLMConfig(base_url="http://custom:8080")
        with patch("sisyphus.llm.client.anthropic.Anthropic"):
            client = LLMClient(config=config)
            assert client.config.base_url == "http://custom:8080"

    def test_send_message_success(self) -> None:
        """Test successful message sending."""
        mock_response = MagicMock(spec=anthropic.types.Message)
        mock_response.content = [MagicMock(type="text", text="Hello!")]

        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            messages = [{"role": "user", "content": "Hello"}]
            response = client.send_message(messages)

            assert response == mock_response
            mock_client.messages.create.assert_called_once()

    def test_send_message_with_system_prompt(self) -> None:
        """Test message sending with system prompt."""
        mock_response = MagicMock(spec=anthropic.types.Message)

        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            messages = [{"role": "user", "content": "Hello"}]
            client.send_message(messages, system="You are a helpful assistant")

            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["system"] == "You are a helpful assistant"

    def test_send_message_connection_error(self) -> None:
        """Test that connection errors are wrapped properly."""
        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = anthropic.APIConnectionError(
                request=MagicMock()
            )
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            with pytest.raises(LLMConnectionError) as exc_info:
                client.send_message([{"role": "user", "content": "Hello"}])

            assert "Failed to connect" in str(exc_info.value)

    def test_send_message_api_error(self) -> None:
        """Test that API errors are wrapped properly."""
        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_error = anthropic.APIStatusError(
                message="Rate limited",
                response=MagicMock(status_code=429),
                body={"error": {"message": "Rate limited"}},
            )
            mock_client.messages.create.side_effect = mock_error
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            with pytest.raises(LLMAPIError) as exc_info:
                client.send_message([{"role": "user", "content": "Hello"}])

            assert exc_info.value.status_code == 429

    def test_get_text_response(self) -> None:
        """Test extracting text from response."""
        mock_response = MagicMock(spec=anthropic.types.Message)
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Hello, world!"
        mock_response.content = [mock_text_block]

        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            text = client.get_text_response([{"role": "user", "content": "Hello"}])

            assert text == "Hello, world!"

    def test_get_text_response_multiple_blocks(self) -> None:
        """Test extracting text from multiple content blocks."""
        mock_response = MagicMock(spec=anthropic.types.Message)
        mock_block1 = MagicMock()
        mock_block1.type = "text"
        mock_block1.text = "Part 1. "
        mock_block2 = MagicMock()
        mock_block2.type = "text"
        mock_block2.text = "Part 2."
        mock_response.content = [mock_block1, mock_block2]

        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            text = client.get_text_response([{"role": "user", "content": "Hello"}])

            assert text == "Part 1. Part 2."

    def test_stream_message_success(self) -> None:
        """Test successful message streaming."""
        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_stream = MagicMock()
            mock_stream.__enter__ = MagicMock(return_value=mock_stream)
            mock_stream.__exit__ = MagicMock(return_value=False)
            mock_stream.text_stream = iter(["Hello", ", ", "world", "!"])
            mock_client.messages.stream.return_value = mock_stream
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            messages = [{"role": "user", "content": "Hello"}]
            chunks = list(client.stream_message(messages))

            assert chunks == ["Hello", ", ", "world", "!"]

    def test_model_override(self) -> None:
        """Test that model can be overridden per request."""
        mock_response = MagicMock(spec=anthropic.types.Message)

        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            messages = [{"role": "user", "content": "Hello"}]
            client.send_message(messages, model="claude-3-opus")

            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-3-opus"

    def test_max_tokens_override(self) -> None:
        """Test that max_tokens can be overridden per request."""
        mock_response = MagicMock(spec=anthropic.types.Message)

        with patch("sisyphus.llm.client.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            client = LLMClient()
            messages = [{"role": "user", "content": "Hello"}]
            client.send_message(messages, max_tokens=1024)

            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["max_tokens"] == 1024
