# LLM Integration: Copilot API

This document describes the LLM integration approach for Sisyphus.

## Decision

**Provider**: Copilot API (via GitHub Copilot subscription)

**Rationale**:
- Leverages existing GitHub Copilot subscription
- Exposes Anthropic-compatible API format
- No additional API costs

## Overview

[Copilot API](https://github.com/ericc-ch/copilot-api) is a reverse-engineered proxy that exposes GitHub Copilot as an OpenAI and Anthropic compatible service.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Sisyphus   │────▶│ Copilot API │────▶│   GitHub    │
│   Agent     │     │   Proxy     │     │   Copilot   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │
      │  Anthropic        │  GitHub
      │  Messages API     │  OAuth
      │  Format           │
```

## API Details

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/messages` | POST | Anthropic-compatible messages API |
| `/v1/chat/completions` | POST | OpenAI-compatible chat API |
| `/v1/models` | GET | List available models |
| `/usage` | GET | Usage statistics |

### Base Configuration

```python
BASE_URL = "http://localhost:4141"
AUTH_TOKEN = "dummy"  # Copilot API handles GitHub auth
```

### Request Format (Anthropic-compatible)

```python
import httpx

response = httpx.post(
    "http://localhost:4141/v1/messages",
    json={
        "model": "claude-opus-4.5",  # or gpt-4.1
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": "Hello, world!"}
        ]
    }
)
```

### Response Format

```json
{
  "id": "msg_xxx",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you today?"
    }
  ],
  "model": "claude-opus-4.5",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 15
  }
}
```

## Setup Requirements

### 1. Start Copilot API Proxy

```bash
# First time (will open browser for GitHub OAuth)
npx copilot-api@latest start --port 4141

# With rate limiting (recommended)
npx copilot-api@latest start --port 4141 --rate-limit 5 --wait
```

### 2. Verify Connection

```bash
curl http://localhost:4141/v1/models
```

## Implementation Notes

### Using anthropic Python SDK

The `anthropic` SDK can be configured to use Copilot API:

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:4141",
    api_key="dummy"  # Required but not used
)

message = client.messages.create(
    model="claude-opus-4.5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

### Streaming Support

Copilot API supports streaming responses:

```python
with client.messages.stream(
    model="claude-opus-4.5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Tool Use

Tool use follows the Anthropic format:

```python
response = client.messages.create(
    model="claude-opus-4.5",
    max_tokens=1024,
    tools=[
        {
            "name": "read_file",
            "description": "Read contents of a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        }
    ],
    messages=[{"role": "user", "content": "Read the README.md file"}]
)
```

## Configuration

Environment variables for Sisyphus:

```bash
# Required
COPILOT_API_URL=http://localhost:4141

# Optional
COPILOT_API_MODEL=claude-opus-4.5
COPILOT_API_MAX_TOKENS=4096
```

## Limitations

1. **Requires Copilot subscription** - Active GitHub Copilot subscription needed
2. **Rate limiting** - GitHub may throttle excessive requests
3. **Model availability** - Limited to models GitHub Copilot supports
4. **No guarantees** - Reverse-engineered, may break with GitHub updates

## Future Considerations

- Add direct Anthropic API support as fallback
- Add OpenAI API support for multi-provider
- Abstract LLM client behind interface for easy provider switching
