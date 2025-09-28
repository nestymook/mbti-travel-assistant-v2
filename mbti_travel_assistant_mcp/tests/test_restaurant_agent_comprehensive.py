"""
Comprehensive Unit Tests for Restaurant Agent Service

Tests all aspects of the restaurant agent including parameter processing,
MCP orchestration, response formatting, and error handling.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from services.restaurant_agent import RestaurantAgent
from models.restaurant_models import Restaurant, Sentiment


class TestRestaurantAgent:
    """Comprehensive test cases for RestaurantAgent."""
    
    @pytest.fixture
    def restaurant_agent(self):
        """Create restaurant agent instance with mocked dependencies."""
        with patch('services.restaurant_agent.MCPClientManager') as mock_mcp_manager:
            with patch('services.restaurant_agent.settings') as mock_settings:
                mock_settings.agentcore.agent_model = "amazon.nova-pro-v1:0:300k"
                mock_settings.agentcore.agent_temperature = 0.1
                mock_settings.agentcore.agent_max_tokens = 4096
                
                agent = RestaurantAgent()
                agent.mcp_client_manager = mock_mcp_manager.return_value
                return agent
    
    @pytest.fixture
    def sample_restaurants(self):
        """Create sample restaurant data."""
        return [
            Restaurant(
                id="rest_001",
                name="Restaurant A",
                address="123 Test St",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
                price_range="$",
                operating_hours={"Monday": ["07:00", "11:30"]},
                location_category="Shopping Mall"
            ),
            Restaurant(
                id="rest_002",
                name="Restaurant B",
                address="456 Test Ave",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=75, dislikes=15, neutral=10),
                price_range="$$",
                operating_hours={"Monday": ["07:00", "11:30"]},
                location_category="Street Food"
            )
        ]
    
    @pytest.fixture
    def sample_reasoning_results(self, sample_restaurants):
        """Create sample reasoning results."""
        return {
            "recommendation": {
                "id": "rest_001",
                "name": "Restaurant A",
                "address": "123 Test St",
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
                    "name": "Restaurant B",
                    "address": "456 Test Ave",
                    "district": "Central district",
                    "meal_type": ["breakfast"],
                    "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},
                    "price_range": "$$",
                    "operating_hours": {"Monday": ["07:00", "11:30"]},
                    "location_category": "Street Food"
                }
            ],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {
                "total_restaurants": 2,
                "average_sentiment": 80.0
            }
        }
    
    def test_init_with_strands_available(self):
        """Test initialization when strands_agents is available."""
        with patch('services.restaurant_agent.STRANDS_AVAILABLE', True):
            with patch('services.restaurant_agent.MCPClientManager'):
                with patch('services.restaurant_agent.settings') as mock_settings:
                    mock_settings.agentcore.agent_model = "test-model"
                    mock_settings.agentcore.agent_temperature = 0.1
                    mock_settings.agentcore.agent_max_tokens = 4096
                    
                    agent = RestaurantAgent()
                    
                    assert agent.mcp_client_manager is not None
                    assert agent.agent is not None
    
    def test_init_with_strands_unavailable(self):
        """Test initialization when strands_agents is not available."""
        with patch('services.restaurant_agent.STRANDS_AVAILABLE', False):
            with patch('services.restaurant_agent.MCPClientManager'):
                with patch('services.restaurant_agent.settings') as mock_settings:
                    mock_settings.agentcore.agent_model = "test-model"
                    mock_settings.agentcore.agent_temperature = 0.1
                    mock_settings.agentcore.agent_max_tokens = 4096
                    
                    agent = RestaurantAgent()
                    
                    assert agent.mcp_client_manager is not None
                    assert agent.agent is not None
    
    def test_get_system_prompt(self, restaurant_agent):
        """Test system prompt generation."""
        prompt = restaurant_agent._get_system_prompt()
        
        assert isinstance(prompt, str)
        assert "restaurant recommendation orchestration agent" in prompt.lower()
        assert "mcp server" in prompt.lower()
        assert "json" in prompt.lower()
        assert "recommendation" in prompt.lower()
        assert "candidates" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_process_parameters_basic(self, restaurant_agent):
        """Test basic parameter processing."""
        result = await restaurant_agent._process_parameters(
            district="Central district",
            meal_time="breakfast",
            user_context=None,
            correlation_id="test-123"
        )
        
        assert result["district"] == "Central district"
        assert result["meal_time"] == "breakfast"
        assert result["user_preferences"] == {}
    
    @pytest.mark.asyncio
    async def test_process_parameters_district_normalization(self, restaurant_agent):
        """Test district name normalization."""
        test_cases = [
            ("central", "Central district"),
            ("Central", "Central district"),
            ("admiralty", "Admiralty"),
            ("ADMIRALTY", "Admiralty"),
            ("causeway bay", "Causeway Bay"),
            ("Causeway Bay", "Causeway Bay"),
            ("Other District", "Other District")
        ]
        
        for input_district, expected_district in test_cases:
            result = await restaurant_agent._process_parameters(
                district=input_district,
                meal_time="breakfast",
                user_context=None,
                correlation_id="test-123"
            )
            
            assert result["district"] == expected_district
    
    @pytest.mark.asyncio
    async def test_process_parameters_meal_time_normalization(self, restaurant_agent):
        """Test meal time normalization."""
        test_cases = [
            ("breakfast", "breakfast"),
            ("morning", "breakfast"),
            ("am", "breakfast"),
            ("lunch", "lunch"),
            ("afternoon", "lunch"),
            ("noon", "lunch"),
            ("dinner", "dinner"),
            ("evening", "dinner"),
            ("night", "dinner"),
            ("pm", "dinner"),
            ("other", "other")
        ]
        
        for input_meal_time, expected_meal_time in test_cases:
            result = await restaurant_agent._process_parameters(
                district="Central district",
                meal_time=input_meal_time,
                user_context=None,
                correlation_id="test-123"
            )
            
            assert result["meal_time"] == expected_meal_time
    
    @pytest.mark.asyncio
    async def test_process_parameters_with_user_context(self, restaurant_agent):
        """Test parameter processing with user context."""
        user_context = {
            "sub": "user-123",
            "custom:preferences": {"cuisine": "asian"},
            "custom:dietary_restrictions": ["vegetarian"]
        }
        
        result = await restaurant_agent._process_parameters(
            district="Central district",
            meal_time="breakfast",
            user_context=user_context,
            correlation_id="test-123"
        )
        
        assert result["user_preferences"]["user_id"] == "user-123"
        assert result["user_preferences"]["preferences"] == {"cuisine": "asian"}
        assert result["user_preferences"]["dietary_restrictions"] == ["vegetarian"]
    
    @pytest.mark.asyncio
    async def test_filter_search_results_basic(self, restaurant_agent, sample_restaurants):
        """Test basic search results filtering."""
        processed_params = {
            "district": "Central district",
            "meal_time": "breakfast",
            "user_preferences": {}
        }
        
        result = await restaurant_agent._filter_search_results(
            sample_restaurants,
            processed_params,
            "test-123"
        )
        
        # Should include both restaurants as they have valid data
        assert len(result) == 2
        assert all(r.id and r.name for r in result)
    
    @pytest.mark.asyncio
    async def test_filter_search_results_invalid_data(self, restaurant_agent):
        """Test filtering out restaurants with invalid data."""
        invalid_restaurants = [
            Restaurant(
                id="",  # Empty ID
                name="Invalid Restaurant",
                address="123 Test St",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                price_range="$",
                operating_hours={},
                location_category=""
            ),
            Restaurant(
                id="rest_002",
                name="",  # Empty name
                address="456 Test Ave",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=75, dislikes=15, neutral=10),
                price_range="$$",
                operating_hours={"Monday": ["07:00", "11:30"]},
                location_category="Street Food"
            )
        ]
        
        processed_params = {
            "district": "Central district",
            "meal_time": "breakfast",
            "user_preferences": {}
        }
        
        result = await restaurant_agent._filter_search_results(
            invalid_restaurants,
            processed_params,
            "test-123"
        )
        
        # Should filter out restaurants with empty ID or name
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_filter_search_results_no_sentiment(self, restaurant_agent):
        """Test filtering out restaurants with no sentiment data."""
        no_sentiment_restaurants = [
            Restaurant(
                id="rest_001",
                name="No Sentiment Restaurant",
                address="123 Test St",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=0, dislikes=0, neutral=0),  # No sentiment data
                price_range="$",
                operating_hours={"Monday": ["07:00", "11:30"]},
                location_category="Shopping Mall"
            )
        ]
        
        processed_params = {
            "district": "Central district",
            "meal_time": "breakfast",
            "user_preferences": {}
        }
        
        result = await restaurant_agent._filter_search_results(
            no_sentiment_restaurants,
            processed_params,
            "test-123"
        )
        
        # Should filter out restaurants with no sentiment data
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_validate_reasoning_results_basic(self, restaurant_agent, sample_reasoning_results):
        """Test basic reasoning results validation."""
        processed_params = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        result = await restaurant_agent._validate_reasoning_results(
            sample_reasoning_results,
            processed_params,
            "test-123"
        )
        
        assert result["recommendation"] is not None
        assert len(result["candidates"]) == 1
        assert result["search_criteria"]["district"] == "Central district"
        assert result["search_criteria"]["meal_time"] == "breakfast"
        assert "analysis_summary" in result
    
    @pytest.mark.asyncio
    async def test_validate_reasoning_results_no_recommendation(self, restaurant_agent):
        """Test validation when no recommendation is provided."""
        reasoning_results = {
            "recommendation": None,
            "candidates": [
                {"id": "rest_001", "name": "Restaurant A"},
                {"id": "rest_002", "name": "Restaurant B"}
            ],
            "ranking_method": "sentiment_likes"
        }
        
        processed_params = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        result = await restaurant_agent._validate_reasoning_results(
            reasoning_results,
            processed_params,
            "test-123"
        )
        
        # Should promote first candidate to recommendation
        assert result["recommendation"]["id"] == "rest_001"
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["id"] == "rest_002"
    
    @pytest.mark.asyncio
    async def test_validate_reasoning_results_too_many_candidates(self, restaurant_agent):
        """Test validation with too many candidates."""
        # Create 25 candidates (exceeds limit of 19)
        candidates = []
        for i in range(25):
            candidates.append({"id": f"rest_{i:03d}", "name": f"Restaurant {i}"})
        
        reasoning_results = {
            "recommendation": {"id": "rest_rec", "name": "Recommended Restaurant"},
            "candidates": candidates,
            "ranking_method": "sentiment_likes"
        }
        
        processed_params = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        result = await restaurant_agent._validate_reasoning_results(
            reasoning_results,
            processed_params,
            "test-123"
        )
        
        # Should truncate to 19 candidates
        assert len(result["candidates"]) == 19
        assert result["recommendation"]["id"] == "rest_rec"
    
    @pytest.mark.asyncio
    async def test_search_restaurants_success(self, restaurant_agent, sample_restaurants):
        """Test successful restaurant search."""
        restaurant_agent.mcp_client_manager.search_restaurants = AsyncMock(
            return_value=sample_restaurants
        )
        
        result = await restaurant_agent._search_restaurants(
            district="Central district",
            meal_time="breakfast",
            correlation_id="test-123"
        )
        
        assert result == sample_restaurants
        restaurant_agent.mcp_client_manager.search_restaurants.assert_called_once_with(
            district="Central district",
            meal_time="breakfast"
        )
    
    @pytest.mark.asyncio
    async def test_search_restaurants_no_criteria(self, restaurant_agent, sample_restaurants):
        """Test restaurant search with no criteria."""
        restaurant_agent.mcp_client_manager.search_restaurants = AsyncMock(
            return_value=sample_restaurants
        )
        
        result = await restaurant_agent._search_restaurants(
            district=None,
            meal_time=None,
            correlation_id="test-123"
        )
        
        assert result == sample_restaurants
        restaurant_agent.mcp_client_manager.search_restaurants.assert_called_once_with(
            district=None,
            meal_time=None
        )
    
    @pytest.mark.asyncio
    async def test_search_restaurants_no_results(self, restaurant_agent):
        """Test restaurant search with no results."""
        restaurant_agent.mcp_client_manager.search_restaurants = AsyncMock(
            return_value=[]
        )
        
        result = await restaurant_agent._search_restaurants(
            district="Nonexistent District",
            meal_time="breakfast",
            correlation_id="test-123"
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_search_restaurants_error(self, restaurant_agent):
        """Test restaurant search error handling."""
        restaurant_agent.mcp_client_manager.search_restaurants = AsyncMock(
            side_effect=Exception("Search MCP error")
        )
        
        with pytest.raises(Exception, match="Search MCP error"):
            await restaurant_agent._search_restaurants(
                district="Central district",
                meal_time="breakfast",
                correlation_id="test-123"
            )
    
    @pytest.mark.asyncio
    async def test_analyze_restaurants_success(self, restaurant_agent, sample_restaurants, sample_reasoning_results):
        """Test successful restaurant analysis."""
        restaurant_agent.mcp_client_manager.analyze_restaurants = AsyncMock(
            return_value=sample_reasoning_results
        )
        
        result = await restaurant_agent._analyze_restaurants(
            sample_restaurants,
            "test-123"
        )
        
        assert result == sample_reasoning_results
        restaurant_agent.mcp_client_manager.analyze_restaurants.assert_called_once_with(
            restaurants=sample_restaurants,
            ranking_method="sentiment_likes"
        )
    
    @pytest.mark.asyncio
    async def test_analyze_restaurants_empty_list(self, restaurant_agent):
        """Test restaurant analysis with empty list."""
        result = await restaurant_agent._analyze_restaurants(
            [],
            "test-123"
        )
        
        assert result["recommendation"] is None
        assert result["candidates"] == []
        assert result["ranking_method"] == "sentiment_likes"
        assert "No restaurants available" in result["analysis_summary"]["message"]
    
    @pytest.mark.asyncio
    async def test_analyze_restaurants_invalid_data(self, restaurant_agent):
        """Test restaurant analysis with invalid data."""
        invalid_restaurants = [
            Restaurant(
                id="",  # Empty ID
                name="",  # Empty name
                address="123 Test St",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
                price_range="$",
                operating_hours={"Monday": ["07:00", "11:30"]},
                location_category="Shopping Mall"
            )
        ]
        
        result = await restaurant_agent._analyze_restaurants(
            invalid_restaurants,
            "test-123"
        )
        
        assert result["recommendation"] is None
        assert result["candidates"] == []
        assert result["analysis_summary"]["valid_restaurants"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_restaurants_error(self, restaurant_agent, sample_restaurants):
        """Test restaurant analysis error handling."""
        restaurant_agent.mcp_client_manager.analyze_restaurants = AsyncMock(
            side_effect=Exception("Reasoning MCP error")
        )
        
        with pytest.raises(Exception, match="Reasoning MCP error"):
            await restaurant_agent._analyze_restaurants(
                sample_restaurants,
                "test-123"
            )
    
    def test_create_formatting_prompt(self, restaurant_agent, sample_reasoning_results):
        """Test formatting prompt creation."""
        start_time = datetime.utcnow()
        
        prompt = restaurant_agent._create_formatting_prompt(
            sample_reasoning_results,
            "Central district",
            "breakfast",
            start_time
        )
        
        assert isinstance(prompt, str)
        assert "REASONING RESULTS:" in prompt
        assert "SEARCH CRITERIA:" in prompt
        assert "Central district" in prompt
        assert "breakfast" in prompt
        assert "REQUIREMENTS:" in prompt
        assert "JSON" in prompt
    
    def test_fallback_format_response(self, restaurant_agent, sample_reasoning_results):
        """Test fallback response formatting."""
        start_time = datetime.utcnow()
        
        result = restaurant_agent._fallback_format_response(
            sample_reasoning_results,
            "Central district",
            "breakfast",
            start_time
        )
        
        assert "recommendation" in result
        assert "candidates" in result
        assert "metadata" in result
        assert result["metadata"]["search_criteria"]["district"] == "Central district"
        assert result["metadata"]["search_criteria"]["meal_time"] == "breakfast"
        assert result["metadata"]["formatted_by"] == "fallback"
    
    def test_fallback_format_response_no_recommendation(self, restaurant_agent):
        """Test fallback formatting when no recommendation is provided."""
        reasoning_results = {
            "recommendation": None,
            "candidates": [
                {"id": "rest_001", "name": "Restaurant A"},
                {"id": "rest_002", "name": "Restaurant B"}
            ]
        }
        
        start_time = datetime.utcnow()
        
        result = restaurant_agent._fallback_format_response(
            reasoning_results,
            "Central district",
            "breakfast",
            start_time
        )
        
        # Should promote first candidate to recommendation
        assert result["recommendation"]["id"] == "rest_001"
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["id"] == "rest_002"
    
    @pytest.mark.asyncio
    async def test_format_agent_response_success(self, restaurant_agent, sample_reasoning_results):
        """Test successful agent response formatting."""
        start_time = datetime.utcnow()
        
        # Mock agent response
        mock_agent_response = Mock()
        mock_agent_response.content = json.dumps({
            "recommendation": sample_reasoning_results["recommendation"],
            "candidates": sample_reasoning_results["candidates"],
            "metadata": {"formatted_by": "agent"}
        })
        
        restaurant_agent.agent.process = AsyncMock(return_value=mock_agent_response)
        
        with patch.object(restaurant_agent, '_validate_and_enhance_response') as mock_validate:
            mock_validate.return_value = {"validated": True}
            
            result = await restaurant_agent._format_agent_response(
                sample_reasoning_results,
                "Central district",
                "breakfast",
                start_time,
                "test-123"
            )
        
        assert result == {"validated": True}
        restaurant_agent.agent.process.assert_called_once()
        mock_validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_format_agent_response_invalid_json(self, restaurant_agent, sample_reasoning_results):
        """Test agent response formatting with invalid JSON."""
        start_time = datetime.utcnow()
        
        # Mock agent response with invalid JSON
        mock_agent_response = Mock()
        mock_agent_response.content = "invalid json{"
        
        restaurant_agent.agent.process = AsyncMock(return_value=mock_agent_response)
        
        with patch.object(restaurant_agent, '_fallback_format_response') as mock_fallback:
            mock_fallback.return_value = {"fallback": True}
            
            result = await restaurant_agent._format_agent_response(
                sample_reasoning_results,
                "Central district",
                "breakfast",
                start_time,
                "test-123"
            )
        
        assert result == {"fallback": True}
        mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_format_agent_response_error(self, restaurant_agent, sample_reasoning_results):
        """Test agent response formatting error handling."""
        start_time = datetime.utcnow()
        
        restaurant_agent.agent.process = AsyncMock(side_effect=Exception("Agent error"))
        
        with patch.object(restaurant_agent, '_fallback_format_response') as mock_fallback:
            mock_fallback.return_value = {"fallback": True}
            
            result = await restaurant_agent._format_agent_response(
                sample_reasoning_results,
                "Central district",
                "breakfast",
                start_time,
                "test-123"
            )
        
        assert result == {"fallback": True}
        mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, restaurant_agent, sample_restaurants, sample_reasoning_results):
        """Test successful end-to-end request processing."""
        # Mock all the dependencies
        restaurant_agent.mcp_client_manager.search_restaurants = AsyncMock(
            return_value=sample_restaurants
        )
        restaurant_agent.mcp_client_manager.analyze_restaurants = AsyncMock(
            return_value=sample_reasoning_results
        )
        
        mock_agent_response = Mock()
        mock_agent_response.content = json.dumps({
            "recommendation": sample_reasoning_results["recommendation"],
            "candidates": sample_reasoning_results["candidates"],
            "metadata": {"test": True}
        })
        restaurant_agent.agent.process = AsyncMock(return_value=mock_agent_response)
        
        with patch.object(restaurant_agent, '_validate_and_enhance_response') as mock_validate:
            mock_validate.return_value = {"final": "response"}
            
            result = await restaurant_agent.process_request(
                district="Central district",
                meal_time="breakfast",
                user_context={"sub": "user-123"},
                correlation_id="test-123"
            )
        
        assert result == {"final": "response"}
        restaurant_agent.mcp_client_manager.search_restaurants.assert_called_once()
        restaurant_agent.mcp_client_manager.analyze_restaurants.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_search_error(self, restaurant_agent):
        """Test request processing with search error."""
        restaurant_agent.mcp_client_manager.search_restaurants = AsyncMock(
            side_effect=Exception("Search failed")
        )
        
        with pytest.raises(Exception, match="Search failed"):
            await restaurant_agent.process_request(
                district="Central district",
                meal_time="breakfast",
                correlation_id="test-123"
            )
    
    @pytest.mark.asyncio
    async def test_process_request_analysis_error(self, restaurant_agent, sample_restaurants):
        """Test request processing with analysis error."""
        restaurant_agent.mcp_client_manager.search_restaurants = AsyncMock(
            return_value=sample_restaurants
        )
        restaurant_agent.mcp_client_manager.analyze_restaurants = AsyncMock(
            side_effect=Exception("Analysis failed")
        )
        
        with pytest.raises(Exception, match="Analysis failed"):
            await restaurant_agent.process_request(
                district="Central district",
                meal_time="breakfast",
                correlation_id="test-123"
            )


if __name__ == "__main__":
    pytest.main([__file__])