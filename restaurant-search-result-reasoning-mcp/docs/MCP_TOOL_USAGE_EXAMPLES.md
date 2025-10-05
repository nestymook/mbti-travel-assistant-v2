# MCP Tool Usage Examples and Integration Patterns

This document provides comprehensive examples for integrating the Restaurant Search MCP tools with different frameworks, including BedrockAgentCoreApp entrypoint integration, authentication patterns, parameter formats, and error handling strategies.

## Table of Contents

1. [BedrockAgentCoreApp Entrypoint Integration](#bedrockagentcoreapp-entrypoint-integration)
2. [Basic MCP Tool Usage](#basic-mcp-tool-usage)
3. [Framework Integration Patterns](#framework-integration-patterns)
4. [Authentication Integration](#authentication-integration)
5. [Parameter Formats and Validation](#parameter-formats-and-validation)
6. [Response Structures](#response-structures)
7. [Error Handling Examples](#error-handling-examples)
8. [Performance Optimization](#performance-optimization)
9. [Production Integration Patterns](#production-integration-patterns)

## BedrockAgentCoreApp Entrypoint Integration

The Restaurant Search MCP system uses BedrockAgentCoreApp entrypoint integration with Strands Agent framework for natural language processing and automatic MCP tool selection.

### Entrypoint Architecture Overview

```python
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

# Initialize the BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Create MCP tools for Strands Agent
def create_mcp_tools() -> list[Tool]:
    """Create MCP tools with proper schemas for automatic selection."""
    
    def search_restaurants_by_district(districts: list[str]) -> str:
        """Search for restaurants in specific districts."""
        # Implementation using RestaurantService
        pass
    
    def search_restaurants_by_meal_type(meal_types: list[str]) -> str:
        """Search for restaurants by meal type based on operating hours."""
        # Implementation using RestaurantService
        pass
    
    def search_restaurants_combined(districts: Optional[list[str]] = None, 
                                  meal_types: Optional[list[str]] = None) -> str:
        """Search for restaurants by both district and meal type."""
        # Implementation using RestaurantService
        pass
    
    # Create Tool objects with detailed schemas
    return [
        Tool(
            name="search_restaurants_by_district",
            description="Search for restaurants in specific Hong Kong districts...",
            function=search_restaurants_by_district,
            parameters={
                "type": "object",
                "properties": {
                    "districts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Hong Kong district names",
                        "minItems": 1
                    }
                },
                "required": ["districts"]
            }
        ),
        # ... other tools
    ]

# Configure Strands Agent
strands_agent = Agent(
    model="amazon.nova-pro-v1:0",
    system_prompt="You are a helpful Hong Kong restaurant search assistant...",
    tools=create_mcp_tools(),
    temperature=0.1,
    max_tokens=2048
)

@app.entrypoint
def process_request(payload: Dict[str, Any]) -> str:
    """Main entrypoint for processing AgentCore Runtime requests."""
    # Extract user prompt from payload
    user_prompt = extract_user_prompt(payload)
    
    # Process with Strands Agent (automatically selects MCP tools)
    agent_response = strands_agent.run(user_prompt)
    
    # Format and return JSON-serializable response
    return format_response(agent_response)

if __name__ == "__main__":
    app.run()
```

### Entrypoint Usage Examples

#### Basic Natural Language Queries

```python
#!/usr/bin/env python3
"""Examples of natural language queries processed by the entrypoint."""

import json
import requests
from services.auth_service import CognitoAuthenticator

def test_entrypoint_queries():
    """Test various natural language queries through the entrypoint."""
    
    # Set up authentication
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    tokens = authenticator.authenticate_user(
        config['test_user']['email'],
        "TempPass123!"
    )
    
    # AgentCore Runtime endpoint
    agentcore_url = "https://your-agentcore-endpoint.amazonaws.com/invocations"
    
    headers = {
        'Authorization': f'Bearer {tokens.access_token}',
        'Content-Type': 'application/json'
    }
    
    # Test queries with expected tool selections
    test_cases = [
        {
            "query": "Find restaurants in Central district",
            "expected_tool": "search_restaurants_by_district",
            "expected_params": {"districts": ["Central district"]}
        },
        {
            "query": "Show me breakfast places in Hong Kong",
            "expected_tool": "search_restaurants_by_meal_type",
            "expected_params": {"meal_types": ["breakfast"]}
        },
        {
            "query": "I want dinner restaurants in Tsim Sha Tsui",
            "expected_tool": "search_restaurants_combined",
            "expected_params": {
                "districts": ["Tsim Sha Tsui"],
                "meal_types": ["dinner"]
            }
        },
        {
            "query": "What lunch options are available in Causeway Bay and Admiralty?",
            "expected_tool": "search_restaurants_combined",
            "expected_params": {
                "districts": ["Causeway Bay", "Admiralty"],
                "meal_types": ["lunch"]
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['query']}")
        print(f"Expected tool: {test_case['expected_tool']}")
        
        payload = {
            "input": {
                "prompt": test_case['query']
            }
        }
        
        try:
            response = requests.post(agentcore_url, headers=headers, json=payload)
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Success: {result['response'][:100]}...")
            else:
                print(f"❌ Error: {result.get('error', {}).get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_entrypoint_queries()
```

#### Advanced Entrypoint Integration

```python
#!/usr/bin/env python3
"""Advanced entrypoint integration with error handling and response processing."""

import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from services.auth_service import CognitoAuthenticator

class RestaurantSearchEntrypointClient:
    """Advanced client for BedrockAgentCoreApp entrypoint integration."""
    
    def __init__(self, agentcore_url: str, cognito_config: Dict[str, Any]):
        """Initialize the entrypoint client."""
        self.agentcore_url = agentcore_url
        self.cognito_config = cognito_config
        self.authenticator = CognitoAuthenticator(
            user_pool_id=cognito_config['user_pool']['user_pool_id'],
            client_id=cognito_config['app_client']['client_id'],
            region=cognito_config['region']
        )
        self.access_token: Optional[str] = None
    
    async def authenticate(self) -> bool:
        """Authenticate and get access token."""
        try:
            tokens = self.authenticator.authenticate_user(
                self.cognito_config['test_user']['email'],
                "TempPass123!"
            )
            self.access_token = tokens.access_token
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    async def query_restaurants(self, prompt: str, 
                              session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send natural language query to entrypoint."""
        
        if not self.access_token:
            if not await self.authenticate():
                return {"success": False, "error": "Authentication failed"}
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "input": {
                "prompt": prompt
            }
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agentcore_url}/invocations",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return self._process_response(result)
                    elif response.status == 401:
                        # Token expired, try to refresh
                        if await self.authenticate():
                            return await self.query_restaurants(prompt, session_id)
                        else:
                            return {"success": False, "error": "Authentication failed"}
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        
        except Exception as e:
            return {"success": False, "error": f"Request failed: {e}"}
    
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enhance the entrypoint response."""
        
        if not response.get('success'):
            return response
        
        # Extract restaurant data if present in the response
        response_text = response.get('response', '')
        
        # Try to extract structured data from the response
        restaurants = self._extract_restaurant_data(response_text)
        
        enhanced_response = {
            "success": True,
            "response": response_text,
            "metadata": response.get('metadata', {}),
            "timestamp": response.get('timestamp'),
            "extracted_data": {
                "restaurant_count": len(restaurants),
                "restaurants": restaurants
            }
        }
        
        return enhanced_response
    
    def _extract_restaurant_data(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract structured restaurant data from response text."""
        # This is a simplified extraction - in production, you might use
        # more sophisticated parsing or have the agent return structured data
        
        restaurants = []
        lines = response_text.split('\n')
        
        current_restaurant = {}
        for line in lines:
            line = line.strip()
            
            # Look for restaurant names (assuming they're in bold markdown)
            if line.startswith('**') and line.endswith('**'):
                if current_restaurant:
                    restaurants.append(current_restaurant)
                current_restaurant = {
                    'name': line.strip('*'),
                    'details': []
                }
            elif line and current_restaurant:
                current_restaurant['details'].append(line)
        
        if current_restaurant:
            restaurants.append(current_restaurant)
        
        return restaurants

async def advanced_entrypoint_example():
    """Demonstrate advanced entrypoint integration."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        cognito_config = json.load(f)
    
    # Initialize client
    agentcore_url = "https://your-agentcore-endpoint.amazonaws.com"
    client = RestaurantSearchEntrypointClient(agentcore_url, cognito_config)
    
    # Test conversational queries
    conversation_queries = [
        "Hi! I'm looking for a good breakfast place in Central district",
        "What about lunch options in the same area?",
        "Can you suggest some dinner restaurants in Tsim Sha Tsui instead?",
        "Are there any vegetarian options among those restaurants?"
    ]
    
    session_id = "test_session_123"
    
    for i, query in enumerate(conversation_queries, 1):
        print(f"\n💬 Query {i}: {query}")
        
        result = await client.query_restaurants(query, session_id)
        
        if result['success']:
            print(f"✅ Response: {result['response'][:200]}...")
            
            extracted_data = result['extracted_data']
            print(f"📊 Found {extracted_data['restaurant_count']} restaurants")
            
            for restaurant in extracted_data['restaurants'][:2]:  # Show first 2
                print(f"   🍽️ {restaurant['name']}")
        else:
            print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(advanced_entrypoint_example())
```

### Entrypoint Error Handling Examples

```python
#!/usr/bin/env python3
"""Error handling examples for entrypoint integration."""

import json
from typing import Dict, Any

def handle_entrypoint_errors(response: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive error handling for entrypoint responses."""
    
    if response.get('success'):
        return response
    
    error = response.get('error', {})
    error_type = error.get('type', 'unknown_error')
    error_message = error.get('message', 'Unknown error occurred')
    
    # Handle different error types
    if error_type == 'validation_error':
        return {
            "success": False,
            "user_message": "I couldn't understand your request. Please try asking about restaurants in a specific Hong Kong district or meal type.",
            "suggestions": [
                "Try: 'Find restaurants in Central district'",
                "Try: 'Show me breakfast places'",
                "Try: 'Dinner options in Tsim Sha Tsui'"
            ],
            "error_details": error
        }
    
    elif error_type == 'processing_error':
        return {
            "success": False,
            "user_message": "I'm having trouble processing your request. Could you please rephrase it?",
            "suggestions": [
                "Be more specific about the location",
                "Mention a meal type (breakfast, lunch, dinner)",
                "Try a simpler query"
            ],
            "error_details": error
        }
    
    elif error_type == 'system_error':
        return {
            "success": False,
            "user_message": "I'm experiencing technical difficulties. Please try again in a moment.",
            "suggestions": [
                "Wait a few seconds and try again",
                "Check your internet connection",
                "Try a different query"
            ],
            "error_details": error
        }
    
    elif error_type == 'authentication_error':
        return {
            "success": False,
            "user_message": "Authentication failed. Please log in again.",
            "suggestions": [
                "Check your credentials",
                "Ensure your session hasn't expired",
                "Contact support if the problem persists"
            ],
            "error_details": error
        }
    
    else:
        return {
            "success": False,
            "user_message": "An unexpected error occurred. Please try again.",
            "suggestions": [
                "Try rephrasing your question",
                "Contact support if the problem persists"
            ],
            "error_details": error
        }

def test_error_scenarios():
    """Test various error scenarios and their handling."""
    
    error_scenarios = [
        {
            "name": "Invalid payload structure",
            "response": {
                "success": False,
                "error": {
                    "type": "validation_error",
                    "message": "No valid prompt found in payload"
                }
            }
        },
        {
            "name": "Agent processing failure",
            "response": {
                "success": False,
                "error": {
                    "type": "processing_error",
                    "message": "Agent failed to process the request"
                }
            }
        },
        {
            "name": "System error",
            "response": {
                "success": False,
                "error": {
                    "type": "system_error",
                    "message": "Internal server error"
                }
            }
        }
    ]
    
    for scenario in error_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        
        handled_error = handle_entrypoint_errors(scenario['response'])
        
        print(f"User Message: {handled_error['user_message']}")
        print(f"Suggestions: {handled_error['suggestions']}")

if __name__ == "__main__":
    test_error_scenarios()
```

### Entrypoint Response Format Examples

```python
#!/usr/bin/env python3
"""Examples of entrypoint response formats and processing."""

import json
from typing import Dict, Any

def example_successful_response() -> Dict[str, Any]:
    """Example of a successful entrypoint response."""
    return {
        "success": True,
        "response": """I found 5 restaurants in Central district for breakfast:

**Maxim's Palace** - Shop 2-5, 2/F, City Hall Low Block, Edinburgh Place
District: Central district, Price: $$, Cuisine: Dim Sum, Cantonese
Hours: Mon-Fri 8:00-11:30, Sat-Sun 7:30-11:30

**Australian Dairy Company** - G/F, 47-49 Parkes Street, Jordan
District: Central district, Price: $, Cuisine: Western, Hong Kong Style
Hours: Mon-Fri 7:30-11:00, Sat-Sun 7:30-11:30

**Lan Fong Yuen** - 2 Gage Street, Central
District: Central district, Price: $, Cuisine: Hong Kong Style, Tea Restaurant
Hours: Mon-Fri 7:00-18:00, Sat 7:00-17:00

Would you like more details about any of these restaurants or search in a different area?""",
        "timestamp": "2025-09-27T10:30:00.000Z",
        "agent_type": "restaurant_search_assistant",
        "version": "2.0.0",
        "metadata": {
            "prompt_length": 45,
            "processing_time": "completed",
            "tools_available": [
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ]
        }
    }

def example_error_response() -> Dict[str, Any]:
    """Example of an error entrypoint response."""
    return {
        "success": False,
        "response": "I don't recognize 'InvalidDistrict' as a Hong Kong district. Could you try a well-known Hong Kong district like Central district, Tsim Sha Tsui, or Causeway Bay?",
        "error": {
            "message": "Invalid districts: ['InvalidDistrict']",
            "type": "validation_error",
            "user_message": "I don't recognize that district name. Could you try a well-known Hong Kong district like Central district, Tsim Sha Tsui, or Causeway Bay?"
        },
        "timestamp": "2025-09-27T10:30:00.000Z",
        "agent_type": "restaurant_search_assistant",
        "suggestions": [
            "Try asking about restaurants in a specific Hong Kong district",
            "Specify a meal type: breakfast, lunch, or dinner",
            "Use district names like 'Central district' or 'Tsim Sha Tsui'"
        ]
    }

def process_entrypoint_response(response: Dict[str, Any]) -> None:
    """Process and display entrypoint response."""
    
    print(f"Success: {response['success']}")
    print(f"Timestamp: {response.get('timestamp', 'N/A')}")
    
    if response['success']:
        print(f"Response: {response['response']}")
        
        metadata = response.get('metadata', {})
        if metadata:
            print(f"Metadata:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
    
    else:
        print(f"Error Response: {response['response']}")
        
        error = response.get('error', {})
        if error:
            print(f"Error Details:")
            print(f"  Type: {error.get('type', 'unknown')}")
            print(f"  Message: {error.get('message', 'No message')}")
        
        suggestions = response.get('suggestions', [])
        if suggestions:
            print(f"Suggestions:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")

def main():
    """Demonstrate response processing."""
    
    print("🟢 Successful Response Example:")
    print("=" * 50)
    success_response = example_successful_response()
    process_entrypoint_response(success_response)
    
    print("\n🔴 Error Response Example:")
    print("=" * 50)
    error_response = example_error_response()
    process_entrypoint_response(error_response)

if __name__ == "__main__":
    main()
```

## Basic MCP Tool Usage

### Simple MCP Client Example

```python
#!/usr/bin/env python3
"""Basic MCP client example for restaurant search tools."""

import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def basic_mcp_example():
    """Demonstrate basic MCP tool usage without authentication."""
    
    # MCP server URL (local development)
    mcp_url = "http://localhost:8080"
    
    # Basic headers
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Connect to MCP server
        async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()
                print("✅ MCP session initialized")
                
                # List available tools
                tools_response = await session.list_tools()
                available_tools = [tool.name for tool in tools_response.tools]
                print(f"📋 Available tools: {available_tools}")
                
                # Example 1: Search by district
                print("\n🔍 Example 1: Search restaurants by district")
                result = await session.call_tool(
                    "search_restaurants_by_district",
                    {"districts": ["Central district"]}
                )
                
                response_data = json.loads(result.content[0].text)
                print(f"Found {response_data['data']['count']} restaurants")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(basic_mcp_example())
```
###
 Authenticated MCP Client Example

```python
#!/usr/bin/env python3
"""Authenticated MCP client example with JWT tokens."""

import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

async def authenticated_mcp_example():
    """Demonstrate MCP tool usage with JWT authentication."""
    
    # Load Cognito configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize authenticator
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    try:
        # Authenticate and get tokens
        print("🔐 Authenticating...")
        tokens = authenticator.authenticate_user(
            config['test_user']['email'],
            "TempPass123!"  # Use actual password
        )
        
        # Set up authenticated headers
        headers = {
            'Authorization': f'Bearer {tokens.access_token}',
            'Content-Type': 'application/json'
        }
        
        # AgentCore Runtime URL (from deployment)
        mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
        
        # Connect with authentication
        async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ Authenticated MCP session initialized")
                
                # Test all three tools
                await test_district_search(session)
                await test_meal_type_search(session)
                await test_combined_search(session)
                
    except Exception as e:
        print(f"❌ Authentication or MCP error: {e}")

async def test_district_search(session):
    """Test district-based restaurant search."""
    print("\n🏙️ Testing District Search")
    
    test_cases = [
        {"districts": ["Central district"]},
        {"districts": ["Tsim Sha Tsui", "Admiralty"]},
        {"districts": ["Causeway Bay", "Wan Chai", "Mong Kok"]}
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {params}")
        try:
            result = await session.call_tool(
                "search_restaurants_by_district",
                params
            )
            
            response_data = json.loads(result.content[0].text)
            if response_data['success']:
                count = response_data['data']['count']
                districts = ', '.join(params['districts'])
                print(f"    ✅ Found {count} restaurants in {districts}")
            else:
                print(f"    ❌ Error: {response_data['error']['message']}")
                
        except Exception as e:
            print(f"    ❌ Exception: {e}")

async def test_meal_type_search(session):
    """Test meal type-based restaurant search."""
    print("\n🍽️ Testing Meal Type Search")
    
    test_cases = [
        {"meal_types": ["breakfast"]},
        {"meal_types": ["lunch", "dinner"]},
        {"meal_types": ["breakfast", "lunch", "dinner"]}
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {params}")
        try:
            result = await session.call_tool(
                "search_restaurants_by_meal_type",
                params
            )
            
            response_data = json.loads(result.content[0].text)
            if response_data['success']:
                count = response_data['data']['count']
                meal_types = ', '.join(params['meal_types'])
                print(f"    ✅ Found {count} restaurants serving {meal_types}")
            else:
                print(f"    ❌ Error: {response_data['error']['message']}")
                
        except Exception as e:
            print(f"    ❌ Exception: {e}")

async def test_combined_search(session):
    """Test combined district and meal type search."""
    print("\n🔍 Testing Combined Search")
    
    test_cases = [
        {
            "districts": ["Central district"],
            "meal_types": ["breakfast"]
        },
        {
            "districts": ["Tsim Sha Tsui", "Causeway Bay"],
            "meal_types": ["lunch", "dinner"]
        },
        {
            "districts": ["Admiralty"]
        },
        {
            "meal_types": ["dinner"]
        }
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {params}")
        try:
            result = await session.call_tool(
                "search_restaurants_combined",
                params
            )
            
            response_data = json.loads(result.content[0].text)
            if response_data['success']:
                count = response_data['data']['count']
                criteria = []
                if 'districts' in params:
                    criteria.append(f"districts: {', '.join(params['districts'])}")
                if 'meal_types' in params:
                    criteria.append(f"meal types: {', '.join(params['meal_types'])}")
                
                print(f"    ✅ Found {count} restaurants ({'; '.join(criteria)})")
            else:
                print(f"    ❌ Error: {response_data['error']['message']}")
                
        except Exception as e:
            print(f"    ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(authenticated_mcp_example())
```

## Framework Integration Patterns

### LangChain Integration

```python
#!/usr/bin/env python3
"""LangChain integration with Restaurant Search MCP tools."""

import asyncio
import json
from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

class RestaurantSearchTool(BaseTool):
    """LangChain tool wrapper for Restaurant Search MCP."""
    
    name: str = "restaurant_search"
    description: str = """Search for restaurants in Hong Kong by district and/or meal type.
    
    Parameters:
    - districts (optional): List of district names (e.g., ["Central district", "Tsim Sha Tsui"])
    - meal_types (optional): List of meal types (e.g., ["breakfast", "lunch", "dinner"])
    
    Examples:
    - Search by district: {"districts": ["Central district"]}
    - Search by meal type: {"meal_types": ["breakfast"]}
    - Combined search: {"districts": ["Tsim Sha Tsui"], "meal_types": ["dinner"]}
    """
    
    def __init__(self, mcp_url: str, auth_token: str):
        super().__init__()
        self.mcp_url = mcp_url
        self.auth_token = auth_token
    
    def _run(self, districts: Optional[List[str]] = None, 
             meal_types: Optional[List[str]] = None) -> str:
        """Execute restaurant search synchronously."""
        return asyncio.run(self._arun(districts, meal_types))
    
    async def _arun(self, districts: Optional[List[str]] = None, 
                    meal_types: Optional[List[str]] = None) -> str:
        """Execute restaurant search asynchronously."""
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Determine which tool to use based on parameters
                    if districts and meal_types:
                        # Use combined search
                        result = await session.call_tool(
                            "search_restaurants_combined",
                            {"districts": districts, "meal_types": meal_types}
                        )
                    elif districts:
                        # Use district search
                        result = await session.call_tool(
                            "search_restaurants_by_district",
                            {"districts": districts}
                        )
                    elif meal_types:
                        # Use meal type search
                        result = await session.call_tool(
                            "search_restaurants_by_meal_type",
                            {"meal_types": meal_types}
                        )
                    else:
                        return "Error: At least one of 'districts' or 'meal_types' must be provided"
                    
                    # Parse and format response
                    response_data = json.loads(result.content[0].text)
                    
                    if response_data['success']:
                        restaurants = response_data['data']['restaurants']
                        count = response_data['data']['count']
                        
                        if count == 0:
                            return "No restaurants found matching the specified criteria."
                        
                        # Format response for LangChain
                        formatted_results = []
                        for restaurant in restaurants[:5]:  # Limit to top 5 results
                            formatted_results.append(
                                f"**{restaurant['name']}** - {restaurant['address']}\n"
                                f"District: {restaurant['district']}, "
                                f"Price: {restaurant['price_range']}, "
                                f"Cuisine: {', '.join(restaurant['meal_type'])}"
                            )
                        
                        summary = f"Found {count} restaurants"
                        if districts:
                            summary += f" in {', '.join(districts)}"
                        if meal_types:
                            summary += f" serving {', '.join(meal_types)}"
                        
                        return f"{summary}:\n\n" + "\n\n".join(formatted_results)
                    
                    else:
                        return f"Search failed: {response_data['error']['message']}"
        
        except Exception as e:
            return f"Error connecting to restaurant search service: {e}"

async def langchain_integration_example():
    """Demonstrate LangChain integration with Restaurant Search MCP."""
    
    # Set up authentication
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Get authentication token
    tokens = authenticator.authenticate_user(
        config['test_user']['email'],
        "TempPass123!"
    )
    
    # Create restaurant search tool
    mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
    restaurant_tool = RestaurantSearchTool(mcp_url, tokens.access_token)
    
    # Set up LangChain agent
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [restaurant_tool]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful Hong Kong restaurant recommendation assistant. 
        You have access to a restaurant search tool that can find restaurants by district and meal type.
        
        Available districts include: Central district, Tsim Sha Tsui, Admiralty, Causeway Bay, Wan Chai, Mong Kok, etc.
        Available meal types: breakfast, lunch, dinner
        
        When users ask about restaurants, use the restaurant search tool to find relevant options and provide helpful recommendations."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # Test queries
    test_queries = [
        "Find me some good breakfast places in Central district",
        "What dinner restaurants are available in Tsim Sha Tsui?",
        "I'm looking for lunch options in Causeway Bay or Admiralty",
        "Show me restaurants in Mong Kok"
    ]
    
    for query in test_queries:
        print(f"\n🤖 Query: {query}")
        print("=" * 50)
        
        try:
            response = agent_executor.invoke({"input": query})
            print(f"Response: {response['output']}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(langchain_integration_example())
```### C
rewAI Integration

```python
#!/usr/bin/env python3
"""CrewAI integration with Restaurant Search MCP tools."""

import asyncio
import json
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Tool
from crewai_tools import BaseTool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

class RestaurantSearchCrewTool(BaseTool):
    """CrewAI tool for restaurant search."""
    
    name: str = "Restaurant Search"
    description: str = """Search for restaurants in Hong Kong by district and meal type.
    Use this tool to find restaurants based on location (district) and/or dining time (meal type).
    
    Parameters should be provided as a JSON string with:
    - districts (optional): List of district names
    - meal_types (optional): List of meal types (breakfast, lunch, dinner)
    """
    
    def __init__(self, mcp_url: str, auth_token: str):
        super().__init__()
        self.mcp_url = mcp_url
        self.auth_token = auth_token
    
    def _run(self, query: str) -> str:
        """Execute restaurant search."""
        try:
            # Parse query parameters
            params = json.loads(query)
            districts = params.get('districts')
            meal_types = params.get('meal_types')
            
            return asyncio.run(self._search_restaurants(districts, meal_types))
            
        except json.JSONDecodeError:
            return "Error: Query must be valid JSON with 'districts' and/or 'meal_types' parameters"
        except Exception as e:
            return f"Error: {e}"
    
    async def _search_restaurants(self, districts: Optional[List[str]], 
                                 meal_types: Optional[List[str]]) -> str:
        """Perform the actual restaurant search."""
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Choose appropriate MCP tool
                    if districts and meal_types:
                        result = await session.call_tool(
                            "search_restaurants_combined",
                            {"districts": districts, "meal_types": meal_types}
                        )
                    elif districts:
                        result = await session.call_tool(
                            "search_restaurants_by_district",
                            {"districts": districts}
                        )
                    elif meal_types:
                        result = await session.call_tool(
                            "search_restaurants_by_meal_type",
                            {"meal_types": meal_types}
                        )
                    else:
                        return "At least one search parameter (districts or meal_types) is required"
                    
                    # Process response
                    response_data = json.loads(result.content[0].text)
                    
                    if response_data['success']:
                        restaurants = response_data['data']['restaurants']
                        count = response_data['data']['count']
                        
                        if count == 0:
                            return "No restaurants found matching the criteria"
                        
                        # Format for CrewAI agent
                        result_summary = f"Found {count} restaurants:\n\n"
                        
                        for restaurant in restaurants[:3]:  # Top 3 results
                            result_summary += (
                                f"• {restaurant['name']}\n"
                                f"  Address: {restaurant['address']}\n"
                                f"  District: {restaurant['district']}\n"
                                f"  Cuisine: {', '.join(restaurant['meal_type'])}\n"
                                f"  Price Range: {restaurant['price_range']}\n\n"
                            )
                        
                        return result_summary
                    
                    else:
                        return f"Search failed: {response_data['error']['message']}"
        
        except Exception as e:
            return f"Connection error: {e}"

async def crewai_integration_example():
    """Demonstrate CrewAI integration with Restaurant Search MCP."""
    
    # Set up authentication
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    tokens = authenticator.authenticate_user(
        config['test_user']['email'],
        "TempPass123!"
    )
    
    # Create restaurant search tool
    mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
    restaurant_tool = RestaurantSearchCrewTool(mcp_url, tokens.access_token)
    
    # Define CrewAI agents
    restaurant_researcher = Agent(
        role='Restaurant Researcher',
        goal='Find the best restaurants based on user preferences',
        backstory="""You are an expert in Hong Kong's dining scene with extensive knowledge 
        of restaurants across different districts and meal types. You use the restaurant search 
        tool to find relevant options and provide detailed recommendations.""",
        tools=[restaurant_tool],
        verbose=True
    )
    
    recommendation_specialist = Agent(
        role='Recommendation Specialist',
        goal='Provide personalized restaurant recommendations',
        backstory="""You specialize in analyzing restaurant data and creating personalized 
        recommendations based on user preferences, location, and dining requirements.""",
        verbose=True
    )
    
    # Define tasks
    research_task = Task(
        description="""Research restaurants in {district} that serve {meal_type}. 
        Use the restaurant search tool to find options and gather detailed information 
        about each restaurant including cuisine type, price range, and location details.""",
        agent=restaurant_researcher,
        expected_output="A comprehensive list of restaurants with detailed information"
    )
    
    recommendation_task = Task(
        description="""Based on the research findings, create personalized restaurant 
        recommendations. Consider factors like cuisine variety, price range, and location 
        convenience. Provide the top 3 recommendations with explanations.""",
        agent=recommendation_specialist,
        expected_output="Top 3 restaurant recommendations with detailed explanations"
    )
    
    # Create crew
    restaurant_crew = Crew(
        agents=[restaurant_researcher, recommendation_specialist],
        tasks=[research_task, recommendation_task],
        verbose=True
    )
    
    # Test scenarios
    test_scenarios = [
        {"district": "Central district", "meal_type": "breakfast"},
        {"district": "Tsim Sha Tsui", "meal_type": "dinner"},
        {"district": "Causeway Bay", "meal_type": "lunch"}
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 Scenario: {scenario}")
        print("=" * 60)
        
        try:
            result = restaurant_crew.kickoff(inputs=scenario)
            print(f"Crew Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(crewai_integration_example())
```

### Strands Agents Integration

```python
#!/usr/bin/env python3
"""Strands Agents integration with Restaurant Search MCP tools."""

import asyncio
import json
from typing import List, Dict, Any, Optional
from strands import Agent, tool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

class RestaurantSearchStrandsTool(Tool):
    """Strands Agents tool for restaurant search."""
    
    def __init__(self, mcp_url: str, auth_token: str):
        super().__init__(
            name="restaurant_search",
            description="""Search for restaurants in Hong Kong by district and/or meal type.
            
            Parameters:
            - districts: List of district names (optional)
            - meal_types: List of meal types - breakfast, lunch, dinner (optional)
            
            At least one parameter must be provided."""
        )
        self.mcp_url = mcp_url
        self.auth_token = auth_token
    
    async def execute(self, districts: Optional[List[str]] = None, 
                     meal_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute restaurant search via MCP."""
        
        if not districts and not meal_types:
            return {
                "success": False,
                "error": "At least one parameter (districts or meal_types) is required"
            }
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Select appropriate MCP tool
                    if districts and meal_types:
                        result = await session.call_tool(
                            "search_restaurants_combined",
                            {"districts": districts, "meal_types": meal_types}
                        )
                    elif districts:
                        result = await session.call_tool(
                            "search_restaurants_by_district",
                            {"districts": districts}
                        )
                    else:  # meal_types only
                        result = await session.call_tool(
                            "search_restaurants_by_meal_type",
                            {"meal_types": meal_types}
                        )
                    
                    # Parse and return response
                    response_data = json.loads(result.content[0].text)
                    return response_data
        
        except Exception as e:
            return {
                "success": False,
                "error": f"MCP connection error: {e}"
            }

class RestaurantRecommendationAgent(Agent):
    """Strands agent for restaurant recommendations."""
    
    def __init__(self, mcp_url: str, auth_token: str):
        self.restaurant_tool = RestaurantSearchStrandsTool(mcp_url, auth_token)
        
        super().__init__(
            name="restaurant_recommendation_agent",
            description="Provides restaurant recommendations in Hong Kong",
            tools=[self.restaurant_tool]
        )
    
    async def process_request(self, user_request: str) -> str:
        """Process user restaurant request."""
        
        # Simple intent parsing (in production, use more sophisticated NLP)
        districts = self._extract_districts(user_request)
        meal_types = self._extract_meal_types(user_request)
        
        if not districts and not meal_types:
            return """I'd be happy to help you find restaurants! Please specify:
            - A district (e.g., Central district, Tsim Sha Tsui, Causeway Bay)
            - A meal type (breakfast, lunch, or dinner)
            - Or both for more specific results"""
        
        # Search for restaurants
        search_result = await self.restaurant_tool.execute(
            districts=districts,
            meal_types=meal_types
        )
        
        if not search_result['success']:
            return f"Sorry, I encountered an error: {search_result['error']}"
        
        restaurants = search_result['data']['restaurants']
        count = search_result['data']['count']
        
        if count == 0:
            return "I couldn't find any restaurants matching your criteria. Try different districts or meal types."
        
        # Format recommendations
        response = f"I found {count} restaurants for you:\n\n"
        
        for i, restaurant in enumerate(restaurants[:5], 1):
            response += (
                f"{i}. **{restaurant['name']}**\n"
                f"   📍 {restaurant['address']}\n"
                f"   🏙️ District: {restaurant['district']}\n"
                f"   🍽️ Cuisine: {', '.join(restaurant['meal_type'])}\n"
                f"   💰 Price: {restaurant['price_range']}\n"
            )
            
            # Add operating hours if available
            if restaurant['operating_hours']:
                hours = restaurant['operating_hours']
                if hours.get('mon_fri'):
                    response += f"   ⏰ Mon-Fri: {', '.join(hours['mon_fri'])}\n"
            
            response += "\n"
        
        return response
    
    def _extract_districts(self, text: str) -> Optional[List[str]]:
        """Extract district names from user text."""
        # Simple keyword matching (in production, use NER or more sophisticated parsing)
        known_districts = [
            "Central district", "Admiralty", "Causeway Bay", "Wan Chai",
            "Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Jordan",
            "Sha Tin", "Tsuen Wan", "Tai Po", "Tung Chung"
        ]
        
        found_districts = []
        text_lower = text.lower()
        
        for district in known_districts:
            if district.lower() in text_lower:
                found_districts.append(district)
        
        return found_districts if found_districts else None
    
    def _extract_meal_types(self, text: str) -> Optional[List[str]]:
        """Extract meal types from user text."""
        meal_keywords = {
            "breakfast": ["breakfast", "morning", "brunch"],
            "lunch": ["lunch", "afternoon", "midday"],
            "dinner": ["dinner", "evening", "night"]
        }
        
        found_meal_types = []
        text_lower = text.lower()
        
        for meal_type, keywords in meal_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_meal_types.append(meal_type)
        
        return found_meal_types if found_meal_types else None

async def strands_integration_example():
    """Demonstrate Strands Agents integration."""
    
    # Set up authentication
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    tokens = authenticator.authenticate_user(
        config['test_user']['email'],
        "TempPass123!"
    )
    
    # Create restaurant recommendation agent
    mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
    agent = RestaurantRecommendationAgent(mcp_url, tokens.access_token)
    
    # Test user requests
    test_requests = [
        "I'm looking for breakfast places in Central district",
        "Can you recommend dinner restaurants in Tsim Sha Tsui?",
        "What lunch options are available in Causeway Bay?",
        "Find me restaurants in Admiralty",
        "I want Chinese food for dinner"
    ]
    
    for request in test_requests:
        print(f"\n👤 User: {request}")
        print("🤖 Agent:", end=" ")
        
        try:
            response = await agent.process_request(request)
            print(response)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(strands_integration_example())
```#
# Authentication Integration

### JWT Token Management

```python
#!/usr/bin/env python3
"""JWT token management for MCP client integration."""

import json
import time
from typing import Optional, Dict, Any
from services.auth_service import CognitoAuthenticator, AuthenticationError

class MCPAuthenticationManager:
    """Manages JWT authentication for MCP clients."""
    
    def __init__(self, config_file: str = 'cognito_config.json'):
        """Initialize authentication manager."""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.config['user_pool']['user_pool_id'],
            client_id=self.config['app_client']['client_id'],
            region=self.config['region']
        )
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
    
    async def get_valid_token(self, username: str = None, password: str = None) -> str:
        """Get a valid access token, refreshing if necessary."""
        
        # Check if current token is still valid
        if self.access_token and self.token_expires_at:
            # Add 5-minute buffer before expiration
            if time.time() < self.token_expires_at - 300:
                return self.access_token
        
        # Try to refresh token if available
        if self.refresh_token:
            try:
                print("🔄 Refreshing access token...")
                new_tokens = self.authenticator.refresh_token(self.refresh_token)
                
                self.access_token = new_tokens.access_token
                self.token_expires_at = time.time() + new_tokens.expires_in
                
                print("✅ Token refreshed successfully")
                return self.access_token
                
            except AuthenticationError as e:
                print(f"⚠️ Token refresh failed: {e.message}")
                # Fall through to full authentication
        
        # Perform full authentication
        if not username or not password:
            # Use test user credentials
            username = self.config['test_user']['email']
            password = "TempPass123!"  # Use actual password
        
        print("🔐 Performing full authentication...")
        tokens = self.authenticator.authenticate_user(username, password)
        
        self.access_token = tokens.access_token
        self.refresh_token = tokens.refresh_token
        self.token_expires_at = time.time() + tokens.expires_in
        
        print("✅ Authentication successful")
        return self.access_token
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authentication headers for MCP requests."""
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def handle_auth_error(self, error: Exception) -> bool:
        """Handle authentication errors and determine if retry is possible."""
        error_str = str(error).lower()
        
        if any(keyword in error_str for keyword in ['401', 'unauthorized', 'token']):
            print("🔄 Authentication error detected, clearing tokens...")
            self.access_token = None
            self.token_expires_at = None
            return True  # Retry possible
        
        return False  # No retry

# Usage example
async def authenticated_mcp_with_token_management():
    """Example using authentication manager."""
    
    auth_manager = MCPAuthenticationManager()
    
    # Get valid token
    token = await auth_manager.get_valid_token()
    headers = auth_manager.get_auth_headers(token)
    
    # Use with MCP client
    mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
    
    try:
        async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Make MCP calls...
                result = await session.call_tool(
                    "search_restaurants_by_district",
                    {"districts": ["Central district"]}
                )
                
                print("✅ MCP call successful")
                
    except Exception as e:
        if auth_manager.handle_auth_error(e):
            # Retry with new token
            token = await auth_manager.get_valid_token()
            headers = auth_manager.get_auth_headers(token)
            # Retry MCP call...
```

### Error Handling with Authentication

```python
#!/usr/bin/env python3
"""Comprehensive error handling for authenticated MCP clients."""

import asyncio
import json
from typing import Dict, Any, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator, AuthenticationError

class AuthenticatedMCPClient:
    """MCP client with comprehensive error handling and authentication."""
    
    def __init__(self, config_file: str = 'cognito_config.json'):
        """Initialize authenticated MCP client."""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.config['user_pool']['user_pool_id'],
            client_id=self.config['app_client']['client_id'],
            region=self.config['region']
        )
        
        self.access_token: Optional[str] = None
        self.max_retries = 3
    
    async def call_mcp_tool_with_retry(self, mcp_url: str, tool_name: str, 
                                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool with authentication and retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                # Ensure we have a valid token
                if not self.access_token:
                    await self._authenticate()
                
                # Set up headers
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Make MCP call
                async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(tool_name, parameters)
                        response_data = json.loads(result.content[0].text)
                        
                        return {
                            'success': True,
                            'data': response_data,
                            'attempt': attempt + 1
                        }
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Handle authentication errors
                if any(keyword in error_str for keyword in ['401', 'unauthorized', 'forbidden']):
                    print(f"🔄 Authentication error on attempt {attempt + 1}: {e}")
                    self.access_token = None  # Clear invalid token
                    
                    if attempt < self.max_retries - 1:
                        print("Retrying with new authentication...")
                        continue
                
                # Handle network errors
                elif any(keyword in error_str for keyword in ['connection', 'timeout', 'network']):
                    print(f"🌐 Network error on attempt {attempt + 1}: {e}")
                    
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                
                # Handle MCP protocol errors
                elif 'mcp' in error_str or 'protocol' in error_str:
                    print(f"📡 MCP protocol error: {e}")
                    return {
                        'success': False,
                        'error': 'MCP_PROTOCOL_ERROR',
                        'message': str(e),
                        'retry_recommended': False
                    }
                
                # Handle other errors
                else:
                    print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                    
                    if attempt < self.max_retries - 1:
                        continue
        
        # All retries exhausted
        return {
            'success': False,
            'error': 'MAX_RETRIES_EXCEEDED',
            'message': f'Failed after {self.max_retries} attempts',
            'retry_recommended': True
        }
    
    async def _authenticate(self) -> None:
        """Perform authentication and get access token."""
        try:
            print("🔐 Authenticating with Cognito...")
            tokens = self.authenticator.authenticate_user(
                self.config['test_user']['email'],
                "TempPass123!"  # Use actual password
            )
            
            self.access_token = tokens.access_token
            print("✅ Authentication successful")
            
        except AuthenticationError as e:
            print(f"❌ Authentication failed: {e.message}")
            raise
    
    async def search_restaurants_with_error_handling(self, mcp_url: str, 
                                                   districts: Optional[list] = None,
                                                   meal_types: Optional[list] = None) -> Dict[str, Any]:
        """Search restaurants with comprehensive error handling."""
        
        # Validate parameters
        if not districts and not meal_types:
            return {
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'At least one of districts or meal_types must be provided'
            }
        
        # Determine which tool to use
        if districts and meal_types:
            tool_name = "search_restaurants_combined"
            parameters = {"districts": districts, "meal_types": meal_types}
        elif districts:
            tool_name = "search_restaurants_by_district"
            parameters = {"districts": districts}
        else:
            tool_name = "search_restaurants_by_meal_type"
            parameters = {"meal_types": meal_types}
        
        # Make the call with retry logic
        result = await self.call_mcp_tool_with_retry(mcp_url, tool_name, parameters)
        
        # Process successful results
        if result['success'] and result['data']['success']:
            restaurants = result['data']['data']['restaurants']
            count = result['data']['data']['count']
            
            return {
                'success': True,
                'restaurants': restaurants,
                'count': count,
                'search_criteria': {
                    'districts': districts,
                    'meal_types': meal_types
                },
                'attempt': result['attempt']
            }
        
        # Handle MCP tool errors
        elif result['success'] and not result['data']['success']:
            error_info = result['data']['error']
            return {
                'success': False,
                'error': 'MCP_TOOL_ERROR',
                'message': error_info['message'],
                'error_type': error_info.get('type', 'Unknown'),
                'details': error_info.get('details')
            }
        
        # Handle connection/retry errors
        else:
            return result

# Usage example
async def error_handling_example():
    """Demonstrate error handling with authenticated MCP client."""
    
    client = AuthenticatedMCPClient()
    mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
    
    # Test cases with different error scenarios
    test_cases = [
        # Valid case
        {
            'name': 'Valid district search',
            'districts': ['Central district'],
            'meal_types': None
        },
        # Invalid district
        {
            'name': 'Invalid district',
            'districts': ['NonexistentDistrict'],
            'meal_types': None
        },
        # Invalid meal type
        {
            'name': 'Invalid meal type',
            'districts': None,
            'meal_types': ['invalidmeal']
        },
        # Empty parameters
        {
            'name': 'Empty parameters',
            'districts': None,
            'meal_types': None
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 40)
        
        result = await client.search_restaurants_with_error_handling(
            mcp_url,
            districts=test_case['districts'],
            meal_types=test_case['meal_types']
        )
        
        if result['success']:
            print(f"✅ Success: Found {result['count']} restaurants")
            if result.get('attempt', 1) > 1:
                print(f"   (Required {result['attempt']} attempts)")
        else:
            print(f"❌ Error: {result['error']}")
            print(f"   Message: {result['message']}")
            if result.get('details'):
                print(f"   Details: {result['details']}")

if __name__ == "__main__":
    asyncio.run(error_handling_example())
```## Parame
ter Formats and Validation

### District Parameter Examples

```python
#!/usr/bin/env python3
"""Examples of district parameter formats and validation."""

# Valid district parameter formats
VALID_DISTRICT_EXAMPLES = {
    "single_district": {
        "districts": ["Central district"]
    },
    "multiple_districts": {
        "districts": ["Central district", "Admiralty", "Causeway Bay"]
    },
    "mixed_regions": {
        "districts": ["Central district", "Tsim Sha Tsui", "Sha Tin"]
    }
}

# Available districts by region
AVAILABLE_DISTRICTS = {
    "Hong Kong Island": [
        "Central district", "Admiralty", "Causeway Bay", "Wan Chai",
        "North Point", "Quarry Bay", "Tai Koo", "Shau Kei Wan",
        "Chai Wan", "Aberdeen", "Wong Chuk Hang", "Stanley"
    ],
    "Kowloon": [
        "Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Jordan",
        "Sham Shui Po", "Cheung Sha Wan", "Lai Chi Kok", "Mei Foo",
        "Kowloon Tong", "Lok Fu", "Wong Tai Sin", "Diamond Hill",
        "Choi Hung", "Kowloon Bay", "Ngau Tau Kok", "Kwun Tong"
    ],
    "New Territories": [
        "Sha Tin", "Tai Wai", "Ma On Shan", "Tsuen Wan", "Kwai Chung",
        "Tsing Yi", "Tuen Mun", "Yuen Long", "Tin Shui Wai", "Fanling",
        "Sheung Shui", "Tai Po", "Fo Tan", "University"
    ],
    "Lantau": [
        "Tung Chung", "Discovery Bay", "Mui Wo", "Tai O"
    ]
}

def validate_districts(districts: list) -> dict:
    """Validate district parameters."""
    
    if not isinstance(districts, list):
        return {
            "valid": False,
            "error": "Districts must be provided as a list",
            "example": ["Central district", "Admiralty"]
        }
    
    if not districts:
        return {
            "valid": False,
            "error": "Districts list cannot be empty",
            "example": ["Central district"]
        }
    
    # Check for non-string items
    non_strings = [d for d in districts if not isinstance(d, str)]
    if non_strings:
        return {
            "valid": False,
            "error": f"All district names must be strings, found: {[type(d).__name__ for d in non_strings]}",
            "example": ["Central district", "Admiralty"]
        }
    
    # Check for valid district names
    all_districts = []
    for region_districts in AVAILABLE_DISTRICTS.values():
        all_districts.extend(region_districts)
    
    invalid_districts = [d for d in districts if d not in all_districts]
    if invalid_districts:
        # Find similar districts for suggestions
        suggestions = []
        for invalid in invalid_districts:
            for valid in all_districts:
                if invalid.lower() in valid.lower() or valid.lower() in invalid.lower():
                    suggestions.append(valid)
                    break
        
        return {
            "valid": False,
            "error": f"Invalid districts: {invalid_districts}",
            "suggestions": suggestions[:3],  # Top 3 suggestions
            "available_districts": all_districts
        }
    
    return {
        "valid": True,
        "districts": districts,
        "regions": {district: get_region_for_district(district) for district in districts}
    }

def get_region_for_district(district: str) -> str:
    """Get the region for a given district."""
    for region, districts in AVAILABLE_DISTRICTS.items():
        if district in districts:
            return region
    return "Unknown"

# Example usage
if __name__ == "__main__":
    test_cases = [
        ["Central district"],
        ["Central district", "Tsim Sha Tsui"],
        ["InvalidDistrict"],
        ["Central", "TST"],  # Common abbreviations
        [],  # Empty list
        "Central district",  # Not a list
        [123, "Central district"],  # Mixed types
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case}")
        result = validate_districts(test_case)
        
        if result["valid"]:
            print(f"✅ Valid: {result['districts']}")
            print(f"   Regions: {result['regions']}")
        else:
            print(f"❌ Invalid: {result['error']}")
            if "suggestions" in result:
                print(f"   Suggestions: {result['suggestions']}")
```

### Meal Type Parameter Examples

```python
#!/usr/bin/env python3
"""Examples of meal type parameter formats and validation."""

# Valid meal type parameter formats
VALID_MEAL_TYPE_EXAMPLES = {
    "single_meal": {
        "meal_types": ["breakfast"]
    },
    "multiple_meals": {
        "meal_types": ["breakfast", "lunch"]
    },
    "all_meals": {
        "meal_types": ["breakfast", "lunch", "dinner"]
    }
}

# Meal time definitions
MEAL_TIME_DEFINITIONS = {
    "breakfast": {
        "time_range": "07:00 - 11:29",
        "description": "Morning dining period",
        "typical_foods": ["dim sum", "congee", "toast", "coffee"]
    },
    "lunch": {
        "time_range": "11:30 - 17:29", 
        "description": "Afternoon dining period",
        "typical_foods": ["rice dishes", "noodles", "set meals", "business lunch"]
    },
    "dinner": {
        "time_range": "17:30 - 22:30",
        "description": "Evening dining period",
        "typical_foods": ["full course meals", "hot pot", "barbecue", "fine dining"]
    }
}

def validate_meal_types(meal_types: list) -> dict:
    """Validate meal type parameters."""
    
    if not isinstance(meal_types, list):
        return {
            "valid": False,
            "error": "Meal types must be provided as a list",
            "example": ["breakfast", "lunch", "dinner"]
        }
    
    if not meal_types:
        return {
            "valid": False,
            "error": "Meal types list cannot be empty",
            "example": ["breakfast"]
        }
    
    # Check for non-string items
    non_strings = [m for m in meal_types if not isinstance(m, str)]
    if non_strings:
        return {
            "valid": False,
            "error": f"All meal types must be strings, found: {[type(m).__name__ for m in non_strings]}",
            "example": ["breakfast", "lunch"]
        }
    
    # Check for valid meal types
    valid_meal_types = set(MEAL_TIME_DEFINITIONS.keys())
    invalid_meal_types = [m for m in meal_types if m.lower() not in valid_meal_types]
    
    if invalid_meal_types:
        # Find suggestions for invalid meal types
        suggestions = {}
        for invalid in invalid_meal_types:
            invalid_lower = invalid.lower()
            if "morning" in invalid_lower or "brunch" in invalid_lower:
                suggestions[invalid] = "breakfast"
            elif "afternoon" in invalid_lower or "midday" in invalid_lower:
                suggestions[invalid] = "lunch"
            elif "evening" in invalid_lower or "night" in invalid_lower:
                suggestions[invalid] = "dinner"
        
        return {
            "valid": False,
            "error": f"Invalid meal types: {invalid_meal_types}",
            "valid_meal_types": list(valid_meal_types),
            "suggestions": suggestions,
            "meal_definitions": MEAL_TIME_DEFINITIONS
        }
    
    # Normalize to lowercase
    normalized_meal_types = [m.lower() for m in meal_types]
    
    return {
        "valid": True,
        "meal_types": normalized_meal_types,
        "time_ranges": {m: MEAL_TIME_DEFINITIONS[m]["time_range"] for m in normalized_meal_types},
        "descriptions": {m: MEAL_TIME_DEFINITIONS[m]["description"] for m in normalized_meal_types}
    }

# Example usage
if __name__ == "__main__":
    test_cases = [
        ["breakfast"],
        ["BREAKFAST", "LUNCH"],  # Case variations
        ["breakfast", "lunch", "dinner"],
        ["morning", "evening"],  # Common alternatives
        ["invalidmeal"],
        [],  # Empty list
        "breakfast",  # Not a list
        [123, "breakfast"],  # Mixed types
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case}")
        result = validate_meal_types(test_case)
        
        if result["valid"]:
            print(f"✅ Valid: {result['meal_types']}")
            print(f"   Time ranges: {result['time_ranges']}")
        else:
            print(f"❌ Invalid: {result['error']}")
            if "suggestions" in result:
                print(f"   Suggestions: {result['suggestions']}")
```

### Combined Parameter Validation

```python
#!/usr/bin/env python3
"""Combined parameter validation for search_restaurants_combined tool."""

def validate_combined_parameters(districts=None, meal_types=None) -> dict:
    """Validate parameters for combined restaurant search."""
    
    # Check that at least one parameter is provided
    if not districts and not meal_types:
        return {
            "valid": False,
            "error": "At least one of 'districts' or 'meal_types' must be provided",
            "examples": {
                "districts_only": {"districts": ["Central district"]},
                "meal_types_only": {"meal_types": ["breakfast"]},
                "combined": {"districts": ["Central district"], "meal_types": ["breakfast"]}
            }
        }
    
    validation_results = {"valid": True, "validated_params": {}}
    
    # Validate districts if provided
    if districts is not None:
        district_validation = validate_districts(districts)
        if not district_validation["valid"]:
            return {
                "valid": False,
                "error": f"District validation failed: {district_validation['error']}",
                "district_details": district_validation
            }
        validation_results["validated_params"]["districts"] = district_validation["districts"]
    
    # Validate meal types if provided
    if meal_types is not None:
        meal_type_validation = validate_meal_types(meal_types)
        if not meal_type_validation["valid"]:
            return {
                "valid": False,
                "error": f"Meal type validation failed: {meal_type_validation['error']}",
                "meal_type_details": meal_type_validation
            }
        validation_results["validated_params"]["meal_types"] = meal_type_validation["meal_types"]
    
    return validation_results

# Example usage
if __name__ == "__main__":
    test_cases = [
        # Valid cases
        {"districts": ["Central district"], "meal_types": ["breakfast"]},
        {"districts": ["Central district"]},
        {"meal_types": ["breakfast"]},
        
        # Invalid cases
        {},  # No parameters
        {"districts": ["InvalidDistrict"], "meal_types": ["breakfast"]},
        {"districts": ["Central district"], "meal_types": ["invalidmeal"]},
        {"districts": [], "meal_types": []},  # Empty lists
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        result = validate_combined_parameters(**test_case)
        
        if result["valid"]:
            print(f"✅ Valid parameters: {result['validated_params']}")
        else:
            print(f"❌ Validation failed: {result['error']}")
```## R
esponse Structures

### Successful Response Format

```python
#!/usr/bin/env python3
"""Examples of successful response structures from MCP tools."""

# Example successful response from search_restaurants_by_district
DISTRICT_SEARCH_RESPONSE = {
    "success": True,
    "data": {
        "restaurants": [
            {
                "id": "rest_001",
                "name": "Golden Dragon Restaurant",
                "address": "123 Queen's Road Central, Central, Hong Kong",
                "meal_type": ["Chinese", "Cantonese", "Dim Sum"],
                "sentiment": {
                    "likes": 245,
                    "dislikes": 12,
                    "neutral": 43
                },
                "location_category": "Shopping Mall",
                "district": "Central district",
                "price_range": "$$",
                "operating_hours": {
                    "mon_fri": ["11:30 - 15:30", "18:00 - 22:30"],
                    "sat_sun": ["10:00 - 15:30", "18:00 - 23:00"],
                    "public_holiday": ["10:00 - 15:30", "18:00 - 22:00"]
                },
                "metadata": {
                    "data_quality": "high",
                    "version": "1.2",
                    "quality_score": 92
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
                "Hong Kong Island": ["Central district", "Admiralty", "Causeway Bay"],
                "Kowloon": ["Tsim Sha Tsui", "Mong Kok"],
                "New Territories": ["Sha Tin", "Tsuen Wan"],
                "Lantau": ["Tung Chung"]
            }
        }
    }
}

# Example successful response from search_restaurants_by_meal_type
MEAL_TYPE_SEARCH_RESPONSE = {
    "success": True,
    "data": {
        "restaurants": [
            {
                "id": "rest_002",
                "name": "Morning Glory Cafe",
                "address": "456 Nathan Road, Tsim Sha Tsui, Kowloon",
                "meal_type": ["Western", "Breakfast", "Coffee"],
                "sentiment": {
                    "likes": 189,
                    "dislikes": 8,
                    "neutral": 23
                },
                "location_category": "Street Level",
                "district": "Tsim Sha Tsui",
                "price_range": "$",
                "operating_hours": {
                    "mon_fri": ["07:00 - 11:30", "12:00 - 15:00"],
                    "sat_sun": ["07:30 - 14:00"],
                    "public_holiday": ["08:00 - 13:00"]
                },
                "metadata": {
                    "data_quality": "high",
                    "version": "1.1",
                    "quality_score": 88
                }
            }
        ],
        "count": 1,
        "metadata": {
            "search_criteria": {
                "meal_types": ["breakfast"],
                "search_type": "meal_type"
            },
            "meal_analysis": {
                "breakfast": {
                    "total_restaurants": 1,
                    "avg_quality_score": 88,
                    "districts": ["Tsim Sha Tsui"]
                }
            },
            "meal_periods": {
                "breakfast": "07:00 - 11:29",
                "lunch": "11:30 - 17:29",
                "dinner": "17:30 - 22:30"
            }
        }
    }
}

# Example successful response from search_restaurants_combined
COMBINED_SEARCH_RESPONSE = {
    "success": True,
    "data": {
        "restaurants": [
            {
                "id": "rest_003",
                "name": "Harbour View Dining",
                "address": "789 Canton Road, Tsim Sha Tsui, Kowloon",
                "meal_type": ["Chinese", "Seafood", "Fine Dining"],
                "sentiment": {
                    "likes": 312,
                    "dislikes": 15,
                    "neutral": 28
                },
                "location_category": "Hotel",
                "district": "Tsim Sha Tsui",
                "price_range": "$$$",
                "operating_hours": {
                    "mon_fri": ["18:00 - 23:00"],
                    "sat_sun": ["17:30 - 23:30"],
                    "public_holiday": ["18:00 - 22:30"]
                },
                "metadata": {
                    "data_quality": "high",
                    "version": "1.3",
                    "quality_score": 95
                }
            }
        ],
        "count": 1,
        "metadata": {
            "search_criteria": {
                "districts": ["Tsim Sha Tsui"],
                "meal_types": ["dinner"],
                "search_type": "combined"
            },
            "district_info": {
                "available_districts": {
                    "Hong Kong Island": ["Central district", "Admiralty"],
                    "Kowloon": ["Tsim Sha Tsui", "Mong Kok"],
                    "New Territories": ["Sha Tin"],
                    "Lantau": ["Tung Chung"]
                },
                "district_counts": {
                    "Tsim Sha Tsui": 1
                }
            },
            "meal_analysis": {
                "dinner": {
                    "total_restaurants": 1,
                    "avg_quality_score": 95,
                    "districts": ["Tsim Sha Tsui"]
                }
            },
            "meal_periods": {
                "breakfast": "07:00 - 11:29",
                "lunch": "11:30 - 17:29",
                "dinner": "17:30 - 22:30"
            },
            "search_summary": {
                "criteria": "1 district(s) and 1 meal type(s)",
                "results_count": 1
            }
        }
    }
}

def parse_restaurant_response(response_json: str) -> dict:
    """Parse and extract key information from restaurant search response."""
    
    try:
        response = json.loads(response_json)
        
        if not response.get('success', False):
            return {
                'success': False,
                'error': response.get('error', 'Unknown error'),
                'restaurants': [],
                'count': 0
            }
        
        data = response['data']
        restaurants = data['restaurants']
        
        # Extract key information
        parsed_restaurants = []
        for restaurant in restaurants:
            parsed_restaurant = {
                'name': restaurant['name'],
                'address': restaurant['address'],
                'district': restaurant['district'],
                'cuisine_types': restaurant['meal_type'],
                'price_range': restaurant['price_range'],
                'quality_score': restaurant['metadata']['quality_score'],
                'sentiment_summary': {
                    'total_reviews': sum(restaurant['sentiment'].values()),
                    'positive_ratio': restaurant['sentiment']['likes'] / sum(restaurant['sentiment'].values()) if sum(restaurant['sentiment'].values()) > 0 else 0
                },
                'operating_hours': restaurant['operating_hours']
            }
            parsed_restaurants.append(parsed_restaurant)
        
        return {
            'success': True,
            'restaurants': parsed_restaurants,
            'count': data['count'],
            'search_criteria': data['metadata']['search_criteria'],
            'summary': f"Found {data['count']} restaurants"
        }
    
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Invalid JSON response: {e}',
            'restaurants': [],
            'count': 0
        }
    except KeyError as e:
        return {
            'success': False,
            'error': f'Missing required field in response: {e}',
            'restaurants': [],
            'count': 0
        }

# Example usage
if __name__ == "__main__":
    # Test parsing different response types
    test_responses = [
        json.dumps(DISTRICT_SEARCH_RESPONSE),
        json.dumps(MEAL_TYPE_SEARCH_RESPONSE),
        json.dumps(COMBINED_SEARCH_RESPONSE)
    ]
    
    for i, response_json in enumerate(test_responses, 1):
        print(f"\n--- Parsing Response {i} ---")
        parsed = parse_restaurant_response(response_json)
        
        if parsed['success']:
            print(f"✅ {parsed['summary']}")
            for restaurant in parsed['restaurants']:
                print(f"   • {restaurant['name']} ({restaurant['district']})")
                print(f"     Cuisine: {', '.join(restaurant['cuisine_types'])}")
                print(f"     Price: {restaurant['price_range']}, Quality: {restaurant['quality_score']}")
        else:
            print(f"❌ Error: {parsed['error']}")
```

### Error Response Format

```python
#!/usr/bin/env python3
"""Examples of error response structures from MCP tools."""

# Validation error response
VALIDATION_ERROR_RESPONSE = {
    "success": False,
    "error": {
        "type": "ValidationError",
        "message": "Invalid districts: ['InvalidDistrict']",
        "details": {
            "invalid_districts": ["InvalidDistrict"],
            "available_districts": {
                "Hong Kong Island": ["Central district", "Admiralty", "Causeway Bay"],
                "Kowloon": ["Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei"],
                "New Territories": ["Sha Tin", "Tsuen Wan", "Tai Po"],
                "Lantau": ["Tung Chung", "Discovery Bay"]
            },
            "requested_districts": ["InvalidDistrict"]
        }
    }
}

# Restaurant search error response
SEARCH_ERROR_RESPONSE = {
    "success": False,
    "error": {
        "type": "RestaurantSearchError",
        "message": "Failed to retrieve restaurant data from S3",
        "details": {
            "s3_error": "NoSuchKey: The specified key does not exist",
            "requested_path": "restaurant-data-209803798463-us-east-1/restaurants/hong-kong-island/invalid-district.json"
        }
    }
}

# Internal error response
INTERNAL_ERROR_RESPONSE = {
    "success": False,
    "error": {
        "type": "InternalError",
        "message": "An unexpected error occurred: Connection timeout"
    }
}

# Authentication error response (from AgentCore Runtime)
AUTHENTICATION_ERROR_RESPONSE = {
    "success": False,
    "error": {
        "type": "AuthenticationError",
        "message": "JWT token validation failed",
        "details": {
            "error_code": "TOKEN_EXPIRED",
            "suggested_action": "Refresh your authentication token and try again"
        }
    }
}

def handle_error_response(response_json: str) -> dict:
    """Handle and categorize error responses from MCP tools."""
    
    try:
        response = json.loads(response_json)
        
        if response.get('success', True):
            return {
                'is_error': False,
                'message': 'Response indicates success'
            }
        
        error_info = response.get('error', {})
        error_type = error_info.get('type', 'UnknownError')
        error_message = error_info.get('message', 'No error message provided')
        error_details = error_info.get('details', {})
        
        # Categorize error and provide handling suggestions
        if error_type == 'ValidationError':
            return {
                'is_error': True,
                'category': 'user_input',
                'type': error_type,
                'message': error_message,
                'details': error_details,
                'retry_recommended': True,
                'user_action_required': True,
                'suggestions': [
                    'Check parameter format and values',
                    'Use valid district names from available_districts list',
                    'Ensure meal types are: breakfast, lunch, or dinner'
                ]
            }
        
        elif error_type == 'RestaurantSearchError':
            return {
                'is_error': True,
                'category': 'service',
                'type': error_type,
                'message': error_message,
                'details': error_details,
                'retry_recommended': True,
                'user_action_required': False,
                'suggestions': [
                    'Try again in a few moments',
                    'Check if the district exists in the system',
                    'Contact support if the error persists'
                ]
            }
        
        elif error_type == 'AuthenticationError':
            return {
                'is_error': True,
                'category': 'authentication',
                'type': error_type,
                'message': error_message,
                'details': error_details,
                'retry_recommended': True,
                'user_action_required': True,
                'suggestions': [
                    'Refresh your authentication token',
                    'Re-authenticate with valid credentials',
                    'Check token expiration time'
                ]
            }
        
        elif error_type == 'InternalError':
            return {
                'is_error': True,
                'category': 'system',
                'type': error_type,
                'message': error_message,
                'details': error_details,
                'retry_recommended': True,
                'user_action_required': False,
                'suggestions': [
                    'Try again in a few moments',
                    'Check network connectivity',
                    'Contact support if the error persists'
                ]
            }
        
        else:
            return {
                'is_error': True,
                'category': 'unknown',
                'type': error_type,
                'message': error_message,
                'details': error_details,
                'retry_recommended': False,
                'user_action_required': False,
                'suggestions': [
                    'Contact support with error details'
                ]
            }
    
    except json.JSONDecodeError as e:
        return {
            'is_error': True,
            'category': 'protocol',
            'type': 'JSONDecodeError',
            'message': f'Invalid JSON response: {e}',
            'details': {},
            'retry_recommended': False,
            'user_action_required': False,
            'suggestions': [
                'Check MCP server status',
                'Verify request format',
                'Contact support'
            ]
        }

# Example usage
if __name__ == "__main__":
    # Test error handling
    error_responses = [
        json.dumps(VALIDATION_ERROR_RESPONSE),
        json.dumps(SEARCH_ERROR_RESPONSE),
        json.dumps(INTERNAL_ERROR_RESPONSE),
        json.dumps(AUTHENTICATION_ERROR_RESPONSE)
    ]
    
    for i, error_json in enumerate(error_responses, 1):
        print(f"\n--- Handling Error Response {i} ---")
        error_info = handle_error_response(error_json)
        
        if error_info['is_error']:
            print(f"❌ Error Category: {error_info['category']}")
            print(f"   Type: {error_info['type']}")
            print(f"   Message: {error_info['message']}")
            print(f"   Retry Recommended: {error_info['retry_recommended']}")
            print(f"   User Action Required: {error_info['user_action_required']}")
            print(f"   Suggestions: {', '.join(error_info['suggestions'])}")
        else:
            print(f"✅ {error_info['message']}")
```##
 Performance Optimization

### Connection Pooling and Reuse

```python
#!/usr/bin/env python3
"""Performance optimization examples for MCP client connections."""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

class OptimizedMCPClient:
    """High-performance MCP client with connection pooling and caching."""
    
    def __init__(self, mcp_url: str, config_file: str = 'cognito_config.json'):
        """Initialize optimized MCP client."""
        self.mcp_url = mcp_url
        
        # Load authentication configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.config['user_pool']['user_pool_id'],
            client_id=self.config['app_client']['client_id'],
            region=self.config['region']
        )
        
        # Connection and caching
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        self.session_cache: Dict[str, Any] = {}
        self.response_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'auth_refreshes': 0,
            'avg_response_time': 0,
            'response_times': []
        }
    
    async def ensure_authenticated(self) -> str:
        """Ensure we have a valid access token with minimal overhead."""
        current_time = time.time()
        
        # Check if current token is still valid (with 5-minute buffer)
        if self.access_token and self.token_expires_at:
            if current_time < self.token_expires_at - 300:
                return self.access_token
        
        # Refresh token
        print("🔄 Refreshing authentication token...")
        tokens = self.authenticator.authenticate_user(
            self.config['test_user']['email'],
            "TempPass123!"
        )
        
        self.access_token = tokens.access_token
        self.token_expires_at = current_time + tokens.expires_in
        self.metrics['auth_refreshes'] += 1
        
        return self.access_token
    
    def _get_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        # Sort parameters for consistent cache keys
        sorted_params = json.dumps(parameters, sort_keys=True)
        return f"{tool_name}:{sorted_params}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - cache_entry['timestamp'] < self.cache_ttl
    
    async def call_tool_optimized(self, tool_name: str, parameters: Dict[str, Any], 
                                 use_cache: bool = True) -> Dict[str, Any]:
        """Call MCP tool with performance optimizations."""
        
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(tool_name, parameters)
            if cache_key in self.response_cache:
                cache_entry = self.response_cache[cache_key]
                if self._is_cache_valid(cache_entry):
                    self.metrics['cache_hits'] += 1
                    print(f"📋 Cache hit for {tool_name}")
                    return cache_entry['response']
        
        self.metrics['cache_misses'] += 1
        
        # Ensure authentication
        token = await self.ensure_authenticated()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Make MCP call
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(tool_name, parameters)
                    response_data = json.loads(result.content[0].text)
                    
                    # Cache successful responses
                    if use_cache and response_data.get('success', False):
                        cache_key = self._get_cache_key(tool_name, parameters)
                        self.response_cache[cache_key] = {
                            'response': response_data,
                            'timestamp': time.time()
                        }
                    
                    # Update performance metrics
                    response_time = time.time() - start_time
                    self.metrics['response_times'].append(response_time)
                    self.metrics['avg_response_time'] = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
                    
                    return response_data
        
        except Exception as e:
            print(f"❌ MCP call failed: {e}")
            return {
                'success': False,
                'error': {
                    'type': 'ConnectionError',
                    'message': str(e)
                }
            }
    
    async def batch_search(self, search_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform multiple searches concurrently for better performance."""
        
        print(f"🚀 Executing {len(search_requests)} searches concurrently...")
        
        # Create tasks for concurrent execution
        tasks = []
        for request in search_requests:
            tool_name = request['tool_name']
            parameters = request['parameters']
            use_cache = request.get('use_cache', True)
            
            task = self.call_tool_optimized(tool_name, parameters, use_cache)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': {
                        'type': 'BatchExecutionError',
                        'message': str(result)
                    },
                    'request_index': i
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        cache_hit_rate = (self.metrics['cache_hits'] / max(self.metrics['total_requests'], 1)) * 100
        
        return {
            'total_requests': self.metrics['total_requests'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'auth_refreshes': self.metrics['auth_refreshes'],
            'avg_response_time': f"{self.metrics['avg_response_time']:.3f}s",
            'cached_responses': len(self.response_cache)
        }
    
    def clear_cache(self) -> None:
        """Clear response cache."""
        self.response_cache.clear()
        print("🗑️ Response cache cleared")

async def performance_optimization_example():
    """Demonstrate performance optimization techniques."""
    
    mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
    client = OptimizedMCPClient(mcp_url)
    
    print("🏃‍♂️ Performance Optimization Demo")
    print("=" * 50)
    
    # Test 1: Single requests with caching
    print("\n📋 Test 1: Caching Performance")
    
    # First request (cache miss)
    start_time = time.time()
    result1 = await client.call_tool_optimized(
        "search_restaurants_by_district",
        {"districts": ["Central district"]}
    )
    first_request_time = time.time() - start_time
    
    # Second identical request (cache hit)
    start_time = time.time()
    result2 = await client.call_tool_optimized(
        "search_restaurants_by_district",
        {"districts": ["Central district"]}
    )
    second_request_time = time.time() - start_time
    
    print(f"First request (cache miss): {first_request_time:.3f}s")
    print(f"Second request (cache hit): {second_request_time:.3f}s")
    print(f"Cache speedup: {first_request_time / second_request_time:.1f}x faster")
    
    # Test 2: Batch concurrent requests
    print("\n🚀 Test 2: Concurrent Batch Processing")
    
    batch_requests = [
        {
            'tool_name': 'search_restaurants_by_district',
            'parameters': {'districts': ['Tsim Sha Tsui']}
        },
        {
            'tool_name': 'search_restaurants_by_district',
            'parameters': {'districts': ['Causeway Bay']}
        },
        {
            'tool_name': 'search_restaurants_by_meal_type',
            'parameters': {'meal_types': ['breakfast']}
        },
        {
            'tool_name': 'search_restaurants_by_meal_type',
            'parameters': {'meal_types': ['dinner']}
        },
        {
            'tool_name': 'search_restaurants_combined',
            'parameters': {'districts': ['Admiralty'], 'meal_types': ['lunch']}
        }
    ]
    
    # Sequential execution
    print("Sequential execution...")
    sequential_start = time.time()
    sequential_results = []
    for request in batch_requests:
        result = await client.call_tool_optimized(
            request['tool_name'],
            request['parameters'],
            use_cache=False  # Disable cache for fair comparison
        )
        sequential_results.append(result)
    sequential_time = time.time() - sequential_start
    
    # Clear cache for fair comparison
    client.clear_cache()
    
    # Concurrent execution
    print("Concurrent execution...")
    concurrent_start = time.time()
    concurrent_results = await client.batch_search(batch_requests)
    concurrent_time = time.time() - concurrent_start
    
    print(f"Sequential time: {sequential_time:.3f}s")
    print(f"Concurrent time: {concurrent_time:.3f}s")
    print(f"Concurrency speedup: {sequential_time / concurrent_time:.1f}x faster")
    
    # Test 3: Performance metrics
    print("\n📊 Test 3: Performance Metrics")
    metrics = client.get_performance_metrics()
    
    for key, value in metrics.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(performance_optimization_example())
```

### Memory Management and Resource Optimization

```python
#!/usr/bin/env python3
"""Memory management and resource optimization for MCP clients."""

import asyncio
import json
import gc
import psutil
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    memory_usage_mb: float
    cpu_percent: float
    active_connections: int
    cache_size_mb: float
    timestamp: float

class ResourceOptimizedMCPClient:
    """MCP client optimized for memory and resource usage."""
    
    def __init__(self, mcp_url: str, max_cache_size_mb: int = 50):
        """Initialize resource-optimized MCP client."""
        self.mcp_url = mcp_url
        self.max_cache_size_mb = max_cache_size_mb
        self.max_cache_entries = 1000
        
        # Resource tracking
        self.process = psutil.Process()
        self.active_connections = 0
        self.cache: Dict[str, Dict] = {}
        self.cache_access_times: Dict[str, float] = {}
        
        # Metrics collection
        self.resource_metrics: List[ResourceMetrics] = []
    
    def _get_cache_size_mb(self) -> float:
        """Calculate current cache size in MB."""
        cache_str = json.dumps(self.cache)
        return len(cache_str.encode('utf-8')) / (1024 * 1024)
    
    def _cleanup_cache(self) -> None:
        """Clean up cache based on size and access time."""
        current_size = self._get_cache_size_mb()
        
        if current_size > self.max_cache_size_mb or len(self.cache) > self.max_cache_entries:
            print(f"🧹 Cache cleanup triggered (size: {current_size:.1f}MB, entries: {len(self.cache)})")
            
            # Sort by access time (LRU eviction)
            sorted_keys = sorted(
                self.cache_access_times.keys(),
                key=lambda k: self.cache_access_times[k]
            )
            
            # Remove oldest entries until under limits
            entries_to_remove = max(
                len(self.cache) - self.max_cache_entries // 2,
                0
            )
            
            for key in sorted_keys[:entries_to_remove]:
                del self.cache[key]
                del self.cache_access_times[key]
            
            # Force garbage collection
            gc.collect()
            
            new_size = self._get_cache_size_mb()
            print(f"✅ Cache cleaned: {new_size:.1f}MB, {len(self.cache)} entries")
    
    def _record_metrics(self) -> None:
        """Record current resource usage metrics."""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        cpu_percent = self.process.cpu_percent()
        cache_size_mb = self._get_cache_size_mb()
        
        metrics = ResourceMetrics(
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent,
            active_connections=self.active_connections,
            cache_size_mb=cache_size_mb,
            timestamp=time.time()
        )
        
        self.resource_metrics.append(metrics)
        
        # Keep only last 100 metrics to prevent memory growth
        if len(self.resource_metrics) > 100:
            self.resource_metrics = self.resource_metrics[-100:]
    
    async def call_tool_with_resource_management(self, tool_name: str, 
                                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool with resource management."""
        
        # Record metrics before call
        self._record_metrics()
        
        # Check cache first
        cache_key = f"{tool_name}:{json.dumps(parameters, sort_keys=True)}"
        if cache_key in self.cache:
            self.cache_access_times[cache_key] = time.time()
            return self.cache[cache_key]
        
        try:
            self.active_connections += 1
            
            # Simulate authentication (simplified for example)
            headers = {
                'Authorization': 'Bearer your-token',
                'Content-Type': 'application/json'
            }
            
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(tool_name, parameters)
                    response_data = json.loads(result.content[0].text)
                    
                    # Cache successful responses
                    if response_data.get('success', False):
                        self.cache[cache_key] = response_data
                        self.cache_access_times[cache_key] = time.time()
                        
                        # Cleanup cache if needed
                        self._cleanup_cache()
                    
                    return response_data
        
        finally:
            self.active_connections -= 1
            # Record metrics after call
            self._record_metrics()
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource usage summary."""
        if not self.resource_metrics:
            return {"error": "No metrics available"}
        
        latest = self.resource_metrics[-1]
        
        # Calculate averages over last 10 measurements
        recent_metrics = self.resource_metrics[-10:]
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        
        return {
            "current_memory_mb": latest.memory_usage_mb,
            "average_memory_mb": avg_memory,
            "current_cpu_percent": latest.cpu_percent,
            "average_cpu_percent": avg_cpu,
            "cache_size_mb": latest.cache_size_mb,
            "cache_entries": len(self.cache),
            "active_connections": latest.active_connections,
            "max_cache_size_mb": self.max_cache_size_mb
        }
    
    def optimize_for_memory(self) -> None:
        """Optimize client for low memory usage."""
        print("🔧 Optimizing for memory usage...")
        
        # Reduce cache limits
        self.max_cache_size_mb = 10
        self.max_cache_entries = 100
        
        # Clear current cache
        self.cache.clear()
        self.cache_access_times.clear()
        
        # Force garbage collection
        gc.collect()
        
        print("✅ Memory optimization complete")
    
    def optimize_for_performance(self) -> None:
        """Optimize client for high performance."""
        print("🚀 Optimizing for performance...")
        
        # Increase cache limits
        self.max_cache_size_mb = 100
        self.max_cache_entries = 5000
        
        print("✅ Performance optimization complete")

async def resource_optimization_example():
    """Demonstrate resource optimization techniques."""
    
    mcp_url = "https://your-agentcore-endpoint.amazonaws.com"
    client = ResourceOptimizedMCPClient(mcp_url)
    
    print("💾 Resource Optimization Demo")
    print("=" * 50)
    
    # Test 1: Memory usage monitoring
    print("\n📊 Test 1: Memory Usage Monitoring")
    
    # Make several requests to build up cache
    test_requests = [
        ("search_restaurants_by_district", {"districts": ["Central district"]}),
        ("search_restaurants_by_district", {"districts": ["Tsim Sha Tsui"]}),
        ("search_restaurants_by_meal_type", {"meal_types": ["breakfast"]}),
        ("search_restaurants_by_meal_type", {"meal_types": ["lunch"]}),
        ("search_restaurants_by_meal_type", {"meal_types": ["dinner"]}),
    ]
    
    for tool_name, parameters in test_requests:
        await client.call_tool_with_resource_management(tool_name, parameters)
        
        # Show resource usage after each request
        summary = client.get_resource_summary()
        print(f"Memory: {summary['current_memory_mb']:.1f}MB, "
              f"Cache: {summary['cache_size_mb']:.1f}MB ({summary['cache_entries']} entries)")
    
    # Test 2: Cache optimization
    print(f"\n🧹 Test 2: Cache Management")
    
    initial_summary = client.get_resource_summary()
    print(f"Before optimization - Memory: {initial_summary['current_memory_mb']:.1f}MB, "
          f"Cache: {initial_summary['cache_size_mb']:.1f}MB")
    
    # Optimize for memory
    client.optimize_for_memory()
    
    optimized_summary = client.get_resource_summary()
    print(f"After optimization - Memory: {optimized_summary['current_memory_mb']:.1f}MB, "
          f"Cache: {optimized_summary['cache_size_mb']:.1f}MB")
    
    # Test 3: Performance vs Memory trade-off
    print(f"\n⚖️ Test 3: Performance vs Memory Trade-off")
    
    # Performance mode
    client.optimize_for_performance()
    perf_start = time.time()
    
    for _ in range(5):
        await client.call_tool_with_resource_management(
            "search_restaurants_by_district",
            {"districts": ["Central district"]}
        )
    
    perf_time = time.time() - perf_start
    perf_summary = client.get_resource_summary()
    
    print(f"Performance mode - Time: {perf_time:.3f}s, "
          f"Memory: {perf_summary['current_memory_mb']:.1f}MB")
    
    # Memory mode
    client.optimize_for_memory()
    memory_start = time.time()
    
    for _ in range(5):
        await client.call_tool_with_resource_management(
            "search_restaurants_by_district",
            {"districts": ["Central district"]}
        )
    
    memory_time = time.time() - memory_start
    memory_summary = client.get_resource_summary()
    
    print(f"Memory mode - Time: {memory_time:.3f}s, "
          f"Memory: {memory_summary['current_memory_mb']:.1f}MB")

if __name__ == "__main__":
    asyncio.run(resource_optimization_example())
```#
# Production Integration Patterns

### Enterprise Integration Example

```python
#!/usr/bin/env python3
"""Enterprise-grade integration pattern for Restaurant Search MCP tools."""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

# Configure enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] %(message)s'
)

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class RequestContext:
    """Request context for tracing and auditing."""
    correlation_id: str
    user_id: str
    session_id: str
    client_ip: str
    user_agent: str
    timestamp: float

@dataclass
class MCPMetrics:
    """MCP operation metrics."""
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    auth_refresh_count: int = 0

class EnterpriseRestaurantSearchClient:
    """Enterprise-grade MCP client with comprehensive features."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize enterprise MCP client."""
        self.config = config
        self.mcp_url = config['mcp_url']
        self.environment = config.get('environment', 'production')
        
        # Authentication
        self.authenticator = CognitoAuthenticator(
            user_pool_id=config['cognito']['user_pool_id'],
            client_id=config['cognito']['client_id'],
            region=config['cognito']['region']
        )
        
        # Caching and performance
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = config.get('cache_ttl', 300)
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30)
        
        # Metrics and monitoring
        self.metrics = MCPMetrics()
        self.request_times: List[float] = []
        
        # Circuit breaker
        self.circuit_breaker_threshold = config.get('circuit_breaker_threshold', 5)
        self.circuit_breaker_window = config.get('circuit_breaker_window', 60)
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        
        # Logging
        self.logger = logging.getLogger(f"RestaurantSearchClient.{self.environment}")
        
        # Rate limiting
        self.rate_limit = config.get('rate_limit', 100)  # requests per minute
        self.request_timestamps: List[float] = []
    
    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limit."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        if len(self.request_timestamps) >= self.rate_limit:
            return False
        
        self.request_timestamps.append(current_time)
        return True
    
    def _check_circuit_breaker(self) -> bool:
        """Check circuit breaker status."""
        current_time = time.time()
        
        # Reset circuit breaker if window has passed
        if (current_time - self.last_failure_time) > self.circuit_breaker_window:
            self.circuit_open = False
            self.failure_count = 0
        
        return not self.circuit_open
    
    def _record_failure(self) -> None:
        """Record a failure for circuit breaker."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.circuit_breaker_threshold:
            self.circuit_open = True
            self.logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures",
                extra={'correlation_id': 'system'}
            )
    
    def _record_success(self) -> None:
        """Record a success for circuit breaker."""
        self.failure_count = max(0, self.failure_count - 1)
    
    async def _get_auth_token(self, context: RequestContext) -> str:
        """Get authentication token with proper logging."""
        try:
            self.logger.info(
                f"Authenticating user: {context.user_id}",
                extra={'correlation_id': context.correlation_id}
            )
            
            tokens = self.authenticator.authenticate_user(
                self.config['test_user']['email'],
                self.config['test_user']['password']
            )
            
            self.metrics.auth_refresh_count += 1
            
            self.logger.info(
                "Authentication successful",
                extra={'correlation_id': context.correlation_id}
            )
            
            return tokens.access_token
            
        except Exception as e:
            self.logger.error(
                f"Authentication failed: {e}",
                extra={'correlation_id': context.correlation_id}
            )
            raise
    
    async def search_restaurants(self, 
                               search_params: Dict[str, Any],
                               context: RequestContext) -> Dict[str, Any]:
        """Search restaurants with enterprise-grade error handling and monitoring."""
        
        start_time = time.time()
        
        # Log request
        self.logger.info(
            f"Restaurant search request: {search_params}",
            extra={'correlation_id': context.correlation_id}
        )
        
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Circuit breaker check
            if not self._check_circuit_breaker():
                raise Exception("Circuit breaker is open")
            
            # Determine tool and parameters
            tool_name, parameters = self._prepare_search_request(search_params)
            
            # Execute search with retries
            result = await self._execute_with_retries(
                tool_name, parameters, context
            )
            
            # Record success metrics
            response_time = time.time() - start_time
            self.request_times.append(response_time)
            self.metrics.request_count += 1
            self.metrics.success_count += 1
            self.metrics.avg_response_time = sum(self.request_times) / len(self.request_times)
            
            self._record_success()
            
            # Log success
            self.logger.info(
                f"Search completed successfully in {response_time:.3f}s",
                extra={'correlation_id': context.correlation_id}
            )
            
            return {
                'success': True,
                'data': result,
                'metadata': {
                    'response_time': response_time,
                    'correlation_id': context.correlation_id,
                    'cached': False  # Would be set by cache logic
                }
            }
            
        except Exception as e:
            # Record failure metrics
            self.metrics.request_count += 1
            self.metrics.error_count += 1
            self._record_failure()
            
            # Log error
            self.logger.error(
                f"Search failed: {e}",
                extra={'correlation_id': context.correlation_id}
            )
            
            return {
                'success': False,
                'error': {
                    'type': type(e).__name__,
                    'message': str(e),
                    'correlation_id': context.correlation_id
                }
            }
    
    def _prepare_search_request(self, search_params: Dict[str, Any]) -> tuple:
        """Prepare MCP tool name and parameters from search request."""
        
        districts = search_params.get('districts')
        meal_types = search_params.get('meal_types')
        
        if districts and meal_types:
            return "search_restaurants_combined", {
                "districts": districts,
                "meal_types": meal_types
            }
        elif districts:
            return "search_restaurants_by_district", {
                "districts": districts
            }
        elif meal_types:
            return "search_restaurants_by_meal_type", {
                "meal_types": meal_types
            }
        else:
            raise ValueError("At least one of 'districts' or 'meal_types' must be provided")
    
    async def _execute_with_retries(self, tool_name: str, parameters: Dict[str, Any],
                                   context: RequestContext) -> Dict[str, Any]:
        """Execute MCP call with retry logic."""
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Get authentication token
                token = await self._get_auth_token(context)
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'X-Correlation-ID': context.correlation_id,
                    'X-User-ID': context.user_id
                }
                
                # Make MCP call
                async with asyncio.timeout(self.timeout):
                    async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            
                            result = await session.call_tool(tool_name, parameters)
                            response_data = json.loads(result.content[0].text)
                            
                            if response_data.get('success', False):
                                return response_data
                            else:
                                raise Exception(f"MCP tool error: {response_data.get('error', {}).get('message', 'Unknown error')}")
            
            except Exception as e:
                last_exception = e
                
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}",
                    extra={'correlation_id': context.correlation_id}
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
        
        raise last_exception
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get client health status for monitoring."""
        
        error_rate = (self.metrics.error_count / max(self.metrics.request_count, 1)) * 100
        
        return {
            'status': 'healthy' if error_rate < 5 and not self.circuit_open else 'degraded',
            'metrics': asdict(self.metrics),
            'error_rate_percent': error_rate,
            'circuit_breaker_open': self.circuit_open,
            'environment': self.environment,
            'timestamp': time.time()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        
        recent_times = self.request_times[-100:]  # Last 100 requests
        
        return {
            'total_requests': self.metrics.request_count,
            'success_rate': (self.metrics.success_count / max(self.metrics.request_count, 1)) * 100,
            'avg_response_time': self.metrics.avg_response_time,
            'p95_response_time': sorted(recent_times)[int(len(recent_times) * 0.95)] if recent_times else 0,
            'p99_response_time': sorted(recent_times)[int(len(recent_times) * 0.99)] if recent_times else 0,
            'cache_hit_rate': self.metrics.cache_hit_rate,
            'auth_refresh_count': self.metrics.auth_refresh_count,
            'circuit_breaker_failures': self.failure_count
        }

# Enterprise configuration example
ENTERPRISE_CONFIG = {
    'mcp_url': 'https://your-agentcore-endpoint.amazonaws.com',
    'environment': 'production',
    'cognito': {
        'user_pool_id': 'us-east-1_KePRX24Bn',
        'client_id': '26k0pnja579pdpb1pt6savs27e',
        'region': 'us-east-1'
    },
    'test_user': {
        'email': 'test@example.com',
        'password': 'TempPass123!'
    },
    'cache_ttl': 300,
    'max_retries': 3,
    'timeout': 30,
    'circuit_breaker_threshold': 5,
    'circuit_breaker_window': 60,
    'rate_limit': 100
}

async def enterprise_integration_example():
    """Demonstrate enterprise integration patterns."""
    
    client = EnterpriseRestaurantSearchClient(ENTERPRISE_CONFIG)
    
    print("🏢 Enterprise Integration Demo")
    print("=" * 50)
    
    # Create request context
    context = RequestContext(
        correlation_id="req-12345",
        user_id="user-67890",
        session_id="sess-abcde",
        client_ip="192.168.1.100",
        user_agent="RestaurantApp/1.0",
        timestamp=time.time()
    )
    
    # Test various search scenarios
    search_scenarios = [
        {
            'name': 'District Search',
            'params': {'districts': ['Central district']}
        },
        {
            'name': 'Meal Type Search',
            'params': {'meal_types': ['breakfast']}
        },
        {
            'name': 'Combined Search',
            'params': {'districts': ['Tsim Sha Tsui'], 'meal_types': ['dinner']}
        },
        {
            'name': 'Invalid Search (should fail)',
            'params': {'districts': ['NonexistentDistrict']}
        }
    ]
    
    for scenario in search_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        
        result = await client.search_restaurants(scenario['params'], context)
        
        if result['success']:
            count = result['data']['data']['count']
            response_time = result['metadata']['response_time']
            print(f"✅ Success: Found {count} restaurants in {response_time:.3f}s")
        else:
            error_type = result['error']['type']
            error_message = result['error']['message']
            print(f"❌ Failed: {error_type} - {error_message}")
    
    # Show health and performance metrics
    print(f"\n📊 Health Status:")
    health = client.get_health_status()
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    print(f"\n📈 Performance Metrics:")
    metrics = client.get_performance_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(enterprise_integration_example())
```

### Microservices Integration Pattern

```python
#!/usr/bin/env python3
"""Microservices integration pattern for Restaurant Search MCP tools."""

import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Pydantic models for API
class RestaurantSearchRequest(BaseModel):
    """Restaurant search request model."""
    districts: Optional[list[str]] = Field(None, description="List of district names")
    meal_types: Optional[list[str]] = Field(None, description="List of meal types (breakfast, lunch, dinner)")
    
    class Config:
        schema_extra = {
            "example": {
                "districts": ["Central district", "Tsim Sha Tsui"],
                "meal_types": ["breakfast", "lunch"]
            }
        }

class RestaurantSearchResponse(BaseModel):
    """Restaurant search response model."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: str
    dependencies: Dict[str, str]

# FastAPI application
app = FastAPI(
    title="Restaurant Search API",
    description="Microservice API for Hong Kong restaurant search using MCP tools",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration (would be loaded from environment/config service)
MCP_URL = "https://your-agentcore-endpoint.amazonaws.com"
SERVICE_VERSION = "1.0.0"

class MCPService:
    """Service class for MCP operations."""
    
    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
    
    async def search_restaurants(self, 
                               districts: Optional[list[str]] = None,
                               meal_types: Optional[list[str]] = None,
                               auth_token: str = None) -> Dict[str, Any]:
        """Search restaurants via MCP tools."""
        
        # Validate parameters
        if not districts and not meal_types:
            raise ValueError("At least one of 'districts' or 'meal_types' must be provided")
        
        # Determine tool and parameters
        if districts and meal_types:
            tool_name = "search_restaurants_combined"
            parameters = {"districts": districts, "meal_types": meal_types}
        elif districts:
            tool_name = "search_restaurants_by_district"
            parameters = {"districts": districts}
        else:
            tool_name = "search_restaurants_by_meal_type"
            parameters = {"meal_types": meal_types}
        
        # Set up headers
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        # Make MCP call
        async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(tool_name, parameters)
                response_data = json.loads(result.content[0].text)
                
                return response_data

# Service instance
mcp_service = MCPService(MCP_URL)

# Dependency for authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate user from JWT token."""
    # In production, validate JWT token here
    token = credentials.credentials
    
    # For demo purposes, return mock user
    return {
        'user_id': 'user-123',
        'email': 'user@example.com',
        'token': token
    }

# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version=SERVICE_VERSION,
        dependencies={
            "mcp_server": "connected",
            "authentication": "enabled"
        }
    )

@app.post("/api/v1/restaurants/search", response_model=RestaurantSearchResponse)
async def search_restaurants(
    request: RestaurantSearchRequest,
    current_user: dict = Depends(get_current_user),
    x_correlation_id: Optional[str] = Header(None)
):
    """Search restaurants by district and/or meal type."""
    
    try:
        # Call MCP service
        result = await mcp_service.search_restaurants(
            districts=request.districts,
            meal_types=request.meal_types,
            auth_token=current_user['token']
        )
        
        # Format response
        if result.get('success', False):
            return RestaurantSearchResponse(
                success=True,
                data=result['data'],
                metadata={
                    'correlation_id': x_correlation_id,
                    'user_id': current_user['user_id'],
                    'search_criteria': {
                        'districts': request.districts,
                        'meal_types': request.meal_types
                    }
                }
            )
        else:
            error_info = result.get('error', {})
            raise HTTPException(
                status_code=400,
                detail=error_info.get('message', 'Search failed')
            )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/api/v1/restaurants/districts")
async def get_available_districts(current_user: dict = Depends(get_current_user)):
    """Get list of available districts."""
    
    # This would typically call an MCP tool or cached data
    districts = {
        "Hong Kong Island": ["Central district", "Admiralty", "Causeway Bay", "Wan Chai"],
        "Kowloon": ["Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Jordan"],
        "New Territories": ["Sha Tin", "Tsuen Wan", "Tai Po", "Fanling"],
        "Lantau": ["Tung Chung", "Discovery Bay", "Mui Wo"]
    }
    
    return {
        "success": True,
        "data": {
            "districts": districts,
            "total_districts": sum(len(d) for d in districts.values())
        }
    }

@app.get("/api/v1/restaurants/meal-types")
async def get_meal_types():
    """Get available meal types and their time periods."""
    
    meal_types = {
        "breakfast": {
            "time_range": "07:00 - 11:29",
            "description": "Morning dining period"
        },
        "lunch": {
            "time_range": "11:30 - 17:29",
            "description": "Afternoon dining period"
        },
        "dinner": {
            "time_range": "17:30 - 22:30",
            "description": "Evening dining period"
        }
    }
    
    return {
        "success": True,
        "data": {
            "meal_types": meal_types
        }
    }

# Example client code for the microservice
class RestaurantSearchClient:
    """Client for the Restaurant Search microservice."""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    async def search_restaurants(self, districts: Optional[list] = None, 
                               meal_types: Optional[list] = None) -> Dict[str, Any]:
        """Search restaurants via microservice API."""
        
        import aiohttp
        
        payload = {}
        if districts:
            payload['districts'] = districts
        if meal_types:
            payload['meal_types'] = meal_types
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/restaurants/search",
                headers=self.headers,
                json=payload
            ) as response:
                return await response.json()
    
    async def get_districts(self) -> Dict[str, Any]:
        """Get available districts."""
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/restaurants/districts",
                headers=self.headers
            ) as response:
                return await response.json()

# Example usage
async def microservice_example():
    """Demonstrate microservice integration."""
    
    print("🔧 Microservice Integration Demo")
    print("=" * 50)
    
    # This would run the FastAPI server
    # uvicorn main:app --host 0.0.0.0 --port 8000
    
    # Example client usage
    client = RestaurantSearchClient(
        base_url="http://localhost:8000",
        auth_token="your-jwt-token"
    )
    
    # Test API calls
    try:
        # Get available districts
        districts_response = await client.get_districts()
        print(f"Available districts: {districts_response['data']['total_districts']}")
        
        # Search restaurants
        search_response = await client.search_restaurants(
            districts=["Central district"],
            meal_types=["breakfast"]
        )
        
        if search_response['success']:
            count = search_response['data']['count']
            print(f"Found {count} restaurants")
        else:
            print(f"Search failed: {search_response.get('error')}")
    
    except Exception as e:
        print(f"Client error: {e}")

if __name__ == "__main__":
    # Run FastAPI server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This comprehensive documentation provides detailed examples for integrating the Restaurant Search MCP tools with various frameworks and production environments, including authentication patterns, error handling, performance optimization, and enterprise-grade features.
#
# BedrockAgentCoreApp Entrypoint Integration Patterns

### Complete Entrypoint Implementation Example

```python
#!/usr/bin/env python3
"""Complete BedrockAgentCoreApp entrypoint implementation with comprehensive features."""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the BedrockAgentCoreApp
app = BedrockAgentCoreApp()

class EntrypointToolManager:
    """Manages MCP tools for the entrypoint."""
    
    def __init__(self, restaurant_service, district_service, time_service):
        self.restaurant_service = restaurant_service
        self.district_service = district_service
        self.time_service = time_service
    
    def create_tools(self) -> List[Tool]:
        """Create MCP tools with comprehensive schemas."""
        
        def search_by_district(districts: List[str]) -> str:
            """Search restaurants by district with detailed error handling."""
            try:
                logger.info(f"Entrypoint: Searching by districts: {districts}")
                results = self.restaurant_service.search_by_districts(districts)
                
                response_data = {
                    "success": True,
                    "query_type": "district_search",
                    "districts": districts,
                    "restaurant_count": len(results),
                    "restaurants": [restaurant.to_dict() for restaurant in results],
                    "metadata": {
                        "search_timestamp": datetime.now().isoformat(),
                        "tool_used": "search_restaurants_by_district"
                    }
                }
                
                return json.dumps(response_data, ensure_ascii=False, indent=2)
                
            except Exception as e:
                logger.error(f"District search error: {e}")
                error_response = {
                    "success": False,
                    "error": {
                        "type": "district_search_error",
                        "message": str(e),
                        "districts": districts
                    },
                    "suggestions": [
                        "Check district names are valid Hong Kong districts",
                        "Try: Central district, Tsim Sha Tsui, Causeway Bay",
                        "Use exact district names from configuration"
                    ]
                }
                return json.dumps(error_response, ensure_ascii=False, indent=2)
        
        def search_by_meal_type(meal_types: List[str]) -> str:
            """Search restaurants by meal type with operating hours analysis."""
            try:
                logger.info(f"Entrypoint: Searching by meal types: {meal_types}")
                results = self.restaurant_service.search_by_meal_types(meal_types)
                
                response_data = {
                    "success": True,
                    "query_type": "meal_type_search",
                    "meal_types": meal_types,
                    "restaurant_count": len(results),
                    "restaurants": [restaurant.to_dict() for restaurant in results],
                    "meal_time_info": {
                        "breakfast": "07:00 - 11:29",
                        "lunch": "11:30 - 17:29",
                        "dinner": "17:30 - 22:30"
                    },
                    "metadata": {
                        "search_timestamp": datetime.now().isoformat(),
                        "tool_used": "search_restaurants_by_meal_type"
                    }
                }
                
                return json.dumps(response_data, ensure_ascii=False, indent=2)
                
            except Exception as e:
                logger.error(f"Meal type search error: {e}")
                error_response = {
                    "success": False,
                    "error": {
                        "type": "meal_type_search_error",
                        "message": str(e),
                        "meal_types": meal_types
                    },
                    "suggestions": [
                        "Use valid meal types: breakfast, lunch, dinner",
                        "Check restaurant operating hours are available",
                        "Try different meal type combinations"
                    ]
                }
                return json.dumps(error_response, ensure_ascii=False, indent=2)
        
        def search_combined(districts: Optional[List[str]] = None, 
                          meal_types: Optional[List[str]] = None) -> str:
            """Combined search with flexible parameters."""
            try:
                logger.info(f"Entrypoint: Combined search - districts: {districts}, meal_types: {meal_types}")
                results = self.restaurant_service.search_combined(districts, meal_types)
                
                response_data = {
                    "success": True,
                    "query_type": "combined_search",
                    "districts": districts,
                    "meal_types": meal_types,
                    "restaurant_count": len(results),
                    "restaurants": [restaurant.to_dict() for restaurant in results],
                    "search_criteria": {
                        "location_filter": districts is not None,
                        "time_filter": meal_types is not None,
                        "filter_count": sum([districts is not None, meal_types is not None])
                    },
                    "metadata": {
                        "search_timestamp": datetime.now().isoformat(),
                        "tool_used": "search_restaurants_combined"
                    }
                }
                
                return json.dumps(response_data, ensure_ascii=False, indent=2)
                
            except Exception as e:
                logger.error(f"Combined search error: {e}")
                error_response = {
                    "success": False,
                    "error": {
                        "type": "combined_search_error",
                        "message": str(e),
                        "districts": districts,
                        "meal_types": meal_types
                    },
                    "suggestions": [
                        "Provide at least one search parameter",
                        "Check district and meal type values",
                        "Try simpler search criteria"
                    ]
                }
                return json.dumps(error_response, ensure_ascii=False, indent=2)
        
        # Create Tool objects with comprehensive schemas
        return [
            Tool(
                name="search_restaurants_by_district",
                description="""Search for restaurants in specific Hong Kong districts.
                
                This tool searches the restaurant database for establishments located in the specified districts.
                It supports multiple districts and returns comprehensive restaurant information including
                cuisine types, operating hours, price ranges, and location details.
                
                Available districts span across Hong Kong Island (Central district, Admiralty, Causeway Bay, 
                Wan Chai), Kowloon (Tsim Sha Tsui, Mong Kok, Yau Ma Tei), New Territories (Sha Tin, 
                Tsuen Wan, Tai Po), and Lantau (Tung Chung, Discovery Bay).
                
                Use this tool when users ask about restaurants in specific locations or areas.""",
                function=search_by_district,
                parameters={
                    "type": "object",
                    "properties": {
                        "districts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Hong Kong district names. Must use exact district names as they appear in the configuration. Examples: ['Central district'], ['Tsim Sha Tsui', 'Causeway Bay']",
                            "minItems": 1,
                            "maxItems": 10
                        }
                    },
                    "required": ["districts"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="search_restaurants_by_meal_type",
                description="""Search for restaurants by meal type based on operating hours analysis.
                
                This tool analyzes restaurant operating hours to determine which establishments serve
                specific meal types. It uses time-based filtering to match restaurants with the
                requested dining periods:
                
                - Breakfast (07:00-11:29): Morning dining, cafes, dim sum restaurants
                - Lunch (11:30-17:29): Business lunch venues, casual dining
                - Dinner (17:30-22:30): Evening dining, fine dining establishments
                
                The tool examines 'Mon-Fri', 'Sat-Sun', and 'Public Holiday' operating hours
                to determine meal availability. Restaurants with multiple time slots are included
                if any slot overlaps with the requested meal period.
                
                Use this tool when users ask about breakfast, lunch, or dinner places.""",
                function=search_by_meal_type,
                parameters={
                    "type": "object",
                    "properties": {
                        "meal_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["breakfast", "lunch", "dinner"]
                            },
                            "description": "List of meal types to search for. Each meal type corresponds to specific time periods: breakfast (07:00-11:29), lunch (11:30-17:29), dinner (17:30-22:30)",
                            "minItems": 1,
                            "maxItems": 3,
                            "uniqueItems": True
                        }
                    },
                    "required": ["meal_types"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="search_restaurants_combined",
                description="""Search for restaurants using both district and meal type filters.
                
                This is the most flexible search tool that can filter restaurants by location,
                dining time, or both criteria simultaneously. It provides the most precise
                search results when users specify both where they want to eat and when.
                
                The tool accepts optional parameters, allowing searches by:
                - District only: Find all restaurants in specific areas
                - Meal type only: Find restaurants serving specific meals across all districts
                - Both criteria: Find restaurants in specific districts that serve specific meals
                
                At least one parameter must be provided. When both are specified, only restaurants
                that match BOTH criteria are returned.
                
                Use this tool when users specify both location and meal preferences, or when
                you need the flexibility to search by either criterion.""",
                function=search_combined,
                parameters={
                    "type": "object",
                    "properties": {
                        "districts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of Hong Kong district names to filter by location",
                            "minItems": 1,
                            "maxItems": 10
                        },
                        "meal_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["breakfast", "lunch", "dinner"]
                            },
                            "description": "Optional list of meal types to filter by dining time",
                            "minItems": 1,
                            "maxItems": 3,
                            "uniqueItems": True
                        }
                    },
                    "additionalProperties": False,
                    "anyOf": [
                        {"required": ["districts"]},
                        {"required": ["meal_types"]},
                        {"required": ["districts", "meal_types"]}
                    ]
                }
            )
        ]

class EntrypointAgent:
    """Manages the Strands Agent for the entrypoint."""
    
    def __init__(self, tools: List[Tool]):
        self.tools = tools
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create and configure the Strands Agent."""
        
        system_prompt = """You are a knowledgeable and friendly restaurant search assistant for Hong Kong.
        You help users discover restaurants across Hong Kong's diverse districts and dining times.
        
        ## Your Expertise:
        You have comprehensive knowledge of Hong Kong's restaurant scene, including:
        
        **Geographic Coverage:**
        - Hong Kong Island: Admiralty, Central district, Causeway Bay, Wan Chai, North Point, Quarry Bay
        - Kowloon: Tsim Sha Tsui, Mong Kok, Yau Ma Tei, Jordan, Hung Hom, Kowloon Tong
        - New Territories: Sha Tin, Tsuen Wan, Tai Po, Fanling, Tuen Mun, Yuen Long
        - Lantau: Tung Chung, Discovery Bay, Mui Wo, Tai O
        
        **Dining Time Classifications:**
        - Breakfast (07:00-11:29): Morning dining, traditional tea houses, hotel breakfast venues
        - Lunch (11:30-17:29): Business lunch spots, dim sum restaurants, casual dining
        - Dinner (17:30-22:30): Fine dining, evening restaurants, night markets
        
        ## Tool Selection Strategy:
        Choose tools based on user query specificity:
        
        1. **search_restaurants_by_district**: When users mention specific locations
           - "restaurants in Central district"
           - "places to eat in Tsim Sha Tsui"
           - "food options in Causeway Bay and Admiralty"
        
        2. **search_restaurants_by_meal_type**: When users focus on dining time
           - "breakfast places"
           - "where to get lunch"
           - "dinner restaurants"
        
        3. **search_restaurants_combined**: When users specify both location and time
           - "breakfast in Central district"
           - "dinner restaurants in Tsim Sha Tsui"
           - "lunch options in Sha Tin"
        
        ## Response Guidelines:
        
        **Conversational Style:**
        - Be warm, helpful, and enthusiastic about Hong Kong's food scene
        - Use natural language that feels like talking to a local food expert
        - Include cultural context when relevant (e.g., dim sum traditions, night market culture)
        
        **Information Presentation:**
        - Present restaurant information clearly with key details
        - Include practical information: address, cuisine type, price range, hours
        - Format operating hours in user-friendly way
        - Highlight special features or popular dishes when available
        
        **Error Handling:**
        - If district names aren't recognized, suggest similar or nearby districts
        - When no results found, offer alternative suggestions or broader searches
        - Provide helpful guidance for refining searches
        
        **Proactive Assistance:**
        - Ask clarifying questions when requests are ambiguous
        - Suggest related searches or nearby options
        - Offer additional information about districts or meal types when helpful
        
        ## Cultural Context:
        - Understand Hong Kong dining culture (yum cha, late-night dining, food courts)
        - Recognize local terminology and food preferences
        - Provide context about different districts' dining characteristics
        
        Remember: Your goal is to help users discover amazing dining experiences in Hong Kong!"""
        
        return Agent(
            model="amazon.nova-pro-v1:0",
            system_prompt=system_prompt,
            tools=self.tools,
            temperature=0.1,  # Low temperature for consistent tool calling
            max_tokens=2048,  # Sufficient for detailed responses
            top_p=0.9,       # Focused but not overly restrictive
            tool_choice="auto"  # Let the model choose appropriate tools
        )
    
    def process_query(self, user_prompt: str) -> str:
        """Process user query with the Strands Agent."""
        try:
            logger.info(f"Processing query: {user_prompt[:100]}...")
            response = self.agent.run(user_prompt)
            logger.info("Agent response generated successfully")
            return response
        except Exception as e:
            logger.error(f"Agent processing error: {e}")
            raise

class EntrypointResponseFormatter:
    """Handles response formatting for the entrypoint."""
    
    @staticmethod
    def format_success_response(agent_response: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Format successful response."""
        response_data = {
            "success": True,
            "response": agent_response,
            "timestamp": datetime.now().isoformat(),
            "agent_type": "restaurant_search_assistant",
            "version": "2.0.0",
            "entrypoint_type": "BedrockAgentCoreApp"
        }
        
        if metadata:
            response_data["metadata"] = metadata
        
        return json.dumps(response_data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def format_error_response(error_message: str, error_type: str = "processing_error", 
                            user_friendly_message: Optional[str] = None) -> str:
        """Format error response with user guidance."""
        
        if not user_friendly_message:
            user_friendly_message = EntrypointResponseFormatter._generate_user_message(error_type, error_message)
        
        error_data = {
            "success": False,
            "response": user_friendly_message,
            "error": {
                "message": error_message,
                "type": error_type,
                "user_message": user_friendly_message
            },
            "timestamp": datetime.now().isoformat(),
            "agent_type": "restaurant_search_assistant",
            "suggestions": EntrypointResponseFormatter._get_error_suggestions(error_type),
            "entrypoint_type": "BedrockAgentCoreApp"
        }
        
        return json.dumps(error_data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def _generate_user_message(error_type: str, error_message: str) -> str:
        """Generate user-friendly error messages."""
        
        if "district" in error_message.lower():
            return ("I don't recognize that district name. Could you try a well-known Hong Kong "
                   "district like Central district, Tsim Sha Tsui, or Causeway Bay?")
        elif "meal" in error_message.lower():
            return ("Please specify a valid meal type: breakfast (morning), lunch (afternoon), "
                   "or dinner (evening).")
        elif "payload" in error_message.lower():
            return ("I'm having trouble understanding your request. Could you please ask about "
                   "restaurants in Hong Kong using natural language?")
        elif error_type == "system_error":
            return ("I'm experiencing technical difficulties right now. Please try again in a "
                   "moment, or try asking about restaurants in a different way.")
        else:
            return ("I couldn't process your request. Could you please rephrase your question "
                   "about Hong Kong restaurants?")
    
    @staticmethod
    def _get_error_suggestions(error_type: str) -> List[str]:
        """Get contextual suggestions based on error type."""
        
        suggestions_map = {
            "validation_error": [
                "Try asking about restaurants in a specific Hong Kong district",
                "Specify a meal type: breakfast, lunch, or dinner",
                "Use district names like 'Central district' or 'Tsim Sha Tsui'",
                "Example: 'Find breakfast places in Central district'"
            ],
            "processing_error": [
                "Try rephrasing your question about restaurants",
                "Be more specific about the location or meal type you want",
                "Ask about a different district or dining time",
                "Example: 'Show me dinner restaurants in Causeway Bay'"
            ],
            "system_error": [
                "Please try again in a few moments",
                "Try a simpler query first",
                "Check your connection and retry",
                "Contact support if the problem persists"
            ]
        }
        
        return suggestions_map.get(error_type, [
            "Please try rephrasing your question about restaurants",
            "Be more specific about what you're looking for",
            "Ask about Hong Kong restaurants using natural language"
        ])

# Initialize services (these would be imported from your services)
from services.restaurant_service import RestaurantService
from services.district_service import DistrictService
from services.time_service import TimeService
from services.data_access import DataAccessClient

# Initialize services
data_access_client = DataAccessClient()
district_service = DistrictService()
time_service = TimeService()
restaurant_service = RestaurantService(data_access_client, district_service, time_service)

# Load district configuration
try:
    district_service.load_district_config()
    logger.info("District configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load district configuration: {e}")
    raise

# Initialize entrypoint components
tool_manager = EntrypointToolManager(restaurant_service, district_service, time_service)
tools = tool_manager.create_tools()
entrypoint_agent = EntrypointAgent(tools)
response_formatter = EntrypointResponseFormatter()

def extract_user_prompt(payload: Dict[str, Any]) -> str:
    """Extract user prompt from various payload formats."""
    
    # Handle different AgentCore Runtime payload structures
    if "input" in payload:
        if isinstance(payload["input"], dict):
            if "prompt" in payload["input"]:
                return payload["input"]["prompt"]
            elif "message" in payload["input"]:
                return payload["input"]["message"]
        elif isinstance(payload["input"], str):
            return payload["input"]
    
    if "prompt" in payload:
        return payload["prompt"]
    
    if "message" in payload:
        return payload["message"]
    
    # Fallback: look for any string value
    for key, value in payload.items():
        if isinstance(value, str) and len(value.strip()) > 0:
            logger.warning(f"Using fallback prompt extraction from key: {key}")
            return value
    
    raise ValueError("No valid prompt found in payload structure")

@app.entrypoint
def process_request(payload: Dict[str, Any]) -> str:
    """Main entrypoint for processing AgentCore Runtime requests."""
    
    user_prompt = None
    
    try:
        logger.info(f"Entrypoint: Processing request with payload keys: {list(payload.keys())}")
        
        # Extract user prompt
        user_prompt = extract_user_prompt(payload)
        logger.info(f"Entrypoint: Extracted prompt: {user_prompt[:100]}..." if len(user_prompt) > 100 else f"Entrypoint: Extracted prompt: {user_prompt}")
        
        # Process with Strands Agent
        agent_response = entrypoint_agent.process_query(user_prompt)
        
        # Create metadata
        metadata = {
            "prompt_length": len(user_prompt),
            "processing_timestamp": datetime.now().isoformat(),
            "tools_available": [tool.name for tool in tools],
            "agent_model": "amazon.nova-pro-v1:0",
            "entrypoint_version": "2.0.0"
        }
        
        # Format and return response
        formatted_response = response_formatter.format_success_response(agent_response, metadata)
        
        logger.info("Entrypoint: Request processed successfully")
        return formatted_response
        
    except ValueError as e:
        logger.error(f"Entrypoint: Payload validation error: {e}")
        return response_formatter.format_error_response(
            error_message=str(e),
            error_type="validation_error"
        )
        
    except Exception as e:
        logger.error(f"Entrypoint: Unexpected error: {e}")
        logger.error(f"Entrypoint: Traceback: {traceback.format_exc()}")
        return response_formatter.format_error_response(
            error_message=str(e),
            error_type="system_error"
        )

if __name__ == "__main__":
    logger.info("Starting Restaurant Search BedrockAgentCoreApp Entrypoint")
    app.run()
```

### Entrypoint Testing Framework

```python
#!/usr/bin/env python3
"""Comprehensive testing framework for BedrockAgentCoreApp entrypoint."""

import json
import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class EntrypointTestCase:
    """Test case for entrypoint testing."""
    name: str
    payload: Dict[str, Any]
    expected_success: bool
    expected_tool: str = None
    expected_params: Dict[str, Any] = None
    description: str = ""

class EntrypointTester:
    """Comprehensive tester for BedrockAgentCoreApp entrypoint."""
    
    def __init__(self, entrypoint_function):
        self.entrypoint_function = entrypoint_function
        self.test_results = []
    
    def create_test_cases(self) -> List[EntrypointTestCase]:
        """Create comprehensive test cases for entrypoint."""
        
        return [
            # Successful cases
            EntrypointTestCase(
                name="District Search - Single District",
                payload={"input": {"prompt": "Find restaurants in Central district"}},
                expected_success=True,
                expected_tool="search_restaurants_by_district",
                expected_params={"districts": ["Central district"]},
                description="Test basic district search functionality"
            ),
            EntrypointTestCase(
                name="District Search - Multiple Districts",
                payload={"input": {"prompt": "Show me restaurants in Tsim Sha Tsui and Causeway Bay"}},
                expected_success=True,
                expected_tool="search_restaurants_by_district",
                expected_params={"districts": ["Tsim Sha Tsui", "Causeway Bay"]},
                description="Test multiple district search"
            ),
            EntrypointTestCase(
                name="Meal Type Search - Breakfast",
                payload={"input": {"prompt": "I want breakfast places"}},
                expected_success=True,
                expected_tool="search_restaurants_by_meal_type",
                expected_params={"meal_types": ["breakfast"]},
                description="Test meal type search for breakfast"
            ),
            EntrypointTestCase(
                name="Combined Search - District and Meal",
                payload={"input": {"prompt": "Find dinner restaurants in Central district"}},
                expected_success=True,
                expected_tool="search_restaurants_combined",
                expected_params={"districts": ["Central district"], "meal_types": ["dinner"]},
                description="Test combined search with both criteria"
            ),
            EntrypointTestCase(
                name="Natural Language - Conversational",
                payload={"input": {"prompt": "Hi! I'm looking for a good lunch place in Admiralty"}},
                expected_success=True,
                expected_tool="search_restaurants_combined",
                expected_params={"districts": ["Admiralty"], "meal_types": ["lunch"]},
                description="Test conversational natural language processing"
            ),
            
            # Alternative payload formats
            EntrypointTestCase(
                name="Alternative Payload - Direct Prompt",
                payload={"prompt": "Show me breakfast places in Wan Chai"},
                expected_success=True,
                description="Test alternative payload structure with direct prompt"
            ),
            EntrypointTestCase(
                name="Alternative Payload - Message Field",
                payload={"input": {"message": "What dinner options are in Mong Kok?"}},
                expected_success=True,
                description="Test payload with message field instead of prompt"
            ),
            
            # Error cases
            EntrypointTestCase(
                name="Invalid District Name",
                payload={"input": {"prompt": "Find restaurants in NonexistentDistrict"}},
                expected_success=False,
                description="Test handling of invalid district names"
            ),
            EntrypointTestCase(
                name="Empty Payload",
                payload={},
                expected_success=False,
                description="Test handling of empty payload"
            ),
            EntrypointTestCase(
                name="Invalid Payload Structure",
                payload={"random_field": "random_value"},
                expected_success=False,
                description="Test handling of invalid payload structure"
            ),
            EntrypointTestCase(
                name="Ambiguous Query",
                payload={"input": {"prompt": "food"}},
                expected_success=True,  # Should succeed but ask for clarification
                description="Test handling of ambiguous queries"
            )
        ]
    
    def run_test_case(self, test_case: EntrypointTestCase) -> Dict[str, Any]:
        """Run a single test case."""
        
        print(f"\n🧪 Running: {test_case.name}")
        print(f"   Description: {test_case.description}")
        print(f"   Payload: {test_case.payload}")
        
        start_time = time.time()
        
        try:
            # Call entrypoint function
            response_str = self.entrypoint_function(test_case.payload)
            response = json.loads(response_str)
            
            execution_time = time.time() - start_time
            
            # Analyze response
            success = response.get('success', False)
            
            result = {
                'test_name': test_case.name,
                'expected_success': test_case.expected_success,
                'actual_success': success,
                'execution_time': execution_time,
                'response': response,
                'passed': success == test_case.expected_success
            }
            
            # Additional validation for successful cases
            if success and test_case.expected_tool:
                # This would require more sophisticated analysis of the response
                # to determine which tool was actually called
                pass
            
            # Print result
            if result['passed']:
                print(f"   ✅ PASSED ({execution_time:.3f}s)")
                if success:
                    response_preview = response.get('response', '')[:100]
                    print(f"   Response: {response_preview}...")
                else:
                    error_msg = response.get('error', {}).get('message', 'Unknown error')
                    print(f"   Expected error: {error_msg}")
            else:
                print(f"   ❌ FAILED ({execution_time:.3f}s)")
                print(f"   Expected success: {test_case.expected_success}")
                print(f"   Actual success: {success}")
                if not success:
                    error_msg = response.get('error', {}).get('message', 'Unknown error')
                    print(f"   Error: {error_msg}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = {
                'test_name': test_case.name,
                'expected_success': test_case.expected_success,
                'actual_success': False,
                'execution_time': execution_time,
                'exception': str(e),
                'passed': not test_case.expected_success  # Pass if we expected failure
            }
            
            print(f"   ❌ EXCEPTION ({execution_time:.3f}s): {e}")
            
            return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and generate report."""
        
        print("🚀 Starting BedrockAgentCoreApp Entrypoint Test Suite")
        print("=" * 60)
        
        test_cases = self.create_test_cases()
        results = []
        
        for test_case in test_cases:
            result = self.run_test_case(test_case)
            results.append(result)
            self.test_results.append(result)
        
        # Generate summary
        total_tests = len(results)
        passed_tests = len([r for r in results if r['passed']])
        failed_tests = total_tests - passed_tests
        
        avg_execution_time = sum(r['execution_time'] for r in results) / total_tests
        
        print(f"\n📊 Test Summary")
        print("=" * 30)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Average Execution Time: {avg_execution_time:.3f}s")
        
        # Show failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in results:
                if not result['passed']:
                    print(f"   • {result['test_name']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'avg_execution_time': avg_execution_time,
            'results': results
        }
    
    def generate_test_report(self, output_file: str = "entrypoint_test_report.json"):
        """Generate detailed test report."""
        
        report = {
            'test_suite': 'BedrockAgentCoreApp Entrypoint Tests',
            'timestamp': time.time(),
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results if r['passed']]),
                'failed_tests': len([r for r in self.test_results if not r['passed']])
            },
            'results': self.test_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Test report saved to: {output_file}")

# Example usage
def test_entrypoint_integration():
    """Test the entrypoint integration."""
    
    # Import the entrypoint function (this would be from your main.py)
    from main import process_request
    
    # Create tester
    tester = EntrypointTester(process_request)
    
    # Run tests
    summary = tester.run_all_tests()
    
    # Generate report
    tester.generate_test_report()
    
    return summary

if __name__ == "__main__":
    test_entrypoint_integration()
```

This comprehensive documentation provides detailed examples for integrating MCP tools with BedrockAgentCoreApp entrypoint, including complete implementation patterns, testing frameworks, and production-ready code examples with authentication and error handling.