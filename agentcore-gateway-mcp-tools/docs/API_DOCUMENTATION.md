# AgentCore Gateway MCP Tools - API Documentation

## Overview

The AgentCore Gateway for MCP Tools provides RESTful HTTP endpoints that expose restaurant search and reasoning MCP tools through a unified API interface. This documentation covers all available endpoints, authentication requirements, request/response formats, and integration examples.

## Base URL

```
Production: https://your-agentcore-gateway.amazonaws.com
Development: http://localhost:8080
```

## Authentication

All API endpoints require JWT authentication using AWS Cognito User Pool tokens.

### Authentication Header

```http
Authorization: Bearer <jwt_token>
```

### Obtaining JWT Tokens

1. **Cognito User Pool Configuration**:
   - User Pool ID: `us-east-1_KePRX24Bn`
   - Client ID: `1ofgeckef3po4i3us4j1m4chvd`
   - Region: `us-east-1`

2. **Token Discovery URL**:
   ```
   https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
   ```

3. **Authentication Flow**:
   ```javascript
   // Example using AWS Amplify
   import { Auth } from 'aws-amplify';
   
   const token = await Auth.currentSession()
     .then(session => session.getIdToken().getJwtToken());
   ```

## API Endpoints

### 1. Restaurant Search Endpoints

#### 1.1 Search by District

Search for restaurants in specific Hong Kong districts.

**Endpoint**: `POST /api/v1/restaurants/search/district`

**Request Body**:
```json
{
  "districts": ["Central district", "Admiralty", "Causeway Bay"]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "restaurants": [
      {
        "id": "rest_001",
        "name": "Restaurant Name",
        "district": "Central district",
        "address": "123 Main Street",
        "cuisine_type": "Cantonese",
        "price_range": "$$",
        "operating_hours": {
          "monday": "11:00-22:00",
          "tuesday": "11:00-22:00"
        },
        "sentiment": {
          "likes": 85,
          "dislikes": 10,
          "neutral": 5
        }
      }
    ],
    "total_count": 150,
    "districts_searched": ["Central district", "Admiralty", "Causeway Bay"]
  },
  "metadata": {
    "search_type": "district",
    "timestamp": "2025-01-03T10:30:00Z",
    "processing_time_ms": 245
  }
}
```

**cURL Example**:
```bash
curl -X POST "https://your-gateway.amazonaws.com/api/v1/restaurants/search/district" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "districts": ["Central district", "Admiralty"]
  }'
```

#### 1.2 Search by Meal Type

Search for restaurants based on meal service times.

**Endpoint**: `POST /api/v1/restaurants/search/meal-type`

**Request Body**:
```json
{
  "meal_types": ["breakfast", "lunch", "dinner"]
}
```

**Meal Type Definitions**:
- `breakfast`: 07:00-11:29
- `lunch`: 11:30-17:29
- `dinner`: 17:30-22:30

**Response**:
```json
{
  "success": true,
  "data": {
    "restaurants": [
      {
        "id": "rest_002",
        "name": "Breakfast Spot",
        "meal_availability": ["breakfast", "lunch"],
        "operating_hours": {
          "monday": "07:00-15:00"
        }
      }
    ],
    "meal_types_searched": ["breakfast", "lunch", "dinner"],
    "availability_summary": {
      "breakfast": 45,
      "lunch": 120,
      "dinner": 98
    }
  }
}
```

#### 1.3 Combined Search

Search restaurants using both district and meal type filters.

**Endpoint**: `POST /api/v1/restaurants/search/combined`

**Request Body**:
```json
{
  "districts": ["Central district", "Admiralty"],
  "meal_types": ["lunch", "dinner"]
}
```

**Response**: Combined format with both district and meal type filtering applied.

### 2. Restaurant Reasoning Endpoints

#### 2.1 Restaurant Recommendations

Get intelligent restaurant recommendations with sentiment-based ranking.

**Endpoint**: `POST /api/v1/restaurants/recommend`

**Request Body**:
```json
{
  "restaurants": [
    {
      "id": "rest_001",
      "name": "Great Restaurant",
      "sentiment": {
        "likes": 85,
        "dislikes": 10,
        "neutral": 5
      },
      "district": "Central district",
      "cuisine_type": "Cantonese"
    }
  ],
  "ranking_method": "sentiment_likes"
}
```

**Ranking Methods**:
- `sentiment_likes`: Rank by highest likes count
- `combined_sentiment`: Rank by (likes + neutral) percentage

**Response**:
```json
{
  "success": true,
  "data": {
    "recommendation": {
      "id": "rest_001",
      "name": "Great Restaurant",
      "recommendation_score": 0.85,
      "ranking_position": 1,
      "sentiment_analysis": {
        "total_reviews": 100,
        "positive_percentage": 85,
        "satisfaction_score": "high"
      }
    },
    "candidates": [
      {
        "id": "rest_001",
        "name": "Great Restaurant",
        "ranking_position": 1,
        "sentiment_score": 0.85
      }
    ],
    "ranking_method": "sentiment_likes",
    "analysis_summary": {
      "total_restaurants": 1,
      "average_sentiment_score": 0.85,
      "recommendation_confidence": "high"
    }
  }
}
```

#### 2.2 Sentiment Analysis

Analyze sentiment patterns across restaurant data.

**Endpoint**: `POST /api/v1/restaurants/analyze`

**Request Body**:
```json
{
  "restaurants": [
    {
      "id": "rest_001",
      "name": "Restaurant A",
      "sentiment": {
        "likes": 85,
        "dislikes": 10,
        "neutral": 5
      }
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "sentiment_analysis": {
      "average_likes": 85.0,
      "average_dislikes": 10.0,
      "average_neutral": 5.0,
      "satisfaction_distribution": {
        "high_satisfaction": 1,
        "medium_satisfaction": 0,
        "low_satisfaction": 0
      },
      "sentiment_trends": {
        "positive_trend": true,
        "overall_rating": "excellent"
      }
    },
    "restaurant_count": 1,
    "ranking_method": "sentiment_likes"
  }
}
```

### 3. Tool Metadata Endpoint

Get comprehensive tool metadata for foundation model integration.

**Endpoint**: `GET /tools/metadata`

**Response**:
```json
{
  "success": true,
  "data": {
    "tools": [
      {
        "name": "search_restaurants_by_district",
        "description": "Search for restaurants in specific Hong Kong districts",
        "purpose": "Location-based restaurant discovery",
        "endpoint": "/api/v1/restaurants/search/district",
        "method": "POST",
        "parameters": {
          "districts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of Hong Kong district names",
            "required": true,
            "examples": ["Central district", "Admiralty", "Causeway Bay"]
          }
        },
        "response_format": {
          "restaurants": "array of restaurant objects",
          "total_count": "number of results",
          "districts_searched": "districts included in search"
        },
        "use_cases": [
          "Find restaurants in specific areas",
          "Location-based meal planning",
          "District-specific dining recommendations"
        ],
        "mbti_integration": {
          "ENFP": "Use for spontaneous exploration of different districts",
          "ISTJ": "Systematic search within familiar districts",
          "ESFJ": "Find restaurants in social gathering areas"
        },
        "examples": [
          {
            "request": {
              "districts": ["Central district"]
            },
            "description": "Find all restaurants in Central district"
          }
        ]
      }
    ],
    "total_tools": 5,
    "categories": ["search", "reasoning", "analysis"]
  }
}
```

### 4. System Endpoints

#### 4.1 Health Check

**Endpoint**: `GET /health`

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-03T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "mcp_search_server": "healthy",
    "mcp_reasoning_server": "healthy",
    "authentication": "healthy"
  },
  "uptime_seconds": 3600
}
```

#### 4.2 Metrics

**Endpoint**: `GET /metrics`

**Authentication**: Not required

**Response**:
```json
{
  "requests_total": 1250,
  "requests_per_minute": 25.5,
  "average_response_time_ms": 245,
  "error_rate_percentage": 0.8,
  "authentication_success_rate": 99.2,
  "mcp_server_status": {
    "search_server_healthy": true,
    "reasoning_server_healthy": true
  }
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid district names provided",
    "details": {
      "invalid_districts": ["Invalid District"],
      "available_districts": ["Central district", "Admiralty"]
    },
    "timestamp": "2025-01-03T10:30:00Z",
    "request_id": "req_12345"
  }
}
```

### HTTP Status Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request parameters or validation errors |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Endpoint or resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | MCP server unavailable |

### Common Error Scenarios

#### 1. Authentication Errors

**Missing Token**:
```json
{
  "success": false,
  "error": {
    "type": "AuthenticationError",
    "message": "Authorization header required",
    "details": {
      "required_format": "Bearer <jwt_token>",
      "cognito_user_pool": "us-east-1_KePRX24Bn"
    }
  }
}
```

**Invalid Token**:
```json
{
  "success": false,
  "error": {
    "type": "AuthenticationError",
    "message": "Invalid JWT token",
    "details": {
      "token_validation_failed": true,
      "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/..."
    }
  }
}
```

#### 2. Validation Errors

**Invalid Districts**:
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid district names provided",
    "details": {
      "invalid_districts": ["NonExistent District"],
      "available_districts": [
        "Central district", "Admiralty", "Causeway Bay",
        "Wan Chai", "Tsim Sha Tsui", "Mong Kok"
      ]
    }
  }
}
```

**Invalid Meal Types**:
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid meal types provided",
    "details": {
      "invalid_meal_types": ["brunch"],
      "valid_meal_types": ["breakfast", "lunch", "dinner"]
    }
  }
}
```

#### 3. Service Errors

**MCP Server Unavailable**:
```json
{
  "success": false,
  "error": {
    "type": "ServiceUnavailableError",
    "message": "Restaurant search service temporarily unavailable",
    "details": {
      "service": "mcp_search_server",
      "retry_after_seconds": 30,
      "estimated_recovery": "2025-01-03T10:35:00Z"
    }
  }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Rate Limit**: 100 requests per minute per user
- **Burst Limit**: 20 requests per 10 seconds
- **Headers**: Rate limit information is included in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641201600
```

## Request/Response Examples

### Complete Search Workflow

```javascript
// 1. Authenticate and get token
const token = await getJWTToken();

// 2. Search restaurants by district
const searchResponse = await fetch('/api/v1/restaurants/search/district', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    districts: ['Central district', 'Admiralty']
  })
});

const restaurants = await searchResponse.json();

// 3. Get recommendations
const recommendResponse = await fetch('/api/v1/restaurants/recommend', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    restaurants: restaurants.data.restaurants,
    ranking_method: 'sentiment_likes'
  })
});

const recommendations = await recommendResponse.json();
```

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- **Development**: `http://localhost:8080/docs`
- **Production**: `https://your-gateway.amazonaws.com/docs`

### Interactive Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## SDK and Client Libraries

### Python Client Example

```python
import requests
from typing import List, Dict, Any

class AgentCoreGatewayClient:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    def search_by_district(self, districts: List[str]) -> Dict[str, Any]:
        """Search restaurants by district."""
        response = requests.post(
            f'{self.base_url}/api/v1/restaurants/search/district',
            headers=self.headers,
            json={'districts': districts}
        )
        response.raise_for_status()
        return response.json()
    
    def get_recommendations(self, restaurants: List[Dict], 
                          ranking_method: str = 'sentiment_likes') -> Dict[str, Any]:
        """Get restaurant recommendations."""
        response = requests.post(
            f'{self.base_url}/api/v1/restaurants/recommend',
            headers=self.headers,
            json={
                'restaurants': restaurants,
                'ranking_method': ranking_method
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = AgentCoreGatewayClient(
    base_url='https://your-gateway.amazonaws.com',
    jwt_token='your_jwt_token'
)

restaurants = client.search_by_district(['Central district'])
recommendations = client.get_recommendations(restaurants['data']['restaurants'])
```

### JavaScript/TypeScript Client

```typescript
interface RestaurantSearchClient {
  searchByDistrict(districts: string[]): Promise<SearchResponse>;
  searchByMealType(mealTypes: string[]): Promise<SearchResponse>;
  getRecommendations(restaurants: Restaurant[], rankingMethod?: string): Promise<RecommendationResponse>;
}

class AgentCoreGatewayClient implements RestaurantSearchClient {
  constructor(
    private baseUrl: string,
    private jwtToken: string
  ) {}

  private async request<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.jwtToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async searchByDistrict(districts: string[]): Promise<SearchResponse> {
    return this.request('/api/v1/restaurants/search/district', { districts });
  }

  async getRecommendations(
    restaurants: Restaurant[], 
    rankingMethod: string = 'sentiment_likes'
  ): Promise<RecommendationResponse> {
    return this.request('/api/v1/restaurants/recommend', {
      restaurants,
      ranking_method: rankingMethod
    });
  }
}
```

## Testing and Validation

### API Testing Tools

1. **Postman Collection**: Available for download with pre-configured requests
2. **cURL Examples**: Provided for each endpoint
3. **Unit Tests**: Comprehensive test suite included in repository

### Validation Checklist

- [ ] JWT token is valid and not expired
- [ ] Request body matches expected schema
- [ ] District names are valid Hong Kong districts
- [ ] Meal types are one of: breakfast, lunch, dinner
- [ ] Restaurant data includes required sentiment fields
- [ ] Response handling includes error scenarios

## Performance Considerations

### Response Times

- **Search Endpoints**: < 500ms typical response time
- **Reasoning Endpoints**: < 1000ms typical response time
- **Metadata Endpoints**: < 100ms typical response time

### Optimization Tips

1. **Batch Requests**: Combine multiple operations when possible
2. **Caching**: Implement client-side caching for metadata
3. **Pagination**: Use appropriate page sizes for large result sets
4. **Compression**: Enable gzip compression for responses

## Support and Troubleshooting

### Common Issues

1. **Authentication Failures**: Verify JWT token and Cognito configuration
2. **Validation Errors**: Check request format against API schema
3. **Service Unavailable**: Implement retry logic with exponential backoff
4. **Rate Limiting**: Implement proper rate limiting handling

### Debug Information

Enable debug mode by including the `X-Debug: true` header in requests to receive additional diagnostic information.

### Contact Information

- **Documentation**: See deployment guides and troubleshooting documentation
- **Issues**: Report issues through the appropriate channels
- **Updates**: Monitor for API version updates and deprecation notices

---

**Last Updated**: January 3, 2025  
**API Version**: 1.0.0  
**OpenAPI Specification**: 3.0.0