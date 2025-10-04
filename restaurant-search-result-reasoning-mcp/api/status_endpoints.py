"""
Status check REST endpoints for reasoning MCP server monitoring.

This module provides REST API endpoints for monitoring reasoning MCP server health,
circuit breaker states, and system metrics.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

from models.status_models import (
    ServerStatus,
    CircuitBreakerState,
    ServerStatusSummary,
    SystemStatusSummary,
    MCPStatusCheckConfig,
    serialize_status_data
)
from services.circuit_breaker import StatusCheckManager, get_reasoning_status_manager
from services.status_config_loader import StatusCheckConfigLoader, get_config_loader
from services.health_check_service import HealthCheckService, quick_health_check


# Pydantic models for API requests/responses
class HealthCheckRequest(BaseModel):
    """Request model for manual health check."""
    server_names: Optional[List[str]] = None
    timeout_seconds: Optional[int] = None


class CircuitBreakerActionRequest(BaseModel):
    """Request model for circuit breaker actions."""
    action: str  # "open", "close", "reset"
    server_names: Optional[List[str]] = None


class StatusCheckResponse(BaseModel):
    """Base response model for status check endpoints."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class ReasoningStatusEndpoints:
    """Status check REST endpoints for reasoning server."""
    
    def __init__(self, app: FastAPI, status_manager: Optional[StatusCheckManager] = None):
        """Initialize reasoning status endpoints.
        
        Args:
            app: FastAPI application instance
            status_manager: Optional status check manager (uses global if None)
        """
        self.app = app
        self.status_manager = status_manager or get_reasoning_status_manager()
        self.config_loader = get_config_loader()
        self.logger = logging.getLogger(__name__)
        
        # Register endpoints
        self._register_endpoints()
    
    def _register_endpoints(self) -> None:
        """Register all reasoning status check endpoints."""
        
        @self.app.get("/status/health", response_model=StatusCheckResponse)
        async def get_reasoning_system_health():
            """Get overall reasoning system health status."""
            try:
                health_summary = await self.status_manager.get_system_health_summary()
                
                return StatusCheckResponse(
                    success=True,
                    message="Reasoning system health retrieved successfully",
                    data=health_summary,
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                self.logger.exception("Error getting reasoning system health")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get reasoning system health: {str(e)}"
                )
        
        @self.app.get("/status/servers", response_model=StatusCheckResponse)
        async def get_all_reasoning_servers_status():
            """Get status for all monitored reasoning servers."""
            try:
                all_metrics = await self.status_manager.get_all_server_metrics()
                all_cb_states = await self.status_manager.get_all_circuit_breaker_states()
                
                servers_status = []
                for server_name, metrics in all_metrics.items():
                    cb_state = all_cb_states.get(server_name, CircuitBreakerState.CLOSED)
                    
                    # Determine server status based on metrics
                    if metrics.consecutive_failures == 0 and metrics.total_requests > 0:
                        status = ServerStatus.HEALTHY
                    elif metrics.consecutive_failures >= 5:
                        status = ServerStatus.UNHEALTHY
                    elif metrics.consecutive_failures > 0:
                        status = ServerStatus.DEGRADED
                    else:
                        status = ServerStatus.UNKNOWN
                    
                    server_summary = ServerStatusSummary(
                        server_name=server_name,
                        status=status,
                        circuit_breaker_state=cb_state,
                        last_check_time=metrics.last_success_time or metrics.last_failure_time,
                        last_success_time=metrics.last_success_time,
                        last_failure_time=metrics.last_failure_time,
                        consecutive_failures=metrics.consecutive_failures,
                        response_time_ms=metrics.average_response_time_ms if metrics.successful_requests > 0 else None,
                        expected_tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
                    )
                    
                    servers_status.append(server_summary.to_dict())
                
                return StatusCheckResponse(
                    success=True,
                    message=f"Retrieved status for {len(servers_status)} reasoning servers",
                    data={"servers": servers_status},
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                self.logger.exception("Error getting reasoning servers status")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get reasoning servers status: {str(e)}"
                )
        
        @self.app.get("/status/servers/{server_name}", response_model=StatusCheckResponse)
        async def get_reasoning_server_status(server_name: str = Path(..., description="Name of the reasoning server")):
            """Get status for a specific reasoning server."""
            try:
                metrics = await self.status_manager.get_server_metrics(server_name)
                if not metrics:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Reasoning server '{server_name}' not found"
                    )
                
                cb_state = await self.status_manager.get_server_circuit_breaker_state(server_name)
                
                # Determine server status
                if metrics.consecutive_failures == 0 and metrics.total_requests > 0:
                    status = ServerStatus.HEALTHY
                elif metrics.consecutive_failures >= 5:
                    status = ServerStatus.UNHEALTHY
                elif metrics.consecutive_failures > 0:
                    status = ServerStatus.DEGRADED
                else:
                    status = ServerStatus.UNKNOWN
                
                server_summary = ServerStatusSummary(
                    server_name=server_name,
                    status=status,
                    circuit_breaker_state=cb_state or CircuitBreakerState.CLOSED,
                    last_check_time=metrics.last_success_time or metrics.last_failure_time,
                    last_success_time=metrics.last_success_time,
                    last_failure_time=metrics.last_failure_time,
                    consecutive_failures=metrics.consecutive_failures,
                    response_time_ms=metrics.average_response_time_ms if metrics.successful_requests > 0 else None,
                    expected_tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
                )
                
                return StatusCheckResponse(
                    success=True,
                    message=f"Retrieved status for reasoning server '{server_name}'",
                    data=server_summary.to_dict(),
                    timestamp=datetime.now().isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"Error getting status for reasoning server {server_name}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get reasoning server status: {str(e)}"
                )
        
        @self.app.get("/status/metrics", response_model=StatusCheckResponse)
        async def get_reasoning_system_metrics():
            """Get detailed reasoning system metrics."""
            try:
                all_metrics = await self.status_manager.get_all_server_metrics()
                all_cb_states = await self.status_manager.get_all_circuit_breaker_states()
                
                # Calculate aggregate metrics
                total_requests = sum(m.total_requests for m in all_metrics.values())
                total_successful = sum(m.successful_requests for m in all_metrics.values())
                total_failed = sum(m.failed_requests for m in all_metrics.values())
                
                avg_response_time = 0.0
                if total_successful > 0:
                    weighted_response_times = [
                        m.average_response_time_ms * m.successful_requests
                        for m in all_metrics.values()
                        if m.successful_requests > 0
                    ]
                    avg_response_time = sum(weighted_response_times) / total_successful
                
                # Circuit breaker statistics
                cb_stats = {
                    "closed": sum(1 for state in all_cb_states.values() if state == CircuitBreakerState.CLOSED),
                    "open": sum(1 for state in all_cb_states.values() if state == CircuitBreakerState.OPEN),
                    "half_open": sum(1 for state in all_cb_states.values() if state == CircuitBreakerState.HALF_OPEN)
                }
                
                metrics_data = {
                    "aggregate_metrics": {
                        "total_servers": len(all_metrics),
                        "total_requests": total_requests,
                        "successful_requests": total_successful,
                        "failed_requests": total_failed,
                        "success_rate": (total_successful / total_requests * 100) if total_requests > 0 else 100.0,
                        "average_response_time_ms": avg_response_time
                    },
                    "circuit_breaker_stats": cb_stats,
                    "server_metrics": {
                        name: metrics.to_dict()
                        for name, metrics in all_metrics.items()
                    },
                    "server_type": "reasoning"
                }
                
                return StatusCheckResponse(
                    success=True,
                    message="Reasoning system metrics retrieved successfully",
                    data=metrics_data,
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                self.logger.exception("Error getting reasoning system metrics")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get reasoning system metrics: {str(e)}"
                )
        
        @self.app.post("/status/health-check", response_model=StatusCheckResponse)
        async def trigger_manual_reasoning_health_check(request: HealthCheckRequest):
            """Trigger manual health check for specified reasoning servers."""
            try:
                # Get server configurations
                server_configs = self.config_loader.get_server_configs()
                
                # Filter servers if specified
                if request.server_names:
                    server_configs = {
                        name: config for name, config in server_configs.items()
                        if name in request.server_names
                    }
                
                if not server_configs:
                    raise HTTPException(
                        status_code=400,
                        detail="No valid reasoning servers specified or found"
                    )
                
                # Perform health checks
                timeout = request.timeout_seconds if request.timeout_seconds is not None else 10
                results = await quick_health_check(
                    list(server_configs.values()),
                    timeout_seconds=timeout
                )
                
                # Record results in status manager
                for result in results.values():
                    await self.status_manager.record_health_check_result(result)
                
                # Format response
                check_results = {
                    name: result.to_dict()
                    for name, result in results.items()
                }
                
                successful_checks = sum(1 for result in results.values() if result.success)
                
                return StatusCheckResponse(
                    success=True,
                    message=f"Reasoning health check completed: {successful_checks}/{len(results)} servers healthy",
                    data={
                        "results": check_results,
                        "summary": {
                            "total_servers": len(results),
                            "healthy_servers": successful_checks,
                            "unhealthy_servers": len(results) - successful_checks
                        }
                    },
                    timestamp=datetime.now().isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception("Error performing manual reasoning health check")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to perform reasoning health check: {str(e)}"
                )
        
        @self.app.post("/status/circuit-breaker", response_model=StatusCheckResponse)
        async def control_reasoning_circuit_breaker(request: CircuitBreakerActionRequest):
            """Control circuit breaker states for reasoning servers."""
            try:
                if request.action not in ["open", "close", "reset"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid action. Must be 'open', 'close', or 'reset'"
                    )
                
                # Get target servers
                if request.server_names:
                    target_servers = request.server_names
                else:
                    all_metrics = await self.status_manager.get_all_server_metrics()
                    target_servers = list(all_metrics.keys())
                
                if not target_servers:
                    raise HTTPException(
                        status_code=400,
                        detail="No reasoning servers specified or found"
                    )
                
                # Perform actions
                results = {}
                for server_name in target_servers:
                    try:
                        if request.action == "open":
                            success = await self.status_manager.force_circuit_breaker_open(server_name)
                        elif request.action == "close":
                            success = await self.status_manager.force_circuit_breaker_closed(server_name)
                        else:  # reset
                            success = await self.status_manager.reset_circuit_breaker(server_name)
                        
                        results[server_name] = {
                            "success": success,
                            "message": f"Reasoning circuit breaker {request.action} {'successful' if success else 'failed'}"
                        }
                        
                    except Exception as e:
                        results[server_name] = {
                            "success": False,
                            "message": f"Error: {str(e)}"
                        }
                
                successful_actions = sum(1 for result in results.values() if result["success"])
                
                return StatusCheckResponse(
                    success=successful_actions > 0,
                    message=f"Reasoning circuit breaker {request.action} completed: {successful_actions}/{len(results)} successful",
                    data={"results": results},
                    timestamp=datetime.now().isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception("Error controlling reasoning circuit breaker")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to control reasoning circuit breaker: {str(e)}"
                )
        
        @self.app.get("/status/config", response_model=StatusCheckResponse)
        async def get_reasoning_status_config():
            """Get current reasoning status check configuration."""
            try:
                system_config = self.config_loader.get_system_config()
                server_configs = self.config_loader.get_server_configs()
                
                config_data = {
                    "system_config": system_config,
                    "server_configs": {
                        name: config.to_dict()
                        for name, config in server_configs.items()
                    },
                    "enabled_servers": self.config_loader.get_enabled_servers(),
                    "server_type": "reasoning"
                }
                
                return StatusCheckResponse(
                    success=True,
                    message="Reasoning status check configuration retrieved successfully",
                    data=config_data,
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                self.logger.exception("Error getting reasoning status config")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get reasoning status config: {str(e)}"
                )


class ReasoningStatusConsoleIntegration:
    """Integration class for reasoning status monitoring console/dashboard."""
    
    def __init__(self, status_manager: Optional[StatusCheckManager] = None):
        """Initialize reasoning console integration.
        
        Args:
            status_manager: Optional status check manager (uses global if None)
        """
        self.status_manager = status_manager or get_reasoning_status_manager()
        self.config_loader = get_config_loader()
        self.logger = logging.getLogger(__name__)
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for reasoning console display.
        
        Returns:
            Dictionary with all dashboard data
        """
        try:
            # Get system health summary
            health_summary = await self.status_manager.get_system_health_summary()
            
            # Get detailed server information
            all_metrics = await self.status_manager.get_all_server_metrics()
            all_cb_states = await self.status_manager.get_all_circuit_breaker_states()
            
            # Build server details
            servers = []
            for server_name, metrics in all_metrics.items():
                cb_state = all_cb_states.get(server_name, CircuitBreakerState.CLOSED)
                
                # Determine status
                if metrics.consecutive_failures == 0 and metrics.total_requests > 0:
                    status = ServerStatus.HEALTHY
                elif metrics.consecutive_failures >= 5:
                    status = ServerStatus.UNHEALTHY
                elif metrics.consecutive_failures > 0:
                    status = ServerStatus.DEGRADED
                else:
                    status = ServerStatus.UNKNOWN
                
                server_info = {
                    "name": server_name,
                    "status": status.value,
                    "circuit_breaker_state": cb_state.value,
                    "metrics": metrics.to_dict(),
                    "is_available": await self.status_manager.is_server_available(server_name),
                    "last_check": (metrics.last_success_time or metrics.last_failure_time).isoformat() if (metrics.last_success_time or metrics.last_failure_time) else None,
                    "expected_tools": ["recommend_restaurants", "analyze_restaurant_sentiment"],
                    "server_type": "reasoning"
                }
                
                servers.append(server_info)
            
            # Sort servers by status (unhealthy first, then degraded, then healthy)
            status_priority = {
                ServerStatus.UNHEALTHY.value: 0,
                ServerStatus.DEGRADED.value: 1,
                ServerStatus.HEALTHY.value: 2,
                ServerStatus.UNKNOWN.value: 3
            }
            servers.sort(key=lambda s: status_priority.get(s["status"], 4))
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_health": health_summary,
                "servers": servers,
                "alerts": await self._get_active_alerts(),
                "recent_events": await self._get_recent_events(),
                "server_type": "reasoning"
            }
            
        except Exception as e:
            self.logger.exception("Error getting reasoning dashboard data")
            raise
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts for reasoning servers.
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        try:
            all_metrics = await self.status_manager.get_all_server_metrics()
            all_cb_states = await self.status_manager.get_all_circuit_breaker_states()
            
            for server_name, metrics in all_metrics.items():
                cb_state = all_cb_states.get(server_name, CircuitBreakerState.CLOSED)
                
                # Circuit breaker open alert
                if cb_state == CircuitBreakerState.OPEN:
                    alerts.append({
                        "type": "circuit_breaker_open",
                        "severity": "critical",
                        "server": server_name,
                        "message": f"Reasoning circuit breaker is OPEN for {server_name}",
                        "timestamp": datetime.now().isoformat(),
                        "server_type": "reasoning"
                    })
                
                # High failure rate alert
                if metrics.total_requests > 10 and metrics.failure_rate > 50:
                    alerts.append({
                        "type": "high_failure_rate",
                        "severity": "warning",
                        "server": server_name,
                        "message": f"High failure rate ({metrics.failure_rate:.1f}%) for reasoning server {server_name}",
                        "timestamp": datetime.now().isoformat(),
                        "server_type": "reasoning"
                    })
                
                # Consecutive failures alert
                if metrics.consecutive_failures >= 3:
                    alerts.append({
                        "type": "consecutive_failures",
                        "severity": "warning" if metrics.consecutive_failures < 5 else "critical",
                        "server": server_name,
                        "message": f"{metrics.consecutive_failures} consecutive failures for reasoning server {server_name}",
                        "timestamp": datetime.now().isoformat(),
                        "server_type": "reasoning"
                    })
            
        except Exception as e:
            self.logger.exception("Error getting active alerts for reasoning servers")
        
        return alerts
    
    async def _get_recent_events(self) -> List[Dict[str, Any]]:
        """Get list of recent events for reasoning servers.
        
        Returns:
            List of event dictionaries
        """
        # This would typically come from a persistent event log
        # For now, return empty list as we don't have event persistence
        return []
    
    def format_server_status_json(self, server_name: str) -> str:
        """Format individual reasoning server status as JSON for console integration.
        
        Args:
            server_name: Name of the reasoning server
            
        Returns:
            JSON string with server status
        """
        try:
            # This would be called asynchronously in a real implementation
            # For now, return a placeholder
            return json.dumps({
                "server_name": server_name,
                "status": "unknown",
                "server_type": "reasoning",
                "expected_tools": ["recommend_restaurants", "analyze_restaurant_sentiment"],
                "message": "Status check not implemented in synchronous context"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Failed to get status for reasoning server {server_name}: {str(e)}"
            }, indent=2)


def create_reasoning_status_endpoints(app: FastAPI, status_manager: Optional[StatusCheckManager] = None) -> ReasoningStatusEndpoints:
    """Create and register reasoning status check endpoints with FastAPI app.
    
    Args:
        app: FastAPI application instance
        status_manager: Optional status check manager
        
    Returns:
        ReasoningStatusEndpoints instance
    """
    return ReasoningStatusEndpoints(app, status_manager)


def create_reasoning_console_integration(status_manager: Optional[StatusCheckManager] = None) -> ReasoningStatusConsoleIntegration:
    """Create reasoning status console integration.
    
    Args:
        status_manager: Optional status check manager
        
    Returns:
        ReasoningStatusConsoleIntegration instance
    """
    return ReasoningStatusConsoleIntegration(status_manager)