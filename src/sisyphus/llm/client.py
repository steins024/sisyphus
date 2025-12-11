"""LLM client wrapper for Copilot API."""

from collections.abc import Iterator
from typing import Any, cast

import anthropic
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """Configuration for the LLM client.

    Settings can be configured via environment variables with SISYPHUS_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="SISYPHUS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = Field(
        default="http://localhost:4141",
        description="Base URL for the Copilot API proxy",
    )
    api_key: str = Field(
        default="dummy",
        description="API key (not used by Copilot API but required by SDK)",
    )
    model: str = Field(
        default="claude-opus-4.5",
        description="Model to use for completions",
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens in response",
        ge=1,
        le=100000,
    )
    timeout: float = Field(
        default=60.0,
        description="Request timeout in seconds",
        gt=0,
    )


class LLMClientError(Exception):
    """Base exception for LLM client errors."""


class LLMConnectionError(LLMClientError):
    """Raised when connection to the LLM API fails."""


class LLMAPIError(LLMClientError):
    """Raised when the LLM API returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LLMClient:
    """Wrapper around the Anthropic SDK for Copilot API.

    Provides a simplified interface for sending messages to the LLM
    with proper error handling and configuration management.
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        """Initialize the LLM client.

        Args:
            config: Optional configuration. If not provided, will be loaded
                from environment variables.
        """
        self.config = config or LLMConfig()
        self._client = anthropic.Anthropic(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
        )

    def send_message(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> anthropic.types.Message:
        """Send a message to the LLM and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system: Optional system prompt.
            tools: Optional list of tool definitions for tool use.
            model: Model to use (overrides config).
            max_tokens: Max tokens in response (overrides config).

        Returns:
            The Anthropic Message response object.

        Raises:
            LLMConnectionError: If connection to the API fails.
            LLMAPIError: If the API returns an error.
        """
        try:
            kwargs: dict[str, Any] = {
                "model": model or self.config.model,
                "max_tokens": max_tokens or self.config.max_tokens,
                "messages": messages,
            }
            if system is not None:
                kwargs["system"] = system
            if tools is not None:
                kwargs["tools"] = tools

            return cast(
                anthropic.types.Message, self._client.messages.create(**kwargs)
            )
        except anthropic.APIConnectionError as e:
            raise LLMConnectionError(
                f"Failed to connect to LLM API at {self.config.base_url}: {e}"
            ) from e
        except anthropic.APIStatusError as e:
            raise LLMAPIError(
                f"LLM API error: {e.message}",
                status_code=e.status_code,
            ) from e

    def stream_message(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """Stream a message response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system: Optional system prompt.
            tools: Optional list of tool definitions for tool use.
            model: Model to use (overrides config).
            max_tokens: Max tokens in response (overrides config).

        Yields:
            Text chunks as they arrive from the API.

        Raises:
            LLMConnectionError: If connection to the API fails.
            LLMAPIError: If the API returns an error.
        """
        try:
            kwargs: dict[str, Any] = {
                "model": model or self.config.model,
                "max_tokens": max_tokens or self.config.max_tokens,
                "messages": messages,
            }
            if system is not None:
                kwargs["system"] = system
            if tools is not None:
                kwargs["tools"] = tools

            with self._client.messages.stream(**kwargs) as stream:
                yield from stream.text_stream
        except anthropic.APIConnectionError as e:
            raise LLMConnectionError(
                f"Failed to connect to LLM API at {self.config.base_url}: {e}"
            ) from e
        except anthropic.APIStatusError as e:
            raise LLMAPIError(
                f"LLM API error: {e.message}",
                status_code=e.status_code,
            ) from e

    def get_text_response(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Send a message and return just the text content.

        Convenience method that extracts the text from the response.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system: Optional system prompt.
            model: Model to use (overrides config).
            max_tokens: Max tokens in response (overrides config).

        Returns:
            The text content of the response.

        Raises:
            LLMConnectionError: If connection to the API fails.
            LLMAPIError: If the API returns an error.
        """
        response = self.send_message(
            messages,
            system=system,
            model=model,
            max_tokens=max_tokens,
        )
        # Extract text from content blocks
        text_parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
        return "".join(text_parts)
