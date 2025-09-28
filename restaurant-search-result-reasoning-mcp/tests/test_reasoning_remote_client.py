#!/usr/bin/env python3
"""
Remote MCP client test for Restaurant Reasoning MCP server with JWT authentication.

This test creates a remote MCP client that connects to the deployed reasoning
MCP server using existing JWT token authentication from Cognito.

Requirements: 4.1, 4.2, 11.1, 11.2
"""

import json
import os
import sys
import getpass
from typing import Dict, Any, Optional
import asyncio

import boto3
from botocore.exceptions import ClientError
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Import existing authentication services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.auth_service import CognitoAuthenticator, AuthenticationError


class ReasoningRemoteClient:
    """Remote MCP client for reasoning server with JWT authentication."""
    
    def __init__(self, cognito_config: Dict[str, Any]):
        """
        Initialize remote client with Cognito configuration.
        
        Args:
            cognito_config: Cognito configuration dictionary
        """
        self.cognito_config = cognito_config
        self.access_token = None
        self.agentcore_runtime_url = None
        
        # Initialize existing CognitoAuthenticator service
        self.authenticator = CognitoAuthenticator(
            user_pool_id=cognito_config['user_pool']['user_pool_id'],
            client_id=cognito_config['app_client']['client_id'],
            region=cognito_config['region']
        )
    
    def authenticate_user(self, username: str = None) -> str:
        """
        Authenticate user and get JWT token using existing CognitoAuthenticator service.
        
        Security: This function never accepts passwords as parameters to prevent
        accidental hardcoding or logging of sensitive credentials.
        
        Args:
            username: Optional username, will prompt if not provided
            
        Returns:
            JWT access token or None if authentication fails
        """
        try:
            # Always prompt for credentials - never use hardcoded values
            if not username:
                username = input("Enter Cognito username (default: testing_user@test.com.hk): ").strip()
                if not username:
                    username = "testing_user@test.com.hk"
            
            # Always prompt for password securely - never accept it as parameter
            password = getpass.getpass(f"Enter password for {username}: ")
            
            if not password:
                print("❌ Password is required")
                return None
            
            print(f"🔐 Authenticating with Cognito using existing CognitoAuthenticator as: {username}")
            
            # Use existing CognitoAuthenticator service with SRP authentication
            tokens = self.authenticator.authenticate_user(username, password)
            
            access_token = tokens.access_token
            print("✓ JWT authentication successful using existing auth service")
            print(f"Access token length: {len(access_token)}")
            print(f"Token type: {tokens.token_type}")
            print(f"Expires in: {tokens.expires_in} seconds")
            
            self.access_token = access_token
            return access_token
            
        except AuthenticationError as e:
            print(f"✗ Authentication failed: {e.error_type} - {e.message}")
            print(f"Suggested action: {e.suggested_action}")
            return None
        except Exception as e:
            print(f"✗ Unexpected authentication error: {e}")
            return None
    
    def construct_agentcore_runtime_url(self, agent_arn: str) -> str:
        """
        Construct AgentCore Runtime URL from agent ARN.
        
        Args:
            agent_arn: AgentCore Runtime agent ARN
            
        Returns:
            MCP endpoint URL for the reasoning server
        """
        try:
            # Extract region and agent name from ARN
            # Format: arn:aws:bedrock-agentcore:region:account:runtime/agent-name
            arn_parts = agent_arn.split(':')
            region = arn_parts[3]
            agent_name = arn_parts[5].split('/')[-1]
            
            # Construct AgentCore Runtime URL
            runtime_url = f"https://{agent_name}.{region}.bedrock-agentcore.amazonaws.com"
            
            print(f"🌐 AgentCore Runtime URL: {runtime_url}")
            self.agentcore_runtime_url = runtime_url
            return runtime_url
            
        except Exception as e:
            print(f"✗ Failed to construct runtime URL: {e}")
            return None
    
    async def test_mcp_connection(self, mcp_url: str) -> bool:
        """
        Test MCP connection to reasoning server.
        
        Args:
            mcp_url: MCP server endpoint URL
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Prepare JWT headers
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            print(f"🔗 Testing MCP connection to: {mcp_url}")
            
            # Connect to MCP server
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize MCP session
                    await session.initialize()
                    print("✓ MCP session initialized successfully")
                    
                    # List available tools
                    tools = await session.list_tools()
                    print(f"✓ Found {len(tools.tools)} MCP tools:")
                    
                    for tool in tools.tools:
                        print(f"  - {tool.name}: {tool.description}")
                    
                    return True
                    
        except Exception as e:
            print(f"✗ MCP connection failed: {e}")
            return False
    
    async def test_reasoning_tools(self, mcp_url: str) -> bool:
        """
        Test reasoning MCP tools with sample restaurant data.
        
        Args:
            mcp_url: MCP server endpoint URL
            
        Returns:
            True if tools work correctly, False otherwise
        """
        try:
            # Prepare JWT headers
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Sample restaurant data with sentiment for testing
            sample_restaurants = [
                {
                    "id": "rest_001",
                    "name": "Golden Dragon Restaurant",
                    "address": "123 Central Street, Central",
                    "sentiment": {
                        "likes": 85,
                        "dislikes": 10,
                        "neutral": 15
                    },
                    "meal_type": ["Chinese", "Dim Sum"],
                    "district": "Central",
                    "price_range": "$$"
                },
                {
                    "id": "rest_002", 
                    "name": "Ocean View Cafe",
                    "address": "456 Harbour Road, Admiralty",
                    "sentiment": {
                        "likes": 92,
                        "dislikes": 5,
                        "neutral": 8
                    },
                    "meal_type": ["Western", "Seafood"],
                    "district": "Admiralty",
                    "price_range": "$$$"
                },
                {
                    "id": "rest_003",
                    "name": "Spice Garden",
                    "address": "789 Nathan Road, Tsim Sha Tsui",
                    "sentiment": {
                        "likes": 78,
                        "dislikes": 15,
                        "neutral": 12
                    },
                    "meal_type": ["Indian", "Vegetarian"],
                    "district": "Tsim Sha Tsui",
                    "price_range": "$$"
                }
            ]
            
            print("🧪 Testing reasoning MCP tools...")
            
            # Connect to MCP server
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Test 1: recommend_restaurants tool
                    print("\n📊 Testing recommend_restaurants tool...")
                    
                    recommendation_result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": sample_restaurants,
                            "ranking_method": "sentiment_likes"
                        }
                    )
                    
                    print("✓ Recommendation tool executed successfully")
                    
                    # Parse and display results
                    if recommendation_result.content:
                        result_data = json.loads(recommendation_result.content[0].text)
                        print(f"  - Found {len(result_data.get('candidates', []))} candidates")
                        print(f"  - Recommended: {result_data.get('recommendation', {}).get('name', 'Unknown')}")
                        print(f"  - Ranking method: {result_data.get('ranking_method', 'Unknown')}")
                    
                    # Test 2: analyze_restaurant_sentiment tool
                    print("\n📈 Testing analyze_restaurant_sentiment tool...")
                    
                    sentiment_result = await session.call_tool(
                        "analyze_restaurant_sentiment",
                        {
                            "restaurants": sample_restaurants
                        }
                    )
                    
                    print("✓ Sentiment analysis tool executed successfully")
                    
                    # Parse and display results
                    if sentiment_result.content:
                        sentiment_data = json.loads(sentiment_result.content[0].text)
                        print(f"  - Analyzed {sentiment_data.get('restaurant_count', 0)} restaurants")
                        print(f"  - Average likes: {sentiment_data.get('average_likes', 0):.1f}")
                        print(f"  - Top sentiment score: {sentiment_data.get('top_sentiment_score', 0):.1f}%")
                    
                    # Test 3: Test with combined_sentiment ranking
                    print("\n🔄 Testing combined sentiment ranking...")
                    
                    combined_result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": sample_restaurants,
                            "ranking_method": "combined_sentiment"
                        }
                    )
                    
                    print("✓ Combined sentiment ranking executed successfully")
                    
                    if combined_result.content:
                        combined_data = json.loads(combined_result.content[0].text)
                        print(f"  - Recommended: {combined_data.get('recommendation', {}).get('name', 'Unknown')}")
                        print(f"  - Ranking method: {combined_data.get('ranking_method', 'Unknown')}")
                    
                    return True
                    
        except Exception as e:
            print(f"✗ Reasoning tools test failed: {e}")
            return False
    
    async def run_comprehensive_test(self, agent_arn: str = None) -> Dict[str, bool]:
        """
        Run comprehensive test of reasoning MCP server with authentication.
        
        Args:
            agent_arn: Optional AgentCore Runtime agent ARN
            
        Returns:
            Dictionary with test results
        """
        results = {
            'authentication': False,
            'mcp_connection': False,
            'reasoning_tools': False,
            'overall_success': False
        }
        
        try:
            print("🚀 Starting comprehensive reasoning MCP client test...")
            print("=" * 70)
            
            # Step 1: Authentication
            print("\n🔐 Step 1: JWT Authentication...")
            access_token = self.authenticate_user()
            results['authentication'] = access_token is not None
            
            if not access_token:
                print("❌ Authentication failed - cannot proceed with MCP tests")
                return results
            
            # Step 2: Construct MCP URL
            print("\n🌐 Step 2: AgentCore Runtime URL Construction...")
            
            if not agent_arn:
                # Try to load from deployment config
                try:
                    with open('agentcore_deployment_config.json', 'r') as f:
                        deployment_config = json.load(f)
                        agent_arn = deployment_config.get('agent_arn')
                        print(f"📄 Loaded agent ARN from config: {agent_arn}")
                except Exception as e:
                    print(f"⚠️ Could not load deployment config: {e}")
                    # Use default reasoning server ARN (update this with actual ARN)
                    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_mcp"
                    print(f"🔧 Using default reasoning server ARN: {agent_arn}")
            
            mcp_url = self.construct_agentcore_runtime_url(agent_arn)
            
            if not mcp_url:
                print("❌ Failed to construct MCP URL")
                return results
            
            # Step 3: Test MCP Connection
            print("\n🔗 Step 3: MCP Connection Test...")
            connection_success = await self.test_mcp_connection(mcp_url)
            results['mcp_connection'] = connection_success
            
            if not connection_success:
                print("❌ MCP connection failed")
                return results
            
            # Step 4: Test Reasoning Tools
            print("\n🧪 Step 4: Reasoning Tools Test...")
            tools_success = await self.test_reasoning_tools(mcp_url)
            results['reasoning_tools'] = tools_success
            
            # Overall success
            results['overall_success'] = all([
                results['authentication'],
                results['mcp_connection'],
                results['reasoning_tools']
            ])
            
            return results
            
        except Exception as e:
            print(f"✗ Comprehensive test failed: {e}")
            return results


def load_cognito_config() -> Dict[str, Any]:
    """Load Cognito configuration from JSON file."""
    try:
        with open('cognito_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Failed to load Cognito config: {e}")
        return {}


async def main():
    """Main function to run reasoning remote client tests."""
    print("🚀 Restaurant Reasoning MCP Remote Client Test")
    print("=" * 70)
    
    # Load Cognito configuration
    cognito_config = load_cognito_config()
    if not cognito_config:
        print("❌ Could not load Cognito configuration")
        return 1
    
    print(f"✓ Loaded Cognito config for User Pool: {cognito_config['user_pool']['user_pool_id']}")
    
    # Initialize remote client
    client = ReasoningRemoteClient(cognito_config)
    
    # Run comprehensive test
    results = await client.run_comprehensive_test()
    
    # Display results
    print("\n" + "=" * 70)
    print("📋 Test Results Summary:")
    print(f"🔐 JWT Authentication: {'✅' if results['authentication'] else '❌'}")
    print(f"🔗 MCP Connection: {'✅' if results['mcp_connection'] else '❌'}")
    print(f"🧪 Reasoning Tools: {'✅' if results['reasoning_tools'] else '❌'}")
    print(f"🎯 Overall Success: {'✅' if results['overall_success'] else '❌'}")
    
    if results['overall_success']:
        print("\n🎉 All tests passed! Reasoning MCP server is working correctly.")
        print("✅ JWT authentication is functional")
        print("✅ MCP protocol connectivity is established")
        print("✅ Reasoning tools are operational")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        
        if not results['authentication']:
            print("- Verify Cognito credentials and user status")
            print("- Check that the test user password is correct")
        
        if not results['mcp_connection']:
            print("- Verify AgentCore Runtime deployment")
            print("- Check JWT authorizer configuration")
            print("- Ensure reasoning MCP server is deployed")
        
        if not results['reasoning_tools']:
            print("- Check reasoning MCP server implementation")
            print("- Verify tool registration and parameter schemas")
            print("- Review server logs for errors")
        
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test reasoning MCP remote client with JWT authentication')
    parser.add_argument('--agent-arn', help='AgentCore Runtime agent ARN for reasoning server')
    
    args = parser.parse_args()
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)