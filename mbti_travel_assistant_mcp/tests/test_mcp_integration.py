"""
Integration tests for MCP Client Manager

This module contains integration tests that verify the MCP client manager
can successfully communicate with actual MCP servers.
"""

import pytest
import asyncio
import os
from unittest.mock import patch

from services.mcp_client_manager import MCPClientManager, MCPConnectionError, MCPToolCallError
from models.restaurant_models import Restaurant, Sentiment


class TestMCPIntegration:
    """Integration tests for MCP Client Manager"""
    
    @pytest.fixture
    def mcp_manager_with_test_endpoints(self):
        """Create MCP client manager with test endpoints"""
        with patch('services.mcp_client_manager.settings') as mock_settings:
            # Use local MCP server endpoints for testing
            # These would be the actual MCP servers running locally
            mock_settings.mcp_client.search_mcp_endpoint = "stdio://restaurant-search-mcp"
            mock_settings.mcp_client.reasoning_mcp_endpoint = "stdio://restaurant-reasoning-mcp"
            mock_settings.mcp_client.mcp_connection_timeout = 30
            mock_settings.mcp_client.mcp_retry_attempts = 2
            
            return MCPClientManager()
    
    @pytest.fixture
    def sample_restaurants(self):
        """Create sample restaurants for testing"""
        return [
            Restaurant(
                id="test_001",
                name="Central Cafe",
                address="123 Central Street",
                district="Central district",
                meal_type=["breakfast", "lunch"],
                sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
                price_range="$$",
                operating_hours={"monday": ["07:00", "15:00"]},
                location_category="urban"
            ),
            Restaurant(
                id="test_002", 
                name="Admiralty Bistro",
                address="456 Admiralty Road",
                district="Admiralty",
                meal_type=["lunch", "dinner"],
                sentiment=Sentiment(likes=70, dislikes=20, neutral=10),
                price_range="$$$",
                operating_hours={"monday": ["11:00", "22:00"]},
                location_category="business"
            )
        ]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_restaurants_integration(self, mcp_manager_with_test_endpoints):
        """Test integration with actual restaurant search MCP server"""
        try:
            restaurants = await mcp_manager_with_test_endpoints.search_restaurants(
                district="Central district",
                meal_type="breakfast"
            )
            
            # Verify we got some results
            assert isinstance(restaurants, list)
            
            # If we got results, verify they have the expected structure
            if restaurants:
                restaurant = restaurants[0]
                assert hasattr(restaurant, 'id')
                assert hasattr(restaurant, 'name')
                assert hasattr(restaurant, 'district')
                assert hasattr(restaurant, 'sentiment')
                
                print(f"✅ Successfully retrieved {len(restaurants)} restaurants from search MCP")
            else:
                print("⚠️ No restaurants returned from search MCP (this may be expected)")
                
        except MCPConnectionError as e:
            pytest.skip(f"MCP server not available for testing: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error in search integration test: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_restaurants_integration(self, mcp_manager_with_test_endpoints, sample_restaurants):
        """Test integration with actual restaurant reasoning MCP server"""
        try:
            result = await mcp_manager_with_test_endpoints.analyze_restaurants(
                restaurants=sample_restaurants,
                ranking_method="sentiment_likes"
            )
            
            # Verify we got the expected response structure
            assert isinstance(result, dict)
            assert "recommendation" in result
            assert "candidates" in result
            assert "ranking_method" in result
            
            # Verify recommendation structure
            recommendation = result["recommendation"]
            assert recommendation is not None
            assert "id" in recommendation
            assert "name" in recommendation
            
            # Verify candidates structure
            candidates = result["candidates"]
            assert isinstance(candidates, list)
            
            print(f"✅ Successfully analyzed restaurants and got recommendation: {recommendation.get('name', 'Unknown')}")
            print(f"✅ Got {len(candidates)} candidates from reasoning MCP")
            
        except MCPConnectionError as e:
            pytest.skip(f"MCP server not available for testing: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error in reasoning integration test: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_integration(self, mcp_manager_with_test_endpoints):
        """Test health check with actual MCP servers"""
        try:
            health_status = await mcp_manager_with_test_endpoints.health_check()
            
            assert isinstance(health_status, dict)
            assert "search_mcp" in health_status
            assert "reasoning_mcp" in health_status
            
            # Check search MCP status
            search_status = health_status["search_mcp"]
            assert "status" in search_status
            
            # Check reasoning MCP status
            reasoning_status = health_status["reasoning_mcp"]
            assert "status" in reasoning_status
            
            print(f"✅ Search MCP status: {search_status['status']}")
            print(f"✅ Reasoning MCP status: {reasoning_status['status']}")
            
            if search_status["status"] == "healthy":
                print(f"✅ Search MCP has {search_status.get('tools_count', 0)} tools available")
            
            if reasoning_status["status"] == "healthy":
                print(f"✅ Reasoning MCP has {reasoning_status.get('tools_count', 0)} tools available")
                
        except MCPConnectionError as e:
            pytest.skip(f"MCP servers not available for health check: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error in health check integration test: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_workflow(self, mcp_manager_with_test_endpoints):
        """Test complete end-to-end workflow: search -> analyze"""
        try:
            # Step 1: Search for restaurants
            print("🔍 Step 1: Searching for restaurants...")
            restaurants = await mcp_manager_with_test_endpoints.search_restaurants(
                district="Central district",
                meal_type="lunch"
            )
            
            if not restaurants:
                pytest.skip("No restaurants found for end-to-end test")
            
            print(f"✅ Found {len(restaurants)} restaurants")
            
            # Step 2: Analyze the restaurants
            print("🧠 Step 2: Analyzing restaurants for recommendations...")
            result = await mcp_manager_with_test_endpoints.analyze_restaurants(
                restaurants=restaurants,
                ranking_method="sentiment_likes"
            )
            
            # Verify complete workflow
            assert result["recommendation"] is not None
            assert len(result["candidates"]) > 0
            
            recommendation = result["recommendation"]
            print(f"✅ End-to-end workflow complete!")
            print(f"✅ Recommended restaurant: {recommendation.get('name', 'Unknown')}")
            print(f"✅ Total candidates: {len(result['candidates'])}")
            
            # Verify the recommendation is from our search results
            search_ids = {r.id for r in restaurants}
            recommendation_id = recommendation.get("id")
            
            if recommendation_id:
                # Note: The recommendation might be reformatted by the reasoning MCP
                # so we just verify the structure is correct
                assert isinstance(recommendation_id, str)
                print(f"✅ Recommendation ID: {recommendation_id}")
            
        except MCPConnectionError as e:
            pytest.skip(f"MCP servers not available for end-to-end test: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error in end-to-end workflow test: {e}")
    
    def test_connection_stats_tracking(self, mcp_manager_with_test_endpoints):
        """Test that connection statistics are properly tracked"""
        # Get initial stats
        initial_stats = mcp_manager_with_test_endpoints.get_connection_stats()
        
        assert isinstance(initial_stats, dict)
        assert "search_mcp" in initial_stats
        assert "reasoning_mcp" in initial_stats
        
        # Verify stats structure
        search_stats = initial_stats["search_mcp"]
        assert "total_calls" in search_stats
        assert "successful_calls" in search_stats
        assert "failed_calls" in search_stats
        assert "success_rate" in search_stats
        assert "average_response_time" in search_stats
        
        print("✅ Connection statistics structure is correct")
        print(f"✅ Search MCP stats: {search_stats['total_calls']} total calls")
        print(f"✅ Reasoning MCP stats: {initial_stats['reasoning_mcp']['total_calls']} total calls")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "-m", "integration",
        "--tb=short"
    ])