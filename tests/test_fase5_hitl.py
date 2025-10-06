"""
Unit tests for FASE 5: Human-in-the-Loop (HITL)

Tests approval requests, decisions, configuration, and manager.
"""

import pytest
import time
from utils.react_hitl import (
    ApprovalAction,
    ApprovalStatus,
    ApprovalRequest,
    ApprovalDecision,
    HITLConfig,
    HITLManager,
    get_hitl_config,
    is_hitl_enabled,
    requires_approval,
    create_approval_request
)


class TestApprovalAction:
    """Test ApprovalAction enum."""

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_approval_actions_exist(self):
        """Test that all expected actions exist."""
        assert ApprovalAction.APPROVE == "approve"
        assert ApprovalAction.REJECT == "reject"
        assert ApprovalAction.MODIFY == "modify"


class TestApprovalRequest:
    """Test ApprovalRequest dataclass."""

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_request_creation(self):
        """Test creating an approval request."""
        request = ApprovalRequest(
            tool_name="send_email",
            tool_input={"to": "user@example.com", "subject": "Test"},
            agent_name="writer",
            task_id="task-001",
            iteration=1,
            timeout_seconds=300.0
        )
        assert request.tool_name == "send_email"
        assert request.agent_name == "writer"
        assert request.timeout_seconds == 300.0

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_request_is_not_expired_initially(self):
        """Test that new request is not expired."""
        request = ApprovalRequest(
            tool_name="test_tool",
            tool_input={},
            agent_name="test",
            task_id="test-001",
            iteration=1,
            timeout_seconds=10.0
        )
        assert not request.is_expired()
        assert request.time_remaining() > 0

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_request_expires_after_timeout(self):
        """Test that request expires after timeout."""
        request = ApprovalRequest(
            tool_name="test_tool",
            tool_input={},
            agent_name="test",
            task_id="test-002",
            iteration=1,
            timeout_seconds=0.1  # 100ms
        )
        time.sleep(0.15)  # Wait for expiry
        assert request.is_expired()
        assert request.time_remaining() == 0

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_request_to_dict(self):
        """Test converting request to dictionary."""
        request = ApprovalRequest(
            tool_name="publish_content",
            tool_input={"url": "/blog/post-1"},
            agent_name="writer",
            task_id="task-003",
            iteration=2
        )
        request_dict = request.to_dict()
        assert "tool_name" in request_dict
        assert "agent_name" in request_dict
        assert "time_remaining" in request_dict
        assert request_dict["tool_name"] == "publish_content"


class TestApprovalDecision:
    """Test ApprovalDecision dataclass."""

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_decision_approve(self):
        """Test creating approve decision."""
        decision = ApprovalDecision(
            action=ApprovalAction.APPROVE,
            reason="Looks good",
            approved_by="user@example.com"
        )
        assert decision.action == ApprovalAction.APPROVE
        assert decision.reason == "Looks good"

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_decision_reject(self):
        """Test creating reject decision."""
        decision = ApprovalDecision(
            action=ApprovalAction.REJECT,
            reason="Wrong recipient"
        )
        assert decision.action == ApprovalAction.REJECT
        assert decision.reason == "Wrong recipient"

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_decision_modify(self):
        """Test creating modify decision."""
        decision = ApprovalDecision(
            action=ApprovalAction.MODIFY,
            modified_input={"to": "correct@example.com"}
        )
        assert decision.action == ApprovalAction.MODIFY
        assert decision.modified_input == {"to": "correct@example.com"}

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_decision_to_dict(self):
        """Test converting decision to dictionary."""
        decision = ApprovalDecision(
            action=ApprovalAction.APPROVE,
            reason="Approved"
        )
        decision_dict = decision.to_dict()
        assert "action" in decision_dict
        assert "timestamp" in decision_dict
        assert decision_dict["action"] == "approve"


class TestHITLConfig:
    """Test HITLConfig class."""

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_config_disabled_by_default(self):
        """Test that HITL is disabled by default."""
        config = HITLConfig()
        assert config.enabled is False
        assert not config.requires_approval("any_tool")

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_config_requires_approval_exact_match(self):
        """Test exact tool name matching."""
        config = HITLConfig(
            enabled=True,
            require_approval_for=["send_email", "delete_data"]
        )
        assert config.requires_approval("send_email")
        assert config.requires_approval("delete_data")
        assert not config.requires_approval("read_data")

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_config_requires_approval_wildcard(self):
        """Test wildcard pattern matching."""
        config = HITLConfig(
            enabled=True,
            require_approval_for=["send_*", "delete_*"]
        )
        assert config.requires_approval("send_email")
        assert config.requires_approval("send_sms")
        assert config.requires_approval("delete_file")
        assert not config.requires_approval("read_file")

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_config_disabled_means_no_approval_needed(self):
        """Test that disabled config never requires approval."""
        config = HITLConfig(
            enabled=False,
            require_approval_for=["send_email"]
        )
        assert not config.requires_approval("send_email")


class TestHITLManager:
    """Test HITLManager class."""

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_manager_create_request(self):
        """Test creating approval request via manager."""
        manager = HITLManager()
        request = manager.create_request(
            tool_name="send_email",
            tool_input={"to": "test@example.com"},
            agent_name="writer",
            task_id="task-100",
            iteration=1
        )
        assert request.tool_name == "send_email"
        assert request.task_id == "task-100"

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_manager_get_request(self):
        """Test retrieving approval request."""
        manager = HITLManager()
        manager.create_request(
            tool_name="test_tool",
            tool_input={},
            agent_name="test",
            task_id="task-101",
            iteration=1
        )
        request = manager.get_request("task-101")
        assert request is not None
        assert request.task_id == "task-101"

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_manager_make_decision(self):
        """Test making decision on request."""
        manager = HITLManager()
        manager.create_request(
            tool_name="test_tool",
            tool_input={},
            agent_name="test",
            task_id="task-102",
            iteration=1
        )
        decision = manager.make_decision(
            task_id="task-102",
            action=ApprovalAction.APPROVE,
            reason="Looks good"
        )
        assert decision.action == ApprovalAction.APPROVE
        assert decision.reason == "Looks good"

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_manager_get_decision(self):
        """Test retrieving decision."""
        manager = HITLManager()
        manager.create_request(
            tool_name="test_tool",
            tool_input={},
            agent_name="test",
            task_id="task-103",
            iteration=1
        )
        manager.make_decision(
            task_id="task-103",
            action=ApprovalAction.REJECT
        )
        decision = manager.get_decision("task-103")
        assert decision is not None
        assert decision.action == ApprovalAction.REJECT

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_manager_clear_request(self):
        """Test clearing request and decision."""
        manager = HITLManager()
        manager.create_request(
            tool_name="test_tool",
            tool_input={},
            agent_name="test",
            task_id="task-104",
            iteration=1
        )
        manager.make_decision(task_id="task-104", action=ApprovalAction.APPROVE)

        manager.clear_request("task-104")

        assert manager.get_request("task-104") is None
        assert manager.get_decision("task-104") is None

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_manager_list_pending(self):
        """Test listing pending requests."""
        manager = HITLManager()
        manager.create_request(
            tool_name="tool1",
            tool_input={},
            agent_name="test",
            task_id="task-105",
            iteration=1
        )
        manager.create_request(
            tool_name="tool2",
            tool_input={},
            agent_name="test",
            task_id="task-106",
            iteration=1
        )

        pending = manager.list_pending()
        assert len(pending) >= 2  # At least our 2 requests
        task_ids = [r.task_id for r in pending]
        assert "task-105" in task_ids
        assert "task-106" in task_ids


class TestHITLIntegration:
    """Integration tests for HITL workflow."""

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_complete_approval_flow(self):
        """Test complete approval workflow."""
        manager = HITLManager()

        # Create request
        request = manager.create_request(
            tool_name="send_email",
            tool_input={"to": "client@example.com", "body": "Hello"},
            agent_name="writer",
            task_id="task-200",
            iteration=1,
            reasoning="Need to send follow-up email"
        )

        assert request is not None
        assert not request.is_expired()

        # Make decision
        decision = manager.make_decision(
            task_id="task-200",
            action=ApprovalAction.APPROVE,
            approved_by="human@example.com"
        )

        assert decision.action == ApprovalAction.APPROVE
        assert decision.approved_by == "human@example.com"

        # Clear after processing
        manager.clear_request("task-200")
        assert manager.get_request("task-200") is None

    @pytest.mark.unit
    @pytest.mark.fase5
    def test_modify_workflow(self):
        """Test modify approval workflow."""
        manager = HITLManager()

        manager.create_request(
            tool_name="send_email",
            tool_input={"to": "wrong@example.com"},
            agent_name="writer",
            task_id="task-201",
            iteration=1
        )

        # Human modifies the input
        decision = manager.make_decision(
            task_id="task-201",
            action=ApprovalAction.MODIFY,
            modified_input={"to": "correct@example.com"},
            reason="Wrong recipient"
        )

        assert decision.action == ApprovalAction.MODIFY
        assert decision.modified_input["to"] == "correct@example.com"
