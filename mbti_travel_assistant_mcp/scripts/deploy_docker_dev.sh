#!/bin/bash
# Development Docker Deployment Script for MBTI Travel Assistant MCP

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE="config/environments/development.env"

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
    log "${BLUE}Checking prerequisites...${NC}"
    
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
    
    log "${GREEN}✓ Prerequisites check passed${NC}"
}

# Build and deploy
deploy() {
    log "${BLUE}Starting development deployment...${NC}"
    
    cd "$PROJECT_DIR"
    
    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        log "Loading environment from $ENV_FILE"
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    else
        log "${YELLOW}Warning: Environment file $ENV_FILE not found${NC}"
    fi
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true
    
    # Build images
    log "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start services
    log "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log "${GREEN}✓ Development deployment completed successfully${NC}"
    log "${BLUE}Services are available at:${NC}"
    log "  - MBTI Travel Assistant: http://localhost:8080"
    log "  - Grafana Dashboard: http://localhost:3000 (admin/admin123)"
    log "  - Prometheus: http://localhost:9091"
    log "  - Jaeger Tracing: http://localhost:16686"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    local max_attempts=10
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
            sleep 10
            attempt=$((attempt + 1))
        fi
    done
    
    # Check other services
    if curl -f -s http://localhost:6379 > /dev/null 2>&1; then
        log "${GREEN}✓ Redis is accessible${NC}"
    else
        log "${YELLOW}⚠ Redis may not be accessible${NC}"
    fi
}

# Show logs
show_logs() {
    log "${BLUE}Showing service logs...${NC}"
    docker-compose -f "$COMPOSE_FILE" logs -f --tail=50
}

# Stop services
stop() {
    log "${BLUE}Stopping development services...${NC}"
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" down
    log "${GREEN}✓ Services stopped${NC}"
}

# Clean up
cleanup() {
    log "${BLUE}Cleaning up development environment...${NC}"
    cd "$PROJECT_DIR"
    docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans
    docker system prune -f
    log "${GREEN}✓ Cleanup completed${NC}"
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            deploy
            ;;
        "logs")
            show_logs
            ;;
        "stop")
            stop
            ;;
        "cleanup")
            cleanup
            ;;
        "restart")
            stop
            sleep 5
            check_prerequisites
            deploy
            ;;
        *)
            echo "Usage: $0 {deploy|logs|stop|cleanup|restart}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Build and deploy development environment (default)"
            echo "  logs     - Show service logs"
            echo "  stop     - Stop all services"
            echo "  cleanup  - Stop services and clean up volumes"
            echo "  restart  - Stop and redeploy services"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"