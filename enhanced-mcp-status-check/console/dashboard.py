"""
Enhanced Status Dashboard

This module provides comprehensive dashboard views for dual monitoring results,
showing MCP and REST health status separately with detailed visualizations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    ServerStatus,
    EnhancedCircuitBreakerState
)
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.enhanced_status_config import EnhancedStatusConfig


logger = logging.getLogger(__name__)


class DashboardViewType(Enum):
    """Dashboard view types."""
    OVERVIEW = "overview"
    MCP_DETAILED = "mcp_detailed"
    REST_DETAILED = "rest_detailed"
    COMBINED = "combined"
    METRICS = "metrics"
    ALERTS = "alerts"


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    widget_id: str
    title: str
    widget_type: str
    position: Tuple[int, int]  # (row, column)
    size: Tuple[int, int]  # (width, height)
    config: Dict[str, Any]
    refresh_interval: int = 30  # seconds


@dataclass
class ServerHealthSummary:
    """Server health summary for dashboard display."""
    server_name: str
    overall_status: ServerStatus
    mcp_status: Optional[str]
    rest_status: Optional[str]
    health_score: float
    last_check: datetime
    response_times: Dict[str, float]  # {"mcp": ms, "rest": ms, "combined": ms}
    available_paths: List[str]
    error_summary: Optional[str]


@dataclass
class SystemHealthOverview:
    """System-wide health overview for dashboard."""
    timestamp: datetime
    overall_status: ServerStatus
    total_servers: int
    status_breakdown: Dict[str, int]  # {"healthy": n, "degraded": n, "unhealthy": n}
    monitoring_breakdown: Dict[str, int]  # {"mcp_only": n, "rest_only": n, "both": n}
    average_health_score: float
    average_response_times: Dict[str, float]
    recent_alerts: List[Dict[str, Any]]
    trend_data: Dict[str, List[float]]  # Historical data for charts


class EnhancedStatusDashboard:
    """
    Enhanced Status Dashboard for dual monitoring visualization.
    
    Provides comprehensive dashboard views showing MCP and REST health status
    separately with detailed server information, metrics, and alert management.
    """
    
    def __init__(
        self,
        health_service: EnhancedHealthCheckService,
        metrics_collector: DualMetricsCollector,
        config_manager: EnhancedStatusConfig
    ):
        """
        Initialize Enhanced Status Dashboard.
        
        Args:
            health_service: Enhanced health check service
            metrics_collector: Dual metrics collector
            config_manager: Enhanced status configuration manager
        """
        self.health_service = health_service
        self.metrics_collector = metrics_collector
        self.config_manager = config_manager
        
        # Dashboard state
        self._current_view = DashboardViewType.OVERVIEW
        self._widgets: Dict[str, DashboardWidget] = {}
        self._refresh_tasks: Dict[str, asyncio.Task] = {}
        
        # Data cache
        self._system_overview_cache: Optional[SystemHealthOverview] = None
        self._server_summaries_cache: Dict[str, ServerHealthSummary] = {}
        self._cache_timestamp = datetime.now()
        self._cache_ttl = timedelta(seconds=30)
        
        # Initialize default widgets
        self._initialize_default_widgets()
    
    def _initialize_default_widgets(self):
        """Initialize default dashboard widgets."""
        self._widgets = {
            "system_overview": DashboardWidget(
                widget_id="system_overview",
                title="System Health Overview",
                widget_type="status_summary",
                position=(0, 0),
                size=(2, 1),
                config={"show_trends": True, "show_alerts": True}
            ),
            "mcp_status_grid": DashboardWidget(
                widget_id="mcp_status_grid",
                title="MCP Health Status",
                widget_type="server_grid",
                position=(0, 2),
                size=(2, 2),
                config={"monitoring_type": "mcp", "show_tools": True}
            ),
            "rest_status_grid": DashboardWidget(
                widget_id="rest_status_grid",
                title="REST Health Status",
                widget_type="server_grid",
                position=(2, 0),
                size=(2, 2),
                config={"monitoring_type": "rest", "show_metrics": True}
            ),
            "combined_metrics": DashboardWidget(
                widget_id="combined_metrics",
                title="Combined Metrics",
                widget_type="metrics_chart",
                position=(2, 2),
                size=(2, 2),
                config={"chart_type": "line", "time_range": 3600}
            ),
            "alert_panel": DashboardWidget(
                widget_id="alert_panel",
                title="Recent Alerts",
                widget_type="alert_list",
                position=(4, 0),
                size=(1, 4),
                config={"max_alerts": 10, "auto_refresh": True}
            )
        }
    
    async def get_system_overview(self, force_refresh: bool = False) -> SystemHealthOverview:
        """
        Get system health overview for dashboard display.
        
        Args:
            force_refresh: Force refresh of cached data
            
        Returns:
            SystemHealthOverview: System health overview data
        """
        # Check cache
        if (not force_refresh and 
            self._system_overview_cache and 
            datetime.now() - self._cache_timestamp < self._cache_ttl):
            return self._system_overview_cache
        
        try:
            # Get server configurations
            server_configs = await self.config_manager.get_all_server_configs()
            
            if not server_configs:
                return SystemHealthOverview(
                    timestamp=datetime.now(),
                    overall_status=ServerStatus.UNKNOWN,
                    total_servers=0,
                    status_breakdown={"healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 0},
                    monitoring_breakdown={"mcp_only": 0, "rest_only": 0, "both": 0, "none": 0},
                    average_health_score=0.0,
                    average_response_times={"mcp": 0.0, "rest": 0.0, "combined": 0.0},
                    recent_alerts=[],
                    trend_data={"health_score": [], "response_time": [], "success_rate": []}
                )
            
            # Perform health checks
            dual_results = await self.health_service.check_multiple_servers_dual(server_configs)
            
            # Calculate status breakdown
            status_counts = {"healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 0}
            monitoring_counts = {"mcp_only": 0, "rest_only": 0, "both": 0, "none": 0}
            
            total_health_score = 0.0
            total_mcp_response_time = 0.0
            total_rest_response_time = 0.0
            total_combined_response_time = 0.0
            
            mcp_count = 0
            rest_count = 0
            
            for result in dual_results:
                # Status breakdown
                status_key = result.overall_status.value.lower()
                if status_key in status_counts:
                    status_counts[status_key] += 1
                
                # Monitoring breakdown
                if result.mcp_success and result.rest_success:
                    monitoring_counts["both"] += 1
                elif result.mcp_success:
                    monitoring_counts["mcp_only"] += 1
                elif result.rest_success:
                    monitoring_counts["rest_only"] += 1
                else:
                    monitoring_counts["none"] += 1
                
                # Metrics aggregation
                total_health_score += result.health_score
                total_combined_response_time += result.combined_response_time_ms
                
                if result.mcp_success and result.mcp_response_time_ms > 0:
                    total_mcp_response_time += result.mcp_response_time_ms
                    mcp_count += 1
                
                if result.rest_success and result.rest_response_time_ms > 0:
                    total_rest_response_time += result.rest_response_time_ms
                    rest_count += 1
            
            # Calculate averages
            total_servers = len(dual_results)
            average_health_score = total_health_score / total_servers if total_servers > 0 else 0.0
            average_mcp_response_time = total_mcp_response_time / mcp_count if mcp_count > 0 else 0.0
            average_rest_response_time = total_rest_response_time / rest_count if rest_count > 0 else 0.0
            average_combined_response_time = total_combined_response_time / total_servers if total_servers > 0 else 0.0
            
            # Determine overall status
            if status_counts["unhealthy"] > 0:
                overall_status = ServerStatus.UNHEALTHY
            elif status_counts["degraded"] > 0:
                overall_status = ServerStatus.DEGRADED
            elif status_counts["healthy"] > 0:
                overall_status = ServerStatus.HEALTHY
            else:
                overall_status = ServerStatus.UNKNOWN
            
            # Get recent alerts (placeholder - would integrate with alert manager)
            recent_alerts = await self._get_recent_alerts()
            
            # Get trend data (placeholder - would integrate with metrics collector)
            trend_data = await self._get_trend_data()
            
            # Create overview
            overview = SystemHealthOverview(
                timestamp=datetime.now(),
                overall_status=overall_status,
                total_servers=total_servers,
                status_breakdown=status_counts,
                monitoring_breakdown=monitoring_counts,
                average_health_score=average_health_score,
                average_response_times={
                    "mcp": average_mcp_response_time,
                    "rest": average_rest_response_time,
                    "combined": average_combined_response_time
                },
                recent_alerts=recent_alerts,
                trend_data=trend_data
            )
            
            # Update cache
            self._system_overview_cache = overview
            self._cache_timestamp = datetime.now()
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            # Return error state
            return SystemHealthOverview(
                timestamp=datetime.now(),
                overall_status=ServerStatus.UNKNOWN,
                total_servers=0,
                status_breakdown={"healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 1},
                monitoring_breakdown={"mcp_only": 0, "rest_only": 0, "both": 0, "none": 1},
                average_health_score=0.0,
                average_response_times={"mcp": 0.0, "rest": 0.0, "combined": 0.0},
                recent_alerts=[{"type": "error", "message": f"Dashboard error: {str(e)}"}],
                trend_data={"health_score": [], "response_time": [], "success_rate": []}
            )
    
    async def get_server_summaries(
        self,
        monitoring_type: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[ServerHealthSummary]:
        """
        Get server health summaries for dashboard display.
        
        Args:
            monitoring_type: Filter by monitoring type ("mcp", "rest", or None for all)
            force_refresh: Force refresh of cached data
            
        Returns:
            List[ServerHealthSummary]: Server health summaries
        """
        try:
            # Get server configurations
            server_configs = await self.config_manager.get_all_server_configs()
            
            if not server_configs:
                return []
            
            # Perform health checks
            dual_results = await self.health_service.check_multiple_servers_dual(server_configs)
            
            summaries = []
            for result in dual_results:
                # Filter by monitoring type if specified
                if monitoring_type == "mcp" and not result.mcp_success:
                    continue
                elif monitoring_type == "rest" and not result.rest_success:
                    continue
                
                # Create response times dict
                response_times = {
                    "combined": result.combined_response_time_ms
                }
                
                if result.mcp_response_time_ms > 0:
                    response_times["mcp"] = result.mcp_response_time_ms
                
                if result.rest_response_time_ms > 0:
                    response_times["rest"] = result.rest_response_time_ms
                
                # Create error summary
                error_summary = None
                if not result.overall_success:
                    errors = []
                    if result.mcp_error_message:
                        errors.append(f"MCP: {result.mcp_error_message}")
                    if result.rest_error_message:
                        errors.append(f"REST: {result.rest_error_message}")
                    error_summary = "; ".join(errors) if errors else "Unknown error"
                
                # Determine individual status
                mcp_status = None
                if result.mcp_result:
                    mcp_status = "SUCCESS" if result.mcp_success else "FAILED"
                
                rest_status = None
                if result.rest_result:
                    rest_status = "SUCCESS" if result.rest_success else "FAILED"
                
                summary = ServerHealthSummary(
                    server_name=result.server_name,
                    overall_status=result.overall_status,
                    mcp_status=mcp_status,
                    rest_status=rest_status,
                    health_score=result.health_score,
                    last_check=result.timestamp,
                    response_times=response_times,
                    available_paths=result.available_paths,
                    error_summary=error_summary
                )
                
                summaries.append(summary)
            
            # Update cache
            for summary in summaries:
                self._server_summaries_cache[summary.server_name] = summary
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting server summaries: {e}")
            return []
    
    async def get_mcp_detailed_view(self) -> Dict[str, Any]:
        """
        Get detailed MCP monitoring view data.
        
        Returns:
            Dict[str, Any]: MCP detailed view data
        """
        try:
            server_summaries = await self.get_server_summaries(monitoring_type="mcp")
            
            # Get MCP-specific metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            mcp_metrics = await self.metrics_collector.get_mcp_metrics(start_time, end_time)
            
            # Organize data for MCP view
            mcp_servers = []
            for summary in server_summaries:
                if summary.mcp_status:
                    server_data = {
                        "server_name": summary.server_name,
                        "status": summary.mcp_status,
                        "response_time_ms": summary.response_times.get("mcp", 0),
                        "last_check": summary.last_check.isoformat(),
                        "tools_count": 0,  # Would get from MCP result
                        "validation_errors": [],  # Would get from MCP result
                        "error_message": summary.error_summary if summary.mcp_status == "FAILED" else None
                    }
                    
                    # Add MCP-specific details if available
                    cached_result = self._server_summaries_cache.get(summary.server_name)
                    if cached_result:
                        # Would extract MCP-specific data here
                        pass
                    
                    mcp_servers.append(server_data)
            
            return {
                "view_type": "mcp_detailed",
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_mcp_servers": len(mcp_servers),
                    "successful_checks": len([s for s in mcp_servers if s["status"] == "SUCCESS"]),
                    "failed_checks": len([s for s in mcp_servers if s["status"] == "FAILED"]),
                    "average_response_time": sum(s["response_time_ms"] for s in mcp_servers) / len(mcp_servers) if mcp_servers else 0
                },
                "servers": mcp_servers,
                "metrics": mcp_metrics,
                "protocol_info": {
                    "jsonrpc_version": "2.0",
                    "method": "tools/list",
                    "expected_tools": []  # Would get from configuration
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting MCP detailed view: {e}")
            return {
                "view_type": "mcp_detailed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "summary": {"total_mcp_servers": 0, "successful_checks": 0, "failed_checks": 0},
                "servers": [],
                "metrics": {},
                "protocol_info": {}
            }
    
    async def get_rest_detailed_view(self) -> Dict[str, Any]:
        """
        Get detailed REST monitoring view data.
        
        Returns:
            Dict[str, Any]: REST detailed view data
        """
        try:
            server_summaries = await self.get_server_summaries(monitoring_type="rest")
            
            # Get REST-specific metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            rest_metrics = await self.metrics_collector.get_rest_metrics(start_time, end_time)
            
            # Organize data for REST view
            rest_servers = []
            for summary in server_summaries:
                if summary.rest_status:
                    server_data = {
                        "server_name": summary.server_name,
                        "status": summary.rest_status,
                        "response_time_ms": summary.response_times.get("rest", 0),
                        "last_check": summary.last_check.isoformat(),
                        "status_code": 0,  # Would get from REST result
                        "endpoint_url": "",  # Would get from configuration
                        "response_size": 0,  # Would get from REST result
                        "error_message": summary.error_summary if summary.rest_status == "FAILED" else None
                    }
                    
                    # Add REST-specific details if available
                    cached_result = self._server_summaries_cache.get(summary.server_name)
                    if cached_result:
                        # Would extract REST-specific data here
                        pass
                    
                    rest_servers.append(server_data)
            
            return {
                "view_type": "rest_detailed",
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_rest_servers": len(rest_servers),
                    "successful_checks": len([s for s in rest_servers if s["status"] == "SUCCESS"]),
                    "failed_checks": len([s for s in rest_servers if s["status"] == "FAILED"]),
                    "average_response_time": sum(s["response_time_ms"] for s in rest_servers) / len(rest_servers) if rest_servers else 0
                },
                "servers": rest_servers,
                "metrics": rest_metrics,
                "protocol_info": {
                    "method": "GET",
                    "expected_status_codes": [200],
                    "health_endpoint_path": "/status/health"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting REST detailed view: {e}")
            return {
                "view_type": "rest_detailed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "summary": {"total_rest_servers": 0, "successful_checks": 0, "failed_checks": 0},
                "servers": [],
                "metrics": {},
                "protocol_info": {}
            }
    
    async def get_combined_view(self) -> Dict[str, Any]:
        """
        Get combined monitoring view showing both MCP and REST data.
        
        Returns:
            Dict[str, Any]: Combined view data
        """
        try:
            # Get both detailed views
            mcp_view = await self.get_mcp_detailed_view()
            rest_view = await self.get_rest_detailed_view()
            
            # Get combined metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            combined_metrics = await self.metrics_collector.get_combined_metrics(start_time, end_time)
            
            # Create combined server data
            all_servers = await self.get_server_summaries()
            combined_servers = []
            
            for summary in all_servers:
                server_data = {
                    "server_name": summary.server_name,
                    "overall_status": summary.overall_status.value,
                    "health_score": summary.health_score,
                    "available_paths": summary.available_paths,
                    "last_check": summary.last_check.isoformat(),
                    "mcp": {
                        "status": summary.mcp_status,
                        "response_time_ms": summary.response_times.get("mcp", 0)
                    },
                    "rest": {
                        "status": summary.rest_status,
                        "response_time_ms": summary.response_times.get("rest", 0)
                    },
                    "combined_response_time_ms": summary.response_times.get("combined", 0),
                    "error_summary": summary.error_summary
                }
                combined_servers.append(server_data)
            
            return {
                "view_type": "combined",
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_servers": len(combined_servers),
                    "mcp_summary": mcp_view["summary"],
                    "rest_summary": rest_view["summary"],
                    "dual_monitoring_coverage": len([s for s in combined_servers if s["mcp"]["status"] and s["rest"]["status"]])
                },
                "servers": combined_servers,
                "metrics": {
                    "mcp": mcp_view["metrics"],
                    "rest": rest_view["metrics"],
                    "combined": combined_metrics
                },
                "comparison": {
                    "mcp_vs_rest_correlation": 0.0,  # Would calculate correlation
                    "path_availability": {
                        "both_available": len([s for s in combined_servers if "mcp" in s["available_paths"] and "rest" in s["available_paths"]]),
                        "mcp_only": len([s for s in combined_servers if "mcp" in s["available_paths"] and "rest" not in s["available_paths"]]),
                        "rest_only": len([s for s in combined_servers if "rest" in s["available_paths"] and "mcp" not in s["available_paths"]]),
                        "none_available": len([s for s in combined_servers if not s["available_paths"]])
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting combined view: {e}")
            return {
                "view_type": "combined",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "summary": {},
                "servers": [],
                "metrics": {},
                "comparison": {}
            }
    
    async def get_widget_data(self, widget_id: str) -> Dict[str, Any]:
        """
        Get data for a specific dashboard widget.
        
        Args:
            widget_id: Widget identifier
            
        Returns:
            Dict[str, Any]: Widget data
        """
        widget = self._widgets.get(widget_id)
        if not widget:
            return {"error": f"Widget '{widget_id}' not found"}
        
        try:
            if widget.widget_type == "status_summary":
                overview = await self.get_system_overview()
                return {
                    "widget_id": widget_id,
                    "title": widget.title,
                    "type": widget.widget_type,
                    "data": {
                        "overall_status": overview.overall_status.value,
                        "total_servers": overview.total_servers,
                        "status_breakdown": overview.status_breakdown,
                        "monitoring_breakdown": overview.monitoring_breakdown,
                        "health_score": overview.average_health_score,
                        "recent_alerts": overview.recent_alerts[:5]  # Show top 5
                    },
                    "timestamp": overview.timestamp.isoformat()
                }
            
            elif widget.widget_type == "server_grid":
                monitoring_type = widget.config.get("monitoring_type")
                summaries = await self.get_server_summaries(monitoring_type)
                
                return {
                    "widget_id": widget_id,
                    "title": widget.title,
                    "type": widget.widget_type,
                    "data": {
                        "monitoring_type": monitoring_type,
                        "servers": [
                            {
                                "name": s.server_name,
                                "status": s.overall_status.value,
                                "health_score": s.health_score,
                                "response_time": s.response_times.get(monitoring_type or "combined", 0),
                                "last_check": s.last_check.isoformat(),
                                "error": s.error_summary
                            }
                            for s in summaries
                        ]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            elif widget.widget_type == "metrics_chart":
                time_range = widget.config.get("time_range", 3600)
                end_time = datetime.now()
                start_time = end_time - timedelta(seconds=time_range)
                
                combined_metrics = await self.metrics_collector.get_combined_metrics(start_time, end_time)
                
                return {
                    "widget_id": widget_id,
                    "title": widget.title,
                    "type": widget.widget_type,
                    "data": {
                        "time_range": time_range,
                        "metrics": combined_metrics,
                        "chart_config": widget.config
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            elif widget.widget_type == "alert_list":
                max_alerts = widget.config.get("max_alerts", 10)
                recent_alerts = await self._get_recent_alerts(limit=max_alerts)
                
                return {
                    "widget_id": widget_id,
                    "title": widget.title,
                    "type": widget.widget_type,
                    "data": {
                        "alerts": recent_alerts,
                        "total_count": len(recent_alerts)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                return {"error": f"Unknown widget type: {widget.widget_type}"}
                
        except Exception as e:
            logger.error(f"Error getting widget data for {widget_id}: {e}")
            return {
                "widget_id": widget_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts (placeholder implementation)."""
        # This would integrate with the alert manager
        return [
            {
                "id": "alert_1",
                "type": "warning",
                "severity": "medium",
                "message": "MCP health check failed for server-1",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "server": "server-1",
                "monitoring_type": "mcp"
            },
            {
                "id": "alert_2",
                "type": "info",
                "severity": "low",
                "message": "REST response time increased for server-2",
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "server": "server-2",
                "monitoring_type": "rest"
            }
        ][:limit]
    
    async def _get_trend_data(self) -> Dict[str, List[float]]:
        """Get trend data for charts (placeholder implementation)."""
        # This would integrate with the metrics collector for historical data
        return {
            "health_score": [0.95, 0.92, 0.88, 0.90, 0.93, 0.91, 0.94],
            "response_time": [120, 135, 150, 140, 125, 130, 128],
            "success_rate": [0.98, 0.96, 0.94, 0.95, 0.97, 0.96, 0.98]
        }
    
    def add_widget(self, widget: DashboardWidget):
        """Add a new widget to the dashboard."""
        self._widgets[widget.widget_id] = widget
        logger.info(f"Added widget '{widget.widget_id}' to dashboard")
    
    def remove_widget(self, widget_id: str):
        """Remove a widget from the dashboard."""
        if widget_id in self._widgets:
            del self._widgets[widget_id]
            logger.info(f"Removed widget '{widget_id}' from dashboard")
    
    def get_dashboard_layout(self) -> Dict[str, Any]:
        """Get current dashboard layout configuration."""
        return {
            "current_view": self._current_view.value,
            "widgets": {
                widget_id: {
                    "title": widget.title,
                    "type": widget.widget_type,
                    "position": widget.position,
                    "size": widget.size,
                    "config": widget.config,
                    "refresh_interval": widget.refresh_interval
                }
                for widget_id, widget in self._widgets.items()
            },
            "layout_timestamp": datetime.now().isoformat()
        }
    
    async def export_dashboard_data(self, format_type: str = "json") -> str:
        """
        Export dashboard data for external use.
        
        Args:
            format_type: Export format ("json", "csv", "html")
            
        Returns:
            str: Exported data
        """
        try:
            # Get all dashboard data
            overview = await self.get_system_overview()
            summaries = await self.get_server_summaries()
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "system_overview": {
                    "overall_status": overview.overall_status.value,
                    "total_servers": overview.total_servers,
                    "status_breakdown": overview.status_breakdown,
                    "monitoring_breakdown": overview.monitoring_breakdown,
                    "average_health_score": overview.average_health_score,
                    "average_response_times": overview.average_response_times
                },
                "server_details": [
                    {
                        "server_name": s.server_name,
                        "overall_status": s.overall_status.value,
                        "mcp_status": s.mcp_status,
                        "rest_status": s.rest_status,
                        "health_score": s.health_score,
                        "response_times": s.response_times,
                        "available_paths": s.available_paths,
                        "last_check": s.last_check.isoformat(),
                        "error_summary": s.error_summary
                    }
                    for s in summaries
                ]
            }
            
            if format_type == "json":
                return json.dumps(export_data, indent=2)
            elif format_type == "csv":
                # Convert to CSV format (simplified)
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write headers
                writer.writerow([
                    "Server Name", "Overall Status", "MCP Status", "REST Status",
                    "Health Score", "MCP Response Time", "REST Response Time",
                    "Available Paths", "Last Check", "Error Summary"
                ])
                
                # Write data
                for server in export_data["server_details"]:
                    writer.writerow([
                        server["server_name"],
                        server["overall_status"],
                        server["mcp_status"] or "N/A",
                        server["rest_status"] or "N/A",
                        server["health_score"],
                        server["response_times"].get("mcp", "N/A"),
                        server["response_times"].get("rest", "N/A"),
                        ", ".join(server["available_paths"]),
                        server["last_check"],
                        server["error_summary"] or "None"
                    ])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            logger.error(f"Error exporting dashboard data: {e}")
            return f"Export error: {str(e)}"