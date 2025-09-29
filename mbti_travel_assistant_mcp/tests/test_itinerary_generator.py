"""Tests for ItineraryGenerator orchestrator.

This module contains unit tests for the ItineraryGenerator class,
testing the main itinerary generation logic, candidate list generation,
and validation integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.itinerary_generator import (
    ItineraryGenerator, 
    ItineraryGenerationContext,
    ItineraryGenerationResult
)
from models.tourist_spot_models import TouristSpot, SessionType
from models.restaurant_models import Restaurant
from models.itinerary_models import MainItinerary, DayItinerary
from services.session_assignment_logic import AssignmentResult
from services.assignment_validator import ValidationReport


class TestItineraryGenerator:
    """Test cases for ItineraryGenerator class."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        with patch.multiple(
            'services.itinerary_generator',
            NovaProKnowledgeBaseClient=Mock(),
            SessionAssignmentLogic=Mock(),
            MCPClientManager=Mock(),
            AssignmentValidator=Mock(),
            ErrorHandler=Mock()
        ) as mocks:
            yield mocks
    
    @pytest.fixture
    def itinerary_generator(self, mock_services):
        """Create ItineraryGenerator instance with mocked services."""
        generator = ItineraryGenerator()
        
        # Configure mock services
        generator.nova_client = mock_services['NovaProKnowledgeBaseClient'].return_value
        generator.session_assigner = mock_services['SessionAssignmentLogic'].return_value
        generator.mcp_client = mock_services['MCPClientManager'].return_value
        generator.validator = mock_services['AssignmentValidator'].return_value
        generator.error_handler = mock_services['ErrorHandler'].return_value
        
        return generator
    
    @pytest.fixture
    def sample_tourist_spot(self):
        """Create sample tourist spot for testing."""
        return TouristSpot(
            id="spot_001",
            name="Test Tourist Spot",
            address="123 Test Street",
            district="Central",
            area="Hong Kong Island",
            location_category="Museum",
            description="A test tourist spot",
            mbti_match=True,
            mbti_personality_types=["INFJ"]
        )
    
    @pytest.fixture
    def sample_restaurant(self):
        """Create sample restaurant for testing."""
        return Restaurant(
            id="rest_001",
            name="Test Restaurant",
            address="456 Food Street",
            district="Central",
            operating_hours="08:00-22:00"
        )
    
    @pytest.mark.asyncio
    async def test_generate_complete_itinerary_success(
        self, 
        itinerary_generator, 
        sample_tourist_spot,
        sample_restaurant
    ):
        """Test successful complete itinerary generation."""
        # Mock nova client to return query results
        mock_query_result = Mock()
        mock_query_result.tourist_spot = sample_tourist_spot
        itinerary_generator.nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=[mock_query_result]
        )
        
        # Mock session assignment results
        assignment_result = AssignmentResult(
            tourist_spot=sample_tourist_spot,
            mbti_match=True,
            assignment_notes="Test assignment"
        )
        
        itinerary_generator.session_assigner.assign_morning_session.return_value = assignment_result
        itinerary_generator.session_assigner.assign_afternoon_session.return_value = assignment_result
        itinerary_generator.session_assigner.assign_night_session.return_value = assignment_result
        
        # Mock MCP client restaurant search
        itinerary_generator.mcp_client.search_restaurants = AsyncMock(
            return_value=[sample_restaurant]
        )
        itinerary_generator.mcp_client.get_restaurant_recommendations = AsyncMock(
            return_value={'recommendation': sample_restaurant}
        )
        
        # Mock validator
        validation_report = ValidationReport(
            is_valid=True,
            total_issues=0,
            error_count=0,
            warning_count=0,
            info_count=0,
            issues=[],
            validation_timestamp=datetime.now().isoformat(),
            validation_summary={},
            correction_suggestions=[]
        )
        itinerary_generator.validator.validate_complete_itinerary.return_value = validation_report
        
        # Execute test
        result = await itinerary_generator.generate_complete_itinerary("INFJ")
        
        # Assertions
        assert result.success is True
        assert result.main_itinerary is not None
        assert result.candidate_lists is not None
        assert result.validation_report is not None
        assert result.processing_time_ms > 0
        assert result.error_details is None
        
        # Verify main itinerary structure
        assert result.main_itinerary.mbti_personality == "INFJ"
        assert result.main_itinerary.day_1 is not None
        assert result.main_itinerary.day_2 is not None
        assert result.main_itinerary.day_3 is not None
    
    @pytest.mark.asyncio
    async def test_generate_complete_itinerary_invalid_mbti(self, itinerary_generator):
        """Test itinerary generation with invalid MBTI format."""
        result = await itinerary_generator.generate_complete_itinerary("INVALID")
        
        assert result.success is False
        assert result.error_details is not None
        assert result.main_itinerary is None
    
    @pytest.mark.asyncio
    async def test_generate_complete_itinerary_with_validation_failures(
        self, 
        itinerary_generator,
        sample_tourist_spot,
        sample_restaurant
    ):
        """Test itinerary generation with validation failures."""
        # Mock nova client
        mock_query_result = Mock()
        mock_query_result.tourist_spot = sample_tourist_spot
        itinerary_generator.nova_client.query_mbti_tourist_spots = AsyncMock(
            return_value=[mock_query_result]
        )
        
        # Mock session assignments
        assignment_result = AssignmentResult(
            tourist_spot=sample_tourist_spot,
            mbti_match=True
        )
        itinerary_generator.session_assigner.assign_morning_session.return_value = assignment_result
        itinerary_generator.session_assigner.assign_afternoon_session.return_value = assignment_result
        itinerary_generator.session_assigner.assign_night_session.return_value = assignment_result
        
        # Mock MCP client
        itinerary_generator.mcp_client.search_restaurants = AsyncMock(
            return_value=[sample_restaurant]
        )
        itinerary_generator.mcp_client.get_restaurant_recommendations = AsyncMock(
            return_value={'recommendation': sample_restaurant}
        )
        
        # Mock validator with failures
        validation_report = ValidationReport(
            is_valid=False,
            total_issues=2,
            error_count=1,
            warning_count=1,
            info_count=0,
            issues=[],
            validation_timestamp=datetime.now().isoformat(),
            validation_summary={},
            correction_suggestions=[]
        )
        itinerary_generator.validator.validate_complete_itinerary.return_value = validation_report
        
        # Execute test
        result = await itinerary_generator.generate_complete_itinerary("INFJ")
        
        # Should still succeed but with validation issues
        assert result.success is True
        assert result.validation_report.is_valid is False
        assert result.validation_report.error_count == 1
    
    def test_validate_mbti_format(self, itinerary_generator):
        """Test MBTI format validation."""
        # Valid formats
        assert itinerary_generator._validate_mbti_format("INFJ") is True
        assert itinerary_generator._validate_mbti_format("enfp") is True
        assert itinerary_generator._validate_mbti_format("INTJ") is True
        
        # Invalid formats
        assert itinerary_generator._validate_mbti_format("") is False
        assert itinerary_generator._validate_mbti_format("INF") is False
        assert itinerary_generator._validate_mbti_format("INFJA") is False
        assert itinerary_generator._validate_mbti_format("XXXX") is False
        assert itinerary_generator._validate_mbti_format(None) is False
    
    @pytest.mark.asyncio
    async def test_assign_meal_restaurant_success(
        self, 
        itinerary_generator,
        sample_restaurant
    ):
        """Test successful meal restaurant assignment."""
        # Mock MCP client
        itinerary_generator.mcp_client.search_restaurants = AsyncMock(
            return_value=[sample_restaurant]
        )
        itinerary_generator.mcp_client.get_restaurant_recommendations = AsyncMock(
            return_value={'recommendation': sample_restaurant}
        )
        
        # Execute test
        result = await itinerary_generator._assign_meal_restaurant(
            "breakfast", "Central", set()
        )
        
        # Assertions
        assert result is not None
        assert result.id == sample_restaurant.id
        assert result.name == sample_restaurant.name
    
    @pytest.mark.asyncio
    async def test_assign_meal_restaurant_no_results(self, itinerary_generator):
        """Test meal restaurant assignment with no results."""
        # Mock MCP client to return empty results
        itinerary_generator.mcp_client.search_restaurants = AsyncMock(
            return_value=[]
        )
        
        # Execute test
        result = await itinerary_generator._assign_meal_restaurant(
            "breakfast", "Central", set()
        )
        
        # Should return None when no restaurants found
        assert result is None
    
    @pytest.mark.asyncio
    async def test_assign_meal_restaurant_with_used_restaurants(
        self, 
        itinerary_generator,
        sample_restaurant
    ):
        """Test meal restaurant assignment with already used restaurants."""
        # Mock MCP client
        itinerary_generator.mcp_client.search_restaurants = AsyncMock(
            return_value=[sample_restaurant]
        )
        
        # Execute test with restaurant already used
        used_restaurants = {sample_restaurant.id}
        result = await itinerary_generator._assign_meal_restaurant(
            "breakfast", "Central", used_restaurants
        )
        
        # Should still return the restaurant as fallback
        assert result is not None
        assert result.id == sample_restaurant.id
    
    def test_generation_statistics(self, itinerary_generator):
        """Test generation statistics tracking."""
        # Initial statistics
        stats = itinerary_generator.get_generation_statistics()
        assert stats['total_generations'] == 0
        assert stats['successful_generations'] == 0
        assert stats['failed_generations'] == 0
        assert stats['success_rate'] == 0
        
        # Update statistics manually for testing
        itinerary_generator.total_generations = 10
        itinerary_generator.successful_generations = 8
        itinerary_generator.failed_generations = 2
        
        stats = itinerary_generator.get_generation_statistics()
        assert stats['total_generations'] == 10
        assert stats['successful_generations'] == 8
        assert stats['failed_generations'] == 2
        assert stats['success_rate'] == 0.8


if __name__ == "__main__":
    pytest.main([__file__])