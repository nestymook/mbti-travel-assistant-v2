# Enhanced MCP Status Check - User Guide

## Overview

The Enhanced MCP Status Check system provides comprehensive health monitoring for MCP servers using dual monitoring approaches: native MCP tools/list requests and RESTful API health checks. This guide will help you configure, deploy, and operate the enhanced monitoring system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Deployment](#deployment)
4. [Monitoring and Alerts](#monitoring-and-alerts)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Access to MCP servers you want to monitor
- AWS credentials configured (if using AWS services)
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd enhanced-mcp-status-check

# Install dependencies
pip install -r requirements.txt

# Run basic health check
python -m enhanced_mcp_status_check.services.enhanced_health_check_service --test
```

### Basic Configuration

Create a configuration file `config/basic_config.json`:

```json
{
  "enhanced_status_check_system": {
    "dual_monitoring_enabled": true,
    "servers": [
      {
        "server_name": "restaurant-search-mcp",
        "mcp_endpoint_url": "http://localhost:8080/mcp",
        "rest_health_endpoint_url": "http://localhost:8080/status/health",
        "mcp_enabled": true,
        "rest_enabled": true
      }
    ],
    "mcp_health_checks": {
      "enabled": true,
      "default_timeout_seconds": 10,
      "tools_list_validation": true,
      "expected_tools_validation": true
    },
    "rest_health_checks": {
      "enabled": true,
      "default_timeout_seconds": 8,
      "health_endpoint_path": "/status/health",
      "metrics_endpoint_path": "/status/metrics"
    }
  }
}
```

### Running Your First Health Check

```python
from enhanced_mcp_status_check.services.enhanced_health_check_service import EnhancedHealthCheckService
from enhanced_mcp_status_check.config.config_loader import ConfigLoader

# Load configuration
config = ConfigLoader.load_config("config/basic_config.json")

# Create health check service
health_service = EnhancedHealthCheckService(config)

# Perform dual health check
result = await health_service.perform_dual_health_check(
    config.servers[0]
)

print(f"Server Status: {result.overall_status}")
print(f"MCP Success: {result.mcp_success}")
print(f"REST Success: {result.rest_success}")
```

## Configuration

### Configuration Structure

The enhanced status check system uses a hierarchical configuration structure:

```json
{
  "enhanced_status_check_system": {
    "dual_monitoring_enabled": true,
    "global_settings": {
      "check_interval_seconds": 30,
      "max_concurrent_checks": 10,
      "retry_attempts": 3,
      "circuit_breaker_enabled": true
    },
    "servers": [...],
    "mcp_health_checks": {...},
    "rest_health_checks": {...},
    "result_aggregation": {...},
    "authentication": {...},
    "observability": {...}
  }
}
```

### Server Configuration

Each server requires both MCP and REST endpoint configuration:

```json
{
  "server_name": "my-mcp-server",
  "mcp_endpoint_url": "http://localhost:8080/mcp",
  "rest_health_endpoint_url": "http://localhost:8080/status/health",
  
  "mcp_enabled": true,
  "mcp_timeout_seconds": 10,
  "mcp_expected_tools": [
    "search_restaurants_by_district",
    "search_restaurants_by_meal_type",
    "recommend_restaurants"
  ],
  "mcp_retry_attempts": 3,
  
  "rest_enabled": true,
  "rest_timeout_seconds": 8,
  "rest_retry_attempts": 2,
  
  "jwt_token": "${JWT_TOKEN}",
  "auth_headers": {
    "Authorization": "Bearer ${API_KEY}",
    "X-API-Version": "v1"
  },
  
  "mcp_priority_weight": 0.6,
  "rest_priority_weight": 0.4,
  "require_both_success": false
}
```

### MCP Health Check Configuration

Configure MCP-specific monitoring settings:

```json
{
  "mcp_health_checks": {
    "enabled": true,
    "default_timeout_seconds": 10,
    "tools_list_validation": true,
    "expected_tools_validation": true,
    "json_rpc_version": "2.0",
    "connection_pool_size": 5,
    "keep_alive_enabled": true,
    "retry_policy": {
      "max_attempts": 3,
      "backoff_multiplier": 2,
      "initial_delay_seconds": 1
    }
  }
}
```

### REST Health Check Configuration

Configure REST API monitoring settings:

```json
{
  "rest_health_checks": {
    "enabled": true,
    "default_timeout_seconds": 8,
    "health_endpoint_path": "/status/health",
    "metrics_endpoint_path": "/status/metrics",
    "expected_status_codes": [200, 201],
    "connection_pool_size": 10,
    "retry_policy": {
      "max_attempts": 2,
      "backoff_multiplier": 1.5,
      "initial_delay_seconds": 0.5
    }
  }
}
```

### Result Aggregation Configuration

Configure how MCP and REST results are combined:

```json
{
  "result_aggregation": {
    "mcp_priority_weight": 0.6,
    "rest_priority_weight": 0.4,
    "require_both_success_for_healthy": false,
    "degraded_on_single_failure": true,
    "health_score_calculation": "weighted_average",
    "failure_threshold_percentage": 50
  }
}
```

### Authentication Configuration

Configure authentication for both MCP and REST requests:

```json
{
  "authentication": {
    "jwt_enabled": true,
    "jwt_discovery_url": "https://cognito-idp.region.amazonaws.com/pool-id/.well-known/openid-configuration",
    "jwt_audience": "client-id",
    "jwt_issuer": "https://cognito-idp.region.amazonaws.com/pool-id",
    "token_refresh_enabled": true,
    "token_cache_ttl_seconds": 3600,
    "api_key_header": "X-API-Key",
    "custom_headers": {
      "User-Agent": "Enhanced-MCP-Status-Check/1.0"
    }
  }
}
```

## Deployment

### Local Development Deployment

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
export MCP_SERVER_URL="http://localhost:8080"
export JWT_TOKEN="your-jwt-token"
export API_KEY="your-api-key"
```

3. **Run Health Check Service**
```bash
python -m enhanced_mcp_status_check.main --config config/development.json
```

### Docker Deployment

1. **Build Docker Image**
```bash
docker build -t enhanced-mcp-status-check:latest .
```

2. **Run Container**
```bash
docker run -d \
  --name enhanced-status-check \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -e JWT_TOKEN="${JWT_TOKEN}" \
  -e API_KEY="${API_KEY}" \
  enhanced-mcp-status-check:latest
```

### Production Deployment

1. **Use Production Configuration**
```json
{
  "enhanced_status_check_system": {
    "dual_monitoring_enabled": true,
    "global_settings": {
      "check_interval_seconds": 15,
      "max_concurrent_checks": 20,
      "retry_attempts": 5,
      "circuit_breaker_enabled": true
    },
    "observability": {
      "metrics_enabled": true,
      "logging_level": "INFO",
      "tracing_enabled": true,
      "health_check_endpoint": "/health"
    }
  }
}
```

2. **Deploy with Load Balancer**
```bash
# Deploy multiple instances behind load balancer
docker-compose up -d --scale enhanced-status-check=3
```

3. **Configure Monitoring**
```bash
# Set up Prometheus metrics collection
curl http://localhost:8080/metrics

# Configure alerting rules
kubectl apply -f k8s/alerting-rules.yaml
```

## Monitoring and Alerts

### Health Check Endpoints

The system exposes several endpoints for monitoring:

- `GET /status/health` - Overall system health
- `GET /status/servers` - All server statuses
- `GET /status/servers/{server_name}` - Specific server status
- `GET /status/metrics` - Prometheus metrics
- `GET /status/dual-check` - Manual dual health check

### Metrics Collection

Key metrics collected by the system:

```python
# Response time metrics
mcp_response_time_seconds
rest_response_time_seconds
combined_response_time_seconds

# Success rate metrics
mcp_success_rate
rest_success_rate
overall_success_rate

# Tool validation metrics
mcp_tools_count
mcp_expected_tools_found
mcp_missing_tools_count

# Circuit breaker metrics
circuit_breaker_state
circuit_breaker_failures
circuit_breaker_successes
```

### Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
  - name: enhanced-mcp-status-check
    rules:
      - alert: MCPServerDown
        expr: mcp_success_rate < 0.5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "MCP server {{ $labels.server_name }} is down"
          
      - alert: RESTHealthCheckFailing
        expr: rest_success_rate < 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "REST health check failing for {{ $labels.server_name }}"
          
      - alert: DualMonitoringDegraded
        expr: overall_success_rate < 0.8
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Dual monitoring degraded for {{ $labels.server_name }}"
```

## Troubleshooting

### Common Issues

#### MCP Connection Failures

**Symptoms:**
- MCP health checks consistently fail
- "Connection refused" errors in logs
- MCP tools/list requests timeout

**Solutions:**
1. Verify MCP server is running and accessible
2. Check network connectivity and firewall rules
3. Validate MCP endpoint URL configuration
4. Increase timeout values if needed

```bash
# Test MCP connectivity manually
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

#### REST Health Check Issues

**Symptoms:**
- REST health checks return 404 or 500 errors
- Authentication failures
- Slow response times

**Solutions:**
1. Verify REST health endpoint exists and is accessible
2. Check authentication credentials and headers
3. Validate expected response format
4. Review server logs for errors

```bash
# Test REST endpoint manually
curl -H "Authorization: Bearer ${JWT_TOKEN}" \
  http://localhost:8080/status/health
```

#### Authentication Problems

**Symptoms:**
- 401 Unauthorized errors
- JWT token validation failures
- API key rejection

**Solutions:**
1. Verify JWT token is valid and not expired
2. Check JWT discovery URL and audience configuration
3. Validate API key and custom headers
4. Enable token refresh if supported

```python
# Debug JWT token
import jwt
token = "your-jwt-token"
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"Token expires: {decoded.get('exp')}")
print(f"Token audience: {decoded.get('aud')}")
```

#### Performance Issues

**Symptoms:**
- Slow health check responses
- High CPU or memory usage
- Connection pool exhaustion

**Solutions:**
1. Optimize connection pool settings
2. Reduce check frequency for stable servers
3. Enable caching for authentication tokens
4. Scale horizontally with multiple instances

### Debug Mode

Enable debug mode for detailed logging:

```json
{
  "observability": {
    "logging_level": "DEBUG",
    "debug_mode": true,
    "request_response_logging": true
  }
}
```

### Log Analysis

Key log patterns to monitor:

```bash
# MCP connection issues
grep "MCP connection failed" logs/enhanced-status-check.log

# REST health check failures
grep "REST health check failed" logs/enhanced-status-check.log

# Authentication errors
grep "Authentication failed" logs/enhanced-status-check.log

# Circuit breaker state changes
grep "Circuit breaker" logs/enhanced-status-check.log
```

## Best Practices

### Configuration Management

1. **Use Environment Variables**
   - Store sensitive data in environment variables
   - Use configuration templates with variable substitution
   - Separate configuration by environment (dev/staging/prod)

2. **Validate Configuration**
   - Use configuration validation before deployment
   - Test configuration changes in staging first
   - Maintain configuration version control

3. **Security**
   - Rotate authentication tokens regularly
   - Use least privilege access principles
   - Encrypt sensitive configuration data

### Monitoring Strategy

1. **Baseline Establishment**
   - Monitor servers for 1-2 weeks to establish baselines
   - Set alert thresholds based on historical data
   - Adjust check frequencies based on server stability

2. **Alerting Hierarchy**
   - Critical: Both MCP and REST checks failing
   - Warning: Single check type failing consistently
   - Info: Temporary failures or degraded performance

3. **Dashboard Design**
   - Show overall system health prominently
   - Provide drill-down capabilities for detailed analysis
   - Include trend analysis and historical data

### Performance Optimization

1. **Connection Management**
   - Use connection pooling for both MCP and REST
   - Configure appropriate pool sizes based on load
   - Enable keep-alive connections where possible

2. **Caching Strategy**
   - Cache authentication tokens until expiration
   - Cache configuration data with hot-reloading
   - Use response caching for stable endpoints

3. **Resource Management**
   - Monitor memory usage and implement limits
   - Use async/await for concurrent operations
   - Implement graceful degradation under load

### Operational Excellence

1. **Documentation**
   - Maintain up-to-date runbooks
   - Document all configuration options
   - Create troubleshooting guides for common issues

2. **Testing**
   - Test configuration changes in staging
   - Perform regular disaster recovery drills
   - Validate monitoring and alerting systems

3. **Continuous Improvement**
   - Review metrics and alerts regularly
   - Optimize based on operational experience
   - Update documentation based on lessons learned

## Advanced Features

### Custom Health Check Logic

Implement custom health check logic for specific requirements:

```python
from enhanced_mcp_status_check.services.enhanced_health_check_service import EnhancedHealthCheckService

class CustomHealthCheckService(EnhancedHealthCheckService):
    async def custom_validation(self, server_config, mcp_result, rest_result):
        """Custom validation logic for specific business requirements."""
        # Implement custom logic here
        if server_config.server_name == "critical-server":
            # Require both checks to succeed for critical servers
            return mcp_result.success and rest_result.success
        return super().determine_overall_status(mcp_result, rest_result)
```

### Integration with External Systems

Integrate with external monitoring and alerting systems:

```python
# Webhook integration
async def send_webhook_alert(server_name, status, details):
    webhook_url = "https://hooks.slack.com/services/..."
    payload = {
        "text": f"Server {server_name} status: {status}",
        "details": details
    }
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)

# PagerDuty integration
async def trigger_pagerduty_incident(server_name, severity):
    pd_client = pypd.PagerDuty(api_token="your-token")
    incident = pd_client.Incident.create(
        title=f"MCP Server {server_name} Health Check Failed",
        service_id="your-service-id",
        urgency=severity
    )
```

### Multi-Region Deployment

Deploy across multiple regions for high availability:

```yaml
# docker-compose.multi-region.yml
version: '3.8'
services:
  enhanced-status-check-us-east-1:
    image: enhanced-mcp-status-check:latest
    environment:
      - AWS_REGION=us-east-1
      - CONFIG_FILE=config/us-east-1.json
    
  enhanced-status-check-us-west-2:
    image: enhanced-mcp-status-check:latest
    environment:
      - AWS_REGION=us-west-2
      - CONFIG_FILE=config/us-west-2.json
```

## Support and Resources

### Getting Help

- **Documentation**: Check this user guide and API documentation
- **Troubleshooting**: Review the troubleshooting guide
- **Examples**: See the examples directory for sample configurations
- **Issues**: Report bugs and feature requests on GitHub

### Additional Resources

- [Developer Documentation](DEVELOPER_GUIDE.md)
- [API Reference](API_DOCUMENTATION.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
- [Configuration Examples](../config/examples/)

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Maintainers**: Enhanced MCP Status Check Team