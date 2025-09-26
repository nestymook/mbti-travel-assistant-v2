#!/usr/bin/env python3
"""
Remote MCP Client with JWT Authentication

This module provides a test client for connecting to the Restaurant Search MCP
server deployed on Bedrock AgentCore Runtime with Cognito JWT authentication.

Requirements: 4.1, 4.2, 4.3, 8.3, 8.4
"""

import asyncio
import json
import os
import sys
from datetime import timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class CognitoAuthenticator:
    """Handle Cognito JWT token authentication."""
    
    def __init__(self, config_file: str = "cognito_config.json"):
        """Initialize authenticator with Cognito configuration.
        
        Args:
            config_file: Path to Cognito configuration file.
        """
        self.config = self._load_config(config_file)
        self.cognito_client = boto3.client(
            'cognito-idp', 
            region_name=self.config['region']
        )
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load Cognito configuration from file.
        
        Args:
            config_file: Path to configuration file.
            
        Returns:
            Configuration dictionary.
        """
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Cognito configuration file not found: {config_file}. "
                "Run setup_cognito.py first."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and retrieve JWT tokens.
        
        Args:
            username: User's email/username.
            password: User's password.
            
        Returns:
            Dictionary containing authentication tokens.
        """
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.config['app_client']['client_id'],
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            auth_result = response['AuthenticationResult']
            
            return {
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': auth_result['RefreshToken'],
                'token_type': auth_result['TokenType'],
                'expires_in': auth_result['ExpiresIn']
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise ValueError("Invalid username or password")
            elif error_code == 'UserNotConfirmedException':
                raise ValueError("User account not confirmed")
            else:
                raise ValueError(f"Authentication failed: {e}")
    
    def get_test_user_credentials(self) -> tuple[str, str]:
        """Get test user credentials from configuration.
        
        Returns:
            Tuple of (username, password).
        """
        test_user = self.config.get('test_user', {})
        username = test_user.get('email', 'test@example.com')
        # Default password from setup_cognito.py
        password = "TempPass123!"
        return username, password


class AgentCoreRuntimeClient:
    """Client for connecting to AgentCore Runtime with authentication."""
    
    def __init__(self, agent_arn: str, region: str = "us-east-1"):
        """Initialize AgentCore Runtime client.
        
        Args:
            agent_arn: ARN of the deployed AgentCore Runtime agent.
            region: AWS region where agent is deployed.
        """
        self.agent_arn = agent_arn
        self.region = region
        self.base_url = f"https://bedrock-agentcore.{region}.amazonaws.com"
    
    def construct_mcp_url(self, qualifier: str = "DEFAULT") -> str:
        """Construct MCP invocation URL for AgentCore Runtime.
        
        Args:
            qualifier: Agent qualifier (version/alias).
            
        Returns:
            Complete MCP invocation URL.
        """
        # URL encode the ARN for safe inclusion in URL path
        encoded_arn = quote(self.agent_arn, safe='')
        
        return f"{self.base_url}/runtimes/{encoded_arn}/invocations?qualifier={qualifier}"
    
    def create_auth_headers(self, bearer_token: str) -> Dict[str, str]:
        """Create authentication headers for MCP requests.
        
        Args:
            bearer_token: JWT access token from Cognito.
            
        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


class RemoteMCPClient:
    """Remote MCP client with JWT authentication for AgentCore Runtime."""
    
    def __init__(self, agent_arn: str, region: str = "us-east-1", 
                 config_file: str = "cognito_config.json"):
        """Initialize remote MCP client.
        
        Args:
            agent_arn: ARN of deployed AgentCore Runtime agent.
            region: AWS region.
            config_file: Path to Cognito configuration file.
        """
        self.authenticator = CognitoAuthenticator(config_file)
        self.runtime_client = AgentCoreRuntimeClient(agent_arn, region)
        self.bearer_token: Optional[str] = None
    
    async def authenticate(self, username: str = None, password: str = None) -> None:
        """Authenticate with Cognito and store bearer token.
        
        Args:
            username: User's email/username. Uses test user if None.
            password: User's password. Uses test password if None.
        """
        if username is None or password is None:
            username, password = self.authenticator.get_test_user_credentials()
        
        print(f"🔐 Authenticating user: {username}")
        
        try:
            auth_result = self.authenticator.authenticate_user(username, password)
            self.bearer_token = auth_result['access_token']
            print(f"✓ Authentication successful, token expires in {auth_result['expires_in']} seconds")
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            raise
    
    async def connect_and_test(self) -> Dict[str, Any]:
        """Connect to remote MCP server and test functionality.
        
        Returns:
            Dictionary containing test results.
        """
        if not self.bearer_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        mcp_url = self.runtime_client.construct_mcp_url()
        headers = self.runtime_client.create_auth_headers(self.bearer_token)
        
        print(f"🌐 Connecting to: {mcp_url}")
        
        try:
            async with streamablehttp_client(
                mcp_url, 
                headers, 
                timeout=timedelta(seconds=120)
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize session
                    await session.initialize()
                    print("✓ MCP session initialized")
                    
                    # List available tools
                    tools_response = await session.list_tools()
                    tools = tools_response.tools
                    print(f"✓ Found {len(tools)} MCP tools")
                    
                    # Test results
                    results = {
                        'connection_successful': True,
                        'tools_count': len(tools),
                        'available_tools': [tool.name for tool in tools],
                        'tool_tests': {}
                    }
                    
                    # Test each tool
                    for tool in tools:
                        print(f"🧪 Testing tool: {tool.name}")
                        try:
                            test_result = await self._test_tool(session, tool.name)
                            results['tool_tests'][tool.name] = {
                                'success': True,
                                'result': test_result
                            }
                            print(f"✓ Tool {tool.name} test passed")
                        except Exception as e:
                            results['tool_tests'][tool.name] = {
                                'success': False,
                                'error': str(e)
                            }
                            print(f"✗ Tool {tool.name} test failed: {e}")
                    
                    return results
                    
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return {
                'connection_successful': False,
                'error': str(e)
            }
    
    async def _test_tool(self, session: ClientSession, tool_name: str) -> Any:
        """Test a specific MCP tool with sample data.
        
        Args:
            session: Active MCP client session.
            tool_name: Name of the tool to test.
            
        Returns:
            Tool execution result.
        """
        # Define test parameters for each tool
        test_params = {
            'search_restaurants_by_district': {
                'districts': ['Central district', 'Admiralty']
            },
            'search_restaurants_by_meal_type': {
                'meal_types': ['lunch']
            },
            'search_restaurants_combined': {
                'districts': ['Central district'],
                'meal_types': ['dinner']
            }
        }
        
        if tool_name not in test_params:
            raise ValueError(f"No test parameters defined for tool: {tool_name}")
        
        # Call the tool
        result = await session.call_tool(
            name=tool_name,
            arguments=test_params[tool_name]
        )
        
        # Parse and validate result
        if hasattr(result, 'content') and result.content:
            content = result.content[0]
            if hasattr(content, 'text'):
                return json.loads(content.text)
        
        return result
    
    async def test_specific_tool(self, tool_name: str, **kwargs) -> Any:
        """Test a specific tool with custom parameters.
        
        Args:
            tool_name: Name of the tool to test.
            **kwargs: Tool parameters.
            
        Returns:
            Tool execution result.
        """
        if not self.bearer_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        mcp_url = self.runtime_client.construct_mcp_url()
        headers = self.runtime_client.create_auth_headers(self.bearer_token)
        
        async with streamablehttp_client(
            mcp_url, 
            headers, 
            timeout=timedelta(seconds=120)
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    name=tool_name,
                    arguments=kwargs
                )
                
                if hasattr(result, 'content') and result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                
                return result


async def run_comprehensive_tests(agent_arn: str, region: str = "us-east-1") -> None:
    """Run comprehensive tests of the remote MCP client.
    
    Args:
        agent_arn: ARN of deployed AgentCore Runtime agent.
        region: AWS region.
    """
    print("🚀 Starting Remote MCP Client Tests")
    print(f"Agent ARN: {agent_arn}")
    print(f"Region: {region}")
    print("-" * 60)
    
    try:
        # Initialize client
        client = RemoteMCPClient(agent_arn, region)
        
        # Authenticate
        await client.authenticate()
        
        # Run comprehensive tests
        results = await client.connect_and_test()
        
        # Print results
        print("\n📊 Test Results Summary:")
        print(f"Connection: {'✓ Success' if results['connection_successful'] else '✗ Failed'}")
        
        if results['connection_successful']:
            print(f"Tools Found: {results['tools_count']}")
            print(f"Available Tools: {', '.join(results['available_tools'])}")
            
            print("\n🧪 Tool Test Results:")
            for tool_name, test_result in results['tool_tests'].items():
                status = "✓ Pass" if test_result['success'] else "✗ Fail"
                print(f"  {tool_name}: {status}")
                if not test_result['success']:
                    print(f"    Error: {test_result['error']}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
        
        return results
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        raise


async def test_individual_tools(agent_arn: str, region: str = "us-east-1") -> None:
    """Test individual MCP tools with various parameters.
    
    Args:
        agent_arn: ARN of deployed AgentCore Runtime agent.
        region: AWS region.
    """
    print("🔧 Testing Individual MCP Tools")
    print("-" * 40)
    
    client = RemoteMCPClient(agent_arn, region)
    await client.authenticate()
    
    # Test district search
    print("\n1. Testing district search...")
    try:
        result = await client.test_specific_tool(
            'search_restaurants_by_district',
            districts=['Central district', 'Admiralty', 'Causeway Bay']
        )
        print(f"✓ Found {len(result.get('data', []))} restaurants")
    except Exception as e:
        print(f"✗ District search failed: {e}")
    
    # Test meal type search
    print("\n2. Testing meal type search...")
    try:
        result = await client.test_specific_tool(
            'search_restaurants_by_meal_type',
            meal_types=['breakfast', 'lunch']
        )
        print(f"✓ Found {len(result.get('data', []))} restaurants")
    except Exception as e:
        print(f"✗ Meal type search failed: {e}")
    
    # Test combined search
    print("\n3. Testing combined search...")
    try:
        result = await client.test_specific_tool(
            'search_restaurants_combined',
            districts=['Central district'],
            meal_types=['dinner']
        )
        print(f"✓ Found {len(result.get('data', []))} restaurants")
    except Exception as e:
        print(f"✗ Combined search failed: {e}")


def main():
    """Main function for running remote client tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Remote MCP Client with Authentication')
    parser.add_argument('agent_arn', help='ARN of deployed AgentCore Runtime agent')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--test-type', choices=['comprehensive', 'individual', 'both'], 
                       default='comprehensive', help='Type of tests to run')
    parser.add_argument('--username', help='Cognito username (uses test user if not provided)')
    parser.add_argument('--password', help='Cognito password (uses test password if not provided)')
    
    args = parser.parse_args()
    
    async def run_tests():
        try:
            if args.test_type in ['comprehensive', 'both']:
                await run_comprehensive_tests(args.agent_arn, args.region)
            
            if args.test_type in ['individual', 'both']:
                await test_individual_tools(args.agent_arn, args.region)
                
            print("\n🎉 All tests completed!")
            
        except Exception as e:
            print(f"\n💥 Tests failed: {e}")
            return 1
        
        return 0
    
    # Run async tests
    return asyncio.run(run_tests())


if __name__ == "__main__":
    sys.exit(main())