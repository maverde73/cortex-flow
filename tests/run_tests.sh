#!/bin/bash

# Test Runner for Cortex Flow
# Runs pytest with various configurations

set -e

echo "🧪 Cortex Flow Test Runner"
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Parse command line arguments
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

# Function to run specific test suite
run_test_suite() {
    local suite=$1
    local markers=$2
    local description=$3

    echo "📋 Running $description..."
    echo ""

    if [ "$VERBOSE" == "-v" ] || [ "$VERBOSE" == "--verbose" ]; then
        pytest tests/$suite -m "$markers" -v --tb=short
    else
        pytest tests/$suite -m "$markers" --tb=short
    fi

    echo ""
}

# Main test execution
case $TEST_TYPE in
    "unit")
        echo "Running unit tests only (no external dependencies)..."
        echo ""
        pytest tests/ -m "unit" ${VERBOSE} --tb=short
        ;;

    "integration")
        echo "Running integration tests (requires running servers)..."
        echo ""
        echo "⚠️  Make sure all agents are running: ./scripts/start_all.sh"
        echo ""
        sleep 2
        pytest tests/ -m "integration" ${VERBOSE} --tb=short
        ;;

    "regression")
        echo "Running regression tests (FASE 1 backward compatibility)..."
        echo ""
        run_test_suite "test_regression_fase1.py" "regression" "FASE 1 Regression Tests"
        ;;

    "fase1")
        echo "Running FASE 1 tests only..."
        echo ""
        pytest tests/ -m "fase1" ${VERBOSE} --tb=short
        ;;

    "fase2")
        echo "Running FASE 2 tests only..."
        echo ""
        pytest tests/ -m "fase2" ${VERBOSE} --tb=short
        ;;

    "quick")
        echo "Running quick unit tests (FASE 2 strategies)..."
        echo ""
        run_test_suite "test_fase2_strategies.py" "unit" "FASE 2 Unit Tests"
        ;;

    "all")
        echo "Running all tests..."
        echo ""

        # Run unit tests first (fast)
        echo "==============================================================================="
        echo "PHASE 1: Unit Tests (no external dependencies)"
        echo "==============================================================================="
        pytest tests/ -m "unit" ${VERBOSE} --tb=short

        echo ""
        echo "==============================================================================="
        echo "PHASE 2: Regression Tests (FASE 1 backward compatibility)"
        echo "==============================================================================="
        pytest tests/test_regression_fase1.py -m "regression and unit" ${VERBOSE} --tb=short

        echo ""
        echo "==============================================================================="
        echo "PHASE 3: Integration Tests (requires running servers)"
        echo "==============================================================================="
        echo "⚠️  Integration tests require running servers"
        echo "   Run: ./scripts/start_all.sh"
        echo ""
        read -p "Do you want to run integration tests? (y/N) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pytest tests/ -m "integration" ${VERBOSE} --tb=short
        else
            echo "Skipping integration tests"
        fi
        ;;

    "coverage")
        echo "Running tests with coverage report..."
        echo ""
        pytest tests/ --cov=agents --cov=utils --cov=schemas --cov=tools --cov=services \
            --cov-report=term-missing --cov-report=html ${VERBOSE}
        echo ""
        echo "📊 Coverage report generated in htmlcov/index.html"
        ;;

    "help"|"-h"|"--help")
        echo "Usage: $0 [test_type] [verbose]"
        echo ""
        echo "Test Types:"
        echo "  all          - Run all tests (unit + regression + integration with prompt)"
        echo "  unit         - Run only unit tests (fast, no external dependencies)"
        echo "  integration  - Run only integration tests (requires running servers)"
        echo "  regression   - Run only regression tests (FASE 1 backward compatibility)"
        echo "  fase1        - Run only FASE 1 tests"
        echo "  fase2        - Run only FASE 2 tests"
        echo "  quick        - Run quick unit tests (FASE 2 strategies)"
        echo "  coverage     - Run tests with coverage report"
        echo "  help         - Show this help message"
        echo ""
        echo "Verbose Options:"
        echo "  -v, --verbose  - Show verbose test output"
        echo ""
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  $0 unit              # Run unit tests only"
        echo "  $0 unit -v           # Run unit tests with verbose output"
        echo "  $0 integration       # Run integration tests"
        echo "  $0 regression        # Run regression tests"
        echo "  $0 quick             # Run quick FASE 2 unit tests"
        echo "  $0 coverage          # Generate coverage report"
        exit 0
        ;;

    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

echo ""
echo "✅ Test execution completed"
