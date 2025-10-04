# Design Document

## Overview

This design document outlines the architecture for updating the mbti-travel-planner-agent to connect directly to the agentcore-gateway-mcp-tools through HTTP endpoints instead of using MCP client connections. The updated agent will use the Amazon Nova Pro foundation model (amazon.nova-pro-v1:0) and communicate with the deployed gateway service to search for restaurants in the "Central" district and receive intelligent recommendations.

The design simplifies the current architecture by removing the complex MCP client authentication layer and replacing it with straightforward HTTP API calls to the gateway service that has already been deployed to Bedrock AgentCore.

## Architecture

### Current Architecture (To Be Replaced)
```
mbti-travel-planner-agent
├── MCP Client Manager
│   ├── Cognito Authentication
│   ├── JWT Token Management
│   └── Direct MCP Server Connections
├── restaurant-search-mcp (Direct Connection)
└── restaurant-search-result-reasoning-mcp (Direct Connection)
```

### New Architecture (Target)
```
mbti-travel-planner-agent
├── HTTP Client Service
│   ├── Environment-based Configuration
│   ├── Request/Response Handling
│   └── Error Management
└── agentcore-gateway-mcp-tools (HTTP API)
    ├── /api/v1/restaurants/search/district
    ├── /api/v1/restaurants/search/combined
    └── /api/v1/restaurants/recommend
```

### Integration Flow
1. **User Request** → mbti-travel-planner-agent
2. **Agent Processing** → Nova Pro model processes request
3. **Tool Invocation** → HTTP calls to gateway endpoints
4. **Gateway Processing** → agentcore-gateway-mcp-tools handles MCP communication
5. **Response Processing** → Agent formats and returns results

## Components and Interfaces

### 1. HTTP Client Service

**Purpose**: Replace the MCP client manager with a simpler HTTP client for gateway communication.

**Key Components**:
- `GatewayHTTPClient`: Main HTTP client class
- `GatewayEndpoints`: Endpoint configuration management
- `ResponseProcessor`: Process and validate gateway responses

**Interface**:
```python
class GatewayHTTPClient:
    def __init__(self, base_url: str, timeout: int = 30)
    async def search_restaurants_by_district(self, districts: List[str]) -> Dict[str, Any]
    async def search_restaurants_combined(self, districts: List[str] = None, meal_types: List[str] = None) -> Dict[str, Any]
    async def recommend_restaurants(self, restaurants: List[Dict], ranking_method: str = "sentiment_likes") -> Dict[str, Any]
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]
    def _handle_error(self, error: Exception) -> Dict[str, Any]
```

### 2. Environment Configuration

**Purpose**: Manage different gateway endpoints for development, staging, and production environments.

**Configuration Structure**:
```python
GATEWAY_ENDPOINTS = {
    "development": "http://localhost:8080",
    "staging": "https://agentcore_gateway_mcp_tools-staging.bedrock-agentcore.us-east-1.amazonaws.com",
    "production": "https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com"
}
```

### 3. Tool Functions

**Purpose**: Provide Strands Agent tools that interface with the gateway HTTP endpoints.

**Tool Implementations**:
- `search_restaurants_by_district_tool`: Calls `/api/v1/restaurants/search/district`
- `search_restaurants_combined_tool`: Calls `/api/v1/restaurants/search/combined`
- `recommend_restaurants_tool`: Calls `/api/v1/restaurants/recommend`

### 4. Nova Pro Model Integration

**Purpose**: Configure the agent to use Amazon Nova Pro foundation model with appropriate parameters.

**Model Configuration**:
```python
agent = Agent(
    model="amazon.nova-pro-v1:0",
    tools=gateway_tools,
    temperature=0.1,
    max_tokens=2048,
    timeout=60  # Nova Pro supports up to 60 minutes
)
```

### 5. Response Processing

**Purpose**: Transform gateway API responses into user-friendly formats for the agent.

**Processing Pipeline**:
1. **Validation**: Ensure response structure matches expected format
2. **Transformation**: Convert API response to agent-friendly format
3. **Error Handling**: Process error responses and provide fallbacks
4. **Formatting**: Format data for presentation to users

## Data Models

### Gateway Request Models

Based on the agentcore-gateway-mcp-tools API specification:

```python
# District Search Request
{
    "districts": ["Central district"]
}

# Combined Search Request
{
    "districts": ["Central district"],
    "meal_types": ["lunch", "dinner"]
}

# Recommendation Request
{
    "restaurants": [
        {
            "id": "rest_001",
            "name": "Restaurant Name",
            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
            "address": "123 Main St",
            "district": "Central district"
        }
    ],
    "ranking_method": "sentiment_likes"
}
```

### Gateway Response Models

```python
# Search Response
{
    "success": true,
    "restaurants": [
        {
            "id": "rest_001",
            "name": "Restaurant Name",
            "address": "123 Main St, Central",
            "meal_type": ["lunch", "dinner"],
            "sentiment": {
                "likes": 85,
                "dislikes": 10,
                "neutral": 5,
                "total_responses": 100,
                "likes_percentage": 85.0,
                "combined_positive_percentage": 90.0
            },
            "district": "Central district",
            "price_range": "$"
        }
    ],
    "metadata": {
        "total_results": 1,
        "search_criteria": {"districts": ["Central district"]},
        "execution_time_ms": 150.5
    }
}

# Recommendation Response
{
    "success": true,
    "recommendation": { /* restaurant object */ },
    "candidates": [ /* array of restaurant objects */ ],
    "ranking_method": "sentiment_likes",
    "analysis_summary": {
        "restaurant_count": 10,
        "average_likes": 75.5,
        "top_sentiment_score": 95.0
    }
}
```

## Error Handling

### Error Categories

1. **Network Errors**: Connection timeouts, DNS resolution failures
2. **HTTP Errors**: 4xx and 5xx status codes from gateway
3. **Validation Errors**: Invalid request parameters or malformed responses
4. **Service Errors**: Gateway service unavailable or MCP server issues

### Error Handling Strategy

```python
class GatewayError(Exception):
    """Base exception for gateway communication errors."""
    pass

class GatewayConnectionError(GatewayError):
    """Network connection errors."""
    pass

class GatewayServiceError(GatewayError):
    """Gateway service errors (4xx, 5xx)."""
    pass

class GatewayValidationError(GatewayError):
    """Request/response validation errors."""
    pass

# Error handling in tools
def handle_gateway_error(error: Exception) -> Dict[str, Any]:
    """Convert gateway errors to user-friendly responses."""
    if isinstance(error, GatewayConnectionError):
        return {
            "success": False,
            "error": "Restaurant search service is temporarily unavailable. Please try again later.",
            "fallback": "I can still help with general travel planning questions."
        }
    elif isinstance(error, GatewayServiceError):
        return {
            "success": False,
            "error": f"Restaurant search encountered an issue: {str(error)}",
            "fallback": "Let me know if you'd like help with other travel planning topics."
        }
    else:
        return {
            "success": False,
            "error": "An unexpected error occurred while searching for restaurants.",
            "fallback": "Please try rephrasing your request or ask about other travel topics."
        }
```

## Testing Strategy

### Unit Tests

1. **HTTP Client Tests**:
   - Test successful API calls with mock responses
   - Test error handling for various HTTP status codes
   - Test timeout and connection error scenarios
   - Test response validation and transformation

2. **Tool Function Tests**:
   - Test tool invocation with valid parameters
   - Test tool error handling and fallback responses
   - Test response formatting for user presentation

3. **Configuration Tests**:
   - Test environment-based endpoint selection
   - Test configuration validation and defaults

### Integration Tests

1. **Gateway Integration Tests**:
   - Test actual HTTP calls to deployed gateway (in test environment)
   - Test end-to-end workflow: search → recommend → format
   - Test authentication handling (if required)

2. **Agent Integration Tests**:
   - Test complete agent workflow with Nova Pro model
   - Test tool invocation through agent framework
   - Test user interaction scenarios

### Performance Tests

1. **Response Time Tests**:
   - Measure HTTP request/response times
   - Test concurrent request handling
   - Monitor memory usage during operations

2. **Reliability Tests**:
   - Test retry mechanisms for failed requests
   - Test graceful degradation when gateway is unavailable
   - Test timeout handling for long-running requests

## Deployment Considerations

### Environment Configuration

The agent will support multiple environments with different gateway endpoints:

- **Development**: Local gateway instance or development deployment
- **Staging**: Staging gateway deployment for testing
- **Production**: Production gateway deployment (agentcore_gateway_mcp_tools-UspJsMG7Fi)

### Configuration Management

Environment-specific settings will be managed through:
1. Environment variables
2. Configuration files
3. Default fallbacks

### Monitoring and Observability

1. **Logging**:
   - HTTP request/response logging
   - Error logging with appropriate severity levels
   - Performance metrics logging

2. **Metrics**:
   - Request success/failure rates
   - Response time distributions
   - Error categorization and counts

3. **Health Checks**:
   - Gateway endpoint availability checks
   - Agent tool functionality validation

## Security Considerations

### Authentication

The gateway may require authentication in production environments:
- Support for bearer token authentication
- Automatic token refresh mechanisms
- Secure credential storage

### Data Privacy

- No sensitive user data stored in logs
- Secure transmission of restaurant search queries
- Proper error message sanitization

### Network Security

- HTTPS-only communication with gateway
- Proper certificate validation
- Request timeout limits to prevent resource exhaustion

## Migration Strategy

### Phase 1: Parallel Implementation
- Implement new HTTP client alongside existing MCP client
- Add feature flag to switch between implementations
- Test new implementation in development environment

### Phase 2: Gradual Rollout
- Deploy to staging environment with new implementation
- Conduct thorough testing and performance validation
- Monitor error rates and response times

### Phase 3: Production Migration
- Deploy to production with feature flag enabled
- Monitor system health and user experience
- Remove old MCP client code after successful validation

### Rollback Plan
- Maintain ability to switch back to MCP client implementation
- Keep old code until new implementation is fully validated
- Have monitoring alerts for increased error rates

## Performance Optimization

### HTTP Client Optimization
- Connection pooling for multiple requests
- Request/response compression
- Appropriate timeout configurations

### Caching Strategy
- Cache restaurant search results for repeated queries
- Implement cache invalidation policies
- Use in-memory caching for session-based requests

### Resource Management
- Proper connection cleanup
- Memory usage monitoring
- Graceful handling of resource exhaustion

## Future Enhancements

### Additional Gateway Features
- Support for additional search filters
- Real-time restaurant availability checking
- User preference-based recommendations

### Agent Capabilities
- Multi-district search optimization
- Personalized recommendation algorithms
- Integration with other travel planning services

### Monitoring and Analytics
- User interaction analytics
- Restaurant search pattern analysis
- Performance optimization based on usage patterns