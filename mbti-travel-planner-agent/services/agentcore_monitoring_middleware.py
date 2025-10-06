"""
AgentCore Monitoring Middleware

This module provides decorators and context managers for automatically
integrating monitoring and observability into AgentCore operations.

Features:
- Automatic invocation logging with decorators
- Context managers for correlation ID management
- Performance tracking integration
- Error handling and reporting
- Health check automation
"""

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Dict, Any, Optional, Callable, Union, AsyncIterator
from dataclasses import dataclass

from .agentcore_monitoring_service import (
    AgentCoreMonitoringService,
    AgentOperationType,
    get_agentcore_monitoring_service
)
# Lazy import to avoid circular dependency
# from .agentcore_runtime_client import AgentCoreRuntimeClient, AgentResponse
from .agentcore_error_handler import AgentCoreError

logger = logging.getLogger(__name__)


@dataclass
class MonitoringContext:
    """Context information for monitoring operations."""
    correlation_id: str
    operation_type: AgentOperationType
    agent_arn: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    start_time: Optional[float] = None


class AgentCoreMonitoringMiddleware:
    """Middleware for automatic monitoring of AgentCore operations."""
    
    def __init__(self, monitoring_service: Optional[AgentCoreMonitoringService] = None):
        """
        Initialize monitoring middleware.
        
        Args:
            monitoring_service: Optional monitoring service instance
        """
        self.monitoring_service = monitoring_service or get_agentcore_monitoring_service()
        self.logger = logging.getLogger(f"{__name__}.middleware")
    
    def monitor_agent_invocation(self,
                                operation_type: AgentOperationType,
                                agent_arn: str,
                                include_input: bool = True,
                                include_output: bool = True):
        """
        Decorator for monitoring AgentCore agent invocations.
        
        Args:
            operation_type: Type of operation being monitored
            agent_arn: ARN of the target agent
            include_input: Whether to log input data
            include_output: Whether to log output data
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self._monitor_async_invocation(
                        func, operation_type, agent_arn, include_input, include_output,
                        *args, **kwargs
                    )
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    return self._monitor_sync_invocation(
                        func, operation_type, agent_arn, include_input, include_output,
                        *args, **kwargs
                    )
                return sync_wrapper
        return decorator
    
    async def _monitor_async_invocation(self,
                                       func: Callable,
                                       operation_type: AgentOperationType,
                                       agent_arn: str,
                                       include_input: bool,
                                       include_output: bool,
                                       *args, **kwargs) -> Any:
        """Monitor an async agent invocation."""
        # Extract monitoring parameters from kwargs
        user_id = kwargs.get('user_id')
        session_id = kwargs.get('session_id')
        request_id = kwargs.get('request_id')
        correlation_id = kwargs.get('correlation_id')
        
        # Extract input text for logging
        input_text = ""
        if include_input:
            if args and isinstance(args[0], str):
                input_text = args[0]
            elif 'input_text' in kwargs:
                input_text = kwargs['input_text']
            elif 'query' in kwargs:
                input_text = str(kwargs['query'])
        
        # Start monitoring
        correlation_id = self.monitoring_service.log_agent_invocation_start(
            agent_arn=agent_arn,
            operation_type=operation_type,
            input_text=input_text,
            session_id=session_id,
            user_id=user_id,
            request_id=request_id,
            correlation_id=correlation_id
        )
        
        # Add correlation ID to kwargs for downstream use
        kwargs['correlation_id'] = correlation_id
        
        start_time = time.time()
        response = None
        error = None
        retry_count = 0
        circuit_breaker_triggered = False
        
        try:
            # Execute the function
            response = await func(*args, **kwargs)
            
            # Extract retry information if available
            if hasattr(response, 'metadata') and isinstance(response.metadata, dict):
                retry_count = response.metadata.get('retry_count', 0)
                circuit_breaker_triggered = response.metadata.get('circuit_breaker_triggered', False)
            
            return response
            
        except Exception as e:
            error = e
            
            # Extract retry information from error if available
            if isinstance(e, AgentCoreError):
                retry_count = getattr(e, 'retry_count', 0)
                circuit_breaker_triggered = getattr(e, 'circuit_breaker_triggered', False)
            
            raise
            
        finally:
            # Log the result
            self.monitoring_service.log_agent_invocation_result(
                correlation_id=correlation_id,
                agent_arn=agent_arn,
                operation_type=operation_type,
                response=response,
                error=error,
                retry_count=retry_count,
                circuit_breaker_triggered=circuit_breaker_triggered
            )
    
    def _monitor_sync_invocation(self,
                                func: Callable,
                                operation_type: AgentOperationType,
                                agent_arn: str,
                                include_input: bool,
                                include_output: bool,
                                *args, **kwargs) -> Any:
        """Monitor a sync agent invocation."""
        # For sync functions, we'll use a simpler approach
        # Most AgentCore operations should be async, but this provides fallback
        
        correlation_id = self.monitoring_service.generate_correlation_id()
        
        try:
            result = func(*args, **kwargs)
            
            # Log basic success
            self.logger.info(
                f"Sync operation completed: {operation_type.value}",
                extra={
                    "correlation_id": correlation_id,
                    "operation_type": operation_type.value,
                    "agent_arn": agent_arn,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            # Log basic error
            self.logger.error(
                f"Sync operation failed: {operation_type.value}",
                extra={
                    "correlation_id": correlation_id,
                    "operation_type": operation_type.value,
                    "agent_arn": agent_arn,
                    "success": False,
                    "error": str(e)
                }
            )
            
            raise
    
    @asynccontextmanager
    async def monitoring_context(self,
                                operation_type: AgentOperationType,
                                agent_arn: str,
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None,
                                request_id: Optional[str] = None,
                                correlation_id: Optional[str] = None) -> AsyncIterator[MonitoringContext]:
        """
        Async context manager for monitoring AgentCore operations.
        
        Args:
            operation_type: Type of operation
            agent_arn: ARN of the target agent
            user_id: Optional user ID
            session_id: Optional session ID
            request_id: Optional request ID
            correlation_id: Optional correlation ID
            
        Yields:
            MonitoringContext with correlation ID and operation details
        """
        if not correlation_id:
            correlation_id = self.monitoring_service.generate_correlation_id()
        else:
            self.monitoring_service.set_correlation_id(correlation_id)
        
        context = MonitoringContext(
            correlation_id=correlation_id,
            operation_type=operation_type,
            agent_arn=agent_arn,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            start_time=time.time()
        )
        
        self.logger.info(
            f"Starting monitored operation: {operation_type.value}",
            extra={
                "correlation_id": correlation_id,
                "operation_type": operation_type.value,
                "agent_arn": agent_arn,
                "user_id": user_id,
                "session_id": session_id,
                "request_id": request_id
            }
        )
        
        try:
            yield context
            
            # Log successful completion
            duration_ms = (time.time() - context.start_time) * 1000
            self.logger.info(
                f"Completed monitored operation: {operation_type.value}",
                extra={
                    "correlation_id": correlation_id,
                    "operation_type": operation_type.value,
                    "agent_arn": agent_arn,
                    "duration_ms": duration_ms,
                    "success": True
                }
            )
            
        except Exception as e:
            # Log error
            duration_ms = (time.time() - context.start_time) * 1000
            self.logger.error(
                f"Failed monitored operation: {operation_type.value}",
                extra={
                    "correlation_id": correlation_id,
                    "operation_type": operation_type.value,
                    "agent_arn": agent_arn,
                    "duration_ms": duration_ms,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            raise
    
    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None):
        """
        Context manager for correlation ID management.
        
        Args:
            correlation_id: Optional correlation ID (will generate if not provided)
            
        Yields:
            Correlation ID for the context
        """
        if not correlation_id:
            correlation_id = self.monitoring_service.generate_correlation_id()
        else:
            self.monitoring_service.set_correlation_id(correlation_id)
        
        old_correlation_id = self.monitoring_service.get_correlation_id()
        
        try:
            self.monitoring_service.set_correlation_id(correlation_id)
            yield correlation_id
        finally:
            if old_correlation_id:
                self.monitoring_service.set_correlation_id(old_correlation_id)
    
    def monitor_authentication(self, event_type: str):
        """
        Decorator for monitoring authentication events.
        
        Args:
            event_type: Type of authentication event
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    correlation_id = self.monitoring_service.get_correlation_id()
                    
                    try:
                        result = await func(*args, **kwargs)
                        
                        # Log successful authentication
                        self.monitoring_service.log_authentication_event(
                            event_type=event_type,
                            success=True,
                            correlation_id=correlation_id
                        )
                        
                        return result
                        
                    except Exception as e:
                        # Log failed authentication
                        self.monitoring_service.log_authentication_event(
                            event_type=event_type,
                            success=False,
                            error_message=str(e),
                            correlation_id=correlation_id
                        )
                        
                        raise
                
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    correlation_id = self.monitoring_service.get_correlation_id()
                    
                    try:
                        result = func(*args, **kwargs)
                        
                        # Log successful authentication
                        self.monitoring_service.log_authentication_event(
                            event_type=event_type,
                            success=True,
                            correlation_id=correlation_id
                        )
                        
                        return result
                        
                    except Exception as e:
                        # Log failed authentication
                        self.monitoring_service.log_authentication_event(
                            event_type=event_type,
                            success=False,
                            error_message=str(e),
                            correlation_id=correlation_id
                        )
                        
                        raise
                
                return sync_wrapper
        
        return decorator


# Global middleware instance
_monitoring_middleware = None


def get_monitoring_middleware() -> AgentCoreMonitoringMiddleware:
    """Get the global monitoring middleware instance."""
    global _monitoring_middleware
    if _monitoring_middleware is None:
        _monitoring_middleware = AgentCoreMonitoringMiddleware()
    return _monitoring_middleware


def initialize_monitoring_middleware(monitoring_service: Optional[AgentCoreMonitoringService] = None) -> AgentCoreMonitoringMiddleware:
    """
    Initialize the global monitoring middleware with custom configuration.
    
    Args:
        monitoring_service: Optional monitoring service instance
        
    Returns:
        Initialized AgentCoreMonitoringMiddleware instance
    """
    global _monitoring_middleware
    _monitoring_middleware = AgentCoreMonitoringMiddleware(monitoring_service)
    return _monitoring_middleware


# Convenience decorators using global middleware
def monitor_restaurant_search(agent_arn: str, include_input: bool = True, include_output: bool = True):
    """Decorator for monitoring restaurant search operations."""
    return get_monitoring_middleware().monitor_agent_invocation(
        AgentOperationType.RESTAURANT_SEARCH, agent_arn, include_input, include_output
    )


def monitor_restaurant_reasoning(agent_arn: str, include_input: bool = True, include_output: bool = True):
    """Decorator for monitoring restaurant reasoning operations."""
    return get_monitoring_middleware().monitor_agent_invocation(
        AgentOperationType.RESTAURANT_REASONING, agent_arn, include_input, include_output
    )


def monitor_central_district_workflow(agent_arn: str = "workflow", include_input: bool = True, include_output: bool = True):
    """Decorator for monitoring central district workflow operations."""
    return get_monitoring_middleware().monitor_agent_invocation(
        AgentOperationType.CENTRAL_DISTRICT_WORKFLOW, agent_arn, include_input, include_output
    )


def monitor_authentication(event_type: str):
    """Decorator for monitoring authentication events."""
    return get_monitoring_middleware().monitor_authentication(event_type)


# Export main classes and functions
__all__ = [
    'AgentCoreMonitoringMiddleware',
    'MonitoringContext',
    'get_monitoring_middleware',
    'initialize_monitoring_middleware',
    'monitor_restaurant_search',
    'monitor_restaurant_reasoning',
    'monitor_central_district_workflow',
    'monitor_authentication'
]