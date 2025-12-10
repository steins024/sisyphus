"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_message() -> dict[str, str]:
    """Sample message fixture for testing."""
    return {"role": "user", "content": "Hello, world!"}
