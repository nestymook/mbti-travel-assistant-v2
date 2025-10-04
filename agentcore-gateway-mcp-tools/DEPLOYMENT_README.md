# AgentCore Gateway MCP Tools - Deployment Guide

This document provides comprehensive guidance for deploying the AgentCore Gateway for MCP Tools to Amazon Bedrock AgentCore Runtime.

## Overview

The AgentCore Gateway exposes existing restaurant search and reasoning MCP tools through RESTful HTTP endpoints with JWT authentication, providing a unified API interface for external clients.

## Prerequisites

### Required Software
- Docker (for ARM64 container building)
- Python 3.10+
- AWS CLI configured with appropriate credentials
- bedrock-agentcore CLI tool

### Required AWS Permissions
- `AmazonBedrockFullAccess`
- `AmazonECRFullAccess`
- `AmazonCloudWatchFullAccess`
- `IAMFullAccess` (for role creation)

### Required AWS Resources
- Cognito User Pool: `us-east-1_KePRX24Bn`
- Cognito Client ID: `1ofgeckef3po4i3us4j1m4chvd`
- Existing MCP servers (restaurant-search-mcp, restaurant-reasoning-mcp)

## Configuration Files

### 1. .bedrock_agentcore.yaml

Main AgentCore configuration file with:
- **Platform**: `linux/arm64` (required for AgentCore Runtime)
- **JWT Authentication**: Using existing Cognito User Pool
- **Environment Variables**: MCP server endpoints and configuration
- **Observability**: Enabled with CloudWatch integration

Key configuration sections:
```yaml
platform: linux/arm64
authorizer_configuration:
  customJWTAuthorizer:
    discoveryUrl: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
    allowedClients:
    - 1ofgeckef3po4i3us4j1m4chvd
environment_variables:
  RESTAURANT_SEARCH_MCP_URL: "http://restaurant-search-mcp:8080"
  RESTAURANT_REASONING_MCP_URL: "http://restaurant-reasoning-mcp:8080"
```

### 2. cognito_config.json

Cognito authentication configuration copied from existing services to ensure consistency:
- User Pool ID: `us-east-1_KePRX24Bn`
- Client ID: `1ofgeckef3po4i3us4j1m4chvd`
- Discovery URL for JWT validation

### 3. Dockerfile

ARM64 container configuration:
- **Base Image**: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- **Platform**: `linux/arm64` (required)
- **Security**: Non-root user execution
- **Observability**: OpenTelemetry instrumentation
- **Health Check**: HTTP health endpoint

## Deployment Process

### Step 1: Validate Configuration

```bash
# Validate all configuration files
python scripts/validate_deployment_config.py

# Validate deployment configuration only
python scripts/deploy_agentcore.py --validate-only
```

### Step 2: Deploy to AgentCore

```bash
# Full deployment with container build
python scripts/deploy_agentcore.py

# Skip container build (use existing image)
python scripts/deploy_agentcore.py --skip-container-build

# Verbose output for debugging
python scripts/deploy_agentcore.py --verbose
```

### Step 3: Verify Deployment

The deployment script automatically:
1. Validates configuration files
2. Creates/verifies ECR repository
3. Builds ARM64 container
4. Pushes container to ECR
5. Deploys to AgentCore Runtime
6. Sets up CloudWatch monitoring
7. Verifies deployment health

## Environment Variables

The following environment variables are configured in the AgentCore deployment:

### MCP Server Configuration
- `RESTAURANT_SEARCH_MCP_URL`: Restaurant search MCP server endpoint
- `RESTAURANT_REASONING_MCP_URL`: Restaurant reasoning MCP server endpoint
- `MCP_TIMEOUT`: MCP client timeout (default: 30 seconds)
- `MCP_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `MCP_RETRY_DELAY`: Retry delay in seconds (default: 1)

### Authentication Configuration
- `COGNITO_USER_POOL_ID`: Cognito User Pool ID
- `COGNITO_CLIENT_ID`: Cognito Client ID
- `COGNITO_REGION`: AWS region for Cognito
- `COGNITO_DISCOVERY_URL`: JWT discovery URL

### Gateway Configuration
- `GATEWAY_PORT`: Gateway server port (default: 8080)
- `GATEWAY_HOST`: Gateway server host (default: 0.0.0.0)
- `LOG_LEVEL`: Logging level (default: INFO)
- `BYPASS_AUTH_PATHS`: Paths that bypass authentication
- `REQUIRE_AUTHENTICATION`: Enable/disable authentication (default: true)

### Observability Configuration
- `ENABLE_METRICS`: Enable metrics collection (default: true)
- `ENABLE_TRACING`: Enable distributed tracing (default: true)
- `METRICS_PORT`: Metrics server port (default: 8081)

### AWS Configuration
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_DEFAULT_REGION`: Default AWS region
- `DOCKER_CONTAINER`: Container environment flag

## Monitoring and Observability

### CloudWatch Dashboard
The deployment creates a CloudWatch dashboard with:
- Gateway invocation metrics
- Error rates and response times
- MCP tool call metrics
- Authentication failure metrics
- Application logs

### CloudWatch Alarms
Automatic alarms for:
- High error rates (>10 errors in 10 minutes)
- MCP connection failures (>5 failures in 10 minutes)
- Authentication failures (>20 failures in 10 minutes)

### Health Checks
- HTTP health endpoint: `/health`
- Container health check every 30 seconds
- MCP server connectivity verification

## API Endpoints

Once deployed, the Gateway exposes the following endpoints:

### Restaurant Search Endpoints
- `POST /api/v1/restaurants/search/district`
- `POST /api/v1/restaurants/search/meal-type`
- `POST /api/v1/restaurants/search/combined`

### Restaurant Reasoning Endpoints
- `POST /api/v1/restaurants/recommend`
- `POST /api/v1/restaurants/analyze`

### System Endpoints
- `GET /health` - Health check (no authentication required)
- `GET /metrics` - Metrics endpoint (no authentication required)
- `GET /tools/metadata` - Tool metadata for foundation models
- `GET /docs` - OpenAPI documentation

## Authentication

All API endpoints (except system endpoints) require JWT authentication:

### Request Headers
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### JWT Token Requirements
- Valid JWT token from Cognito User Pool `us-east-1_KePRX24Bn`
- Client ID must be `1ofgeckef3po4i3us4j1m4chvd`
- Token must not be expired
- Token signature must be valid

### Bypass Paths
The following paths bypass authentication:
- `/health`
- `/metrics`
- `/docs`
- `/openapi.json`
- `/tools/metadata`

## Troubleshooting

### Common Issues

#### 1. Container Build Failures
```bash
# Check Docker is available and supports ARM64
docker --version
docker buildx ls

# Verify platform specification in Dockerfile
grep "platform=linux/arm64" Dockerfile
```

#### 2. Authentication Issues
```bash
# Verify Cognito configuration
python -c "import json; print(json.load(open('cognito_config.json')))"

# Test JWT discovery URL
curl https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
```

#### 3. MCP Server Connectivity
```bash
# Check MCP server endpoints are accessible
curl http://restaurant-search-mcp:8080/health
curl http://restaurant-reasoning-mcp:8080/health
```

#### 4. Deployment Failures
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify required permissions
aws iam list-attached-user-policies --user-name $(aws sts get-caller-identity --query 'Arn' --output text | cut -d'/' -f2)

# Check AgentCore CLI
agentcore --version
```

### Log Analysis

#### CloudWatch Logs
```bash
# View AgentCore logs
aws logs describe-log-groups --log-group-name-prefix "/aws/bedrock-agentcore"

# Stream logs
aws logs tail /aws/bedrock-agentcore/agentcore-gateway-mcp-tools --follow
```

#### Container Logs
```bash
# View container logs during build
docker logs <container_id>

# Check container health
docker inspect <container_id> | grep Health
```

## Security Considerations

### Container Security
- Runs as non-root user (`agentcore_gateway`)
- Minimal base image with security updates
- No sensitive data in container layers

### Network Security
- Public network mode for external access
- HTTPS termination at AgentCore Runtime
- JWT authentication for all API endpoints

### Data Protection
- No persistent data storage in container
- JWT tokens validated against Cognito
- Audit logging for all authentication events

## Performance Optimization

### Resource Allocation
- CPU: 1 vCPU (configurable)
- Memory: 2 GB (configurable)
- Auto-scaling based on demand

### Caching
- JWT token validation caching
- MCP client connection pooling
- Response caching for metadata endpoints

### Monitoring
- Request/response time tracking
- MCP tool call latency monitoring
- Resource utilization metrics

## Maintenance

### Updates
1. Update container image
2. Push to ECR
3. Update AgentCore deployment
4. Verify health checks

### Backup
- Configuration files in version control
- CloudWatch logs retention (30 days)
- Metrics data retention (15 months)

### Scaling
- Automatic scaling based on request volume
- Manual scaling through AgentCore configuration
- Load balancing across multiple instances

## Support

For issues and questions:
1. Check CloudWatch logs and metrics
2. Verify configuration with validation script
3. Test individual components (MCP servers, authentication)
4. Review deployment logs and error messages

## Next Steps

After successful deployment:
1. Test all API endpoints with authentication
2. Monitor CloudWatch dashboard and alarms
3. Integrate with client applications
4. Set up automated testing and monitoring
5. Configure backup and disaster recovery procedures