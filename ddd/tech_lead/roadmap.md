# Sisyphus Development Roadmap

## Overview

This roadmap outlines the phased development of the Sisyphus AI Agent Framework.

---

## Phase 1: Minimal Chat Completion (Current)
**Target**: Sprint 01-02 (2-4 weeks)
**Status**: In Progress

### Goals
- Project foundation with proper tooling
- Basic LLM integration via Copilot API
- Functional REPL for chat interactions
- Streaming response support

### Key Deliverables
- [ ] Working `sisyphus chat` command
- [ ] Conversation with Claude via Copilot API
- [ ] Message history within session
- [ ] Clean, typed codebase

---

## Phase 2: Basic Tool Use
**Target**: Sprint 03-04 (4 weeks)
**Status**: Planned

### Goals
- Define Tool interface/protocol
- Implement Tool Registry
- Basic tool execution engine
- Built-in tools (read_file, write_file, terminal, search)

### Key Deliverables
- [ ] Tool definition YAML format
- [ ] Tool registration and discovery
- [ ] Tool execution with result handling
- [ ] 4+ built-in tools working

---

## Phase 3: Sub-agent Support
**Target**: Sprint 05-06 (4 weeks)
**Status**: Planned

### Goals
- Agent interface definition
- Subagent spawning mechanism
- Tool subset filtering
- Agent communication

### Key Deliverables
- [ ] Subagent definition YAML format
- [ ] Subagent invocation from main agent
- [ ] Tool permission isolation
- [ ] Result aggregation

---

## Phase 4: Skills System
**Target**: Sprint 07-08 (4 weeks)
**Status**: Planned

### Goals
- Skill interface definition
- Skill loader (manifest + prompt)
- Trigger detection
- Prompt injection

### Key Deliverables
- [ ] Skill definition format (manifest.yaml + prompt.md)
- [ ] Skill activation and deactivation
- [ ] Script execution support
- [ ] 2+ example skills

---

## Phase 5: MCP Support
**Target**: Sprint 09-10 (4 weeks)
**Status**: Planned

### Goals
- MCP client implementation
- Server discovery
- Tool integration
- Resource handling

### Key Deliverables
- [ ] MCP protocol support
- [ ] External MCP server connectivity
- [ ] MCP tools in registry
- [ ] Resource access

---

## Timeline Summary

```
2025-Q4 (Dec)    : Phase 1 - Chat Completion
2025-Q1 (Jan-Feb): Phase 2 - Tool Use
2025-Q1 (Feb-Mar): Phase 3 - Sub-agents
2025-Q2 (Mar-Apr): Phase 4 - Skills
2025-Q2 (Apr-May): Phase 5 - MCP
```

---

## Success Metrics

| Phase | Metric | Target |
|-------|--------|--------|
| 1 | Chat roundtrip working | 100% |
| 2 | Built-in tools functional | 4 tools |
| 3 | Subagent delegation working | 1 subagent |
| 4 | Skills activating correctly | 2 skills |
| 5 | MCP servers connected | 1 server |

---

## Dependencies and Prerequisites

### Phase 1
- Copilot API proxy running locally
- GitHub Copilot subscription active
- Python 3.11+ installed

### Phase 2+
- Phase 1 complete
- Tool execution sandbox considerations
- File system access permissions

---

## Open Questions

1. **Configuration storage**: File-based vs database for larger deployments?
2. **Multi-model support**: Add OpenAI/other providers in parallel with Phase 2?
3. **Plugin system**: Should skills/tools be installable packages?
