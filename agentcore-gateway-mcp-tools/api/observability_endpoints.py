"""
Observability endpoints for AgentCore Gateway MCP Tools.

This module provides endpoints for health checks, metrics, and operational statistics.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import structlog

from services.observability_service import get_observability_service, ObservabilityService
from services.mcp_client_manager import get_mcp_client_manager, MCPClientManager, MCPServerStatus


router = APIRouter(
    prefix="",
    tags=["observability"],
    responses={
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable"}
    }
)

logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check(
    observability_service: ObservabilityService = Depends(get_observability_service),
    mcp_client_manager: MCPClientManager = Depends(get_mcp_client_manager)
) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint with MCP server connectivity verification.
    
    This endpoint is used by AgentCore Runtime for health monitoring and
    provides detailed status information about the Gateway and its dependencies.
    
    Returns:
        Dict containing health status, service information, and MCP server status
    """
    try:
        health_data = await observability_service.get_health_status(mcp_client_manager)
        
        # Return appropriate HTTP status based on health
        if health_data["status"] == "healthy":
            return health_data
        elif health_data["status"] == "degraded":
            return JSONResponse(status_code=200, content=health_data)  # Still return 200 for degraded
        else:
            return JSONResponse(status_code=503, content=health_data)
            
    except Exception as e:
        error_msg = f"Health check failed: {str(e)}"
        logger.error("Health check endpoint error", error=error_msg)
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "agentcore-gateway-mcp-tools",
                "error": error_msg
            }
        )


@router.get("/metrics")
async def metrics_endpoint(
    observability_service: ObservabilityService = Depends(get_observability_service)
) -> Dict[str, Any]:
    """
    Operational metrics endpoint providing detailed statistics.
    
    This endpoint provides comprehensive operational metrics including:
    - Request counts and performance statistics
    - Authentication and security metrics
    - MCP server interaction statistics
    - System uptime and health indicators
    
    Returns:
        Dict containing operational statistics and metrics
    """
    try:
        stats = observability_service.get_operational_stats()
        
        # Add additional metrics context
        metrics_data = {
            "service": "agentcore-gateway-mcp-tools",
            "version": "1.0.0",
            "metrics": stats,
            "collection_info": {
                "metrics_namespace": observability_service.metrics_namespace,
                "cloudwatch_enabled": observability_service.cloudwatch_client is not None,
                "aws_region": observability_service.aws_region,
                "max_history_size": observability_service.max_history_size
            }
        }
        
        logger.info("Metrics endpoint accessed", metrics_summary={
            "total_requests": stats["total_requests"],
            "successful_requests": stats["successful_requests"],
            "failed_requests": stats["failed_requests"],
            "uptime_seconds": stats["uptime_seconds"]
        })
        
        return metrics_data
        
    except Exception as e:
        error_msg = f"Metrics collection failed: {str(e)}"
        logger.error("Metrics endpoint error", error=error_msg)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "metrics_collection_failed",
                "message": error_msg
            }
        )


@router.get("/metrics/performance")
async def performance_metrics(
    limit: int = 100,
    observability_service: ObservabilityService = Depends(get_observability_service)
) -> Dict[str, Any]:
    """
    Detailed performance metrics endpoint.
    
    Args:
        limit: Maximum number of recent performance records to return (default: 100)
    
    Returns:
        Dict containing recent performance metrics and analysis
    """
    try:
        # Get recent performance history
        recent_metrics = observability_service.performance_history[-limit:] if limit > 0 else []
        
        # Calculate performance statistics
        if recent_metrics:
            durations = [m.duration_ms for m in recent_metrics]
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            p50_idx = int(len(sorted_durations) * 0.5)
            p95_idx = int(len(sorted_durations) * 0.95)
            p99_idx = int(len(sorted_durations) * 0.99)
            
            performance_stats = {
                "total_requests": len(recent_metrics),
                "avg_duration_ms": round(avg_duration, 2),
                "min_duration_ms": round(min_duration, 2),
                "max_duration_ms": round(max_duration, 2),
                "p50_duration_ms": round(sorted_durations[p50_idx], 2),
                "p95_duration_ms": round(sorted_durations[p95_idx], 2),
                "p99_duration_ms": round(sorted_durations[p99_idx], 2)
            }
            
            # Group by endpoint
            endpoint_stats = {}
            for metric in recent_metrics:
                endpoint = metric.endpoint
                if endpoint not in endpoint_stats:
                    endpoint_stats[endpoint] = {
                        "count": 0,
                        "total_duration_ms": 0,
                        "mcp_calls": 0,
                        "status_codes": {}
                    }
                
                endpoint_stats[endpoint]["count"] += 1
                endpoint_stats[endpoint]["total_duration_ms"] += metric.duration_ms
                endpoint_stats[endpoint]["mcp_calls"] += metric.mcp_server_calls
                
                status_code = str(metric.status_code)
                endpoint_stats[endpoint]["status_codes"][status_code] = \
                    endpoint_stats[endpoint]["status_codes"].get(status_code, 0) + 1
            
            # Calculate averages for each endpoint
            for endpoint, stats in endpoint_stats.items():
                stats["avg_duration_ms"] = round(stats["total_duration_ms"] / stats["count"], 2)
                stats["avg_mcp_calls"] = round(stats["mcp_calls"] / stats["count"], 2)
        else:
            performance_stats = {
                "total_requests": 0,
                "message": "No performance data available"
            }
            endpoint_stats = {}
        
        return {
            "service": "agentcore-gateway-mcp-tools",
            "performance_summary": performance_stats,
            "endpoint_breakdown": endpoint_stats,
            "data_range": {
                "limit": limit,
                "actual_records": len(recent_metrics)
            }
        }
        
    except Exception as e:
        error_msg = f"Performance metrics collection failed: {str(e)}"
        logger.error("Performance metrics endpoint error", error=error_msg)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "performance_metrics_failed",
                "message": error_msg
            }
        )


@router.get("/metrics/security")
async def security_metrics(
    limit: int = 100,
    observability_service: ObservabilityService = Depends(get_observability_service)
) -> Dict[str, Any]:
    """
    Security metrics endpoint providing authentication and security event statistics.
    
    Args:
        limit: Maximum number of recent security events to return (default: 100)
    
    Returns:
        Dict containing security metrics and recent events
    """
    try:
        # Get recent security events
        recent_events = observability_service.security_events[-limit:] if limit > 0 else []
        
        # Calculate security statistics
        if recent_events:
            event_types = {}
            for event in recent_events:
                event_type = event.event_type.value
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Group by endpoint
            endpoint_events = {}
            for event in recent_events:
                endpoint = event.endpoint
                if endpoint not in endpoint_events:
                    endpoint_events[endpoint] = {}
                
                event_type = event.event_type.value
                endpoint_events[endpoint][event_type] = \
                    endpoint_events[endpoint].get(event_type, 0) + 1
        else:
            event_types = {}
            endpoint_events = {}
        
        return {
            "service": "agentcore-gateway-mcp-tools",
            "security_summary": {
                "total_events": len(recent_events),
                "event_types": event_types,
                "total_auth_failures": observability_service.stats.auth_failures
            },
            "endpoint_breakdown": endpoint_events,
            "data_range": {
                "limit": limit,
                "actual_records": len(recent_events)
            }
        }
        
    except Exception as e:
        error_msg = f"Security metrics collection failed: {str(e)}"
        logger.error("Security metrics endpoint error", error=error_msg)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "security_metrics_failed",
                "message": error_msg
            }
        )


@router.get("/metrics/mcp")
async def mcp_metrics(
    mcp_client_manager: MCPClientManager = Depends(get_mcp_client_manager)
) -> Dict[str, Any]:
    """
    MCP server metrics endpoint providing connectivity and performance statistics.
    
    Returns:
        Dict containing MCP server status and performance metrics
    """
    try:
        # Get current server status
        server_status = mcp_client_manager.get_all_server_status()
        
        # Prepare detailed server information
        server_details = {}
        for server_name, health in server_status.items():
            server_details[server_name] = {
                "status": health.status.value,
                "last_check": datetime.fromtimestamp(health.last_check, timezone.utc).isoformat() if health.last_check else None,
                "response_time_ms": health.response_time,
                "error": health.error_message,
                "consecutive_failures": health.consecutive_failures
            }
        
        # Calculate overall MCP statistics (simplified since we don't have call counts)
        total_servers = len(server_status)
        healthy_servers = sum(1 for h in server_status.values() if h.status == MCPServerStatus.HEALTHY)
        
        health_rate = (healthy_servers / total_servers * 100) if total_servers > 0 else 0
        
        return {
            "service": "agentcore-gateway-mcp-tools",
            "mcp_summary": {
                "total_servers": total_servers,
                "healthy_servers": healthy_servers,
                "health_rate_percent": round(health_rate, 2),
                "avg_response_time_ms": round(
                    sum(h.response_time for h in server_status.values() if h.response_time) / 
                    len([h for h in server_status.values() if h.response_time]), 2
                ) if any(h.response_time for h in server_status.values()) else 0
            },
            "server_details": server_details
        }
        
    except Exception as e:
        error_msg = f"MCP metrics collection failed: {str(e)}"
        logger.error("MCP metrics endpoint error", error=error_msg)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "mcp_metrics_failed",
                "message": error_msg
            }
        )