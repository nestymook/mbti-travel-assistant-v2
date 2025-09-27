# Kiro MCP Integration Testing Guide

## 🎯 Overview

Kiro IDE has built-in MCP (Model Context Protocol) integration that allows you to directly test MCP tools. This is the **recommended and most accurate** way to test your restaurant search MCP functionality.

## 🔧 Prerequisites

### 1. MCP Server Configuration
Ensure your MCP server is configured in Kiro's settings:

**File**: `.kiro/settings/mcp.json`
```json
{
  "mcpServers": {
    "restaurant-search-mcp": {
      "command": "python",
      "args": ["./restaurant_mcp_server.py"],
      "cwd": ".",
      "env": {
        "REQUIRE_AUTHENTICATION": "false",
        "PYTHONPATH": "."
      },
      "disabled": false,
      "autoApprove": [
        "search_restaurants_by_district",
        "search_restaurants_by_meal_type", 
        "search_restaurants_combined"
      ],
      "disabledTools": []
    }
  }
}
```

### 2. MCP Server Status
Check that your MCP server is running and connected:
- Look for the MCP server status in Kiro's MCP panel
- Ensure no connection errors in the MCP logs

## 🧪 Testing Methods

### Method 1: Direct Tool Invocation (Recommended)

You can directly invoke MCP tools in Kiro using the function call syntax:

#### Test District Search
```python
# Search for restaurants in Central district
search_restaurants_by_district(["Central district"])
```

#### Test Meal Type Search  
```python
# Search for breakfast restaurants
search_restaurants_by_meal_type(["breakfast"])
```

#### Test Combined Search
```python
# Search for dinner restaurants in Central district
search_restaurants_combined(
    districts=["Central district"], 
    meal_types=["dinner"]
)
```

### Method 2: Chat Integration Testing

Use Kiro's chat interface to test MCP tools through natural language:

#### Example Queries
```
Find restaurants in Central district
Show me breakfast places in Tsim Sha Tsui
I want dinner in Causeway Bay
What restaurants are open for lunch?
```

## 📋 Comprehensive Test Suite

### 1. District Search Tests

#### Test Valid Districts
```python
# Test major Hong Kong districts
search_restaurants_by_district(["Central district"])
search_restaurants_by_district(["Tsim Sha Tsui"])
search_restaurants_by_district(["Causeway Bay"])
search_restaurants_by_district(["Admiralty"])

# Test multiple districts
search_restaurants_by_district(["Central district", "Admiralty"])
```

#### Test Invalid Districts
```python
# Test non-existent district (should return empty results)
search_restaurants_by_district(["NonExistent District"])

# Test empty list (should return validation error)
search_restaurants_by_district([])
```

### 2. Meal Type Search Tests

#### Test Valid Meal Types
```python
# Test individual meal types
search_restaurants_by_meal_type(["breakfast"])
search_restaurants_by_meal_type(["lunch"])
search_restaurants_by_meal_type(["dinner"])

# Test multiple meal types
search_restaurants_by_meal_type(["breakfast", "lunch"])
search_restaurants_by_meal_type(["lunch", "dinner"])
```

#### Test Invalid Meal Types
```python
# Test invalid meal type (should return validation error)
search_restaurants_by_meal_type(["brunch"])

# Test empty list (should return validation error)
search_restaurants_by_meal_type([])
```

### 3. Combined Search Tests

#### Test Valid Combinations
```python
# Test district + meal type
search_restaurants_combined(
    districts=["Central district"], 
    meal_types=["breakfast"]
)

# Test multiple districts + multiple meal types
search_restaurants_combined(
    districts=["Central district", "Tsim Sha Tsui"], 
    meal_types=["lunch", "dinner"]
)

# Test district only
search_restaurants_combined(districts=["Causeway Bay"])

# Test meal type only
search_restaurants_combined(meal_types=["dinner"])
```

#### Test Invalid Combinations
```python
# Test with no parameters (should return validation error)
search_restaurants_combined()

# Test with empty lists
search_restaurants_combined(districts=[], meal_types=[])
```

## 📊 Expected Results

### Successful Response Format
```json
{
  "success": true,
  "data": {
    "restaurants": [
      {
        "id": "rest_001",
        "name": "Restaurant Name",
        "address": "123 Main St, Central",
        "district": "Central district",
        "meal_type": "lunch",
        "sentiment": {
          "likes": 85,
          "dislikes": 10,
          "neutral": 5
        },
        "location_category": "business_district",
        "price_range": "$$",
        "operating_hours": {
          "mon_fri": "11:00-22:00",
          "sat_sun": "10:00-23:00",
          "public_holiday": "10:00-21:00"
        },
        "metadata": {
          "data_quality": "high",
          "version": "1.0",
          "quality_score": 0.95
        }
      }
    ],
    "count": 1,
    "metadata": {
      "search_criteria": {
        "districts": ["Central district"],
        "search_type": "district"
      },
      "district_counts": {
        "Central district": 1
      },
      "available_districts": {
        "Hong Kong Island": ["Central district", "Admiralty", ...],
        "Kowloon": ["Tsim Sha Tsui", "Mong Kok", ...],
        "New Territories": ["Sha Tin", "Tai Po", ...],
        "Island": ["Lantau Island", "Discovery Bay", ...]
      }
    }
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid districts: ['NonExistent']. Valid districts are: [...]",
    "details": {
      "invalid_districts": ["NonExistent"],
      "valid_districts": ["Central district", "Tsim Sha Tsui", ...],
      "requested_districts": ["NonExistent"]
    }
  }
}
```

## 🔍 Testing Checklist

### Basic Functionality
- [ ] District search returns results for valid districts
- [ ] Meal type search returns results for valid meal types
- [ ] Combined search works with both parameters
- [ ] Combined search works with single parameter
- [ ] Error handling for invalid inputs
- [ ] Empty result handling for non-existent data

### Data Validation
- [ ] Restaurant data structure is complete
- [ ] All required fields are present
- [ ] Operating hours format is correct
- [ ] District names match expected values
- [ ] Meal type classifications are accurate

### Performance
- [ ] Responses return within reasonable time (< 5 seconds)
- [ ] Large result sets are handled properly
- [ ] Multiple concurrent requests work correctly

### Error Handling
- [ ] Invalid district names return proper errors
- [ ] Invalid meal types return proper errors
- [ ] Empty parameters return validation errors
- [ ] Malformed requests are handled gracefully

## 🚨 Troubleshooting

### MCP Server Not Connected
**Symptoms**: Tools not available, connection errors
**Solutions**:
1. Check MCP server configuration in `.kiro/settings/mcp.json`
2. Restart MCP server connection in Kiro
3. Check MCP logs for errors
4. Verify Python environment and dependencies

### Tool Execution Errors
**Symptoms**: Tools fail when invoked
**Solutions**:
1. Check restaurant service dependencies (S3 access)
2. Verify district configuration files
3. Check authentication settings
4. Review MCP server logs

### Empty Results
**Symptoms**: Valid queries return no restaurants
**Solutions**:
1. Verify S3 bucket access and data
2. Check district name spelling and case
3. Confirm meal type classifications
4. Review data loading in restaurant service

### Performance Issues
**Symptoms**: Slow responses, timeouts
**Solutions**:
1. Check S3 connection and latency
2. Review data caching implementation
3. Monitor resource usage
4. Optimize query parameters

## 📈 Advanced Testing

### Load Testing
```python
# Test multiple rapid requests
for i in range(10):
    search_restaurants_by_district(["Central district"])
```

### Stress Testing
```python
# Test with large parameter lists
all_districts = [
    "Central district", "Tsim Sha Tsui", "Causeway Bay", 
    "Admiralty", "Wan Chai", "Mong Kok", "Yau Ma Tei"
]
search_restaurants_by_district(all_districts)
```

### Edge Case Testing
```python
# Test with special characters
search_restaurants_by_district(["Central district"])

# Test with different case variations
search_restaurants_by_district(["central district"])
search_restaurants_by_district(["CENTRAL DISTRICT"])
```

## 📚 Integration with Other Tools

### Combine with Authentication Testing
1. Test MCP tools after authentication setup
2. Verify tools work with different user contexts
3. Test permission-based access if implemented

### Combine with Deployment Testing
1. Test MCP tools after deployment
2. Verify tools work in production environment
3. Test with real AWS S3 data

### Combine with Performance Monitoring
1. Monitor response times during testing
2. Track resource usage during tool execution
3. Analyze error rates and patterns

---

**Testing Method**: Direct MCP Integration (Recommended)  
**Accuracy**: Highest (tests actual MCP protocol)  
**Ease of Use**: Excellent (built into Kiro IDE)  
**Coverage**: Complete (all MCP functionality)