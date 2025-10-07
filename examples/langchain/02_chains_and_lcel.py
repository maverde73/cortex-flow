"""
Example 2: Chains and LCEL (LangChain Expression Language)

This example demonstrates:
- Creating chains using LCEL (| operator)
- Using prompt templates
- Chaining multiple operations
- Using helper functions for common patterns
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.langchain_helpers import (
    create_cortex_flow_llm,
    create_research_prompt,
    create_analysis_prompt
)


def example_basic_chain():
    """Basic chain with prompt template."""
    print("BASIC CHAIN EXAMPLE")
    print("-" * 50)

    # Create LLM
    llm = create_cortex_flow_llm()

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("user", "{query}")
    ])

    # Create chain using LCEL (pipe operator)
    chain = prompt | llm | StrOutputParser()

    # Invoke chain
    result = chain.invoke({"query": "What are the benefits of AI agents?"})
    print(f"Result: {result[:200]}...")
    print()


def example_research_chain():
    """Research chain using helper function."""
    print("RESEARCH CHAIN EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()
    prompt = create_research_prompt()

    # Create research chain
    research_chain = prompt | llm | StrOutputParser()

    # Invoke with research parameters
    result = research_chain.invoke({
        "topic": "LangChain multi-agent systems",
        "depth": "comprehensive"
    })

    print(f"Research Result (first 300 chars):")
    print(f"{result[:300]}...")
    print()


def example_multi_step_chain():
    """Multi-step chain with sequential processing."""
    print("MULTI-STEP CHAIN EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Step 1: Research
    research_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a research specialist. Provide key facts only."),
        ("user", "Research: {topic}")
    ])

    # Step 2: Summarize
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a summarization expert. Create a concise summary."),
        ("user", "Summarize this research:\n\n{research}")
    ])

    # Create research chain
    research_chain = research_prompt | llm | StrOutputParser()

    # Get research results
    print("Step 1: Researching...")
    research_result = research_chain.invoke({"topic": "AI agent frameworks"})
    print(f"✅ Research completed ({len(research_result)} chars)")

    # Create summary chain
    summary_chain = summary_prompt | llm | StrOutputParser()

    # Get summary
    print("Step 2: Summarizing...")
    summary = summary_chain.invoke({"research": research_result})
    print(f"✅ Summary completed")
    print()
    print(f"Final Summary:")
    print(summary)
    print()


def example_parallel_chains():
    """Parallel chains with different prompts."""
    print("PARALLEL CHAINS EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Create multiple chains for different aspects
    technical_chain = (
        ChatPromptTemplate.from_messages([
            ("system", "Focus on technical details only."),
            ("user", "{topic}")
        ])
        | llm
        | StrOutputParser()
    )

    business_chain = (
        ChatPromptTemplate.from_messages([
            ("system", "Focus on business value only."),
            ("user", "{topic}")
        ])
        | llm
        | StrOutputParser()
    )

    topic = "AI agents in enterprise applications"

    print(f"Topic: {topic}")
    print()

    # Run chains (could be parallelized with async)
    technical_view = technical_chain.invoke({"topic": topic})
    print(f"Technical View: {technical_view[:150]}...")
    print()

    business_view = business_chain.invoke({"topic": topic})
    print(f"Business View: {business_view[:150]}...")
    print()


def example_conditional_chain():
    """Chain with conditional routing."""
    print("CONDITIONAL CHAIN EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm()

    # Classifier chain
    classifier_prompt = ChatPromptTemplate.from_messages([
        ("system", "Classify the query type. Reply with ONLY one word: RESEARCH, ANALYSIS, or WRITING."),
        ("user", "{query}")
    ])

    classifier_chain = classifier_prompt | llm | StrOutputParser()

    # Create specialized chains
    research_chain = create_research_prompt() | llm | StrOutputParser()
    analysis_chain = create_analysis_prompt() | llm | StrOutputParser()

    # Example queries
    queries = [
        "Find information about LangChain agents",
        "Analyze the trends in AI adoption"
    ]

    for query in queries:
        print(f"Query: {query}")

        # Classify
        classification = classifier_chain.invoke({"query": query}).strip().upper()
        print(f"Classification: {classification}")

        # Route to appropriate chain
        if "RESEARCH" in classification:
            result = research_chain.invoke({"topic": query, "depth": "quick"})
        elif "ANALYSIS" in classification:
            result = analysis_chain.invoke({"data": query, "focus": "trends"})
        else:
            result = "Unsupported query type"

        print(f"Result: {result[:150]}...")
        print()


def main():
    print("=" * 70)
    print("EXAMPLE 2: CHAINS AND LCEL")
    print("=" * 70)
    print()

    example_basic_chain()
    example_research_chain()
    example_multi_step_chain()
    example_parallel_chains()
    example_conditional_chain()

    print("=" * 70)
    print("EXAMPLE 2 COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
