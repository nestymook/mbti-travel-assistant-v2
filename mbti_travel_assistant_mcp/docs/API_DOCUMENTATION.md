# MBTI Travel Assistant MCP - API Documentation

## Overview

The MBTI Travel Assistant is a BedrockAgentCore runtime service that provides intelligent restaurant recommendations by orchestrating calls to existing MCP servers. It receives HTTP requests with district and meal time parameters, authenticates via JWT tokens, and returns structured JSON responses optimized for frontend web applications.

## Base Information

- **Service Type**: BedrockAgentCore Runtime
- **Architecture**: ARM64 containers required
- **Authentication**: JWT tokens via AWS Cognito
- **Protocol**: HTTP/HTTPS with JSON payloads
- **Response Format**: Structured JSON with exactly 1 recommendation + up to 19 candidates

## Authentication

### JWT Token Authentication

All requests must include a valid JWT token for authentication. The token can be provided in multiple ways:

#### Authorization Header (Recommended)
```http
Authorization: Bearer <jwt_token>
```

#### Request Payload
```json
{
  "auth_token": "<jwt_token>",
  "district": "Central district",
  "meal_time": "breakfast"
}
```

### Token Requirements

- **Issuer**: AWS Cognito User Pool
- **Algorithm**: RS256
- **Claims**: Must include `sub` (user ID) and valid `exp` (expiration)
- **Scope**: Restaurant recommendation access

### Authentication Errors

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `AUTH_FAILED` | 401 | Invalid or expired JWT token |
| `AUTH_MISSING` | 401 | No authentication token provided |
| `AUTH_MALFORMED` | 400 | Malformed authorization header |

## API Endpoints

### POST /invocations

The main entrypoint for restaurant recommendations following BedrockAgentCore runtime patterns.

#### Request Format

```http
POST /invocations
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "district": "Central district",
  "meal_time": "breakfast",
  "natural_language_query": "Find me a good breakfast place in Central",
  "user_context": {
    "user_id": "user123",
    "preferences": {}
  }
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `district` | string | Conditional* | District name for restaurant search |
| `meal_time` | string | Optional | Meal time filter: `breakfast`, `lunch`, `dinner` |
| `natural_language_query` | string | Conditional* | Natural language search query |
| `user_context` | object | Optional | User context from JWT token |

*Either `district` or `natural_language_query` must be provided.

#### Response Format

```json
{
  "recommendation": {
    "id": "rest_001",
    "name": "Great Breakfast Cafe",
    "address": "123 Main Street, Central",
    "district": "Central district",
    "meal_type": ["breakfast", "brunch"],
    "sentiment": {
      "likes": 85,
      "dislikes": 10,
      "neutral": 5,
      "total_responses": 100,
      "positive_percentage": 90.0
    },
    "price_range": "$$",
    "operating_hours": {
      "monday": ["07:00-11:30"],
      "tuesday": ["07:00-11:30"],
      "wednesday": ["07:00-11:30"],
      "thursday": ["07:00-11:30"],
      "friday": ["07:00-11:30"],
      "saturday": ["08:00-12:00"],
      "sunday": ["08:00-12:00"]
    },
    "location_category": "urban",
    "metadata": {
      "cuisine_type": "Western",
      "rating": 4.5,
      "review_count": 100
    }
  },
  "candidates": [
    {
      "id": "rest_002",
      "name": "Morning Glory Diner",
      "address": "456 Side Street, Central",
      "district": "Central district",
      "meal_type": ["breakfast"],
      "sentiment": {
        "likes": 75,
        "dislikes": 15,
        "neutral": 10,
        "total_responses": 100,
        "positive_percentage": 85.0
      },
      "price_range": "$",
      "operating_hours": {
        "monday": ["06:00-11:00"],
        "tuesday": ["06:00-11:00"],
        "wednesday": ["06:00-11:00"],
        "thursday": ["06:00-11:00"],
        "friday": ["06:00-11:00"],
        "saturday": ["07:00-12:00"],
        "sunday": ["07:00-12:00"]
      },
      "location_category": "urban",
      "metadata": {
        "cuisine_type": "American",
        "rating": 4.2,
        "review_count": 85
      }
    }
    // ... up to 18 more candidates
  ],
  "metadata": {
    "search_criteria": {
      "district": "Central district",
      "meal_time": "breakfast"
    },
    "total_found": 20,
    "timestamp": "2024-01-15T10:30:00Z",
    "processing_time_ms": 1250,
    "cache_hit": false,
    "mcp_calls": [
      "search_restaurants_combined",
      "recommend_restaurants"
    ]
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `recommendation` | Restaurant | Single recommended restaurant (exactly 1) |
| `candidates` | Restaurant[] | List of candidate restaurants (max 19) |
| `metadata` | ResponseMetadata | Search metadata and timing information |
| `error` | ErrorInfo | Error information (only present on failure) |

### GET /health

Health check endpoint for monitoring and load balancing.

#### Request Format

```http
GET /health
```

#### Response Format

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "mcp_search_client": {
      "status": "healthy",
      "response_time_ms": 45,
      "last_check": "2024-01-15T10:29:55Z"
    },
    "mcp_reasoning_client": {
      "status": "healthy", 
      "response_time_ms": 67,
      "last_check": "2024-01-15T10:29:55Z"
    },
    "cache_service": {
      "status": "healthy",
      "hit_rate": 0.75,
      "last_check": "2024-01-15T10:29:55Z"
    },
    "jwt_auth": {
      "status": "healthy",
      "cognito_reachable": true,
      "last_check": "2024-01-15T10:29:55Z"
    }
  },
  "performance_metrics": {
    "avg_response_time_ms": 1150,
    "requests_per_minute": 45,
    "error_rate": 0.02,
    "cache_hit_rate": 0.75
  }
}
```

## Data Models

### Restaurant Object

```json
{
  "id": "string",
  "name": "string", 
  "address": "string",
  "district": "string",
  "meal_type": ["string"],
  "sentiment": {
    "likes": "integer",
    "dislikes": "integer", 
    "neutral": "integer",
    "total_responses": "integer",
    "positive_percentage": "float"
  },
  "price_range": "string",
  "operating_hours": {
    "monday": ["string"],
    "tuesday": ["string"],
    "wednesday": ["string"],
    "thursday": ["string"],
    "friday": ["string"],
    "saturday": ["string"],
    "sunday": ["string"]
  },
  "location_category": "string",
  "metadata": "object"
}
```

### ResponseMetadata Object

```json
{
  "search_criteria": {
    "district": "string",
    "meal_time": "string"
  },
  "total_found": "integer",
  "timestamp": "string (ISO 8601)",
  "processing_time_ms": "integer",
  "cache_hit": "boolean",
  "mcp_calls": ["string"]
}
```

### ErrorInfo Object

```json
{
  "error_type": "string",
  "message": "string",
  "suggested_actions": ["string"],
  "error_code": "string"
}
```

## Example Requests and Responses

### Example 1: District and Meal Time Search

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "district": "Central district",
  "meal_time": "breakfast"
}
```

#### Response (200 OK)
```json
{
  "recommendation": {
    "id": "rest_central_001",
    "name": "Central Breakfast House",
    "address": "789 Queen's Road Central, Central",
    "district": "Central district",
    "meal_type": ["breakfast", "brunch"],
    "sentiment": {
      "likes": 92,
      "dislikes": 5,
      "neutral": 3,
      "total_responses": 100,
      "positive_percentage": 95.0
    },
    "price_range": "$$$",
    "operating_hours": {
      "monday": ["07:00-11:30"],
      "tuesday": ["07:00-11:30"],
      "wednesday": ["07:00-11:30"],
      "thursday": ["07:00-11:30"],
      "friday": ["07:00-11:30"],
      "saturday": ["08:00-12:00"],
      "sunday": ["08:00-12:00"]
    },
    "location_category": "business_district",
    "metadata": {
      "cuisine_type": "International",
      "rating": 4.7,
      "review_count": 156
    }
  },
  "candidates": [
    {
      "id": "rest_central_002",
      "name": "Morning Delight Cafe",
      "address": "321 Des Voeux Road Central, Central",
      "district": "Central district",
      "meal_type": ["breakfast"],
      "sentiment": {
        "likes": 78,
        "dislikes": 12,
        "neutral": 10,
        "total_responses": 100,
        "positive_percentage": 88.0
      },
      "price_range": "$$",
      "operating_hours": {
        "monday": ["06:30-11:00"],
        "tuesday": ["06:30-11:00"],
        "wednesday": ["06:30-11:00"],
        "thursday": ["06:30-11:00"],
        "friday": ["06:30-11:00"],
        "saturday": ["07:00-12:00"],
        "sunday": ["07:00-12:00"]
      },
      "location_category": "business_district",
      "metadata": {
        "cuisine_type": "Western",
        "rating": 4.3,
        "review_count": 89
      }
    }
  ],
  "metadata": {
    "search_criteria": {
      "district": "Central district",
      "meal_time": "breakfast"
    },
    "total_found": 15,
    "timestamp": "2024-01-15T10:30:00Z",
    "processing_time_ms": 1180,
    "cache_hit": false,
    "mcp_calls": [
      "search_restaurants_combined",
      "recommend_restaurants"
    ]
  }
}
```

### Example 2: Natural Language Query

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "natural_language_query": "Find me a good lunch place in Admiralty with reasonable prices"
}
```

#### Response (200 OK)
```json
{
  "recommendation": {
    "id": "rest_admiralty_005",
    "name": "Admiralty Lunch Corner",
    "address": "88 Queensway, Admiralty",
    "district": "Admiralty",
    "meal_type": ["lunch", "dinner"],
    "sentiment": {
      "likes": 84,
      "dislikes": 8,
      "neutral": 8,
      "total_responses": 100,
      "positive_percentage": 92.0
    },
    "price_range": "$$",
    "operating_hours": {
      "monday": ["11:30-15:00", "18:00-22:00"],
      "tuesday": ["11:30-15:00", "18:00-22:00"],
      "wednesday": ["11:30-15:00", "18:00-22:00"],
      "thursday": ["11:30-15:00", "18:00-22:00"],
      "friday": ["11:30-15:00", "18:00-22:00"],
      "saturday": ["11:30-15:30", "18:00-22:30"],
      "sunday": ["11:30-15:30", "18:00-22:30"]
    },
    "location_category": "business_district",
    "metadata": {
      "cuisine_type": "Asian Fusion",
      "rating": 4.4,
      "review_count": 127
    }
  },
  "candidates": [
    // ... up to 19 candidate restaurants
  ],
  "metadata": {
    "search_criteria": {
      "natural_language_query": "Find me a good lunch place in Admiralty with reasonable prices"
    },
    "total_found": 12,
    "timestamp": "2024-01-15T10:35:00Z",
    "processing_time_ms": 1420,
    "cache_hit": false,
    "mcp_calls": [
      "search_restaurants_combined",
      "recommend_restaurants"
    ]
  }
}
```

### Example 3: Cached Response

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "district": "Causeway Bay",
  "meal_time": "dinner"
}
```

#### Response (200 OK)
```json
{
  "recommendation": {
    "id": "rest_cb_010",
    "name": "Causeway Bay Dinner House",
    "address": "555 Hennessy Road, Causeway Bay",
    "district": "Causeway Bay",
    "meal_type": ["dinner"],
    "sentiment": {
      "likes": 89,
      "dislikes": 6,
      "neutral": 5,
      "total_responses": 100,
      "positive_percentage": 94.0
    },
    "price_range": "$$$",
    "operating_hours": {
      "monday": ["17:30-22:30"],
      "tuesday": ["17:30-22:30"],
      "wednesday": ["17:30-22:30"],
      "thursday": ["17:30-22:30"],
      "friday": ["17:30-23:00"],
      "saturday": ["17:30-23:00"],
      "sunday": ["17:30-22:30"]
    },
    "location_category": "shopping_district",
    "metadata": {
      "cuisine_type": "Cantonese",
      "rating": 4.6,
      "review_count": 203
    }
  },
  "candidates": [
    // ... candidate restaurants
  ],
  "metadata": {
    "search_criteria": {
      "district": "Causeway Bay",
      "meal_time": "dinner"
    },
    "total_found": 18,
    "timestamp": "2024-01-15T10:40:00Z",
    "processing_time_ms": 45,
    "cache_hit": true,
    "mcp_calls": []
  }
}
```

## Error Responses

### Validation Error

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "meal_time": "invalid_meal"
}
```

#### Response (400 Bad Request)
```json
{
  "recommendation": null,
  "candidates": [],
  "metadata": {
    "search_criteria": {},
    "total_found": 0,
    "timestamp": "2024-01-15T10:45:00Z",
    "processing_time_ms": 15,
    "cache_hit": false,
    "mcp_calls": []
  },
  "error": {
    "error_type": "validation_error",
    "message": "meal_time must be one of: breakfast, lunch, dinner",
    "suggested_actions": [
      "Check request parameters",
      "Ensure required fields are provided",
      "Validate parameter formats"
    ],
    "error_code": "VALIDATION_FAILED"
  }
}
```

### Authentication Error

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer invalid_token

{
  "district": "Central district",
  "meal_time": "breakfast"
}
```

#### Response (401 Unauthorized)
```json
{
  "recommendation": null,
  "candidates": [],
  "metadata": {
    "search_criteria": {},
    "total_found": 0,
    "timestamp": "2024-01-15T10:50:00Z",
    "processing_time_ms": 25,
    "cache_hit": false,
    "mcp_calls": []
  },
  "error": {
    "error_type": "authentication_error",
    "message": "JWT token validation failed: Invalid signature",
    "suggested_actions": [
      "Check JWT token validity",
      "Ensure proper Authorization header",
      "Verify token has not expired"
    ],
    "error_code": "AUTH_FAILED"
  }
}
```

### MCP Service Error

#### Response (503 Service Unavailable)
```json
{
  "recommendation": null,
  "candidates": [],
  "metadata": {
    "search_criteria": {
      "district": "Central district",
      "meal_time": "breakfast"
    },
    "total_found": 0,
    "timestamp": "2024-01-15T10:55:00Z",
    "processing_time_ms": 5000,
    "cache_hit": false,
    "mcp_calls": ["search_restaurants_combined"]
  },
  "error": {
    "error_type": "mcp_service_error",
    "message": "restaurant-search-mcp: Connection timeout after 5000ms",
    "suggested_actions": [
      "Try again in a few moments",
      "Check service status",
      "Contact support if problem persists"
    ],
    "error_code": "MCP_SERVICE_UNAVAILABLE"
  }
}
```

### Rate Limit Error

#### Response (429 Too Many Requests)
```json
{
  "recommendation": null,
  "candidates": [],
  "metadata": {
    "search_criteria": {},
    "total_found": 0,
    "timestamp": "2024-01-15T11:00:00Z",
    "processing_time_ms": 10,
    "cache_hit": false,
    "mcp_calls": []
  },
  "error": {
    "error_type": "rate_limit_error",
    "message": "Rate limit exceeded: 100 requests per minute",
    "suggested_actions": [
      "Wait before making another request",
      "Implement exponential backoff",
      "Consider request batching"
    ],
    "error_code": "RATE_LIMIT_EXCEEDED"
  }
}
```

## Error Codes Reference

| Error Code | HTTP Status | Category | Description |
|------------|-------------|----------|-------------|
| `VALIDATION_FAILED` | 400 | validation_error | Request parameters are invalid |
| `AUTH_FAILED` | 401 | authentication_error | JWT token validation failed |
| `AUTH_MISSING` | 401 | authentication_error | No authentication token provided |
| `AUTH_MALFORMED` | 400 | authentication_error | Malformed authorization header |
| `MCP_SERVICE_UNAVAILABLE` | 503 | mcp_service_error | MCP server is unavailable |
| `MCP_TIMEOUT` | 504 | mcp_service_error | MCP server request timeout |
| `MCP_PARSING_ERROR` | 502 | mcp_service_error | Failed to parse MCP response |
| `RATE_LIMIT_EXCEEDED` | 429 | rate_limit_error | Too many requests |
| `INTERNAL_ERROR` | 500 | internal_error | Unexpected server error |
| `RESPONSE_FORMAT_ERROR` | 500 | internal_error | Failed to format response |
| `CACHE_ERROR` | 500 | internal_error | Cache service error |

## Performance Characteristics

### Response Times

| Scenario | Expected Response Time | Notes |
|----------|----------------------|-------|
| Cache Hit | < 100ms | Served from in-memory cache |
| Fresh Request | < 2000ms | Full MCP orchestration |
| Complex Query | < 5000ms | Natural language processing |
| Error Response | < 500ms | Fast error handling |

### Rate Limits

| Limit Type | Value | Window |
|------------|-------|--------|
| Per User | 100 requests | 1 minute |
| Per IP | 500 requests | 1 minute |
| Global | 10,000 requests | 1 minute |

### Caching Behavior

- **Cache TTL**: 30 minutes for successful responses
- **Cache Key**: Based on district + meal_time + date
- **Cache Hit Rate**: ~75% in production
- **Cache Invalidation**: Daily at midnight UTC

## Integration Guidelines

### Client Implementation

#### Recommended HTTP Client Settings

```javascript
// JavaScript/Node.js example
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://your-agentcore-endpoint.amazonaws.com',
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'YourApp/1.0.0'
  }
});

// Add JWT token interceptor
client.interceptors.request.use((config) => {
  const token = getJWTToken(); // Your token retrieval logic
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

#### Error Handling Best Practices

```javascript
async function getRestaurantRecommendation(district, mealTime) {
  try {
    const response = await client.post('/invocations', {
      district: district,
      meal_time: mealTime
    });
    
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data;
      console.error('API Error:', errorData.error);
      
      // Handle specific error types
      switch (errorData.error?.error_code) {
        case 'AUTH_FAILED':
          // Refresh token and retry
          await refreshAuthToken();
          return getRestaurantRecommendation(district, mealTime);
        
        case 'RATE_LIMIT_EXCEEDED':
          // Implement exponential backoff
          await delay(1000);
          return getRestaurantRecommendation(district, mealTime);
        
        case 'MCP_SERVICE_UNAVAILABLE':
          // Show user-friendly error message
          throw new Error('Restaurant service temporarily unavailable');
        
        default:
          throw new Error(errorData.error?.message || 'Unknown error');
      }
    } else if (error.request) {
      // Network error
      throw new Error('Network error - please check your connection');
    } else {
      // Request setup error
      throw new Error('Request configuration error');
    }
  }
}
```

#### Retry Logic Implementation

```javascript
async function makeRequestWithRetry(requestFn, maxRetries = 3) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      
      // Don't retry on client errors (4xx)
      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw error;
      }
      
      // Exponential backoff
      const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}
```

### Frontend Integration

#### React Hook Example

```javascript
import { useState, useEffect } from 'react';

function useRestaurantRecommendation(district, mealTime) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (!district && !mealTime) return;
    
    setLoading(true);
    setError(null);
    
    getRestaurantRecommendation(district, mealTime)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [district, mealTime]);
  
  return { data, loading, error };
}

// Usage in component
function RestaurantRecommendations() {
  const { data, loading, error } = useRestaurantRecommendation(
    'Central district', 
    'breakfast'
  );
  
  if (loading) return <div>Loading recommendations...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return null;
  
  return (
    <div>
      <h2>Recommended Restaurant</h2>
      <RestaurantCard restaurant={data.recommendation} />
      
      <h3>Other Options</h3>
      {data.candidates.map(restaurant => (
        <RestaurantCard key={restaurant.id} restaurant={restaurant} />
      ))}
    </div>
  );
}
```

## Monitoring and Observability

### Health Check Monitoring

```bash
# Basic health check
curl -X GET https://your-endpoint.amazonaws.com/health

# Health check with detailed response
curl -X GET https://your-endpoint.amazonaws.com/health \
  -H "Accept: application/json" | jq '.'
```

### Metrics to Monitor

| Metric | Type | Description |
|--------|------|-------------|
| `response_time_ms` | Histogram | Request processing time |
| `request_count` | Counter | Total requests processed |
| `error_rate` | Gauge | Percentage of failed requests |
| `cache_hit_rate` | Gauge | Cache effectiveness |
| `mcp_call_duration` | Histogram | MCP service call times |
| `jwt_validation_time` | Histogram | Authentication processing time |

### Log Formats

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "correlation_id": "req_1705315800000",
  "message": "Request completed successfully",
  "district": "Central district",
  "meal_time": "breakfast",
  "processing_time_ms": 1180,
  "cache_hit": false,
  "mcp_calls": ["search_restaurants_combined", "recommend_restaurants"],
  "user_id": "user123"
}
```

## Troubleshooting Guide

### Common Issues

#### 1. Authentication Failures

**Symptoms**: 401 errors, "AUTH_FAILED" error codes

**Causes**:
- Expired JWT tokens
- Invalid token signatures
- Misconfigured Cognito User Pool

**Solutions**:
- Verify token expiration time
- Check Cognito configuration
- Ensure proper token refresh logic

#### 2. Slow Response Times

**Symptoms**: Requests taking > 5 seconds

**Causes**:
- MCP service latency
- Network connectivity issues
- Cache misses

**Solutions**:
- Check MCP service health
- Verify network connectivity
- Monitor cache hit rates

#### 3. MCP Service Unavailable

**Symptoms**: "MCP_SERVICE_UNAVAILABLE" errors

**Causes**:
- MCP server downtime
- Network partitions
- Service overload

**Solutions**:
- Check MCP server status
- Verify network connectivity
- Implement circuit breaker patterns

#### 4. Rate Limiting

**Symptoms**: 429 errors, "RATE_LIMIT_EXCEEDED"

**Causes**:
- Too many requests from single client
- Burst traffic patterns

**Solutions**:
- Implement exponential backoff
- Add request queuing
- Consider request batching

### Debug Commands

```bash
# Test authentication
curl -X POST https://your-endpoint.amazonaws.com/invocations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"district": "Central district"}' \
  -v

# Check service health
curl -X GET https://your-endpoint.amazonaws.com/health \
  -H "Accept: application/json" | jq '.components'

# Test with minimal payload
curl -X POST https://your-endpoint.amazonaws.com/invocations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"natural_language_query": "test"}' \
  -w "Response time: %{time_total}s\n"
```

## Security Considerations

### Data Protection

- All requests must use HTTPS
- JWT tokens are validated against AWS Cognito
- Sensitive data is not logged
- Request/response data is encrypted in transit

### Rate Limiting

- Per-user and per-IP rate limits
- Exponential backoff for retry logic
- Circuit breaker patterns for service protection

### Input Validation

- All input parameters are validated
- SQL injection protection (not applicable - no direct DB access)
- XSS protection for natural language queries
- Maximum payload size limits

## Support and Contact

For technical support or questions about the MBTI Travel Assistant API:

- **Documentation**: This document and inline code comments
- **Health Endpoint**: Monitor service status via `/health`
- **Error Codes**: Reference the error codes table for troubleshooting
- **Logs**: Check CloudWatch logs for detailed error information

---

**API Version**: 1.0.0  
**Last Updated**: January 15, 2024  
**BedrockAgentCore Runtime**: Compatible with ARM64 architecture  
**Authentication**: AWS Cognito JWT tokens required