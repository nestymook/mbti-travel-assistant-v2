#!/bin/bash
# Docker Health Check Script for MBTI Travel Assistant MCP
# This script performs comprehensive health checks for the containerized application

set -e

# Configuration
HEALTH_ENDPOINT="http://localhost:8080/health"
TIMEOUT=10
MAX_RETRIES=3
RETRY_DELAY=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if process is running
check_process() {
    log "Checking if main process is running..."
    
    if pgrep -f "python.*main" > /dev/null; then
        log "${GREEN}✓ Main process is running${NC}"
        return 0
    else
        log "${RED}✗ Main process not found${NC}"
        return 1
    fi
}

# Check HTTP health endpoint
check_http_health() {
    log "Checking HTTP health endpoint..."
    
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if curl -f -s --max-time $TIMEOUT "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
            log "${GREEN}✓ HTTP health endpoint responding${NC}"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                log "${YELLOW}⚠ HTTP health check failed, retrying in ${RETRY_DELAY}s (attempt $retry_count/$MAX_RETRIES)${NC}"
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    log "${RED}✗ HTTP health endpoint not responding after $MAX_RETRIES attempts${NC}"
    return 1
}

# Check detailed health status
check_detailed_health() {
    log "Checking detailed health status..."
    
    local health_response
    health_response=$(curl -f -s --max-time $TIMEOUT "$HEALTH_ENDPOINT" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        # Parse JSON response to check overall status
        local overall_status
        overall_status=$(echo "$health_response" | grep -o '"overall_status":"[^"]*"' | cut -d'"' -f4)
        
        if [ "$overall_status" = "healthy" ]; then
            log "${GREEN}✓ Application health status: healthy${NC}"
            return 0
        else
            log "${YELLOW}⚠ Application health status: $overall_status${NC}"
            # Still return 0 for partial health - let the application decide
            return 0
        fi
    else
        log "${RED}✗ Failed to get detailed health status${NC}"
        return 1
    fi
}

# Check system resources
check_system_resources() {
    log "Checking system resources..."
    
    # Check memory usage
    local memory_usage
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        log "${RED}✗ High memory usage: ${memory_usage}%${NC}"
        return 1
    elif (( $(echo "$memory_usage > 80" | bc -l) )); then
        log "${YELLOW}⚠ Moderate memory usage: ${memory_usage}%${NC}"
    else
        log "${GREEN}✓ Memory usage: ${memory_usage}%${NC}"
    fi
    
    # Check disk space
    local disk_usage
    disk_usage=$(df /app | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt 90 ]; then
        log "${RED}✗ High disk usage: ${disk_usage}%${NC}"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log "${YELLOW}⚠ Moderate disk usage: ${disk_usage}%${NC}"
    else
        log "${GREEN}✓ Disk usage: ${disk_usage}%${NC}"
    fi
    
    return 0
}

# Main health check function
main() {
    log "Starting Docker health check for MBTI Travel Assistant MCP..."
    
    local exit_code=0
    
    # Perform all health checks
    check_process || exit_code=1
    check_http_health || exit_code=1
    check_detailed_health || exit_code=1
    check_system_resources || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        log "${GREEN}✓ All health checks passed${NC}"
    else
        log "${RED}✗ Some health checks failed${NC}"
    fi
    
    exit $exit_code
}

# Run main function
main "$@"