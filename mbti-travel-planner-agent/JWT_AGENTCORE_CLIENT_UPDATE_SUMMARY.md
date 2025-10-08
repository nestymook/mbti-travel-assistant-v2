# JWT AgentCore Client Update Summary

## Overview

The `agentcore_runtime_client.py` has been updated to use JWT token authentication with HTTP requests instead of boto3 for AgentCore invocations, following the approach demonstrated in `test_deployed_agent_restaurant_functionality.py`.

## Key Changes

### 1. Authentication Method
- **Before**: Used boto3 with AWS credentials
- **After**: Uses JWT tokens with HTTP requests to AgentCore endpoints

### 2. HTTP-Based Invocation
- Replaced boto3 `bedrock-agentcore` client calls with direct HTTP requests
- Uses `requests` library for HTTP communication
- Supports both synchronous and streaming responses

### 3. New Constructor Parameters
```python
AgentCoreRuntimeClient(
    # ... existing parameters ...
    jwt_token: Optional[str] = None,                    # Direct JWT token
    authentication_manager: Optional[Any] = None        # Authentication manager for automatic token refresh
)
```

### 4. JWT Token Management
- Supports direct JWT token provision
- Integrates with `AuthenticationManager` for automatic token refresh
- Handles token expiration and refresh automatically

### 5. HTTP Endpoint Construction
- Constructs AgentCore HTTP endpoints: `https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_agent_arn}/invocations?qualifier=DEFAULT`
- URL-encodes agent ARNs properly
- Handles streaming responses via Server-Sent Events (SSE)

## New Methods

### `_get_jwt_token()`
```python
async def _get_jwt_token(self) -> str:
    """Get valid JWT token for authentication."""
```
- Returns JWT token from authentication manager or direct token
- Handles automatic token refresh when using authentication manager

### `_invoke_agent_http_with_request()`
```python
async def _invoke_agent_http_with_request(self, request: AgentCoreInvocationRequest) -> Dict[str, Any]:
    """Invoke agent using HTTP requests with JWT authentication."""
```
- Main HTTP-based invocation method
- Handles JWT authentication headers
- Processes streaming responses
- Comprehensive error handling for HTTP status codes

## Utility Functions

### `create_agentcore_client_with_jwt()`
```python
def create_agentcore_client_with_jwt(jwt_token: str, region: str = "us-east-1", **kwargs) -> AgentCoreRuntimeClient:
    """Create AgentCore Runtime client with JWT token."""
```

### `create_agentcore_client_with_auth_manager()`
```python
def create_agentcore_client_with_auth_manager(authentication_manager: Any, region: str = "us-east-1", **kwargs) -> AgentCoreRuntimeClient:
    """Create AgentCore Runtime client with authentication manager."""
```

## Usage Examples

### Direct JWT Token
```python
from services.agentcore_runtime_client import create_agentcore_client_with_jwt

client = create_agentcore_client_with_jwt(
    jwt_token="eyJhbGciOiJSUzI1NiIs...",
    region="us-east-1"
)

response = await client.invoke_agent(
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    input_text="Hello, world!",
    session_id="my_session_123"
)
```

### With Authentication Manager
```python
from services.agentcore_runtime_client import create_agentcore_client_with_auth_manager
from services.authentication_manager import AuthenticationManager, CognitoConfig

# Configure Cognito
cognito_config = CognitoConfig(
    user_pool_id="us-east-1_ABC123DEF",
    client_id="your_client_id",
    client_secret="your_client_secret",
    region="us-east-1"
)

# Create authentication manager
auth_manager = AuthenticationManager(cognito_config)

# Create client with automatic token management
client = create_agentcore_client_with_auth_manager(
    authentication_manager=auth_manager,
    region="us-east-1"
)

response = await client.invoke_agent(
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    input_text="Hello, world!",
    session_id="my_session_123"
)
```

## HTTP Request Format

### Headers
```python
headers = {
    'Authorization': f'Bearer {jwt_token}',
    'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': 'agentcore-client',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
```

### Payload
```python
payload = {
    "prompt": input_text,
    "sessionId": session_id,
    "enableTrace": True
}
```

### Endpoint URL
```
https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{url_encoded_agent_arn}/invocations?qualifier=DEFAULT
```

## Error Handling

The client maintains comprehensive error handling for HTTP-specific scenarios:

- **401 Unauthorized**: Raises `AuthenticationError` with JWT auth type
- **403 Forbidden**: Raises `AuthenticationError` for access denied
- **408/504 Timeout**: Raises `AgentTimeoutError`
- **429 Too Many Requests**: Raises `AgentUnavailableError`
- **Connection Errors**: Raises `AgentUnavailableError`
- **Request Exceptions**: Raises `AgentInvocationError`

## Streaming Support

Streaming responses are handled via Server-Sent Events (SSE):

```python
async for chunk in client.invoke_agent_with_streaming(
    agent_arn=agent_arn,
    input_text="Tell me a story",
    session_id="streaming_session"
):
    if chunk.chunk_text:
        print(chunk.chunk_text, end='', flush=True)
    
    if chunk.is_final:
        break
```

## Backward Compatibility

- All existing method signatures remain unchanged
- Performance optimization features (caching, connection pooling, parallel execution) are preserved
- Legacy response format support is maintained
- Error handling maintains the same exception hierarchy

## Removed Components

- Removed boto3 client initialization (`_init_aws_client()`)
- Removed boto3-based invocation methods
- Removed AWS credential dependency
- Removed `_parse_agent_response()` method (replaced with direct HTTP response parsing)

## Dependencies

### Added
- `urllib.parse` for URL encoding
- `requests` for HTTP communication (already imported)

### Removed
- `boto3` dependency for AgentCore calls
- `botocore` exceptions for AgentCore operations

## Testing

A comprehensive demo script is provided at `examples/jwt_agentcore_client_demo.py` that demonstrates:

1. Direct JWT token usage
2. Authentication manager integration
3. Streaming response handling
4. Performance metrics collection

## Migration Guide

### For Direct JWT Token Usage
```python
# Before (boto3)
client = AgentCoreRuntimeClient(region="us-east-1")

# After (JWT)
client = create_agentcore_client_with_jwt(
    jwt_token="your_jwt_token",
    region="us-east-1"
)
```

### For Authentication Manager Usage
```python
# Before (boto3)
client = AgentCoreRuntimeClient(region="us-east-1")

# After (JWT with auth manager)
auth_manager = AuthenticationManager(cognito_config)
client = create_agentcore_client_with_auth_manager(
    authentication_manager=auth_manager,
    region="us-east-1"
)
```

## Benefits

1. **No AWS Credentials Required**: Uses JWT tokens instead of AWS credentials
2. **Direct HTTP Communication**: More control over request/response handling
3. **Automatic Token Refresh**: When using authentication manager
4. **Better Error Handling**: HTTP-specific error codes and messages
5. **Streaming Support**: Native SSE handling for streaming responses
6. **Performance**: Maintains all existing performance optimizations

## Security Considerations

- JWT tokens should be stored securely
- Use authentication manager for automatic token refresh
- Tokens have expiration times and should be refreshed appropriately
- HTTPS is used for all communications

This update provides a more flexible and secure approach to AgentCore communication while maintaining all existing functionality and performance optimizations.