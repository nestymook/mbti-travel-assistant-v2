#!/usr/bin/env python3
"""
Integration test for tool metadata system.

This script tests the complete tool metadata system including service and API endpoints.
"""

import json
import sys
from services.tool_metadata_service import tool_metadata_service
from models.tool_metadata_models import ToolCategory, MBTIPersonalityType


def test_service_integration():
    """Test the tool metadata service integration."""
    print("Testing tool metadata service...")
    
    # Test getting all tools metadata
    metadata = tool_metadata_service.get_all_tools_metadata()
    print(f"✓ Retrieved metadata for {metadata.total_tools} tools")
    
    # Verify expected tools are present
    expected_tools = [
        "search_restaurants_by_district",
        "search_restaurants_by_meal_type",
        "search_restaurants_combined",
        "recommend_restaurants",
        "analyze_restaurant_sentiment"
    ]
    
    actual_tools = [tool.name for tool in metadata.tools]
    for expected_tool in expected_tools:
        if expected_tool in actual_tools:
            print(f"✓ Found expected tool: {expected_tool}")
        else:
            print(f"✗ Missing expected tool: {expected_tool}")
            return False
    
    # Test getting individual tool metadata
    for tool_name in expected_tools:
        try:
            tool = tool_metadata_service.get_tool_metadata(tool_name)
            print(f"✓ Retrieved individual metadata for: {tool.name}")
            
            # Verify required fields
            assert tool.name
            assert tool.display_name
            assert tool.description
            assert tool.purpose
            assert tool.endpoint
            assert tool.http_method
            assert tool.parameters
            assert tool.response_schema
            assert tool.use_cases
            assert tool.mbti_integration
            assert tool.examples
            
        except Exception as e:
            print(f"✗ Failed to get metadata for {tool_name}: {e}")
            return False
    
    # Test categories
    expected_categories = [ToolCategory.SEARCH, ToolCategory.ANALYSIS, ToolCategory.RECOMMENDATION]
    for category in expected_categories:
        if category in metadata.categories:
            print(f"✓ Found expected category: {category.value}")
        else:
            print(f"✗ Missing expected category: {category.value}")
            return False
    
    # Test MBTI types
    if len(metadata.supported_mbti_types) == 16:
        print(f"✓ All 16 MBTI types supported")
    else:
        print(f"✗ Expected 16 MBTI types, found {len(metadata.supported_mbti_types)}")
        return False
    
    print("✓ Service integration test passed!")
    return True


def test_metadata_completeness():
    """Test that metadata is comprehensive and well-structured."""
    print("\nTesting metadata completeness...")
    
    metadata = tool_metadata_service.get_all_tools_metadata()
    
    for tool in metadata.tools:
        print(f"\nValidating tool: {tool.name}")
        
        # Test parameter schemas
        for param_name, param_schema in tool.parameters.items():
            assert param_schema.type
            assert param_schema.description
            print(f"  ✓ Parameter {param_name}: {param_schema.type.value}")
        
        # Test use cases
        if len(tool.use_cases) >= 2:
            print(f"  ✓ Has {len(tool.use_cases)} use cases")
        else:
            print(f"  ✗ Insufficient use cases: {len(tool.use_cases)}")
            return False
        
        # Test MBTI integration
        if len(tool.mbti_integration) >= 2:
            print(f"  ✓ Has MBTI guidance for {len(tool.mbti_integration)} personality types")
        else:
            print(f"  ✗ Insufficient MBTI guidance: {len(tool.mbti_integration)}")
            return False
        
        # Test examples
        if len(tool.examples) >= 1:
            print(f"  ✓ Has {len(tool.examples)} examples")
        else:
            print(f"  ✗ No examples provided")
            return False
        
        # Test response schema
        assert tool.response_schema.type
        assert tool.response_schema.description
        print(f"  ✓ Response schema: {tool.response_schema.type.value}")
    
    print("✓ Metadata completeness test passed!")
    return True


def test_json_serialization():
    """Test that metadata can be properly JSON serialized."""
    print("\nTesting JSON serialization...")
    
    try:
        metadata = tool_metadata_service.get_all_tools_metadata()
        
        # Convert to dict (JSON serializable)
        metadata_dict = metadata.model_dump()
        
        # Serialize to JSON
        json_str = json.dumps(metadata_dict, indent=2)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        
        assert parsed["total_tools"] == metadata.total_tools
        assert len(parsed["tools"]) == len(metadata.tools)
        
        print(f"✓ Successfully serialized {len(json_str)} characters of JSON")
        print("✓ JSON serialization test passed!")
        return True
        
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        return False


def test_foundation_model_integration():
    """Test metadata features specifically for foundation model integration."""
    print("\nTesting foundation model integration features...")
    
    metadata = tool_metadata_service.get_all_tools_metadata()
    
    # Test that each tool has comprehensive information for AI models
    for tool in metadata.tools:
        print(f"\nValidating AI integration for: {tool.name}")
        
        # Check parameter validation schemas
        for param_name, param_schema in tool.parameters.items():
            if param_schema.type.value == "array":
                if param_schema.min_items is not None:
                    print(f"  ✓ Array parameter {param_name} has min_items: {param_schema.min_items}")
                if param_schema.enum:
                    print(f"  ✓ Parameter {param_name} has enum values: {param_schema.enum}")
        
        # Check use case scenarios
        for i, use_case in enumerate(tool.use_cases):
            assert use_case.scenario
            assert use_case.when_to_use
            assert use_case.example_input
            assert use_case.expected_outcome
            print(f"  ✓ Use case {i+1}: {use_case.scenario[:50]}...")
        
        # Check MBTI integration guidance
        mbti_types = [guidance.personality_type.value for guidance in tool.mbti_integration]
        print(f"  ✓ MBTI guidance for: {', '.join(mbti_types)}")
        
        # Check examples have proper structure
        for i, example in enumerate(tool.examples):
            assert example.title
            assert example.description
            assert isinstance(example.input, dict)
            assert isinstance(example.output, dict)
            print(f"  ✓ Example {i+1}: {example.title}")
    
    print("✓ Foundation model integration test passed!")
    return True


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("TOOL METADATA SYSTEM INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_service_integration,
        test_metadata_completeness,
        test_json_serialization,
        test_foundation_model_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("❌ Some integration tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())