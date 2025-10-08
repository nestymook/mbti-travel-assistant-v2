# MCP OpenAPI Schemas Documentation

## Overview

This document provides comprehensive OpenAPI 3.0.3 schemas for both restaurant MCP (Model Context Protocol) services in the MBTI Travel Planning system:

1. **Restaurant Search MCP** - District and meal-type based restaurant search
2. **Restaurant Reasoning MCP** - Sentiment analysis and intelligent recommendations

## Generated Files

### 1. Restaurant Search MCP API
**File:** `restaurant-search-mcp/openapi.yaml`

**Purpose:** Provides restaurant search functionality across Hong Kong districts with meal type filtering based on operating hours analysis.

**Key Endpoints:**
- `POST /mcp/tools/search_restaurants_by_district` - Search by Hong Kong districts
- `POST /mcp/tools/search_restaurants_by_meal_type` - Search by meal times (breakfast, lunch, dinner)
- `POST /mcp/tools/search_restaurants_combined` - Combined district and meal type search
- `GET /health` - Health check endpoint

**Key Features:**
- Comprehensive coverage of Hong Kong districts (Hong Kong Island, Kowloon, New Territories, Lantau)
- Intelligent meal type detection based on operating hours
- Flexible combined search capabilities
- Rich restaurant data including sentiment, pricing, and operating hours

### 2. Restaurant Reasoning MCP API
**File:** `restaurant-search-result-reasoning-mcp/openapi.yaml`

**Purpose:** Provides intelligent restaurant recommendations based on customer sentiment analysis and data-driven ranking algorithms.

**Key Endpoints:**
- `POST /mcp/tools/recommend_restaurants` - Analyze sentiment and provide recommendations
- `POST /mcp/tools/analyze_restaurant_sentiment` - Sentiment analysis without recommendations
- `GET /health` - Health check endpoint

**Key Features:**
- Multiple ranking algorithms (sentiment likes, combined sentiment)
- Comprehensive sentiment analysis with statistics
- Data validation and quality assessment
- Intelligent candidate selection with random recommendation from top performers

## API Schema Highlights

### Restaurant Search MCP Schema Features

#### District Coverage
The API covers all major Hong Kong districts:
- **Hong Kong Island:** Admiralty, Central district, Causeway Bay, Wan Chai
- **Kowloon:** Tsim Sha Tsui, Mong Kok, Yau Ma Tei, Jordan
- **New Territories:** Sha Tin, Tsuen Wan, Tai Po, Tuen Mun
- **Lantau:** Tung Chung, Discovery Bay

#### Meal Type Analysis
Intelligent meal type detection based on operating hours:
- **Breakfast:** 7:00-11:29 (morning dining, cafes, dim sum)
- **Lunch:** 11:30-17:29 (business lunch, casual dining)
- **Dinner:** 17:30-22:30 (evening dining, fine dining)

#### Data Models
```yaml
Restaurant:
  properties:
    id: string (unique identifier)
    name: string (restaurant name)
    address: string (full address)
    mealType: array of strings (cuisine types)
    sentiment: Sentiment object
    district: string (Hong Kong district)
    priceRange: string ($ to $$$$)
    operatingHours: OperatingHours object
    metadata: RestaurantMetadata object

Sentiment:
  properties:
    likes: integer (positive reviews)
    dislikes: integer (negative reviews)
    neutral: integer (neutral reviews)

OperatingHours:
  properties:
    "Mon - Fri": array of time ranges
    "Sat - Sun": array of time ranges
    "Public Holiday": array of time ranges
```

### Restaurant Reasoning MCP Schema Features

#### Ranking Methods
- **sentiment_likes:** Ranks by highest number of customer likes (popularity-focused)
- **combined_sentiment:** Ranks by combined likes + neutral percentage (inclusive approach)

#### Analysis Capabilities
- Individual restaurant sentiment scores and percentages
- Overall statistics across restaurant datasets
- Data validation with detailed error reporting
- Candidate selection with top 20 restaurants
- Random recommendation selection from top candidates

#### Enhanced Data Models
```yaml
RestaurantInput:
  required: [id, name, sentiment]
  properties:
    id: string
    name: string
    sentiment: SentimentInput object
    # Optional fields: address, meal_type, district, price_range

SentimentInput:
  required: [likes, dislikes, neutral]
  properties:
    likes: integer (≥ 0)
    dislikes: integer (≥ 0)
    neutral: integer (≥ 0)

SentimentOutput:
  extends: SentimentInput
  additional_properties:
    total_responses: integer
    likes_percentage: float
    combined_positive_percentage: float

RecommendationResponse:
  properties:
    recommendation: RestaurantOutput (single recommended restaurant)
    candidates: array of CandidateRestaurant (top performers)
    analysis_summary: statistical analysis
    ranking_method: string
```

## Request/Response Examples

### Restaurant Search Examples

#### Search by District
```json
POST /mcp/tools/search_restaurants_by_district
{
  "districts": ["Central district", "Tsim Sha Tsui"]
}

Response:
{
  "success": true,
  "query_type": "district_search",
  "districts": ["Central district", "Tsim Sha Tsui"],
  "restaurant_count": 45,
  "restaurants": [...]
}
```

#### Search by Meal Type
```json
POST /mcp/tools/search_restaurants_by_meal_type
{
  "meal_types": ["lunch", "dinner"]
}

Response:
{
  "success": true,
  "query_type": "meal_type_search",
  "meal_types": ["lunch", "dinner"],
  "restaurant_count": 120,
  "restaurants": [...]
}
```

### Restaurant Reasoning Examples

#### Get Recommendations
```json
POST /mcp/tools/recommend_restaurants
{
  "restaurants": [
    {
      "id": "rest_001",
      "name": "Dim Sum Palace",
      "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
    }
  ],
  "ranking_method": "sentiment_likes"
}

Response:
{
  "success": true,
  "recommendation_type": "intelligent_analysis",
  "ranking_method": "sentiment_likes",
  "recommendation": {
    "id": "rest_001",
    "name": "Dim Sum Palace",
    "sentiment": {
      "likes": 85,
      "likes_percentage": 85.0,
      "combined_positive_percentage": 90.0
    }
  },
  "candidates": [...],
  "analysis_summary": {...}
}
```

#### Analyze Sentiment
```json
POST /mcp/tools/analyze_restaurant_sentiment
{
  "restaurants": [
    {
      "id": "rest_001",
      "name": "Restaurant A",
      "sentiment": {"likes": 150, "dislikes": 20, "neutral": 30}
    }
  ]
}

Response:
{
  "success": true,
  "analysis_type": "sentiment_analysis",
  "total_restaurants_analyzed": 1,
  "overall_statistics": {
    "total_likes": 150,
    "average_likes_percentage": 75.0
  },
  "restaurant_sentiment_scores": [...]
}
```

## Error Handling

Both APIs provide comprehensive error handling with:

### Error Response Format
```yaml
ErrorResponse:
  properties:
    success: false
    response: string (user-friendly message)
    error:
      message: string (technical error)
      type: string (error classification)
      user_message: string (user-friendly explanation)
    suggestions: array of strings (helpful suggestions)
    timestamp: string (ISO datetime)
    agent_type: string (service identifier)
```

### Error Types
- **validation_error:** Invalid input parameters or data structure
- **processing_error:** Issues during search or analysis operations
- **reasoning_error:** Problems with sentiment analysis or recommendation logic
- **data_error:** Data format or content issues
- **system_error:** Internal service errors

## Authentication

Both APIs use JWT Bearer token authentication:

```yaml
securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
```

## Health Monitoring

Both services provide health check endpoints:

### Restaurant Search Health Check
```json
GET /health
Response:
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:30:00Z",
  "services": {
    "district_service": true,
    "s3_connection": true,
    "time_service": true
  }
}
```

### Restaurant Reasoning Health Check
```json
GET /health
Response:
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:30:00Z",
  "capabilities": [
    "sentiment_analysis",
    "intelligent_recommendations",
    "ranking_algorithms",
    "data_validation"
  ]
}
```

## Integration Guidelines

### Using Restaurant Search MCP
1. **District Search:** Use when users specify locations or areas
2. **Meal Type Search:** Use when users ask about specific dining times
3. **Combined Search:** Use when users specify both location and meal preferences
4. **Data Processing:** Handle operating hours analysis for meal type detection

### Using Restaurant Reasoning MCP
1. **Recommendations:** Use when users want specific restaurant suggestions
2. **Analysis:** Use when users want to understand sentiment patterns
3. **Ranking Methods:** Choose based on user preferences (popularity vs. inclusivity)
4. **Data Validation:** Ensure proper sentiment data structure before analysis

### Workflow Integration
```
1. Search Phase (Restaurant Search MCP)
   ↓ Get restaurant data with sentiment
2. Analysis Phase (Restaurant Reasoning MCP)
   ↓ Analyze sentiment and generate recommendations
3. Present Results
   ↓ Show recommended restaurants with analysis
```

## Technical Specifications

### OpenAPI Version
- **Version:** 3.0.3
- **Format:** YAML
- **Validation:** Full schema validation with examples

### Schema Features
- Comprehensive data models with validation
- Detailed request/response examples
- Error handling specifications
- Security scheme definitions
- External documentation links

### Compliance
- RESTful API design principles
- JSON request/response format
- HTTP status code standards
- Bearer token authentication
- Comprehensive error responses

## Usage Notes

1. **Data Requirements:** Restaurant reasoning requires sentiment data; search service provides it
2. **District Names:** Use exact district names as specified in the schema
3. **Meal Types:** Limited to "breakfast", "lunch", "dinner" with specific time ranges
4. **Ranking Methods:** Choose based on analysis goals (popularity vs. inclusivity)
5. **Error Handling:** Always check success field and handle error responses appropriately

## Future Enhancements

Potential schema extensions:
- Additional ranking algorithms
- More granular time-based filtering
- Enhanced metadata fields
- Batch processing capabilities
- Real-time sentiment updates
- Geographic coordinate support
- Multi-language support

These OpenAPI schemas provide a solid foundation for integrating both MCP services into larger applications while maintaining clear API contracts and comprehensive documentation.