#!/bin/bash

# AI Share Platform Test Runner
# Generated: 2024-01-16 15:30:00
# Runs comprehensive test suite for all platform features

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
TEST_DIR="tests"
RESULTS_DIR="test_results"
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo -e "${BLUE}🧪 AI Share Platform Test Suite Runner${NC}"
echo -e "${BLUE}📅 Timestamp: $TIMESTAMP${NC}"
echo "=================================================="

# Create results directory
mkdir -p $RESULTS_DIR

# Function to check if server is running
check_server() {
    local url=$1
    local name=$2
    
    echo -e "${YELLOW}🔍 Checking $name server at $url...${NC}"
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name server is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name server is not running${NC}"
        return 1
    fi
}

# Function to run Python test
run_python_test() {
    local test_file=$1
    local test_name=$2
    
    echo -e "${BLUE}🏃 Running $test_name...${NC}"
    
    if python3 "$test_file"; then
        echo -e "${GREEN}✅ $test_name passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        return 1
    fi
}

# Function to run specific test category
run_test_category() {
    local category=$1
    shift
    local tests=("$@")
    
    echo -e "\n${BLUE}🎯 Running $category Tests${NC}"
    echo "----------------------------------------"
    
    local passed=0
    local total=${#tests[@]}
    
    for test in "${tests[@]}"; do
        if [ -f "$test" ]; then
            if run_python_test "$test" "$(basename "$test" .py)"; then
                ((passed++))
            fi
        else
            echo -e "${YELLOW}⚠️ Test file not found: $test${NC}"
        fi
    done
    
    echo -e "\n${BLUE}📊 $category Results: $passed/$total passed${NC}"
    return $((total - passed))
}

# Main test execution
main() {
    echo -e "${BLUE}🔧 Pre-flight checks...${NC}"
    
    # Check if test directory exists
    if [ ! -d "$TEST_DIR" ]; then
        echo -e "${RED}❌ Test directory not found: $TEST_DIR${NC}"
        exit 1
    fi
    
    # Check servers
    backend_running=true
    frontend_running=true
    
    if ! check_server "$BACKEND_URL" "Backend"; then
        backend_running=false
    fi
    
    if ! check_server "$FRONTEND_URL" "Frontend"; then
        frontend_running=false
    fi
    
    if [ "$backend_running" = false ] || [ "$frontend_running" = false ]; then
        echo -e "${YELLOW}⚠️ Some servers are not running. Some tests may fail.${NC}"
        echo -e "${YELLOW}💡 Start servers with: ./start-dev.sh${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    echo -e "\n${GREEN}🚀 Starting test execution...${NC}"
    
    # Define test categories
    declare -a unit_tests=(
        "$TEST_DIR/test_auth.py"
        "$TEST_DIR/test_organizations.py"
        "$TEST_DIR/test_datasets.py"
        "$TEST_DIR/test_models.py"
    )
    
    declare -a integration_tests=(
        "$TEST_DIR/integration_test_${TIMESTAMP:0:8}.py"
        "$TEST_DIR/test_suite_${TIMESTAMP}.py"
    )
    
    declare -a api_tests=(
        "$TEST_DIR/test_api_endpoints.py"
        "$TEST_DIR/test_authentication.py"
    )
    
    # Initialize counters
    total_passed=0
    total_failed=0
    
    # Run test categories
    echo -e "\n${BLUE}📋 Test Execution Plan:${NC}"
    echo "  1. Unit Tests"
    echo "  2. Integration Tests" 
    echo "  3. API Tests"
    echo "  4. Performance Tests"
    
    # Unit Tests
    if run_test_category "Unit" "${unit_tests[@]}"; then
        echo -e "${GREEN}✅ Unit tests passed${NC}"
    else
        echo -e "${RED}❌ Some unit tests failed${NC}"
        ((total_failed++))
    fi
    
    # Integration Tests
    if run_test_category "Integration" "${integration_tests[@]}"; then
        echo -e "${GREEN}✅ Integration tests passed${NC}"
    else
        echo -e "${RED}❌ Some integration tests failed${NC}"
        ((total_failed++))
    fi
    
    # API Tests
    if run_test_category "API" "${api_tests[@]}"; then
        echo -e "${GREEN}✅ API tests passed${NC}"
    else
        echo -e "${RED}❌ Some API tests failed${NC}"
        ((total_failed++))
    fi
    
    # Generate summary report
    echo -e "\n${BLUE}📊 Generating test report...${NC}"
    
    report_file="$RESULTS_DIR/test_summary_$TIMESTAMP.txt"
    
    cat > "$report_file" << EOF
=== AI SHARE PLATFORM TEST SUMMARY ===
Generated: $(date)
Timestamp: $TIMESTAMP

=== ENVIRONMENT ===
Backend URL: $BACKEND_URL
Frontend URL: $FRONTEND_URL
Backend Running: $backend_running
Frontend Running: $frontend_running

=== RESULTS SUMMARY ===
Total Test Categories: 3
Passed Categories: $((3 - total_failed))
Failed Categories: $total_failed

=== DETAILED RESULTS ===
Unit Tests: $([ ${#unit_tests[@]} -gt 0 ] && echo "Executed" || echo "No tests found")
Integration Tests: $([ ${#integration_tests[@]} -gt 0 ] && echo "Executed" || echo "No tests found")
API Tests: $([ ${#api_tests[@]} -gt 0 ] && echo "Executed" || echo "No tests found")

=== RECOMMENDATIONS ===
EOF
    
    if [ $total_failed -eq 0 ]; then
        echo "✅ All test categories passed successfully!" >> "$report_file"
        echo "🚀 Platform is ready for deployment." >> "$report_file"
    else
        echo "⚠️ $total_failed test categories failed." >> "$report_file"
        echo "🔧 Review failed tests before deployment." >> "$report_file"
    fi
    
    echo -e "${GREEN}📄 Test report saved to: $report_file${NC}"
    
    # Final summary
    echo -e "\n${'='*50}"
    echo -e "${BLUE}🏁 Test Suite Completed${NC}"
    echo -e "${BLUE}⏱️  Total Duration: $((SECONDS/60))m $((SECONDS%60))s${NC}"
    
    if [ $total_failed -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        echo -e "${GREEN}✅ Platform is ready for production${NC}"
        exit 0
    else
        echo -e "${RED}💥 $total_failed test categories failed${NC}"
        echo -e "${YELLOW}🔧 Check the test report for details${NC}"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up test artifacts...${NC}"
    # Remove temporary test files if any
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main "$@" 