# Tests Directory

This directory contains all test files for the Cortex Flow system.

## Test Files

### `test_system.py`
Integration test that verifies the entire multi-agent system.

**Usage:**
```bash
# Make sure agents are running first
./scripts/start_all.sh

# Run tests
python tests/test_system.py
```

**What it tests:**
- Health checks for all agents
- MCP protocol communication
- Supervisor orchestration
- End-to-end workflow

**Expected output:**
```
🧪 Cortex Flow System Test Suite
================================================================
📋 Phase 1: Health Checks
   ✅ Researcher is healthy
   ✅ Analyst is healthy
   ✅ Writer is healthy
   ✅ Supervisor is healthy

📋 Phase 2: Supervisor Orchestration
   ✅ Supervisor orchestration successful!
```

---

## Adding New Tests

### Unit Tests

For testing individual components:

```python
# tests/test_registry.py
import pytest
from services.registry import AgentRegistry

@pytest.mark.asyncio
async def test_agent_registration():
    registry = AgentRegistry()
    success = await registry.register(
        agent_id="test",
        url="http://localhost:9999",
        check_health=False
    )
    assert success
```

### Integration Tests

For testing multi-component interactions:

```python
# tests/test_proxy_tools.py
import pytest
from tools.proxy_tools import research_web

@pytest.mark.asyncio
async def test_researcher_proxy():
    result = await research_web("test query")
    assert isinstance(result, str)
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_system.py

# Run with coverage
pytest --cov=. tests/

# Run with verbose output
pytest -v tests/
```

## Test Organization

```
tests/
├── README.md                # This file
├── test_system.py           # System integration tests
├── test_agents.py           # Agent-specific tests
├── test_registry.py         # Service registry tests
├── test_proxy_tools.py      # Proxy tool tests
└── conftest.py              # Shared fixtures
```

## Writing Good Tests

### Best Practices

1. **Use descriptive names**: `test_agent_retries_on_connection_error`
2. **One assertion per test**: Focus on single behavior
3. **Use fixtures**: Share setup code with `@pytest.fixture`
4. **Mark async tests**: Use `@pytest.mark.asyncio`
5. **Mock external services**: Don't rely on real APIs

### Example Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_supervisor_handles_agent_failure():
    """Test that supervisor gracefully handles agent failures."""

    # Arrange
    with patch('tools.proxy_tools._call_agent_async') as mock_call:
        mock_call.return_value = "⚠️ Agent unavailable"

        # Act
        from agents.supervisor import get_supervisor_agent
        agent = await get_supervisor_agent()
        result = await agent.ainvoke({"messages": [...]})

        # Assert
        assert "unavailable" in result["messages"][-1].content
```

## CI/CD Integration

Tests should be run in CI pipeline:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov
```

## Test Coverage Goals

- **Agents**: 80%+ coverage
- **Services**: 90%+ coverage
- **Tools**: 85%+ coverage
- **Overall**: 80%+ coverage

Check coverage with:
```bash
pytest --cov=. --cov-report=html tests/
open htmlcov/index.html
```
