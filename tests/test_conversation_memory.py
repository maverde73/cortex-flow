"""
Tests for Conversation Memory (Chatbot Features)

Tests checkpointer integration, multi-turn conversations,
thread isolation, and message trimming.
"""

import pytest
import asyncio
from langchain_core.messages import HumanMessage, AIMessage

from agents.supervisor import get_checkpointer, get_supervisor_agent


class TestCheckpointerFactory:
    """Tests for checkpointer factory function."""

    def test_checkpointer_initialization(self):
        """Test checkpointer can be initialized."""
        checkpointer = get_checkpointer()
        assert checkpointer is not None
        # Should be MemorySaver by default
        assert "Saver" in type(checkpointer).__name__

    def test_checkpointer_type_memory(self, monkeypatch):
        """Test memory checkpointer type."""
        monkeypatch.setenv("CHECKPOINTER_TYPE", "memory")
        checkpointer = get_checkpointer()
        assert checkpointer is not None


class TestConversationMemory:
    """Tests for conversation memory persistence."""

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_basic(self):
        """
        Test basic multi-turn conversation with memory.

        Scenario:
        1. User: "My name is Alice"
        2. User: "What's my name?" (should remember "Alice")
        """
        agent = await get_supervisor_agent()

        thread_id = "test-basic-memory"

        # Turn 1: Introduce name
        result1 = await agent.ainvoke(
            {"messages": [HumanMessage(content="My name is Alice")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        response1 = result1["messages"][-1].content
        assert "Alice" in response1 or "alice" in response1.lower()

        # Turn 2: Ask about name (should remember!)
        result2 = await agent.ainvoke(
            {"messages": [HumanMessage(content="What's my name?")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        response2 = result2["messages"][-1].content

        # Should remember the name from Turn 1
        assert "Alice" in response2 or "alice" in response2.lower(), \
            f"Agent forgot the name! Response: {response2}"

    @pytest.mark.asyncio
    async def test_thread_isolation(self):
        """
        Test that different threads are isolated.

        Thread 1: User is Alice
        Thread 2: User is Bob
        Each thread should remember its own name only.
        """
        agent = await get_supervisor_agent()

        # Thread 1: Alice
        thread1 = "test-thread-alice"
        await agent.ainvoke(
            {"messages": [HumanMessage(content="My name is Alice")]},
            config={"configurable": {"thread_id": thread1}}
        )

        # Thread 2: Bob
        thread2 = "test-thread-bob"
        await agent.ainvoke(
            {"messages": [HumanMessage(content="My name is Bob")]},
            config={"configurable": {"thread_id": thread2}}
        )

        # Query Thread 1
        result1 = await agent.ainvoke(
            {"messages": [HumanMessage(content="What's my name?")]},
            config={"configurable": {"thread_id": thread1}}
        )
        response1 = result1["messages"][-1].content

        # Query Thread 2
        result2 = await agent.ainvoke(
            {"messages": [HumanMessage(content="What's my name?")]},
            config={"configurable": {"thread_id": thread2}}
        )
        response2 = result2["messages"][-1].content

        # Thread 1 should remember Alice, not Bob
        assert "Alice" in response1 or "alice" in response1.lower()
        assert "Bob" not in response1 and "bob" not in response1.lower()

        # Thread 2 should remember Bob, not Alice
        assert "Bob" in response2 or "bob" in response2.lower()
        assert "Alice" not in response2 and "alice" not in response2.lower()

    @pytest.mark.asyncio
    async def test_conversation_continuity(self):
        """
        Test conversation context is maintained across multiple turns.

        3-turn conversation about a topic.
        """
        agent = await get_supervisor_agent()
        thread_id = "test-continuity"

        # Turn 1
        result1 = await agent.ainvoke(
            {"messages": [HumanMessage(content="I love Python programming")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Turn 2: Reference previous context
        result2 = await agent.ainvoke(
            {"messages": [HumanMessage(content="What are some benefits of it?")]},
            config={"configurable": {"thread_id": thread_id}}
        )
        response2 = result2["messages"][-1].content

        # Should understand "it" refers to Python
        assert "python" in response2.lower() or "programming" in response2.lower()

        # Turn 3: Continue conversation
        result3 = await agent.ainvoke(
            {"messages": [HumanMessage(content="Thanks! Can you recommend libraries?")]},
            config={"configurable": {"thread_id": thread_id}}
        )
        response3 = result3["messages"][-1].content

        # Should still be in Python context
        assert len(response3) > 20  # Got a real response


class TestBackwardCompatibility:
    """Tests for backward compatibility (stateless mode)."""

    @pytest.mark.asyncio
    async def test_works_without_thread_id(self):
        """Test agent works without thread_id (stateless)."""
        agent = await get_supervisor_agent()

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="Hello")]},
            config={}  # No thread_id
        )

        assert "messages" in result
        assert len(result["messages"]) > 0

    @pytest.mark.asyncio
    async def test_stateless_no_memory(self):
        """Test that without thread_id, no memory is preserved."""
        agent = await get_supervisor_agent()

        # Call 1
        await agent.ainvoke(
            {"messages": [HumanMessage(content="My name is Charlie")]},
            config={}  # No thread_id = stateless
        )

        # Call 2 (separate invocation, no thread)
        result2 = await agent.ainvoke(
            {"messages": [HumanMessage(content="What's my name?")]},
            config={}
        )
        response2 = result2["messages"][-1].content

        # Should NOT remember Charlie (stateless)
        # (This test might be flaky if LLM halluc inates, but generally should fail to recall)
        assert "Charlie" not in response2 or "don't know" in response2.lower()


# Test configuration
@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
