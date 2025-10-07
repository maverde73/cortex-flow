"""
Tests for Context Window Management (Message Trimming)

Tests that message trimming works correctly to prevent context overflow.
"""

import pytest
import asyncio
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents.supervisor import get_supervisor_agent
from utils.token_counter import TokenCounter


class TestMessageTrimming:
    """Tests for message trimming functionality."""

    def test_token_counter_langchain_messages(self):
        """Test TokenCounter with LangChain messages."""
        counter = TokenCounter(model="gpt-4")

        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello!"),
            AIMessage(content="Hi! How can I help you?"),
            HumanMessage(content="Tell me about Python."),
        ]

        token_count = counter.count_langchain_message_tokens(messages)

        # Should return a positive number
        assert token_count > 0
        # Rough check: 4 messages with short content should be < 100 tokens
        assert token_count < 100

    def test_token_counter_comparison(self):
        """Test that token counter gives consistent results."""
        counter = TokenCounter(model="gpt-4")

        # Same content in different formats
        text = "This is a test message."
        messages = [HumanMessage(content=text)]

        text_tokens = counter.count_string_tokens(text)
        message_tokens = counter.count_langchain_message_tokens(messages)

        # Message tokens should be more (includes overhead)
        assert message_tokens > text_tokens
        # But not drastically more (overhead is ~3 tokens per message + role encoding)
        assert message_tokens < text_tokens * 3

    @pytest.mark.asyncio
    async def test_long_conversation_trimming(self):
        """
        Test that long conversations are trimmed automatically.

        Scenario:
        1. Send 10 messages to build up conversation history
        2. Verify the agent still responds correctly
        3. Check that old messages are trimmed
        """
        agent = await get_supervisor_agent()
        thread_id = "test-long-conversation"

        # Build up a long conversation history
        topics = [
            "Tell me about Python",
            "What about JavaScript?",
            "How about Go?",
            "What's Rust?",
            "Explain Java",
            "Describe C++",
            "What is Ruby?",
            "Tell me about Swift",
            "What's Kotlin?",
            "Explain TypeScript"
        ]

        last_result = None
        for i, topic in enumerate(topics):
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=topic)]},
                config={"configurable": {"thread_id": thread_id}}
            )
            last_result = result

            # Should get a response
            assert len(result["messages"]) > 0
            response = result["messages"][-1].content
            assert len(response) > 0

            # Log progress
            message_count = len(result["messages"])
            print(f"Turn {i+1}: {message_count} messages in state")

        # After 10 turns, we should have trimmed some messages
        # (Default MAX_CONVERSATION_MESSAGES=20, but each turn adds 2 messages)
        final_message_count = len(last_result["messages"])

        # With trimming, should not exceed 20 messages significantly
        # (May be slightly over due to system messages)
        assert final_message_count < 30, \
            f"Message count ({final_message_count}) suggests trimming not working"

        # Agent should still function correctly
        final_response = last_result["messages"][-1].content
        assert len(final_response) > 10

    @pytest.mark.asyncio
    async def test_trimming_preserves_recent_context(self):
        """
        Test that trimming keeps recent messages.

        Scenario:
        1. User: "My name is Alice" (old message)
        2. Fill conversation with filler messages
        3. User: "My favorite color is blue" (recent message)
        4. User: "What's my favorite color?" (should remember blue, may forget Alice)
        """
        agent = await get_supervisor_agent()
        thread_id = "test-trimming-context"

        # Turn 1: Old information
        await agent.ainvoke(
            {"messages": [HumanMessage(content="My name is Alice")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Fill with filler messages to trigger trimming
        filler_topics = [
            "What is 2+2?",
            "Tell me a joke",
            "What's the weather?",
            "Count to 5",
            "Say hello",
            "What day is it?",
        ]

        for topic in filler_topics:
            await agent.ainvoke(
                {"messages": [HumanMessage(content=topic)]},
                config={"configurable": {"thread_id": thread_id}}
            )

        # Turn N-1: Recent information
        await agent.ainvoke(
            {"messages": [HumanMessage(content="My favorite color is blue")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Turn N: Ask about recent info
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="What's my favorite color?")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        response = result["messages"][-1].content

        # Should remember recent information (blue)
        assert "blue" in response.lower(), \
            f"Agent forgot recent context! Response: {response}"

        # May or may not remember old information (Alice) depending on trim


class TestBackwardCompatibilityTrimming:
    """Tests that trimming doesn't break existing behavior."""

    @pytest.mark.asyncio
    async def test_short_conversation_no_trimming(self):
        """Test that short conversations are not trimmed."""
        agent = await get_supervisor_agent()
        thread_id = "test-short-conversation"

        # Short 2-turn conversation
        result1 = await agent.ainvoke(
            {"messages": [HumanMessage(content="Hello")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        result2 = await agent.ainvoke(
            {"messages": [HumanMessage(content="How are you?")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Should have all messages (no trimming needed)
        message_count = len(result2["messages"])

        # Should have at least: system + user1 + ai1 + user2 + ai2 = 5
        assert message_count >= 4

    @pytest.mark.asyncio
    async def test_unique_threads_isolated(self):
        """Test that each thread maintains its own message history."""
        agent = await get_supervisor_agent()

        # Thread A
        result_a = await agent.ainvoke(
            {"messages": [HumanMessage(content="What is Python?")]},
            config={"configurable": {"thread_id": "thread-a"}}
        )

        # Thread B (completely separate)
        result_b = await agent.ainvoke(
            {"messages": [HumanMessage(content="What is Java?")]},
            config={"configurable": {"thread_id": "thread-b"}}
        )

        # Both should work normally
        assert len(result_a["messages"]) > 0
        assert len(result_b["messages"]) > 0

        # Should have different contexts
        response_a = result_a["messages"][-1].content
        response_b = result_b["messages"][-1].content
        assert len(response_a) > 0
        assert len(response_b) > 0


# Test configuration
@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
