# Comprehensive Error Handling System

## Overview

The MBTI Travel Planner Agent now includes a comprehensive error handling system that converts technical errors into user-friendly messages, provides fallback responses, and maintains excellent user experience even when services are unavailable.

## Key Components

### 1. Error Handler (`services/error_handler.py`)

The central error handling system that provides:

- **Custom Exception Classes**: Specific error types for different scenarios
- **Error Classification**: Automatic categorization of unknown errors
- **User-Friendly Messages**: Conversion of technical errors to helpful messages
- **Fallback Responses**: Alternative suggestions when services fail
- **Structured Logging**: Comprehensive logging with context and severity levels
- **Performance Monitoring**: Tracking and logging of slow operations

### 2. Enhanced Gateway HTTP Client (`services/gateway_http_client.py`)

Updated to use the comprehensive error handling system:

- **Integrated Error Handling**: Uses the centralized error handler
- **Performance Monitoring**: Tracks request duration and logs slow operations
- **Enhanced Validation**: Detailed validation with field-specific error messages
- **Context-Aware Logging**: Includes operation context in all error logs

## Error Categories

The system classifies errors into the following categories:

### Connection Errors
- **Triggers**: Network timeouts, DNS failures, connection refused
- **User Message**: "I'm having trouble connecting to the restaurant search service right now."
- **Fallback**: "I can still help you with general travel planning questions while we work on this."
- **Severity**: HIGH

### Service Errors
- **Triggers**: HTTP 4xx/5xx responses, API-level errors
- **User Message**: "The restaurant search service is experiencing some issues."
- **Fallback**: "Let me know if you'd like help with other travel planning topics."
- **Severity**: MEDIUM to HIGH (based on status code)

### Validation Errors
- **Triggers**: Invalid input parameters, missing required fields
- **User Message**: "There seems to be an issue with your request format."
- **Fallback**: "Let me help you rephrase your request."
- **Severity**: LOW

### Authentication Errors
- **Triggers**: Invalid tokens, expired credentials, 401 responses
- **User Message**: "I'm having trouble accessing the restaurant database right now."
- **Fallback**: "I can still provide general travel advice while this is resolved."
- **Severity**: HIGH

### Timeout Errors
- **Triggers**: Request timeouts, slow responses
- **User Message**: "The restaurant search is taking longer than expected."
- **Fallback**: "Let me try a different approach or help with other travel topics."
- **Severity**: MEDIUM

### Rate Limit Errors
- **Triggers**: HTTP 429 responses, too many requests
- **User Message**: "I'm making too many restaurant searches right now."
- **Fallback**: "Let's wait a moment before trying again, or I can help with other topics."
- **Severity**: MEDIUM
- **Special**: Includes retry_after information

### Configuration Errors
- **Triggers**: Invalid configuration, missing environment variables
- **User Message**: "There's a configuration issue with the restaurant search system."
- **Fallback**: "I can still help with general travel planning while this is resolved."
- **Severity**: HIGH

## Error Response Structure

All errors return a standardized response format:

```json
{
  "success": false,
  "error": {
    "type": "connection",
    "message": "I'm having trouble connecting to the restaurant search service right now.",
    "fallback": "I can still help you with general travel planning questions while we work on this.",
    "suggestions": [
      "Please try again in a few moments",
      "Check your internet connection",
      "Ask me about other travel planning topics"
    ],
    "details": {
      "operation": "search_restaurants_by_district",
      "timestamp": "2025-10-03T17:41:31.945864",
      "severity": "high",
      "category": "connection",
      "environment": "development"
    },
    "support_reference": "MBTI_search_restaurants_by_district_20251003_174131",
    "retry_after": null
  }
}
```

## Fallback Responses

When services are completely unavailable, the system provides helpful fallback responses:

### Restaurant Search Fallback
```json
{
  "success": false,
  "fallback": true,
  "message": "I can't search the restaurant database right now, but I can suggest some popular dining areas in Hong Kong.",
  "suggestions": [
    "Central district has many international restaurants",
    "Tsim Sha Tsui offers great harbor views with dining",
    "Causeway Bay is known for shopping and casual dining",
    "Wan Chai has excellent local Hong Kong cuisine"
  ],
  "alternative_help": [
    "Ask me about tourist attractions in these areas",
    "I can provide general dining tips for Hong Kong",
    "Let me know what type of cuisine you're interested in"
  ]
}
```

## Logging and Monitoring

### Structured Logging
All errors are logged with comprehensive context:

```python
{
  "operation": "search_restaurants_by_district",
  "error_type": "GatewayConnectionError",
  "error_message": "Connection failed",
  "severity": "high",
  "timestamp": "2025-10-03T17:41:31.945864",
  "environment": "development",
  "user_id": "user123",
  "session_id": "session456",
  "additional_data": {
    "districts": ["Central"],
    "timeout": 30
  }
}
```

### Performance Monitoring
Slow operations are automatically detected and logged:

```python
# Logs when operations exceed threshold (default 5 seconds)
handler.log_performance_issue(
    operation="restaurant_search",
    duration=7.5,
    threshold=5.0,
    context=context
)
```

### Support References
Each error generates a unique support reference for tracking:

```
Format: MBTI_{operation}_{timestamp}
Example: MBTI_search_restaurants_by_district_20251003_174131
```

## Usage Examples

### Basic Error Handling
```python
from services.error_handler import handle_gateway_error

try:
    # Some operation that might fail
    result = await gateway_client.search_restaurants_by_district(["Central"])
except Exception as e:
    error_response = handle_gateway_error(
        error=e,
        operation="search_restaurants_by_district",
        user_id="user123",
        environment="production"
    )
    return error_response
```

### Creating Fallback Responses
```python
from services.error_handler import create_fallback_response

# When service is completely unavailable
fallback = create_fallback_response(
    operation="search_restaurants_by_district",
    partial_data={"attempted_districts": ["Central"]}
)
```

### Custom Error Context
```python
from services.error_handler import ErrorHandler

handler = ErrorHandler("my_service")
context = handler.create_error_context(
    operation="custom_operation",
    user_id="user123",
    session_id="session456",
    additional_data={"custom_field": "value"}
)
```

## Testing

The system includes comprehensive tests:

- **Unit Tests**: `tests/test_error_handling.py`
- **Integration Tests**: `tests/test_error_handling_integration.py`
- **Demo Script**: `demo_error_handling.py`

Run tests with:
```bash
python3 -m pytest tests/test_error_handling.py -v
python3 -m pytest tests/test_error_handling_integration.py -v
python3 demo_error_handling.py
```

## Benefits

### For Users
- **Clear Communication**: Technical errors are translated to understandable messages
- **Helpful Suggestions**: Users get actionable advice on what to do next
- **Continuous Service**: Fallback responses keep the conversation going
- **No Confusion**: Consistent error messaging across all operations

### For Developers
- **Comprehensive Logging**: Full context for debugging and monitoring
- **Performance Insights**: Automatic detection of slow operations
- **Error Classification**: Automatic categorization of unknown errors
- **Support Tracking**: Unique references for customer support

### For Operations
- **Monitoring**: Structured logs for operational dashboards
- **Alerting**: Severity-based error classification for alerts
- **Debugging**: Rich context information for troubleshooting
- **Metrics**: Performance and error rate tracking

## Configuration

### Environment Variables
```bash
ENVIRONMENT=production          # Affects error detail level
GATEWAY_AUTH_TOKEN=token       # Authentication token
```

### Logging Configuration
The system uses Python's standard logging module and can be configured through:
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Custom formatters and handlers
- Environment-specific logging configurations

## Future Enhancements

Potential improvements to the error handling system:

1. **Metrics Integration**: Integration with monitoring systems (CloudWatch, Prometheus)
2. **Error Recovery**: Automatic retry mechanisms with exponential backoff
3. **Circuit Breaker**: Prevent cascading failures with circuit breaker pattern
4. **Error Analytics**: Aggregation and analysis of error patterns
5. **Custom Error Pages**: Web-friendly error responses for frontend integration

## Conclusion

The comprehensive error handling system ensures that the MBTI Travel Planner Agent provides excellent user experience even when things go wrong. It converts technical failures into helpful, actionable messages while providing developers and operators with the information they need to maintain and improve the system.