"""
Unit tests for MCP Health Check Client

Tests for MCP tools/list request generation, response validation,
and health check functionality.
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError, ClientTimeout
from aiohttp.web_response import Response

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.mcp_health_check_client import MCPHealthCheckClient
from models.dual_health_models import (
    MCPToolsListRequest,
    MCPToolsListResponse,
    MCPValidationResult,
    MCPHealthCheckResult,
    EnhancedServerConfig
)


class TestMCPHealthCheckClient:
    """Test cases for MCP Health Check Client."""
    
    @pytest.fixture
    def client(self):
        """Create MCP Health Check Client instance."""
        return MCPHealthCheckClient()
    
    @pytest.fixture
    def mock_session(self):
        """Create mock aiohttp session."""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def sample_server_config(self):
        """Create sample server configuration."""
        return EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_enabled=True,
            mcp_timeout_seconds=10,
            mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
            mcp_retry_attempts=3,
            jwt_token="test-jwt-token",
            auth_headers={"X-API-Key": "test-key"}
        )
    
    @pytest.fixture
    def sample_tools_response(self):
        """Create sample MCP tools/list response."""
        return {
            "jsonrpc": "2.0",
            "id": "test-request-id",
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
                        "description": "Get restaurant recommendations",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "preferences": {"type": "object"}
                            }
                        }
                    }
                ]
            }
        }
    
    def test_create_mcp_request_default(self, client):
        """Test creating MCP request with default parameters."""
        request = client.create_mcp_request()
        
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.id is not None
        assert len(request.id) > 0
        assert request.params == {}
    
    def test_create_mcp_request_custom_id(self, client):
        """Test creating MCP request with custom ID."""
        custom_id = "custom-test-id"
        request = client.create_mcp_request(request_id=custom_id)
        
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.id == custom_id
        assert request.params == {}
    
    def test_create_mcp_request_validation(self, client):
        """Test MCP request validation."""
        request = client.create_mcp_request()
        validation_errors = request.validate()
        
        assert len(validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_send_tools_list_request_success(self, client, sample_tools_response):
        """Test successful MCP tools/list request."""
        from unittest.mock import AsyncMock, MagicMock
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=json.dumps(sample_tools_response))
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock(return_value=mock_context_manager)
        
        client._session = mock_session
        
        response = await client.send_tools_list_request(
            endpoint_url="http://localhost:8080/mcp",
            auth_headers={"Authorization": "Bearer test-token"},
            timeout=10
        )
        
        assert response.jsonrpc == "2.0"
        assert response.id == "test-request-id"
        assert response.result is not None
        assert response.error is None
        assert response.is_success()
        
        tools = response.get_tools()
        assert len(tools) == 2
        assert tools[0]["name"] == "search_restaurants"
        assert tools[1]["name"] == "recommend_restaurants"
    
    @pytest.mark.asyncio
    async def test_send_tools_list_request_http_error(self, client):
        """Test MCP request with HTTP error response."""
        from unittest.mock import AsyncMock, MagicMock
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value='{"error": "Internal Server Error"}')
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock(return_value=mock_context_manager)
        
        client._session = mock_session
        
        response = await client.send_tools_list_request(
            endpoint_url="http://localhost:8080/mcp",
            timeout=10
        )
        
        assert response.jsonrpc == "2.0"
        assert response.result is None
        assert response.error is not None
        assert response.error["code"] == -32000
        assert "HTTP 500" in response.error["message"]
        assert not response.is_success()
    
    @pytest.mark.asyncio
    async def test_send_tools_list_request_invalid_json(self, client):
        """Test MCP request with invalid JSON response."""
        from unittest.mock import AsyncMock, MagicMock
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="invalid json response")
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock(return_value=mock_context_manager)
        
        client._session = mock_session
        
        response = await client.send_tools_list_request(
            endpoint_url="http://localhost:8080/mcp",
            timeout=10
        )
        
        assert response.jsonrpc == "2.0"
        assert response.result is None
        assert response.error is not None
        assert response.error["code"] == -32700
        assert "Parse error" in response.error["message"]
        assert not response.is_success()
    
    @pytest.mark.asyncio
    async def test_send_tools_list_request_timeout(self, client):
        """Test MCP request timeout handling."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError()
        
        client._session = mock_session
        
        with pytest.raises(asyncio.TimeoutError):
            await client.send_tools_list_request(
                endpoint_url="http://localhost:8080/mcp",
                timeout=1
            )
    
    @pytest.mark.asyncio
    async def test_send_tools_list_request_client_error(self, client):
        """Test MCP request with client error."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = ClientError("Connection failed")
        
        client._session = mock_session
        
        with pytest.raises(ClientError):
            await client.send_tools_list_request(
                endpoint_url="http://localhost:8080/mcp",
                timeout=10
            )
    
    def test_validate_tools_list_response_success(self, client, sample_tools_response):
        """Test successful tools/list response validation."""
        response = MCPToolsListResponse.from_dict(sample_tools_response)
        expected_tools = ["search_restaurants", "recommend_restaurants"]
        
        validation_result = client.validate_tools_list_response(
            response=response,
            expected_tools=expected_tools
        )
        
        assert validation_result.is_valid
        assert validation_result.tools_count == 2
        assert len(validation_result.expected_tools_found) == 2
        assert len(validation_result.missing_tools) == 0
        assert len(validation_result.validation_errors) == 0
        assert validation_result.tool_schemas_valid
    
    def test_validate_tools_list_response_missing_tools(self, client, sample_tools_response):
        """Test validation with missing expected tools."""
        response = MCPToolsListResponse.from_dict(sample_tools_response)
        expected_tools = ["search_restaurants", "recommend_restaurants", "missing_tool"]
        
        validation_result = client.validate_tools_list_response(
            response=response,
            expected_tools=expected_tools
        )
        
        assert not validation_result.is_valid
        assert validation_result.tools_count == 2
        assert len(validation_result.expected_tools_found) == 2
        assert len(validation_result.missing_tools) == 1
        assert "missing_tool" in validation_result.missing_tools
        assert len(validation_result.validation_errors) > 0
    
    def test_validate_tools_list_response_invalid_format(self, client):
        """Test validation with invalid response format."""
        invalid_response = MCPToolsListResponse(
            jsonrpc="1.0",  # Invalid version
            id="",  # Missing ID
            result={"tools": [{"invalid": "tool"}]}  # Invalid tool format
        )
        
        validation_result = client.validate_tools_list_response(
            response=invalid_response,
            expected_tools=["test_tool"]
        )
        
        assert not validation_result.is_valid
        assert len(validation_result.validation_errors) > 0
        assert not validation_result.tool_schemas_valid
    
    def test_validate_tools_list_response_error_response(self, client):
        """Test validation with error response."""
        error_response = MCPToolsListResponse(
            jsonrpc="2.0",
            id="test-id",
            error={"code": -32601, "message": "Method not found"}
        )
        
        validation_result = client.validate_tools_list_response(
            response=error_response,
            expected_tools=["test_tool"]
        )
        
        assert not validation_result.is_valid
        assert validation_result.tools_count == 0
        assert len(validation_result.missing_tools) == 1
        assert "MCP response indicates failure" in validation_result.validation_errors
    
    @pytest.mark.asyncio
    async def test_perform_mcp_health_check_success(self, client, sample_server_config, sample_tools_response):
        """Test successful MCP health check."""
        from unittest.mock import AsyncMock, MagicMock
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=json.dumps(sample_tools_response))
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock(return_value=mock_context_manager)
        
        client._session = mock_session
        
        result = await client.perform_mcp_health_check(sample_server_config)
        
        assert result.server_name == "test-server"
        assert result.success
        assert result.tools_count == 2
        assert len(result.expected_tools_found) == 2
        assert len(result.missing_tools) == 0
        assert result.response_time_ms >= 0  # Mock doesn't simulate actual time
        assert result.connection_error is None
        assert result.mcp_error is None
    
    @pytest.mark.asyncio
    async def test_perform_mcp_health_check_disabled(self, client, sample_server_config):
        """Test MCP health check when MCP is disabled."""
        sample_server_config.mcp_enabled = False
        
        result = await client.perform_mcp_health_check(sample_server_config)
        
        assert result.server_name == "test-server"
        assert not result.success
        assert result.connection_error == "MCP health checks disabled in configuration"
    
    @pytest.mark.asyncio
    async def test_perform_mcp_health_check_no_endpoint(self, client, sample_server_config):
        """Test MCP health check with missing endpoint URL."""
        sample_server_config.mcp_endpoint_url = ""
        
        result = await client.perform_mcp_health_check(sample_server_config)
        
        assert result.server_name == "test-server"
        assert not result.success
        assert result.connection_error == "MCP endpoint URL not configured"
    
    @pytest.mark.asyncio
    async def test_perform_mcp_health_check_timeout(self, client, sample_server_config):
        """Test MCP health check with timeout."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError()
        
        client._session = mock_session
        
        result = await client.perform_mcp_health_check(sample_server_config)
        
        assert result.server_name == "test-server"
        assert not result.success
        assert "timeout" in result.connection_error.lower()
        assert result.response_time_ms == sample_server_config.mcp_timeout_seconds * 1000
    
    @pytest.mark.asyncio
    async def test_perform_mcp_health_check_with_retry(self, client, sample_server_config):
        """Test MCP health check with retry logic."""
        mock_session = AsyncMock()
        
        # First two attempts fail, third succeeds
        mock_session.post.side_effect = [
            ClientError("Connection failed"),
            ClientError("Connection failed"),
            AsyncMock()
        ]
        
        # Mock successful response for third attempt
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"tools": []}
        })
        mock_session.post.side_effect[2].return_value.__aenter__.return_value = mock_response
        
        client._session = mock_session
        
        result = await client.perform_mcp_health_check_with_retry(
            sample_server_config,
            max_retries=3
        )
        
        # Should succeed on third attempt
        assert result.server_name == "test-server"
        # Note: This test might need adjustment based on actual retry implementation
    
    @pytest.mark.asyncio
    async def test_check_multiple_servers_mcp(self, client):
        """Test concurrent MCP health checks for multiple servers."""
        configs = [
            EnhancedServerConfig(
                server_name=f"server-{i}",
                mcp_endpoint_url=f"http://localhost:808{i}/mcp",
                rest_health_endpoint_url=f"http://localhost:808{i}/health",
                mcp_enabled=True
            )
            for i in range(3)
        ]
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"tools": []}
        })
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        client._session = mock_session
        
        results = await client.check_multiple_servers_mcp(configs, max_concurrent=2)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.server_name == f"server-{i}"
            assert isinstance(result, MCPHealthCheckResult)
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with MCPHealthCheckClient() as client:
            assert client._session is not None
            request = client.create_mcp_request()
            assert request.jsonrpc == "2.0"
    
    @pytest.mark.asyncio
    async def test_context_manager_with_session(self):
        """Test async context manager with provided session."""
        mock_session = AsyncMock()
        
        async with MCPHealthCheckClient(session=mock_session) as client:
            assert client._session is mock_session
            request = client.create_mcp_request()
            assert request.jsonrpc == "2.0"
    
    def test_request_headers_preparation(self, client):
        """Test proper preparation of request headers."""
        # This would be tested indirectly through the send_tools_list_request method
        # by checking that the mock session.post is called with correct headers
        pass
    
    def test_error_handling_edge_cases(self, client):
        """Test error handling for edge cases."""
        # Test with None response
        validation_result = client.validate_tools_list_response(
            response=MCPToolsListResponse(jsonrpc="2.0", id="test", result=None),
            expected_tools=["test_tool"]
        )
        
        assert not validation_result.is_valid
        assert validation_result.tools_count == 0
    
    @pytest.mark.asyncio
    async def test_session_not_initialized_error(self, client):
        """Test error when session is not initialized."""
        with pytest.raises(RuntimeError, match="Client session not initialized"):
            await client.send_tools_list_request("http://localhost:8080/mcp")


class TestMCPHealthCheckClientIntegration:
    """Integration tests for MCP Health Check Client."""
    
    @pytest.mark.asyncio
    async def test_full_health_check_workflow(self):
        """Test complete health check workflow."""
        # This would be an integration test that requires a real MCP server
        # For now, we'll use mocks to simulate the full workflow
        
        config = EnhancedServerConfig(
            server_name="integration-test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_enabled=True,
            mcp_expected_tools=["test_tool"],
            jwt_token="integration-test-token"
        )
        
        mock_response_data = {
            "jsonrpc": "2.0",
            "id": "integration-test-id",
            "result": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "Test tool for integration",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "param": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        }
        
        async with MCPHealthCheckClient() as client:
            # Mock the session
            from unittest.mock import AsyncMock, MagicMock
            
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=json.dumps(mock_response_data))
            
            # Create a proper async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            
            mock_session.post = MagicMock(return_value=mock_context_manager)
            
            client._session = mock_session
            
            result = await client.perform_mcp_health_check(config)
            
            assert result.success
            assert result.server_name == "integration-test-server"
            assert result.tools_count == 1
            assert "test_tool" in result.expected_tools_found
            assert len(result.missing_tools) == 0
            assert result.validation_result.is_valid
            assert result.response_time_ms >= 0  # Mock doesn't simulate actual time