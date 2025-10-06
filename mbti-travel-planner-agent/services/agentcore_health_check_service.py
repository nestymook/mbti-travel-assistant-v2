"""
AgentCore Health Check Service

This module provides specialized health checking capabilities for AgentCore agents,
including connectivity tests, authentication validation, and performance monitoring.

Features:
- Direct AgentCore agent health checks
- Authentication status monitoring
- Performance threshold monitoring
- Automated health check scheduling
- Integration with monitoring service
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

# Lazy import to avoid circular dependency
# from .agentcore_runtime_client import AgentCoreRuntimeClient, AgentResponse
from .authentication_manager import AuthenticationManager
from .agentcore_monitoring_service import (
    AgentCoreMonitoringService,
    AgentHealthCheckResult,
    AgentOperationType,
    get_agentcore_monitoring_service
)
from .agentcore_error_handler import AgentCoreError, AuthenticationError, AgentTimeoutError
from config.agentcore_environment_config import EnvironmentConfig

logger = logging.getLogger(__name__)


class AgentHealthStatus(Enum):
    """Health status levels for AgentCore agents."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    AUTHENTICATION_FAILED = "authentication_failed"


@dataclass
class AgentHealthCheckConfig:
    """Configuration for agent health checks."""
    agent_arn: str
    agent_name: str
    test_inputs: List[str] = field(default_factory=lambda: ["health check", "test"])
    timeout_seconds: float = 30.0
    healthy_threshold_ms: float = 5000.0  # 5 seconds
    degraded_threshold_ms: float = 15000.0  # 15 seconds
    check_interval_seconds: int = 300  # 5 minutes
    failure_threshold: int = 3  # Consecutive failures before marking unhealthy
    enable_authentication_check: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if self.healthy_threshold_ms >= self.degraded_threshold_ms:
            raise ValueError("Healthy threshold must be less than degraded threshold")
        if self.check_interval_seconds <= 0:
            raise ValueError("Check interval must be positive")


@dataclass
class AgentHealthHistory:
    """History of health check results for an agent."""
    agent_arn: str
    agent_name: str
    results: List[AgentHealthCheckResult] = field(default_factory=list)
    consecutive_failures: int = 0
    last_healthy_time: Optional[datetime] = None
    last_check_time: Optional[datetime] = None
    authentication_failures: int = 0
    
    def add_result(self, result: AgentHealthCheckResult, max_history: int = 100) -> None:
        """Add a health check result to the history."""
        self.results.append(result)
        self.last_check_time = result.timestamp
        
        if result.status == AgentHealthStatus.HEALTHY.value:
            self.consecutive_failures = 0
            self.last_healthy_time = result.timestamp
        else:
            self.consecutive_failures += 1
        
        # Track authentication failures
        if result.authentication_status in ["invalid", "expired"]:
            self.authentication_failures += 1
        elif result.authentication_status == "valid":
            self.authentication_failures = 0  # Reset on successful auth
        
        # Limit history size
        if len(self.results) > max_history:
            self.results = self.results[-max_history:]
    
    def get_current_status(self, failure_threshold: int) -> AgentHealthStatus:
        """Get the current health status based on recent results."""
        if not self.results:
            return AgentHealthStatus.UNKNOWN
        
        latest_result = self.results[-1]
        
        # Check for authentication failures
        if latest_result.authentication_status in ["invalid", "expired"]:
            return AgentHealthStatus.AUTHENTICATION_FAILED
        
        # Check for consecutive failures
        if self.consecutive_failures >= failure_threshold:
            return AgentHealthStatus.UNHEALTHY
        
        # Return the latest status
        try:
            return AgentHealthStatus(latest_result.status)
        except ValueError:
            return AgentHealthStatus.UNKNOWN
    
    def get_availability_percentage(self, window_minutes: int = 60) -> float:
        """Calculate availability percentage for the specified time window."""
        if not self.results:
            return 0.0
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_results = [r for r in self.results if r.timestamp > cutoff_time]
        
        if not recent_results:
            return 0.0
        
        healthy_count = sum(1 for r in recent_results if r.status == AgentHealthStatus.HEALTHY.value)
        return (healthy_count / len(recent_results)) * 100.0
    
    def get_average_response_time(self, window_minutes: int = 60) -> float:
        """Get average response time for the specified time window."""
        if not self.results:
            return 0.0
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_results = [r for r in self.results if r.timestamp > cutoff_time]
        
        if not recent_results:
            return 0.0
        
        total_time = sum(r.response_time_ms for r in recent_results)
        return total_time / len(recent_results)


class AgentCoreHealthCheckService:
    """
    Specialized health check service for AgentCore agents.
    
    Features:
    - Direct agent connectivity testing
    - Authentication status monitoring
    - Performance threshold monitoring
    - Automated background health checks
    - Integration with monitoring service
    """
    
    def __init__(self,
                 config: EnvironmentConfig,
                 runtime_client: Optional[AgentCoreRuntimeClient] = None,
                 auth_manager: Optional[AuthenticationManager] = None,
                 monitoring_service: Optional[AgentCoreMonitoringService] = None,
                 enable_background_checks: bool = True):
        """
        Initialize the AgentCore health check service.
        
        Args:
            config: AgentCore environment configuration
            runtime_client: Optional runtime client (will create if not provided)
            auth_manager: Optional authentication manager (will create if not provided)
            monitoring_service: Optional monitoring service
            enable_background_checks: Whether to run background health checks
        """
        self.config = config
        self.runtime_client = runtime_client
        self.auth_manager = auth_manager
        self.monitoring_service = monitoring_service or get_agentcore_monitoring_service()
        self.enable_background_checks = enable_background_checks
        
        self.logger = logging.getLogger(f"{__name__}.health_check")
        
        # Health check configurations
        self.agent_configs: Dict[str, AgentHealthCheckConfig] = {}
        self.health_history: Dict[str, AgentHealthHistory] = {}
        
        # Background check control
        self._background_task = None
        self._stop_background_checks = threading.Event()
        self._check_lock = threading.Lock()
        
        # Initialize default agent configurations
        self._initialize_agent_configs()
        
        self.logger.info(f"AgentCore health check service initialized for {config.environment} environment")
    
    def _initialize_agent_configs(self) -> None:
        """Initialize health check configurations for known agents."""
        # Restaurant search agent
        if self.config.agentcore.restaurant_search_agent_arn:
            self.add_agent_config(AgentHealthCheckConfig(
                agent_arn=self.config.agentcore.restaurant_search_agent_arn,
                agent_name="restaurant_search",
                test_inputs=[
                    "Find restaurants in Central district",
                    "Search for restaurants",
                    "health check"
                ],
                timeout_seconds=30.0,
                healthy_threshold_ms=10000.0,  # 10 seconds for search operations
                degraded_threshold_ms=20000.0,  # 20 seconds
                check_interval_seconds=300,
                failure_threshold=2
            ))
        
        # Restaurant reasoning agent
        if self.config.agentcore.restaurant_reasoning_agent_arn:
            self.add_agent_config(AgentHealthCheckConfig(
                agent_arn=self.config.agentcore.restaurant_reasoning_agent_arn,
                agent_name="restaurant_reasoning",
                test_inputs=[
                    "Recommend restaurants for ENFP personality",
                    "Analyze restaurant preferences",
                    "health check"
                ],
                timeout_seconds=45.0,  # Reasoning takes longer
                healthy_threshold_ms=15000.0,  # 15 seconds for reasoning operations
                degraded_threshold_ms=30000.0,  # 30 seconds
                check_interval_seconds=300,
                failure_threshold=2
            ))
    
    def add_agent_config(self, config: AgentHealthCheckConfig) -> None:
        """
        Add an agent health check configuration.
        
        Args:
            config: AgentHealthCheckConfig for the agent
        """
        self.agent_configs[config.agent_arn] = config
        self.health_history[config.agent_arn] = AgentHealthHistory(
            agent_arn=config.agent_arn,
            agent_name=config.agent_name
        )
        self.logger.info(f"Added health check config for agent: {config.agent_name}")
    
    def remove_agent_config(self, agent_arn: str) -> None:
        """
        Remove an agent health check configuration.
        
        Args:
            agent_arn: ARN of the agent to remove
        """
        if agent_arn in self.agent_configs:
            agent_name = self.agent_configs[agent_arn].agent_name
            del self.agent_configs[agent_arn]
            del self.health_history[agent_arn]
            self.logger.info(f"Removed health check config for agent: {agent_name}")
    
    async def check_agent_health(self, agent_arn: str) -> AgentHealthCheckResult:
        """
        Perform a health check on a specific AgentCore agent.
        
        Args:
            agent_arn: ARN of the agent to check
            
        Returns:
            AgentHealthCheckResult with the check results
        """
        if agent_arn not in self.agent_configs:
            raise ValueError(f"No health check configuration for agent: {agent_arn}")
        
        config = self.agent_configs[agent_arn]
        start_time = time.time()
        
        # Ensure we have a runtime client
        if not self.runtime_client:
            self.runtime_client = AgentCoreRuntimeClient(
                region=self.config.agentcore.region,
                connection_config=self.config.get_connection_config()
            )
        
        # Test authentication first if enabled
        auth_status = "unknown"
        if config.enable_authentication_check and self.auth_manager:
            try:
                await self.auth_manager.get_valid_token()
                auth_status = "valid"
            except AuthenticationError as e:
                if "expired" in str(e).lower():
                    auth_status = "expired"
                else:
                    auth_status = "invalid"
                
                # Log authentication failure
                self.monitoring_service.log_authentication_event(
                    event_type="health_check_auth",
                    success=False,
                    error_message=str(e)
                )
            except Exception as e:
                auth_status = "invalid"
                self.logger.warning(f"Authentication check failed for {config.agent_name}: {e}")
        
        # Perform agent invocation test
        test_input = config.test_inputs[0] if config.test_inputs else "health check"
        
        try:
            # Use monitoring service to perform the health check
            result = await self.monitoring_service.perform_agent_health_check(
                agent_arn=agent_arn,
                agent_name=config.agent_name,
                runtime_client=self.runtime_client,
                test_input=test_input
            )
            
            # Override authentication status if we checked it
            if config.enable_authentication_check:
                result.authentication_status = auth_status
            
            # Adjust status based on authentication
            if auth_status in ["invalid", "expired"]:
                result.status = AgentHealthStatus.AUTHENTICATION_FAILED.value
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            # Create error result
            result = AgentHealthCheckResult(
                agent_arn=agent_arn,
                agent_name=config.agent_name,
                status=AgentHealthStatus.UNHEALTHY.value,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                test_input=test_input,
                test_output=None,
                error_message=str(e),
                authentication_status=auth_status
            )
            
            self.logger.error(f"Health check failed for {config.agent_name}: {e}")
        
        # Update health history
        with self._check_lock:
            self.health_history[agent_arn].add_result(result)
        
        return result
    
    async def check_all_agents(self) -> Dict[str, AgentHealthCheckResult]:
        """
        Perform health checks on all configured agents.
        
        Returns:
            Dictionary mapping agent ARNs to health check results
        """
        results = {}
        
        # Run health checks concurrently
        tasks = []
        for agent_arn in self.agent_configs.keys():
            task = asyncio.create_task(self.check_agent_health(agent_arn))
            tasks.append((agent_arn, task))
        
        # Wait for all checks to complete
        for agent_arn, task in tasks:
            try:
                result = await task
                results[agent_arn] = result
            except Exception as e:
                config = self.agent_configs[agent_arn]
                self.logger.error(f"Health check failed for {config.agent_name}: {e}")
                
                # Create error result
                results[agent_arn] = AgentHealthCheckResult(
                    agent_arn=agent_arn,
                    agent_name=config.agent_name,
                    status=AgentHealthStatus.UNHEALTHY.value,
                    response_time_ms=0,
                    timestamp=datetime.utcnow(),
                    test_input="health check",
                    test_output=None,
                    error_message=str(e),
                    authentication_status="unknown"
                )
        
        return results
    
    def get_agent_status(self, agent_arn: str) -> Dict[str, Any]:
        """
        Get the current status of a specific agent.
        
        Args:
            agent_arn: ARN of the agent
            
        Returns:
            Dictionary with agent status information
        """
        if agent_arn not in self.health_history:
            return {"status": AgentHealthStatus.UNKNOWN.value, "error": "Agent not found"}
        
        history = self.health_history[agent_arn]
        config = self.agent_configs[agent_arn]
        current_status = history.get_current_status(config.failure_threshold)
        
        status_info = {
            "agent_arn": agent_arn,
            "agent_name": config.agent_name,
            "status": current_status.value,
            "last_check": history.last_check_time.isoformat() if history.last_check_time else None,
            "last_healthy": history.last_healthy_time.isoformat() if history.last_healthy_time else None,
            "consecutive_failures": history.consecutive_failures,
            "authentication_failures": history.authentication_failures,
            "availability_1h": history.get_availability_percentage(60),
            "availability_24h": history.get_availability_percentage(1440),
            "avg_response_time_1h": history.get_average_response_time(60),
            "check_count": len(history.results),
            "config": {
                "check_interval": config.check_interval_seconds,
                "failure_threshold": config.failure_threshold,
                "healthy_threshold_ms": config.healthy_threshold_ms,
                "degraded_threshold_ms": config.degraded_threshold_ms
            }
        }
        
        # Add latest result details
        if history.results:
            latest = history.results[-1]
            status_info.update({
                "latest_response_time_ms": latest.response_time_ms,
                "latest_error": latest.error_message,
                "latest_check_time": latest.timestamp.isoformat(),
                "latest_authentication_status": latest.authentication_status
            })
        
        return status_info
    
    def get_overall_health_status(self) -> Dict[str, Any]:
        """
        Get the overall health status of all monitored agents.
        
        Returns:
            Dictionary with overall health information
        """
        agent_statuses = {}
        overall_status = AgentHealthStatus.HEALTHY
        
        for agent_arn in self.agent_configs.keys():
            agent_status = self.get_agent_status(agent_arn)
            agent_statuses[agent_arn] = agent_status
            
            # Determine overall status (worst case)
            agent_health = AgentHealthStatus(agent_status["status"])
            if agent_health == AgentHealthStatus.UNHEALTHY or agent_health == AgentHealthStatus.AUTHENTICATION_FAILED:
                overall_status = AgentHealthStatus.UNHEALTHY
            elif agent_health == AgentHealthStatus.DEGRADED and overall_status == AgentHealthStatus.HEALTHY:
                overall_status = AgentHealthStatus.DEGRADED
        
        # Calculate summary statistics
        total_agents = len(agent_statuses)
        healthy_count = sum(1 for s in agent_statuses.values() if s["status"] == AgentHealthStatus.HEALTHY.value)
        degraded_count = sum(1 for s in agent_statuses.values() if s["status"] == AgentHealthStatus.DEGRADED.value)
        unhealthy_count = sum(1 for s in agent_statuses.values() if s["status"] in [AgentHealthStatus.UNHEALTHY.value, AgentHealthStatus.AUTHENTICATION_FAILED.value])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "environment": self.config.environment,
            "summary": {
                "total_agents": total_agents,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "availability_percentage": (healthy_count / total_agents * 100) if total_agents > 0 else 0
            },
            "agents": agent_statuses
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
        
        self.logger.info("Started background AgentCore health checks")
    
    def stop_background_checks(self) -> None:
        """Stop background health checks."""
        if self._background_task and self._background_task.is_alive():
            self._stop_background_checks.set()
            self._background_task.join(timeout=30)
            self.logger.info("Stopped background AgentCore health checks")
    
    def _background_check_loop(self) -> None:
        """Background thread loop for periodic health checks."""
        self.logger.info("Background AgentCore health check loop started")
        
        while not self._stop_background_checks.is_set():
            try:
                # Run health checks
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                results = loop.run_until_complete(self.check_all_agents())
                
                # Log summary
                healthy_count = sum(1 for r in results.values() if r.status == AgentHealthStatus.HEALTHY.value)
                total_count = len(results)
                
                self.logger.info(f"Background AgentCore health check completed: {healthy_count}/{total_count} agents healthy")
                
                loop.close()
                
            except Exception as e:
                self.logger.error(f"Error in background AgentCore health check: {e}")
            
            # Wait for next check interval (use minimum interval from all configs)
            min_interval = min(
                (config.check_interval_seconds for config in self.agent_configs.values()),
                default=300
            )
            self._stop_background_checks.wait(min_interval)
        
        self.logger.info("Background AgentCore health check loop stopped")
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """
        Get health metrics for monitoring dashboards.
        
        Returns:
            Dictionary with health metrics
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.config.environment,
            "agents": {}
        }
        
        for agent_arn, history in self.health_history.items():
            config = self.agent_configs[agent_arn]
            
            # Calculate response time statistics
            recent_results = [
                r for r in history.results 
                if r.timestamp > datetime.utcnow() - timedelta(hours=1)
            ]
            
            response_times = [r.response_time_ms for r in recent_results]
            
            agent_metrics = {
                "agent_name": config.agent_name,
                "status": history.get_current_status(config.failure_threshold).value,
                "check_count_1h": len(recent_results),
                "availability_1h": history.get_availability_percentage(60),
                "availability_24h": history.get_availability_percentage(1440),
                "consecutive_failures": history.consecutive_failures,
                "authentication_failures": history.authentication_failures,
                "response_time_stats": {
                    "count": len(response_times),
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "avg": sum(response_times) / len(response_times) if response_times else 0
                },
                "thresholds": {
                    "healthy_ms": config.healthy_threshold_ms,
                    "degraded_ms": config.degraded_threshold_ms,
                    "timeout_ms": config.timeout_seconds * 1000
                }
            }
            
            metrics["agents"][agent_arn] = agent_metrics
        
        return metrics
    
    async def close(self) -> None:
        """Close the health check service and cleanup resources."""
        self.logger.info("Shutting down AgentCore health check service")
        self.stop_background_checks()
        
        if self.runtime_client:
            await self.runtime_client.close()


# Export main classes and functions
__all__ = [
    'AgentCoreHealthCheckService',
    'AgentHealthCheckConfig',
    'AgentHealthHistory',
    'AgentHealthStatus'
]