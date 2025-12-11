"""CLI REPL interface for Sisyphus."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from sisyphus.core import Conversation
from sisyphus.execution.tool_orchestrator import ToolOrchestrator
from sisyphus.llm import LLMAPIError, LLMClient, LLMConfig, LLMConnectionError
from sisyphus.llm.response_parser import (
    extract_text_content,
    has_tool_calls,
    message_to_dict,
    parse_tool_calls,
)
from sisyphus.llm.tool_formatter import format_tools_for_anthropic
from sisyphus.registry.tool_registry import ToolRegistry

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
    "/tools": "List available tools",
}


def handle_special_command(
    cmd: str, conversation: Conversation, registry: ToolRegistry | None = None
) -> bool:
    """Handle special commands.

    Args:
        cmd: The command string (e.g., "/exit").
        conversation: The current conversation.
        registry: Optional tool registry for /tools command.

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
    elif cmd_lower == "/tools":
        if registry is None:
            console.print("[yellow]Tool registry not initialized.[/yellow]\n")
            return True
        tools = registry.list()
        if not tools:
            console.print("[dim]No tools registered.[/dim]\n")
        else:
            console.print("\n[bold]Available Tools:[/bold]")
            for tool_name in tools:
                definition = registry.get_definition(tool_name)
                if definition:
                    console.print(
                        f"  [cyan]{tool_name}[/cyan]: {definition.description}"
                    )
            console.print()
        return True

    return False


def handle_message_with_tools(
    client: LLMClient,
    conversation: Conversation,
    registry: ToolRegistry,
    orchestrator: ToolOrchestrator,
    user_input: str,
) -> str:
    """Handle a user message with full tool use support.

    This implements the tool use loop:
    1. Send message to LLM with tools
    2. If LLM wants to use tools, execute them
    3. Send results back to LLM
    4. Repeat until LLM responds with text

    Args:
        client: The LLM client
        conversation: The current conversation
        registry: Tool registry with available tools
        orchestrator: Tool orchestrator for execution
        user_input: The user's message

    Returns:
        The final text response from the assistant

    Raises:
        LLMConnectionError: If connection fails
        LLMAPIError: If API returns an error
    """
    # Add user message to conversation
    conversation.add_user_message(user_input)

    # Format tools for API
    tools = format_tools_for_anthropic(registry)

    # Tool use loop (max 5 iterations to prevent infinite loops)
    max_iterations = 5
    for iteration in range(max_iterations):
        # Call LLM
        response = client.send_message(
            conversation.to_api_format(),
            system=conversation.system_prompt,
            tools=tools if tools else None,
        )

        # Check if response contains tool calls
        if not has_tool_calls(response):
            # No tool use - extract text and return
            text = extract_text_content(response)
            conversation.add_assistant_message(text)
            return text

        # Response has tool calls - show indicator
        tool_calls = parse_tool_calls(response)
        console.print(
            f"[dim]🔧 Using {len(tool_calls)} tool(s)...[/dim]",
            end=" ",
        )

        # Add assistant message with tool use to conversation
        response_dict = message_to_dict(response)
        conversation.add_structured_message(
            response_dict["role"], response_dict["content"]
        )

        # Execute tools
        tool_results = orchestrator.execute_tool_calls(tool_calls)

        # Show completion
        console.print("[dim]✓[/dim]")

        # Format results for LLM
        result_blocks = orchestrator.format_results_for_llm(tool_results)

        # Add tool results to conversation
        conversation.add_tool_result_message(result_blocks)

    # Max iterations reached
    error_msg = "Error: Maximum tool use iterations reached"
    conversation.add_assistant_message(error_msg)
    return error_msg


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

    # Initialize tool registry and register built-in tools
    registry = ToolRegistry.get_instance()
    # Tools are at project root: config/tools
    # __file__ is at: src/sisyphus/ui/cli.py
    # So we need to go up 4 levels: cli.py -> ui -> sisyphus -> src -> project_root
    tools_dir = Path(__file__).parent.parent.parent.parent / "config" / "tools"

    try:
        if tools_dir.exists():
            registered = registry.register_from_yaml_directory(str(tools_dir))
            tools_count = len(registered)
        else:
            tools_count = 0
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to register tools:[/yellow] {e}")
        tools_count = 0

    # Create tool orchestrator for executing tool calls
    orchestrator = ToolOrchestrator(registry)

    # Welcome message
    tools_msg = (
        f"Tools: [cyan]{tools_count} registered[/cyan]\n"
        if tools_count > 0
        else ""
    )
    console.print(
        Panel(
            "[bold]Sisyphus Chat[/bold]\n"
            f"Model: [cyan]{config.model}[/cyan]\n"
            f"{tools_msg}"
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
                user_input, conversation, registry
            ):
                continue

            # Get and display response with tool support
            console.print()
            try:
                response_text = handle_message_with_tools(
                    client, conversation, registry, orchestrator, user_input
                )
                # Display the response
                if not no_markdown:
                    console.print(Markdown(response_text))
                else:
                    console.print(f"[bold blue]Assistant:[/bold blue] {response_text}")
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
