# Sprint 01 - Blockers and Risks

## Active Blockers

*No active blockers at sprint start.*

---

## Risk Register

### RISK-001: Copilot API Proxy Availability
- **Likelihood**: Medium
- **Impact**: High
- **Mitigation**: Have direct Anthropic API setup instructions as fallback
- **Status**: Monitoring

### RISK-002: Streaming Implementation Complexity
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**: anthropic SDK has good streaming support; fallback to non-streaming
- **Status**: Monitoring

### RISK-003: Async/Sync Complexity in REPL
- **Likelihood**: Medium
- **Impact**: Low
- **Mitigation**: Use asyncio.run() pattern; typer supports async
- **Status**: Monitoring

---

## Blocker Template

```markdown
### BLOCKER-XXX: Title
- **Task Affected**: [TASK-XXX]
- **Description**: What is blocking progress
- **Owner**: Who is responsible for resolution
- **Raised**: YYYY-MM-DD
- **Target Resolution**: YYYY-MM-DD
- **Status**: Open | In Progress | Resolved
- **Resolution**: (filled when resolved)
```
