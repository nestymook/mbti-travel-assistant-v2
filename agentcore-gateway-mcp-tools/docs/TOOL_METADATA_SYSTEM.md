# Tool Metadata System

The Tool Metadata System provides comprehensive metadata for all available MCP tools in the AgentCore Gateway, specifically designed to help foundation models understand when and how to use each tool effectively.

## Overview

The system consists of:
- **Tool Metadata Models**: Pydantic models defining metadata structure
- **Tool Metadata Service**: Service for generating and managing metadata
- **Tool Metadata API Endpoints**: REST API for accessing metadata
- **MBTI Integration Guidance**: Personality-specific tool usage guidance

## Features

### Comprehensive Tool Information
- Tool descriptions, purposes, and use cases
- Parameter schemas with validation rules
- Response format documentation
- Performance metrics and reliability data

### Foundation Model Integration
- Detailed parameter descriptions and constraints
- Example requests and responses
- Use case scenarios for different contexts
- Error handling guidance

### MBTI Personality Integration
- Personality-specific tool usage patterns
- Preference-based recommendation guidance
- Search pattern optimization for different types

## API Endpoints

### Get All Tools Metadata
```http
GET /tools/metadata
```

Returns comprehensive metadata for all available tools.

**Response:**
```json
{
  "tools": [...],
  "total_tools": 5,
  "categories": ["search", "analysis", "recommendation"],
  "supported_mbti_types": ["ENFP", "INTJ", ...],
  "version": "1.0.0",
  "last_updated": "2025-01-03T10:30:00Z"
}
```

### Get Specific Tool Metadata
```http
GET /tools/metadata/{tool_name}
```

Returns detailed metadata for a specific tool.

**Available Tools:**
- `search_restaurants_by_district`
- `search_restaurants_by_meal_type`
- `search_restaurants_combined`
- `recommend_restaurants`
- `analyze_restaurant_sentiment`

### Get Tools by Category
```http
GET /tools/metadata/categories/{category}
```

Returns metadata for all tools in a specific category.

**Available Categories:**
- `search`: Restaurant search tools
- `analysis`: Sentiment analysis tools
- `recommendation`: Restaurant recommendation tools

### Get Tools for MBTI Type
```http
GET /tools/metadata/mbti/{personality_type}
```

Returns tool metadata with MBTI-specific guidance.

**Supported MBTI Types:**
All 16 types: ENFJ, ENFP, ENTJ, ENTP, ESFJ, ESFP, ESTJ, ESTP, INFJ, INFP, INTJ, INTP, ISFJ, ISFP, ISTJ, ISTP

### Health Check
```http
GET /tools/health
```

Returns health status of the metadata service (no authentication required).

## Tool Metadata Structure

Each tool includes:

### Basic Information
- `name`: Tool identifier
- `display_name`: Human-readable name
- `category`: Tool category (search/analysis/recommendation)
- `description`: Detailed description
- `purpose`: Primary purpose

### Technical Details
- `endpoint`: API endpoint path
- `http_method`: HTTP method (POST/GET)
- `authentication_required`: Whether auth is needed
- `rate_limit`: Rate limiting information
- `average_response_time_ms`: Performance metrics
- `success_rate_percentage`: Reliability metrics

### Parameter Information
- `parameters`: Parameter schemas with validation rules
- `response_schema`: Response format documentation

### Usage Guidance
- `use_cases`: Scenario-based usage examples
- `mbti_integration`: Personality-specific guidance
- `examples`: Complete request/response examples

## MBTI Integration

Each tool provides guidance for different MBTI personality types:

### ENFP (The Campaigner)
- Prefers variety and exploration
- Uses multiple search criteria
- Values social atmosphere and unique experiences

### INTJ (The Architect)
- Focuses on efficiency and strategic planning
- Uses precise search criteria
- Values quality over quantity

### ESFJ (The Consul)
- Prioritizes family-friendly options
- Seeks community-oriented restaurants
- Values social validation and group satisfaction

### And 13 more personality types...

## Usage Examples

### Foundation Model Integration

```python
# Get all tools metadata for AI model
response = requests.get("/tools/metadata", headers=auth_headers)
metadata = response.json()

# Use metadata to understand tool capabilities
for tool in metadata["tools"]:
    print(f"Tool: {tool['name']}")
    print(f"Purpose: {tool['purpose']}")
    print(f"Parameters: {list(tool['parameters'].keys())}")
```

### MBTI-Specific Recommendations

```python
# Get tools optimized for ENFP personality
response = requests.get("/tools/metadata/mbti/ENFP", headers=auth_headers)
enfp_tools = response.json()

# Each tool now includes ENFP-specific guidance
for tool in enfp_tools["tools"]:
    for guidance in tool["mbti_integration"]:
        if guidance["personality_type"] == "ENFP":
            print(f"ENFP preferences: {guidance['preferences']}")
            print(f"Search patterns: {guidance['search_patterns']}")
```

### Category-Based Tool Selection

```python
# Get only search tools
response = requests.get("/tools/metadata/categories/search", headers=auth_headers)
search_tools = response.json()

# Use search tools for restaurant discovery
for tool in search_tools["tools"]:
    print(f"Search tool: {tool['name']}")
    print(f"Endpoint: {tool['endpoint']}")
```

## Service Usage

### Direct Service Access

```python
from services.tool_metadata_service import tool_metadata_service

# Get all metadata
metadata = tool_metadata_service.get_all_tools_metadata()

# Get specific tool
tool = tool_metadata_service.get_tool_metadata("search_restaurants_by_district")

# Access tool information
print(f"Tool: {tool.name}")
print(f"Parameters: {list(tool.parameters.keys())}")
print(f"Use cases: {len(tool.use_cases)}")
```

### Caching

The service automatically caches metadata for 1 hour to improve performance:

```python
# First call generates metadata
metadata1 = tool_metadata_service.get_all_tools_metadata()

# Second call uses cache (same object)
metadata2 = tool_metadata_service.get_all_tools_metadata()
assert metadata1 is metadata2
```

## Authentication

All metadata endpoints require JWT authentication except for the health check:

```python
headers = {
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json"
}

response = requests.get("/tools/metadata", headers=headers)
```

## Error Handling

The API provides detailed error responses:

### Tool Not Found (404)
```json
{
  "detail": {
    "error": "Tool not found",
    "message": "Tool 'invalid_tool' does not exist",
    "type": "ToolNotFoundError",
    "available_tools": [...]
  }
}
```

### Category Not Found (404)
```json
{
  "detail": {
    "error": "Category not found",
    "message": "No tools found for category 'invalid_category'",
    "type": "CategoryNotFoundError",
    "available_categories": ["search", "analysis", "recommendation"]
  }
}
```

### MBTI Type Not Supported (404)
```json
{
  "detail": {
    "error": "MBTI type not supported",
    "message": "MBTI personality type 'INVALID' is not supported",
    "type": "MBTITypeNotFoundError",
    "supported_types": ["ENFP", "INTJ", ...]
  }
}
```

### Service Error (500)
```json
{
  "detail": {
    "error": "Failed to generate tools metadata",
    "message": "An internal error occurred while generating tool metadata",
    "type": "MetadataGenerationError"
  }
}
```

## Testing

### Unit Tests
```bash
# Test the service
python -m pytest tests/test_tool_metadata_service.py -v

# Test the API endpoints
python -m pytest tests/test_tool_metadata_endpoints.py -v
```

### Integration Tests
```bash
# Run comprehensive integration tests
python test_tool_metadata_integration.py
```

## Performance

- **Metadata Generation**: ~100ms for all tools
- **API Response Time**: ~50-100ms (cached)
- **Memory Usage**: ~2MB for complete metadata
- **Cache Duration**: 1 hour
- **JSON Size**: ~37KB for all tools

## Best Practices

### For Foundation Models
1. Use the complete metadata to understand tool capabilities
2. Reference use cases to determine appropriate tool selection
3. Follow parameter validation rules strictly
4. Use MBTI guidance for personalized recommendations

### For API Consumers
1. Cache metadata responses when possible
2. Use category-specific endpoints to reduce payload size
3. Handle all error types gracefully
4. Monitor the health endpoint for service availability

### For Developers
1. Update metadata when adding new tools
2. Include comprehensive examples and use cases
3. Test metadata accuracy with integration tests
4. Follow the established metadata structure

## Future Enhancements

- **Dynamic Tool Discovery**: Automatically detect new MCP tools
- **Usage Analytics**: Track which tools are most commonly used
- **A/B Testing**: Support for different metadata versions
- **Localization**: Multi-language metadata support
- **Tool Versioning**: Support for multiple tool versions