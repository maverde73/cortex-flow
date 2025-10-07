# Chatbot API Guide - Cortex Flow

This guide explains how to use Cortex Flow as a chatbot with conversation memory, message trimming, and full LangChain compatibility.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Configuration](#configuration)
- [API Usage](#api-usage)
- [LangChain Integration](#langchain-integration)
- [Advanced Topics](#advanced-topics)
- [Troubleshooting](#troubleshooting)

## Overview

Cortex Flow exposes an **OpenAI-compatible Chat Completions API** at `/v1/chat/completions`, making it a drop-in replacement for OpenAI's API in existing chatbot applications.

### Key Features

✅ **Conversation Memory** - Conversations persist across requests using `thread_id`
✅ **Message Trimming** - Automatic management of context window limits
✅ **LangChain Compatible** - Works seamlessly with LangChain's chatbot tools
✅ **Streaming Support** - Real-time token streaming via Server-Sent Events
✅ **Multi-Agent Orchestration** - Powered by LangGraph supervisor agent
✅ **PostgreSQL/Redis Persistence** - Production-ready state management

## Quick Start

### 1. Start the Server

```bash
# Activate environment
source .venv/bin/activate

# Run the OpenAI-compatible API server
python -m servers.openai_compat_server
```

Server will start on `http://localhost:8001` by default.

### 2. Make a Simple Request

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cortex-flow",
    "messages": [
      {"role": "user", "content": "Hello! My name is Alice."}
    ]
  }'
```

### 3. Continue the Conversation

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cortex-flow",
    "messages": [
      {"role": "user", "content": "What'\''s my name?"}
    ],
    "user": "alice-session-123"
  }'
```

The agent will remember "Alice" from the previous request because they share the same `user` field (used as `thread_id`).

## Features

### Conversation Memory

Cortex Flow uses **LangGraph checkpointers** to persist conversation state across requests.

#### How It Works

1. **thread_id**: Each conversation is identified by a unique `thread_id`
2. **Checkpointer**: State is saved after each agent turn
3. **Retrieval**: On next request with same `thread_id`, full conversation history is loaded
4. **Isolation**: Different threads are completely isolated from each other

#### Example: Multi-Turn Conversation

```python
import httpx

client = httpx.Client(base_url="http://localhost:8001")

thread_id = "user-alice-session-1"

# Turn 1
response1 = client.post("/v1/chat/completions", json={
    "model": "cortex-flow",
    "messages": [{"role": "user", "content": "My favorite color is blue"}],
    "user": thread_id
})

# Turn 2 - Agent remembers previous context
response2 = client.post("/v1/chat/completions", json={
    "model": "cortex-flow",
    "messages": [{"role": "user", "content": "What's my favorite color?"}],
    "user": thread_id
})

# Response will mention "blue"
print(response2.json()["choices"][0]["message"]["content"])
```

### Message Trimming

**Problem**: Long conversations can exceed the LLM's context window limit.

**Solution**: Cortex Flow automatically trims old messages while preserving recent context.

#### Trimming Strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `last` | Keep most recent messages | **Recommended** - Chatbots |
| `first` | Keep oldest messages | Preserving initial instructions |
| `smart` | Keep system prompt + recent | Balance between context and instructions |

#### Configuration

```bash
# .env
ENABLE_MESSAGE_TRIMMING=true
MAX_CONVERSATION_TOKENS=4000
MAX_CONVERSATION_MESSAGES=20
TRIMMING_STRATEGY=last
```

#### How Trimming Works

```
Conversation History:
┌─────────────────────────────────┐
│ SystemMessage: "You are..."     │ ← Preserved
│ HumanMessage: "Hello" (old)     │ ← Trimmed
│ AIMessage: "Hi!" (old)          │ ← Trimmed
│ HumanMessage: "What's Python?"  │ ← Trimmed
│ AIMessage: "Python is..." (old) │ ← Trimmed
│ ...                             │
│ HumanMessage: "My name is Bob"  │ ← Kept (recent)
│ AIMessage: "Hi Bob!"            │ ← Kept (recent)
│ HumanMessage: "What's my name?" │ ← Kept (current)
└─────────────────────────────────┘

After Trimming:
┌─────────────────────────────────┐
│ SystemMessage: "You are..."     │
│ HumanMessage: "My name is Bob"  │
│ AIMessage: "Hi Bob!"            │
│ HumanMessage: "What's my name?" │
└─────────────────────────────────┘
```

### Streaming

Enable real-time token streaming for better UX:

```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        "http://localhost:8001/v1/chat/completions",
        json={
            "model": "cortex-flow",
            "messages": [{"role": "user", "content": "Tell me a story"}],
            "stream": True,
            "user": "alice"
        }
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                content = chunk["choices"][0]["delta"].get("content", "")
                print(content, end="", flush=True)
```

## Configuration

### Environment Variables

```bash
# ============================================================================
# CONVERSATION MEMORY
# ============================================================================

# Enable conversation memory (default: true)
ENABLE_CONVERSATION_MEMORY=true

# Checkpointer type: memory | postgres | redis
CHECKPOINTER_TYPE=memory

# PostgreSQL URL (if using postgres checkpointer)
POSTGRES_CHECKPOINT_URL=postgresql://user:pass@localhost:5432/cortex_checkpoints

# ============================================================================
# MESSAGE TRIMMING
# ============================================================================

# Enable automatic message trimming (default: true)
ENABLE_MESSAGE_TRIMMING=true

# Maximum tokens to keep in conversation history
MAX_CONVERSATION_TOKENS=4000

# Maximum number of messages to keep
MAX_CONVERSATION_MESSAGES=20

# Trimming strategy: last | first | smart
TRIMMING_STRATEGY=last

# ============================================================================
# API SERVER
# ============================================================================

# Enable OpenAI-compatible API (default: true)
OPENAI_COMPAT_ENABLE=true

# API server port
OPENAI_COMPAT_PORT=8001

# Virtual model name
OPENAI_COMPAT_MODEL_NAME=cortex-flow
```

### Production Setup

For production deployments, use **PostgreSQL** for persistent state:

```bash
# 1. Create PostgreSQL database
createdb cortex_checkpoints

# 2. Configure .env
CHECKPOINTER_TYPE=postgres
POSTGRES_CHECKPOINT_URL=postgresql://cortex:password@localhost:5432/cortex_checkpoints

# 3. Install PostgreSQL extras
pip install langgraph[postgres]

# 4. Start server
python -m servers.openai_compat_server
```

The checkpointer will automatically create required tables on first run.

## API Usage

### Endpoint: POST /v1/chat/completions

OpenAI-compatible chat completions endpoint.

#### Request Format

```json
{
  "model": "cortex-flow",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "user": "unique-thread-id",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model name (use "cortex-flow") |
| `messages` | array | Yes | Conversation history |
| `stream` | boolean | No | Enable streaming (default: false) |
| `user` | string | **Recommended** | Thread ID for conversation memory |
| `temperature` | number | No | Sampling temperature (0-2) |
| `max_tokens` | number | No | Maximum tokens to generate |

#### Response Format (Non-Streaming)

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
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  }
}
```

### Other Endpoints

```bash
# List available models
GET /v1/models

# Health check
GET /health

# API information
GET /
```

## LangChain Integration

Cortex Flow works seamlessly with LangChain's chatbot tools.

### Using with LangChain

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Point to Cortex Flow instead of OpenAI
llm = ChatOpenAI(
    model="cortex-flow",
    base_url="http://localhost:8001/v1",
    api_key="dummy"  # Not required but LangChain expects it
)

# Use with conversation memory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

chat_history = InMemoryChatMessageHistory()

chain_with_history = RunnableWithMessageHistory(
    llm,
    lambda session_id: chat_history,
    input_messages_key="input",
    history_messages_key="history",
)

# Chat with memory
response = chain_with_history.invoke(
    {"input": "My name is Alice"},
    config={"configurable": {"session_id": "user-123"}}
)

response = chain_with_history.invoke(
    {"input": "What's my name?"},
    config={"configurable": {"session_id": "user-123"}}
)
# Will respond with "Alice"
```

### Using with LangGraph

```python
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="cortex-flow",
    base_url="http://localhost:8001/v1",
    api_key="dummy"
)

# LangGraph automatically uses the checkpointer from Cortex Flow
# No need to add your own - conversation state is managed server-side!

from langchain_core.messages import HumanMessage

response = llm.invoke(
    [HumanMessage(content="Tell me about AI agents")],
    config={"configurable": {"thread_id": "my-conversation"}}
)
```

## Advanced Topics

### Thread Management

#### Thread Naming Convention

Use descriptive thread IDs:

```python
# ✅ Good
thread_id = f"user-{user_id}-session-{timestamp}"
thread_id = f"support-ticket-{ticket_id}"
thread_id = f"demo-{demo_id}"

# ❌ Bad
thread_id = "thread1"
thread_id = "abc"
```

#### Thread Isolation

Threads are **completely isolated**:

```python
# Thread A
response_a = chat(messages=[...], user="alice-thread-1")

# Thread B - completely separate context
response_b = chat(messages=[...], user="bob-thread-2")
```

### Custom System Prompts

Override the default supervisor prompt:

```python
response = client.post("/v1/chat/completions", json={
    "model": "cortex-flow",
    "messages": [
        {
            "role": "system",
            "content": "You are a Python expert. Answer questions concisely."
        },
        {"role": "user", "content": "What is a decorator?"}
    ],
    "user": "alice"
})
```

### Token Usage Tracking

Every response includes token usage:

```python
response = client.post("/v1/chat/completions", json={...})
usage = response.json()["usage"]

print(f"Prompt tokens: {usage['prompt_tokens']}")
print(f"Completion tokens: {usage['completion_tokens']}")
print(f"Total tokens: {usage['total_tokens']}")
```

### Metadata and Tracing

Enable LangSmith for detailed tracing:

```bash
# .env
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=cortex-flow
LANGSMITH_TRACING=true
```

Each request will appear in LangSmith with:
- Full conversation history
- Agent delegation trace
- Tool calls and results
- Token usage
- Latency breakdown

## Troubleshooting

### Issue: Agent forgets previous messages

**Cause**: `thread_id` not provided or changing between requests

**Solution**: Pass consistent `user` field:

```python
# ❌ Bad - no thread_id
response = client.post("/v1/chat/completions", json={
    "messages": [...]
})

# ✅ Good - consistent thread_id
response = client.post("/v1/chat/completions", json={
    "messages": [...],
    "user": "alice-session-123"
})
```

### Issue: Context window exceeded

**Cause**: Long conversation exceeding token limit

**Solution**: Enable message trimming:

```bash
# .env
ENABLE_MESSAGE_TRIMMING=true
MAX_CONVERSATION_TOKENS=4000
```

Or manually reset the thread:

```python
# Start new conversation with same user
new_thread_id = f"alice-session-{datetime.now().timestamp()}"
```

### Issue: Checkpointer error with PostgreSQL

**Error**: `langgraph.checkpoint.postgres module not found`

**Solution**: Install PostgreSQL extras:

```bash
pip install langgraph[postgres]
```

**Error**: `POSTGRES_CHECKPOINT_URL not set`

**Solution**: Set the connection URL:

```bash
CHECKPOINTER_TYPE=postgres
POSTGRES_CHECKPOINT_URL=postgresql://user:pass@localhost:5432/dbname
```

### Issue: Memory not persisting (development)

**Cause**: Using `CHECKPOINTER_TYPE=memory` (in-memory storage, lost on restart)

**Solution**: For persistence, use PostgreSQL:

```bash
CHECKPOINTER_TYPE=postgres
POSTGRES_CHECKPOINT_URL=postgresql://localhost/cortex_checkpoints
```

### Issue: Streaming not working

**Cause**: Client not handling Server-Sent Events correctly

**Solution**: Use proper SSE client or check response headers:

```python
async with httpx.AsyncClient() as client:
    async with client.stream("POST", url, json={"stream": True, ...}) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                # Process chunk
                pass
```

## Examples

### Complete Chatbot Example

```python
import httpx
import json
from datetime import datetime

class CortexChatbot:
    """Simple chatbot client for Cortex Flow."""

    def __init__(self, base_url="http://localhost:8001", user_id="default"):
        self.base_url = base_url
        self.thread_id = f"user-{user_id}-{datetime.now().timestamp()}"
        self.client = httpx.Client(base_url=base_url)

    def chat(self, message: str, stream: bool = False):
        """Send message and get response."""
        payload = {
            "model": "cortex-flow",
            "messages": [{"role": "user", "content": message}],
            "user": self.thread_id,
            "stream": stream
        }

        if not stream:
            response = self.client.post("/v1/chat/completions", json=payload)
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            # Streaming response
            with self.client.stream("POST", "/v1/chat/completions", json=payload) as response:
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            print(content, end="", flush=True)
                print()  # Newline at end

    def reset_conversation(self):
        """Start a new conversation thread."""
        self.thread_id = f"user-{self.user_id}-{datetime.now().timestamp()}"


# Usage
bot = CortexChatbot(user_id="alice")

# Multi-turn conversation
bot.chat("Hello! My name is Alice.")
bot.chat("What's my name?")  # Will respond "Alice"
bot.chat("What's the capital of France?")
bot.chat("What did I ask you before?")  # Will remember "capital of France"

# Start new conversation
bot.reset_conversation()
bot.chat("Hi!")  # Fresh context, no memory of previous conversation
```

## Next Steps

- See [Architecture Documentation](../docs/README.md) for system design
- See [LangGraph Compatibility Guide](workflows/07_langgraph_compatibility.md) for workflow details
- See [.env.example](../.env.example) for complete configuration reference

---

**Documentation Version**: v1.0.0
**Last Updated**: 2025-10-07
