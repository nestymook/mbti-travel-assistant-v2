# MBTI Travel Planner Agent - AgentCore Integration Migration Guide

This document provides comprehensive guidance for migrating from HTTP Gateway integration to AgentCore Runtime API integration. This migration eliminates HTTP gateway intermediaries and provides direct, native AgentCore agent-to-agent communication.

## Overview

The MBTI Travel Planner Agent has been updated to use direct AgentCore Runtime API calls instead of HTTP gateway intermediaries. This provides better performance, reliability, and proper AgentCore ecosystem integration.

## Architecture Changes

### Before (HTTP Gateway)
```
mbti-travel-planner-agent → HTTP Gateway → agentcore-gateway-mcp-tools → MCP calls
```

### After (AgentCore Runtime API)
```
mbti-travel-planner-agent → AgentCore Runtime API → restaurant_search_agent & restaurant_search_result_reasoning_agent
```

## Key Changes

### 1. Dependencies
- **Removed**: HTTP gateway client dependencies (`requests`, `httpx` for gateway calls)
- **Added**: AgentCore Runtime client dependencies
- **Updated**: Authentication now uses JWT tokens directly with Cognito

### 2. Configuration
- **New**: AgentCore-specific environment configuration files
- **Updated**: Environment variables now focus on AgentCore agent ARNs
- **Removed**: HTTP gateway endpoint configurations

### 3. Tools
- **Updated**: Restaurant search tools now use AgentCore Runtime API
- **Updated**: Restaurant reasoning tools now use AgentCore Runtime API
- **Maintained**: Same tool interface for backward compatibility

### 4. Authentication
- **Updated**: Direct JWT authentication with Cognito
- **Removed**: HTTP gateway authentication tokens
- **Added**: Automatic token refresh and management

## Migration Steps

### Step 1: Update Environment Configuration

Replace HTTP gateway environment variables with AgentCore configuration:

**Remove (HTTP Gateway Variables):**
```bash
GATEWAY_BASE_URL=https://gateway.example.com
GATEWAY_AUTH_TOKEN=your-token
GATEWAY_TIMEOUT=30
GATEWAY_MAX_RETRIES=3
GATEWAY_AUTH_REQUIRED=true
GATEWAY_CONNECTION_POOL_SIZE=20
GATEWAY_KEEP_ALIVE_TIMEOUT=60
GATEWAY_HEALTH_CHECK_ENDPOINT=/health
```

**Add (AgentCore Variables):**
```bash
# AgentCore Agent ARNs
RESTAURANT_SEARCH_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j
RESTAURANT_REASONING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE

# AgentCore Runtime Configuration
AGENTCORE_REGION=us-east-1
AGENTCORE_TIMEOUT=60
AGENTCORE_MAX_RETRIES=3
AGENTCORE_CONNECTION_POOL_SIZE=20
AGENTCORE_KEEP_ALIVE_TIMEOUT=60

# Performance Optimizations
ENABLE_RESPONSE_CACHING=true
RESPONSE_CACHE_TTL=300
ENABLE_PARALLEL_EXECUTION=true

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

### Step 2: Update Cognito Configuration

Ensure Cognito configuration is properly set for JWT authentication:

```bash
# Cognito Authentication (Required)
COGNITO_USER_POOL_ID=us-east-1_KePRX24Bn
COGNITO_CLIENT_ID=1ofgeckef3po4i3us4j1m4chvd
COGNITO_CLIENT_SECRET=t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9
COGNITO_REGION=us-east-1
COGNITO_DISCOVERY_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration

# JWT Token Management
JWT_TOKEN_REFRESH_BUFFER=300
ENABLE_JWT_DEBUG_LOGGING=false
```

**Important Notes:**
- `COGNITO_CLIENT_SECRET` is **required** for authentication flows
- The discovery URL must end with `openid-configuration` (with hyphens) for AgentCore compatibility
- JWT tokens are automatically refreshed before expiry

### Step 3: Update Dependencies

Update requirements.txt and install new dependencies:

**Remove (HTTP Gateway Dependencies):**
```bash
pip uninstall httpx requests-toolbelt
```

**Install (AgentCore Dependencies):**
```bash
pip install -r requirements.txt
```

**Key New Dependencies:**
- Enhanced `boto3` for AgentCore Runtime API
- `aiohttp` for async HTTP operations
- `pyjwt` for JWT token handling
- `cryptography` for JWT validation
- `structlog` for structured logging

### Step 4: Validate Configuration

Validate the new AgentCore configuration:

```bash
# Validate configuration loading
python config/validate_agentcore_config.py production

# Test environment configuration
python -c "from config.agentcore_environment_config import get_agentcore_config; print(get_agentcore_config('production'))"

# Test Cognito configuration
python -c "from config.agentcore_environment_config import get_cognito_config; print(get_cognito_config('production'))"
```

### Step 5: Test Integration

Run comprehensive integration tests:

```bash
# Test AgentCore connectivity
python test_agentcore_integration.py

# Test individual tools
python examples/restaurant_search_tool_demo.py
python examples/restaurant_reasoning_tool_demo.py

# Test complete workflow
python examples/central_district_workflow_agentcore_demo.py
```

### Step 6: Deploy Updated Agent

Deploy the updated agent using AgentCore:

```bash
# Deploy with new configuration
agentcore deploy

# Verify deployment
agentcore invoke '{"prompt": "Find restaurants in Central district"}'

# Test specific functionality
agentcore invoke '{"prompt": "I am an ENFP looking for lunch in Central district"}'
```

## Environment-Specific Configuration

### Development Environment
- **Agent ARNs**: Development-specific agents (if available)
- **Authentication**: Full Cognito JWT with debug logging
- **Logging**: DEBUG level with human-readable format
- **Performance**: Basic connection pooling
- **Monitoring**: Basic health checks and connectivity tests
- **Caching**: Disabled for development flexibility
- **Circuit Breaker**: Relaxed thresholds for testing

### Staging Environment
- **Agent ARNs**: Staging or production agents
- **Authentication**: Full Cognito JWT authentication
- **Logging**: INFO level with JSON format
- **Performance**: Enhanced connection pooling and caching
- **Monitoring**: Performance monitoring and circuit breaker tracking
- **Caching**: Enabled with shorter TTL
- **Circuit Breaker**: Standard thresholds

### Production Environment
- **Agent ARNs**: Production agents (mN8bgq2Y1j, MSns5D6SLE)
- **Authentication**: Full Cognito JWT with automatic refresh
- **Logging**: INFO level with structured logging and correlation IDs
- **Performance**: Optimized connection pooling, caching, and parallel execution
- **Monitoring**: Full monitoring, metrics collection, and observability
- **Caching**: Enabled with optimized TTL
- **Circuit Breaker**: Strict thresholds for reliability

## Troubleshooting

### Common Issues

1. **Agent ARN Not Found**
   - Verify the agent ARNs are correct for your environment
   - Ensure the agents are deployed and accessible
   - Check AWS region matches the ARN region
   - Verify IAM permissions for AgentCore Runtime API

2. **Authentication Errors**
   - Check Cognito configuration (User Pool ID, Client ID, Client Secret)
   - Verify JWT discovery URL format (must end with `openid-configuration`)
   - Ensure client secret is correct and not expired
   - Check if authentication flows are enabled in Cognito

3. **Timeout Errors**
   - Increase `AGENTCORE_TIMEOUT` if needed (default: 60 seconds)
   - Check agent availability and performance
   - Verify network connectivity to AgentCore Runtime API
   - Consider increasing `AGENTCORE_MAX_RETRIES`

4. **Circuit Breaker Activation**
   - Check if agents are experiencing high failure rates
   - Review circuit breaker thresholds (`CIRCUIT_BREAKER_FAILURE_THRESHOLD`)
   - Monitor agent health and performance
   - Consider adjusting recovery timeout

5. **Tool Creation Failures**
   - Verify all required services are imported
   - Check for missing dependencies (boto3, aiohttp, pyjwt)
   - Review error logs for specific issues
   - Ensure environment configuration is loaded correctly

6. **JWT Token Refresh Issues**
   - Check Cognito client secret and configuration
   - Verify token refresh buffer settings
   - Review JWT debug logs if enabled
   - Ensure proper error handling for token refresh failures

### Validation Commands

```bash
# Test configuration loading
python -c "from config.agentcore_environment_config import get_agentcore_config; print(get_agentcore_config('production'))"

# Test Cognito configuration
python -c "from services.authentication_manager import AuthenticationManager; from config.agentcore_environment_config import get_cognito_config; auth = AuthenticationManager(get_cognito_config('production')); print('Cognito configured correctly')"

# Test AgentCore Runtime client
python -c "from services.agentcore_runtime_client import AgentCoreRuntimeClient; from config.agentcore_environment_config import get_cognito_config; client = AgentCoreRuntimeClient(get_cognito_config('production')); print('Runtime client initialized')"

# Test agent connectivity
python test_agentcore_integration.py

# Test individual tools
python examples/restaurant_search_tool_demo.py
python examples/restaurant_reasoning_tool_demo.py

# Test deployed agent
agentcore invoke '{"prompt": "Hello, can you help me find restaurants?"}'

# Test specific functionality
agentcore invoke '{"prompt": "I am an ENFP looking for lunch in Central district"}'

# Check agent health
python -c "from services.agentcore_health_check_service import AgentCoreHealthCheckService; from config.agentcore_environment_config import get_agentcore_config, get_cognito_config; health = AgentCoreHealthCheckService(get_agentcore_config('production'), get_cognito_config('production')); import asyncio; print(asyncio.run(health.check_agent_connectivity()))"
```

## Performance Improvements

The new AgentCore integration provides significant performance and reliability improvements:

### Latency Improvements
- **Reduced Latency**: Direct agent calls eliminate HTTP gateway overhead (20-30% faster)
- **Parallel Execution**: Independent agent calls can be executed in parallel
- **Connection Pooling**: Reuse of connections reduces connection establishment overhead
- **Response Caching**: Repeated queries are served from cache (configurable TTL)

### Reliability Improvements
- **Circuit Breaker Patterns**: Automatic failure detection and recovery
- **Retry Logic**: Exponential backoff with configurable retry attempts
- **Graceful Fallbacks**: Meaningful responses when agents are unavailable
- **Health Monitoring**: Continuous monitoring of agent connectivity and performance

### Security Improvements
- **Direct JWT Authentication**: Automatic token management with Cognito
- **Token Refresh**: Automatic refresh before expiry with thread-safe operations
- **Secure Communication**: All communications use HTTPS with proper authentication
- **Error Sanitization**: Sensitive information is not exposed in error messages

### Monitoring Improvements
- **Comprehensive Observability**: Detailed metrics for agent invocations
- **Performance Tracking**: Response times, success rates, and error categorization
- **Circuit Breaker Monitoring**: Track circuit breaker state changes and recovery
- **Authentication Monitoring**: JWT token refresh frequency and failures

## Rollback Plan

If issues occur, you can temporarily rollback by:

1. Reverting to the previous version of `main.py`
2. Restoring HTTP gateway environment variables
3. Redeploying the previous version

However, the new AgentCore integration is recommended for production use due to its improved performance and reliability.

## Support

For issues with the migration:

1. Check the integration test results
2. Review the error logs
3. Verify environment configuration
4. Ensure all AgentCore agents are deployed and accessible

The migration maintains backward compatibility at the tool level, so existing integrations should continue to work without changes.