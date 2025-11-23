#!/bin/bash
#
# Audio Testing Runner Script
#
# Runs comprehensive audio tests for the RTSTT system including:
# - Unit tests for audio components
# - Integration tests for audio pipeline
# - Performance benchmarks
# - Coverage reporting
#
# Usage:
#   ./scripts/run_audio_tests.sh [OPTIONS]
#
# Options:
#   --unit          Run only unit tests
#   --integration   Run only integration tests
#   --performance   Run only performance tests
#   --all           Run all tests (default)
#   --coverage      Generate coverage report
#   --verbose       Verbose output
#   --quick         Skip slow tests
#   --help          Show this help message
#
# Author: ORCHIDEA Agent System
# Created: 2025-11-23

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_PERFORMANCE=false
RUN_ALL=true
GENERATE_COVERAGE=false
VERBOSE=false
SKIP_SLOW=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        --performance)
            RUN_PERFORMANCE=true
            RUN_ALL=false
            shift
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --quick)
            SKIP_SLOW=true
            shift
            ;;
        --help)
            head -n 25 "$0" | grep "^#" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set pytest options
PYTEST_OPTS="-v"

if [ "$VERBOSE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -vv"
fi

if [ "$SKIP_SLOW" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -m 'not slow'"
fi

if [ "$GENERATE_COVERAGE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS --cov=src/core/audio_capture --cov-report=html --cov-report=term"
fi

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}RTSTT Audio Testing Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-asyncio pytest-cov"
    exit 1
fi

# Check if numpy is installed (required for audio tests)
if ! python3 -c "import numpy" 2>/dev/null; then
    echo -e "${YELLOW}Warning: numpy is not installed${NC}"
    echo "Some audio tests may be skipped"
    echo "Install with: pip install numpy"
    echo ""
fi

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2
    local marker=$3

    echo -e "${GREEN}Running $test_name...${NC}"

    if [ -n "$marker" ]; then
        pytest $PYTEST_OPTS -m "$marker" $test_path
    else
        pytest $PYTEST_OPTS $test_path
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        return 1
    fi
    echo ""
}

# Run tests based on options
if [ "$RUN_ALL" = true ]; then
    echo -e "${BLUE}Running all audio tests...${NC}"
    echo ""

    # Run unit tests
    run_tests "tests/unit/test_audio_format.py" "Audio Format Tests" || true
    run_tests "tests/unit/test_circular_buffer.py" "Circular Buffer Tests" || true
    run_tests "tests/unit/test_vad.py" "VAD Tests" || true
    run_tests "tests/unit/test_wasapi_capture.py" "WASAPI Capture Tests" || true

    # Run integration tests
    run_tests "tests/integration/test_audio_service.py" "Audio Service Tests" || true
    run_tests "tests/integration/test_websocket_audio_stream.py" "WebSocket Streaming Tests" || true
    run_tests "tests/integration/test_audio_pipeline_e2e.py" "E2E Pipeline Tests" || true

    # Run performance tests (if not skipping slow tests)
    if [ "$SKIP_SLOW" = false ]; then
        run_tests "tests/performance/test_audio_latency.py" "Latency Benchmarks" || true
        run_tests "tests/performance/test_throughput.py" "Throughput Tests" || true
    fi

elif [ "$RUN_UNIT" = true ]; then
    echo -e "${BLUE}Running unit tests...${NC}"
    echo ""
    run_tests "tests/unit/" "Unit Tests" "unit"

elif [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${BLUE}Running integration tests...${NC}"
    echo ""
    run_tests "tests/integration/" "Integration Tests" "integration"

elif [ "$RUN_PERFORMANCE" = true ]; then
    echo -e "${BLUE}Running performance tests...${NC}"
    echo ""
    run_tests "tests/performance/" "Performance Tests" "performance"
fi

# Generate coverage report
if [ "$GENERATE_COVERAGE" = true ]; then
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}Coverage Report${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""

    if [ -f "htmlcov/index.html" ]; then
        echo -e "${GREEN}HTML coverage report generated: htmlcov/index.html${NC}"
    fi

    if [ -f "coverage.xml" ]; then
        echo -e "${GREEN}XML coverage report generated: coverage.xml${NC}"
    fi
fi

# Print summary
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Test Suite Complete${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${GREEN}All specified tests have been executed.${NC}"
echo ""

# Print next steps
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review test results above"
echo "  2. Check coverage report (if generated)"
echo "  3. Fix any failing tests"
echo "  4. Run performance benchmarks regularly"
echo ""

# Print useful commands
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  Run specific test file:"
echo "    pytest tests/unit/test_vad.py -v"
echo ""
echo "  Run tests with marker:"
echo "    pytest -m audio -v"
echo ""
echo "  Run tests and show coverage:"
echo "    pytest --cov=src/core/audio_capture --cov-report=html"
echo ""
echo "  Run only fast tests:"
echo "    pytest -m 'not slow' -v"
echo ""
