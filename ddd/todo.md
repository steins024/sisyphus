# Sisyphus Implementation TODO

## Decisions

- [x] **Language**: Python 3.11+
- [x] **LLM Provider**: Anthropic (start with Claude, add others later)
- [ ] **UX**: CLI/REPL (recommended for Phase 1)

### Python Stack
```
CLI:         typer
LLM Client:  anthropic SDK
Validation:  pydantic
Config:      PyYAML
Async:       asyncio + httpx
Testing:     pytest
Linting:     ruff
Type Check:  pyright
```

---

## Phase 1: Minimal Chat Completion

- [x] Project setup (package manager, linting, formatting)
- [x] Basic LLM client wrapper
- [ ] Simple REPL interface
- [ ] Message history management
- [ ] Streaming response support

---

## Phase 2: Basic Tool Use

- [ ] Define Tool interface/protocol
- [ ] Implement Tool Registry
- [ ] Tool execution engine
- [ ] Built-in tools (e.g., read_file, write_file, terminal, search)
- [ ] Tool result handling in conversation
- [ ] Tool definition loader (parse YAML, generate JSON schema)

---

## Phase 3: Sub-agent Support

- [ ] Define Agent interface
- [ ] Agent spawning mechanism
- [ ] Subagent config loader (parse YAML)
- [ ] Tool subset filtering for subagents
- [ ] Context/state sharing between agents
- [ ] Agent communication protocol
- [ ] Parent-child agent relationships

---

## Phase 4: Skills System

- [ ] Define Skill interface
- [ ] Skill loader (parse manifest.yaml + prompt.md)
- [ ] Skill registration and discovery
- [ ] Skill trigger detection (keywords, intent)
- [ ] Skill prompt injection into agent context
- [ ] Skill script execution support
- [ ] Skill invocation in conversations

---

## Phase 5: MCP (Model Context Protocol) Support

- [ ] MCP client implementation
- [ ] MCP server discovery
- [ ] MCP tool integration with Tool Registry
- [ ] MCP resource handling

---

## Infrastructure

- [ ] Unified Registry (tools, subagents, skills)
- [ ] Config directory structure setup
  - [ ] `config/system_prompt.md`
  - [ ] `config/tools/*.yaml`
  - [ ] `config/subagents/*.yaml`
  - [ ] `config/skills/*/manifest.yaml`
  - [ ] `config/skills/*/prompt.md`
  - [ ] `config/skills/*/scripts/`
- [ ] System prompt assembly (base + tools + subagents + skills)
- [ ] Error handling and logging
- [ ] Tests

---

## Notes

- Tools: Agent registers full toolset, Subagent registers subset
- Skills: No direct tool registration, inject prompt + scripts, agent executes tools
- Lazy loading for skill prompts (inject only when activated)
- Permission isolation for subagents (only allowed tools)
