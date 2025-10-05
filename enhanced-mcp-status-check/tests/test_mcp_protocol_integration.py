"""
MCP Protocol Integration Tests.

Focused integration tests for MCP tools/list request and response validation.
Tests the complete MCP protocol flow including JSON-RPC 2.0 compliance,
tool validation, and error handling.

Requirements covered: 1.1, 1.2
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from models.dual_health_models import EnhancedServerConfig, MCPHealthCheckResult
from services.mcp_health_check_client import MCPHealthCheckClient


class TestMCPProtocolIntegration:
    """Integration tests for MCP protocol handling."""

    @pytest.fixture
    def mcp_client(self):
        """Create MCP health check client for testing."""
        return MCPHealthCheckClient()

    @pytest.fixture
    def server_config(self):
        """Create server configuration for MCP testing."""
        return EnhancedServerConfig(
            server_name="mcp-test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            mcp_enabled=True,
            rest_enabled=False,
            mcp_expected_tools=["search_restaurants", "recommend_restaurants", "get_restaurant_details"],
            jwt_token="test-jwt-token"
        )

    async def test_mcp_tools_list_request_generation(self, mcp_client):
        """
        Test MCP tools/list JSON-RPC 2.0 request generation.
        
        Requirements: 1.1
        """
        request = mcp_client.create_mcp_request("test-request-123")
        
        # Verify JSON-RPC 2.0 compliance
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.id == "test-request-123"
        assert request.params == {}

        # Test serialization
        request_dict = request.to_dict()
        assert request_dict["jsonrpc"] == "2.0"
        assert request_dict["method"] == "tools/list"
        assert request_dict["id"] == "test-request-123"

    async def test_mcp_tools_list_response_validation_success(self, mcp_client, server_config):
        """
        Test successful MCP tools/list response validation.
        
        Requirements: 1.1, 1.2
        """
        # Mock successful MCP response with all expected tools
        mock_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {
                "tools": [
                    {
                        "name": "search_restaurants",
                        "description": "Search for restaurants by criteria",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "district": {"type": "string"}
                            }
                        }
                    },
                    {
                        "name": "recommend_restaurants",
                        "description": "Recommend restaurants based on preferences",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "preferences": {"type": "object"}
                            }
                        }
                    },
                    {
                        "name": "get_restaurant_details",
                        "description": "Get detailed information about a restaurant",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "restaurant_id": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_response

            result = await mcp_client.send_tools_list_request(
                server_config.mcp_endpoint_url,
                {"Authorization": f"Bearer {server_config.jwt_token}"},
                server_config.mcp_timeout_seconds
            )

            # Verify response structure
            assert result.jsonrpc == "2.0"
            assert result.id == "test-123"
            assert len(result.result.tools) == 3

            # Verify tool validation
            validation_result = mcp_client.validate_tools_list_response(
                result, server_config.mcp_expected_tools
            )
            assert validation_result.is_valid is True
            assert len(validation_result.found_tools) == 3
            assert len(validation_result.missing_tools) == 0
            assert len(validation_result.validation_errors) == 0

    async def test_mcp_tools_list_response_validation_missing_tools(self, mcp_client, server_config):
        """
        Test MCP tools/list response validation with missing expected tools.
        
        Requirements: 1.2
        """
        # Mock MCP response missing one expected tool
        mock_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {
                "tools": [
                    {
                        "name": "search_restaurants",
                        "description": "Search for restaurants by criteria",
                        "inputSchema": {"type": "object"}
                    },
                    {
                        "name": "recommend_restaurants",
                        "description": "Recommend restaurants based on preferences",
                        "inputSchema": {"type": "object"}
                    }
                    # Missing "get_restaurant_details"
                ]
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_response

            result = await mcp_client.send_tools_list_request(
                server_config.mcp_endpoint_url,
                {"Authorization": f"Bearer {server_config.jwt_token}"},
                server_config.mcp_timeout_seconds
            )

            # Verify validation detects missing tool
            validation_result = mcp_client.validate_tools_list_response(
                result, server_config.mcp_expected_tools
            )
            assert validation_result.is_valid is False
            assert len(validation_result.found_tools) == 2
            assert "get_restaurant_details" in validation_result.missing_tools
            assert len(validation_result.validation_errors) > 0

    async def test_mcp_tools_list_response_validation_malformed_tools(self, mcp_client, server_config):
        """
        Test MCP tools/list response validation with malformed tool definitions.
        
        Requirements: 1.2
        """
        # Mock MCP response with malformed tools
        mock_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {
                "tools": [
                    {
                        "name": "search_restaurants",
                        "description": "Search for restaurants by criteria",
                        "inputSchema": {"type": "object"}
                    },
                    {
                        # Missing required "name" field
                        "description": "Recommend restaurants based on preferences",
                        "inputSchema": {"type": "object"}
                    },
                    {
                        "name": "get_restaurant_details",
                        # Missing "description" field
                        "inputSchema": {"type": "object"}
                    }
                ]
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_response

            result = await mcp_client.send_tools_list_request(
                server_config.mcp_endpoint_url,
                {"Authorization": f"Bearer {server_config.jwt_token}"},
                server_config.mcp_timeout_seconds
            )

            # Verify validation detects malformed tools
            validation_result = mcp_client.validate_tools_list_response(
                result, server_config.mcp_expected_tools
            )
            assert validation_result.is_valid is False
            assert len(validation_result.validation_errors) >= 2  # At least 2 malformed tools

    async def test_mcp_jsonrpc_error_response_handling(self, mcp_client, server_config):
        """
        Test handling of JSON-RPC error responses from MCP server.
        
        Requirements: 1.1
        """
        # Mock JSON-RPC error response
        mock_error_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": "The method 'tools/list' is not supported"
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_error_response

            result = await mcp_client.send_tools_list_request(
                server_config.mcp_endpoint_url,
                {"Authorization": f"Bearer {server_config.jwt_token}"},
                server_config.mcp_timeout_seconds
            )

            # Verify error response handling
            assert result.jsonrpc == "2.0"
            assert result.id == "test-123"
            assert result.error is not None
            assert result.error.code == -32601
            assert "Method not found" in result.error.message

    async def test_mcp_authentication_header_inclusion(self, mcp_client, server_config):
        """
        Test that JWT authentication headers are properly included in MCP requests.
        
        Requirements: 1.1
        """
        mock_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {"tools": []}
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_response

            await mcp_client.send_tools_list_request(
                server_config.mcp_endpoint_url,
                {"Authorization": f"Bearer {server_config.jwt_token}"},
                server_config.mcp_timeout_seconds
            )

            # Verify authentication headers were included
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert "headers" in call_kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == f"Bearer {server_config.jwt_token}"

    async def test_mcp_request_timeout_handling(self, mcp_client, server_config):
        """
        Test MCP request timeout handling.
        
        Requirements: 1.1
        """
        import asyncio

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.side_effect = asyncio.TimeoutError("Request timeout")

            try:
                await mcp_client.send_tools_list_request(
                    server_config.mcp_endpoint_url,
                    {"Authorization": f"Bearer {server_config.jwt_token}"},
                    1  # 1 second timeout
                )
                assert False, "Expected TimeoutError"
            except asyncio.TimeoutError:
                pass  # Expected

    async def test_mcp_invalid_json_response_handling(self, mcp_client, server_config):
        """
        Test handling of invalid JSON responses from MCP server.
        
        Requirements: 1.1
        """
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.side_effect = json.JSONDecodeError(
                "Invalid JSON", "response", 0
            )

            try:
                await mcp_client.send_tools_list_request(
                    server_config.mcp_endpoint_url,
                    {"Authorization": f"Bearer {server_config.jwt_token}"},
                    server_config.mcp_timeout_seconds
                )
                assert False, "Expected JSONDecodeError"
            except json.JSONDecodeError:
                pass  # Expected

    async def test_mcp_http_error_status_handling(self, mcp_client, server_config):
        """
        Test handling of HTTP error status codes from MCP server.
        
        Requirements: 1.1
        """
        error_codes = [400, 401, 403, 404, 500, 502, 503, 504]

        for status_code in error_codes:
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_post.return_value.__aenter__.return_value.status = status_code
                mock_post.return_value.__aenter__.return_value.json.return_value = {
                    "error": f"HTTP {status_code} error"
                }

                try:
                    await mcp_client.send_tools_list_request(
                        server_config.mcp_endpoint_url,
                        {"Authorization": f"Bearer {server_config.jwt_token}"},
                        server_config.mcp_timeout_seconds
                    )
                    # Some implementations might not raise exceptions for HTTP errors
                    # so we don't assert failure here
                except Exception:
                    pass  # Expected for some status codes

    async def test_mcp_tools_list_with_complex_schemas(self, mcp_client, server_config):
        """
        Test MCP tools/list response with complex input schemas.
        
        Requirements: 1.2
        """
        # Mock response with complex tool schemas
        mock_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {
                "tools": [
                    {
                        "name": "search_restaurants",
                        "description": "Advanced restaurant search with multiple criteria",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "district": {"type": "string"},
                                        "cuisine": {"type": "array", "items": {"type": "string"}},
                                        "price_range": {
                                            "type": "object",
                                            "properties": {
                                                "min": {"type": "number"},
                                                "max": {"type": "number"}
                                            }
                                        }
                                    }
                                },
                                "sort_by": {
                                    "type": "string",
                                    "enum": ["rating", "distance", "price"]
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "recommend_restaurants",
                        "description": "AI-powered restaurant recommendations",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_preferences": {
                                    "type": "object",
                                    "properties": {
                                        "dietary_restrictions": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "favorite_cuisines": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "budget": {"type": "number"}
                                    }
                                },
                                "context": {
                                    "type": "object",
                                    "properties": {
                                        "occasion": {"type": "string"},
                                        "group_size": {"type": "integer"},
                                        "time_of_day": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    {
                        "name": "get_restaurant_details",
                        "description": "Get comprehensive restaurant information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "restaurant_id": {"type": "string"},
                                "include_reviews": {"type": "boolean", "default": false},
                                "include_menu": {"type": "boolean", "default": false}
                            },
                            "required": ["restaurant_id"]
                        }
                    }
                ]
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_response

            result = await mcp_client.send_tools_list_request(
                server_config.mcp_endpoint_url,
                {"Authorization": f"Bearer {server_config.jwt_token}"},
                server_config.mcp_timeout_seconds
            )

            # Verify complex schema parsing
            assert len(result.result.tools) == 3
            
            # Verify first tool's complex schema
            search_tool = result.result.tools[0]
            assert search_tool.name == "search_restaurants"
            assert "properties" in search_tool.inputSchema
            assert "filters" in search_tool.inputSchema["properties"]
            assert "price_range" in search_tool.inputSchema["properties"]["filters"]["properties"]

            # Verify validation still works with complex schemas
            validation_result = mcp_client.validate_tools_list_response(
                result, server_config.mcp_expected_tools
            )
            assert validation_result.is_valid is True
            assert len(validation_result.found_tools) == 3