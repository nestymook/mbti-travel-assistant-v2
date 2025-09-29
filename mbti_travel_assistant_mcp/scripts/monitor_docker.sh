#!/bin/bash
# Docker Monitoring Script for MBTI Travel Assistant MCP
# This script monitors Docker containers and services health

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_FILE_PROD="docker-compose.prod.yml"
MONITORING_INTERVAL=30
LOG_FILE="/var/log/mbti-docker-monitor.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$message"
    echo "$message" >> "$LOG_FILE" 2>/dev/null || true
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Check if running as daemon
DAEMON_MODE=false
if [ "$1" = "--daemon" ] || [ "$1" = "-d" ]; then
    DAEMON_MODE=true
    shift
fi

# Environment detection
ENVIRONMENT="${1:-development}"
if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="$COMPOSE_FILE_PROD"
fi

# Check prerequisites
check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed or not in PATH"
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error_exit "Docker Compose is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running"
    fi
}

# Get container status
get_container_status() {
    local container_name="$1"
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo "running"
    elif docker ps -a --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo "stopped"
    else
        echo "not_found"
    fi
}

# Check container health
check_container_health() {
    local container_name="$1"
    local health_status
    
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no_health_check")
    
    case "$health_status" in
        "healthy")
            echo "healthy"
            ;;
        "unhealthy")
            echo "unhealthy"
            ;;
        "starting")
            echo "starting"
            ;;
        "no_health_check")
            # Check if container is running
            if [ "$(get_container_status "$container_name")" = "running" ]; then
                echo "running_no_health_check"
            else
                echo "not_running"
            fi
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Check service endpoint
check_service_endpoint() {
    local url="$1"
    local timeout="${2:-10}"
    
    if curl -f -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Monitor main application
monitor_main_application() {
    local container_name="mbti-travel-assistant-mcp"
    if [ "$ENVIRONMENT" = "production" ]; then
        container_name="mbti-travel-assistant-mcp-prod"
    fi
    
    local status=$(get_container_status "$container_name")
    local health=$(check_container_health "$container_name")
    
    log "${BLUE}Main Application Status:${NC}"
    log "  Container: $status"
    log "  Health: $health"
    
    if [ "$status" = "running" ]; then
        # Check HTTP endpoints
        if check_service_endpoint "http://localhost:8080/health"; then
            log "  ${GREEN}✓ Health endpoint responding${NC}"
        else
            log "  ${RED}✗ Health endpoint not responding${NC}"
            return 1
        fi
        
        if check_service_endpoint "http://localhost:9090/metrics"; then
            log "  ${GREEN}✓ Metrics endpoint responding${NC}"
        else
            log "  ${YELLOW}⚠ Metrics endpoint not responding${NC}"
        fi
        
        # Check resource usage
        local cpu_usage=$(docker stats --no-stream --format "table {{.CPUPerc}}" "$container_name" | tail -n 1 | sed 's/%//')
        local mem_usage=$(docker stats --no-stream --format "table {{.MemPerc}}" "$container_name" | tail -n 1 | sed 's/%//')
        
        log "  CPU Usage: ${cpu_usage}%"
        log "  Memory Usage: ${mem_usage}%"
        
        # Alert on high resource usage
        if (( $(echo "$cpu_usage > 80" | bc -l) )); then
            log "  ${YELLOW}⚠ High CPU usage: ${cpu_usage}%${NC}"
        fi
        
        if (( $(echo "$mem_usage > 80" | bc -l) )); then
            log "  ${YELLOW}⚠ High memory usage: ${mem_usage}%${NC}"
        fi
    else
        log "  ${RED}✗ Container not running${NC}"
        return 1
    fi
    
    return 0
}

# Monitor Redis
monitor_redis() {
    local container_name="mbti-redis"
    if [ "$ENVIRONMENT" = "production" ]; then
        container_name="mbti-redis-prod"
    fi
    
    local status=$(get_container_status "$container_name")
    local health=$(check_container_health "$container_name")
    
    log "${BLUE}Redis Status:${NC}"
    log "  Container: $status"
    log "  Health: $health"
    
    if [ "$status" = "running" ]; then
        # Check Redis connectivity
        if docker exec "$container_name" redis-cli ping | grep -q "PONG" 2>/dev/null; then
            log "  ${GREEN}✓ Redis responding to ping${NC}"
        else
            log "  ${RED}✗ Redis not responding to ping${NC}"
            return 1
        fi
        
        # Check Redis info
        local connected_clients=$(docker exec "$container_name" redis-cli info clients | grep "connected_clients:" | cut -d: -f2 | tr -d '\r')
        local used_memory=$(docker exec "$container_name" redis-cli info memory | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
        
        log "  Connected Clients: $connected_clients"
        log "  Used Memory: $used_memory"
    else
        log "  ${RED}✗ Container not running${NC}"
        return 1
    fi
    
    return 0
}

# Monitor Prometheus
monitor_prometheus() {
    local container_name="mbti-prometheus"
    if [ "$ENVIRONMENT" = "production" ]; then
        container_name="mbti-prometheus-prod"
    fi
    
    local status=$(get_container_status "$container_name")
    
    log "${BLUE}Prometheus Status:${NC}"
    log "  Container: $status"
    
    if [ "$status" = "running" ]; then
        # Check Prometheus endpoint
        if check_service_endpoint "http://localhost:9091/-/healthy"; then
            log "  ${GREEN}✓ Prometheus healthy${NC}"
        else
            log "  ${YELLOW}⚠ Prometheus health check failed${NC}"
        fi
        
        # Check targets
        if check_service_endpoint "http://localhost:9091/api/v1/targets"; then
            log "  ${GREEN}✓ Prometheus API responding${NC}"
        else
            log "  ${YELLOW}⚠ Prometheus API not responding${NC}"
        fi
    else
        log "  ${YELLOW}⚠ Container not running${NC}"
    fi
}

# Monitor Grafana
monitor_grafana() {
    local container_name="mbti-grafana"
    
    local status=$(get_container_status "$container_name")
    
    log "${BLUE}Grafana Status:${NC}"
    log "  Container: $status"
    
    if [ "$status" = "running" ]; then
        # Check Grafana endpoint
        if check_service_endpoint "http://localhost:3000/api/health"; then
            log "  ${GREEN}✓ Grafana healthy${NC}"
        else
            log "  ${YELLOW}⚠ Grafana health check failed${NC}"
        fi
    else
        log "  ${YELLOW}⚠ Container not running${NC}"
    fi
}

# Monitor Nginx (production only)
monitor_nginx() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return 0
    fi
    
    local container_name="mbti-nginx-prod"
    local status=$(get_container_status "$container_name")
    
    log "${BLUE}Nginx Status:${NC}"
    log "  Container: $status"
    
    if [ "$status" = "running" ]; then
        # Check Nginx health
        if check_service_endpoint "http://localhost/health"; then
            log "  ${GREEN}✓ Nginx healthy${NC}"
        else
            log "  ${RED}✗ Nginx health check failed${NC}"
            return 1
        fi
    else
        log "  ${RED}✗ Container not running${NC}"
        return 1
    fi
    
    return 0
}

# Check Docker system health
check_docker_system() {
    log "${BLUE}Docker System Status:${NC}"
    
    # Check Docker daemon
    if docker info > /dev/null 2>&1; then
        log "  ${GREEN}✓ Docker daemon healthy${NC}"
    else
        log "  ${RED}✗ Docker daemon issues${NC}"
        return 1
    fi
    
    # Check disk space
    local disk_usage=$(df /var/lib/docker | tail -1 | awk '{print $5}' | sed 's/%//')
    log "  Docker disk usage: ${disk_usage}%"
    
    if [ "$disk_usage" -gt 80 ]; then
        log "  ${YELLOW}⚠ High Docker disk usage: ${disk_usage}%${NC}"
    fi
    
    # Check for dead containers
    local dead_containers=$(docker ps -a --filter "status=dead" --format "table {{.Names}}" | wc -l)
    if [ "$dead_containers" -gt 1 ]; then  # Subtract 1 for header
        log "  ${YELLOW}⚠ Found $((dead_containers - 1)) dead containers${NC}"
    fi
    
    return 0
}

# Generate monitoring report
generate_report() {
    local report_file="/tmp/mbti-docker-monitor-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "MBTI Travel Assistant Docker Monitoring Report"
        echo "=============================================="
        echo "Generated: $(date)"
        echo "Environment: $ENVIRONMENT"
        echo ""
        
        echo "Container Status:"
        echo "----------------"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        echo "Resource Usage:"
        echo "--------------"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
        echo ""
        
        echo "Recent Logs (last 50 lines):"
        echo "----------------------------"
        if [ "$ENVIRONMENT" = "production" ]; then
            docker-compose -f "$COMPOSE_FILE" logs --tail=50
        else
            docker-compose -f "$COMPOSE_FILE" logs --tail=50
        fi
        
    } > "$report_file"
    
    log "Monitoring report generated: $report_file"
    echo "$report_file"
}

# Restart unhealthy services
restart_unhealthy_services() {
    log "${BLUE}Checking for unhealthy services to restart...${NC}"
    
    local restart_needed=false
    
    # Check main application
    if ! monitor_main_application > /dev/null 2>&1; then
        log "${YELLOW}Main application unhealthy, marking for restart${NC}"
        restart_needed=true
    fi
    
    # Check Redis
    if ! monitor_redis > /dev/null 2>&1; then
        log "${YELLOW}Redis unhealthy, marking for restart${NC}"
        restart_needed=true
    fi
    
    if [ "$restart_needed" = true ]; then
        log "${YELLOW}Restarting unhealthy services...${NC}"
        cd "$PROJECT_DIR"
        
        if [ "$ENVIRONMENT" = "production" ]; then
            docker-compose -f "$COMPOSE_FILE" restart
        else
            docker-compose -f "$COMPOSE_FILE" restart
        fi
        
        log "${GREEN}Services restarted${NC}"
        
        # Wait for services to stabilize
        sleep 60
        
        # Re-check health
        log "Re-checking service health after restart..."
        monitor_all_services
    else
        log "${GREEN}All services healthy, no restart needed${NC}"
    fi
}

# Monitor all services
monitor_all_services() {
    log "${BLUE}=== Docker Monitoring Report - $(date) ===${NC}"
    
    local overall_health=true
    
    check_docker_system || overall_health=false
    monitor_main_application || overall_health=false
    monitor_redis || overall_health=false
    monitor_prometheus
    monitor_grafana
    monitor_nginx || overall_health=false
    
    if [ "$overall_health" = true ]; then
        log "${GREEN}✓ Overall system health: HEALTHY${NC}"
    else
        log "${RED}✗ Overall system health: UNHEALTHY${NC}"
    fi
    
    log "${BLUE}=== End of Monitoring Report ===${NC}"
    echo ""
    
    return $([ "$overall_health" = true ] && echo 0 || echo 1)
}

# Daemon mode function
run_daemon() {
    log "Starting Docker monitoring daemon for environment: $ENVIRONMENT"
    log "Monitoring interval: ${MONITORING_INTERVAL}s"
    
    while true; do
        if ! monitor_all_services; then
            log "${YELLOW}Unhealthy services detected${NC}"
            
            # Auto-restart if enabled
            if [ "$AUTO_RESTART" = "true" ]; then
                restart_unhealthy_services
            fi
        fi
        
        sleep "$MONITORING_INTERVAL"
    done
}

# Main function
main() {
    check_prerequisites
    
    cd "$PROJECT_DIR"
    
    if [ "$DAEMON_MODE" = true ]; then
        run_daemon
    else
        monitor_all_services
    fi
}

# Handle script arguments
case "${1:-monitor}" in
    "monitor")
        main
        ;;
    "daemon"|"-d"|"--daemon")
        DAEMON_MODE=true
        main
        ;;
    "report")
        generate_report
        ;;
    "restart")
        restart_unhealthy_services
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [COMMAND] [ENVIRONMENT]"
        echo ""
        echo "Commands:"
        echo "  monitor    - Run monitoring once (default)"
        echo "  daemon     - Run monitoring continuously"
        echo "  report     - Generate detailed monitoring report"
        echo "  restart    - Restart unhealthy services"
        echo "  help       - Show this help message"
        echo ""
        echo "Environment:"
        echo "  development - Monitor development environment (default)"
        echo "  production  - Monitor production environment"
        echo ""
        echo "Environment Variables:"
        echo "  AUTO_RESTART=true     - Automatically restart unhealthy services in daemon mode"
        echo "  MONITORING_INTERVAL   - Monitoring interval in seconds (default: 30)"
        echo ""
        echo "Examples:"
        echo "  $0                    # Monitor once (development)"
        echo "  $0 daemon production  # Run daemon for production"
        echo "  $0 report             # Generate monitoring report"
        exit 0
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac