# Development Guide

This guide covers development workflow, testing, and contribution guidelines for Cortex-Flow.

---

## Development Setup

### Prerequisites

```bash
# Python 3.12+
python --version

# Git
git --version

# Docker (optional, for PostgreSQL)
docker --version
```

### Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd cortex-flow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Add API keys
nano .env
```

---

## Project Structure

```
cortex-flow/
├── agents/              # Agent implementations (LangGraph)
│   ├── supervisor.py    # Orchestrator agent
│   ├── researcher.py    # Research agent
│   ├── analyst.py       # Analysis agent
│   └── writer.py        # Writing agent
│
├── servers/             # FastAPI servers
│   ├── supervisor_server.py
│   ├── researcher_server.py
│   ├── analyst_server.py
│   └── writer_server.py
│
├── tools/               # Agent tools
│   ├── web_tools.py     # Direct tools (Tavily, etc.)
│   └── proxy_tools.py   # Cross-server communication
│
├── utils/               # Shared utilities
│   ├── mcp_registry.py  # MCP server management
│   ├── mcp_client.py    # MCP tool execution
│   ├── react_*.py       # ReAct pattern utilities
│   └── checkpointer.py  # State persistence
│
├── schemas/             # Pydantic models
│   └── mcp_protocol.py  # MCP data structures
│
├── tests/               # Test suite
│   ├── test_fase*.py    # Feature tests
│   └── test_*.py        # Unit tests
│
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── config.py            # Configuration management
└── requirements.txt     # Dependencies
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Implement Changes

Follow the coding standards:
- Type hints for all functions
- Docstrings for public APIs
- Pydantic models for data validation
- Async/await for I/O operations

### 3. Write Tests

```bash
# Create test file
touch tests/test_my_feature.py
```

Example test:

```python
import pytest
from my_module import my_function

@pytest.mark.unit
def test_my_function():
    result = my_function(input_data)
    assert result == expected_output
```

### 4. Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_my_feature.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

Commit message format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Build/config changes

---

## Testing

### Test Markers

```python
@pytest.mark.unit          # Unit test (no dependencies)
@pytest.mark.integration   # Integration test (requires services)
@pytest.mark.regression    # Backward compatibility test
@pytest.mark.fase1         # Feature-specific tests
```

### Run Tests by Type

```bash
# Unit tests only
pytest tests/ -m unit

# Integration tests
pytest tests/ -m integration

# Feature tests
pytest tests/ -m fase2  # Strategies
pytest tests/ -m fase3  # Reflection
pytest tests/ -m fase4  # Logging
pytest tests/ -m fase5  # HITL
```

### Test Coverage

```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html

# View report
open htmlcov/index.html
```

---

## Code Quality

### Type Checking

```bash
# Install mypy
pip install mypy

# Run type checker
mypy agents/ servers/ utils/
```

### Linting

```bash
# Install ruff
pip install ruff

# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Formatting

```bash
# Install black
pip install black

# Format code
black .
```

---

## Debugging

### Enable Verbose Logging

In `.env`:

```bash
REACT_ENABLE_VERBOSE_LOGGING=true
REACT_LOG_THOUGHTS=true
REACT_LOG_ACTIONS=true
REACT_LOG_OBSERVATIONS=true
```

### Debug Specific Agent

```bash
# Run agent with debug logging
python -m servers.supervisor_server --log-level DEBUG
```

### Use Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

---

## Adding New Features

### Add New Agent

1. Create agent file: `agents/my_agent.py`
2. Implement LangGraph StateGraph
3. Define tools
4. Create server: `servers/my_agent_server.py`
5. Add configuration to `.env`
6. Update proxy tools for Supervisor

### Add New Tool

1. Create tool in `tools/`:

```python
from langchain_core.tools import tool

@tool
def my_tool(input: str) -> str:
    """Tool description."""
    # Implementation
    return result
```

2. Register tool with agent
3. Test tool execution

### Add New MCP Server

1. Configure in `.env`:

```bash
MCP_SERVER_MYSERVER_TYPE=remote
MCP_SERVER_MYSERVER_URL=http://localhost:8005
MCP_SERVER_MYSERVER_ENABLED=true
```

2. Restart supervisor
3. Verify discovery: `python scripts/test_mcp_servers.py`

---

## Documentation

### Update Documentation

When adding features:

1. Update relevant `.md` files in `docs/`
2. Add examples to `workflows/examples/`
3. Update `.env.example` for new config
4. Update `CHANGELOG.md`

### Generate API Docs

```bash
# View OpenAPI docs
# Start supervisor and visit:
open http://localhost:8000/docs
```

---

## Performance Testing

### Measure Latency

```bash
# Install hyperfine
brew install hyperfine  # Mac
# OR apt install hyperfine  # Linux

# Benchmark endpoint
hyperfine 'curl -X POST http://localhost:8000/invoke -d @test_payload.json'
```

### Monitor Resource Usage

```bash
# CPU and memory
htop

# Or with Docker stats
docker stats
```

---

## Useful Scripts

Located in `scripts/`:

```bash
# Start all agents
./scripts/start_all.sh

# Stop all agents
./scripts/stop_all.sh

# Run MCP tests
python scripts/test_corporate_prompts.py
python scripts/test_langchain_tool_prompts.py

# Health check all agents
./scripts/health_check.sh
```

---

## Common Issues

### Import Errors

```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Port Conflicts

```bash
# Find and kill process on port
lsof -i :8000
kill -9 <PID>
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection
psql postgresql://cortex:cortex_dev_password@localhost:5432/cortex_flow
```

---

## CI/CD

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

---

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Make changes
4. Write tests
5. Update documentation
6. Submit pull request

### Code Review Checklist

- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] Type hints added
- [ ] No breaking changes (or documented)

---

## Resources

- [**Scripts Reference**](scripts.md) - Utility scripts
- [**Testing Guide**](testing.md) - Complete testing documentation
- [**Claude Code Guide**](claude-code.md) - AI-assisted development
- [**Contributing**](contributing.md) - How to contribute

---

**Last Updated**: 2025-10-06
