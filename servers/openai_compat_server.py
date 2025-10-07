"""
OpenAI-Compatible API Server

FastAPI server providing OpenAI Chat Completions API compatibility.
Allows Cortex Flow to be used as a drop-in replacement for OpenAI API in chatbot applications.
"""

import time
import logging
import json
from typing import Optional, AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_core.messages import HumanMessage, trim_messages

from schemas.openai_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ModelInfo,
    ModelList,
    OpenAIErrorResponse,
    OpenAIError
)
from utils.openai_adapter import OpenAIAdapter
from utils.token_counter import TokenCounter
from agents.supervisor import get_supervisor_agent
from config_legacy import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="Cortex Flow - OpenAI Compatible API",
    description="OpenAI Chat Completions API compatible interface for Cortex Flow multi-agent system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize adapter and token counter
adapter = OpenAIAdapter()
token_counter = TokenCounter(model="gpt-4")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Cortex Flow - OpenAI Compatible API",
        "version": "1.0.0",
        "status": "operational",
        "description": "OpenAI Chat Completions API compatible interface",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health"
        },
        "documentation": "/docs"
    }


@app.get("/health", tags=["monitoring"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "openai-compat-server",
        "version": "1.0.0",
        "timestamp": time.time()
    }


@app.get("/v1/models", response_model=ModelList, tags=["models"])
async def list_models():
    """
    List available models.

    Compatible with OpenAI GET /v1/models endpoint.
    """
    available_models = adapter.get_available_models()
    created_ts = int(time.time())

    model_infos = [
        ModelInfo(
            id=model_id,
            object="model",
            created=created_ts,
            owned_by="cortex-flow"
        )
        for model_id in available_models
    ]

    return ModelList(
        object="list",
        data=model_infos
    )


@app.post("/v1/chat/completions", tags=["chat"])
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Create chat completion.

    Compatible with OpenAI POST /v1/chat/completions endpoint.

    Supports:
    - Standard chat completions
    - Conversation context via conversation_id
    - Streaming responses (stream=true)
    - Token usage tracking

    Example:
    ```json
    {
        "model": "cortex-flow",
        "messages": [
            {"role": "user", "content": "Research AI agent trends"}
        ],
        "stream": false
    }
    ```
    """
    start_time = time.time()

    try:
        # Validate model
        available_models = adapter.get_available_models()
        if not adapter.validate_model_name(request.model, available_models):
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model}' not found. Available: {available_models}"
            )

        # Generate or extract conversation ID
        conversation_id = adapter.generate_conversation_id(request)

        logger.info(f"Chat completion request: model={request.model}, "
                   f"conversation_id={conversation_id}, stream={request.stream}")

        # Handle streaming vs non-streaming
        if request.stream:
            return await _handle_streaming_completion(request, conversation_id)
        else:
            return await _handle_non_streaming_completion(
                request,
                conversation_id,
                start_time
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {e}", exc_info=True)

        # Return OpenAI-compatible error
        error_response = OpenAIErrorResponse(
            error=OpenAIError(
                message=str(e),
                type="server_error",
                code="internal_error"
            )
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump()
        )


async def _handle_non_streaming_completion(
    request: ChatCompletionRequest,
    conversation_id: str,
    start_time: float
) -> ChatCompletionResponse:
    """
    Handle non-streaming chat completion.

    Args:
        request: Chat completion request
        conversation_id: Conversation/thread ID
        start_time: Request start time

    Returns:
        ChatCompletionResponse
    """
    # Convert OpenAI messages to LangChain format
    langchain_messages = adapter.openai_messages_to_langchain(request.messages)

    # Trim messages if enabled
    if getattr(settings, 'enable_message_trimming', True):
        max_tokens = getattr(settings, 'max_conversation_tokens', 4000)
        strategy = getattr(settings, 'trimming_strategy', 'last')

        logger.debug(f"Trimming messages: max_tokens={max_tokens}, strategy={strategy}")

        langchain_messages = trim_messages(
            langchain_messages,
            max_tokens=max_tokens,
            strategy=strategy,
            token_counter=token_counter.count_langchain_message_tokens
        )

    # Get last user message for the task
    _, user_message = adapter.extract_system_and_user_messages(request.messages)

    # Invoke supervisor agent
    agent = await get_supervisor_agent()

    result = await agent.ainvoke(
        {"messages": langchain_messages},
        config={
            "configurable": {"thread_id": conversation_id},
            "recursion_limit": settings.max_iterations
        }
    )

    # Extract final response
    final_message = result["messages"][-1]
    response_content = final_message.content

    # Calculate token usage
    usage = token_counter.create_usage(
        prompt_messages=request.messages,
        completion_text=response_content
    )

    # Prepare metadata
    execution_time = time.time() - start_time
    metadata = adapter.merge_metadata(
        supervisor_metadata={
            "message_count": len(result["messages"]),
            "iteration_count": result.get("iteration_count", 0)
        },
        execution_time=execution_time
    )

    # Create OpenAI-compatible response
    response = adapter.create_completion_response(
        request=request,
        result_content=response_content,
        conversation_id=conversation_id,
        usage_data=usage,
        metadata=metadata,
        finish_reason="stop"
    )

    logger.info(f"Completion finished: conversation_id={conversation_id}, "
               f"tokens={usage.total_tokens}, time={execution_time:.2f}s")

    return response


async def _handle_streaming_completion(
    request: ChatCompletionRequest,
    conversation_id: str
) -> StreamingResponse:
    """
    Handle streaming chat completion.

    Args:
        request: Chat completion request
        conversation_id: Conversation/thread ID

    Returns:
        StreamingResponse with SSE
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events stream."""
        try:
            # Convert messages
            langchain_messages = adapter.openai_messages_to_langchain(request.messages)

            # Trim messages if enabled
            if getattr(settings, 'enable_message_trimming', True):
                max_tokens = getattr(settings, 'max_conversation_tokens', 4000)
                strategy = getattr(settings, 'trimming_strategy', 'last')

                logger.debug(f"Trimming messages (streaming): max_tokens={max_tokens}, strategy={strategy}")

                langchain_messages = trim_messages(
                    langchain_messages,
                    max_tokens=max_tokens,
                    strategy=strategy,
                    token_counter=token_counter.count_langchain_message_tokens
                )

            # Get agent
            agent = await get_supervisor_agent()

            # Stream from agent
            completion_id = f"chatcmpl-{conversation_id[:16]}"
            created_ts = int(time.time())

            # Initial chunk with role
            initial_chunk = ChatCompletionChunk(
                id=completion_id,
                object="chat.completion.chunk",
                created=created_ts,
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionChunkDelta(role="assistant"),
                        finish_reason=None
                    )
                ]
            )
            yield f"data: {initial_chunk.model_dump_json()}\n\n"

            # Stream chunks
            async for chunk in agent.astream(
                {"messages": langchain_messages},
                config={
                    "configurable": {"thread_id": conversation_id},
                    "recursion_limit": settings.max_iterations
                }
            ):
                # Extract content from chunk
                if "messages" in chunk and chunk["messages"]:
                    last_message = chunk["messages"][-1]
                    content = getattr(last_message, "content", "")

                    if content:
                        # Send content chunk
                        content_chunk = ChatCompletionChunk(
                            id=completion_id,
                            object="chat.completion.chunk",
                            created=created_ts,
                            model=request.model,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionChunkDelta(content=content),
                                    finish_reason=None
                                )
                            ]
                        )
                        yield f"data: {content_chunk.model_dump_json()}\n\n"

            # Final chunk with finish_reason
            final_chunk = ChatCompletionChunk(
                id=completion_id,
                object="chat.completion.chunk",
                created=created_ts,
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionChunkDelta(),
                        finish_reason="stop"
                    )
                ]
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"

            # Done marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)

            # Send error chunk
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = getattr(settings, "openai_compat_port", 8001)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
