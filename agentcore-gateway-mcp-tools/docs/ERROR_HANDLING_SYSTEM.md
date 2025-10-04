# Error Handling System

The AgentCore Gateway MCP Tools service implements a comprehensive error handling system that provides structured error responses, detailed field validation, MCP server error handling with retry guidance, and authentication error responses with clear requirements.

## Overview

The error handling system consists of several key components:

1. **Error Models** - Pydantic models for structured error responses
2. **Error Handler Middleware** - Comprehensive middleware for catching and formatting errors
3. **Error Service** - Utilities for creating and managing different types of errors
4. **Custom Exceptions** - Specialized exceptions for different error scenarios

## Error Models

### Core Error Types

```python
class ErrorType(str, Enum):
    VALIDATION_ERROR = "ValidationError"
    AUTHENTICATION_ERROR = "AuthenticationError"
    AUTHORIZATION_ERROR = "AuthorizationError"
    MCP_SERVER_ERROR = "MCPServerError"
    RATE_LIMIT_ERROR = "RateLimitError"
    INTERNAL_ERROR = "InternalError"
    SERVICE_UNAVAILABLE = "ServiceUnavailableError"
    TIMEOUT_ERROR = "TimeoutError"
```

### Standard Error Response Format

All error responses follow a consistent structure:

```json
{
    "success": false,
    "error": {
        "type": "ValidationError",
        "message": "Request validation failed",
        "code": "VALIDATION_FAILED",
        "details": { /* type-specific details */ },
        "trace_id": "uuid-trace-id"
    },
    "request_id": "uuid-request-id",
    "timestamp": "2025-01-03T10:30:00Z"
}
```

## Error Types and Responses

### 1. Validation Errors (400 Bad Request)

Returned when request validation fails with detailed field information:

```json
{
    "success": false,
    "error": {
        "type": "ValidationError",
        "message": "Request validation failed",
        "code": "VALIDATION_FAILED",
        "field_errors": [
            {
                "field": "districts",
                "message": "Invalid district name",
                "invalid_value": "Invalid District",
                "valid_values": ["Central district", "Admiralty"],
                "constraint": "enum",
                "suggestion": "Please use a valid Hong Kong district name"
            }
        ],
        "invalid_fields": ["districts"],
        "trace_id": "trace-123"
    },
    "request_id": "req-123",
    "timestamp": "2025-01-03T10:30:00Z"
}
```

### 2. Authentication Errors (401 Unauthorized)

Returned when authentication fails with clear requirements:

```json
{
    "success": false,
    "error": {
        "type": "AuthenticationError",
        "message": "Authentication token is required",
        "code": "AUTHENTICATION_REQUIRED",
        "auth_details": {
            "auth_type": "JWT",
            "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/.well-known/openid-configuration",
            "token_format": "Bearer <JWT_TOKEN>",
            "example_header": "Authorization: Bearer eyJhbGciOiJSUzI1NiIs...",
            "required_scopes": ["read:restaurants"]
        },
        "help_url": "https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-authentication.html",
        "trace_id": "trace-123"
    },
    "request_id": "req-123",
    "timestamp": "2025-01-03T10:30:00Z"
}
```

**Response Headers:**
- `WWW-Authenticate: JWT realm="AgentCore Gateway"`

### 3. MCP Server Errors (503 Service Unavailable)

Returned when MCP servers are unavailable with retry guidance:

```json
{
    "success": false,
    "error": {
        "type": "MCPServerError",
        "message": "MCP server 'restaurant-search' is unavailable",
        "code": "MCP_SERVER_UNAVAILABLE",
        "server_details": {
            "server_name": "restaurant-search",
            "server_endpoint": "http://restaurant-search:8080",
            "error_message": "Connection refused",
            "retry_after": 30,
            "max_retries": 3,
            "current_attempt": 1,
            "health_check_url": "http://restaurant-search:8080/health"
        },
        "retry_guidance": "Wait 30 seconds before retrying. You have 2 retry attempts remaining. Check server health at: http://restaurant-search:8080/health",
        "trace_id": "trace-123"
    },
    "request_id": "req-123",
    "timestamp": "2025-01-03T10:30:00Z"
}
```

**Response Headers:**
- `Retry-After: 30`

### 4. Rate Limit Errors (429 Too Many Requests)

Returned when rate limits are exceeded:

```json
{
    "success": false,
    "error": {
        "type": "RateLimitError",
        "message": "Rate limit exceeded: 105/100 requests per 3600 seconds",
        "code": "RATE_LIMIT_EXCEEDED",
        "rate_limit_details": {
            "limit": 100,
            "window": 3600,
            "retry_after": 1800,
            "current_usage": 105
        },
        "trace_id": "trace-123"
    },
    "request_id": "req-123",
    "timestamp": "2025-01-03T10:30:00Z"
}
```

**Response Headers:**
- `Retry-After: 1800`
- `X-RateLimit-Limit: 100`
- `X-RateLimit-Window: 3600`
- `X-RateLimit-Remaining: 0`

### 5. Internal Server Errors (500 Internal Server Error)

Returned for unexpected errors:

```json
{
    "success": false,
    "error": {
        "type": "InternalError",
        "message": "An unexpected error occurred",
        "code": "INTERNAL_SERVER_ERROR",
        "details": {
            "exception_type": "ValueError",
            "exception_message": "Invalid value provided"
        },
        "trace_id": "trace-123"
    },
    "request_id": "req-123",
    "timestamp": "2025-01-03T10:30:00Z"
}
```

## Custom Exceptions

### MCPServerException

Used for MCP server-related errors:

```python
raise MCPServerException(
    message="Server unavailable",
    server_name="restaurant-search",
    server_endpoint="http://restaurant-search:8080",
    retry_after=30,
    max_retries=3,
    current_attempt=1,
    health_check_url="http://restaurant-search:8080/health"
)
```

### AuthenticationException

Used for authentication-related errors:

```python
raise AuthenticationException(
    message="Token expired",
    auth_type="JWT",
    discovery_url="https://example.com/.well-known/openid-configuration",
    required_scopes=["read:restaurants"],
    token_format="Bearer <JWT_TOKEN>",
    example_header="Authorization: Bearer token",
    help_url="https://docs.example.com/auth"
)
```

### RateLimitException

Used for rate limiting errors:

```python
raise RateLimitException(
    message="Too many requests",
    limit=100,
    window=3600,
    retry_after=1800,
    current_usage=105
)
```

## Error Handler Middleware

The `ErrorHandlerMiddleware` automatically catches and formats all exceptions:

```python
from middleware.error_handler import ErrorHandlerMiddleware

app.add_middleware(
    ErrorHandlerMiddleware,
    include_trace_id=True,
    log_errors=True
)
```

### Features

- **Automatic Exception Handling** - Catches all unhandled exceptions
- **Trace ID Generation** - Generates unique trace IDs for request tracking
- **Structured Logging** - Logs errors with context information
- **HTTP Status Code Mapping** - Maps exceptions to appropriate HTTP status codes
- **Retry Guidance** - Provides intelligent retry guidance for recoverable errors

## Error Service

The `ErrorService` provides utilities for creating and managing errors:

```python
from services.error_service import error_service

# Handle validation errors
try:
    model = SomeModel(**data)
except ValidationError as e:
    error_service.handle_validation_error(e, "user input")

# Handle MCP connection errors
mcp_error = error_service.handle_mcp_connection_error(
    server_name="restaurant-search",
    server_endpoint="http://restaurant-search:8080",
    original_error=ConnectionError("Connection refused"),
    retry_attempt=1,
    max_retries=3
)

# Handle authentication errors
auth_error = error_service.handle_authentication_error(
    error_type="invalid_token",
    discovery_url="https://example.com/.well-known/openid-configuration"
)
```

## Validation Error Suggestions

The system provides intelligent suggestions for validation errors:

- **District Validation**: "Please provide valid Hong Kong district names such as 'Central district', 'Admiralty', 'Causeway Bay'."
- **Meal Type Validation**: "Please use valid meal types: 'breakfast', 'lunch', or 'dinner'."
- **Generic Validation**: Contextual suggestions based on validation constraint type

## Retry Logic

The error handling system includes intelligent retry logic:

### Retryable Errors
- `ConnectionError`
- `TimeoutError`
- `MCPServerException`
- HTTP 408, 429, 502, 503, 504 status codes

### Retry Delay Calculation
- **Exponential Backoff**: `delay = base_delay * (2 ** (attempt - 1))`
- **Linear Backoff**: `delay = base_delay * attempt`
- **Maximum Delay**: Configurable maximum delay cap

### Example Usage

```python
attempt = 1
max_attempts = 3

while attempt <= max_attempts:
    try:
        result = call_mcp_server()
        break
    except Exception as e:
        if error_service.should_retry_error(e, attempt, max_attempts):
            delay = error_service.calculate_retry_delay(attempt)
            await asyncio.sleep(delay)
            attempt += 1
        else:
            raise
```

## Configuration

### Middleware Configuration

```python
app.add_middleware(
    ErrorHandlerMiddleware,
    include_trace_id=True,    # Generate trace IDs for requests
    log_errors=True           # Enable error logging
)
```

### Logging Configuration

The error handling system uses structured logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Error context is automatically included
logger.error(
    "Error processing request",
    extra={
        "trace_id": "trace-123",
        "method": "POST",
        "url": "/api/v1/restaurants/search",
        "exception_type": "ValidationError"
    }
)
```

## Testing

The error handling system includes comprehensive tests:

- **Unit Tests**: Test individual components and error models
- **Integration Tests**: Test end-to-end error handling flows
- **Edge Case Tests**: Test boundary conditions and error scenarios

### Running Tests

```bash
# Run all error handling tests
python -m pytest tests/test_error_models.py tests/test_error_handler.py tests/test_error_service.py -v

# Run integration tests
python -m pytest tests/test_error_handling_integration.py -v
```

## Best Practices

1. **Use Specific Exceptions**: Use custom exceptions for different error types
2. **Provide Context**: Include relevant context in error messages
3. **Log Appropriately**: Log errors with sufficient detail for debugging
4. **Handle Retries**: Implement retry logic for transient errors
5. **Validate Input**: Validate all input data and provide helpful error messages
6. **Secure Error Messages**: Don't expose sensitive information in error responses
7. **Monitor Errors**: Track error rates and patterns for system health

## Security Considerations

- **Information Disclosure**: Error messages are sanitized to prevent information leakage
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Authentication**: Ensure proper authentication for all endpoints
- **Logging**: Log security events for monitoring and alerting
- **Trace IDs**: Use trace IDs for request correlation without exposing sensitive data