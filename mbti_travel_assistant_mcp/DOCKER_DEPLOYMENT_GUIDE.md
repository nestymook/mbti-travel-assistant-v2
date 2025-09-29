# Docker Deployment Guide for MBTI Travel Assistant MCP

This guide provides comprehensive instructions for deploying the MBTI Travel Assistant MCP using Docker containers with ARM64 platform support for Amazon Bedrock AgentCore Runtime.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Environment Configuration](#environment-configuration)
4. [Development Deployment](#development-deployment)
5. [Production Deployment](#production-deployment)
6. [Testing with Docker](#testing-with-docker)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)
10. [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements

- **Docker Engine**: 20.10+ with ARM64 support
- **Docker Compose**: 2.0+ or docker-compose 1.29+
- **Platform**: ARM64 architecture (required for AgentCore Runtime)
- **Memory**: Minimum 4GB RAM, recommended 8GB+
- **Storage**: Minimum 20GB free space
- **Network**: Internet access for image pulls and AWS services

### AWS Requirements

- AWS CLI configured with appropriate credentials
- Access to Amazon Bedrock and Nova Pro foundation model
- Knowledge Base ID: `RCWW86CLM9` (or your configured KB)
- Cognito User Pool configured for JWT authentication
- MCP server endpoints accessible

### Docker Platform Support

**CRITICAL**: Amazon Bedrock AgentCore Runtime **REQUIRES** `linux/arm64` architecture. All Docker images must be built with `--platform=linux/arm64`.

```bash
# Verify Docker supports ARM64
docker buildx ls
docker buildx inspect --bootstrap
```

## Architecture Overview

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ MBTI Travel     │  │ Redis Cache     │  │ Prometheus  │ │
│  │ Assistant       │  │                 │  │ Metrics     │ │
│  │ (ARM64)         │  │                 │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Nginx Proxy     │  │ Grafana         │  │ Jaeger      │ │
│  │ (Production)    │  │ Dashboard       │  │ Tracing     │ │
│  │                 │  │                 │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Mock Search     │  │ Mock Reasoning  │                  │
│  │ MCP Server      │  │ MCP Server      │                  │
│  │ (Dev/Test)      │  │ (Dev/Test)      │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Port Mapping

| Service | Development Port | Production Port | Purpose |
|---------|------------------|-----------------|---------|
| MBTI Travel Assistant | 8080 | 8080 | AgentCore Runtime |
| Metrics Endpoint | 9090 | 9090 | Prometheus metrics |
| Redis | 6379 | - | Cache service |
| Prometheus | 9091 | 9091 | Metrics collection |
| Grafana | 3000 | - | Metrics visualization |
| Jaeger | 16686 | - | Distributed tracing |
| Nginx | - | 80, 443 | Reverse proxy |
| Mock Search MCP | 8001 | - | Development testing |
| Mock Reasoning MCP | 8002 | - | Development testing |

## Environment Configuration

### Environment Files

Create environment-specific configuration files:

#### Development Environment
```bash
# config/environments/development.env
ENVIRONMENT=development
AWS_REGION=us-east-1
LOG_LEVEL=DEBUG
CACHE_ENABLED=true
TRACING_ENABLED=true
METRICS_ENABLED=true

# MCP Endpoints (using mock servers)
SEARCH_MCP_ENDPOINT=http://search-mcp-mock:8080
REASONING_MCP_ENDPOINT=http://reasoning-mcp-mock:8080

# Authentication (development mode)
COGNITO_USER_POOL_ID=us-east-1_dev123456
JWT_ALGORITHM=RS256
```

#### Production Environment
```bash
# config/environments/production.env
ENVIRONMENT=production
AWS_REGION=us-east-1
LOG_LEVEL=INFO
LOG_FORMAT=json
CACHE_ENABLED=true
CACHE_TTL=1800
TRACING_ENABLED=true
METRICS_ENABLED=true

# MCP Endpoints (production URLs)
SEARCH_MCP_ENDPOINT=https://your-search-mcp-endpoint.com
REASONING_MCP_ENDPOINT=https://your-reasoning-mcp-endpoint.com
MCP_CONNECTION_TIMEOUT=45
MCP_RETRY_ATTEMPTS=5

# Authentication (production)
COGNITO_USER_POOL_ID=us-east-1_your_pool_id
COGNITO_REGION=us-east-1
JWT_ALGORITHM=RS256
JWT_AUDIENCE=mbti-travel-assistant-prod
TOKEN_CACHE_TTL=1800

# AgentCore Configuration
AGENT_MODEL=amazon.nova-pro-v1:0:300k
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=4096
```

## Development Deployment

### Quick Start

1. **Clone and Navigate**
   ```bash
   cd mbti_travel_assistant_mcp
   ```

2. **Build and Deploy**
   ```bash
   ./scripts/deploy_docker_dev.sh
   ```

3. **Verify Deployment**
   ```bash
   curl http://localhost:8080/health
   ```

### Manual Development Deployment

1. **Build Images**
   ```bash
   docker-compose build --no-cache
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Check Service Status**
   ```bash
   docker-compose ps
   ```

4. **View Logs**
   ```bash
   docker-compose logs -f mbti-travel-assistant
   ```

### Development Services

- **MBTI Travel Assistant**: http://localhost:8080
- **Health Check**: http://localhost:8080/health
- **Metrics**: http://localhost:9090/metrics
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9091
- **Jaeger Tracing**: http://localhost:16686

## Production Deployment

### Prerequisites Checklist

- [ ] AWS credentials configured
- [ ] Production MCP endpoints accessible
- [ ] Cognito User Pool configured
- [ ] SSL certificates available (optional)
- [ ] Production environment variables set
- [ ] Monitoring infrastructure ready

### Production Deployment Steps

1. **Set Environment Variables**
   ```bash
   export SEARCH_MCP_ENDPOINT="https://your-search-mcp.com"
   export REASONING_MCP_ENDPOINT="https://your-reasoning-mcp.com"
   export COGNITO_USER_POOL_ID="us-east-1_your_pool_id"
   export JWT_AUDIENCE="mbti-travel-assistant-prod"
   ```

2. **Deploy Production Stack**
   ```bash
   ./scripts/deploy_docker_prod.sh
   ```

3. **Verify Production Health**
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:9090/metrics
   ```

### Production Services

- **MBTI Travel Assistant**: http://localhost:8080 (behind Nginx)
- **Nginx Reverse Proxy**: http://localhost:80, https://localhost:443
- **Prometheus**: http://localhost:9091
- **Alertmanager**: http://localhost:9093

### Production Monitoring

The production deployment includes:

- **Nginx**: Reverse proxy with SSL termination
- **Fluentd**: Log aggregation to CloudWatch
- **Prometheus**: Metrics collection with alerting rules
- **Alertmanager**: Alert routing and notification

## Testing with Docker

### Automated Testing

1. **Run All Tests**
   ```bash
   ./scripts/test_docker.sh
   ```

2. **Run Specific Test Types**
   ```bash
   ./scripts/test_docker.sh unit
   ./scripts/test_docker.sh integration
   ./scripts/test_docker.sh e2e
   ./scripts/test_docker.sh load
   ./scripts/test_docker.sh security
   ```

### Manual Testing

1. **Start Test Environment**
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

2. **Run Tests**
   ```bash
   docker-compose -f docker-compose.test.yml run --rm test-runner
   ```

3. **Load Testing**
   ```bash
   docker-compose -f docker-compose.test.yml run --rm load-tester
   ```

### Test Results

Test results are stored in `tests/results/`:
- `unit_tests.xml` - Unit test results
- `integration_tests.xml` - Integration test results
- `load_test_results.json` - Load test metrics
- `test_summary.txt` - Overall test summary

## Monitoring and Health Checks

### Built-in Health Checks

All containers include comprehensive health checks:

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View health check logs
docker inspect mbti-travel-assistant-mcp --format='{{.State.Health}}'
```

### Monitoring Script

Use the monitoring script for continuous health monitoring:

```bash
# One-time monitoring
./scripts/monitor_docker.sh

# Continuous monitoring (daemon mode)
./scripts/monitor_docker.sh daemon

# Generate detailed report
./scripts/monitor_docker.sh report
```

### Health Endpoints

- **Application Health**: `GET /health`
- **Metrics**: `GET /metrics`
- **Prometheus Health**: `GET http://localhost:9091/-/healthy`

### Monitoring Dashboards

Access monitoring dashboards:

- **Grafana**: http://localhost:3000
  - Username: admin
  - Password: admin123
- **Prometheus**: http://localhost:9091
- **Jaeger**: http://localhost:16686

## Troubleshooting

### Common Issues

#### 1. ARM64 Platform Issues

**Problem**: Container fails to start with architecture mismatch
```
Error: exec format error
```

**Solution**: Ensure all images are built for ARM64
```bash
docker buildx build --platform linux/arm64 -t mbti-travel-assistant .
```

#### 2. Health Check Failures

**Problem**: Container health checks failing
```bash
# Check health check script
docker exec mbti-travel-assistant-mcp /app/health_check.sh

# View health check logs
docker logs mbti-travel-assistant-mcp
```

**Solution**: Verify application is listening on correct ports and endpoints are accessible

#### 3. Memory Issues

**Problem**: Out of memory errors
```bash
# Check memory usage
docker stats --no-stream

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

#### 4. Network Connectivity

**Problem**: Services cannot communicate
```bash
# Check network
docker network ls
docker network inspect mbti-travel-assistant-network

# Test connectivity
docker exec mbti-travel-assistant-mcp ping redis
```

### Debug Commands

```bash
# View container logs
docker-compose logs -f [service_name]

# Execute shell in container
docker exec -it mbti-travel-assistant-mcp /bin/bash

# Check container processes
docker exec mbti-travel-assistant-mcp ps aux

# Check container environment
docker exec mbti-travel-assistant-mcp env

# View container resource usage
docker stats mbti-travel-assistant-mcp
```

### Log Analysis

```bash
# Application logs
docker-compose logs mbti-travel-assistant | grep ERROR

# System logs
docker-compose logs mbti-travel-assistant | grep -E "(WARN|ERROR|FATAL)"

# Performance logs
docker-compose logs mbti-travel-assistant | grep "response_time"
```

## Performance Optimization

### Container Optimization

1. **Multi-stage Builds**
   ```dockerfile
   # Use multi-stage builds to reduce image size
   FROM --platform=linux/arm64 python:3.12-slim as builder
   # ... build stage
   
   FROM --platform=linux/arm64 python:3.12-slim as runtime
   # ... runtime stage
   ```

2. **Layer Caching**
   ```dockerfile
   # Copy requirements first for better caching
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   # Copy application code last
   COPY . .
   ```

3. **Resource Limits**
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

### Application Optimization

1. **Connection Pooling**
   - Configure Redis connection pooling
   - Use HTTP connection pooling for MCP clients

2. **Caching Strategy**
   - Enable response caching
   - Configure appropriate TTL values

3. **Async Processing**
   - Use async/await for I/O operations
   - Implement connection pooling

### Monitoring Performance

```bash
# Monitor resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check application metrics
curl http://localhost:9090/metrics | grep -E "(response_time|request_count)"

# Load testing
./scripts/test_docker.sh load
```

## Security Considerations

### Container Security

1. **Non-root User**
   ```dockerfile
   # Create and use non-root user
   RUN useradd -m -u 1000 bedrock_agentcore
   USER bedrock_agentcore
   ```

2. **Read-only Filesystem**
   ```yaml
   security_opt:
     - no-new-privileges:true
   read_only: true
   tmpfs:
     - /tmp
     - /var/tmp
   ```

3. **Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ulimits:
     nofile: 65536
   ```

### Network Security

1. **Internal Networks**
   ```yaml
   networks:
     mbti-network:
       driver: bridge
       internal: true  # No external access
   ```

2. **Port Restrictions**
   - Only expose necessary ports
   - Use internal service discovery

3. **TLS/SSL**
   - Configure SSL certificates for production
   - Use HTTPS for all external communication

### Secrets Management

1. **Environment Variables**
   ```bash
   # Use Docker secrets for sensitive data
   echo "secret_value" | docker secret create my_secret -
   ```

2. **AWS Secrets Manager**
   ```python
   # Retrieve secrets from AWS Secrets Manager
   import boto3
   secrets_client = boto3.client('secretsmanager')
   ```

### Security Scanning

```bash
# Scan images for vulnerabilities
docker scout cves mbti-travel-assistant:latest

# Check for security issues
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image mbti-travel-assistant:latest
```

## Backup and Recovery

### Data Backup

```bash
# Backup Docker volumes
docker run --rm -v mbti-redis-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Backup application data
docker cp mbti-travel-assistant-mcp:/app/data ./backup/app-data
```

### Recovery Procedures

```bash
# Restore from backup
docker run --rm -v mbti-redis-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/redis-backup.tar.gz -C /data

# Restart services
docker-compose restart
```

## Maintenance

### Regular Maintenance Tasks

1. **Update Images**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **Clean Up**
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

3. **Log Rotation**
   ```bash
   # Configure log rotation in docker-compose.yml
   logging:
     driver: "json-file"
     options:
       max-size: "100m"
       max-file: "5"
   ```

### Monitoring Maintenance

- Monitor disk usage regularly
- Check log file sizes
- Review performance metrics
- Update security patches

## Support and Documentation

### Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [Project README](./README.md)

### Getting Help

1. Check container logs: `docker-compose logs [service]`
2. Review health check status: `./scripts/monitor_docker.sh`
3. Generate monitoring report: `./scripts/monitor_docker.sh report`
4. Check troubleshooting section above

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Platform**: linux/arm64 (required for AgentCore)