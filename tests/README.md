# Tests Directory

This directory contains all test files for the Cortex Flow multi-agent system.

## Test Files Organization

### Database Query Project Tests
- `test_direct_mcp.py` - Direct MCP tool testing via supervisor API
- `test_database_workflow.py` - Workflow engine testing (database_query_with_retry)
- `test_complex_scenarios.py` - Complex multi-agent scenarios (5 tests)
- `test_complex_results.log` - Results from complex scenarios test

### MCP Integration Tests
- `test_mcp_integration.py` - Comprehensive MCP integration tests
- `test_mcp_manual.py` - Manual MCP testing
- `test_mcp_tool_call.py` - MCP tool call testing
- `test_workflow_mcp.py` - Workflow + MCP integration

### Workflow Tests
- `test_workflows.py` - Workflow engine tests

### Phase Tests (Progressive Implementation)
- `test_regression_fase1.py` - Phase 1 regression tests
- `test_fase4_logging.py` - Phase 4: Logging tests
- `test_fase5_hitl.py` - Phase 5: Human-in-the-loop tests
- `test_fase6_advanced_reasoning.py` - Phase 6: Advanced reasoning tests

### System Tests
- `test_system.py` - System-level integration tests

## Running Tests

### Individual Test
```bash
source .venv/bin/activate
python tests/test_direct_mcp.py
```

### Complex Scenarios (Multi-Agent)
```bash
source .venv/bin/activate
python tests/test_complex_scenarios.py
```

### All Tests
```bash
source .venv/bin/activate
pytest tests/
```

## Test Results

Test results and logs are stored in this directory:
- `*.log` files contain test execution logs
- Results are also logged to `logs/supervisor.log`

## Documentation

For detailed test results, see:
- `/projects/database_query/TEST_SUCCESS.md` - MCP tool success
- `/projects/database_query/COMPLEX_TEST_RESULTS.md` - Multi-agent test analysis
- `/projects/database_query/TEST_RESULTS.md` - Initial test findings
