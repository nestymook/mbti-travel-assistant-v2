# Restaurant Reasoning MCP Server - API Reference

## Overview

This document provides detailed API reference for the Restaurant Reasoning MCP Server, including tool specifications, data models, and integration patterns.

## MCP Tools

### 1. recommend_restaurants

Analyzes restaurant sentiment data and provides intelligent recommendations with detailed reasoning.

#### Function Signature
```python
def recommend_restaurants(
    restaurants: List[Dict[str, Any]], 
    ranking_method: str = "sentiment_likes"
) -> str
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `restaurants` | `List[Dict[str, Any]]` | Yes | - | List of restaurant objects with sentiment data |
| `ranking_method` | `str` | No | `"sentiment_likes"` | Ranking algorithm to use |

#### Restaurant Object Schema

Each restaurant in the `restaurants` list must contain:

```json
{
    "id": "string",           // Required: Unique identifier
    "name": "string",         // Required: Restaurant name
    "sentiment": {            // Required: Sentiment data
        "likes": "integer",   // Required: Number of likes (≥0)
        "dislikes": "integer", // Required: Number of dislikes (≥0)
        "neutral": "integer"  // Required: Number of neutral responses (≥0)
    },
    "district": "string",     // Optional: Location district
    "address": "string",      // Optional: Full address
    "cuisine_type": "string", // Optional: Type of cuisine
    "price_range": "string"   // Optional: Price indicator ($, $$, $$$)
}
```

#### Ranking Methods

| Method | Description | Algorithm |
|--------|-------------|-----------|
| `sentiment_likes` | Rank by highest likes count | `ORDER BY likes DESC` |
| `combined_positive` | Rank by net positive sentiment | `ORDER BY (likes - dislikes) DESC` |

#### Return Value

Returns a JSON string containing:

```json
{
    "analysis": {
        "total_restaurants": "integer",
        "ranking_method": "string",
        "top_recommendation": {
            "id": "string",
            "name": "string", 
            "sentiment_score": "number",
            "reasoning": "string"
        }
    },
    "ranked_restaurants": [
        {
            "rank": "integer",
            "id": "string",
            "name": "string",
            "sentiment": {
                "likes": "integer",
                "dislikes": "integer", 
                "neutral": "integer"
            },
            "sentiment_score": "number",
            "reasoning": "string"
        }
    ],
    "summary": "string"
}
```

#### Example Usage

```python
# Example restaurant data
restaurants = [
    {
        "id": "rest_001",
        "name": "Golden Dragon Restaurant",
        "sentiment": {"likes": 45, "dislikes": 5, "neutral": 10},
        "district": "Central",
        "address": "123 Queen's Road Central",
        "cuisine_type": "Cantonese",
        "price_range": "$$"
    },
    {
        "id": "rest_002",
        "name": "Harbour View Cafe", 
        "sentiment": {"likes": 32, "dislikes": 8, "neutral": 15},
        "district": "Tsim Sha Tsui",
        "address": "456 Nathan Road",
        "cuisine_type": "International",
        "price_range": "$"
    }
]

# Get recommendations using sentiment likes
result = recommend_restaurants(restaurants, "sentiment_likes")

# Get recommendations using combined positive sentiment
result = recommend_restaurants(restaurants, "combined_positive")
```

#### Error Handling

The tool validates input and returns structured error responses:

```json
{
    "error": "string",
    "error_type": "validation_error|processing_error",
    "details": "string",
    "timestamp": "ISO8601 datetime"
}
```

Common validation errors:
- Empty restaurant list
- Missing required fields (id, name, sentiment)
- Invalid sentiment values (negative numbers)
- Invalid ranking method

### 2. analyze_restaurant_sentiment

Analyzes sentiment data for restaurants without providing recommendations.

#### Function Signature
```python
def analyze_restaurant_sentiment(restaurants: List[Dict[str, Any]]) -> str
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `restaurants` | `List[Dict[str, Any]]` | Yes | List of restaurant objects with sentiment data |

#### Return Value

Returns a JSON string containing sentiment analysis:

```json
{
    "analysis": {
        "total_restaurants": "integer",
        "sentiment_summary": {
            "total_likes": "integer",
            "total_dislikes": "integer", 
            "total_neutral": "integer",
            "average_likes": "number",
            "average_dislikes": "number",
            "average_neutral": "number"
        },
        "sentiment_distribution": [
            {
                "id": "string",
                "name": "string",
                "sentiment": {
                    "likes": "integer",
                    "dislikes": "integer",
                    "neutral": "integer"
                },
                "sentiment_ratio": {
                    "likes_percentage": "number",
                    "dislikes_percentage": "number", 
                    "neutral_percentage": "number"
                }
            }
        ]
    },
    "insights": [
        "string"  // Array of analytical insights
    ]
}
```

#### Example Usage

```python
# Analyze sentiment patterns
analysis = analyze_restaurant_sentiment(restaurants)
print(analysis)  # JSON string with sentiment analysis
```

## Health Check Endpoints

### GET /health

Health check endpoint that bypasses authentication.

#### Response
```json
{
    "status": "healthy|unhealthy",
    "service": "restaurant-reasoning-mcp",
    "version": "1.0.0",
    "timestamp": "ISO8601 datetime",
    "components": {
        "reasoning_service": "operational|error",
        "authentication": "configured|disabled"
    }
}
```

### GET /metrics

Metrics endpoint that bypasses authentication.

#### Response
```json
{
    "service": "restaurant-reasoning-mcp",
    "metrics": {
        "uptime": "operational",
        "tools_available": 2,
        "authentication_enabled": "boolean"
    },
    "timestamp": "ISO8601 datetime"
}
```

## Data Models

### Restaurant Model

```python
class Restaurant(BaseModel):
    id: str
    name: str
    sentiment: Sentiment
    district: Optional[str] = None
    address: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
```

### Sentiment Model

```python
class Sentiment(BaseModel):
    likes: int = Field(ge=0, description="Number of likes (≥0)")
    dislikes: int = Field(ge=0, description="Number of dislikes (≥0)")
    neutral: int = Field(ge=0, description="Number of neutral responses (≥0)")
```

### Recommendation Result Model

```python
class RecommendationResult(BaseModel):
    analysis: Dict[str, Any]
    ranked_restaurants: List[Dict[str, Any]]
    summary: str
```

### Sentiment Analysis Model

```python
class SentimentAnalysis(BaseModel):
    analysis: Dict[str, Any]
    insights: List[str]
```

## Authentication

### JWT Authentication

The server uses JWT authentication via Amazon Cognito:

```python
# Authentication configuration
auth_config = AuthenticationConfig(
    cognito_config={
        'user_pool_id': 'us-east-1_KePRX24Bn',
        'client_id': '26k0pnja579pdpb1pt6savs27e', 
        'region': 'us-east-1',
        'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration'
    },
    bypass_paths=['/health', '/metrics', '/docs', '/openapi.json', '/'],
    require_authentication=True,
    log_user_context=True
)
```

### Authentication Headers

Include JWT token in requests:

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Bypass Paths

These endpoints bypass authentication:
- `/health` - Health check
- `/metrics` - Metrics
- `/docs` - API documentation
- `/openapi.json` - OpenAPI schema
- `/` - Root endpoint

## Error Responses

### Validation Errors

```json
{
    "error": "Validation failed",
    "error_type": "validation_error",
    "details": "Restaurants parameter must be a list, got str",
    "timestamp": "2025-09-28T13:45:00.000Z"
}
```

### Authentication Errors

```json
{
    "error": "Authentication required",
    "error_type": "authentication_error", 
    "details": "Missing or invalid JWT token",
    "timestamp": "2025-09-28T13:45:00.000Z"
}
```

### Processing Errors

```json
{
    "error": "Processing failed",
    "error_type": "processing_error",
    "details": "Failed to analyze sentiment data",
    "timestamp": "2025-09-28T13:45:00.000Z"
}
```

## Integration Patterns

### MCP Client Integration

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Connect to reasoning server
async with streamablehttp_client(mcp_url, headers) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # List available tools
        tools = await session.list_tools()
        
        # Call recommendation tool
        result = await session.call_tool(
            "recommend_restaurants",
            {
                "restaurants": restaurant_data,
                "ranking_method": "sentiment_likes"
            }
        )
```

### Kiro IDE Integration

```python
# Direct tool usage in Kiro
restaurants = [
    {"id": "r1", "name": "Restaurant A", "sentiment": {"likes": 50, "dislikes": 5, "neutral": 10}},
    {"id": "r2", "name": "Restaurant B", "sentiment": {"likes": 30, "dislikes": 15, "neutral": 8}}
]

# Get recommendations
recommendations = recommend_restaurants(restaurants, "sentiment_likes")

# Analyze sentiment
analysis = analyze_restaurant_sentiment(restaurants)
```

### Foundation Model Integration

The tools are designed to work with foundation models for natural language processing:

```
User: "Analyze these restaurants and recommend the best one based on customer satisfaction"

Foundation Model: Uses recommend_restaurants tool with provided restaurant data

Response: "Based on sentiment analysis, Golden Dragon Restaurant is the top recommendation with 45 likes and only 5 dislikes, indicating high customer satisfaction..."
```

## Performance Considerations

### Request Limits
- Maximum restaurants per request: 1000
- Request timeout: 30 seconds
- Memory usage: ~1MB per 100 restaurants

### Optimization Tips
- Batch multiple restaurants in single requests
- Use appropriate ranking method for use case
- Cache results for repeated queries
- Monitor memory usage with large datasets

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-09-28 | Initial release with sentiment analysis and recommendations |

---

**Last Updated**: September 28, 2025  
**API Version**: 1.0.0