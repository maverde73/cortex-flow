"""
Token Counter

Utilities for counting tokens in messages and responses.
Uses tiktoken for OpenAI-compatible token counting.
Supports both OpenAI ChatMessage format and LangChain BaseMessage format.
"""

import logging
from typing import List, Optional, Union
from schemas.openai_schemas import ChatMessage, Usage

# LangChain imports for message trimming support
try:
    from langchain_core.messages import BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseMessage = None

logger = logging.getLogger(__name__)

# Try to import tiktoken (optional dependency)
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning(
        "tiktoken not installed - token counting will use approximations. "
        "Install with: pip install tiktoken"
    )


class TokenCounter:
    """Token counting utilities."""

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize token counter.

        Args:
            model: Model name for tokenization (gpt-4, gpt-3.5-turbo, etc.)
        """
        self.model = model
        self.encoding = None

        if TIKTOKEN_AVAILABLE:
            try:
                # Try to get encoding for model
                self.encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
                logger.warning(f"No encoding found for model {model}, using cl100k_base")
                self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_message_tokens(self, messages: List[ChatMessage]) -> int:
        """
        Count tokens in a list of messages.

        Args:
            messages: List of chat messages

        Returns:
            Number of tokens
        """
        if not TIKTOKEN_AVAILABLE or self.encoding is None:
            return self._approximate_message_tokens(messages)

        # Token counting based on OpenAI's documentation
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

        num_tokens = 0

        # Every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 3
        tokens_per_name = 1

        for message in messages:
            num_tokens += tokens_per_message

            # Count role
            if message.role:
                num_tokens += len(self.encoding.encode(message.role))

            # Count content
            if message.content:
                num_tokens += len(self.encoding.encode(message.content))

            # Count name if present
            if message.name:
                num_tokens += tokens_per_name
                num_tokens += len(self.encoding.encode(message.name))

        # Every reply is primed with <|start|>assistant<|message|>
        num_tokens += 3

        return num_tokens

    def count_string_tokens(self, text: str) -> int:
        """
        Count tokens in a string.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if not TIKTOKEN_AVAILABLE or self.encoding is None:
            return self._approximate_string_tokens(text)

        return len(self.encoding.encode(text))

    def count_langchain_message_tokens(self, messages: List) -> int:
        """
        Count tokens in LangChain BaseMessage list.

        Compatible with langchain_core.messages.trim_messages().

        Args:
            messages: List of LangChain BaseMessage objects

        Returns:
            Number of tokens
        """
        if not messages:
            return 0

        if not LANGCHAIN_AVAILABLE:
            # Fallback: approximate based on content length
            return self._approximate_langchain_tokens(messages)

        num_tokens = 0
        tokens_per_message = 3  # Message overhead

        for msg in messages:
            num_tokens += tokens_per_message

            # Count role/type
            msg_type = msg.type if hasattr(msg, 'type') else 'unknown'
            num_tokens += len(self.encoding.encode(msg_type)) if self.encoding else len(msg_type) // 4

            # Count content
            content = msg.content if hasattr(msg, 'content') else str(msg)
            if content:
                if self.encoding:
                    num_tokens += len(self.encoding.encode(content))
                else:
                    num_tokens += len(content) // 4

        # Reply priming
        num_tokens += 3

        return num_tokens

    def _approximate_langchain_tokens(self, messages: List) -> int:
        """
        Approximate token count for LangChain messages.

        Args:
            messages: List of LangChain BaseMessage objects

        Returns:
            Approximate token count
        """
        total_chars = 0

        for msg in messages:
            # Type/role
            if hasattr(msg, 'type'):
                total_chars += len(msg.type)

            # Content
            if hasattr(msg, 'content'):
                total_chars += len(msg.content)

            # Overhead
            total_chars += 10

        return total_chars // 4

    def create_usage(
        self,
        prompt_messages: List[ChatMessage],
        completion_text: str
    ) -> Usage:
        """
        Create Usage object with token counts.

        Args:
            prompt_messages: Input messages
            completion_text: Generated completion text

        Returns:
            Usage object with token counts
        """
        prompt_tokens = self.count_message_tokens(prompt_messages)
        completion_tokens = self.count_string_tokens(completion_text)
        total_tokens = prompt_tokens + completion_tokens

        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )

    @staticmethod
    def _approximate_message_tokens(messages: List[ChatMessage]) -> int:
        """
        Approximate token count when tiktoken is not available.

        Uses rough heuristic: 1 token ≈ 4 characters for English text.

        Args:
            messages: List of chat messages

        Returns:
            Approximate number of tokens
        """
        total_chars = 0

        for message in messages:
            # Count role (usually 4-10 chars)
            if message.role:
                total_chars += len(message.role)

            # Count content
            if message.content:
                total_chars += len(message.content)

            # Count name
            if message.name:
                total_chars += len(message.name)

            # Add overhead for message structure
            total_chars += 10

        # Rough approximation: 4 characters ≈ 1 token
        return total_chars // 4

    @staticmethod
    def _approximate_string_tokens(text: str) -> int:
        """
        Approximate token count for a string.

        Args:
            text: Text to count

        Returns:
            Approximate number of tokens
        """
        # Rough approximation: 4 characters ≈ 1 token
        return len(text) // 4


# Global token counter instance
_default_counter: Optional[TokenCounter] = None


def get_token_counter(model: str = "gpt-4") -> TokenCounter:
    """
    Get or create default token counter.

    Args:
        model: Model name

    Returns:
        TokenCounter instance
    """
    global _default_counter

    if _default_counter is None or _default_counter.model != model:
        _default_counter = TokenCounter(model=model)

    return _default_counter


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Quick helper to count tokens in text.

    Args:
        text: Text to count tokens for
        model: Model name for tokenization

    Returns:
        Number of tokens
    """
    counter = get_token_counter(model)
    return counter.count_string_tokens(text)


def count_message_tokens(messages: List[ChatMessage], model: str = "gpt-4") -> int:
    """
    Quick helper to count tokens in messages.

    Args:
        messages: List of chat messages
        model: Model name for tokenization

    Returns:
        Number of tokens
    """
    counter = get_token_counter(model)
    return counter.count_message_tokens(messages)
