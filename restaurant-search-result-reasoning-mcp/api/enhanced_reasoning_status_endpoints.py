"""
Enhanced Status Endpoints for Restaurant Reasoning MCP

This module provides enhanced REST API endpoints for the restaurant reasoning MCP server
with dual monitoring capabilities, reasoning-specific metrics, and backward compatibility.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from services.enhanced_reasoning_status_service import (
    get_enhanced_reasoning_status_service, 
    RestaurantReasoningEnhancedStatusService
)

logger = logging.getLogger(__name__)

# Create router for enhanced reasoning status endpoints
enhanced_reasoning_status_router = APIRouter(prefix="/status", tags=["Enhanced Reasoning Status"])


async def get_reasoning_status_service() -> RestaurantReasoningEnhancedStatusService:
    """Dependency to get the enhanced reasoning status service."""
    try:
        return await get_enhanced_reasoning_status_service()
    except Exception as e:
        logger.error(f"Failed to get enhanced reasoning status service: {e}")
        raise HTTPException(status_code=503, detail="Enhanced reasoning status service unavailable")


@enhanced_reasoning_status_router.get("/enhanced")
async def get_enhanced_reasoning_status(
    include_metrics: bool = Query(True, description="Include reasoning metrics data"),
    include_capabilities: bool = Query(True, description="Include reasoning capabilities status"),
    include_config: bool = Query(False, description="Include configuration data"),
    status_service: RestaurantReasoningEnhancedStatusService = Depends(get_reasoning_status_service)
):
    """
    Get comprehensive enhanced status information for reasoning service.
    
    Provides detailed status from both MCP tools/list and REST health checks
    with reasoning-specific metrics, capabilities, and service information.
    """
    try:
        # Get enhanced reasoning status
        status_data = await status_service.get_enhanced_reasoning_status()
        
        # Get reasoning capabilities if requested
        capabilities_data = None
        if include_capabilities:
            capabilities_data = await status_service.get_reasoning_capabilities_status()
        
        # Filter response based on query parameters
        if not include_metrics:
            status_data.pop("reasoning_metrics", None)
            status_data.pop("system_metrics", None)
            status_data.pop("connection_pools", None)
        
        if not include_config:
            status_data.pop("configuration", None)
        
        response_data = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "service_type": "reasoning_and_sentiment_analysis",
            "enhanced_status": status_data
        }
        
        if capabilities_data:
            response_data["reasoning_capabilities"] = capabilities_data
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Error getting enhanced reasoning status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@enhanced_reasoning_status_router.get("/dual-check")
async def perform_dual_reasoning_health_check(
    timeout: int = Query(30, description="Timeout for health check in seconds"),
    validate_reasoning: bool = Query(True, description="Validate reasoning capabilities"),
    status_service: RestaurantReasoningEnhancedStatusService = Depends(get_reasoning_status_service)
):
    """
    Perform manual dual health check (MCP + REST) with reasoning validation.
    
    Executes both MCP tools/list request and REST health check concurrently
    and returns aggregated results with reasoning-specific validation and metrics.
    """
    try:
        # Perform dual reasoning health check
        health_result = await status_service.perform_reasoning_health_check()
        
        # Get reasoning capabilities status if validation requested
        reasoning_validation = None
        if validate_reasoning:
            reasoning_validation = await status_service.get_reasoning_capabilities_status()
        
        response_data = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "check_type": "dual_reasoning_health_check",
            "health_result": health_result.to_dict(),
            "summary": {
                "overall_status": health_result.overall_status.value,
                "overall_success": health_result.overall_success,
                "health_score": health_result.health_score,
                "available_paths": health_result.available_paths,
                "mcp_success": health_result.mcp_success,
                "rest_success": health_result.rest_success,
                "combined_response_time_ms": health_result.combined_response_time_ms
            },
            "reasoning_tools": {
                "recommend_restaurants": health_result.mcp_success,
                "analyze_restaurant_sentiment": health_result.mcp_success,
                "tools_validated": health_result.mcp_result.tools_count if health_result.mcp_result else 0
            }
        }
        
        if reasoning_validation:
            response_data["reasoning_validation"] = reasoning_validation
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Error performing dual reasoning health check: {e}")
        raise HTTPException(status_code=500, detail=f"Reasoning health check failed: {str(e)}")


@enhanced_reasoning_status_router.get("/capabilities")
async def get_reasoning_capabilities(
    include_performance: bool = Query(True, description="Include performance metrics"),
    status_service: RestaurantReasoningEnhancedStatusService = Depends(get_reasoning_status_service)
):
    """
    Get detailed information about reasoning capabilities and performance.
    
    Returns comprehensive information about sentiment analysis, recommendation algorithms,
    data validation, and intelligent ranking capabilities.
    """
    try:
        capabilities = await status_service.get_reasoning_capabilities_status()
        
        # Add enhanced monitoring capabilities
        enhanced_capabilities = {
            "dual_monitoring": {
                "enabled": True,
                "description": "Concurrent MCP and REST health checks for reasoning services"
            },
            "mcp_monitoring": {
                "enabled": True,
                "tools_validation": True,
                "expected_tools": ["recommend_restaurants", "analyze_restaurant_sentiment"],
                "reasoning_specific": True
            },
            "rest_monitoring": {
                "enabled": True,
                "reasoning_validation": True,
                "capabilities_check": True
            },
            "reasoning_features": {
                "sentiment_analysis": "Customer satisfaction analysis with likes/dislikes/neutral metrics",
                "recommendation_algorithm": "Intelligent restaurant ranking with multiple algorithms",
                "data_validation": "Restaurant data structure and sentiment validation",
                "intelligent_ranking": "Priority-based ranking with configurable weights"
            }
        }
        
        response_data = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "server_name": "restaurant-search-result-reasoning-mcp",
            "service_type": "reasoning_and_sentiment_analysis",
            "capabilities": capabilities,
            "enhanced_monitoring": enhanced_capabilities
        }
        
        if not include_performance:
            capabilities.pop("performance", None)
            capabilities.pop("reasoning_metrics", None)
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Error getting reasoning capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@enhanced_reasoning_status_router.post("/reasoning/record")
async def record_reasoning_operation(
    operation_data: Dict[str, Any],
    status_service: RestaurantReasoningEnhancedStatusService = Depends(get_reasoning_status_service)
):
    """
    Record a reasoning operation for metrics tracking.
    
    Allows external systems to report reasoning operations for comprehensive
    performance monitoring and metrics collection.
    """
    try:
        # Validate operation data
        required_fields = ["operation_type", "success", "duration_ms"]
        missing_fields = [field for field in required_fields if field not in operation_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {missing_fields}"
            )
        
        # Record the operation
        await status_service.record_reasoning_operation(
            operation_type=operation_data["operation_type"],
            success=operation_data["success"],
            duration_ms=operation_data["duration_ms"],
            metadata=operation_data.get("metadata")
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Reasoning operation recorded successfully",
                "operation_type": operation_data["operation_type"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording reasoning operation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record operation: {str(e)}")


@enhanced_reasoning_status_router.get("/health/mcp")
async def get_mcp_reasoning_health_status(
    validate_tools: bool = Query(True, description="Validate reasoning tools"),
    status_service: RestaurantReasoningEnhancedStatusService = Depends(get_reasoning_status_service)
):
    """
    Get MCP-specific health status with reasoning tools validation.
    
    Returns health status from MCP tools/list requests only,
    with specific validation for reasoning and sentiment analysis tools.
    """
    try:
        # Get enhanced status and extract MCP result
        status_data = await status_service.get_enhanced_reasoning_status()
        health_result = status_data.get("health_check", {})
        mcp_result = health_result.get("mcp_result")
        
        if not mcp_result:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                    "mcp_enabled": False,
                    "message": "MCP health checks are not enabled or available"
                }
            )
        
        # Prepare reasoning tools validation
        reasoning_tools_status = {}
        if validate_tools:
            expected_tools = ["recommend_restaurants", "analyze_restaurant_sentiment"]
            found_tools = mcp_result.get("expected_tools_found", [])
            
            for tool in expected_tools:
                reasoning_tools_status[tool] = {
                    "available": tool in found_tools,
                    "validated": tool in found_tools,
                    "description": {
                        "recommend_restaurants": "Intelligent restaurant recommendation with sentiment analysis",
                        "analyze_restaurant_sentiment": "Customer sentiment analysis and statistics"
                    }.get(tool, "Reasoning tool")
                }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": mcp_result.get("success", False),
                "timestamp": datetime.now().isoformat(),
                "mcp_result": mcp_result,
                "reasoning_tools": reasoning_tools_status,
                "tools_validation": {
                    "tools_count": mcp_result.get("tools_count"),
                    "expected_tools_found": mcp_result.get("expected_tools_found", []),
                    "missing_tools": mcp_result.get("missing_tools", []),
                    "validation_errors": mcp_result.get("validation_errors", [])
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting MCP reasoning health status: {e}")
        raise HTTPException(status_code=500, detail=f"MCP reasoning health check failed: {str(e)}")


@enhanced_reasoning_status_router.get("/health/rest")
async def get_rest_reasoning_health_status(
    validate_capabilities: bool = Query(True, description="Validate reasoning capabilities"),
    status_service: RestaurantReasoningEnhancedStatusService = Depends(get_reasoning_status_service)
):
    """
    Get REST-specific health status with reasoning capabilities validation.
    
    Returns health status from REST API health checks only,
    with specific validation for reasoning and sentiment analysis capabilities.
    """
    try:
        # Get enhanced status and extract REST result
        status_data = await status_service.get_enhanced_reasoning_status()
        health_result = status_data.get("health_check", {})
        rest_result = health_result.get("rest_result")
        
        if not rest_result:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                    "rest_enabled": False,
                    "message": "REST health checks are not enabled or available"
                }
            )
        
        # Prepare reasoning capabilities validation
        reasoning_capabilities_status = {}
        if validate_capabilities:
            response_body = rest_result.get("response_body", {})
            reasoning_capabilities = response_body.get("reasoning_capabilities", {})
            
            expected_capabilities = ["sentiment_analysis", "recommendation_algorithm", "data_validation"]
            for capability in expected_capabilities:
                reasoning_capabilities_status[capability] = {
                    "available": capability in reasoning_capabilities,
                    "status": reasoning_capabilities.get(capability, "unknown"),
                    "description": {
                        "sentiment_analysis": "Customer sentiment analysis with statistical metrics",
                        "recommendation_algorithm": "Intelligent ranking and recommendation algorithms",
                        "data_validation": "Restaurant data structure and format validation"
                    }.get(capability, "Reasoning capability")
                }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": rest_result.get("success", False),
                "timestamp": datetime.now().isoformat(),
                "rest_result": rest_result,
                "reasoning_capabilities": reasoning_capabilities_status,
                "http_details": {
                    "status_code": rest_result.get("status_code"),
                    "health_endpoint_url": rest_result.get("health_endpoint_url"),
                    "response_time_ms": rest_result.get("response_time_ms"),
                    "server_metrics": rest_result.get("server_metrics"),
                    "system_health": rest_result.get("system_health")
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting REST reasoning health status: {e}")
        raise HTTPException(status_code=500, detail=f"REST reasoning health check failed: {str(e)}")


# Backward compatibility endpoints
@enhanced_reasoning_status_router.get("/legacy")
async def get_legacy_reasoning_status_format(
    status_service: RestaurantReasoningEnhancedStatusService = Depends(get_reasoning_status_service)
):
    """
    Get status in legacy format for backward compatibility.
    
    Provides status information in the format expected by existing
    monitoring systems while leveraging enhanced dual monitoring for reasoning services.
    """
    try:
        # Get enhanced reasoning status
        status_data = await status_service.get_enhanced_reasoning_status()
        health_result = status_data.get("health_check", {})
        reasoning_metrics = status_data.get("reasoning_metrics", {})
        
        # Convert to legacy format
        overall_success = health_result.get("overall_success", False)
        overall_status = health_result.get("overall_status", "UNKNOWN").lower()
        
        legacy_response = {
            "status": overall_status,
            "healthy": overall_success,
            "timestamp": datetime.now().isoformat(),
            "server_name": "restaurant-search-result-reasoning-mcp",
            "service_type": "reasoning",
            "response_time_ms": health_result.get("combined_response_time_ms", 0),
            "available_tools": [
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ],
            "reasoning_metrics": {
                "recommendation_requests": reasoning_metrics.get("recommendation_requests", 0),
                "sentiment_analysis_requests": reasoning_metrics.get("sentiment_analysis_requests", 0),
                "success_rate": reasoning_metrics.get("successful_reasoning_operations", 0) / max(
                    reasoning_metrics.get("successful_reasoning_operations", 0) + 
                    reasoning_metrics.get("failed_reasoning_operations", 0), 1
                )
            },
            "enhanced_monitoring": {
                "enabled": True,
                "mcp_success": health_result.get("mcp_success", False),
                "rest_success": health_result.get("rest_success", False),
                "health_score": health_result.get("health_score", 0.0)
            }
        }
        
        return JSONResponse(
            status_code=200 if overall_success else 503,
            content=legacy_response
        )
        
    except Exception as e:
        logger.error(f"Error getting legacy reasoning status: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "healthy": False,
                "timestamp": datetime.now().isoformat(),
                "service_type": "reasoning",
                "error": str(e)
            }
        )


def get_enhanced_reasoning_status_router() -> APIRouter:
    """
    Get the enhanced reasoning status router for integration with FastAPI app.
    
    Returns:
        APIRouter: Configured router with enhanced reasoning status endpoints
    """
    return enhanced_reasoning_status_router