# LangChain Examples

This directory contains practical examples demonstrating the integration between Cortex Flow and LangChain.

## Prerequisites

1. **OpenAI-Compatible API Server Running**:
```bash
python -m servers.openai_compat_server
```

2. **LangChain Installed**:
```bash
pip install langchain-core langchain-community
```

## Examples

### 01_basic_usage.py

**Topics Covered:**
- Creating a `CortexFlowChatModel` instance
- Simple chat completions
- Accessing token usage and metadata
- Making multiple invocations

**Run:**
```bash
python examples/langchain/01_basic_usage.py
```

**Key Concepts:**
- Basic LLM setup
- Token tracking
- Execution metadata
- Sequential requests

---

### 02_chains_and_lcel.py

**Topics Covered:**
- Creating chains using LCEL (LangChain Expression Language)
- Using prompt templates
- Chaining multiple operations
- Multi-step and parallel chains
- Conditional routing

**Run:**
```bash
python examples/langchain/02_chains_and_lcel.py
```

**Key Concepts:**
- LCEL `|` operator
- Prompt templates
- Sequential chains
- Research/Analysis/Writing patterns
- Conditional logic

---

### 03_conversation_memory.py

**Topics Covered:**
- Using `conversation_id` for context persistence
- Building multi-turn conversations
- Managing conversation history
- Session management
- Complete chatbot implementation

**Run:**
```bash
python examples/langchain/03_conversation_memory.py
```

**Key Concepts:**
- Conversation context
- Memory management
- Multi-turn dialogues
- Session separation
- Chatbot patterns

---

### 04_streaming.py

**Topics Covered:**
- Streaming chat completions
- Using async streaming
- Real-time token-by-token output
- Streaming with callbacks
- Collecting streamed chunks

**Run:**
```bash
python examples/langchain/04_streaming.py
```

**Key Concepts:**
- Synchronous streaming
- Asynchronous streaming
- Callback handlers
- Stream collectors
- Streaming conversations

---

### 05_agents_and_rag.py

**Topics Covered:**
- Using CortexFlowChatModel in LangChain agents
- RAG (Retrieval-Augmented Generation) pipelines
- Tool-using patterns
- Document Q&A
- Retrieval QA chains

**Run:**
```bash
python examples/langchain/05_agents_and_rag.py
```

**Key Concepts:**
- RAG patterns
- Document retrieval
- Q&A systems
- Tool integration
- Context-based answering

## Quick Start

Run all examples in sequence:

```bash
cd /path/to/cortex-flow
python examples/langchain/01_basic_usage.py
python examples/langchain/02_chains_and_lcel.py
python examples/langchain/03_conversation_memory.py
python examples/langchain/04_streaming.py
python examples/langchain/05_agents_and_rag.py
```

Or run individually based on your learning goals.

## Example Output

Each example includes:
- ✅ Success indicators
- Detailed console output
- Explanatory messages
- Performance metrics (where applicable)

## Learning Path

**Beginner:**
1. Start with `01_basic_usage.py` to understand the basics
2. Move to `02_chains_and_lcel.py` to learn LCEL
3. Try `03_conversation_memory.py` for conversational apps

**Intermediate:**
4. Explore `04_streaming.py` for real-time responses
5. Study `05_agents_and_rag.py` for advanced patterns

**Advanced:**
- Combine patterns from multiple examples
- Build custom chains and agents
- Integrate with LangChain ecosystem components

## Troubleshooting

### Server Not Running

If you see connection errors:
```bash
# Terminal 1: Start supervisor
python -m servers.supervisor_server

# Terminal 2: Start OpenAI API
python -m servers.openai_compat_server

# Check health
curl http://localhost:8001/health
```

### Import Errors

If you see `ModuleNotFoundError`:
```bash
pip install langchain-core langchain-community
```

### Slow Responses

If examples run slowly:
- Check server logs for errors
- Verify API keys are configured
- Ensure no rate limiting is occurring

## Next Steps

After running these examples:

1. **Read Documentation**: `docs/integrations/langchain.md`
2. **Run Tests**: `pytest tests/test_langchain_integration.py -v`
3. **Build Your App**: Start building with LangChain + Cortex Flow
4. **Explore Ecosystem**: Try LangChain tools, agents, retrievers

## Resources

- **LangChain Docs**: https://python.langchain.com/
- **Cortex Flow API Docs**: `docs/api/openai_compatibility.md`
- **Integration Guide**: `docs/integrations/langchain.md`
- **Test Suite**: `tests/test_langchain_integration.py`

## Support

For questions or issues:
- Check `docs/integrations/langchain.md` for detailed documentation
- Review test suite for additional examples
- Open GitHub issue for bugs or feature requests

---

**Happy Coding!** 🚀
