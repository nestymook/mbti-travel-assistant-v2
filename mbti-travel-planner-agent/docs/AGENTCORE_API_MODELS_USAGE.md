# AgentCore API Models Usage Guide

This document explains how to use the new AgentCore API models for proper parameter mapping and response parsing while maintaining backward compatibility.

## Overview

The new API models provide:
- **Proper parameter mapping** for AgentCore API compatibility
- **Structured response parsing** with error handling
- **Backward compatibility** with existing response formats
- **Data transformation utilities** for seamless integration

## Key Components

### 1. AgentCoreInvocationRequest

Handles proper parameter mapping for AgentCore API calls.

```python
from models.agentcore_api_models import AgentCoreInvocationRequest

# Create a request with proper parameter mapping
request = AgentCoreInvocationRequest(
    agent_runtime_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    input_text="Hello, how can you help me?",
    session_id="my-custom-session-id"  # Optional, auto-generated if not provided
)

# Get API parameters for AgentCore
api_params = request.to_api_params()
# Returns: {
#     'agentRuntimeArn': '...',
#     'runtimeSessionId': '...',  # Padded to 33+ characters
#     'payload': '{"input": {"prompt": "Hello, how can you help me?"}}',
#     'qualifier': 'DEFAULT'
# }

# Get legacy parameters for backward compatibility
legacy_params = request.to_legacy_params()
# Returns: {
#     'agentId': 'my-agent',
#     'agentAliasId': 'TSTALIASID',
#     'sessionId': '...',
#     'inputText': 'Hello, how can you help me?'
# }
```

### 2. AgentCoreInvocationResponse

Handles structured response parsing with proper error handling.

```python
from models.agentcore_api_models import AgentCoreInvocationResponse

# Parse AgentCore API response
response = AgentCoreInvocationResponse.from_api_response(
    response=raw_api_response,
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    execution_time_ms=150
)

# Access response data
print(f"Response: {response.response_text}")
print(f"Session ID: {response.session_id}")
print(f"Status: {response.status_code}")
print(f"Success: {response.is_successful()}")

# Convert to legacy format for backward compatibility
legacy_response = response.to_legacy_format()
# Returns: {
#     'completion': 'response text',
#     'sessionId': 'session-id',
#     'ResponseMetadata': {...}
# }

# Get structured dictionary
response_dict = response.to_dict()
# Returns all fields in a structured format
```

### 3. AgentCoreStreamingResponse

Handles streaming responses from AgentCore agents.

```python
from models.agentcore_api_models import AgentCoreStreamingResponse

# Parse streaming chunk
streaming_response = AgentCoreStreamingResponse.from_stream_chunk(
    chunk_data=chunk_from_stream,
    session_id="session-id",
    chunk_index=0
)

print(f"Chunk: {streaming_response.chunk_text}")
print(f"Final: {streaming_response.is_final}")
print(f"Index: {streaming_response.chunk_index}")
```

### 4. AgentCoreAPITransformer

Utility class for data transformation and backward compatibility.

```python
from models.agentcore_api_models import AgentCoreAPITransformer

# Transform request to AgentCore format
request = AgentCoreAPITransformer.transform_request_to_agentcore(
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    input_text="Transform this request",
    session_id="transform-session",
    custom_param="custom_value"
)

# Transform response from AgentCore format
response = AgentCoreAPITransformer.transform_response_from_agentcore(
    response=raw_api_response,
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    execution_time_ms=200
)

# Ensure backward compatibility
compat_response = AgentCoreAPITransformer.ensure_backward_compatibility(response)
# Returns dictionary with both new and legacy fields
```

## Updated AgentCore Runtime Client

The `AgentCoreRuntimeClient` has been updated to use the new API models internally while maintaining backward compatibility.

### New Response Format

```python
from services.agentcore_runtime_client import AgentCoreRuntimeClient

client = AgentCoreRuntimeClient(region="us-east-1")

# New method returns AgentCoreInvocationResponse
response = await client.invoke_agent(
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    input_text="Hello, agent!"
)

# Access structured response
print(f"Response: {response.response_text}")
print(f"Execution time: {response.execution_time_ms}ms")
print(f"Success: {response.is_successful()}")
```

### Backward Compatibility

```python
# Legacy method returns dictionary with both new and legacy fields
legacy_response = await client.invoke_agent_legacy(
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my-agent",
    input_text="Hello, agent!"
)

# Access both formats
print(f"New format: {legacy_response['response_text']}")
print(f"Legacy format: {legacy_response['completion']}")
print(f"Success: {legacy_response['success']}")
```

### Transform Existing Responses

```python
# Transform new response for compatibility with existing code
response = await client.invoke_agent(...)
compat_response = client.transform_response_for_compatibility(response)

# Now has both new and legacy fields
assert compat_response['response_text'] == compat_response['completion']
assert compat_response['session_id'] == compat_response['sessionId']
```

## Migration Guide

### For New Code

Use the new API models directly:

```python
from models.agentcore_api_models import AgentCoreInvocationRequest, AgentCoreInvocationResponse
from services.agentcore_runtime_client import AgentCoreRuntimeClient

client = AgentCoreRuntimeClient()
response = await client.invoke_agent(agent_arn="...", input_text="...")

# Use structured response
if response.is_successful():
    print(f"Agent response: {response.response_text}")
else:
    error_details = response.get_error_details()
    print(f"Error: {error_details}")
```

### For Existing Code

Minimal changes required - use legacy compatibility methods:

```python
# Change this:
# response = await client.invoke_agent(...)
# result = response['completion']

# To this:
response = await client.invoke_agent_legacy(...)
result = response['completion']  # Still works!

# Or transform the response:
new_response = await client.invoke_agent(...)
compat_response = client.transform_response_for_compatibility(new_response)
result = compat_response['completion']  # Still works!
```

## Key Benefits

1. **Proper Parameter Mapping**: Ensures correct AgentCore API parameter names and formats
2. **Session ID Validation**: Automatically ensures session IDs meet AgentCore requirements (33+ characters)
3. **Structured Error Handling**: Provides detailed error information and success indicators
4. **Backward Compatibility**: Existing code continues to work without changes
5. **Response Parsing**: Handles various AgentCore response formats consistently
6. **Data Transformation**: Utilities for converting between formats as needed

## Testing

The new API models include comprehensive tests:

```bash
# Run API model tests
python -m pytest tests/test_agentcore_api_models.py -v

# Run integration tests
python -m pytest tests/test_agentcore_runtime_client_integration.py -v
```

## Error Handling

The new models provide better error handling:

```python
response = await client.invoke_agent(...)

if not response.is_successful():
    error_details = response.get_error_details()
    print(f"Status Code: {error_details['status_code']}")
    print(f"Error Message: {error_details['error_message']}")
    print(f"Agent ARN: {error_details['agent_arn']}")
```

## Performance Considerations

- **Validation**: Request validation ensures early error detection
- **Caching**: Response objects are cache-friendly
- **Memory**: Efficient parsing of streaming responses
- **Compatibility**: Minimal overhead for backward compatibility features

This implementation ensures that the MBTI Travel Planner Agent can properly communicate with AgentCore while maintaining compatibility with existing code.