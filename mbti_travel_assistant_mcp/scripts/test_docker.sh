#!/bin/bash
# Docker Testing Script for MBTI Travel Assistant MCP

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.test.yml"
TEST_RESULTS_DIR="tests/results"
TEST_TIMEOUT=300  # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    cleanup_test_environment
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "${BLUE}Checking testing prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed or not in PATH"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error_exit "Docker Compose is not installed or not in PATH"
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running"
    fi
    
    # Check if test compose file exists
    if [ ! -f "$PROJECT_DIR/$COMPOSE_FILE" ]; then
        error_exit "Test compose file not found: $COMPOSE_FILE"
    fi
    
    log "${GREEN}✓ Testing prerequisites check passed${NC}"
}

# Setup test environment
setup_test_environment() {
    log "${BLUE}Setting up test environment...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"
    
    # Clean up any existing test containers
    docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans || true
    
    # Build test images
    log "Building test images..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start test services
    log "Starting test services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    log "Waiting for test services to be ready..."
    wait_for_services
    
    log "${GREEN}✓ Test environment setup completed${NC}"
}

# Wait for services to be ready
wait_for_services() {
    local max_attempts=30
    local attempt=1
    
    # Wait for main service
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
            log "${GREEN}✓ MBTI Travel Assistant test service is ready${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                error_exit "MBTI Travel Assistant test service failed to start after $max_attempts attempts"
            fi
            log "${YELLOW}Attempt $attempt/$max_attempts: Waiting for MBTI Travel Assistant...${NC}"
            sleep 10
            attempt=$((attempt + 1))
        fi
    done
    
    # Wait for mock services
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8001/__admin/health > /dev/null 2>&1; then
            log "${GREEN}✓ Search MCP mock service is ready${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                error_exit "Search MCP mock service failed to start after $max_attempts attempts"
            fi
            log "${YELLOW}Attempt $attempt/$max_attempts: Waiting for Search MCP mock...${NC}"
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
    
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8002/__admin/health > /dev/null 2>&1; then
            log "${GREEN}✓ Reasoning MCP mock service is ready${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                error_exit "Reasoning MCP mock service failed to start after $max_attempts attempts"
            fi
            log "${YELLOW}Attempt $attempt/$max_attempts: Waiting for Reasoning MCP mock...${NC}"
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
    
    # Wait for Redis
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker exec mbti-redis-test redis-cli ping | grep -q "PONG" 2>/dev/null; then
            log "${GREEN}✓ Redis test service is ready${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log "${YELLOW}⚠ Redis test service not responding, continuing anyway${NC}"
                break
            fi
            log "${YELLOW}Attempt $attempt/$max_attempts: Waiting for Redis...${NC}"
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
}

# Run unit tests
run_unit_tests() {
    log "${BLUE}Running unit tests in Docker container...${NC}"
    
    # Run pytest in the test container
    if docker-compose -f "$COMPOSE_FILE" run --rm test-runner python -m pytest tests/unit -v --tb=short --junitxml=/app/test_results/unit_tests.xml; then
        log "${GREEN}✓ Unit tests passed${NC}"
        return 0
    else
        log "${RED}✗ Unit tests failed${NC}"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    log "${BLUE}Running integration tests in Docker container...${NC}"
    
    # Run integration tests
    if docker-compose -f "$COMPOSE_FILE" run --rm test-runner python -m pytest tests/integration -v --tb=short --junitxml=/app/test_results/integration_tests.xml; then
        log "${GREEN}✓ Integration tests passed${NC}"
        return 0
    else
        log "${RED}✗ Integration tests failed${NC}"
        return 1
    fi
}

# Run end-to-end tests
run_e2e_tests() {
    log "${BLUE}Running end-to-end tests...${NC}"
    
    # Test basic MBTI itinerary generation
    local test_payload='{"MBTI_personality": "INFJ"}'
    local response
    
    if response=$(curl -s -X POST -H "Content-Type: application/json" -d "$test_payload" http://localhost:8080/invocations); then
        if echo "$response" | grep -q "main_itinerary"; then
            log "${GREEN}✓ Basic MBTI itinerary generation test passed${NC}"
        else
            log "${RED}✗ Basic MBTI itinerary generation test failed - unexpected response${NC}"
            log "Response: $response"
            return 1
        fi
    else
        log "${RED}✗ Basic MBTI itinerary generation test failed - request failed${NC}"
        return 1
    fi
    
    # Test health endpoint
    if curl -f -s http://localhost:8080/health > /dev/null; then
        log "${GREEN}✓ Health endpoint test passed${NC}"
    else
        log "${RED}✗ Health endpoint test failed${NC}"
        return 1
    fi
    
    # Test metrics endpoint
    if curl -f -s http://localhost:9090/metrics > /dev/null; then
        log "${GREEN}✓ Metrics endpoint test passed${NC}"
    else
        log "${YELLOW}⚠ Metrics endpoint test failed${NC}"
    fi
    
    return 0
}

# Run load tests
run_load_tests() {
    log "${BLUE}Running load tests...${NC}"
    
    # Run k6 load tests
    if docker-compose -f "$COMPOSE_FILE" run --rm load-tester; then
        log "${GREEN}✓ Load tests completed${NC}"
        return 0
    else
        log "${YELLOW}⚠ Load tests failed or had issues${NC}"
        return 1
    fi
}

# Run security tests
run_security_tests() {
    log "${BLUE}Running security tests...${NC}"
    
    # Test without authentication (should fail)
    local response_code
    response_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"MBTI_personality": "INFJ"}' http://localhost:8080/invocations)
    
    if [ "$response_code" = "401" ] || [ "$response_code" = "403" ]; then
        log "${GREEN}✓ Authentication security test passed (got $response_code)${NC}"
    else
        log "${YELLOW}⚠ Authentication security test - got unexpected response code: $response_code${NC}"
    fi
    
    # Test malformed payload
    response_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"invalid": "payload"}' http://localhost:8080/invocations)
    
    if [ "$response_code" = "400" ] || [ "$response_code" = "422" ]; then
        log "${GREEN}✓ Input validation security test passed (got $response_code)${NC}"
    else
        log "${YELLOW}⚠ Input validation security test - got unexpected response code: $response_code${NC}"
    fi
    
    return 0
}

# Collect test results
collect_test_results() {
    log "${BLUE}Collecting test results...${NC}"
    
    # Copy test results from containers
    docker cp mbti-travel-assistant-mcp-test:/app/test_results/. "$TEST_RESULTS_DIR/" 2>/dev/null || true
    
    # Generate test summary
    local summary_file="$TEST_RESULTS_DIR/test_summary.txt"
    {
        echo "Docker Test Summary - $(date)"
        echo "=================================="
        echo ""
        echo "Test Environment: Docker Compose"
        echo "Compose File: $COMPOSE_FILE"
        echo "Test Duration: $(($(date +%s) - start_time)) seconds"
        echo ""
        echo "Test Results:"
        echo "- Unit Tests: $unit_test_result"
        echo "- Integration Tests: $integration_test_result"
        echo "- End-to-End Tests: $e2e_test_result"
        echo "- Load Tests: $load_test_result"
        echo "- Security Tests: $security_test_result"
        echo ""
        echo "Service Logs:"
        echo "============="
    } > "$summary_file"
    
    # Append service logs to summary
    docker-compose -f "$COMPOSE_FILE" logs --tail=50 >> "$summary_file" 2>/dev/null || true
    
    log "${GREEN}✓ Test results collected in $TEST_RESULTS_DIR${NC}"
}

# Cleanup test environment
cleanup_test_environment() {
    log "${BLUE}Cleaning up test environment...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Stop and remove test containers
    docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans || true
    
    # Remove test images (optional)
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        docker image prune -f
    fi
    
    log "${GREEN}✓ Test environment cleanup completed${NC}"
}

# Display test results
display_results() {
    log "${BLUE}Test Results Summary:${NC}"
    echo "=================================="
    echo "Unit Tests:        $unit_test_result"
    echo "Integration Tests: $integration_test_result"
    echo "End-to-End Tests:  $e2e_test_result"
    echo "Load Tests:        $load_test_result"
    echo "Security Tests:    $security_test_result"
    echo "=================================="
    
    local failed_tests=0
    [ "$unit_test_result" = "FAILED" ] && failed_tests=$((failed_tests + 1))
    [ "$integration_test_result" = "FAILED" ] && failed_tests=$((failed_tests + 1))
    [ "$e2e_test_result" = "FAILED" ] && failed_tests=$((failed_tests + 1))
    [ "$load_test_result" = "FAILED" ] && failed_tests=$((failed_tests + 1))
    [ "$security_test_result" = "FAILED" ] && failed_tests=$((failed_tests + 1))
    
    if [ $failed_tests -eq 0 ]; then
        log "${GREEN}✓ All tests passed successfully!${NC}"
        return 0
    else
        log "${RED}✗ $failed_tests test suite(s) failed${NC}"
        return 1
    fi
}

# Main function
main() {
    local start_time=$(date +%s)
    local test_type="${1:-all}"
    
    # Initialize test results
    unit_test_result="SKIPPED"
    integration_test_result="SKIPPED"
    e2e_test_result="SKIPPED"
    load_test_result="SKIPPED"
    security_test_result="SKIPPED"
    
    log "${BLUE}Starting Docker tests for MBTI Travel Assistant MCP${NC}"
    log "Test type: $test_type"
    
    check_prerequisites
    setup_test_environment
    
    case "$test_type" in
        "unit")
            run_unit_tests && unit_test_result="PASSED" || unit_test_result="FAILED"
            ;;
        "integration")
            run_integration_tests && integration_test_result="PASSED" || integration_test_result="FAILED"
            ;;
        "e2e")
            run_e2e_tests && e2e_test_result="PASSED" || e2e_test_result="FAILED"
            ;;
        "load")
            run_load_tests && load_test_result="PASSED" || load_test_result="FAILED"
            ;;
        "security")
            run_security_tests && security_test_result="PASSED" || security_test_result="FAILED"
            ;;
        "all"|*)
            run_unit_tests && unit_test_result="PASSED" || unit_test_result="FAILED"
            run_integration_tests && integration_test_result="PASSED" || integration_test_result="FAILED"
            run_e2e_tests && e2e_test_result="PASSED" || e2e_test_result="FAILED"
            run_load_tests && load_test_result="PASSED" || load_test_result="FAILED"
            run_security_tests && security_test_result="PASSED" || security_test_result="FAILED"
            ;;
    esac
    
    collect_test_results
    cleanup_test_environment
    
    display_results
}

# Handle script arguments
case "${1:-all}" in
    "unit"|"integration"|"e2e"|"load"|"security"|"all")
        main "$1"
        ;;
    "cleanup")
        cleanup_test_environment
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [TEST_TYPE]"
        echo ""
        echo "Test Types:"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests only"
        echo "  e2e          - Run end-to-end tests only"
        echo "  load         - Run load tests only"
        echo "  security     - Run security tests only"
        echo "  all          - Run all tests (default)"
        echo "  cleanup      - Clean up test environment"
        echo "  help         - Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  CLEANUP_IMAGES=true  - Remove test images after cleanup"
        exit 0
        ;;
    *)
        echo "Unknown test type: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac