# Tool Orchestration API Reference

## Table of Contents

1. [Overview](#overview)
2. [Core APIs](#core-apis)
3. [Data Models](#data-models)
4. [Error Handling](#error-handling)
5. [Authentication](#authentication)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

## Overview

This document provides comprehensive API reference for the Tool Orchestration System. All APIs follow RESTful principles and return JSON responses. The system provides both synchronous and asynchronous interfaces for different use cases.

### Base URL

```
https://api.mbti-travel-planner.com/orchestration/v1
```

### Content Type

All requests and responses use `application/json` content type unless otherwise specified.

### Authentication

All API endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

## Core APIs

### Tool Orchestration Engine

#### POST /orchestrate

Process a user request through the orchestration system.

**Request Body:**
```json
{
  "request": {
    "text": "Find restaurants in Central district for lunch",
    "user_id": "user-123",
    "session_id": "session-456",
    "context": {
      "mbti_type": "ENFP",
      "preferences": {
        "cuisine_types": ["Asian", "Italian"],
        "price_range": "moderate"
      },
      "conversation_history": [
        {
          "timestamp": "2025-10-08T10:00:00Z",
          "request": "What's good for breakfast?",
          "response": "Here are some breakfast recommendations..."
        }
      ]
    }
  },
  "options": {
    "enable_tracing": true,
    "max_execution_time": 30,
    "preferred_tools": ["restaurant_search", "restaurant_reasoning"]
  }
}
```

**Response:**
```json
{
  "orchestration_id": "orch-789",
  "status": "completed",
  "result": {
    "response": "I found 15 restaurants in Central district that serve lunch...",
    "confidence": 0.95,
    "tools_used": [
      {
        "tool_id": "restaurant_search",
        "tool_name": "search_restaurants_combined",
        "execution_time": 1.2,
        "success": true
      },
      {
        "tool_id": "restaurant_reasoning",
        "tool_name": "recommend_restaurants",
        "execution_time": 0.8,
        "success": true
      }
    ],
    "workflow_type": "SEARCH_AND_RECOMMEND",
    "execution_metadata": {
      "total_execution_time": 2.1,
      "intent_analysis_time": 0.1,
      "tool_selection_time": 0.05,
      "workflow_execution_time": 2.0
    }
  },
  "trace": {
    "intent": {
      "type": "COMBINED_SEARCH_AND_RECOMMENDATION",
      "confidence": 0.92,
      "parameters": {
        "districts": ["Central district"],
        "meal_types": ["lunch"],
        "mbti_type": "ENFP"
      }
    },
    "tool_selection": {
      "candidates": [
        {
          "tool_id": "restaurant_search",
          "confidence": 0.95,
          "reasoning": "High capability match for district-based search"
        },
        {
          "tool_id": "restaurant_reasoning",
          "confidence": 0.88,
          "reasoning": "Good for MBTI-based recommendations"
        }
      ],
      "selected": ["restaurant_search", "restaurant_reasoning"]
    },
    "workflow_execution": {
      "steps": [
        {
          "step_id": "search",
          "tool_id": "restaurant_search",
          "input": {"districts": ["Central district"], "meal_types": ["lunch"]},
          "output": {"restaurants": [...], "count": 15},
          "execution_time": 1.2
        },
        {
          "step_id": "recommend",
          "tool_id": "restaurant_reasoning",
          "input": {"restaurants": [...], "mbti_type": "ENFP"},
          "output": {"recommendations": [...], "reasoning": "..."},
          "execution_time": 0.8
        }
      ]
    }
  }
}
```

**Error Response:**
```json
{
  "error": {
    "code": "ORCHESTRATION_FAILED",
    "message": "Failed to process orchestration request",
    "details": {
      "orchestration_id": "orch-789",
      "failure_reason": "Tool selection failed",
      "failed_component": "tool_selector",
      "retry_possible": true
    }
  }
}
```

#### GET /orchestrate/{orchestration_id}

Retrieve the status and results of a specific orchestration request.

**Response:**
```json
{
  "orchestration_id": "orch-789",
  "status": "completed",
  "created_at": "2025-10-08T10:00:00Z",
  "completed_at": "2025-10-08T10:00:02Z",
  "result": {
    // Same as POST response result
  }
}
```

#### GET /orchestrate/{orchestration_id}/trace

Retrieve detailed execution trace for debugging and analysis.

**Response:**
```json
{
  "orchestration_id": "orch-789",
  "trace": {
    // Detailed execution trace
  }
}
```

### Tool Registry

#### GET /tools

List all registered tools with their capabilities and status.

**Query Parameters:**
- `status` (optional): Filter by tool status (`active`, `inactive`, `degraded`)
- `capability` (optional): Filter by capability name
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "tools": [
    {
      "tool_id": "restaurant_search",
      "name": "Restaurant Search Tool",
      "description": "Search for restaurants by location and meal type",
      "status": "active",
      "capabilities": [
        {
          "name": "search_by_district",
          "description": "Search restaurants in specific districts",
          "required_parameters": ["districts"],
          "optional_parameters": ["meal_types", "cuisine_types"]
        },
        {
          "name": "search_by_meal_type",
          "description": "Search restaurants by meal type",
          "required_parameters": ["meal_types"],
          "optional_parameters": ["districts"]
        }
      ],
      "performance_metrics": {
        "average_response_time": 1.2,
        "success_rate": 0.98,
        "last_24h_invocations": 150
      },
      "health_status": {
        "status": "healthy",
        "last_check": "2025-10-08T10:00:00Z",
        "response_time": 0.8
      }
    }
  ],
  "pagination": {
    "total": 2,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

#### POST /tools

Register a new tool with the orchestration system.

**Request Body:**
```json
{
  "tool_id": "new_tool",
  "name": "New Tool",
  "description": "Description of the new tool",
  "mcp_endpoint": "https://api.example.com/mcp",
  "capabilities": [
    {
      "name": "new_capability",
      "description": "New capability description",
      "required_parameters": ["param1"],
      "optional_parameters": ["param2"]
    }
  ],
  "configuration": {
    "timeout": 15,
    "retry_count": 3,
    "health_check_endpoint": "/health"
  }
}
```

**Response:**
```json
{
  "tool_id": "new_tool",
  "status": "registered",
  "registration_time": "2025-10-08T10:00:00Z"
}
```

#### GET /tools/{tool_id}

Get detailed information about a specific tool.

**Response:**
```json
{
  "tool_id": "restaurant_search",
  "name": "Restaurant Search Tool",
  "description": "Search for restaurants by location and meal type",
  "status": "active",
  "capabilities": [...],
  "performance_metrics": {...},
  "health_status": {...},
  "configuration": {
    "timeout": 15,
    "retry_count": 3,
    "health_check_endpoint": "/health"
  }
}
```

#### PUT /tools/{tool_id}

Update tool configuration or metadata.

**Request Body:**
```json
{
  "configuration": {
    "timeout": 20,
    "retry_count": 5
  },
  "description": "Updated description"
}
```

#### DELETE /tools/{tool_id}

Unregister a tool from the orchestration system.

**Response:**
```json
{
  "tool_id": "restaurant_search",
  "status": "unregistered",
  "unregistration_time": "2025-10-08T10:00:00Z"
}
```

### Performance Monitoring

#### GET /metrics

Get system-wide performance metrics.

**Query Parameters:**
- `time_window` (optional): Time window for metrics (`1h`, `24h`, `7d`, `30d`)
- `metric_type` (optional): Filter by metric type (`performance`, `usage`, `errors`)

**Response:**
```json
{
  "time_window": "24h",
  "metrics": {
    "orchestration": {
      "total_requests": 1250,
      "successful_requests": 1225,
      "failed_requests": 25,
      "average_response_time": 2.1,
      "p95_response_time": 4.2,
      "p99_response_time": 8.1
    },
    "tools": {
      "restaurant_search": {
        "invocations": 800,
        "success_rate": 0.98,
        "average_response_time": 1.2,
        "error_rate": 0.02
      },
      "restaurant_reasoning": {
        "invocations": 650,
        "success_rate": 0.96,
        "average_response_time": 1.8,
        "error_rate": 0.04
      }
    },
    "workflows": {
      "SEARCH_AND_RECOMMEND": {
        "executions": 450,
        "success_rate": 0.97,
        "average_execution_time": 3.2
      },
      "SIMPLE_SEARCH": {
        "executions": 350,
        "success_rate": 0.99,
        "average_execution_time": 1.5
      }
    }
  }
}
```

#### GET /metrics/tools/{tool_id}

Get performance metrics for a specific tool.

**Response:**
```json
{
  "tool_id": "restaurant_search",
  "time_window": "24h",
  "metrics": {
    "invocations": 800,
    "success_rate": 0.98,
    "average_response_time": 1.2,
    "error_rate": 0.02,
    "response_time_distribution": {
      "p50": 1.0,
      "p90": 2.0,
      "p95": 2.5,
      "p99": 4.0
    },
    "error_breakdown": {
      "timeout": 8,
      "authentication": 2,
      "service_unavailable": 6
    }
  }
}
```

### Health Monitoring

#### GET /health

Get overall system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-08T10:00:00Z",
  "components": {
    "orchestration_engine": {
      "status": "healthy",
      "response_time": 0.05
    },
    "intent_analyzer": {
      "status": "healthy",
      "response_time": 0.02
    },
    "tool_selector": {
      "status": "healthy",
      "response_time": 0.03
    },
    "workflow_engine": {
      "status": "healthy",
      "response_time": 0.08
    },
    "performance_monitor": {
      "status": "healthy",
      "response_time": 0.01
    }
  },
  "tools": {
    "restaurant_search": {
      "status": "healthy",
      "last_check": "2025-10-08T09:59:30Z",
      "response_time": 0.8
    },
    "restaurant_reasoning": {
      "status": "degraded",
      "last_check": "2025-10-08T09:59:30Z",
      "response_time": 3.2,
      "issues": ["High response time"]
    }
  }
}
```

#### GET /health/tools/{tool_id}

Get health status for a specific tool.

**Response:**
```json
{
  "tool_id": "restaurant_search",
  "status": "healthy",
  "last_check": "2025-10-08T09:59:30Z",
  "response_time": 0.8,
  "health_checks": [
    {
      "timestamp": "2025-10-08T09:59:30Z",
      "status": "healthy",
      "response_time": 0.8
    },
    {
      "timestamp": "2025-10-08T09:59:00Z",
      "status": "healthy",
      "response_time": 0.9
    }
  ]
}
```

### Configuration Management

#### GET /config

Get current orchestration configuration.

**Response:**
```json
{
  "orchestration": {
    "intent_analysis": {
      "confidence_threshold": 0.8,
      "nlp_model": "intent-classifier-v1"
    },
    "tool_selection": {
      "ranking_algorithm": "weighted_performance",
      "performance_weight": 0.4,
      "health_weight": 0.3,
      "capability_weight": 0.3
    },
    "workflow_engine": {
      "max_concurrent_workflows": 50,
      "step_timeout": 30
    }
  }
}
```

#### PUT /config

Update orchestration configuration.

**Request Body:**
```json
{
  "orchestration": {
    "tool_selection": {
      "performance_weight": 0.5,
      "health_weight": 0.3,
      "capability_weight": 0.2
    }
  }
}
```

**Response:**
```json
{
  "status": "updated",
  "timestamp": "2025-10-08T10:00:00Z",
  "changes": [
    {
      "path": "orchestration.tool_selection.performance_weight",
      "old_value": 0.4,
      "new_value": 0.5
    }
  ]
}
```

## Data Models

### UserRequest

```json
{
  "text": "string",
  "user_id": "string",
  "session_id": "string",
  "context": {
    "mbti_type": "string",
    "preferences": "object",
    "conversation_history": "array"
  },
  "timestamp": "string (ISO 8601)"
}
```

### Intent

```json
{
  "type": "string (enum)",
  "confidence": "number (0-1)",
  "parameters": "object",
  "required_capabilities": "array of strings",
  "optional_capabilities": "array of strings"
}
```

### SelectedTool

```json
{
  "tool_id": "string",
  "tool_name": "string",
  "confidence": "number (0-1)",
  "expected_performance": {
    "response_time": "number",
    "success_rate": "number"
  },
  "fallback_tools": "array of strings"
}
```

### WorkflowResult

```json
{
  "workflow_id": "string",
  "status": "string (enum)",
  "steps": "array of WorkflowStep",
  "execution_time": "number",
  "success": "boolean",
  "result": "object",
  "error": "object (optional)"
}
```

### ToolMetadata

```json
{
  "tool_id": "string",
  "name": "string",
  "description": "string",
  "capabilities": "array of Capability",
  "performance_characteristics": "object",
  "health_check_endpoint": "string (optional)",
  "configuration": "object"
}
```

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)",
    "timestamp": "string (ISO 8601)",
    "request_id": "string"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `ORCHESTRATION_FAILED` | 500 | Orchestration processing failed |
| `TOOL_UNAVAILABLE` | 503 | Required tool is unavailable |
| `TIMEOUT` | 504 | Request timeout |

### Error Handling Examples

#### Tool Selection Failed

```json
{
  "error": {
    "code": "ORCHESTRATION_FAILED",
    "message": "No suitable tools found for the request",
    "details": {
      "intent_type": "RESTAURANT_SEARCH_BY_LOCATION",
      "required_capabilities": ["search_by_district"],
      "available_tools": [],
      "suggestion": "Check tool availability and registration"
    }
  }
}
```

#### Tool Timeout

```json
{
  "error": {
    "code": "TIMEOUT",
    "message": "Tool execution timed out",
    "details": {
      "tool_id": "restaurant_search",
      "timeout_duration": 15,
      "execution_time": 16.2,
      "retry_possible": true
    }
  }
}
```

## Authentication

### JWT Token Requirements

JWT tokens must include the following claims:

```json
{
  "sub": "user-123",
  "iss": "https://auth.mbti-travel-planner.com",
  "aud": "orchestration-api",
  "exp": 1696780800,
  "iat": 1696777200,
  "scope": "orchestration:read orchestration:write tools:read"
}
```

### Required Scopes

| Scope | Description |
|-------|-------------|
| `orchestration:read` | Read orchestration results and status |
| `orchestration:write` | Submit orchestration requests |
| `tools:read` | Read tool information and metrics |
| `tools:write` | Register and update tools |
| `config:read` | Read configuration |
| `config:write` | Update configuration |
| `metrics:read` | Read performance metrics |

## Rate Limiting

### Rate Limit Headers

All responses include rate limiting headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1696780800
```

### Rate Limits by Endpoint

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| `POST /orchestrate` | 100 requests | 1 minute |
| `GET /orchestrate/*` | 500 requests | 1 minute |
| `GET /tools` | 200 requests | 1 minute |
| `POST /tools` | 10 requests | 1 minute |
| `GET /metrics` | 100 requests | 1 minute |
| `GET /health` | 1000 requests | 1 minute |

## Examples

### Basic Orchestration Request

```bash
curl -X POST https://api.mbti-travel-planner.com/orchestration/v1/orchestrate \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "text": "Find Italian restaurants in Central district",
      "user_id": "user-123",
      "context": {
        "mbti_type": "ENFP",
        "preferences": {
          "cuisine_types": ["Italian"]
        }
      }
    }
  }'
```

### Tool Registration

```bash
curl -X POST https://api.mbti-travel-planner.com/orchestration/v1/tools \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "new_search_tool",
    "name": "Advanced Search Tool",
    "description": "Advanced restaurant search with ML recommendations",
    "mcp_endpoint": "https://api.example.com/mcp",
    "capabilities": [
      {
        "name": "ml_search",
        "description": "ML-powered restaurant search",
        "required_parameters": ["query"],
        "optional_parameters": ["location", "preferences"]
      }
    ]
  }'
```

### Performance Metrics Query

```bash
curl -X GET "https://api.mbti-travel-planner.com/orchestration/v1/metrics?time_window=24h" \
  -H "Authorization: Bearer <jwt_token>"
```

---

**API Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Maintained By**: MBTI Travel Planner Agent Team