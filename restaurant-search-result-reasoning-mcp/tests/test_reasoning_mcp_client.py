#!/usr/bin/env python3
"""
MCP Client Tests for Restaurant Reasoning Tools.

This module provides comprehensive tests for the MCP client functionality,
testing tool listing, invocation, and integration with the reasoning MCP server
using MCP ClientSession and streamable_http transport.
"""

import sys
import os
import json
import asyncio
import unittest
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.types import Tool, CallToolResult
except ImportError:
    print("Warning: MCP client dependencies not available. Some tests will be skipped.")
    ClientSession = None
    streamablehttp_client = None


class TestReasoningMCPClient(unittest.TestCase):
    """Test cases for MCP client functionality with reasoning tools."""
    
    def setUp(self):
        """Set up test data and mock configurations."""
        # Test server configuration
        self.server_url = "http://localhost:8080"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "test-mcp-client/1.0"
        }
        
        # Sample restaurant data for testing
        self.sample_restaurants = [
            {
                "id": "rest_001",
                "name": "Excellent Dim Sum",
                "address": "123 Central Street",
                "meal_type": ["breakfast", "lunch"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "location_category": "restaurant",
                "district": "Central district",
                "price_range": "$$"
            },
            {
                "id": "rest_002",
                "name": "Great Noodle House", 
                "address": "456 Admiralty Road",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {"likes": 70, "dislikes": 15, "neutral": 15},
                "location_category": "restaurant",
                "district": "Admiralty",
                "price_range": "$"
            },
            {
                "id": "rest_003",
                "name": "Amazing Seafood",
                "address": "789 Causeway Bay",
                "meal_type": ["dinner"],
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "location_category": "restaurant",
                "district": "Causeway Bay", 
                "price_range": "$$"
            }
        ]
        
        # Expected tool schemas
        self.expected_tools = [
            {
                "name": "recommend_restaurants",
                "description": "Analyze restaurant sentiment data and provide intelligent recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "restaurants": {
                            "type": "array",
                            "items": {"type": "object"}
                        },
                        "ranking_method": {
                            "type": "string",
                            "default": "sentiment_likes"
                        }
                    },
                    "required": ["restaurants"]
                }
            },
            {
                "name": "analyze_restaurant_sentiment",
                "description": "Analyze sentiment data for a list of restaurants without providing recommendations",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "restaurants": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    },
                    "required": ["restaurants"]
                }
            }
        ]
    
    @unittest.skipIf(ClientSession is None, "MCP client dependencies not available")
    async def test_mcp_client_connection(self):
        """Test MCP client connection to reasoning server."""
        with patch('mcp.client.streamable_http.streamablehttp_client') as mock_client:
            # Mock the client connection
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_client.return_value.__aenter__.return_value = (mock_read, mock_write, None)
            
            # Mock session initialization
            with patch('mcp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.initialize.return_value = None
                
                # Test connection
                async with streamablehttp_client(self.server_url, self.headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        # Verify connection was established
                        mock_session.initialize.assert_called_once()
    
    @unittest.skipIf(ClientSession is None, "MCP client dependencies not available")
    async def test_list_reasoning_tools(self):
        """Test listing available reasoning tools via MCP client."""
        with patch('mcp.client.streamable_http.streamablehttp_client') as mock_client:
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_client.return_value.__aenter__.return_value = (mock_read, mock_write, None)
            
            with patch('mcp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.initialize.return_value = None
                
                # Mock list_tools response
                mock_tools = [
                    Tool(
                        name="recommend_restaurants",
                        description="Analyze restaurant sentiment data and provide intelligent recommendations",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "restaurants": {"type": "array", "items": {"type": "object"}},
                                "ranking_method": {"type": "string", "default": "sentiment_likes"}
                            },
                            "required": ["restaurants"]
                        }
                    ),
                    Tool(
                        name="analyze_restaurant_sentiment", 
                        description="Analyze sentiment data for a list of restaurants without providing recommendations",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "restaurants": {"type": "array", "items": {"type": "object"}}
                            },
                            "required": ["restaurants"]
                        }
                    )
                ]
                mock_session.list_tools.return_value = mock_tools
                
                # Test tool listing
                async with streamablehttp_client(self.server_url, self.headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        
                        # Verify tools are available
                        self.assertEqual(len(tools), 2)
                        tool_names = [tool.name for tool in tools]
                        self.assertIn("recommend_restaurants", tool_names)
                        self.assertIn("analyze_restaurant_sentiment", tool_names)
    
    @unittest.skipIf(ClientSession is None, "MCP client dependencies not available")
    async def test_invoke_recommend_restaurants_tool(self):
        """Test invoking recommend_restaurants tool via MCP client."""
        with patch('mcp.client.streamable_http.streamablehttp_client') as mock_client:
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_client.return_value.__aenter__.return_value = (mock_read, mock_write, None)
            
            with patch('mcp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.initialize.return_value = None
                
                # Mock successful tool call response
                mock_response = CallToolResult(
                    content=[{
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "data": {
                                "recommendation": {
                                    "id": "rest_003",
                                    "name": "Amazing Seafood",
                                    "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
                                },
                                "candidates": self.sample_restaurants,
                                "ranking_method": "sentiment_likes",
                                "candidate_count": 3,
                                "analysis_summary": {
                                    "restaurant_count": 3,
                                    "average_likes": 83.33,
                                    "top_sentiment_score": 95.0
                                }
                            }
                        })
                    }]
                )
                mock_session.call_tool.return_value = mock_response
                
                # Test tool invocation
                async with streamablehttp_client(self.server_url, self.headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "recommend_restaurants",
                            {
                                "restaurants": self.sample_restaurants,
                                "ranking_method": "sentiment_likes"
                            }
                        )
                        
                        # Verify tool was called correctly
                        mock_session.call_tool.assert_called_once_with(
                            "recommend_restaurants",
                            {
                                "restaurants": self.sample_restaurants,
                                "ranking_method": "sentiment_likes"
                            }
                        )
                        
                        # Verify response structure
                        self.assertIsInstance(result, CallToolResult)
                        self.assertEqual(len(result.content), 1)
                        
                        # Parse and verify response content
                        response_text = result.content[0]["text"]
                        response_data = json.loads(response_text)
                        
                        self.assertTrue(response_data["success"])
                        self.assertIn("recommendation", response_data["data"])
                        self.assertIn("candidates", response_data["data"])
                        self.assertEqual(response_data["data"]["ranking_method"], "sentiment_likes")
    
    @unittest.skipIf(ClientSession is None, "MCP client dependencies not available")
    async def test_invoke_analyze_sentiment_tool(self):
        """Test invoking analyze_restaurant_sentiment tool via MCP client."""
        with patch('mcp.client.streamable_http.streamablehttp_client') as mock_client:
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_client.return_value.__aenter__.return_value = (mock_read, mock_write, None)
            
            with patch('mcp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.initialize.return_value = None
                
                # Mock sentiment analysis response
                mock_response = CallToolResult(
                    content=[{
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "data": {
                                "sentiment_analysis": {
                                    "restaurant_count": 3,
                                    "average_likes": 83.33,
                                    "average_dislikes": 9.33,
                                    "average_neutral": 7.33,
                                    "top_sentiment_score": 95.0,
                                    "bottom_sentiment_score": 70.0,
                                    "ranking_method": "sentiment_likes"
                                },
                                "restaurant_count": 3,
                                "ranking_method": "sentiment_likes"
                            }
                        })
                    }]
                )
                mock_session.call_tool.return_value = mock_response
                
                # Test tool invocation
                async with streamablehttp_client(self.server_url, self.headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "analyze_restaurant_sentiment",
                            {"restaurants": self.sample_restaurants}
                        )
                        
                        # Verify tool was called correctly
                        mock_session.call_tool.assert_called_once_with(
                            "analyze_restaurant_sentiment",
                            {"restaurants": self.sample_restaurants}
                        )
                        
                        # Parse and verify response
                        response_text = result.content[0]["text"]
                        response_data = json.loads(response_text)
                        
                        self.assertTrue(response_data["success"])
                        self.assertIn("sentiment_analysis", response_data["data"])
                        self.assertEqual(response_data["data"]["restaurant_count"], 3)
    
    @unittest.skipIf(ClientSession is None, "MCP client dependencies not available")
    async def test_mcp_client_error_handling(self):
        """Test MCP client error handling for invalid requests."""
        with patch('mcp.client.streamable_http.streamablehttp_client') as mock_client:
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_client.return_value.__aenter__.return_value = (mock_read, mock_write, None)
            
            with patch('mcp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.initialize.return_value = None
                
                # Mock error response
                mock_response = CallToolResult(
                    content=[{
                        "type": "text",
                        "text": json.dumps({
                            "success": False,
                            "error": {
                                "type": "ValidationError",
                                "message": "Restaurants list cannot be empty",
                                "timestamp": "2024-01-01T00:00:00Z"
                            }
                        })
                    }]
                )
                mock_session.call_tool.return_value = mock_response
                
                # Test error handling
                async with streamablehttp_client(self.server_url, self.headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "recommend_restaurants",
                            {"restaurants": [], "ranking_method": "sentiment_likes"}
                        )
                        
                        # Parse and verify error response
                        response_text = result.content[0]["text"]
                        response_data = json.loads(response_text)
                        
                        self.assertFalse(response_data["success"])
                        self.assertIn("error", response_data)
                        self.assertEqual(response_data["error"]["type"], "ValidationError")
                        self.assertIn("empty", response_data["error"]["message"])


class TestReasoningMCPClientHelpers(unittest.TestCase):
    """Helper functions for testing recommendation logic and sentiment analysis."""
    
    def setUp(self):
        """Set up helper test data."""
        self.test_restaurants = [
            {
                "id": "helper_001",
                "name": "Test Restaurant 1",
                "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5}
            },
            {
                "id": "helper_002", 
                "name": "Test Restaurant 2",
                "sentiment": {"likes": 60, "dislikes": 25, "neutral": 15}
            },
            {
                "id": "helper_003",
                "name": "Test Restaurant 3",
                "sentiment": {"likes": 90, "dislikes": 5, "neutral": 5}
            }
        ]
    
    def create_test_restaurant_data(
        self, 
        count: int = 5,
        base_likes: int = 50,
        likes_increment: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Create test restaurant data with varying sentiment scores.
        
        Args:
            count: Number of restaurants to create
            base_likes: Base number of likes for first restaurant
            likes_increment: Increment in likes for each subsequent restaurant
            
        Returns:
            List of restaurant dictionaries with sentiment data
        """
        restaurants = []
        for i in range(count):
            restaurant = {
                "id": f"test_{i:03d}",
                "name": f"Test Restaurant {i}",
                "address": f"{i} Test Street",
                "meal_type": ["lunch"],
                "sentiment": {
                    "likes": base_likes + (i * likes_increment),
                    "dislikes": 10,
                    "neutral": 5
                },
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
            restaurants.append(restaurant)
        return restaurants
    
    def validate_recommendation_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Validate the structure of a recommendation response.
        
        Args:
            response_data: Response data to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        try:
            # Check top-level structure
            if not response_data.get("success"):
                return False
            
            data = response_data.get("data", {})
            
            # Check required fields
            required_fields = ["recommendation", "candidates", "ranking_method", "analysis_summary"]
            for field in required_fields:
                if field not in data:
                    return False
            
            # Validate recommendation structure
            recommendation = data["recommendation"]
            if not isinstance(recommendation, dict) or "id" not in recommendation:
                return False
            
            # Validate candidates structure
            candidates = data["candidates"]
            if not isinstance(candidates, list) or len(candidates) == 0:
                return False
            
            # Validate ranking method
            ranking_method = data["ranking_method"]
            if ranking_method not in ["sentiment_likes", "combined_sentiment"]:
                return False
            
            # Validate analysis summary
            analysis = data["analysis_summary"]
            if not isinstance(analysis, dict) or "restaurant_count" not in analysis:
                return False
            
            return True
            
        except Exception:
            return False
    
    def validate_sentiment_analysis_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Validate the structure of a sentiment analysis response.
        
        Args:
            response_data: Response data to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        try:
            # Check top-level structure
            if not response_data.get("success"):
                return False
            
            data = response_data.get("data", {})
            
            # Check required fields
            required_fields = ["sentiment_analysis", "restaurant_count", "ranking_method"]
            for field in required_fields:
                if field not in data:
                    return False
            
            # Validate sentiment analysis structure
            analysis = data["sentiment_analysis"]
            required_analysis_fields = [
                "restaurant_count", "average_likes", "average_dislikes", 
                "average_neutral", "top_sentiment_score", "bottom_sentiment_score"
            ]
            
            for field in required_analysis_fields:
                if field not in analysis:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def calculate_expected_sentiment_scores(self, restaurants: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate expected sentiment scores for validation.
        
        Args:
            restaurants: List of restaurant data
            
        Returns:
            Dictionary with expected sentiment statistics
        """
        if not restaurants:
            return {}
        
        likes_scores = []
        combined_scores = []
        
        for restaurant in restaurants:
            sentiment = restaurant.get("sentiment", {})
            likes = sentiment.get("likes", 0)
            dislikes = sentiment.get("dislikes", 0)
            neutral = sentiment.get("neutral", 0)
            
            total = likes + dislikes + neutral
            if total > 0:
                likes_percentage = (likes / total) * 100
                combined_percentage = ((likes + neutral) / total) * 100
                
                likes_scores.append(likes_percentage)
                combined_scores.append(combined_percentage)
        
        if not likes_scores:
            return {}
        
        return {
            "average_likes_percentage": sum(likes_scores) / len(likes_scores),
            "average_combined_percentage": sum(combined_scores) / len(combined_scores),
            "top_likes_score": max(likes_scores),
            "bottom_likes_score": min(likes_scores),
            "top_combined_score": max(combined_scores),
            "bottom_combined_score": min(combined_scores)
        }
    
    def test_create_test_restaurant_data(self):
        """Test the helper function for creating test restaurant data."""
        # Test default parameters
        restaurants = self.create_test_restaurant_data()
        self.assertEqual(len(restaurants), 5)
        
        # Verify sentiment progression
        for i, restaurant in enumerate(restaurants):
            expected_likes = 50 + (i * 10)
            self.assertEqual(restaurant["sentiment"]["likes"], expected_likes)
        
        # Test custom parameters
        custom_restaurants = self.create_test_restaurant_data(count=3, base_likes=100, likes_increment=20)
        self.assertEqual(len(custom_restaurants), 3)
        self.assertEqual(custom_restaurants[0]["sentiment"]["likes"], 100)
        self.assertEqual(custom_restaurants[1]["sentiment"]["likes"], 120)
        self.assertEqual(custom_restaurants[2]["sentiment"]["likes"], 140)
    
    def test_validate_recommendation_response(self):
        """Test recommendation response validation helper."""
        # Valid response
        valid_response = {
            "success": True,
            "data": {
                "recommendation": {"id": "rest_001", "name": "Test"},
                "candidates": [{"id": "rest_001", "name": "Test"}],
                "ranking_method": "sentiment_likes",
                "analysis_summary": {"restaurant_count": 1}
            }
        }
        self.assertTrue(self.validate_recommendation_response(valid_response))
        
        # Invalid response - missing fields
        invalid_response = {
            "success": True,
            "data": {
                "recommendation": {"id": "rest_001"}
                # Missing candidates, ranking_method, analysis_summary
            }
        }
        self.assertFalse(self.validate_recommendation_response(invalid_response))
        
        # Error response
        error_response = {"success": False, "error": {"message": "Test error"}}
        self.assertFalse(self.validate_recommendation_response(error_response))
    
    def test_validate_sentiment_analysis_response(self):
        """Test sentiment analysis response validation helper."""
        # Valid response
        valid_response = {
            "success": True,
            "data": {
                "sentiment_analysis": {
                    "restaurant_count": 3,
                    "average_likes": 80.0,
                    "average_dislikes": 10.0,
                    "average_neutral": 10.0,
                    "top_sentiment_score": 90.0,
                    "bottom_sentiment_score": 70.0
                },
                "restaurant_count": 3,
                "ranking_method": "sentiment_likes"
            }
        }
        self.assertTrue(self.validate_sentiment_analysis_response(valid_response))
        
        # Invalid response - missing analysis fields
        invalid_response = {
            "success": True,
            "data": {
                "sentiment_analysis": {"restaurant_count": 3},  # Missing other fields
                "restaurant_count": 3,
                "ranking_method": "sentiment_likes"
            }
        }
        self.assertFalse(self.validate_sentiment_analysis_response(invalid_response))
    
    def test_calculate_expected_sentiment_scores(self):
        """Test sentiment score calculation helper."""
        scores = self.calculate_expected_sentiment_scores(self.test_restaurants)
        
        # Verify calculations
        self.assertIn("average_likes_percentage", scores)
        self.assertIn("top_likes_score", scores)
        self.assertIn("bottom_likes_score", scores)
        
        # Test with empty list
        empty_scores = self.calculate_expected_sentiment_scores([])
        self.assertEqual(empty_scores, {})


class TestMCPClientIntegration(unittest.TestCase):
    """Integration tests for MCP client with reasoning server."""
    
    def setUp(self):
        """Set up integration test data."""
        self.helper = TestReasoningMCPClientHelpers()
        self.helper.setUp()
    
    @unittest.skipIf(ClientSession is None, "MCP client dependencies not available")
    async def test_end_to_end_recommendation_workflow(self):
        """Test complete recommendation workflow via MCP client."""
        # Create test data
        test_restaurants = self.helper.create_test_restaurant_data(count=10)
        
        with patch('mcp.client.streamable_http.streamablehttp_client') as mock_client:
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_client.return_value.__aenter__.return_value = (mock_read, mock_write, None)
            
            with patch('mcp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                mock_session.initialize.return_value = None
                
                # Mock successful workflow
                mock_response = CallToolResult(
                    content=[{
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "data": {
                                "recommendation": test_restaurants[0],
                                "candidates": test_restaurants,
                                "ranking_method": "sentiment_likes",
                                "analysis_summary": {"restaurant_count": 10}
                            }
                        })
                    }]
                )
                mock_session.call_tool.return_value = mock_response
                
                # Test workflow
                async with streamablehttp_client("http://localhost:8080") as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        # Call recommendation tool
                        result = await session.call_tool(
                            "recommend_restaurants",
                            {
                                "restaurants": test_restaurants,
                                "ranking_method": "sentiment_likes"
                            }
                        )
                        
                        # Validate response
                        response_text = result.content[0]["text"]
                        response_data = json.loads(response_text)
                        
                        self.assertTrue(self.helper.validate_recommendation_response(response_data))


def run_async_test(coro):
    """Helper function to run async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def run_mcp_client_tests():
    """Run all MCP client tests and display results."""
    print("Running Restaurant Reasoning MCP Client Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(loader.loadTestsFromTestCase(TestReasoningMCPClientHelpers))
    
    # Add async tests if MCP is available
    if ClientSession is not None:
        # Convert async tests to sync for unittest
        class AsyncTestWrapper(unittest.TestCase):
            def test_mcp_client_connection(self):
                test_instance = TestReasoningMCPClient()
                test_instance.setUp()
                run_async_test(test_instance.test_mcp_client_connection())
            
            def test_list_reasoning_tools(self):
                test_instance = TestReasoningMCPClient()
                test_instance.setUp()
                run_async_test(test_instance.test_list_reasoning_tools())
            
            def test_invoke_recommend_restaurants_tool(self):
                test_instance = TestReasoningMCPClient()
                test_instance.setUp()
                run_async_test(test_instance.test_invoke_recommend_restaurants_tool())
            
            def test_invoke_analyze_sentiment_tool(self):
                test_instance = TestReasoningMCPClient()
                test_instance.setUp()
                run_async_test(test_instance.test_invoke_analyze_sentiment_tool())
            
            def test_mcp_client_error_handling(self):
                test_instance = TestReasoningMCPClient()
                test_instance.setUp()
                run_async_test(test_instance.test_mcp_client_error_handling())
            
            def test_end_to_end_recommendation_workflow(self):
                test_instance = TestMCPClientIntegration()
                test_instance.setUp()
                run_async_test(test_instance.test_end_to_end_recommendation_workflow())
        
        test_suite.addTest(loader.loadTestsFromTestCase(AsyncTestWrapper))
    else:
        print("Warning: MCP client dependencies not available. Skipping async tests.")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success


if __name__ == "__main__":
    success = run_mcp_client_tests()
    sys.exit(0 if success else 1)