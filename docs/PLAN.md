# Sisyphus - AI Agent Framework

A practice project to build an AI agent system from scratch, supporting chat completion, tool use, MCP, sub-agents, and skills.

## Tech Stack (To Be Decided)

### Language Options
| Option | Pros | Cons |
|--------|------|------|
| **Python** | Rich LLM ecosystem, fast prototyping, great libraries | Runtime type checking only |
| **TypeScript** | Strong typing, good async, works for CLI/web | Smaller LLM ecosystem |
| **Rust** | Performance, safety | Slower development |
| **Go** | Great for CLI, concurrency | Less LLM tooling |

**Decision**: TBD

### UX Options
| Option | Description | Complexity |
|--------|-------------|------------|
| **CLI/REPL** | Simple terminal interface | Low |
| **TUI** | Rich terminal UI (panels, colors) | Medium |
| **Web UI** | Browser-based interface | High |
| **API-first** | HTTP server, UI added later | Medium |

**Decision**: TBD

### LLM Provider
- [ ] Anthropic (Claude)
- [ ] OpenAI
- [ ] Multi-provider support

**Decision**: TBD

## Architecture Principles

1. **Tool Registry Pattern** - Central registry for tool reusability across agents/subagents
2. **Interface-driven Design** - Define clear protocols/interfaces for tools, agents, skills
3. **Dependency Injection** - Pass dependencies to agents at creation time
4. **Separation of Concerns** - Core logic independent of UI layer

## Implementation Roadmap

### Phase 1: Minimal Chat Completion
- [ ] Project setup (package manager, linting, formatting)
- [ ] Basic LLM client wrapper
- [ ] Simple REPL interface
- [ ] Message history management
- [ ] Streaming response support

### Phase 2: Basic Tool Use
- [ ] Define Tool interface/protocol
- [ ] Implement Tool Registry
- [ ] Tool execution engine
- [ ] Built-in tools (e.g., calculator, file read)
- [ ] Tool result handling in conversation

### Phase 3: Sub-agent Support
- [ ] Define Agent interface
- [ ] Agent spawning mechanism
- [ ] Context/state sharing between agents
- [ ] Agent communication protocol
- [ ] Parent-child agent relationships

### Phase 4: Skills System
- [ ] Define Skill interface
- [ ] Skill loader (from files/config)
- [ ] Skill registration and discovery
- [ ] Skill invocation in conversations

### Phase 5: MCP (Model Context Protocol) Support
- [ ] MCP client implementation
- [ ] MCP server discovery
- [ ] MCP tool integration with Tool Registry
- [ ] MCP resource handling

## Open Questions

1. Language choice?
2. LLM provider(s) to support?
3. CLI framework preference?
4. Configuration approach (env vars, config file, both)?

## Project Structure (Draft)

```
sisyphus/
├── src/
│   ├── core/           # Core abstractions
│   │   ├── agent.py    # Agent interface
│   │   ├── tool.py     # Tool interface
│   │   └── skill.py    # Skill interface
│   ├── llm/            # LLM client wrappers
│   ├── tools/          # Built-in tools
│   ├── registry/       # Tool/Skill registries
│   ├── mcp/            # MCP client
│   └── ui/             # CLI/TUI interface
├── config/             # Configuration files
├── tests/              # Test suite
└── examples/           # Example usage
```

## References

- [Anthropic Claude API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
