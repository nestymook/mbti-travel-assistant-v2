"""
Health Check Service for MBTI Travel Planner Agent

This module provides comprehensive health checking capabilities for monitoring
gateway connectivity and service availability. It performs periodic health checks,
logs results, and provides health status information for monitoring dashboards.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading

import httpx

from .logging_service import get_logging_service, HealthCheckResult
from .gateway_http_client import GatewayHTTPClient, Environment
from .error_handler import ErrorHandler, ErrorContext, ErrorSeverity


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceEndpoint:
    """Configuration for a service endpoint to monitor."""
    name: str
    url: str
    timeout: float = 5.0
    expected_status_codes: List[int] = field(default_factory=lambda: [200])
    check_interval: int = 300  # 5 minutes
    failure_threshold: int = 3  # Number of consecutive failures before marking unhealthy
    degraded_threshold: float = 2.0  # Response time threshold for degraded status (seconds)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.check_interval <= 0:
            raise ValueError("Check interval must be positive")
        if self.failure_threshold <= 0:
            raise ValueError("Failure threshold must be positive")


@dataclass
class HealthCheckHistory:
    """History of health check results for a service."""
    service_name: str
    results: List[HealthCheckResult] = field(default_factory=list)
    consecutive_failures: int = 0
    last_healthy_time: Optional[datetime] = None
    last_check_time: Optional[datetime] = None
    
    def add_result(self, result: HealthCheckResult, max_history: int = 100) -> None:
        """Add a health check result to the history."""
        self.results.append(result)
        self.last_check_time = result.timestamp
        
        if result.status == HealthStatus.HEALTHY.value:
            self.consecutive_failures = 0
            self.last_healthy_time = result.timestamp
        else:
            self.consecutive_failures += 1
        
        # Limit history size
        if len(self.results) > max_history:
            self.results = self.results[-max_history:]
    
    def get_current_status(self, failure_threshold: int) -> HealthStatus:
        """Get the current health status based on recent results."""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        latest_result = self.results[-1]
        
        if self.consecutive_failures >= failure_threshold:
            return HealthStatus.UNHEALTHY
        elif latest_result.status == HealthStatus.DEGRADED.value:
            return HealthStatus.DEGRADED
        elif latest_result.status == HealthStatus.HEALTHY.value:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_availability_percentage(self, window_minutes: int = 60) -> float:
        """Calculate availability percentage for the specified time window."""
        if not self.results:
            return 0.0
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_results = [r for r in self.results if r.timestamp > cutoff_time]
        
        if not recent_results:
            return 0.0
        
        healthy_count = sum(1 for r in recent_results if r.status == HealthStatus.HEALTHY.value)
        return (healthy_count / len(recent_results)) * 100.0


class HealthCheckService:
    """
    Comprehensive health check service for monitoring gateway connectivity and service availability.
    
    Features:
    - Periodic health checks for configured endpoints
    - Health status tracking with history
    - Availability metrics and statistics
    - Integration with logging service
    - Configurable thresholds and intervals
    """
    
    def __init__(self, 
                 environment: str = "production",
                 check_interval: int = 300,
                 enable_background_checks: bool = True):
        """
        Initialize the health check service.
        
        Args:
            environment: Environment name for configuration
            check_interval: Default check interval in seconds
            enable_background_checks: Whether to run background health checks
        """
        self.environment = environment
        self.default_check_interval = check_interval
        self.enable_background_checks = enable_background_checks
        
        # Initialize services
        self.logging_service = get_logging_service()
        self.error_handler = ErrorHandler("health_check_service")
        self.logger = logging.getLogger(f"mbti_travel_planner.health_check")
        
        # Service endpoints to monitor
        self.endpoints: Dict[str, ServiceEndpoint] = {}
        self.health_history: Dict[str, HealthCheckHistory] = {}
        
        # Background check control
        self._background_task = None
        self._stop_background_checks = threading.Event()
        self._check_lock = threading.Lock()
        
        # Initialize default gateway endpoints
        self._initialize_default_endpoints()
        
        self.logger.info(f"Health check service initialized for {environment} environment")
    
    def _initialize_default_endpoints(self) -> None:
        """Initialize default gateway endpoints based on environment."""
        # Get gateway configuration
        gateway_endpoints = {
            "development": "http://localhost:8080",
            "staging": "https://agentcore-gateway-mcp-tools-staging.bedrock-agentcore.us-east-1.amazonaws.com",
            "production": "https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com"
        }
        
        base_url = gateway_endpoints.get(self.environment, gateway_endpoints["production"])
        
        # Add gateway health endpoint
        self.add_endpoint(ServiceEndpoint(
            name="gateway_health",
            url=f"{base_url}/health",
            timeout=10.0,
            check_interval=self.default_check_interval,
            failure_threshold=3,
            degraded_threshold=2.0
        ))
        
        # Add gateway metrics endpoint
        self.add_endpoint(ServiceEndpoint(
            name="gateway_metrics",
            url=f"{base_url}/metrics",
            timeout=15.0,
            check_interval=self.default_check_interval * 2,  # Check less frequently
            failure_threshold=5,  # More tolerant for metrics endpoint
            degraded_threshold=5.0
        ))
        
        # Add restaurant search endpoint
        self.add_endpoint(ServiceEndpoint(
            name="restaurant_search",
            url=f"{base_url}/api/v1/restaurants/search/district",
            timeout=20.0,
            check_interval=self.default_check_interval,
            failure_threshold=2,
            degraded_threshold=10.0,
            expected_status_codes=[200, 400, 422]  # 400/422 are valid for missing parameters
        ))
        
        # Add restaurant recommendation endpoint
        self.add_endpoint(ServiceEndpoint(
            name="restaurant_recommendation",
            url=f"{base_url}/api/v1/restaurants/recommend",
            timeout=30.0,
            check_interval=self.default_check_interval,
            failure_threshold=2,
            degraded_threshold=15.0,
            expected_status_codes=[200, 400, 422]  # 400/422 are valid for missing parameters
        ))
    
    def add_endpoint(self, endpoint: ServiceEndpoint) -> None:
        """
        Add a service endpoint to monitor.
        
        Args:
            endpoint: ServiceEndpoint configuration
        """
        self.endpoints[endpoint.name] = endpoint
        self.health_history[endpoint.name] = HealthCheckHistory(service_name=endpoint.name)
        self.logger.info(f"Added health check endpoint: {endpoint.name} -> {endpoint.url}")
    
    def remove_endpoint(self, service_name: str) -> None:
        """
        Remove a service endpoint from monitoring.
        
        Args:
            service_name: Name of the service to remove
        """
        if service_name in self.endpoints:
            del self.endpoints[service_name]
            del self.health_history[service_name]
            self.logger.info(f"Removed health check endpoint: {service_name}")
    
    async def check_endpoint_health(self, service_name: str) -> HealthCheckResult:
        """
        Perform a health check on a specific endpoint.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            HealthCheckResult with the check results
        """
        if service_name not in self.endpoints:
            raise ValueError(f"Unknown service: {service_name}")
        
        endpoint = self.endpoints[service_name]
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
                # For POST endpoints, send minimal valid request
                if "search" in endpoint.url or "recommend" in endpoint.url:
                    # Send a minimal request to test endpoint availability
                    response = await client.post(endpoint.url, json={})
                else:
                    # GET request for health/metrics endpoints
                    response = await client.get(endpoint.url)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Determine health status
                if response.status_code in endpoint.expected_status_codes:
                    if duration_ms > endpoint.degraded_threshold * 1000:
                        status = HealthStatus.DEGRADED.value
                        error_message = f"Slow response: {duration_ms:.2f}ms (threshold: {endpoint.degraded_threshold * 1000}ms)"
                    else:
                        status = HealthStatus.HEALTHY.value
                        error_message = None
                else:
                    status = HealthStatus.UNHEALTHY.value
                    error_message = f"Unexpected status code: {response.status_code}"
                
                # Try to parse response for additional info
                additional_info = {}
                try:
                    if response.headers.get("content-type", "").startswith("application/json"):
                        response_data = response.json()
                        if isinstance(response_data, dict):
                            additional_info = {
                                "response_keys": list(response_data.keys()),
                                "success": response_data.get("success"),
                                "error": response_data.get("error")
                            }
                except Exception:
                    pass
                
                additional_info.update({
                    "status_code": response.status_code,
                    "response_size": len(response.content) if response.content else 0,
                    "headers": dict(response.headers)
                })
                
                result = HealthCheckResult(
                    service_name=service_name,
                    endpoint=endpoint.url,
                    status=status,
                    response_time_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    error_message=error_message,
                    additional_info=additional_info
                )
                
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service_name=service_name,
                endpoint=endpoint.url,
                status=HealthStatus.UNHEALTHY.value,
                response_time_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error_message=f"Request timed out after {endpoint.timeout}s",
                additional_info={"error_type": "timeout", "timeout": endpoint.timeout}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service_name=service_name,
                endpoint=endpoint.url,
                status=HealthStatus.UNHEALTHY.value,
                response_time_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error_message=str(e),
                additional_info={"error_type": type(e).__name__}
            )
        
        # Update health history
        with self._check_lock:
            self.health_history[service_name].add_result(result)
        
        # Log the health check result
        self.logging_service.log_health_check(
            service_name=result.service_name,
            endpoint=result.endpoint,
            status=result.status,
            response_time_ms=result.response_time_ms,
            error_message=result.error_message,
            additional_info=result.additional_info
        )
        
        return result
    
    async def check_all_endpoints(self) -> Dict[str, HealthCheckResult]:
        """
        Perform health checks on all configured endpoints.
        
        Returns:
            Dictionary mapping service names to health check results
        """
        results = {}
        
        # Run health checks concurrently
        tasks = []
        for service_name in self.endpoints.keys():
            task = asyncio.create_task(self.check_endpoint_health(service_name))
            tasks.append((service_name, task))
        
        # Wait for all checks to complete
        for service_name, task in tasks:
            try:
                result = await task
                results[service_name] = result
            except Exception as e:
                self.logger.error(f"Health check failed for {service_name}: {e}")
                self.logging_service.log_error(
                    error=e,
                    operation=f"health_check_{service_name}",
                    context={"service_name": service_name}
                )
        
        return results
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get the current status of a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary with service status information
        """
        if service_name not in self.health_history:
            return {"status": HealthStatus.UNKNOWN.value, "error": "Service not found"}
        
        history = self.health_history[service_name]
        endpoint = self.endpoints[service_name]
        current_status = history.get_current_status(endpoint.failure_threshold)
        
        status_info = {
            "service_name": service_name,
            "status": current_status.value,
            "endpoint": endpoint.url,
            "last_check": history.last_check_time.isoformat() if history.last_check_time else None,
            "last_healthy": history.last_healthy_time.isoformat() if history.last_healthy_time else None,
            "consecutive_failures": history.consecutive_failures,
            "availability_1h": history.get_availability_percentage(60),
            "availability_24h": history.get_availability_percentage(1440),
            "check_count": len(history.results)
        }
        
        # Add latest result details
        if history.results:
            latest = history.results[-1]
            status_info.update({
                "latest_response_time_ms": latest.response_time_ms,
                "latest_error": latest.error_message,
                "latest_check_time": latest.timestamp.isoformat()
            })
        
        return status_info
    
    def get_overall_health_status(self) -> Dict[str, Any]:
        """
        Get the overall health status of all monitored services.
        
        Returns:
            Dictionary with overall health information
        """
        service_statuses = {}
        overall_status = HealthStatus.HEALTHY
        
        for service_name in self.endpoints.keys():
            service_status = self.get_service_status(service_name)
            service_statuses[service_name] = service_status
            
            # Determine overall status (worst case)
            if service_status["status"] == HealthStatus.UNHEALTHY.value:
                overall_status = HealthStatus.UNHEALTHY
            elif service_status["status"] == HealthStatus.DEGRADED.value and overall_status != HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        # Calculate summary statistics
        total_services = len(service_statuses)
        healthy_count = sum(1 for s in service_statuses.values() if s["status"] == HealthStatus.HEALTHY.value)
        degraded_count = sum(1 for s in service_statuses.values() if s["status"] == HealthStatus.DEGRADED.value)
        unhealthy_count = sum(1 for s in service_statuses.values() if s["status"] == HealthStatus.UNHEALTHY.value)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "environment": self.environment,
            "summary": {
                "total_services": total_services,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "availability_percentage": (healthy_count / total_services * 100) if total_services > 0 else 0
            },
            "services": service_statuses
        }
    
    def start_background_checks(self) -> None:
        """Start background health checks in a separate thread."""
        if not self.enable_background_checks:
            self.logger.info("Background health checks are disabled")
            return
        
        if self._background_task and self._background_task.is_alive():
            self.logger.warning("Background health checks are already running")
            return
        
        self._stop_background_checks.clear()
        self._background_task = threading.Thread(target=self._background_check_loop, daemon=True)
        self._background_task.start()
        
        self.logger.info("Started background health checks")
    
    def stop_background_checks(self) -> None:
        """Stop background health checks."""
        if self._background_task and self._background_task.is_alive():
            self._stop_background_checks.set()
            self._background_task.join(timeout=30)
            self.logger.info("Stopped background health checks")
    
    def _background_check_loop(self) -> None:
        """Background thread loop for periodic health checks."""
        self.logger.info("Background health check loop started")
        
        while not self._stop_background_checks.is_set():
            try:
                # Run health checks
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                results = loop.run_until_complete(self.check_all_endpoints())
                
                # Log summary
                healthy_count = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY.value)
                total_count = len(results)
                
                self.logger.info(f"Background health check completed: {healthy_count}/{total_count} services healthy")
                
                loop.close()
                
            except Exception as e:
                self.logger.error(f"Error in background health check: {e}")
                self.logging_service.log_error(
                    error=e,
                    operation="background_health_check",
                    context={"thread": "background"}
                )
            
            # Wait for next check interval
            self._stop_background_checks.wait(self.default_check_interval)
        
        self.logger.info("Background health check loop stopped")
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """
        Get health metrics for monitoring dashboards.
        
        Returns:
            Dictionary with health metrics
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "services": {}
        }
        
        for service_name, history in self.health_history.items():
            endpoint = self.endpoints[service_name]
            
            # Calculate response time statistics
            recent_results = [
                r for r in history.results 
                if r.timestamp > datetime.utcnow() - timedelta(hours=1)
            ]
            
            response_times = [r.response_time_ms for r in recent_results]
            
            service_metrics = {
                "status": history.get_current_status(endpoint.failure_threshold).value,
                "endpoint": endpoint.url,
                "check_count_1h": len(recent_results),
                "availability_1h": history.get_availability_percentage(60),
                "availability_24h": history.get_availability_percentage(1440),
                "consecutive_failures": history.consecutive_failures,
                "response_time_stats": {
                    "count": len(response_times),
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "avg": sum(response_times) / len(response_times) if response_times else 0
                }
            }
            
            metrics["services"][service_name] = service_metrics
        
        return metrics
    
    def shutdown(self) -> None:
        """Shutdown the health check service."""
        self.logger.info("Shutting down health check service")
        self.stop_background_checks()


# Global health check service instance
_health_check_service = None


def get_health_check_service() -> HealthCheckService:
    """Get the global health check service instance."""
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service


def initialize_health_check_service(**kwargs) -> HealthCheckService:
    """
    Initialize the global health check service with custom configuration.
    
    Args:
        **kwargs: Configuration parameters for HealthCheckService
        
    Returns:
        Initialized HealthCheckService instance
    """
    global _health_check_service
    _health_check_service = HealthCheckService(**kwargs)
    return _health_check_service


# Export main classes and functions
__all__ = [
    'HealthCheckService',
    'ServiceEndpoint',
    'HealthCheckHistory',
    'HealthStatus',
    'get_health_check_service',
    'initialize_health_check_service'
]