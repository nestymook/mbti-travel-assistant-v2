"""
Unit tests for tool metadata models.

This module contains comprehensive tests for tool metadata models used
for foundation model integration and tool discovery.
"""

import pytest
from pydantic import ValidationError
from typing import List, Dict, Any

from models.tool_metadata_models import (
    ParameterType,
    ToolCategory,
    MBTIPersonalityType,
    ParameterSchema,
    ResponseSchema,
    UseCaseScenario,
    MBTIIntegrationGuidance,
    ToolExample,
    ToolMetadata,
    ToolsMetadataResponse
)


class TestParameterTypeEnum:
    """Test ParameterType enum."""
    
    def test_valid_parameter_types(self):
        """Test valid parameter type values."""
        assert ParameterType.STRING == "string"
        assert ParameterType.INTEGER == "integer"
        assert ParameterType.NUMBER == "number"
        assert ParameterType.BOOLEAN == "boolean"
        assert ParameterType.ARRAY == "array"
        assert ParameterType.OBJECT == "object"


class TestToolCategoryEnum:
    """Test ToolCategory enum."""
    
    def test_valid_tool_categories(self):
        """Test valid tool category values."""
        assert ToolCategory.SEARCH == "search"
        assert ToolCategory.ANALYSIS == "analysis"
        assert ToolCategory.RECOMMENDATION == "recommendation"


class TestMBTIPersonalityTypeEnum:
    """Test MBTIPersonalityType enum."""
    
    def test_valid_mbti_types(self):
        """Test valid MBTI personality type values."""
        assert MBTIPersonalityType.ENFJ == "ENFJ"
        assert MBTIPersonalityType.ENFP == "ENFP"
        assert MBTIPersonalityType.INTJ == "INTJ"
        assert MBTIPersonalityType.ISFP == "ISFP"
    
    def test_all_mbti_types_present(self):
        """Test that all 16 MBTI types are present."""
        mbti_types = list(MBTIPersonalityType)
        assert len(mbti_types) == 16
        
        # Test a few key ones
        assert MBTIPersonalityType.ENFP in mbti_types
        assert MBTIPersonalityType.INTJ in mbti_types
        assert MBTIPersonalityType.ESFJ in mbti_types
        assert MBTIPersonalityType.ISTP in mbti_types


class TestParameterSchema:
    """Test ParameterSchema model."""
    
    def test_valid_parameter_schema(self):
        """Test valid parameter schema."""
        schema = ParameterSchema(
            type=ParameterType.ARRAY,
            description="List of Hong Kong districts to search",
            required=True,
            min_items=1,
            max_items=20,
            example=["Central district", "Admiralty"]
        )
        
        assert schema.type == ParameterType.ARRAY
        assert schema.description == "List of Hong Kong districts to search"
        assert schema.required is True
        assert schema.min_items == 1
        assert schema.max_items == 20
        assert schema.example == ["Central district", "Admiralty"]
    
    def test_minimal_parameter_schema(self):
        """Test parameter schema with only required fields."""
        schema = ParameterSchema(
            type=ParameterType.STRING,
            description="A string parameter"
        )
        
        assert schema.type == ParameterType.STRING
        assert schema.description == "A string parameter"
        assert schema.required is False  # Default value
        assert schema.default is None
    
    def test_enum_parameter_schema(self):
        """Test parameter schema with enum values."""
        schema = ParameterSchema(
            type=ParameterType.STRING,
            description="Meal type selection",
            required=True,
            enum=["breakfast", "lunch", "dinner"],
            example="lunch"
        )
        
        assert schema.enum == ["breakfast", "lunch", "dinner"]
        assert schema.example == "lunch"
    
    def test_string_pattern_parameter(self):
        """Test parameter schema with regex pattern."""
        schema = ParameterSchema(
            type=ParameterType.STRING,
            description="Restaurant ID",
            required=True,
            pattern=r"^rest_\d{3}$",
            example="rest_001"
        )
        
        assert schema.pattern == r"^rest_\d{3}$"
        assert schema.example == "rest_001"


class TestResponseSchema:
    """Test ResponseSchema model."""
    
    def test_valid_response_schema(self):
        """Test valid response schema."""
        schema = ResponseSchema(
            type=ParameterType.OBJECT,
            description="Restaurant search results",
            example={"restaurants": [], "metadata": {}}
        )
        
        assert schema.type == ParameterType.OBJECT
        assert schema.description == "Restaurant search results"
        assert schema.example == {"restaurants": [], "metadata": {}}
    
    def test_array_response_schema(self):
        """Test response schema for array type."""
        item_schema = ResponseSchema(
            type=ParameterType.OBJECT,
            description="Individual restaurant"
        )
        
        schema = ResponseSchema(
            type=ParameterType.ARRAY,
            description="List of restaurants",
            items=item_schema
        )
        
        assert schema.type == ParameterType.ARRAY
        assert schema.items is not None
        assert schema.items.type == ParameterType.OBJECT
    
    def test_object_response_schema_with_properties(self):
        """Test response schema with object properties."""
        properties = {
            "restaurants": ParameterSchema(
                type=ParameterType.ARRAY,
                description="List of matching restaurants"
            ),
            "metadata": ParameterSchema(
                type=ParameterType.OBJECT,
                description="Search metadata"
            )
        }
        
        schema = ResponseSchema(
            type=ParameterType.OBJECT,
            description="Search response",
            properties=properties
        )
        
        assert schema.properties is not None
        assert len(schema.properties) == 2
        assert "restaurants" in schema.properties
        assert "metadata" in schema.properties


class TestUseCaseScenario:
    """Test UseCaseScenario model."""
    
    def test_valid_use_case_scenario(self):
        """Test valid use case scenario."""
        scenario = UseCaseScenario(
            scenario="Tourist looking for breakfast options in Central",
            when_to_use="When user wants restaurants in specific districts for specific meal times",
            example_input={
                "districts": ["Central district"],
                "meal_types": ["breakfast"]
            },
            expected_outcome="List of restaurants in Central district that serve breakfast"
        )
        
        assert scenario.scenario == "Tourist looking for breakfast options in Central"
        assert "specific districts" in scenario.when_to_use
        assert scenario.example_input["districts"] == ["Central district"]
        assert "breakfast" in scenario.expected_outcome
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            UseCaseScenario(
                scenario="Test scenario"
                # Missing other required fields
            )
        
        errors = exc_info.value.errors()
        assert len(errors) >= 3  # Missing when_to_use, example_input, expected_outcome


class TestMBTIIntegrationGuidance:
    """Test MBTIIntegrationGuidance model."""
    
    def test_valid_mbti_integration_guidance(self):
        """Test valid MBTI integration guidance."""
        guidance = MBTIIntegrationGuidance(
            personality_type=MBTIPersonalityType.ENFP,
            preferences=["Variety", "Social atmosphere", "Unique experiences"],
            search_patterns=["Multiple districts", "All meal types", "High sentiment scores"],
            recommendation_focus="Restaurants with high social engagement and positive reviews"
        )
        
        assert guidance.personality_type == MBTIPersonalityType.ENFP
        assert len(guidance.preferences) == 3
        assert "Variety" in guidance.preferences
        assert len(guidance.search_patterns) == 3
        assert "social engagement" in guidance.recommendation_focus
    
    def test_different_personality_types(self):
        """Test guidance for different personality types."""
        intj_guidance = MBTIIntegrationGuidance(
            personality_type=MBTIPersonalityType.INTJ,
            preferences=["Efficiency", "Quality", "Privacy"],
            search_patterns=["Specific criteria", "High ratings", "Detailed analysis"],
            recommendation_focus="High-quality restaurants with excellent reviews"
        )
        
        esfj_guidance = MBTIIntegrationGuidance(
            personality_type=MBTIPersonalityType.ESFJ,
            preferences=["Social dining", "Popular places", "Group-friendly"],
            search_patterns=["Popular districts", "Social atmosphere", "Group dining"],
            recommendation_focus="Popular restaurants suitable for group dining"
        )
        
        assert intj_guidance.personality_type == MBTIPersonalityType.INTJ
        assert esfj_guidance.personality_type == MBTIPersonalityType.ESFJ
        assert "Efficiency" in intj_guidance.preferences
        assert "Social dining" in esfj_guidance.preferences


class TestToolExample:
    """Test ToolExample model."""
    
    def test_valid_tool_example(self):
        """Test valid tool example."""
        example = ToolExample(
            title="Search restaurants in Central for lunch",
            description="Find lunch restaurants in Central district",
            input={
                "districts": ["Central district"],
                "meal_types": ["lunch"]
            },
            output={
                "success": True,
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Central Lunch Spot",
                        "district": "Central district"
                    }
                ]
            },
            notes="This example shows combined search functionality"
        )
        
        assert example.title == "Search restaurants in Central for lunch"
        assert "Central district" in example.description
        assert example.input["districts"] == ["Central district"]
        assert example.output["success"] is True
        assert example.notes == "This example shows combined search functionality"
    
    def test_example_without_notes(self):
        """Test tool example without optional notes field."""
        example = ToolExample(
            title="Basic search example",
            description="Simple restaurant search",
            input={"districts": ["Central district"]},
            output={"success": True, "restaurants": []}
        )
        
        assert example.title == "Basic search example"
        assert example.notes is None
    
    def test_complex_input_output(self):
        """Test tool example with complex input/output structures."""
        example = ToolExample(
            title="Complex recommendation example",
            description="Restaurant recommendation with multiple criteria",
            input={
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Restaurant A",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                    }
                ],
                "ranking_method": "sentiment_likes"
            },
            output={
                "success": True,
                "recommendation": {
                    "id": "rest_001",
                    "name": "Restaurant A"
                },
                "candidates": [],
                "analysis_summary": {
                    "restaurant_count": 1,
                    "average_likes": 85.0
                }
            }
        )
        
        assert len(example.input["restaurants"]) == 1
        assert example.output["recommendation"]["id"] == "rest_001"


class TestToolMetadata:
    """Test ToolMetadata model."""
    
    def test_valid_tool_metadata(self):
        """Test valid tool metadata."""
        parameter_schema = ParameterSchema(
            type=ParameterType.ARRAY,
            description="List of districts",
            required=True,
            example=["Central district"]
        )
        
        response_schema = ResponseSchema(
            type=ParameterType.OBJECT,
            description="Search results"
        )
        
        use_case = UseCaseScenario(
            scenario="District search",
            when_to_use="When searching by district",
            example_input={"districts": ["Central district"]},
            expected_outcome="List of restaurants"
        )
        
        mbti_guidance = MBTIIntegrationGuidance(
            personality_type=MBTIPersonalityType.ENFP,
            preferences=["Variety"],
            search_patterns=["Multiple districts"],
            recommendation_focus="Diverse options"
        )
        
        example = ToolExample(
            title="Example usage",
            description="How to use this tool",
            input={"districts": ["Central district"]},
            output={"success": True}
        )
        
        metadata = ToolMetadata(
            name="search_restaurants_by_district",
            display_name="Search Restaurants by District",
            category=ToolCategory.SEARCH,
            description="Search for restaurants in specific Hong Kong districts",
            purpose="Find restaurants located in one or more specified districts",
            parameters={"districts": parameter_schema},
            response_schema=response_schema,
            use_cases=[use_case],
            mbti_integration=[mbti_guidance],
            examples=[example],
            endpoint="/api/v1/restaurants/search/district",
            http_method="POST",
            authentication_required=True
        )
        
        assert metadata.name == "search_restaurants_by_district"
        assert metadata.display_name == "Search Restaurants by District"
        assert metadata.category == ToolCategory.SEARCH
        assert metadata.authentication_required is True
        assert len(metadata.parameters) == 1
        assert "districts" in metadata.parameters
        assert len(metadata.use_cases) == 1
        assert len(metadata.mbti_integration) == 1
        assert len(metadata.examples) == 1
    
    def test_tool_metadata_with_optional_fields(self):
        """Test tool metadata with optional performance fields."""
        parameter_schema = ParameterSchema(
            type=ParameterType.STRING,
            description="Query parameter",
            required=True
        )
        
        response_schema = ResponseSchema(
            type=ParameterType.OBJECT,
            description="Results"
        )
        
        metadata = ToolMetadata(
            name="test_tool",
            display_name="Test Tool",
            category=ToolCategory.ANALYSIS,
            description="Test tool description",
            purpose="Testing purposes",
            parameters={"query": parameter_schema},
            response_schema=response_schema,
            use_cases=[],
            mbti_integration=[],
            examples=[],
            endpoint="/api/v1/test",
            http_method="GET",
            authentication_required=False,
            rate_limit="100 requests per minute",
            average_response_time_ms=250.5,
            success_rate_percentage=99.5
        )
        
        assert metadata.authentication_required is False
        assert metadata.rate_limit == "100 requests per minute"
        assert metadata.average_response_time_ms == 250.5
        assert metadata.success_rate_percentage == 99.5
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ToolMetadata(
                name="test_tool",
                display_name="Test Tool"
                # Missing many required fields
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        missing_fields = [error["loc"][0] for error in errors if error["type"] == "missing"]
        assert "category" in missing_fields
        assert "description" in missing_fields


class TestToolsMetadataResponse:
    """Test ToolsMetadataResponse model."""
    
    def test_valid_tools_metadata_response(self):
        """Test valid tools metadata response."""
        # Create a minimal tool metadata for testing
        parameter_schema = ParameterSchema(
            type=ParameterType.STRING,
            description="Test parameter",
            required=True
        )
        
        response_schema = ResponseSchema(
            type=ParameterType.OBJECT,
            description="Test response"
        )
        
        tool_metadata = ToolMetadata(
            name="test_tool",
            display_name="Test Tool",
            category=ToolCategory.SEARCH,
            description="Test tool",
            purpose="Testing",
            parameters={"test": parameter_schema},
            response_schema=response_schema,
            use_cases=[],
            mbti_integration=[],
            examples=[],
            endpoint="/api/v1/test",
            http_method="GET"
        )
        
        response = ToolsMetadataResponse(
            tools=[tool_metadata],
            total_tools=1,
            categories=[ToolCategory.SEARCH, ToolCategory.ANALYSIS],
            supported_mbti_types=[MBTIPersonalityType.ENFP, MBTIPersonalityType.INTJ],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        
        assert len(response.tools) == 1
        assert response.total_tools == 1
        assert len(response.categories) == 2
        assert ToolCategory.SEARCH in response.categories
        assert len(response.supported_mbti_types) == 2
        assert MBTIPersonalityType.ENFP in response.supported_mbti_types
        assert response.version == "1.0.0"
        assert response.last_updated == "2025-01-03T10:30:00Z"
    
    def test_empty_tools_metadata_response(self):
        """Test tools metadata response with no tools."""
        response = ToolsMetadataResponse(
            tools=[],
            total_tools=0,
            categories=[],
            supported_mbti_types=[],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        
        assert len(response.tools) == 0
        assert response.total_tools == 0
        assert len(response.categories) == 0
        assert len(response.supported_mbti_types) == 0
    
    def test_comprehensive_tools_metadata_response(self):
        """Test tools metadata response with all tool categories and MBTI types."""
        response = ToolsMetadataResponse(
            tools=[],  # Empty for this test
            total_tools=5,
            categories=list(ToolCategory),  # All categories
            supported_mbti_types=list(MBTIPersonalityType),  # All MBTI types
            version="2.0.0",
            last_updated="2025-01-03T15:45:00Z"
        )
        
        assert response.total_tools == 5
        assert len(response.categories) == 3  # search, analysis, recommendation
        assert len(response.supported_mbti_types) == 16  # All 16 MBTI types
        assert ToolCategory.SEARCH in response.categories
        assert ToolCategory.ANALYSIS in response.categories
        assert ToolCategory.RECOMMENDATION in response.categories


# Integration tests for model serialization
class TestToolMetadataModelSerialization:
    """Test tool metadata model serialization and deserialization."""
    
    def test_parameter_schema_serialization(self):
        """Test ParameterSchema serialization."""
        schema = ParameterSchema(
            type=ParameterType.ARRAY,
            description="List of districts",
            required=True,
            min_items=1,
            max_items=20,
            example=["Central district", "Admiralty"]
        )
        
        # Test dict conversion
        schema_dict = schema.dict()
        assert schema_dict["type"] == "array"
        assert schema_dict["required"] is True
        assert schema_dict["example"] == ["Central district", "Admiralty"]
        
        # Test JSON conversion
        schema_json = schema.json()
        assert "array" in schema_json
        assert "Central district" in schema_json
    
    def test_tool_metadata_serialization(self):
        """Test ToolMetadata serialization."""
        parameter_schema = ParameterSchema(
            type=ParameterType.STRING,
            description="Test parameter",
            required=True
        )
        
        response_schema = ResponseSchema(
            type=ParameterType.OBJECT,
            description="Test response"
        )
        
        use_case = UseCaseScenario(
            scenario="Test scenario",
            when_to_use="For testing",
            example_input={"test": "value"},
            expected_outcome="Test result"
        )
        
        metadata = ToolMetadata(
            name="test_tool",
            display_name="Test Tool",
            category=ToolCategory.SEARCH,
            description="Test tool",
            purpose="Testing",
            parameters={"test": parameter_schema},
            response_schema=response_schema,
            use_cases=[use_case],
            mbti_integration=[],
            examples=[],
            endpoint="/api/v1/test",
            http_method="GET"
        )
        
        # Test dict conversion
        metadata_dict = metadata.dict()
        assert metadata_dict["name"] == "test_tool"
        assert metadata_dict["category"] == "search"
        assert len(metadata_dict["parameters"]) == 1
        assert len(metadata_dict["use_cases"]) == 1
        
        # Test JSON conversion
        metadata_json = metadata.json()
        assert "test_tool" in metadata_json
        assert "search" in metadata_json
    
    def test_tools_metadata_response_serialization(self):
        """Test ToolsMetadataResponse serialization."""
        response = ToolsMetadataResponse(
            tools=[],
            total_tools=0,
            categories=[ToolCategory.SEARCH],
            supported_mbti_types=[MBTIPersonalityType.ENFP],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        
        # Test dict conversion
        response_dict = response.dict()
        assert response_dict["total_tools"] == 0
        assert response_dict["categories"] == ["search"]
        assert response_dict["supported_mbti_types"] == ["ENFP"]
        
        # Test JSON conversion
        response_json = response.json()
        assert "total_tools" in response_json
        assert "search" in response_json
        assert "ENFP" in response_json