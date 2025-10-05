# Enhanced MCP Status Check - API Documentation

## Overview

The Enhanced MCP Status Check system provides a comprehensive REST API for monitoring MCP servers using dual monitoring approaches. This API documentation covers all available endpoints, request/response formats, and usage examples.

## Table of Contents

1. [Base URL and Authentication](#base-url-and-authentication)
2. [Health Check Endpoints](#health-check-endpoints)
3. [Server Status Endpoints](#server-status-endpoints)
4. [Metrics Endpoints](#metrics-endpoints)
5. [Configuration Endpoints](#configuration-endpoints)
6. [Circuit Breaker Endpoints](#circuit-breaker-endpoints)
7. [Administrative Endpoints](#administrative-endpoints)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

## Base URL and Authentication

### Base URL
```
http://localhost:8080
```

### Authentication

The API supports multiple authentication methods:

#### API Key Authentication
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8080/status/health
```

#### JWT Bearer Token
```bash
curl -H "Authorization: Bearer your-jwt-token" http://localhost:8080/status/health
```

#### No Authentication (Development)
```bash
curl http://localhost:8080/status/health
```

## Health Check Endpoints

### GET /status/health

Get overall system health status.

**Response Format:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-10-01T12:00:00Z",
  "system_info": {
    "version": "1.0.0",
    "uptime_seconds": 3600,
    "dual_monitoring_enabled": true
  },
  "overall_metrics": {
    "total_servers": 3,
    "healthy_servers": 2,
    "degraded_servers": 1,
    "unhealthy_servers": 0,
    "overall_success_rate": 0.85,
    "average_response_time_ms": 150.5
  },
  "monitoring_summary": {
    "mcp_monitoring": {
      "enabled": true,
      "success_rate": 0.90,
      "average_response_time_ms": 120.3
    },
    "rest_monitoring": {
      "enabled": true,
      "success_rate": 0.80,
      "average_response_time_ms": 180.7
    }
  }
}
```

**Status Codes:**
- `200 OK` - System is operational
- `503 Service Unavailable` - System is unhealthy
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - System error

**Example:**
```bash
curl -X GET http://localhost:8080/status/health \
  -H "Accept: application/json"
```

### GET /status/health/detailed

Get detailed system health with individual server statuses.

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T12:00:00Z",
  "system_info": {
    "version": "1.0.0",
    "uptime_seconds": 3600,
    "dual_monitoring_enabled": true
  },
  "servers": [
    {
      "server_name": "restaurant-search-mcp",
      "overall_status": "healthy",
      "overall_success": true,
      "mcp_result": {
        "success": true,
        "response_time_ms": 120.5,
        "tools_count": 3,
        "expected_tools_found": ["search_restaurants_by_district", "recommend_restaurants"],
        "missing_tools": []
      },
      "rest_result": {
        "success": true,
        "response_time_ms": 85.2,
        "status_code": 200,
        "server_metrics": {
          "cpu_usage": 0.25,
          "memory_usage": 0.45
        }
      },
      "combined_response_time_ms": 102.8,
      "health_score": 0.95,
      "available_paths": ["mcp", "rest"]
    }
  ],
  "circuit_breaker_states": {
    "restaurant-search-mcp": {
      "mcp_circuit_open": false,
      "rest_circuit_open": false,
      "overall_circuit_open": false
    }
  }
}
```

## Server Status Endpoints

### GET /status/servers

Get status of all monitored servers.

**Query Parameters:**
- `include_history` (boolean, optional) - Include historical data
- `limit` (integer, optional) - Limit number of history entries (default: 10)

**Response Format:**
```json
{
  "servers": [
    {
      "server_name": "restaurant-search-mcp",
      "current_status": {
        "overall_status": "healthy",
        "timestamp": "2025-10-01T12:00:00Z",
        "mcp_success": true,
        "rest_success": true,
        "response_time_ms": 102.8
      },
      "history": [
        {
          "timestamp": "2025-10-01T11:59:00Z",
          "overall_status": "healthy",
          "mcp_success": true,
          "rest_success": true,
          "response_time_ms": 98.3
        }
      ]
    }
  ],
  "summary": {
    "total_servers": 3,
    "healthy_count": 2,
    "degraded_count": 1,
    "unhealthy_count": 0
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8080/status/servers?include_history=true&limit=5" \
  -H "Accept: application/json"
```

### GET /status/servers/{server_name}

Get detailed status for a specific server.

**Path Parameters:**
- `server_name` (string, required) - Name of the server

**Response Format:**
```json
{
  "server_name": "restaurant-search-mcp",
  "current_status": {
    "overall_status": "healthy",
    "overall_success": true,
    "timestamp": "2025-10-01T12:00:00Z",
    "mcp_result": {
      "success": true,
      "response_time_ms": 120.5,
      "tools_count": 3,
      "tools_list_response": {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
          "tools": [
            {
              "name": "search_restaurants_by_district",
              "description": "Search restaurants by district"
            }
          ]
        }
      },
      "expected_tools_found": ["search_restaurants_by_district"],
      "missing_tools": [],
      "validation_errors": []
    },
    "rest_result": {
      "success": true,
      "response_time_ms": 85.2,
      "status_code": 200,
      "response_body": {
        "status": "healthy",
        "timestamp": "2025-10-01T12:00:00Z",
        "metrics": {
          "cpu_usage": 0.25,
          "memory_usage": 0.45,
          "active_connections": 12
        }
      },
      "health_endpoint_url": "http://localhost:8080/status/health"
    },
    "combined_response_time_ms": 102.8,
    "health_score": 0.95,
    "available_paths": ["mcp", "rest"]
  },
  "configuration": {
    "mcp_enabled": true,
    "rest_enabled": true,
    "mcp_timeout_seconds": 10,
    "rest_timeout_seconds": 8,
    "mcp_priority_weight": 0.6,
    "rest_priority_weight": 0.4
  },
  "circuit_breaker_state": {
    "mcp_circuit_open": false,
    "rest_circuit_open": false,
    "overall_circuit_open": false,
    "failure_count": 0,
    "last_failure_time": null
  }
}
```

**Status Codes:**
- `200 OK` - Server found and status retrieved
- `404 Not Found` - Server not found
- `401 Unauthorized` - Authentication required

**Example:**
```bash
curl -X GET http://localhost:8080/status/servers/restaurant-search-mcp \
  -H "Accept: application/json"
```

### POST /status/servers/{server_name}/check

Trigger manual health check for a specific server.

**Path Parameters:**
- `server_name` (string, required) - Name of the server

**Request Body (optional):**
```json
{
  "check_types": ["mcp", "rest"],
  "timeout_override": {
    "mcp_timeout_seconds": 15,
    "rest_timeout_seconds": 10
  }
}
```

**Response Format:**
```json
{
  "server_name": "restaurant-search-mcp",
  "check_triggered": true,
  "timestamp": "2025-10-01T12:00:00Z",
  "result": {
    "overall_status": "healthy",
    "overall_success": true,
    "mcp_result": {
      "success": true,
      "response_time_ms": 115.3
    },
    "rest_result": {
      "success": true,
      "response_time_ms": 92.1
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/status/servers/restaurant-search-mcp/check \
  -H "Content-Type: application/json" \
  -d '{"check_types": ["mcp", "rest"]}'
```

## Metrics Endpoints

### GET /status/metrics

Get comprehensive metrics for all servers.

**Query Parameters:**
- `format` (string, optional) - Response format: `json` (default) or `prometheus`
- `server_name` (string, optional) - Filter by specific server
- `time_range` (string, optional) - Time range: `1h`, `24h`, `7d` (default: `1h`)

**Response Format (JSON):**
```json
{
  "timestamp": "2025-10-01T12:00:00Z",
  "time_range": "1h",
  "global_metrics": {
    "total_checks_performed": 1200,
    "successful_checks": 1020,
    "failed_checks": 180,
    "overall_success_rate": 0.85,
    "average_response_time_ms": 145.7
  },
  "mcp_metrics": {
    "total_mcp_checks": 600,
    "successful_mcp_checks": 540,
    "failed_mcp_checks": 60,
    "mcp_success_rate": 0.90,
    "average_mcp_response_time_ms": 125.3,
    "tools_validation_success_rate": 0.95
  },
  "rest_metrics": {
    "total_rest_checks": 600,
    "successful_rest_checks": 480,
    "failed_rest_checks": 120,
    "rest_success_rate": 0.80,
    "average_rest_response_time_ms": 166.1,
    "status_code_distribution": {
      "200": 480,
      "404": 20,
      "500": 100
    }
  },
  "server_metrics": {
    "restaurant-search-mcp": {
      "total_checks": 400,
      "success_rate": 0.88,
      "average_response_time_ms": 135.2,
      "mcp_metrics": {
        "success_rate": 0.92,
        "average_response_time_ms": 120.5,
        "tools_count": 3
      },
      "rest_metrics": {
        "success_rate": 0.84,
        "average_response_time_ms": 149.9,
        "last_status_code": 200
      }
    }
  },
  "circuit_breaker_metrics": {
    "total_circuit_opens": 5,
    "total_circuit_closes": 4,
    "currently_open_circuits": 1
  }
}
```

**Response Format (Prometheus):**
```
# HELP mcp_requests_total Total number of MCP requests
# TYPE mcp_requests_total counter
mcp_requests_total{server="restaurant-search-mcp",status="success"} 540
mcp_requests_total{server="restaurant-search-mcp",status="failure"} 60

# HELP mcp_response_time_seconds MCP response time in seconds
# TYPE mcp_response_time_seconds histogram
mcp_response_time_seconds_bucket{server="restaurant-search-mcp",le="0.1"} 200
mcp_response_time_seconds_bucket{server="restaurant-search-mcp",le="0.5"} 580
mcp_response_time_seconds_bucket{server="restaurant-search-mcp",le="+Inf"} 600

# HELP rest_requests_total Total number of REST requests
# TYPE rest_requests_total counter
rest_requests_total{server="restaurant-search-mcp",status="success"} 480
rest_requests_total{server="restaurant-search-mcp",status="failure"} 120
```

**Example:**
```bash
# Get JSON metrics
curl -X GET "http://localhost:8080/status/metrics?format=json&time_range=24h" \
  -H "Accept: application/json"

# Get Prometheus metrics
curl -X GET "http://localhost:8080/status/metrics?format=prometheus" \
  -H "Accept: text/plain"
```

### GET /status/metrics/{server_name}

Get detailed metrics for a specific server.

**Path Parameters:**
- `server_name` (string, required) - Name of the server

**Response Format:**
```json
{
  "server_name": "restaurant-search-mcp",
  "timestamp": "2025-10-01T12:00:00Z",
  "time_range": "1h",
  "overall_metrics": {
    "total_checks": 400,
    "successful_checks": 352,
    "failed_checks": 48,
    "success_rate": 0.88,
    "average_response_time_ms": 135.2,
    "health_score": 0.92
  },
  "mcp_metrics": {
    "total_checks": 200,
    "successful_checks": 184,
    "failed_checks": 16,
    "success_rate": 0.92,
    "average_response_time_ms": 120.5,
    "tools_validation": {
      "total_validations": 184,
      "successful_validations": 180,
      "validation_success_rate": 0.98
    },
    "expected_tools_found": 3,
    "missing_tools_count": 0
  },
  "rest_metrics": {
    "total_checks": 200,
    "successful_checks": 168,
    "failed_checks": 32,
    "success_rate": 0.84,
    "average_response_time_ms": 149.9,
    "status_code_distribution": {
      "200": 168,
      "404": 5,
      "500": 27
    },
    "response_validation": {
      "valid_responses": 168,
      "invalid_responses": 0
    }
  },
  "performance_trends": {
    "response_time_trend": "stable",
    "success_rate_trend": "improving",
    "last_24h_average_ms": 142.1,
    "last_7d_average_ms": 138.7
  }
}
```

## Configuration Endpoints

### GET /status/config

Get current system configuration (sanitized).

**Response Format:**
```json
{
  "system_info": {
    "version": "1.0.0",
    "dual_monitoring_enabled": true,
    "total_servers_configured": 3
  },
  "global_settings": {
    "check_interval_seconds": 30,
    "max_concurrent_checks": 10,
    "retry_attempts": 3,
    "circuit_breaker_enabled": true
  },
  "monitoring_settings": {
    "mcp_health_checks": {
      "enabled": true,
      "default_timeout_seconds": 10,
      "tools_list_validation": true,
      "connection_pool_size": 5
    },
    "rest_health_checks": {
      "enabled": true,
      "default_timeout_seconds": 8,
      "connection_pool_size": 10
    }
  },
  "servers": [
    {
      "server_name": "restaurant-search-mcp",
      "mcp_enabled": true,
      "rest_enabled": true,
      "mcp_timeout_seconds": 10,
      "rest_timeout_seconds": 8,
      "mcp_priority_weight": 0.6,
      "rest_priority_weight": 0.4
    }
  ]
}
```

### GET /status/config/{server_name}

Get configuration for a specific server.

**Path Parameters:**
- `server_name` (string, required) - Name of the server

**Response Format:**
```json
{
  "server_name": "restaurant-search-mcp",
  "mcp_configuration": {
    "enabled": true,
    "endpoint_url": "http://localhost:8080/mcp",
    "timeout_seconds": 10,
    "retry_attempts": 3,
    "expected_tools": [
      "search_restaurants_by_district",
      "recommend_restaurants"
    ],
    "tools_validation_enabled": true
  },
  "rest_configuration": {
    "enabled": true,
    "health_endpoint_url": "http://localhost:8080/status/health",
    "timeout_seconds": 8,
    "retry_attempts": 2,
    "expected_status_codes": [200]
  },
  "aggregation_settings": {
    "mcp_priority_weight": 0.6,
    "rest_priority_weight": 0.4,
    "require_both_success": false
  },
  "authentication": {
    "jwt_enabled": true,
    "api_key_enabled": true
  }
}
```

## Circuit Breaker Endpoints

### GET /status/circuit-breaker

Get circuit breaker states for all servers.

**Response Format:**
```json
{
  "timestamp": "2025-10-01T12:00:00Z",
  "global_circuit_breaker_enabled": true,
  "servers": {
    "restaurant-search-mcp": {
      "mcp_circuit_state": {
        "state": "CLOSED",
        "failure_count": 2,
        "success_count": 8,
        "last_failure_time": "2025-10-01T11:45:00Z",
        "next_attempt_time": null
      },
      "rest_circuit_state": {
        "state": "CLOSED",
        "failure_count": 0,
        "success_count": 10,
        "last_failure_time": null,
        "next_attempt_time": null
      },
      "overall_circuit_state": {
        "state": "CLOSED",
        "available_paths": ["mcp", "rest"]
      }
    }
  },
  "circuit_breaker_config": {
    "failure_threshold": 5,
    "success_threshold": 3,
    "timeout_seconds": 60
  }
}
```

### GET /status/circuit-breaker/{server_name}

Get circuit breaker state for a specific server.

**Path Parameters:**
- `server_name` (string, required) - Name of the server

**Response Format:**
```json
{
  "server_name": "restaurant-search-mcp",
  "timestamp": "2025-10-01T12:00:00Z",
  "mcp_circuit_state": {
    "state": "CLOSED",
    "failure_count": 2,
    "success_count": 8,
    "failure_rate": 0.2,
    "last_failure_time": "2025-10-01T11:45:00Z",
    "last_success_time": "2025-10-01T12:00:00Z",
    "next_attempt_time": null,
    "state_change_history": [
      {
        "timestamp": "2025-10-01T11:30:00Z",
        "from_state": "OPEN",
        "to_state": "HALF_OPEN",
        "reason": "Timeout expired"
      }
    ]
  },
  "rest_circuit_state": {
    "state": "CLOSED",
    "failure_count": 0,
    "success_count": 10,
    "failure_rate": 0.0,
    "last_success_time": "2025-10-01T12:00:00Z",
    "next_attempt_time": null
  },
  "overall_circuit_state": {
    "state": "CLOSED",
    "available_paths": ["mcp", "rest"],
    "recommended_action": "continue_normal_operation"
  }
}
```

### POST /status/circuit-breaker/{server_name}/reset

Reset circuit breaker for a specific server.

**Path Parameters:**
- `server_name` (string, required) - Name of the server

**Request Body (optional):**
```json
{
  "reset_type": "both|mcp|rest",
  "force_reset": true
}
```

**Response Format:**
```json
{
  "server_name": "restaurant-search-mcp",
  "reset_performed": true,
  "timestamp": "2025-10-01T12:00:00Z",
  "reset_details": {
    "mcp_circuit_reset": true,
    "rest_circuit_reset": true,
    "previous_state": "OPEN",
    "new_state": "CLOSED"
  }
}
```

## Administrative Endpoints

### POST /status/dual-check

Perform manual dual health check for all servers or specific servers.

**Request Body (optional):**
```json
{
  "server_names": ["restaurant-search-mcp", "reasoning-service"],
  "check_options": {
    "include_detailed_results": true,
    "timeout_override": {
      "mcp_timeout_seconds": 15,
      "rest_timeout_seconds": 12
    }
  }
}
```

**Response Format:**
```json
{
  "check_initiated": true,
  "timestamp": "2025-10-01T12:00:00Z",
  "servers_checked": 2,
  "results": [
    {
      "server_name": "restaurant-search-mcp",
      "overall_status": "healthy",
      "check_duration_ms": 205.3,
      "mcp_result": {
        "success": true,
        "response_time_ms": 118.7
      },
      "rest_result": {
        "success": true,
        "response_time_ms": 86.6
      }
    }
  ],
  "summary": {
    "total_healthy": 2,
    "total_degraded": 0,
    "total_unhealthy": 0,
    "average_response_time_ms": 152.1
  }
}
```

### GET /status/system-info

Get system information and runtime details.

**Response Format:**
```json
{
  "system": {
    "version": "1.0.0",
    "build_date": "2025-10-01T00:00:00Z",
    "git_commit": "abc123def456",
    "environment": "production"
  },
  "runtime": {
    "uptime_seconds": 86400,
    "start_time": "2025-09-30T12:00:00Z",
    "python_version": "3.11.5",
    "memory_usage_mb": 256.7,
    "cpu_usage_percent": 15.3
  },
  "configuration": {
    "dual_monitoring_enabled": true,
    "total_servers": 3,
    "circuit_breaker_enabled": true,
    "metrics_collection_enabled": true
  },
  "statistics": {
    "total_checks_performed": 15420,
    "total_uptime_hours": 24.0,
    "average_checks_per_hour": 642.5
  }
}
```

## Error Handling

### Error Response Format

All API endpoints return errors in a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional error details",
      "timestamp": "2025-10-01T12:00:00Z"
    },
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request format or parameters |
| `UNAUTHORIZED` | 401 | Authentication required or invalid |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method not supported |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Examples

**Server Not Found:**
```json
{
  "error": {
    "code": "SERVER_NOT_FOUND",
    "message": "Server 'invalid-server' not found in configuration",
    "details": {
      "server_name": "invalid-server",
      "available_servers": ["restaurant-search-mcp", "reasoning-service"]
    },
    "request_id": "req_123456789"
  }
}
```

**Authentication Error:**
```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "JWT token is expired or invalid",
    "details": {
      "token_expired": true,
      "expiry_time": "2025-10-01T11:00:00Z"
    },
    "request_id": "req_123456789"
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

### Rate Limit Headers

All responses include rate limiting headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1633024800
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again later.",
    "details": {
      "limit": 1000,
      "window_seconds": 3600,
      "reset_time": "2025-10-01T13:00:00Z"
    },
    "request_id": "req_123456789"
  }
}
```

## Examples

### Complete Health Check Workflow

```bash
#!/bin/bash

# 1. Check overall system health
echo "Checking system health..."
curl -s http://localhost:8080/status/health | jq .

# 2. Get detailed server statuses
echo "Getting server statuses..."
curl -s http://localhost:8080/status/servers | jq .

# 3. Check specific server
echo "Checking restaurant-search-mcp..."
curl -s http://localhost:8080/status/servers/restaurant-search-mcp | jq .

# 4. Trigger manual health check
echo "Triggering manual check..."
curl -s -X POST http://localhost:8080/status/servers/restaurant-search-mcp/check | jq .

# 5. Get metrics
echo "Getting metrics..."
curl -s "http://localhost:8080/status/metrics?time_range=1h" | jq .

# 6. Check circuit breaker status
echo "Checking circuit breakers..."
curl -s http://localhost:8080/status/circuit-breaker | jq .
```

### Monitoring Script

```python
#!/usr/bin/env python3
import requests
import time
import json

class MCPStatusMonitor:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.headers = {}
        if api_key:
            self.headers['X-API-Key'] = api_key
    
    def check_system_health(self):
        """Check overall system health."""
        response = requests.get(
            f"{self.base_url}/status/health",
            headers=self.headers
        )
        return response.json()
    
    def get_server_status(self, server_name):
        """Get status for specific server."""
        response = requests.get(
            f"{self.base_url}/status/servers/{server_name}",
            headers=self.headers
        )
        return response.json()
    
    def trigger_health_check(self, server_name):
        """Trigger manual health check."""
        response = requests.post(
            f"{self.base_url}/status/servers/{server_name}/check",
            headers=self.headers,
            json={"check_types": ["mcp", "rest"]}
        )
        return response.json()
    
    def get_metrics(self, time_range="1h"):
        """Get system metrics."""
        response = requests.get(
            f"{self.base_url}/status/metrics",
            headers=self.headers,
            params={"time_range": time_range}
        )
        return response.json()
    
    def monitor_continuously(self, interval=30):
        """Continuously monitor system health."""
        while True:
            try:
                health = self.check_system_health()
                print(f"System Status: {health['status']}")
                print(f"Success Rate: {health['overall_metrics']['overall_success_rate']:.2%}")
                
                if health['status'] != 'healthy':
                    print("⚠️  System is not healthy!")
                    # Could trigger alerts here
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error monitoring system: {e}")
                time.sleep(interval)

# Usage
if __name__ == "__main__":
    monitor = MCPStatusMonitor("http://localhost:8080", api_key="your-api-key")
    
    # Check system health
    health = monitor.check_system_health()
    print(json.dumps(health, indent=2))
    
    # Start continuous monitoring
    # monitor.monitor_continuously(interval=60)
```

### Prometheus Integration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'enhanced-mcp-status-check'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/status/metrics'
    params:
      format: ['prometheus']
    scrape_interval: 30s
    scrape_timeout: 10s
```

### Grafana Dashboard Query Examples

```promql
# Overall success rate
rate(mcp_requests_total{status="success"}[5m]) / rate(mcp_requests_total[5m])

# Average response time
rate(mcp_response_time_seconds_sum[5m]) / rate(mcp_response_time_seconds_count[5m])

# Circuit breaker state
circuit_breaker_state{server="restaurant-search-mcp"}

# Server availability
up{job="enhanced-mcp-status-check"}
```

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Maintainers**: Enhanced MCP Status Check API Team