# Tool Registration System

This document provides a comprehensive guide to the tool registration system in Sisyphus, covering tool definitions, registration methods, dynamic handler resolution, and usage patterns.

---

## Table of Contents

1. [Overview](#overview)
2. [Tool Protocol Interface](#tool-protocol-interface)
3. [Tool Definition Format](#tool-definition-format)
4. [Registration Methods](#registration-methods)
5. [Dynamic Handler Resolution](#dynamic-handler-resolution)
6. [Tool Registry API](#tool-registry-api)
7. [Usage Patterns](#usage-patterns)
8. [Design Decisions](#design-decisions)
9. [Examples](#examples)

---

## Overview

The Sisyphus tool system provides a flexible, protocol-based architecture for defining and registering executable actions that agents, subagents, and skills can invoke. The system consists of three main components:

1. **Tool Protocol** - Defines the interface that all tools must implement
2. **Tool Definition** - Declarative YAML-based tool configuration
3. **Tool Registry** - Centralized singleton registry for managing tool instances

### Key Design Principles

- **Protocol-based**: Uses `typing.Protocol` for flexible implementations without inheritance
- **Async-first**: Supports both synchronous and asynchronous execution patterns
- **Type-safe**: Strict typing with Pydantic validation
- **Configuration-driven**: Tools can be defined via YAML files or programmatically
- **Reusable**: Designed for use across agents, subagents, and skills
- **Thread-safe**: Registry operations use locks to ensure thread safety

---

## Tool Protocol Interface

### Tool Protocol

All tools must implement the `Tool` protocol, which defines the minimum interface:

```python
from typing import Protocol, Any
from sisyphus.core.tool import ToolResult

class Tool(Protocol):
    """Protocol defining the interface for all tools."""

    @property
    def name(self) -> str:
        """Unique identifier for this tool (e.g., 'read_file')."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description for LLM context."""
        ...

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema describing the tool's parameters."""
        ...

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool synchronously."""
        ...
```

### AsyncTool Protocol

For tools that require asynchronous execution (I/O-bound operations):

```python
class AsyncTool(Protocol):
    """Protocol for tools that support async execution."""

    @property
    def name(self) -> str:
        ...

    @property
    def description(self) -> str:
        ...

    @property
    def parameters(self) -> dict[str, Any]:
        ...

    async def execute_async(self, **kwargs: Any) -> ToolResult:
        """Execute the tool asynchronously."""
        ...
```

### ToolResult

All tool executions return a standardized `ToolResult`:

```python
@dataclass
class ToolResult:
    status: ToolStatus  # SUCCESS, ERROR, TIMEOUT, CANCELLED
    data: Any = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == ToolStatus.SUCCESS

    @classmethod
    def success(cls, data: Any = None, **metadata: Any) -> "ToolResult":
        """Create a successful result."""
        ...

    @classmethod
    def error(cls, error: str, **metadata: Any) -> "ToolResult":
        """Create an error result."""
        ...
```

**Example:**
```python
# Success case
result = ToolResult.success(data={"content": "file contents"}, duration=0.5)

# Error case
result = ToolResult.error(error="File not found", path="/invalid/path")
```

---

## Tool Definition Format

Tools can be defined declaratively using YAML files. The `ToolDefinition` Pydantic model validates these definitions.

### YAML Structure

```yaml
name: tool_name                # Required: snake_case identifier
description: Tool description  # Required: Human-readable description
parameters:                    # Required: JSON Schema object
  type: object
  properties:
    param_name:
      type: string
      description: Parameter description
  required:
    - param_name
handler: module.path.function  # Required: Python module path to handler
timeout: 30.0                  # Optional: Timeout in seconds
async: false                   # Optional: Whether handler is async
metadata:                      # Optional: Custom metadata
  version: "1.0"
  author: "author_name"
```

### Field Specifications

#### `name` (required)
- **Type**: `string`
- **Pattern**: `^[a-z][a-z0-9_]*$` (lowercase, starting with letter, underscores allowed)
- **Description**: Unique identifier for the tool
- **Examples**: `read_file`, `terminal_exec`, `search_web`

#### `description` (required)
- **Type**: `string`
- **Min length**: 1
- **Description**: Human-readable explanation of what the tool does
- **Purpose**: Included in LLM context to help the agent understand when to use the tool

#### `parameters` (required)
- **Type**: `object` (JSON Schema)
- **Required fields**: `type`, `properties`
- **Constraints**:
  - `type` must be `"object"`
  - `properties` must be a dictionary
  - Can include `required` array for required parameters
- **Purpose**: Defines the tool's input schema for validation

#### `handler` (required)
- **Type**: `string`
- **Format**: `module.submodule.function_name`
- **Description**: Python module path to the handler function
- **Examples**:
  - `sisyphus.tools.filesystem.read_file`
  - `tools.custom.my_handler`
- **Constraints**: Must contain at least one dot

#### `timeout` (optional)
- **Type**: `float`
- **Constraints**: Must be > 0
- **Description**: Maximum execution time in seconds
- **Default**: `None` (no timeout)

#### `async` (optional)
- **Type**: `boolean`
- **Description**: Whether the handler is an async function
- **Default**: `false`
- **Note**: Uses the alias `async_handler` internally (Python keyword)

#### `metadata` (optional)
- **Type**: `object`
- **Description**: Arbitrary metadata for tool-specific configuration
- **Default**: `{}`

### Validation Rules

The `ToolDefinition` model enforces these validations:

1. **Name validation**: Must match pattern `^[a-z][a-z0-9_]*$`
2. **Description validation**: Cannot be empty
3. **Parameters validation**:
   - Must have `type: object`
   - Must have `properties` field (dict)
4. **Handler validation**: Must contain at least one dot (module.function format)
5. **Timeout validation**: If provided, must be > 0

---

## Registration Methods

The `ToolRegistry` singleton provides multiple ways to register tools.

### Method 1: Direct Registration

Register a tool instance that implements the `Tool` or `AsyncTool` protocol:

```python
from sisyphus.registry import ToolRegistry

registry = ToolRegistry.get_instance()

# Create a tool instance
class MyTool:
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "My custom tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            }
        }

    def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult.success(data=kwargs.get("input"))

tool = MyTool()
registry.register(tool)
```

**Parameters:**
- `tool`: Tool instance implementing `Tool` or `AsyncTool` protocol
- `allow_override`: If `True`, allows replacing existing tools (default: `False`)

**Raises:**
- `ToolRegistrationError`: If tool with same name already registered (and `allow_override=False`)

---

### Method 2: Register from Definition

Register a tool from a `ToolDefinition` object (programmatic definition):

```python
from sisyphus.core.tool import ToolDefinition

definition = ToolDefinition(
    name="read_file",
    description="Read contents of a file",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file"
            }
        },
        "required": ["file_path"]
    },
    handler="sisyphus.tools.filesystem.read_file"
)

registry.register_from_definition(definition)
```

**Parameters:**
- `definition`: `ToolDefinition` object with tool configuration
- `allow_override`: If `True`, allows replacing existing tools (default: `False`)

**Behavior:**
1. Validates the definition (automatic via Pydantic)
2. Resolves the handler function from the module path
3. Creates a wrapper that implements `Tool` or `AsyncTool`
4. Registers the wrapper in the registry

**Raises:**
- `ToolRegistrationError`: If handler cannot be imported or instantiation fails

---

### Method 3: Register from YAML File

Load a tool from a YAML definition file:

```python
from pathlib import Path

yaml_path = Path("config/tools/read_file.yaml")
registry.register_from_yaml(yaml_path)
```

**Parameters:**
- `yaml_path`: Path to YAML file containing tool definition
- `allow_override`: If `True`, allows replacing existing tools (default: `False`)

**Behavior:**
1. Reads and parses the YAML file
2. Validates the structure via `ToolDefinition`
3. Calls `register_from_definition()` internally

**Raises:**
- `ToolRegistrationError`: If YAML is invalid, missing required fields, or registration fails

---

### Method 4: Register from Directory

Batch-load all tools from a directory of YAML files:

```python
from pathlib import Path

tools_dir = Path("config/tools")
registered_names = registry.register_from_yaml_directory(tools_dir)
print(f"Registered tools: {registered_names}")
```

**Parameters:**
- `directory`: Path to directory containing YAML files
- `pattern`: Glob pattern for file matching (default: `"*.yaml"`)
- `allow_override`: If `True`, allows replacing existing tools (default: `False`)

**Returns:**
- `list[str]`: Names of successfully registered tools

**Behavior:**
1. Scans directory for files matching the pattern
2. Attempts to register each file via `register_from_yaml()`
3. Collects errors and raises if any fail

**Raises:**
- `ToolRegistrationError`: If directory doesn't exist or if any registration fails

**Example with custom pattern:**
```python
# Load only .yml files
registered = registry.register_from_yaml_directory(
    Path("config/tools"),
    pattern="*.yml"
)
```

---

## Dynamic Handler Resolution

The registry uses dynamic handler resolution to instantiate tools from YAML definitions. This allows tools to be defined declaratively without manual instantiation code.

### Resolution Process

When you call `register_from_definition()` or `register_from_yaml()`:

1. **Parse Handler Path**
   ```python
   handler_path = "sisyphus.tools.filesystem.read_file"
   # Split: module_path = "sisyphus.tools.filesystem"
   #        function_name = "read_file"
   ```

2. **Import Module**
   ```python
   import importlib
   module = importlib.import_module("sisyphus.tools.filesystem")
   ```

3. **Get Handler Function**
   ```python
   handler = getattr(module, "read_file")
   # Verify it's callable
   ```

4. **Create Wrapper**
   ```python
   # For sync handlers
   tool = _SyncToolWrapper(definition, handler)

   # For async handlers
   tool = _AsyncToolWrapper(definition, handler)
   ```

5. **Register Wrapper**
   ```python
   registry._tools[definition.name] = tool
   ```

### Handler Function Signature

Handler functions must follow this signature:

**Synchronous:**
```python
def my_handler(**kwargs: Any) -> ToolResult:
    """Handler implementation."""
    # kwargs matches the parameters defined in tool definition
    result = do_something(kwargs["param1"], kwargs["param2"])
    return ToolResult.success(data=result)
```

**Asynchronous:**
```python
async def my_async_handler(**kwargs: Any) -> ToolResult:
    """Async handler implementation."""
    result = await do_something_async(kwargs["param1"])
    return ToolResult.success(data=result)
```

### Internal Wrapper Classes

The registry uses internal wrapper classes to adapt handler functions to the Tool protocol:

```python
class _SyncToolWrapper:
    """Wrapper for synchronous handlers."""

    def __init__(self, definition: ToolDefinition, handler: SyncToolHandler):
        self._definition = definition
        self._handler = handler

    @property
    def name(self) -> str:
        return self._definition.name

    @property
    def description(self) -> str:
        return self._definition.description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._definition.parameters

    def execute(self, **kwargs: Any) -> ToolResult:
        return self._handler(**kwargs)


class _AsyncToolWrapper:
    """Wrapper for asynchronous handlers."""

    def __init__(self, definition: ToolDefinition, handler: AsyncToolHandler):
        self._definition = definition
        self._handler = handler

    @property
    def name(self) -> str:
        return self._definition.name

    @property
    def description(self) -> str:
        return self._definition.description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._definition.parameters

    async def execute_async(self, **kwargs: Any) -> ToolResult:
        return await self._handler(**kwargs)
```

### Error Handling

If handler resolution fails, a `ToolRegistrationError` is raised with details:

```python
try:
    registry.register_from_definition(definition)
except ToolRegistrationError as e:
    print(f"Failed to register tool: {e}")
    print(f"Tool name: {e.tool_name}")
```

Common failure reasons:
- Module not found (`ImportError`)
- Function not found in module (`AttributeError`)
- Handler is not callable (`TypeError`)

---

## Tool Registry API

### Singleton Access

```python
from sisyphus.registry import ToolRegistry

# Get singleton instance
registry = ToolRegistry.get_instance()

# Reset singleton (mainly for testing)
ToolRegistry.reset_instance()
```

### Registration Methods

| Method | Purpose | Parameters |
|--------|---------|------------|
| `register(tool, allow_override=False)` | Register a tool instance | Tool instance |
| `register_from_definition(definition, allow_override=False)` | Register from ToolDefinition | ToolDefinition object |
| `register_from_yaml(yaml_path, allow_override=False)` | Register from YAML file | Path to YAML file |
| `register_from_yaml_directory(directory, pattern="*.yaml", allow_override=False)` | Batch register from directory | Directory path, glob pattern |

### Retrieval Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `get(name)` | Get tool by name | Tool instance |
| `get_definition(name)` | Get tool definition | ToolDefinition or None |
| `has(name)` | Check if tool exists | bool |
| `list()` | List all tool names | list[str] (sorted) |
| `list_tools()` | List all tool instances | list[Tool \| AsyncTool] |
| `items()` | Get name-instance pairs | list[tuple[str, Tool \| AsyncTool]] |

### Management Methods

| Method | Purpose |
|--------|---------|
| `unregister(name)` | Remove a tool from registry |
| `clear()` | Remove all tools from registry |

### Thread Safety

All registry operations are thread-safe. The registry uses two levels of locking:

1. **Class-level lock**: For singleton instantiation
2. **Instance-level lock**: For registry operations (register, get, unregister, etc.)

```python
import threading

def register_tool(i):
    registry = ToolRegistry.get_instance()
    registry.register(create_tool(i))

threads = [threading.Thread(target=register_tool, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
# All registrations succeed safely
```

---

## Usage Patterns

### Pattern 1: Agent Initialization

Load all tools at agent startup:

```python
from pathlib import Path
from sisyphus.registry import ToolRegistry

def initialize_agent():
    registry = ToolRegistry.get_instance()

    # Load all tools from config directory
    tools_dir = Path("config/tools")
    tool_names = registry.register_from_yaml_directory(tools_dir)

    print(f"Loaded {len(tool_names)} tools: {', '.join(tool_names)}")

    return registry
```

### Pattern 2: Subagent with Tool Subset

Subagents register only a filtered subset of tools:

```python
def create_subagent(allowed_tools: list[str]):
    # Get the main registry
    main_registry = ToolRegistry.get_instance()

    # Create a new registry for the subagent
    ToolRegistry.reset_instance()
    subagent_registry = ToolRegistry.get_instance()

    # Register only allowed tools
    for tool_name in allowed_tools:
        if main_registry.has(tool_name):
            tool = main_registry.get(tool_name)
            subagent_registry.register(tool, allow_override=True)

    return subagent_registry
```

### Pattern 3: Dynamic Tool Discovery

List available tools and their capabilities:

```python
def list_available_tools():
    registry = ToolRegistry.get_instance()

    for name, tool in registry.items():
        print(f"\nTool: {name}")
        print(f"Description: {tool.description}")
        print(f"Parameters: {tool.parameters}")
```

### Pattern 4: Tool Execution

Execute a tool by name:

```python
def execute_tool(tool_name: str, **params):
    registry = ToolRegistry.get_instance()

    if not registry.has(tool_name):
        return ToolResult.error(error=f"Tool '{tool_name}' not found")

    tool = registry.get(tool_name)

    # Check if async
    if isinstance(tool, AsyncTool):
        # Run in async context
        import asyncio
        return asyncio.run(tool.execute_async(**params))
    else:
        return tool.execute(**params)
```

### Pattern 5: Override Built-in Tool

Replace a built-in tool with a custom implementation:

```python
# Define custom implementation
class CustomReadFile:
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Custom file reader with caching"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"file_path": {"type": "string"}}}

    def execute(self, **kwargs) -> ToolResult:
        # Custom implementation with caching
        ...

# Override existing tool
registry = ToolRegistry.get_instance()
registry.register(CustomReadFile(), allow_override=True)
```

---

## Design Decisions

### 1. Protocol-Based Design

**Decision**: Use `typing.Protocol` instead of abstract base classes.

**Rationale**:
- Allows "duck typing" - any class with matching methods conforms
- No inheritance required - tools can be plain classes
- More Pythonic and flexible
- Easier to integrate third-party tools

**Tradeoff**: Less explicit inheritance hierarchy, but greater flexibility.

---

### 2. Singleton Registry

**Decision**: Use singleton pattern for `ToolRegistry`.

**Rationale**:
- Ensures single source of truth for registered tools
- Simplifies access - no need to pass registry around
- Matches typical usage pattern (one registry per process)

**Tradeoff**: Global state can make testing harder (addressed with `reset_instance()`).

---

### 3. YAML Configuration

**Decision**: Support declarative tool definitions via YAML files.

**Rationale**:
- Separation of configuration from code
- Easier to add/modify tools without code changes
- Human-readable format
- Standard configuration format

**Tradeoff**: Additional parsing/validation layer, but worth it for maintainability.

---

### 4. Dynamic Handler Resolution

**Decision**: Resolve handler functions at runtime via `importlib`.

**Rationale**:
- Enables declarative tool definitions
- Allows tools to be defined in any module
- No need to import handler modules manually
- Supports plugin architecture

**Tradeoff**: Errors caught at runtime rather than import time, but validation helps.

---

### 5. Async-First with Sync Support

**Decision**: Provide both `Tool` and `AsyncTool` protocols.

**Rationale**:
- Many tools involve I/O (files, network, etc.) - benefit from async
- Some tools are purely computational - no benefit from async
- Allow tools to choose the right execution model
- Future-proof for async agent architectures

**Tradeoff**: Slightly more complex API, but necessary for performance.

---

### 6. ToolResult Standardization

**Decision**: All tools return `ToolResult` with status, data, error, metadata.

**Rationale**:
- Consistent error handling across all tools
- Structured result format easy to process
- Metadata allows tools to provide execution context (timing, etc.)
- Clear success/failure semantics

**Tradeoff**: More structured than raw return values, but improves reliability.

---

### 7. Pydantic Validation

**Decision**: Use Pydantic for `ToolDefinition` validation.

**Rationale**:
- Type-safe parsing of YAML/dict data
- Automatic validation with clear error messages
- JSON Schema generation support
- Consistent with modern Python best practices

**Tradeoff**: Adds dependency, but worth it for validation and type safety.

---

### 8. Thread-Safe Operations

**Decision**: Make all registry operations thread-safe with locks.

**Rationale**:
- Agents may use threads for concurrent tool execution
- Prevents race conditions in multi-threaded environments
- Small performance cost, large safety gain

**Tradeoff**: Slight overhead from locking, but necessary for correctness.

---

## Examples

### Example 1: Complete Tool Definition (YAML)

**File**: `config/tools/read_file.yaml`

```yaml
name: read_file
description: Read the contents of a file from the filesystem
parameters:
  type: object
  properties:
    file_path:
      type: string
      description: The absolute path to the file to read
    encoding:
      type: string
      description: The file encoding (default is utf-8)
      default: utf-8
    start_line:
      type: integer
      description: Start reading from this line (1-indexed)
    end_line:
      type: integer
      description: Stop reading at this line (1-indexed, inclusive)
  required:
    - file_path
handler: sisyphus.tools.filesystem.read_file
timeout: 30.0
metadata:
  version: "1.0"
  category: "filesystem"
```

**Handler Implementation**: `sisyphus/tools/filesystem.py`

```python
from pathlib import Path
from sisyphus.core.tool import ToolResult

def read_file(**kwargs) -> ToolResult:
    """Read file handler."""
    try:
        file_path = Path(kwargs["file_path"])
        encoding = kwargs.get("encoding", "utf-8")
        start_line = kwargs.get("start_line")
        end_line = kwargs.get("end_line")

        if not file_path.exists():
            return ToolResult.error(
                error=f"File not found: {file_path}",
                path=str(file_path)
            )

        with file_path.open("r", encoding=encoding) as f:
            lines = f.readlines()

        # Apply line range if specified
        if start_line is not None and end_line is not None:
            lines = lines[start_line-1:end_line]

        content = "".join(lines)

        return ToolResult.success(
            data={"content": content, "lines": len(lines)},
            path=str(file_path),
            duration=0.1
        )

    except Exception as e:
        return ToolResult.error(
            error=f"Failed to read file: {e}",
            exception=str(type(e).__name__)
        )
```

---

### Example 2: Async Tool Definition (YAML)

**File**: `config/tools/fetch_url.yaml`

```yaml
name: fetch_url
description: Fetch content from a URL via HTTP/HTTPS
parameters:
  type: object
  properties:
    url:
      type: string
      description: The URL to fetch
    method:
      type: string
      description: HTTP method (GET, POST, etc.)
      default: GET
    headers:
      type: object
      description: HTTP headers as key-value pairs
    timeout:
      type: number
      description: Request timeout in seconds
      default: 30.0
  required:
    - url
handler: sisyphus.tools.network.fetch_url
timeout: 60.0
async: true
metadata:
  version: "1.0"
  category: "network"
```

**Handler Implementation**: `sisyphus/tools/network.py`

```python
import httpx
from sisyphus.core.tool import ToolResult

async def fetch_url(**kwargs) -> ToolResult:
    """Async URL fetch handler."""
    try:
        url = kwargs["url"]
        method = kwargs.get("method", "GET")
        headers = kwargs.get("headers", {})
        timeout = kwargs.get("timeout", 30.0)

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout
            )

            response.raise_for_status()

            return ToolResult.success(
                data={
                    "content": response.text,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                },
                url=url,
                duration=response.elapsed.total_seconds()
            )

    except httpx.HTTPError as e:
        return ToolResult.error(
            error=f"HTTP error: {e}",
            url=url,
            exception=str(type(e).__name__)
        )

    except Exception as e:
        return ToolResult.error(
            error=f"Failed to fetch URL: {e}",
            exception=str(type(e).__name__)
        )
```

---

### Example 3: Tool with Complex Parameters (YAML)

**File**: `config/tools/search_code.yaml`

```yaml
name: search_code
description: Search for code patterns in the codebase using regex
parameters:
  type: object
  properties:
    pattern:
      type: string
      description: Regular expression pattern to search for
    directory:
      type: string
      description: Directory to search in
    file_extensions:
      type: array
      description: File extensions to include (e.g., [".py", ".js"])
      items:
        type: string
    case_sensitive:
      type: boolean
      description: Whether the search is case-sensitive
      default: true
    max_results:
      type: integer
      description: Maximum number of results to return
      default: 100
    include_context:
      type: boolean
      description: Include surrounding lines as context
      default: false
    context_lines:
      type: integer
      description: Number of context lines before and after match
      default: 2
  required:
    - pattern
    - directory
handler: sisyphus.tools.search.search_code
timeout: 60.0
metadata:
  version: "1.0"
  category: "search"
```

---

### Example 4: Complete Registration and Usage

```python
from pathlib import Path
from sisyphus.registry import ToolRegistry
from sisyphus.core.tool import ToolResult

def main():
    # Initialize registry
    registry = ToolRegistry.get_instance()

    # Load all tools from config directory
    config_dir = Path("config/tools")
    tool_names = registry.register_from_yaml_directory(config_dir)

    print(f"Registered {len(tool_names)} tools:")
    for name in tool_names:
        tool = registry.get(name)
        print(f"  - {name}: {tool.description}")

    # Execute a tool
    if registry.has("read_file"):
        tool = registry.get("read_file")
        result = tool.execute(file_path="/path/to/file.txt")

        if result.is_success:
            print(f"File content: {result.data['content']}")
        else:
            print(f"Error: {result.error_message}")

    # Get tool definition
    definition = registry.get_definition("read_file")
    if definition:
        print(f"\nTool metadata: {definition.metadata}")
        print(f"Timeout: {definition.timeout}s")

if __name__ == "__main__":
    main()
```

---

### Example 5: Subagent Tool Filtering

```python
from sisyphus.registry import ToolRegistry

def create_researcher_subagent():
    """Create a subagent with limited tool access."""
    main_registry = ToolRegistry.get_instance()

    # Define allowed tools for researcher
    allowed_tools = [
        "search_code",
        "read_file",
        "fetch_url",
        "search_web"
    ]

    # Create filtered tool list
    subagent_tools = []
    for tool_name in allowed_tools:
        if main_registry.has(tool_name):
            subagent_tools.append(main_registry.get(tool_name))

    print(f"Researcher has access to {len(subagent_tools)} tools")

    return subagent_tools
```

---

## Summary

The Sisyphus tool registration system provides a robust, flexible foundation for defining and managing executable tools. Key takeaways:

1. **Flexible Definition**: Tools can be defined programmatically or via YAML
2. **Multiple Registration Methods**: Direct, definition-based, file-based, or directory-based
3. **Dynamic Resolution**: Handlers are resolved at runtime for maximum flexibility
4. **Type Safety**: Pydantic validation ensures correct configuration
5. **Protocol-Based**: No inheritance required - any matching class works
6. **Thread-Safe**: Safe for concurrent access in multi-threaded environments
7. **Async Support**: First-class support for both sync and async tools

This architecture enables:
- Easy addition of new tools without code changes
- Tool reuse across agents, subagents, and skills
- Clear separation of tool definition and implementation
- Consistent error handling and result formats
- Plugin-style extensibility

For more information on how agents and subagents use these tools, see [ARCHITECTURE.md](./ARCHITECTURE.md).
