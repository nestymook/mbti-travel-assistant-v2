# Migration Guide: MCP Client to HTTP Gateway Integration

This guide helps you migrate from the previous MCP client implementation to the new HTTP gateway integration for the MBTI Travel Planner Agent.

## 🔄 Migration Overview

The agent has been updated to use direct HTTP API calls to the agentcore-gateway-mcp-tools service instead of managing complex MCP client connections with JWT authentication.

### Before (MCP Client Architecture)
```
Agent → MCP Client Manager → Cognito Auth → JWT Tokens → MCP Servers
```

### After (HTTP Gateway Architecture)
```
Agent → HTTP Client → Gateway Service → MCP Tools
```

## 📋 Migration Checklist

### ✅ Configuration Changes

#### 1. Environment Variables - REMOVED
The following environment variables are **no longer needed**:
```bash
# ❌ Remove these variables
MCP_SERVER_URL=
MCP_AUTH_TOKEN=
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
COGNITO_CLIENT_SECRET=
JWT_DISCOVERY_URL=
```

#### 2. Environment Variables - ADDED
Add these new HTTP gateway configuration variables:
```bash
# ✅ Add these variables
GATEWAY_BASE_URL=https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com
GATEWAY_TIMEOUT=60
GATEWAY_MAX_RETRIES=3
GATEWAY_AUTH_REQUIRED=true
GATEWAY_AUTH_TOKEN=your-jwt-token-if-required
```

#### 3. Dependencies - UPDATED
Update `requirements.txt`:
```diff
# Core AgentCore dependencies
bedrock-agentcore
strands-agents
boto3

# HTTP client dependencies
+ httpx>=0.25.0
+ pydantic>=2.0.0
aiohttp

# REMOVED: MCP client dependencies
- mcp>=1.9.0

# Data processing
pandas
requests

# AWS services
aws-opentelemetry-distro>=0.10.1

# Authentication (simplified)
pyjwt
cryptography

# Configuration
pyyaml
python-dotenv

# Logging
python-dateutil
+ structlog

# Performance
+ psutil
```

### ✅ Code Changes

#### 1. Import Changes
```python
# ❌ Old imports (remove)
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.mcp_client_service import MCPClientService

# ✅ New imports (add)
from services.gateway_http_client import GatewayHTTPClient
from services.gateway_tools import (
    create_restaurant_search_tools,
    create_restaurant_recommendation_tools
)
```

#### 2. Client Initialization
```python
# ❌ Old MCP client initialization
mcp_client = MCPClientService(
    cognito_config=cognito_config,
    mcp_servers=mcp_server_config
)

# ✅ New HTTP client initialization
http_client = GatewayHTTPClient(
    environment=current_environment,
    base_url=gateway_config.base_url,
    timeout=gateway_config.timeout,
    auth_token=auth_token
)
```

#### 3. Tool Creation
```python
# ❌ Old MCP tool creation
tools = await mcp_client.create_tools()

# ✅ New HTTP tool creation
search_tools = create_restaurant_search_tools(http_client)
recommendation_tools = create_restaurant_recommendation_tools(http_client)
tools = search_tools + recommendation_tools
```

### ✅ Configuration Files

#### 1. Update `.bedrock_agentcore.yaml`
```yaml
# Enhanced observability for HTTP client monitoring
observability:
  enabled: true
  metrics:
    custom_metrics_enabled: true
    http_request_metrics: true
  logging:
    structured_logging: true
    log_level: INFO
```

#### 2. Environment Configuration Files
Update all environment files (`config/environments/*.env`) with new variables:
- `GATEWAY_*` variables for HTTP client configuration
- Enhanced logging configuration
- Performance monitoring settings
- Health check configuration

### ✅ File Structure Changes

#### Files to Remove
```
services/mcp_client_service.py          # ❌ Remove (COMPLETED)
services/agentcore_endpoints.py         # ❌ Remove (COMPLETED)
mcp_config.py                           # ❌ Remove (COMPLETED)
deploy_mcp_client_agent.py              # ❌ Remove (COMPLETED)
test_agent_with_mcp_client.py           # ❌ Remove (COMPLETED)
test_mcp_client_integration.py          # ❌ Remove (COMPLETED)
test_direct_mcp_tools.py                # ❌ Remove (COMPLETED)
MCP_CLIENT_INTEGRATION_README.md        # ❌ Remove (COMPLETED)
MCP_CLIENT_INTEGRATION_SUMMARY.md       # ❌ Remove (COMPLETED)
AGENTCORE_MCP_INTEGRATION_SUCCESS_REPORT.md # ❌ Remove (COMPLETED)
cognito_config.json                     # ❌ Remove (COMPLETED)
fresh_jwt.txt                           # ❌ Remove (COMPLETED)
access_token.txt                        # ❌ Remove (COMPLETED)
test_auth_prompt.py                     # ❌ Remove (COMPLETED)
test_agentcore_basic.py                 # ❌ Remove (COMPLETED)
test_agentcore_simple.py                # ❌ Remove (COMPLETED)
agentcore_mcp_test_results.json         # ❌ Remove (COMPLETED)
direct_mcp_test_results.json            # ❌ Remove (COMPLETED)
```

#### Files Added/Updated
```
services/gateway_http_client.py         # ✅ New HTTP client
services/gateway_tools.py               # ✅ Updated tools
services/error_handler.py               # ✅ Enhanced error handling
config/gateway_config.py                # ✅ Gateway configuration
ENVIRONMENT_VARIABLES.md                # ✅ New documentation
MIGRATION_GUIDE.md                      # ✅ This file
```

## 🚀 Step-by-Step Migration

### Step 1: Backup Current Configuration
```bash
# Backup current environment files
cp config/environments/production.env config/environments/production.env.backup
cp .bedrock_agentcore.yaml .bedrock_agentcore.yaml.backup
cp requirements.txt requirements.txt.backup
```

### Step 2: Update Dependencies
```bash
# Install new dependencies
pip install httpx>=0.25.0 pydantic>=2.0.0 structlog psutil

# Remove old MCP client dependency
pip uninstall mcp
```

### Step 3: Update Configuration Files
```bash
# Copy new configuration templates
cp config/example.env config/environments/production.env

# Edit with your specific values
nano config/environments/production.env
```

### Step 4: Update Environment Variables
```bash
# Remove old variables
unset MCP_SERVER_URL MCP_AUTH_TOKEN COGNITO_USER_POOL_ID COGNITO_CLIENT_ID

# Set new variables
export ENVIRONMENT=production
export GATEWAY_BASE_URL=https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com
export GATEWAY_AUTH_REQUIRED=true
export GATEWAY_AUTH_TOKEN=your-token-here
```

### Step 5: Validate Configuration
```bash
# Run configuration validation
python scripts/validate_deployment_config.py production
```

### Step 6: Test Locally (Optional)
```bash
# Test with development environment first
export ENVIRONMENT=development
python main.py
```

### Step 7: Deploy
```bash
# Deploy with new configuration
python scripts/deploy_with_http_gateway.py production
```

### Step 8: Verify Deployment
```bash
# Test the deployed agent
python test_central_district_workflow.py
python test_recommendation_functionality.py
```

## 🔧 Troubleshooting Migration Issues

### Issue: Gateway Connection Errors
```bash
# Check gateway connectivity
curl -X GET https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com/health

# Validate configuration
python scripts/validate_deployment_config.py production
```

### Issue: Authentication Failures
```bash
# Verify JWT token format
echo $GATEWAY_AUTH_TOKEN | cut -d'.' -f2 | base64 -d

# Test authentication
python -c "
from services.gateway_http_client import GatewayHTTPClient
client = GatewayHTTPClient('production', auth_token='$GATEWAY_AUTH_TOKEN')
print('Authentication configured correctly')
"
```

### Issue: Missing Dependencies
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# Check for conflicts
pip check
```

### Issue: Configuration Validation Errors
```bash
# Run detailed validation
python scripts/validate_deployment_config.py production

# Check specific configuration
python -c "
from config.gateway_config import get_gateway_config
config = get_gateway_config('production')
print(f'Gateway URL: {config.base_url}')
print(f'Auth Required: {config.auth_required}')
"
```

## 📊 Performance Comparison

### Before (MCP Client)
- Complex authentication flow
- Multiple JWT token refreshes
- Direct MCP server connections
- Manual error handling

### After (HTTP Gateway)
- Simplified HTTP requests
- Single authentication point
- Centralized error handling
- Built-in retry logic
- Connection pooling
- Health monitoring

## 🎯 Benefits of Migration

### 1. Simplified Architecture
- Fewer moving parts
- Easier to debug and monitor
- Reduced authentication complexity

### 2. Better Error Handling
- Comprehensive error categorization
- User-friendly error messages
- Automatic fallback responses

### 3. Enhanced Monitoring
- HTTP request/response metrics
- Performance monitoring
- Health check system

### 4. Improved Reliability
- Connection pooling
- Automatic retries
- Circuit breaker patterns

### 5. Easier Deployment
- Environment-specific configuration
- Validation scripts
- Automated deployment

## 🔄 Rollback Plan

If you need to rollback to the MCP client implementation:

### 1. Restore Backup Files
```bash
cp config/environments/production.env.backup config/environments/production.env
cp .bedrock_agentcore.yaml.backup .bedrock_agentcore.yaml
cp requirements.txt.backup requirements.txt
```

### 2. Reinstall MCP Dependencies
```bash
pip install mcp>=1.9.0
```

### 3. Restore Environment Variables
```bash
export MCP_SERVER_URL=your-mcp-server-url
export COGNITO_USER_POOL_ID=your-pool-id
# ... other MCP variables
```

### 4. Redeploy
```bash
python -m bedrock_agentcore deploy
```

## 📞 Support

If you encounter issues during migration:

1. **Check Configuration**: Run `python scripts/validate_deployment_config.py`
2. **Review Logs**: Check agent logs for detailed error information
3. **Test Connectivity**: Verify gateway service is accessible
4. **Validate Environment**: Ensure all required variables are set

## 📝 Post-Migration Checklist

- [ ] All tests pass (`python -m pytest tests/ -v`)
- [ ] Configuration validation passes
- [ ] Gateway connectivity confirmed
- [ ] Agent responds to test requests
- [ ] Monitoring and logging working
- [ ] Performance metrics collected
- [ ] Documentation updated
- [ ] Team notified of changes

## 🧹 Cleanup Completed

The following legacy files and components have been successfully removed:

### Removed Files
- ✅ **MCP Client Services**: `services/mcp_client_service.py`, `services/agentcore_endpoints.py`
- ✅ **MCP Configuration**: `mcp_config.py`
- ✅ **Legacy Deployment**: `deploy_mcp_client_agent.py`
- ✅ **Legacy Tests**: All MCP client-specific test files
- ✅ **Legacy Documentation**: MCP client integration documentation
- ✅ **Authentication Files**: Cognito config, JWT tokens, access tokens
- ✅ **Test Results**: Legacy MCP test result files

### Updated Files
- ✅ **Documentation**: README.md, MIGRATION_GUIDE.md updated for HTTP gateway
- ✅ **Code Comments**: All references to MCP client updated to HTTP gateway
- ✅ **Version Numbers**: Updated to v2.0.0 (HTTP Gateway Integration)
- ✅ **Dependencies**: requirements.txt cleaned of MCP client dependencies

### Architecture Changes
- ✅ **Simplified Authentication**: No more complex JWT token management
- ✅ **HTTP-Only Communication**: Direct API calls to gateway service
- ✅ **Environment-Based Configuration**: Automatic endpoint detection
- ✅ **Enhanced Error Handling**: User-friendly error messages and fallbacks

---

**Migration Date**: October 4, 2025  
**From**: MCP Client Architecture  
**To**: HTTP Gateway Integration  
**Status**: Complete ✅  
**Cleanup Status**: Complete ✅