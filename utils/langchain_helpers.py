"""
Helper utilities for LangChain integration with Cortex Flow.

This module provides utility functions for working with the CortexFlowChatModel,
including message conversion, prompt templates, and common patterns.
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage


def create_cortex_flow_llm(
    base_url: str = "http://localhost:8001/v1",
    model_name: str = "cortex-flow",
    temperature: float = 0.7,
    conversation_id: Optional[str] = None,
    **kwargs: Any
):
    """
    Factory function to create CortexFlowChatModel with sensible defaults.

    Args:
        base_url: Base URL for Cortex Flow API
        model_name: Model identifier
        temperature: Sampling temperature
        conversation_id: Optional conversation ID for context
        **kwargs: Additional parameters for CortexFlowChatModel

    Returns:
        Configured CortexFlowChatModel instance

    Example:
        ```python
        from utils.langchain_helpers import create_cortex_flow_llm

        # Basic usage
        llm = create_cortex_flow_llm()

        # With conversation context
        llm = create_cortex_flow_llm(conversation_id="user_123_session_1")

        # Custom configuration
        llm = create_cortex_flow_llm(
            temperature=0.5,
            max_tokens=1000,
            timeout=180.0
        )
        ```
    """
    from utils.langchain_chat_model import CortexFlowChatModel

    return CortexFlowChatModel(
        base_url=base_url,
        model_name=model_name,
        temperature=temperature,
        conversation_id=conversation_id,
        **kwargs
    )


def create_research_prompt() -> Any:
    """
    Create a prompt template for research tasks.

    Returns:
        ChatPromptTemplate configured for research

    Example:
        ```python
        from utils.langchain_helpers import create_research_prompt, create_cortex_flow_llm

        llm = create_cortex_flow_llm()
        prompt = create_research_prompt()

        chain = prompt | llm
        result = chain.invoke({"topic": "AI agent frameworks", "depth": "comprehensive"})
        ```
    """
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_messages([
        ("system", """You are a research specialist AI agent. Your task is to:
1. Conduct thorough research on the given topic
2. Gather information from reliable sources
3. Organize findings in a structured format
4. Provide citations and references

Research depth: {depth}
"""),
        ("user", "Research the following topic: {topic}")
    ])


def create_analysis_prompt() -> Any:
    """
    Create a prompt template for analysis tasks.

    Returns:
        ChatPromptTemplate configured for analysis

    Example:
        ```python
        from utils.langchain_helpers import create_analysis_prompt, create_cortex_flow_llm

        llm = create_cortex_flow_llm()
        prompt = create_analysis_prompt()

        chain = prompt | llm
        result = chain.invoke({"data": "Research findings...", "focus": "trends"})
        ```
    """
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_messages([
        ("system", """You are an analytical AI agent. Your task is to:
1. Analyze the provided data or information
2. Identify key patterns, trends, and insights
3. Draw evidence-based conclusions
4. Present findings in a clear, structured format

Analysis focus: {focus}
"""),
        ("user", "Analyze the following data:\n\n{data}")
    ])


def create_writing_prompt() -> Any:
    """
    Create a prompt template for writing tasks.

    Returns:
        ChatPromptTemplate configured for writing

    Example:
        ```python
        from utils.langchain_helpers import create_writing_prompt, create_cortex_flow_llm

        llm = create_cortex_flow_llm()
        prompt = create_writing_prompt()

        chain = prompt | llm
        result = chain.invoke({
            "content": "Research findings...",
            "format": "blog post",
            "audience": "technical professionals"
        })
        ```
    """
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_messages([
        ("system", """You are a professional writer AI agent. Your task is to:
1. Transform information into well-written content
2. Adapt style and tone for the target audience
3. Ensure clarity, coherence, and engagement
4. Follow the specified format and structure

Target format: {format}
Target audience: {audience}
"""),
        ("user", "Write content based on:\n\n{content}")
    ])


def extract_token_usage(llm) -> Optional[Dict[str, int]]:
    """
    Extract token usage from last LLM completion.

    Args:
        llm: CortexFlowChatModel instance

    Returns:
        Dictionary with token usage statistics or None

    Example:
        ```python
        from utils.langchain_helpers import create_cortex_flow_llm, extract_token_usage

        llm = create_cortex_flow_llm()
        response = llm.invoke("What are AI agents?")

        usage = extract_token_usage(llm)
        print(f"Tokens used: {usage['total_tokens']}")
        ```
    """
    if hasattr(llm, 'get_last_usage'):
        return llm.get_last_usage()
    return None


def extract_execution_metadata(llm) -> Optional[Dict[str, Any]]:
    """
    Extract execution metadata from last LLM completion.

    Args:
        llm: CortexFlowChatModel instance

    Returns:
        Dictionary with execution metadata or None

    Example:
        ```python
        from utils.langchain_helpers import create_cortex_flow_llm, extract_execution_metadata

        llm = create_cortex_flow_llm()
        response = llm.invoke("Research AI trends")

        metadata = extract_execution_metadata(llm)
        print(f"Agents used: {metadata.get('agents_used')}")
        print(f"Execution time: {metadata.get('execution_time_seconds')}s")
        ```
    """
    if hasattr(llm, 'get_last_metadata'):
        return llm.get_last_metadata()
    return None


def format_conversation_history(messages: List[BaseMessage]) -> str:
    """
    Format conversation history for display.

    Args:
        messages: List of LangChain messages

    Returns:
        Formatted string representation

    Example:
        ```python
        from langchain_core.messages import HumanMessage, AIMessage
        from utils.langchain_helpers import format_conversation_history

        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi! How can I help?"),
            HumanMessage(content="What are AI agents?")
        ]

        print(format_conversation_history(messages))
        ```
    """
    formatted_lines = []

    for msg in messages:
        if isinstance(msg, SystemMessage):
            formatted_lines.append(f"[SYSTEM]: {msg.content}")
        elif isinstance(msg, HumanMessage):
            formatted_lines.append(f"[USER]: {msg.content}")
        elif isinstance(msg, AIMessage):
            formatted_lines.append(f"[ASSISTANT]: {msg.content}")
        else:
            formatted_lines.append(f"[{msg.__class__.__name__.upper()}]: {msg.content}")

    return "\n".join(formatted_lines)


def create_conversational_chain(
    llm = None,
    system_message: str = "You are a helpful AI assistant.",
    conversation_id: Optional[str] = None
):
    """
    Create a conversational chain with memory.

    Args:
        llm: Optional CortexFlowChatModel instance (created if not provided)
        system_message: System prompt for the conversation
        conversation_id: Optional conversation ID for context

    Returns:
        Configured conversational chain

    Example:
        ```python
        from utils.langchain_helpers import create_conversational_chain

        chain = create_conversational_chain(
            system_message="You are a research assistant",
            conversation_id="session_123"
        )

        # Use the chain
        response1 = chain.invoke({"input": "My name is Alice"})
        response2 = chain.invoke({"input": "What is my name?"})  # Remembers Alice
        ```
    """
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    # Create LLM if not provided
    if llm is None:
        llm = create_cortex_flow_llm(conversation_id=conversation_id)

    # Create prompt with message history placeholder
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("user", "{input}")
    ])

    # Create chain
    chain = prompt | llm

    return chain


def create_rag_chain(
    retriever: Any,
    llm = None,
    system_message: str = "Answer questions based on the provided context."
):
    """
    Create a RAG (Retrieval-Augmented Generation) chain.

    Args:
        retriever: Vector store retriever for document search
        llm: Optional CortexFlowChatModel instance
        system_message: System prompt for RAG

    Returns:
        Configured RAG chain

    Example:
        ```python
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        from utils.langchain_helpers import create_rag_chain

        # Create vector store
        documents = [...]  # Your documents
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(documents, embeddings)
        retriever = vectorstore.as_retriever()

        # Create RAG chain
        rag_chain = create_rag_chain(retriever)

        # Use the chain
        result = rag_chain.invoke({"question": "What are AI agents?"})
        ```
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough

    # Create LLM if not provided
    if llm is None:
        llm = create_cortex_flow_llm()

    # Create RAG prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", """Context information:
{context}

Question: {question}

Answer the question based on the context provided above.""")
    ])

    # Create RAG chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def create_streaming_handler():
    """
    Create a callback handler for streaming responses.

    Returns:
        StreamingStdOutCallbackHandler instance

    Example:
        ```python
        from utils.langchain_helpers import (
            create_cortex_flow_llm,
            create_streaming_handler
        )

        handler = create_streaming_handler()
        llm = create_cortex_flow_llm()

        # Stream response
        for chunk in llm.stream("Tell me about AI agents", callbacks=[handler]):
            pass  # Handler prints to stdout
        ```
    """
    from langchain_core.callbacks import StreamingStdOutCallbackHandler

    return StreamingStdOutCallbackHandler()


class CortexFlowUsageTracker:
    """
    Callback handler to track token usage across multiple LLM calls.

    Example:
        ```python
        from utils.langchain_helpers import (
            create_cortex_flow_llm,
            CortexFlowUsageTracker
        )

        tracker = CortexFlowUsageTracker()
        llm = create_cortex_flow_llm()

        # Make multiple calls
        llm.invoke("Question 1", callbacks=[tracker])
        llm.invoke("Question 2", callbacks=[tracker])

        # Get total usage
        print(f"Total tokens: {tracker.total_tokens}")
        print(f"Total cost estimate: ${tracker.estimate_cost():.4f}")
        ```
    """

    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0

    def on_llm_end(self, response, **kwargs):
        """Track token usage from LLM response."""
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('usage', {})

            if usage:
                self.total_prompt_tokens += usage.get('prompt_tokens', 0)
                self.total_completion_tokens += usage.get('completion_tokens', 0)
                self.total_tokens += usage.get('total_tokens', 0)
                self.call_count += 1

    def estimate_cost(
        self,
        prompt_cost_per_1k: float = 0.01,
        completion_cost_per_1k: float = 0.03
    ) -> float:
        """
        Estimate cost based on token usage.

        Args:
            prompt_cost_per_1k: Cost per 1K prompt tokens
            completion_cost_per_1k: Cost per 1K completion tokens

        Returns:
            Estimated cost in dollars
        """
        prompt_cost = (self.total_prompt_tokens / 1000) * prompt_cost_per_1k
        completion_cost = (self.total_completion_tokens / 1000) * completion_cost_per_1k
        return prompt_cost + completion_cost

    def reset(self):
        """Reset all counters."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0

    def __str__(self):
        return (
            f"CortexFlowUsageTracker("
            f"calls={self.call_count}, "
            f"total_tokens={self.total_tokens}, "
            f"prompt={self.total_prompt_tokens}, "
            f"completion={self.total_completion_tokens}"
            f")"
        )
