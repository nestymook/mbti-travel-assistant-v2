# Docker Setup for MBTI Travel Assistant MCP

This document provides a quick reference for running the MBTI Travel Assistant MCP using Docker containers with ARM64 platform support for Amazon Bedrock AgentCore Runtime.

> 📖 **For comprehensive deployment instructions, troubleshooting, and advanced configuration, see the [Docker Deployment Guide](./DOCKER_DEPLOYMENT_GUIDE.md)**

## 🚀 Quick Commands

```bash
# Development deployment
./scripts/deploy_docker_dev.sh

# Production deployment  
./scripts/deploy_docker_prod.sh

# Run tests
./scripts/test_docker.sh

# Monitor services
./scripts/monitor_docker.sh

# Health check
curl http://localhost:8080/health
```

## 📋 Service Ports

| Service | Development | Production | Purpose |
|---------|-------------|------------|---------|
| MBTI Travel Assistant | 8080 | 8080 | AgentCore Runtime |
| Redis | 6379 | - | Cache service |
| Prometheus | 9091 | 9091 | Metrics collection |
| Grafana | 3000 | - | Dashboards |
| Jaeger | 16686 | - | Tracing |
| Nginx | - | 80, 443 | Reverse proxy |

## Overview

The MBTI Travel Assistant MCP is containerized using Docker with ARM64 platform support required for Amazon Bedrock AgentCore Runtime. The deployment includes:

- Main application container with AgentCore Runtime
- Redis cache for performance optimization
- Mock MCP servers for development testing
- Monitoring stack (Prometheus, Grafana, Jaeger)
- Health checks and observability

## Prerequisites

### Required Software

- **Docker Desktop** (latest version with buildx support)
- **Docker Compose** v2.0 or later
- **Git** for cloning the repository

### System Requirements

- **Platform**: ARM64 architecture support (required for AgentCore)
- **Memory**: Minimum 8GB RAM (16GB recommended for full stack)
- **Storage**: At least 10GB free disk space
- **Network**: Internet access for pulling base images

### AWS Prerequisites

- AWS account with configured credentials
- Bedrock model access enabled (Anthropic Claude models)
- Cognito User Pool configured (for production)

## Quick Start

### Development Environment

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd mbti_travel_assistant_mcp
   ```

2. **Start development environment**:
   ```bash
   # Using bash script (Linux/macOS)
   ./scripts/deploy_docker.sh start
   
   # Using PowerShell script (Windows)
   .\scripts\deploy_docker.ps1 start
   
   # Using docker-compose directly
   docker-compose up -d
   ```

3. **Verify deployment**:
   ```bash
   # Check service status
   ./scripts/deploy_docker.sh status
   
   # Run health checks
   ./scripts/deploy_docker.sh health
   
   # View logs
   ./scripts/deploy_docker.sh logs mbti-travel-assistant -f
   ```

4. **Access services**:
   - **Main Service**: http://localhost:8080
   - **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
   - **Prometheus**: http://localhost:9091
   - **Jaeger Tracing**: http://localhost:16686

### Production Environment

1. **Configure environment variables**:
   ```bash
   # Copy and customize production environment file
   cp config/environments/production.env.example config/environments/production.env
   
   # Edit with your production values
   nano config/environments/production.env
   ```

2. **Deploy to production**:
   ```bash
   # Using deployment script
   ./scripts/deploy_docker.sh start -e production
   
   # Using docker-compose directly
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Configuration

### Environment Files

Environment-specific configuration is managed through `.env` files:

- `config/environments/development.env` - Development settings
- `config/environments/staging.env` - Staging settings  
- `config/environments/production.env` - Production settings

### Key Configuration Variables

#### MCP Client Configuration
```bash
SEARCH_MCP_ENDPOINT=https://prod-search-mcp.agentcore.aws
REASONING_MCP_ENDPOINT=https://prod-reasoning-mcp.agentcore.aws
MCP_CONNECTION_TIMEOUT=45
MCP_RETRY_ATTEMPTS=5
```

#### Authentication Configuration
```bash
COGNITO_USER_POOL_ID=us-east-1_prod456789
COGNITO_REGION=us-east-1
JWT_ALGORITHM=RS256
JWT_AUDIENCE=mbti-travel-assistant-prod
```

#### AgentCore Runtime Configuration
```bash
AGENT_MODEL=amazon.nova-pro-v1:0:300k
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=4096
```

### Validation

Validate your configuration before deployment:

```bash
# Validate all environments
python config/validate_config.py

# Initialize configuration if needed
python config/init_config.py
```

## Docker Images

### Base Image

The application uses ARM64-compatible base images:

```dockerfile
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim
```

### Building Images

#### Using Build Script

```bash
# Build with default settings
./scripts/build_docker.sh

# Build with custom tag and push to registry
./scripts/build_docker.sh -t v1.0.0 -r my-registry.com -p

# Build for specific environment
./scripts/build_docker.sh -e production -t latest
```

#### Manual Build

```bash
# Build for ARM64 platform
docker buildx build --platform linux/arm64 -t mbti-travel-assistant-mcp:latest .

# Build and load for local testing
docker buildx build --platform linux/arm64 -t mbti-travel-assistant-mcp:latest --load .
```

### Image Registry

For production deployments, push images to a container registry:

```bash
# Tag for registry
docker tag mbti-travel-assistant-mcp:latest your-registry.com/mbti-travel-assistant-mcp:latest

# Push to registry
docker push your-registry.com/mbti-travel-assistant-mcp:latest
```

## Service Architecture

### Development Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Environment                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ MBTI Travel     │    │ Redis Cache     │                │
│  │ Assistant       │    │ (localhost:6379)│                │
│  │ (localhost:8080)│    └─────────────────┘                │
│  └─────────────────┘                                       │
│           │                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Search MCP Mock │    │ Reasoning MCP   │                │
│  │ (localhost:8001)│    │ Mock            │                │
│  └─────────────────┘    │ (localhost:8002)│                │
│                         └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│                    Monitoring Stack                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Prometheus      │    │ Grafana         │                │
│  │ (localhost:9091)│    │ (localhost:3000)│                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐                                       │
│  │ Jaeger Tracing  │                                       │
│  │ (localhost:16686)│                                      │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

### Production Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Nginx Proxy     │    │ MBTI Travel     │                │
│  │ (ports 80/443)  │────│ Assistant       │                │
│  └─────────────────┘    │ (internal:8080) │                │
│                         └─────────────────┘                │
│                                  │                          │
│                         ┌─────────────────┐                │
│                         │ External Redis  │                │
│                         │ (AWS ElastiCache)│               │
│                         └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│                    External Services                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Search MCP      │    │ Reasoning MCP   │                │
│  │ (AgentCore)     │    │ (AgentCore)     │                │
│  └─────────────────┘    └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│                    Monitoring & Logging                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Prometheus      │    │ Alertmanager    │                │
│  │ (internal:9090) │    │ (internal:9093) │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐                                       │
│  │ Fluentd         │                                       │
│  │ (log aggregation)│                                      │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## Health Checks

### Container Health Checks

Each container includes comprehensive health checks:

```bash
# Check container health status
docker ps --format "table {{.Names}}\t{{.Status}}"

# View health check logs
docker inspect mbti-travel-assistant-mcp-prod --format='{{json .State.Health}}'
```

### Service Health Endpoints

- **Main Service**: `GET /health`
- **Metrics**: `GET /metrics`
- **Ready**: `GET /ready`

### Health Check Script

The application includes a comprehensive health check script:

```bash
# Run health check manually
docker exec mbti-travel-assistant-mcp /app/health_check.sh

# Check specific components
curl -f http://localhost:8080/health
curl -f http://localhost:8080/metrics
```

## Monitoring and Observability

### Metrics Collection

Prometheus collects metrics from:
- Application performance metrics
- Container resource usage
- MCP client connection metrics
- Authentication success/failure rates

### Dashboards

Grafana provides pre-configured dashboards:
- **Application Overview**: Service health and performance
- **MCP Client Metrics**: Connection status and response times
- **Infrastructure**: Container resources and system metrics
- **Security**: Authentication events and security metrics

### Distributed Tracing

Jaeger provides distributed tracing for:
- HTTP request flows
- MCP client calls
- Authentication processes
- Cache operations

### Log Aggregation

Fluentd (production) aggregates logs from:
- Application containers
- Nginx access/error logs
- System logs
- Docker container logs

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker logs mbti-travel-assistant-mcp

# Check resource usage
docker stats

# Verify platform compatibility
docker inspect mbti-travel-assistant-mcp | grep Architecture
```

#### Health Check Failures

```bash
# Run health check manually
docker exec mbti-travel-assistant-mcp /app/health_check.sh

# Check service endpoints
curl -v http://localhost:8080/health

# Verify MCP connectivity
curl -v http://localhost:8001/health
curl -v http://localhost:8002/health
```

#### Performance Issues

```bash
# Check resource usage
docker stats mbti-travel-assistant-mcp

# View application metrics
curl http://localhost:8080/metrics

# Check cache hit rates
docker exec mbti-redis redis-cli info stats
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment variables
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart with debug logging
./scripts/deploy_docker.sh restart
```

### Log Analysis

```bash
# View application logs
./scripts/deploy_docker.sh logs mbti-travel-assistant -f

# View all service logs
docker-compose logs -f

# Search logs for errors
docker-compose logs | grep ERROR

# View structured logs
docker-compose logs --json mbti-travel-assistant
```

## Security Considerations

### Container Security

- **Non-root user**: Containers run as non-root user (uid 1000)
- **Read-only filesystem**: Application files are read-only
- **Resource limits**: CPU and memory limits enforced
- **Network isolation**: Services communicate through internal networks

### Secrets Management

- **Environment variables**: Sensitive data via environment variables
- **Docker secrets**: Use Docker secrets for production
- **AWS Secrets Manager**: Integration for cloud deployments

### Network Security

- **Internal networks**: Services communicate via internal Docker networks
- **TLS encryption**: HTTPS/TLS for external communications
- **Firewall rules**: Restrict external access to necessary ports only

## Maintenance

### Updates and Upgrades

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
./scripts/deploy_docker.sh restart

# Update specific service
docker-compose up -d --no-deps mbti-travel-assistant
```

### Backup and Recovery

```bash
# Backup volumes
docker run --rm -v mbti-redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz /data

# Restore volumes
docker run --rm -v mbti-redis-data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-backup.tar.gz -C /
```

### Cleanup

```bash
# Clean up development environment
./scripts/deploy_docker.sh cleanup

# Remove unused images and volumes
docker system prune -a --volumes

# Reset to clean state
docker-compose down -v --remove-orphans
docker system prune -a --volumes
```

## Performance Tuning

### Resource Allocation

Adjust resource limits in docker-compose files:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

### Cache Optimization

Configure Redis cache settings:

```bash
# Redis memory optimization
docker exec mbti-redis redis-cli CONFIG SET maxmemory 1gb
docker exec mbti-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Connection Pooling

Optimize MCP client connections:

```bash
# Environment variables for connection pooling
MCP_CONNECTION_POOL_SIZE=10
MCP_CONNECTION_TIMEOUT=30
MCP_RETRY_ATTEMPTS=3
```

## Support

For issues and questions:

1. **Check logs**: Review application and container logs
2. **Health checks**: Verify all health check endpoints
3. **Documentation**: Refer to API documentation and troubleshooting guides
4. **Monitoring**: Check Grafana dashboards and Prometheus metrics
5. **Community**: Consult project documentation and community resources

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Platform**: linux/arm64 (required for AgentCore)