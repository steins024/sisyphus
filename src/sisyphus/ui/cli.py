"""CLI REPL interface for Sisyphus."""

from typing import Annotated

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from sisyphus.core import Conversation
from sisyphus.llm import LLMAPIError, LLMClient, LLMConfig, LLMConnectionError

app = typer.Typer(
    name="sisyphus",
    help="AI Agent Framework supporting chat completion, tool use, and more.",
    no_args_is_help=True,
)
console = Console()

# Special commands
SPECIAL_COMMANDS: dict[str, str] = {
    "/exit": "Exit the chat",
    "/quit": "Exit the chat (alias for /exit)",
    "/clear": "Clear conversation history",
    "/help": "Show available commands",
}


def handle_special_command(cmd: str, conversation: Conversation) -> bool:
    """Handle special commands.

    Args:
        cmd: The command string (e.g., "/exit").
        conversation: The current conversation.

    Returns:
        True if command was handled, False otherwise.

    Raises:
        typer.Exit: When /exit or /quit is called.
    """
    cmd_lower = cmd.strip().lower()

    if cmd_lower in ("/exit", "/quit"):
        console.print("\n[dim]Goodbye![/dim]")
        raise typer.Exit()
    elif cmd_lower == "/clear":
        conversation.clear()
        console.print("[dim]Conversation cleared.[/dim]\n")
        return True
    elif cmd_lower == "/help":
        console.print("\n[bold]Available Commands:[/bold]")
        for command, desc in SPECIAL_COMMANDS.items():
            console.print(f"  [cyan]{command}[/cyan]: {desc}")
        console.print()
        return True

    return False


def stream_response(
    client: LLMClient,
    conversation: Conversation,
    use_markdown: bool = True,
) -> str:
    """Stream response from LLM with live display.

    Args:
        client: The LLM client.
        conversation: The current conversation with messages.
        use_markdown: Whether to render as markdown.

    Returns:
        The complete response text.
    """
    response_text = ""
    messages = conversation.to_api_format()
    system = conversation.system_prompt

    if use_markdown:
        with Live(
            Markdown(""),
            refresh_per_second=10,
            console=console,
            vertical_overflow="visible",
        ) as live:
            for chunk in client.stream_message(messages, system=system):
                response_text += chunk
                live.update(Markdown(response_text))
    else:
        console.print("[bold blue]Assistant:[/bold blue] ", end="")
        for chunk in client.stream_message(messages, system=system):
            response_text += chunk
            console.print(chunk, end="")
        console.print()

    return response_text


@app.command()
def chat(
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Model to use for completions"),
    ] = None,
    system: Annotated[
        str | None,
        typer.Option("--system", "-s", help="System prompt"),
    ] = None,
    no_markdown: Annotated[
        bool,
        typer.Option("--no-markdown", help="Disable markdown rendering"),
    ] = False,
) -> None:
    """Start an interactive chat session.

    Chat with the LLM in a REPL-style interface. Messages are streamed
    in real-time with markdown rendering.

    Special commands:
        /exit, /quit - Exit the chat
        /clear - Clear conversation history
        /help - Show available commands
    """
    # Build config
    config = LLMConfig()
    if model:
        config = LLMConfig(model=model)

    try:
        client = LLMClient(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize LLM client:[/red] {e}")
        raise typer.Exit(1) from e

    conversation = Conversation(system_prompt=system)

    # Welcome message
    console.print(
        Panel(
            "[bold]Sisyphus Chat[/bold]\n"
            f"Model: [cyan]{config.model}[/cyan]\n"
            "Type [cyan]/help[/cyan] for commands, [cyan]Ctrl+C[/cyan] to exit",
            title="Welcome",
            border_style="blue",
        )
    )
    console.print()

    # Main REPL loop
    while True:
        try:
            # Get user input
            user_input = console.input("[bold green]You:[/bold green] ")

            # Skip empty input
            if not user_input.strip():
                continue

            # Check for special commands
            if user_input.strip().startswith("/") and handle_special_command(
                user_input, conversation
            ):
                continue

            # Add user message
            conversation.add_user_message(user_input)

            # Get and display response
            console.print()
            try:
                response_text = stream_response(
                    client, conversation, use_markdown=not no_markdown
                )
                conversation.add_assistant_message(response_text)
            except LLMConnectionError as e:
                console.print(f"\n[red]Connection error:[/red] {e}")
                console.print(
                    "[dim]Make sure the Copilot API proxy is running "
                    "(npx copilot-api@latest start --port 4141)[/dim]\n"
                )
                # Remove the user message since we didn't get a response
                conversation.messages.pop()
                continue
            except LLMAPIError as e:
                console.print(f"\n[red]API error ({e.status_code}):[/red] {e}")
                # Remove the user message since we didn't get a response
                conversation.messages.pop()
                continue

            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            raise typer.Exit() from None
        except EOFError:
            # Handle Ctrl+D
            console.print("\n[dim]Goodbye![/dim]")
            raise typer.Exit() from None


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold]Sisyphus[/bold] v0.1.0")


if __name__ == "__main__":
    app()
