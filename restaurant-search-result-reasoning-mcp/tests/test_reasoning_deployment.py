#!/usr/bin/env python3
"""
Deployment Validation Tests for Restaurant Reasoning MCP Server.

This module provides comprehensive tests for validating the deployed reasoning MCP server,
including authentication flow, tool functionality, and performance validation.
"""

import pytest
import json
import asyncio
import time
import os
import boto3
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import MCP client components
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Import authentication services
from services.auth_service import CognitoAuthenticator
from models.auth_models import CognitoConfig, AuthenticationTokens


class TestReasoningDeployment:
    """Comprehensive deployment validation tests for reasoning MCP server."""
    
    @pytest.fixture
    def cognito_config(self) -> CognitoConfig:
        """Load Cognito configuration for authentication testing."""
        config_path = Path("cognito_config.json")
        if not config_path.exists():
            pytest.skip("Cognito configuration not found - skipping deployment tests")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return CognitoConfig(
            user_pool_id=config_data["user_pool_id"],
            client_id=config_data["client_id"],
            region=config_data["region"],
            discovery_url=config_data["discovery_url"],
            jwks_url=config_data["jwks_url"],
            issuer_url=config_data["issuer_url"]
        )
    
    @pytest.fixture
    def auth_tokens(self, cognito_config: CognitoConfig) -> Optional[AuthenticationTokens]:
        """Authenticate and get JWT tokens for testing."""
        try:
            authenticator = CognitoAuthenticator(cognito_config)
            
            # Get test credentials from environment or prompt
            username = os.getenv("TEST_USERNAME")
            password = os.getenv("TEST_PASSWORD")
            
            if not username or not password:
                pytest.skip("Test credentials not provided - set TEST_USERNAME and TEST_PASSWORD environment variables")
            
            tokens = authenticator.authenticate_user(username, password)
            return tokens
            
        except Exception as e:
            pytest.skip(f"Authentication failed: {e}")
    
    @pytest.fixture
    def agentcore_url(self) -> str:
        """Get AgentCore Runtime URL for the deployed reasoning server."""
        # Try to load from deployment results
        deployment_file = Path("deployment_test_results.json")
        if deployment_file.exists():
            with open(deployment_file, 'r') as f:
                deployment_data = json.load(f)
                if "agentcore_url" in deployment_data:
                    return deployment_data["agentcore_url"]
        
        # Fallback to environment variable
        url = os.getenv("AGENTCORE_REASONING_URL")
        if not url:
            pytest.skip("AgentCore URL not provided - set AGENTCORE_REASONING_URL environment variable or run deployment")
        
        return url
    
    @pytest.fixture
    def sample_reasoning_data(self) -> List[Dict[str, Any]]:
        """Generate sample restaurant data for reasoning tests."""
        return [
            {
                "id": "deploy_001",
                "name": "Deployment Test Restaurant A",
                "address": "123 Test Street, Central",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "location_category": "restaurant",
                "district": "Central district",
                "price_range": "$$"
            },
            {
                "id": "deploy_002",
                "name": "Deployment Test Restaurant B",
                "address": "456 Test Avenue, Admiralty",
                "meal_type": ["breakfast", "lunch"],
                "sentiment": {"likes": 70, "dislikes": 15, "neutral": 15},
                "location_category": "cafe",
                "district": "Admiralty",
                "price_range": "$"
            },
            {
                "id": "deploy_003",
                "name": "Deployment Test Restaurant C",
                "address": "789 Test Road, Causeway Bay",
                "meal_type": ["dinner"],
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "location_category": "fine_dining",
                "district": "Causeway Bay",
                "price_range": "$$$"
            }
        ]
    
    async def create_authenticated_mcp_client(
        self, 
        agentcore_url: str, 
        auth_tokens: AuthenticationTokens
    ) -> ClientSession:
        """Create authenticated MCP client session."""
        headers = {
            "Authorization": f"Bearer {auth_tokens.id_token}",
            "Content-Type": "application/json"
        }
        
        read, write, _ = await streamablehttp_client(agentcore_url, headers=headers)
        session = ClientSession(read, write)
        await session.initialize()
        return session
    
    @pytest.mark.asyncio
    async def test_deployment_connectivity(
        self, 
        agentcore_url: str, 
        auth_tokens: AuthenticationTokens
    ):
        """Test basic connectivity to deployed reasoning server."""
        try:
            session = await self.create_authenticated_mcp_client(agentcore_url, auth_tokens)
            
            # Test basic MCP protocol functionality
            tools = await session.list_tools()
            assert len(tools.tools) > 0, "No MCP tools found"
            
            # Verify reasoning tools are available
            tool_names = [tool.name for tool in tools.tools]
            expected_tools = ["recommend_restaurants", "analyze_restaurant_sentiment"]
            
            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"Missing expected tool: {expected_tool}"
            
            print(f"✅ Successfully connected to reasoning server at {agentcore_url}")
            print(f"Available tools: {tool_names}")
            
        except Exception as e:
            pytest.fail(f"Failed to connect to deployed reasoning server: {e}")
    
    @pytest.mark.asyncio
    async def test_authentication_flow_validation(
        self, 
        agentcore_url: str, 
        cognito_config: CognitoConfig
    ):
        """Test JWT authentication flow with Cognito tokens."""
        # Test without authentication (should fail)
        try:
            read, write, _ = await streamablehttp_client(agentcore_url)
            session = ClientSession(read, write)
            await session.initialize()
            pytest.fail("Connection should have failed without authentication")
        except Exception:
            # Expected to fail without authentication
            pass
        
        # Test with invalid token (should fail)
        try:
            invalid_headers = {
                "Authorization": "Bearer invalid_token_here",
                "Content-Type": "application/json"
            }
            read, write, _ = await streamablehttp_client(agentcore_url, headers=invalid_headers)
            session = ClientSession(read, write)
            await session.initialize()
            pytest.fail("Connection should have failed with invalid token")
        except Exception:
            # Expected to fail with invalid token
            pass
        
        print("✅ Authentication validation passed - unauthorized requests properly rejected")
    
    @pytest.mark.asyncio
    async def test_recommend_restaurants_tool_deployment(
        self, 
        agentcore_url: str, 
        auth_tokens: AuthenticationTokens,
        sample_reasoning_data: List[Dict[str, Any]]
    ):
        """Test recommend_restaurants tool against deployed server."""
        session = await self.create_authenticated_mcp_client(agentcore_url, auth_tokens)
        
        try:
            # Test sentiment_likes ranking method
            start_time = time.time()
            result = await session.call_tool(
                "recommend_restaurants",
                {
                    "restaurants": sample_reasoning_data,
                    "ranking_method": "sentiment_likes"
                }
            )
            execution_time = time.time() - start_time
            
            # Validate response structure
            assert result.isError is False, f"Tool execution failed: {result.content}"
            
            # Parse response content
            response_data = json.loads(result.content[0].text)
            
            # Validate response structure
            required_fields = ["candidates", "recommendation", "ranking_method", "analysis_summary"]
            for field in required_fields:
                assert field in response_data, f"Missing field in response: {field}"
            
            assert response_data["ranking_method"] == "sentiment_likes"
            assert len(response_data["candidates"]) <= 20
            assert len(response_data["candidates"]) <= len(sample_reasoning_data)
            
            # Validate recommendation is from candidates
            recommendation_id = response_data["recommendation"]["id"]
            candidate_ids = [c["id"] for c in response_data["candidates"]]
            assert recommendation_id in candidate_ids
            
            print(f"✅ recommend_restaurants (sentiment_likes) executed in {execution_time:.3f}s")
            print(f"   Candidates: {len(response_data['candidates'])}")
            print(f"   Recommendation: {response_data['recommendation']['name']}")
            
            # Test combined_sentiment ranking method
            start_time = time.time()
            result = await session.call_tool(
                "recommend_restaurants",
                {
                    "restaurants": sample_reasoning_data,
                    "ranking_method": "combined_sentiment"
                }
            )
            execution_time = time.time() - start_time
            
            assert result.isError is False, f"Tool execution failed: {result.content}"
            response_data = json.loads(result.content[0].text)
            assert response_data["ranking_method"] == "combined_sentiment"
            
            print(f"✅ recommend_restaurants (combined_sentiment) executed in {execution_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"recommend_restaurants tool test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_analyze_restaurant_sentiment_tool_deployment(
        self, 
        agentcore_url: str, 
        auth_tokens: AuthenticationTokens,
        sample_reasoning_data: List[Dict[str, Any]]
    ):
        """Test analyze_restaurant_sentiment tool against deployed server."""
        session = await self.create_authenticated_mcp_client(agentcore_url, auth_tokens)
        
        try:
            start_time = time.time()
            result = await session.call_tool(
                "analyze_restaurant_sentiment",
                {
                    "restaurants": sample_reasoning_data
                }
            )
            execution_time = time.time() - start_time
            
            # Validate response
            assert result.isError is False, f"Tool execution failed: {result.content}"
            
            # Parse response content
            response_data = json.loads(result.content[0].text)
            
            # Validate sentiment analysis response structure
            required_fields = ["sentiment_analysis", "restaurant_count"]
            for field in required_fields:
                assert field in response_data, f"Missing field in response: {field}"
            
            sentiment_analysis = response_data["sentiment_analysis"]
            required_analysis_fields = [
                "restaurant_count", "average_likes", "average_dislikes", 
                "average_neutral", "top_sentiment_score", "bottom_sentiment_score"
            ]
            for field in required_analysis_fields:
                assert field in sentiment_analysis, f"Missing analysis field: {field}"
            
            assert sentiment_analysis["restaurant_count"] == len(sample_reasoning_data)
            assert sentiment_analysis["average_likes"] > 0
            
            print(f"✅ analyze_restaurant_sentiment executed in {execution_time:.3f}s")
            print(f"   Restaurant count: {sentiment_analysis['restaurant_count']}")
            print(f"   Average likes: {sentiment_analysis['average_likes']:.1f}")
            
        except Exception as e:
            pytest.fail(f"analyze_restaurant_sentiment tool test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling_deployment(
        self, 
        agentcore_url: str, 
        auth_tokens: AuthenticationTokens
    ):
        """Test error handling in deployed server."""
        session = await self.create_authenticated_mcp_client(agentcore_url, auth_tokens)
        
        # Test with invalid restaurant data
        invalid_data = [
            {
                "id": "invalid_001",
                "name": "Invalid Restaurant",
                # Missing sentiment field
                "address": "1 Invalid Street",
                "meal_type": ["lunch"],
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
        
        try:
            result = await session.call_tool(
                "recommend_restaurants",
                {
                    "restaurants": invalid_data,
                    "ranking_method": "sentiment_likes"
                }
            )
            
            # Should return error response, not crash
            if result.isError:
                print("✅ Error handling working - invalid data properly rejected")
            else:
                # If not an error, check if response indicates validation failure
                response_data = json.loads(result.content[0].text)
                if "error" in response_data or "validation" in str(response_data).lower():
                    print("✅ Error handling working - validation error returned")
                else:
                    pytest.fail("Invalid data should have been rejected")
            
        except Exception as e:
            # Exception is also acceptable for invalid data
            print(f"✅ Error handling working - exception raised: {type(e).__name__}")
        
        # Test with empty restaurant list
        try:
            result = await session.call_tool(
                "recommend_restaurants",
                {
                    "restaurants": [],
                    "ranking_method": "sentiment_likes"
                }
            )
            
            if result.isError:
                print("✅ Empty list handling working - properly rejected")
            else:
                response_data = json.loads(result.content[0].text)
                if "error" in response_data:
                    print("✅ Empty list handling working - error returned")
                else:
                    pytest.fail("Empty list should have been rejected")
            
        except Exception:
            print("✅ Empty list handling working - exception raised")
    
    @pytest.mark.asyncio
    async def test_performance_requirements_deployment(
        self, 
        agentcore_url: str, 
        auth_tokens: AuthenticationTokens
    ):
        """Test performance requirements against deployed server."""
        session = await self.create_authenticated_mcp_client(agentcore_url, auth_tokens)
        
        # Generate larger dataset for performance testing
        large_dataset = []
        for i in range(50):  # Reasonable size for deployment testing
            restaurant = {
                "id": f"perf_{i:03d}",
                "name": f"Performance Restaurant {i}",
                "address": f"{i} Performance Street",
                "meal_type": ["lunch"],
                "sentiment": {
                    "likes": 50 + (i % 50),
                    "dislikes": 25,
                    "neutral": 25
                },
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
            large_dataset.append(restaurant)
        
        # Test performance
        start_time = time.time()
        result = await session.call_tool(
            "recommend_restaurants",
            {
                "restaurants": large_dataset,
                "ranking_method": "sentiment_likes"
            }
        )
        execution_time = time.time() - start_time
        
        # Validate response
        assert result.isError is False, f"Performance test failed: {result.content}"
        
        # Performance requirements (adjust based on your needs)
        max_execution_time = 10.0  # 10 seconds for 50 restaurants
        assert execution_time < max_execution_time, f"Performance requirement not met: {execution_time:.3f}s > {max_execution_time}s"
        
        response_data = json.loads(result.content[0].text)
        assert len(response_data["candidates"]) == 20  # Should return top 20
        
        print(f"✅ Performance test passed: {len(large_dataset)} restaurants processed in {execution_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_deployment(
        self, 
        agentcore_url: str, 
        auth_tokens: AuthenticationTokens,
        sample_reasoning_data: List[Dict[str, Any]]
    ):
        """Test concurrent request handling in deployed server."""
        # Create multiple concurrent requests
        async def make_request(session_id: int):
            session = await self.create_authenticated_mcp_client(agentcore_url, auth_tokens)
            
            start_time = time.time()
            result = await session.call_tool(
                "recommend_restaurants",
                {
                    "restaurants": sample_reasoning_data,
                    "ranking_method": "sentiment_likes"
                }
            )
            execution_time = time.time() - start_time
            
            return {
                "session_id": session_id,
                "success": not result.isError,
                "execution_time": execution_time,
                "result": result
            }
        
        # Run 5 concurrent requests
        concurrent_requests = 5
        tasks = [make_request(i) for i in range(concurrent_requests)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Validate results
        successful_requests = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Request {i} failed with exception: {result}")
            else:
                if result["success"]:
                    successful_requests += 1
                    print(f"Request {i} completed in {result['execution_time']:.3f}s")
                else:
                    print(f"Request {i} failed: {result['result'].content}")
        
        # At least 80% of requests should succeed
        success_rate = successful_requests / concurrent_requests
        assert success_rate >= 0.8, f"Concurrent request success rate too low: {success_rate:.2%}"
        
        print(f"✅ Concurrent requests test passed: {successful_requests}/{concurrent_requests} successful in {total_time:.3f}s")
    
    def test_deployment_configuration_validation(self):
        """Test that deployment configuration is valid."""
        # Check if deployment configuration files exist
        config_files = [
            "cognito_config.json",
            "deploy_reasoning_agentcore.py",
            ".bedrock_agentcore.yaml"
        ]
        
        missing_files = []
        for config_file in config_files:
            if not Path(config_file).exists():
                missing_files.append(config_file)
        
        if missing_files:
            pytest.skip(f"Deployment configuration files missing: {missing_files}")
        
        # Validate Cognito configuration
        with open("cognito_config.json", 'r') as f:
            cognito_config = json.load(f)
        
        required_cognito_fields = [
            "user_pool_id", "client_id", "region", 
            "discovery_url", "jwks_url", "issuer_url"
        ]
        
        for field in required_cognito_fields:
            assert field in cognito_config, f"Missing Cognito config field: {field}"
            assert cognito_config[field], f"Empty Cognito config field: {field}"
        
        print("✅ Deployment configuration validation passed")
    
    def test_save_deployment_test_results(
        self, 
        agentcore_url: str, 
        auth_tokens: Optional[AuthenticationTokens]
    ):
        """Save deployment test results for future reference."""
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "agentcore_url": agentcore_url,
            "authentication_successful": auth_tokens is not None,
            "test_status": "completed"
        }
        
        # Save results
        results_file = Path("tests/results/deployment_validation_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Deployment test results saved to {results_file}")


class TestReasoningDeploymentHealthCheck:
    """Health check tests for deployed reasoning server."""
    
    def test_health_endpoint_availability(self):
        """Test if health check endpoint is available (if implemented)."""
        # This would test a health endpoint if implemented
        # For now, we'll skip this test
        pytest.skip("Health endpoint not implemented yet")
    
    def test_metrics_endpoint_availability(self):
        """Test if metrics endpoint is available (if implemented)."""
        # This would test a metrics endpoint if implemented
        # For now, we'll skip this test
        pytest.skip("Metrics endpoint not implemented yet")


if __name__ == "__main__":
    # Run deployment tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])