# MCP Tool Usage Examples and Integration Patterns

This document provides comprehensive examples and integration patterns for using the Restaurant Search MCP tools with BedrockAgentCoreApp entrypoint, including authentication, status monitoring, and error handling.

## Table of Contents

1. [BedrockAgentCoreApp Integration](#bedrockagentcoreapp-integration)
2. [MCP Tool Examples](#mcp-tool-examples)
3. [Authentication Integration](#authentication-integration)
4. [Status Monitoring Integration](#status-monitoring-integration)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Testing and Validation](#testing-and-validation)
7. [Performance Optimization](#performance-optimization)
8. [Integration Patterns](#integration-patterns)

## BedrockAgentCoreApp Integration

### Basic Entrypoint Setup

The Restaurant Search MCP system uses BedrockAgentCoreApp as the main entrypoint, which processes natural language queries and automatically selects appropriate MCP tools.

```python
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

# Initialize the BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Create Strands Agent with restaurant search tools
strands_agent = Agent(
    model="amazon.nova-pro-v1:0",
    system_prompt="""You are a helpful restaurant search assistant for Hong Kong...""",
    tools=[
        search_restaurants_by_district_tool,
        search_restaurants_by_meal_type_tool,
        search_restaurants_combined_tool
    ],
    temperature=0.1,
    max_tokens=2048,
    top_p=0.9,
    tool_choice="auto"
)

@app.entrypoint
def process_request(payload: Dict[str, Any]) -> str:
    """Process natural language queries and return formatted responses."""
    user_prompt = extract_user_prompt(payload)
    agent_response = strands_agent.run(user_prompt)
    return format_response(agent_response, success=True)
```

### Natural Language Query Processing

The system automatically converts natural language queries to MCP tool calls:

```python
# Example natural language queries and their tool mappings
query_examples = {
    "Find restaurants in Central district": {
        "tool": "search_restaurants_by_district_tool",
        "parameters": {"districts": ["Central district"]},
        "expected_response": "JSON with Central district restaurants"
    },
    
    "Show me breakfast places": {
        "tool": "search_restaurants_by_meal_type_tool", 
        "parameters": {"meal_types": ["breakfast"]},
        "expected_response": "JSON with breakfast restaurants"
    },
    
    "I want dinner in Tsim Sha Tsui": {
        "tool": "search_restaurants_combined_tool",
        "parameters": {
            "districts": ["Tsim Sha Tsui"],
            "meal_types": ["dinner"]
        },
        "expected_response": "JSON with dinner restaurants in Tsim Sha Tsui"
    }
}
```

## MCP Tool Examples

### 1. search_restaurants_by_district Tool

#### Basic Usage
```python
@tool
def search_restaurants_by_district_tool(districts: list[str]) -> str:
    """
    Search for restaurants in specific Hong Kong districts.
    
    Args:
        districts: List of Hong Kong district names
        
    Returns:
        JSON string containing restaurant data and metadata
    """
    try:
        results = restaurant_service.search_by_districts(districts)
        
        response_data = {
            "success": True,
            "query_type": "district_search",
            "districts": districts,
            "restaurant_count": len(results),
            "restaurants": [restaurant.to_dict() for restaurant in results]
        }
        
        return json.dumps(response_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "query_type": "district_search",
            "districts": districts
        }, ensure_ascii=False, indent=2)
```

#### Example Requests and Responses

**Single District Search:**
```python
# Input
districts = ["Central district"]

# Expected Response
{
  "success": true,
  "query_type": "district_search",
  "districts": ["Central district"],
  "restaurant_count": 25,
  "restaurants": [
    {
      "id": "rest_001",
      "name": "Central Cafe",
      "address": "123 Des Voeux Road Central",
      "meal_type": ["Western", "Coffee"],
      "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
      "location_category": "Business District",
      "district": "Central district",
      "price_range": "$$",
      "operating_hours": {
        "mon_fri": ["07:00 - 22:00"],
        "sat_sun": ["08:00 - 23:00"],
        "public_holiday": ["08:00 - 23:00"]
      }
    }
    // ... more restaurants
  ]
}
```

**Multiple Districts Search:**
```python
# Input
districts = ["Central district", "Admiralty", "Wan Chai"]

# Expected Response
{
  "success": true,
  "query_type": "district_search", 
  "districts": ["Central district", "Admiralty", "Wan Chai"],
  "restaurant_count": 78,
  "restaurants": [
    // Restaurants from all three districts
  ]
}
```

**Invalid District Handling:**
```python
# Input
districts = ["InvalidDistrict"]

# Expected Response
{
  "success": false,
  "error": "Invalid district name: 'InvalidDistrict'. Available districts: ['Admiralty', 'Central district', 'Causeway Bay', ...]",
  "query_type": "district_search",
  "districts": ["InvalidDistrict"],
  "suggestions": ["Central district", "Admiralty", "Causeway Bay"]
}
```

### 2. search_restaurants_by_meal_type Tool

#### Basic Usage
```python
@tool
def search_restaurants_by_meal_type_tool(meal_types: list[str]) -> str:
    """
    Search for restaurants by meal type based on operating hours.
    
    Args:
        meal_types: List of meal types ("breakfast", "lunch", "dinner")
        
    Returns:
        JSON string containing restaurant data filtered by operating hours
    """
    try:
        results = restaurant_service.search_by_meal_types(meal_types)
        
        response_data = {
            "success": True,
            "query_type": "meal_type_search",
            "meal_types": meal_types,
            "restaurant_count": len(results),
            "meal_time_definitions": {
                "breakfast": "07:00-11:29",
                "lunch": "11:30-17:29", 
                "dinner": "17:30-22:30"
            },
            "restaurants": [restaurant.to_dict() for restaurant in results]
        }
        
        return json.dumps(response_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "query_type": "meal_type_search",
            "meal_types": meal_types
        }, ensure_ascii=False, indent=2)
```

#### Example Requests and Responses

**Breakfast Search:**
```python
# Input
meal_types = ["breakfast"]

# Expected Response
{
  "success": true,
  "query_type": "meal_type_search",
  "meal_types": ["breakfast"],
  "restaurant_count": 42,
  "meal_time_definitions": {
    "breakfast": "07:00-11:29",
    "lunch": "11:30-17:29",
    "dinner": "17:30-22:30"
  },
  "restaurants": [
    {
      "id": "rest_breakfast_001",
      "name": "Morning Glory Cafe",
      "operating_hours": {
        "mon_fri": ["06:30 - 11:00", "12:00 - 15:00"],
        "sat_sun": ["07:00 - 11:30"],
        "public_holiday": ["07:00 - 11:30"]
      },
      "meal_availability": {
        "breakfast": true,
        "lunch": true,
        "dinner": false
      }
    }
    // ... more breakfast restaurants
  ]
}
```

**Multiple Meal Types:**
```python
# Input
meal_types = ["breakfast", "lunch"]

# Expected Response
{
  "success": true,
  "query_type": "meal_type_search",
  "meal_types": ["breakfast", "lunch"],
  "restaurant_count": 156,
  "restaurants": [
    // Restaurants serving breakfast OR lunch
  ]
}
```

### 3. search_restaurants_combined Tool

#### Basic Usage
```python
@tool
def search_restaurants_combined_tool(
    districts: Optional[list[str]] = None,
    meal_types: Optional[list[str]] = None
) -> str:
    """
    Search for restaurants by both district and meal type.
    
    Args:
        districts: Optional list of Hong Kong district names
        meal_types: Optional list of meal types
        
    Returns:
        JSON string containing filtered restaurant data
    """
    try:
        results = restaurant_service.search_combined(districts, meal_types)
        
        response_data = {
            "success": True,
            "query_type": "combined_search",
            "districts": districts,
            "meal_types": meal_types,
            "restaurant_count": len(results),
            "filters_applied": {
                "district_filter": districts is not None,
                "meal_type_filter": meal_types is not None
            },
            "restaurants": [restaurant.to_dict() for restaurant in results]
        }
        
        return json.dumps(response_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "query_type": "combined_search",
            "districts": districts,
            "meal_types": meal_types
        }, ensure_ascii=False, indent=2)
```

#### Example Requests and Responses

**Combined District and Meal Type:**
```python
# Input
districts = ["Central district"]
meal_types = ["dinner"]

# Expected Response
{
  "success": true,
  "query_type": "combined_search",
  "districts": ["Central district"],
  "meal_types": ["dinner"],
  "restaurant_count": 18,
  "filters_applied": {
    "district_filter": true,
    "meal_type_filter": true
  },
  "restaurants": [
    // Restaurants in Central district serving dinner
  ]
}
```

**District Only:**
```python
# Input
districts = ["Tsim Sha Tsui"]
meal_types = None

# Expected Response
{
  "success": true,
  "query_type": "combined_search",
  "districts": ["Tsim Sha Tsui"],
  "meal_types": null,
  "restaurant_count": 34,
  "filters_applied": {
    "district_filter": true,
    "meal_type_filter": false
  },
  "restaurants": [
    // All restaurants in Tsim Sha Tsui
  ]
}
```

## Authentication Integration

### JWT Token Management

```python
import boto3
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

class CognitoAuthenticator:
    """Handle Cognito authentication for MCP tools."""
    
    def __init__(self, user_pool_id: str, client_id: str, client_secret: str):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    def calculate_secret_hash(self, username: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication."""
        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return tokens."""
        try:
            secret_hash = self.calculate_secret_hash(username)
            
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                    'SECRET_HASH': secret_hash
                }
            )
            
            return {
                'success': True,
                'tokens': response['AuthenticationResult'],
                'expires_at': datetime.now() + timedelta(
                    seconds=response['AuthenticationResult']['ExpiresIn']
                )
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'authentication_failed'
            }

# Usage example
authenticator = CognitoAuthenticator(
    user_pool_id="us-east-1_KePRX24Bn",
    client_id="1ofgeckef3po4i3us4j1m4chvd",
    client_secret="your-client-secret"
)

# Authenticate and get tokens
auth_result = await authenticator.authenticate_user("test@mbti-travel.com", "password")
if auth_result['success']:
    jwt_token = auth_result['tokens']['IdToken']
    # Use token for MCP requests
```

### MCP Request Authentication

```python
import aiohttp
import json

class AuthenticatedMCPClient:
    """MCP client with JWT authentication."""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    async def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool with authentication."""
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/mcp",
                    headers=self.headers,
                    json=mcp_request,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'data': result,
                            'status_code': response.status
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {error_text}",
                            'status_code': response.status
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'request_failed'
            }

# Usage example
client = AuthenticatedMCPClient(
    base_url="https://your-gateway-url",
    jwt_token=jwt_token
)

# Call restaurant search tool
result = await client.call_mcp_tool(
    tool_name="search_restaurants_by_district",
    parameters={"districts": ["Central district"]}
)
```

## Status Monitoring Integration

### Health Check API Usage

```python
import aiohttp
import asyncio
from datetime import datetime

class StatusMonitoringClient:
    """Client for status monitoring API."""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/status/health",
                    headers=self.headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'health_data': data,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}",
                            'status_code': response.status
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'health_check_failed'
            }
    
    async def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """Get status for specific server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/status/servers/{server_name}",
                    headers=self.headers
                ) as response:
                    
                    data = await response.json()
                    return {
                        'success': response.status == 200,
                        'server_status': data,
                        'status_code': response.status
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'server_name': server_name
            }
    
    async def trigger_health_check(self, server_names: List[str] = None) -> Dict[str, Any]:
        """Trigger manual health check."""
        try:
            request_data = {}
            if server_names:
                request_data['server_names'] = server_names
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/status/health-check",
                    headers=self.headers,
                    json=request_data
                ) as response:
                    
                    data = await response.json()
                    return {
                        'success': response.status == 200,
                        'health_check_results': data,
                        'status_code': response.status
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'manual_health_check_failed'
            }

# Usage examples
monitor = StatusMonitoringClient(
    base_url="https://your-gateway-url",
    jwt_token=jwt_token
)

# Get system health
health = await monitor.get_system_health()
print(f"System Health: {health}")

# Get specific server status
server_status = await monitor.get_server_status("restaurant-search-mcp")
print(f"Server Status: {server_status}")

# Trigger manual health check
health_check = await monitor.trigger_health_check(["restaurant-search-mcp"])
print(f"Health Check Results: {health_check}")
```

### Circuit Breaker Integration

```python
class CircuitBreakerClient:
    """Client for circuit breaker operations."""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    async def reset_circuit_breaker(self, server_names: List[str]) -> Dict[str, Any]:
        """Reset circuit breaker for specified servers."""
        try:
            request_data = {
                'action': 'reset',
                'server_names': server_names
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/status/circuit-breaker",
                    headers=self.headers,
                    json=request_data
                ) as response:
                    
                    data = await response.json()
                    return {
                        'success': response.status == 200,
                        'circuit_breaker_results': data,
                        'status_code': response.status
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'circuit_breaker_operation_failed'
            }
    
    async def force_circuit_breaker_open(self, server_names: List[str]) -> Dict[str, Any]:
        """Force circuit breaker open for maintenance."""
        request_data = {
            'action': 'open',
            'server_names': server_names
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/status/circuit-breaker",
                headers=self.headers,
                json=request_data
            ) as response:
                data = await response.json()
                return {
                    'success': response.status == 200,
                    'results': data
                }

# Usage example
cb_client = CircuitBreakerClient(
    base_url="https://your-gateway-url",
    jwt_token=jwt_token
)

# Reset circuit breaker
reset_result = await cb_client.reset_circuit_breaker(["restaurant-search-mcp"])
print(f"Circuit Breaker Reset: {reset_result}")
```

## Error Handling Patterns

### Comprehensive Error Handling

```python
class RestaurantSearchClient:
    """Comprehensive client with error handling."""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def search_restaurants_with_retry(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search restaurants with retry logic and comprehensive error handling."""
        
        for attempt in range(self.max_retries):
            try:
                result = await self._make_request(tool_name, parameters)
                
                if result['success']:
                    return result
                
                # Handle specific error types
                if 'authentication' in result.get('error', '').lower():
                    return {
                        'success': False,
                        'error': 'Authentication failed. Please check your credentials.',
                        'error_type': 'authentication_error',
                        'retry_recommended': False
                    }
                
                if 'circuit breaker' in result.get('error', '').lower():
                    return {
                        'success': False,
                        'error': 'Service temporarily unavailable due to circuit breaker.',
                        'error_type': 'circuit_breaker_open',
                        'retry_recommended': True,
                        'retry_after_seconds': 60
                    }
                
                # Retry on transient errors
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                
                return result
                
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                
                return {
                    'success': False,
                    'error': 'Request timeout after multiple attempts',
                    'error_type': 'timeout_error',
                    'attempts': self.max_retries
                }
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}',
                    'error_type': 'unexpected_error',
                    'attempts': self.max_retries
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded',
            'error_type': 'max_retries_exceeded'
        }
    
    async def _make_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated MCP request."""
        headers = {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json'
        }
        
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/mcp",
                headers=headers,
                json=mcp_request,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'data': data,
                        'status_code': response.status
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}: {error_text}",
                        'status_code': response.status
                    }

# Usage with error handling
client = RestaurantSearchClient(
    base_url="https://your-gateway-url",
    jwt_token=jwt_token
)

result = await client.search_restaurants_with_retry(
    tool_name="search_restaurants_by_district",
    parameters={"districts": ["Central district"]}
)

if result['success']:
    restaurants = result['data']
    print(f"Found {len(restaurants)} restaurants")
else:
    print(f"Error: {result['error']}")
    if result.get('retry_recommended'):
        print(f"Retry recommended after {result.get('retry_after_seconds', 60)} seconds")
```

### Error Response Formatting

```python
def format_user_friendly_error(error_response: Dict[str, Any]) -> str:
    """Format error responses for user consumption."""
    
    error_messages = {
        'authentication_error': "Please check your login credentials and try again.",
        'circuit_breaker_open': "The service is temporarily unavailable. Please try again in a few minutes.",
        'timeout_error': "The request took too long to complete. Please try again.",
        'validation_error': "Please check your input and try again.",
        'district_not_found': "I don't recognize that district name. Try using districts like 'Central district', 'Tsim Sha Tsui', or 'Causeway Bay'.",
        'meal_type_invalid': "Please specify a valid meal type: breakfast, lunch, or dinner.",
        'no_results_found': "No restaurants found matching your criteria. Try broadening your search.",
        'service_unavailable': "The restaurant search service is currently unavailable. Please try again later."
    }
    
    error_type = error_response.get('error_type', 'unknown_error')
    user_message = error_messages.get(error_type, "An unexpected error occurred. Please try again.")
    
    response = {
        'success': False,
        'message': user_message,
        'error_details': {
            'type': error_type,
            'technical_message': error_response.get('error', 'Unknown error'),
            'timestamp': datetime.now().isoformat()
        }
    }
    
    # Add suggestions based on error type
    if error_type == 'district_not_found':
        response['suggestions'] = [
            "Try 'Central district' for business area restaurants",
            "Try 'Tsim Sha Tsui' for tourist area dining",
            "Try 'Causeway Bay' for shopping district food"
        ]
    elif error_type == 'no_results_found':
        response['suggestions'] = [
            "Try searching in nearby districts",
            "Try different meal times",
            "Remove some filters to broaden your search"
        ]
    
    return json.dumps(response, ensure_ascii=False, indent=2)
```

## Testing and Validation

### Unit Testing Examples

```python
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

class TestRestaurantSearchMCP:
    """Test cases for Restaurant Search MCP tools."""
    
    @pytest.fixture
    def mock_restaurant_service(self):
        """Mock restaurant service for testing."""
        service = Mock()
        service.search_by_districts.return_value = [
            Mock(to_dict=lambda: {
                'id': 'test_001',
                'name': 'Test Restaurant',
                'district': 'Central district'
            })
        ]
        return service
    
    @pytest.mark.asyncio
    async def test_search_by_district_success(self, mock_restaurant_service):
        """Test successful district search."""
        # Setup
        with patch('main.restaurant_service', mock_restaurant_service):
            from main import search_restaurants_by_district_tool
            
            # Execute
            result = search_restaurants_by_district_tool(["Central district"])
            
            # Verify
            result_data = json.loads(result)
            assert result_data['success'] is True
            assert result_data['query_type'] == 'district_search'
            assert result_data['restaurant_count'] == 1
            assert len(result_data['restaurants']) == 1
    
    @pytest.mark.asyncio
    async def test_search_by_district_invalid_district(self, mock_restaurant_service):
        """Test district search with invalid district."""
        # Setup
        mock_restaurant_service.search_by_districts.side_effect = ValueError("Invalid district")
        
        with patch('main.restaurant_service', mock_restaurant_service):
            from main import search_restaurants_by_district_tool
            
            # Execute
            result = search_restaurants_by_district_tool(["InvalidDistrict"])
            
            # Verify
            result_data = json.loads(result)
            assert result_data['success'] is False
            assert 'Invalid district' in result_data['error']
    
    @pytest.mark.asyncio
    async def test_entrypoint_payload_processing(self):
        """Test entrypoint payload processing."""
        from main import extract_user_prompt, process_request
        
        # Test various payload formats
        test_payloads = [
            {"input": {"prompt": "Find restaurants in Central"}},
            {"input": "Find restaurants in Central"},
            {"prompt": "Find restaurants in Central"},
            {"message": "Find restaurants in Central"}
        ]
        
        for payload in test_payloads:
            prompt = extract_user_prompt(payload)
            assert "Find restaurants in Central" in prompt
    
    @pytest.mark.asyncio
    async def test_authentication_integration(self):
        """Test authentication integration."""
        from tests.test_auth_integration import CognitoAuthenticator
        
        # Mock Cognito client
        mock_cognito = AsyncMock()
        mock_cognito.admin_initiate_auth.return_value = {
            'AuthenticationResult': {
                'IdToken': 'mock_token',
                'AccessToken': 'mock_access_token',
                'ExpiresIn': 3600
            }
        }
        
        authenticator = CognitoAuthenticator(
            user_pool_id="test_pool",
            client_id="test_client",
            client_secret="test_secret"
        )
        authenticator.cognito_client = mock_cognito
        
        # Test authentication
        result = await authenticator.authenticate_user("test@example.com", "password")
        
        assert result['success'] is True
        assert 'tokens' in result
        assert result['tokens']['IdToken'] == 'mock_token'
```

### Integration Testing

```python
class TestMCPIntegration:
    """Integration tests for MCP tools."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_restaurant_search(self):
        """Test complete end-to-end restaurant search flow."""
        # Setup authenticated client
        client = AuthenticatedMCPClient(
            base_url=os.getenv('TEST_MCP_URL'),
            jwt_token=os.getenv('TEST_JWT_TOKEN')
        )
        
        # Test district search
        result = await client.call_mcp_tool(
            tool_name="search_restaurants_by_district",
            parameters={"districts": ["Central district"]}
        )
        
        assert result['success'] is True
        assert 'data' in result
        
        # Validate response structure
        data = result['data']
        assert 'result' in data
        assert 'content' in data['result']
        
        # Parse restaurant data
        restaurant_data = json.loads(data['result']['content'])
        assert restaurant_data['success'] is True
        assert restaurant_data['restaurant_count'] > 0
        assert len(restaurant_data['restaurants']) > 0
    
    @pytest.mark.asyncio
    async def test_status_monitoring_integration(self):
        """Test status monitoring integration."""
        monitor = StatusMonitoringClient(
            base_url=os.getenv('TEST_MCP_URL'),
            jwt_token=os.getenv('TEST_JWT_TOKEN')
        )
        
        # Test system health
        health = await monitor.get_system_health()
        assert health['success'] is True
        
        # Test server status
        server_status = await monitor.get_server_status("restaurant-search-mcp")
        assert server_status['success'] is True
        
        # Test manual health check
        health_check = await monitor.trigger_health_check(["restaurant-search-mcp"])
        assert health_check['success'] is True
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        client = RestaurantSearchClient(
            base_url=os.getenv('TEST_MCP_URL'),
            jwt_token="invalid_token"  # Intentionally invalid
        )
        
        # Test authentication error handling
        result = await client.search_restaurants_with_retry(
            tool_name="search_restaurants_by_district",
            parameters={"districts": ["Central district"]}
        )
        
        assert result['success'] is False
        assert result['error_type'] == 'authentication_error'
        assert result['retry_recommended'] is False
```

## Performance Optimization

### Caching Strategies

```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class CachedMCPClient:
    """MCP client with response caching."""
    
    def __init__(self, base_url: str, jwt_token: str, cache_ttl: int = 300):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        import hashlib
        param_str = json.dumps(parameters, sort_keys=True)
        key_data = f"{tool_name}:{param_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        cached_at = datetime.fromisoformat(cache_entry['cached_at'])
        return datetime.now() - cached_at < timedelta(seconds=self.cache_ttl)
    
    async def call_mcp_tool_cached(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Call MCP tool with caching support."""
        
        cache_key = self._get_cache_key(tool_name, parameters)
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry):
                cache_entry['cache_hit'] = True
                return cache_entry
        
        # Make actual request
        result = await self._make_request(tool_name, parameters)
        
        # Cache successful results
        if result['success']:
            result['cached_at'] = datetime.now().isoformat()
            result['cache_hit'] = False
            self.cache[cache_key] = result
        
        return result
    
    async def _make_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make actual MCP request."""
        # Implementation similar to previous examples
        pass

# Usage with caching
cached_client = CachedMCPClient(
    base_url="https://your-gateway-url",
    jwt_token=jwt_token,
    cache_ttl=300  # 5 minutes
)

# First call - cache miss
result1 = await cached_client.call_mcp_tool_cached(
    tool_name="search_restaurants_by_district",
    parameters={"districts": ["Central district"]}
)
print(f"Cache hit: {result1.get('cache_hit', False)}")

# Second call - cache hit
result2 = await cached_client.call_mcp_tool_cached(
    tool_name="search_restaurants_by_district",
    parameters={"districts": ["Central district"]}
)
print(f"Cache hit: {result2.get('cache_hit', False)}")
```

### Batch Processing

```python
class BatchMCPClient:
    """MCP client with batch processing capabilities."""
    
    def __init__(self, base_url: str, jwt_token: str, max_concurrent: int = 5):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def batch_search_restaurants(
        self, 
        search_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple restaurant search requests concurrently."""
        
        async def process_single_request(request: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    result = await self._make_request(
                        request['tool_name'],
                        request['parameters']
                    )
                    return {
                        'request_id': request.get('id'),
                        'success': True,
                        'result': result
                    }
                except Exception as e:
                    return {
                        'request_id': request.get('id'),
                        'success': False,
                        'error': str(e)
                    }
        
        # Process all requests concurrently
        tasks = [process_single_request(req) for req in search_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'request_id': search_requests[i].get('id'),
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results

# Usage example
batch_client = BatchMCPClient(
    base_url="https://your-gateway-url",
    jwt_token=jwt_token,
    max_concurrent=5
)

# Batch search requests
search_requests = [
    {
        'id': 'req_1',
        'tool_name': 'search_restaurants_by_district',
        'parameters': {'districts': ['Central district']}
    },
    {
        'id': 'req_2',
        'tool_name': 'search_restaurants_by_district',
        'parameters': {'districts': ['Tsim Sha Tsui']}
    },
    {
        'id': 'req_3',
        'tool_name': 'search_restaurants_by_meal_type',
        'parameters': {'meal_types': ['breakfast']}
    }
]

# Process batch
results = await batch_client.batch_search_restaurants(search_requests)
for result in results:
    print(f"Request {result['request_id']}: {'Success' if result['success'] else 'Failed'}")
```

## Integration Patterns

### Web Application Integration

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Restaurant Search API")
security = HTTPBearer()

class RestaurantSearchRequest(BaseModel):
    districts: Optional[List[str]] = None
    meal_types: Optional[List[str]] = None
    query: Optional[str] = None  # Natural language query

class RestaurantSearchResponse(BaseModel):
    success: bool
    restaurants: List[Dict[str, Any]]
    total_count: int
    query_info: Dict[str, Any]

# Initialize MCP client
mcp_client = AuthenticatedMCPClient(
    base_url=os.getenv('MCP_BASE_URL'),
    jwt_token=os.getenv('MCP_JWT_TOKEN')
)

@app.post("/api/restaurants/search", response_model=RestaurantSearchResponse)
async def search_restaurants(
    request: RestaurantSearchRequest,
    token: str = Depends(security)
):
    """Search restaurants via MCP tools."""
    try:
        # Determine which MCP tool to use
        if request.query:
            # Use entrypoint for natural language processing
            result = await mcp_client.call_entrypoint({
                "input": {"prompt": request.query}
            })
        elif request.districts and request.meal_types:
            # Use combined search
            result = await mcp_client.call_mcp_tool(
                "search_restaurants_combined",
                {
                    "districts": request.districts,
                    "meal_types": request.meal_types
                }
            )
        elif request.districts:
            # Use district search
            result = await mcp_client.call_mcp_tool(
                "search_restaurants_by_district",
                {"districts": request.districts}
            )
        elif request.meal_types:
            # Use meal type search
            result = await mcp_client.call_mcp_tool(
                "search_restaurants_by_meal_type",
                {"meal_types": request.meal_types}
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide districts, meal_types, or natural language query"
            )
        
        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"MCP tool error: {result['error']}"
            )
        
        # Parse MCP response
        restaurant_data = json.loads(result['data']['result']['content'])
        
        return RestaurantSearchResponse(
            success=True,
            restaurants=restaurant_data['restaurants'],
            total_count=restaurant_data['restaurant_count'],
            query_info={
                'districts': request.districts,
                'meal_types': request.meal_types,
                'query': request.query,
                'tool_used': result.get('tool_name')
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/health")
async def get_health_status():
    """Get system health status."""
    monitor = StatusMonitoringClient(
        base_url=os.getenv('MCP_BASE_URL'),
        jwt_token=os.getenv('MCP_JWT_TOKEN')
    )
    
    health = await monitor.get_system_health()
    return health
```

### Mobile App Integration

```python
class MobileAppMCPClient:
    """MCP client optimized for mobile applications."""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.offline_cache = {}
    
    async def search_restaurants_mobile(
        self,
        query: str,
        location: Optional[Dict[str, float]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mobile-optimized restaurant search."""
        try:
            # Enhance query with location context if available
            enhanced_query = query
            if location:
                enhanced_query += f" (near {location['lat']}, {location['lng']})"
            
            # Add user preferences to query
            if preferences:
                if preferences.get('dietary_restrictions'):
                    enhanced_query += f" with {', '.join(preferences['dietary_restrictions'])}"
                if preferences.get('price_range'):
                    enhanced_query += f" in {preferences['price_range']} price range"
            
            # Call entrypoint with enhanced query
            result = await self._call_with_fallback(
                method="entrypoint",
                payload={"input": {"prompt": enhanced_query}}
            )
            
            if result['success']:
                # Format for mobile consumption
                return self._format_mobile_response(result['data'])
            else:
                return self._get_fallback_response(query)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback_available': len(self.offline_cache) > 0
            }
    
    async def _call_with_fallback(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make request with offline fallback."""
        try:
            # Try online request first
            if method == "entrypoint":
                result = await self._call_entrypoint(payload)
            else:
                result = await self._call_mcp_tool(method, payload)
            
            # Cache successful results
            if result['success']:
                cache_key = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                self.offline_cache[cache_key] = {
                    'data': result,
                    'cached_at': datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            # Try offline cache
            cache_key = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            if cache_key in self.offline_cache:
                cached_result = self.offline_cache[cache_key]
                cached_result['data']['from_cache'] = True
                return cached_result['data']
            
            raise e
    
    def _format_mobile_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for mobile consumption."""
        # Parse restaurant data
        if 'result' in data and 'content' in data['result']:
            restaurant_data = json.loads(data['result']['content'])
            
            # Simplify for mobile
            mobile_restaurants = []
            for restaurant in restaurant_data.get('restaurants', []):
                mobile_restaurant = {
                    'id': restaurant['id'],
                    'name': restaurant['name'],
                    'address': restaurant['address'],
                    'cuisine': restaurant.get('meal_type', []),
                    'price_range': restaurant.get('price_range', 'Unknown'),
                    'rating': self._calculate_rating(restaurant.get('sentiment', {})),
                    'is_open_now': self._check_if_open_now(restaurant.get('operating_hours', {})),
                    'distance': None  # Would be calculated based on user location
                }
                mobile_restaurants.append(mobile_restaurant)
            
            return {
                'success': True,
                'restaurants': mobile_restaurants,
                'total_count': len(mobile_restaurants),
                'from_cache': data.get('from_cache', False)
            }
        
        return {'success': False, 'error': 'Invalid response format'}
    
    def _calculate_rating(self, sentiment: Dict[str, int]) -> float:
        """Calculate rating from sentiment data."""
        total = sentiment.get('likes', 0) + sentiment.get('dislikes', 0) + sentiment.get('neutral', 0)
        if total == 0:
            return 0.0
        
        likes = sentiment.get('likes', 0)
        return (likes / total) * 5.0  # Convert to 5-star rating
    
    def _check_if_open_now(self, operating_hours: Dict[str, List[str]]) -> bool:
        """Check if restaurant is currently open."""
        # Simplified implementation
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Check today's hours (simplified)
        today_hours = operating_hours.get('mon_fri', [])
        if now.weekday() >= 5:  # Weekend
            today_hours = operating_hours.get('sat_sun', [])
        
        for time_range in today_hours:
            if ' - ' in time_range:
                start_time, end_time = time_range.split(' - ')
                if start_time <= current_time <= end_time:
                    return True
        
        return False

# Usage in mobile app
mobile_client = MobileAppMCPClient(
    base_url="https://your-gateway-url",
    jwt_token=jwt_token
)

# Search with mobile context
result = await mobile_client.search_restaurants_mobile(
    query="Find good breakfast places",
    location={"lat": 22.2783, "lng": 114.1747},  # Hong Kong coordinates
    preferences={
        "dietary_restrictions": ["vegetarian"],
        "price_range": "budget"
    }
)
```

This comprehensive documentation provides detailed examples and patterns for integrating with the Restaurant Search MCP system, covering authentication, status monitoring, error handling, testing, and various integration scenarios. The examples demonstrate best practices for production use and provide a solid foundation for building applications that leverage the MCP tools effectively.