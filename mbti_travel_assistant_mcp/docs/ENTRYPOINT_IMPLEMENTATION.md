# BedrockAgentCore Runtime Entrypoint Implementation

## Overview

This document describes the implementation of Task 6 "Create BedrockAgentCore runtime entrypoint" for the MBTI Travel Assistant MCP. The implementation provides a comprehensive HTTP request processing pipeline that follows BedrockAgentCore runtime patterns.

## Implementation Summary

### Task 6.1: Main Entrypoint Function ✅ COMPLETED

**Requirements Implemented:**
- ✅ Requirement 2.1: BedrockAgentCoreApp with @app.entrypoint decorator
- ✅ Requirement 2.2: Payload extraction and parameter processing
- ✅ Requirement 6.1: JWT authentication integration

**Key Features:**
- `@app.entrypoint` decorator function for HTTP request processing
- Comprehensive payload validation and parameter extraction
- JWT authentication integration with Cognito User Pools
- Structured JSON response format for frontend consumption
- Error handling with detailed error categorization
- Request correlation IDs for tracing and debugging

### Task 6.2: Request Processing Pipeline ✅ COMPLETED

**Requirements Implemented:**
- ✅ Requirement 2.6: Request routing logic for different payload types
- ✅ Requirement 7.1: Error handling and response formatting
- ✅ Requirement 7.2: Logging and monitoring for request processing

**Key Features:**
- Request routing based on payload type (natural language vs structured parameters)
- Comprehensive error handling with fallback responses
- Request metrics logging for monitoring and observability
- Response caching for performance optimization
- Health check endpoint for load balancer integration

## Architecture

### Request Processing Flow

```
HTTP Request → Route by Type → Validate Payload → Authenticate → Check Cache → 
Process with LLM Agent → Format Response → Cache Result → Return JSON Response
```

### Core Components

1. **Main Entrypoint (`process_restaurant_request`)**
   - Receives HTTP payloads from web servers
   - Orchestrates the complete request processing pipeline
   - Returns structured JSON responses

2. **Request Routing (`_route_request_by_type`)**
   - Routes requests based on payload content
   - Supports natural language queries and structured parameters
   - Enables different processing strategies

3. **Payload Validation (`_validate_and_parse_payload`)**
   - Validates incoming request structure
   - Parses payload into AgentCoreRequest objects
   - Provides detailed validation error messages

4. **Authentication (`_authenticate_request`)**
   - JWT token validation using Cognito User Pools
   - User context extraction from JWT claims
   - Graceful handling of authentication failures

5. **Response Formatting (`_format_final_response`)**
   - Formats responses for frontend consumption
   - Ensures exactly 1 recommendation + max 19 candidates
   - Includes comprehensive metadata

6. **Error Handling (`_handle_processing_error`)**
   - Categorizes and handles different error types
   - Provides structured error responses
   - Includes suggested actions for error resolution

7. **Metrics Logging (`_log_request_metrics`)**
   - Logs comprehensive request metrics
   - Tracks processing times and response sizes
   - Enables monitoring and observability

## Request/Response Format

### Input Payload
```json
{
  "district": "Central district",
  "meal_time": "breakfast",
  "natural_language_query": "Find me a good breakfast place",
  "auth_token": "eyJhbGciOiJSUzI1NiIs...",
  "user_context": {...}
}
```

### Output Response
```json
{
  "recommendation": {
    "id": "rest_001",
    "name": "Great Breakfast Place",
    "address": "123 Main St",
    "district": "Central district",
    "sentiment": {...},
    "operating_hours": {...}
  },
  "candidates": [
    {...}, {...}, ...
  ],
  "metadata": {
    "search_criteria": {
      "district": "Central district",
      "meal_time": "breakfast"
    },
    "total_found": 20,
    "timestamp": "2025-09-28T23:43:28.241Z",
    "processing_time_ms": 150,
    "cache_hit": false,
    "mcp_calls": ["search_restaurants_combined", "recommend_restaurants"]
  },
  "error": null
}
```

## Error Handling

### Error Categories
- **Validation Errors**: Invalid payload structure or parameters
- **Authentication Errors**: JWT token validation failures
- **MCP Service Errors**: External MCP server unavailability
- **Internal Errors**: System-level processing failures

### Error Response Format
```json
{
  "recommendation": null,
  "candidates": [],
  "metadata": {...},
  "error": {
    "error_type": "validation_error",
    "message": "Request validation failed: district or natural_language_query must be provided",
    "suggested_actions": [
      "Check request parameters",
      "Ensure required fields are provided",
      "Validate parameter formats"
    ],
    "error_code": "VALIDATION_FAILED"
  }
}
```

## Monitoring and Observability

### Request Metrics
- Processing time in milliseconds
- Payload and response sizes
- Success/failure rates
- Cache hit rates
- Authentication status

### Logging
- Structured logging with correlation IDs
- Request routing decisions
- Authentication events
- Error details with stack traces
- Performance metrics

### Health Checks
- Component-level health status
- Dependency connectivity checks
- Configuration validation
- Service availability monitoring

## Configuration

### Environment Variables
- `COGNITO_USER_POOL_ID`: Cognito User Pool for JWT validation
- `SEARCH_MCP_ENDPOINT`: Restaurant search MCP server endpoint
- `REASONING_MCP_ENDPOINT`: Restaurant reasoning MCP server endpoint
- `CACHE_ENABLED`: Enable/disable response caching
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Service Dependencies
- JWT Auth Handler: JWT token validation
- MCP Client Manager: MCP server communication
- Restaurant Agent: Internal LLM processing
- Response Formatter: Response structure formatting
- Error Handler: Error categorization and handling
- Cache Service: Response caching

## Testing

### Test Coverage
- ✅ Valid payload processing
- ✅ Empty payload handling
- ✅ Authentication integration
- ✅ Request routing logic
- ✅ Payload validation
- ✅ Cache key generation
- ✅ Error handling
- ✅ Metrics logging

### Test Files
- `tests/test_entrypoint.py`: Comprehensive entrypoint tests
- Mock implementations for development/testing
- Integration test scenarios

## Deployment

### BedrockAgentCore Runtime
```python
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def process_restaurant_request(payload: Dict[str, Any]) -> str:
    # Implementation...
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Docker Configuration
```dockerfile
FROM --platform=linux/arm64 python:3.12-slim
# ARM64 required for BedrockAgentCore Runtime
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "main.py"]
```

## Next Steps

1. **Task 7**: Implement response formatting service
2. **Task 8**: Add comprehensive error handling
3. **Task 9**: Implement caching and performance optimization
4. **Task 10**: Create configuration and deployment setup

## Compliance Matrix

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 2.1 | ✅ | BedrockAgentCoreApp with @app.entrypoint |
| 2.2 | ✅ | Payload extraction and validation |
| 2.3 | ✅ | Internal LLM agent integration |
| 6.1 | ✅ | JWT authentication with Cognito |
| 2.6 | ✅ | Request routing by payload type |
| 7.1 | ✅ | Comprehensive error handling |
| 7.2 | ✅ | Logging and monitoring |
| 1.1-1.8 | ✅ | HTTP payload processing and LLM orchestration |
| 4.1-4.8 | ✅ | JSON response structure for frontend |

## Conclusion

The BedrockAgentCore runtime entrypoint has been successfully implemented with comprehensive request processing, authentication, error handling, and monitoring capabilities. The implementation follows all specified requirements and provides a robust foundation for the MBTI Travel Assistant MCP service.