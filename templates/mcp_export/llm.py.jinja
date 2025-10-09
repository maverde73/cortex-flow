"""
Modular LLM Client for Standalone MCP Export

Supports multiple LLM providers with a unified interface.
Configuration via environment variables.
"""

import os
import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    LITE = "lite"  # Minimal HTTP-only implementation


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            provider: Provider to use (auto-detect from env if not specified)
        """
        self.provider = self._detect_provider(provider)
        self.client = None
        self.model = None
        self.api_key = None
        self.base_url = None
        self.timeout = float(os.getenv("LLM_TIMEOUT", "300"))  # Default 5 minutes

        self._initialize_provider()

    def _detect_provider(self, provider: Optional[str]) -> LLMProvider:
        """
        Detect LLM provider from environment or parameter.

        Args:
            provider: Explicitly specified provider

        Returns:
            LLMProvider enum value
        """
        if provider:
            try:
                return LLMProvider(provider.lower())
            except ValueError:
                logger.warning(f"Unknown provider {provider}, falling back to auto-detect")

        # Auto-detect based on available API keys
        if os.getenv("OPENAI_API_KEY"):
            return LLMProvider.OPENAI
        elif os.getenv("ANTHROPIC_API_KEY"):
            return LLMProvider.ANTHROPIC
        elif os.getenv("GROQ_API_KEY"):
            return LLMProvider.GROQ
        elif os.getenv("OPENROUTER_API_KEY"):
            return LLMProvider.OPENROUTER
        elif os.getenv("OLLAMA_BASE_URL"):
            return LLMProvider.OLLAMA
        else:
            logger.warning("No API keys found, using LITE provider (mock responses)")
            return LLMProvider.LITE

    def _initialize_provider(self):
        """Initialize the selected provider."""
        logger.info(f"Initializing LLM provider: {self.provider.value}")

        if self.provider == LLMProvider.OPENAI:
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        elif self.provider == LLMProvider.ANTHROPIC:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            self.base_url = "https://api.anthropic.com/v1"
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

        elif self.provider == LLMProvider.GROQ:
            self.api_key = os.getenv("GROQ_API_KEY")
            self.base_url = "https://api.groq.com/openai/v1"
            self.model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

        elif self.provider == LLMProvider.OPENROUTER:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.base_url = "https://openrouter.ai/api/v1"
            self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

        elif self.provider == LLMProvider.OLLAMA:
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.model = os.getenv("OLLAMA_MODEL", "llama2")

        elif self.provider == LLMProvider.LITE:
            # Lite mode - will return mock responses
            self.model = "mock"

    async def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Get completion from LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response

        Returns:
            LLM response text
        """
        if self.provider == LLMProvider.LITE:
            return self._mock_response(prompt)

        try:
            if self.provider in [LLMProvider.OPENAI, LLMProvider.GROQ, LLMProvider.OPENROUTER]:
                return await self._openai_compatible_complete(prompt, max_tokens)
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._anthropic_complete(prompt, max_tokens)
            elif self.provider == LLMProvider.OLLAMA:
                return await self._ollama_complete(prompt, max_tokens)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            # Fallback to mock response
            return self._mock_response(prompt)

    async def _openai_compatible_complete(self, prompt: str, max_tokens: int) -> str:
        """
        Complete using OpenAI-compatible API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens

        Returns:
            Response text
        """
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Add special headers for OpenRouter
            if self.provider == LLMProvider.OPENROUTER:
                headers["HTTP-Referer"] = "https://github.com/cortex-flow"
                headers["X-Title"] = "Cortex Flow MCP Export"

            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

    async def _anthropic_complete(self, prompt: str, max_tokens: int) -> str:
        """
        Complete using Anthropic API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens

        Returns:
            Response text
        """
        async with httpx.AsyncClient() as client:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens
            }

            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=data,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]

    async def _ollama_complete(self, prompt: str, max_tokens: int) -> str:
        """
        Complete using Ollama API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens

        Returns:
            Response text
        """
        async with httpx.AsyncClient() as client:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()
            return result["response"]

    def _mock_response(self, prompt: str) -> str:
        """
        Generate mock response for LITE mode.

        Args:
            prompt: Input prompt

        Returns:
            Mock response
        """
        # Parse the prompt to understand what kind of response is expected
        prompt_lower = prompt.lower()

        if "research" in prompt_lower:
            return """# Research Report

## Key Information
Based on the available information, here are the main findings related to the research task.

## Context
The topic relates to several important areas that require further investigation.

## Insights
Several patterns have been identified that warrant attention.

## Summary
This research provides a foundation for understanding the topic at hand."""

        elif "analy" in prompt_lower:
            return """# Analysis Report

## Data Overview
The information has been systematically analyzed.

## Key Patterns
Several significant trends have been identified.

## Insights
The analysis reveals important implications.

## Recommendations
Based on the analysis, several actions are recommended."""

        elif "writ" in prompt_lower:
            return """# Document

## Introduction
This document addresses the requested topic comprehensively.

## Main Content
The key points have been organized and presented clearly.

## Conclusion
The document provides a complete overview of the subject matter."""

        else:
            return f"Response to task: {prompt[:100]}..."


def create_llm_client(provider: Optional[str] = None) -> LLMClient:
    """
    Factory function to create LLM client.

    Args:
        provider: Optional provider override

    Returns:
        Configured LLM client
    """
    return LLMClient(provider)