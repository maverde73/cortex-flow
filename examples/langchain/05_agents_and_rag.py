"""
Example 5: Agents and RAG (Retrieval-Augmented Generation)

This example demonstrates:
- Using CortexFlowChatModel in LangChain agents
- RAG pipelines with vector stores
- Tool-using agents
- Combining Cortex Flow with LangChain ecosystem
"""

import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from utils.langchain_helpers import (
    create_cortex_flow_llm,
    create_rag_chain
)


def example_simple_rag_pattern():
    """Simple RAG pattern without vector store."""
    print("SIMPLE RAG PATTERN EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Mock document context
    context = """
    LangChain is a framework for developing applications powered by language models.
    It provides abstractions for chains, agents, memory, and retrieval.

    LangGraph extends LangChain with stateful, multi-actor applications using graphs.
    It enables building complex agent workflows with state management.

    LangSmith is a platform for debugging, testing, and monitoring LLM applications.
    It provides tracing and evaluation capabilities.
    """

    # Create RAG prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer questions based on the provided context."),
        ("user", """Context:
{context}

Question: {question}

Answer:""")
    ])

    # Create RAG chain
    rag_chain = (
        {
            "context": lambda x: context,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # Ask questions
    questions = [
        "What is LangChain?",
        "How does LangGraph extend LangChain?",
        "What is LangSmith used for?"
    ]

    for question in questions:
        print(f"Q: {question}")
        answer = rag_chain.invoke(question)
        print(f"A: {answer[:150]}...")
        print()


def example_document_qa():
    """Document Q&A with in-memory documents."""
    print("DOCUMENT Q&A EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Mock documents (in real scenario, these would be from a vector store)
    documents = {
        "ai_agents": """
        AI agents are autonomous systems that can perceive their environment,
        make decisions, and take actions to achieve specific goals.
        They use language models for reasoning and planning.
        """,
        "multi_agent": """
        Multi-agent systems consist of multiple AI agents that collaborate
        to solve complex problems. Each agent can have specialized capabilities
        and they communicate to coordinate their actions.
        """,
        "cortex_flow": """
        Cortex Flow is a multi-agent AI system that uses specialized agents
        for research, analysis, and writing tasks. It provides an OpenAI-compatible
        API and integrates with LangChain.
        """
    }

    def retrieve_docs(query: str) -> str:
        """Simple keyword-based retrieval."""
        query_lower = query.lower()
        relevant_docs = []

        for key, doc in documents.items():
            if any(word in doc.lower() for word in query_lower.split()):
                relevant_docs.append(doc)

        return "\n\n".join(relevant_docs) if relevant_docs else "No relevant documents found."

    # Create Q&A chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question using the provided documents."),
        ("user", """Documents:
{documents}

Question: {question}

Provide a concise answer:""")
    ])

    qa_chain = (
        {
            "documents": lambda x: retrieve_docs(x["question"]),
            "question": lambda x: x["question"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # Test questions
    questions = [
        "What are AI agents?",
        "Tell me about Cortex Flow",
        "How do multi-agent systems work?"
    ]

    for question in questions:
        print(f"Q: {question}")
        answer = qa_chain.invoke({"question": question})
        print(f"A: {answer[:150]}...")
        print()


def example_conversational_rag():
    """RAG with conversation history."""
    print("CONVERSATIONAL RAG EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm(conversation_id="rag_conv_001")

    # Knowledge base
    knowledge = """
    LangChain Agents:
    - Can use tools to interact with external systems
    - Make decisions about which tools to use
    - Follow the ReAct pattern (Reasoning + Acting)

    Tool Examples:
    - Web search for current information
    - Calculator for mathematical operations
    - Database queries for structured data
    - API calls for external services
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant with access to the following knowledge:

{knowledge}

Answer questions based on this knowledge and maintain conversation context."""),
        ("user", "{question}")
    ])

    chain = (
        {
            "knowledge": lambda x: knowledge,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # Conversation
    print("Starting conversational RAG session...")
    print()

    conversation = [
        "What patterns do LangChain agents follow?",
        "Can you explain what that means?",
        "What are some example tools they can use?"
    ]

    for i, question in enumerate(conversation, 1):
        print(f"Turn {i}: {question}")
        answer = chain.invoke(question)
        print(f"Answer: {answer[:150]}...")
        print()


def example_tool_using_pattern():
    """Pattern for tool-using agents."""
    print("TOOL-USING PATTERN EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Mock tools (in real scenario, these would be actual LangChain tools)
    def search_tool(query: str) -> str:
        """Mock search tool."""
        return f"Search results for '{query}': [AI agents are autonomous systems...]"

    def calculator_tool(expression: str) -> str:
        """Mock calculator tool."""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except:
            return "Invalid expression"

    # Tool descriptions for the LLM
    tool_descriptions = """
Available Tools:
1. search(query) - Search for information
2. calculator(expression) - Calculate mathematical expressions

To use a tool, respond with:
TOOL: tool_name(arguments)
"""

    # Agent prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an AI agent that can use tools.

{tool_descriptions}

Think step by step and use tools when needed."""),
        ("user", "{task}")
    ])

    chain = prompt | llm | StrOutputParser()

    # Example tasks
    tasks = [
        "Search for information about ReAct agents",
        "Calculate 123 * 456"
    ]

    for task in tasks:
        print(f"Task: {task}")
        response = chain.invoke({"task": task})
        print(f"Agent Response: {response[:200]}...")
        print()


def example_retrieval_qa_chain():
    """Complete retrieval QA chain pattern."""
    print("RETRIEVAL QA CHAIN EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Document store (mock)
    class SimpleDocStore:
        """Simple in-memory document store."""

        def __init__(self):
            self.docs = {
                "doc1": "Cortex Flow uses a supervisor agent to orchestrate specialized agents.",
                "doc2": "The system supports OpenAI-compatible API for easy integration.",
                "doc3": "LangChain integration enables use in chains, agents, and RAG pipelines.",
                "doc4": "Streaming responses are supported via Server-Sent Events.",
                "doc5": "Conversation context is maintained using thread-based memory."
            }

        def search(self, query: str, top_k: int = 2):
            """Simple relevance search."""
            # In real scenario, this would use embeddings and vector similarity
            query_words = set(query.lower().split())
            scores = []

            for doc_id, content in self.docs.items():
                content_words = set(content.lower().split())
                overlap = len(query_words & content_words)
                scores.append((doc_id, content, overlap))

            # Sort by score and return top_k
            scores.sort(key=lambda x: x[2], reverse=True)
            return [(doc_id, content) for doc_id, content, _ in scores[:top_k]]

    doc_store = SimpleDocStore()

    # Create retrieval QA chain
    def format_docs(docs):
        return "\n\n".join(f"[{doc_id}] {content}" for doc_id, content in docs)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question using only the provided documents. Cite document IDs."),
        ("user", """Retrieved Documents:
{context}

Question: {question}

Answer:""")
    ])

    qa_chain = (
        {
            "context": lambda x: format_docs(doc_store.search(x["question"])),
            "question": lambda x: x["question"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # Ask questions
    questions = [
        "How does Cortex Flow work?",
        "What API does it support?",
        "Can it maintain conversation context?"
    ]

    for question in questions:
        print(f"Q: {question}")

        # Show retrieved docs
        retrieved = doc_store.search(question)
        print(f"Retrieved: {[doc_id for doc_id, _ in retrieved]}")

        # Get answer
        answer = qa_chain.invoke({"question": question})
        print(f"A: {answer[:150]}...")
        print()


def main():
    print("=" * 70)
    print("EXAMPLE 5: AGENTS AND RAG")
    print("=" * 70)
    print()

    example_simple_rag_pattern()
    example_document_qa()
    example_conversational_rag()
    example_tool_using_pattern()
    example_retrieval_qa_chain()

    print("=" * 70)
    print("EXAMPLE 5 COMPLETED!")
    print("=" * 70)
    print()
    print("Note: These examples use mock implementations for simplicity.")
    print("In production, you would use:")
    print("  - Real vector stores (FAISS, Pinecone, Weaviate)")
    print("  - Actual embeddings (OpenAI, HuggingFace)")
    print("  - LangChain tools and agents framework")
    print("  - Persistent storage for documents")


if __name__ == "__main__":
    main()
