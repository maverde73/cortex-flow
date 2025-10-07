"""
Tests for OpenAI API Compatibility

Tests the OpenAI-compatible API endpoints to ensure they work correctly
with standard OpenAI SDK and chatbot applications.
"""

import pytest
import httpx
import asyncio
from schemas.openai_schemas import ChatMessage, ChatCompletionRequest


class TestOpenAICompatibility:
    """Test OpenAI API compatibility."""

    BASE_URL = "http://localhost:8001"

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_list_models(self):
        """Test GET /v1/models endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/v1/models")
            assert response.status_code == 200

            data = response.json()
            assert data["object"] == "list"
            assert "data" in data
            assert len(data["data"]) > 0

            # Check model structure
            model = data["data"][0]
            assert "id" in model
            assert "object" in model
            assert model["object"] == "model"

    @pytest.mark.asyncio
    async def test_simple_chat_completion(self):
        """Test basic chat completion."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            request_data = {
                "model": "cortex-flow",
                "messages": [
                    {"role": "user", "content": "Say hello"}
                ],
                "stream": False
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()

            # Verify OpenAI response structure
            assert data["object"] == "chat.completion"
            assert "id" in data
            assert "created" in data
            assert data["model"] == "cortex-flow"
            assert "choices" in data
            assert len(data["choices"]) > 0

            # Check choice structure
            choice = data["choices"][0]
            assert choice["index"] == 0
            assert "message" in choice
            assert choice["message"]["role"] == "assistant"
            assert "content" in choice["message"]
            assert len(choice["message"]["content"]) > 0

            # Check usage
            assert "usage" in data
            assert "prompt_tokens" in data["usage"]
            assert "completion_tokens" in data["usage"]
            assert "total_tokens" in data["usage"]

    @pytest.mark.asyncio
    async def test_conversation_with_system_message(self):
        """Test chat completion with system message."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            request_data = {
                "model": "cortex-flow",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "What is 2+2?"}
                ],
                "stream": False
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["choices"][0]["message"]["content"]

    @pytest.mark.asyncio
    async def test_conversation_context(self):
        """Test conversation context with conversation_id."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            conversation_id = "test_conv_123"

            # First message
            request1 = {
                "model": "cortex-flow",
                "messages": [
                    {"role": "user", "content": "My name is Alice"}
                ],
                "conversation_id": conversation_id,
                "stream": False
            }

            response1 = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request1
            )

            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["conversation_id"] == conversation_id

            # Second message (should remember context)
            request2 = {
                "model": "cortex-flow",
                "messages": [
                    {"role": "user", "content": "My name is Alice"},
                    {"role": "assistant", "content": data1["choices"][0]["message"]["content"]},
                    {"role": "user", "content": "What is my name?"}
                ],
                "conversation_id": conversation_id,
                "stream": False
            }

            response2 = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request2
            )

            assert response2.status_code == 200
            data2 = response2.json()
            # Response should mention "Alice"
            assert "alice" in data2["choices"][0]["message"]["content"].lower()

    @pytest.mark.asyncio
    async def test_streaming_response(self):
        """Test streaming chat completion."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            request_data = {
                "model": "cortex-flow",
                "messages": [
                    {"role": "user", "content": "Count to 3"}
                ],
                "stream": True
            }

            async with client.stream(
                "POST",
                f"{self.BASE_URL}/v1/chat/completions",
                json=request_data
            ) as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

                chunks = []
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str == "[DONE]":
                            break

                        # Parse JSON chunk
                        import json
                        chunk_data = json.loads(data_str)

                        assert chunk_data["object"] == "chat.completion.chunk"
                        chunks.append(chunk_data)

                # Should have received multiple chunks
                assert len(chunks) > 0

                # Last chunk should have finish_reason
                last_chunk = chunks[-1]
                assert last_chunk["choices"][0]["finish_reason"] in ["stop", None]

    @pytest.mark.asyncio
    async def test_invalid_model(self):
        """Test request with invalid model name."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            request_data = {
                "model": "invalid-model",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "stream": False
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request_data
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_empty_messages(self):
        """Test request with empty messages array."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            request_data = {
                "model": "cortex-flow",
                "messages": [],
                "stream": False
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request_data
            )

            # Should return 422 (validation error)
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_with_temperature_parameter(self):
        """Test chat completion with temperature parameter."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            request_data = {
                "model": "cortex-flow",
                "messages": [
                    {"role": "user", "content": "Tell me a fun fact"}
                ],
                "temperature": 0.9,
                "stream": False
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["choices"][0]["message"]["content"]

    @pytest.mark.asyncio
    async def test_with_max_tokens_parameter(self):
        """Test chat completion with max_tokens parameter."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            request_data = {
                "model": "cortex-flow",
                "messages": [
                    {"role": "user", "content": "Write a short story"}
                ],
                "max_tokens": 100,
                "stream": False
            }

            response = await client.post(
                f"{self.BASE_URL}/v1/chat/completions",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()
            # Note: max_tokens is passed but actual enforcement depends on LLM
            assert data["choices"][0]["message"]["content"]


class TestOpenAISDKCompatibility:
    """Test compatibility with OpenAI Python SDK."""

    @pytest.mark.asyncio
    async def test_openai_sdk_basic_usage(self):
        """Test that OpenAI SDK can interact with our API."""
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url="http://localhost:8001/v1",
                api_key="dummy"  # API key not validated yet
            )

            response = client.chat.completions.create(
                model="cortex-flow",
                messages=[
                    {"role": "user", "content": "Say hello"}
                ]
            )

            assert response.choices[0].message.content
            assert response.usage.total_tokens > 0

        except ImportError:
            pytest.skip("OpenAI SDK not installed")

    @pytest.mark.asyncio
    async def test_openai_sdk_streaming(self):
        """Test streaming with OpenAI SDK."""
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url="http://localhost:8001/v1",
                api_key="dummy"
            )

            stream = client.chat.completions.create(
                model="cortex-flow",
                messages=[
                    {"role": "user", "content": "Count to 3"}
                ],
                stream=True
            )

            chunks = list(stream)
            assert len(chunks) > 0

        except ImportError:
            pytest.skip("OpenAI SDK not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
