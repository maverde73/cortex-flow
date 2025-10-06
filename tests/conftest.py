"""
Pytest configuration and shared fixtures for Cortex Flow tests.

This module provides common fixtures and configuration for all test modules.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path is set
from config_legacy import settings
from utils.react_strategies import ReactConfig, ReactStrategy


@pytest.fixture
def test_settings():
    """Fixture that provides test settings."""
    return settings


@pytest.fixture
def fast_config():
    """Fixture that provides FAST ReactConfig."""
    return ReactConfig.from_strategy(ReactStrategy.FAST)


@pytest.fixture
def balanced_config():
    """Fixture that provides BALANCED ReactConfig."""
    return ReactConfig.from_strategy(ReactStrategy.BALANCED)


@pytest.fixture
def deep_config():
    """Fixture that provides DEEP ReactConfig."""
    return ReactConfig.from_strategy(ReactStrategy.DEEP)


@pytest.fixture
def creative_config():
    """Fixture that provides CREATIVE ReactConfig."""
    return ReactConfig.from_strategy(ReactStrategy.CREATIVE)


@pytest.fixture
def mock_state():
    """Fixture that provides a mock agent state for testing."""
    import time
    return {
        "messages": [],
        "iteration_count": 0,
        "error_count": 0,
        "start_time": time.time(),
        "react_history": [],
        "should_stop": False,
        "early_stop_reason": None
    }


@pytest.fixture
def supervisor_url():
    """Fixture that provides supervisor API URL."""
    return f"http://{settings.supervisor_host}:{settings.supervisor_port}"


@pytest.fixture
def researcher_url():
    """Fixture that provides researcher API URL."""
    return f"http://{settings.researcher_host}:{settings.researcher_port}"


@pytest.fixture
def analyst_url():
    """Fixture that provides analyst API URL."""
    return f"http://{settings.analyst_host}:{settings.analyst_port}"


@pytest.fixture
def writer_url():
    """Fixture that provides writer API URL."""
    return f"http://{settings.writer_host}:{settings.writer_port}"


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require running servers)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "regression: marks tests as regression tests (verify old features still work)"
    )
    config.addinivalue_line(
        "markers", "fase1: marks tests for FASE 1 features"
    )
    config.addinivalue_line(
        "markers", "fase2: marks tests for FASE 2 features"
    )
    config.addinivalue_line(
        "markers", "fase3: marks tests for FASE 3 features (Self-Reflection)"
    )
    config.addinivalue_line(
        "markers", "fase4: marks tests for FASE 4 features (Structured Logging)"
    )
    config.addinivalue_line(
        "markers", "fase5: marks tests for FASE 5 features (Human-in-the-Loop)"
    )
    config.addinivalue_line(
        "markers", "fase6: marks tests for FASE 6 features (Advanced Reasoning Modes)"
    )
