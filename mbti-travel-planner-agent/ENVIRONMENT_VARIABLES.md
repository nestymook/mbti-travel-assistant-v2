# Environment Variables Documentation

This document describes all environment variables used by the MBTI Travel Planner Agent with AgentCore Runtime Integration.

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

## AgentCore Runtime Configuration

### RESTAURANT_SEARCH_AGENT_ARN
- **Description**: ARN of the restaurant search AgentCore agent
- **Default**: Environment-specific
- **Required**: Yes
- **Examples**:
  - Development: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-dev`
  - Production: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j`

### RESTAURANT_REASONING_AGENT_ARN
- **Description**: ARN of the restaurant reasoning AgentCore agent
- **Default**: Environment-specific
- **Required**: Yes
- **Examples**:
  - Development: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_agent-dev`
  - Production: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE`

### AGENTCORE_REGION
- **Description**: AWS region for AgentCore Runtime API calls
- **Default**: `us-east-1`
- **Required**: No
- **Example**: `AGENTCORE_REGION=us-east-1`

### AGENTCORE_TIMEOUT
- **Description**: AgentCore agent invocation timeout in seconds
- **Default**: Environment-specific (30/45/60)
- **Required**: No
- **Example**: `AGENTCORE_TIMEOUT=60`

### AGENTCORE_MAX_RETRIES
- **Description**: Maximum number of retry attempts for failed agent calls
- **Default**: Environment-specific (2/3/3)
- **Required**: No
- **Example**: `AGENTCORE_MAX_RETRIES=3`

### AGENTCORE_CONNECTION_POOL_SIZE
- **Description**: Connection pool size for AgentCore Runtime client
- **Default**: Environment-specific (10/20/50)
- **Required**: No
- **Example**: `AGENTCORE_CONNECTION_POOL_SIZE=20`

### AGENTCORE_KEEP_ALIVE_TIMEOUT
- **Description**: Keep-alive timeout for AgentCore connections in seconds
- **Default**: Environment-specific (30/60/120)
- **Required**: No
- **Example**: `AGENTCORE_KEEP_ALIVE_TIMEOUT=60`

## Cognito Authentication Configuration

### COGNITO_USER_POOL_ID
- **Description**: Cognito User Pool ID for JWT authentication
- **Default**: `us-east-1_KePRX24Bn`
- **Required**: Yes
- **Example**: `COGNITO_USER_POOL_ID=us-east-1_KePRX24Bn`

### COGNITO_CLIENT_ID
- **Description**: Cognito App Client ID
- **Default**: `1ofgeckef3po4i3us4j1m4chvd`
- **Required**: Yes
- **Example**: `COGNITO_CLIENT_ID=1ofgeckef3po4i3us4j1m4chvd`

### COGNITO_CLIENT_SECRET
- **Description**: Cognito App Client Secret for authentication
- **Default**: None
- **Required**: Yes
- **Example**: `COGNITO_CLIENT_SECRET=t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9`

### COGNITO_REGION
- **Description**: AWS region for Cognito service
- **Default**: `us-east-1`
- **Required**: No
- **Example**: `COGNITO_REGION=us-east-1`

### COGNITO_DISCOVERY_URL
- **Description**: OIDC discovery URL for JWT validation
- **Default**: `https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration`
- **Required**: No
- **Example**: `COGNITO_DISCOVERY_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration`

### JWT_TOKEN_REFRESH_BUFFER
- **Description**: Buffer time in seconds before token expiry to refresh
- **Default**: `300` (5 minutes)
- **Required**: No
- **Example**: `JWT_TOKEN_REFRESH_BUFFER=300`

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

### ENABLE_RESPONSE_CACHING
- **Description**: Enable response caching for repeated queries
- **Default**: Environment-specific (false/true/true)
- **Required**: No
- **Example**: `ENABLE_RESPONSE_CACHING=true`

### RESPONSE_CACHE_TTL
- **Description**: Response cache time-to-live in seconds
- **Default**: `300` (5 minutes)
- **Required**: No
- **Example**: `RESPONSE_CACHE_TTL=300`

### ENABLE_PARALLEL_EXECUTION
- **Description**: Enable parallel execution for independent agent calls
- **Default**: Environment-specific (false/true/true)
- **Required**: No
- **Example**: `ENABLE_PARALLEL_EXECUTION=true`

### CONNECTION_POOL_MAX_SIZE
- **Description**: Maximum size of AgentCore connection pool
- **Default**: Environment-specific (10/20/50)
- **Required**: No
- **Example**: `CONNECTION_POOL_MAX_SIZE=20`

### CONNECTION_POOL_MAX_OVERFLOW
- **Description**: Maximum overflow connections beyond pool size
- **Default**: Environment-specific (5/10/25)
- **Required**: No
- **Example**: `CONNECTION_POOL_MAX_OVERFLOW=10`

## Circuit Breaker Configuration

### CIRCUIT_BREAKER_FAILURE_THRESHOLD
- **Description**: Number of failures before circuit breaker opens
- **Default**: `5`
- **Required**: No
- **Example**: `CIRCUIT_BREAKER_FAILURE_THRESHOLD=5`

### CIRCUIT_BREAKER_RECOVERY_TIMEOUT
- **Description**: Time in seconds before attempting to close circuit breaker
- **Default**: `60`
- **Required**: No
- **Example**: `CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60`

### CIRCUIT_BREAKER_EXPECTED_EXCEPTION
- **Description**: Exception type that triggers circuit breaker
- **Default**: `AgentInvocationError`
- **Required**: No
- **Example**: `CIRCUIT_BREAKER_EXPECTED_EXCEPTION=AgentInvocationError`

## Monitoring Configuration (Staging/Production Only)

### ENABLE_PERFORMANCE_MONITORING
- **Description**: Enable performance metrics collection
- **Default**: `false` (development), `true` (staging/production)
- **Required**: No
- **Example**: `ENABLE_PERFORMANCE_MONITORING=true`

### ENABLE_AGENTCORE_REQUEST_TRACING
- **Description**: Enable AgentCore API request tracing
- **Default**: `false` (development), `true` (staging/production)
- **Required**: No
- **Example**: `ENABLE_AGENTCORE_REQUEST_TRACING=true`

### ENABLE_JWT_DEBUG_LOGGING
- **Description**: Enable detailed JWT authentication logging
- **Default**: `false`
- **Required**: No
- **Example**: `ENABLE_JWT_DEBUG_LOGGING=true`

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

The agent supports three deployment environments, each with its own AgentCore configuration:

### Development Environment
- **File**: `config/environments/agentcore_development.env`
- **Agents**: Development AgentCore agents
- **Authentication**: Cognito JWT with development settings
- **Logging**: Debug level, human-readable format
- **Monitoring**: Basic health checks and connectivity tests
- **Performance**: Basic connection pooling

### Staging Environment
- **File**: `config/environments/agentcore_staging.env`
- **Agents**: Staging AgentCore agents
- **Authentication**: Full Cognito JWT authentication
- **Logging**: Info level, JSON format
- **Monitoring**: Performance monitoring and circuit breaker tracking
- **Performance**: Enhanced connection pooling and caching

### Production Environment
- **File**: `config/environments/agentcore_production.env`
- **Agents**: Production AgentCore agents (mN8bgq2Y1j, MSns5D6SLE)
- **Authentication**: Full Cognito JWT with automatic refresh
- **Logging**: Info level, JSON format, structured with correlation IDs
- **Monitoring**: Full monitoring, metrics collection, and observability
- **Performance**: Optimized connection pooling, caching, and parallel execution
- **Security**: Circuit breaker patterns and graceful fallback responses

## Configuration Loading Priority

The agent loads configuration in the following order (later values override earlier ones):

1. Default values in code
2. Environment-specific configuration file (`config/environments/agentcore_{ENVIRONMENT}.env`)
3. AgentCore configuration file (`config/agentcore_environment_config.py`)
4. Cognito configuration file (`config/cognito_config.json`)
5. Environment variables
6. Runtime configuration (if applicable)

## Example Configuration

### Development Setup
```bash
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export COGNITO_CLIENT_SECRET="your-dev-client-secret"
export ENABLE_JWT_DEBUG_LOGGING=true
export ENABLE_JSON_LOGGING=false
```

### Production Setup
```bash
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export COGNITO_CLIENT_SECRET="your-production-client-secret"
export ENABLE_PERFORMANCE_MONITORING=true
export ENABLE_METRICS_COLLECTION=true
export ENABLE_RESPONSE_CACHING=true
export ENABLE_PARALLEL_EXECUTION=true
```

## Validation

The agent validates all configuration on startup and will fail with clear error messages if:

- Required environment variables are missing (agent ARNs, Cognito settings)
- Configuration values are invalid (e.g., negative timeouts, invalid ARNs)
- AgentCore agents are unreachable or invalid
- Cognito authentication configuration is invalid
- JWT token refresh fails

## Migration from HTTP Gateway

When migrating from the previous HTTP gateway implementation, the following environment variables are **no longer needed**:

- `GATEWAY_BASE_URL`
- `GATEWAY_AUTH_TOKEN`
- `GATEWAY_TIMEOUT`
- `GATEWAY_MAX_RETRIES`
- `GATEWAY_AUTH_REQUIRED`
- `GATEWAY_CONNECTION_POOL_SIZE`
- `GATEWAY_KEEP_ALIVE_TIMEOUT`
- `GATEWAY_HEALTH_CHECK_ENDPOINT`

These have been replaced with the AgentCore Runtime configuration described above.

### New Required Variables for AgentCore Integration

- `RESTAURANT_SEARCH_AGENT_ARN`
- `RESTAURANT_REASONING_AGENT_ARN`
- `COGNITO_CLIENT_SECRET`

### Enhanced Variables for Better Performance

- `ENABLE_RESPONSE_CACHING`
- `ENABLE_PARALLEL_EXECUTION`
- `CIRCUIT_BREAKER_FAILURE_THRESHOLD`
- `ENABLE_AGENTCORE_REQUEST_TRACING`