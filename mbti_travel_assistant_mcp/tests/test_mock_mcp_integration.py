"""
Integration Tests with Mock MCP Servers

Tests end-to-end functionality using mock MCP servers to simulate
the complete workflow without requiring actual MCP server instances.
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from contextlib import asynccontextmanager

from services.mcp_client_manager import MCPClientManager
from services.restaurant_agent import RestaurantAgent
from models.restaurant_models import Restaurant, Sentiment


class MockMCPSession:
    """Mock MCP session for testing."""
    
    def __init__(self, tools_responses=None):
        self.tools_responses = tools_responses or {}
        self.initialized = False
    
    async def initialize(self):
        """Mock session initialization."""
        self.initialized = True
    
    async def list_tools(self):
        """Mock list tools."""
        return [
            Mock(name="search_restaurants_combined"),
            Mock(name="recommend_restaurants")
        ]
    
    async def call_tool(self, tool_name, parameters):
        """Mock tool call."""
        if tool_name in self.tools_responses:
            response_data = self.tools_responses[tool_name]
            
            # Create mock result
            mock_result = Mock()
            mock_result.isError = False
            mock_result.content = [Mock(text=json.dumps(response_data))]
            
            return mock_result
        else:
            # Return empty result for unknown tools
            mock_result = Mock()
            mock_result.isError = False
            mock_result.content = [Mock(text=json.dumps({"success": False, "error": "Tool not found"}))]
            return mock_result


class MockMCPClient:
    """Mock MCP client for testing."""
    
    def __init__(self, endpoint, tools_responses=None):
        self.endpoint = endpoint
        self.tools_responses = tools_responses or {}
    
    @asynccontextmanager
    async def connect(self):
        """Mock connection context manager."""
        # Simulate connection
        read_stream = Mock()
        write_stream = Mock()
        connection_info = Mock()
        
        yield read_stream, write_stream, connection_info


class TestMockMCPIntegration:
    """Integration tests using mock MCP servers."""
    
    @pytest.fixture
    def mock_search_responses(self):
        """Mock responses for search MCP server."""
        return {
            "search_restaurants_combined": {
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Central Breakfast Cafe",
                            "address": "123 Central Street",
                            "district": "Central district",
                            "meal_type": ["breakfast"],
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                            "price_range": "$",
                            "operating_hours": {"Monday": ["07:00", "11:30"]},
                            "location_category": "Shopping Mall"
                        },
                        {
                            "id": "rest_002",
                            "name": "Morning Delights",
                            "address": "456 Central Avenue",
                            "district": "Central district",
                            "meal_type": ["breakfast"],
                            "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},
                            "price_range": "$$",
                            "operating_hours": {"Monday": ["06:30", "12:00"]},
                            "location_category": "Street Food"
                        }
                    ],
                    "total_count": 2,
                    "search_criteria": {
                        "districts": ["Central district"],
                        "meal_types": ["breakfast"]
                    }
                }
            }
        }
    
    @pytest.fixture
    def mock_reasoning_responses(self):
        """Mock responses for reasoning MCP server."""
        return {
            "recommend_restaurants": {
                "success": True,
                "data": {
                    "recommendation": {
                        "id": "rest_001",
                        "name": "Central Breakfast Cafe",
                        "address": "123 Central Street",
                        "district": "Central district",
                        "meal_type": ["breakfast"],
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                        "price_range": "$",
                        "operating_hours": {"Monday": ["07:00", "11:30"]},
                        "location_category": "Shopping Mall"
                    },
                    "candidates": [
                        {
                            "id": "rest_002",
                            "name": "Morning Delights",
                            "address": "456 Central Avenue",
                            "district": "Central district",
                            "meal_type": ["breakfast"],
                            "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},
                            "price_range": "$$",
                            "operating_hours": {"Monday": ["06:30", "12:00"]},
                            "location_category": "Street Food"
                        }
                    ],
                    "ranking_method": "sentiment_likes",
                    "analysis_summary": {
                        "total_restaurants": 2,
                        "average_sentiment": 80.0,
                        "top_sentiment_score": 85
                    }
                }
            }
        }
    
    @pytest.fixture
    def mock_mcp_client_manager(self, mock_search_responses, mock_reasoning_responses):
        """Create mock MCP client manager with configured responses."""
        with patch('services.mcp_client_manager.settings') as mock_settings:
            mock_settings.mcp_client.search_mcp_endpoint = "mock://search-mcp"
            mock_settings.mcp_client.reasoning_mcp_endpoint = "mock://reasoning-mcp"
            mock_settings.mcp_client.mcp_connection_timeout = 30
            mock_settings.mcp_client.mcp_retry_attempts = 3
            
            manager = MCPClientManager()
            
            # Mock the _get_mcp_session method to return our mock session
            async def mock_get_session(endpoint):
                if "search" in endpoint:
                    return MockMCPSession(mock_search_responses)
                elif "reasoning" in endpoint:
                    return MockMCPSession(mock_reasoning_responses)
                else:
                    return MockMCPSession()
            
            manager._get_mcp_session = mock_get_session
            
            return manager
    
    @pytest.mark.asyncio
    async def test_end_to_end_mock_mcp_workflow(self, mock_mcp_client_manager):
        """Test complete end-to-end workflow with mock MCP servers."""
        # Step 1: Search for restaurants
        restaurants = await mock_mcp_client_manager.search_restaurants(
            district="Central district",
            meal_time="breakfast"
        )
        
        # Verify search results
        assert len(restaurants) == 2
        assert restaurants[0].id == "rest_001"
        assert restaurants[0].name == "Central Breakfast Cafe"
        assert restaurants[0].district == "Central district"
        assert restaurants[0].sentiment.likes == 85
        
        assert restaurants[1].id == "rest_002"
        assert restaurants[1].name == "Morning Delights"
        
        # Step 2: Analyze restaurants for recommendations
        reasoning_result = await mock_mcp_client_manager.analyze_restaurants(
            restaurants=restaurants,
            ranking_method="sentiment_likes"
        )
        
        # Verify reasoning results
        assert "recommendation" in reasoning_result
        assert "candidates" in reasoning_result
        assert "ranking_method" in reasoning_result
        assert "analysis_summary" in reasoning_result
        
        # Verify recommendation
        recommendation = reasoning_result["recommendation"]
        assert recommendation["id"] == "rest_001"
        assert recommendation["name"] == "Central Breakfast Cafe"
        
        # Verify candidates
        candidates = reasoning_result["candidates"]
        assert len(candidates) == 1
        assert candidates[0]["id"] == "rest_002"
        assert candidates[0]["name"] == "Morning Delights"
        
        # Verify analysis summary
        analysis = reasoning_result["analysis_summary"]
        assert analysis["total_restaurants"] == 2
        assert analysis["average_sentiment"] == 80.0
    
    @pytest.mark.asyncio
    async def test_restaurant_agent_with_mock_mcp(self, mock_search_responses, mock_reasoning_responses):
        """Test restaurant agent integration with mock MCP servers."""
        with patch('services.restaurant_agent.MCPClientManager') as mock_mcp_class:
            # Create mock MCP client manager
            mock_mcp_manager = Mock()
            mock_mcp_class.return_value = mock_mcp_manager
            
            # Mock search restaurants
            search_restaurants = [
                Restaurant(
                    id="rest_001",
                    name="Central Breakfast Cafe",
                    address="123 Central Street",
                    district="Central district",
                    meal_type=["breakfast"],
                    sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
                    price_range="$",
                    operating_hours={"Monday": ["07:00", "11:30"]},
                    location_category="Shopping Mall"
                ),
                Restaurant(
                    id="rest_002",
                    name="Morning Delights",
                    address="456 Central Avenue",
                    district="Central district",
                    meal_type=["breakfast"],
                    sentiment=Sentiment(likes=75, dislikes=15, neutral=10),
                    price_range="$$",
                    operating_hours={"Monday": ["06:30", "12:00"]},
                    location_category="Street Food"
                )
            ]
            
            mock_mcp_manager.search_restaurants = AsyncMock(return_value=search_restaurants)
            mock_mcp_manager.analyze_restaurants = AsyncMock(
                return_value=mock_reasoning_responses["recommend_restaurants"]["data"]
            )
            
            # Create restaurant agent
            with patch('services.restaurant_agent.settings') as mock_settings:
                mock_settings.agentcore.agent_model = "amazon.nova-pro-v1:0:300k"
                mock_settings.agentcore.agent_temperature = 0.1
                mock_settings.agentcore.agent_max_tokens = 4096
                
                agent = RestaurantAgent()
                agent.mcp_client_manager = mock_mcp_manager
                
                # Mock agent response formatting
                mock_agent_response = Mock()
                mock_agent_response.content = json.dumps({
                    "recommendation": mock_reasoning_responses["recommend_restaurants"]["data"]["recommendation"],
                    "candidates": mock_reasoning_responses["recommend_restaurants"]["data"]["candidates"],
                    "metadata": {
                        "search_criteria": {"district": "Central district", "meal_time": "breakfast"},
                        "total_found": 2,
                        "timestamp": datetime.utcnow().isoformat(),
                        "processing_time_ms": 250.0,
                        "mcp_calls": ["search", "reasoning"]
                    }
                })
                
                agent.agent.process = AsyncMock(return_value=mock_agent_response)
                
                # Mock validation and enhancement
                with patch.object(agent, '_validate_and_enhance_response') as mock_validate:
                    mock_validate.return_value = json.loads(mock_agent_response.content)
                    
                    # Process request
                    result = await agent.process_request(
                        district="Central district",
                        meal_time="breakfast",
                        correlation_id="test-integration-123"
                    )
                    
                    # Verify result structure
                    assert "recommendation" in result
                    assert "candidates" in result
                    assert "metadata" in result
                    
                    # Verify recommendation
                    assert result["recommendation"]["id"] == "rest_001"
                    assert result["recommendation"]["name"] == "Central Breakfast Cafe"
                    
                    # Verify candidates
                    assert len(result["candidates"]) == 1
                    assert result["candidates"][0]["id"] == "rest_002"
                    
                    # Verify MCP calls were made
                    mock_mcp_manager.search_restaurants.assert_called_once_with(
                        district="Central district",
                        meal_time="breakfast"
                    )
                    mock_mcp_manager.analyze_restaurants.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mock_mcp_error_handling(self):
        """Test error handling with mock MCP servers."""
        with patch('services.mcp_client_manager.settings') as mock_settings:
            mock_settings.mcp_client.search_mcp_endpoint = "mock://search-mcp"
            mock_settings.mcp_client.reasoning_mcp_endpoint = "mock://reasoning-mcp"
            mock_settings.mcp_client.mcp_connection_timeout = 30
            mock_settings.mcp_client.mcp_retry_attempts = 2
            
            manager = MCPClientManager()
            
            # Mock session that returns error
            error_responses = {
                "search_restaurants_combined": {
                    "success": False,
                    "error": {
                        "message": "District not found",
                        "code": "DISTRICT_NOT_FOUND"
                    }
                }
            }
            
            async def mock_get_error_session(endpoint):
                return MockMCPSession(error_responses)
            
            manager._get_mcp_session = mock_get_error_session
            
            # Test search error handling
            with pytest.raises(Exception) as exc_info:
                await manager.search_restaurants(
                    district="Nonexistent District",
                    meal_time="breakfast"
                )
            
            assert "Search MCP tool failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_mock_mcp_health_check(self, mock_mcp_client_manager):
        """Test health check with mock MCP servers."""
        health_status = await mock_mcp_client_manager.health_check()
        
        # Verify health check structure
        assert isinstance(health_status, dict)
        assert "search_mcp" in health_status
        assert "reasoning_mcp" in health_status
        
        # Verify search MCP health
        search_health = health_status["search_mcp"]
        assert search_health["status"] == "healthy"
        assert search_health["tools_count"] == 2
        assert "response_time_ms" in search_health
        
        # Verify reasoning MCP health
        reasoning_health = health_status["reasoning_mcp"]
        assert reasoning_health["status"] == "healthy"
        assert reasoning_health["tools_count"] == 2
        assert "response_time_ms" in reasoning_health
    
    @pytest.mark.asyncio
    async def test_mock_mcp_connection_stats(self, mock_mcp_client_manager):
        """Test connection statistics tracking with mock MCP servers."""
        # Perform some operations to generate stats
        await mock_mcp_client_manager.search_restaurants(
            district="Central district",
            meal_time="breakfast"
        )
        
        restaurants = [
            Restaurant(
                id="rest_001",
                name="Test Restaurant",
                address="123 Test St",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
                price_range="$",
                operating_hours={"Monday": ["07:00", "11:30"]},
                location_category="Shopping Mall"
            )
        ]
        
        await mock_mcp_client_manager.analyze_restaurants(
            restaurants=restaurants,
            ranking_method="sentiment_likes"
        )
        
        # Get connection stats
        stats = mock_mcp_client_manager.get_connection_stats()
        
        # Verify stats structure
        assert isinstance(stats, dict)
        assert "search_mcp" in stats
        assert "reasoning_mcp" in stats
        
        # Verify search MCP stats
        search_stats = stats["search_mcp"]
        assert search_stats["total_calls"] >= 1
        assert search_stats["successful_calls"] >= 1
        assert search_stats["failed_calls"] >= 0
        assert "success_rate" in search_stats
        assert "average_response_time" in search_stats
        
        # Verify reasoning MCP stats
        reasoning_stats = stats["reasoning_mcp"]
        assert reasoning_stats["total_calls"] >= 1
        assert reasoning_stats["successful_calls"] >= 1
        assert reasoning_stats["failed_calls"] >= 0
    
    def test_mock_mcp_session_initialization(self):
        """Test mock MCP session initialization."""
        session = MockMCPSession()
        
        # Initially not initialized
        assert session.initialized is False
        
        # After initialization
        asyncio.run(session.initialize())
        assert session.initialized is True
    
    @pytest.mark.asyncio
    async def test_mock_mcp_session_tool_calls(self):
        """Test mock MCP session tool calls."""
        responses = {
            "test_tool": {
                "success": True,
                "data": {"result": "test_result"}
            }
        }
        
        session = MockMCPSession(responses)
        await session.initialize()
        
        # Test successful tool call
        result = await session.call_tool("test_tool", {"param": "value"})
        
        assert result.isError is False
        assert len(result.content) == 1
        
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is True
        assert response_data["data"]["result"] == "test_result"
        
        # Test unknown tool call
        result = await session.call_tool("unknown_tool", {})
        
        assert result.isError is False
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is False
    
    @pytest.mark.asyncio
    async def test_mock_mcp_session_list_tools(self):
        """Test mock MCP session list tools."""
        session = MockMCPSession()
        await session.initialize()
        
        tools = await session.list_tools()
        
        assert len(tools) == 2
        assert tools[0].name == "search_restaurants_combined"
        assert tools[1].name == "recommend_restaurants"
    
    @pytest.mark.asyncio
    async def test_concurrent_mock_mcp_calls(self, mock_mcp_client_manager):
        """Test concurrent calls to mock MCP servers."""
        # Create multiple concurrent search requests
        search_tasks = []
        for i in range(5):
            task = mock_mcp_client_manager.search_restaurants(
                district=f"District_{i}",
                meal_time="breakfast"
            )
            search_tasks.append(task)
        
        # Execute all searches concurrently
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Verify all requests completed successfully
        assert len(results) == 5
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent request failed: {result}")
            else:
                assert isinstance(result, list)
                assert len(result) == 2  # Based on our mock response


if __name__ == "__main__":
    pytest.main([__file__])