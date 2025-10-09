"""
Base Agent Template for Lite Implementation

Provides common functionality for all lite agents.
"""

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLiteAgent(ABC):
    """Base class for all lite agent implementations."""

    def __init__(self, agent_type: str):
        """
        Initialize the base agent.

        Args:
            agent_type: Type of agent (researcher, analyst, writer)
        """
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"agent.{agent_type}")

    async def execute(self, instruction: str, llm_client) -> str:
        """
        Execute the agent with given instruction.

        Args:
            instruction: The task instruction
            llm_client: LLM client instance

        Returns:
            Agent response as string
        """
        try:
            self.logger.info(f"Executing {self.agent_type} agent")
            self.logger.debug(f"Instruction: {instruction[:200]}...")

            # Build the prompt
            prompt = self._build_prompt(instruction)

            # Call LLM
            response = await llm_client.complete(prompt)

            # Post-process if needed
            result = self._post_process(response)

            self.logger.debug(f"Response: {result[:200]}...")
            return result

        except Exception as e:
            self.logger.error(f"Error in {self.agent_type} agent: {e}")
            raise

    @abstractmethod
    def _build_prompt(self, instruction: str) -> str:
        """
        Build the agent-specific prompt.

        Args:
            instruction: The task instruction

        Returns:
            Formatted prompt for the LLM
        """
        pass

    def _post_process(self, response: str) -> str:
        """
        Post-process the LLM response.

        Args:
            response: Raw LLM response

        Returns:
            Processed response
        """
        # Default: no processing
        return response

    def _get_system_prompt(self) -> str:
        """
        Get the base system prompt common to all agents.

        Returns:
            System prompt string
        """
        return """You are an AI assistant specialized in {role}.
You provide clear, accurate, and helpful responses.
Focus on the specific task provided and deliver high-quality output."""