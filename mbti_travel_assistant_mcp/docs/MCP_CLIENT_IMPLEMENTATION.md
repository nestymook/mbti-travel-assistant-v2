# MCP Client Manager Implementation

## Overview

This document describes the implementation of the MCP Client Manager for the MBTI Travel Assistant. The MCP Client Manager provides connection management and orchestration for communicating with existing restaurant MCP servers.

## Architecture

The MCP Client Manager follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Internal LLM Agent                      │
│                  (Strands Framework)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                MCP Client Manager                          │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Connection Pool │    │    Retry Logic & Error         │ │
│  │ & Semaphores    │    │    Handling                     │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Response Parser │    │    Statistics & Monitoring      │ │
│  │ & Formatter     │    │                                 │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────┬───────────────┬───────────────────────┘
                      │               │
┌─────────────────────▼───────────────▼───────────────────────┐
│                    MCP Protocol                            │
└─────────────────────┬───────────────┬───────────────────────┘
                      │               │
┌─────────────────────▼─────────┐   ┌─▼─────────────────────────┐
│  Restaurant Search MCP        │   │  Restaurant Reasoning MCP │
│  - search_restaurants_combined│   │  - recommend_restaurants  │
└───────────────────────────────┘   └───────────────────────────┘
```

## Key Components

### 1. MCPClientManager Class

The main class that orchestrates MCP client connections and tool calls.

**Key Features:**
- Connection pooling with semaphores for concurrent request management
- Retry logic with exponential backoff for failed connections
- Comprehensive error handling and logging
- Statistics tracking for monitoring and observability
- Health check functionality for MCP server status

**Configuration:**
- Configurable endpoints for search and reasoning MCP servers
- Adjustable timeout and retry parameters
- Connection pool size management

### 2. Connection Management

**Connection Pooling:**
- Uses asyncio semaphores to limit concurrent connections
- Separate pools for search and reasoning MCP servers
- Configurable pool sizes based on server capacity

**Retry Logic:**
- Exponential backoff with configurable maximum delay
- Separate retry attempts for different types of failures
- Comprehensive error categorization and handling

### 3. MCP Tool Integration

**Search MCP Server Integration:**
- Calls `search_restaurants_combined` tool
- Supports district and meal_type parameters
- Parses restaurant data into structured objects

**Reasoning MCP Server Integration:**
- Calls `recommend_restaurants` tool
- Converts Restaurant objects to MCP-compatible format
- Supports different ranking methods (sentiment_likes, combined_sentiment)

### 4. Error Handling

**Error Categories:**
- `MCPConnectionError`: Connection-related failures
- `MCPToolCallError`: MCP tool execution failures
- Comprehensive error context and logging

**Resilience Features:**
- Circuit breaker pattern for server unavailability
- Graceful degradation with fallback responses
- Detailed error messages for debugging

## Implementation Details

### Core Methods

#### `search_restaurants(district, meal_type)`
```python
async def search_restaurants(
    self,
    district: Optional[str] = None,
    meal_type: Optional[str] = None
) -> List[Restaurant]:
```

**Purpose:** Search for restaurants using the search MCP server
**MCP Tool:** `search_restaurants_combined`
**Parameters:** 
- `districts`: List containing the district name
- `meal_types`: List containing the meal type

#### `analyze_restaurants(restaurants, ranking_method)`
```python
async def analyze_restaurants(
    self,
    restaurants: List[Restaurant],
    ranking_method: str = "sentiment_likes"
) -> Dict[str, Any]:
```

**Purpose:** Analyze restaurants for recommendations using the reasoning MCP server
**MCP Tool:** `recommend_restaurants`
**Parameters:**
- `restaurants`: List of restaurant dictionaries
- `ranking_method`: Ranking algorithm to use

### Configuration Integration

The MCP Client Manager integrates with the application settings:

```python
# Search MCP server configuration
search_mcp_endpoint: str = Field(env="SEARCH_MCP_ENDPOINT")
reasoning_mcp_endpoint: str = Field(env="REASONING_MCP_ENDPOINT")
mcp_connection_timeout: int = Field(default=30, env="MCP_CONNECTION_TIMEOUT")
mcp_retry_attempts: int = Field(default=3, env="MCP_RETRY_ATTEMPTS")
```

### Data Model Integration

**Restaurant Object Conversion:**
- Converts between internal Restaurant objects and MCP-compatible dictionaries
- Handles sentiment data structure transformation
- Preserves all restaurant metadata and attributes

**Response Parsing:**
- Parses JSON responses from MCP tools
- Validates response structure and handles errors
- Extracts recommendation and candidate data

## Testing Strategy

### Unit Tests (`test_mcp_client_manager.py`)

**Test Coverage:**
- Connection management and retry logic
- MCP tool call success and failure scenarios
- Data model conversion and validation
- Error handling and exception propagation
- Statistics tracking and health checks

**Mocking Strategy:**
- Mock MCP sessions and tool responses
- Test retry logic with controlled failures
- Validate parameter formatting and response parsing

### Integration Tests (`test_mcp_integration.py`)

**Test Scenarios:**
- End-to-end workflow with actual MCP servers
- Health check validation
- Connection statistics tracking
- Error handling with real MCP failures

**Test Markers:**
- `@pytest.mark.integration` for integration tests
- Conditional skipping when MCP servers unavailable

## Usage Examples

### Basic Usage

```python
from services.mcp_client_manager import MCPClientManager

# Initialize manager
mcp_manager = MCPClientManager()

# Search for restaurants
restaurants = await mcp_manager.search_restaurants(
    district="Central district",
    meal_type="breakfast"
)

# Analyze for recommendations
result = await mcp_manager.analyze_restaurants(
    restaurants=restaurants,
    ranking_method="sentiment_likes"
)

# Get recommendation and candidates
recommendation = result["recommendation"]
candidates = result["candidates"]
```

### Health Monitoring

```python
# Check MCP server health
health_status = await mcp_manager.health_check()

# Get connection statistics
stats = mcp_manager.get_connection_stats()
success_rate = stats["search_mcp"]["success_rate"]
```

## Monitoring and Observability

### Statistics Tracking

**Connection Statistics:**
- Total calls, successful calls, failed calls
- Success rate calculation
- Average response time tracking
- Last successful/failed call timestamps

**Health Monitoring:**
- MCP server availability status
- Tool availability verification
- Error rate monitoring

### Logging Integration

**Log Levels:**
- DEBUG: Detailed connection and operation logs
- INFO: Successful operations and statistics
- WARNING: Retry attempts and recoverable errors
- ERROR: Connection failures and tool errors

**Structured Logging:**
- Operation context and timing
- Error details and stack traces
- Performance metrics and statistics

## Security Considerations

### Authentication
- MCP servers handle their own authentication
- Client manager passes through authentication headers
- Secure credential management through settings

### Data Protection
- No sensitive data logged in error messages
- Secure handling of restaurant data
- Input validation and sanitization

## Performance Optimization

### Connection Pooling
- Configurable connection pool sizes
- Semaphore-based concurrency control
- Connection reuse and management

### Caching Strategy
- Response caching at higher application layers
- Statistics caching for monitoring
- Connection state management

### Async Operations
- Full async/await support
- Concurrent MCP tool calls when possible
- Non-blocking connection management

## Deployment Considerations

### Configuration
- Environment-based endpoint configuration
- Adjustable timeout and retry parameters
- Monitoring and logging configuration

### Dependencies
- MCP client library (mcp>=1.9.0)
- HTTP client (httpx>=0.25.0)
- Async support libraries

### Container Support
- ARM64 architecture compatibility
- Environment variable configuration
- Health check endpoint integration

## Future Enhancements

### Planned Features
- Circuit breaker pattern implementation
- Advanced caching strategies
- Load balancing across multiple MCP servers
- Metrics export for external monitoring

### Scalability Improvements
- Connection pool optimization
- Batch processing capabilities
- Parallel MCP tool execution
- Resource usage optimization

## Troubleshooting

### Common Issues

**Connection Errors:**
- Verify MCP server endpoints are accessible
- Check network connectivity and firewall rules
- Validate authentication configuration

**Tool Call Failures:**
- Verify MCP tool names and parameters
- Check MCP server logs for detailed errors
- Validate input data format and structure

**Performance Issues:**
- Monitor connection pool utilization
- Check retry attempt configuration
- Analyze response time statistics

### Debug Information

**Connection Statistics:**
```python
stats = mcp_manager.get_connection_stats()
print(f"Success rate: {stats['search_mcp']['success_rate']:.2%}")
print(f"Average response time: {stats['search_mcp']['average_response_time']:.2f}s")
```

**Health Check:**
```python
health = await mcp_manager.health_check()
print(f"Search MCP: {health['search_mcp']['status']}")
print(f"Reasoning MCP: {health['reasoning_mcp']['status']}")
```

## Conclusion

The MCP Client Manager provides a robust, scalable foundation for communicating with restaurant MCP servers. It implements best practices for connection management, error handling, and observability while maintaining high performance and reliability.

The implementation satisfies all requirements from the specification:
- ✅ Connection pooling and retry logic (Requirement 3.1, 3.4, 7.7)
- ✅ Restaurant search MCP client calls (Requirement 3.2, 3.3)
- ✅ Restaurant reasoning MCP client calls (Requirement 3.5, 3.6)
- ✅ Comprehensive error handling and monitoring
- ✅ Integration with application configuration and data models