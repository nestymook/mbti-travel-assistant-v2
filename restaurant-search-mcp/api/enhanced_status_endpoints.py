"""
Enhanced Status Endpoints for Restaurant Search MCP

This module provides enhanced REST API endpoints for the restaurant search MCP server
with dual monitoring capabilities and backward compatibility.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from services.enhanced_status_service import get_enhanced_status_service, RestaurantSearchEnhancedStatusService

logger = logging.getLogger(__name__)

# Create router for enhanced status endpoints
enhanced_status_router = APIRouter(prefix="/status", tags=["Enhanced Status"])


async def get_status_service() -> RestaurantSearchEnhancedStatusService:
    """Dependency to get the enhanced status service."""
    try:
        return await get_enhanced_status_service()
    except Exception as e:
        logger.error(f"Failed to get enhanced status service: {e}")
        raise HTTPException(status_code=503, detail="Enhanced status service unavailable")


@enhanced_status_router.get("/enhanced")
async def get_enhanced_status(
    include_metrics: bool = Query(True, description="Include metrics data"),
    include_config: bool = Query(False, description="Include configuration data"),
    status_service: RestaurantSearchEnhancedStatusService = Depends(get_status_service)
):
    """
    Get comprehensive enhanced status information.
    
    Provides detailed status from both MCP tools/list and REST health checks
    with metrics, configuration, and service information.
    """
    try:
        # Get enhanced status
        status_data = await status_service.get_enhanced_status()
        
        # Filter response based on query parameters
        if not include_metrics:
            status_data.pop("metrics", None)
            status_data.pop("connection_pools", None)
        
        if not include_config:
            status_data.pop("configuration", None)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "enhanced_status": status_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting enhanced status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@enhanced_status_router.get("/dual-check")
async def perform_dual_health_check(
    timeout: int = Query(30, description="Timeout for health check in seconds"),
    status_service: RestaurantSearchEnhancedStatusService = Depends(get_status_service)
):
    """
    Perform manual dual health check (MCP + REST).
    
    Executes both MCP tools/list request and REST health check concurrently
    and returns aggregated results with detailed metrics.
    """
    try:
        # Perform dual health check
        health_result = await status_service.perform_self_health_check()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "check_type": "dual_health_check",
                "health_result": health_result.to_dict(),
                "summary": {
                    "overall_status": health_result.overall_status.value,
                    "overall_success": health_result.overall_success,
                    "health_score": health_result.health_score,
                    "available_paths": health_result.available_paths,
                    "mcp_success": health_result.mcp_success,
                    "rest_success": health_result.rest_success,
                    "combined_response_time_ms": health_result.combined_response_time_ms
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error performing dual health check: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@enhanced_status_router.get("/capabilities")
async def get_monitoring_capabilities(
    status_service: RestaurantSearchEnhancedStatusService = Depends(get_status_service)
):
    """
    Get information about enhanced monitoring capabilities.
    
    Returns details about dual monitoring features, MCP and REST health checks,
    aggregation methods, and circuit breaker configuration.
    """
    try:
        capabilities = await status_service.get_monitoring_capabilities()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "server_name": "restaurant-search-mcp",
                "capabilities": capabilities,
                "features": {
                    "dual_monitoring": "Concurrent MCP and REST health checks",
                    "intelligent_aggregation": "Weighted result combination with priority settings",
                    "circuit_breaker": "Independent circuit breakers for MCP and REST paths",
                    "metrics_collection": "Separate metrics for MCP and REST monitoring methods",
                    "backward_compatibility": "Compatible with existing monitoring systems"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@enhanced_status_router.put("/config")
async def update_server_configuration(
    config_updates: Dict[str, Any],
    status_service: RestaurantSearchEnhancedStatusService = Depends(get_status_service)
):
    """
    Update server configuration at runtime.
    
    Allows updating timeout values, retry policies, priority weights,
    and other configuration parameters without service restart.
    """
    try:
        # Update configuration
        success = await status_service.update_server_configuration(
            server_name="restaurant-search-mcp",
            config_updates=config_updates
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Configuration update failed")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Configuration updated successfully",
                "updated_fields": list(config_updates.keys())
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")


@enhanced_status_router.get("/health/mcp")
async def get_mcp_health_status(
    status_service: RestaurantSearchEnhancedStatusService = Depends(get_status_service)
):
    """
    Get MCP-specific health status.
    
    Returns health status from MCP tools/list requests only,
    useful for debugging MCP protocol issues.
    """
    try:
        # Get enhanced status and extract MCP result
        status_data = await status_service.get_enhanced_status()
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
        
        return JSONResponse(
            status_code=200,
            content={
                "success": mcp_result.get("success", False),
                "timestamp": datetime.now().isoformat(),
                "mcp_result": mcp_result,
                "tools_validation": {
                    "tools_count": mcp_result.get("tools_count"),
                    "expected_tools_found": mcp_result.get("expected_tools_found", []),
                    "missing_tools": mcp_result.get("missing_tools", []),
                    "validation_errors": mcp_result.get("validation_errors", [])
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting MCP health status: {e}")
        raise HTTPException(status_code=500, detail=f"MCP health check failed: {str(e)}")


@enhanced_status_router.get("/health/rest")
async def get_rest_health_status(
    status_service: RestaurantSearchEnhancedStatusService = Depends(get_status_service)
):
    """
    Get REST-specific health status.
    
    Returns health status from REST API health checks only,
    useful for debugging HTTP connectivity issues.
    """
    try:
        # Get enhanced status and extract REST result
        status_data = await status_service.get_enhanced_status()
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
        
        return JSONResponse(
            status_code=200,
            content={
                "success": rest_result.get("success", False),
                "timestamp": datetime.now().isoformat(),
                "rest_result": rest_result,
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
        logger.error(f"Error getting REST health status: {e}")
        raise HTTPException(status_code=500, detail=f"REST health check failed: {str(e)}")


# Backward compatibility endpoints
@enhanced_status_router.get("/legacy")
async def get_legacy_status_format(
    status_service: RestaurantSearchEnhancedStatusService = Depends(get_status_service)
):
    """
    Get status in legacy format for backward compatibility.
    
    Provides status information in the format expected by existing
    monitoring systems while leveraging enhanced dual monitoring.
    """
    try:
        # Get enhanced status
        status_data = await status_service.get_enhanced_status()
        health_result = status_data.get("health_check", {})
        
        # Convert to legacy format
        overall_success = health_result.get("overall_success", False)
        overall_status = health_result.get("overall_status", "UNKNOWN").lower()
        
        legacy_response = {
            "status": overall_status,
            "healthy": overall_success,
            "timestamp": datetime.now().isoformat(),
            "server_name": "restaurant-search-mcp",
            "response_time_ms": health_result.get("combined_response_time_ms", 0),
            "available_tools": [
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ],
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
        logger.error(f"Error getting legacy status: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "healthy": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


def get_enhanced_status_router() -> APIRouter:
    """
    Get the enhanced status router for integration with FastAPI app.
    
    Returns:
        APIRouter: Configured router with enhanced status endpoints
    """
    return enhanced_status_router