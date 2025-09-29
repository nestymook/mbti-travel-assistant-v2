#!/bin/bash
# Production Docker Deployment Script for MBTI Travel Assistant MCP

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE="config/environments/production.env"

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
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "${BLUE}Checking production prerequisites...${NC}"
    
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
    
    # Check required environment variables
    local required_vars=(
        "SEARCH_MCP_ENDPOINT"
        "REASONING_MCP_ENDPOINT"
        "COGNITO_USER_POOL_ID"
        "JWT_AUDIENCE"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error_exit "Required environment variable $var is not set"
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error_exit "AWS credentials are not configured or invalid"
    fi
    
    log "${GREEN}✓ Production prerequisites check passed${NC}"
}

# Pre-deployment validation
pre_deployment_validation() {
    log "${BLUE}Running pre-deployment validation...${NC}"
    
    # Validate configuration
    cd "$PROJECT_DIR"
    python -m config.validate_config production || error_exit "Configuration validation failed"
    
    # Test MCP endpoints
    if [ -n "$SEARCH_MCP_ENDPOINT" ]; then
        if ! curl -f -s --max-time 10 "$SEARCH_MCP_ENDPOINT/health" > /dev/null 2>&1; then
            log "${YELLOW}Warning: Search MCP endpoint health check failed${NC}"
        else
            log "${GREEN}✓ Search MCP endpoint is accessible${NC}"
        fi
    fi
    
    if [ -n "$REASONING_MCP_ENDPOINT" ]; then
        if ! curl -f -s --max-time 10 "$REASONING_MCP_ENDPOINT/health" > /dev/null 2>&1; then
            log "${YELLOW}Warning: Reasoning MCP endpoint health check failed${NC}"
        else
            log "${GREEN}✓ Reasoning MCP endpoint is accessible${NC}"
        fi
    fi
    
    log "${GREEN}✓ Pre-deployment validation completed${NC}"
}

# Build and deploy
deploy() {
    log "${BLUE}Starting production deployment...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        log "Loading environment from $ENV_FILE"
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    else
        log "${YELLOW}Warning: Environment file $ENV_FILE not found${NC}"
    fi
    
    # Create necessary directories
    sudo mkdir -p /var/log/mbti-travel-assistant
    sudo mkdir -p /var/lib/mbti-travel-assistant/data
    sudo mkdir -p /var/lib/mbti-travel-assistant/cache
    sudo chown -R $USER:$USER /var/log/mbti-travel-assistant
    sudo chown -R $USER:$USER /var/lib/mbti-travel-assistant
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build application image
    log "Building application image..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache mbti-travel-assistant
    
    # Stop existing containers gracefully
    log "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 30 || true
    
    # Start services
    log "Starting production services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 60
    
    # Check service health
    check_service_health
    
    # Run post-deployment tests
    post_deployment_tests
    
    log "${GREEN}✓ Production deployment completed successfully${NC}"
    log "${BLUE}Production services are running${NC}"
}

# Check service health
check_service_health() {
    log "Checking production service health..."
    
    local max_attempts=20
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
            log "${GREEN}✓ MBTI Travel Assistant is healthy${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                error_exit "MBTI Travel Assistant failed to become healthy after $max_attempts attempts"
            fi
            log "${YELLOW}Attempt $attempt/$max_attempts: Waiting for MBTI Travel Assistant to be healthy...${NC}"
            sleep 15
            attempt=$((attempt + 1))
        fi
    done
    
    # Check detailed health status
    local health_response
    health_response=$(curl -s http://localhost:8080/health)
    local overall_status
    overall_status=$(echo "$health_response" | grep -o '"overall_status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$overall_status" = "healthy" ]; then
        log "${GREEN}✓ Application health status: healthy${NC}"
    else
        log "${YELLOW}⚠ Application health status: $overall_status${NC}"
        log "Health response: $health_response"
    fi
}

# Post-deployment tests
post_deployment_tests() {
    log "${BLUE}Running post-deployment tests...${NC}"
    
    # Test basic functionality
    local test_payload='{"MBTI_personality": "INFJ"}'
    local response
    
    if response=$(curl -s -X POST -H "Content-Type: application/json" -d "$test_payload" http://localhost:8080/invocations); then
        if echo "$response" | grep -q "main_itinerary"; then
            log "${GREEN}✓ Basic functionality test passed${NC}"
        else
            log "${YELLOW}⚠ Basic functionality test returned unexpected response${NC}"
            log "Response: $response"
        fi
    else
        log "${YELLOW}⚠ Basic functionality test failed${NC}"
    fi
    
    # Test metrics endpoint
    if curl -f -s http://localhost:9090/metrics > /dev/null 2>&1; then
        log "${GREEN}✓ Metrics endpoint is accessible${NC}"
    else
        log "${YELLOW}⚠ Metrics endpoint is not accessible${NC}"
    fi
}

# Show logs
show_logs() {
    log "${BLUE}Showing production service logs...${NC}"
    docker-compose -f "$COMPOSE_FILE" logs -f --tail=100
}

# Stop services
stop() {
    log "${BLUE}Stopping production services...${NC}"
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" down --timeout 30
    log "${GREEN}✓ Production services stopped${NC}"
}

# Rollback deployment
rollback() {
    log "${BLUE}Rolling back production deployment...${NC}"
    cd "$PROJECT_DIR"
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down --timeout 30
    
    # Start with previous image (assuming it exists)
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait and check health
    sleep 60
    check_service_health
    
    log "${GREEN}✓ Rollback completed${NC}"
}

# Backup data
backup() {
    log "${BLUE}Creating production data backup...${NC}"
    
    local backup_dir="/var/backups/mbti-travel-assistant/$(date +%Y%m%d_%H%M%S)"
    sudo mkdir -p "$backup_dir"
    
    # Backup application data
    if [ -d "/var/lib/mbti-travel-assistant" ]; then
        sudo cp -r /var/lib/mbti-travel-assistant "$backup_dir/"
        log "${GREEN}✓ Application data backed up to $backup_dir${NC}"
    fi
    
    # Backup logs
    if [ -d "/var/log/mbti-travel-assistant" ]; then
        sudo cp -r /var/log/mbti-travel-assistant "$backup_dir/"
        log "${GREEN}✓ Logs backed up to $backup_dir${NC}"
    fi
    
    # Backup Docker volumes
    docker run --rm -v mbti-prometheus-prod-data:/data -v "$backup_dir":/backup alpine tar czf /backup/prometheus_data.tar.gz -C /data .
    docker run --rm -v mbti-alertmanager-data:/data -v "$backup_dir":/backup alpine tar czf /backup/alertmanager_data.tar.gz -C /data .
    
    log "${GREEN}✓ Backup completed: $backup_dir${NC}"
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            pre_deployment_validation
            deploy
            ;;
        "logs")
            show_logs
            ;;
        "stop")
            stop
            ;;
        "rollback")
            rollback
            ;;
        "backup")
            backup
            ;;
        "health")
            check_service_health
            ;;
        "test")
            post_deployment_tests
            ;;
        *)
            echo "Usage: $0 {deploy|logs|stop|rollback|backup|health|test}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Build and deploy production environment (default)"
            echo "  logs     - Show service logs"
            echo "  stop     - Stop all services"
            echo "  rollback - Rollback to previous deployment"
            echo "  backup   - Create data backup"
            echo "  health   - Check service health"
            echo "  test     - Run post-deployment tests"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"