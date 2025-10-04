"""
Integration tests for MCP client manager and server communication.

Tests end-to-end communication between the Gateway and MCP servers,
including connection management, error handling, and data flow.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from typing import Dict, Any, List
import httpx
import json

from services.mcp_client_manager import (
    MCPClientManager,
    MCPConnectionPool,
    MCPServerConfig,
    MCPServerHealth,
    MCPServerStatus,
    get_mcp_client_manager,
    shutdown_mcp_client_manager
)


class TestMCPClientServerIntegration:
    """Integration tests for MCP client-server communication."""
    
    @pytest_asyncio.fixture
    async def client_manager(self):
        """Create and start MCP client manager for integration testing."""
        manager = MCPClientManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.fixture
    def mock_server_responses(self):
        """Mock server responses for integration testing."""
        return {
            "search_success": {
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Integration Test Restaurant",
                            "district": "Central district",
                            "address": "123 Integration Street",
                            "sentiment": {"likes": 88, "dislikes": 8, "neutral": 4},
                            "operating_hours": "09:00-22:00",
                            "cuisine_type": "Chinese"
                        },
                        {
                            "id": "rest_002", 
                            "name": "Second Test Restaurant",
                            "district": "Admiralty",
                            "address": "456 Test Avenue",
                            "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3},
                            "operating_hours": "11:00-23:00",
                            "cuisine_type": "Western"
                        }
                    ],
                    "total_count": 2,
                    "search_criteria": {"districts": ["Central district", "Admiralty"]},
                    "execution_time": 0.125
                }
            },
            "reasoning_success": {
                "success": True,
                "data": {
                    "recommendation": {
                        "id": "rest_002",
                        "name": "Second Test Restaurant", 
                        "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3},
                        "score": 0.92,
                        "reasoning": "Highest sentiment score with excellent customer satisfaction"
                    },
                    "candidates": [
                        {
                            "id": "rest_002",
                            "name": "Second Test Restaurant",
                            "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3},
                            "score": 0.92
                        },
                        {
                            "id": "rest_001",
                            "name": "Integration Test Restaurant",
                            "sentiment": {"likes": 88, "dislikes": 8, "neutral": 4},
                            "score": 0.88
                        }
                    ],
                    "ranking_method": "sentiment_likes",
                    "analysis_summary": {
                        "total_restaurants": 2,
                        "average_likes": 90.0,
                        "average_dislikes": 6.5,
                        "top_score": 0.92,
                        "score_distribution": {"excellent": 1, "good": 1, "fair": 0, "poor": 0}
                    }
                }
            },
            "server_error": {
                "success": False,
                "error": {
                    "type": "ServerError",
                    "message": "Internal server error occurred",
                    "code": "INTERNAL_ERROR",
                    "timestamp": "2025-01-03T10:30:00Z"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_search_flow(self, client_manager, mock_server_responses):
        """Test complete end-to-end search flow through MCP client manager."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            # Mock HTTP client
            mock_http_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = mock_server_responses["search_success"]
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client
            
            # Execute search request
            result = await client_manager.call_mcp_tool(
                server_name="restaurant-search",
                tool_name="search_restaurants_by_district",
                parameters={"districts": ["Central district", "Admiralty"]},
                user_context={
                    "user_id": "integration-test-user",
                    "username": "integrationuser",
                    "token": "integration-test-token"
                }
            )
            
            # Verify complete response structure
            assert result["success"] is True
            assert "data" in result
            assert len(result["data"]["restaurants"]) == 2
            assert result["data"]["total_count"] == 2
            assert result["data"]["execution_time"] == 0.125
            
            # Verify restaurant data integrity
            restaurants = result["data"]["restaurants"]
            assert restaurants[0]["id"] == "rest_001"
            assert restaurants[0]["name"] == "Integration Test Restaurant"
            assert restaurants[0]["district"] == "Central district"
            assert restaurants[0]["sentiment"]["likes"] == 88
            
            assert restaurants[1]["id"] == "rest_002"
            assert restaurants[1]["name"] == "Second Test Restaurant"
            assert restaurants[1]["district"] == "Admiralty"
            assert restaurants[1]["sentiment"]["likes"] == 92
            
            # Verify HTTP request was made correctly
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            
            # Verify request structure
            assert call_args[0][0] == "/invoke"
            request_data = call_args[1]["json"]
            assert request_data["tool_name"] == "search_restaurants_by_district"
            assert request_data["parameters"]["districts"] == ["Central district", "Admiralty"]
            
            # Verify authentication headers
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer integration-test-token"
            assert headers["Content-Type"] == "application/json"
            assert headers["X-User-ID"] == "integration-test-user"
    
    @pytest.mark.asyncio
    async def test_end_to_end_reasoning_flow(self, client_manager, mock_server_responses):
        """Test complete end-to-end reasoning flow through MCP client manager."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            # Mock HTTP client
            mock_http_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = mock_server_responses["reasoning_success"]
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client
            
            # Prepare restaurant data for reasoning
            restaurant_data = [
                {
                    "id": "rest_001",
                    "name": "Integration Test Restaurant",
                    "sentiment": {"likes": 88, "dislikes": 8, "neutral": 4},
                    "district": "Central district"
                },
                {
                    "id": "rest_002",
                    "name": "Second Test Restaurant", 
                    "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3},
                    "district": "Admiralty"
                }
            ]
            
            # Execute reasoning request
            result = await client_manager.call_mcp_tool(
                server_name="restaurant-reasoning",
                tool_name="recommend_restaurants",
                parameters={
                    "restaurants": restaurant_data,
                    "ranking_method": "sentiment_likes"
                },
                user_context={
                    "user_id": "integration-test-user",
                    "username": "integrationuser",
                    "token": "integration-test-token"
                }
            )
            
            # Verify complete reasoning response
            assert result["success"] is True
            assert "data" in result
            
            # Verify recommendation
            recommendation = result["data"]["recommendation"]
            assert recommendation["id"] == "rest_002"
            assert recommendation["name"] == "Second Test Restaurant"
            assert recommendation["score"] == 0.92
            assert "reasoning" in recommendation
            
            # Verify candidates list
            candidates = result["data"]["candidates"]
            assert len(candidates) == 2
            assert candidates[0]["score"] >= candidates[1]["score"]  # Should be sorted by score
            
            # Verify analysis summary
            analysis = result["data"]["analysis_summary"]
            assert analysis["total_restaurants"] == 2
            assert analysis["average_likes"] == 90.0
            assert analysis["top_score"] == 0.92
            assert "score_distribution" in analysis
            
            # Verify HTTP request structure
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            request_data = call_args[1]["json"]
            assert request_data["tool_name"] == "recommend_restaurants"
            assert request_data["parameters"]["ranking_method"] == "sentiment_likes"
            assert len(request_data["parameters"]["restaurants"]) == 2
    
    @pytest.mark.asyncio
    async def test_connection_pool_integration(self, client_manager):
        """Test connection pool behavior in integration scenarios."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            # Track connection reuse
            mock_http_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {"success": True, "data": {"restaurants": []}}
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client
            
            # Make multiple requests to same server
            for i in range(5):
                await client_manager.call_mcp_tool(
                    server_name="restaurant-search",
                    tool_name="search_restaurants_by_district",
                    parameters={"districts": [f"District_{i}"]},
                    user_context={"user_id": f"user_{i}", "token": f"token_{i}"}
                )
            
            # Verify connection reuse
            assert mock_get_client.call_count == 5  # Should get client for each request
            assert mock_http_client.post.call_count == 5  # Should reuse same client
            
            # Verify each request had correct parameters
            for call_idx, call in enumerate(mock_http_client.post.call_args_list):
                request_data = call[1]["json"]
                assert request_data["parameters"]["districts"] == [f"District_{call_idx}"]
                
                headers = call[1]["headers"]
                assert headers["Authorization"] == f"Bearer token_{call_idx}"
                assert headers["X-User-ID"] == f"user_{call_idx}"
    
    @pytest.mark.asyncio
    async def test_error_propagation_integration(self, client_manager, mock_server_responses):
        """Test error propagation through the integration stack."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            # Test different error scenarios
            error_scenarios = [
                {
                    "name": "HTTP 500 Error",
                    "status_code": 500,
                    "response": mock_server_responses["server_error"],
                    "expected_exception": httpx.RequestError
                },
                {
                    "name": "HTTP 404 Error", 
                    "status_code": 404,
                    "response": {"error": "Tool not found"},
                    "expected_exception": httpx.RequestError
                },
                {
                    "name": "Connection Timeout",
                    "exception": httpx.TimeoutException("Request timeout"),
                    "expected_exception": httpx.TimeoutException
                },
                {
                    "name": "Connection Error",
                    "exception": httpx.ConnectError("Connection failed"),
                    "expected_exception": httpx.ConnectError
                }
            ]
            
            for scenario in error_scenarios:
                mock_http_client = AsyncMock()
                
                if "exception" in scenario:
                    # Mock client raises exception
                    mock_http_client.post.side_effect = scenario["exception"]
                else:
                    # Mock HTTP error response
                    mock_response = Mock()
                    mock_response.json.return_value = scenario["response"]
                    mock_response.status_code = scenario["status_code"]
                    mock_response.raise_for_status.side_effect = httpx.RequestError(
                        f"HTTP {scenario['status_code']}"
                    )
                    mock_http_client.post.return_value = mock_response
                
                mock_get_client.return_value = mock_http_client
                
                # Verify error is properly propagated
                with pytest.raises(scenario["expected_exception"]):
                    await client_manager.call_mcp_tool(
                        server_name="restaurant-search",
                        tool_name="search_restaurants_by_district",
                        parameters={"districts": ["Central district"]},
                        user_context={"user_id": "error-test-user", "token": "error-token"}
                    )
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, client_manager):
        """Test health monitoring integration with MCP servers."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            # Mock health check responses
            health_scenarios = [
                {
                    "server": "restaurant-search",
                    "status_code": 200,
                    "response": {"status": "healthy", "uptime": 3600, "version": "1.0.0"},
                    "expected_status": MCPServerStatus.HEALTHY
                },
                {
                    "server": "restaurant-reasoning",
                    "status_code": 503,
                    "response": {"status": "unhealthy", "error": "Database connection failed"},
                    "expected_status": MCPServerStatus.UNHEALTHY
                }
            ]
            
            for scenario in health_scenarios:
                mock_http_client = AsyncMock()
                mock_response = Mock()
                mock_response.json.return_value = scenario["response"]
                mock_response.status_code = scenario["status_code"]
                
                if scenario["status_code"] == 200:
                    mock_response.raise_for_status.return_value = None
                else:
                    mock_response.raise_for_status.side_effect = httpx.RequestError(
                        f"HTTP {scenario['status_code']}"
                    )
                
                mock_http_client.get.return_value = mock_response
                mock_get_client.return_value = mock_http_client
                
                # Check server health
                health = await client_manager.check_server_health(scenario["server"])
                
                # Verify health status
                assert health.status == scenario["expected_status"]
                
                if scenario["expected_status"] == MCPServerStatus.HEALTHY:
                    assert health.response_time is not None
                    assert health.response_time > 0
                    assert health.consecutive_failures == 0
                    assert health.error_message is None
                else:
                    assert health.consecutive_failures > 0
                    assert health.error_message is not None
                
                # Verify health check request
                mock_http_client.get.assert_called_with("/health", timeout=30)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_integration(self, client_manager):
        """Test concurrent request handling in integration environment."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            # Mock HTTP client with realistic response times
            mock_http_client = AsyncMock()
            
            async def mock_post(*args, **kwargs):
                # Simulate realistic response time
                await asyncio.sleep(0.1)
                mock_response = Mock()
                mock_response.json.return_value = {
                    "success": True,
                    "data": {"restaurants": [], "request_id": kwargs.get("json", {}).get("request_id")}
                }
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                return mock_response
            
            mock_http_client.post = mock_post
            mock_get_client.return_value = mock_http_client
            
            # Execute concurrent requests
            num_concurrent = 10
            start_time = time.time()
            
            tasks = []
            for i in range(num_concurrent):
                task = client_manager.call_mcp_tool(
                    server_name="restaurant-search",
                    tool_name="search_restaurants_by_district",
                    parameters={"districts": ["Central district"], "request_id": i},
                    user_context={"user_id": f"concurrent_user_{i}", "token": f"token_{i}"}
                )
                tasks.append(task)
            
            # Wait for all requests to complete
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Verify all requests completed successfully
            assert len(results) == num_concurrent
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["data"]["request_id"] == i
            
            # Verify concurrent execution was efficient
            total_time = end_time - start_time
            # Should complete in roughly the time of a single request (due to concurrency)
            # Allow some overhead for test environment
            assert total_time < 0.5, f"Concurrent requests took {total_time:.2f}s, should be under 0.5s"
            
            print(f"Concurrent integration test: {num_concurrent} requests in {total_time:.3f}s")


class TestMCPServerCommunicationProtocol:
    """Test MCP server communication protocol compliance."""
    
    @pytest_asyncio.fixture
    async def protocol_client_manager(self):
        """Create client manager for protocol testing."""
        manager = MCPClientManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_mcp_request_protocol_compliance(self, protocol_client_manager):
        """Test MCP request protocol compliance."""
        with patch.object(protocol_client_manager.connection_pool, 'get_client') as mock_get_client:
            mock_http_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {"success": True, "data": {}}
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client
            
            # Test protocol-compliant request
            await protocol_client_manager.call_mcp_tool(
                server_name="restaurant-search",
                tool_name="search_restaurants_by_district",
                parameters={"districts": ["Central district"]},
                user_context={
                    "user_id": "protocol-test-user",
                    "username": "protocoluser",
                    "token": "protocol-token",
                    "session_id": "session-123"
                }
            )
            
            # Verify protocol compliance
            call_args = mock_http_client.post.call_args
            
            # Verify endpoint
            assert call_args[0][0] == "/invoke"
            
            # Verify request structure
            request_data = call_args[1]["json"]
            assert "tool_name" in request_data
            assert "parameters" in request_data
            assert request_data["tool_name"] == "search_restaurants_by_district"
            assert isinstance(request_data["parameters"], dict)
            
            # Verify headers
            headers = call_args[1]["headers"]
            assert headers["Content-Type"] == "application/json"
            assert headers["Authorization"] == "Bearer protocol-token"
            assert headers["X-User-ID"] == "protocol-test-user"
            assert headers["X-Session-ID"] == "session-123"
            
            # Verify timeout is set
            assert "timeout" in call_args[1]
            assert call_args[1]["timeout"] == 30
    
    @pytest.mark.asyncio
    async def test_mcp_response_protocol_handling(self, protocol_client_manager):
        """Test MCP response protocol handling."""
        with patch.object(protocol_client_manager.connection_pool, 'get_client') as mock_get_client:
            # Test various protocol-compliant response formats
            response_formats = [
                # Standard success response
                {
                    "success": True,
                    "data": {"restaurants": []},
                    "metadata": {"server_version": "1.0", "execution_time": 0.123}
                },
                # Error response
                {
                    "success": False,
                    "error": {
                        "type": "ValidationError",
                        "message": "Invalid parameters",
                        "code": "INVALID_PARAMS",
                        "details": {"field": "districts", "issue": "required"}
                    }
                },
                # Minimal response
                {
                    "success": True,
                    "data": {}
                }
            ]
            
            for response_format in response_formats:
                mock_http_client = AsyncMock()
                mock_response = Mock()
                mock_response.json.return_value = response_format
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                mock_http_client.post.return_value = mock_response
                mock_get_client.return_value = mock_http_client
                
                # Should handle all protocol-compliant responses
                result = await protocol_client_manager.call_mcp_tool(
                    server_name="restaurant-search",
                    tool_name="search_restaurants_by_district",
                    parameters={"districts": ["Central district"]}
                )
                
                # Should return response as-is for protocol compliance
                assert result == response_format
    
    @pytest.mark.asyncio
    async def test_authentication_protocol_integration(self, protocol_client_manager):
        """Test authentication protocol integration."""
        with patch.object(protocol_client_manager.connection_pool, 'get_client') as mock_get_client:
            mock_http_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {"success": True, "data": {}}
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client
            
            # Test different authentication contexts
            auth_contexts = [
                {
                    "user_id": "user1",
                    "username": "testuser1",
                    "token": "jwt-token-1",
                    "email": "user1@test.com",
                    "roles": ["user"]
                },
                {
                    "user_id": "admin1",
                    "username": "adminuser",
                    "token": "jwt-admin-token",
                    "email": "admin@test.com", 
                    "roles": ["admin", "user"]
                }
            ]
            
            for auth_context in auth_contexts:
                await protocol_client_manager.call_mcp_tool(
                    server_name="restaurant-search",
                    tool_name="search_restaurants_by_district",
                    parameters={"districts": ["Central district"]},
                    user_context=auth_context
                )
                
                # Verify authentication headers are properly set
                call_args = mock_http_client.post.call_args
                headers = call_args[1]["headers"]
                
                assert headers["Authorization"] == f"Bearer {auth_context['token']}"
                assert headers["X-User-ID"] == auth_context["user_id"]
                
                # Optional headers should be included if present
                if "email" in auth_context:
                    assert headers["X-User-Email"] == auth_context["email"]
                if "roles" in auth_context:
                    assert headers["X-User-Roles"] == ",".join(auth_context["roles"])


class TestDataFlowIntegration:
    """Test data flow integration between Gateway and MCP servers."""
    
    @pytest_asyncio.fixture
    async def data_flow_manager(self):
        """Create client manager for data flow testing."""
        manager = MCPClientManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_search_to_reasoning_data_flow(self, data_flow_manager):
        """Test data flow from search to reasoning operations."""
        with patch.object(data_flow_manager.connection_pool, 'get_client') as mock_get_client:
            # Mock search response
            search_response = {
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "flow_rest_001",
                            "name": "Flow Test Restaurant 1",
                            "district": "Central district",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                        },
                        {
                            "id": "flow_rest_002",
                            "name": "Flow Test Restaurant 2", 
                            "district": "Admiralty",
                            "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3}
                        }
                    ],
                    "total_count": 2
                }
            }
            
            # Mock reasoning response
            reasoning_response = {
                "success": True,
                "data": {
                    "recommendation": {
                        "id": "flow_rest_002",
                        "name": "Flow Test Restaurant 2",
                        "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3},
                        "score": 0.92
                    },
                    "candidates": [
                        {"id": "flow_rest_002", "score": 0.92},
                        {"id": "flow_rest_001", "score": 0.85}
                    ],
                    "ranking_method": "sentiment_likes"
                }
            }
            
            # Setup mock responses
            mock_http_client = AsyncMock()
            responses = [search_response, reasoning_response]
            response_iter = iter(responses)
            
            async def mock_post(*args, **kwargs):
                mock_response = Mock()
                mock_response.json.return_value = next(response_iter)
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                return mock_response
            
            mock_http_client.post = mock_post
            mock_get_client.return_value = mock_http_client
            
            # Step 1: Search for restaurants
            search_result = await data_flow_manager.call_mcp_tool(
                server_name="restaurant-search",
                tool_name="search_restaurants_by_district",
                parameters={"districts": ["Central district", "Admiralty"]},
                user_context={"user_id": "flow-test-user", "token": "flow-token"}
            )
            
            # Verify search result
            assert search_result["success"] is True
            restaurants = search_result["data"]["restaurants"]
            assert len(restaurants) == 2
            
            # Step 2: Use search results for reasoning
            reasoning_result = await data_flow_manager.call_mcp_tool(
                server_name="restaurant-reasoning",
                tool_name="recommend_restaurants",
                parameters={
                    "restaurants": restaurants,
                    "ranking_method": "sentiment_likes"
                },
                user_context={"user_id": "flow-test-user", "token": "flow-token"}
            )
            
            # Verify reasoning result
            assert reasoning_result["success"] is True
            recommendation = reasoning_result["data"]["recommendation"]
            assert recommendation["id"] == "flow_rest_002"
            assert recommendation["score"] == 0.92
            
            # Verify data consistency between operations
            candidates = reasoning_result["data"]["candidates"]
            assert len(candidates) == 2
            
            # Verify the data flowed correctly from search to reasoning
            search_ids = {r["id"] for r in restaurants}
            candidate_ids = {c["id"] for c in candidates}
            assert search_ids == candidate_ids
    
    @pytest.mark.asyncio
    async def test_complex_parameter_data_flow(self, data_flow_manager):
        """Test complex parameter data flow through MCP operations."""
        with patch.object(data_flow_manager.connection_pool, 'get_client') as mock_get_client:
            # Test complex nested parameters
            complex_parameters = {
                "districts": ["Central district", "Admiralty", "Causeway Bay"],
                "meal_types": ["breakfast", "lunch", "dinner"],
                "filters": {
                    "price_range": {"min": 50, "max": 200},
                    "cuisine_types": ["Chinese", "Western", "Japanese"],
                    "ratings": {"min_likes": 80, "max_dislikes": 15}
                },
                "sorting": {
                    "primary": "sentiment_score",
                    "secondary": "distance",
                    "order": "desc"
                },
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "offset": 0
                }
            }
            
            mock_http_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "restaurants": [],
                    "total_count": 0,
                    "applied_filters": complex_parameters["filters"],
                    "sorting_applied": complex_parameters["sorting"]
                }
            }
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client
            
            # Execute request with complex parameters
            result = await data_flow_manager.call_mcp_tool(
                server_name="restaurant-search",
                tool_name="search_restaurants_combined",
                parameters=complex_parameters,
                user_context={"user_id": "complex-test-user", "token": "complex-token"}
            )
            
            # Verify complex parameters were passed correctly
            call_args = mock_http_client.post.call_args
            request_data = call_args[1]["json"]
            
            assert request_data["parameters"] == complex_parameters
            assert request_data["parameters"]["filters"]["price_range"]["min"] == 50
            assert request_data["parameters"]["sorting"]["primary"] == "sentiment_score"
            assert request_data["parameters"]["pagination"]["limit"] == 20
            
            # Verify response handling
            assert result["success"] is True
            assert result["data"]["applied_filters"] == complex_parameters["filters"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])