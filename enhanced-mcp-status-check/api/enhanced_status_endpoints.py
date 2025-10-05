"""
Enhanced Status Check REST API Endpoints

This module implements enhanced REST API endpoints that provide detailed status information
from both MCP tools/list and REST health checks with backward-compatible response formats.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Query, Path, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import json

from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig,
    ServerStatus,
    AggregationConfig,
    PriorityConfig
)
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.enhanced_status_config import EnhancedStatusConfig


logger = logging.getLogger(__name__)


# Request/Response Models
class HealthCheckRequest(BaseModel):
    """Request model for manual health checks."""
    server_names: Optional[List[str]] = Field(None, description="Specific servers to check")
    timeout_seconds: Optional[int] = Field(30, description="Timeout for health checks")
    include_mcp: bool = Field(True, description="Include MCP health checks")
    include_rest: bool = Field(True, description="Include REST health checks")


class ServerStatusResponse(BaseModel):
    """Response model for server status."""
    server_name: str
    status: str
    success: bool
    timestamp: str
    mcp_result: Optional[Dict[str, Any]] = None
    rest_result: Optional[Dict[str, Any]] = None
    combined_metrics: Optional[Dict[str, Any]] = None
    health_score: float
    available_paths: List[str]
    error_message: Optional[str] = None


class SystemHealthResponse(BaseModel):
    """Response model for system health overview."""
    overall_status: str
    total_servers: int
    healthy_servers: int
    degraded_servers: int
    unhealthy_servers: int
    unknown_servers: int
    last_check_timestamp: str
    average_health_score: float
    average_response_time_ms: float
    servers: List[ServerStatusResponse]


class MetricsResponse(BaseModel):
    """Response model for metrics data."""
    timestamp: str
    mcp_metrics: Dict[str, Any]
    rest_metrics: Dict[str, Any]
    combined_metrics: Dict[str, Any]
    server_metrics: Dict[str, Dict[str, Any]]


class ConfigurationResponse(BaseModel):
    """Response model for configuration data."""
    enhanced_monitoring_enabled: bool
    mcp_health_checks: Dict[str, Any]
    rest_health_checks: Dict[str, Any]
    result_aggregation: Dict[str, Any]
    servers: List[Dict[str, Any]]
    last_updated: str


class EnhancedStatusEndpoints:
    """
    Enhanced Status Check REST API Endpoints.
    
    Provides comprehensive REST API endpoints for dual monitoring with MCP and REST
    health checks, including backward compatibility with existing monitoring systems.
    """
    
    def __init__(
        self,
        health_service: EnhancedHealthCheckService,
        metrics_collector: DualMetricsCollector,
        config_manager: EnhancedStatusConfig,
        app: Optional[FastAPI] = None
    ):
        """
        Initialize Enhanced Status Endpoints.
        
        Args:
            health_service: Enhanced health check service
            metrics_collector: Dual metrics collector
            config_manager: Enhanced status configuration manager
            app: Optional FastAPI app instance
        """
        self.health_service = health_service
        self.metrics_collector = metrics_collector
        self.config_manager = config_manager
        self.app = app or FastAPI(title="Enhanced MCP Status Check API")
        
        # Cache for recent results
        self._result_cache: Dict[str, DualHealthCheckResult] = {}
        self._cache_ttl = timedelta(minutes=5)
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        
        # Register endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Register all API endpoints."""
        
        @self.app.get("/status/health", response_model=SystemHealthResponse)
        async def get_system_health(
            include_servers: bool = Query(True, description="Include individual server details"),
            force_check: bool = Query(False, description="Force new health checks"),
            timeout: int = Query(30, description="Timeout for health checks")
        ):
            """
            Enhanced /status/health endpoint with dual monitoring results.
            
            Provides comprehensive system health status with results from both
            MCP tools/list and REST health checks, maintaining backward compatibility.
            """
            return await self._get_system_health(include_servers, force_check, timeout)
        
        @self.app.get("/status/servers/{server_name}", response_model=ServerStatusResponse)
        async def get_server_status(
            server_name: str = Path(..., description="Server name to check"),
            force_check: bool = Query(False, description="Force new health check"),
            timeout: int = Query(30, description="Timeout for health check")
        ):
            """
            Enhanced /status/servers/{server_name} endpoint with detailed MCP and REST data.
            
            Provides detailed server status with separate MCP and REST health check results,
            combined metrics, and intelligent status aggregation.
            """
            return await self._get_server_status(server_name, force_check, timeout)
        
        @self.app.get("/status/metrics", response_model=MetricsResponse)
        async def get_system_metrics(
            time_range: int = Query(3600, description="Time range in seconds"),
            include_server_breakdown: bool = Query(True, description="Include per-server metrics")
        ):
            """
            Enhanced /status/metrics endpoint with separate MCP and REST metrics.
            
            Provides comprehensive metrics from both monitoring methods with
            aggregated statistics and per-server breakdowns.
            """
            return await self._get_system_metrics(time_range, include_server_breakdown)
        
        @self.app.post("/status/dual-check")
        async def trigger_dual_health_check(
            request: HealthCheckRequest,
            background_tasks: BackgroundTasks
        ):
            """
            Enhanced /status/dual-check endpoint for manual dual health checks.
            
            Triggers manual health checks using both MCP tools/list and REST methods
            with configurable options and returns combined results.
            """
            return await self._trigger_dual_health_check(request, background_tasks)
        
        @self.app.get("/status/config", response_model=ConfigurationResponse)
        async def get_configuration(
            include_sensitive: bool = Query(False, description="Include sensitive configuration data")
        ):
            """
            Enhanced /status/config endpoint with enhanced configuration display.
            
            Provides current dual monitoring configuration including MCP and REST
            settings, aggregation rules, and server configurations.
            """
            return await self._get_configuration(include_sensitive)
        
        @self.app.put("/status/config")
        async def update_configuration(
            config_update: Dict[str, Any]
        ):
            """
            Update enhanced status check configuration.
            
            Allows runtime updates to dual monitoring configuration including
            timeout values, retry policies, and aggregation rules.
            """
            return await self._update_configuration(config_update)
        
        # Backward compatibility endpoints
        @self.app.get("/health")
        async def legacy_health_endpoint():
            """Legacy /health endpoint for backward compatibility."""
            return await self._get_legacy_health()
        
        @self.app.get("/status")
        async def legacy_status_endpoint():
            """Legacy /status endpoint for backward compatibility."""
            return await self._get_legacy_status()
    
    async def _get_system_health(
        self,
        include_servers: bool,
        force_check: bool,
        timeout: int
    ) -> SystemHealthResponse:
        """Get comprehensive system health status."""
        try:
            # Get server configurations
            server_configs = await self.config_manager.get_all_server_configs()
            
            if not server_configs:
                return SystemHealthResponse(
                    overall_status="UNKNOWN",
                    total_servers=0,
                    healthy_servers=0,
                    degraded_servers=0,
                    unhealthy_servers=0,
                    unknown_servers=0,
                    last_check_timestamp=datetime.now().isoformat(),
                    average_health_score=0.0,
                    average_response_time_ms=0.0,
                    servers=[]
                )
            
            # Perform health checks
            if force_check:
                dual_results = await self.health_service.check_multiple_servers_dual(
                    server_configs=server_configs,
                    timeout_per_server=timeout
                )
                # Update cache
                for result in dual_results:
                    self._result_cache[result.server_name] = result
            else:
                # Use cached results if available and recent
                dual_results = []
                for config in server_configs:
                    cached_result = self._result_cache.get(config.server_name)
                    if (cached_result and 
                        datetime.now() - cached_result.timestamp < self._cache_ttl):
                        dual_results.append(cached_result)
                    else:
                        # Perform fresh check
                        result = await self.health_service.perform_dual_health_check(config)
                        dual_results.append(result)
                        self._result_cache[config.server_name] = result
            
            # Create summary statistics
            summary = self.health_service.aggregator.create_aggregation_summary(dual_results)
            
            # Determine overall system status
            if summary["unhealthy_servers"] > 0:
                overall_status = "UNHEALTHY"
            elif summary["degraded_servers"] > 0:
                overall_status = "DEGRADED"
            elif summary["healthy_servers"] > 0:
                overall_status = "HEALTHY"
            else:
                overall_status = "UNKNOWN"
            
            # Create server responses
            servers = []
            if include_servers:
                for result in dual_results:
                    server_response = self._create_server_status_response(result)
                    servers.append(server_response)
            
            return SystemHealthResponse(
                overall_status=overall_status,
                total_servers=summary["total_servers"],
                healthy_servers=summary["healthy_servers"],
                degraded_servers=summary["degraded_servers"],
                unhealthy_servers=summary["unhealthy_servers"],
                unknown_servers=summary["unknown_servers"],
                last_check_timestamp=datetime.now().isoformat(),
                average_health_score=summary["average_health_score"],
                average_response_time_ms=summary["average_response_time_ms"],
                servers=servers
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _get_server_status(
        self,
        server_name: str,
        force_check: bool,
        timeout: int
    ) -> ServerStatusResponse:
        """Get detailed status for a specific server."""
        try:
            # Get server configuration
            server_config = await self.config_manager.get_server_config(server_name)
            if not server_config:
                raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
            
            # Get or perform health check
            if force_check:
                dual_result = await self.health_service.perform_dual_health_check(
                    server_config=server_config,
                    timeout_override=timeout
                )
                self._result_cache[server_name] = dual_result
            else:
                cached_result = self._result_cache.get(server_name)
                if (cached_result and 
                    datetime.now() - cached_result.timestamp < self._cache_ttl):
                    dual_result = cached_result
                else:
                    dual_result = await self.health_service.perform_dual_health_check(server_config)
                    self._result_cache[server_name] = dual_result
            
            return self._create_server_status_response(dual_result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting server status for {server_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _get_system_metrics(
        self,
        time_range: int,
        include_server_breakdown: bool
    ) -> MetricsResponse:
        """Get comprehensive system metrics."""
        try:
            # Get metrics from collector
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=time_range)
            
            mcp_metrics = await self.metrics_collector.get_mcp_metrics(start_time, end_time)
            rest_metrics = await self.metrics_collector.get_rest_metrics(start_time, end_time)
            combined_metrics = await self.metrics_collector.get_combined_metrics(start_time, end_time)
            
            # Get per-server metrics if requested
            server_metrics = {}
            if include_server_breakdown:
                server_configs = await self.config_manager.get_all_server_configs()
                for config in server_configs:
                    server_name = config.server_name
                    server_mcp_metrics = await self.metrics_collector.get_server_mcp_metrics(
                        server_name, start_time, end_time
                    )
                    server_rest_metrics = await self.metrics_collector.get_server_rest_metrics(
                        server_name, start_time, end_time
                    )
                    
                    server_metrics[server_name] = {
                        "mcp_metrics": server_mcp_metrics,
                        "rest_metrics": server_rest_metrics
                    }
            
            return MetricsResponse(
                timestamp=datetime.now().isoformat(),
                mcp_metrics=mcp_metrics,
                rest_metrics=rest_metrics,
                combined_metrics=combined_metrics,
                server_metrics=server_metrics
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _trigger_dual_health_check(
        self,
        request: HealthCheckRequest,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Trigger manual dual health checks."""
        try:
            # Get server configurations
            if request.server_names:
                server_configs = []
                for server_name in request.server_names:
                    config = await self.config_manager.get_server_config(server_name)
                    if config:
                        server_configs.append(config)
                    else:
                        logger.warning(f"Server '{server_name}' not found in configuration")
            else:
                server_configs = await self.config_manager.get_all_server_configs()
            
            if not server_configs:
                raise HTTPException(status_code=400, detail="No valid servers found")
            
            # Modify configurations based on request
            for config in server_configs:
                if not request.include_mcp:
                    config.mcp_enabled = False
                if not request.include_rest:
                    config.rest_enabled = False
            
            # Perform health checks
            dual_results = await self.health_service.check_multiple_servers_dual(
                server_configs=server_configs,
                timeout_per_server=request.timeout_seconds
            )
            
            # Update cache
            for result in dual_results:
                self._result_cache[result.server_name] = result
            
            # Create response
            server_results = []
            for result in dual_results:
                server_response = self._create_server_status_response(result)
                server_results.append(server_response.dict())
            
            # Create summary
            summary = self.health_service.aggregator.create_aggregation_summary(dual_results)
            
            return {
                "check_id": f"manual-{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "request_parameters": request.dict(),
                "summary": summary,
                "servers": server_results
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error triggering dual health check: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _get_configuration(
        self,
        include_sensitive: bool
    ) -> ConfigurationResponse:
        """Get current configuration."""
        try:
            config = await self.config_manager.get_current_config()
            server_configs = await self.config_manager.get_all_server_configs()
            
            # Prepare server configurations
            servers = []
            for server_config in server_configs:
                server_dict = server_config.to_dict()
                if not include_sensitive:
                    # Remove sensitive information
                    server_dict.pop("jwt_token", None)
                    server_dict.pop("auth_headers", None)
                servers.append(server_dict)
            
            return ConfigurationResponse(
                enhanced_monitoring_enabled=config.dual_monitoring_enabled,
                mcp_health_checks=config.mcp_health_checks,
                rest_health_checks=config.rest_health_checks,
                result_aggregation=config.result_aggregation,
                servers=servers,
                last_updated=config.last_updated.isoformat() if config.last_updated else datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _update_configuration(
        self,
        config_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update configuration."""
        try:
            # Validate and apply configuration update
            success = await self.config_manager.update_config(config_update)
            
            if not success:
                raise HTTPException(status_code=400, detail="Invalid configuration update")
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "timestamp": datetime.now().isoformat(),
                "updated_fields": list(config_update.keys())
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _get_legacy_health(self) -> Dict[str, Any]:
        """Legacy health endpoint for backward compatibility."""
        try:
            system_health = await self._get_system_health(
                include_servers=False,
                force_check=False,
                timeout=30
            )
            
            # Convert to legacy format
            return {
                "status": system_health.overall_status.lower(),
                "healthy": system_health.overall_status == "HEALTHY",
                "timestamp": system_health.last_check_timestamp,
                "servers": {
                    "total": system_health.total_servers,
                    "healthy": system_health.healthy_servers,
                    "unhealthy": system_health.unhealthy_servers + system_health.degraded_servers
                }
            }
            
        except Exception as e:
            logger.error(f"Error in legacy health endpoint: {e}")
            return {
                "status": "error",
                "healthy": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _get_legacy_status(self) -> Dict[str, Any]:
        """Legacy status endpoint for backward compatibility."""
        try:
            system_health = await self._get_system_health(
                include_servers=True,
                force_check=False,
                timeout=30
            )
            
            # Convert to legacy format
            servers = {}
            for server in system_health.servers:
                servers[server.server_name] = {
                    "status": server.status.lower(),
                    "healthy": server.success,
                    "last_check": server.timestamp,
                    "response_time_ms": getattr(server, 'response_time_ms', 0)
                }
            
            return {
                "overall_status": system_health.overall_status.lower(),
                "servers": servers,
                "summary": {
                    "total": system_health.total_servers,
                    "healthy": system_health.healthy_servers,
                    "degraded": system_health.degraded_servers,
                    "unhealthy": system_health.unhealthy_servers
                },
                "timestamp": system_health.last_check_timestamp
            }
            
        except Exception as e:
            logger.error(f"Error in legacy status endpoint: {e}")
            return {
                "overall_status": "error",
                "servers": {},
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_server_status_response(
        self,
        dual_result: DualHealthCheckResult
    ) -> ServerStatusResponse:
        """Create server status response from dual result."""
        # Determine error message
        error_message = None
        if not dual_result.overall_success:
            errors = []
            if dual_result.mcp_error_message:
                errors.append(f"MCP: {dual_result.mcp_error_message}")
            if dual_result.rest_error_message:
                errors.append(f"REST: {dual_result.rest_error_message}")
            error_message = "; ".join(errors) if errors else "Unknown error"
        
        return ServerStatusResponse(
            server_name=dual_result.server_name,
            status=dual_result.overall_status.value,
            success=dual_result.overall_success,
            timestamp=dual_result.timestamp.isoformat(),
            mcp_result=dual_result.mcp_result.to_dict() if dual_result.mcp_result else None,
            rest_result=dual_result.rest_result.to_dict() if dual_result.rest_result else None,
            combined_metrics=dual_result.combined_metrics.to_dict() if dual_result.combined_metrics else None,
            health_score=dual_result.health_score,
            available_paths=dual_result.available_paths,
            error_message=error_message
        )
    
    async def start_background_tasks(self):
        """Start background tasks for cache management."""
        async def cache_cleanup_task():
            """Background task to clean up expired cache entries."""
            while True:
                try:
                    current_time = datetime.now()
                    expired_keys = []
                    
                    for server_name, result in self._result_cache.items():
                        if current_time - result.timestamp > self._cache_ttl:
                            expired_keys.append(server_name)
                    
                    for key in expired_keys:
                        self._result_cache.pop(key, None)
                    
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                    
                    # Sleep for 1 minute before next cleanup
                    await asyncio.sleep(60)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cache cleanup task: {e}")
                    await asyncio.sleep(60)
        
        # Start cache cleanup task
        cleanup_task = asyncio.create_task(cache_cleanup_task())
        self._background_tasks.append(cleanup_task)
        
        logger.info("Started background tasks for enhanced status endpoints")
    
    async def stop_background_tasks(self):
        """Stop all background tasks."""
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
        logger.info("Stopped background tasks for enhanced status endpoints")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_background_tasks()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_background_tasks()


def create_enhanced_status_app(
    health_service: EnhancedHealthCheckService,
    metrics_collector: DualMetricsCollector,
    config_manager: EnhancedStatusConfig
) -> FastAPI:
    """
    Create FastAPI application with enhanced status endpoints.
    
    Args:
        health_service: Enhanced health check service
        metrics_collector: Dual metrics collector
        config_manager: Enhanced status configuration manager
        
    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title="Enhanced MCP Status Check API",
        description="Comprehensive health monitoring for MCP servers with dual monitoring approaches",
        version="1.0.0"
    )
    
    # Create endpoints
    endpoints = EnhancedStatusEndpoints(
        health_service=health_service,
        metrics_collector=metrics_collector,
        config_manager=config_manager,
        app=app
    )
    
    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        await endpoints.start_background_tasks()
        logger.info("Enhanced MCP Status Check API started")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await endpoints.stop_background_tasks()
        logger.info("Enhanced MCP Status Check API stopped")
    
    return app