# Sprint 01 Backlog

## Epic: Project Setup

### [TASK-001] Initialize Python Project with uv
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: Critical
- **Dependencies**: None
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Initialize Python project using `uv` as the package manager. Set up pyproject.toml with project metadata, Python version (3.11+), and initial dependencies.
- **Acceptance Criteria**:
  - [ ] `uv init` creates project structure
  - [ ] pyproject.toml includes: name, version, description, python >= 3.11
  - [ ] Initial dependencies added: anthropic, typer, pydantic, pyyaml, httpx
  - [ ] Dev dependencies added: pytest, ruff, pyright
  - [ ] `uv sync` successfully installs all dependencies
  - [ ] Virtual environment created and working

---

### [TASK-002] Configure Ruff Linting and Formatting
- **Status**: Backlog
- **Estimate**: 1 hour (Small)
- **Priority**: High
- **Dependencies**: [TASK-001]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Configure ruff for both linting and formatting in pyproject.toml. Set up sensible defaults for the project.
- **Acceptance Criteria**:
  - [ ] Ruff config in pyproject.toml with line-length=88
  - [ ] Enable recommended rule sets (E, F, I, UP, B, SIM)
  - [ ] Configure src layout (src/sisyphus)
  - [ ] `uv run ruff check .` runs without errors
  - [ ] `uv run ruff format .` formats code consistently

---

### [TASK-003] Configure Pyright Type Checking
- **Status**: Backlog
- **Estimate**: 1 hour (Small)
- **Priority**: High
- **Dependencies**: [TASK-001]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Configure pyright for strict type checking. Set up pyrightconfig.json or pyproject.toml section.
- **Acceptance Criteria**:
  - [ ] Pyright config with strict mode enabled
  - [ ] Type stub packages installed if needed
  - [ ] `uv run pyright` runs without errors on empty project
  - [ ] VSCode/IDE integration works (if applicable)

---

### [TASK-004] Create Source Directory Structure
- **Status**: Backlog
- **Estimate**: 1 hour (Small)
- **Priority**: High
- **Dependencies**: [TASK-001]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Create the src/sisyphus directory structure as outlined in PLAN.md. Add __init__.py files and placeholder modules.
- **Acceptance Criteria**:
  - [ ] src/sisyphus/ directory created with __init__.py
  - [ ] src/sisyphus/core/ for core abstractions
  - [ ] src/sisyphus/llm/ for LLM client
  - [ ] src/sisyphus/ui/ for CLI/REPL
  - [ ] config/ directory for configuration files
  - [ ] tests/ directory for test files
  - [ ] All directories have __init__.py where appropriate

---

### [TASK-005] Set Up Pytest Configuration
- **Status**: Backlog
- **Estimate**: 1 hour (Small)
- **Priority**: Medium
- **Dependencies**: [TASK-001], [TASK-004]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Configure pytest with sensible defaults. Set up conftest.py and verify test discovery works.
- **Acceptance Criteria**:
  - [ ] pytest config in pyproject.toml
  - [ ] tests/ directory with conftest.py
  - [ ] Sample test file that passes
  - [ ] `uv run pytest` discovers and runs tests
  - [ ] pytest-asyncio configured for async test support

---

## Epic: LLM Client

### [TASK-006] Define LLM Client Interface/Protocol
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: Critical
- **Dependencies**: [TASK-004]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Define a Protocol/ABC for the LLM client that abstracts the provider. This allows future providers (direct Anthropic, OpenAI) to be added easily.
- **Acceptance Criteria**:
  - [ ] LLMClient Protocol defined in src/sisyphus/llm/base.py
  - [ ] Methods: `complete()`, `stream()` defined
  - [ ] Pydantic models for Message, Response, Usage
  - [ ] Type hints complete and pyright passes
  - [ ] Docstrings explain usage

---

### [TASK-007] Implement Copilot API Client
- **Status**: Backlog
- **Estimate**: 4 hours (Medium)
- **Priority**: Critical
- **Dependencies**: [TASK-006]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Implement the LLM client using anthropic SDK configured to point at Copilot API proxy. Handle authentication and basic error cases.
- **Acceptance Criteria**:
  - [ ] CopilotClient class implements LLMClient protocol
  - [ ] Uses anthropic SDK with custom base_url
  - [ ] Configurable via environment variables (COPILOT_API_URL)
  - [ ] Default model configurable (COPILOT_API_MODEL)
  - [ ] Basic error handling (connection errors, API errors)
  - [ ] Unit tests with mocked responses

---

### [TASK-008] Implement Streaming Response Handler
- **Status**: Backlog
- **Estimate**: 3 hours (Medium)
- **Priority**: High
- **Dependencies**: [TASK-007]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Implement streaming response support using anthropic SDK's streaming API. Handle partial messages and text deltas.
- **Acceptance Criteria**:
  - [ ] `stream()` method yields text chunks as they arrive
  - [ ] Properly handles stream start/end events
  - [ ] Collects final message for history
  - [ ] Handles stream interruption gracefully
  - [ ] Async generator pattern for streaming
  - [ ] Integration test with real API (manual verification)

---

### [TASK-009] Add Configuration Management
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: Medium
- **Dependencies**: [TASK-004]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Create configuration management using pydantic-settings or similar. Load from environment variables and optional config file.
- **Acceptance Criteria**:
  - [ ] Config class with pydantic validation
  - [ ] Loads from environment variables
  - [ ] Optional YAML config file support
  - [ ] Defaults for all settings
  - [ ] Settings: api_url, model, max_tokens, timeout
  - [ ] Config singleton or factory pattern

---

## Epic: Message History

### [TASK-010] Define Message Models
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: High
- **Dependencies**: [TASK-004]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Define Pydantic models for messages that match Anthropic's message format. Support user and assistant roles.
- **Acceptance Criteria**:
  - [ ] Message model with role, content fields
  - [ ] Support for text content blocks
  - [ ] Serialization to/from Anthropic API format
  - [ ] Validation of message structure
  - [ ] Future-proof for tool_use content blocks

---

### [TASK-011] Implement Conversation History Manager
- **Status**: Backlog
- **Estimate**: 3 hours (Medium)
- **Priority**: High
- **Dependencies**: [TASK-010]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Create a ConversationHistory class that manages the message list. Handles adding messages, formatting for API calls, and optional persistence.
- **Acceptance Criteria**:
  - [ ] ConversationHistory class in src/sisyphus/core/
  - [ ] add_user_message() and add_assistant_message() methods
  - [ ] get_messages() returns API-ready format
  - [ ] clear() method to reset conversation
  - [ ] Optional: Token counting/truncation for context limits
  - [ ] Unit tests for all methods

---

## Epic: REPL Interface

### [TASK-012] Create Basic CLI Entry Point
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: High
- **Dependencies**: [TASK-004]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Create the main CLI entry point using typer. Set up basic command structure with a `chat` command to start the REPL.
- **Acceptance Criteria**:
  - [ ] Main CLI app with typer in src/sisyphus/ui/cli.py
  - [ ] `sisyphus chat` command to start REPL
  - [ ] `--help` shows usage information
  - [ ] Entry point configured in pyproject.toml
  - [ ] `uv run sisyphus` works after install

---

### [TASK-013] Implement REPL Input Loop
- **Status**: Backlog
- **Estimate**: 3 hours (Medium)
- **Priority**: High
- **Dependencies**: [TASK-012], [TASK-007], [TASK-011]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Implement the main REPL loop that reads user input, sends to LLM, and displays responses. Handle basic commands like /quit, /clear.
- **Acceptance Criteria**:
  - [ ] Async REPL loop with prompt
  - [ ] User input sent to LLM client
  - [ ] Response displayed to user
  - [ ] Messages added to conversation history
  - [ ] /quit or /exit command to exit
  - [ ] /clear command to reset history
  - [ ] Empty input handled gracefully

---

### [TASK-014] Add Streaming Output Display
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: High
- **Dependencies**: [TASK-013], [TASK-008]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Integrate streaming response display in REPL. Print text chunks as they arrive with proper formatting.
- **Acceptance Criteria**:
  - [ ] Streaming text displays character-by-character
  - [ ] No flickering or buffer issues
  - [ ] Proper newline handling
  - [ ] "Thinking..." indicator while waiting for first chunk
  - [ ] Clean formatting after response completes

---

### [TASK-015] Implement Graceful Shutdown
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: Medium
- **Dependencies**: [TASK-013]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Handle Ctrl+C and other interrupts gracefully. Cancel ongoing requests and exit cleanly.
- **Acceptance Criteria**:
  - [ ] Ctrl+C during input prompts for exit confirmation
  - [ ] Ctrl+C during streaming cancels request cleanly
  - [ ] No orphaned async tasks
  - [ ] Exit message displayed
  - [ ] Return code 0 on clean exit

---

### [TASK-016] Add System Prompt Support
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: Medium
- **Dependencies**: [TASK-009], [TASK-007]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Load and include a system prompt from config/system_prompt.md. Pass to LLM with each request.
- **Acceptance Criteria**:
  - [ ] Default system prompt file at config/system_prompt.md
  - [ ] System prompt loaded at startup
  - [ ] Included in LLM requests
  - [ ] CLI flag to override system prompt file
  - [ ] Graceful fallback if file not found

---

## Epic: Testing and Polish

### [TASK-017] Write Unit Tests for LLM Client
- **Status**: Backlog
- **Estimate**: 3 hours (Medium)
- **Priority**: Medium
- **Dependencies**: [TASK-007], [TASK-008]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Write comprehensive unit tests for the LLM client. Mock API responses for reliable testing.
- **Acceptance Criteria**:
  - [ ] Tests for successful completion
  - [ ] Tests for streaming responses
  - [ ] Tests for error handling (timeout, API error)
  - [ ] Tests for configuration loading
  - [ ] >80% code coverage for llm module

---

### [TASK-018] Write Integration Tests
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: Low
- **Dependencies**: [TASK-017], [TASK-013]
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Write integration tests that verify the full flow from input to output. Use mocked LLM for deterministic tests.
- **Acceptance Criteria**:
  - [ ] Test: User message -> LLM -> Response displayed
  - [ ] Test: Conversation history maintained
  - [ ] Test: /quit command exits cleanly
  - [ ] Test: /clear resets history
  - [ ] Tests marked appropriately (skip if no API)

---

### [TASK-019] Documentation and README
- **Status**: Backlog
- **Estimate**: 2 hours (Small)
- **Priority**: Low
- **Dependencies**: All other tasks
- **Created**: 2025-12-10
- **Updated**: 2025-12-10
- **Description**: Update README with installation instructions, usage examples, and configuration guide.
- **Acceptance Criteria**:
  - [ ] Installation instructions (uv based)
  - [ ] Quick start guide
  - [ ] Configuration reference
  - [ ] Development setup guide
  - [ ] Copilot API setup instructions

---

## Summary

| Category | Tasks | Total Estimate |
|----------|-------|----------------|
| Project Setup | 5 | 6 hours |
| LLM Client | 4 | 11 hours |
| Message History | 2 | 5 hours |
| REPL Interface | 5 | 11 hours |
| Testing/Polish | 3 | 7 hours |
| **Total** | **19** | **40 hours** |

**Sprint Capacity**: 40-50 hours (with 20% buffer)
**Risk Assessment**: On track, buffer available for unexpected issues
