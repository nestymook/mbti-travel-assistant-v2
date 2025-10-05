# Enhanced MCP Status Check - Troubleshooting Guide

## Overview

This troubleshooting guide provides solutions for common issues encountered when using the Enhanced MCP Status Check system. The guide is organized by problem category and includes diagnostic steps, solutions, and prevention strategies.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [MCP Health Check Issues](#mcp-health-check-issues)
3. [REST Health Check Issues](#rest-health-check-issues)
4. [Authentication Problems](#authentication-problems)
5. [Configuration Issues](#configuration-issues)
6. [Performance Problems](#performance-problems)
7. [Circuit Breaker Issues](#circuit-breaker-issues)
8. [Metrics and Monitoring Issues](#metrics-and-monitoring-issues)
9. [Deployment Problems](#deployment-problems)
10. [Advanced Troubleshooting](#advanced-troubleshooting)

## Quick Diagnostics

### Health Check Status

First, check the overall system status:

```bash
# Check system health
curl http://localhost:8080/status/health

# Check specific server status
curl http://localhost:8080/status/servers/restaurant-search-mcp

# Check metrics
curl http://localhost:8080/status/metrics
```

### Log Analysis

Enable debug logging and check for common patterns:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check logs for common issues
tail -f logs/enhanced-status-check.log | grep -E "(ERROR|WARN|Failed|Timeout)"

# Filter by component
grep "MCP Health Check" logs/enhanced-status-check.log
grep "REST Health Check" logs/enhanced-status-check.log
grep "Circuit Breaker" logs/enhanced-status-check.log
```

### Configuration Validation

Validate your configuration:

```python
from enhanced_mcp_status_check.config.config_validator import ConfigValidator

validator = ConfigValidator()
errors = validator.validate_config("config/your-config.json")
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
```

## MCP Health Check Issues

### Issue: MCP Connection Refused

**Symptoms:**
- MCP health checks consistently fail
- Error messages: "Connection refused", "Connection timeout"
- MCP success rate is 0%

**Diagnostic Steps:**

1. **Verify MCP Server Status**
```bash
# Check if MCP server is running
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

2. **Check Network Connectivity**
```bash
# Test basic connectivity
telnet localhost 8080

# Check DNS resolution
nslookup your-mcp-server.com

# Test with different timeout
curl -m 30 http://localhost:8080/mcp
```

3. **Verify Configuration**
```json
{
  "server_name": "your-server",
  "mcp_endpoint_url": "http://localhost:8080/mcp",  // Correct URL?
  "mcp_enabled": true,  // Enabled?
  "mcp_timeout_seconds": 10  // Sufficient timeout?
}
```

**Solutions:**

1. **Start MCP Server**
```bash
# If server is not running
python -m your_mcp_server --port 8080
```

2. **Fix Network Issues**
```bash
# Check firewall rules
sudo ufw status
sudo iptables -L

# Check port binding
netstat -tlnp | grep 8080
```

3. **Update Configuration**
```json
{
  "mcp_endpoint_url": "http://correct-host:correct-port/mcp",
  "mcp_timeout_seconds": 30,
  "mcp_retry_attempts": 3
}
```

### Issue: MCP Tools/List Validation Failures

**Symptoms:**
- MCP connection succeeds but validation fails
- Missing expected tools in response
- Tools count mismatch

**Diagnostic Steps:**

1. **Check Tools/List Response**
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | jq .
```

2. **Compare Expected vs Actual Tools**
```python
# Debug tool validation
from enhanced_mcp_status_check.services.mcp_health_check_client import MCPHealthCheckClient

client = MCPHealthCheckClient()
response = await client.send_tools_list_request(
    "http://localhost:8080/mcp", {}, 10
)
print(f"Found tools: {response.tools_list}")
print(f"Expected tools: {expected_tools}")
```

**Solutions:**

1. **Update Expected Tools List**
```json
{
  "mcp_expected_tools": [
    "search_restaurants_by_district",
    "search_restaurants_by_meal_type",
    "recommend_restaurants"
  ]
}
```

2. **Fix MCP Server Tool Registration**
```python
# In your MCP server
@mcp_server.tool()
def search_restaurants_by_district(district: str) -> dict:
    """Search restaurants by district."""
    pass

# Ensure all expected tools are registered
```

3. **Disable Tool Validation (Temporary)**
```json
{
  "mcp_health_checks": {
    "tools_list_validation": false,
    "expected_tools_validation": false
  }
}
```

### Issue: MCP JSON-RPC Protocol Errors

**Symptoms:**
- Invalid JSON-RPC responses
- Protocol version mismatches
- Malformed requests/responses

**Diagnostic Steps:**

1. **Validate JSON-RPC Format**
```bash
# Check response format
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python -m json.tool
```

2. **Check Protocol Version**
```python
# Verify JSON-RPC version
response = await mcp_client.send_tools_list_request(...)
print(f"JSON-RPC version: {response.jsonrpc}")
```

**Solutions:**

1. **Fix MCP Server JSON-RPC Implementation**
```python
# Ensure proper JSON-RPC 2.0 format
{
    "jsonrpc": "2.0",
    "id": request_id,
    "result": {
        "tools": [...]
    }
}
```

2. **Update Client Configuration**
```json
{
  "mcp_health_checks": {
    "json_rpc_version": "2.0"
  }
}
```

## REST Health Check Issues

### Issue: REST Endpoint Not Found (404)

**Symptoms:**
- REST health checks return 404 errors
- Health endpoint not accessible
- REST success rate is 0%

**Diagnostic Steps:**

1. **Verify Endpoint Exists**
```bash
# Test health endpoint
curl -v http://localhost:8080/status/health

# Check available endpoints
curl http://localhost:8080/
```

2. **Check Server Routes**
```python
# In your server code, ensure health endpoint is registered
@app.get("/status/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

**Solutions:**

1. **Implement Health Endpoint**
```python
# FastAPI example
from fastapi import FastAPI

app = FastAPI()

@app.get("/status/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

2. **Update Configuration**
```json
{
  "rest_health_endpoint_url": "http://localhost:8080/health",  // Correct path
  "rest_health_checks": {
    "health_endpoint_path": "/health"  // Match server implementation
  }
}
```

### Issue: REST Authentication Failures (401/403)

**Symptoms:**
- REST health checks return 401 or 403 errors
- Authentication headers rejected
- API key validation failures

**Diagnostic Steps:**

1. **Test Authentication Manually**
```bash
# Test with authentication headers
curl -H "Authorization: Bearer your-token" \
     -H "X-API-Key: your-api-key" \
     http://localhost:8080/status/health
```

2. **Verify Token Validity**
```python
# Check JWT token
import jwt
token = "your-jwt-token"
try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(f"Token expires: {decoded.get('exp')}")
    print(f"Current time: {time.time()}")
except Exception as e:
    print(f"Token error: {e}")
```

**Solutions:**

1. **Update Authentication Configuration**
```json
{
  "auth_headers": {
    "Authorization": "Bearer ${JWT_TOKEN}",
    "X-API-Key": "${API_KEY}",
    "Content-Type": "application/json"
  }
}
```

2. **Refresh Authentication Tokens**
```bash
# Set environment variables
export JWT_TOKEN="new-valid-token"
export API_KEY="new-valid-api-key"
```

3. **Configure Token Refresh**
```json
{
  "authentication": {
    "token_refresh_enabled": true,
    "token_cache_ttl_seconds": 3600
  }
}
```

### Issue: REST Response Format Validation

**Symptoms:**
- REST endpoint returns 200 but validation fails
- Unexpected response format
- Missing required fields

**Diagnostic Steps:**

1. **Check Response Format**
```bash
curl http://localhost:8080/status/health | jq .
```

2. **Validate Against Expected Schema**
```python
# Expected format
{
    "status": "healthy|degraded|unhealthy",
    "timestamp": "2025-10-01T12:00:00Z",
    "metrics": {...}
}
```

**Solutions:**

1. **Fix Server Response Format**
```python
@app.get("/status/health")
async def health_check():
    return {
        "status": "healthy",  # Required field
        "timestamp": datetime.utcnow().isoformat(),  # Required field
        "metrics": {
            "response_time": 0.1,
            "memory_usage": 0.5
        }
    }
```

2. **Update Validation Rules**
```json
{
  "rest_health_checks": {
    "expected_status_codes": [200, 201],
    "required_fields": ["status", "timestamp"]
  }
}
```

## Authentication Problems

### Issue: JWT Token Validation Failures

**Symptoms:**
- JWT authentication consistently fails
- Token signature validation errors
- Discovery URL issues

**Diagnostic Steps:**

1. **Test JWT Discovery URL**
```bash
# Test OIDC discovery endpoint
curl https://cognito-idp.region.amazonaws.com/pool-id/.well-known/openid-configuration
```

2. **Validate Token Format**
```python
import jwt
import json

token = "your-jwt-token"
header = jwt.get_unverified_header(token)
payload = jwt.decode(token, options={"verify_signature": False})

print(f"Header: {json.dumps(header, indent=2)}")
print(f"Payload: {json.dumps(payload, indent=2)}")
```

**Solutions:**

1. **Fix Discovery URL Format**
```json
{
  "authentication": {
    "jwt_discovery_url": "https://cognito-idp.region.amazonaws.com/pool-id/.well-known/openid-configuration"
  }
}
```

2. **Update JWT Configuration**
```json
{
  "authentication": {
    "jwt_audience": "correct-client-id",
    "jwt_issuer": "https://cognito-idp.region.amazonaws.com/pool-id"
  }
}
```

### Issue: API Key Authentication Problems

**Symptoms:**
- API key rejected by server
- Header format issues
- Key rotation problems

**Solutions:**

1. **Verify API Key Format**
```json
{
  "auth_headers": {
    "X-API-Key": "your-api-key",  // Correct header name
    "Authorization": "ApiKey your-api-key"  // Alternative format
  }
}
```

2. **Implement Key Rotation**
```python
# Automatic key rotation
async def refresh_api_key():
    new_key = await get_new_api_key()
    config.auth_headers["X-API-Key"] = new_key
```

## Configuration Issues

### Issue: Configuration File Not Found

**Symptoms:**
- "Configuration file not found" errors
- Default configuration used unexpectedly
- Missing configuration sections

**Solutions:**

1. **Verify File Path**
```bash
# Check file exists
ls -la config/your-config.json

# Use absolute path
export CONFIG_FILE="/absolute/path/to/config.json"
```

2. **Create Missing Configuration**
```bash
# Copy from example
cp config/examples/default_config.json config/production.json
```

### Issue: Configuration Validation Errors

**Symptoms:**
- Configuration validation failures
- Missing required fields
- Invalid configuration values

**Diagnostic Steps:**

```python
from enhanced_mcp_status_check.config.config_validator import ConfigValidator

validator = ConfigValidator()
errors = validator.validate_config("config/your-config.json")
for error in errors:
    print(f"Error: {error}")
```

**Solutions:**

1. **Fix Configuration Structure**
```json
{
  "enhanced_status_check_system": {  // Required root key
    "dual_monitoring_enabled": true,
    "servers": [  // Required array
      {
        "server_name": "required-field",
        "mcp_endpoint_url": "required-field",
        "rest_health_endpoint_url": "required-field"
      }
    ]
  }
}
```

2. **Use Configuration Schema Validation**
```bash
# Validate against schema
python -m enhanced_mcp_status_check.config.config_validator config/your-config.json
```

## Performance Problems

### Issue: Slow Health Check Response Times

**Symptoms:**
- Health checks taking longer than expected
- Timeout errors
- High response times in metrics

**Diagnostic Steps:**

1. **Measure Component Performance**
```python
import time

start_time = time.time()
result = await health_service.perform_dual_health_check(server_config)
end_time = time.time()

print(f"Total time: {end_time - start_time:.2f}s")
print(f"MCP time: {result.mcp_response_time_ms}ms")
print(f"REST time: {result.rest_response_time_ms}ms")
```

2. **Check Network Latency**
```bash
# Test network latency
ping your-server.com
traceroute your-server.com
```

**Solutions:**

1. **Optimize Timeouts**
```json
{
  "mcp_timeout_seconds": 5,  // Reduce if servers are fast
  "rest_timeout_seconds": 3,
  "global_settings": {
    "max_concurrent_checks": 20  // Increase for better parallelism
  }
}
```

2. **Enable Connection Pooling**
```json
{
  "mcp_health_checks": {
    "connection_pool_size": 10,
    "keep_alive_enabled": true
  },
  "rest_health_checks": {
    "connection_pool_size": 20
  }
}
```

3. **Implement Caching**
```json
{
  "authentication": {
    "token_cache_ttl_seconds": 3600
  },
  "result_caching": {
    "enabled": true,
    "ttl_seconds": 30
  }
}
```

### Issue: High Memory Usage

**Symptoms:**
- Memory usage continuously increasing
- Out of memory errors
- Slow garbage collection

**Diagnostic Steps:**

```python
import psutil
import gc

# Check memory usage
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# Force garbage collection
gc.collect()
print(f"Objects in memory: {len(gc.get_objects())}")
```

**Solutions:**

1. **Limit Result History**
```json
{
  "metrics_collection": {
    "max_history_entries": 1000,
    "cleanup_interval_seconds": 300
  }
}
```

2. **Optimize Connection Pools**
```json
{
  "connection_pool_settings": {
    "max_pool_size": 10,
    "pool_timeout_seconds": 30
  }
}
```

## Circuit Breaker Issues

### Issue: Circuit Breaker Stuck Open

**Symptoms:**
- Circuit breaker remains open despite server recovery
- Health checks not being attempted
- False positive failures

**Diagnostic Steps:**

```python
# Check circuit breaker state
circuit_state = await circuit_breaker.get_circuit_state("server-name")
print(f"MCP Circuit: {'OPEN' if circuit_state.mcp_circuit_open else 'CLOSED'}")
print(f"REST Circuit: {'OPEN' if circuit_state.rest_circuit_open else 'CLOSED'}")
print(f"Failure count: {circuit_state.failure_count}")
```

**Solutions:**

1. **Adjust Circuit Breaker Thresholds**
```json
{
  "circuit_breaker": {
    "failure_threshold": 10,  // Increase threshold
    "success_threshold": 3,   // Reduce success requirement
    "timeout_seconds": 60     // Reduce timeout
  }
}
```

2. **Manual Circuit Reset**
```python
# Reset circuit breaker
await circuit_breaker.reset_circuit("server-name")
```

3. **Disable Circuit Breaker Temporarily**
```json
{
  "global_settings": {
    "circuit_breaker_enabled": false
  }
}
```

### Issue: Circuit Breaker False Positives

**Symptoms:**
- Circuit breaker opens for healthy servers
- Intermittent failures trigger circuit opening
- Over-sensitive failure detection

**Solutions:**

1. **Tune Sensitivity**
```json
{
  "circuit_breaker": {
    "failure_threshold": 5,
    "failure_rate_threshold": 0.5,  // 50% failure rate required
    "minimum_requests": 10          // Minimum requests before evaluation
  }
}
```

2. **Implement Adaptive Thresholds**
```python
class AdaptiveCircuitBreaker(EnhancedCircuitBreaker):
    def calculate_adaptive_threshold(self, server_name: str) -> int:
        # Calculate based on historical performance
        history = self.get_server_history(server_name)
        return max(5, int(history.average_failures * 1.5))
```

## Metrics and Monitoring Issues

### Issue: Missing Metrics Data

**Symptoms:**
- Metrics endpoints return empty data
- Prometheus scraping failures
- Dashboard shows no data

**Diagnostic Steps:**

```bash
# Check metrics endpoint
curl http://localhost:8080/status/metrics

# Verify Prometheus format
curl http://localhost:8080/metrics | grep mcp_
```

**Solutions:**

1. **Enable Metrics Collection**
```json
{
  "observability": {
    "metrics_enabled": true,
    "prometheus_enabled": true,
    "metrics_port": 9090
  }
}
```

2. **Fix Metrics Registration**
```python
# Ensure metrics are properly registered
from prometheus_client import Counter, Histogram

mcp_requests_total = Counter('mcp_requests_total', 'Total MCP requests')
mcp_response_time = Histogram('mcp_response_time_seconds', 'MCP response time')
```

### Issue: Incorrect Metrics Values

**Symptoms:**
- Metrics show unexpected values
- Success rates don't match logs
- Response times seem wrong

**Solutions:**

1. **Verify Metrics Calculation**
```python
# Debug metrics calculation
metrics = metrics_collector.get_server_metrics("server-name")
print(f"Total checks: {metrics['total_checks']}")
print(f"Successful checks: {metrics['successful_checks']}")
print(f"Success rate: {metrics['success_rate']}")
```

2. **Reset Metrics State**
```python
# Clear metrics history
metrics_collector.reset_metrics("server-name")
```

## Deployment Problems

### Issue: Docker Container Startup Failures

**Symptoms:**
- Container exits immediately
- Configuration not found in container
- Port binding failures

**Diagnostic Steps:**

```bash
# Check container logs
docker logs enhanced-status-check

# Inspect container
docker exec -it enhanced-status-check /bin/bash

# Check port binding
docker port enhanced-status-check
```

**Solutions:**

1. **Fix Volume Mounts**
```bash
docker run -d \
  --name enhanced-status-check \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  enhanced-mcp-status-check:latest
```

2. **Set Environment Variables**
```bash
docker run -d \
  -e CONFIG_FILE=/app/config/production.json \
  -e LOG_LEVEL=INFO \
  -e JWT_TOKEN="${JWT_TOKEN}" \
  enhanced-mcp-status-check:latest
```

### Issue: Kubernetes Deployment Problems

**Symptoms:**
- Pods failing to start
- Service discovery issues
- ConfigMap not mounted

**Solutions:**

1. **Fix ConfigMap**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: enhanced-status-config
data:
  config.json: |
    {
      "enhanced_status_check_system": {
        ...
      }
    }
```

2. **Update Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-status-check
spec:
  template:
    spec:
      containers:
      - name: enhanced-status-check
        image: enhanced-mcp-status-check:latest
        volumeMounts:
        - name: config
          mountPath: /app/config
        env:
        - name: CONFIG_FILE
          value: /app/config/config.json
      volumes:
      - name: config
        configMap:
          name: enhanced-status-config
```

## Advanced Troubleshooting

### Debug Mode

Enable comprehensive debugging:

```json
{
  "observability": {
    "logging_level": "DEBUG",
    "debug_mode": true,
    "request_response_logging": true,
    "performance_profiling": true
  }
}
```

### Network Debugging

Use network debugging tools:

```bash
# Capture network traffic
sudo tcpdump -i any -w health-check.pcap port 8080

# Analyze with Wireshark
wireshark health-check.pcap

# Use curl with verbose output
curl -v -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Performance Profiling

Profile application performance:

```python
import cProfile
import pstats

# Profile health check execution
profiler = cProfile.Profile()
profiler.enable()

result = await health_service.perform_dual_health_check(server_config)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Debugging

Debug memory issues:

```python
import tracemalloc
import gc

# Start memory tracing
tracemalloc.start()

# Perform operations
await health_service.check_multiple_servers_dual(servers)

# Get memory statistics
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")

# Find memory leaks
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

## Getting Help

### Log Collection

When reporting issues, collect relevant logs:

```bash
# Collect system logs
journalctl -u enhanced-status-check > system.log

# Collect application logs
tar -czf logs.tar.gz logs/

# Collect configuration
cp config/production.json config-sanitized.json
# Remove sensitive data from config-sanitized.json
```

### Issue Reporting Template

When reporting issues, include:

1. **Environment Information**
   - Operating system and version
   - Python version
   - Docker version (if applicable)
   - Kubernetes version (if applicable)

2. **Configuration**
   - Sanitized configuration file
   - Environment variables (without secrets)

3. **Error Details**
   - Complete error messages
   - Stack traces
   - Relevant log entries

4. **Reproduction Steps**
   - Minimal steps to reproduce the issue
   - Expected vs actual behavior

5. **Diagnostic Information**
   - Health check endpoint responses
   - Metrics data
   - Network connectivity tests

### Support Resources

- **Documentation**: Check user guide and API documentation
- **Examples**: Review configuration examples
- **Community**: Join discussions and forums
- **Issues**: Report bugs on GitHub

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Maintainers**: Enhanced MCP Status Check Support Team