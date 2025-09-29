# MBTI Travel Assistant - API Documentation

## Overview

The MBTI Travel Assistant is a BedrockAgentCore runtime service that generates comprehensive 3-day travel itineraries based on MBTI personality types. It receives HTTP requests with 4-character MBTI personality codes, uses Amazon Nova Pro foundation model to query an OpenSearch knowledge base for personality-matched tourist spots, and integrates with existing MCP servers for restaurant recommendations.

## Base Information

- **Service Type**: BedrockAgentCore Runtime
- **Architecture**: ARM64 containers required
- **Authentication**: JWT tokens via AWS Cognito
- **Protocol**: HTTP/HTTPS with JSON payloads
- **Response Format**: Structured JSON with 3-day itinerary, candidate lists, and metadata
- **Foundation Model**: Amazon Nova Pro for knowledge base queries
- **Knowledge Base**: OpenSearch with MBTI-matched tourist spots
- **Response Time**: < 10 seconds for complete 3-day itinerary generation

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
  "MBTI_personality": "INFJ"
}
```

### Token Requirements

- **Issuer**: AWS Cognito User Pool
- **Algorithm**: RS256
- **Claims**: Must include `sub` (user ID) and valid `exp` (expiration)
- **Scope**: MBTI itinerary generation access

### Authentication Errors

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `AUTH_FAILED` | 401 | Invalid or expired JWT token |
| `AUTH_MISSING` | 401 | No authentication token provided |
| `AUTH_MALFORMED` | 400 | Malformed authorization header |

## API Endpoints

### POST /invocations

The main entrypoint for MBTI-based 3-day itinerary generation following BedrockAgentCore runtime patterns.

#### Request Format

```http
POST /invocations
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "MBTI_personality": "INFJ",
  "user_context": {
    "user_id": "user123",
    "preferences": {}
  }
}
```####
 Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `MBTI_personality` | string | Yes | 4-character MBTI personality code (e.g., INFJ, ENFP, INTJ) |
| `user_context` | object | Optional | User context from JWT token |

#### Valid MBTI Personality Types

| Analysts | Diplomats | Sentinels | Explorers |
|----------|-----------|-----------|-----------|
| INTJ | INFJ | ISTJ | ISTP |
| INTP | INFP | ISFJ | ISFP |
| ENTJ | ENFJ | ESTJ | ESTP |
| ENTP | ENFP | ESFJ | ESFP |

#### Response Format

The response contains a complete 3-day itinerary with morning/afternoon/night sessions and breakfast/lunch/dinner assignments for each day:

```json
{
  "main_itinerary": {
    "day_1": {
      "morning_session": {
        "id": "spot_001",
        "name": "Hong Kong Museum of Art",
        "address": "10 Salisbury Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "area": "Tsim Sha Tsui",
        "operating_hours": "10:00-18:00",
        "operating_days": "Tuesday-Sunday",
        "location_category": "Cultural",
        "description": "Contemporary and traditional Chinese art",
        "MBTI_match": true
      },
      "afternoon_session": {
        "id": "spot_002", 
        "name": "Avenue of Stars",
        "address": "Tsim Sha Tsui Promenade",
        "district": "Tsim Sha Tsui",
        "area": "Tsim Sha Tsui",
        "operating_hours": "24 hours",
        "operating_days": "Daily",
        "location_category": "Scenic",
        "description": "Waterfront promenade with harbor views",
        "MBTI_match": true
      },
      "night_session": {
        "id": "spot_003",
        "name": "Symphony of Lights",
        "address": "Victoria Harbour",
        "district": "Tsim Sha Tsui",
        "area": "Tsim Sha Tsui", 
        "operating_hours": "20:00-20:15",
        "operating_days": "Daily",
        "location_category": "Entertainment",
        "description": "Multimedia light and sound show",
        "MBTI_match": true
      },      "br
eakfast": {
        "id": "rest_001",
        "name": "Morning Cafe TST",
        "address": "15 Nathan Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "operating_hours": {
          "monday": ["07:00-11:30"],
          "tuesday": ["07:00-11:30"],
          "wednesday": ["07:00-11:30"],
          "thursday": ["07:00-11:30"],
          "friday": ["07:00-11:30"],
          "saturday": ["08:00-12:00"],
          "sunday": ["08:00-12:00"]
        },
        "meal_type": ["breakfast"],
        "sentiment": {
          "likes": 85,
          "dislikes": 10,
          "neutral": 5
        }
      },
      "lunch": {
        "id": "rest_002",
        "name": "Harbour View Restaurant",
        "address": "25 Canton Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "operating_hours": {
          "monday": ["11:30-15:00"],
          "tuesday": ["11:30-15:00"],
          "wednesday": ["11:30-15:00"],
          "thursday": ["11:30-15:00"],
          "friday": ["11:30-15:00"],
          "saturday": ["11:30-15:30"],
          "sunday": ["11:30-15:30"]
        },
        "meal_type": ["lunch"],
        "sentiment": {
          "likes": 78,
          "dislikes": 12,
          "neutral": 10
        }
      },
      "dinner": {
        "id": "rest_003",
        "name": "Evening Dining TST",
        "address": "35 Salisbury Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "operating_hours": {
          "monday": ["17:30-22:30"],
          "tuesday": ["17:30-22:30"],
          "wednesday": ["17:30-22:30"],
          "thursday": ["17:30-22:30"],
          "friday": ["17:30-23:00"],
          "saturday": ["17:30-23:00"],
          "sunday": ["17:30-22:30"]
        },
        "meal_type": ["dinner"],
        "sentiment": {
          "likes": 92,
          "dislikes": 5,
          "neutral": 3
        }
      }
    },    "day_2
": {
      // Similar structure for day 2 with different locations
    },
    "day_3": {
      // Similar structure for day 3 with different locations
    }
  },
  "candidate_tourist_spots": {
    "day_1": [
      {
        "id": "spot_alt_001",
        "name": "Hong Kong Space Museum",
        "address": "10 Salisbury Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "area": "Tsim Sha Tsui",
        "operating_hours": "10:00-21:00",
        "operating_days": "Monday, Wednesday-Sunday",
        "location_category": "Educational",
        "description": "Space and astronomy exhibits",
        "MBTI_match": true
      }
      // ... more candidate spots for day 1
    ],
    "day_2": [
      // ... candidate spots for day 2
    ],
    "day_3": [
      // ... candidate spots for day 3
    ]
  },
  "candidate_restaurants": {
    "day_1": {
      "breakfast": [
        {
          "id": "rest_alt_001",
          "name": "TST Morning Delight",
          "address": "20 Nathan Road, Tsim Sha Tsui",
          "district": "Tsim Sha Tsui",
          "operating_hours": {
            "monday": ["06:30-11:00"],
            "tuesday": ["06:30-11:00"],
            "wednesday": ["06:30-11:00"],
            "thursday": ["06:30-11:00"],
            "friday": ["06:30-11:00"],
            "saturday": ["07:00-12:00"],
            "sunday": ["07:00-12:00"]
          },
          "meal_type": ["breakfast"],
          "sentiment": {
            "likes": 80,
            "dislikes": 12,
            "neutral": 8
          }
        }
        // ... more breakfast candidates
      ],
      "lunch": [
        // ... lunch candidates for day 1
      ],
      "dinner": [
        // ... dinner candidates for day 1
      ]
    },
    "day_2": {
      // ... restaurant candidates for day 2
    },
    "day_3": {
      // ... restaurant candidates for day 3
    }
  },  "met
adata": {
    "MBTI_personality": "INFJ",
    "generation_timestamp": "2024-01-15T10:30:00Z",
    "total_spots_found": 45,
    "total_restaurants_found": 120,
    "processing_time_ms": 8500,
    "validation_status": "passed",
    "nova_pro_queries": 3,
    "mcp_calls": [
      "search_restaurants_by_meal_type",
      "search_restaurants_combined",
      "recommend_restaurants"
    ],
    "cache_hit": false
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `main_itinerary` | ItineraryObject | Complete 3-day itinerary with sessions and meals |
| `candidate_tourist_spots` | CandidateSpots | Alternative tourist spots organized by day |
| `candidate_restaurants` | CandidateRestaurants | Alternative restaurants organized by day and meal |
| `metadata` | ResponseMetadata | Generation metadata and timing information |
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
    "nova_pro_client": {
      "status": "healthy",
      "response_time_ms": 245,
      "last_check": "2024-01-15T10:29:55Z"
    },
    "knowledge_base": {
      "status": "healthy",
      "response_time_ms": 180,
      "last_check": "2024-01-15T10:29:55Z"
    },
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
  }
}
```## Da
ta Models

### Tourist Spot Object

```json
{
  "id": "string",
  "name": "string", 
  "address": "string",
  "district": "string",
  "area": "string",
  "operating_hours": "string",
  "operating_days": "string",
  "location_category": "string",
  "description": "string",
  "MBTI_match": "boolean"
}
```

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
    "neutral": "integer"
  },
  "operating_hours": {
    "monday": ["string"],
    "tuesday": ["string"],
    "wednesday": ["string"],
    "thursday": ["string"],
    "friday": ["string"],
    "saturday": ["string"],
    "sunday": ["string"]
  }
}
```

### ResponseMetadata Object

```json
{
  "MBTI_personality": "string",
  "generation_timestamp": "string (ISO 8601)",
  "total_spots_found": "integer",
  "total_restaurants_found": "integer",
  "processing_time_ms": "integer",
  "validation_status": "string",
  "nova_pro_queries": "integer",
  "mcp_calls": ["string"],
  "cache_hit": "boolean"
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
```#
# Example Requests and Responses

### Example 1: INFJ Personality Type

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "MBTI_personality": "INFJ"
}
```

#### Response (200 OK)
```json
{
  "main_itinerary": {
    "day_1": {
      "morning_session": {
        "id": "spot_001",
        "name": "Hong Kong Museum of Art",
        "address": "10 Salisbury Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "area": "Tsim Sha Tsui",
        "operating_hours": "10:00-18:00",
        "operating_days": "Tuesday-Sunday",
        "location_category": "Cultural",
        "description": "Contemporary and traditional Chinese art",
        "MBTI_match": true
      },
      "afternoon_session": {
        "id": "spot_002",
        "name": "Avenue of Stars",
        "address": "Tsim Sha Tsui Promenade",
        "district": "Tsim Sha Tsui",
        "area": "Tsim Sha Tsui",
        "operating_hours": "24 hours",
        "operating_days": "Daily",
        "location_category": "Scenic",
        "description": "Waterfront promenade with harbor views",
        "MBTI_match": true
      },
      "night_session": {
        "id": "spot_003",
        "name": "Symphony of Lights",
        "address": "Victoria Harbour",
        "district": "Tsim Sha Tsui",
        "area": "Tsim Sha Tsui",
        "operating_hours": "20:00-20:15",
        "operating_days": "Daily",
        "location_category": "Entertainment",
        "description": "Multimedia light and sound show",
        "MBTI_match": true
      },
      "breakfast": {
        "id": "rest_001",
        "name": "Morning Cafe TST",
        "address": "15 Nathan Road, Tsim Sha Tsui",
        "district": "Tsim Sha Tsui",
        "operating_hours": {
          "monday": ["07:00-11:30"]
        },
        "meal_type": ["breakfast"],
        "sentiment": {
          "likes": 85,
          "dislikes": 10,
          "neutral": 5
        }
      }
    }
  },
  "metadata": {
    "MBTI_personality": "INFJ",
    "generation_timestamp": "2024-01-15T10:30:00Z",
    "total_spots_found": 45,
    "total_restaurants_found": 120,
    "processing_time_ms": 8500,
    "validation_status": "passed"
  }
}
```### E
xample 2: ENFP Personality Type

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "MBTI_personality": "ENFP",
  "user_context": {
    "user_id": "user456",
    "preferences": {
      "activity_level": "high"
    }
  }
}
```

#### Response (200 OK)
```json
{
  "main_itinerary": {
    "day_1": {
      "morning_session": {
        "id": "spot_010",
        "name": "Ocean Park",
        "address": "Ocean Park Road, Aberdeen",
        "district": "Southern",
        "area": "Aberdeen",
        "operating_hours": "10:00-19:00",
        "operating_days": "Daily",
        "location_category": "Theme Park",
        "description": "Marine life theme park with rides",
        "MBTI_match": true
      },
      "afternoon_session": {
        "id": "spot_011",
        "name": "Aberdeen Fishing Village",
        "address": "Aberdeen Harbour, Aberdeen",
        "district": "Southern",
        "area": "Aberdeen",
        "operating_hours": "24 hours",
        "operating_days": "Daily",
        "location_category": "Cultural",
        "description": "Traditional floating village",
        "MBTI_match": true
      },
      "night_session": {
        "id": "spot_012",
        "name": "Lan Kwai Fong",
        "address": "Lan Kwai Fong, Central",
        "district": "Central and Western",
        "area": "Central",
        "operating_hours": "18:00-02:00",
        "operating_days": "Daily",
        "location_category": "Entertainment",
        "description": "Vibrant nightlife district",
        "MBTI_match": true
      }
    }
  },
  "metadata": {
    "MBTI_personality": "ENFP",
    "generation_timestamp": "2024-01-15T10:35:00Z",
    "total_spots_found": 52,
    "total_restaurants_found": 135,
    "processing_time_ms": 7800,
    "validation_status": "passed"
  }
}
```#
# Error Responses

### Validation Error

#### Request
```http
POST /invocations
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "MBTI_personality": "INVALID"
}
```

#### Response (400 Bad Request)
```json
{
  "main_itinerary": null,
  "candidate_tourist_spots": {},
  "candidate_restaurants": {},
  "metadata": {
    "MBTI_personality": "INVALID",
    "generation_timestamp": "2024-01-15T10:45:00Z",
    "total_spots_found": 0,
    "total_restaurants_found": 0,
    "processing_time_ms": 15,
    "validation_status": "failed"
  },
  "error": {
    "error_type": "validation_error",
    "message": "Invalid MBTI personality format. Expected 4-character code like INFJ, ENFP.",
    "suggested_actions": [
      "Provide valid MBTI personality type",
      "Check supported MBTI types in documentation",
      "Ensure 4-character format (e.g., INFJ, ENFP)"
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
  "MBTI_personality": "INFJ"
}
```

#### Response (401 Unauthorized)
```json
{
  "main_itinerary": null,
  "candidate_tourist_spots": {},
  "candidate_restaurants": {},
  "metadata": {
    "generation_timestamp": "2024-01-15T10:50:00Z",
    "processing_time_ms": 25,
    "validation_status": "auth_failed"
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
```### Knowle
dge Base Service Error

#### Response (503 Service Unavailable)
```json
{
  "main_itinerary": null,
  "candidate_tourist_spots": {},
  "candidate_restaurants": {},
  "metadata": {
    "MBTI_personality": "INFJ",
    "generation_timestamp": "2024-01-15T10:55:00Z",
    "processing_time_ms": 5000,
    "validation_status": "service_error",
    "nova_pro_queries": 1
  },
  "error": {
    "error_type": "knowledge_base_error",
    "message": "Nova Pro knowledge base query failed: Connection timeout after 5000ms",
    "suggested_actions": [
      "Try again in a few moments",
      "Check knowledge base service status",
      "Contact support if problem persists"
    ],
    "error_code": "KNOWLEDGE_BASE_UNAVAILABLE"
  }
}
```

### MCP Service Error

#### Response (503 Service Unavailable)
```json
{
  "main_itinerary": {
    "day_1": {
      "morning_session": {
        "id": "spot_001",
        "name": "Hong Kong Museum of Art",
        "MBTI_match": true
      }
    }
  },
  "candidate_tourist_spots": {},
  "candidate_restaurants": {},
  "metadata": {
    "MBTI_personality": "INFJ",
    "generation_timestamp": "2024-01-15T11:00:00Z",
    "processing_time_ms": 3000,
    "validation_status": "partial_success",
    "mcp_calls": ["search_restaurants_by_meal_type"]
  },
  "error": {
    "error_type": "mcp_service_error",
    "message": "restaurant-search-mcp: Connection timeout after 3000ms",
    "suggested_actions": [
      "Tourist spots assigned successfully",
      "Restaurant assignments failed - try again",
      "Check MCP service status"
    ],
    "error_code": "MCP_SERVICE_UNAVAILABLE"
  }
}
```

## Error Codes Reference

| Error Code | HTTP Status | Category | Description |
|------------|-------------|----------|-------------|
| `VALIDATION_FAILED` | 400 | validation_error | MBTI personality format is invalid |
| `AUTH_FAILED` | 401 | authentication_error | JWT token validation failed |
| `AUTH_MISSING` | 401 | authentication_error | No authentication token provided |
| `AUTH_MALFORMED` | 400 | authentication_error | Malformed authorization header |
| `KNOWLEDGE_BASE_UNAVAILABLE` | 503 | knowledge_base_error | Nova Pro knowledge base is unavailable |
| `KNOWLEDGE_BASE_TIMEOUT` | 504 | knowledge_base_error | Knowledge base query timeout |
| `KNOWLEDGE_BASE_PARSING_ERROR` | 502 | knowledge_base_error | Failed to parse knowledge base response |
| `MCP_SERVICE_UNAVAILABLE` | 503 | mcp_service_error | MCP server is unavailable |
| `MCP_TIMEOUT` | 504 | mcp_service_error | MCP server request timeout |
| `MCP_PARSING_ERROR` | 502 | mcp_service_error | Failed to parse MCP response |
| `SESSION_ASSIGNMENT_FAILED` | 500 | internal_error | Failed to assign tourist spots to sessions |
| `RESTAURANT_ASSIGNMENT_FAILED` | 500 | internal_error | Failed to assign restaurants to meals |
| `VALIDATION_LOGIC_FAILED` | 500 | internal_error | Itinerary validation failed |
| `RESPONSE_FORMAT_ERROR` | 500 | internal_error | Failed to format response |
| `INTERNAL_ERROR` | 500 | internal_error | Unexpected server error |## Per
formance Characteristics

### Response Times

| Scenario | Expected Response Time | Notes |
|----------|----------------------|-------|
| Cache Hit | < 500ms | Served from in-memory cache |
| Fresh MBTI Request | < 10000ms | Full Nova Pro + MCP orchestration |
| Knowledge Base Only | < 5000ms | Tourist spots without restaurants |
| Error Response | < 1000ms | Fast error handling |

### Rate Limits

| Limit Type | Value | Window |
|------------|-------|--------|
| Per User | 10 requests | 1 minute |
| Per IP | 50 requests | 1 minute |
| Global | 1,000 requests | 1 minute |

### Caching Behavior

- **Cache TTL**: 24 hours for successful MBTI responses
- **Cache Key**: Based on MBTI_personality + date
- **Cache Hit Rate**: ~60% in production (MBTI types are limited)
- **Cache Invalidation**: Daily at midnight UTC

## MBTI Personality Matching Logic

### Personality Trait Mapping

| MBTI Type | Preferred Activities | Location Categories | Session Preferences |
|-----------|---------------------|-------------------|-------------------|
| **INFJ** | Cultural, Reflective, Meaningful | Museums, Temples, Gardens | Morning: Cultural, Afternoon: Scenic, Night: Quiet |
| **ENFP** | Social, Adventurous, Diverse | Theme Parks, Markets, Entertainment | Morning: Active, Afternoon: Social, Night: Vibrant |
| **INTJ** | Strategic, Educational, Efficient | Museums, Architecture, Technology | Morning: Educational, Afternoon: Strategic, Night: Efficient |
| **ESTP** | Active, Spontaneous, Physical | Sports, Adventure, Outdoor | Morning: Physical, Afternoon: Adventure, Night: Social |
| **ISFJ** | Traditional, Service, Community | Cultural Sites, Local Markets, Family-friendly | Morning: Traditional, Afternoon: Community, Night: Quiet |
| **ENTP** | Innovative, Experimental, Intellectual | Science Museums, Tech Centers, Unique Experiences | Morning: Innovative, Afternoon: Experimental, Night: Intellectual |

### Session Assignment Logic

#### Morning Sessions (07:00-11:59)
- **Priority 1**: MBTI-matched spots with morning operating hours
- **Priority 2**: MBTI-matched spots with no operating hours restriction
- **Priority 3**: Non-MBTI spots with morning operating hours
- **Fallback**: Any available spot with appropriate hours

#### Afternoon Sessions (12:00-17:59)
- **Priority 1**: Same district as morning spot + MBTI-matched + afternoon hours
- **Priority 2**: Same area as morning spot + MBTI-matched + afternoon hours
- **Priority 3**: Any MBTI-matched spot with afternoon hours
- **Priority 4**: Same district/area + non-MBTI spots
- **Fallback**: Any available spot with appropriate hours

#### Night Sessions (18:00-23:59)
- **Priority 1**: Same district as morning/afternoon + MBTI-matched + night hours
- **Priority 2**: Same area as morning/afternoon + MBTI-matched + night hours
- **Priority 3**: Any MBTI-matched spot with night hours
- **Priority 4**: Same district/area + non-MBTI spots
- **Fallback**: Any available spot with appropriate hours

### Restaurant Assignment Logic

#### Breakfast (06:00-11:29)
- **Priority 1**: Same district as morning tourist spot
- **Priority 2**: Adjacent districts
- **Priority 3**: Any district with breakfast operating hours

#### Lunch (11:30-17:29)
- **Priority 1**: Same district as morning or afternoon tourist spot
- **Priority 2**: Adjacent districts
- **Priority 3**: Any district with lunch operating hours

#### Dinner (17:30-23:59)
- **Priority 1**: Same district as afternoon or night tourist spot
- **Priority 2**: Adjacent districts
- **Priority 3**: Any district with dinner operating hours## 
Integration Guidelines

### Client Implementation

#### Recommended HTTP Client Settings

```javascript
// JavaScript/Node.js example
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://your-agentcore-endpoint.amazonaws.com',
  timeout: 15000, // 15 second timeout for itinerary generation
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
async function generateMBTIItinerary(mbtiPersonality) {
  try {
    const response = await client.post('/invocations', {
      MBTI_personality: mbtiPersonality
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
          return generateMBTIItinerary(mbtiPersonality);
        
        case 'VALIDATION_FAILED':
          // Show validation error to user
          throw new Error(`Invalid MBTI type: ${mbtiPersonality}`);
        
        case 'KNOWLEDGE_BASE_UNAVAILABLE':
          // Show user-friendly error message
          throw new Error('Travel planning service temporarily unavailable');
        
        case 'MCP_SERVICE_UNAVAILABLE':
          // Partial success - show what we have
          if (errorData.main_itinerary) {
            console.warn('Restaurants unavailable, showing tourist spots only');
            return errorData;
          }
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
async function makeRequestWithRetry(requestFn, maxRetries = 2) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      
      // Don't retry on client errors (4xx) except auth failures
      if (error.response?.status >= 400 && error.response?.status < 500) {
        if (error.response.status !== 401) {
          throw error;
        }
      }
      
      // Exponential backoff for server errors
      const delay = Math.min(2000 * Math.pow(2, attempt - 1), 10000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}
```#
## Frontend Integration

#### React Hook Example

```javascript
import { useState, useEffect } from 'react';

function useMBTIItinerary(mbtiPersonality) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (!mbtiPersonality) return;
    
    setLoading(true);
    setError(null);
    
    generateMBTIItinerary(mbtiPersonality)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [mbtiPersonality]);
  
  return { data, loading, error };
}

// Usage in component
function MBTIItineraryPlanner() {
  const [selectedMBTI, setSelectedMBTI] = useState('');
  const { data, loading, error } = useMBTIItinerary(selectedMBTI);
  
  if (loading) return <div>Generating your personalized 3-day itinerary...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!data) return (
    <div>
      <select onChange={(e) => setSelectedMBTI(e.target.value)}>
        <option value="">Select your MBTI type</option>
        <option value="INFJ">INFJ - The Advocate</option>
        <option value="ENFP">ENFP - The Campaigner</option>
        <option value="INTJ">INTJ - The Architect</option>
        <option value="ESTP">ESTP - The Entrepreneur</option>
        {/* ... other MBTI types */}
      </select>
    </div>
  );
  
  return (
    <div>
      <h1>Your {data.metadata.MBTI_personality} 3-Day Hong Kong Itinerary</h1>
      
      {Object.entries(data.main_itinerary).map(([day, dayData]) => (
        <div key={day}>
          <h2>{day.replace('_', ' ').toUpperCase()}</h2>
          
          <div className="sessions">
            <div className="morning">
              <h3>Morning</h3>
              <TouristSpotCard spot={dayData.morning_session} />
              <RestaurantCard restaurant={dayData.breakfast} mealType="Breakfast" />
            </div>
            
            <div className="afternoon">
              <h3>Afternoon</h3>
              <TouristSpotCard spot={dayData.afternoon_session} />
              <RestaurantCard restaurant={dayData.lunch} mealType="Lunch" />
            </div>
            
            <div className="night">
              <h3>Night</h3>
              <TouristSpotCard spot={dayData.night_session} />
              <RestaurantCard restaurant={dayData.dinner} mealType="Dinner" />
            </div>
          </div>
          
          {data.candidate_tourist_spots[day] && (
            <div className="alternatives">
              <h4>Alternative Spots</h4>
              {data.candidate_tourist_spots[day].map(spot => (
                <TouristSpotCard key={spot.id} spot={spot} isAlternative={true} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function TouristSpotCard({ spot, isAlternative = false }) {
  return (
    <div className={`spot-card ${isAlternative ? 'alternative' : ''}`}>
      <h4>{spot.name} {spot.MBTI_match && <span className="mbti-match">✨ Perfect Match</span>}</h4>
      <p>{spot.description}</p>
      <p><strong>Address:</strong> {spot.address}</p>
      <p><strong>Hours:</strong> {spot.operating_hours}</p>
      <p><strong>Days:</strong> {spot.operating_days}</p>
    </div>
  );
}

function RestaurantCard({ restaurant, mealType }) {
  if (!restaurant) return <div>Restaurant assignment failed</div>;
  
  return (
    <div className="restaurant-card">
      <h4>{mealType}: {restaurant.name}</h4>
      <p><strong>Address:</strong> {restaurant.address}</p>
      <p><strong>Sentiment:</strong> {restaurant.sentiment.likes} likes, {restaurant.sentiment.dislikes} dislikes</p>
    </div>
  );
}
```## Monit
oring and Observability

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
| `itinerary_generation_time_ms` | Histogram | Complete itinerary processing time |
| `nova_pro_query_time_ms` | Histogram | Knowledge base query response time |
| `mcp_call_duration_ms` | Histogram | MCP service call times |
| `request_count` | Counter | Total itinerary requests processed |
| `error_rate` | Gauge | Percentage of failed requests |
| `cache_hit_rate` | Gauge | Cache effectiveness for MBTI types |
| `jwt_validation_time_ms` | Histogram | Authentication processing time |
| `session_assignment_success_rate` | Gauge | Tourist spot assignment success |
| `restaurant_assignment_success_rate` | Gauge | Restaurant assignment success |

### Log Formats

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "correlation_id": "req_1705315800000",
  "message": "3-day itinerary generated successfully",
  "MBTI_personality": "INFJ",
  "processing_time_ms": 8500,
  "cache_hit": false,
  "nova_pro_queries": 3,
  "mcp_calls": ["search_restaurants_by_meal_type", "recommend_restaurants"],
  "user_id": "user123",
  "validation_status": "passed",
  "spots_assigned": 9,
  "restaurants_assigned": 9
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

#### 2. Slow Response Times (> 10 seconds)

**Symptoms**: Requests taking longer than expected

**Causes**:
- Nova Pro knowledge base latency
- MCP service latency
- Network connectivity issues
- Complex MBTI personality matching

**Solutions**:
- Check Nova Pro service health
- Verify MCP server status
- Monitor knowledge base query performance
- Consider caching for frequent MBTI types

#### 3. Knowledge Base Unavailable

**Symptoms**: "KNOWLEDGE_BASE_UNAVAILABLE" errors

**Causes**:
- Nova Pro service downtime
- OpenSearch knowledge base issues
- Network partitions
- Service overload

**Solutions**:
- Check Nova Pro service status
- Verify knowledge base connectivity
- Monitor OpenSearch cluster health
- Implement circuit breaker patterns

#### 4. Partial Itinerary Generation

**Symptoms**: Tourist spots assigned but restaurants missing

**Causes**:
- MCP server downtime
- Restaurant data unavailable
- District matching failures

**Solutions**:
- Check MCP server status
- Verify restaurant data completeness
- Review district matching logic
- Provide fallback restaurant options#### 5.
 Session Assignment Logic Failures

**Symptoms**: "SESSION_ASSIGNMENT_FAILED" errors, invalid itineraries

**Causes**:
- Insufficient tourist spots for MBTI type
- Operating hours conflicts
- District matching failures
- Uniqueness constraint violations

**Solutions**:
- Verify tourist spot data completeness
- Check operating hours validation logic
- Review district and area matching
- Ensure uniqueness constraints are properly implemented

### Debug Commands

```bash
# Test authentication
curl -X POST https://your-endpoint.amazonaws.com/invocations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"MBTI_personality": "INFJ"}' \
  -v

# Check service health
curl -X GET https://your-endpoint.amazonaws.com/health \
  -H "Accept: application/json" | jq '.components'

# Test with different MBTI types
for mbti in INFJ ENFP INTJ ESTP; do
  echo "Testing $mbti..."
  curl -X POST https://your-endpoint.amazonaws.com/invocations \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"MBTI_personality\": \"$mbti\"}" \
    -w "Response time: %{time_total}s\n" \
    -s -o /dev/null
done

# Test minimal payload
curl -X POST https://your-endpoint.amazonaws.com/invocations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"MBTI_personality": "INFJ"}' \
  -w "Response time: %{time_total}s\nHTTP status: %{http_code}\n"
```

## Security Considerations

### Data Protection

- All requests must use HTTPS
- JWT tokens are validated against AWS Cognito
- Sensitive data is not logged
- Request/response data is encrypted in transit
- MBTI personality data is not stored permanently

### Rate Limiting

- Per-user and per-IP rate limits
- Exponential backoff for retry logic
- Circuit breaker patterns for service protection
- Request queuing for burst traffic

### Input Validation

- MBTI personality format validation
- JWT token signature verification
- Request payload size limits
- SQL injection protection (not applicable - no direct DB access)
- XSS protection for user context data

## Support and Contact

For technical support or questions about the MBTI Travel Assistant API:

- **Documentation**: This document and inline code comments
- **Health Endpoint**: Monitor service status via `/health`
- **Error Codes**: Reference the error codes table for troubleshooting
- **Logs**: Check CloudWatch logs for detailed error information
- **Knowledge Base**: OpenSearch knowledge base ID: `RCWW86CLM9`

---

**API Version**: 1.0.0  
**Last Updated**: January 15, 2024  
**BedrockAgentCore Runtime**: Compatible with ARM64 architecture  
**Authentication**: AWS Cognito JWT tokens required  
**Foundation Model**: Amazon Nova Pro  
**Knowledge Base**: OpenSearch with MBTI-matched tourist spots  
**MCP Integration**: restaurant-search-mcp and restaurant-search-result-reasoning-mcp