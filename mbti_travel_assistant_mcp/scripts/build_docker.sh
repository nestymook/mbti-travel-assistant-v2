#!/bin/bash

# Docker build script for MBTI Travel Assistant MCP
# This script builds the Docker image with ARM64 platform support for AgentCore

set -e

# Configuration
IMAGE_NAME="mbti-travel-assistant-mcp"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"
PLATFORM="linux/arm64"
BUILD_CONTEXT="."

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
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if buildx is available for multi-platform builds
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx is not available. Please update Docker to a version that supports buildx"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to validate Dockerfile
validate_dockerfile() {
    log_info "Validating Dockerfile..."
    
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile not found in current directory"
        exit 1
    fi
    
    # Check if Dockerfile specifies ARM64 platform
    if ! grep -q "linux/arm64" Dockerfile; then
        log_error "Dockerfile must specify --platform=linux/arm64 for AgentCore compatibility"
        exit 1
    fi
    
    log_success "Dockerfile validation passed"
}

# Function to create buildx builder if needed
setup_buildx() {
    log_info "Setting up Docker buildx..."
    
    # Create a new builder instance if it doesn't exist
    if ! docker buildx ls | grep -q "mbti-builder"; then
        log_info "Creating new buildx builder instance..."
        docker buildx create --name mbti-builder --driver docker-container --bootstrap
    fi
    
    # Use the builder
    docker buildx use mbti-builder
    
    log_success "Buildx setup completed"
}

# Function to build the Docker image
build_image() {
    log_info "Building Docker image..."
    
    # Construct full image name
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    log_info "Building image: $FULL_IMAGE_NAME"
    log_info "Platform: $PLATFORM"
    log_info "Build context: $BUILD_CONTEXT"
    
    # Build arguments
    BUILD_ARGS=""
    if [ -n "$BUILD_ARG_ENV" ]; then
        BUILD_ARGS="--build-arg ENVIRONMENT=$BUILD_ARG_ENV"
    fi
    
    # Build the image
    docker buildx build \
        --platform "$PLATFORM" \
        --tag "$FULL_IMAGE_NAME" \
        --load \
        $BUILD_ARGS \
        "$BUILD_CONTEXT"
    
    log_success "Docker image built successfully: $FULL_IMAGE_NAME"
}

# Function to test the built image
test_image() {
    log_info "Testing Docker image..."
    
    # Construct full image name
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    # Test image by running health check
    log_info "Running container health check..."
    
    # Start container in detached mode
    CONTAINER_ID=$(docker run -d --platform "$PLATFORM" "$FULL_IMAGE_NAME")
    
    # Wait for container to start
    sleep 10
    
    # Check if container is running
    if docker ps | grep -q "$CONTAINER_ID"; then
        log_success "Container started successfully"
        
        # Run health check
        if docker exec "$CONTAINER_ID" /app/health_check.sh; then
            log_success "Health check passed"
        else
            log_warning "Health check failed, but container is running"
        fi
    else
        log_error "Container failed to start"
        docker logs "$CONTAINER_ID"
        docker rm "$CONTAINER_ID"
        exit 1
    fi
    
    # Clean up test container
    docker stop "$CONTAINER_ID" > /dev/null
    docker rm "$CONTAINER_ID" > /dev/null
    
    log_success "Image testing completed"
}

# Function to push image to registry
push_image() {
    if [ -n "$REGISTRY" ] && [ "$PUSH_IMAGE" = "true" ]; then
        log_info "Pushing image to registry..."
        
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        
        docker push "$FULL_IMAGE_NAME"
        
        log_success "Image pushed to registry: $FULL_IMAGE_NAME"
    else
        log_info "Skipping image push (PUSH_IMAGE not set to true or no registry specified)"
    fi
}

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG          Image tag (default: latest)"
    echo "  -r, --registry REG     Docker registry URL"
    echo "  -p, --push             Push image to registry after build"
    echo "  -e, --env ENV          Build environment (development, staging, production)"
    echo "  --no-test              Skip image testing"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  IMAGE_TAG              Image tag (default: latest)"
    echo "  REGISTRY               Docker registry URL"
    echo "  PUSH_IMAGE             Set to 'true' to push image"
    echo "  BUILD_ARG_ENV          Build environment argument"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build with default settings"
    echo "  $0 -t v1.0.0 -p                     # Build and push with tag v1.0.0"
    echo "  $0 -r my-registry.com -t latest -p  # Build and push to custom registry"
}

# Parse command line arguments
PUSH_IMAGE="false"
RUN_TESTS="true"

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH_IMAGE="true"
            shift
            ;;
        -e|--env)
            BUILD_ARG_ENV="$2"
            shift 2
            ;;
        --no-test)
            RUN_TESTS="false"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting Docker build process for MBTI Travel Assistant MCP"
    log_info "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "Platform: ${PLATFORM}"
    
    check_prerequisites
    validate_dockerfile
    setup_buildx
    build_image
    
    if [ "$RUN_TESTS" = "true" ]; then
        test_image
    fi
    
    push_image
    
    log_success "Docker build process completed successfully!"
    
    # Display final image information
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    echo ""
    log_info "Built image: $FULL_IMAGE_NAME"
    log_info "Platform: $PLATFORM"
    log_info "Size: $(docker images --format "table {{.Size}}" "$FULL_IMAGE_NAME" | tail -n 1)"
    echo ""
    log_info "To run the container:"
    echo "  docker run --platform $PLATFORM -p 8080:8080 $FULL_IMAGE_NAME"
}

# Run main function
main "$@"