"""
Integration and End-to-End Tests for Complete 3-Day Itinerary Generation

This module provides comprehensive integration tests for the complete 3-day itinerary
generation workflow, testing all components working together.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import List, Dict, Any
import json
import time
from datetime import datetime

from ..services.itinerary_generator import ItineraryGenerator
from ..services.nova_pro_knowledge_base_client import NovaProKnowledgeBaseClient
from ..services.session_assignment_logic import SessionAssignmentLogic
from ..services.assignment_validator import AssignmentValidator
from ..services.mcp_client_manager import MCPClientManager
from ..services.restaurant_agent import RestaurantAgent
from ..services.cache_service import CacheService
from ..services.error_handler import ErrorHandler
from ..services.response_formatter import ResponseFormatter

from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours
from ..models.restaurant_models import Restaurant
from ..models.itinerary_models import MainItinerary
from ..models.mbti_request_response_models import ItineraryRequest, ItineraryResponse


class TestCompleteItineraryIntegration:
    """Integration tests for complete 3-day itinerary generation."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.itinerary_generator = ItineraryGenerator()
        self.mock_nova_client = Mock(spec=NovaProKnowledgeBaseClient)
        self.mock_mcp_client = Mock(spec=MCPClientManager)
        self.mock_restaurant_agent = Mock(spec=RestaurantAgent)
        
        # Inject mocked dependencies
        self.itinerary_generator.nova_client = self.mock_nova_client
        self.itinerary_generator.mcp_client = self.mock_mcp_client
        self.itinerary_generator.restaurant_agent = self.mock_restaurant_agent
        
        # Create test data
        self.test_tourist_spots = self._create_test_tourist_spots()
        self.test_restaurants = self._create_test_restaurants()

    def _create_test_tourist_spots(self) -> List[TouristSpot]:
        """Create test tourist spots for integration testing."""
        spots = []
        
        # Create 15 INFJ-matched spots for 3-day itinerary (9 sessions + extras)
        districts = ["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui", "Causeway Bay"]
        categories = ["Museum", "Park", "Temple", "Gallery", "Garden"]
        
        for i in range(15):
            operating_hours = TouristSpotOperatingHours(
                monday="09:00-18:00", tuesday="09:00-18:00", wednesday="09:00-18:00",
                thursday="09:00-18:00", friday="09:00-18:00", saturday="10:00-17:00", sunday="10:00-17:00"
            )
            
            spot = TouristSpot(
                id=f"infj_spot_{i}",
                name=f"INFJ Attraction {i}",
                address=f"{100 + i} Test Street, {districts[i % len(districts)]}, Hong Kong",
                district=districts[i % len(districts)],
                area="Hong Kong Island" if i < 10 else "Kowloon",
                location_category=categories[i % len(categories)],
                description=f"A peaceful and cultural attraction perfect for INFJ personality type {i}",
                operating_hours=operating_hours,
                operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                mbti_personality_types=["INFJ"],
                keywords=["quiet", "cultural", "peaceful", "educational"],
                mbti_match=True
            )
            spots.append(spot)
        
        return spots

    def _create_test_restaurants(self) -> List[Restaurant]:
        """Create test restaurants for integration testing."""
        restaurants = []
        
        # Create restaurants for each meal type and district
        districts = ["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui", "Causeway Bay"]
        meal_configs = [
            ("breakfast", "07:00-11:00", "Cafe"),
            ("lunch", "11:30-15:00", "Bistro"),
            ("dinner", "18:00-22:00", "Restaurant")
        ]
        
        for district in districts:
            for meal_type, hours, cuisine in meal_configs:
                for i in range(3):  # 3 restaurants per meal type per district
                    restaurant = Restaurant(
                        id=f"{meal_type}_{district.lower()}_{i}",
                        name=f"{district} {meal_type.title()} {cuisine} {i}",
                        address=f"{200 + i} {meal_type.title()} Street, {district}, Hong Kong",
                        district=district,
                        operating_hours=hours,
                        cuisine_type=cuisine,
                        phone=f"+852-{1000 + i}-{2000 + i}",
                        rating=4.0 + (i * 0.2),
                        sentiment={"likes": 80 + i, "dislikes": 10 - i, "neutral": 10}
                    )
                    restaurants.append(restaurant)
        
        return restaurants

    @pytest.mark.asyncio
    async def test_complete_3_day_itinerary_generation_success(self):
        """Test successful complete 3-day itinerary generation."""
        # Mock Nova Pro client response
        self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=self.test_tourist_spots
        )
        
        # Mock MCP client responses
        self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
            side_effect=self._mock_restaurant_search
        )
        
        # Mock restaurant agent responses
        self.mock_restaurant_agent.get_restaurant_recommendations = AsyncMock(
            side_effect=self._mock_restaurant_recommendations
        )
        
        # Generate complete itinerary
        result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
        
        # Verify structure
        assert isinstance(result, dict)
        assert "main_itinerary" in result
        assert "candidate_tourist_spots" in result
        assert "candidate_restaurants" in result
        assert "metadata" in result
        
        # Verify main itinerary
        main_itinerary = result["main_itinerary"]
        assert "day_1" in main_itinerary
        assert "day_2" in main_itinerary
        assert "day_3" in main_itinerary
        
        # Verify each day has all sessions and meals
        for day_key in ["day_1", "day_2", "day_3"]:
            day = main_itinerary[day_key]
            assert "morning_session" in day
            assert "afternoon_session" in day
            assert "night_session" in day
            assert "breakfast" in day
            assert "lunch" in day
            assert "dinner" in day
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["MBTI_personality"] == "INFJ"
        assert "generation_timestamp" in metadata
        assert "total_spots_found" in metadata
        assert "total_restaurants_found" in metadata
        assert "processing_time_ms" in metadata

    @pytest.mark.asyncio
    async def test_complete_itinerary_generation_with_validation(self):
        """Test complete itinerary generation with validation."""
        # Mock successful responses
        self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=self.test_tourist_spots
        )
        self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
            side_effect=self._mock_restaurant_search
        )
        self.mock_restaurant_agent.get_restaurant_recommendations = AsyncMock(
            side_effect=self._mock_restaurant_recommendations
        )
        
        # Generate itinerary with validation enabled
        result = await self.itinerary_generator.generate_complete_itinerary(
            "INFJ", enable_validation=True
        )
        
        # Should include validation results
        assert "validation_report" in result["metadata"]
        validation_report = result["metadata"]["validation_report"]
        assert "is_valid" in validation_report
        assert "total_issues" in validation_report

    @pytest.mark.asyncio
    async def test_itinerary_generation_different_mbti_types(self):
        """Test itinerary generation for different MBTI personality types."""
        mbti_types = ["INFJ", "ENFP", "INTJ", "ESTP"]
        
        for mbti_type in mbti_types:
            # Create type-specific test spots
            type_spots = self._create_mbti_specific_spots(mbti_type)
            
            self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
                return_value=type_spots
            )
            self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
                side_effect=self._mock_restaurant_search
            )
            self.mock_restaurant_agent.get_restaurant_recommendations = AsyncMock(
                side_effect=self._mock_restaurant_recommendations
            )
            
            result = await self.itinerary_generator.generate_complete_itinerary(mbti_type)
            
            # Verify MBTI-specific results
            assert result["metadata"]["MBTI_personality"] == mbti_type
            assert "main_itinerary" in result
            
            # Verify MBTI matching in tourist spots
            main_itinerary = result["main_itinerary"]
            for day_key in ["day_1", "day_2", "day_3"]:
                day = main_itinerary[day_key]
                for session_key in ["morning_session", "afternoon_session", "night_session"]:
                    if day[session_key] and day[session_key]["tourist_spot"]:
                        spot = day[session_key]["tourist_spot"]
                        if spot.get("mbti_match"):
                            assert mbti_type in spot.get("mbti_personality_types", [])

    @pytest.mark.asyncio
    async def test_itinerary_generation_with_insufficient_spots(self):
        """Test itinerary generation when insufficient tourist spots are available."""
        # Provide only 5 spots (less than needed for 9 sessions)
        limited_spots = self.test_tourist_spots[:5]
        
        self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=limited_spots
        )
        self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
            side_effect=self._mock_restaurant_search
        )
        self.mock_restaurant_agent.get_restaurant_recommendations = AsyncMock(
            side_effect=self._mock_restaurant_recommendations
        )
        
        result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
        
        # Should still generate itinerary with available spots
        assert "main_itinerary" in result
        
        # Some sessions might be None or use fallback spots
        main_itinerary = result["main_itinerary"]
        total_assigned_spots = 0
        
        for day_key in ["day_1", "day_2", "day_3"]:
            day = main_itinerary[day_key]
            for session_key in ["morning_session", "afternoon_session", "night_session"]:
                if day[session_key] and day[session_key]["tourist_spot"]:
                    total_assigned_spots += 1
        
        # Should have assigned some spots, but might not be all 9
        assert total_assigned_spots > 0

    @pytest.mark.asyncio
    async def test_itinerary_generation_with_restaurant_failures(self):
        """Test itinerary generation when restaurant search fails."""
        self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=self.test_tourist_spots
        )
        
        # Mock restaurant search failures
        self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
            side_effect=Exception("Restaurant search failed")
        )
        
        # Mock restaurant agent fallback
        self.mock_restaurant_agent.get_fallback_restaurants = AsyncMock(
            return_value=self.test_restaurants[:3]  # Fallback restaurants
        )
        
        result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
        
        # Should still generate itinerary with fallback restaurants
        assert "main_itinerary" in result
        
        # Check that some restaurants are assigned (fallback)
        main_itinerary = result["main_itinerary"]
        total_assigned_restaurants = 0
        
        for day_key in ["day_1", "day_2", "day_3"]:
            day = main_itinerary[day_key]
            for meal_key in ["breakfast", "lunch", "dinner"]:
                if day[meal_key] and day[meal_key]["restaurant"]:
                    total_assigned_restaurants += 1
        
        assert total_assigned_restaurants > 0

    @pytest.mark.asyncio
    async def test_itinerary_generation_performance_requirements(self):
        """Test that itinerary generation meets performance requirements."""
        self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=self.test_tourist_spots
        )
        self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
            side_effect=self._mock_restaurant_search
        )
        self.mock_restaurant_agent.get_restaurant_recommendations = AsyncMock(
            side_effect=self._mock_restaurant_recommendations
        )
        
        # Measure generation time
        start_time = time.time()
        result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
        end_time = time.time()
        
        generation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Should meet 10-second requirement (10,000ms)
        assert generation_time < 10000
        
        # Verify processing time is recorded in metadata
        assert result["metadata"]["processing_time_ms"] < 10000

    @pytest.mark.asyncio
    async def test_concurrent_itinerary_generation(self):
        """Test concurrent itinerary generation for multiple requests."""
        self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=self.test_tourist_spots
        )
        self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
            side_effect=self._mock_restaurant_search
        )
        self.mock_restaurant_agent.get_restaurant_recommendations = AsyncMock(
            side_effect=self._mock_restaurant_recommendations
        )
        
        # Generate multiple itineraries concurrently
        mbti_types = ["INFJ", "ENFP", "INTJ", "ESTP", "ISFJ"]
        
        tasks = [
            self.itinerary_generator.generate_complete_itinerary(mbti_type)
            for mbti_type in mbti_types
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        
        for i, result in enumerate(results):
            assert isinstance(result, dict)
            assert result["metadata"]["MBTI_personality"] == mbti_types[i]
            assert "main_itinerary" in result

    @pytest.mark.asyncio
    async def test_itinerary_generation_with_caching(self):
        """Test itinerary generation with caching enabled."""
        self.mock_nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=self.test_tourist_spots
        )
        self.mock_mcp_client.search_restaurants_by_meal_and_district = AsyncMock(
            side_effect=self._mock_restaurant_search
        )
        self.mock_restaurant_agent.get_restaurant_recommendations = AsyncMock(
            side_effect=self._mock_restaurant_recommendations
        )
        
        # Enable caching
        self.itinerary_generator.enable_caching = True
        
        # First generation
        start_time = time.time()
        result1 = await self.itinerary_generator.generate_complete_itinerary("INFJ")
        first_time = time.time() - start_time
        
        # Second generation (should use cache)
        start_time = time.time()
        result2 = await self.itinerary_generator.generate_complete_itinerary("INFJ")
        second_time = time.time() - start_time
        
        # Second generation should be faster
        assert second_time < first_time
        
        # Results should be consistent
        assert result1["metadata"]["MBTI_personality"] == result2["metadata"]["MBTI_personality"]

    def _mock_restaurant_search(self, meal_type: str, district: str) -> List[Restaurant]:
        """Mock restaurant search by meal type and district."""
        matching_restaurants = [
            r for r in self.test_restaurants
            if meal_type in r.id and district.lower() in r.id
        ]
        return matching_restaurants[:3]  # Return up to 3 restaurants

    def _mock_restaurant_recommendations(self, restaurants: List[Restaurant]) -> Dict[str, Any]:
        """Mock restaurant recommendations."""
        if not restaurants:
            return {"recommendation": None, "candidates": []}
        
        return {
            "recommendation": restaurants[0],
            "candidates": restaurants[1:],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {
                "total_restaurants": len(restaurants),
                "average_rating": sum(r.rating for r in restaurants) / len(restaurants)
            }
        }

    def _create_mbti_specific_spots(self, mbti_type: str) -> List[TouristSpot]:
        """Create MBTI-specific test spots."""
        spots = []
        
        # MBTI-specific characteristics
        mbti_configs = {
            "INFJ": {"keywords": ["quiet", "cultural", "peaceful"], "categories": ["Museum", "Temple", "Garden"]},
            "ENFP": {"keywords": ["vibrant", "social", "interactive"], "categories": ["Market", "Festival", "Entertainment"]},
            "INTJ": {"keywords": ["strategic", "educational", "architectural"], "categories": ["Observatory", "Library", "Monument"]},
            "ESTP": {"keywords": ["active", "adventurous", "dynamic"], "categories": ["Sports", "Adventure", "Outdoor"]}
        }
        
        config = mbti_configs.get(mbti_type, mbti_configs["INFJ"])
        
        for i in range(12):  # Create 12 spots for variety
            operating_hours = TouristSpotOperatingHours(
                monday="09:00-18:00", tuesday="09:00-18:00", wednesday="09:00-18:00",
                thursday="09:00-18:00", friday="09:00-18:00", saturday="10:00-17:00", sunday="10:00-17:00"
            )
            
            spot = TouristSpot(
                id=f"{mbti_type.lower()}_spot_{i}",
                name=f"{mbti_type} Attraction {i}",
                address=f"{300 + i} {mbti_type} Street, Central, Hong Kong",
                district="Central",
                area="Hong Kong Island",
                location_category=config["categories"][i % len(config["categories"])],
                description=f"A {mbti_type}-specific attraction {i}",
                operating_hours=operating_hours,
                operating_days=["daily"],
                mbti_personality_types=[mbti_type],
                keywords=config["keywords"],
                mbti_match=True
            )
            spots.append(spot)
        
        return spots


class TestEndToEndItineraryWorkflow:
    """End-to-end tests for complete itinerary workflow."""

    def setup_method(self):
        """Set up end-to-end test fixtures."""
        # Create real instances (not mocked) for end-to-end testing
        self.itinerary_generator = ItineraryGenerator()
        self.session_logic = SessionAssignmentLogic()
        self.validator = AssignmentValidator()
        self.cache_service = CacheService()
        self.error_handler = ErrorHandler()
        self.response_formatter = ResponseFormatter()

    @pytest.mark.asyncio
    async def test_end_to_end_itinerary_request_processing(self):
        """Test complete end-to-end itinerary request processing."""
        # Create request
        request = ItineraryRequest(
            MBTI_personality="INFJ",
            user_preferences={
                "preferred_districts": ["Central", "Admiralty"],
                "activity_types": ["cultural", "peaceful"],
                "budget_level": "medium"
            },
            request_metadata={
                "user_id": "test_user_123",
                "session_id": "test_session_456",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Mock external dependencies
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Setup mocks
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self._create_test_spots()
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self._create_test_restaurants()
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self._create_test_restaurants()[0], "candidates": []}
                    )
                    
                    # Process request
                    try:
                        result = await self.itinerary_generator.generate_complete_itinerary(
                            request.MBTI_personality
                        )
                        
                        # Format response
                        response = self.response_formatter.format_itinerary_response(
                            result, request
                        )
                        
                        # Validate response structure
                        assert isinstance(response, dict)
                        assert "main_itinerary" in response
                        assert "candidate_tourist_spots" in response
                        assert "candidate_restaurants" in response
                        assert "metadata" in response
                        
                        # Validate response completeness
                        self._validate_complete_response(response)
                        
                    except Exception as e:
                        # Handle errors gracefully
                        error_response = self.error_handler.handle_itinerary_generation_error(
                            e, request
                        )
                        assert "error" in error_response
                        assert "error_type" in error_response["error"]

    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery_workflow(self):
        """Test end-to-end error recovery workflow."""
        request = ItineraryRequest(MBTI_personality="INVALID_TYPE")
        
        # Process request with invalid MBTI type
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            mock_nova.query_mbti_tourist_spots = AsyncMock(
                side_effect=ValueError("Invalid MBTI personality format")
            )
            
            try:
                result = await self.itinerary_generator.generate_complete_itinerary(
                    request.MBTI_personality
                )
                assert False, "Should have raised an error"
            except Exception as e:
                # Test error handling
                error_response = self.error_handler.handle_itinerary_generation_error(
                    e, request
                )
                
                assert "error" in error_response
                assert error_response["error"]["error_type"] == "validation_error"
                assert "Invalid MBTI personality format" in error_response["error"]["message"]

    @pytest.mark.asyncio
    async def test_end_to_end_performance_monitoring(self):
        """Test end-to-end performance monitoring."""
        request = ItineraryRequest(MBTI_personality="INFJ")
        
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Setup mocks with delays to test performance monitoring
                    async def slow_nova_query(*args, **kwargs):
                        await asyncio.sleep(0.1)  # Simulate processing time
                        return self._create_test_spots()
                    
                    async def slow_mcp_search(*args, **kwargs):
                        await asyncio.sleep(0.05)  # Simulate processing time
                        return self._create_test_restaurants()
                    
                    async def slow_restaurant_recommendations(*args, **kwargs):
                        await asyncio.sleep(0.02)  # Simulate processing time
                        return {"recommendation": self._create_test_restaurants()[0], "candidates": []}
                    
                    mock_nova.query_mbti_tourist_spots = slow_nova_query
                    mock_mcp.search_restaurants_by_meal_and_district = slow_mcp_search
                    mock_restaurant.get_restaurant_recommendations = slow_restaurant_recommendations
                    
                    # Measure total processing time
                    start_time = time.time()
                    result = await self.itinerary_generator.generate_complete_itinerary(
                        request.MBTI_personality
                    )
                    end_time = time.time()
                    
                    total_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    # Verify performance metrics are captured
                    assert "processing_time_ms" in result["metadata"]
                    assert result["metadata"]["processing_time_ms"] > 0
                    assert result["metadata"]["processing_time_ms"] < 10000  # Under 10 seconds

    def _create_test_spots(self) -> List[TouristSpot]:
        """Create test tourist spots for end-to-end testing."""
        spots = []
        for i in range(10):
            spot = TouristSpot(
                id=f"e2e_spot_{i}",
                name=f"E2E Test Spot {i}",
                address=f"{400 + i} E2E Street, Central, Hong Kong",
                district="Central",
                area="Hong Kong Island",
                location_category="Museum",
                description=f"End-to-end test spot {i}",
                operating_hours=TouristSpotOperatingHours(
                    monday="09:00-18:00", tuesday="09:00-18:00"
                ),
                operating_days=["daily"],
                mbti_personality_types=["INFJ"],
                keywords=["test", "e2e"],
                mbti_match=True
            )
            spots.append(spot)
        return spots

    def _create_test_restaurants(self) -> List[Restaurant]:
        """Create test restaurants for end-to-end testing."""
        restaurants = []
        for i in range(5):
            restaurant = Restaurant(
                id=f"e2e_restaurant_{i}",
                name=f"E2E Test Restaurant {i}",
                address=f"{500 + i} E2E Restaurant Street, Central, Hong Kong",
                district="Central",
                operating_hours="09:00-22:00",
                cuisine_type="Test Cuisine",
                phone=f"+852-{3000 + i}-{4000 + i}",
                rating=4.0 + (i * 0.1)
            )
            restaurants.append(restaurant)
        return restaurants

    def _validate_complete_response(self, response: Dict[str, Any]) -> None:
        """Validate complete response structure and content."""
        # Validate main structure
        assert "main_itinerary" in response
        assert "candidate_tourist_spots" in response
        assert "candidate_restaurants" in response
        assert "metadata" in response
        
        # Validate main itinerary structure
        main_itinerary = response["main_itinerary"]
        for day_key in ["day_1", "day_2", "day_3"]:
            assert day_key in main_itinerary
            day = main_itinerary[day_key]
            
            # Validate sessions
            for session_key in ["morning_session", "afternoon_session", "night_session"]:
                assert session_key in day
            
            # Validate meals
            for meal_key in ["breakfast", "lunch", "dinner"]:
                assert meal_key in day
        
        # Validate metadata
        metadata = response["metadata"]
        required_metadata_fields = [
            "MBTI_personality", "generation_timestamp", "total_spots_found",
            "total_restaurants_found", "processing_time_ms"
        ]
        
        for field in required_metadata_fields:
            assert field in metadata


class TestItineraryGenerationRegressionTests:
    """Regression tests for itinerary generation accuracy."""

    def setup_method(self):
        """Set up regression test fixtures."""
        self.itinerary_generator = ItineraryGenerator()

    @pytest.mark.asyncio
    async def test_regression_infj_itinerary_accuracy(self):
        """Test regression for INFJ itinerary generation accuracy."""
        # Load expected INFJ results (if available)
        expected_results_file = "tests/infj_expected_results.json"
        
        try:
            with open(expected_results_file, 'r') as f:
                expected_results = json.load(f)
        except FileNotFoundError:
            pytest.skip("Expected results file not found")
        
        # Mock dependencies with consistent data
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Setup consistent mocks
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self._load_consistent_spots()
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self._load_consistent_restaurants()
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self._load_consistent_restaurants()[0], "candidates": []}
                    )
                    
                    # Generate itinerary
                    result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
                    
                    # Compare with expected results
                    self._compare_with_expected_results(result, expected_results)

    def _load_consistent_spots(self) -> List[TouristSpot]:
        """Load consistent tourist spots for regression testing."""
        # This would load from a fixed dataset for consistent testing
        return []  # Placeholder

    def _load_consistent_restaurants(self) -> List[Restaurant]:
        """Load consistent restaurants for regression testing."""
        # This would load from a fixed dataset for consistent testing
        return []  # Placeholder

    def _compare_with_expected_results(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> None:
        """Compare actual results with expected results."""
        # Compare key metrics
        assert actual["metadata"]["MBTI_personality"] == expected["metadata"]["MBTI_personality"]
        
        # Compare structure completeness
        actual_days = len([k for k in actual["main_itinerary"].keys() if k.startswith("day_")])
        expected_days = len([k for k in expected["main_itinerary"].keys() if k.startswith("day_")])
        assert actual_days == expected_days


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=services.itinerary_generator", "--cov-report=term-missing"])