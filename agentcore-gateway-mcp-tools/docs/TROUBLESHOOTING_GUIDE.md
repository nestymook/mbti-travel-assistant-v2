# AgentCore Gateway MCP Tools - Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide helps diagnose and resolve common issues with the AgentCore Gateway for MCP Tools. It covers deployment problems, authentication failures, API errors, performance issues, and provides diagnostic tools and solutions.

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Deployment Issues](#deployment-issues)
3. [Authentication Problems](#authentication-problems)
4. [API Request Failures](#api-request-failures)
5. [MCP Server Connectivity](#mcp-server-connectivity)
6. [Performance Issues](#performance-issues)
7. [Error Code Reference](#error-code-reference)
8. [Diagnostic Tools](#diagnostic-tools)
9. [Log Analysis](#log-analysis)
10. [Common Solutions](#common-solutions)

## Quick Diagnostic Checklist

Before diving into specific issues, run through this quick checklist:

### ✅ Basic Health Checks

```bash
# 1. Check Gateway health endpoint
curl -X GET "https://your-gateway.amazonaws.com/health"

# 2. Verify Cognito configuration
curl -X GET "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"

# 3. Test MCP server connectivity
curl -X GET "http://restaurant-search-mcp:8080/health"
curl -X GET "http://restaurant-reasoning-mcp:8080/health"

# 4. Check AgentCore deployment status
agentcore status

# 5. Verify JWT token format (if you have one)
echo "YOUR_JWT_TOKEN" | cut -d'.' -f2 | base64 -d | jq .
```

### ✅ Environment Verification

```bash
# Check required environment variables
echo "AWS_REGION: $AWS_REGION"
echo "COGNITO_USER_POOL_ID: $COGNITO_USER_POOL_ID"
echo "COGNITO_CLIENT_ID: $COGNITO_CLIENT_ID"

# Verify AWS credentials
aws sts get-caller-identity

# Check AgentCore configuration
cat .bedrock_agentcore.yaml
```

## Deployment Issues

### Issue 1: Container Build Failures

**Symptoms**:
- Docker build fails with platform errors
- "exec format error" when running container
- AgentCore deployment fails with image issues

**Causes**:
- Incorrect platform specification
- Missing ARM64 support
- Base image compatibility issues

**Solutions**:

```bash
# 1. Verify Docker buildx support
docker buildx ls

# 2. Build with explicit ARM64 platform
docker buildx build --platform linux/arm64 -t agentcore-gateway-mcp-tools .

# 3. Test container locally
docker run --platform linux/arm64 -p 8080:8080 agentcore-gateway-mcp-tools

# 4. Verify image architecture
docker inspect agentcore-gateway-mcp-tools | grep Architecture
```

**Dockerfile Fix**:
```dockerfile
# Ensure ARM64 platform is specified
FROM --platform=linux/arm64 python:3.12-slim

# Use multi-stage build for optimization
FROM --platform=linux/arm64 python:3.12-slim as builder
# ... build steps ...

FROM --platform=linux/arm64 python:3.12-slim as runtime
# ... runtime setup ...
```

### Issue 2: AgentCore Deployment Failures

**Symptoms**:
- `agentcore launch` fails
- Configuration validation errors
- Service not starting after deployment

**Diagnostic Commands**:
```bash
# Check deployment logs
agentcore logs --tail 100

# Validate configuration
python scripts/validate_deployment_config.py

# Check service status
agentcore status --verbose
```

**Common Fixes**:

1. **Invalid Configuration**:
```yaml
# Fix .bedrock_agentcore.yaml
name: "agentcore-gateway-mcp-tools"
platform: "linux/arm64"  # Must be ARM64
container:
  image: "your-account.dkr.ecr.us-east-1.amazonaws.com/agentcore-gateway-mcp-tools:latest"
  port: 8080
```

2. **Missing Permissions**:
```bash
# Add required IAM permissions
aws iam attach-role-policy \
  --role-name your-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

3. **ECR Access Issues**:
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  your-account.dkr.ecr.us-east-1.amazonaws.com

# Verify image exists
aws ecr describe-images --repository-name agentcore-gateway-mcp-tools
```

### Issue 3: Network Connectivity Problems

**Symptoms**:
- Gateway cannot reach MCP servers
- Timeout errors during deployment
- Service discovery failures

**Diagnostic Steps**:
```bash
# 1. Check network configuration
aws ec2 describe-vpcs
aws ec2 describe-subnets
aws ec2 describe-security-groups

# 2. Test internal connectivity
# (Run from within the same network)
telnet restaurant-search-mcp 8080
telnet restaurant-reasoning-mcp 8080

# 3. Check DNS resolution
nslookup restaurant-search-mcp
nslookup restaurant-reasoning-mcp
```

**Solutions**:

1. **Security Group Rules**:
```bash
# Allow internal communication
aws ec2 authorize-security-group-ingress \
  --group-id sg-gateway \
  --protocol tcp \
  --port 8080 \
  --source-group sg-mcp-servers
```

2. **Service Discovery Configuration**:
```yaml
# Update .bedrock_agentcore.yaml
environment:
  MCP_SEARCH_SERVER_URL: "http://restaurant-search-mcp.internal:8080"
  MCP_REASONING_SERVER_URL: "http://restaurant-reasoning-mcp.internal:8080"
```

## Authentication Problems

### Issue 1: JWT Token Validation Failures

**Symptoms**:
- 401 Unauthorized responses
- "Invalid JWT token" errors
- Token signature verification failures

**Diagnostic Commands**:
```bash
# 1. Decode token without verification
python -c "
import jwt
import json
token = 'YOUR_JWT_TOKEN'
header = jwt.get_unverified_header(token)
payload = jwt.decode(token, options={'verify_signature': False})
print('Header:', json.dumps(header, indent=2))
print('Payload:', json.dumps(payload, indent=2))
"

# 2. Check token expiration
python -c "
import jwt
import time
token = 'YOUR_JWT_TOKEN'
payload = jwt.decode(token, options={'verify_signature': False})
exp = payload.get('exp', 0)
now = time.time()
print(f'Token expires: {time.ctime(exp)}')
print(f'Current time: {time.ctime(now)}')
print(f'Expired: {exp < now}')
"

# 3. Verify JWKS endpoint
curl -s "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json" | jq .
```

**Common Causes and Solutions**:

1. **Expired Token**:
```javascript
// Implement automatic token refresh
async function refreshTokenIfNeeded(authClient) {
  const token = authClient.getCurrentToken();
  if (!token) return null;
  
  const payload = JSON.parse(atob(token.split('.')[1]));
  const exp = payload.exp * 1000; // Convert to milliseconds
  const now = Date.now();
  
  // Refresh if token expires in next 5 minutes
  if (exp - now < 5 * 60 * 1000) {
    await authClient.refreshTokens();
  }
  
  return authClient.getCurrentToken();
}
```

2. **Invalid Signature**:
```python
# Verify JWKS key ID matches token
import jwt
import requests

def debug_token_signature(token):
    header = jwt.get_unverified_header(token)
    kid = header.get('kid')
    
    # Fetch JWKS
    jwks_url = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    
    # Find matching key
    matching_key = None
    for key in jwks['keys']:
        if key['kid'] == kid:
            matching_key = key
            break
    
    if not matching_key:
        print(f"No matching key found for kid: {kid}")
        print(f"Available keys: {[k['kid'] for k in jwks['keys']]}")
    else:
        print(f"Found matching key for kid: {kid}")
```

3. **Clock Skew Issues**:
```python
# Add clock skew tolerance
import jwt
from datetime import timedelta

def validate_token_with_skew(token, public_key):
    return jwt.decode(
        token,
        public_key,
        algorithms=['RS256'],
        audience='1ofgeckef3po4i3us4j1m4chvd',
        issuer='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn',
        leeway=timedelta(seconds=30)  # Allow 30 seconds clock skew
    )
```

### Issue 2: Cognito Authentication Failures

**Symptoms**:
- Cannot obtain tokens from Cognito
- "NotAuthorizedException" errors
- User not found or not confirmed

**Diagnostic Steps**:
```bash
# 1. Test Cognito endpoint connectivity
curl -X POST "https://cognito-idp.us-east-1.amazonaws.com/" \
  -H "Content-Type: application/x-amz-json-1.1" \
  -H "X-Amz-Target: AWSCognitoIdentityProviderService.ListUsers" \
  -d '{"UserPoolId": "us-east-1_KePRX24Bn", "Limit": 1}'

# 2. Check user status
aws cognito-idp admin-get-user \
  --user-pool-id us-east-1_KePRX24Bn \
  --username your-username

# 3. Verify client configuration
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_KePRX24Bn \
  --client-id 1ofgeckef3po4i3us4j1m4chvd
```

**Solutions**:

1. **User Not Confirmed**:
```bash
# Confirm user manually
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id us-east-1_KePRX24Bn \
  --username your-username
```

2. **Invalid Client Configuration**:
```python
# Test authentication with proper error handling
import boto3
from botocore.exceptions import ClientError

def test_cognito_auth(username, password):
    client = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        response = client.initiate_auth(
            ClientId='1ofgeckef3po4i3us4j1m4chvd',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        print("Authentication successful")
        return response['AuthenticationResult']
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'NotAuthorizedException':
            print("Invalid username or password")
        elif error_code == 'UserNotConfirmedException':
            print("User account not confirmed")
        elif error_code == 'UserNotFoundException':
            print("User not found")
        else:
            print(f"Authentication error: {error_code} - {error_message}")
        
        return None
```

## API Request Failures

### Issue 1: 400 Bad Request - Validation Errors

**Symptoms**:
- Request validation failures
- Invalid parameter errors
- Schema validation errors

**Common Validation Issues**:

1. **Invalid District Names**:
```json
// Error response
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid district names provided",
    "details": {
      "invalid_districts": ["NonExistent District"],
      "available_districts": ["Central district", "Admiralty", "Causeway Bay"]
    }
  }
}
```

**Solution**:
```javascript
// Use valid district names
const validDistricts = [
  "Central district", "Admiralty", "Causeway Bay", "Wan Chai",
  "Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Jordan"
];

// Validate before sending request
function validateDistricts(districts) {
  const invalid = districts.filter(d => !validDistricts.includes(d));
  if (invalid.length > 0) {
    throw new Error(`Invalid districts: ${invalid.join(', ')}`);
  }
}
```

2. **Invalid Meal Types**:
```python
# Valid meal types
VALID_MEAL_TYPES = ['breakfast', 'lunch', 'dinner']

def validate_meal_types(meal_types):
    invalid = [mt for mt in meal_types if mt not in VALID_MEAL_TYPES]
    if invalid:
        raise ValueError(f"Invalid meal types: {invalid}")
```

3. **Missing Required Fields**:
```typescript
// Ensure all required fields are present
interface RestaurantSearchRequest {
  districts: string[];  // Required, non-empty array
}

interface RecommendationRequest {
  restaurants: Restaurant[];  // Required, non-empty array
  ranking_method?: string;    // Optional
}
```

### Issue 2: 503 Service Unavailable - MCP Server Issues

**Symptoms**:
- MCP server temporarily unavailable
- Connection timeout errors
- Service discovery failures

**Diagnostic Commands**:
```bash
# 1. Check MCP server health directly
curl -X GET "http://restaurant-search-mcp:8080/health"
curl -X GET "http://restaurant-reasoning-mcp:8080/health"

# 2. Check service logs
kubectl logs deployment/restaurant-search-mcp
kubectl logs deployment/restaurant-reasoning-mcp

# 3. Test MCP protocol connectivity
python -c "
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def test_mcp():
    try:
        async with streamablehttp_client('http://restaurant-search-mcp:8080') as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print(f'Available tools: {[t.name for t in tools]}')
    except Exception as e:
        print(f'MCP connection failed: {e}')

asyncio.run(test_mcp())
"
```

**Solutions**:

1. **Implement Retry Logic**:
```python
import asyncio
import aiohttp
from typing import Optional

class MCPClientWithRetry:
    def __init__(self, base_url: str, max_retries: int = 3):
        self.base_url = base_url
        self.max_retries = max_retries
    
    async def call_with_retry(self, endpoint: str, data: dict) -> Optional[dict]:
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}{endpoint}",
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status
                            )
            
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
                break
        
        raise last_error
```

2. **Health Check Integration**:
```python
async def check_mcp_server_health(server_url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{server_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
    except:
        return False

# Use in request handler
async def search_restaurants(request_data):
    if not await check_mcp_server_health("http://restaurant-search-mcp:8080"):
        raise ServiceUnavailableError("Search service temporarily unavailable")
    
    # Proceed with request
```

## MCP Server Connectivity

### Issue 1: Connection Timeouts

**Symptoms**:
- Request timeouts to MCP servers
- Intermittent connectivity issues
- Slow response times

**Diagnostic Tools**:
```bash
# 1. Network latency test
ping restaurant-search-mcp
ping restaurant-reasoning-mcp

# 2. Port connectivity test
telnet restaurant-search-mcp 8080
nc -zv restaurant-search-mcp 8080

# 3. HTTP response time test
time curl -X GET "http://restaurant-search-mcp:8080/health"
```

**Solutions**:

1. **Adjust Timeout Settings**:
```python
# Configure appropriate timeouts
MCP_CLIENT_CONFIG = {
    'connection_timeout': 10,  # seconds
    'read_timeout': 30,        # seconds
    'total_timeout': 45        # seconds
}
```

2. **Connection Pooling**:
```python
import aiohttp

class MCPConnectionPool:
    def __init__(self):
        self.connector = aiohttp.TCPConnector(
            limit=100,           # Total connection pool size
            limit_per_host=30,   # Per-host connection limit
            ttl_dns_cache=300,   # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30
        )
        self.session = aiohttp.ClientSession(connector=self.connector)
    
    async def close(self):
        await self.session.close()
```

### Issue 2: Service Discovery Problems

**Symptoms**:
- Cannot resolve MCP server hostnames
- DNS resolution failures
- Service not found errors

**Diagnostic Commands**:
```bash
# 1. DNS resolution test
nslookup restaurant-search-mcp
dig restaurant-search-mcp

# 2. Service discovery test (Kubernetes)
kubectl get services
kubectl get endpoints

# 3. Network policy check
kubectl get networkpolicies
```

**Solutions**:

1. **Use IP Addresses Temporarily**:
```bash
# Find service IP
kubectl get service restaurant-search-mcp -o wide

# Update configuration with IP
export MCP_SEARCH_SERVER_URL="http://10.0.1.100:8080"
```

2. **Fix Service Configuration**:
```yaml
# Kubernetes service definition
apiVersion: v1
kind: Service
metadata:
  name: restaurant-search-mcp
spec:
  selector:
    app: restaurant-search-mcp
  ports:
    - port: 8080
      targetPort: 8080
  type: ClusterIP
```

## Performance Issues

### Issue 1: Slow Response Times

**Symptoms**:
- API responses taking longer than expected
- Timeout errors under load
- High latency measurements

**Performance Monitoring**:
```python
import time
import asyncio
from typing import Dict, Any

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0
        }
    
    async def monitor_request(self, func, *args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            self.metrics['request_count'] += 1
            return result
        except Exception as e:
            self.metrics['errors'] += 1
            raise
        finally:
            duration = time.time() - start_time
            self.metrics['total_time'] += duration
            self.metrics['min_time'] = min(self.metrics['min_time'], duration)
            self.metrics['max_time'] = max(self.metrics['max_time'], duration)
    
    def get_stats(self) -> Dict[str, Any]:
        if self.metrics['request_count'] == 0:
            return self.metrics
        
        return {
            **self.metrics,
            'avg_time': self.metrics['total_time'] / self.metrics['request_count'],
            'error_rate': self.metrics['errors'] / (self.metrics['request_count'] + self.metrics['errors'])
        }
```

**Optimization Strategies**:

1. **Connection Pooling**:
```python
# Use persistent connections
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(
        limit=100,
        limit_per_host=30,
        keepalive_timeout=30
    )
)
```

2. **Response Caching**:
```python
from functools import lru_cache
import asyncio

class AsyncLRUCache:
    def __init__(self, maxsize=128, ttl=300):
        self.cache = {}
        self.maxsize = maxsize
        self.ttl = ttl
    
    async def get_or_set(self, key, coro_func):
        now = time.time()
        
        if key in self.cache:
            value, timestamp = self.cache[key]
            if now - timestamp < self.ttl:
                return value
        
        # Cache miss or expired
        result = await coro_func()
        self.cache[key] = (result, now)
        
        # Cleanup old entries
        if len(self.cache) > self.maxsize:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        return result
```

### Issue 2: Memory Leaks

**Symptoms**:
- Increasing memory usage over time
- Out of memory errors
- Container restarts due to memory limits

**Memory Monitoring**:
```python
import psutil
import gc
import tracemalloc

def monitor_memory():
    # Start memory tracing
    tracemalloc.start()
    
    # Get current memory usage
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # Get top memory allocations
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print("Top 10 memory allocations:")
    for stat in top_stats[:10]:
        print(stat)

# Call periodically
import threading
def memory_monitor_thread():
    while True:
        monitor_memory()
        time.sleep(60)  # Check every minute

threading.Thread(target=memory_monitor_thread, daemon=True).start()
```

**Memory Leak Solutions**:

1. **Proper Session Management**:
```python
# Always close aiohttp sessions
async def make_request():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://example.com') as response:
            return await response.json()
    # Session automatically closed
```

2. **Garbage Collection**:
```python
import gc
import weakref

class ResourceManager:
    def __init__(self):
        self._resources = weakref.WeakSet()
    
    def add_resource(self, resource):
        self._resources.add(resource)
    
    def cleanup(self):
        # Force garbage collection
        gc.collect()
        
        # Log remaining resources
        print(f"Active resources: {len(self._resources)}")
```

## Error Code Reference

### HTTP Status Codes

| Code | Error Type | Description | Solution |
|------|------------|-------------|----------|
| 400 | Bad Request | Invalid request parameters | Validate request format and parameters |
| 401 | Unauthorized | Missing or invalid JWT token | Check authentication and token validity |
| 403 | Forbidden | Valid token but insufficient permissions | Verify user permissions and token claims |
| 404 | Not Found | Endpoint or resource not found | Check API endpoint URL and method |
| 429 | Too Many Requests | Rate limit exceeded | Implement rate limiting and retry logic |
| 500 | Internal Server Error | Unexpected server error | Check server logs and error handling |
| 503 | Service Unavailable | MCP server unavailable | Check MCP server health and connectivity |

### Custom Error Types

| Error Type | Cause | Solution |
|------------|-------|----------|
| `AuthenticationError` | JWT token validation failed | Refresh token or re-authenticate |
| `ValidationError` | Request validation failed | Fix request parameters |
| `ServiceUnavailableError` | MCP server unavailable | Retry request or check server status |
| `TimeoutError` | Request timeout | Increase timeout or check connectivity |
| `RateLimitError` | Rate limit exceeded | Implement backoff strategy |

## Diagnostic Tools

### 1. Health Check Script

```bash
#!/bin/bash
# health_check.sh - Comprehensive health check

set -e

GATEWAY_URL="${GATEWAY_URL:-https://your-gateway.amazonaws.com}"
USER_POOL_ID="us-east-1_KePRX24Bn"
CLIENT_ID="1ofgeckef3po4i3us4j1m4chvd"

echo "=== AgentCore Gateway Health Check ==="

# 1. Gateway health
echo "1. Checking Gateway health..."
if curl -s -f "${GATEWAY_URL}/health" > /dev/null; then
    echo "✅ Gateway is healthy"
    curl -s "${GATEWAY_URL}/health" | jq .
else
    echo "❌ Gateway health check failed"
    exit 1
fi

# 2. Cognito configuration
echo -e "\n2. Checking Cognito configuration..."
DISCOVERY_URL="https://cognito-idp.us-east-1.amazonaws.com/${USER_POOL_ID}/.well-known/openid-configuration"
if curl -s -f "$DISCOVERY_URL" > /dev/null; then
    echo "✅ Cognito configuration accessible"
else
    echo "❌ Cognito configuration not accessible"
    exit 1
fi

# 3. JWKS endpoint
echo -e "\n3. Checking JWKS endpoint..."
JWKS_URL="https://cognito-idp.us-east-1.amazonaws.com/${USER_POOL_ID}/.well-known/jwks.json"
if curl -s -f "$JWKS_URL" > /dev/null; then
    echo "✅ JWKS endpoint accessible"
    KEY_COUNT=$(curl -s "$JWKS_URL" | jq '.keys | length')
    echo "   Available keys: $KEY_COUNT"
else
    echo "❌ JWKS endpoint not accessible"
    exit 1
fi

# 4. Tool metadata
echo -e "\n4. Checking tool metadata..."
if curl -s -f "${GATEWAY_URL}/tools/metadata" > /dev/null; then
    echo "✅ Tool metadata accessible"
    TOOL_COUNT=$(curl -s "${GATEWAY_URL}/tools/metadata" | jq '.data.tools | length')
    echo "   Available tools: $TOOL_COUNT"
else
    echo "❌ Tool metadata not accessible"
fi

# 5. Metrics endpoint
echo -e "\n5. Checking metrics endpoint..."
if curl -s -f "${GATEWAY_URL}/metrics" > /dev/null; then
    echo "✅ Metrics endpoint accessible"
else
    echo "❌ Metrics endpoint not accessible"
fi

echo -e "\n=== Health Check Complete ==="
```

### 2. Token Validation Tool

```python
#!/usr/bin/env python3
# validate_token.py - JWT token validation tool

import sys
import jwt
import json
import requests
import argparse
from datetime import datetime, timezone

def validate_jwt_token(token, user_pool_id, client_id, region='us-east-1'):
    """Validate JWT token against Cognito User Pool."""
    
    try:
        # 1. Decode header
        header = jwt.get_unverified_header(token)
        print("Token Header:")
        print(json.dumps(header, indent=2))
        
        # 2. Decode payload (without verification)
        payload = jwt.decode(token, options={"verify_signature": False})
        print("\nToken Payload:")
        print(json.dumps(payload, indent=2, default=str))
        
        # 3. Check basic claims
        print("\n=== Token Validation ===")
        
        # Check expiration
        exp = payload.get('exp')
        if exp:
            exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            print(f"Expires: {exp_time}")
            print(f"Current: {now}")
            print(f"Expired: {'Yes' if exp_time < now else 'No'}")
        
        # Check audience
        aud = payload.get('aud')
        print(f"Audience: {aud}")
        print(f"Expected: {client_id}")
        print(f"Audience Valid: {'Yes' if aud == client_id else 'No'}")
        
        # Check issuer
        iss = payload.get('iss')
        expected_iss = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        print(f"Issuer: {iss}")
        print(f"Expected: {expected_iss}")
        print(f"Issuer Valid: {'Yes' if iss == expected_iss else 'No'}")
        
        # 4. Verify signature
        print("\n=== Signature Verification ===")
        
        # Get JWKS
        jwks_url = f"{expected_iss}/.well-known/jwks.json"
        jwks_response = requests.get(jwks_url)
        jwks_response.raise_for_status()
        jwks = jwks_response.json()
        
        # Find matching key
        kid = header.get('kid')
        public_key = None
        for key in jwks['keys']:
            if key['kid'] == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break
        
        if not public_key:
            print(f"❌ No matching public key found for kid: {kid}")
            return False
        
        # Verify signature
        try:
            verified_payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=client_id,
                issuer=expected_iss
            )
            print("✅ Token signature is valid")
            print("✅ All validations passed")
            return True
        
        except jwt.ExpiredSignatureError:
            print("❌ Token has expired")
        except jwt.InvalidAudienceError:
            print("❌ Invalid audience")
        except jwt.InvalidIssuerError:
            print("❌ Invalid issuer")
        except jwt.InvalidSignatureError:
            print("❌ Invalid signature")
        except Exception as e:
            print(f"❌ Validation failed: {e}")
        
        return False
    
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate JWT token')
    parser.add_argument('--token', required=True, help='JWT token to validate')
    parser.add_argument('--user-pool-id', default='us-east-1_KePRX24Bn', help='Cognito User Pool ID')
    parser.add_argument('--client-id', default='1ofgeckef3po4i3us4j1m4chvd', help='Cognito Client ID')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    is_valid = validate_jwt_token(
        args.token,
        args.user_pool_id,
        args.client_id,
        args.region
    )
    
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
```

### 3. Load Testing Script

```python
#!/usr/bin/env python3
# load_test.py - Load testing tool

import asyncio
import aiohttp
import time
import json
import argparse
from typing import List, Dict, Any

class LoadTester:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.results = []
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single request and record metrics."""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers={'Authorization': f'Bearer {self.jwt_token}'}
            ) as response:
                response_data = await response.json()
                duration = time.time() - start_time
                
                return {
                    'success': response.status == 200,
                    'status_code': response.status,
                    'duration': duration,
                    'response_size': len(json.dumps(response_data))
                }
        
        except Exception as e:
            duration = time.time() - start_time
            return {
                'success': False,
                'status_code': 0,
                'duration': duration,
                'error': str(e)
            }
    
    async def run_load_test(self, concurrent_requests: int, total_requests: int):
        """Run load test with specified parameters."""
        print(f"Starting load test: {total_requests} requests, {concurrent_requests} concurrent")
        
        # Test data
        test_data = {
            'districts': ['Central district', 'Admiralty']
        }
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def bounded_request(session):
            async with semaphore:
                return await self.make_request(
                    session, 
                    '/api/v1/restaurants/search/district', 
                    test_data
                )
        
        # Run requests
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [bounded_request(session) for _ in range(total_requests)]
            self.results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        successful_requests = sum(1 for r in self.results if r['success'])
        failed_requests = total_requests - successful_requests
        
        durations = [r['duration'] for r in self.results if r['success']]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        requests_per_second = total_requests / total_time
        
        # Print results
        print(f"\n=== Load Test Results ===")
        print(f"Total requests: {total_requests}")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        print(f"Success rate: {successful_requests/total_requests*100:.2f}%")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests per second: {requests_per_second:.2f}")
        print(f"Average response time: {avg_duration*1000:.2f}ms")
        print(f"Min response time: {min_duration*1000:.2f}ms")
        print(f"Max response time: {max_duration*1000:.2f}ms")
        
        # Print error summary
        if failed_requests > 0:
            print(f"\n=== Error Summary ===")
            error_counts = {}
            for result in self.results:
                if not result['success']:
                    error_key = result.get('error', f"HTTP {result['status_code']}")
                    error_counts[error_key] = error_counts.get(error_key, 0) + 1
            
            for error, count in error_counts.items():
                print(f"{error}: {count}")

async def main():
    parser = argparse.ArgumentParser(description='Load test AgentCore Gateway')
    parser.add_argument('--url', required=True, help='Gateway base URL')
    parser.add_argument('--token', required=True, help='JWT token for authentication')
    parser.add_argument('--concurrent', type=int, default=10, help='Concurrent requests')
    parser.add_argument('--total', type=int, default=100, help='Total requests')
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url, args.token)
    await tester.run_load_test(args.concurrent, args.total)

if __name__ == '__main__':
    asyncio.run(main())
```

## Log Analysis

### CloudWatch Logs Analysis

```bash
# View recent logs
aws logs tail /aws/agentcore/agentcore-gateway-mcp-tools/application --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/agentcore/agentcore-gateway-mcp-tools/application \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Search for authentication failures
aws logs filter-log-events \
  --log-group-name /aws/agentcore/agentcore-gateway-mcp-tools/application \
  --filter-pattern "401" \
  --start-time $(date -d '1 hour ago' +%s)000
```

### Log Pattern Analysis

```python
#!/usr/bin/env python3
# analyze_logs.py - Log analysis tool

import re
import json
from collections import defaultdict, Counter
from datetime import datetime

def analyze_log_file(log_file_path):
    """Analyze log file for patterns and issues."""
    
    error_patterns = {
        'auth_failures': r'401.*Unauthorized',
        'validation_errors': r'400.*ValidationError',
        'mcp_timeouts': r'timeout.*mcp',
        'service_unavailable': r'503.*Service Unavailable'
    }
    
    pattern_counts = defaultdict(int)
    error_details = defaultdict(list)
    response_times = []
    
    with open(log_file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            # Extract response time if present
            time_match = re.search(r'response_time["\s:]+(\d+\.?\d*)', line)
            if time_match:
                response_times.append(float(time_match.group(1)))
            
            # Check for error patterns
            for pattern_name, pattern in error_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    pattern_counts[pattern_name] += 1
                    error_details[pattern_name].append({
                        'line': line_num,
                        'content': line.strip()
                    })
    
    # Print analysis results
    print("=== Log Analysis Results ===")
    print(f"Total lines analyzed: {line_num}")
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        print(f"Average response time: {avg_response_time:.2f}ms")
        print(f"Max response time: {max(response_times):.2f}ms")
        print(f"Min response time: {min(response_times):.2f}ms")
    
    print("\n=== Error Pattern Summary ===")
    for pattern_name, count in pattern_counts.items():
        print(f"{pattern_name}: {count}")
        
        # Show first few examples
        if count > 0:
            print("  Examples:")
            for detail in error_details[pattern_name][:3]:
                print(f"    Line {detail['line']}: {detail['content'][:100]}...")
    
    return pattern_counts, error_details

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python analyze_logs.py <log_file_path>")
        sys.exit(1)
    
    analyze_log_file(sys.argv[1])
```

## Common Solutions

### 1. Authentication Token Refresh

```javascript
class TokenManager {
  constructor(authClient) {
    this.authClient = authClient;
    this.refreshPromise = null;
  }

  async getValidToken() {
    const token = this.authClient.getCurrentToken();
    if (!token) {
      throw new Error('No token available');
    }

    // Check if token is expired or expires soon
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000;
    const now = Date.now();
    
    // Refresh if expires in next 5 minutes
    if (exp - now < 5 * 60 * 1000) {
      return this.refreshToken();
    }

    return token;
  }

  async refreshToken() {
    // Prevent multiple concurrent refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.authClient.refreshTokens()
      .then(() => this.authClient.getCurrentToken())
      .finally(() => {
        this.refreshPromise = null;
      });

    return this.refreshPromise;
  }
}
```

### 2. Circuit Breaker Implementation

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self):
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
```

### 3. Request Retry with Exponential Backoff

```python
import asyncio
import random

async def retry_with_backoff(func, max_retries=3, base_delay=1, max_delay=60, jitter=True):
    """Retry function with exponential backoff."""
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            # Calculate delay
            delay = min(base_delay * (2 ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            if jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
            await asyncio.sleep(delay)
```

---

**Last Updated**: January 3, 2025  
**Version**: 1.0.0  
**Coverage**: Comprehensive troubleshooting for deployment, authentication, API requests, MCP connectivity, performance, and diagnostic tools