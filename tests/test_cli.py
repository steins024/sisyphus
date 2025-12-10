"""Tests for the CLI module."""

import pytest
from typer.testing import CliRunner

from sisyphus.core import Conversation
from sisyphus.ui.cli import SPECIAL_COMMANDS, app, handle_special_command

runner = CliRunner()


class TestSpecialCommands:
    """Tests for special command handling."""

    def test_special_commands_defined(self) -> None:
        """Test that all expected special commands are defined."""
        assert "/exit" in SPECIAL_COMMANDS
        assert "/quit" in SPECIAL_COMMANDS
        assert "/clear" in SPECIAL_COMMANDS
        assert "/help" in SPECIAL_COMMANDS

    def test_handle_exit_command(self) -> None:
        """Test /exit command raises Exit."""
        import typer

        conv = Conversation()
        with pytest.raises(typer.Exit):
            handle_special_command("/exit", conv)

    def test_handle_quit_command(self) -> None:
        """Test /quit command raises Exit."""
        import typer

        conv = Conversation()
        with pytest.raises(typer.Exit):
            handle_special_command("/quit", conv)

    def test_handle_clear_command(self) -> None:
        """Test /clear command clears conversation."""
        conv = Conversation()
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi!")
        assert len(conv) == 2

        result = handle_special_command("/clear", conv)
        assert result is True
        assert len(conv) == 0

    def test_handle_help_command(self) -> None:
        """Test /help command returns True."""
        conv = Conversation()
        result = handle_special_command("/help", conv)
        assert result is True

    def test_handle_unknown_command(self) -> None:
        """Test unknown command returns False."""
        conv = Conversation()
        result = handle_special_command("/unknown", conv)
        assert result is False

    def test_command_case_insensitive(self) -> None:
        """Test that commands are case insensitive."""
        import typer

        conv = Conversation()
        with pytest.raises(typer.Exit):
            handle_special_command("/EXIT", conv)

    def test_command_with_whitespace(self) -> None:
        """Test that commands work with surrounding whitespace."""
        import typer

        conv = Conversation()
        with pytest.raises(typer.Exit):
            handle_special_command("  /exit  ", conv)


class TestCLI:
    """Tests for CLI app."""

    def test_app_help(self) -> None:
        """Test that --help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "sisyphus" in result.output.lower() or "usage" in result.output.lower()

    def test_chat_help(self) -> None:
        """Test that chat --help works."""
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "chat" in result.output.lower()

    def test_version_command(self) -> None:
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_no_args_shows_help(self) -> None:
        """Test that running with no args shows help."""
        result = runner.invoke(app, [])
        # Typer returns exit code 0 when showing help with no_args_is_help=True
        # and the output contains usage information
        assert "Usage" in result.output or "usage" in result.output
