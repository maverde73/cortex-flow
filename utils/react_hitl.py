"""
Human-in-the-Loop (HITL) Module for ReAct Pattern (FASE 5)

Enables human approval for critical agent actions before execution.
Supports approve, reject, and modify workflows.
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ApprovalAction(str, Enum):
    """Actions that can be taken on a pending approval."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"


@dataclass
class ApprovalRequest:
    """
    Request for human approval of an agent action.

    Contains all information needed for human to make decision.
    """
    tool_name: str                    # Name of tool/action requiring approval
    tool_input: Dict[str, Any]        # Input parameters for the tool
    agent_name: str                   # Agent requesting approval
    task_id: str                      # Task identifier
    iteration: int                    # Current ReAct iteration
    timestamp: float = field(default_factory=time.time)  # Request time
    timeout_seconds: float = 300.0    # Approval timeout (5 min default)
    reasoning: Optional[str] = None   # Agent's reasoning for action
    metadata: Optional[Dict[str, Any]] = None  # Additional context

    def is_expired(self) -> bool:
        """Check if approval request has timed out."""
        elapsed = time.time() - self.timestamp
        return elapsed > self.timeout_seconds

    def time_remaining(self) -> float:
        """Get seconds remaining before timeout."""
        elapsed = time.time() - self.timestamp
        remaining = self.timeout_seconds - elapsed
        return max(0.0, remaining)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "iteration": self.iteration,
            "timestamp": self.timestamp,
            "timeout_seconds": self.timeout_seconds,
            "time_remaining": self.time_remaining(),
            "is_expired": self.is_expired(),
            "reasoning": self.reasoning,
            "metadata": self.metadata or {}
        }


@dataclass
class ApprovalDecision:
    """
    Human decision on an approval request.

    Can approve, reject, or modify the agent action.
    """
    action: ApprovalAction                    # approve, reject, or modify
    timestamp: float = field(default_factory=time.time)
    reason: Optional[str] = None              # Human's reason for decision
    modified_input: Optional[Dict[str, Any]] = None  # Modified tool input (if action=modify)
    approved_by: Optional[str] = None         # User who approved (for audit)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "modified_input": self.modified_input,
            "approved_by": self.approved_by
        }


@dataclass
class HITLConfig:
    """
    Configuration for Human-in-the-Loop functionality.

    Defines which actions require approval and timeout settings.
    """
    enabled: bool = False                                 # Master HITL switch
    require_approval_for: List[str] = field(default_factory=list)  # Tool names requiring approval
    default_timeout_seconds: float = 300.0                # Default approval timeout
    timeout_action: ApprovalAction = ApprovalAction.REJECT  # Action on timeout (reject or approve)
    notify_url: Optional[str] = None                      # Webhook URL for notifications

    def requires_approval(self, tool_name: str) -> bool:
        """Check if a tool requires human approval."""
        if not self.enabled:
            return False

        # Check exact match
        if tool_name in self.require_approval_for:
            return True

        # Check wildcard patterns (e.g., "send_*" matches "send_email")
        for pattern in self.require_approval_for:
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if tool_name.startswith(prefix):
                    return True

        return False

    @classmethod
    def from_agent(cls, agent_name: str) -> "HITLConfig":
        """
        Create HITL config for specific agent from environment settings.

        Loads agent-specific and global HITL configuration.
        """
        from config_legacy import settings

        # Check if HITL enabled globally
        global_enabled = getattr(settings, "react_enable_hitl", False)

        # Check if enabled for this specific agent
        agent_enabled_key = f"{agent_name}_enable_hitl"
        agent_enabled = getattr(settings, agent_enabled_key, global_enabled)

        # Get approval requirements
        approval_list_key = f"{agent_name}_hitl_require_approval_for"
        approval_list_str = getattr(settings, approval_list_key, "")

        # Parse comma-separated list
        require_approval_for = []
        if approval_list_str:
            require_approval_for = [s.strip() for s in approval_list_str.split(",") if s.strip()]

        # Get timeout
        timeout_key = f"{agent_name}_hitl_timeout_seconds"
        timeout = getattr(settings, timeout_key, getattr(settings, "react_hitl_timeout_seconds", 300.0))

        # Get timeout action
        timeout_action_str = getattr(settings, "react_hitl_timeout_action", "reject")
        timeout_action = ApprovalAction.REJECT if timeout_action_str == "reject" else ApprovalAction.APPROVE

        return cls(
            enabled=agent_enabled,
            require_approval_for=require_approval_for,
            default_timeout_seconds=timeout,
            timeout_action=timeout_action
        )


class HITLManager:
    """
    Manager for Human-in-the-Loop approval requests.

    Tracks pending approvals and provides decision API.
    """

    def __init__(self):
        self.pending_requests: Dict[str, ApprovalRequest] = {}  # task_id -> request
        self.decisions: Dict[str, ApprovalDecision] = {}        # task_id -> decision

    def create_request(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        agent_name: str,
        task_id: str,
        iteration: int,
        timeout_seconds: float = 300.0,
        reasoning: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Stores request and returns it for state management.
        """
        request = ApprovalRequest(
            tool_name=tool_name,
            tool_input=tool_input,
            agent_name=agent_name,
            task_id=task_id,
            iteration=iteration,
            timeout_seconds=timeout_seconds,
            reasoning=reasoning
        )

        self.pending_requests[task_id] = request
        logger.info(f"[HITL] Approval request created for task {task_id}: {tool_name}")

        return request

    def get_request(self, task_id: str) -> Optional[ApprovalRequest]:
        """Get pending approval request for task."""
        request = self.pending_requests.get(task_id)

        # Check if expired
        if request and request.is_expired():
            logger.warning(f"[HITL] Approval request for task {task_id} has expired")
            # Auto-handle timeout (will be handled by agent)

        return request

    def make_decision(
        self,
        task_id: str,
        action: ApprovalAction,
        reason: Optional[str] = None,
        modified_input: Optional[Dict[str, Any]] = None,
        approved_by: Optional[str] = None
    ) -> ApprovalDecision:
        """
        Make a decision on a pending approval request.

        Returns the decision for agent to process.
        """
        if task_id not in self.pending_requests:
            raise ValueError(f"No pending approval request for task {task_id}")

        decision = ApprovalDecision(
            action=action,
            reason=reason,
            modified_input=modified_input,
            approved_by=approved_by
        )

        self.decisions[task_id] = decision
        logger.info(f"[HITL] Decision made for task {task_id}: {action.value}")

        return decision

    def get_decision(self, task_id: str) -> Optional[ApprovalDecision]:
        """Get decision for task if available."""
        return self.decisions.get(task_id)

    def clear_request(self, task_id: str):
        """Clear approval request and decision after processing."""
        self.pending_requests.pop(task_id, None)
        self.decisions.pop(task_id, None)
        logger.debug(f"[HITL] Cleared approval data for task {task_id}")

    def list_pending(self) -> List[ApprovalRequest]:
        """List all pending approval requests."""
        return list(self.pending_requests.values())


# Global HITL manager instance
hitl_manager = HITLManager()


# Convenience functions

def get_hitl_config(agent_name: str) -> HITLConfig:
    """Get HITL configuration for agent."""
    return HITLConfig.from_agent(agent_name)


def is_hitl_enabled(agent_name: str) -> bool:
    """Check if HITL is enabled for agent."""
    config = get_hitl_config(agent_name)
    return config.enabled


def requires_approval(agent_name: str, tool_name: str) -> bool:
    """Check if tool requires approval for agent."""
    config = get_hitl_config(agent_name)
    return config.requires_approval(tool_name)


def create_approval_request(
    tool_name: str,
    tool_input: Dict[str, Any],
    agent_name: str,
    task_id: str,
    iteration: int,
    config: Optional[HITLConfig] = None,
    reasoning: Optional[str] = None
) -> ApprovalRequest:
    """Create approval request (convenience wrapper)."""
    if config is None:
        config = get_hitl_config(agent_name)

    return hitl_manager.create_request(
        tool_name=tool_name,
        tool_input=tool_input,
        agent_name=agent_name,
        task_id=task_id,
        iteration=iteration,
        timeout_seconds=config.default_timeout_seconds,
        reasoning=reasoning
    )
