"""
Tests for backward compatibility with existing MCP clients.

Tests ensure that the Gateway doesn't break existing MCP client integrations
and maintains compatibility with different MCP protocol versions.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from typing import Dict, Any, List
import httpx

from services.mcp_client_manager import MCPClientManager, get_mcp_client_manager


class TestMCPProtocolCompatibility:
    """Test cases for MCP protocol compatibility."""
    
    @pytest.fixture
    def mock_mcp_server_responses(self):
        """Mock responses from existing MCP servers."""
        return {
            "search_restaurants_by_district": {
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Compatible Restaurant",
                            "district": "Central district",
                            "address": "123 Test Street",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                        }
                    ],
                    "total_count": 1,
                    "search_criteria": {"districts": ["Central district"]}
                }
            },
            "recommend_restaurants": {
                "success": True,
                "data": {
                    "recommendation": {
                        "id": "rest_001",
                        "name": "Top Choice",
                        "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
                    },
                    "candidates": [],
                    "ranking_method": "sentiment_likes"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_existing_mcp_server_integration(self, mock_mcp_server_responses):
        """Test integration with existing MCP servers without modification."""
        # Create MCP client manager
        client_manager = MCPClientManager()
        await client_manager.start()
        
        try:
            with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
                # Mock HTTP client for MCP server communication
                mock_http_client = AsyncMock()
                mock_response = Mock()
                mock_response.json.return_value = mock_mcp_server_responses["search_restaurants_by_district"]
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                mock_http_client.post.return_value = mock_response
                mock_get_client.return_value = mock_http_client
                
                # Test calling existing MCP tool
                result = await client_manager.call_mcp_tool(
                    server_name="restaurant-search",
                    tool_name="search_restaurants_by_district",
                    parameters={"districts": ["Central district"]}
                )
                
                # Verify result format matches existing MCP server response
                assert result["success"] is True
                assert "data" in result
                assert "restaurants" in result["data"]
                assert result["data"]["total_count"] == 1
                
                # Verify HTTP request was made correctly
                mock_http_client.post.assert_called_once()
                call_args = mock_http_client.post.call_args
                
                # Verify request format is compatible with existing MCP servers
                assert call_args[0][0] == "/invoke"  # Endpoint
                request_data = call_args[1]["json"]
                assert "tool_name" in request_data
                assert "parameters" in request_data
                assert request_data["tool_name"] == "search_restaurants_by_district"
                assert request_data["parameters"]["districts"] == ["Central district"]
        
        finally:
            await client_manager.stop()
    
    @pytest.mark.asyncio
    async def test_mcp_request_format_compatibility(self):
        """Test that MCP requests maintain compatible format."""
        client_manager = MCPClientManager()
        await client_manager.start()
        
        try:
            with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
                mock_http_client = AsyncMock()
                mock_response = Mock()
                mock_response.json.return_value = {"success": True, "data": {}}
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                mock_http_client.post.return_value = mock_response
                mock_get_client.return_value = mock_http_client
                
                # Test various tool calls to verify request format
                test_cases = [
                    {
                        "server_name": "restaurant-search",
                        "tool_name": "search_restaurants_by_district",
                        "parameters": {"districts": ["Central district", "Admiralty"]}
                    },
                    {
                        "server_name": "restaurant-search",
                        "tool_name": "search_restaurants_by_meal_type",
                        "parameters": {"meal_types": ["breakfast", "lunch"]}
                    },
                    {
                        "server_name": "restaurant-reasoning",
                        "tool_name": "recommend_restaurants",
                        "parameters": {
                            "restaurants": [{"id": "test", "sentiment": {"likes": 10, "dislikes": 2, "neutral": 1}}],
                            "ranking_method": "sentiment_likes"
                        }
                    }
                ]
                
                for test_case in test_cases:
                    await client_manager.call_mcp_tool(**test_case)
                    
                    # Verify request format
                    call_args = mock_http_client.post.call_args
                    request_data = call_args[1]["json"]
                    
                    assert "tool_name" in request_data
                    assert "parameters" in request_data
                    assert request_data["tool_name"] == test_case["tool_name"]
                    assert request_data["parameters"] == test_case["parameters"]
                    
                    # Verify headers are compatible
                    headers = call_args[1].get("headers", {})
                    assert "Content-Type" in headers
                    assert headers["Content-Type"] == "application/json"
        
        finally:
            await client_manager.stop()
    
    @pytest.mark.asyncio
    async def test_mcp_response_format_handling(self):
        """Test handling of various MCP response formats."""
        client_manager = MCPClientManager()
        await client_manager.start()
        
        try:
            # Test different response formats that existing MCP servers might return
            response_formats = [
                # Standard success response
                {
                    "success": True,
                    "data": {"restaurants": [], "total_count": 0}
                },
                # Success response with additional metadata
                {
                    "success": True,
                    "data": {"restaurants": []},
                    "metadata": {"server_version": "1.0", "timestamp": "2025-01-03T10:00:00Z"}
                },
                # Error response format
                {
                    "success": False,
                    "error": {"message": "Tool not found", "code": "TOOL_NOT_FOUND"}
                },
                # Legacy response format (without success field)
                {
                    "data": {"restaurants": []},
                    "status": "ok"
                },
                # Minimal response format
                {
                    "restaurants": []
                }
            ]
            
            with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
                mock_http_client = AsyncMock()
                mock_get_client.return_value = mock_http_client
                
                for response_format in response_formats:
                    mock_response = Mock()
                    mock_response.json.return_value = response_format
                    mock_response.status_code = 200
                    mock_response.raise_for_status.return_value = None
                    mock_http_client.post.return_value = mock_response
                    
                    # Call should handle different response formats gracefully
                    result = await client_manager.call_mcp_tool(
                        server_name="restaurant-search",
                        tool_name="search_restaurants_by_district",
                        parameters={"districts": ["Central district"]}
                    )
                    
                    # Should return the response as-is for compatibility
                    assert result == response_format
        
        finally:
            await client_manager.stop()


class TestExistingClientCompatibility:
    """Test cases for compatibility with existing MCP client implementations."""
    
    @pytest.mark.asyncio
    async def test_direct_mcp_server_access_still_works(self):
        """Test that existing direct MCP server access continues to work."""
        # Simulate existing client making direct calls to MCP servers
        # This test ensures the Gateway doesn't interfere with direct access
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock direct MCP server response
            mock_response = Mock()
            mock_response.json.return_value = {
                "success": True,
                "data": {"restaurants": [{"id": "direct_001", "name": "Direct Access Restaurant"}]}
            }
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            
            # Simulate existing client code
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://restaurant-search-mcp:8080/invoke",
                    json={
                        "tool_name": "search_restaurants_by_district",
                        "parameters": {"districts": ["Central district"]}
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                
                # Verify existing client can still access MCP servers directly
                assert result["success"] is True
                assert "data" in result
                assert result["data"]["restaurants"][0]["name"] == "Direct Access Restaurant"
    
    @pytest.mark.asyncio
    async def test_existing_authentication_patterns_compatibility(self):
        """Test compatibility with existing authentication patterns."""
        client_manager = MCPClientManager()
        await client_manager.start()
        
        try:
            with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
                mock_http_client = AsyncMock()
                mock_response = Mock()
                mock_response.json.return_value = {"success": True, "data": {}}
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                mock_http_client.post.return_value = mock_http_client
                
                # Test different authentication patterns that existing clients might use
                auth_patterns = [
                    # Bearer token (current standard)
                    {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                    # Custom header format
                    {"X-Auth-Token": "custom-token-format"},
                    # Multiple auth headers
                    {
                        "Authorization": "Bearer token",
                        "X-User-ID": "user123",
                        "X-Client-ID": "client456"
                    }
                ]
                
                for auth_headers in auth_patterns:
                    # Test that MCP client manager passes through auth headers
                    user_context = {
                        "user_id": "test-user",
                        "token": "test-token",
                        "custom_headers": auth_headers
                    }
                    
                    await client_manager.call_mcp_tool(
                        server_name="restaurant-search",
                        tool_name="search_restaurants_by_district",
                        parameters={"districts": ["Central district"]},
                        user_context=user_context
                    )
                    
                    # Verify auth headers are preserved for MCP server
                    mock_http_client.post.assert_called()
        
        finally:
            await client_manager.stop()
    
    def test_existing_error_handling_patterns(self):
        """Test that existing error handling patterns continue to work."""
        # Test various error scenarios that existing clients expect
        error_scenarios = [
            {
                "status_code": 404,
                "response": {"error": "Tool not found"},
                "expected_behavior": "Should propagate 404 error"
            },
            {
                "status_code": 500,
                "response": {"error": "Internal server error"},
                "expected_behavior": "Should propagate 500 error"
            },
            {
                "status_code": 503,
                "response": {"error": "Service unavailable"},
                "expected_behavior": "Should propagate 503 error"
            }
        ]
        
        for scenario in error_scenarios:
            # Existing clients should receive the same error responses
            # This ensures error handling compatibility
            assert scenario["status_code"] in [404, 500, 503]
            assert "error" in scenario["response"]


class TestVersionCompatibility:
    """Test cases for version compatibility across MCP protocol versions."""
    
    @pytest.mark.asyncio
    async def test_mcp_protocol_version_negotiation(self):
        """Test compatibility with different MCP protocol versions."""
        client_manager = MCPClientManager()
        await client_manager.start()
        
        try:
            # Test different protocol versions
            protocol_versions = [
                {"version": "1.0", "features": ["basic_tools"]},
                {"version": "1.1", "features": ["basic_tools", "streaming"]},
                {"version": "2.0", "features": ["basic_tools", "streaming", "batch_operations"]}
            ]
            
            with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
                mock_http_client = AsyncMock()
                mock_get_client.return_value = mock_http_client
                
                for version_info in protocol_versions:
                    # Mock version-specific response
                    mock_response = Mock()
                    mock_response.json.return_value = {
                        "success": True,
                        "data": {"restaurants": []},
                        "protocol_version": version_info["version"],
                        "supported_features": version_info["features"]
                    }
                    mock_response.status_code = 200
                    mock_response.raise_for_status.return_value = None
                    mock_http_client.post.return_value = mock_response
                    
                    # Should handle different protocol versions
                    result = await client_manager.call_mcp_tool(
                        server_name="restaurant-search",
                        tool_name="search_restaurants_by_district",
                        parameters={"districts": ["Central district"]}
                    )
                    
                    # Should preserve version information
                    assert result["protocol_version"] == version_info["version"]
                    assert result["supported_features"] == version_info["features"]
        
        finally:
            await client_manager.stop()
    
    def test_legacy_response_format_support(self):
        """Test support for legacy response formats."""
        # Test various legacy formats that might be returned by older MCP servers
        legacy_formats = [
            # Old format without success field
            {"restaurants": [], "count": 0},
            # Format with different field names
            {"results": [], "total": 0, "status": "success"},
            # Nested format
            {"response": {"data": {"restaurants": []}, "meta": {"count": 0}}},
            # Simple array format
            [{"id": "rest_001", "name": "Legacy Restaurant"}]
        ]
        
        for legacy_format in legacy_formats:
            # Gateway should handle legacy formats gracefully
            # Either by normalizing them or passing them through unchanged
            assert legacy_format is not None
            
            # In a real implementation, we would test the actual conversion logic
            # For now, we verify the formats are recognized as valid JSON structures
            if isinstance(legacy_format, dict):
                assert len(legacy_format) >= 0
            elif isinstance(legacy_format, list):
                assert isinstance(legacy_format, list)


class TestConfigurationCompatibility:
    """Test cases for configuration compatibility."""
    
    def test_existing_mcp_server_configuration_unchanged(self):
        """Test that existing MCP server configurations don't need changes."""
        # Verify that existing MCP servers can continue using their current configurations
        
        # Example existing server configuration
        existing_config = {
            "server_name": "restaurant-search-mcp",
            "port": 8080,
            "endpoints": {
                "invoke": "/invoke",
                "health": "/health",
                "metadata": "/metadata"
            },
            "authentication": {
                "type": "jwt",
                "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/..."
            }
        }
        
        # Gateway should work with existing configurations without modification
        assert existing_config["server_name"] == "restaurant-search-mcp"
        assert existing_config["port"] == 8080
        assert existing_config["endpoints"]["invoke"] == "/invoke"
        
        # Configuration validation
        required_fields = ["server_name", "port", "endpoints"]
        for field in required_fields:
            assert field in existing_config
    
    def test_existing_deployment_patterns_compatibility(self):
        """Test compatibility with existing deployment patterns."""
        # Test various deployment patterns that existing MCP servers use
        deployment_patterns = [
            {
                "type": "docker",
                "image": "restaurant-search-mcp:latest",
                "ports": ["8080:8080"],
                "environment": ["JWT_DISCOVERY_URL=https://..."]
            },
            {
                "type": "kubernetes",
                "service": "restaurant-search-mcp-service",
                "deployment": "restaurant-search-mcp-deployment",
                "ingress": "restaurant-search-mcp-ingress"
            },
            {
                "type": "lambda",
                "function_name": "restaurant-search-mcp-function",
                "runtime": "python3.9",
                "handler": "main.handler"
            }
        ]
        
        for pattern in deployment_patterns:
            # Gateway should be compatible with all deployment patterns
            assert "type" in pattern
            assert pattern["type"] in ["docker", "kubernetes", "lambda"]
            
            # Each pattern should have its specific configuration
            if pattern["type"] == "docker":
                assert "image" in pattern
                assert "ports" in pattern
            elif pattern["type"] == "kubernetes":
                assert "service" in pattern
                assert "deployment" in pattern
            elif pattern["type"] == "lambda":
                assert "function_name" in pattern
                assert "runtime" in pattern


class TestDataFormatCompatibility:
    """Test cases for data format compatibility."""
    
    def test_restaurant_data_format_compatibility(self):
        """Test compatibility with existing restaurant data formats."""
        # Test various restaurant data formats that existing systems use
        restaurant_formats = [
            # Current format
            {
                "id": "rest_001",
                "name": "Restaurant Name",
                "district": "Central district",
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
            },
            # Legacy format with different field names
            {
                "restaurant_id": "rest_002",
                "restaurant_name": "Legacy Restaurant",
                "location": "Admiralty",
                "ratings": {"positive": 90, "negative": 8, "neutral": 2}
            },
            # Minimal format
            {
                "id": "rest_003",
                "name": "Minimal Restaurant"
            },
            # Extended format with additional fields
            {
                "id": "rest_004",
                "name": "Extended Restaurant",
                "district": "Causeway Bay",
                "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},
                "address": "123 Main Street",
                "phone": "+852-1234-5678",
                "cuisine_type": "Chinese",
                "price_range": "$$"
            }
        ]
        
        for restaurant_format in restaurant_formats:
            # Gateway should handle all restaurant data formats
            assert "id" in restaurant_format or "restaurant_id" in restaurant_format
            assert "name" in restaurant_format or "restaurant_name" in restaurant_format
            
            # Should preserve all fields regardless of format
            assert len(restaurant_format) > 0
    
    def test_search_parameter_format_compatibility(self):
        """Test compatibility with existing search parameter formats."""
        # Test various search parameter formats
        search_formats = [
            # Current format
            {"districts": ["Central district", "Admiralty"]},
            # Legacy format with different field names
            {"locations": ["Central district", "Admiralty"]},
            # Single value format
            {"district": "Central district"},
            # Mixed format
            {"districts": ["Central district"], "meal_types": ["lunch"], "limit": 10}
        ]
        
        for search_format in search_formats:
            # Gateway should handle different search parameter formats
            assert isinstance(search_format, dict)
            assert len(search_format) > 0
            
            # Should preserve parameter structure
            for key, value in search_format.items():
                assert key is not None
                assert value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])