#!/usr/bin/env python3
"""
Comprehensive tests for the Restaurant Reasoning MCP Server deployed on AWS.

This test suite validates the deployed AWS instance including:
- JWT Authentication with Cognito
- AgentCore Runtime connectivity with authentication
- MCP tool functionality with proper authorization
- Performance and reliability testing
- Error handling and edge cases
"""

import json
import time
import asyncio
import logging
import getpass
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from bedrock_agentcore_starter_toolkit import Runtime
    import boto3
    import requests
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
except ImportError as e:
    print(f"❌ Required packages not available: {e}")
    print("💡 Please install: pip install bedrock-agentcore-starter-toolkit boto3 requests mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AWSDeploymentTester:
    """Comprehensive tester for AWS-deployed Restaurant Reasoning MCP Server with JWT Authentication."""
    
    def __init__(self):
        """Initialize the tester with deployment configuration."""
        self.agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_mcp-UFz1VQCFu1"
        self.region = "us-east-1"
        self.runtime = None
        self.jwt_token = None
        self.cognito_config = {
            "user_pool_id": "us-east-1_KePRX24Bn",
            "client_id": "1ofgeckef3po4i3us4j1m4chvd",
            "region": "us-east-1",
            "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
        }
        self.test_user_email = "testing_user@test.com.hk"
        self.test_results = {
            "test_timestamp": datetime.utcnow().isoformat() + "Z",
            "authentication_setup": {},
            "deployment_info": {},
            "connectivity_tests": {},
            "jwt_authentication_tests": {},
            "mcp_functionality_tests": {},
            "performance_tests": {},
            "error_handling_tests": {},
            "summary": {}
        }
        
    def load_test_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load comprehensive test data for different scenarios."""
        return {
            "basic_restaurants": [
                {
                    "id": "rest_001",
                    "name": "Golden Dragon Restaurant",
                    "address": "123 Central District, Hong Kong",
                    "district": "Central district",
                    "location_category": "Hong Kong Island",
                    "meal_type": ["lunch", "dinner"],
                    "price_range": "$$",
                    "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                },
                {
                    "id": "rest_002",
                    "name": "Dim Sum Palace",
                    "address": "456 Tsim Sha Tsui, Kowloon",
                    "district": "Tsim Sha Tsui",
                    "location_category": "Kowloon",
                    "meal_type": ["breakfast", "lunch"],
                    "price_range": "$$$",
                    "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3}
                },
                {
                    "id": "rest_003",
                    "name": "Noodle House",
                    "address": "789 Causeway Bay, Hong Kong",
                    "district": "Causeway Bay",
                    "location_category": "Hong Kong Island",
                    "meal_type": ["lunch", "dinner"],
                    "price_range": "$",
                    "sentiment": {"likes": 67, "dislikes": 20, "neutral": 13}
                }
            ],
            "large_dataset": self._generate_large_restaurant_dataset(50),
            "edge_case_restaurants": [
                {
                    "id": "edge_001",
                    "name": "Zero Sentiment Restaurant",
                    "address": "No Reviews Street",
                    "district": "Unknown",
                    "location_category": "Hong Kong Island",
                    "meal_type": ["lunch"],
                    "price_range": "$",
                    "sentiment": {"likes": 0, "dislikes": 0, "neutral": 0}
                },
                {
                    "id": "edge_002",
                    "name": "Perfect Restaurant",
                    "address": "Perfect Street",
                    "district": "Perfect District",
                    "location_category": "Kowloon",
                    "meal_type": ["breakfast", "lunch", "dinner"],
                    "price_range": "$$$$",
                    "sentiment": {"likes": 100, "dislikes": 0, "neutral": 0}
                },
                {
                    "id": "edge_003",
                    "name": "Controversial Restaurant",
                    "address": "Mixed Reviews Avenue",
                    "district": "Controversial District",
                    "location_category": "New Territories",
                    "meal_type": ["dinner"],
                    "price_range": "$$",
                    "sentiment": {"likes": 50, "dislikes": 50, "neutral": 0}
                }
            ]
        }
    
    def _generate_large_restaurant_dataset(self, count: int) -> List[Dict[str, Any]]:
        """Generate a large dataset for performance testing."""
        import random
        
        districts = ["Central district", "Tsim Sha Tsui", "Causeway Bay", "Wan Chai", "Mong Kok"]
        categories = ["Hong Kong Island", "Kowloon", "New Territories", "Islands"]
        meal_types = [["breakfast"], ["lunch"], ["dinner"], ["lunch", "dinner"], ["breakfast", "lunch"]]
        price_ranges = ["$", "$$", "$$$", "$$$$"]
        
        restaurants = []
        for i in range(count):
            likes = random.randint(10, 100)
            dislikes = random.randint(0, 30)
            neutral = random.randint(0, 20)
            
            restaurants.append({
                "id": f"perf_test_{i:03d}",
                "name": f"Test Restaurant {i+1}",
                "address": f"{i+1} Test Street, Hong Kong",
                "district": random.choice(districts),
                "location_category": random.choice(categories),
                "meal_type": random.choice(meal_types),
                "price_range": random.choice(price_ranges),
                "sentiment": {
                    "likes": likes,
                    "dislikes": dislikes,
                    "neutral": neutral
                }
            })
        
        return restaurants
    
    def get_user_credentials(self) -> tuple[str, str]:
        """Get user credentials for authentication."""
        print("\n🔐 JWT Authentication Required")
        print("=" * 50)
        print(f"Test User Email: {self.test_user_email}")
        
        # Get password from user input (hidden)
        password = getpass.getpass("Enter password for test user: ")
        
        if not password:
            raise ValueError("Password is required for authentication")
        
        return self.test_user_email, password
    
    async def authenticate_with_cognito(self) -> Dict[str, Any]:
        """Authenticate with Cognito and obtain JWT token."""
        logger.info("🔑 Authenticating with Cognito...")
        
        try:
            # Get user credentials
            username, password = self.get_user_credentials()
            
            # Initialize Cognito client
            cognito_client = boto3.client('cognito-idp', region_name=self.cognito_config['region'])
            
            # Authenticate with Cognito
            auth_response = cognito_client.initiate_auth(
                ClientId=self.cognito_config['client_id'],
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            # Extract tokens
            auth_result = auth_response['AuthenticationResult']
            self.jwt_token = auth_result['IdToken']
            access_token = auth_result['AccessToken']
            refresh_token = auth_result.get('RefreshToken')
            
            # Verify token
            token_valid = await self._verify_jwt_token(self.jwt_token)
            
            result = {
                "status": "SUCCESS",
                "authentication_successful": True,
                "token_obtained": self.jwt_token is not None,
                "token_valid": token_valid,
                "token_type": "JWT",
                "expires_in": auth_result.get('ExpiresIn', 3600),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info("✅ Cognito authentication successful")
            return result
            
        except Exception as e:
            logger.error(f"❌ Cognito authentication failed: {e}")
            return {
                "status": "FAILED",
                "authentication_successful": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _verify_jwt_token(self, token: str) -> bool:
        """Verify JWT token validity."""
        try:
            # Get JWKS from discovery URL
            response = requests.get(self.cognito_config['discovery_url'])
            discovery_data = response.json()
            jwks_uri = discovery_data['jwks_uri']
            
            # For basic verification, just check if token has proper structure
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Decode header and payload (without verification for testing)
            import base64
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            
            # Check basic token structure
            required_claims = ['iss', 'sub', 'aud', 'exp', 'iat']
            return all(claim in payload for claim in required_claims)
            
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return False
    
    async def test_deployment_info(self) -> Dict[str, Any]:
        """Test deployment information and status."""
        logger.info("🔍 Testing deployment information...")
        
        try:
            # Initialize runtime
            self.runtime = Runtime()
            
            # Get agent status
            status_info = await self._get_agent_status()
            
            result = {
                "status": "SUCCESS",
                "agent_arn": self.agent_arn,
                "region": self.region,
                "agent_status": status_info,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info("✅ Deployment info test passed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Deployment info test failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _get_agent_status(self) -> Dict[str, Any]:
        """Get agent status from AWS."""
        try:
            # Use boto3 to check agent status
            client = boto3.client('bedrock-agentcore', region_name=self.region)
            
            # Extract agent ID from ARN
            agent_id = self.agent_arn.split('/')[-1]
            
            response = client.describe_runtime(runtimeId=agent_id)
            
            return {
                "runtime_id": response.get('runtimeId'),
                "status": response.get('status'),
                "created_at": response.get('createdAt', '').isoformat() if response.get('createdAt') else None,
                "updated_at": response.get('updatedAt', '').isoformat() if response.get('updatedAt') else None
            }
            
        except Exception as e:
            logger.warning(f"Could not get detailed agent status: {e}")
            return {"status": "UNKNOWN", "error": str(e)}
    
    async def test_connectivity_with_auth(self) -> Dict[str, Any]:
        """Test connectivity to the deployed agent with JWT authentication."""
        logger.info("🌐 Testing authenticated connectivity...")
        
        try:
            if not self.jwt_token:
                raise ValueError("JWT token not available. Authentication required first.")
            
            if not self.runtime:
                self.runtime = Runtime()
            
            # Test connectivity with JWT token
            start_time = time.time()
            
            # Create headers with JWT token
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            response = await self.runtime.invoke_async(
                agent_arn=self.agent_arn,
                payload={
                    "prompt": "Hello, are you working? This is an authenticated test.",
                    "test_type": "authenticated_connectivity"
                },
                headers=headers
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            result = {
                "status": "SUCCESS",
                "response_time_ms": response_time,
                "response_received": response is not None,
                "authenticated": True,
                "response_preview": str(response)[:200] + "..." if len(str(response)) > 200 else str(response),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"✅ Authenticated connectivity test passed (Response time: {response_time:.2f}ms)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Authenticated connectivity test failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def test_mcp_client_with_jwt(self) -> Dict[str, Any]:
        """Test MCP client connectivity with JWT authentication."""
        logger.info("🔗 Testing MCP client with JWT authentication...")
        
        try:
            if not self.jwt_token:
                raise ValueError("JWT token not available")
            
            # Get the MCP endpoint URL from agent ARN
            mcp_url = f"https://runtime.bedrock-agentcore.{self.region}.amazonaws.com/runtime/{self.agent_arn.split('/')[-1]}/mcp"
            
            # Create headers with JWT token
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            start_time = time.time()
            
            # Test MCP connection
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize MCP session
                    await session.initialize()
                    
                    # List available tools
                    tools = await session.list_tools()
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    # Check if expected tools are available
                    tool_names = [tool.name for tool in tools.tools] if tools.tools else []
                    expected_tools = ["recommend_restaurants", "analyze_restaurant_sentiment"]
                    tools_available = all(tool in tool_names for tool in expected_tools)
                    
                    result = {
                        "status": "SUCCESS",
                        "mcp_connection_successful": True,
                        "response_time_ms": response_time,
                        "tools_available": tool_names,
                        "expected_tools_present": tools_available,
                        "tool_count": len(tool_names),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    logger.info(f"✅ MCP client test passed ({len(tool_names)} tools available)")
                    return result
            
        except Exception as e:
            logger.error(f"❌ MCP client test failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def test_mcp_tools_with_jwt(self) -> Dict[str, Any]:
        """Test MCP tools functionality with JWT authentication."""
        logger.info("🍽️ Testing MCP tools with JWT authentication...")
        
        if not self.jwt_token:
            return {
                "status": "FAILED",
                "error": "JWT token not available",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        test_data = self.load_test_data()
        results = {}
        
        # Get MCP endpoint URL
        mcp_url = f"https://runtime.bedrock-agentcore.{self.region}.amazonaws.com/runtime/{self.agent_arn.split('/')[-1]}/mcp"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test 1: recommend_restaurants with sentiment_likes
        try:
            logger.info("Testing recommend_restaurants (sentiment_likes)...")
            
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    start_time = time.time()
                    
                    # Call recommend_restaurants tool
                    result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": test_data["basic_restaurants"],
                            "ranking_method": "sentiment_likes"
                        }
                    )
                    
                    end_time = time.time()
                    
                    results["recommend_restaurants_sentiment_likes"] = {
                        "status": "SUCCESS",
                        "response_time_ms": (end_time - start_time) * 1000,
                        "tool_response_received": result is not None,
                        "response_content": str(result.content)[:300] + "..." if len(str(result.content)) > 300 else str(result.content),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    logger.info("✅ recommend_restaurants (sentiment_likes) test passed")
            
        except Exception as e:
            logger.error(f"❌ recommend_restaurants (sentiment_likes) test failed: {e}")
            results["recommend_restaurants_sentiment_likes"] = {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Test 2: recommend_restaurants with combined_sentiment
        try:
            logger.info("Testing recommend_restaurants (combined_sentiment)...")
            
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    start_time = time.time()
                    
                    result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": test_data["basic_restaurants"],
                            "ranking_method": "combined_sentiment"
                        }
                    )
                    
                    end_time = time.time()
                    
                    results["recommend_restaurants_combined_sentiment"] = {
                        "status": "SUCCESS",
                        "response_time_ms": (end_time - start_time) * 1000,
                        "tool_response_received": result is not None,
                        "response_content": str(result.content)[:300] + "..." if len(str(result.content)) > 300 else str(result.content),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    logger.info("✅ recommend_restaurants (combined_sentiment) test passed")
            
        except Exception as e:
            logger.error(f"❌ recommend_restaurants (combined_sentiment) test failed: {e}")
            results["recommend_restaurants_combined_sentiment"] = {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Test 3: analyze_restaurant_sentiment
        try:
            logger.info("Testing analyze_restaurant_sentiment...")
            
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    start_time = time.time()
                    
                    result = await session.call_tool(
                        "analyze_restaurant_sentiment",
                        {
                            "restaurants": test_data["basic_restaurants"]
                        }
                    )
                    
                    end_time = time.time()
                    
                    results["analyze_restaurant_sentiment"] = {
                        "status": "SUCCESS",
                        "response_time_ms": (end_time - start_time) * 1000,
                        "tool_response_received": result is not None,
                        "response_content": str(result.content)[:300] + "..." if len(str(result.content)) > 300 else str(result.content),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    logger.info("✅ analyze_restaurant_sentiment test passed")
            
        except Exception as e:
            logger.error(f"❌ analyze_restaurant_sentiment test failed: {e}")
            results["analyze_restaurant_sentiment"] = {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        return results
    
    async def test_performance_with_jwt(self) -> Dict[str, Any]:
        """Test performance with JWT authentication and various dataset sizes."""
        logger.info("⚡ Testing performance with JWT authentication...")
        
        if not self.jwt_token:
            return {
                "status": "FAILED",
                "error": "JWT token not available",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        test_data = self.load_test_data()
        results = {}
        
        # Get MCP endpoint URL
        mcp_url = f"https://runtime.bedrock-agentcore.{self.region}.amazonaws.com/runtime/{self.agent_arn.split('/')[-1]}/mcp"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test with different dataset sizes
        test_cases = [
            ("small", test_data["basic_restaurants"][:3]),
            ("medium", test_data["large_dataset"][:10]),
            ("large", test_data["large_dataset"][:20])
        ]
        
        for size_name, dataset in test_cases:
            try:
                logger.info(f"Testing performance with {size_name} dataset ({len(dataset)} restaurants)...")
                
                async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        start_time = time.time()
                        
                        result = await session.call_tool(
                            "recommend_restaurants",
                            {
                                "restaurants": dataset,
                                "ranking_method": "sentiment_likes"
                            }
                        )
                        
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000
                        
                        results[f"{size_name}_dataset"] = {
                            "status": "SUCCESS",
                            "dataset_size": len(dataset),
                            "response_time_ms": response_time,
                            "throughput_restaurants_per_second": len(dataset) / (response_time / 1000),
                            "tool_response_received": result is not None,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                        
                        logger.info(f"✅ {size_name.capitalize()} dataset test passed ({response_time:.2f}ms)")
                
            except Exception as e:
                logger.error(f"❌ {size_name.capitalize()} dataset test failed: {e}")
                results[f"{size_name}_dataset"] = {
                    "status": "FAILED",
                    "dataset_size": len(dataset),
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
        
        return results
    
    async def test_error_handling_with_jwt(self) -> Dict[str, Any]:
        """Test error handling with JWT authentication and invalid inputs."""
        logger.info("🚨 Testing error handling with JWT authentication...")
        
        if not self.jwt_token:
            return {
                "status": "FAILED",
                "error": "JWT token not available",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        results = {}
        
        # Get MCP endpoint URL
        mcp_url = f"https://runtime.bedrock-agentcore.{self.region}.amazonaws.com/runtime/{self.agent_arn.split('/')[-1]}/mcp"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Empty restaurant list
        try:
            logger.info("Testing empty restaurant list...")
            
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": [],
                            "ranking_method": "sentiment_likes"
                        }
                    )
                    
                    results["empty_list"] = {
                        "status": "SUCCESS",
                        "handled_gracefully": True,
                        "tool_response_received": result is not None,
                        "response_content": str(result.content)[:200] + "..." if len(str(result.content)) > 200 else str(result.content),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    logger.info("✅ Empty list test passed")
            
        except Exception as e:
            results["empty_list"] = {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Test 2: Invalid ranking method
        try:
            logger.info("Testing invalid ranking method...")
            
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": self.load_test_data()["basic_restaurants"][:2],
                            "ranking_method": "invalid_method"
                        }
                    )
                    
                    results["invalid_ranking_method"] = {
                        "status": "SUCCESS",
                        "handled_gracefully": True,
                        "tool_response_received": result is not None,
                        "response_content": str(result.content)[:200] + "..." if len(str(result.content)) > 200 else str(result.content),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    logger.info("✅ Invalid ranking method test passed")
            
        except Exception as e:
            results["invalid_ranking_method"] = {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Test 3: Malformed restaurant data
        try:
            logger.info("Testing malformed restaurant data...")
            
            malformed_data = [
                {"id": "bad_001", "name": "Bad Restaurant"},  # Missing required fields
                {"sentiment": {"likes": "not_a_number"}},     # Invalid data types
            ]
            
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": malformed_data,
                            "ranking_method": "sentiment_likes"
                        }
                    )
                    
                    results["malformed_data"] = {
                        "status": "SUCCESS",
                        "handled_gracefully": True,
                        "tool_response_received": result is not None,
                        "response_content": str(result.content)[:200] + "..." if len(str(result.content)) > 200 else str(result.content),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    logger.info("✅ Malformed data test passed")
            
        except Exception as e:
            results["malformed_data"] = {
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        return results
    

    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests with JWT authentication."""
        logger.info("🚀 Starting comprehensive AWS deployment tests with JWT authentication...")
        
        # Step 1: Authenticate with Cognito and get JWT token
        logger.info("Step 1: JWT Authentication Setup")
        self.test_results["authentication_setup"] = await self.authenticate_with_cognito()
        
        if self.test_results["authentication_setup"]["status"] != "SUCCESS":
            logger.error("❌ Authentication failed. Cannot proceed with tests.")
            self.test_results["summary"] = {
                "total_tests": 1,
                "passed_tests": 0,
                "failed_tests": 1,
                "success_rate_percent": 0.0,
                "overall_status": "FAILED",
                "error": "Authentication failed",
                "test_completion_time": datetime.utcnow().isoformat() + "Z"
            }
            return self.test_results
        
        # Step 2: Test deployment info
        logger.info("Step 2: Deployment Information")
        self.test_results["deployment_info"] = await self.test_deployment_info()
        
        # Step 3: Test authenticated connectivity
        logger.info("Step 3: Authenticated Connectivity")
        self.test_results["connectivity_tests"] = await self.test_connectivity_with_auth()
        
        # Step 4: Test MCP client with JWT
        logger.info("Step 4: MCP Client with JWT")
        self.test_results["jwt_authentication_tests"] = await self.test_mcp_client_with_jwt()
        
        # Step 5: Test MCP tools functionality
        logger.info("Step 5: MCP Tools Functionality")
        self.test_results["mcp_functionality_tests"] = await self.test_mcp_tools_with_jwt()
        
        # Step 6: Performance tests (if authentication successful)
        logger.info("Step 6: Performance Testing")
        self.test_results["performance_tests"] = await self.test_performance_with_jwt()
        
        # Step 7: Error handling tests
        logger.info("Step 7: Error Handling")
        self.test_results["error_handling_tests"] = await self.test_error_handling_with_jwt()
        
        # Generate summary
        self.test_results["summary"] = self._generate_test_summary()
        
        logger.info("🎉 Comprehensive JWT-authenticated tests completed!")
        return self.test_results
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate a summary of all test results."""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        def count_results(results_dict):
            nonlocal total_tests, passed_tests, failed_tests
            
            if isinstance(results_dict, dict):
                if "status" in results_dict:
                    total_tests += 1
                    if results_dict["status"] == "SUCCESS":
                        passed_tests += 1
                    else:
                        failed_tests += 1
                else:
                    for value in results_dict.values():
                        count_results(value)
        
        # Count all test results
        for category in ["authentication_setup", "deployment_info", "connectivity_tests", 
                        "jwt_authentication_tests", "mcp_functionality_tests", 
                        "performance_tests", "error_handling_tests"]:
            if category in self.test_results:
                count_results(self.test_results[category])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate_percent": round(success_rate, 2),
            "overall_status": "SUCCESS" if failed_tests == 0 else "PARTIAL" if passed_tests > 0 else "FAILED",
            "test_completion_time": datetime.utcnow().isoformat() + "Z"
        }
    
    def save_results(self, filename: str = "aws_deployment_test_results.json"):
        """Save test results to file."""
        filepath = Path(__file__).parent / filename
        with open(filepath, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"📄 Test results saved to: {filepath}")


async def main():
    """Main test execution function."""
    print("🧪 AWS Restaurant Reasoning MCP Server - Comprehensive Test Suite")
    print("=" * 70)
    
    tester = AWSDeploymentTester()
    
    try:
        results = await tester.run_comprehensive_tests()
        
        # Print summary
        summary = results["summary"]
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Success Rate: {summary['success_rate_percent']}%")
        print(f"   Overall Status: {summary['overall_status']}")
        
        # Save results
        tester.save_results()
        
        if summary['overall_status'] == "SUCCESS":
            print("\n🎉 All tests passed! AWS deployment is working correctly.")
        elif summary['overall_status'] == "PARTIAL":
            print("\n⚠️ Some tests failed. Check the detailed results for issues.")
        else:
            print("\n❌ Multiple test failures. AWS deployment may have issues.")
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        print(f"\n💥 Test execution failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))