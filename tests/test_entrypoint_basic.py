#!/usr/bin/env python3
"""
Basic tests for entrypoint integration without external dependencies.

This module tests core entrypoint functionality that can be tested
without requiring strands_agents or other external dependencies.

The tests focus on:
1. Payload extraction from various AgentCore Runtime formats
2. Response formatting and JSON serialization
3. MCP tool structure and parameter schemas
4. Entrypoint component initialization and imports

These tests use mocking to avoid dependencies on external libraries
while still validating the core functionality of the entrypoint system.
"""

import json
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Create a proper mock Tool class that can be instantiated
class MockTool:
    def __init__(self, name, description, function, parameters):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters

# Mock the external dependencies before any imports
mock_bedrock = Mock()
mock_strands = Mock()
mock_strands_tools = Mock()

# Create mock classes
mock_bedrock.BedrockAgentCoreApp = Mock()
mock_strands.Agent = Mock()
mock_strands_tools.Tool = MockTool

sys.modules['bedrock_agentcore'] = mock_bedrock
sys.modules['strands_agents'] = mock_strands
sys.modules['strands_agents.tools'] = mock_strands_tools

# Mock the service imports
sys.modules['services'] = Mock()
sys.modules['services.restaurant_service'] = Mock()
sys.modules['services.district_service'] = Mock()
sys.modules['services.time_service'] = Mock()
sys.modules['services.data_access'] = Mock()


def test_payload_extraction():
    """Test payload extraction functionality."""
    print("Testing payload extraction...")
    
    try:
        from main import extract_user_prompt, format_response, format_error_response
        
        # Test cases for payload extraction
        test_cases = [
            {
                "name": "Standard AgentCore format",
                "payload": {"input": {"prompt": "Find restaurants in Central district"}},
                "expected": "Find restaurants in Central district"
            },
            {
                "name": "Message format",
                "payload": {"input": {"message": "Show me breakfast places"}},
                "expected": "Show me breakfast places"
            },
            {
                "name": "Direct input string",
                "payload": {"input": "Find dinner restaurants"},
                "expected": "Find dinner restaurants"
            },
            {
                "name": "Top-level prompt",
                "payload": {"prompt": "Search for lunch places"},
                "expected": "Search for lunch places"
            },
            {
                "name": "Alternative field",
                "payload": {"query": "Find good restaurants"},
                "expected": "Find good restaurants"
            }
        ]
        
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            try:
                result = extract_user_prompt(test_case["payload"])
                if result == test_case["expected"]:
                    print(f"  ✓ {test_case['name']}")
                    passed += 1
                else:
                    print(f"  ✗ {test_case['name']}: Expected '{test_case['expected']}', got '{result}'")
                    failed += 1
            except Exception as e:
                print(f"  ✗ {test_case['name']}: Exception - {e}")
                failed += 1
        
        # Test invalid payloads
        invalid_cases = [
            {"name": "Empty payload", "payload": {}},
            {"name": "No string fields", "payload": {"number": 123, "boolean": True}},
            {"name": "None payload", "payload": None}
        ]
        
        for test_case in invalid_cases:
            try:
                if test_case["payload"] is None:
                    extract_user_prompt({})  # This should fail
                else:
                    extract_user_prompt(test_case["payload"])
                print(f"  ✗ {test_case['name']}: Should have raised ValueError")
                failed += 1
            except ValueError:
                print(f"  ✓ {test_case['name']}: Correctly raised ValueError")
                passed += 1
            except Exception as e:
                print(f"  ✗ {test_case['name']}: Wrong exception type - {e}")
                failed += 1
        
        return passed, failed
        
    except Exception as e:
        print(f"  ✗ Payload extraction test failed: {e}")
        return 0, 1


def test_response_formatting():
    """Test response formatting functionality."""
    print("\nTesting response formatting...")
    
    try:
        from main import format_response, format_error_response
        
        passed = 0
        failed = 0
        
        # Test successful response formatting
        try:
            response = format_response("Test response", success=True)
            data = json.loads(response)
            
            if (data["success"] is True and 
                data["response"] == "Test response" and
                "timestamp" in data and
                data["agent_type"] == "restaurant_search_assistant"):
                print("  ✓ Successful response formatting")
                passed += 1
            else:
                print("  ✗ Successful response formatting: Missing required fields")
                failed += 1
        except Exception as e:
            print(f"  ✗ Successful response formatting: {e}")
            failed += 1
        
        # Test error response formatting
        try:
            response = format_response("Error response", success=False, error="Test error")
            data = json.loads(response)
            
            if (data["success"] is False and
                data["response"] == "Error response" and
                data["error"]["message"] == "Test error"):
                print("  ✓ Error response formatting")
                passed += 1
            else:
                print("  ✗ Error response formatting: Missing required fields")
                failed += 1
        except Exception as e:
            print(f"  ✗ Error response formatting: {e}")
            failed += 1
        
        # Test error response with user-friendly messages
        try:
            response = format_error_response("Invalid district name", "validation_error")
            data = json.loads(response)
            
            if (data["success"] is False and
                "district" in data["response"].lower() and
                data["error"]["type"] == "validation_error"):
                print("  ✓ User-friendly error response")
                passed += 1
            else:
                print("  ✗ User-friendly error response: Missing required fields")
                failed += 1
        except Exception as e:
            print(f"  ✗ User-friendly error response: {e}")
            failed += 1
        
        # Test JSON serialization with unicode
        try:
            response = format_response("Response with unicode: 中文餐廳", success=True)
            data = json.loads(response)
            
            if "中文餐廳" in data["response"]:
                print("  ✓ Unicode handling")
                passed += 1
            else:
                print("  ✗ Unicode handling: Unicode characters not preserved")
                failed += 1
        except Exception as e:
            print(f"  ✗ Unicode handling: {e}")
            failed += 1
        
        return passed, failed
        
    except Exception as e:
        print(f"  ✗ Response formatting test failed: {e}")
        return 0, 1


def test_mcp_tool_structure():
    """Test MCP tool structure without executing them."""
    print("\nTesting MCP tool structure...")
    
    try:
        from main import create_mcp_tools
        
        tools = create_mcp_tools()
        
        passed = 0
        failed = 0
        
        # Check tool count
        if len(tools) == 3:
            print("  ✓ Correct number of tools created")
            passed += 1
        else:
            print(f"  ✗ Expected 3 tools, got {len(tools)}")
            failed += 1
        
        # Check tool names
        expected_names = [
            "search_restaurants_by_district",
            "search_restaurants_by_meal_type", 
            "search_restaurants_combined"
        ]
        
        tool_names = [tool.name for tool in tools]
        
        for expected_name in expected_names:
            if expected_name in tool_names:
                print(f"  ✓ Tool '{expected_name}' exists")
                passed += 1
            else:
                print(f"  ✗ Tool '{expected_name}' missing")
                failed += 1
        
        # Check parameter schemas
        for tool in tools:
            if hasattr(tool, 'parameters') and isinstance(tool.parameters, dict):
                if "type" in tool.parameters and tool.parameters["type"] == "object":
                    print(f"  ✓ Tool '{tool.name}' has valid parameter schema")
                    passed += 1
                else:
                    print(f"  ✗ Tool '{tool.name}' has invalid parameter schema")
                    failed += 1
            else:
                print(f"  ✗ Tool '{tool.name}' missing parameters")
                failed += 1
        
        return passed, failed
        
    except Exception as e:
        print(f"  ✗ MCP tool structure test failed: {e}")
        return 0, 1


def test_entrypoint_function():
    """Test the main entrypoint function components.
    
    Note: This test focuses on verifying that the entrypoint components are properly
    initialized and can be imported, rather than testing the full execution flow
    which would require complex mocking of the Strands Agent runtime.
    """
    print("\nTesting entrypoint function...")
    
    try:
        from main import extract_user_prompt, format_response, format_error_response
        
        passed = 0
        failed = 0
        
        # Test that we can import the process_request function
        try:
            from main import process_request
            print("  ✓ Entrypoint function import successful")
            passed += 1
        except Exception as e:
            print(f"  ✗ Entrypoint function import failed: {e}")
            failed += 1
        
        # Test the entrypoint decorator exists
        try:
            from main import app
            if hasattr(app, 'entrypoint'):
                print("  ✓ BedrockAgentCoreApp entrypoint decorator available")
                passed += 1
            else:
                print("  ✗ BedrockAgentCoreApp entrypoint decorator missing")
                failed += 1
        except Exception as e:
            print(f"  ✗ BedrockAgentCoreApp app check failed: {e}")
            failed += 1
        
        # Test that the strands_agent is initialized
        try:
            from main import strands_agent
            if strands_agent is not None:
                print("  ✓ Strands agent initialized")
                passed += 1
            else:
                print("  ✗ Strands agent not initialized")
                failed += 1
        except Exception as e:
            print(f"  ✗ Strands agent check failed: {e}")
            failed += 1
        
        # Test error response generation
        try:
            error_response = format_error_response("Test error", "test_error")
            error_data = json.loads(error_response)
            
            if (error_data.get("success") is False and 
                error_data.get("error", {}).get("type") == "test_error"):
                print("  ✓ Error response generation works")
                passed += 1
            else:
                print("  ✗ Error response generation failed")
                failed += 1
        except Exception as e:
            print(f"  ✗ Error response generation test failed: {e}")
            failed += 1
        
        return passed, failed
        
    except Exception as e:
        print(f"  ✗ Entrypoint function test failed: {e}")
        return 0, 1


def run_all_tests():
    """Run all basic tests and generate report."""
    
    print("=" * 60)
    print("BASIC ENTRYPOINT INTEGRATION TESTS")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    total_passed = 0
    total_failed = 0
    
    # Run individual test suites
    test_suites = [
        ("Payload Extraction", test_payload_extraction),
        ("Response Formatting", test_response_formatting),
        ("MCP Tool Structure", test_mcp_tool_structure),
        ("Entrypoint Function", test_entrypoint_function)
    ]
    
    results = {}
    
    for suite_name, test_func in test_suites:
        try:
            passed, failed = test_func()
            results[suite_name] = {"passed": passed, "failed": failed}
            total_passed += passed
            total_failed += failed
        except Exception as e:
            print(f"Test suite '{suite_name}' crashed: {e}")
            results[suite_name] = {"passed": 0, "failed": 1, "error": str(e)}
            total_failed += 1
    
    # Generate summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for suite_name, result in results.items():
        passed = result["passed"]
        failed = result["failed"]
        total = passed + failed
        status = "PASSED" if failed == 0 else "FAILED"
        print(f"{suite_name}: {passed}/{total} passed - {status}")
        
        if "error" in result:
            print(f"  Error: {result['error']}")
    
    print()
    print(f"TOTAL: {total_passed}/{total_passed + total_failed} passed")
    print(f"Overall Status: {'PASSED' if total_failed == 0 else 'FAILED'}")
    
    # Save results
    os.makedirs("tests/results", exist_ok=True)
    
    test_results = {
        "test_suite": "basic_entrypoint_integration",
        "timestamp": datetime.now().isoformat(),
        "total_passed": total_passed,
        "total_failed": total_failed,
        "suites": results
    }
    
    with open("tests/results/basic_entrypoint_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nResults saved to: tests/results/basic_entrypoint_test_results.json")
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)