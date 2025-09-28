#!/bin/bash

# Docker Compose deployment script for MBTI Travel Assistant MCP
# This script manages deployment using docker-compose for different environments

set -e

# Configuration
ENVIRONMENT="${ENVIRONMENT:-development}"
COMPOSE_PROJECT_NAME="mbti-travel-assistant"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_FILE_PROD="docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to validate environment configuration
validate_environment() {
    log_info "Validating environment configuration for: $ENVIRONMENT"
    
    # Check if environment configuration exists
    ENV_FILE="config/environments/${ENVIRONMENT}.env"
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment configuration file not found: $ENV_FILE"
        exit 1
    fi
    
    # Validate required environment variables for production
    if [ "$ENVIRONMENT" = "production" ]; then
        REQUIRED_VARS=(
            "SEARCH_MCP_ENDPOINT"
            "REASONING_MCP_ENDPOINT"
            "COGNITO_USER_POOL_ID"
            "JWT_AUDIENCE"
        )
        
        for var in "${REQUIRED_VARS[@]}"; do
            if [ -z "${!var}" ]; then
                log_error "Required environment variable not set: $var"
                exit 1
            fi
        done
    fi
    
    log_success "Environment configuration validated"
}

# Function to select compose file based on environment
select_compose_file() {
    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="$COMPOSE_FILE_PROD"
        log_info "Using production compose file: $COMPOSE_FILE"
    else
        log_info "Using development compose file: $COMPOSE_FILE"
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
}

# Function to load environment variables
load_environment() {
    log_info "Loading environment variables..."
    
    # Load base .env file if it exists
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
        log_info "Loaded base .env file"
    fi
    
    # Load environment-specific configuration
    ENV_FILE="config/environments/${ENVIRONMENT}.env"
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        log_info "Loaded environment-specific configuration: $ENV_FILE"
    fi
    
    # Export environment for docker-compose
    export ENVIRONMENT
    export COMPOSE_PROJECT_NAME
}

# Function to build images
build_images() {
    log_info "Building Docker images..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" build
    else
        docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" build
    fi
    
    log_success "Docker images built successfully"
}

# Function to start services
start_services() {
    log_info "Starting services..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" up -d
    else
        docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" up -d
    fi
    
    log_success "Services started successfully"
}

# Function to stop services
stop_services() {
    log_info "Stopping services..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" down
    else
        docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" down
    fi
    
    log_success "Services stopped successfully"
}

# Function to restart services
restart_services() {
    log_info "Restarting services..."
    
    stop_services
    start_services
    
    log_success "Services restarted successfully"
}

# Function to show service status
show_status() {
    log_info "Service status:"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" ps
    else
        docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" ps
    fi
}

# Function to show service logs
show_logs() {
    local service="$1"
    local follow="$2"
    
    if [ -n "$service" ]; then
        log_info "Showing logs for service: $service"
        if [ "$follow" = "true" ]; then
            if command -v docker-compose &> /dev/null; then
                docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" logs -f "$service"
            else
                docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" logs -f "$service"
            fi
        else
            if command -v docker-compose &> /dev/null; then
                docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" logs "$service"
            else
                docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" logs "$service"
            fi
        fi
    else
        log_info "Showing logs for all services"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" logs
        else
            docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" logs
        fi
    fi
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check main service health
    if curl -f -s http://localhost:8080/health > /dev/null; then
        log_success "Main service health check passed"
    else
        log_error "Main service health check failed"
        return 1
    fi
    
    # Check Redis health (if running)
    if docker ps --format "table {{.Names}}" | grep -q "mbti-redis"; then
        if docker exec mbti-redis redis-cli ping | grep -q "PONG"; then
            log_success "Redis health check passed"
        else
            log_warning "Redis health check failed"
        fi
    fi
    
    # Check Prometheus health (if running)
    if docker ps --format "table {{.Names}}" | grep -q "prometheus"; then
        if curl -f -s http://localhost:9091/-/healthy > /dev/null; then
            log_success "Prometheus health check passed"
        else
            log_warning "Prometheus health check failed"
        fi
    fi
    
    log_success "Health checks completed"
}

# Function to clean up resources
cleanup() {
    log_info "Cleaning up resources..."
    
    # Stop and remove containers
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" down -v --remove-orphans
    else
        docker compose -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" down -v --remove-orphans
    fi
    
    # Remove unused images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Function to display usage
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start                  Start all services"
    echo "  stop                   Stop all services"
    echo "  restart                Restart all services"
    echo "  build                  Build Docker images"
    echo "  status                 Show service status"
    echo "  logs [SERVICE]         Show logs (optionally for specific service)"
    echo "  health                 Run health checks"
    echo "  cleanup                Clean up resources"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV          Environment (development, staging, production)"
    echo "  -f, --follow           Follow logs (for logs command)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT            Deployment environment"
    echo ""
    echo "Examples:"
    echo "  $0 start                           # Start development environment"
    echo "  $0 start -e production            # Start production environment"
    echo "  $0 logs mbti-travel-assistant -f  # Follow logs for main service"
    echo "  $0 health                         # Run health checks"
}

# Parse command line arguments
COMMAND=""
SERVICE=""
FOLLOW_LOGS="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|build|status|logs|health|cleanup)
            COMMAND="$1"
            shift
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--follow)
            FOLLOW_LOGS="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            if [ "$COMMAND" = "logs" ] && [ -z "$SERVICE" ]; then
                SERVICE="$1"
            else
                log_error "Unknown option: $1"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Main execution
main() {
    if [ -z "$COMMAND" ]; then
        log_error "No command specified"
        usage
        exit 1
    fi
    
    log_info "MBTI Travel Assistant MCP Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Command: $COMMAND"
    
    check_prerequisites
    validate_environment
    select_compose_file
    load_environment
    
    case $COMMAND in
        start)
            build_images
            start_services
            run_health_checks
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            run_health_checks
            ;;
        build)
            build_images
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$SERVICE" "$FOLLOW_LOGS"
            ;;
        health)
            run_health_checks
            ;;
        cleanup)
            cleanup
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
    
    log_success "Deployment command completed successfully!"
}

# Run main function
main "$@"