"""
Tests for tool metadata service.

This module contains comprehensive tests for the ToolMetadataService class,
ensuring accurate metadata generation and proper functionality.
"""

import pytest
from datetime import datetime
from services.tool_metadata_service import ToolMetadataService, tool_metadata_service
from models.tool_metadata_models import (
    ToolsMetadataResponse,
    ToolMetadata,
    ToolCategory,
    MBTIPersonalityType,
    ParameterType
)


class TestToolMetadataService:
    """Test cases for ToolMetadataService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ToolMetadataService()
    
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service.version == "1.0.0"
        assert self.service._metadata_cache is None
        assert self.service._last_generated is None
    
    def test_get_all_tools_metadata(self):
        """Test getting all tools metadata."""
        metadata = self.service.get_all_tools_metadata()
        
        # Verify response structure
        assert isinstance(metadata, ToolsMetadataResponse)
        assert metadata.total_tools == 5
        assert len(metadata.tools) == 5
        assert len(metadata.categories) == 3
        assert ToolCategory.SEARCH in metadata.categories
        assert ToolCategory.ANALYSIS in metadata.categories
        assert ToolCategory.RECOMMENDATION in metadata.categories
        
        # Verify MBTI types
        assert len(metadata.supported_mbti_types) == 16
        assert MBTIPersonalityType.ENFP in metadata.supported_mbti_types
        assert MBTIPersonalityType.INTJ in metadata.supported_mbti_types
        
        # Verify version and timestamp
        assert metadata.version == "1.0.0"
        assert metadata.last_updated is not None
        
        # Verify tool names
        tool_names = [tool.name for tool in metadata.tools]
        expected_names = [
            "search_restaurants_by_district",
            "search_restaurants_by_meal_type",
            "search_restaurants_combined",
            "recommend_restaurants",
            "analyze_restaurant_sentiment"
        ]
        assert all(name in tool_names for name in expected_names)
    
    def test_metadata_caching(self):
        """Test metadata caching functionality."""
        # First call should generate metadata
        metadata1 = self.service.get_all_tools_metadata()
        assert self.service._metadata_cache is not None
        assert self.service._last_generated is not None
        
        # Second call should use cache
        metadata2 = self.service.get_all_tools_metadata()
        assert metadata1 is metadata2  # Same object reference
    
    def test_get_tool_metadata_valid_tool(self):
        """Test getting metadata for a valid tool."""
        tool_metadata = self.service.get_tool_metadata("search_restaurants_by_district")
        
        assert isinstance(tool_metadata, ToolMetadata)
        assert tool_metadata.name == "search_restaurants_by_district"
        assert tool_metadata.display_name == "Search Restaurants by District"
        assert tool_metadata.category == ToolCategory.SEARCH
        assert tool_metadata.endpoint == "/api/v1/restaurants/search/district"
        assert tool_metadata.http_method == "POST"
        assert tool_metadata.authentication_required is True
    
    def test_get_tool_metadata_invalid_tool(self):
        """Test getting metadata for an invalid tool."""
        with pytest.raises(ValueError, match="Tool 'invalid_tool' not found"):
            self.service.get_tool_metadata("invalid_tool")
    
    def test_district_search_metadata_structure(self):
        """Test district search tool metadata structure."""
        tool = self.service.get_tool_metadata("search_restaurants_by_district")
        
        # Verify parameters
        assert "districts" in tool.parameters
        districts_param = tool.parameters["districts"]
        assert districts_param.type == ParameterType.ARRAY
        assert districts_param.required is True
        assert districts_param.min_items == 1
        assert districts_param.max_items == 20
        
        # Verify response schema
        assert tool.response_schema.type == ParameterType.OBJECT
        assert "success" in tool.response_schema.properties
        assert "restaurants" in tool.response_schema.properties
        
        # Verify use cases
        assert len(tool.use_cases) >= 3
        assert any("tourist" in case.scenario.lower() for case in tool.use_cases)
        
        # Verify MBTI integration
        assert len(tool.mbti_integration) >= 3
        mbti_types = [guidance.personality_type for guidance in tool.mbti_integration]
        assert MBTIPersonalityType.ENFP in mbti_types
        assert MBTIPersonalityType.INTJ in mbti_types
        
        # Verify examples
        assert len(tool.examples) >= 1
        assert all(example.input and example.output for example in tool.examples)
    
    def test_meal_type_search_metadata_structure(self):
        """Test meal type search tool metadata structure."""
        tool = self.service.get_tool_metadata("search_restaurants_by_meal_type")
        
        # Verify parameters
        assert "meal_types" in tool.parameters
        meal_types_param = tool.parameters["meal_types"]
        assert meal_types_param.type == ParameterType.ARRAY
        assert meal_types_param.required is True
        assert meal_types_param.enum == ["breakfast", "lunch", "dinner"]
        assert meal_types_param.min_items == 1
        assert meal_types_param.max_items == 3
        
        # Verify endpoint
        assert tool.endpoint == "/api/v1/restaurants/search/meal-type"
        assert tool.category == ToolCategory.SEARCH
    
    def test_combined_search_metadata_structure(self):
        """Test combined search tool metadata structure."""
        tool = self.service.get_tool_metadata("search_restaurants_combined")
        
        # Verify parameters (both optional)
        assert "districts" in tool.parameters
        assert "meal_types" in tool.parameters
        assert tool.parameters["districts"].required is False
        assert tool.parameters["meal_types"].required is False
        
        # Verify endpoint
        assert tool.endpoint == "/api/v1/restaurants/search/combined"
        assert tool.category == ToolCategory.SEARCH
    
    def test_recommendation_metadata_structure(self):
        """Test recommendation tool metadata structure."""
        tool = self.service.get_tool_metadata("recommend_restaurants")
        
        # Verify parameters
        assert "restaurants" in tool.parameters
        assert "ranking_method" in tool.parameters
        
        restaurants_param = tool.parameters["restaurants"]
        assert restaurants_param.type == ParameterType.ARRAY
        assert restaurants_param.required is True
        assert restaurants_param.min_items == 1
        
        ranking_param = tool.parameters["ranking_method"]
        assert ranking_param.type == ParameterType.STRING
        assert ranking_param.required is False
        assert ranking_param.default == "sentiment_likes"
        assert ranking_param.enum == ["sentiment_likes", "combined_sentiment"]
        
        # Verify category and endpoint
        assert tool.category == ToolCategory.RECOMMENDATION
        assert tool.endpoint == "/api/v1/restaurants/recommend"
    
    def test_sentiment_analysis_metadata_structure(self):
        """Test sentiment analysis tool metadata structure."""
        tool = self.service.get_tool_metadata("analyze_restaurant_sentiment")
        
        # Verify parameters
        assert "restaurants" in tool.parameters
        restaurants_param = tool.parameters["restaurants"]
        assert restaurants_param.type == ParameterType.ARRAY
        assert restaurants_param.required is True
        assert restaurants_param.min_items == 1
        
        # Verify category and endpoint
        assert tool.category == ToolCategory.ANALYSIS
        assert tool.endpoint == "/api/v1/restaurants/analyze"
    
    def test_all_tools_have_required_fields(self):
        """Test that all tools have required metadata fields."""
        metadata = self.service.get_all_tools_metadata()
        
        for tool in metadata.tools:
            # Required string fields
            assert tool.name
            assert tool.display_name
            assert tool.description
            assert tool.purpose
            assert tool.endpoint
            assert tool.http_method
            
            # Required structured fields
            assert tool.category in [ToolCategory.SEARCH, ToolCategory.ANALYSIS, ToolCategory.RECOMMENDATION]
            assert isinstance(tool.parameters, dict)
            assert tool.response_schema is not None
            assert isinstance(tool.use_cases, list) and len(tool.use_cases) > 0
            assert isinstance(tool.mbti_integration, list) and len(tool.mbti_integration) > 0
            assert isinstance(tool.examples, list) and len(tool.examples) > 0
            
            # Authentication and performance fields
            assert isinstance(tool.authentication_required, bool)
            if tool.rate_limit:
                assert isinstance(tool.rate_limit, str)
            if tool.average_response_time_ms:
                assert isinstance(tool.average_response_time_ms, float)
            if tool.success_rate_percentage:
                assert isinstance(tool.success_rate_percentage, float)
    
    def test_mbti_integration_completeness(self):
        """Test that MBTI integration guidance is comprehensive."""
        metadata = self.service.get_all_tools_metadata()
        
        for tool in metadata.tools:
            for mbti_guidance in tool.mbti_integration:
                assert mbti_guidance.personality_type in MBTIPersonalityType
                assert isinstance(mbti_guidance.preferences, list) and len(mbti_guidance.preferences) > 0
                assert isinstance(mbti_guidance.search_patterns, list) and len(mbti_guidance.search_patterns) > 0
                assert mbti_guidance.recommendation_focus
    
    def test_use_cases_completeness(self):
        """Test that use cases are comprehensive and well-structured."""
        metadata = self.service.get_all_tools_metadata()
        
        for tool in metadata.tools:
            for use_case in tool.use_cases:
                assert use_case.scenario
                assert use_case.when_to_use
                assert isinstance(use_case.example_input, dict)
                assert use_case.expected_outcome
    
    def test_examples_completeness(self):
        """Test that examples are comprehensive and valid."""
        metadata = self.service.get_all_tools_metadata()
        
        for tool in metadata.tools:
            for example in tool.examples:
                assert example.title
                assert example.description
                assert isinstance(example.input, dict)
                assert isinstance(example.output, dict)
                # Notes are optional
    
    def test_parameter_schemas_validity(self):
        """Test that parameter schemas are valid and complete."""
        metadata = self.service.get_all_tools_metadata()
        
        for tool in metadata.tools:
            for param_name, param_schema in tool.parameters.items():
                assert param_schema.type in ParameterType
                assert param_schema.description
                assert isinstance(param_schema.required, bool)
                
                # Validate array parameters
                if param_schema.type == ParameterType.ARRAY:
                    if param_schema.min_items is not None:
                        assert param_schema.min_items >= 0
                    if param_schema.max_items is not None:
                        assert param_schema.max_items > 0
                        if param_schema.min_items is not None:
                            assert param_schema.max_items >= param_schema.min_items
                
                # Validate enum parameters
                if param_schema.enum:
                    assert isinstance(param_schema.enum, list)
                    assert len(param_schema.enum) > 0
    
    def test_response_schemas_validity(self):
        """Test that response schemas are valid and complete."""
        metadata = self.service.get_all_tools_metadata()
        
        for tool in metadata.tools:
            response_schema = tool.response_schema
            assert response_schema.type in ParameterType
            assert response_schema.description
            
            if response_schema.properties:
                assert isinstance(response_schema.properties, dict)
                for prop_name, prop_schema in response_schema.properties.items():
                    assert prop_schema.type in ParameterType
                    assert prop_schema.description
    
    def test_performance_metrics_validity(self):
        """Test that performance metrics are valid when present."""
        metadata = self.service.get_all_tools_metadata()
        
        for tool in metadata.tools:
            if tool.average_response_time_ms is not None:
                assert tool.average_response_time_ms > 0
                assert tool.average_response_time_ms < 10000  # Reasonable upper bound
            
            if tool.success_rate_percentage is not None:
                assert 0 <= tool.success_rate_percentage <= 100
    
    def test_global_service_instance(self):
        """Test that global service instance works correctly."""
        metadata = tool_metadata_service.get_all_tools_metadata()
        assert isinstance(metadata, ToolsMetadataResponse)
        assert metadata.total_tools == 5
    
    def test_cache_expiration_simulation(self):
        """Test cache expiration behavior (simulated)."""
        # Get initial metadata
        metadata1 = self.service.get_all_tools_metadata()
        initial_cache = self.service._metadata_cache
        
        # Simulate cache expiration by clearing it
        self.service._metadata_cache = None
        self.service._last_generated = None
        
        # Get metadata again (should regenerate)
        metadata2 = self.service.get_all_tools_metadata()
        
        # Should be different objects but same content
        assert metadata1 is not metadata2
        assert metadata1.total_tools == metadata2.total_tools
        assert len(metadata1.tools) == len(metadata2.tools)


class TestToolMetadataServiceIntegration:
    """Integration tests for tool metadata service."""
    
    def test_metadata_consistency_across_calls(self):
        """Test that metadata is consistent across multiple calls."""
        service = ToolMetadataService()
        
        # Get metadata multiple times
        metadata_calls = [service.get_all_tools_metadata() for _ in range(3)]
        
        # All should be the same object (cached)
        assert all(metadata is metadata_calls[0] for metadata in metadata_calls[1:])
    
    def test_individual_tool_metadata_matches_all_tools(self):
        """Test that individual tool metadata matches the all-tools response."""
        service = ToolMetadataService()
        
        all_metadata = service.get_all_tools_metadata()
        
        for tool in all_metadata.tools:
            individual_metadata = service.get_tool_metadata(tool.name)
            
            # Should be equivalent (but may be different objects)
            assert individual_metadata.name == tool.name
            assert individual_metadata.display_name == tool.display_name
            assert individual_metadata.category == tool.category
            assert individual_metadata.endpoint == tool.endpoint
            assert individual_metadata.http_method == tool.http_method
    
    def test_all_expected_tools_present(self):
        """Test that all expected tools are present in metadata."""
        service = ToolMetadataService()
        metadata = service.get_all_tools_metadata()
        
        expected_tools = {
            "search_restaurants_by_district": ToolCategory.SEARCH,
            "search_restaurants_by_meal_type": ToolCategory.SEARCH,
            "search_restaurants_combined": ToolCategory.SEARCH,
            "recommend_restaurants": ToolCategory.RECOMMENDATION,
            "analyze_restaurant_sentiment": ToolCategory.ANALYSIS
        }
        
        actual_tools = {tool.name: tool.category for tool in metadata.tools}
        
        assert actual_tools == expected_tools
    
    def test_metadata_json_serialization(self):
        """Test that metadata can be properly JSON serialized."""
        service = ToolMetadataService()
        metadata = service.get_all_tools_metadata()
        
        # Should be able to convert to dict (JSON serializable)
        metadata_dict = metadata.model_dump()
        assert isinstance(metadata_dict, dict)
        assert "tools" in metadata_dict
        assert "total_tools" in metadata_dict
        assert "version" in metadata_dict
        
        # Should be able to recreate from dict
        recreated_metadata = ToolsMetadataResponse(**metadata_dict)
        assert recreated_metadata.total_tools == metadata.total_tools
        assert len(recreated_metadata.tools) == len(metadata.tools)