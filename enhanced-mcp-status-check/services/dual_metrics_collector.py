"""
Enhanced MCP Status Check Dual Metrics Collector

This module implements the DualMetricsCollector class that collects and manages
metrics from both MCP tools/list requests and REST health checks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import threading

from models import (
    DualHealthCheckResult, MCPHealthCheckResult, RESTHealthCheckResult,
    EnhancedServerConfig, ServerStatus, MCPMetrics, RESTMetrics, 
    CombinedMetrics, MetricsAggregationReport, TimeWindow, 
    MetricDataPoint, MetricSeries
)


class DualMetricsCollector:
    """
    Collects and manages metrics from both MCP and REST health checks.
    
    This class provides comprehensive metrics collection for the enhanced status check system,
    tracking response times, success rates, tool availability, and other key performance indicators
    for both MCP tools/list requests and REST health check endpoints.
    """
    
    def __init__(self, retention_period: timedelta = timedelta(days=7)):
        """
        Initialize the dual metrics collector.
        
        Args:
            retention_period: How long to retain metric data points
        """
        self.logger = logging.getLogger(__name__)
        self.retention_period = retention_period
        
        # Metrics storage by server name
        self._mcp_metrics: Dict[str, MCPMetrics] = {}
        self._rest_metrics: Dict[str, RESTMetrics] = {}
        self._combined_metrics: Dict[str, CombinedMetrics] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        self.logger.info("DualMetricsCollector initialized with retention period: %s", retention_period)
    
    async def start(self) -> None:
        """Start the metrics collector background tasks."""
        self.logger.info("Starting DualMetricsCollector background tasks")
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())
    
    async def stop(self) -> None:
        """Stop the metrics collector and cleanup resources."""
        self.logger.info("Stopping DualMetricsCollector")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for cleanup task to finish
        if self._cleanup_task:
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("Cleanup task did not finish within timeout")
                self._cleanup_task.cancel()
    
    def record_dual_health_check_result(self, result: DualHealthCheckResult) -> None:
        """
        Record metrics from a dual health check result.
        
        Args:
            result: The dual health check result to extract metrics from
        """
        with self._lock:
            server_name = result.server_name
            
            # Ensure metrics objects exist for this server
            self._ensure_metrics_exist(server_name)
            
            # Record MCP metrics if available
            if result.mcp_result:
                self._record_mcp_metrics(result.mcp_result)
            
            # Record REST metrics if available
            if result.rest_result:
                self._record_rest_metrics(result.rest_result)
            
            # Record combined metrics
            self._record_combined_metrics(result)
            
            self.logger.debug("Recorded metrics for server: %s", server_name)
    
    def record_mcp_health_check_result(self, result: MCPHealthCheckResult) -> None:
        """
        Record metrics from an MCP health check result.
        
        Args:
            result: The MCP health check result to extract metrics from
        """
        with self._lock:
            self._ensure_metrics_exist(result.server_name)
            self._record_mcp_metrics(result)
    
    def record_rest_health_check_result(self, result: RESTHealthCheckResult) -> None:
        """
        Record metrics from a REST health check result.
        
        Args:
            result: The REST health check result to extract metrics from
        """
        with self._lock:
            self._ensure_metrics_exist(result.server_name)
            self._record_rest_metrics(result)
    
    def get_mcp_metrics(self, server_name: str) -> Optional[MCPMetrics]:
        """
        Get MCP metrics for a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            MCPMetrics object or None if not found
        """
        with self._lock:
            return self._mcp_metrics.get(server_name)
    
    def get_rest_metrics(self, server_name: str) -> Optional[RESTMetrics]:
        """
        Get REST metrics for a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            RESTMetrics object or None if not found
        """
        with self._lock:
            return self._rest_metrics.get(server_name)
    
    def get_combined_metrics(self, server_name: str) -> Optional[CombinedMetrics]:
        """
        Get combined metrics for a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            CombinedMetrics object or None if not found
        """
        with self._lock:
            return self._combined_metrics.get(server_name)
    
    def get_all_server_names(self) -> List[str]:
        """
        Get list of all servers being monitored.
        
        Returns:
            List of server names
        """
        with self._lock:
            # Combine all server names from different metric types
            all_servers = set()
            all_servers.update(self._mcp_metrics.keys())
            all_servers.update(self._rest_metrics.keys())
            all_servers.update(self._combined_metrics.keys())
            return sorted(list(all_servers))
    
    def generate_aggregation_report(
        self, 
        server_name: str, 
        time_window: TimeWindow = TimeWindow.LAST_HOUR
    ) -> Optional[MetricsAggregationReport]:
        """
        Generate an aggregated metrics report for a server.
        
        Args:
            server_name: Name of the server
            time_window: Time window for aggregation
            
        Returns:
            MetricsAggregationReport or None if server not found
        """
        with self._lock:
            mcp_metrics = self._mcp_metrics.get(server_name)
            rest_metrics = self._rest_metrics.get(server_name)
            combined_metrics = self._combined_metrics.get(server_name)
            
            if not any([mcp_metrics, rest_metrics, combined_metrics]):
                return None
            
            # Calculate MCP metrics
            mcp_success_rate = mcp_metrics.get_success_rate() if mcp_metrics else 0.0
            mcp_avg_response_time = mcp_metrics.get_average_response_time(time_window) if mcp_metrics else 0.0
            mcp_p95_response_time = mcp_metrics.get_response_time_percentile(95.0, time_window) if mcp_metrics else 0.0
            mcp_tools_availability = mcp_metrics.get_validation_success_rate() if mcp_metrics else 0.0
            
            # Calculate REST metrics
            rest_success_rate = rest_metrics.get_success_rate() if rest_metrics else 0.0
            rest_avg_response_time = rest_metrics.get_average_response_time(time_window) if rest_metrics else 0.0
            rest_p95_response_time = rest_metrics.get_response_time_percentile(95.0, time_window) if rest_metrics else 0.0
            rest_endpoint_availability = rest_metrics.get_health_endpoint_availability_rate() if rest_metrics else 0.0
            
            # Calculate combined metrics
            combined_success_rate = combined_metrics.get_combined_success_rate() if combined_metrics else 0.0
            combined_avg_response_time = combined_metrics.get_combined_average_response_time(time_window) if combined_metrics else 0.0
            overall_availability = combined_metrics.get_overall_availability_rate() if combined_metrics else 0.0
            
            # Get top HTTP status codes
            top_status_codes = rest_metrics.get_most_common_status_codes() if rest_metrics else []
            
            # Build error breakdown
            error_breakdown = {}
            if mcp_metrics:
                error_breakdown.update({
                    "mcp_connection_errors": mcp_metrics.connection_errors,
                    "mcp_timeout_errors": mcp_metrics.timeout_errors,
                    "mcp_protocol_errors": mcp_metrics.protocol_errors
                })
            
            if rest_metrics:
                error_breakdown.update({
                    "rest_connection_errors": rest_metrics.connection_errors,
                    "rest_timeout_errors": rest_metrics.timeout_errors,
                    "rest_http_errors": rest_metrics.http_errors
                })
            
            return MetricsAggregationReport(
                server_name=server_name,
                report_timestamp=datetime.now(),
                time_window=time_window,
                mcp_success_rate=mcp_success_rate,
                mcp_average_response_time=mcp_avg_response_time,
                mcp_p95_response_time=mcp_p95_response_time,
                mcp_tools_availability_rate=mcp_tools_availability,
                rest_success_rate=rest_success_rate,
                rest_average_response_time=rest_avg_response_time,
                rest_p95_response_time=rest_p95_response_time,
                rest_endpoint_availability_rate=rest_endpoint_availability,
                combined_success_rate=combined_success_rate,
                combined_average_response_time=combined_avg_response_time,
                overall_availability_rate=overall_availability,
                top_http_status_codes=top_status_codes,
                error_breakdown=error_breakdown
            )
    
    def generate_all_servers_report(
        self, 
        time_window: TimeWindow = TimeWindow.LAST_HOUR
    ) -> List[MetricsAggregationReport]:
        """
        Generate aggregation reports for all monitored servers.
        
        Args:
            time_window: Time window for aggregation
            
        Returns:
            List of MetricsAggregationReport objects
        """
        reports = []
        for server_name in self.get_all_server_names():
            report = self.generate_aggregation_report(server_name, time_window)
            if report:
                reports.append(report)
        return reports
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all collected metrics.
        
        Returns:
            Dictionary containing metrics summary
        """
        with self._lock:
            summary = {
                "total_servers_monitored": len(self.get_all_server_names()),
                "mcp_servers_count": len(self._mcp_metrics),
                "rest_servers_count": len(self._rest_metrics),
                "combined_servers_count": len(self._combined_metrics),
                "retention_period_days": self.retention_period.days,
                "collection_timestamp": datetime.now().isoformat()
            }
            
            # Add per-server summaries
            server_summaries = {}
            for server_name in self.get_all_server_names():
                mcp_metrics = self._mcp_metrics.get(server_name)
                rest_metrics = self._rest_metrics.get(server_name)
                
                server_summary = {
                    "mcp_enabled": mcp_metrics is not None,
                    "rest_enabled": rest_metrics is not None,
                    "mcp_total_requests": mcp_metrics.total_requests if mcp_metrics else 0,
                    "rest_total_requests": rest_metrics.total_requests if rest_metrics else 0,
                    "mcp_success_rate": mcp_metrics.get_success_rate() if mcp_metrics else 0.0,
                    "rest_success_rate": rest_metrics.get_success_rate() if rest_metrics else 0.0
                }
                server_summaries[server_name] = server_summary
            
            summary["servers"] = server_summaries
            return summary
    
    def cleanup_old_metrics(self) -> None:
        """Remove old metric data points beyond retention period."""
        with self._lock:
            cleanup_count = 0
            
            # Cleanup MCP metrics
            for metrics in self._mcp_metrics.values():
                metrics.response_times.cleanup_old_data(self.retention_period)
                metrics.tools_count_series.cleanup_old_data(self.retention_period)
                metrics.expected_tools_found_series.cleanup_old_data(self.retention_period)
                metrics.missing_tools_count_series.cleanup_old_data(self.retention_period)
                cleanup_count += 1
            
            # Cleanup REST metrics
            for metrics in self._rest_metrics.values():
                metrics.response_times.cleanup_old_data(self.retention_period)
                cleanup_count += 1
            
            # Cleanup combined metrics
            for metrics in self._combined_metrics.values():
                metrics.combined_response_times.cleanup_old_data(self.retention_period)
                cleanup_count += 1
            
            if cleanup_count > 0:
                self.logger.debug("Cleaned up old metrics for %d metric objects", cleanup_count)
    
    def reset_metrics(self, server_name: Optional[str] = None) -> None:
        """
        Reset metrics for a specific server or all servers.
        
        Args:
            server_name: Server to reset metrics for, or None for all servers
        """
        with self._lock:
            if server_name:
                # Reset specific server
                if server_name in self._mcp_metrics:
                    del self._mcp_metrics[server_name]
                if server_name in self._rest_metrics:
                    del self._rest_metrics[server_name]
                if server_name in self._combined_metrics:
                    del self._combined_metrics[server_name]
                self.logger.info("Reset metrics for server: %s", server_name)
            else:
                # Reset all servers
                self._mcp_metrics.clear()
                self._rest_metrics.clear()
                self._combined_metrics.clear()
                self.logger.info("Reset all metrics")
    
    def export_metrics_data(self) -> Dict[str, Any]:
        """
        Export all metrics data for persistence or analysis.
        
        Returns:
            Dictionary containing all metrics data
        """
        with self._lock:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "retention_period_days": self.retention_period.days,
                "mcp_metrics": {},
                "rest_metrics": {},
                "combined_metrics": {}
            }
            
            # Export MCP metrics
            for server_name, metrics in self._mcp_metrics.items():
                export_data["mcp_metrics"][server_name] = metrics.to_dict()
            
            # Export REST metrics
            for server_name, metrics in self._rest_metrics.items():
                export_data["rest_metrics"][server_name] = metrics.to_dict()
            
            # Export combined metrics
            for server_name, metrics in self._combined_metrics.items():
                export_data["combined_metrics"][server_name] = metrics.to_dict()
            
            return export_data
    
    def import_metrics_data(self, data: Dict[str, Any]) -> None:
        """
        Import metrics data from exported data.
        
        Args:
            data: Dictionary containing exported metrics data
        """
        with self._lock:
            # Import MCP metrics
            for server_name, metrics_data in data.get("mcp_metrics", {}).items():
                self._mcp_metrics[server_name] = MCPMetrics.from_dict(metrics_data)
            
            # Import REST metrics
            for server_name, metrics_data in data.get("rest_metrics", {}).items():
                self._rest_metrics[server_name] = RESTMetrics.from_dict(metrics_data)
            
            # Import combined metrics
            for server_name, metrics_data in data.get("combined_metrics", {}).items():
                mcp_metrics = self._mcp_metrics.get(server_name)
                rest_metrics = self._rest_metrics.get(server_name)
                
                if mcp_metrics and rest_metrics:
                    combined_metrics = CombinedMetrics(
                        server_name=server_name,
                        mcp_metrics=mcp_metrics,
                        rest_metrics=rest_metrics
                    )
                    # Load additional combined data
                    combined_data = metrics_data.get("combined_metrics", {})
                    if "combined_response_times" in combined_data:
                        combined_metrics.combined_response_times = MetricSeries.from_dict(
                            combined_data["combined_response_times"]
                        )
                    combined_metrics.overall_availability_count = combined_data.get("overall_availability_count", 0)
                    combined_metrics.overall_unavailability_count = combined_data.get("overall_unavailability_count", 0)
                    
                    self._combined_metrics[server_name] = combined_metrics
            
            self.logger.info("Imported metrics data for %d servers", len(data.get("mcp_metrics", {})))
    
    def _ensure_metrics_exist(self, server_name: str) -> None:
        """Ensure metrics objects exist for the given server."""
        if server_name not in self._mcp_metrics:
            self._mcp_metrics[server_name] = MCPMetrics(server_name=server_name)
        
        if server_name not in self._rest_metrics:
            self._rest_metrics[server_name] = RESTMetrics(server_name=server_name)
        
        if server_name not in self._combined_metrics:
            self._combined_metrics[server_name] = CombinedMetrics(
                server_name=server_name,
                mcp_metrics=self._mcp_metrics[server_name],
                rest_metrics=self._rest_metrics[server_name]
            )
    
    def _record_mcp_metrics(self, result: MCPHealthCheckResult) -> None:
        """Record metrics from MCP health check result."""
        self._ensure_metrics_exist(result.server_name)
        mcp_metrics = self._mcp_metrics[result.server_name]
        
        # Record response time
        mcp_metrics.record_response_time(result.response_time_ms)
        
        # Record success/failure
        if result.success:
            mcp_metrics.record_success()
        else:
            # Determine error type
            error_type = "general"
            if result.connection_error:
                error_type = "connection"
            elif "timeout" in str(result.mcp_error).lower():
                error_type = "timeout"
            elif result.mcp_error:
                error_type = "protocol"
            
            mcp_metrics.record_failure(error_type)
        
        # Record tool-specific metrics
        if result.tools_count is not None:
            mcp_metrics.record_tools_count(result.tools_count)
        
        if result.expected_tools_found:
            mcp_metrics.record_expected_tools_found(len(result.expected_tools_found))
        
        if result.missing_tools:
            mcp_metrics.record_missing_tools(len(result.missing_tools))
        
        # Record validation result
        if result.validation_result:
            mcp_metrics.record_validation_result(result.validation_result.is_valid)
    
    def _record_rest_metrics(self, result: RESTHealthCheckResult) -> None:
        """Record metrics from REST health check result."""
        self._ensure_metrics_exist(result.server_name)
        rest_metrics = self._rest_metrics[result.server_name]
        
        # Record response time
        rest_metrics.record_response_time(result.response_time_ms)
        
        # Record success/failure
        if result.success:
            rest_metrics.record_success()
        else:
            # Determine error type
            error_type = "general"
            if result.connection_error:
                error_type = "connection"
            elif "timeout" in str(result.http_error).lower():
                error_type = "timeout"
            elif result.http_error:
                error_type = "http"
            
            rest_metrics.record_failure(error_type)
        
        # Record HTTP status code
        if result.status_code:
            rest_metrics.record_status_code(result.status_code)
        
        # Record health endpoint availability
        rest_metrics.record_health_endpoint_availability(result.success)
        
        # Record response body validation
        if result.validation_result:
            rest_metrics.record_response_body_validation(result.validation_result.is_valid)
    
    def _record_combined_metrics(self, result: DualHealthCheckResult) -> None:
        """Record combined metrics from dual health check result."""
        self._ensure_metrics_exist(result.server_name)
        combined_metrics = self._combined_metrics[result.server_name]
        
        # Record combined response time if both are available
        if result.mcp_result and result.rest_result:
            combined_metrics.record_combined_response_time(
                result.mcp_result.response_time_ms,
                result.rest_result.response_time_ms
            )
        
        # Record overall availability
        is_available = result.overall_status in [ServerStatus.HEALTHY, ServerStatus.DEGRADED]
        combined_metrics.record_overall_availability(is_available)
    
    async def _cleanup_worker(self) -> None:
        """Background worker for periodic cleanup of old metrics."""
        self.logger.info("Started metrics cleanup worker")
        
        try:
            while not self._shutdown_event.is_set():
                # Wait for shutdown event or cleanup interval (1 hour)
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=3600.0)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    # Timeout reached, perform cleanup
                    pass
                
                # Perform cleanup
                try:
                    self.cleanup_old_metrics()
                except Exception as e:
                    self.logger.error("Error during metrics cleanup: %s", e)
        
        except asyncio.CancelledError:
            self.logger.info("Metrics cleanup worker cancelled")
        except Exception as e:
            self.logger.error("Unexpected error in metrics cleanup worker: %s", e)
        finally:
            self.logger.info("Metrics cleanup worker stopped")