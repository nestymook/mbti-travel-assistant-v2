"""
Tool metadata API endpoints for AgentCore Gateway MCP Tools.

This module provides REST API endpoints for accessing comprehensive tool metadata
that helps foundation models understand when and how to use each available tool.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from models.tool_metadata_models import ToolsMetadataResponse, ToolMetadata
from services.tool_metadata_service import tool_metadata_service
from middleware.auth_middleware import get_current_user
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create router for tool metadata endpoints
router = APIRouter(
    prefix="/tools",
    tags=["Tool Metadata"],
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Tool not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/metadata",
    response_model=ToolsMetadataResponse,
    summary="Get comprehensive metadata for all available tools",
    description="""
    Retrieve comprehensive metadata for all available MCP tools in the Gateway.
    
    This endpoint provides foundation models with detailed information about:
    - Tool capabilities and purposes
    - Parameter schemas and validation rules
    - Response formats and examples
    - MBTI personality integration guidance
    - Use case scenarios and examples
    - Performance metrics and reliability data
    
    The metadata is designed to help AI models understand when and how to use
    each tool effectively for restaurant search and recommendation tasks.
    """,
    response_description="Complete metadata for all available tools"
)
async def get_all_tools_metadata(
    current_user: dict = Depends(get_current_user)
) -> ToolsMetadataResponse:
    """
    Get comprehensive metadata for all available tools.
    
    Args:
        current_user: Authenticated user context from JWT token
        
    Returns:
        ToolsMetadataResponse: Complete metadata for all tools
        
    Raises:
        HTTPException: If metadata generation fails
    """
    try:
        logger.info(f"User {current_user.get('username', 'unknown')} requested all tools metadata")
        
        # Get metadata from service
        metadata = tool_metadata_service.get_all_tools_metadata()
        
        logger.info(f"Successfully returned metadata for {metadata.total_tools} tools")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to generate tools metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to generate tools metadata",
                "message": "An internal error occurred while generating tool metadata",
                "type": "MetadataGenerationError"
            }
        )


@router.get(
    "/metadata/{tool_name}",
    response_model=ToolMetadata,
    summary="Get metadata for a specific tool",
    description="""
    Retrieve detailed metadata for a specific tool by name.
    
    Available tool names:
    - search_restaurants_by_district
    - search_restaurants_by_meal_type
    - search_restaurants_combined
    - recommend_restaurants
    - analyze_restaurant_sentiment
    
    This endpoint provides the same comprehensive metadata as the general endpoint
    but filtered to a single tool for more focused integration scenarios.
    """,
    response_description="Detailed metadata for the specified tool"
)
async def get_tool_metadata(
    tool_name: str,
    current_user: dict = Depends(get_current_user)
) -> ToolMetadata:
    """
    Get metadata for a specific tool.
    
    Args:
        tool_name: Name of the tool to get metadata for
        current_user: Authenticated user context from JWT token
        
    Returns:
        ToolMetadata: Metadata for the specified tool
        
    Raises:
        HTTPException: If tool not found or metadata generation fails
    """
    try:
        logger.info(f"User {current_user.get('username', 'unknown')} requested metadata for tool: {tool_name}")
        
        # Get metadata for specific tool
        metadata = tool_metadata_service.get_tool_metadata(tool_name)
        
        logger.info(f"Successfully returned metadata for tool: {tool_name}")
        return metadata
        
    except ValueError as e:
        logger.warning(f"Tool not found: {tool_name}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Tool not found",
                "message": f"Tool '{tool_name}' does not exist",
                "type": "ToolNotFoundError",
                "available_tools": [
                    "search_restaurants_by_district",
                    "search_restaurants_by_meal_type", 
                    "search_restaurants_combined",
                    "recommend_restaurants",
                    "analyze_restaurant_sentiment"
                ]
            }
        )
    except Exception as e:
        logger.error(f"Failed to get metadata for tool {tool_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get tool metadata",
                "message": f"An internal error occurred while getting metadata for tool '{tool_name}'",
                "type": "MetadataRetrievalError"
            }
        )


@router.get(
    "/metadata/categories/{category}",
    response_model=ToolsMetadataResponse,
    summary="Get metadata for tools in a specific category",
    description="""
    Retrieve metadata for all tools in a specific category.
    
    Available categories:
    - search: Restaurant search tools (district, meal type, combined)
    - analysis: Sentiment analysis tools
    - recommendation: Restaurant recommendation tools
    
    This endpoint helps foundation models focus on specific types of tools
    based on the task category they need to perform.
    """,
    response_description="Metadata for all tools in the specified category"
)
async def get_tools_by_category(
    category: str,
    current_user: dict = Depends(get_current_user)
) -> ToolsMetadataResponse:
    """
    Get metadata for tools in a specific category.
    
    Args:
        category: Tool category to filter by
        current_user: Authenticated user context from JWT token
        
    Returns:
        ToolsMetadataResponse: Metadata for tools in the specified category
        
    Raises:
        HTTPException: If category not found or metadata generation fails
    """
    try:
        logger.info(f"User {current_user.get('username', 'unknown')} requested tools for category: {category}")
        
        # Get all metadata first
        all_metadata = tool_metadata_service.get_all_tools_metadata()
        
        # Filter by category
        filtered_tools = [
            tool for tool in all_metadata.tools 
            if tool.category.value == category.lower()
        ]
        
        if not filtered_tools:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Category not found",
                    "message": f"No tools found for category '{category}'",
                    "type": "CategoryNotFoundError",
                    "available_categories": ["search", "analysis", "recommendation"]
                }
            )
        
        # Create filtered response
        filtered_metadata = ToolsMetadataResponse(
            tools=filtered_tools,
            total_tools=len(filtered_tools),
            categories=all_metadata.categories,
            supported_mbti_types=all_metadata.supported_mbti_types,
            version=all_metadata.version,
            last_updated=all_metadata.last_updated
        )
        
        logger.info(f"Successfully returned {len(filtered_tools)} tools for category: {category}")
        return filtered_metadata
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to get tools for category {category}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get tools by category",
                "message": f"An internal error occurred while getting tools for category '{category}'",
                "type": "CategoryRetrievalError"
            }
        )


@router.get(
    "/metadata/mbti/{personality_type}",
    response_model=ToolsMetadataResponse,
    summary="Get tool metadata with MBTI personality guidance",
    description="""
    Retrieve tool metadata with specific guidance for a given MBTI personality type.
    
    This endpoint filters and prioritizes tool metadata based on MBTI personality
    preferences, helping foundation models provide more personalized recommendations.
    
    Supported MBTI types: ENFJ, ENFP, ENTJ, ENTP, ESFJ, ESFP, ESTJ, ESTP,
                         INFJ, INFP, INTJ, INTP, ISFJ, ISFP, ISTJ, ISTP
    """,
    response_description="Tool metadata with MBTI-specific guidance"
)
async def get_tools_for_mbti_type(
    personality_type: str,
    current_user: dict = Depends(get_current_user)
) -> ToolsMetadataResponse:
    """
    Get tool metadata with MBTI personality guidance.
    
    Args:
        personality_type: MBTI personality type (e.g., ENFP, INTJ)
        current_user: Authenticated user context from JWT token
        
    Returns:
        ToolsMetadataResponse: Tool metadata with MBTI-specific guidance
        
    Raises:
        HTTPException: If personality type not supported or metadata generation fails
    """
    try:
        logger.info(f"User {current_user.get('username', 'unknown')} requested MBTI guidance for: {personality_type}")
        
        # Validate personality type
        personality_type_upper = personality_type.upper()
        valid_types = [mbti.value for mbti in tool_metadata_service.get_all_tools_metadata().supported_mbti_types]
        
        if personality_type_upper not in valid_types:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "MBTI type not supported",
                    "message": f"MBTI personality type '{personality_type}' is not supported",
                    "type": "MBTITypeNotFoundError",
                    "supported_types": valid_types
                }
            )
        
        # Get all metadata
        all_metadata = tool_metadata_service.get_all_tools_metadata()
        
        # Filter MBTI guidance for each tool
        mbti_filtered_tools = []
        for tool in all_metadata.tools:
            # Create a copy of the tool with filtered MBTI guidance
            mbti_guidance = [
                guidance for guidance in tool.mbti_integration
                if guidance.personality_type.value == personality_type_upper
            ]
            
            if mbti_guidance:
                # Create tool copy with filtered MBTI guidance
                tool_copy = tool.model_copy()
                tool_copy.mbti_integration = mbti_guidance
                mbti_filtered_tools.append(tool_copy)
        
        # Create response with MBTI-filtered tools
        mbti_metadata = ToolsMetadataResponse(
            tools=mbti_filtered_tools,
            total_tools=len(mbti_filtered_tools),
            categories=all_metadata.categories,
            supported_mbti_types=[personality_type_upper],  # Only the requested type
            version=all_metadata.version,
            last_updated=all_metadata.last_updated
        )
        
        logger.info(f"Successfully returned MBTI guidance for {personality_type_upper} across {len(mbti_filtered_tools)} tools")
        return mbti_metadata
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to get MBTI guidance for {personality_type}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get MBTI guidance",
                "message": f"An internal error occurred while getting MBTI guidance for '{personality_type}'",
                "type": "MBTIGuidanceError"
            }
        )


@router.post(
    "/mcp/tools/list",
    summary="Native MCP tool discovery endpoint",
    description="""
    Native MCP protocol endpoint for tool discovery by foundation models.
    
    This endpoint implements the MCP tools/list protocol, providing comprehensive
    tool metadata aggregated from all registered MCP servers. The response format
    follows the native MCP JSON-RPC 2.0 specification.
    
    The aggregated metadata includes:
    - Native MCP tool schemas from source servers
    - MBTI personality integration guidance
    - Use case scenarios and examples
    - Performance metrics and reliability data
    - Validation rules preserved from source MCP servers
    
    This endpoint enables foundation models to discover and understand available
    tools through the standard MCP protocol interface.
    """,
    response_description="Native MCP tools/list response with aggregated tool schemas"
)
async def mcp_tools_list(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Native MCP tool discovery endpoint for foundation models.
    
    Args:
        request: MCP JSON-RPC 2.0 request with tools/list method
        current_user: Authenticated user context from JWT token
        
    Returns:
        Native MCP tools/list response with aggregated tool metadata
        
    Raises:
        HTTPException: If request is invalid or tool discovery fails
    """
    try:
        logger.info(f"User {current_user.get('username', 'unknown')} requested native MCP tool discovery")
        
        # Validate MCP request format
        if not isinstance(request, dict):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid request format",
                    "message": "Request must be a JSON object",
                    "type": "InvalidRequestError"
                }
            )
        
        # Extract request ID (default to 1 if not provided)
        request_id = request.get("id", 1)
        
        # Validate JSON-RPC format
        if request.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request",
                    "data": {
                        "error_type": "InvalidJSONRPCVersion",
                        "expected": "2.0",
                        "received": request.get("jsonrpc")
                    }
                }
            }
        
        # Validate method
        if request.get("method") != "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found",
                    "data": {
                        "error_type": "MethodNotFound",
                        "expected": "tools/list",
                        "received": request.get("method")
                    }
                }
            }
        
        # Generate native MCP tool discovery response
        mcp_response = await tool_metadata_service.get_native_mcp_tool_discovery(request_id)
        
        logger.info(f"Successfully generated native MCP tool discovery response for user {current_user.get('username', 'unknown')}")
        return mcp_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to process native MCP tool discovery request: {str(e)}")
        
        # Return MCP error response
        request_id = request.get("id", 1) if isinstance(request, dict) else 1
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


@router.get(
    "/aggregation/status",
    summary="Get schema aggregation status from MCP servers",
    description="""
    Get the current status of schema aggregation from registered MCP servers.
    
    This endpoint provides information about:
    - Which MCP servers have been contacted for schema aggregation
    - The health status of each server during aggregation
    - Number of tools discovered from each server
    - Last aggregation timestamp and any errors encountered
    
    This is useful for monitoring and debugging the tool metadata aggregation system.
    """,
    response_description="Schema aggregation status and server information"
)
async def get_aggregation_status(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get schema aggregation status from MCP servers.
    
    Args:
        current_user: Authenticated user context from JWT token
        
    Returns:
        Dictionary containing aggregation status and server information
    """
    try:
        logger.info(f"User {current_user.get('username', 'unknown')} requested aggregation status")
        
        # Get aggregation status from service
        status = tool_metadata_service.get_aggregated_server_info()
        
        logger.info(f"Successfully returned aggregation status for {status['total_servers']} servers")
        return {
            "success": True,
            "aggregation_info": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregation status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get aggregation status",
                "message": "An internal error occurred while getting schema aggregation status",
                "type": "AggregationStatusError"
            }
        )


@router.post(
    "/aggregation/refresh",
    summary="Refresh schema aggregation from MCP servers",
    description="""
    Force a refresh of schema aggregation from all registered MCP servers.
    
    This endpoint triggers immediate re-aggregation of tool schemas from all
    healthy MCP servers, updating the cached metadata with the latest information.
    
    Use this endpoint when:
    - MCP servers have been updated with new tools
    - Tool schemas have changed on source servers
    - Aggregation appears to be stale or incomplete
    """,
    response_description="Aggregation refresh status and results"
)
async def refresh_aggregation(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Force refresh of schema aggregation from MCP servers.
    
    Args:
        current_user: Authenticated user context from JWT token
        
    Returns:
        Dictionary containing refresh results and updated status
    """
    try:
        logger.info(f"User {current_user.get('username', 'unknown')} requested aggregation refresh")
        
        # Force schema aggregation refresh
        await tool_metadata_service._aggregate_schemas_from_mcp_servers()
        
        # Get updated status
        status = tool_metadata_service.get_aggregated_server_info()
        
        logger.info(f"Successfully refreshed aggregation for {status['total_servers']} servers")
        return {
            "success": True,
            "message": "Schema aggregation refreshed successfully",
            "aggregation_info": status,
            "refresh_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh aggregation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to refresh aggregation",
                "message": "An internal error occurred while refreshing schema aggregation",
                "type": "AggregationRefreshError"
            }
        )


@router.get(
    "/health",
    summary="Tool metadata service health check",
    description="Check the health status of the tool metadata service",
    response_description="Health status of the metadata service"
)
async def metadata_health_check():
    """
    Health check endpoint for tool metadata service.
    
    Returns:
        dict: Health status information
    """
    try:
        # Test metadata generation
        metadata = tool_metadata_service.get_all_tools_metadata()
        
        # Get aggregation status
        aggregation_status = tool_metadata_service.get_aggregated_server_info()
        
        return {
            "status": "healthy",
            "service": "tool_metadata_service",
            "tools_available": metadata.total_tools,
            "categories": len(metadata.categories),
            "mbti_types_supported": len(metadata.supported_mbti_types),
            "version": metadata.version,
            "last_updated": metadata.last_updated,
            "aggregation": {
                "servers_aggregated": aggregation_status["total_servers"],
                "healthy_servers": aggregation_status["healthy_servers"],
                "last_aggregation": aggregation_status["last_aggregation"],
                "status": aggregation_status["aggregation_status"]
            }
        }
        
    except Exception as e:
        logger.error(f"Tool metadata service health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "tool_metadata_service",
                "error": str(e),
                "message": "Tool metadata service is not functioning properly"
            }
        )