"""
Observability service for AgentCore Gateway MCP Tools.

This module provides comprehensive observability features including:
- Structured logging with user context and performance metrics
- CloudWatch metrics integration
- Security event logging
- Health monitoring for MCP servers
- Operational statistics collection
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json

from middleware.jwt_validator import UserContext
from services.mcp_client_manager import MCPClientManager, MCPServerHealth, MCPServerStatus


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class SecurityEventType(Enum):
    """Types of security events."""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass
class PerformanceMetrics:
    """Performance metrics for requests."""
    request_id: str
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    user_id: Optional[str] = None
    mcp_server_calls: int = 0
    mcp_server_duration_ms: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class SecurityEvent:
    """Security event data."""
    event_type: SecurityEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    endpoint: str
    details: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class OperationalStats:
    """Operational statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    auth_failures: int = 0
    avg_response_time_ms: float = 0.0
    mcp_server_calls: int = 0
    uptime_seconds: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)


class ObservabilityService:
    """Service for handling observability features."""
    
    def __init__(self, aws_region: str = "us-east-1", service_name: str = "agentcore-gateway-mcp-tools"):
        self.aws_region = aws_region
        self.service_name = service_name
        self.logger = structlog.get_logger(__name__)
        self.start_time = time.time()
        
        # Configuration
        self.max_history_size = 1000
        self.metrics_namespace = f"AgentCore/{service_name}"
        
        # Initialize CloudWatch client
        self.cloudwatch_client = None
        self._init_cloudwatch()
        
        # Operational statistics
        self.stats = OperationalStats()
        self.performance_history: List[PerformanceMetrics] = []
        self.security_events: List[SecurityEvent] = []
        
        self.logger.info(
            "Observability service initialized",
            service_name=service_name,
            aws_region=aws_region,
            cloudwatch_enabled=self.cloudwatch_client is not None
        )
    
    def _init_cloudwatch(self):
        """Initialize CloudWatch client."""
        try:
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
            # Test connection
            self.cloudwatch_client.list_metrics(Namespace=self.metrics_namespace, MaxRecords=1)
            self.logger.info("CloudWatch client initialized successfully")
        except (ClientError, NoCredentialsError) as e:
            self.logger.warning(
                "CloudWatch client initialization failed",
                error=str(e),
                fallback="metrics will be logged only"
            )
            self.cloudwatch_client = None
        except Exception as e:
            self.logger.error(
                "Unexpected error initializing CloudWatch client",
                error=str(e)
            )
            self.cloudwatch_client = None
    
    def log_request_start(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        user_context: Optional[UserContext] = None,
        ip_address: str = "unknown",
        user_agent: str = "unknown"
    ) -> float:
        """Log the start of a request and return start time."""
        start_time = time.time()
        
        log_data = {
            "event_type": "request_start",
            "request_id": request_id,
            "endpoint": endpoint,
            "method": method,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if user_context:
            log_data.update({
                "user_id": user_context.user_id,
                "username": user_context.username,
                "authenticated": True
            })
        else:
            log_data["authenticated"] = False
        
        self.logger.info("Request started", **log_data)
        return start_time
    
    def log_request_end(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        start_time: float,
        user_context: Optional[UserContext] = None,
        mcp_server_calls: int = 0,
        mcp_server_duration_ms: float = 0.0,
        error: Optional[str] = None
    ):
        """Log the end of a request and record performance metrics."""
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Create performance metrics
        metrics = PerformanceMetrics(
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_context.user_id if user_context else None,
            mcp_server_calls=mcp_server_calls,
            mcp_server_duration_ms=mcp_server_duration_ms
        )
        
        # Add to history
        self._add_performance_metrics(metrics)
        
        # Log request completion
        log_data = {
            "event_type": "request_end",
            "request_id": request_id,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "mcp_server_calls": mcp_server_calls,
            "mcp_server_duration_ms": mcp_server_duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if user_context:
            log_data.update({
                "user_id": user_context.user_id,
                "username": user_context.username
            })
        
        if error:
            log_data["error"] = error
            self.logger.error("Request completed with error", **log_data)
        else:
            self.logger.info("Request completed successfully", **log_data)
        
        # Send metrics to CloudWatch (if event loop is running)
        try:
            asyncio.create_task(self._send_performance_metrics(metrics))
        except RuntimeError:
            # No event loop running (e.g., in tests)
            pass
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
        endpoint: str,
        details: Dict[str, Any]
    ):
        """Log a security event."""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            details=details
        )
        
        # Add to security events history
        self._add_security_event(event)
        
        # Log the event
        log_data = {
            "log_type": "security_event",
            "security_event_type": event_type.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "endpoint": endpoint,
            "details": details,
            "timestamp": event.timestamp.isoformat()
        }
        
        if event_type in [SecurityEventType.AUTH_FAILURE, SecurityEventType.TOKEN_EXPIRED, 
                         SecurityEventType.TOKEN_INVALID, SecurityEventType.UNAUTHORIZED_ACCESS]:
            self.logger.warning("Security event detected", **log_data)
        else:
            self.logger.info("Security event logged", **log_data)
        
        # Send security metrics to CloudWatch (if event loop is running)
        try:
            asyncio.create_task(self._send_security_metrics(event))
        except RuntimeError:
            # No event loop running (e.g., in tests)
            pass
    
    def log_mcp_server_call(
        self,
        server_name: str,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Log an MCP server tool call."""
        log_data = {
            "log_type": "mcp_server_call",
            "server_name": server_name,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if error:
            log_data["error"] = error
            self.logger.error("MCP server call failed", **log_data)
        else:
            self.logger.info("MCP server call completed", **log_data)
        
        # Send MCP metrics to CloudWatch (if event loop is running)
        try:
            asyncio.create_task(self._send_mcp_metrics(server_name, tool_name, duration_ms, success))
        except RuntimeError:
            # No event loop running (e.g., in tests)
            pass
    
    async def get_health_status(self, mcp_client_manager: MCPClientManager) -> Dict[str, Any]:
        """Get comprehensive health status including MCP server connectivity."""
        try:
            # Get MCP server health
            server_status = mcp_client_manager.get_all_server_status()
            
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            
            # Determine overall health
            all_servers_healthy = all(
                health.status == MCPServerStatus.HEALTHY 
                for health in server_status.values()
            )
            
            overall_status = "healthy" if all_servers_healthy else "degraded"
            
            # Prepare MCP server status for JSON serialization
            mcp_servers = {}
            for server_name, health in server_status.items():
                mcp_servers[server_name] = {
                    "status": health.status.value,
                    "last_check": datetime.fromtimestamp(health.last_check, timezone.utc).isoformat() if health.last_check else None,
                    "error": health.error_message,
                    "response_time_ms": health.response_time
                }
            
            health_data = {
                "status": overall_status,
                "service": self.service_name,
                "version": "1.0.0",
                "uptime_seconds": uptime_seconds,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mcp_servers": mcp_servers,
                "observability": {
                    "cloudwatch_enabled": self.cloudwatch_client is not None,
                    "metrics_namespace": self.metrics_namespace,
                    "total_requests": self.stats.total_requests,
                    "performance_history_size": len(self.performance_history),
                    "security_events_count": len(self.security_events)
                }
            }
            
            self.logger.info("Health check completed", **health_data)
            return health_data
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            self.logger.error("Health check error", error=error_msg)
            
            return {
                "status": "unhealthy",
                "service": self.service_name,
                "version": "1.0.0",
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_operational_stats(self) -> Dict[str, Any]:
        """Get current operational statistics."""
        # Update stats
        self.stats.uptime_seconds = time.time() - self.start_time
        self.stats.last_updated = datetime.now(timezone.utc)
        
        # Calculate average response time from recent history
        if self.performance_history:
            recent_metrics = self.performance_history[-100:]  # Last 100 requests
            self.stats.avg_response_time_ms = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
        
        stats_dict = asdict(self.stats)
        stats_dict["last_updated"] = self.stats.last_updated.isoformat()
        
        # Add additional operational data
        stats_dict.update({
            "performance_history_size": len(self.performance_history),
            "security_events_count": len(self.security_events),
            "recent_security_events": len([
                e for e in self.security_events 
                if (datetime.now(timezone.utc) - e.timestamp).total_seconds() < 3600  # Last hour
            ]),
            "cloudwatch_enabled": self.cloudwatch_client is not None,
            "metrics_namespace": self.metrics_namespace
        })
        
        return stats_dict
    
    def _add_performance_metrics(self, metrics: PerformanceMetrics):
        """Add performance metrics to history."""
        self.performance_history.append(metrics)
        
        # Trim history if too large
        if len(self.performance_history) > self.max_history_size:
            self.performance_history = self.performance_history[-self.max_history_size:]
        
        # Update operational stats
        self.stats.total_requests += 1
        if 200 <= metrics.status_code < 400:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
        
        self.stats.mcp_server_calls += metrics.mcp_server_calls
    
    def _add_security_event(self, event: SecurityEvent):
        """Add security event to history."""
        self.security_events.append(event)
        
        # Trim history if too large
        if len(self.security_events) > self.max_history_size:
            self.security_events = self.security_events[-self.max_history_size:]
        
        # Update operational stats
        if event.event_type in [SecurityEventType.AUTH_FAILURE, SecurityEventType.TOKEN_EXPIRED,
                               SecurityEventType.TOKEN_INVALID, SecurityEventType.UNAUTHORIZED_ACCESS]:
            self.stats.auth_failures += 1
    
    async def _send_performance_metrics(self, metrics: PerformanceMetrics):
        """Send performance metrics to CloudWatch."""
        if not self.cloudwatch_client:
            return
        
        try:
            metric_data = [
                {
                    'MetricName': 'RequestDuration',
                    'Value': metrics.duration_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': metrics.endpoint},
                        {'Name': 'Method', 'Value': metrics.method},
                        {'Name': 'StatusCode', 'Value': str(metrics.status_code)}
                    ]
                },
                {
                    'MetricName': 'RequestCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': metrics.endpoint},
                        {'Name': 'Method', 'Value': metrics.method}
                    ]
                }
            ]
            
            if metrics.mcp_server_calls > 0:
                metric_data.append({
                    'MetricName': 'MCPServerCalls',
                    'Value': metrics.mcp_server_calls,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': metrics.endpoint}
                    ]
                })
                
                metric_data.append({
                    'MetricName': 'MCPServerDuration',
                    'Value': metrics.mcp_server_duration_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': metrics.endpoint}
                    ]
                })
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cloudwatch_client.put_metric_data(
                    Namespace=self.metrics_namespace,
                    MetricData=metric_data
                )
            )
            
        except Exception as e:
            self.logger.warning(
                "Failed to send performance metrics to CloudWatch",
                error=str(e),
                request_id=metrics.request_id
            )
    
    async def _send_security_metrics(self, event: SecurityEvent):
        """Send security metrics to CloudWatch."""
        if not self.cloudwatch_client:
            return
        
        try:
            metric_data = [
                {
                    'MetricName': 'SecurityEvents',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'EventType', 'Value': event.event_type.value},
                        {'Name': 'Endpoint', 'Value': event.endpoint}
                    ]
                }
            ]
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cloudwatch_client.put_metric_data(
                    Namespace=self.metrics_namespace,
                    MetricData=metric_data
                )
            )
            
        except Exception as e:
            self.logger.warning(
                "Failed to send security metrics to CloudWatch",
                error=str(e),
                event_type=event.event_type.value
            )
    
    async def _send_mcp_metrics(self, server_name: str, tool_name: str, duration_ms: float, success: bool):
        """Send MCP server metrics to CloudWatch."""
        if not self.cloudwatch_client:
            return
        
        try:
            metric_data = [
                {
                    'MetricName': 'MCPToolCalls',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'ServerName', 'Value': server_name},
                        {'Name': 'ToolName', 'Value': tool_name},
                        {'Name': 'Success', 'Value': str(success)}
                    ]
                },
                {
                    'MetricName': 'MCPToolDuration',
                    'Value': duration_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'ServerName', 'Value': server_name},
                        {'Name': 'ToolName', 'Value': tool_name}
                    ]
                }
            ]
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cloudwatch_client.put_metric_data(
                    Namespace=self.metrics_namespace,
                    MetricData=metric_data
                )
            )
            
        except Exception as e:
            self.logger.warning(
                "Failed to send MCP metrics to CloudWatch",
                error=str(e),
                server_name=server_name,
                tool_name=tool_name
            )


# Global observability service instance
_observability_service: Optional[ObservabilityService] = None


def get_observability_service() -> ObservabilityService:
    """Get the global observability service instance."""
    global _observability_service
    if _observability_service is None:
        from config.settings import get_settings
        settings = get_settings()
        _observability_service = ObservabilityService(
            aws_region=settings.app.aws_region,
            service_name=settings.app.otel_service_name
        )
    return _observability_service


def shutdown_observability_service():
    """Shutdown the observability service."""
    global _observability_service
    if _observability_service:
        _observability_service.logger.info("Observability service shutting down")
        _observability_service = None