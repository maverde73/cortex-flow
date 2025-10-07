"""
OpenAI Adapter

Utilities for converting between OpenAI API format and internal LangChain format.
Handles message conversion, thread management, and response formatting.
"""

import time
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    FunctionMessage
)

from schemas.openai_schemas import (
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionMessage,
    Usage
)

logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """Adapter for OpenAI API compatibility."""

    @staticmethod
    def openai_messages_to_langchain(messages: List[ChatMessage]) -> List:
        """
        Convert OpenAI message format to LangChain message format.

        Args:
            messages: List of OpenAI ChatMessage objects

        Returns:
            List of LangChain message objects
        """
        langchain_messages = []

        for msg in messages:
            role = msg.role
            content = msg.content or ""

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            elif role == "function":
                # Function messages (legacy)
                langchain_messages.append(FunctionMessage(
                    content=content,
                    name=msg.name or "unknown_function"
                ))
            else:
                logger.warning(f"Unknown message role: {role}, treating as user message")
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    @staticmethod
    def langchain_messages_to_openai(messages: List) -> List[ChatMessage]:
        """
        Convert LangChain message format to OpenAI message format.

        Args:
            messages: List of LangChain message objects

        Returns:
            List of OpenAI ChatMessage objects
        """
        openai_messages = []

        for msg in messages:
            msg_type = type(msg).__name__

            if msg_type == "SystemMessage":
                openai_messages.append(ChatMessage(
                    role="system",
                    content=msg.content
                ))
            elif msg_type == "HumanMessage":
                openai_messages.append(ChatMessage(
                    role="user",
                    content=msg.content
                ))
            elif msg_type == "AIMessage":
                openai_messages.append(ChatMessage(
                    role="assistant",
                    content=msg.content
                ))
            elif msg_type == "FunctionMessage":
                openai_messages.append(ChatMessage(
                    role="function",
                    content=msg.content,
                    name=getattr(msg, "name", None)
                ))
            else:
                logger.warning(f"Unknown LangChain message type: {msg_type}")
                openai_messages.append(ChatMessage(
                    role="assistant",
                    content=str(msg.content)
                ))

        return openai_messages

    @staticmethod
    def generate_conversation_id(request: ChatCompletionRequest) -> str:
        """
        Generate or extract conversation ID for thread management.

        Args:
            request: OpenAI chat completion request

        Returns:
            Conversation ID (thread_id)
        """
        if request.conversation_id:
            return request.conversation_id

        # Generate new conversation ID based on user or random UUID
        if request.user:
            return f"conv_{request.user}_{int(time.time())}"

        return f"conv_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def create_completion_response(
        request: ChatCompletionRequest,
        result_content: str,
        conversation_id: str,
        usage_data: Optional[Usage] = None,
        metadata: Optional[Dict[str, Any]] = None,
        finish_reason: str = "stop"
    ) -> ChatCompletionResponse:
        """
        Create OpenAI-compatible chat completion response.

        Args:
            request: Original request
            result_content: The completion text
            conversation_id: Conversation/thread ID
            usage_data: Token usage information
            metadata: Additional metadata
            finish_reason: Reason the completion finished

        Returns:
            ChatCompletionResponse object
        """
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:16]}"
        created_ts = int(time.time())

        # Default usage if not provided
        if usage_data is None:
            usage_data = Usage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0
            )

        choice = ChatCompletionChoice(
            index=0,
            message=ChatCompletionMessage(
                role="assistant",
                content=result_content
            ),
            finish_reason=finish_reason
        )

        return ChatCompletionResponse(
            id=completion_id,
            object="chat.completion",
            created=created_ts,
            model=request.model,
            choices=[choice],
            usage=usage_data,
            conversation_id=conversation_id,
            metadata=metadata or {}
        )

    @staticmethod
    def extract_system_and_user_messages(
        messages: List[ChatMessage]
    ) -> Tuple[Optional[str], str]:
        """
        Extract system prompt and last user message from conversation.

        Args:
            messages: List of chat messages

        Returns:
            Tuple of (system_prompt, user_message)
        """
        system_prompt = None
        user_message = ""

        # Extract system message (usually first)
        system_messages = [msg for msg in messages if msg.role == "system"]
        if system_messages:
            system_prompt = system_messages[0].content

        # Get last user message (most recent request)
        user_messages = [msg for msg in messages if msg.role == "user"]
        if user_messages:
            user_message = user_messages[-1].content or ""

        # If no user message, use last message content
        if not user_message and messages:
            user_message = messages[-1].content or ""

        return system_prompt, user_message

    @staticmethod
    def build_context_from_history(messages: List[ChatMessage]) -> str:
        """
        Build context string from message history for agents.

        Args:
            messages: List of chat messages

        Returns:
            Context string
        """
        context_parts = []

        for i, msg in enumerate(messages[:-1]):  # Exclude last message (current request)
            role = msg.role.upper()
            content = msg.content or ""

            if content:
                context_parts.append(f"[{role}]: {content}")

        if context_parts:
            return "\n\n".join(context_parts)

        return ""

    @staticmethod
    def merge_metadata(
        supervisor_metadata: Dict[str, Any],
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Merge metadata from supervisor with additional info.

        Args:
            supervisor_metadata: Metadata from supervisor agent
            execution_time: Total execution time in seconds

        Returns:
            Merged metadata dict
        """
        merged = {
            "execution_time_seconds": round(execution_time, 2),
            **(supervisor_metadata or {})
        }

        # Extract useful info
        if "agents_used" in supervisor_metadata:
            merged["agents_used"] = supervisor_metadata["agents_used"]

        if "iteration_count" in supervisor_metadata:
            merged["iterations"] = supervisor_metadata["iteration_count"]

        return merged

    @staticmethod
    def validate_model_name(model: str, available_models: List[str]) -> bool:
        """
        Validate model name against available models.

        Args:
            model: Requested model name
            available_models: List of available model names

        Returns:
            True if model is available
        """
        return model in available_models

    @staticmethod
    def get_available_models() -> List[str]:
        """
        Get list of available model names.

        Returns:
            List of model identifiers
        """
        return [
            "cortex-flow",
            "cortex-flow-supervisor",
            "cortex-flow-researcher",
            "cortex-flow-analyst",
            "cortex-flow-writer"
        ]
