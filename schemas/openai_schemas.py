"""
OpenAI-Compatible API Schemas

Pydantic models for OpenAI Chat Completions API compatibility.
This allows Cortex Flow to be used as a drop-in replacement for OpenAI API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, Union
from datetime import datetime


# ========== Message Schemas ==========

class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    role: Literal["system", "user", "assistant", "function"] = Field(
        ...,
        description="The role of the message sender"
    )
    content: Optional[str] = Field(
        None,
        description="The content of the message"
    )
    name: Optional[str] = Field(
        None,
        description="The name of the author (for function messages)"
    )
    function_call: Optional[Dict[str, Any]] = Field(
        None,
        description="Function call information (deprecated, use tool_calls)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Tell me about AI agents"
            }
        }


class FunctionCall(BaseModel):
    """Function call information."""
    name: str
    arguments: str  # JSON string


class ToolCall(BaseModel):
    """Tool call information."""
    id: str
    type: Literal["function"] = "function"
    function: FunctionCall


# ========== Request Schemas ==========

class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""

    model: str = Field(
        default="cortex-flow",
        description="Model to use for completion"
    )
    messages: List[ChatMessage] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0-2)"
    )
    top_p: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    n: Optional[int] = Field(
        default=1,
        ge=1,
        description="Number of completions to generate"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response"
    )
    stop: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Stop sequences"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate"
    )
    presence_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty (-2 to 2)"
    )
    frequency_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty (-2 to 2)"
    )
    logit_bias: Optional[Dict[str, float]] = Field(
        default=None,
        description="Token bias adjustments"
    )
    user: Optional[str] = Field(
        default=None,
        description="Unique user identifier"
    )

    # Extensions for conversation management
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for maintaining context (maps to thread_id)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "cortex-flow",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Research AI agent trends"}
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            }
        }


# ========== Response Schemas ==========

class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(
        ...,
        description="Number of tokens in the prompt"
    )
    completion_tokens: int = Field(
        ...,
        description="Number of tokens in the completion"
    )
    total_tokens: int = Field(
        ...,
        description="Total number of tokens used"
    )


class ChatCompletionMessage(BaseModel):
    """Message in the completion response."""
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = Field(
        None,
        description="The content of the message"
    )
    function_call: Optional[FunctionCall] = None
    tool_calls: Optional[List[ToolCall]] = None


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""
    index: int = Field(
        ...,
        description="Index of this choice"
    )
    message: ChatCompletionMessage = Field(
        ...,
        description="The completion message"
    )
    finish_reason: Optional[Literal["stop", "length", "function_call", "content_filter", "null"]] = Field(
        None,
        description="Reason the completion finished"
    )
    logprobs: Optional[Dict[str, Any]] = None


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""
    id: str = Field(
        ...,
        description="Unique identifier for this completion"
    )
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(
        ...,
        description="Unix timestamp of when the completion was created"
    )
    model: str = Field(
        ...,
        description="Model used for completion"
    )
    choices: List[ChatCompletionChoice] = Field(
        ...,
        description="List of completion choices"
    )
    usage: Usage = Field(
        ...,
        description="Token usage information"
    )
    system_fingerprint: Optional[str] = None

    # Extensions
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for context tracking"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata (agents_used, execution_time, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-abc123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "cortex-flow",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "AI agents are autonomous systems..."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 150,
                    "total_tokens": 170
                }
            }
        }


# ========== Streaming Schemas ==========

class ChatCompletionChunkDelta(BaseModel):
    """Delta content in streaming response."""
    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionChunkChoice(BaseModel):
    """Choice in streaming chunk."""
    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[Literal["stop", "length", "function_call", "content_filter", "null"]] = None
    logprobs: Optional[Dict[str, Any]] = None


class ChatCompletionChunk(BaseModel):
    """Streaming chunk response."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
    system_fingerprint: Optional[str] = None


# ========== Model Info Schemas ==========

class ModelPermission(BaseModel):
    """Model permission information."""
    id: str
    object: Literal["model_permission"] = "model_permission"
    created: int
    allow_create_engine: bool = False
    allow_sampling: bool = True
    allow_logprobs: bool = False
    allow_search_indices: bool = False
    allow_view: bool = True
    allow_fine_tuning: bool = False
    organization: str = "*"
    group: Optional[str] = None
    is_blocking: bool = False


class ModelInfo(BaseModel):
    """Model information."""
    id: str = Field(
        ...,
        description="Model identifier"
    )
    object: Literal["model"] = "model"
    created: int = Field(
        ...,
        description="Unix timestamp of model creation"
    )
    owned_by: str = Field(
        default="cortex-flow",
        description="Organization owning the model"
    )
    permission: Optional[List[ModelPermission]] = None
    root: Optional[str] = None
    parent: Optional[str] = None


class ModelList(BaseModel):
    """List of available models."""
    object: Literal["list"] = "list"
    data: List[ModelInfo]


# ========== Error Schemas ==========

class OpenAIError(BaseModel):
    """OpenAI-compatible error response."""
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class OpenAIErrorResponse(BaseModel):
    """Error response wrapper."""
    error: OpenAIError
