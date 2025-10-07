"""
Integration tests for LangChain interface.

Tests the CortexFlowChatModel and helper functions to ensure
proper integration with LangChain ecosystem.
"""

import pytest
import asyncio
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Import components to test
try:
    from utils.langchain_chat_model import CortexFlowChatModel
    from utils.langchain_helpers import (
        create_cortex_flow_llm,
        create_research_prompt,
        create_analysis_prompt,
        create_writing_prompt,
        extract_token_usage,
        extract_execution_metadata,
        format_conversation_history,
        CortexFlowUsageTracker
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    pytest.skip("LangChain integration not available", allow_module_level=True)


# Base URL for tests
BASE_URL = "http://localhost:8001/v1"


class TestCortexFlowChatModel:
    """Tests for CortexFlowChatModel."""

    def test_model_creation(self):
        """Test creating a CortexFlowChatModel instance."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        assert llm._llm_type == "cortex-flow"
        assert llm.model_name == "cortex-flow"
        assert llm.temperature == 0.7
        assert llm.base_url == BASE_URL

    def test_model_with_custom_params(self):
        """Test model with custom parameters."""
        llm = CortexFlowChatModel(
            base_url=BASE_URL,
            model_name="custom-model",
            temperature=0.5,
            max_tokens=1000,
            conversation_id="test_conv_123"
        )

        assert llm.model_name == "custom-model"
        assert llm.temperature == 0.5
        assert llm.max_tokens == 1000
        assert llm.conversation_id == "test_conv_123"

    def test_invoke_simple(self):
        """Test simple invocation."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        response = llm.invoke("Say hello in one word")

        assert response is not None
        assert hasattr(response, 'content')
        assert len(response.content) > 0

    def test_invoke_with_messages(self):
        """Test invocation with message list."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is 2+2? Answer with just the number.")
        ]

        response = llm.invoke(messages)

        assert response is not None
        assert hasattr(response, 'content')
        assert "4" in response.content

    def test_conversation_context(self):
        """Test conversation context maintenance."""
        conversation_id = "test_context_123"
        llm = CortexFlowChatModel(
            base_url=BASE_URL,
            conversation_id=conversation_id
        )

        # First message
        response1 = llm.invoke("My favorite color is red.")
        assert response1 is not None

        # Second message - should remember context
        response2 = llm.invoke("What is my favorite color?")
        assert "red" in response2.content.lower()

    def test_token_usage_tracking(self):
        """Test token usage tracking."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        response = llm.invoke("Hello")

        usage = llm.get_last_usage()
        assert usage is not None
        assert 'total_tokens' in usage
        assert 'prompt_tokens' in usage
        assert 'completion_tokens' in usage
        assert usage['total_tokens'] > 0

    def test_metadata_extraction(self):
        """Test execution metadata extraction."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        response = llm.invoke("Test message")

        metadata = llm.get_last_metadata()
        assert metadata is not None
        # Metadata structure depends on server implementation

    def test_streaming(self):
        """Test streaming responses."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        chunks = []
        for chunk in llm.stream("Count to 3"):
            chunks.append(chunk)
            assert hasattr(chunk, 'content')

        assert len(chunks) > 0

        # Reconstruct full response
        full_text = "".join(c.content for c in chunks)
        assert len(full_text) > 0

    @pytest.mark.asyncio
    async def test_async_invoke(self):
        """Test async invocation."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        response = await llm.ainvoke("Say hello in one word")

        assert response is not None
        assert hasattr(response, 'content')
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_async_streaming(self):
        """Test async streaming."""
        llm = CortexFlowChatModel(base_url=BASE_URL)

        chunks = []
        async for chunk in llm.astream("Count to 3"):
            chunks.append(chunk)
            assert hasattr(chunk, 'content')

        assert len(chunks) > 0


class TestLangChainHelpers:
    """Tests for helper functions."""

    def test_create_cortex_flow_llm(self):
        """Test LLM factory function."""
        llm = create_cortex_flow_llm(
            base_url=BASE_URL,
            temperature=0.5
        )

        assert isinstance(llm, CortexFlowChatModel)
        assert llm.temperature == 0.5

    def test_create_research_prompt(self):
        """Test research prompt creation."""
        prompt = create_research_prompt()

        assert prompt is not None
        assert isinstance(prompt, ChatPromptTemplate)

        # Format prompt to verify structure
        messages = prompt.format_messages(
            topic="AI agents",
            depth="comprehensive"
        )
        assert len(messages) >= 2

    def test_create_analysis_prompt(self):
        """Test analysis prompt creation."""
        prompt = create_analysis_prompt()

        assert prompt is not None
        assert isinstance(prompt, ChatPromptTemplate)

    def test_create_writing_prompt(self):
        """Test writing prompt creation."""
        prompt = create_writing_prompt()

        assert prompt is not None
        assert isinstance(prompt, ChatPromptTemplate)

    def test_extract_token_usage(self):
        """Test token usage extraction."""
        llm = CortexFlowChatModel(base_url=BASE_URL)
        llm.invoke("Test")

        usage = extract_token_usage(llm)

        assert usage is not None
        assert 'total_tokens' in usage

    def test_extract_execution_metadata(self):
        """Test metadata extraction."""
        llm = CortexFlowChatModel(base_url=BASE_URL)
        llm.invoke("Test")

        metadata = extract_execution_metadata(llm)

        assert metadata is not None

    def test_format_conversation_history(self):
        """Test conversation history formatting."""
        messages = [
            SystemMessage(content="System message"),
            HumanMessage(content="User message"),
            AIMessage(content="Assistant message")
        ]

        formatted = format_conversation_history(messages)

        assert "[SYSTEM]" in formatted
        assert "[USER]" in formatted
        assert "[ASSISTANT]" in formatted
        assert "System message" in formatted
        assert "User message" in formatted
        assert "Assistant message" in formatted

    def test_usage_tracker(self):
        """Test usage tracker callback."""
        tracker = CortexFlowUsageTracker()

        assert tracker.total_tokens == 0
        assert tracker.call_count == 0

        # Tracker would be updated via callbacks in real usage
        # Here we just test the structure
        assert hasattr(tracker, 'estimate_cost')
        assert hasattr(tracker, 'reset')


class TestLCELIntegration:
    """Tests for LCEL (LangChain Expression Language) integration."""

    def test_simple_chain(self):
        """Test basic LCEL chain."""
        llm = create_cortex_flow_llm(base_url=BASE_URL)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("user", "{query}")
        ])

        chain = prompt | llm | StrOutputParser()

        result = chain.invoke({"query": "Say hello in one word"})

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_chain_with_multiple_steps(self):
        """Test multi-step chain."""
        llm = create_cortex_flow_llm(base_url=BASE_URL)

        # First step
        step1_prompt = ChatPromptTemplate.from_messages([
            ("user", "List one AI framework. Just the name.")
        ])

        # Second step
        step2_prompt = ChatPromptTemplate.from_messages([
            ("user", "Describe {framework} in one sentence.")
        ])

        # Execute first step
        chain1 = step1_prompt | llm | StrOutputParser()
        framework = chain1.invoke({})

        # Execute second step
        chain2 = step2_prompt | llm | StrOutputParser()
        description = chain2.invoke({"framework": framework})

        assert framework is not None
        assert description is not None
        assert len(description) > 0

    def test_research_chain(self):
        """Test research chain with helper."""
        llm = create_cortex_flow_llm(base_url=BASE_URL)
        prompt = create_research_prompt()

        chain = prompt | llm | StrOutputParser()

        result = chain.invoke({
            "topic": "LangChain",
            "depth": "brief"
        })

        assert result is not None
        assert len(result) > 0


class TestConversationalPatterns:
    """Tests for conversational patterns."""

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation."""
        conversation_id = "test_multi_turn"
        llm = create_cortex_flow_llm(
            base_url=BASE_URL,
            conversation_id=conversation_id
        )

        # Turn 1
        response1 = llm.invoke("My name is Alice")
        assert response1 is not None

        # Turn 2 - should remember
        response2 = llm.invoke("What is my name?")
        assert "alice" in response2.content.lower()

    def test_conversation_with_system_message(self):
        """Test conversation with system message."""
        llm = create_cortex_flow_llm(base_url=BASE_URL)

        messages = [
            SystemMessage(content="You are a math tutor. Be concise."),
            HumanMessage(content="What is 5 + 3?")
        ]

        response = llm.invoke(messages)

        assert response is not None
        assert "8" in response.content


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_base_url(self):
        """Test handling of invalid base URL."""
        llm = CortexFlowChatModel(base_url="http://invalid-url:9999/v1")

        with pytest.raises(Exception):
            llm.invoke("Test")

    def test_timeout_handling(self):
        """Test timeout handling."""
        llm = CortexFlowChatModel(
            base_url=BASE_URL,
            timeout=0.001  # Very short timeout
        )

        with pytest.raises(Exception):
            llm.invoke("Test")


class TestIntegrationScenarios:
    """End-to-end integration scenarios."""

    def test_chatbot_scenario(self):
        """Test complete chatbot scenario."""
        llm = create_cortex_flow_llm(
            base_url=BASE_URL,
            conversation_id="chatbot_test"
        )

        # Simulate chatbot interaction
        conversations = [
            ("What are AI agents?", None),
            ("Give me an example", None),
            ("How do they work?", None)
        ]

        for question, _ in conversations:
            response = llm.invoke(question)
            assert response is not None
            assert len(response.content) > 0

    def test_rag_pattern(self):
        """Test RAG pattern."""
        llm = create_cortex_flow_llm(base_url=BASE_URL)

        context = "LangChain is a framework for building LLM applications."

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Answer based on context: {context}"),
            ("user", "{question}")
        ])

        chain = prompt | llm | StrOutputParser()

        result = chain.invoke({
            "context": context,
            "question": "What is LangChain?"
        })

        assert "langchain" in result.lower() or "framework" in result.lower()

    @pytest.mark.asyncio
    async def test_async_scenario(self):
        """Test async usage scenario."""
        llm = create_cortex_flow_llm(base_url=BASE_URL)

        tasks = [
            llm.ainvoke("Question 1"),
            llm.ainvoke("Question 2"),
            llm.ainvoke("Question 3")
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 3
        for response in responses:
            assert response is not None
            assert hasattr(response, 'content')


# Pytest configuration
@pytest.fixture(scope="module")
def check_server():
    """Check if OpenAI-compatible server is running."""
    import httpx

    try:
        response = httpx.get(f"{BASE_URL.replace('/v1', '')}/health", timeout=2.0)
        if response.status_code != 200:
            pytest.skip("Server not healthy")
    except Exception:
        pytest.skip("OpenAI-compatible server not running. Start with: python -m servers.openai_compat_server")


@pytest.fixture(autouse=True)
def ensure_server(check_server):
    """Ensure server is running before each test."""
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
