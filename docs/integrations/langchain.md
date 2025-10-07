# LangChain Integration

Cortex Flow provides full LangChain integration through the `CortexFlowChatModel` class, enabling seamless use in LangChain chains, agents, RAG pipelines, and the broader LangChain ecosystem.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Usage Patterns](#usage-patterns)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

### Why LangChain Integration?

LangChain is the leading framework for building LLM-powered applications. By providing a native LangChain interface, Cortex Flow enables:

- **Drop-in Compatibility**: Use Cortex Flow anywhere you'd use an OpenAI or Anthropic model
- **LCEL Support**: Full compatibility with LangChain Expression Language (`|` operator)
- **Ecosystem Access**: Integrate with LangChain's tools, agents, retrievers, and more
- **Multi-Agent Power**: Leverage Cortex Flow's specialized agents within LangChain workflows
- **Conversation Memory**: Built-in support for conversation context management

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangChain Application                    │
│  (Chains, Agents, RAG Pipelines, Tools, Memory, etc.)      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ BaseChatModel Interface
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              CortexFlowChatModel                            │
│  - _generate() / _agenerate()                               │
│  - _stream() / _astream()                                   │
│  - Message conversion (LangChain ↔ OpenAI format)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTP/REST
                           │
┌──────────────────────────▼──────────────────────────────────┐
│           OpenAI-Compatible API Server                      │
│               (Port 8001)                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ MCP Protocol
                           │
┌──────────────────────────▼──────────────────────────────────┐
│            Cortex Flow Multi-Agent System                   │
│  Supervisor → Researcher, Analyst, Writer Agents            │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

1. **OpenAI-Compatible API Server Running**:
```bash
python -m servers.openai_compat_server
```

2. **LangChain Installed**:
```bash
pip install langchain-core langchain-community
```

### Verify Installation

```python
from utils.langchain_chat_model import CortexFlowChatModel

llm = CortexFlowChatModel()
print(f"LangChain model: {llm._llm_type}")
```

## Quick Start

### Basic Usage

```python
from utils.langchain_helpers import create_cortex_flow_llm

# Create LLM
llm = create_cortex_flow_llm()

# Simple invocation
response = llm.invoke("What are AI agents?")
print(response.content)
```

### LCEL Chain

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Create chain using LCEL
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{query}")
])

chain = prompt | llm | StrOutputParser()

# Invoke chain
result = chain.invoke({"query": "Explain LangChain"})
print(result)
```

### Conversation Memory

```python
# Create LLM with conversation ID
llm = create_cortex_flow_llm(conversation_id="user_123_session_1")

# First message
llm.invoke("My name is Alice")

# Second message - remembers context
response = llm.invoke("What is my name?")
print(response.content)  # "Your name is Alice"
```

## Core Concepts

### 1. CortexFlowChatModel

The main class that implements LangChain's `BaseChatModel` interface.

**Key Features:**
- Implements all required LangChain methods
- Supports sync and async operations
- Provides streaming capabilities
- Tracks token usage and execution metadata
- Manages conversation context

**Creation:**
```python
from utils.langchain_chat_model import CortexFlowChatModel

llm = CortexFlowChatModel(
    base_url="http://localhost:8001/v1",  # API endpoint
    model_name="cortex-flow",              # Model identifier
    temperature=0.7,                       # Sampling temperature
    max_tokens=2000,                       # Max generation length
    conversation_id="session_123",         # Conversation context
    timeout=120.0                          # Request timeout
)
```

### 2. Message Conversion

LangChain uses its own message types, which are automatically converted:

| LangChain Message | OpenAI Format |
|-------------------|---------------|
| `SystemMessage` | `role: "system"` |
| `HumanMessage` | `role: "user"` |
| `AIMessage` | `role: "assistant"` |

**Example:**
```python
from langchain_core.messages import SystemMessage, HumanMessage

messages = [
    SystemMessage(content="You are a helpful assistant"),
    HumanMessage(content="What are AI agents?")
]

response = llm.invoke(messages)
```

### 3. Token Usage Tracking

Track token consumption for cost management:

```python
from utils.langchain_helpers import extract_token_usage

llm = create_cortex_flow_llm()
response = llm.invoke("Hello")

usage = extract_token_usage(llm)
print(f"Prompt tokens: {usage['prompt_tokens']}")
print(f"Completion tokens: {usage['completion_tokens']}")
print(f"Total tokens: {usage['total_tokens']}")
```

### 4. Execution Metadata

Access multi-agent execution details:

```python
from utils.langchain_helpers import extract_execution_metadata

llm = create_cortex_flow_llm()
response = llm.invoke("Research AI trends")

metadata = extract_execution_metadata(llm)
print(f"Agents used: {metadata.get('agents_used')}")
print(f"Execution time: {metadata.get('execution_time_seconds')}s")
print(f"Iterations: {metadata.get('iterations')}")
```

## Usage Patterns

### Pattern 1: Simple Chain

```python
from langchain_core.prompts import ChatPromptTemplate
from utils.langchain_helpers import create_cortex_flow_llm

llm = create_cortex_flow_llm()

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}"),
    ("user", "{task}")
])

chain = prompt | llm

result = chain.invoke({
    "role": "research assistant",
    "task": "Find information about LangGraph"
})
```

### Pattern 2: Multi-Step Pipeline

```python
# Step 1: Research
research_prompt = ChatPromptTemplate.from_messages([
    ("user", "Research: {topic}")
])

# Step 2: Summarize
summary_prompt = ChatPromptTemplate.from_messages([
    ("user", "Summarize: {content}")
])

# Execute pipeline
research_chain = research_prompt | llm
summary_chain = summary_prompt | llm

research_result = research_chain.invoke({"topic": "AI agents"})
summary = summary_chain.invoke({"content": research_result.content})
```

### Pattern 3: RAG (Retrieval-Augmented Generation)

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def retrieve_docs(query):
    # Your retrieval logic here
    return "Retrieved context documents..."

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer based on context: {context}"),
    ("user", "{question}")
])

rag_chain = (
    {
        "context": lambda x: retrieve_docs(x["question"]),
        "question": lambda x: x["question"]
    }
    | prompt
    | llm
    | StrOutputParser()
)

answer = rag_chain.invoke({"question": "What are AI agents?"})
```

### Pattern 4: Streaming Responses

```python
# Synchronous streaming
for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)

# Asynchronous streaming
async for chunk in llm.astream("Explain LangChain"):
    print(chunk.content, end="", flush=True)
```

### Pattern 5: Conversational Chatbot

```python
from utils.langchain_helpers import create_conversational_chain

chain = create_conversational_chain(
    system_message="You are a helpful AI assistant",
    conversation_id="chat_session_123"
)

# Multi-turn conversation
response1 = chain.invoke({"input": "My name is Alice"})
response2 = chain.invoke({"input": "What's my name?"})  # Remembers Alice
```

## API Reference

### CortexFlowChatModel

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | `"http://localhost:8001/v1"` | API endpoint |
| `model_name` | str | `"cortex-flow"` | Model identifier |
| `temperature` | float | `0.7` | Sampling temperature (0-2) |
| `max_tokens` | int | `None` | Max tokens to generate |
| `conversation_id` | str | `None` | Conversation context ID |
| `timeout` | float | `120.0` | Request timeout (seconds) |

#### Methods

##### `invoke(input, config=None, **kwargs)`

Synchronous invocation.

**Parameters:**
- `input`: String or list of messages
- `config`: Optional configuration
- `**kwargs`: Additional parameters

**Returns:** `AIMessage`

**Example:**
```python
response = llm.invoke("What are AI agents?")
print(response.content)
```

##### `ainvoke(input, config=None, **kwargs)` (async)

Asynchronous invocation.

**Example:**
```python
response = await llm.ainvoke("What are AI agents?")
```

##### `stream(input, config=None, **kwargs)`

Synchronous streaming.

**Yields:** `ChatGenerationChunk`

**Example:**
```python
for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="")
```

##### `astream(input, config=None, **kwargs)` (async)

Asynchronous streaming.

**Example:**
```python
async for chunk in llm.astream("Tell me a story"):
    print(chunk.content, end="")
```

##### `get_last_usage()`

Get token usage from last completion.

**Returns:** `Dict[str, int]` with keys:
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`

##### `get_last_metadata()`

Get execution metadata from last completion.

**Returns:** `Dict[str, Any]` with keys:
- `agents_used`: List of agents involved
- `execution_time_seconds`: Total execution time
- `iterations`: Number of ReAct iterations

### Helper Functions

#### `create_cortex_flow_llm(**kwargs)`

Factory function to create `CortexFlowChatModel` with defaults.

**Example:**
```python
llm = create_cortex_flow_llm(
    temperature=0.5,
    conversation_id="session_123"
)
```

#### `create_research_prompt()`

Returns `ChatPromptTemplate` configured for research tasks.

**Variables:**
- `{topic}`: Research topic
- `{depth}`: Research depth (brief, comprehensive, etc.)

#### `create_analysis_prompt()`

Returns `ChatPromptTemplate` configured for analysis tasks.

**Variables:**
- `{data}`: Data to analyze
- `{focus}`: Analysis focus

#### `create_writing_prompt()`

Returns `ChatPromptTemplate` configured for writing tasks.

**Variables:**
- `{content}`: Content to transform
- `{format}`: Target format
- `{audience}`: Target audience

#### `extract_token_usage(llm)`

Extract token usage from last completion.

**Returns:** `Dict[str, int]`

#### `extract_execution_metadata(llm)`

Extract execution metadata from last completion.

**Returns:** `Dict[str, Any]`

#### `format_conversation_history(messages)`

Format conversation history for display.

**Parameters:**
- `messages`: List of `BaseMessage`

**Returns:** Formatted string

### CortexFlowUsageTracker

Callback handler for tracking token usage across multiple calls.

**Example:**
```python
from utils.langchain_helpers import CortexFlowUsageTracker

tracker = CortexFlowUsageTracker()

llm.invoke("Question 1", config={"callbacks": [tracker]})
llm.invoke("Question 2", config={"callbacks": [tracker]})

print(f"Total tokens: {tracker.total_tokens}")
print(f"Cost estimate: ${tracker.estimate_cost():.4f}")
```

## Examples

### Example 1: Research Assistant

```python
from utils.langchain_helpers import (
    create_cortex_flow_llm,
    create_research_prompt
)

llm = create_cortex_flow_llm()
prompt = create_research_prompt()

chain = prompt | llm

result = chain.invoke({
    "topic": "LangChain multi-agent systems",
    "depth": "comprehensive"
})

print(result.content)
```

### Example 2: Multi-Turn Chatbot

```python
class Chatbot:
    def __init__(self, conversation_id):
        self.llm = create_cortex_flow_llm(
            conversation_id=conversation_id
        )
        self.messages = []

    def send(self, user_input):
        self.messages.append(HumanMessage(content=user_input))
        response = self.llm.invoke(self.messages)
        self.messages.append(response)
        return response.content

bot = Chatbot("session_123")
print(bot.send("My favorite color is blue"))
print(bot.send("What's my favorite color?"))  # Remembers blue
```

### Example 3: Streaming RAG

```python
from langchain_core.output_parsers import StrOutputParser

# Retriever (mock)
def retrieve_docs(query):
    return "Context: LangChain enables building LLM applications..."

# RAG chain with streaming
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer based on: {context}"),
    ("user", "{question}")
])

chain = prompt | llm

# Stream response
for chunk in chain.stream({
    "context": retrieve_docs("What is LangChain?"),
    "question": "What is LangChain?"
}):
    print(chunk.content, end="", flush=True)
```

### Example 4: Token Tracking

```python
from utils.langchain_helpers import CortexFlowUsageTracker

tracker = CortexFlowUsageTracker()
llm = create_cortex_flow_llm()

questions = [
    "What are AI agents?",
    "How do they work?",
    "Give me examples"
]

for question in questions:
    llm.invoke(question, config={"callbacks": [tracker]})

print(f"Total calls: {tracker.call_count}")
print(f"Total tokens: {tracker.total_tokens}")
print(f"Estimated cost: ${tracker.estimate_cost():.4f}")
```

### Example 5: Parallel Processing

```python
import asyncio

async def process_queries():
    llm = create_cortex_flow_llm()

    queries = [
        "What is LangChain?",
        "What is LangGraph?",
        "What is LangSmith?"
    ]

    tasks = [llm.ainvoke(query) for query in queries]
    responses = await asyncio.gather(*tasks)

    for query, response in zip(queries, responses):
        print(f"Q: {query}")
        print(f"A: {response.content[:100]}...")
        print()

asyncio.run(process_queries())
```

## Best Practices

### 1. Use Conversation IDs for Context

Always provide a `conversation_id` when building conversational applications:

```python
# Good
llm = create_cortex_flow_llm(conversation_id=f"user_{user_id}_session_{session_id}")

# Bad
llm = create_cortex_flow_llm()  # No context preservation
```

### 2. Track Token Usage

Monitor token consumption for cost management:

```python
tracker = CortexFlowUsageTracker()

# Use tracker in all invocations
llm.invoke(prompt, config={"callbacks": [tracker]})

# Check periodically
if tracker.total_tokens > 10000:
    print("Warning: High token usage")
```

### 3. Handle Errors Gracefully

```python
try:
    response = llm.invoke(user_input)
except Exception as e:
    print(f"Error: {e}")
    response = "I'm having trouble processing that request."
```

### 4. Use Streaming for Long Responses

```python
# Good for long content
for chunk in llm.stream("Write a detailed report"):
    print(chunk.content, end="", flush=True)

# Bad for long content - blocks until complete
response = llm.invoke("Write a detailed report")
print(response.content)
```

### 5. Leverage Helper Functions

```python
# Good - use helpers for common patterns
llm = create_cortex_flow_llm(temperature=0.5)
prompt = create_research_prompt()

# Bad - manual setup every time
llm = CortexFlowChatModel(
    base_url="http://localhost:8001/v1",
    temperature=0.5
)
prompt = ChatPromptTemplate.from_messages([...])  # Repeated boilerplate
```

### 6. Separate Conversations by Context

```python
# Good - separate IDs for different contexts
technical_llm = create_cortex_flow_llm(conversation_id="tech_discussion_1")
casual_llm = create_cortex_flow_llm(conversation_id="casual_chat_1")

# Bad - sharing conversation ID across contexts
llm = create_cortex_flow_llm(conversation_id="mixed")
```

### 7. Use Async for Concurrent Operations

```python
# Good - parallel processing
async def process():
    tasks = [llm.ainvoke(q) for q in questions]
    return await asyncio.gather(*tasks)

# Bad - sequential processing
def process():
    return [llm.invoke(q) for q in questions]  # Slower
```

## Troubleshooting

### Server Not Running

**Error:** `Connection refused` or `Server not running`

**Solution:**
```bash
# Start OpenAI-compatible server
python -m servers.openai_compat_server

# Check health
curl http://localhost:8001/health
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'langchain_core'`

**Solution:**
```bash
pip install langchain-core langchain-community
```

### Context Not Maintained

**Problem:** Conversation context not preserved across messages

**Solution:** Ensure you're using the same `conversation_id`:
```python
# Correct
llm = create_cortex_flow_llm(conversation_id="session_123")
llm.invoke("Message 1")
llm.invoke("Message 2")  # Same llm instance

# Incorrect
llm1 = create_cortex_flow_llm()  # New instance, no conversation_id
llm1.invoke("Message 1")
llm2 = create_cortex_flow_llm()  # Different instance
llm2.invoke("Message 2")  # No shared context
```

### Token Usage Not Tracked

**Problem:** `get_last_usage()` returns `None`

**Solution:** Ensure server is returning usage information:
```python
# Check if tiktoken is installed on server
# Server-side: pip install tiktoken

# Verify usage in response
response = llm.invoke("Test")
usage = llm.get_last_usage()
print(usage)  # Should not be None
```

### Timeout Errors

**Problem:** Requests timing out

**Solution:** Increase timeout or optimize prompts:
```python
# Increase timeout
llm = create_cortex_flow_llm(timeout=300.0)  # 5 minutes

# Or make prompts more concise
prompt = "Briefly explain..."  # Better than "Write a comprehensive..."
```

### Streaming Issues

**Problem:** Streaming returns all content at once

**Solution:** This is expected behavior if the underlying model doesn't support true streaming. Check server logs for streaming configuration.

## Integration with LangChain Ecosystem

### LangChain Tools

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool

# Define tools
tools = [
    Tool(name="Search", func=search_function, description="Search the web"),
    Tool(name="Calculator", func=calculate, description="Perform calculations")
]

# Create agent with Cortex Flow
llm = create_cortex_flow_llm()
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

result = agent_executor.invoke({"input": "What is 123 * 456?"})
```

### LangChain Memory

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()

# Use with chains
chain = create_conversational_chain(llm=llm)
response = chain.invoke({"input": "Hello", "history": memory.chat_memory})
```

### Vector Stores

```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

# Use with Cortex Flow for RAG
retriever = vectorstore.as_retriever()
rag_chain = create_rag_chain(retriever, llm)
```

## Performance Considerations

### Response Times

- **Simple queries**: 1-3 seconds
- **Research tasks**: 5-10 seconds (multi-agent orchestration)
- **Complex analysis**: 10-30 seconds (multiple agent iterations)

### Token Limits

- Default max context: 8,000 tokens
- Configurable via `OPENAI_COMPAT_MAX_CONTEXT_TOKENS`
- Monitor with `CortexFlowUsageTracker`

### Concurrent Requests

Use async methods for parallel processing:

```python
# Efficient
async def process_batch(queries):
    llm = create_cortex_flow_llm()
    tasks = [llm.ainvoke(q) for q in queries]
    return await asyncio.gather(*tasks)

# Less efficient
def process_batch(queries):
    llm = create_cortex_flow_llm()
    return [llm.invoke(q) for q in queries]
```

## Next Steps

- **Explore Examples**: Run examples in `examples/langchain/`
- **Run Tests**: `pytest tests/test_langchain_integration.py -v`
- **Build Applications**: Start building with LangChain + Cortex Flow
- **Read OpenAI API Docs**: `docs/api/openai_compatibility.md`
- **Check Architecture**: `docs/architecture/README.md`

## Support

For issues or questions:
- GitHub Issues: [cortex-flow/issues](https://github.com/your-org/cortex-flow/issues)
- Documentation: Full docs at `/docs`
- Examples: Browse `examples/langchain/`

## Changelog

### v1.0.0 (Current)

- ✅ Full `BaseChatModel` implementation
- ✅ Sync and async methods (`invoke`, `ainvoke`, `stream`, `astream`)
- ✅ LCEL compatibility
- ✅ Conversation context management
- ✅ Token usage tracking
- ✅ Execution metadata access
- ✅ Helper functions and utilities
- ✅ Comprehensive examples and tests

### Future Enhancements

- 🔜 Function calling support
- 🔜 Tool use integration
- 🔜 Structured output parsing
- 🔜 Advanced memory patterns
- 🔜 LangSmith integration examples
