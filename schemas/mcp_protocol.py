"""
Model Context Protocol (MCP) definitions.

This module defines the standardized communication protocol for inter-agent messaging.
All agents communicate using these Pydantic models to ensure type safety and validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4


class MCPRequest(BaseModel):
    """
    Standard request format for inter-agent communication.

    This is the payload sent from one agent to another when delegating a task.
    """

    task_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this task"
    )
    source_agent_id: str = Field(
        ...,
        description="Identifier of the agent making the request"
    )
    target_agent_id: str = Field(
        ...,
        description="Identifier of the agent that should handle this task"
    )
    task_description: str = Field(
        ...,
        description="Natural language description of the task to be performed"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context or parameters for the task"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this request was created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "source_agent_id": "supervisor",
                "target_agent_id": "researcher",
                "task_description": "Find the latest news about LangGraph framework",
                "context": {
                    "keywords": ["LangGraph", "AI agents"],
                    "time_range": "last_7_days"
                },
                "timestamp": "2025-10-06T10:30:00Z"
            }
        }


class MCPResponse(BaseModel):
    """
    Standard response format for inter-agent communication.

    This is returned by the agent that performed the task.
    """

    task_id: str = Field(
        ...,
        description="Same task_id from the request for correlation"
    )
    source_agent_id: str = Field(
        ...,
        description="Agent that performed the task"
    )
    status: str = Field(
        ...,
        description="Status of task execution: 'success', 'error', 'partial'"
    )
    result: Optional[str] = Field(
        None,
        description="The result of the task execution"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if status is 'error'"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the execution"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this response was created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "source_agent_id": "researcher",
                "status": "success",
                "result": "Found 5 recent articles about LangGraph...",
                "error_message": None,
                "metadata": {
                    "sources_count": 5,
                    "execution_time_ms": 2450
                },
                "timestamp": "2025-10-06T10:30:15Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response for monitoring agent availability."""

    agent_id: str
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
