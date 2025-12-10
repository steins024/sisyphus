"""Sample test to verify pytest setup."""


def test_sample_message_fixture(sample_message: dict[str, str]) -> None:
    """Test that the sample_message fixture works."""
    assert sample_message["role"] == "user"
    assert sample_message["content"] == "Hello, world!"


def test_import_sisyphus() -> None:
    """Test that sisyphus can be imported."""
    import sisyphus

    assert sisyphus.__version__ == "0.1.0"
