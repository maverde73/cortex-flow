"""
Example 4: Streaming Responses

This example demonstrates:
- Streaming chat completions
- Using async streaming
- Real-time token-by-token output
- Streaming with callbacks
"""

import asyncio
from utils.langchain_helpers import (
    create_cortex_flow_llm,
    create_streaming_handler
)
from langchain_core.prompts import ChatPromptTemplate


def example_basic_streaming():
    """Basic synchronous streaming."""
    print("BASIC STREAMING EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    print("Prompt: Tell me a short story about an AI agent")
    print()
    print("Response (streaming): ", end="", flush=True)

    # Stream response
    for chunk in llm.stream("Tell me a short story about an AI agent (max 3 sentences)"):
        print(chunk.content, end="", flush=True)

    print("\n")


async def example_async_streaming():
    """Asynchronous streaming."""
    print("ASYNC STREAMING EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    print("Prompt: Explain LangChain in simple terms")
    print()
    print("Response (async streaming): ", end="", flush=True)

    # Async stream
    async for chunk in llm.astream("Explain LangChain in simple terms (max 2 sentences)"):
        print(chunk.content, end="", flush=True)
        await asyncio.sleep(0.01)  # Small delay for visual effect

    print("\n")


def example_streaming_with_callback():
    """Streaming with callback handler."""
    print("STREAMING WITH CALLBACK EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()
    handler = create_streaming_handler()

    print("Prompt: What are the benefits of multi-agent systems?")
    print()
    print("Response (with callback): ", end="", flush=True)

    # Stream with callback - handler prints to stdout automatically
    for chunk in llm.stream(
        "What are the benefits of multi-agent systems? (List 3 benefits)",
        config={"callbacks": [handler]}
    ):
        pass  # Callback handler prints automatically

    print("\n")


def example_streaming_chain():
    """Streaming through a chain."""
    print("STREAMING CHAIN EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Be concise."),
        ("user", "{query}")
    ])

    # Create chain
    chain = prompt | llm

    print("Prompt: Compare LangChain and LangGraph")
    print()
    print("Response (streaming chain): ", end="", flush=True)

    # Stream through chain
    for chunk in chain.stream({"query": "Compare LangChain and LangGraph (max 3 sentences)"}):
        print(chunk.content, end="", flush=True)

    print("\n")


async def example_multiple_async_streams():
    """Multiple async streams in parallel."""
    print("MULTIPLE ASYNC STREAMS EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    async def stream_response(question: str, label: str):
        """Stream a single response."""
        print(f"\n{label}: {question}")
        print(f"Response: ", end="", flush=True)

        async for chunk in llm.astream(question):
            print(chunk.content, end="", flush=True)

        print()

    # Create multiple streaming tasks
    questions = [
        ("What is LangChain?", "Q1"),
        ("What is LangGraph?", "Q2"),
        ("What is LangSmith?", "Q3")
    ]

    # Note: In practice, these would run sequentially due to API rate limits
    # But the pattern shows how to structure parallel async streaming
    for question, label in questions:
        await stream_response(question + " (One sentence)", label)


def example_streaming_with_metadata():
    """Streaming with metadata tracking."""
    print("STREAMING WITH METADATA EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    print("Prompt: Explain AI agent architectures")
    print()

    # Collect chunks
    chunks = []
    print("Response: ", end="", flush=True)

    for chunk in llm.stream("Explain AI agent architectures (max 2 sentences)"):
        print(chunk.content, end="", flush=True)
        chunks.append(chunk)

    print("\n")

    # Show metadata
    print(f"Total chunks received: {len(chunks)}")
    print(f"Total characters: {sum(len(c.content) for c in chunks)}")
    print()


class StreamCollector:
    """Helper class to collect streaming chunks."""

    def __init__(self):
        self.chunks = []
        self.complete_text = ""

    def collect(self, chunk):
        """Collect a chunk."""
        self.chunks.append(chunk)
        self.complete_text += chunk.content

    def get_text(self) -> str:
        """Get complete text."""
        return self.complete_text

    def get_chunk_count(self) -> int:
        """Get number of chunks."""
        return len(self.chunks)


def example_stream_collector():
    """Using stream collector helper."""
    print("STREAM COLLECTOR EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()
    collector = StreamCollector()

    print("Prompt: What are ReAct agents?")
    print()
    print("Response: ", end="", flush=True)

    # Stream and collect
    for chunk in llm.stream("What are ReAct agents? (max 2 sentences)"):
        print(chunk.content, end="", flush=True)
        collector.collect(chunk)

    print("\n")

    # Show collected data
    print(f"Collected {collector.get_chunk_count()} chunks")
    print(f"Total text length: {len(collector.get_text())} characters")
    print(f"Complete text: {collector.get_text()[:100]}...")
    print()


async def example_streaming_conversation():
    """Streaming multi-turn conversation."""
    print("STREAMING CONVERSATION EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm(conversation_id="streaming_conv_001")

    conversations = [
        "My favorite topic is artificial intelligence.",
        "What did I just tell you my favorite topic was?",
        "Tell me something interesting about it."
    ]

    for i, message in enumerate(conversations, 1):
        print(f"Turn {i}: {message}")
        print(f"Response: ", end="", flush=True)

        async for chunk in llm.astream(message):
            print(chunk.content, end="", flush=True)

        print("\n")


def main():
    print("=" * 70)
    print("EXAMPLE 4: STREAMING RESPONSES")
    print("=" * 70)
    print()

    # Synchronous examples
    example_basic_streaming()
    example_streaming_with_callback()
    example_streaming_chain()
    example_streaming_with_metadata()
    example_stream_collector()

    # Asynchronous examples
    print("Running async examples...")
    print()
    asyncio.run(example_async_streaming())
    asyncio.run(example_multiple_async_streams())
    asyncio.run(example_streaming_conversation())

    print("=" * 70)
    print("EXAMPLE 4 COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
