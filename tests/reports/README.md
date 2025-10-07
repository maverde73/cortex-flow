# Test Reports

This directory contains test reports and regression test results.

## Available Reports

### [LangGraph Regression Test Report](LANGGRAPH_REGRESSION_TEST_REPORT.md)
Comprehensive regression test report for LangGraph v0.4.0 compatibility:
- 292 total tests executed
- 19/19 LangGraph compiler tests ✅
- 34/37 workflow system tests (3 skipped) ✅
- 14/14 DSL roundtrip tests ✅
- Backward compatibility verification
- Performance analysis

**Status**: All critical tests passing

## Test Coverage

- **Unit Tests**: Token counting, checkpointer initialization
- **Integration Tests**: Conversation memory, message trimming
- **Regression Tests**: LangGraph compilation compatibility
- **System Tests**: Workflow execution, agent coordination

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_conversation_memory.py -v

# With coverage
pytest --cov=. --cov-report=html
```

## Report Format

Test reports follow this structure:
- Executive Summary
- Test Results by Category
- Detailed Findings
- Performance Metrics
- Sign-off and Recommendations

---

**Last Updated**: 2025-10-07
