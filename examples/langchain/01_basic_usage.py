"""
Example 1: Basic Usage of CortexFlowChatModel

This example demonstrates:
- Creating a CortexFlowChatModel instance
- Making simple chat completions
- Accessing token usage and metadata
"""

from utils.langchain_chat_model import CortexFlowChatModel
from utils.langchain_helpers import extract_token_usage, extract_execution_metadata


def main():
    print("=" * 70)
    print("EXAMPLE 1: BASIC USAGE")
    print("=" * 70)
    print()

    # Create Cortex Flow LLM
    print("Creating CortexFlowChatModel...")
    llm = CortexFlowChatModel(
        base_url="http://localhost:8001/v1",
        model_name="cortex-flow",
        temperature=0.7
    )
    print(f"✅ LLM created: {llm._llm_type}")
    print()

    # Simple invocation
    print("Invoking LLM with simple question...")
    response = llm.invoke("What are AI agents? Answer in 2 sentences.")
    print(f"✅ Response received:")
    print(f"{response.content}")
    print()

    # Extract token usage
    usage = extract_token_usage(llm)
    if usage:
        print(f"Token Usage:")
        print(f"  - Prompt tokens: {usage.get('prompt_tokens')}")
        print(f"  - Completion tokens: {usage.get('completion_tokens')}")
        print(f"  - Total tokens: {usage.get('total_tokens')}")
        print()

    # Extract execution metadata
    metadata = extract_execution_metadata(llm)
    if metadata:
        print(f"Execution Metadata:")
        print(f"  - Agents used: {metadata.get('agents_used')}")
        print(f"  - Execution time: {metadata.get('execution_time_seconds')}s")
        print(f"  - Iterations: {metadata.get('iterations')}")
        print()

    # Multiple invocations
    print("Making multiple invocations...")
    questions = [
        "What is LangChain?",
        "What is LangGraph?",
        "How do they work together?"
    ]

    for i, question in enumerate(questions, 1):
        response = llm.invoke(question + " (One sentence only)")
        print(f"{i}. Q: {question}")
        print(f"   A: {response.content[:100]}...")
        print()

    print("=" * 70)
    print("EXAMPLE 1 COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
