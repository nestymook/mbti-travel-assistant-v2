# Authentication Usage Examples - Restaurant Reasoning MCP Server

This document provides comprehensive examples for implementing authentication with the Restaurant Reasoning MCP server using AWS Cognito and JWT tokens. The reasoning server reuses the existing authentication infrastructure from the restaurant search MCP server.

## Table of Contents

1. [SRP Authentication Examples for Reasoning](#srp-authentication-examples-for-reasoning)
2. [JWT Token Management for Reasoning Operations](#jwt-token-management-for-reasoning-operations)
3. [Reasoning MCP Client Integration](#reasoning-mcp-client-integration)
4. [Error Handling Examples for Reasoning](#error-handling-examples-for-reasoning)
5. [Token Refresh Scenarios for Reasoning](#token-refresh-scenarios-for-reasoning)
6. [Production Integration Patterns for Reasoning](#production-integration-patterns-for-reasoning)

## SRP Authentication Examples for Reasoning

### Basic SRP Authentication for Reasoning Server

```python
#!/usr/bin/env python3
"""
Basic SRP authentication example for Restaurant Reasoning MCP server.
"""

import json
import sys
from services.auth_service import CognitoAuthenticator, AuthenticationError

def basic_reasoning_authentication_example():
    """Demonstrate basic SRP authentication flow for reasoning server."""
    
    # Load Cognito configuration (reused from restaurant search server)
    try:
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: cognito_config.json not found. Copy from restaurant-search-mcp or run setup_cognito.py.")
        return False
    
    # Initialize authenticator for reasoning server
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Authentication credentials
    username = config['test_user']['email']
    password = "TempPass123!"  # Use actual password
    
    try:
        print(f"🧠 Authenticating user for reasoning server: {username}")
        
        # Perform SRP authentication for reasoning operations
        tokens = authenticator.authenticate_user(username, password)
        
        print("✅ Reasoning server authentication successful!")
        print(f"Token Type: {tokens.token_type}")
        print(f"Access Token: {tokens.access_token[:50]}...")
        print(f"ID Token: {tokens.id_token[:50]}...")
        print(f"Expires In: {tokens.expires_in} seconds")
        print("🎯 Ready for restaurant sentiment analysis and recommendations!")
        
        return tokens
        
    except AuthenticationError as e:
        print(f"❌ Reasoning server authentication failed:")
        print(f"  Error Type: {e.error_type}")
        print(f"  Error Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  Suggested Action: {e.suggested_action}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in reasoning authentication: {e}")
        return None

if __name__ == "__main__":
    basic_reasoning_authentication_example()
```
### I
nteractive Authentication Script for Reasoning Operations

```python
#!/usr/bin/env python3
"""
Interactive authentication script for reasoning operations with user input.
"""

import getpass
import json
from services.auth_service import CognitoAuthenticator, AuthenticationError

def interactive_reasoning_authentication():
    """Interactive authentication for reasoning operations with user input."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    print("🧠 Restaurant Reasoning MCP Authentication")
    print("=" * 45)
    print("🎯 Authenticate to access sentiment analysis and recommendation tools")
    
    # Get credentials from user
    username = input("Username (email): ").strip()
    password = getpass.getpass("Password: ")
    
    try:
        print("\n🔄 Authenticating for reasoning operations...")
        tokens = authenticator.authenticate_user(username, password)
        
        print("✅ Reasoning authentication successful!")
        print(f"Welcome to Restaurant Reasoning, {username}!")
        
        # Validate session for reasoning context
        user_context = authenticator.validate_user_session(tokens.access_token)
        print(f"User ID: {user_context.user_id}")
        print(f"Email: {user_context.email}")
        print("🎯 Ready for sentiment analysis and recommendations!")
        
        # Save tokens for reasoning operations (in production, use secure storage)
        token_data = {
            'access_token': tokens.access_token,
            'id_token': tokens.id_token,
            'refresh_token': tokens.refresh_token,
            'expires_in': tokens.expires_in,
            'token_type': tokens.token_type,
            'reasoning_context': True
        }
        
        with open('reasoning_user_tokens.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("💾 Reasoning tokens saved to reasoning_user_tokens.json")
        return tokens
        
    except AuthenticationError as e:
        print(f"\n❌ Reasoning authentication failed: {e.message}")
        print(f"💡 Suggestion: {e.suggested_action}")
        return None

if __name__ == "__main__":
    interactive_reasoning_authentication()
```

### Batch User Authentication for Reasoning Operations

```python
#!/usr/bin/env python3
"""
Batch authentication for multiple users accessing reasoning operations.
"""

import json
import csv
from typing import List, Dict
from services.auth_service import CognitoAuthenticator, AuthenticationError

def batch_reasoning_authentication(users_file: str = "reasoning_test_users.csv"):
    """Authenticate multiple users for reasoning operations from CSV file."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    results = []
    
    try:
        with open(users_file, 'r') as f:
            reader = csv.DictReader(f)
            users = list(reader)
    except FileNotFoundError:
        print(f"❌ Reasoning users file not found: {users_file}")
        return []
    
    print(f"🧠 Batch authenticating {len(users)} users for reasoning operations...")
    
    for i, user in enumerate(users, 1):
        username = user['username']
        password = user['password']
        
        print(f"\n[{i}/{len(users)}] Authenticating for reasoning: {username}")
        
        try:
            tokens = authenticator.authenticate_user(username, password)
            
            result = {
                'username': username,
                'status': 'success',
                'user_id': None,
                'email': None,
                'reasoning_ready': True,
                'error': None
            }
            
            # Get user info for reasoning context
            try:
                user_context = authenticator.validate_user_session(tokens.access_token)
                result['user_id'] = user_context.user_id
                result['email'] = user_context.email
            except Exception as e:
                result['error'] = f"Session validation failed: {e}"
                result['reasoning_ready'] = False
            
            print(f"  ✅ Success - User ID: {result['user_id']} (Reasoning Ready)")
            
        except AuthenticationError as e:
            result = {
                'username': username,
                'status': 'failed',
                'user_id': None,
                'email': None,
                'reasoning_ready': False,
                'error': f"{e.error_type}: {e.message}"
            }
            print(f"  ❌ Failed - {e.error_type}")
        
        results.append(result)
    
    # Save results
    with open('batch_reasoning_auth_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    successful = len([r for r in results if r['status'] == 'success'])
    reasoning_ready = len([r for r in results if r['reasoning_ready']])
    failed = len(results) - successful
    
    print(f"\n📊 Batch Reasoning Authentication Summary:")
    print(f"  Total Users: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Reasoning Ready: {reasoning_ready}")
    print(f"  Failed: {failed}")
    print(f"  Results saved to: batch_reasoning_auth_results.json")
    
    return results

if __name__ == "__main__":
    # Example CSV format for reasoning users:
    # username,password
    # reasoning_user1@example.com,Password123!
    # reasoning_user2@example.com,Password456!
    
    batch_reasoning_authentication()
```

## JWT Token Management for Reasoning Operations

### Token Validation Example for Reasoning

```python
#!/usr/bin/env python3
"""
JWT token validation examples for reasoning operations.
"""

import json
import asyncio
from services.auth_service import TokenValidator, AuthenticationError

async def reasoning_token_validation_example():
    """Demonstrate JWT token validation for reasoning operations."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize token validator for reasoning
    validator_config = {
        'user_pool_id': config['user_pool']['user_pool_id'],
        'client_id': config['app_client']['client_id'],
        'region': config['region'],
        'discovery_url': config['discovery_url']
    }
    
    validator = TokenValidator(validator_config)
    
    # Load test token (from previous reasoning authentication)
    try:
        with open('reasoning_user_tokens.json', 'r') as f:
            token_data = json.load(f)
        access_token = token_data['access_token']
    except FileNotFoundError:
        print("❌ No reasoning tokens found. Run reasoning authentication example first.")
        return
    
    try:
        print("🔍 Validating JWT token for reasoning operations...")
        
        # Validate token for reasoning context
        claims = await validator.validate_jwt_token(access_token)
        
        print("✅ Reasoning token validation successful!")
        print(f"User ID: {claims.user_id}")
        print(f"Username: {claims.username}")
        print(f"Email: {claims.email}")
        print(f"Client ID: {claims.client_id}")
        print(f"Token Use: {claims.token_use}")
        print(f"Issued At: {claims.iat}")
        print(f"Expires At: {claims.exp}")
        print("🎯 Token valid for reasoning operations!")
        
        # Check if token is expired
        if validator.is_token_expired(access_token):
            print("⚠️ Token is expired - refresh needed for reasoning operations")
        else:
            print("✅ Token is valid and ready for sentiment analysis and recommendations")
        
    except AuthenticationError as e:
        print(f"❌ Reasoning token validation failed:")
        print(f"  Error Type: {e.error_type}")
        print(f"  Error Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  Suggested Action: {e.suggested_action}")

if __name__ == "__main__":
    asyncio.run(reasoning_token_validation_example())
```

### Token Refresh Example for Reasoning Operations

```python
#!/usr/bin/env python3
"""
Token refresh example for reasoning operations using refresh tokens.
"""

import json
import time
from services.auth_service import CognitoAuthenticator, AuthenticationError

def reasoning_token_refresh_example():
    """Demonstrate token refresh flow for reasoning operations."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Load existing reasoning tokens
    try:
        with open('reasoning_user_tokens.json', 'r') as f:
            token_data = json.load(f)
        refresh_token = token_data['refresh_token']
    except FileNotFoundError:
        print("❌ No reasoning tokens found. Authenticate first.")
        return
    
    try:
        print("🔄 Refreshing access token for reasoning operations...")
        
        # Refresh tokens for continued reasoning access
        new_tokens = authenticator.refresh_token(refresh_token)
        
        print("✅ Reasoning token refresh successful!")
        print(f"New Access Token: {new_tokens.access_token[:50]}...")
        print(f"New ID Token: {new_tokens.id_token[:50]}...")
        print(f"Expires In: {new_tokens.expires_in} seconds")
        print("🎯 Ready for continued reasoning operations!")
        
        # Update stored reasoning tokens
        token_data.update({
            'access_token': new_tokens.access_token,
            'id_token': new_tokens.id_token,
            'expires_in': new_tokens.expires_in,
            'refreshed_at': time.time(),
            'reasoning_context': True
        })
        
        with open('reasoning_user_tokens.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("💾 Updated reasoning tokens saved")
        
        return new_tokens
        
    except AuthenticationError as e:
        print(f"❌ Reasoning token refresh failed:")
        print(f"  Error Type: {e.error_type}")
        print(f"  Message: {e.message}")
        print(f"  Suggested Action: {e.suggested_action}")
        
        if e.error_code == 'NotAuthorizedException':
            print("💡 Refresh token may be expired. Re-authentication required for reasoning operations.")
        
        return None

if __name__ == "__main__":
    reasoning_token_refresh_example()
```

## Reasoning MCP Client Integration

### Basic Authenticated Reasoning MCP Client

```python
#!/usr/bin/env python3
"""
Basic authenticated MCP client example for reasoning operations.
"""

import json
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

async def authenticated_reasoning_mcp_client():
    """Example of MCP client with JWT authentication for reasoning operations."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Load AgentCore deployment configuration for reasoning server
    try:
        with open('reasoning_deployment_config.json', 'r') as f:
            deployment_config = json.load(f)
        
        # Extract reasoning AgentCore endpoint URL
        agent_arn = deployment_config['launch_result']['agent_arn']
        # Construct reasoning endpoint URL
        mcp_url = f"https://{agent_arn.split('/')[-1]}.bedrock-agentcore.us-east-1.amazonaws.com"
        
    except FileNotFoundError:
        print("❌ Reasoning deployment config not found. Deploy reasoning AgentCore first.")
        return
    
    # Authenticate and get tokens for reasoning
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    try:
        # Load existing tokens or authenticate for reasoning
        try:
            with open('reasoning_user_tokens.json', 'r') as f:
                token_data = json.load(f)
            access_token = token_data['access_token']
            
            # Check if token is expired and refresh if needed
            if authenticator.validate_user_session(access_token):
                print("✅ Using existing valid token for reasoning operations")
            
        except (FileNotFoundError, Exception):
            print("🔐 Authenticating for reasoning operations...")
            tokens = authenticator.authenticate_user(
                config['test_user']['email'],
                "TempPass123!"  # Use actual password
            )
            access_token = tokens.access_token
        
        # Set up authenticated headers for reasoning
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔗 Connecting to reasoning MCP server: {mcp_url}")
        
        # Sample restaurant data for reasoning operations
        sample_restaurants = [
            {
                "id": "rest_001",
                "name": "Central Gourmet",
                "address": "123 Central Street, Central",
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "meal_type": ["breakfast", "lunch"],
                "district": "Central district",
                "price_range": "$$$"
            },
            {
                "id": "rest_002",
                "name": "Tsim Sha Tsui Delight",
                "address": "456 Nathan Road, TST",
                "sentiment": {"likes": 78, "dislikes": 15, "neutral": 7},
                "meal_type": ["lunch", "dinner"],
                "district": "Tsim Sha Tsui",
                "price_range": "$$"
            },
            {
                "id": "rest_003",
                "name": "Causeway Bay Bistro",
                "address": "789 Hennessy Road, CWB",
                "sentiment": {"likes": 82, "dislikes": 12, "neutral": 6},
                "meal_type": ["breakfast", "dinner"],
                "district": "Causeway Bay",
                "price_range": "$$"
            }
        ]
        
        # Connect to reasoning MCP server with authentication
        async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialize reasoning session
                await session.initialize()
                print("✅ Reasoning MCP session initialized")
                
                # List available reasoning tools
                tools_response = await session.list_tools()
                tools = [tool.name for tool in tools_response.tools]
                print(f"🧠 Available reasoning tools: {tools}")
                
                # Test restaurant recommendation with sentiment analysis
                print("\n🎯 Testing restaurant recommendation by sentiment likes...")
                result = await session.call_tool(
                    "recommend_restaurants",
                    {
                        "restaurants": sample_restaurants,
                        "ranking_method": "sentiment_likes"
                    }
                )
                
                print("✅ Sentiment-based recommendation completed!")
                print(f"Result: {result.content[0].text[:300]}...")
                
                # Test restaurant recommendation with combined sentiment
                print("\n🎯 Testing restaurant recommendation by combined sentiment...")
                result = await session.call_tool(
                    "recommend_restaurants",
                    {
                        "restaurants": sample_restaurants,
                        "ranking_method": "combined_sentiment"
                    }
                )
                
                print("✅ Combined sentiment recommendation completed!")
                print(f"Result: {result.content[0].text[:300]}...")
                
                # Test sentiment analysis only
                print("\n📊 Testing sentiment analysis without recommendation...")
                result = await session.call_tool(
                    "analyze_restaurant_sentiment",
                    {"restaurants": sample_restaurants}
                )
                
                print("✅ Sentiment analysis completed!")
                print(f"Result: {result.content[0].text[:300]}...")
                
    except Exception as e:
        print(f"❌ Reasoning MCP client error: {e}")

if __name__ == "__main__":
    asyncio.run(authenticated_reasoning_mcp_client())
```##
# Advanced Reasoning MCP Client with Error Handling

```python
#!/usr/bin/env python3
"""
Advanced MCP client with comprehensive error handling for reasoning operations.
"""

import json
import asyncio
import time
from typing import Optional, Dict, Any
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator, AuthenticationError

class AuthenticatedReasoningMCPClient:
    """Advanced MCP client with authentication and error handling for reasoning operations."""
    
    def __init__(self, config_file: str = 'cognito_config.json'):
        """Initialize the authenticated reasoning MCP client."""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.config['user_pool']['user_pool_id'],
            client_id=self.config['app_client']['client_id'],
            region=self.config['region']
        )
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
    async def ensure_reasoning_authenticated(self) -> bool:
        """Ensure we have a valid access token for reasoning operations."""
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expires_at:
                if time.time() < self.token_expires_at - 300:  # 5 min buffer
                    return True
            
            # Try to load existing reasoning tokens
            try:
                with open('reasoning_user_tokens.json', 'r') as f:
                    token_data = json.load(f)
                
                # Try to refresh token for reasoning
                if 'refresh_token' in token_data:
                    print("🔄 Refreshing access token for reasoning operations...")
                    new_tokens = self.authenticator.refresh_token(
                        token_data['refresh_token']
                    )
                    
                    self.access_token = new_tokens.access_token
                    self.token_expires_at = time.time() + new_tokens.expires_in
                    
                    # Update stored reasoning tokens
                    token_data.update({
                        'access_token': new_tokens.access_token,
                        'id_token': new_tokens.id_token,
                        'expires_in': new_tokens.expires_in,
                        'refreshed_at': time.time(),
                        'reasoning_context': True
                    })
                    
                    with open('reasoning_user_tokens.json', 'w') as f:
                        json.dump(token_data, f, indent=2)
                    
                    print("✅ Reasoning token refreshed successfully")
                    return True
                    
            except (FileNotFoundError, AuthenticationError):
                pass
            
            # Fall back to full authentication for reasoning
            print("🔐 Performing full authentication for reasoning operations...")
            tokens = self.authenticator.authenticate_user(
                self.config['test_user']['email'],
                "TempPass123!"  # Use actual password
            )
            
            self.access_token = tokens.access_token
            self.token_expires_at = time.time() + tokens.expires_in
            
            print("✅ Reasoning authentication successful")
            return True
            
        except AuthenticationError as e:
            print(f"❌ Reasoning authentication failed: {e.message}")
            return False
        except Exception as e:
            print(f"❌ Unexpected reasoning authentication error: {e}")
            return False
    
    async def call_reasoning_mcp_tool(self, tool_name: str, parameters: Dict[str, Any], 
                                    mcp_url: str) -> Optional[Dict]:
        """Call a reasoning MCP tool with authentication and error handling."""
        
        # Ensure we're authenticated for reasoning
        if not await self.ensure_reasoning_authenticated():
            return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"🔗 Connecting to reasoning MCP server (attempt {retry_count + 1})...")
                
                async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        print(f"🧠 Calling reasoning tool: {tool_name}")
                        result = await session.call_tool(tool_name, parameters)
                        
                        return {
                            'success': True,
                            'result': result.content[0].text if result.content else None,
                            'tool_name': tool_name,
                            'parameters': parameters,
                            'reasoning_operation': True
                        }
                        
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                print(f"❌ Reasoning MCP call failed (attempt {retry_count}): {error_msg}")
                
                # Check if it's an authentication error
                if "401" in error_msg or "Unauthorized" in error_msg:
                    print("🔄 Authentication error, refreshing token for reasoning...")
                    self.access_token = None
                    self.token_expires_at = None
                    
                    if not await self.ensure_reasoning_authenticated():
                        print("❌ Failed to refresh reasoning authentication")
                        break
                    
                    headers['Authorization'] = f'Bearer {self.access_token}'
                
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    print(f"⏳ Waiting {wait_time}s before reasoning retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Max retries ({max_retries}) exceeded for reasoning operation")
        
        return {
            'success': False,
            'error': f"Reasoning operation failed after {max_retries} attempts",
            'tool_name': tool_name,
            'parameters': parameters,
            'reasoning_operation': True
        }

async def advanced_reasoning_mcp_example():
    """Demonstrate advanced reasoning MCP client usage."""
    
    client = AuthenticatedReasoningMCPClient()
    
    # Load reasoning deployment configuration to get MCP URL
    try:
        with open('reasoning_deployment_config.json', 'r') as f:
            deployment_config = json.load(f)
        
        agent_arn = deployment_config['launch_result']['agent_arn']
        mcp_url = f"https://{agent_arn.split('/')[-1]}.bedrock-agentcore.us-east-1.amazonaws.com"
        
    except FileNotFoundError:
        print("❌ Reasoning deployment config not found")
        return
    
    # Sample restaurant data for comprehensive reasoning tests
    test_restaurants = [
        {
            "id": "rest_001",
            "name": "Premium Central Dining",
            "address": "1 Central Plaza, Central",
            "sentiment": {"likes": 120, "dislikes": 8, "neutral": 12},
            "meal_type": ["breakfast", "lunch", "dinner"],
            "district": "Central district",
            "price_range": "$$$$"
        },
        {
            "id": "rest_002",
            "name": "TST Family Restaurant",
            "address": "88 Nathan Road, TST",
            "sentiment": {"likes": 95, "dislikes": 25, "neutral": 15},
            "meal_type": ["lunch", "dinner"],
            "district": "Tsim Sha Tsui",
            "price_range": "$$"
        },
        {
            "id": "rest_003",
            "name": "Causeway Bay Express",
            "address": "200 Hennessy Road, CWB",
            "sentiment": {"likes": 65, "dislikes": 30, "neutral": 25},
            "meal_type": ["breakfast", "lunch"],
            "district": "Causeway Bay",
            "price_range": "$"
        },
        {
            "id": "rest_004",
            "name": "Admiralty Fine Dining",
            "address": "5 Admiralty Centre, Admiralty",
            "sentiment": {"likes": 110, "dislikes": 5, "neutral": 10},
            "meal_type": ["dinner"],
            "district": "Admiralty",
            "price_range": "$$$$$"
        }
    ]
    
    # Test multiple reasoning scenarios
    test_cases = [
        {
            'tool': 'recommend_restaurants',
            'params': {
                'restaurants': test_restaurants,
                'ranking_method': 'sentiment_likes'
            },
            'description': 'Recommendation by sentiment likes'
        },
        {
            'tool': 'recommend_restaurants',
            'params': {
                'restaurants': test_restaurants,
                'ranking_method': 'combined_sentiment'
            },
            'description': 'Recommendation by combined sentiment'
        },
        {
            'tool': 'analyze_restaurant_sentiment',
            'params': {
                'restaurants': test_restaurants
            },
            'description': 'Sentiment analysis without recommendation'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing {test_case['description']}...")
        
        result = await client.call_reasoning_mcp_tool(
            test_case['tool'],
            test_case['params'],
            mcp_url
        )
        
        results.append({
            **result,
            'test_description': test_case['description']
        })
        
        if result['success']:
            print(f"✅ Success: {len(result['result'])} characters returned")
        else:
            print(f"❌ Failed: {result['error']}")
    
    # Save reasoning results
    with open('reasoning_mcp_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Reasoning Test Results Summary:")
    successful = len([r for r in results if r['success']])
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Results saved to: reasoning_mcp_test_results.json")

if __name__ == "__main__":
    asyncio.run(advanced_reasoning_mcp_example())
```

## Error Handling Examples for Reasoning

### Comprehensive Error Handler for Reasoning Operations

```python
#!/usr/bin/env python3
"""
Comprehensive error handling examples for reasoning authentication scenarios.
"""

import json
import asyncio
from typing import Optional, Dict, Any
from services.auth_service import (
    CognitoAuthenticator, 
    TokenValidator, 
    AuthenticationError
)

class ReasoningAuthenticationErrorHandler:
    """Centralized error handling for reasoning authentication scenarios."""
    
    def __init__(self):
        """Initialize error handler with reasoning-specific error patterns."""
        self.error_handlers = {
            'REASONING_AUTHENTICATION_FAILED': self._handle_reasoning_auth_failed,
            'REASONING_USER_NOT_FOUND': self._handle_reasoning_user_not_found,
            'REASONING_TOKEN_EXPIRED': self._handle_reasoning_token_expired,
            'REASONING_TOKEN_VALIDATION_ERROR': self._handle_reasoning_token_validation,
            'REASONING_NETWORK_ERROR': self._handle_reasoning_network_error,
            'REASONING_MCP_ERROR': self._handle_reasoning_mcp_error
        }
    
    def handle_reasoning_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle reasoning authentication error and provide recovery suggestions."""
        
        handler = self.error_handlers.get(
            f"REASONING_{error.error_type}", 
            self._handle_unknown_reasoning_error
        )
        
        return handler(error)
    
    def _handle_reasoning_auth_failed(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle reasoning authentication failure errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Invalid credentials for reasoning operations. Please check your username and password.',
            'recovery_actions': [
                'Verify username (email) is correct for reasoning access',
                'Check password for typos',
                'Ensure caps lock is off',
                'Try password reset if needed',
                'Verify you have access to reasoning operations'
            ],
            'retry_recommended': True,
            'contact_support': False,
            'reasoning_context': True
        }
    
    def _handle_reasoning_user_not_found(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle reasoning user not found errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'User account not found for reasoning operations. Please check your email address.',
            'recovery_actions': [
                'Verify email address is correct',
                'Check if account was created with reasoning access',
                'Contact administrator for reasoning permissions',
                'Verify you are using the correct Cognito User Pool'
            ],
            'retry_recommended': False,
            'contact_support': True,
            'reasoning_context': True
        }
    
    def _handle_reasoning_token_expired(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle reasoning token expiration errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Reasoning session expired. Please log in again to continue sentiment analysis.',
            'recovery_actions': [
                'Use refresh token if available for reasoning session',
                'Re-authenticate with username/password for reasoning access',
                'Clear stored reasoning tokens',
                'Restart reasoning operations'
            ],
            'retry_recommended': True,
            'contact_support': False,
            'reasoning_context': True
        }
    
    def _handle_reasoning_token_validation(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle reasoning token validation errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Reasoning authentication token is invalid. Please log in again to access sentiment analysis.',
            'recovery_actions': [
                'Clear stored reasoning tokens',
                'Re-authenticate for reasoning operations',
                'Check system clock is correct',
                'Verify reasoning server configuration'
            ],
            'retry_recommended': True,
            'contact_support': False,
            'reasoning_context': True
        }
    
    def _handle_reasoning_network_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle reasoning network-related errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Network connection error for reasoning operations. Please check your internet connection.',
            'recovery_actions': [
                'Check internet connectivity',
                'Verify firewall settings for reasoning server access',
                'Try reasoning operations again in a few moments',
                'Contact IT support if reasoning access persists to fail'
            ],
            'retry_recommended': True,
            'contact_support': False,
            'reasoning_context': True
        }
    
    def _handle_reasoning_mcp_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle reasoning MCP-specific errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Reasoning MCP server error. The sentiment analysis service may be temporarily unavailable.',
            'recovery_actions': [
                'Check reasoning server deployment status',
                'Verify reasoning MCP server is running',
                'Try reasoning operations again in a few moments',
                'Contact support if reasoning service remains unavailable'
            ],
            'retry_recommended': True,
            'contact_support': True,
            'reasoning_context': True
        }
    
    def _handle_unknown_reasoning_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle unknown reasoning errors."""
        return {
            'error_type': 'UNKNOWN_REASONING_ERROR',
            'user_message': 'An unexpected error occurred during reasoning operations. Please try again.',
            'recovery_actions': [
                'Try reasoning authentication again',
                'Check reasoning server logs',
                'Contact support with error details',
                'Verify reasoning system status'
            ],
            'retry_recommended': True,
            'contact_support': True,
            'reasoning_context': True
        }

async def reasoning_error_handling_example():
    """Demonstrate reasoning error handling patterns."""
    
    error_handler = ReasoningAuthenticationErrorHandler()
    
    # Simulate various reasoning authentication errors
    test_errors = [
        AuthenticationError(
            error_type='AUTHENTICATION_FAILED',
            error_code='NotAuthorizedException',
            message='Invalid credentials for reasoning operations',
            suggested_action='Check username and password for reasoning access'
        ),
        AuthenticationError(
            error_type='TOKEN_EXPIRED',
            error_code='TokenExpiredException',
            message='Reasoning session token has expired',
            suggested_action='Refresh token or re-authenticate for reasoning'
        ),
        AuthenticationError(
            error_type='NETWORK_ERROR',
            error_code='NetworkException',
            message='Cannot connect to reasoning authentication service',
            suggested_action='Check network connectivity for reasoning operations'
        )
    ]
    
    print("🧠 Testing reasoning error handling patterns...")
    
    for i, error in enumerate(test_errors, 1):
        print(f"\n[{i}] Handling reasoning error: {error.error_type}")
        
        error_response = error_handler.handle_reasoning_error(error)
        
        print(f"  User Message: {error_response['user_message']}")
        print(f"  Recovery Actions: {len(error_response['recovery_actions'])} suggested")
        print(f"  Retry Recommended: {error_response['retry_recommended']}")
        print(f"  Reasoning Context: {error_response['reasoning_context']}")
    
    print("\n✅ Reasoning error handling examples completed")

if __name__ == "__main__":
    asyncio.run(reasoning_error_handling_example())
```

## Token Refresh Scenarios for Reasoning

### Automatic Token Refresh for Long Reasoning Sessions

```python
#!/usr/bin/env python3
"""
Automatic token refresh for long-running reasoning sessions.
"""

import json
import asyncio
import time
from typing import Optional
from services.auth_service import CognitoAuthenticator, AuthenticationError

class ReasoningSessionManager:
    """Manages authentication tokens for extended reasoning sessions."""
    
    def __init__(self, config_file: str = 'cognito_config.json'):
        """Initialize reasoning session manager."""
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
        self.session_active = False
    
    async def start_reasoning_session(self, username: str, password: str) -> bool:
        """Start a new reasoning session with authentication."""
        try:
            print("🧠 Starting reasoning session...")
            
            tokens = self.authenticator.authenticate_user(username, password)
            
            self.access_token = tokens.access_token
            self.refresh_token = tokens.refresh_token
            self.token_expires_at = time.time() + tokens.expires_in
            self.session_active = True
            
            # Save reasoning session tokens
            session_data = {
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'id_token': tokens.id_token,
                'expires_in': tokens.expires_in,
                'session_started_at': time.time(),
                'reasoning_session': True
            }
            
            with open('reasoning_session_tokens.json', 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print("✅ Reasoning session started successfully")
            return True
            
        except AuthenticationError as e:
            print(f"❌ Failed to start reasoning session: {e.message}")
            return False
    
    async def ensure_valid_reasoning_token(self) -> bool:
        """Ensure we have a valid token for reasoning operations."""
        if not self.session_active:
            print("❌ No active reasoning session")
            return False
        
        # Check if token needs refresh (5 minutes before expiry)
        if time.time() >= self.token_expires_at - 300:
            print("🔄 Reasoning token expiring soon, refreshing...")
            
            try:
                new_tokens = self.authenticator.refresh_token(self.refresh_token)
                
                self.access_token = new_tokens.access_token
                self.token_expires_at = time.time() + new_tokens.expires_in
                
                # Update session tokens
                with open('reasoning_session_tokens.json', 'r') as f:
                    session_data = json.load(f)
                
                session_data.update({
                    'access_token': new_tokens.access_token,
                    'id_token': new_tokens.id_token,
                    'expires_in': new_tokens.expires_in,
                    'last_refreshed_at': time.time()
                })
                
                with open('reasoning_session_tokens.json', 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                print("✅ Reasoning token refreshed successfully")
                return True
                
            except AuthenticationError as e:
                print(f"❌ Failed to refresh reasoning token: {e.message}")
                self.session_active = False
                return False
        
        return True
    
    async def perform_reasoning_operation(self, operation_name: str, data: dict) -> dict:
        """Perform a reasoning operation with automatic token management."""
        if not await self.ensure_valid_reasoning_token():
            return {'success': False, 'error': 'Invalid reasoning session'}
        
        print(f"🎯 Performing reasoning operation: {operation_name}")
        
        # Simulate reasoning operation (replace with actual MCP call)
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            'success': True,
            'operation': operation_name,
            'data': data,
            'timestamp': time.time(),
            'token_valid': True
        }
    
    def end_reasoning_session(self):
        """End the reasoning session and clear tokens."""
        self.session_active = False
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # Clear session tokens
        try:
            import os
            os.remove('reasoning_session_tokens.json')
        except FileNotFoundError:
            pass
        
        print("🔚 Reasoning session ended")

async def long_reasoning_session_example():
    """Demonstrate long-running reasoning session with automatic token refresh."""
    
    session_manager = ReasoningSessionManager()
    
    # Load test credentials
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Start reasoning session
    success = await session_manager.start_reasoning_session(
        config['test_user']['email'],
        'TempPass123!'
    )
    
    if not success:
        return
    
    # Simulate long-running reasoning operations
    reasoning_operations = [
        {'name': 'sentiment_analysis_batch_1', 'data': {'restaurants': 50}},
        {'name': 'recommendation_generation_1', 'data': {'method': 'sentiment_likes'}},
        {'name': 'sentiment_analysis_batch_2', 'data': {'restaurants': 75}},
        {'name': 'recommendation_generation_2', 'data': {'method': 'combined_sentiment'}},
        {'name': 'sentiment_analysis_batch_3', 'data': {'restaurants': 100}}
    ]
    
    print(f"\n🧠 Starting {len(reasoning_operations)} reasoning operations...")
    
    for i, operation in enumerate(reasoning_operations, 1):
        print(f"\n[{i}/{len(reasoning_operations)}] {operation['name']}")
        
        result = await session_manager.perform_reasoning_operation(
            operation['name'],
            operation['data']
        )
        
        if result['success']:
            print(f"  ✅ Completed successfully")
        else:
            print(f"  ❌ Failed: {result['error']}")
        
        # Simulate time between operations
        await asyncio.sleep(2)
    
    # End session
    session_manager.end_reasoning_session()
    print("\n🎉 Long reasoning session completed successfully")

if __name__ == "__main__":
    asyncio.run(long_reasoning_session_example())
```

## Production Integration Patterns for Reasoning

### Production Reasoning Client with Full Error Handling

```python
#!/usr/bin/env python3
"""
Production-ready reasoning client with comprehensive error handling and retry logic.
"""

import json
import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator, AuthenticationError

@dataclass
class ReasoningRequest:
    """Represents a reasoning request with metadata."""
    request_id: str
    operation_type: str
    restaurants: List[Dict]
    ranking_method: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class ReasoningResponse:
    """Represents a reasoning response with metadata."""
    request_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class ProductionReasoningClient:
    """Production-ready reasoning client with full error handling."""
    
    def __init__(self, config_file: str = 'cognito_config.json'):
        """Initialize production reasoning client."""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - REASONING - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Initialize authenticator
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.config['user_pool']['user_pool_id'],
            client_id=self.config['app_client']['client_id'],
            region=self.config['region']
        )
        
        # Token management
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 30.0
        
        # Load MCP URL
        self.mcp_url = self._load_mcp_url()
    
    def _load_mcp_url(self) -> str:
        """Load reasoning MCP server URL from deployment config."""
        try:
            with open('reasoning_deployment_config.json', 'r') as f:
                deployment_config = json.load(f)
            
            agent_arn = deployment_config['launch_result']['agent_arn']
            return f"https://{agent_arn.split('/')[-1]}.bedrock-agentcore.us-east-1.amazonaws.com"
            
        except FileNotFoundError:
            self.logger.error("Reasoning deployment config not found")
            raise ValueError("Reasoning deployment configuration not available")
    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate for reasoning operations."""
        try:
            self.logger.info(f"Authenticating user for reasoning: {username}")
            
            tokens = self.authenticator.authenticate_user(username, password)
            
            self.access_token = tokens.access_token
            self.refresh_token = tokens.refresh_token
            self.token_expires_at = time.time() + tokens.expires_in
            
            self.logger.info("Reasoning authentication successful")
            return True
            
        except AuthenticationError as e:
            self.logger.error(f"Reasoning authentication failed: {e.message}")
            return False
    
    async def ensure_valid_token(self) -> bool:
        """Ensure we have a valid token for reasoning operations."""
        if not self.access_token or not self.token_expires_at:
            self.logger.error("No valid reasoning token available")
            return False
        
        # Check if token needs refresh
        if time.time() >= self.token_expires_at - 300:  # 5 min buffer
            try:
                self.logger.info("Refreshing reasoning token")
                
                new_tokens = self.authenticator.refresh_token(self.refresh_token)
                
                self.access_token = new_tokens.access_token
                self.token_expires_at = time.time() + new_tokens.expires_in
                
                self.logger.info("Reasoning token refreshed successfully")
                return True
                
            except AuthenticationError as e:
                self.logger.error(f"Failed to refresh reasoning token: {e.message}")
                return False
        
        return True
    
    async def process_reasoning_request(self, request: ReasoningRequest) -> ReasoningResponse:
        """Process a reasoning request with full error handling."""
        start_time = time.time()
        
        self.logger.info(f"Processing reasoning request: {request.request_id}")
        
        # Ensure authentication
        if not await self.ensure_valid_token():
            return ReasoningResponse(
                request_id=request.request_id,
                success=False,
                error="Authentication failed for reasoning operation"
            )
        
        # Prepare MCP call parameters
        if request.operation_type == "recommend_restaurants":
            tool_name = "recommend_restaurants"
            parameters = {
                "restaurants": request.restaurants,
                "ranking_method": request.ranking_method or "sentiment_likes"
            }
        elif request.operation_type == "analyze_sentiment":
            tool_name = "analyze_restaurant_sentiment"
            parameters = {"restaurants": request.restaurants}
        else:
            return ReasoningResponse(
                request_id=request.request_id,
                success=False,
                error=f"Unknown reasoning operation type: {request.operation_type}"
            )
        
        # Execute MCP call with retries
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Reasoning attempt {attempt + 1}/{self.max_retries}")
                
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(tool_name, parameters)
                        
                        processing_time = time.time() - start_time
                        
                        self.logger.info(f"Reasoning request completed: {request.request_id}")
                        
                        return ReasoningResponse(
                            request_id=request.request_id,
                            success=True,
                            result=result.content[0].text if result.content else None,
                            processing_time=processing_time
                        )
                        
            except Exception as e:
                self.logger.warning(f"Reasoning attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    processing_time = time.time() - start_time
                    
                    return ReasoningResponse(
                        request_id=request.request_id,
                        success=False,
                        error=f"Reasoning operation failed after {self.max_retries} attempts: {e}",
                        processing_time=processing_time
                    )

async def production_reasoning_example():
    """Demonstrate production reasoning client usage."""
    
    client = ProductionReasoningClient()
    
    # Load test credentials
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Authenticate
    auth_success = await client.authenticate(
        config['test_user']['email'],
        'TempPass123!'
    )
    
    if not auth_success:
        print("❌ Authentication failed")
        return
    
    # Sample restaurant data for production testing
    production_restaurants = [
        {
            "id": "prod_rest_001",
            "name": "Central Business Lunch",
            "address": "Tower 1, Central Plaza",
            "sentiment": {"likes": 150, "dislikes": 12, "neutral": 18},
            "meal_type": ["lunch"],
            "district": "Central district",
            "price_range": "$$$"
        },
        {
            "id": "prod_rest_002",
            "name": "TST Night Market",
            "address": "Temple Street, TST",
            "sentiment": {"likes": 200, "dislikes": 45, "neutral": 35},
            "meal_type": ["dinner"],
            "district": "Tsim Sha Tsui",
            "price_range": "$"
        }
    ]
    
    # Create reasoning requests
    requests = [
        ReasoningRequest(
            request_id="req_001",
            operation_type="recommend_restaurants",
            restaurants=production_restaurants,
            ranking_method="sentiment_likes"
        ),
        ReasoningRequest(
            request_id="req_002",
            operation_type="recommend_restaurants",
            restaurants=production_restaurants,
            ranking_method="combined_sentiment"
        ),
        ReasoningRequest(
            request_id="req_003",
            operation_type="analyze_sentiment",
            restaurants=production_restaurants
        )
    ]
    
    # Process requests
    results = []
    
    for request in requests:
        response = await client.process_reasoning_request(request)
        results.append(response)
        
        if response.success:
            print(f"✅ {request.request_id}: Success ({response.processing_time:.2f}s)")
        else:
            print(f"❌ {request.request_id}: Failed - {response.error}")
    
    # Save production results
    results_data = [
        {
            'request_id': r.request_id,
            'success': r.success,
            'result_length': len(r.result) if r.result else 0,
            'error': r.error,
            'processing_time': r.processing_time,
            'timestamp': r.timestamp
        }
        for r in results
    ]
    
    with open('production_reasoning_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📊 Production Results: {len([r for r in results if r.success])}/{len(results)} successful")
    print("💾 Results saved to production_reasoning_results.json")

if __name__ == "__main__":
    asyncio.run(production_reasoning_example())
```

---

## Summary

This document provides comprehensive authentication usage examples specifically adapted for the Restaurant Reasoning MCP server, including:

1. **SRP Authentication Examples**: Basic, interactive, and batch authentication patterns for reasoning operations
2. **JWT Token Management**: Token validation, refresh, and lifecycle management for reasoning sessions
3. **Reasoning MCP Client Integration**: Basic and advanced MCP client examples with reasoning-specific tools
4. **Error Handling**: Comprehensive error handling patterns for reasoning authentication scenarios
5. **Token Refresh Scenarios**: Automatic token refresh for long-running reasoning sessions
6. **Production Integration**: Production-ready client with full error handling and retry logic

All examples are specifically tailored for reasoning operations while reusing the existing Cognito authentication infrastructure from the restaurant search MCP server.