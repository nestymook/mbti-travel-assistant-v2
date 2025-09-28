"""
Tests for MCP Client Manager

This module contains unit tests for the MCP client manager, including
connection management, retry logic, and MCP tool calls.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.mcp_client_manager import (
    MCPClientManager,
    MCPConnectionError,
    MCPToolCallError,
    MCPConnectionConfig,
    MCPConnectionStats
)
from models.restaurant_models import Restaurant, Sentiment


class TestMCPClientManager:
    """Test cases for MCP Client Manager"""
    
    @pytest.fixture
    def mcp_manager(self):
        """Create MCP client manager for testing"""
        with patch('services.mcp_client_manager.settings') as mock_settings:
            mock_settings.mcp_client.search_mcp_endpoint = "http://test-search-mcp:8000"
            mock_settings.mcp_client.reasoning_mcp_endpoint = "http://test-reasoning-mcp:8000"
            mock_settings.mcp_client.mcp_connection_timeout = 30
            mock_settings.mcp_client.mcp_retry_attempts = 3
            
            return MCPClientManager()
    
    @pytest.fixture
    def sample_restaurant(self):
        """Create sample restaurant for testing"""
        return Restaurant(
            id="test_001",
            name="Test Restaurant",
            address="123 Test Street",
            district="Test District",
            meal_type=["lunch", "dinner"],
            sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
            price_range="$$",
            operating_hours={"monday": ["11:00", "22:00"]},
            location_category="urban"
        )
    
    def test_mcp_manager_initialization(self, mcp_manager):
        """Test MCP client manager initialization"""
        assert mcp_manager.search_config.endpoint == "http://test-search-mcp:8000"
        assert mcp_manager.reasoning_config.endpoint == "http://test-reasoning-mcp:8000"
        assert mcp_manager.search_config.timeout == 30
        assert mcp_manager.search_config.retry_attempts == 3
    
    @pytest.mark.asyncio
    async def test_search_restaurants_success(self, mcp_manager):
        """Test successful restaurant search MCP call"""
        # Mock MCP session and response
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.isError = False
        mock_result.content = [MagicMock(text=json.dumps({
            "success": True,
            "data": {
                "restaurants": [{
                    "id": "test_001",
                    "name": "Test Restaurant",
                    "address": "123 Test Street",
                    "district": "Test District",
                    "meal_type": ["lunch"],
                    "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                    "price_range": "$$",
                    "operating_hours": {"monday": ["11:00", "22:00"]},
                    "location_category": "urban"
                }]
            }
        }))]
        
        mock_session.call_tool.return_value = mock_result
        
        with patch.object(mcp_manager, '_get_mcp_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            restaurants = await mcp_manager.search_restaurants(
                district="Test District",
                meal_type="lunch"
            )
            
            assert len(restaurants) == 1
            assert restaurants[0].name == "Test Restaurant"
            assert restaurants[0].district == "Test District"
            
            # Verify MCP tool was called with correct parameters
            mock_session.call_tool.assert_called_once_with(
                "search_restaurants_combined",
                {"districts": ["Test District"], "meal_types": ["lunch"]}
            )
    
    @pytest.mark.asyncio
    async def test_analyze_restaurants_success(self, mcp_manager, sample_restaurant):
        """Test successful restaurant analysis MCP call"""
        # Mock MCP session and response
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.isError = False
        mock_result.content = [MagicMock(text=json.dumps({
            "success": True,
            "data": {
                "recommendation": {
                    "id": "test_001",
                    "name": "Test Restaurant",
                    "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                },
                "candidates": [{
                    "id": "test_001",
                    "name": "Test Restaurant",
                    "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                }],
                "ranking_method": "sentiment_likes",
                "analysis_summary": {"total_restaurants": 1}
            }
        }))]
        
        mock_session.call_tool.return_value = mock_result
        
        with patch.object(mcp_manager, '_get_mcp_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            result = await mcp_manager.analyze_restaurants([sample_restaurant])
            
            assert result["recommendation"]["id"] == "test_001"
            assert len(result["candidates"]) == 1
            assert result["ranking_method"] == "sentiment_likes"
            
            # Verify MCP tool was called with correct parameters
            expected_params = {
                "restaurants": [mcp_manager._restaurant_to_dict(sample_restaurant)],
                "ranking_method": "sentiment_likes"
            }
            mock_session.call_tool.assert_called_once_with(
                "recommend_restaurants",
                expected_params
            )
    
    @pytest.mark.asyncio
    async def test_search_restaurants_mcp_error(self, mcp_manager):
        """Test handling of MCP tool error in search"""
        # Mock MCP session with error response
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.isError = False
        mock_result.content = [MagicMock(text=json.dumps({
            "success": False,
            "error": {"message": "District not found"}
        }))]
        
        mock_session.call_tool.return_value = mock_result
        
        with patch.object(mcp_manager, '_get_mcp_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            with pytest.raises(MCPToolCallError) as exc_info:
                await mcp_manager.search_restaurants(district="Invalid District")
            
            assert "Search MCP tool failed" in str(exc_info.value)
            assert "District not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connection_retry_logic(self, mcp_manager):
        """Test retry logic for failed connections"""
        # Mock connection that fails twice then succeeds
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        config = MCPConnectionConfig(endpoint="test", retry_attempts=3)
        stats = MCPConnectionStats()
        
        result = await mcp_manager._execute_with_retry(
            mock_operation,
            config,
            stats,
            "test-server",
            "test-operation"
        )
        
        assert result == "success"
        assert call_count == 3
        assert stats.total_calls == 3
        assert stats.successful_calls == 1
        assert stats.failed_calls == 2
    
    @pytest.mark.asyncio
    async def test_connection_retry_exhausted(self, mcp_manager):
        """Test retry logic when all attempts fail"""
        async def mock_operation():
            raise ConnectionError("Connection failed")
        
        config = MCPConnectionConfig(endpoint="test", retry_attempts=2)
        stats = MCPConnectionStats()
        
        with pytest.raises(MCPConnectionError) as exc_info:
            await mcp_manager._execute_with_retry(
                mock_operation,
                config,
                stats,
                "test-server",
                "test-operation"
            )
        
        assert "Failed test-operation after 2 attempts" in str(exc_info.value)
        assert stats.total_calls == 2
        assert stats.successful_calls == 0
        assert stats.failed_calls == 2
    
    def test_restaurant_to_dict_conversion(self, mcp_manager, sample_restaurant):
        """Test conversion of Restaurant object to dictionary"""
        result = mcp_manager._restaurant_to_dict(sample_restaurant)
        
        assert result["id"] == "test_001"
        assert result["name"] == "Test Restaurant"
        assert result["district"] == "Test District"
        assert result["sentiment"]["likes"] == 85
        assert result["sentiment"]["dislikes"] == 10
        assert result["sentiment"]["neutral"] == 5
        assert result["price_range"] == "$$"
    
    def test_dict_to_restaurant_conversion(self, mcp_manager):
        """Test conversion of dictionary to Restaurant object"""
        data = {
            "id": "test_001",
            "name": "Test Restaurant",
            "address": "123 Test Street",
            "district": "Test District",
            "meal_type": ["lunch"],
            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
            "price_range": "$$",
            "operating_hours": {"monday": ["11:00", "22:00"]},
            "location_category": "urban"
        }
        
        restaurant = mcp_manager._dict_to_restaurant(data)
        
        assert restaurant.id == "test_001"
        assert restaurant.name == "Test Restaurant"
        assert restaurant.district == "Test District"
        assert restaurant.sentiment.likes == 85
        assert restaurant.sentiment.dislikes == 10
        assert restaurant.sentiment.neutral == 5
    
    @pytest.mark.asyncio
    async def test_health_check(self, mcp_manager):
        """Test health check functionality"""
        # Mock successful health checks
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = [MagicMock(), MagicMock()]
        
        with patch.object(mcp_manager, '_get_mcp_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            health_status = await mcp_manager.health_check()
            
            assert health_status["search_mcp"]["status"] == "healthy"
            assert health_status["reasoning_mcp"]["status"] == "healthy"
            assert health_status["search_mcp"]["tools_count"] == 2
            assert health_status["reasoning_mcp"]["tools_count"] == 2
    
    def test_get_connection_stats(self, mcp_manager):
        """Test connection statistics retrieval"""
        # Set some test statistics
        mcp_manager.search_stats.total_calls = 10
        mcp_manager.search_stats.successful_calls = 8
        mcp_manager.search_stats.failed_calls = 2
        mcp_manager.search_stats.average_response_time = 1.5
        
        stats = mcp_manager.get_connection_stats()
        
        assert stats["search_mcp"]["total_calls"] == 10
        assert stats["search_mcp"]["successful_calls"] == 8
        assert stats["search_mcp"]["failed_calls"] == 2
        assert stats["search_mcp"]["success_rate"] == 0.8
        assert stats["search_mcp"]["average_response_time"] == 1.5


if __name__ == "__main__":
    pytest.main([__file__])