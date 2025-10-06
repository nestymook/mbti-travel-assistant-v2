"""
AgentCore Monitoring Integration Service

This module provides a comprehensive monitoring integration service that ties together
all monitoring components and provides a unified interface for observability across
the MBTI Travel Planner Agent with AgentCore integration.

Features:
- Unified monitoring initialization and configuration
- Centralized health check orchestration
- Performance metrics aggregation and reporting
- Correlation ID management across all components
- Integration with existing logging infrastructure
- Monitoring dashboard data preparation
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Import all monitoring components
from .agentcore_monitoring_service import (
    AgentCoreMonitoringService,
    AgentCoreMetricsCollector,
    AgentOperationType,
    get_agentcore_monitoring_service,
    initialize_agentcore_monitoring_service
)

from .agentcore_monitoring_middleware import (
    AgentCoreMonitoringMiddleware,
    get_monitoring_middleware,
    initialize_monitoring_middleware
)

from .agentcore_health_check_service import (
    AgentCoreHealthCheckService,
    AgentHealthCheckConfig,
    AgentHealthStatus
)

# Import AgentCore components
from .agentcore_runtime_client import AgentCoreRuntimeClient
from .authentication_manager import AuthenticationManager
from config.agentcore_environment_config import EnvironmentConfig

logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfiguration:
    """Configuration for comprehensive monitoring integration."""
    environment: str
    enable_detailed_logging: bool = True
    enable_performance_tracking: bool = True
    enable_health_checks: bool = True
    enable_background_health_checks: bool = True
    health_check_interval_seconds: int = 300  # 5 minutes
    metrics_retention_hours: int = 24
    correlation_id_header: str = "X-Correlation-ID"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class MonitoringStatus:
    """Overall monitoring system status."""
    timestamp: datetime
    environment: str
    monitoring_service_status: str
    health_check_service_status: str
    middleware_status: str
    agent_health_summary: Dict[str, Any]
    performance_summary: Dict[str, Any]
    error_summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class AgentCoreMonitoringIntegration:
    """
    Comprehensive monitoring integration service for AgentCore operations.
    
    This service provides a unified interface for all monitoring capabilities,
    including structured logging, performance metrics, health checks, and
    correlation ID management across the entire MBTI Travel Planner Agent.
    """
    
    def __init__(self, 
                 config: EnvironmentConfig,
                 monitoring_config: Optional[MonitoringConfiguration] = None):
        """
        Initialize the comprehensive monitoring integration.
        
        Args:
            config: AgentCore environment configuration
            monitoring_config: Optional monitoring configuration
        """
        self.config = config
        self.monitoring_config = monitoring_config or MonitoringConfiguration(
            environment=config.environment
        )
        
        self.logger = logging.getLogger(f"{__name__}.integration")
        
        # Initialize monitoring components
        self.monitoring_service: Optional[AgentCoreMonitoringService] = None
        self.monitoring_middleware: Optional[AgentCoreMonitoringMiddleware] = None
        self.health_check_service: Optional[AgentCoreHealthCheckService] = None
        
        # Runtime components (will be set during initialization)
        self.runtime_client: Optional[AgentCoreRuntimeClient] = None
        self.auth_manager: Optional[AuthenticationManager] = None
        
        # Status tracking
        self._initialized = False
        self._background_tasks: List[asyncio.Task] = []
        
        self.logger.info(f"AgentCore monitoring integration created for {config.environment} environment")
    
    async def initialize(self, 
                        runtime_client: Optional[AgentCoreRuntimeClient] = None,
                        auth_manager: Optional[AuthenticationManager] = None) -> None:
        """
        Initialize all monitoring components.
        
        Args:
            runtime_client: Optional AgentCore runtime client
            auth_manager: Optional authentication manager
        """
        if self._initialized:
            self.logger.warning("Monitoring integration already initialized")
            return
        
        try:
            self.logger.info("Initializing comprehensive AgentCore monitoring integration...")
            
            # Store runtime components
            self.runtime_client = runtime_client
            self.auth_manager = auth_manager
            
            # Initialize monitoring service
            self.monitoring_service = initialize_agentcore_monitoring_service(
                environment=self.monitoring_config.environment,
                enable_detailed_logging=self.monitoring_config.enable_detailed_logging,
                enable_performance_tracking=self.monitoring_config.enable_performance_tracking,
                enable_health_checks=self.monitoring_config.enable_health_checks
            )
            
            # Initialize monitoring middleware
            self.monitoring_middleware = initialize_monitoring_middleware(
                monitoring_service=self.monitoring_service
            )
            
            # Initialize health check service if enabled
            if self.monitoring_config.enable_health_checks:
                self.health_check_service = AgentCoreHealthCheckService(
                    config=self.config,
                    runtime_client=runtime_client,
                    auth_manager=auth_manager,
                    monitoring_service=self.monitoring_service,
                    enable_background_checks=self.monitoring_config.enable_background_health_checks
                )
                
                # Start background health checks if enabled
                if self.monitoring_config.enable_background_health_checks:
                    self.health_check_service.start_background_checks()
            
            self._initialized = True
            
            # Log successful initialization
            self.monitoring_service.log_authentication_event(
                event_type="monitoring_initialization",
                success=True
            )
            
            self.logger.info("AgentCore monitoring integration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring integration: {e}")
            
            # Log initialization failure
            if self.monitoring_service:
                self.monitoring_service.log_authentication_event(
                    event_type="monitoring_initialization",
                    success=False,
                    error_message=str(e)
                )
            
            raise
    
    def is_initialized(self) -> bool:
        """Check if monitoring integration is initialized."""
        return self._initialized
    
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID for request tracing."""
        if not self._initialized or not self.monitoring_service:
            # Fallback correlation ID generation
            return f"fallback_{int(time.time() * 1000)}_{id(self) % 10000}"
        
        return self.monitoring_service.generate_correlation_id()
    
    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID from thread-local storage."""
        if not self._initialized or not self.monitoring_service:
            return None
        
        return self.monitoring_service.get_correlation_id()
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID in thread-local storage."""
        if self._initialized and self.monitoring_service:
            self.monitoring_service.set_correlation_id(correlation_id)
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of all monitored components.
        
        Returns:
            Dictionary with health check results
        """
        if not self._initialized:
            return {
                "status": "error",
                "message": "Monitoring integration not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        health_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.config.environment,
            "overall_status": "healthy",
            "components": {}
        }
        
        try:
            # Check monitoring service health
            health_results["components"]["monitoring_service"] = {
                "status": "healthy" if self.monitoring_service else "unhealthy",
                "details": "Monitoring service operational" if self.monitoring_service else "Monitoring service not available"
            }
            
            # Check middleware health
            health_results["components"]["monitoring_middleware"] = {
                "status": "healthy" if self.monitoring_middleware else "unhealthy",
                "details": "Monitoring middleware operational" if self.monitoring_middleware else "Monitoring middleware not available"
            }
            
            # Check health check service
            if self.health_check_service:
                agent_health = await self.health_check_service.check_all_agents()
                overall_agent_health = self.health_check_service.get_overall_health_status()
                
                health_results["components"]["health_check_service"] = {
                    "status": overall_agent_health["overall_status"],
                    "details": f"Monitoring {len(agent_health)} agents",
                    "agent_summary": overall_agent_health["summary"],
                    "individual_agents": {
                        arn: {
                            "status": result.status,
                            "response_time_ms": result.response_time_ms,
                            "last_check": result.timestamp.isoformat()
                        }
                        for arn, result in agent_health.items()
                    }
                }
                
                # Update overall status based on agent health
                if overall_agent_health["overall_status"] in ["unhealthy", "authentication_failed"]:
                    health_results["overall_status"] = "unhealthy"
                elif overall_agent_health["overall_status"] == "degraded":
                    health_results["overall_status"] = "degraded"
            else:
                health_results["components"]["health_check_service"] = {
                    "status": "disabled",
                    "details": "Health check service not enabled"
                }
            
            # Check authentication status
            if self.auth_manager:
                try:
                    await self.auth_manager.get_valid_token()
                    health_results["components"]["authentication"] = {
                        "status": "healthy",
                        "details": "Authentication manager operational with valid token"
                    }
                except Exception as e:
                    health_results["components"]["authentication"] = {
                        "status": "unhealthy",
                        "details": f"Authentication error: {str(e)}"
                    }
                    health_results["overall_status"] = "unhealthy"
            else:
                health_results["components"]["authentication"] = {
                    "status": "unknown",
                    "details": "Authentication manager not available"
                }
            
            # Check runtime client status
            if self.runtime_client:
                health_results["components"]["runtime_client"] = {
                    "status": "healthy",
                    "details": "AgentCore runtime client available"
                }
            else:
                health_results["components"]["runtime_client"] = {
                    "status": "unknown",
                    "details": "AgentCore runtime client not available"
                }
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive health check: {e}")
            health_results["overall_status"] = "error"
            health_results["error"] = str(e)
        
        return health_results
    
    def get_performance_metrics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for all monitored components.
        
        Args:
            window_minutes: Time window for metrics calculation
            
        Returns:
            Dictionary with performance metrics
        """
        if not self._initialized or not self.monitoring_service:
            return {
                "status": "error",
                "message": "Monitoring integration not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "environment": self.config.environment,
                "window_minutes": window_minutes,
                "agent_metrics": {},
                "operation_metrics": {},
                "authentication_metrics": {},
                "health_metrics": {}
            }
            
            # Get agent-specific metrics
            for agent_arn in [
                self.config.agentcore.restaurant_search_agent_arn,
                self.config.agentcore.restaurant_reasoning_agent_arn
            ]:
                if agent_arn:
                    agent_metrics = self.monitoring_service.metrics_collector.get_agent_metrics(
                        agent_arn, window_minutes
                    )
                    metrics["agent_metrics"][agent_arn] = agent_metrics
            
            # Get operation-specific metrics
            for operation in AgentOperationType:
                operation_metrics = self.monitoring_service.metrics_collector.get_operation_metrics(
                    operation.value, window_minutes
                )
                metrics["operation_metrics"][operation.value] = operation_metrics
            
            # Get authentication metrics
            metrics["authentication_metrics"] = self.monitoring_service.metrics_collector.get_authentication_metrics(
                window_minutes
            )
            
            # Get health metrics if available
            if self.health_check_service:
                metrics["health_metrics"] = self.health_check_service.get_health_metrics()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_monitoring_status(self) -> MonitoringStatus:
        """
        Get the overall status of the monitoring system.
        
        Returns:
            MonitoringStatus object with comprehensive status information
        """
        try:
            # Get performance summary
            performance_metrics = self.get_performance_metrics(60)  # Last hour
            performance_summary = {
                "total_operations": sum(
                    metrics.get("total_calls", 0) 
                    for metrics in performance_metrics.get("operation_metrics", {}).values()
                ),
                "overall_success_rate": 0,
                "avg_response_time_ms": 0
            }
            
            # Calculate overall success rate
            total_calls = 0
            successful_calls = 0
            total_response_time = 0
            response_count = 0
            
            for metrics in performance_metrics.get("operation_metrics", {}).values():
                calls = metrics.get("total_calls", 0)
                success = metrics.get("successful_calls", 0)
                response_stats = metrics.get("response_time_stats", {})
                
                total_calls += calls
                successful_calls += success
                
                if response_stats.get("count", 0) > 0:
                    total_response_time += response_stats.get("mean", 0) * response_stats.get("count", 0)
                    response_count += response_stats.get("count", 0)
            
            if total_calls > 0:
                performance_summary["overall_success_rate"] = (successful_calls / total_calls) * 100
            
            if response_count > 0:
                performance_summary["avg_response_time_ms"] = total_response_time / response_count
            
            # Get error summary
            error_summary = {
                "total_errors": total_calls - successful_calls,
                "error_rate": ((total_calls - successful_calls) / total_calls * 100) if total_calls > 0 else 0,
                "authentication_failures": performance_metrics.get("authentication_metrics", {}).get("failed_events", 0)
            }
            
            # Get agent health summary
            agent_health_summary = {}
            if self.health_check_service:
                overall_health = self.health_check_service.get_overall_health_status()
                agent_health_summary = overall_health.get("summary", {})
            
            return MonitoringStatus(
                timestamp=datetime.utcnow(),
                environment=self.config.environment,
                monitoring_service_status="healthy" if self.monitoring_service else "unhealthy",
                health_check_service_status="healthy" if self.health_check_service else "disabled",
                middleware_status="healthy" if self.monitoring_middleware else "unhealthy",
                agent_health_summary=agent_health_summary,
                performance_summary=performance_summary,
                error_summary=error_summary
            )
            
        except Exception as e:
            self.logger.error(f"Error getting monitoring status: {e}")
            return MonitoringStatus(
                timestamp=datetime.utcnow(),
                environment=self.config.environment,
                monitoring_service_status="error",
                health_check_service_status="error",
                middleware_status="error",
                agent_health_summary={"error": str(e)},
                performance_summary={"error": str(e)},
                error_summary={"error": str(e)}
            )
    
    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive monitoring report.
        
        Returns:
            Dictionary with complete monitoring report
        """
        try:
            report = {
                "report_timestamp": datetime.utcnow().isoformat(),
                "environment": self.config.environment,
                "monitoring_configuration": self.monitoring_config.to_dict(),
                "system_status": self.get_monitoring_status().to_dict(),
                "health_check_results": await self.perform_health_check(),
                "performance_metrics": {
                    "last_hour": self.get_performance_metrics(60),
                    "last_24_hours": self.get_performance_metrics(1440)
                }
            }
            
            # Add agent-specific details
            if self.health_check_service:
                report["agent_details"] = {}
                for agent_arn in self.health_check_service.agent_configs.keys():
                    agent_status = self.health_check_service.get_agent_status(agent_arn)
                    report["agent_details"][agent_arn] = agent_status
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating monitoring report: {e}")
            return {
                "report_timestamp": datetime.utcnow().isoformat(),
                "environment": self.config.environment,
                "status": "error",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close the monitoring integration and cleanup resources."""
        if not self._initialized:
            return
        
        try:
            self.logger.info("Shutting down AgentCore monitoring integration...")
            
            # Cancel background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Close health check service
            if self.health_check_service:
                await self.health_check_service.close()
            
            # Close runtime client if we own it
            if self.runtime_client:
                await self.runtime_client.close()
            
            self._initialized = False
            
            self.logger.info("AgentCore monitoring integration shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error during monitoring integration shutdown: {e}")


# Global monitoring integration instance
_monitoring_integration: Optional[AgentCoreMonitoringIntegration] = None


def get_monitoring_integration() -> Optional[AgentCoreMonitoringIntegration]:
    """Get the global monitoring integration instance."""
    return _monitoring_integration


def initialize_monitoring_integration(
    config: EnvironmentConfig,
    monitoring_config: Optional[MonitoringConfiguration] = None
) -> AgentCoreMonitoringIntegration:
    """
    Initialize the global monitoring integration.
    
    Args:
        config: AgentCore environment configuration
        monitoring_config: Optional monitoring configuration
        
    Returns:
        Initialized AgentCoreMonitoringIntegration instance
    """
    global _monitoring_integration
    _monitoring_integration = AgentCoreMonitoringIntegration(config, monitoring_config)
    return _monitoring_integration


# Export main classes and functions
__all__ = [
    'AgentCoreMonitoringIntegration',
    'MonitoringConfiguration',
    'MonitoringStatus',
    'get_monitoring_integration',
    'initialize_monitoring_integration'
]