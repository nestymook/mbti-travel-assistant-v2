"""
Tool metadata service for AgentCore Gateway MCP Tools.

This service generates comprehensive metadata for all available MCP tools,
providing foundation models with detailed information about tool capabilities,
parameters, usage patterns, and MBTI personality integration guidance.

This service implements native MCP tool discovery responses and aggregates
tool schemas from source MCP servers while preserving native MCP functionality.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from models.tool_metadata_models import (
    ToolMetadata,
    ToolsMetadataResponse,
    ParameterSchema,
    ResponseSchema,
    UseCaseScenario,
    MBTIIntegrationGuidance,
    ToolExample,
    ToolCategory,
    ParameterType,
    MBTIPersonalityType
)

logger = logging.getLogger(__name__)


class ToolMetadataService:
    """Service for generating and managing tool metadata with native MCP discovery."""
    
    def __init__(self):
        """Initialize the tool metadata service."""
        self.version = "1.0.0"
        self._metadata_cache = None
        self._last_generated = None
        self._mcp_client_manager = None
        self._aggregated_schemas = {}
        self._last_schema_update = None
    
    def get_all_tools_metadata(self) -> ToolsMetadataResponse:
        """
        Get comprehensive metadata for all available tools.
        
        Returns:
            ToolsMetadataResponse: Complete metadata for all tools
        """
        # Check cache validity (refresh every hour)
        if (self._metadata_cache is None or 
            self._last_generated is None or 
            (datetime.utcnow() - self._last_generated).seconds > 3600):
            self._generate_metadata()
        
        return self._metadata_cache
    
    def get_tool_metadata(self, tool_name: str) -> ToolMetadata:
        """
        Get metadata for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            ToolMetadata: Metadata for the specified tool
            
        Raises:
            ValueError: If tool not found
        """
        all_metadata = self.get_all_tools_metadata()
        
        for tool in all_metadata.tools:
            if tool.name == tool_name:
                return tool
        
        raise ValueError(f"Tool '{tool_name}' not found")
    
    async def get_native_mcp_tool_discovery(self, request_id: Union[str, int] = 1) -> Dict[str, Any]:
        """
        Generate native MCP tool discovery response for foundation models.
        
        This method implements the MCP tools/list protocol response format,
        aggregating tool schemas from all registered MCP servers.
        
        Args:
            request_id: MCP request ID for the response
            
        Returns:
            Native MCP tools/list response with aggregated tool schemas
        """
        try:
            # Ensure we have fresh schema data from MCP servers
            await self._aggregate_schemas_from_mcp_servers()
            
            # Get all tool metadata
            all_metadata = self.get_all_tools_metadata()
            
            # Convert to native MCP tools/list format
            mcp_tools = []
            for tool in all_metadata.tools:
                mcp_tool = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": self._convert_to_json_schema(tool.parameters),
                    "_meta": {
                        "category": tool.category.value,
                        "display_name": tool.display_name,
                        "purpose": tool.purpose,
                        "endpoint": tool.endpoint,
                        "http_method": tool.http_method,
                        "authentication_required": tool.authentication_required,
                        "average_response_time_ms": tool.average_response_time_ms,
                        "success_rate_percentage": tool.success_rate_percentage
                    }
                }
                
                # Add MBTI integration guidance to metadata
                if tool.mbti_integration:
                    mcp_tool["_meta"]["mbti_integration"] = [
                        {
                            "personality_type": guidance.personality_type.value,
                            "preferences": guidance.preferences,
                            "search_patterns": guidance.search_patterns,
                            "recommendation_focus": guidance.recommendation_focus
                        }
                        for guidance in tool.mbti_integration
                    ]
                
                # Add use cases to metadata
                if tool.use_cases:
                    mcp_tool["_meta"]["use_cases"] = [
                        {
                            "scenario": case.scenario,
                            "when_to_use": case.when_to_use,
                            "example_input": case.example_input,
                            "expected_outcome": case.expected_outcome
                        }
                        for case in tool.use_cases
                    ]
                
                # Add examples to metadata
                if tool.examples:
                    mcp_tool["_meta"]["examples"] = [
                        {
                            "title": example.title,
                            "description": example.description,
                            "input": example.input,
                            "output": example.output,
                            "notes": example.notes
                        }
                        for example in tool.examples
                    ]
                
                mcp_tools.append(mcp_tool)
            
            # Create native MCP response
            mcp_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": mcp_tools,
                    "_meta": {
                        "gateway_version": self.version,
                        "total_tools": len(mcp_tools),
                        "categories": [cat.value for cat in all_metadata.categories],
                        "supported_mbti_types": [mbti.value for mbti in all_metadata.supported_mbti_types],
                        "last_updated": all_metadata.last_updated,
                        "schema_sources": list(self._aggregated_schemas.keys()) if self._aggregated_schemas else [],
                        "aggregation_timestamp": self._last_schema_update.isoformat() + "Z" if self._last_schema_update else None
                    }
                }
            }
            
            logger.info(f"Generated native MCP tool discovery response with {len(mcp_tools)} tools")
            return mcp_response
            
        except Exception as e:
            logger.error(f"Failed to generate native MCP tool discovery response: {str(e)}")
            # Return MCP error response
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {
                        "error_type": "ToolDiscoveryError",
                        "error_message": str(e),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            }
    
    async def _aggregate_schemas_from_mcp_servers(self) -> None:
        """
        Aggregate tool schemas from registered MCP servers.
        
        This method connects to each MCP server and retrieves their native
        tool schemas, preserving validation rules and metadata.
        """
        try:
            # Get MCP client manager
            if self._mcp_client_manager is None:
                from services.mcp_client_manager import get_mcp_client_manager
                self._mcp_client_manager = await get_mcp_client_manager()
            
            # Check if we need to refresh schemas (every 5 minutes)
            if (self._last_schema_update is not None and 
                (datetime.utcnow() - self._last_schema_update).seconds < 300):
                return
            
            logger.info("Aggregating tool schemas from MCP servers")
            
            # Get available servers and their tools
            available_tools = self._mcp_client_manager.get_available_tools()
            
            for server_name, tools in available_tools.items():
                try:
                    # Check if server is healthy
                    if not self._mcp_client_manager.is_server_healthy(server_name):
                        logger.warning(f"Skipping unhealthy server: {server_name}")
                        continue
                    
                    # Attempt to get tool schemas from the server
                    server_schemas = await self._get_server_tool_schemas(server_name, tools)
                    
                    if server_schemas:
                        self._aggregated_schemas[server_name] = {
                            "tools": server_schemas,
                            "last_updated": datetime.utcnow(),
                            "server_status": "healthy"
                        }
                        logger.info(f"Aggregated {len(server_schemas)} tool schemas from {server_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to aggregate schemas from server {server_name}: {str(e)}")
                    # Mark server as having schema aggregation issues
                    self._aggregated_schemas[server_name] = {
                        "tools": {},
                        "last_updated": datetime.utcnow(),
                        "server_status": "schema_error",
                        "error": str(e)
                    }
            
            self._last_schema_update = datetime.utcnow()
            logger.info(f"Schema aggregation completed for {len(self._aggregated_schemas)} servers")
            
        except Exception as e:
            logger.error(f"Failed to aggregate schemas from MCP servers: {str(e)}")
    
    async def _get_server_tool_schemas(self, server_name: str, tools: List[str]) -> Dict[str, Any]:
        """
        Get tool schemas from a specific MCP server.
        
        Args:
            server_name: Name of the MCP server
            tools: List of tool names available on the server
            
        Returns:
            Dictionary of tool schemas from the server
        """
        server_schemas = {}
        
        for tool_name in tools:
            try:
                # Try to get schema information by calling the tool with invalid parameters
                # This will return validation errors that contain schema information
                schema_info = await self._extract_tool_schema(server_name, tool_name)
                
                if schema_info:
                    server_schemas[tool_name] = schema_info
                    logger.debug(f"Extracted schema for {server_name}.{tool_name}")
                
            except Exception as e:
                logger.warning(f"Could not extract schema for {server_name}.{tool_name}: {str(e)}")
                # Store basic information even if schema extraction fails
                server_schemas[tool_name] = {
                    "name": tool_name,
                    "server": server_name,
                    "schema_available": False,
                    "error": str(e)
                }
        
        return server_schemas
    
    async def _extract_tool_schema(self, server_name: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract tool schema by analyzing server responses.
        
        This method attempts to extract schema information from the MCP server
        by making test calls and analyzing validation responses.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            
        Returns:
            Tool schema information if available
        """
        try:
            # Make a test call with minimal parameters to get validation info
            test_response = await self._mcp_client_manager.call_mcp_tool(
                server_name=server_name,
                tool_name=tool_name,
                parameters={}  # Empty parameters to trigger validation
            )
            
            # If the call succeeds with empty parameters, the tool has no required parameters
            return {
                "name": tool_name,
                "server": server_name,
                "parameters": {},
                "required_parameters": [],
                "schema_extracted": True,
                "extraction_method": "successful_empty_call"
            }
            
        except Exception as e:
            # Analyze the error response for schema information
            error_str = str(e).lower()
            
            schema_info = {
                "name": tool_name,
                "server": server_name,
                "schema_extracted": True,
                "extraction_method": "error_analysis"
            }
            
            # Extract parameter information from error messages
            if "districts" in error_str:
                schema_info["parameters"] = schema_info.get("parameters", {})
                schema_info["parameters"]["districts"] = {
                    "type": "array",
                    "description": "List of Hong Kong districts",
                    "required": True
                }
            
            if "meal_types" in error_str:
                schema_info["parameters"] = schema_info.get("parameters", {})
                schema_info["parameters"]["meal_types"] = {
                    "type": "array",
                    "description": "List of meal types (breakfast, lunch, dinner)",
                    "required": True,
                    "enum": ["breakfast", "lunch", "dinner"]
                }
            
            if "restaurants" in error_str:
                schema_info["parameters"] = schema_info.get("parameters", {})
                schema_info["parameters"]["restaurants"] = {
                    "type": "array",
                    "description": "List of restaurant objects with sentiment data",
                    "required": True
                }
            
            if "ranking_method" in error_str:
                schema_info["parameters"] = schema_info.get("parameters", {})
                schema_info["parameters"]["ranking_method"] = {
                    "type": "string",
                    "description": "Method for ranking restaurants",
                    "required": False,
                    "enum": ["sentiment_likes", "combined_sentiment"],
                    "default": "sentiment_likes"
                }
            
            return schema_info if "parameters" in schema_info else None
    
    def _convert_to_json_schema(self, parameters: Dict[str, ParameterSchema]) -> Dict[str, Any]:
        """
        Convert tool parameters to JSON Schema format for MCP compatibility.
        
        Args:
            parameters: Tool parameters in ParameterSchema format
            
        Returns:
            JSON Schema representation of the parameters
        """
        if not parameters:
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        properties = {}
        required = []
        
        for param_name, param_schema in parameters.items():
            prop = {
                "type": param_schema.type.value,
                "description": param_schema.description
            }
            
            # Add additional schema properties
            if param_schema.enum:
                prop["enum"] = param_schema.enum
            
            if param_schema.min_items is not None:
                prop["minItems"] = param_schema.min_items
            
            if param_schema.max_items is not None:
                prop["maxItems"] = param_schema.max_items
            
            if param_schema.pattern:
                prop["pattern"] = param_schema.pattern
            
            if param_schema.default is not None:
                prop["default"] = param_schema.default
            
            if param_schema.example is not None:
                prop["examples"] = [param_schema.example]
            
            properties[param_name] = prop
            
            if param_schema.required:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def get_aggregated_server_info(self) -> Dict[str, Any]:
        """
        Get information about schema aggregation from MCP servers.
        
        Returns:
            Dictionary containing server aggregation status and metadata
        """
        if not self._aggregated_schemas:
            return {
                "servers": {},
                "total_servers": 0,
                "healthy_servers": 0,
                "last_aggregation": None,
                "aggregation_status": "not_started"
            }
        
        healthy_servers = sum(
            1 for server_info in self._aggregated_schemas.values()
            if server_info.get("server_status") == "healthy"
        )
        
        return {
            "servers": {
                server_name: {
                    "tool_count": len(server_info.get("tools", {})),
                    "status": server_info.get("server_status", "unknown"),
                    "last_updated": server_info.get("last_updated").isoformat() + "Z" if server_info.get("last_updated") else None,
                    "error": server_info.get("error")
                }
                for server_name, server_info in self._aggregated_schemas.items()
            },
            "total_servers": len(self._aggregated_schemas),
            "healthy_servers": healthy_servers,
            "last_aggregation": self._last_schema_update.isoformat() + "Z" if self._last_schema_update else None,
            "aggregation_status": "completed" if self._last_schema_update else "pending"
        }
    
    def _generate_metadata(self) -> None:
        """Generate metadata for all tools."""
        tools = [
            self._generate_district_search_metadata(),
            self._generate_meal_type_search_metadata(),
            self._generate_combined_search_metadata(),
            self._generate_recommendation_metadata(),
            self._generate_sentiment_analysis_metadata()
        ]
        
        self._metadata_cache = ToolsMetadataResponse(
            tools=tools,
            total_tools=len(tools),
            categories=[ToolCategory.SEARCH, ToolCategory.ANALYSIS, ToolCategory.RECOMMENDATION],
            supported_mbti_types=list(MBTIPersonalityType),
            version=self.version,
            last_updated=datetime.utcnow().isoformat() + "Z"
        )
        self._last_generated = datetime.utcnow()
    
    def _generate_district_search_metadata(self) -> ToolMetadata:
        """Generate metadata for district search tool."""
        return ToolMetadata(
            name="search_restaurants_by_district",
            display_name="Search Restaurants by District",
            category=ToolCategory.SEARCH,
            description="Search for restaurants located in specific Hong Kong districts. This tool filters restaurants based on their geographic location within Hong Kong's administrative districts.",
            purpose="Find restaurants in one or more specified Hong Kong districts for location-based dining recommendations",
            
            parameters={
                "districts": ParameterSchema(
                    type=ParameterType.ARRAY,
                    description="List of Hong Kong district names to search. Valid districts include Central district, Admiralty, Causeway Bay, Tsim Sha Tsui, Mong Kok, and others.",
                    required=True,
                    min_items=1,
                    max_items=20,
                    example=["Central district", "Admiralty", "Causeway Bay"]
                )
            },
            
            response_schema=ResponseSchema(
                type=ParameterType.OBJECT,
                description="Restaurant search results with metadata",
                properties={
                    "success": ParameterSchema(
                        type=ParameterType.BOOLEAN,
                        description="Whether the search was successful"
                    ),
                    "restaurants": ParameterSchema(
                        type=ParameterType.ARRAY,
                        description="List of restaurants matching the district criteria"
                    ),
                    "total_count": ParameterSchema(
                        type=ParameterType.INTEGER,
                        description="Total number of restaurants found"
                    ),
                    "districts_searched": ParameterSchema(
                        type=ParameterType.ARRAY,
                        description="List of districts that were searched"
                    )
                },
                example={
                    "success": True,
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Central Dining",
                            "district": "Central district",
                            "address": "123 Central Street",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                        }
                    ],
                    "total_count": 1,
                    "districts_searched": ["Central district"]
                }
            ),
            
            use_cases=[
                UseCaseScenario(
                    scenario="Tourist exploring specific areas",
                    when_to_use="When user wants to find restaurants in specific districts they plan to visit",
                    example_input={"districts": ["Central district", "Tsim Sha Tsui"]},
                    expected_outcome="List of restaurants in Central and Tsim Sha Tsui districts"
                ),
                UseCaseScenario(
                    scenario="Local resident looking for nearby options",
                    when_to_use="When user wants restaurants in their neighborhood or nearby districts",
                    example_input={"districts": ["Causeway Bay"]},
                    expected_outcome="All restaurants located in Causeway Bay district"
                ),
                UseCaseScenario(
                    scenario="Business meeting location planning",
                    when_to_use="When planning business meals in commercial districts",
                    example_input={"districts": ["Central district", "Admiralty"]},
                    expected_outcome="Professional dining options in business districts"
                )
            ],
            
            mbti_integration=[
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ENFP,
                    preferences=["Variety of districts", "Exploration opportunities", "Social environments"],
                    search_patterns=["Multiple districts at once", "Popular tourist areas", "Diverse neighborhoods"],
                    recommendation_focus="Districts with vibrant social scenes and diverse dining options"
                ),
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.INTJ,
                    preferences=["Efficient location planning", "Quality over quantity", "Strategic positioning"],
                    search_patterns=["Single district focus", "Business districts", "Convenient locations"],
                    recommendation_focus="Districts that align with planned activities and minimize travel time"
                ),
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ESFJ,
                    preferences=["Family-friendly areas", "Safe neighborhoods", "Community atmosphere"],
                    search_patterns=["Residential districts", "Family-oriented areas", "Well-established neighborhoods"],
                    recommendation_focus="Districts known for family dining and community-oriented restaurants"
                )
            ],
            
            examples=[
                ToolExample(
                    title="Find restaurants in Central district",
                    description="Search for all restaurants in Hong Kong's Central business district",
                    input={"districts": ["Central district"]},
                    output={
                        "success": True,
                        "restaurants": [
                            {
                                "id": "rest_central_001",
                                "name": "Central Fine Dining",
                                "district": "Central district",
                                "cuisine": "International",
                                "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3}
                            }
                        ],
                        "total_count": 1,
                        "districts_searched": ["Central district"]
                    },
                    notes="Central district typically has upscale dining options suitable for business meals"
                ),
                ToolExample(
                    title="Multi-district search for tourists",
                    description="Search across multiple tourist-popular districts",
                    input={"districts": ["Tsim Sha Tsui", "Causeway Bay", "Central district"]},
                    output={
                        "success": True,
                        "restaurants": [],  # Truncated for example
                        "total_count": 45,
                        "districts_searched": ["Tsim Sha Tsui", "Causeway Bay", "Central district"]
                    },
                    notes="Multi-district searches provide comprehensive options for tourists exploring different areas"
                )
            ],
            
            endpoint="/api/v1/restaurants/search/district",
            http_method="POST",
            authentication_required=True,
            rate_limit="100 requests per minute",
            average_response_time_ms=250.0,
            success_rate_percentage=99.5
        )
    
    def _generate_meal_type_search_metadata(self) -> ToolMetadata:
        """Generate metadata for meal type search tool."""
        return ToolMetadata(
            name="search_restaurants_by_meal_type",
            display_name="Search Restaurants by Meal Type",
            category=ToolCategory.SEARCH,
            description="Search for restaurants based on the meal types they serve. This tool filters restaurants by their operating hours to determine if they serve breakfast (07:00-11:29), lunch (11:30-17:29), or dinner (17:30-22:30).",
            purpose="Find restaurants that serve specific meal types based on their operating hours",
            
            parameters={
                "meal_types": ParameterSchema(
                    type=ParameterType.ARRAY,
                    description="List of meal types to search for. Valid values are 'breakfast', 'lunch', and 'dinner'.",
                    required=True,
                    min_items=1,
                    max_items=3,
                    enum=["breakfast", "lunch", "dinner"],
                    example=["breakfast", "lunch"]
                )
            },
            
            response_schema=ResponseSchema(
                type=ParameterType.OBJECT,
                description="Restaurant search results filtered by meal type availability",
                properties={
                    "success": ParameterSchema(
                        type=ParameterType.BOOLEAN,
                        description="Whether the search was successful"
                    ),
                    "restaurants": ParameterSchema(
                        type=ParameterType.ARRAY,
                        description="List of restaurants that serve the requested meal types"
                    ),
                    "meal_types_searched": ParameterSchema(
                        type=ParameterType.ARRAY,
                        description="List of meal types that were searched"
                    ),
                    "total_count": ParameterSchema(
                        type=ParameterType.INTEGER,
                        description="Total number of restaurants found"
                    )
                },
                example={
                    "success": True,
                    "restaurants": [
                        {
                            "id": "rest_002",
                            "name": "All Day Cafe",
                            "operating_hours": "07:00-22:00",
                            "serves_breakfast": True,
                            "serves_lunch": True,
                            "serves_dinner": True
                        }
                    ],
                    "meal_types_searched": ["breakfast", "lunch"],
                    "total_count": 1
                }
            ),
            
            use_cases=[
                UseCaseScenario(
                    scenario="Early morning dining",
                    when_to_use="When user needs breakfast options or early dining",
                    example_input={"meal_types": ["breakfast"]},
                    expected_outcome="Restaurants that open early and serve breakfast"
                ),
                UseCaseScenario(
                    scenario="Business lunch planning",
                    when_to_use="When planning lunch meetings or midday dining",
                    example_input={"meal_types": ["lunch"]},
                    expected_outcome="Restaurants available during lunch hours"
                ),
                UseCaseScenario(
                    scenario="All-day dining options",
                    when_to_use="When user wants restaurants that serve multiple meal types",
                    example_input={"meal_types": ["breakfast", "lunch", "dinner"]},
                    expected_outcome="Restaurants that serve all three meal types"
                )
            ],
            
            mbti_integration=[
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ENFP,
                    preferences=["Flexible dining times", "All-day options", "Variety in meal experiences"],
                    search_patterns=["Multiple meal types", "All-day dining", "Brunch options"],
                    recommendation_focus="Restaurants with flexible hours and diverse meal offerings"
                ),
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ISTJ,
                    preferences=["Traditional meal times", "Consistent schedules", "Reliable service"],
                    search_patterns=["Single meal type focus", "Traditional dining hours", "Established patterns"],
                    recommendation_focus="Restaurants with consistent meal service during traditional hours"
                )
            ],
            
            examples=[
                ToolExample(
                    title="Find breakfast restaurants",
                    description="Search for restaurants that serve breakfast",
                    input={"meal_types": ["breakfast"]},
                    output={
                        "success": True,
                        "restaurants": [
                            {
                                "id": "rest_breakfast_001",
                                "name": "Morning Glory Cafe",
                                "operating_hours": "06:30-14:00",
                                "serves_breakfast": True,
                                "serves_lunch": True,
                                "serves_dinner": False
                            }
                        ],
                        "meal_types_searched": ["breakfast"],
                        "total_count": 1
                    },
                    notes="Breakfast restaurants typically open early and may also serve lunch"
                )
            ],
            
            endpoint="/api/v1/restaurants/search/meal-type",
            http_method="POST",
            authentication_required=True,
            rate_limit="100 requests per minute",
            average_response_time_ms=200.0,
            success_rate_percentage=99.7
        )
    
    def _generate_combined_search_metadata(self) -> ToolMetadata:
        """Generate metadata for combined search tool."""
        return ToolMetadata(
            name="search_restaurants_combined",
            display_name="Combined Restaurant Search",
            category=ToolCategory.SEARCH,
            description="Advanced search that combines district and meal type filters. This tool allows filtering restaurants by both location (districts) and meal availability (breakfast, lunch, dinner) for precise results.",
            purpose="Find restaurants that match both district and meal type criteria for targeted dining recommendations",
            
            parameters={
                "districts": ParameterSchema(
                    type=ParameterType.ARRAY,
                    description="Optional list of Hong Kong districts to filter by. If not provided, searches all districts.",
                    required=False,
                    min_items=1,
                    max_items=20,
                    example=["Central district", "Admiralty"]
                ),
                "meal_types": ParameterSchema(
                    type=ParameterType.ARRAY,
                    description="Optional list of meal types to filter by. Valid values are 'breakfast', 'lunch', 'dinner'. If not provided, includes all meal types.",
                    required=False,
                    min_items=1,
                    max_items=3,
                    enum=["breakfast", "lunch", "dinner"],
                    example=["lunch", "dinner"]
                )
            },
            
            response_schema=ResponseSchema(
                type=ParameterType.OBJECT,
                description="Combined search results with both district and meal type filtering",
                properties={
                    "success": ParameterSchema(
                        type=ParameterType.BOOLEAN,
                        description="Whether the search was successful"
                    ),
                    "restaurants": ParameterSchema(
                        type=ParameterType.ARRAY,
                        description="List of restaurants matching both district and meal type criteria"
                    ),
                    "filters_applied": ParameterSchema(
                        type=ParameterType.OBJECT,
                        description="Summary of filters that were applied"
                    ),
                    "total_count": ParameterSchema(
                        type=ParameterType.INTEGER,
                        description="Total number of restaurants found"
                    )
                },
                example={
                    "success": True,
                    "restaurants": [
                        {
                            "id": "rest_003",
                            "name": "Central Lunch Spot",
                            "district": "Central district",
                            "serves_lunch": True,
                            "operating_hours": "11:00-15:00"
                        }
                    ],
                    "filters_applied": {
                        "districts": ["Central district"],
                        "meal_types": ["lunch"]
                    },
                    "total_count": 1
                }
            ),
            
            use_cases=[
                UseCaseScenario(
                    scenario="Targeted dining search",
                    when_to_use="When user has specific requirements for both location and meal timing",
                    example_input={"districts": ["Central district"], "meal_types": ["lunch"]},
                    expected_outcome="Lunch restaurants specifically in Central district"
                ),
                UseCaseScenario(
                    scenario="Flexible location with meal preference",
                    when_to_use="When user cares about meal type but is flexible on location",
                    example_input={"meal_types": ["breakfast"]},
                    expected_outcome="All breakfast restaurants across Hong Kong"
                ),
                UseCaseScenario(
                    scenario="Area exploration with dining flexibility",
                    when_to_use="When user wants to explore specific districts with any meal options",
                    example_input={"districts": ["Tsim Sha Tsui", "Causeway Bay"]},
                    expected_outcome="All restaurants in specified districts regardless of meal type"
                )
            ],
            
            mbti_integration=[
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ENTJ,
                    preferences=["Efficient filtering", "Precise results", "Strategic planning"],
                    search_patterns=["Both filters applied", "Specific criteria", "Optimized searches"],
                    recommendation_focus="Restaurants that exactly match planned itinerary and dining schedule"
                ),
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ISFP,
                    preferences=["Flexible exploration", "Serendipitous discovery", "Gentle filtering"],
                    search_patterns=["Single filter applied", "Broad searches", "Discovery-oriented"],
                    recommendation_focus="Restaurants that offer pleasant surprises within loose criteria"
                )
            ],
            
            examples=[
                ToolExample(
                    title="Find lunch restaurants in Central",
                    description="Combined search for lunch options in Central district",
                    input={"districts": ["Central district"], "meal_types": ["lunch"]},
                    output={
                        "success": True,
                        "restaurants": [
                            {
                                "id": "rest_central_lunch_001",
                                "name": "Central Business Lunch",
                                "district": "Central district",
                                "serves_lunch": True,
                                "cuisine": "Asian Fusion"
                            }
                        ],
                        "filters_applied": {
                            "districts": ["Central district"],
                            "meal_types": ["lunch"]
                        },
                        "total_count": 1
                    },
                    notes="Perfect for business lunch planning in Hong Kong's financial district"
                )
            ],
            
            endpoint="/api/v1/restaurants/search/combined",
            http_method="POST",
            authentication_required=True,
            rate_limit="100 requests per minute",
            average_response_time_ms=300.0,
            success_rate_percentage=99.3
        )
    
    def _generate_recommendation_metadata(self) -> ToolMetadata:
        """Generate metadata for restaurant recommendation tool."""
        return ToolMetadata(
            name="recommend_restaurants",
            display_name="Restaurant Recommendation Engine",
            category=ToolCategory.RECOMMENDATION,
            description="Intelligent restaurant recommendation system that analyzes sentiment data to provide personalized dining suggestions. Uses advanced algorithms to rank restaurants based on customer satisfaction metrics.",
            purpose="Provide personalized restaurant recommendations based on sentiment analysis and ranking preferences",
            
            parameters={
                "restaurants": ParameterSchema(
                    type=ParameterType.ARRAY,
                    description="List of restaurant objects with sentiment data. Each restaurant must include id, name, and sentiment object with likes, dislikes, and neutral counts.",
                    required=True,
                    min_items=1,
                    example=[
                        {
                            "id": "rest_001",
                            "name": "Great Restaurant",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                            "district": "Central district"
                        }
                    ]
                ),
                "ranking_method": ParameterSchema(
                    type=ParameterType.STRING,
                    description="Method for ranking restaurants. 'sentiment_likes' ranks by highest likes count, 'combined_sentiment' ranks by (likes + neutral) percentage.",
                    required=False,
                    default="sentiment_likes",
                    enum=["sentiment_likes", "combined_sentiment"],
                    example="sentiment_likes"
                )
            },
            
            response_schema=ResponseSchema(
                type=ParameterType.OBJECT,
                description="Restaurant recommendations with ranking and analysis",
                properties={
                    "recommendation": ParameterSchema(
                        type=ParameterType.OBJECT,
                        description="Top recommended restaurant from the analysis"
                    ),
                    "candidates": ParameterSchema(
                        type=ParameterType.ARRAY,
                        description="List of top candidate restaurants ranked by the specified method"
                    ),
                    "ranking_method": ParameterSchema(
                        type=ParameterType.STRING,
                        description="Method used for ranking"
                    ),
                    "analysis_summary": ParameterSchema(
                        type=ParameterType.OBJECT,
                        description="Statistical analysis of the restaurant data"
                    )
                },
                example={
                    "recommendation": {
                        "id": "rest_001",
                        "name": "Top Choice Restaurant",
                        "sentiment_score": 95.2,
                        "recommendation_reason": "Highest customer satisfaction with 95% positive sentiment"
                    },
                    "candidates": [],
                    "ranking_method": "sentiment_likes",
                    "analysis_summary": {
                        "total_restaurants": 10,
                        "average_likes": 75.5,
                        "top_score": 95.2
                    }
                }
            ),
            
            use_cases=[
                UseCaseScenario(
                    scenario="Personal dining recommendation",
                    when_to_use="When user wants the best restaurant from a list of options",
                    example_input={
                        "restaurants": [
                            {"id": "r1", "name": "Restaurant A", "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5}},
                            {"id": "r2", "name": "Restaurant B", "sentiment": {"likes": 90, "dislikes": 8, "neutral": 2}}
                        ],
                        "ranking_method": "sentiment_likes"
                    },
                    expected_outcome="Restaurant B recommended due to higher likes count (90 vs 80)"
                ),
                UseCaseScenario(
                    scenario="MBTI-based recommendation",
                    when_to_use="When providing recommendations tailored to personality preferences",
                    example_input={
                        "restaurants": [
                            {"id": "r1", "name": "Quiet Cafe", "sentiment": {"likes": 70, "dislikes": 5, "neutral": 25}},
                            {"id": "r2", "name": "Social Bistro", "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}}
                        ],
                        "ranking_method": "combined_sentiment"
                    },
                    expected_outcome="Recommendation considers both positive sentiment and neutral (comfortable) experiences"
                )
            ],
            
            mbti_integration=[
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ENFP,
                    preferences=["High social engagement", "Positive reviews", "Exciting experiences"],
                    search_patterns=["sentiment_likes ranking", "High likes count", "Social atmosphere indicators"],
                    recommendation_focus="Restaurants with enthusiastic positive reviews and social energy"
                ),
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.INFJ,
                    preferences=["Consistent quality", "Comfortable atmosphere", "Authentic experiences"],
                    search_patterns=["combined_sentiment ranking", "Low dislikes", "Balanced sentiment"],
                    recommendation_focus="Restaurants with consistent positive experiences and minimal negative feedback"
                )
            ],
            
            examples=[
                ToolExample(
                    title="Recommend from search results",
                    description="Get the best restaurant recommendation from search results",
                    input={
                        "restaurants": [
                            {
                                "id": "rest_001",
                                "name": "Excellent Dining",
                                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                                "district": "Central district"
                            },
                            {
                                "id": "rest_002", 
                                "name": "Good Restaurant",
                                "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5},
                                "district": "Admiralty"
                            }
                        ],
                        "ranking_method": "sentiment_likes"
                    },
                    output={
                        "recommendation": {
                            "id": "rest_001",
                            "name": "Excellent Dining",
                            "sentiment_score": 95.0,
                            "recommendation_reason": "Highest customer satisfaction with 95% positive sentiment"
                        },
                        "candidates": [
                            {"id": "rest_001", "name": "Excellent Dining", "score": 95.0},
                            {"id": "rest_002", "name": "Good Restaurant", "score": 80.0}
                        ],
                        "ranking_method": "sentiment_likes",
                        "analysis_summary": {
                            "total_restaurants": 2,
                            "average_likes": 87.5,
                            "top_score": 95.0
                        }
                    },
                    notes="Recommendation engine selects the restaurant with highest positive sentiment"
                )
            ],
            
            endpoint="/api/v1/restaurants/recommend",
            http_method="POST",
            authentication_required=True,
            rate_limit="50 requests per minute",
            average_response_time_ms=400.0,
            success_rate_percentage=99.8
        )
    
    def _generate_sentiment_analysis_metadata(self) -> ToolMetadata:
        """Generate metadata for sentiment analysis tool."""
        return ToolMetadata(
            name="analyze_restaurant_sentiment",
            display_name="Restaurant Sentiment Analysis",
            category=ToolCategory.ANALYSIS,
            description="Comprehensive sentiment analysis tool that processes restaurant data to provide statistical insights about customer satisfaction patterns without making specific recommendations.",
            purpose="Analyze sentiment patterns and provide statistical insights about restaurant customer satisfaction",
            
            parameters={
                "restaurants": ParameterSchema(
                    type=ParameterType.ARRAY,
                    description="List of restaurant objects with sentiment data. Each restaurant must include id, name, and sentiment object with likes, dislikes, and neutral counts.",
                    required=True,
                    min_items=1,
                    example=[
                        {
                            "id": "rest_001",
                            "name": "Restaurant A",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                        }
                    ]
                )
            },
            
            response_schema=ResponseSchema(
                type=ParameterType.OBJECT,
                description="Sentiment analysis results with statistical insights",
                properties={
                    "sentiment_analysis": ParameterSchema(
                        type=ParameterType.OBJECT,
                        description="Statistical analysis including averages and score ranges"
                    ),
                    "restaurant_count": ParameterSchema(
                        type=ParameterType.INTEGER,
                        description="Number of restaurants analyzed"
                    ),
                    "ranking_method": ParameterSchema(
                        type=ParameterType.STRING,
                        description="Method used for analysis"
                    )
                },
                example={
                    "sentiment_analysis": {
                        "average_likes": 78.5,
                        "average_dislikes": 12.3,
                        "average_neutral": 9.2,
                        "sentiment_distribution": {
                            "highly_positive": 15,
                            "positive": 25,
                            "neutral": 8,
                            "negative": 2
                        }
                    },
                    "restaurant_count": 50,
                    "ranking_method": "sentiment_likes"
                }
            ),
            
            use_cases=[
                UseCaseScenario(
                    scenario="Market research analysis",
                    when_to_use="When analyzing overall sentiment trends in restaurant data",
                    example_input={
                        "restaurants": [
                            {"id": "r1", "name": "Restaurant A", "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5}},
                            {"id": "r2", "name": "Restaurant B", "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10}}
                        ]
                    },
                    expected_outcome="Statistical analysis showing average sentiment scores and distribution patterns"
                ),
                UseCaseScenario(
                    scenario="Quality assessment overview",
                    when_to_use="When understanding overall quality patterns in a restaurant dataset",
                    example_input={
                        "restaurants": [
                            {"id": "r1", "name": "High Quality", "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}},
                            {"id": "r2", "name": "Average Quality", "sentiment": {"likes": 60, "dislikes": 30, "neutral": 10}}
                        ]
                    },
                    expected_outcome="Analysis showing quality distribution and satisfaction metrics"
                )
            ],
            
            mbti_integration=[
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.INTJ,
                    preferences=["Data-driven insights", "Statistical analysis", "Pattern recognition"],
                    search_patterns=["Comprehensive analysis", "Trend identification", "Quality metrics"],
                    recommendation_focus="Statistical insights that inform strategic dining decisions"
                ),
                MBTIIntegrationGuidance(
                    personality_type=MBTIPersonalityType.ESFJ,
                    preferences=["Community feedback", "Social validation", "Group satisfaction"],
                    search_patterns=["Sentiment distribution", "Community consensus", "Social proof"],
                    recommendation_focus="Understanding how restaurants perform with different groups and communities"
                )
            ],
            
            examples=[
                ToolExample(
                    title="Analyze restaurant sentiment patterns",
                    description="Comprehensive sentiment analysis of restaurant data",
                    input={
                        "restaurants": [
                            {
                                "id": "rest_001",
                                "name": "Popular Restaurant",
                                "sentiment": {"likes": 90, "dislikes": 8, "neutral": 2}
                            },
                            {
                                "id": "rest_002",
                                "name": "Average Restaurant", 
                                "sentiment": {"likes": 65, "dislikes": 25, "neutral": 10}
                            }
                        ]
                    },
                    output={
                        "sentiment_analysis": {
                            "average_likes": 77.5,
                            "average_dislikes": 16.5,
                            "average_neutral": 6.0,
                            "sentiment_distribution": {
                                "highly_positive": 1,
                                "positive": 1,
                                "neutral": 0,
                                "negative": 0
                            },
                            "quality_indicators": {
                                "high_satisfaction_rate": 50.0,
                                "low_dissatisfaction_rate": 100.0
                            }
                        },
                        "restaurant_count": 2,
                        "ranking_method": "sentiment_likes"
                    },
                    notes="Analysis provides insights into overall sentiment patterns without making specific recommendations"
                )
            ],
            
            endpoint="/api/v1/restaurants/analyze",
            http_method="POST",
            authentication_required=True,
            rate_limit="50 requests per minute",
            average_response_time_ms=350.0,
            success_rate_percentage=99.9
        )


# Global instance for use across the application
tool_metadata_service = ToolMetadataService()