# OpenAI-Compatible API

Cortex Flow provides an OpenAI Chat Completions API compatible interface, allowing it to be used as a drop-in replacement for OpenAI in chatbot applications and other integrations.

## Overview

The OpenAI-compatible API server exposes endpoints that match the OpenAI API specification, enabling you to use standard OpenAI SDKs and tools with Cortex Flow's multi-agent system.

**Base URL:** `http://localhost:8001` (configurable via `OPENAI_COMPAT_PORT`)

## Key Features

- ✅ **Standard OpenAI Format** - Compatible with OpenAI Chat Completions API
- ✅ **Drop-in Replacement** - Works with OpenAI Python SDK and other clients
- ✅ **Conversation Context** - Maintains conversation history via `conversation_id`
- ✅ **Streaming Support** - Server-Sent Events (SSE) for real-time responses
- ✅ **Token Tracking** - Accurate token counting and usage reporting
- ✅ **Multi-Agent** - Transparent orchestration of specialized AI agents

## Quick Start

### 1. Start the Server

```bash
# Ensure supervisor and other agents are running
python -m servers.supervisor_server &

# Start OpenAI-compatible API server
python -m servers.openai_compat_server
```

The server will start on port 8001 (configurable in `.env`).

### 2. Use with OpenAI Python SDK

```python
from openai import OpenAI

# Point to Cortex Flow instead of OpenAI
client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="dummy"  # API key not required yet
)

# Use exactly like OpenAI
response = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Research the latest AI agent frameworks"}
    ]
)

print(response.choices[0].message.content)
```

### 3. Use with Streaming

```python
# Streaming example
stream = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "Create a report on AI trends"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## API Endpoints

### GET /v1/models

List available models.

**Response:**
```json
{
    "object": "list",
    "data": [
        {
            "id": "cortex-flow",
            "object": "model",
            "created": 1234567890,
            "owned_by": "cortex-flow"
        },
        {
            "id": "cortex-flow-supervisor",
            "object": "model",
            "created": 1234567890,
            "owned_by": "cortex-flow"
        }
    ]
}
```

### POST /v1/chat/completions

Create a chat completion.

**Request Body:**
```json
{
    "model": "cortex-flow",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What are AI agents?"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000,
    "stream": false,
    "conversation_id": "optional-conv-id"
}
```

**Response:**
```json
{
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "cortex-flow",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "AI agents are autonomous systems..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 20,
        "completion_tokens": 150,
        "total_tokens": 170
    },
    "conversation_id": "optional-conv-id",
    "metadata": {
        "execution_time_seconds": 3.45,
        "agents_used": ["researcher", "analyst"],
        "iterations": 2
    }
}
```

## Conversation Management

### Maintaining Context

Use `conversation_id` to maintain conversation context across multiple requests:

```python
# First message
response1 = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "My name is Alice"}
    ],
    conversation_id="user_123_conv_1"  # Custom conversation ID
)

# Follow-up message (same conversation)
response2 = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "My name is Alice"},
        {"role": "assistant", "content": response1.choices[0].message.content},
        {"role": "user", "content": "What is my name?"}
    ],
    conversation_id="user_123_conv_1"  # Same ID
)

# Agent will remember "Alice" from previous message
```

### Auto-Generated Conversation IDs

If you don't provide a `conversation_id`, one will be generated automatically:

```python
response = client.chat.completions.create(
    model="cortex-flow",
    messages=[{"role": "user", "content": "Hello"}]
)

# Get the auto-generated conversation_id
conv_id = response.conversation_id
print(f"Conversation ID: {conv_id}")
```

## Streaming Responses

### Server-Sent Events (SSE)

Enable streaming with `stream=True`:

```python
stream = client.chat.completions.create(
    model="cortex-flow",
    messages=[
        {"role": "user", "content": "Write a short story"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Raw SSE Format

SSE chunks follow this format:

```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":123,"model":"cortex-flow","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":123,"model":"cortex-flow","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":123,"model":"cortex-flow","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

## Request Parameters

### Supported Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | string | Model identifier | Required |
| `messages` | array | Conversation messages | Required |
| `temperature` | float | Sampling temperature (0-2) | 0.7 |
| `max_tokens` | integer | Max tokens to generate | None |
| `stream` | boolean | Enable streaming | false |
| `top_p` | float | Nucleus sampling (0-1) | 1.0 |
| `n` | integer | Number of completions | 1 |
| `stop` | string/array | Stop sequences | None |
| `presence_penalty` | float | Presence penalty (-2 to 2) | 0.0 |
| `frequency_penalty` | float | Frequency penalty (-2 to 2) | 0.0 |
| `user` | string | User identifier | None |
| `conversation_id` | string | Conversation ID (extension) | Auto-generated |

### Cortex Flow Extensions

In addition to standard OpenAI parameters, we support:

- **`conversation_id`**: For explicit conversation tracking
- **`metadata`**: Additional execution metadata in response

## Using with Chatbot Frameworks

### LangChain Integration

```python
from langchain.chat_models import ChatOpenAI

# Use Cortex Flow as LLM
llm = ChatOpenAI(
    model="cortex-flow",
    openai_api_base="http://localhost:8001/v1",
    openai_api_key="dummy"
)

response = llm.invoke("Tell me about AI agents")
print(response.content)
```

### Custom Chatbot Example

```python
class CortexChatbot:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:8001/v1",
            api_key="dummy"
        )
        self.conversation_id = None

    def chat(self, user_message: str) -> str:
        """Send message and get response."""
        messages = [{"role": "user", "content": user_message}]

        response = self.client.chat.completions.create(
            model="cortex-flow",
            messages=messages,
            conversation_id=self.conversation_id
        )

        # Store conversation ID for next message
        self.conversation_id = response.conversation_id

        return response.choices[0].message.content

# Usage
bot = CortexChatbot()
print(bot.chat("Research AI agents"))
print(bot.chat("Summarize the key findings"))  # Maintains context
```

## Token Counting

Cortex Flow provides accurate token counting using `tiktoken`:

```python
response = client.chat.completions.create(
    model="cortex-flow",
    messages=[{"role": "user", "content": "Hello"}]
)

print(f"Prompt tokens: {response.usage.prompt_tokens}")
print(f"Completion tokens: {response.usage.completion_tokens}")
print(f"Total tokens: {response.usage.total_tokens}")
```

### Install tiktoken for Accurate Counting

```bash
pip install tiktoken
```

Without tiktoken, token counts are approximated (1 token ≈ 4 characters).

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Enable OpenAI-compatible API
OPENAI_COMPAT_ENABLE=true

# Server port
OPENAI_COMPAT_PORT=8001

# Model name
OPENAI_COMPAT_MODEL_NAME=cortex-flow

# Max context tokens
OPENAI_COMPAT_MAX_CONTEXT_TOKENS=8000

# Token counter model
OPENAI_COMPAT_TOKEN_MODEL=gpt-4
```

## Error Handling

Errors follow OpenAI format:

```json
{
    "error": {
        "message": "Model 'invalid-model' not found",
        "type": "invalid_request_error",
        "code": "model_not_found"
    }
}
```

### Common Errors

| HTTP Status | Error Type | Description |
|-------------|------------|-------------|
| 400 | `invalid_request_error` | Invalid parameters |
| 404 | `not_found_error` | Model not found |
| 500 | `server_error` | Internal server error |
| 422 | `validation_error` | Request validation failed |

## Multi-Agent Transparency

When you use Cortex Flow, the supervisor agent automatically:

1. Analyzes your request
2. Delegates to specialized agents (Researcher, Analyst, Writer)
3. Synthesizes results
4. Returns unified response

This is transparent in the API - you just see the final result. Check `metadata.agents_used` for details:

```python
response = client.chat.completions.create(
    model="cortex-flow",
    messages=[{"role": "user", "content": "Research and analyze AI trends"}]
)

print(response.metadata)
# {
#     "agents_used": ["researcher", "analyst"],
#     "execution_time_seconds": 5.2,
#     "iterations": 3
# }
```

## Testing

Run compatibility tests:

```bash
# Install OpenAI SDK
pip install openai

# Run tests
pytest tests/test_openai_compatibility.py -v
```

## Limitations

Current limitations:

- ❌ Function calling not yet supported
- ❌ Tool use not yet supported
- ❌ Vision/image inputs not supported
- ❌ Audio not supported
- ❌ API key authentication not enforced (coming soon)

## Next Steps

- See [API Examples](./examples.md) for more use cases
- Check [Deployment Guide](../deployment/README.md) for production setup
- Read [Architecture](../architecture/README.md) to understand the multi-agent system

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/cortex-flow/issues
- Documentation: Full docs at `/docs`
