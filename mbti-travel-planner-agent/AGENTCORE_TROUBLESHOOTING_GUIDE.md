# AgentCore Integration Troubleshooting Guide

This guide provides comprehensive troubleshooting information for the MBTI Travel Planner Agent's AgentCore Runtime integration.

## Quick Diagnostics

### Health Check Commands

Run these commands to quickly diagnose common issues:

```bash
# 1. Test configuration loading
python config/validate_agentcore_config.py production

# 2. Test AgentCore connectivity
python test_agentcore_integration.py

# 3. Test individual components
python examples/agentcore_client_demo.py
python examples/restaurant_search_tool_demo.py
python examples/restaurant_reasoning_tool_demo.py

# 4. Check deployed agent
agentcore invoke '{"prompt": "test connectivity"}'
```

### Environment Validation

```bash
# Check required environment variables
echo "Environment: $ENVIRONMENT"
echo "Search Agent ARN: $RESTAURANT_SEARCH_AGENT_ARN"
echo "Reasoning Agent ARN: $RESTAURANT_REASONING_AGENT_ARN"
echo "Cognito User Pool: $COGNITO_USER_POOL_ID"
echo "Cognito Client ID: $COGNITO_CLIENT_ID"
echo "Client Secret Set: $([ -n "$COGNITO_CLIENT_SECRET" ] && echo "Yes" || echo "No")"
```

## Common Issues and Solutions

### 1. Agent ARN Not Found

**Symptoms:**
- `AgentNotFoundException` errors
- "Agent not found" messages
- HTTP 404 responses from AgentCore Runtime API

**Causes:**
- Incorrect agent ARN
- Agent not deployed or deleted
- Wrong AWS region
- Insufficient IAM permissions

**Solutions:**

1. **Verify Agent ARNs:**
   ```bash
   # List available agents
   aws bedrock-agentcore list-agent-runtimes --region us-east-1
   
   # Check specific agent
   aws bedrock-agentcore get-agent-runtime \
     --agent-runtime-id restaurant_search_agent-mN8bgq2Y1j \
     --region us-east-1
   ```

2. **Check Environment Configuration:**
   ```bash
   python -c "
   from config.agentcore_environment_config import get_agentcore_config
   config = get_agentcore_config('production')
   print(f'Search Agent: {config.restaurant_search_agent_arn}')
   print(f'Reasoning Agent: {config.restaurant_reasoning_agent_arn}')
   "
   ```

3. **Verify IAM Permissions:**
   ```bash
   # Test AgentCore permissions
   aws bedrock-agentcore list-agent-runtimes --region us-east-1
   
   # Check current identity
   aws sts get-caller-identity
   ```

### 2. Authentication Errors

**Symptoms:**
- `AuthenticationError` exceptions
- "Invalid JWT token" messages
- HTTP 401/403 responses
- Token refresh failures

**Causes:**
- Invalid Cognito configuration
- Expired or malformed client secret
- Incorrect discovery URL format
- Missing authentication flows in Cognito

**Solutions:**

1. **Verify Cognito Configuration:**
   ```bash
   # Test Cognito configuration
   python -c "
   from config.agentcore_environment_config import get_cognito_config
   config = get_cognito_config('production')
   print(f'User Pool: {config.user_pool_id}')
   print(f'Client ID: {config.client_id}')
   print(f'Discovery URL: {config.discovery_url}')
   "
   ```

2. **Test JWT Token Generation:**
   ```bash
   python -c "
   from services.authentication_manager import AuthenticationManager
   from config.agentcore_environment_config import get_cognito_config
   import asyncio
   
   async def test_auth():
       auth = AuthenticationManager(get_cognito_config('production'))
       try:
           token = await auth.get_valid_token()
           print('JWT token generated successfully')
           print(f'Token length: {len(token)}')
       except Exception as e:
           print(f'Authentication failed: {e}')
   
   asyncio.run(test_auth())
   "
   ```

3. **Verify Discovery URL Format:**
   ```bash
   # Test discovery URL (must end with openid-configuration)
   curl -s "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration" | jq .
   ```

4. **Check Cognito App Client Settings:**
   ```bash
   # Verify authentication flows are enabled
   aws cognito-idp describe-user-pool-client \
     --user-pool-id us-east-1_KePRX24Bn \
     --client-id 1ofgeckef3po4i3us4j1m4chvd \
     --region us-east-1 \
     --query 'UserPoolClient.ExplicitAuthFlows'
   ```

### 3. Timeout Errors

**Symptoms:**
- `TimeoutError` exceptions
- "Request timed out" messages
- Slow response times
- Agent invocation failures

**Causes:**
- Network connectivity issues
- Agent performance problems
- Insufficient timeout settings
- High agent load

**Solutions:**

1. **Increase Timeout Settings:**
   ```bash
   export AGENTCORE_TIMEOUT=120
   export AGENTCORE_MAX_RETRIES=5
   ```

2. **Test Network Connectivity:**
   ```bash
   # Test AWS connectivity
   aws bedrock-agentcore list-agent-runtimes --region us-east-1
   
   # Test with curl (if applicable)
   curl -w "@curl-format.txt" -o /dev/null -s "https://bedrock-agentcore.us-east-1.amazonaws.com"
   ```

3. **Monitor Agent Performance:**
   ```bash
   python -c "
   from services.agentcore_monitoring_service import AgentCoreMonitoringService
   import asyncio
   
   async def test_performance():
       monitor = AgentCoreMonitoringService()
       metrics = await monitor.get_agent_performance_metrics()
       print(f'Average response time: {metrics.get(\"avg_response_time\", \"N/A\")}ms')
   
   asyncio.run(test_performance())
   "
   ```

### 4. Circuit Breaker Activation

**Symptoms:**
- "Circuit breaker is open" messages
- Immediate failures without retries
- Fallback responses being returned
- High error rates

**Causes:**
- High failure rate from agents
- Network issues
- Agent unavailability
- Incorrect circuit breaker thresholds

**Solutions:**

1. **Check Circuit Breaker Status:**
   ```bash
   python -c "
   from services.agentcore_error_handler import AgentCoreErrorHandler
   handler = AgentCoreErrorHandler('test')
   print(f'Circuit breaker state: {handler.circuit_breaker.state}')
   print(f'Failure count: {handler.circuit_breaker.failure_count}')
   "
   ```

2. **Adjust Circuit Breaker Settings:**
   ```bash
   export CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
   export CIRCUIT_BREAKER_RECOVERY_TIMEOUT=120
   ```

3. **Reset Circuit Breaker:**
   ```bash
   python -c "
   from services.agentcore_error_handler import AgentCoreErrorHandler
   handler = AgentCoreErrorHandler('test')
   handler.circuit_breaker.reset()
   print('Circuit breaker reset')
   "
   ```

### 5. Configuration Loading Issues

**Symptoms:**
- `ConfigurationError` exceptions
- "Configuration not found" messages
- Missing environment variables
- Invalid configuration values

**Causes:**
- Missing environment files
- Incorrect environment variable names
- Invalid configuration values
- File permission issues

**Solutions:**

1. **Verify Configuration Files Exist:**
   ```bash
   ls -la config/environments/agentcore_*.env
   ls -la config/agentcore_environment_config.py
   ls -la config/cognito_config.json
   ```

2. **Test Configuration Loading:**
   ```bash
   python -c "
   import os
   from config.agentcore_environment_config import get_agentcore_config, get_cognito_config
   
   env = os.getenv('ENVIRONMENT', 'development')
   print(f'Loading configuration for environment: {env}')
   
   try:
       agentcore_config = get_agentcore_config(env)
       print('AgentCore configuration loaded successfully')
   except Exception as e:
       print(f'AgentCore configuration error: {e}')
   
   try:
       cognito_config = get_cognito_config(env)
       print('Cognito configuration loaded successfully')
   except Exception as e:
       print(f'Cognito configuration error: {e}')
   "
   ```

3. **Validate Configuration Values:**
   ```bash
   python config/validate_agentcore_config.py production
   ```

### 6. Tool Creation Failures

**Symptoms:**
- Import errors
- "Tool not found" messages
- Missing tool functions
- Initialization failures

**Causes:**
- Missing dependencies
- Import path issues
- Incorrect tool configuration
- Runtime client not initialized

**Solutions:**

1. **Check Dependencies:**
   ```bash
   pip list | grep -E "(boto3|aiohttp|pyjwt|structlog|pydantic)"
   ```

2. **Test Tool Imports:**
   ```bash
   python -c "
   try:
       from services.restaurant_search_tool import RestaurantSearchTool
       print('RestaurantSearchTool imported successfully')
   except ImportError as e:
       print(f'Import error: {e}')
   
   try:
       from services.restaurant_reasoning_tool import RestaurantReasoningTool
       print('RestaurantReasoningTool imported successfully')
   except ImportError as e:
       print(f'Import error: {e}')
   "
   ```

3. **Test Tool Initialization:**
   ```bash
   python examples/restaurant_search_tool_demo.py
   python examples/restaurant_reasoning_tool_demo.py
   ```

## Debug Mode

### Enable Comprehensive Debugging

```bash
export LOG_LEVEL=DEBUG
export ENABLE_AGENTCORE_REQUEST_TRACING=true
export ENABLE_JWT_DEBUG_LOGGING=true
export ENABLE_CIRCUIT_BREAKER_LOGGING=true
```

### Debug Logging Analysis

1. **AgentCore API Calls:**
   - Look for `agentcore_runtime_client` log entries
   - Check request/response details
   - Monitor response times

2. **Authentication Flow:**
   - Look for `authentication_manager` log entries
   - Check JWT token generation and refresh
   - Monitor authentication errors

3. **Circuit Breaker Activity:**
   - Look for `circuit_breaker` log entries
   - Check failure counts and state changes
   - Monitor recovery attempts

4. **Tool Execution:**
   - Look for tool-specific log entries
   - Check input/output data
   - Monitor error handling

## Performance Monitoring

### Key Metrics to Monitor

1. **Agent Invocation Metrics:**
   ```bash
   python -c "
   from services.agentcore_monitoring_service import AgentCoreMonitoringService
   import asyncio
   
   async def show_metrics():
       monitor = AgentCoreMonitoringService()
       metrics = await monitor.get_performance_metrics()
       print(f'Total invocations: {metrics.get(\"total_invocations\", 0)}')
       print(f'Success rate: {metrics.get(\"success_rate\", 0):.2%}')
       print(f'Average response time: {metrics.get(\"avg_response_time\", 0):.2f}ms')
   
   asyncio.run(show_metrics())
   "
   ```

2. **Circuit Breaker Status:**
   ```bash
   python -c "
   from services.agentcore_error_handler import AgentCoreErrorHandler
   handler = AgentCoreErrorHandler('monitoring')
   print(f'Circuit breaker failures: {handler.circuit_breaker.failure_count}')
   print(f'Circuit breaker state: {handler.circuit_breaker.state}')
   "
   ```

3. **Authentication Metrics:**
   ```bash
   python -c "
   from services.authentication_manager import AuthenticationManager
   from config.agentcore_environment_config import get_cognito_config
   import asyncio
   
   async def show_auth_metrics():
       auth = AuthenticationManager(get_cognito_config('production'))
       print(f'Token valid: {auth.is_token_valid()}')
       if auth.token_expiry:
           import datetime
           remaining = auth.token_expiry - datetime.datetime.utcnow()
           print(f'Token expires in: {remaining.total_seconds():.0f} seconds')
   
   asyncio.run(show_auth_metrics())
   "
   ```

## Log Analysis

### Important Log Patterns

1. **Successful Agent Invocation:**
   ```
   INFO agentcore_runtime_client Agent invocation successful agent_arn=arn:aws:bedrock-agentcore:... response_time=1234ms
   ```

2. **Authentication Success:**
   ```
   INFO authentication_manager JWT token refreshed successfully expires_in=3600s
   ```

3. **Circuit Breaker Activation:**
   ```
   WARNING agentcore_error_handler Circuit breaker opened due to failures threshold=5 current_failures=5
   ```

4. **Configuration Loading:**
   ```
   INFO agentcore_environment_config Configuration loaded successfully environment=production
   ```

### Log File Locations

- **Main Log**: `logs/main.log`
- **Error Log**: `logs/errors.log`
- **Performance Log**: `logs/performance.log`
- **HTTP Log**: `logs/http.log`

## Emergency Recovery

### Quick Recovery Steps

1. **Reset Circuit Breakers:**
   ```bash
   python -c "
   from services.agentcore_error_handler import AgentCoreErrorHandler
   for component in ['restaurant_search', 'restaurant_reasoning']:
       handler = AgentCoreErrorHandler(component)
       handler.circuit_breaker.reset()
       print(f'Reset circuit breaker for {component}')
   "
   ```

2. **Clear Response Cache:**
   ```bash
   python -c "
   from services.response_cache import ResponseCache
   cache = ResponseCache()
   cache.clear()
   print('Response cache cleared')
   "
   ```

3. **Force Token Refresh:**
   ```bash
   python -c "
   from services.authentication_manager import AuthenticationManager
   from config.agentcore_environment_config import get_cognito_config
   import asyncio
   
   async def force_refresh():
       auth = AuthenticationManager(get_cognito_config('production'))
       token = await auth.refresh_token()
       print('Token refreshed successfully')
   
   asyncio.run(force_refresh())
   "
   ```

### Fallback Configuration

If all else fails, use minimal configuration:

```bash
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export AGENTCORE_TIMEOUT=120
export AGENTCORE_MAX_RETRIES=5
export CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
export ENABLE_RESPONSE_CACHING=false
export ENABLE_PARALLEL_EXECUTION=false
```

## Getting Help

### Information to Collect

When reporting issues, collect this information:

1. **Environment Information:**
   ```bash
   echo "Environment: $ENVIRONMENT"
   echo "Python Version: $(python --version)"
   echo "AWS CLI Version: $(aws --version)"
   ```

2. **Configuration Summary:**
   ```bash
   python -c "
   from config.agentcore_environment_config import get_agentcore_config
   config = get_agentcore_config('production')
   print(f'Timeout: {config.timeout_seconds}s')
   print(f'Max Retries: {config.max_retries}')
   print(f'Region: {config.region}')
   "
   ```

3. **Recent Logs:**
   ```bash
   tail -50 logs/errors.log
   tail -50 logs/main.log
   ```

4. **Test Results:**
   ```bash
   python test_agentcore_integration.py > test_results.txt 2>&1
   ```

### Support Channels

1. Check the troubleshooting section in README.md
2. Review configuration documentation
3. Run validation scripts
4. Check logs for detailed error information
5. Test with minimal configuration

---

**Last Updated**: October 6, 2025  
**Version**: 3.0.0 (AgentCore Runtime Integration)  
**Scope**: Comprehensive troubleshooting for AgentCore integration