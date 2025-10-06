"""
Regression tests for FASE 1: ReAct Fondamenti

Ensures that FASE 1 features still work after FASE 2 implementation.
Tests timeout, max_iterations, error tracking, and verbose logging.
"""

import pytest
import httpx
import time
from config import settings


class TestFase1TimeoutControl:
    """Regression tests for timeout control (FASE 1)."""

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_timeout_configured(self, test_settings):
        """Test that react_timeout_seconds is configured."""
        assert hasattr(test_settings, 'react_timeout_seconds')
        assert test_settings.react_timeout_seconds > 0

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_early_stopping_enabled(self, test_settings):
        """Test that early stopping is enabled."""
        assert hasattr(test_settings, 'react_enable_early_stopping')
        assert isinstance(test_settings.react_enable_early_stopping, bool)


class TestFase1MaxIterations:
    """Regression tests for max iterations control (FASE 1)."""

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_max_iterations_configured(self, test_settings):
        """Test that max_iterations is configured."""
        assert hasattr(test_settings, 'max_iterations')
        assert test_settings.max_iterations > 0

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_max_iterations_positive(self, test_settings):
        """Test that max_iterations is a positive number."""
        assert test_settings.max_iterations >= 1


class TestFase1ErrorTracking:
    """Regression tests for error tracking (FASE 1)."""

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_max_consecutive_errors_configured(self, test_settings):
        """Test that max_consecutive_errors is configured."""
        assert hasattr(test_settings, 'react_max_consecutive_errors')
        assert test_settings.react_max_consecutive_errors > 0

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_error_count_in_mock_state(self, mock_state):
        """Test that error_count is present in agent state."""
        assert "error_count" in mock_state
        assert mock_state["error_count"] == 0


class TestFase1VerboseLogging:
    """Regression tests for verbose logging (FASE 1)."""

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_verbose_logging_configured(self, test_settings):
        """Test that verbose logging flags are configured."""
        assert hasattr(test_settings, 'react_enable_verbose_logging')
        assert hasattr(test_settings, 'react_log_thoughts')
        assert hasattr(test_settings, 'react_log_actions')
        assert hasattr(test_settings, 'react_log_observations')

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_logging_flags_are_boolean(self, test_settings):
        """Test that logging flags are boolean values."""
        assert isinstance(test_settings.react_enable_verbose_logging, bool)
        assert isinstance(test_settings.react_log_thoughts, bool)
        assert isinstance(test_settings.react_log_actions, bool)
        assert isinstance(test_settings.react_log_observations, bool)


class TestFase1StateSchema:
    """Regression tests for agent state schema (FASE 1)."""

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_state_has_required_fields(self, mock_state):
        """Test that state has all required FASE 1 fields."""
        required_fields = [
            "messages",
            "iteration_count",
            "error_count",
            "start_time",
            "react_history",
            "should_stop",
            "early_stop_reason"
        ]
        for field in required_fields:
            assert field in mock_state, f"Missing required field: {field}"

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_iteration_count_initialized_to_zero(self, mock_state):
        """Test that iteration_count starts at 0."""
        assert mock_state["iteration_count"] == 0

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_start_time_is_recent(self, mock_state):
        """Test that start_time is a recent timestamp."""
        now = time.time()
        assert abs(now - mock_state["start_time"]) < 2  # Within 2 seconds

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_react_history_is_list(self, mock_state):
        """Test that react_history is initialized as empty list."""
        assert isinstance(mock_state["react_history"], list)
        assert len(mock_state["react_history"]) == 0

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_should_stop_is_false(self, mock_state):
        """Test that should_stop is initialized to False."""
        assert mock_state["should_stop"] is False

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_early_stop_reason_is_none(self, mock_state):
        """Test that early_stop_reason is initialized to None."""
        assert mock_state["early_stop_reason"] is None


class TestFase1AgentHealth:
    """Regression tests for agent health endpoints (FASE 1)."""

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.fase1
    @pytest.mark.asyncio
    async def test_supervisor_health(self, supervisor_url):
        """Test that supervisor health endpoint responds."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{supervisor_url}/health", timeout=5.0)
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Supervisor not running - skipping integration test")

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.fase1
    @pytest.mark.asyncio
    async def test_researcher_health(self, researcher_url):
        """Test that researcher health endpoint responds."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{researcher_url}/health", timeout=5.0)
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Researcher not running - skipping integration test")

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.fase1
    @pytest.mark.asyncio
    async def test_analyst_health(self, analyst_url):
        """Test that analyst health endpoint responds."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{analyst_url}/health", timeout=5.0)
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Analyst not running - skipping integration test")

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.fase1
    @pytest.mark.asyncio
    async def test_writer_health(self, writer_url):
        """Test that writer health endpoint responds."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{writer_url}/health", timeout=5.0)
                assert response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Writer not running - skipping integration test")


class TestFase1BackwardCompatibility:
    """Regression tests for backward compatibility (FASE 1)."""

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_settings_still_has_temperature(self, test_settings):
        """Test that global temperature setting still exists."""
        assert hasattr(test_settings, 'temperature')
        assert 0.0 <= test_settings.temperature <= 1.0

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_agent_urls_still_work(self, test_settings):
        """Test that agent URL properties still work."""
        assert hasattr(test_settings, 'supervisor_url')
        assert hasattr(test_settings, 'researcher_url')
        assert hasattr(test_settings, 'analyst_url')
        assert hasattr(test_settings, 'writer_url')

        # Test that URLs are properly formatted
        assert test_settings.supervisor_url.startswith("http://")
        assert test_settings.researcher_url.startswith("http://")

    @pytest.mark.unit
    @pytest.mark.regression
    @pytest.mark.fase1
    def test_llm_configuration_exists(self, test_settings):
        """Test that LLM configuration still exists."""
        assert hasattr(test_settings, 'default_model')
        assert hasattr(test_settings, 'researcher_model')
        assert hasattr(test_settings, 'analyst_model')
        assert hasattr(test_settings, 'writer_model')
        assert hasattr(test_settings, 'supervisor_model')


class TestFase1Integration:
    """Integration tests to verify FASE 1 features work end-to-end."""

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.fase1
    @pytest.mark.asyncio
    async def test_simple_query_completes(self, supervisor_url):
        """Test that a simple query completes successfully."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "task_id": "regression-test-001",
                    "source_agent_id": "test",
                    "target_agent_id": "supervisor",
                    "task_description": "What is 1+1?",
                    "context": {}
                }
                response = await client.post(
                    f"{supervisor_url}/invoke",
                    json=payload,
                    timeout=30.0
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "2" in data["result"] or "two" in data["result"].lower()
            except httpx.ConnectError:
                pytest.skip("Supervisor not running - skipping integration test")

    @pytest.mark.integration
    @pytest.mark.regression
    @pytest.mark.fase1
    @pytest.mark.asyncio
    async def test_response_has_metadata(self, supervisor_url):
        """Test that response includes FASE 1 metadata."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "task_id": "regression-test-002",
                    "source_agent_id": "test",
                    "target_agent_id": "supervisor",
                    "task_description": "Test query",
                    "context": {}
                }
                response = await client.post(
                    f"{supervisor_url}/invoke",
                    json=payload,
                    timeout=30.0
                )
                data = response.json()
                assert "metadata" in data
                assert "message_count" in data["metadata"]
                assert "thread_id" in data["metadata"]
            except httpx.ConnectError:
                pytest.skip("Supervisor not running - skipping integration test")
