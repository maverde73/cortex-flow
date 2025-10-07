"""
Example 3: Conversation Memory and Context Management

This example demonstrates:
- Using conversation_id for context persistence
- Building multi-turn conversations
- Creating conversational chains with memory
- Managing conversation history
"""

from langchain_core.messages import HumanMessage, SystemMessage
from utils.langchain_helpers import (
    create_cortex_flow_llm,
    create_conversational_chain,
    format_conversation_history
)


def example_simple_context():
    """Simple context management with conversation_id."""
    print("SIMPLE CONTEXT EXAMPLE")
    print("-" * 50)

    # Create LLM with conversation ID
    conversation_id = "demo_session_001"
    llm = create_cortex_flow_llm(conversation_id=conversation_id)

    print(f"Conversation ID: {conversation_id}")
    print()

    # Turn 1: Provide information
    print("Turn 1: Setting context...")
    response1 = llm.invoke("My favorite programming language is Python.")
    print(f"Assistant: {response1.content}")
    print()

    # Turn 2: Ask about it (should remember)
    print("Turn 2: Testing memory...")
    response2 = llm.invoke("What is my favorite programming language?")
    print(f"Assistant: {response2.content}")
    print()

    # Turn 3: Follow-up
    print("Turn 3: Follow-up question...")
    response3 = llm.invoke("Why is it popular?")
    print(f"Assistant: {response3.content}")
    print()


def example_multi_turn_conversation():
    """Multi-turn conversation with explicit message history."""
    print("MULTI-TURN CONVERSATION EXAMPLE")
    print("-" * 50)

    llm = create_cortex_flow_llm(conversation_id="demo_session_002")

    # Build conversation history
    messages = []

    # Turn 1
    messages.append(HumanMessage(content="I'm working on a project about AI agents."))
    response1 = llm.invoke(messages)
    messages.append(response1)
    print(f"Turn 1:")
    print(f"  User: I'm working on a project about AI agents.")
    print(f"  Assistant: {response1.content[:100]}...")
    print()

    # Turn 2
    messages.append(HumanMessage(content="What frameworks should I consider?"))
    response2 = llm.invoke(messages)
    messages.append(response2)
    print(f"Turn 2:")
    print(f"  User: What frameworks should I consider?")
    print(f"  Assistant: {response2.content[:100]}...")
    print()

    # Turn 3
    messages.append(HumanMessage(content="Tell me more about the first one you mentioned."))
    response3 = llm.invoke(messages)
    messages.append(response3)
    print(f"Turn 3:")
    print(f"  User: Tell me more about the first one you mentioned.")
    print(f"  Assistant: {response3.content[:100]}...")
    print()


def example_conversational_chain():
    """Using conversational chain helper."""
    print("CONVERSATIONAL CHAIN EXAMPLE")
    print("-" * 50)

    # Create conversational chain
    chain = create_conversational_chain(
        system_message="You are a helpful AI tutor teaching about multi-agent systems.",
        conversation_id="demo_session_003"
    )

    print("Starting tutoring session...")
    print()

    # Simulated conversation
    questions = [
        "What are multi-agent systems?",
        "Can you give me a simple example?",
        "How do they communicate with each other?",
        "What are the main challenges?"
    ]

    conversation_history = []

    for i, question in enumerate(questions, 1):
        print(f"Turn {i}:")
        print(f"  Student: {question}")

        # Invoke chain
        result = chain.invoke({
            "input": question,
            "history": conversation_history
        })

        # Update history
        conversation_history.append(HumanMessage(content=question))
        conversation_history.append(result)

        print(f"  Tutor: {result.content[:150]}...")
        print()


def example_session_management():
    """Managing multiple conversation sessions."""
    print("SESSION MANAGEMENT EXAMPLE")
    print("-" * 50)

    # Session 1: Technical discussion
    session1_id = "technical_session_001"
    llm_technical = create_cortex_flow_llm(conversation_id=session1_id)

    print(f"Session 1 ({session1_id}):")
    llm_technical.invoke("Let's discuss LangGraph architecture.")
    response = llm_technical.invoke("What are the key components?")
    print(f"  Response: {response.content[:100]}...")
    print()

    # Session 2: Business discussion (separate context)
    session2_id = "business_session_001"
    llm_business = create_cortex_flow_llm(conversation_id=session2_id)

    print(f"Session 2 ({session2_id}):")
    llm_business.invoke("Let's discuss the business value of AI agents.")
    response = llm_business.invoke("What are the key benefits?")
    print(f"  Response: {response.content[:100]}...")
    print()

    # Back to Session 1 - should remember LangGraph context
    print(f"Back to Session 1 ({session1_id}):")
    response = llm_technical.invoke("Can you remind me what we were discussing?")
    print(f"  Response: {response.content[:150]}...")
    print()


def example_chatbot_class():
    """Complete chatbot class implementation."""
    print("CHATBOT CLASS EXAMPLE")
    print("-" * 50)

    class CortexChatbot:
        """Simple chatbot with conversation management."""

        def __init__(self, system_message: str = "You are a helpful assistant."):
            self.conversation_id = None
            self.system_message = system_message
            self.messages = [SystemMessage(content=system_message)]
            self.llm = None

        def start_conversation(self, conversation_id: str = None):
            """Start a new conversation."""
            import uuid
            self.conversation_id = conversation_id or f"chat_{uuid.uuid4().hex[:8]}"
            self.llm = create_cortex_flow_llm(conversation_id=self.conversation_id)
            print(f"Started conversation: {self.conversation_id}")

        def send(self, user_message: str) -> str:
            """Send a message and get response."""
            if not self.llm:
                self.start_conversation()

            # Add user message
            self.messages.append(HumanMessage(content=user_message))

            # Get response
            response = self.llm.invoke(self.messages)

            # Add assistant response
            self.messages.append(response)

            return response.content

        def get_history(self) -> str:
            """Get formatted conversation history."""
            return format_conversation_history(self.messages)

    # Use the chatbot
    bot = CortexChatbot(system_message="You are a friendly AI assistant.")
    bot.start_conversation("chatbot_demo_001")
    print()

    # Have a conversation
    print("User: Hello! My name is Alice.")
    print(f"Bot: {bot.send('Hello! My name is Alice.')}")
    print()

    print("User: What's the weather like in AI land?")
    print(f"Bot: {bot.send('What\\'s the weather like in AI land?')[:100]}...")
    print()

    print("User: What was my name again?")
    print(f"Bot: {bot.send('What was my name again?')}")
    print()


def main():
    print("=" * 70)
    print("EXAMPLE 3: CONVERSATION MEMORY")
    print("=" * 70)
    print()

    example_simple_context()
    example_multi_turn_conversation()
    example_conversational_chain()
    example_session_management()
    example_chatbot_class()

    print("=" * 70)
    print("EXAMPLE 3 COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
