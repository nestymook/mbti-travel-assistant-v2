"""
Tests for native MCP tool discovery functionality.

This module tests the native MCP tool discovery implementation that aggregates
schemas from MCP servers and provides foundation models with comprehensive
tool metadata through the standard MCP protocol interface.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from services.tool_metadata_service import ToolMetadataService
from services.mcp_client_manager import MCPClientManager, MCPServerHealth, MCPServerStatus
from models.tool_metadata_models import MCPToolDiscoveryResponse, AggregatedServerInfo


class TestNativeMCPToolDiscovery:
    """Test cases for native MCP tool discovery functionality."""
    
    @pytest_asyncio.fixture
    async def metadata_service(self):
        """Create a tool metadata service for testing."""
        service = ToolMetadataService()
        yield service
    
    @pytest_asyncio.fixture
    async def mock_mcp_client_manager(self):
        """Create a mock MCP client manager."""
        manager = AsyncMock(spec=MCPClientManager)
        
        # Mock available tools
        manager.get_available_tools.return_value = {
            "restaurant-search": [
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ],
            "restaurant-reasoning": [
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ]
        }
        
        # Mock server health status
        manager.is_server_healthy.return_value = True
        
        # Mock tool calls for schema extraction
        async def mock_call_tool(server_name, tool_name, parameters, user_context=None):
            if not parameters:
                # Simulate validation error for empty parameters
                if "district" in tool_name:
                    raise Exception("Missing required parameter: districts")
                elif "meal_type" in tool_name:
                    raise Exception("Missing required parameter: meal_types")
                elif "recommend" in tool_name:
                    raise Exception("Missing required parameter: restaurants")
                else:
                    # Tool accepts empty parameters
                    return {"success": True, "result": "test"}
            return {"success": True, "result": "test"}
        
        manager.call_mcp_tool.side_effect = mock_call_tool
        
        return manager
    
    @pytest.mark.asyncio
    async def test_get_native_mcp_tool_discovery_success(self, metadata_service, mock_mcp_client_manager):
        """Test successful native MCP tool discovery response generation."""
        # Mock the MCP client manager
        with patch('services.mcp_client_manager.get_mcp_client_manager', return_value=mock_mcp_client_manager):
            metadata_service._mcp_client_manager = mock_mcp_client_manager
            
            # Generate MCP tool discovery response
            response = await metadata_service.get_native_mcp_tool_discovery(request_id=123)
            
            # Verify response structure
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 123
            assert "result" in response
            assert "tools" in response["result"]
            assert "_meta" in response["result"]
            
            # Verify tools are present
            tools = response["result"]["tools"]
            assert len(tools) == 5  # 5 tools total from both servers
            
            # Verify tool structure
            for tool in tools:
                assert "name" in tool
                assert "description" in tool
                assert "inputSchema" in tool
                assert "_meta" in tool
                
                # Verify JSON Schema format
                input_schema = tool["inputSchema"]
                assert input_schema["type"] == "object"
                assert "properties" in input_schema
                assert "required" in input_schema
            
            # Verify metadata
            meta = response["result"]["_meta"]
            assert "gateway_version" in meta
            assert "total_tools" in meta
            assert "categories" in meta
            assert "supported_mbti_types" in meta
            assert "last_updated" in meta
    
    @pytest.mark.asyncio
    async def test_get_native_mcp_tool_discovery_error_handling(self, metadata_service):
        """Test error handling in native MCP tool discovery."""
        # Mock failure in metadata generation
        with patch.object(metadata_service, 'get_all_tools_metadata', side_effect=Exception("Test error")):
            response = await metadata_service.get_native_mcp_tool_discovery(request_id=456)
            
            # Verify error response structure
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 456
            assert "error" in response
            assert response["error"]["code"] == -32603
            assert response["error"]["message"] == "Internal error"
            assert "data" in response["error"]
            assert response["error"]["data"]["error_type"] == "ToolDiscoveryError"
    
    @pytest.mark.asyncio
    async def test_aggregate_schemas_from_mcp_servers(self, metadata_service, mock_mcp_client_manager):
        """Test schema aggregation from MCP servers."""
        # Mock the MCP client manager
        metadata_service._mcp_client_manager = mock_mcp_client_manager
        
        # Perform schema aggregation
        await metadata_service._aggregate_schemas_from_mcp_servers()
        
        # Verify aggregation results
        assert metadata_service._aggregated_schemas is not None
        assert len(metadata_service._aggregated_schemas) == 2  # Two servers
        assert "restaurant-search" in metadata_service._aggregated_schemas
        assert "restaurant-reasoning" in metadata_service._aggregated_schemas
        
        # Verify server information
        for server_name, server_info in metadata_service._aggregated_schemas.items():
            assert "tools" in server_info
            assert "last_updated" in server_info
            assert "server_status" in server_info
            assert server_info["server_status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_extract_tool_schema_from_validation_errors(self, metadata_service, mock_mcp_client_manager):
        """Test tool schema extraction from validation error messages."""
        metadata_service._mcp_client_manager = mock_mcp_client_manager
        
        # Test schema extraction for district search tool
        schema = await metadata_service._extract_tool_schema("restaurant-search", "search_restaurants_by_district")
        
        assert schema is not None
        assert schema["name"] == "search_restaurants_by_district"
        assert schema["server"] == "restaurant-search"
        assert "parameters" in schema
        assert "districts" in schema["parameters"]
        assert schema["parameters"]["districts"]["type"] == "array"
        assert schema["parameters"]["districts"]["required"] is True
    
    @pytest.mark.asyncio
    async def test_extract_tool_schema_no_required_params(self, metadata_service, mock_mcp_client_manager):
        """Test tool schema extraction for tools with no required parameters."""
        # Mock a tool that accepts empty parameters
        async def mock_call_tool_success(server_name, tool_name, parameters, user_context=None):
            return {"success": True, "result": "test"}
        
        mock_mcp_client_manager.call_mcp_tool.side_effect = mock_call_tool_success
        metadata_service._mcp_client_manager = mock_mcp_client_manager
        
        # Test schema extraction
        schema = await metadata_service._extract_tool_schema("test-server", "test_tool")
        
        assert schema is not None
        assert schema["name"] == "test_tool"
        assert schema["server"] == "test-server"
        assert schema["parameters"] == {}
        assert schema["required_parameters"] == []
        assert schema["extraction_method"] == "successful_empty_call"
    
    def test_convert_to_json_schema(self, metadata_service):
        """Test conversion of ParameterSchema to JSON Schema format."""
        from models.tool_metadata_models import ParameterSchema, ParameterType
        
        # Create test parameters
        parameters = {
            "districts": ParameterSchema(
                type=ParameterType.ARRAY,
                description="List of Hong Kong districts",
                required=True,
                min_items=1,
                max_items=20,
                example=["Central district", "Admiralty"]
            ),
            "meal_types": ParameterSchema(
                type=ParameterType.ARRAY,
                description="List of meal types",
                required=False,
                enum=["breakfast", "lunch", "dinner"],
                default=["lunch"]
            )
        }
        
        # Convert to JSON Schema
        json_schema = metadata_service._convert_to_json_schema(parameters)
        
        # Verify structure
        assert json_schema["type"] == "object"
        assert "properties" in json_schema
        assert "required" in json_schema
        
        # Verify districts parameter
        districts_prop = json_schema["properties"]["districts"]
        assert districts_prop["type"] == "array"
        assert districts_prop["description"] == "List of Hong Kong districts"
        assert districts_prop["minItems"] == 1
        assert districts_prop["maxItems"] == 20
        assert "examples" in districts_prop
        
        # Verify meal_types parameter
        meal_types_prop = json_schema["properties"]["meal_types"]
        assert meal_types_prop["type"] == "array"
        assert meal_types_prop["enum"] == ["breakfast", "lunch", "dinner"]
        assert meal_types_prop["default"] == ["lunch"]
        
        # Verify required fields
        assert "districts" in json_schema["required"]
        assert "meal_types" not in json_schema["required"]
    
    def test_convert_to_json_schema_empty_parameters(self, metadata_service):
        """Test JSON Schema conversion with empty parameters."""
        json_schema = metadata_service._convert_to_json_schema({})
        
        assert json_schema["type"] == "object"
        assert json_schema["properties"] == {}
        assert json_schema["required"] == []
    
    def test_get_aggregated_server_info_no_aggregation(self, metadata_service):
        """Test getting server info when no aggregation has been performed."""
        info = metadata_service.get_aggregated_server_info()
        
        assert info["servers"] == {}
        assert info["total_servers"] == 0
        assert info["healthy_servers"] == 0
        assert info["last_aggregation"] is None
        assert info["aggregation_status"] == "not_started"
    
    def test_get_aggregated_server_info_with_data(self, metadata_service):
        """Test getting server info with aggregated data."""
        # Mock aggregated data
        metadata_service._aggregated_schemas = {
            "server1": {
                "tools": {"tool1": {}, "tool2": {}},
                "last_updated": datetime(2025, 1, 3, 10, 30, 0),
                "server_status": "healthy"
            },
            "server2": {
                "tools": {"tool3": {}},
                "last_updated": datetime(2025, 1, 3, 10, 31, 0),
                "server_status": "schema_error",
                "error": "Connection failed"
            }
        }
        metadata_service._last_schema_update = datetime(2025, 1, 3, 10, 32, 0)
        
        info = metadata_service.get_aggregated_server_info()
        
        assert info["total_servers"] == 2
        assert info["healthy_servers"] == 1
        assert info["aggregation_status"] == "completed"
        assert "server1" in info["servers"]
        assert "server2" in info["servers"]
        
        # Verify server1 info
        server1_info = info["servers"]["server1"]
        assert server1_info["tool_count"] == 2
        assert server1_info["status"] == "healthy"
        assert server1_info["error"] is None
        
        # Verify server2 info
        server2_info = info["servers"]["server2"]
        assert server2_info["tool_count"] == 1
        assert server2_info["status"] == "schema_error"
        assert server2_info["error"] == "Connection failed"


class TestMCPToolDiscoveryModels:
    """Test cases for MCP tool discovery data models."""
    
    def test_mcp_tool_schema_model(self):
        """Test MCPToolSchema model validation."""
        from models.tool_metadata_models import MCPToolSchema
        
        tool_data = {
            "name": "test_tool",
            "description": "Test tool description",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Test parameter"}
                },
                "required": ["param1"]
            },
            "_meta": {
                "category": "test",
                "endpoint": "/test"
            }
        }
        
        tool = MCPToolSchema(**tool_data)
        
        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.inputSchema["type"] == "object"
        assert tool.meta["category"] == "test"
    
    def test_mcp_tool_discovery_response_model(self):
        """Test MCPToolDiscoveryResponse model validation."""
        from models.tool_metadata_models import MCPToolDiscoveryResponse
        
        response_data = {
            "jsonrpc": "2.0",
            "id": 123,
            "result": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "Test tool",
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ],
                "_meta": {
                    "total_tools": 1
                }
            }
        }
        
        response = MCPToolDiscoveryResponse(**response_data)
        
        assert response.jsonrpc == "2.0"
        assert response.id == 123
        assert response.result is not None
        assert response.error is None
    
    def test_mcp_tool_discovery_response_error(self):
        """Test MCPToolDiscoveryResponse with error."""
        from models.tool_metadata_models import MCPToolDiscoveryResponse
        
        response_data = {
            "jsonrpc": "2.0",
            "id": 456,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": {"error_type": "TestError"}
            }
        }
        
        response = MCPToolDiscoveryResponse(**response_data)
        
        assert response.jsonrpc == "2.0"
        assert response.id == 456
        assert response.result is None
        assert response.error is not None
        assert response.error["code"] == -32603
    
    def test_aggregated_server_info_model(self):
        """Test AggregatedServerInfo model validation."""
        from models.tool_metadata_models import AggregatedServerInfo
        
        info_data = {
            "servers": {
                "server1": {
                    "tool_count": 3,
                    "status": "healthy",
                    "last_updated": "2025-01-03T10:30:00Z",
                    "error": None
                }
            },
            "total_servers": 1,
            "healthy_servers": 1,
            "last_aggregation": "2025-01-03T10:30:00Z",
            "aggregation_status": "completed"
        }
        
        info = AggregatedServerInfo(**info_data)
        
        assert info.total_servers == 1
        assert info.healthy_servers == 1
        assert info.aggregation_status == "completed"
        assert "server1" in info.servers
        assert info.servers["server1"]["tool_count"] == 3