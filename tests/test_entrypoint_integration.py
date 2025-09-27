"""
Tests for BedrockAgentCoreApp entrypoint integration.

This module tests the main entrypoint functionality including payload processing,
Strands Agent integration, MCP tool selection, response formatting, and error handling.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the main module components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    extract_user_prompt,
    format_response,
    format_error_response,
    create_mcp_tools,
    create_strands_agent,
    process_request,
    log_request_processing
)


class TestPayloadProcessing:
    """Test payload processing and user prompt extraction."""
    
    def test_extract_user_prompt_standard_format(self):
        """Test extracting prompt from standard AgentCore payload format."""
        payload = {
            "input": {
                "prompt": "Find restaurants in Central district"
            }
        }
        
        result = extract_user_prompt(payload)
        assert result == "Find restaurants in Central district"
    
    def test_extract_user_prompt_message_format(self):
        """Test extracting prompt from message format."""
        payload = {
            "input": {
                "message": "Show me breakfast places in Tsim Sha Tsui"
            }
        }
        
        result = extract_user_prompt(payload)
        assert result == "Show me breakfast places in Tsim Sha Tsui"
    
    def test_extract_user_prompt_direct_input(self):
        """Test extracting prompt from direct input string."""
        payload = {
            "input": "Find dinner restaurants"
        }
        
        result = extract_user_prompt(payload)
        assert result == "Find dinner restaurants"
    
    def test_extract_user_prompt_top_level_prompt(self):
        """Test extracting prompt from top-level prompt field."""
        payload = {
            "prompt": "Search for lunch places in Causeway Bay"
        }
        
        result = extract_user_prompt(payload)
        assert result == "Search for lunch places in Causeway Bay"
    
    def test_extract_user_prompt_fallback(self):
        """Test fallback prompt extraction from any string field."""
        payload = {
            "query": "Find good restaurants",
            "other_field": 123
        }
        
        result = extract_user_prompt(payload)
        assert result == "Find good restaurants"
    
    def test_extract_user_prompt_invalid_payload(self):
        """Test error handling for invalid payload."""
        payload = {
            "number": 123,
            "boolean": True
        }
        
        with pytest.raises(ValueError, match="No valid prompt found in payload"):
            extract_user_prompt(payload)
    
    def test_extract_user_prompt_empty_payload(self):
        """Test error handling for empty payload."""
        payload = {}
        
        with pytest.raises(ValueError, match="No valid prompt found in payload"):
            extract_user_prompt(payload)


class TestResponseFormatting:
    """Test response formatting and JSON serialization."""
    
    def test_format_response_success(self):
        """Test formatting successful response."""
        agent_response = "I found 3 restaurants in Central district."
        
        result = format_response(agent_response, success=True)
        response_data = json.loads(result)
        
        assert response_data["success"] is True
        assert response_data["response"] == agent_response
        assert response_data["agent_type"] == "restaurant_search_assistant"
        assert "timestamp" in response_data
        assert "version" in response_data
    
    def test_format_response_with_error(self):
        """Test formatting response with error."""
        agent_response = "Error occurred"
        error_message = "District not found"
        
        result = format_response(agent_response, success=False, error=error_message)
        response_data = json.loads(result)
        
        assert response_data["success"] is False
        assert response_data["response"] == agent_response
        assert response_data["error"]["message"] == error_message
        assert response_data["error"]["type"] == "processing_error"
    
    def test_format_response_with_metadata(self):
        """Test formatting response with additional metadata."""
        agent_response = "Found restaurants"
        metadata = {"tool_used": "search_by_district", "result_count": 5}
        
        result = format_response(agent_response, success=True, metadata=metadata)
        response_data = json.loads(result)
        
        assert response_data["success"] is True
        assert response_data["metadata"] == metadata
    
    def test_format_error_response_district_error(self):
        """Test formatting district-specific error response."""
        error_message = "Invalid district name: UnknownDistrict"
        
        result = format_error_response(error_message, "validation_error")
        response_data = json.loads(result)
        
        assert response_data["success"] is False
        assert "district" in response_data["response"].lower()
        assert "Central district" in response_data["response"]
        assert len(response_data["suggestions"]) > 0
    
    def test_format_error_response_meal_error(self):
        """Test formatting meal-type specific error response."""
        error_message = "Invalid meal type specified"
        
        result = format_error_response(error_message, "validation_error")
        response_data = json.loads(result)
        
        assert response_data["success"] is False
        assert "meal type" in response_data["response"]
        assert "breakfast" in response_data["response"]
    
    def test_format_error_response_system_error(self):
        """Test formatting system error response."""
        error_message = "Database connection failed"
        
        result = format_error_response(error_message, "system_error")
        response_data = json.loads(result)
        
        assert response_data["success"] is False
        assert "technical difficulties" in response_data["response"]
        assert response_data["error"]["type"] == "system_error"


class TestMCPToolsIntegration:
    """Test MCP tools creation and integration."""
    
    @patch('main.restaurant_service')
    def test_create_mcp_tools_structure(self, mock_service):
        """Test MCP tools are created with proper structure."""
        tools = create_mcp_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "search_restaurants_by_district" in tool_names
        assert "search_restaurants_by_meal_type" in tool_names
        assert "search_restaurants_combined" in tool_names
    
    @patch('main.restaurant_service')
    def test_mcp_tool_parameters_schema(self, mock_service):
        """Test MCP tools have proper parameter schemas."""
        tools = create_mcp_tools()
        
        district_tool = next(tool for tool in tools if tool.name == "search_restaurants_by_district")
        assert "districts" in district_tool.parameters["properties"]
        assert district_tool.parameters["properties"]["districts"]["type"] == "array"
        assert "districts" in district_tool.parameters["required"]
        
        meal_tool = next(tool for tool in tools if tool.name == "search_restaurants_by_meal_type")
        assert "meal_types" in meal_tool.parameters["properties"]
        assert meal_tool.parameters["properties"]["meal_types"]["items"]["enum"] == ["breakfast", "lunch", "dinner"]
    
    @patch('main.restaurant_service')
    def test_district_search_tool_execution(self, mock_service):
        """Test district search tool execution."""
        # Mock restaurant service response
        mock_restaurant = Mock()
        mock_restaurant.to_dict.return_value = {
            "id": "rest1",
            "name": "Test Restaurant",
            "district": "Central district"
        }
        mock_service.search_by_districts.return_value = [mock_restaurant]
        
        tools = create_mcp_tools()
        district_tool = next(tool for tool in tools if tool.name == "search_restaurants_by_district")
        
        result = district_tool.function(["Central district"])
        response_data = json.loads(result)
        
        assert response_data["success"] is True
        assert response_data["query_type"] == "district_search"
        assert response_data["districts"] == ["Central district"]
        assert response_data["restaurant_count"] == 1
        assert len(response_data["restaurants"]) == 1
    
    @patch('main.restaurant_service')
    def test_meal_type_search_tool_execution(self, mock_service):
        """Test meal type search tool execution."""
        mock_restaurant = Mock()
        mock_restaurant.to_dict.return_value = {
            "id": "rest1",
            "name": "Breakfast Place",
            "meal_type": ["breakfast"]
        }
        mock_service.search_by_meal_types.return_value = [mock_restaurant]
        
        tools = create_mcp_tools()
        meal_tool = next(tool for tool in tools if tool.name == "search_restaurants_by_meal_type")
        
        result = meal_tool.function(["breakfast"])
        response_data = json.loads(result)
        
        assert response_data["success"] is True
        assert response_data["query_type"] == "meal_type_search"
        assert response_data["meal_types"] == ["breakfast"]
        assert response_data["restaurant_count"] == 1
    
    @patch('main.restaurant_service')
    def test_combined_search_tool_execution(self, mock_service):
        """Test combined search tool execution."""
        mock_restaurant = Mock()
        mock_restaurant.to_dict.return_value = {
            "id": "rest1",
            "name": "Central Breakfast",
            "district": "Central district",
            "meal_type": ["breakfast"]
        }
        mock_service.search_combined.return_value = [mock_restaurant]
        
        tools = create_mcp_tools()
        combined_tool = next(tool for tool in tools if tool.name == "search_restaurants_combined")
        
        result = combined_tool.function(["Central district"], ["breakfast"])
        response_data = json.loads(result)
        
        assert response_data["success"] is True
        assert response_data["query_type"] == "combined_search"
        assert response_data["districts"] == ["Central district"]
        assert response_data["meal_types"] == ["breakfast"]
    
    @patch('main.restaurant_service')
    def test_tool_error_handling(self, mock_service):
        """Test MCP tool error handling."""
        mock_service.search_by_districts.side_effect = Exception("Service error")
        
        tools = create_mcp_tools()
        district_tool = next(tool for tool in tools if tool.name == "search_restaurants_by_district")
        
        result = district_tool.function(["Invalid District"])
        response_data = json.loads(result)
        
        assert response_data["success"] is False
        assert "error" in response_data
        assert response_data["query_type"] == "district_search"


class TestStrandsAgentIntegration:
    """Test Strands Agent configuration and integration."""
    
    @patch('main.create_mcp_tools')
    @patch('strands_agents.Agent')
    def test_create_strands_agent_configuration(self, mock_agent_class, mock_tools):
        """Test Strands Agent is configured with proper parameters."""
        mock_tools.return_value = []
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        agent = create_strands_agent()
        
        # Verify Agent was called with correct parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        assert call_args[1]["model"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert call_args[1]["temperature"] == 0.1
        assert call_args[1]["max_tokens"] == 2048
        assert call_args[1]["top_p"] == 0.9
        assert call_args[1]["tool_choice"] == "auto"
        assert "Hong Kong" in call_args[1]["system_prompt"]
    
    @patch('main.create_mcp_tools')
    @patch('strands_agents.Agent')
    def test_strands_agent_system_prompt_content(self, mock_agent_class, mock_tools):
        """Test Strands Agent system prompt contains required information."""
        mock_tools.return_value = []
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        create_strands_agent()
        
        call_args = mock_agent_class.call_args
        system_prompt = call_args[1]["system_prompt"]
        
        # Check for key information in system prompt
        assert "Hong Kong" in system_prompt
        assert "breakfast" in system_prompt and "lunch" in system_prompt and "dinner" in system_prompt
        assert "7:00-11:29" in system_prompt  # Breakfast hours
        assert "11:30-17:29" in system_prompt  # Lunch hours
        assert "17:30-22:30" in system_prompt  # Dinner hours
        assert "Central district" in system_prompt
        assert "Tsim Sha Tsui" in system_prompt


class TestEntrypointIntegration:
    """Test complete entrypoint integration."""
    
    @patch('main.strands_agent')
    @patch('main.log_request_processing')
    def test_process_request_success(self, mock_log, mock_agent):
        """Test successful request processing."""
        payload = {"input": {"prompt": "Find restaurants in Central district"}}
        mock_agent.run.return_value = "I found 3 restaurants in Central district."
        
        result = process_request(payload)
        response_data = json.loads(result)
        
        assert response_data["success"] is True
        assert "restaurants" in response_data["response"]
        assert "metadata" in response_data
        mock_agent.run.assert_called_once_with("Find restaurants in Central district")
        mock_log.assert_called_once()
    
    @patch('main.strands_agent')
    @patch('main.log_request_processing')
    def test_process_request_payload_error(self, mock_log, mock_agent):
        """Test request processing with invalid payload."""
        payload = {"invalid": "data"}
        
        result = process_request(payload)
        response_data = json.loads(result)
        
        assert response_data["success"] is False
        assert response_data["error"]["type"] == "validation_error"
        assert "couldn't understand" in response_data["response"]
        mock_agent.run.assert_not_called()
        mock_log.assert_called_once()
    
    @patch('main.strands_agent')
    @patch('main.log_request_processing')
    def test_process_request_agent_error(self, mock_log, mock_agent):
        """Test request processing with agent error."""
        payload = {"input": {"prompt": "Find restaurants"}}
        mock_agent.run.side_effect = Exception("Agent processing error")
        
        result = process_request(payload)
        response_data = json.loads(result)
        
        assert response_data["success"] is False
        assert response_data["error"]["type"] == "system_error"
        assert "technical difficulties" in response_data["response"]
        mock_log.assert_called_once()
    
    @patch('main.strands_agent')
    def test_process_request_response_serialization(self, mock_agent):
        """Test response is properly JSON serializable."""
        payload = {"input": {"prompt": "Test query"}}
        mock_agent.run.return_value = "Test response with unicode: 中文"
        
        result = process_request(payload)
        
        # Should not raise JSON decode error
        response_data = json.loads(result)
        assert response_data["success"] is True
        assert "中文" in response_data["response"]
    
    def test_log_request_processing_success(self):
        """Test request processing logging for successful requests."""
        payload = {"input": {"prompt": "test"}}
        user_prompt = "test prompt"
        
        # Should not raise any exceptions
        log_request_processing(payload, user_prompt, success=True)
    
    def test_log_request_processing_failure(self):
        """Test request processing logging for failed requests."""
        payload = {"input": {"prompt": "test"}}
        user_prompt = "test prompt"
        error = "Test error"
        
        # Should not raise any exceptions
        log_request_processing(payload, user_prompt, success=False, error=error)


class TestErrorHandlingScenarios:
    """Test various error handling scenarios."""
    
    def test_malformed_json_in_tools(self):
        """Test handling of malformed JSON in tool responses."""
        # This would be tested with actual tool execution
        pass
    
    def test_timeout_scenarios(self):
        """Test handling of timeout scenarios."""
        # This would require integration with actual timeout mechanisms
        pass
    
    def test_memory_constraints(self):
        """Test handling of memory constraint scenarios."""
        # This would require testing with large payloads
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])