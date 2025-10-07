"""
LangChain ChatModel wrapper for Cortex Flow.

This module provides a LangChain-compatible ChatModel that uses the Cortex Flow
OpenAI-compatible API, enabling integration with LangChain chains, agents, and RAG pipelines.
"""

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional
import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from pydantic import Field


class CortexFlowChatModel(BaseChatModel):
    """
    LangChain ChatModel for Cortex Flow multi-agent system.

    This model wraps the Cortex Flow OpenAI-compatible API, providing:
    - Full LangChain compatibility (chains, agents, RAG)
    - LCEL (LangChain Expression Language) support
    - Conversation context management via conversation_id
    - Streaming and non-streaming modes
    - Token usage tracking
    - Multi-agent orchestration transparency

    Example:
        ```python
        from utils.langchain_chat_model import CortexFlowChatModel

        # Basic usage
        llm = CortexFlowChatModel(base_url="http://localhost:8001/v1")
        response = llm.invoke("Research AI agent frameworks")

        # With conversation context
        llm = CortexFlowChatModel(conversation_id="session_123")
        response1 = llm.invoke("My name is Alice")
        response2 = llm.invoke("What is my name?")  # Remembers "Alice"

        # In a chain (LCEL)
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful research assistant"),
            ("user", "{query}")
        ])
        chain = prompt | llm
        result = chain.invoke({"query": "Latest AI trends"})
        ```
    """

    base_url: str = Field(
        default="http://localhost:8001/v1",
        description="Base URL for Cortex Flow OpenAI-compatible API"
    )

    model_name: str = Field(
        default="cortex-flow",
        description="Model identifier to use"
    )

    temperature: float = Field(
        default=0.7,
        description="Sampling temperature (0-2)"
    )

    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate"
    )

    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for context management"
    )

    timeout: float = Field(
        default=120.0,
        description="Request timeout in seconds"
    )

    # LangChain metadata
    _last_usage: Optional[Dict[str, int]] = None
    _last_metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        """Return identifier of LLM type."""
        return "cortex-flow"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _convert_messages_to_openai_format(
        self,
        messages: List[BaseMessage]
    ) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenAI format."""
        openai_messages = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({
                    "role": "system",
                    "content": msg.content
                })
            elif isinstance(msg, HumanMessage):
                openai_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, AIMessage):
                openai_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
            else:
                # Generic message - treat as user
                openai_messages.append({
                    "role": "user",
                    "content": msg.content
                })

        return openai_messages

    def _create_request_payload(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Create request payload for OpenAI API."""
        payload = {
            "model": self.model_name,
            "messages": self._convert_messages_to_openai_format(messages),
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": False,
        }

        # Add optional parameters
        if self.max_tokens or kwargs.get("max_tokens"):
            payload["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        if stop:
            payload["stop"] = stop

        if self.conversation_id or kwargs.get("conversation_id"):
            payload["conversation_id"] = kwargs.get("conversation_id", self.conversation_id)

        return payload

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Synchronous chat completion.

        Args:
            messages: List of messages in the conversation
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Returns:
            ChatResult with generations and metadata
        """
        payload = self._create_request_payload(messages, stop, **kwargs)

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        # Extract response
        choice = data["choices"][0]
        message = choice["message"]
        content = message["content"]

        # Store usage and metadata
        self._last_usage = data.get("usage")
        self._last_metadata = data.get("metadata")

        # Create ChatResult
        ai_message = AIMessage(content=content)
        generation = ChatGeneration(message=ai_message)

        # Add token usage to metadata
        llm_output = {
            "model_name": data.get("model", self.model_name),
            "usage": self._last_usage,
            "metadata": self._last_metadata,
        }

        return ChatResult(generations=[generation], llm_output=llm_output)

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Asynchronous chat completion.

        Args:
            messages: List of messages in the conversation
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Returns:
            ChatResult with generations and metadata
        """
        payload = self._create_request_payload(messages, stop, **kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        # Extract response
        choice = data["choices"][0]
        message = choice["message"]
        content = message["content"]

        # Store usage and metadata
        self._last_usage = data.get("usage")
        self._last_metadata = data.get("metadata")

        # Create ChatResult
        ai_message = AIMessage(content=content)
        generation = ChatGeneration(message=ai_message)

        # Add token usage to metadata
        llm_output = {
            "model_name": data.get("model", self.model_name),
            "usage": self._last_usage,
            "metadata": self._last_metadata,
        }

        return ChatResult(generations=[generation], llm_output=llm_output)

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """
        Synchronous streaming chat completion.

        Args:
            messages: List of messages in the conversation
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Yields:
            ChatGenerationChunk for each token
        """
        payload = self._create_request_payload(messages, stop, **kwargs)
        payload["stream"] = True

        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            import json
                            chunk_data = json.loads(data_str)

                            # Extract content from chunk
                            if chunk_data.get("choices"):
                                delta = chunk_data["choices"][0].get("delta", {})
                                content = delta.get("content", "")

                                if content:
                                    chunk = ChatGenerationChunk(
                                        message=AIMessage(content=content)
                                    )

                                    if run_manager:
                                        run_manager.on_llm_new_token(content, chunk=chunk)

                                    yield chunk

                        except Exception:
                            # Skip malformed chunks
                            continue

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """
        Asynchronous streaming chat completion.

        Args:
            messages: List of messages in the conversation
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Yields:
            ChatGenerationChunk for each token
        """
        payload = self._create_request_payload(messages, stop, **kwargs)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or line.startswith(":"):
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            import json
                            chunk_data = json.loads(data_str)

                            # Extract content from chunk
                            if chunk_data.get("choices"):
                                delta = chunk_data["choices"][0].get("delta", {})
                                content = delta.get("content", "")

                                if content:
                                    chunk = ChatGenerationChunk(
                                        message=AIMessage(content=content)
                                    )

                                    if run_manager:
                                        await run_manager.on_llm_new_token(content, chunk=chunk)

                                    yield chunk

                        except Exception:
                            # Skip malformed chunks
                            continue

    def get_last_usage(self) -> Optional[Dict[str, int]]:
        """
        Get token usage from last completion.

        Returns:
            Dictionary with prompt_tokens, completion_tokens, total_tokens
        """
        return self._last_usage

    def get_last_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get execution metadata from last completion.

        Returns:
            Dictionary with agents_used, execution_time, iterations, etc.
        """
        return self._last_metadata
