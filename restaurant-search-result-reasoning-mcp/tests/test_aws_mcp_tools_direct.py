#!/usr/bin/env python3
"""
Direct MCP Tools Test for AWS-deployed Restaurant Reasoning Server.

This script tests the MCP tools directly using the MCP client with JWT authentication.
It focuses specifically on testing the recommend_restaurants and analyze_restaurant_sentiment tools.
"""

import json
import time
import asyncio
import logging
import getpass
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import sys

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import boto3
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
except ImportError as e:
    print(f"❌ Required packages not available: {e}")
    print("💡 Please install: pip install boto3 mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPToolsTester:
    """Direct MCP tools tester with JWT authentication."""
    
    def __init__(self):
        """Initialize the tester."""
        self.agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_mcp-UFz1VQCFu1"
        self.region = "us-east-1"
        self.cognito_config = {
            "user_pool_id": "us-east-1_KePRX24Bn",
            "client_id": "26k0pnja579pdpb1pt6savs27e",
            "region": "us-east-1"
        }
        self.test_user_email = "testing_user@test.com.hk"
        self.jwt_token = None
        self.mcp_url = f"https://runtime.bedrock-agentcore.{self.region}.amazonaws.com/runtime/{self.agent_arn.split('/')[-1]}/mcp"
    
    def get_user_credentials(self) -> tuple[str, str]:
        """Get user credentials for authentication."""
        print("\n🔐 JWT Authentication Required")
        print("=" * 50)
        print(f"Test User Email: {self.test_user_email}")
        print(f"AWS Region: {self.region}")
        print(f"User Pool ID: {self.cognito_config['user_pool_id']}")
        
        password = getpass.getpass("Enter password for test user: ")
        
        if not password:
            raise ValueError("Password is required for authentication")
        
        return self.test_user_email, password
    
    async def authenticate(self) -> bool:
        """Authenticate with Cognito and obtain JWT token."""
        logger.info("🔑 Authenticating with Cognito...")
        
        try:
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
            
            # Extract JWT token
            auth_result = auth_response['AuthenticationResult']
            self.jwt_token = auth_result['IdToken']
            
            logger.info("✅ Authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            return False
    
    def create_test_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create test restaurant data."""
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
                },
                {
                    "id": "rest_004",
                    "name": "Seafood Paradise",
                    "address": "321 Aberdeen, Hong Kong",
                    "district": "Aberdeen",
                    "location_category": "Hong Kong Island",
                    "meal_type": ["dinner"],
                    "price_range": "$$$$",
                    "sentiment": {"likes": 78, "dislikes": 12, "neutral": 10}
                },
                {
                    "id": "rest_005",
                    "name": "Tea Garden Cafe",
                    "address": "654 Wan Chai, Hong Kong",
                    "district": "Wan Chai",
                    "location_category": "Hong Kong Island",
                    "meal_type": ["breakfast", "lunch"],
                    "price_range": "$$",
                    "sentiment": {"likes": 45, "dislikes": 35, "neutral": 20}
                }
            ]
        }
    
    async def test_mcp_connection(self) -> Dict[str, Any]:
        """Test MCP connection and list available tools."""
        logger.info("🔗 Testing MCP connection...")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List available tools
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools] if tools.tools else []
                    
                    result = {
                        "status": "SUCCESS",
                        "connection_successful": True,
                        "tools_available": tool_names,
                        "tool_count": len(tool_names),
                        "expected_tools_present": all(tool in tool_names for tool in ["recommend_restaurants", "analyze_restaurant_sentiment"])
                    }
                    
                    logger.info(f"✅ MCP connection successful. Found {len(tool_names)} tools: {tool_names}")
                    return result
        
        except Exception as e:
            logger.error(f"❌ MCP connection failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_recommend_restaurants(self, ranking_method: str = "sentiment_likes") -> Dict[str, Any]:
        """Test the recommend_restaurants tool."""
        logger.info(f"🍽️ Testing recommend_restaurants (method: {ranking_method})...")
        
        try:
            test_data = self.create_test_data()
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    start_time = time.time()
                    
                    result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": test_data["basic_restaurants"],
                            "ranking_method": ranking_method
                        }
                    )
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    # Parse the response
                    response_content = str(result.content)
                    
                    test_result = {
                        "status": "SUCCESS",
                        "ranking_method": ranking_method,
                        "response_time_ms": response_time,
                        "response_received": result is not None,
                        "response_length": len(response_content),
                        "contains_recommendation": "recommendation" in response_content.lower(),
                        "contains_candidates": "candidates" in response_content.lower(),
                        "response_preview": response_content[:500] + "..." if len(response_content) > 500 else response_content
                    }
                    
                    logger.info(f"✅ recommend_restaurants ({ranking_method}) test passed ({response_time:.2f}ms)")
                    return test_result
        
        except Exception as e:
            logger.error(f"❌ recommend_restaurants ({ranking_method}) test failed: {e}")
            return {
                "status": "FAILED",
                "ranking_method": ranking_method,
                "error": str(e)
            }
    
    async def test_analyze_restaurant_sentiment(self) -> Dict[str, Any]:
        """Test the analyze_restaurant_sentiment tool."""
        logger.info("📊 Testing analyze_restaurant_sentiment...")
        
        try:
            test_data = self.create_test_data()
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            async with streamablehttp_client(self.mcp_url, headers=headers) as (read, write, _):
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
                    response_time = (end_time - start_time) * 1000
                    
                    # Parse the response
                    response_content = str(result.content)
                    
                    test_result = {
                        "status": "SUCCESS",
                        "response_time_ms": response_time,
                        "response_received": result is not None,
                        "response_length": len(response_content),
                        "contains_analysis": "sentiment" in response_content.lower() or "analysis" in response_content.lower(),
                        "response_preview": response_content[:500] + "..." if len(response_content) > 500 else response_content
                    }
                    
                    logger.info(f"✅ analyze_restaurant_sentiment test passed ({response_time:.2f}ms)")
                    return test_result
        
        except Exception as e:
            logger.error(f"❌ analyze_restaurant_sentiment test failed: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MCP tool tests."""
        logger.info("🚀 Starting MCP tools testing...")
        
        test_results = {
            "test_timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_arn": self.agent_arn,
            "mcp_url": self.mcp_url,
            "tests": {}
        }
        
        # Step 1: Authenticate
        if not await self.authenticate():
            test_results["authentication"] = {"status": "FAILED", "error": "Authentication failed"}
            return test_results
        
        test_results["authentication"] = {"status": "SUCCESS", "message": "JWT authentication successful"}
        
        # Step 2: Test MCP connection
        test_results["tests"]["mcp_connection"] = await self.test_mcp_connection()
        
        if test_results["tests"]["mcp_connection"]["status"] != "SUCCESS":
            logger.error("❌ MCP connection failed. Skipping tool tests.")
            return test_results
        
        # Step 3: Test recommend_restaurants with sentiment_likes
        test_results["tests"]["recommend_restaurants_sentiment_likes"] = await self.test_recommend_restaurants("sentiment_likes")
        
        # Step 4: Test recommend_restaurants with combined_sentiment
        test_results["tests"]["recommend_restaurants_combined_sentiment"] = await self.test_recommend_restaurants("combined_sentiment")
        
        # Step 5: Test analyze_restaurant_sentiment
        test_results["tests"]["analyze_restaurant_sentiment"] = await self.test_analyze_restaurant_sentiment()
        
        # Generate summary
        total_tests = len([t for t in test_results["tests"].values() if "status" in t])
        passed_tests = len([t for t in test_results["tests"].values() if t.get("status") == "SUCCESS"])
        
        test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "overall_status": "SUCCESS" if passed_tests == total_tests else "PARTIAL" if passed_tests > 0 else "FAILED"
        }
        
        logger.info("🎉 MCP tools testing completed!")
        return test_results
    
    def save_results(self, results: Dict[str, Any], filename: str = "mcp_tools_test_results.json"):
        """Save test results to file."""
        filepath = Path(__file__).parent / filename
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Test results saved to: {filepath}")


async def main():
    """Main test execution function."""
    print("🧪 AWS Restaurant Reasoning MCP Tools - Direct Test Suite")
    print("=" * 65)
    
    tester = MCPToolsTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Print summary
        if "summary" in results:
            summary = results["summary"]
            print(f"\n📊 Test Summary:")
            print(f"   Total Tests: {summary['total_tests']}")
            print(f"   Passed: {summary['passed_tests']} ✅")
            print(f"   Failed: {summary['failed_tests']} ❌")
            print(f"   Success Rate: {summary['success_rate']:.1f}%")
            print(f"   Overall Status: {summary['overall_status']}")
        
        # Save results
        tester.save_results(results)
        
        if results.get("summary", {}).get("overall_status") == "SUCCESS":
            print("\n🎉 All MCP tool tests passed! AWS deployment is working correctly.")
            return 0
        else:
            print("\n⚠️ Some tests failed. Check the detailed results for issues.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        print(f"\n💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))