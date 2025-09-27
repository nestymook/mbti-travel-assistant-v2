# Authentication Usage Examples

This document provides comprehensive examples for implementing authentication with the Restaurant Search MCP server using AWS Cognito and JWT tokens.

## Table of Contents

1. [SRP Authentication Examples](#srp-authentication-examples)
2. [JWT Token Management](#jwt-token-management)
3. [MCP Client Integration](#mcp-client-integration)
4. [Error Handling Examples](#error-handling-examples)
5. [Token Refresh Scenarios](#token-refresh-scenarios)
6. [Production Integration Patterns](#production-integration-patterns)

## SRP Authentication Examples

### Basic SRP Authentication

```python
#!/usr/bin/env python3
"""
Basic SRP authentication example using CognitoAuthenticator.
"""

import json
import sys
from services.auth_service import CognitoAuthenticator, AuthenticationError

def basic_authentication_example():
    """Demonstrate basic SRP authentication flow."""
    
    # Load Cognito configuration
    try:
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: cognito_config.json not found. Run setup_cognito.py first.")
        return False
    
    # Initialize authenticator
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Authentication credentials
    username = config['test_user']['email']
    password = "TempPass123!"  # Use actual password
    
    try:
        print(f"🔐 Authenticating user: {username}")
        
        # Perform SRP authentication
        tokens = authenticator.authenticate_user(username, password)
        
        print("✅ Authentication successful!")
        print(f"Token Type: {tokens.token_type}")
        print(f"Access Token: {tokens.access_token[:50]}...")
        print(f"ID Token: {tokens.id_token[:50]}...")
        print(f"Expires In: {tokens.expires_in} seconds")
        
        return tokens
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed:")
        print(f"  Error Type: {e.error_type}")
        print(f"  Error Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  Suggested Action: {e.suggested_action}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    basic_authentication_example()
```
#
## Interactive Authentication Script

```python
#!/usr/bin/env python3
"""
Interactive authentication script with user input.
"""

import getpass
import json
from services.auth_service import CognitoAuthenticator, AuthenticationError

def interactive_authentication():
    """Interactive authentication with user input."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    print("🔐 Restaurant Search MCP Authentication")
    print("=" * 40)
    
    # Get credentials from user
    username = input("Username (email): ").strip()
    password = getpass.getpass("Password: ")
    
    try:
        print("\n🔄 Authenticating...")
        tokens = authenticator.authenticate_user(username, password)
        
        print("✅ Authentication successful!")
        print(f"Welcome, {username}!")
        
        # Validate session
        user_context = authenticator.validate_user_session(tokens.access_token)
        print(f"User ID: {user_context.user_id}")
        print(f"Email: {user_context.email}")
        
        # Save tokens for later use (in production, use secure storage)
        token_data = {
            'access_token': tokens.access_token,
            'id_token': tokens.id_token,
            'refresh_token': tokens.refresh_token,
            'expires_in': tokens.expires_in,
            'token_type': tokens.token_type
        }
        
        with open('user_tokens.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("💾 Tokens saved to user_tokens.json")
        return tokens
        
    except AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e.message}")
        print(f"💡 Suggestion: {e.suggested_action}")
        return None

if __name__ == "__main__":
    interactive_authentication()
```

### Batch User Authentication

```python
#!/usr/bin/env python3
"""
Batch authentication for multiple users.
"""

import json
import csv
from typing import List, Dict
from services.auth_service import CognitoAuthenticator, AuthenticationError

def batch_authentication(users_file: str = "test_users.csv"):
    """Authenticate multiple users from CSV file."""
    
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
        print(f"❌ Users file not found: {users_file}")
        return []
    
    print(f"🔐 Batch authenticating {len(users)} users...")
    
    for i, user in enumerate(users, 1):
        username = user['username']
        password = user['password']
        
        print(f"\n[{i}/{len(users)}] Authenticating: {username}")
        
        try:
            tokens = authenticator.authenticate_user(username, password)
            
            result = {
                'username': username,
                'status': 'success',
                'user_id': None,
                'email': None,
                'error': None
            }
            
            # Get user info
            try:
                user_context = authenticator.validate_user_session(tokens.access_token)
                result['user_id'] = user_context.user_id
                result['email'] = user_context.email
            except Exception as e:
                result['error'] = f"Session validation failed: {e}"
            
            print(f"  ✅ Success - User ID: {result['user_id']}")
            
        except AuthenticationError as e:
            result = {
                'username': username,
                'status': 'failed',
                'user_id': None,
                'email': None,
                'error': f"{e.error_type}: {e.message}"
            }
            print(f"  ❌ Failed - {e.error_type}")
        
        results.append(result)
    
    # Save results
    with open('batch_auth_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len(results) - successful
    
    print(f"\n📊 Batch Authentication Summary:")
    print(f"  Total Users: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Results saved to: batch_auth_results.json")
    
    return results

if __name__ == "__main__":
    # Example CSV format:
    # username,password
    # user1@example.com,Password123!
    # user2@example.com,Password456!
    
    batch_authentication()
```

## JWT Token Management

### Token Validation Example

```python
#!/usr/bin/env python3
"""
JWT token validation examples.
"""

import json
import asyncio
from services.auth_service import TokenValidator, AuthenticationError

async def token_validation_example():
    """Demonstrate JWT token validation."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize token validator
    validator_config = {
        'user_pool_id': config['user_pool']['user_pool_id'],
        'client_id': config['app_client']['client_id'],
        'region': config['region'],
        'discovery_url': config['discovery_url']
    }
    
    validator = TokenValidator(validator_config)
    
    # Load test token (from previous authentication)
    try:
        with open('user_tokens.json', 'r') as f:
            token_data = json.load(f)
        access_token = token_data['access_token']
    except FileNotFoundError:
        print("❌ No tokens found. Run authentication example first.")
        return
    
    try:
        print("🔍 Validating JWT token...")
        
        # Validate token
        claims = await validator.validate_jwt_token(access_token)
        
        print("✅ Token validation successful!")
        print(f"User ID: {claims.user_id}")
        print(f"Username: {claims.username}")
        print(f"Email: {claims.email}")
        print(f"Client ID: {claims.client_id}")
        print(f"Token Use: {claims.token_use}")
        print(f"Issued At: {claims.iat}")
        print(f"Expires At: {claims.exp}")
        
        # Check if token is expired
        if validator.is_token_expired(access_token):
            print("⚠️ Token is expired")
        else:
            print("✅ Token is valid and not expired")
        
    except AuthenticationError as e:
        print(f"❌ Token validation failed:")
        print(f"  Error Type: {e.error_type}")
        print(f"  Error Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  Suggested Action: {e.suggested_action}")

if __name__ == "__main__":
    asyncio.run(token_validation_example())
```

### Token Refresh Example

```python
#!/usr/bin/env python3
"""
Token refresh example using refresh tokens.
"""

import json
import time
from services.auth_service import CognitoAuthenticator, AuthenticationError

def token_refresh_example():
    """Demonstrate token refresh flow."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Load existing tokens
    try:
        with open('user_tokens.json', 'r') as f:
            token_data = json.load(f)
        refresh_token = token_data['refresh_token']
    except FileNotFoundError:
        print("❌ No tokens found. Authenticate first.")
        return
    
    try:
        print("🔄 Refreshing access token...")
        
        # Refresh tokens
        new_tokens = authenticator.refresh_token(refresh_token)
        
        print("✅ Token refresh successful!")
        print(f"New Access Token: {new_tokens.access_token[:50]}...")
        print(f"New ID Token: {new_tokens.id_token[:50]}...")
        print(f"Expires In: {new_tokens.expires_in} seconds")
        
        # Update stored tokens
        token_data.update({
            'access_token': new_tokens.access_token,
            'id_token': new_tokens.id_token,
            'expires_in': new_tokens.expires_in,
            'refreshed_at': time.time()
        })
        
        with open('user_tokens.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("💾 Updated tokens saved")
        
        return new_tokens
        
    except AuthenticationError as e:
        print(f"❌ Token refresh failed:")
        print(f"  Error Type: {e.error_type}")
        print(f"  Message: {e.message}")
        print(f"  Suggested Action: {e.suggested_action}")
        
        if e.error_code == 'NotAuthorizedException':
            print("💡 Refresh token may be expired. Re-authentication required.")
        
        return None

if __name__ == "__main__":
    token_refresh_example()
```

## MCP Client Integration

### Basic Authenticated MCP Client

```python
#!/usr/bin/env python3
"""
Basic authenticated MCP client example.
"""

import json
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator

async def authenticated_mcp_client():
    """Example of MCP client with JWT authentication."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Load AgentCore deployment configuration
    try:
        with open('agentcore_deployment_config.json', 'r') as f:
            deployment_config = json.load(f)
        
        # Extract AgentCore endpoint URL
        agent_arn = deployment_config['configuration_response']['agent_arn']
        # Construct endpoint URL (this may vary based on your deployment)
        mcp_url = f"https://{agent_arn.split('/')[-1]}.bedrock-agentcore.us-east-1.amazonaws.com"
        
    except FileNotFoundError:
        print("❌ Deployment config not found. Deploy AgentCore first.")
        return
    
    # Authenticate and get tokens
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    try:
        # Load existing tokens or authenticate
        try:
            with open('user_tokens.json', 'r') as f:
                token_data = json.load(f)
            access_token = token_data['access_token']
            
            # Check if token is expired and refresh if needed
            if authenticator.validate_user_session(access_token):
                print("✅ Using existing valid token")
            
        except (FileNotFoundError, Exception):
            print("🔐 Authenticating...")
            tokens = authenticator.authenticate_user(
                config['test_user']['email'],
                "TempPass123!"  # Use actual password
            )
            access_token = tokens.access_token
        
        # Set up authenticated headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔗 Connecting to MCP server: {mcp_url}")
        
        # Connect to MCP server with authentication
        async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()
                print("✅ MCP session initialized")
                
                # List available tools
                tools_response = await session.list_tools()
                tools = [tool.name for tool in tools_response.tools]
                print(f"📋 Available tools: {tools}")
                
                # Test restaurant search by district
                print("\n🔍 Testing restaurant search by district...")
                result = await session.call_tool(
                    "search_restaurants_by_district",
                    {"districts": ["Central district"]}
                )
                
                print("✅ Search completed!")
                print(f"Result: {result.content[0].text[:200]}...")
                
                # Test restaurant search by meal type
                print("\n🔍 Testing restaurant search by meal type...")
                result = await session.call_tool(
                    "search_restaurants_by_meal_type",
                    {"meal_types": ["breakfast"]}
                )
                
                print("✅ Search completed!")
                print(f"Result: {result.content[0].text[:200]}...")
                
    except Exception as e:
        print(f"❌ MCP client error: {e}")

if __name__ == "__main__":
    asyncio.run(authenticated_mcp_client())
```

### Advanced MCP Client with Error Handling

```python
#!/usr/bin/env python3
"""
Advanced MCP client with comprehensive error handling.
"""

import json
import asyncio
import time
from typing import Optional, Dict, Any
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from services.auth_service import CognitoAuthenticator, AuthenticationError

class AuthenticatedMCPClient:
    """Advanced MCP client with authentication and error handling."""
    
    def __init__(self, config_file: str = 'cognito_config.json'):
        """Initialize the authenticated MCP client."""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.config['user_pool']['user_pool_id'],
            client_id=self.config['app_client']['client_id'],
            region=self.config['region']
        )
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
    async def ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token."""
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expires_at:
                if time.time() < self.token_expires_at - 300:  # 5 min buffer
                    return True
            
            # Try to load existing tokens
            try:
                with open('user_tokens.json', 'r') as f:
                    token_data = json.load(f)
                
                # Try to refresh token
                if 'refresh_token' in token_data:
                    print("🔄 Refreshing access token...")
                    new_tokens = self.authenticator.refresh_token(
                        token_data['refresh_token']
                    )
                    
                    self.access_token = new_tokens.access_token
                    self.token_expires_at = time.time() + new_tokens.expires_in
                    
                    # Update stored tokens
                    token_data.update({
                        'access_token': new_tokens.access_token,
                        'id_token': new_tokens.id_token,
                        'expires_in': new_tokens.expires_in,
                        'refreshed_at': time.time()
                    })
                    
                    with open('user_tokens.json', 'w') as f:
                        json.dump(token_data, f, indent=2)
                    
                    print("✅ Token refreshed successfully")
                    return True
                    
            except (FileNotFoundError, AuthenticationError):
                pass
            
            # Fall back to full authentication
            print("🔐 Performing full authentication...")
            tokens = self.authenticator.authenticate_user(
                self.config['test_user']['email'],
                "TempPass123!"  # Use actual password
            )
            
            self.access_token = tokens.access_token
            self.token_expires_at = time.time() + tokens.expires_in
            
            print("✅ Authentication successful")
            return True
            
        except AuthenticationError as e:
            print(f"❌ Authentication failed: {e.message}")
            return False
        except Exception as e:
            print(f"❌ Unexpected authentication error: {e}")
            return False
    
    async def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any], 
                           mcp_url: str) -> Optional[Dict]:
        """Call an MCP tool with authentication and error handling."""
        
        # Ensure we're authenticated
        if not await self.ensure_authenticated():
            return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"🔗 Connecting to MCP server (attempt {retry_count + 1})...")
                
                async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        print(f"🛠️ Calling tool: {tool_name}")
                        result = await session.call_tool(tool_name, parameters)
                        
                        return {
                            'success': True,
                            'result': result.content[0].text if result.content else None,
                            'tool_name': tool_name,
                            'parameters': parameters
                        }
                        
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                print(f"❌ MCP call failed (attempt {retry_count}): {error_msg}")
                
                # Check if it's an authentication error
                if "401" in error_msg or "Unauthorized" in error_msg:
                    print("🔄 Authentication error, refreshing token...")
                    self.access_token = None
                    self.token_expires_at = None
                    
                    if not await self.ensure_authenticated():
                        print("❌ Failed to refresh authentication")
                        break
                    
                    headers['Authorization'] = f'Bearer {self.access_token}'
                
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Max retries ({max_retries}) exceeded")
        
        return {
            'success': False,
            'error': f"Failed after {max_retries} attempts",
            'tool_name': tool_name,
            'parameters': parameters
        }

async def advanced_mcp_example():
    """Demonstrate advanced MCP client usage."""
    
    client = AuthenticatedMCPClient()
    
    # Load deployment configuration to get MCP URL
    try:
        with open('agentcore_deployment_config.json', 'r') as f:
            deployment_config = json.load(f)
        
        agent_arn = deployment_config['configuration_response']['agent_arn']
        mcp_url = f"https://{agent_arn.split('/')[-1]}.bedrock-agentcore.us-east-1.amazonaws.com"
        
    except FileNotFoundError:
        print("❌ Deployment config not found")
        return
    
    # Test multiple tool calls
    test_cases = [
        {
            'tool': 'search_restaurants_by_district',
            'params': {'districts': ['Central district', 'Tsim Sha Tsui']}
        },
        {
            'tool': 'search_restaurants_by_meal_type',
            'params': {'meal_types': ['breakfast', 'lunch']}
        },
        {
            'tool': 'search_restaurants_combined',
            'params': {
                'districts': ['Causeway Bay'],
                'meal_types': ['dinner']
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing {test_case['tool']}...")
        
        result = await client.call_mcp_tool(
            test_case['tool'],
            test_case['params'],
            mcp_url
        )
        
        results.append(result)
        
        if result['success']:
            print(f"✅ Success: {len(result['result'])} characters returned")
        else:
            print(f"❌ Failed: {result['error']}")
    
    # Save results
    with open('mcp_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Test Results Summary:")
    successful = len([r for r in results if r['success']])
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Results saved to: mcp_test_results.json")

if __name__ == "__main__":
    asyncio.run(advanced_mcp_example())
```## 
Error Handling Examples

### Comprehensive Error Handler

```python
#!/usr/bin/env python3
"""
Comprehensive error handling examples for authentication scenarios.
"""

import json
import asyncio
from typing import Optional, Dict, Any
from services.auth_service import (
    CognitoAuthenticator, 
    TokenValidator, 
    AuthenticationError
)

class AuthenticationErrorHandler:
    """Centralized error handling for authentication scenarios."""
    
    def __init__(self):
        """Initialize error handler with common error patterns."""
        self.error_handlers = {
            'AUTHENTICATION_FAILED': self._handle_auth_failed,
            'USER_NOT_FOUND': self._handle_user_not_found,
            'USER_NOT_CONFIRMED': self._handle_user_not_confirmed,
            'TOKEN_EXPIRED': self._handle_token_expired,
            'TOKEN_VALIDATION_ERROR': self._handle_token_validation,
            'NETWORK_ERROR': self._handle_network_error,
            'COGNITO_ERROR': self._handle_cognito_error
        }
    
    def handle_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle authentication error and provide recovery suggestions."""
        
        handler = self.error_handlers.get(
            error.error_type, 
            self._handle_unknown_error
        )
        
        return handler(error)
    
    def _handle_auth_failed(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle authentication failure errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Invalid username or password. Please check your credentials.',
            'recovery_actions': [
                'Verify username (email) is correct',
                'Check password for typos',
                'Ensure caps lock is off',
                'Try password reset if needed'
            ],
            'retry_recommended': True,
            'contact_support': False
        }
    
    def _handle_user_not_found(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle user not found errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'User account not found. Please check your email address.',
            'recovery_actions': [
                'Verify email address is correct',
                'Check if account was created',
                'Contact administrator if needed'
            ],
            'retry_recommended': False,
            'contact_support': True
        }
    
    def _handle_user_not_confirmed(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle user not confirmed errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Account not verified. Please check your email for verification link.',
            'recovery_actions': [
                'Check email inbox for verification message',
                'Check spam/junk folder',
                'Request new verification email',
                'Contact support if no email received'
            ],
            'retry_recommended': False,
            'contact_support': True
        }
    
    def _handle_token_expired(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle token expiration errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Session expired. Please log in again.',
            'recovery_actions': [
                'Use refresh token if available',
                'Re-authenticate with username/password',
                'Clear stored tokens'
            ],
            'retry_recommended': True,
            'contact_support': False
        }
    
    def _handle_token_validation(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle token validation errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Authentication token is invalid. Please log in again.',
            'recovery_actions': [
                'Clear stored tokens',
                'Re-authenticate',
                'Check system clock is correct'
            ],
            'retry_recommended': True,
            'contact_support': False
        }
    
    def _handle_network_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle network-related errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Network connection error. Please check your internet connection.',
            'recovery_actions': [
                'Check internet connectivity',
                'Verify firewall settings',
                'Try again in a few moments',
                'Contact IT support if persistent'
            ],
            'retry_recommended': True,
            'contact_support': False
        }
    
    def _handle_cognito_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle Cognito service errors."""
        return {
            'error_type': error.error_type,
            'user_message': 'Authentication service error. Please try again later.',
            'recovery_actions': [
                'Wait a few minutes and retry',
                'Check AWS service status',
                'Contact support if persistent'
            ],
            'retry_recommended': True,
            'contact_support': True
        }
    
    def _handle_unknown_error(self, error: AuthenticationError) -> Dict[str, Any]:
        """Handle unknown errors."""
        return {
            'error_type': 'UNKNOWN_ERROR',
            'user_message': 'An unexpected error occurred. Please contact support.',
            'recovery_actions': [
                'Note the exact error message',
                'Try again later',
                'Contact technical support'
            ],
            'retry_recommended': False,
            'contact_support': True
        }

async def error_handling_example():
    """Demonstrate comprehensive error handling."""
    
    error_handler = AuthenticationErrorHandler()
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Test various error scenarios
    test_scenarios = [
        {
            'name': 'Invalid Password',
            'username': config['test_user']['email'],
            'password': 'WrongPassword123!'
        },
        {
            'name': 'Non-existent User',
            'username': 'nonexistent@example.com',
            'password': 'Password123!'
        },
        {
            'name': 'Valid Credentials',
            'username': config['test_user']['email'],
            'password': 'TempPass123!'  # Use actual password
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"Username: {scenario['username']}")
        
        try:
            tokens = authenticator.authenticate_user(
                scenario['username'],
                scenario['password']
            )
            
            result = {
                'scenario': scenario['name'],
                'success': True,
                'message': 'Authentication successful',
                'tokens_received': True
            }
            
            print("✅ Success!")
            
        except AuthenticationError as e:
            # Handle the error using our error handler
            error_info = error_handler.handle_error(e)
            
            result = {
                'scenario': scenario['name'],
                'success': False,
                'error_type': e.error_type,
                'error_code': e.error_code,
                'error_message': e.message,
                'user_message': error_info['user_message'],
                'recovery_actions': error_info['recovery_actions'],
                'retry_recommended': error_info['retry_recommended'],
                'contact_support': error_info['contact_support']
            }
            
            print(f"❌ {error_info['user_message']}")
            print("💡 Recovery actions:")
            for action in error_info['recovery_actions']:
                print(f"  - {action}")
        
        results.append(result)
    
    # Save error handling results
    with open('error_handling_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Error Handling Test Results:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['scenario']}")
    
    print(f"\nResults saved to: error_handling_results.json")

if __name__ == "__main__":
    asyncio.run(error_handling_example())
```

### Retry Logic with Exponential Backoff

```python
#!/usr/bin/env python3
"""
Retry logic with exponential backoff for authentication operations.
"""

import asyncio
import time
import random
from typing import Optional, Callable, Any
from services.auth_service import CognitoAuthenticator, AuthenticationError

class RetryableAuthenticator:
    """Authenticator with built-in retry logic and exponential backoff."""
    
    def __init__(self, authenticator: CognitoAuthenticator, 
                 max_retries: int = 3, base_delay: float = 1.0):
        """Initialize retryable authenticator."""
        self.authenticator = authenticator
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def authenticate_with_retry(self, username: str, password: str) -> Optional[Any]:
        """Authenticate with retry logic and exponential backoff."""
        
        for attempt in range(self.max_retries + 1):
            try:
                print(f"🔐 Authentication attempt {attempt + 1}/{self.max_retries + 1}")
                
                tokens = self.authenticator.authenticate_user(username, password)
                
                print(f"✅ Authentication successful on attempt {attempt + 1}")
                return tokens
                
            except AuthenticationError as e:
                # Don't retry for certain error types
                non_retryable_errors = [
                    'AUTHENTICATION_FAILED',  # Wrong credentials
                    'USER_NOT_FOUND',         # User doesn't exist
                    'USER_NOT_CONFIRMED'      # User not verified
                ]
                
                if e.error_type in non_retryable_errors:
                    print(f"❌ Non-retryable error: {e.error_type}")
                    raise e
                
                if attempt < self.max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = self.base_delay * (2 ** attempt)
                    jitter = random.uniform(0, 0.1 * delay)
                    total_delay = delay + jitter
                    
                    print(f"⚠️ Attempt {attempt + 1} failed: {e.error_type}")
                    print(f"⏳ Retrying in {total_delay:.2f} seconds...")
                    
                    await asyncio.sleep(total_delay)
                else:
                    print(f"❌ All {self.max_retries + 1} attempts failed")
                    raise e
        
        return None
    
    async def refresh_token_with_retry(self, refresh_token: str) -> Optional[Any]:
        """Refresh token with retry logic."""
        
        for attempt in range(self.max_retries + 1):
            try:
                print(f"🔄 Token refresh attempt {attempt + 1}/{self.max_retries + 1}")
                
                tokens = self.authenticator.refresh_token(refresh_token)
                
                print(f"✅ Token refresh successful on attempt {attempt + 1}")
                return tokens
                
            except AuthenticationError as e:
                # Don't retry for invalid refresh tokens
                if e.error_code == 'NotAuthorizedException':
                    print(f"❌ Invalid refresh token, cannot retry")
                    raise e
                
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    jitter = random.uniform(0, 0.1 * delay)
                    total_delay = delay + jitter
                    
                    print(f"⚠️ Refresh attempt {attempt + 1} failed: {e.error_type}")
                    print(f"⏳ Retrying in {total_delay:.2f} seconds...")
                    
                    await asyncio.sleep(total_delay)
                else:
                    print(f"❌ All {self.max_retries + 1} refresh attempts failed")
                    raise e
        
        return None

async def retry_logic_example():
    """Demonstrate retry logic with exponential backoff."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Create base authenticator
    base_authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Create retryable authenticator
    retryable_auth = RetryableAuthenticator(
        authenticator=base_authenticator,
        max_retries=3,
        base_delay=1.0
    )
    
    # Test authentication with retry
    try:
        start_time = time.time()
        
        tokens = await retryable_auth.authenticate_with_retry(
            username=config['test_user']['email'],
            password='TempPass123!'  # Use actual password
        )
        
        end_time = time.time()
        
        if tokens:
            print(f"\n✅ Authentication completed in {end_time - start_time:.2f} seconds")
            print(f"Access Token: {tokens.access_token[:50]}...")
            
            # Test token refresh with retry
            print(f"\n🔄 Testing token refresh with retry...")
            
            refresh_start = time.time()
            new_tokens = await retryable_auth.refresh_token_with_retry(
                tokens.refresh_token
            )
            refresh_end = time.time()
            
            if new_tokens:
                print(f"✅ Token refresh completed in {refresh_end - refresh_start:.2f} seconds")
        
    except AuthenticationError as e:
        print(f"\n❌ Final authentication failure:")
        print(f"  Error Type: {e.error_type}")
        print(f"  Message: {e.message}")
        print(f"  Suggested Action: {e.suggested_action}")

if __name__ == "__main__":
    asyncio.run(retry_logic_example())
```

## Token Refresh Scenarios

### Automatic Token Refresh Manager

```python
#!/usr/bin/env python3
"""
Automatic token refresh manager for long-running applications.
"""

import asyncio
import json
import time
from typing import Optional, Callable
from dataclasses import dataclass
from services.auth_service import CognitoAuthenticator, AuthenticationTokens, AuthenticationError

@dataclass
class TokenState:
    """Token state management."""
    tokens: Optional[AuthenticationTokens] = None
    expires_at: Optional[float] = None
    refresh_threshold: float = 300  # 5 minutes before expiry
    last_refresh: Optional[float] = None

class TokenManager:
    """Automatic token refresh manager."""
    
    def __init__(self, authenticator: CognitoAuthenticator, 
                 token_file: str = 'user_tokens.json'):
        """Initialize token manager."""
        self.authenticator = authenticator
        self.token_file = token_file
        self.state = TokenState()
        self.refresh_callbacks = []
        self._refresh_task = None
        self._running = False
    
    def add_refresh_callback(self, callback: Callable[[AuthenticationTokens], None]):
        """Add callback to be called when tokens are refreshed."""
        self.refresh_callbacks.append(callback)
    
    async def initialize(self, username: str = None, password: str = None) -> bool:
        """Initialize token manager with authentication."""
        
        # Try to load existing tokens
        if await self._load_tokens():
            if await self._validate_current_tokens():
                print("✅ Loaded valid tokens from file")
                return True
        
        # Authenticate if credentials provided
        if username and password:
            try:
                print("🔐 Performing initial authentication...")
                tokens = self.authenticator.authenticate_user(username, password)
                
                self.state.tokens = tokens
                self.state.expires_at = time.time() + tokens.expires_in
                self.state.last_refresh = time.time()
                
                await self._save_tokens()
                print("✅ Initial authentication successful")
                return True
                
            except AuthenticationError as e:
                print(f"❌ Initial authentication failed: {e.message}")
                return False
        
        print("❌ No valid tokens and no credentials provided")
        return False
    
    async def get_valid_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary."""
        
        if not self.state.tokens:
            return None
        
        # Check if token needs refresh
        if self._needs_refresh():
            if not await self._refresh_tokens():
                return None
        
        return self.state.tokens.access_token
    
    def start_auto_refresh(self):
        """Start automatic token refresh background task."""
        if not self._running:
            self._running = True
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
            print("🔄 Started automatic token refresh")
    
    def stop_auto_refresh(self):
        """Stop automatic token refresh."""
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
            print("⏹️ Stopped automatic token refresh")
    
    async def _auto_refresh_loop(self):
        """Background task for automatic token refresh."""
        
        while self._running:
            try:
                if self._needs_refresh():
                    print("🔄 Auto-refreshing tokens...")
                    await self._refresh_tokens()
                
                # Check every minute
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Auto-refresh error: {e}")
                await asyncio.sleep(60)
    
    def _needs_refresh(self) -> bool:
        """Check if tokens need refresh."""
        if not self.state.tokens or not self.state.expires_at:
            return False
        
        time_until_expiry = self.state.expires_at - time.time()
        return time_until_expiry <= self.state.refresh_threshold
    
    async def _refresh_tokens(self) -> bool:
        """Refresh access tokens using refresh token."""
        
        if not self.state.tokens or not self.state.tokens.refresh_token:
            print("❌ No refresh token available")
            return False
        
        try:
            new_tokens = self.authenticator.refresh_token(
                self.state.tokens.refresh_token
            )
            
            # Update state
            old_refresh_token = self.state.tokens.refresh_token
            self.state.tokens = new_tokens
            self.state.tokens.refresh_token = old_refresh_token  # Keep original refresh token
            self.state.expires_at = time.time() + new_tokens.expires_in
            self.state.last_refresh = time.time()
            
            await self._save_tokens()
            
            # Notify callbacks
            for callback in self.refresh_callbacks:
                try:
                    callback(self.state.tokens)
                except Exception as e:
                    print(f"⚠️ Refresh callback error: {e}")
            
            print("✅ Tokens refreshed successfully")
            return True
            
        except AuthenticationError as e:
            print(f"❌ Token refresh failed: {e.message}")
            return False
    
    async def _validate_current_tokens(self) -> bool:
        """Validate current tokens."""
        if not self.state.tokens:
            return False
        
        try:
            self.authenticator.validate_user_session(self.state.tokens.access_token)
            return True
        except Exception:
            return False
    
    async def _load_tokens(self) -> bool:
        """Load tokens from file."""
        try:
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            self.state.tokens = AuthenticationTokens(
                id_token=token_data['id_token'],
                access_token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                expires_in=token_data['expires_in'],
                token_type=token_data.get('token_type', 'Bearer')
            )
            
            # Calculate expiry time
            if 'refreshed_at' in token_data:
                self.state.expires_at = token_data['refreshed_at'] + token_data['expires_in']
                self.state.last_refresh = token_data['refreshed_at']
            else:
                # Assume tokens are fresh
                self.state.expires_at = time.time() + token_data['expires_in']
                self.state.last_refresh = time.time()
            
            return True
            
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            return False
    
    async def _save_tokens(self):
        """Save tokens to file."""
        if not self.state.tokens:
            return
        
        token_data = {
            'id_token': self.state.tokens.id_token,
            'access_token': self.state.tokens.access_token,
            'refresh_token': self.state.tokens.refresh_token,
            'expires_in': self.state.tokens.expires_in,
            'token_type': self.state.tokens.token_type,
            'refreshed_at': self.state.last_refresh or time.time()
        }
        
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)

async def token_manager_example():
    """Demonstrate automatic token management."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    # Create authenticator
    authenticator = CognitoAuthenticator(
        user_pool_id=config['user_pool']['user_pool_id'],
        client_id=config['app_client']['client_id'],
        region=config['region']
    )
    
    # Create token manager
    token_manager = TokenManager(authenticator)
    
    # Add refresh callback
    def on_token_refresh(tokens):
        print(f"🔔 Tokens refreshed at {time.strftime('%H:%M:%S')}")
    
    token_manager.add_refresh_callback(on_token_refresh)
    
    # Initialize with credentials
    success = await token_manager.initialize(
        username=config['test_user']['email'],
        password='TempPass123!'  # Use actual password
    )
    
    if not success:
        print("❌ Failed to initialize token manager")
        return
    
    # Start auto-refresh
    token_manager.start_auto_refresh()
    
    try:
        # Simulate long-running application
        for i in range(10):
            print(f"\n[{i+1}/10] Getting valid token...")
            
            token = await token_manager.get_valid_token()
            if token:
                print(f"✅ Got valid token: {token[:50]}...")
                
                # Simulate some work
                await asyncio.sleep(2)
            else:
                print("❌ Failed to get valid token")
                break
        
        print("\n🎯 Simulating token expiry scenario...")
        
        # Force token refresh by setting short expiry
        if token_manager.state.tokens:
            token_manager.state.expires_at = time.time() + 10  # Expire in 10 seconds
            token_manager.state.refresh_threshold = 5  # Refresh 5 seconds before
            
            print("⏳ Waiting for auto-refresh...")
            await asyncio.sleep(15)
            
            # Get token after refresh
            token = await token_manager.get_valid_token()
            if token:
                print(f"✅ Token after auto-refresh: {token[:50]}...")
    
    finally:
        # Clean up
        token_manager.stop_auto_refresh()

if __name__ == "__main__":
    asyncio.run(token_manager_example())
```## Product
ion Integration Patterns

### Web Application Integration

```python
#!/usr/bin/env python3
"""
Web application integration example using FastAPI.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Optional
from services.auth_service import TokenValidator, AuthenticationError, UserContext

app = FastAPI(title="Restaurant Search API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# Global token validator
token_validator = None

@app.on_event("startup")
async def startup_event():
    """Initialize token validator on startup."""
    global token_validator
    
    # Load Cognito configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    validator_config = {
        'user_pool_id': config['user_pool']['user_pool_id'],
        'client_id': config['app_client']['client_id'],
        'region': config['region'],
        'discovery_url': config['discovery_url']
    }
    
    token_validator = TokenValidator(validator_config)
    print("✅ Token validator initialized")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserContext:
    """Dependency to get current authenticated user."""
    
    if not token_validator:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized"
        )
    
    try:
        # Validate JWT token
        claims = await token_validator.validate_jwt_token(credentials.credentials)
        
        # Create user context
        user_context = UserContext(
            user_id=claims.user_id,
            username=claims.username,
            email=claims.email,
            authenticated=True,
            token_claims=claims
        )
        
        return user_context
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.message}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/")
async def root():
    """Public endpoint - no authentication required."""
    return {"message": "Restaurant Search API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint - no authentication required."""
    return {"status": "healthy", "timestamp": "2025-09-27T12:00:00Z"}

@app.get("/profile")
async def get_user_profile(current_user: UserContext = Depends(get_current_user)):
    """Get user profile - authentication required."""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "authenticated": current_user.authenticated
    }

@app.post("/restaurants/search")
async def search_restaurants(
    search_request: dict,
    current_user: UserContext = Depends(get_current_user)
):
    """Search restaurants - authentication required."""
    
    # Log authenticated request
    print(f"🔍 Restaurant search by user: {current_user.email}")
    
    # Here you would integrate with your MCP client
    # For this example, we'll return a mock response
    
    districts = search_request.get('districts', [])
    meal_types = search_request.get('meal_types', [])
    
    return {
        "user": current_user.email,
        "search_criteria": {
            "districts": districts,
            "meal_types": meal_types
        },
        "results": [
            {
                "id": "rest_001",
                "name": "Sample Restaurant",
                "district": "Central district",
                "meal_types": ["breakfast", "lunch"],
                "address": "123 Sample Street, Central"
            }
        ],
        "total_results": 1
    }

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request, exc: AuthenticationError):
    """Global authentication error handler."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error_type": exc.error_type,
            "error_code": exc.error_code,
            "message": exc.message,
            "suggested_action": exc.suggested_action
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Client SDK Example

```python
#!/usr/bin/env python3
"""
Client SDK for Restaurant Search API with authentication.
"""

import json
import asyncio
import aiohttp
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from services.auth_service import CognitoAuthenticator, AuthenticationTokens, AuthenticationError

@dataclass
class RestaurantSearchRequest:
    """Restaurant search request model."""
    districts: Optional[List[str]] = None
    meal_types: Optional[List[str]] = None

@dataclass
class Restaurant:
    """Restaurant model."""
    id: str
    name: str
    district: str
    meal_types: List[str]
    address: str

class RestaurantSearchClient:
    """Client SDK for Restaurant Search API."""
    
    def __init__(self, api_base_url: str, cognito_config: Dict[str, Any]):
        """Initialize the client SDK."""
        self.api_base_url = api_base_url.rstrip('/')
        self.cognito_config = cognito_config
        
        self.authenticator = CognitoAuthenticator(
            user_pool_id=cognito_config['user_pool']['user_pool_id'],
            client_id=cognito_config['app_client']['client_id'],
            region=cognito_config['region']
        )
        
        self.access_token: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with the API."""
        try:
            tokens = self.authenticator.authenticate_user(username, password)
            self.access_token = tokens.access_token
            print("✅ Authentication successful")
            return True
        except AuthenticationError as e:
            print(f"❌ Authentication failed: {e.message}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {'Content-Type': 'application/json'}
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    async def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        async with self.session.get(
            f"{self.api_base_url}/profile",
            headers=self._get_headers()
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 401:
                raise AuthenticationError(
                    error_type="UNAUTHORIZED",
                    error_code="TOKEN_INVALID",
                    message="Authentication token is invalid or expired",
                    details="",
                    suggested_action="Re-authenticate with valid credentials"
                )
            else:
                response.raise_for_status()
    
    async def search_restaurants(self, search_request: RestaurantSearchRequest) -> List[Restaurant]:
        """Search for restaurants."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        request_data = {
            'districts': search_request.districts,
            'meal_types': search_request.meal_types
        }
        
        async with self.session.post(
            f"{self.api_base_url}/restaurants/search",
            headers=self._get_headers(),
            json=request_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                restaurants = []
                for item in data.get('results', []):
                    restaurant = Restaurant(
                        id=item['id'],
                        name=item['name'],
                        district=item['district'],
                        meal_types=item['meal_types'],
                        address=item['address']
                    )
                    restaurants.append(restaurant)
                
                return restaurants
            elif response.status == 401:
                raise AuthenticationError(
                    error_type="UNAUTHORIZED",
                    error_code="TOKEN_INVALID",
                    message="Authentication token is invalid or expired",
                    details="",
                    suggested_action="Re-authenticate with valid credentials"
                )
            else:
                response.raise_for_status()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health (no authentication required)."""
        async with self.session.get(f"{self.api_base_url}/health") as response:
            response.raise_for_status()
            return await response.json()

async def client_sdk_example():
    """Demonstrate client SDK usage."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        cognito_config = json.load(f)
    
    api_url = "http://localhost:8000"  # Your API URL
    
    async with RestaurantSearchClient(api_url, cognito_config) as client:
        # Test health check (no auth required)
        print("🏥 Testing health check...")
        health = await client.health_check()
        print(f"Health status: {health['status']}")
        
        # Authenticate
        print("\n🔐 Authenticating...")
        success = await client.authenticate(
            username=cognito_config['test_user']['email'],
            password='TempPass123!'  # Use actual password
        )
        
        if not success:
            print("❌ Authentication failed")
            return
        
        # Get user profile
        print("\n👤 Getting user profile...")
        profile = await client.get_profile()
        print(f"User: {profile['email']}")
        
        # Search restaurants
        print("\n🔍 Searching restaurants...")
        
        search_requests = [
            RestaurantSearchRequest(districts=['Central district']),
            RestaurantSearchRequest(meal_types=['breakfast']),
            RestaurantSearchRequest(
                districts=['Tsim Sha Tsui'],
                meal_types=['dinner']
            )
        ]
        
        for i, request in enumerate(search_requests, 1):
            print(f"\n[{i}] Search: districts={request.districts}, meal_types={request.meal_types}")
            
            try:
                restaurants = await client.search_restaurants(request)
                print(f"Found {len(restaurants)} restaurants:")
                
                for restaurant in restaurants:
                    print(f"  - {restaurant.name} ({restaurant.district})")
                    
            except Exception as e:
                print(f"❌ Search failed: {e}")

if __name__ == "__main__":
    asyncio.run(client_sdk_example())
```

### Production Configuration Example

```python
#!/usr/bin/env python3
"""
Production configuration and deployment example.
"""

import json
import os
from typing import Dict, Any

class ProductionConfig:
    """Production configuration management."""
    
    def __init__(self, environment: str = "production"):
        """Initialize production configuration."""
        self.environment = environment
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration based on environment."""
        
        # Base configuration
        config = {
            "authentication": {
                "token_refresh_threshold": 300,  # 5 minutes
                "max_retry_attempts": 3,
                "retry_base_delay": 1.0,
                "jwks_cache_ttl": 3600,  # 1 hour
                "session_timeout": 3600  # 1 hour
            },
            "api": {
                "timeout": 30,
                "max_connections": 100,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "burst_size": 10
                }
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "include_sensitive_data": False
            },
            "security": {
                "require_https": True,
                "cors_origins": [],
                "csrf_protection": True,
                "content_security_policy": True
            }
        }
        
        # Environment-specific overrides
        if self.environment == "development":
            config.update({
                "logging": {"level": "DEBUG"},
                "security": {
                    "require_https": False,
                    "cors_origins": ["http://localhost:3000", "http://localhost:8080"]
                }
            })
        elif self.environment == "staging":
            config.update({
                "security": {
                    "cors_origins": ["https://staging.example.com"]
                }
            })
        elif self.environment == "production":
            config.update({
                "security": {
                    "cors_origins": ["https://app.example.com"]
                }
            })
        
        # Load from environment variables
        self._load_from_env(config)
        
        return config
    
    def _load_from_env(self, config: Dict[str, Any]):
        """Load sensitive configuration from environment variables."""
        
        # Cognito configuration from environment
        cognito_config = {}
        
        env_mappings = {
            'COGNITO_USER_POOL_ID': 'user_pool_id',
            'COGNITO_CLIENT_ID': 'client_id',
            'COGNITO_REGION': 'region',
            'COGNITO_DISCOVERY_URL': 'discovery_url'
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                cognito_config[config_key] = value
        
        if cognito_config:
            config['cognito'] = cognito_config
        
        # API configuration from environment
        api_config = {}
        
        if os.getenv('API_BASE_URL'):
            api_config['base_url'] = os.getenv('API_BASE_URL')
        
        if os.getenv('MCP_SERVER_URL'):
            api_config['mcp_server_url'] = os.getenv('MCP_SERVER_URL')
        
        if api_config:
            config['api'].update(api_config)
        
        # Security configuration
        if os.getenv('SECRET_KEY'):
            config['security']['secret_key'] = os.getenv('SECRET_KEY')
        
        if os.getenv('CORS_ORIGINS'):
            origins = os.getenv('CORS_ORIGINS').split(',')
            config['security']['cors_origins'] = [origin.strip() for origin in origins]
    
    def get_cognito_config(self) -> Dict[str, Any]:
        """Get Cognito configuration."""
        if 'cognito' in self.config:
            return self.config['cognito']
        
        # Fall back to file-based configuration
        try:
            with open('cognito_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValueError("Cognito configuration not found in environment or file")
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.config['api']
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.config['security']
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config['logging']
    
    def validate_config(self) -> bool:
        """Validate configuration completeness."""
        
        required_cognito_fields = [
            'user_pool_id', 'client_id', 'region', 'discovery_url'
        ]
        
        try:
            cognito_config = self.get_cognito_config()
            
            for field in required_cognito_fields:
                if field not in cognito_config:
                    print(f"❌ Missing required Cognito field: {field}")
                    return False
            
            print("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False

def production_deployment_example():
    """Example of production deployment configuration."""
    
    # Set environment variables (in production, these would be set by your deployment system)
    os.environ.update({
        'ENVIRONMENT': 'production',
        'COGNITO_USER_POOL_ID': 'us-east-1_XXXXXXXXX',
        'COGNITO_CLIENT_ID': 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
        'COGNITO_REGION': 'us-east-1',
        'COGNITO_DISCOVERY_URL': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX/.well-known/openid-configuration',
        'API_BASE_URL': 'https://api.example.com',
        'MCP_SERVER_URL': 'https://mcp.example.com',
        'SECRET_KEY': 'your-secret-key-here',
        'CORS_ORIGINS': 'https://app.example.com,https://admin.example.com'
    })
    
    # Initialize production configuration
    config = ProductionConfig(environment='production')
    
    # Validate configuration
    if not config.validate_config():
        print("❌ Configuration validation failed")
        return
    
    print("🚀 Production Configuration:")
    print(f"Environment: {config.environment}")
    print(f"API Config: {json.dumps(config.get_api_config(), indent=2)}")
    print(f"Security Config: {json.dumps(config.get_security_config(), indent=2)}")
    print(f"Logging Config: {json.dumps(config.get_logging_config(), indent=2)}")
    
    # Example of using configuration in production
    cognito_config = config.get_cognito_config()
    print(f"\n🔐 Cognito Configuration:")
    print(f"User Pool ID: {cognito_config['user_pool_id']}")
    print(f"Client ID: {cognito_config['client_id']}")
    print(f"Region: {cognito_config['region']}")

if __name__ == "__main__":
    production_deployment_example()
```

## Summary

This document provides comprehensive examples for implementing authentication with the Restaurant Search MCP server:

### Key Components Covered:

1. **SRP Authentication**: Basic, interactive, and batch authentication examples
2. **JWT Token Management**: Validation, refresh, and automatic management
3. **MCP Client Integration**: Basic and advanced authenticated MCP clients
4. **Error Handling**: Comprehensive error handling with retry logic
5. **Token Refresh**: Automatic token refresh scenarios and management
6. **Production Integration**: Web API, client SDK, and production configuration

### Best Practices Demonstrated:

- **Security**: Proper token handling and validation
- **Reliability**: Retry logic with exponential backoff
- **Maintainability**: Clean error handling and logging
- **Scalability**: Automatic token management for long-running applications
- **Production-Ready**: Environment-based configuration and security

### Usage Guidelines:

1. Start with basic authentication examples to understand the flow
2. Implement error handling for robust applications
3. Use token managers for long-running applications
4. Follow production patterns for deployment
5. Customize examples based on your specific requirements

All examples are designed to work with the existing Restaurant Search MCP authentication infrastructure and can be adapted for different use cases and environments.