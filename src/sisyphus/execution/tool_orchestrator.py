"""Tool orchestrator for managing tool execution workflows.

This module coordinates the execution of tool calls from LLM responses,
bridging between the response parser, tool registry, and tool executor.
"""

import json
from typing import Any

from sisyphus.core.tool import ToolNotFoundError
from sisyphus.core.tool_call import ToolCall, ToolCallResult
from sisyphus.execution.tool_executor import ToolExecutor
from sisyphus.registry.tool_registry import ToolRegistry


class ToolOrchestrator:
    """Orchestrates tool call execution from LLM responses.

    Manages the flow from parsed tool calls to execution results,
    handling errors and formatting results for LLM consumption.
    """

    def __init__(
        self, registry: ToolRegistry, executor: ToolExecutor | None = None
    ) -> None:
        """Initialize the tool orchestrator.

        Args:
            registry: ToolRegistry containing available tools
            executor: Optional ToolExecutor instance (creates default if None)
        """
        self.registry = registry
        self.executor = executor or ToolExecutor()

    def execute_tool_calls(
        self, tool_calls: list[ToolCall]
    ) -> list[ToolCallResult]:
        """Execute multiple tool calls and return results.

        Args:
            tool_calls: List of ToolCall objects to execute

        Returns:
            List of ToolCallResult objects, one for each tool call
        """
        results: list[ToolCallResult] = []
        for call in tool_calls:
            result = self.execute_single_tool_call(call)
            results.append(result)
        return results

    def execute_single_tool_call(self, tool_call: ToolCall) -> ToolCallResult:
        """Execute a single tool call and return the result.

        Args:
            tool_call: ToolCall object describing the tool to execute

        Returns:
            ToolCallResult with the execution result or error
        """
        try:
            # Check if tool exists in registry
            if not self.registry.has(tool_call.name):
                return ToolCallResult(
                    tool_use_id=tool_call.id,
                    content=f"Error: Tool '{tool_call.name}' not found in registry",
                    is_error=True,
                )

            # Get tool from registry
            tool = self.registry.get(tool_call.name)

            # Execute tool with provided parameters
            result = self.executor.execute(tool, **tool_call.input)

            # Format result for LLM
            if result.is_success:
                # Serialize result data as JSON for structured output
                if result.data is None:
                    content = "Success"
                elif isinstance(result.data, str):
                    content = result.data
                else:
                    content = json.dumps(result.data, indent=2)

                return ToolCallResult(
                    tool_use_id=tool_call.id,
                    content=content,
                    is_error=False,
                )
            else:
                # Tool execution failed
                return ToolCallResult(
                    tool_use_id=tool_call.id,
                    content=result.error_message or "Unknown error occurred",
                    is_error=True,
                )

        except ToolNotFoundError as e:
            return ToolCallResult(
                tool_use_id=tool_call.id,
                content=f"Tool not found: {e}",
                is_error=True,
            )
        except Exception as e:
            # Catch any unexpected errors during execution
            return ToolCallResult(
                tool_use_id=tool_call.id,
                content=f"Execution error: {type(e).__name__}: {e}",
                is_error=True,
            )

    def format_results_for_llm(
        self, results: list[ToolCallResult]
    ) -> list[dict[str, Any]]:
        """Convert tool results to Anthropic message format.

        Args:
            results: List of ToolCallResult objects

        Returns:
            List of tool_result content blocks for Anthropic API
        """
        return [result.to_anthropic_format() for result in results]
