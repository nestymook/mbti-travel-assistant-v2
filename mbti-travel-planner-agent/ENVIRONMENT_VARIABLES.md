# Environment Variables Documentation

This document describes all environment variables used by the MBTI Travel Planner Agent with HTTP Gateway Integration.

## Core Application Settings

### ENVIRONMENT
- **Description**: Deployment environment (development, staging, production)
- **Default**: `production`
- **Required**: No
- **Example**: `ENVIRONMENT=development`

### AWS_REGION
- **Description**: AWS region for all services
- **Default**: `us-east-1`
- **Required**: Yes
- **Example**: `AWS_REGION=us-east-1`

## Gateway HTTP Client Configuration

### GATEWAY_BASE_URL
- **Description**: Base URL for the agentcore-gateway-mcp-tools service
- **Default**: Environment-specific (see gateway.json)
- **Required**: No (uses environment defaults)
- **Examples**:
  - Development: `http://localhost:8080`
  - Staging: `https://agentcore-gateway-mcp-tools-staging.bedrock-agentcore.us-east-1.amazonaws.com`
  - Production: `https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com`

### GATEWAY_TIMEOUT
- **Description**: HTTP request timeout in seconds
- **Default**: Environment-specific (30/45/60)
- **Required**: No
- **Example**: `GATEWAY_TIMEOUT=60`

### GATEWAY_MAX_RETRIES
- **Description**: Maximum number of retry attempts for failed requests
- **Default**: Environment-specific (2/3/3)
- **Required**: No
- **Example**: `GATEWAY_MAX_RETRIES=3`

### GATEWAY_AUTH_REQUIRED
- **Description**: Whether gateway authentication is required
- **Default**: Environment-specific (false/true/true)
- **Required**: No
- **Example**: `GATEWAY_AUTH_REQUIRED=true`

### GATEWAY_AUTH_TOKEN
- **Description**: Authentication token for gateway requests (if required)
- **Default**: None
- **Required**: Only if GATEWAY_AUTH_REQUIRED=true
- **Example**: `GATEWAY_AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### GATEWAY_CONNECTION_POOL_SIZE
- **Description**: HTTP connection pool size for gateway client
- **Default**: Environment-specific (10/20/50)
- **Required**: No
- **Example**: `GATEWAY_CONNECTION_POOL_SIZE=20`

### GATEWAY_KEEP_ALIVE_TIMEOUT
- **Description**: Keep-alive timeout for HTTP connections in seconds
- **Default**: Environment-specific (30/60/120)
- **Required**: No
- **Example**: `GATEWAY_KEEP_ALIVE_TIMEOUT=60`

### GATEWAY_HEALTH_CHECK_ENDPOINT
- **Description**: Health check endpoint path on gateway service
- **Default**: `/health`
- **Required**: No
- **Example**: `GATEWAY_HEALTH_CHECK_ENDPOINT=/health`

## Agent Model Configuration

### AGENT_MODEL
- **Description**: Amazon Bedrock foundation model to use
- **Default**: `amazon.nova-pro-v1:0`
- **Required**: No
- **Example**: `AGENT_MODEL=amazon.nova-pro-v1:0`

### AGENT_TEMPERATURE
- **Description**: Model temperature for response generation (0.0-1.0)
- **Default**: `0.1`
- **Required**: No
- **Example**: `AGENT_TEMPERATURE=0.1`

### AGENT_MAX_TOKENS
- **Description**: Maximum tokens for model responses
- **Default**: `2048`
- **Required**: No
- **Example**: `AGENT_MAX_TOKENS=2048`

### AGENT_TIMEOUT
- **Description**: Agent processing timeout in seconds
- **Default**: `60`
- **Required**: No
- **Example**: `AGENT_TIMEOUT=60`

## Logging Configuration

### LOG_LEVEL
- **Description**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Default**: `INFO`
- **Required**: No
- **Example**: `LOG_LEVEL=DEBUG`

### LOG_DIR
- **Description**: Directory for log files
- **Default**: `./logs`
- **Required**: No
- **Example**: `LOG_DIR=/var/log/mbti-agent`

### ENABLE_FILE_LOGGING
- **Description**: Enable logging to files
- **Default**: `true`
- **Required**: No
- **Example**: `ENABLE_FILE_LOGGING=true`

### ENABLE_JSON_LOGGING
- **Description**: Enable JSON-formatted logging
- **Default**: Environment-specific (false/true/true)
- **Required**: No
- **Example**: `ENABLE_JSON_LOGGING=true`

### ENABLE_STRUCTURED_LOGGING
- **Description**: Enable structured logging with additional context
- **Default**: `true`
- **Required**: No
- **Example**: `ENABLE_STRUCTURED_LOGGING=true`

## Health Check Configuration

### HEALTH_CHECK_INTERVAL
- **Description**: Health check interval in seconds
- **Default**: Environment-specific (300/300/180)
- **Required**: No
- **Example**: `HEALTH_CHECK_INTERVAL=300`

### ENABLE_BACKGROUND_HEALTH_CHECKS
- **Description**: Enable background health monitoring
- **Default**: `true`
- **Required**: No
- **Example**: `ENABLE_BACKGROUND_HEALTH_CHECKS=true`

## Performance Configuration

### HTTP_CLIENT_POOL_CONNECTIONS
- **Description**: Number of connection pools for HTTP client
- **Default**: Environment-specific (10/20/50)
- **Required**: No
- **Example**: `HTTP_CLIENT_POOL_CONNECTIONS=20`

### HTTP_CLIENT_POOL_MAXSIZE
- **Description**: Maximum size of each connection pool
- **Default**: Environment-specific (10/20/50)
- **Required**: No
- **Example**: `HTTP_CLIENT_POOL_MAXSIZE=20`

### HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS
- **Description**: Maximum keep-alive connections
- **Default**: Environment-specific (5/10/25)
- **Required**: No
- **Example**: `HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS=10`

## Monitoring Configuration (Staging/Production Only)

### ENABLE_PERFORMANCE_MONITORING
- **Description**: Enable performance metrics collection
- **Default**: `false` (development), `true` (staging/production)
- **Required**: No
- **Example**: `ENABLE_PERFORMANCE_MONITORING=true`

### ENABLE_REQUEST_TRACING
- **Description**: Enable HTTP request tracing
- **Default**: `false` (development), `true` (staging/production)
- **Required**: No
- **Example**: `ENABLE_REQUEST_TRACING=true`

### ENABLE_METRICS_COLLECTION
- **Description**: Enable comprehensive metrics collection
- **Default**: `false` (development/staging), `true` (production)
- **Required**: No
- **Example**: `ENABLE_METRICS_COLLECTION=true`

## Security Configuration (Production Only)

### ENABLE_REQUEST_VALIDATION
- **Description**: Enable strict request validation
- **Default**: `false` (development/staging), `true` (production)
- **Required**: No
- **Example**: `ENABLE_REQUEST_VALIDATION=true`

### ENABLE_RESPONSE_VALIDATION
- **Description**: Enable strict response validation
- **Default**: `false` (development/staging), `true` (production)
- **Required**: No
- **Example**: `ENABLE_RESPONSE_VALIDATION=true`

## Environment-Specific Configuration Files

The agent supports three deployment environments, each with its own configuration:

### Development Environment
- **File**: `config/environments/development.env`
- **Gateway**: Local development server (http://localhost:8080)
- **Authentication**: Disabled
- **Logging**: Debug level, human-readable format
- **Monitoring**: Basic health checks only

### Staging Environment
- **File**: `config/environments/staging.env`
- **Gateway**: Staging deployment on AgentCore
- **Authentication**: JWT required
- **Logging**: Info level, JSON format
- **Monitoring**: Performance monitoring enabled

### Production Environment
- **File**: `config/environments/production.env`
- **Gateway**: Production deployment on AgentCore
- **Authentication**: JWT required
- **Logging**: Info level, JSON format, structured
- **Monitoring**: Full monitoring and metrics collection
- **Security**: Request/response validation enabled

## Configuration Loading Priority

The agent loads configuration in the following order (later values override earlier ones):

1. Default values in code
2. Environment-specific configuration file (`config/environments/{ENVIRONMENT}.env`)
3. Gateway configuration file (`config/environments/gateway.json`)
4. Environment variables
5. Runtime configuration (if applicable)

## Example Configuration

### Development Setup
```bash
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export GATEWAY_TIMEOUT=30
export ENABLE_JSON_LOGGING=false
```

### Production Setup
```bash
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export GATEWAY_AUTH_TOKEN="your-jwt-token-here"
export ENABLE_PERFORMANCE_MONITORING=true
export ENABLE_METRICS_COLLECTION=true
```

## Validation

The agent validates all configuration on startup and will fail with clear error messages if:

- Required environment variables are missing
- Configuration values are invalid (e.g., negative timeouts)
- Gateway endpoints are unreachable
- Authentication tokens are invalid (if required)

## Migration from MCP Client

When migrating from the previous MCP client implementation, the following environment variables are **no longer needed**:

- `MCP_SERVER_URL`
- `MCP_AUTH_TOKEN`
- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`
- `COGNITO_CLIENT_SECRET`
- `JWT_DISCOVERY_URL`

These have been replaced with the simpler HTTP gateway configuration described above.