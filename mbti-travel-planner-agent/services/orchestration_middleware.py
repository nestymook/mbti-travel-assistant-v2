"""
Orchestration Middleware

This module provides middleware for transparent orchestration integration,
enabling request routing through the orchestration engine while maintaining
backward compatibility with existing tool interfaces.

Features:
- Transparent request routing through orchestration engine
- Response formatting and error handling integration
- Backward compatibility with existing tool interfaces
- Performance monitoring and metrics collection
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass
from functools import wraps

from .agentcore_monitoring_service import AgentCoreMonitoringService
from .tool_orchestration_engine import ToolOrchestrationEngine
from .orchestration_types import UserContext, RequestType, OrchestrationResult


@dataclass
class MiddlewareConfig:
    """Configuration for orchestration middleware."""
    enable_orchestration: bool = True
    enable_fallback_to_direct: bool = True
    enable_request_logging: bool = True
    enable_performance_tracking: bool = True
    orchestration_timeout_seconds: int = 60
    fallback_timeout_seconds: int = 30


class OrchestrationMiddleware:
    """
    Middleware layer for transparent orchestration integration.
    
    This middleware intercepts tool invocations and routes them through
    the orchestration engine for intelligent tool selection and execution.
    """
    
    def __init__(self, 
                 orchestration_engine: ToolOrchestrationEngine,
                 monitoring_service: AgentCoreMonitoringService,
                 config: Optional[MiddlewareConfig] = None):
        """
        Initialize orchestration middleware.
        
        Args:
            orchestration_engine: Tool orchestration engine instance
            monitoring_service: Monitoring service for metrics collection
            config: Middleware configuration
        """
        self.orchestration_engine = orchestration_engine
        self.monitoring_service = monitoring_service
        self.config = config or MiddlewareConfig()
        self.logger = logging.getLogger("mbti_travel_planner.orchestration_middleware")
        
        # Track middleware state
        self._enabled = self.config.enable_orchestration
        self._request_count = 0
        self._success_count = 0
        self._fallback_count = 0
        
        self.logger.info("Orchestration middleware initialized")
    
    def enable_orchestration(self):
        """Enable orchestration routing."""
        self._enabled = True
        self.logger.info("Orchestration middleware enabled")
    
    def disable_orchestration(self):
        """Disable orchestration routing (fallback to direct tool calls)."""
        self._enabled = False
        self.logger.info("Orchestration middleware disabled - using direct tool calls")
    
    def is_enabled(self) -> bool:
        """Check if orchestration is enabled."""
        return self._enabled
    
    async def route_request(self, 
                           request_text: str,
                           user_context: Optional[UserContext] = None,
                           correlation_id: Optional[str] = None,
                           direct_tool_fallback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Route request through orchestration engine or fallback to direct tool call.
        
        Args:
            request_text: User request text
            user_context: Optional user context
            correlation_id: Optional correlation ID for tracking
            direct_tool_fallback: Optional direct tool function for fallback
            
        Returns:
            Formatted response from orchestration or direct tool call
        """
        start_time = time.time()
        
        if not correlation_id:
            correlation_id = f"mid_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        self._request_count += 1
        
        # Log request routing
        if self.config.enable_request_logging:
            self.logger.info(f"Routing request through middleware", extra={
                'correlation_id': correlation_id,
                'orchestration_enabled': self._enabled,
                'request_length': len(request_text),
                'has_user_context': user_context is not None
            })
        
        try:
            # Route through orchestration engine if enabled
            if self._enabled:
                result = await self._route_through_orchestration(
                    request_text, user_context, correlation_id
                )
                
                if result.success:
                    self._success_count += 1
                    
                    # Format orchestration response
                    formatted_response = self._format_orchestration_response(result)
                    
                    # Log successful orchestration
                    if self.config.enable_performance_tracking:
                        self.monitoring_service.log_performance_metric(
                            operation="orchestration_middleware_route",
                            duration=(time.time() - start_time),
                            success=True,
                            additional_data={
                                'correlation_id': correlation_id,
                                'orchestration_execution_time_ms': result.execution_time_ms,
                                'tools_used': len(result.tools_used) if result.tools_used else 0,
                                'routing_method': 'orchestration'
                            }
                        )
                    
                    return formatted_response
                
                # Orchestration failed, try fallback if enabled
                elif self.config.enable_fallback_to_direct and direct_tool_fallback:
                    self.logger.warning(f"Orchestration failed, falling back to direct tool call", extra={
                        'correlation_id': correlation_id,
                        'error': result.error_message
                    })
                    
                    return await self._route_through_fallback(
                        request_text, user_context, correlation_id, direct_tool_fallback, start_time
                    )
                
                else:
                    # No fallback available, return orchestration error
                    raise Exception(f"Orchestration failed: {result.error_message}")
            
            # Orchestration disabled, use direct tool call if available
            elif direct_tool_fallback:
                return await self._route_through_fallback(
                    request_text, user_context, correlation_id, direct_tool_fallback, start_time
                )
            
            else:
                raise Exception("Orchestration disabled and no direct tool fallback available")
        
        except Exception as e:
            # Log middleware error
            self.logger.error(f"Middleware routing failed", extra={
                'correlation_id': correlation_id,
                'error': str(e),
                'execution_time_ms': (time.time() - start_time) * 1000
            })
            
            if self.config.enable_performance_tracking:
                self.monitoring_service.log_error(
                    error=e,
                    operation="orchestration_middleware_route",
                    context={
                        'correlation_id': correlation_id,
                        'orchestration_enabled': self._enabled,
                        'has_fallback': direct_tool_fallback is not None
                    }
                )
            
            # Return error response
            return {
                'success': False,
                'error': str(e),
                'correlation_id': correlation_id,
                'routing_method': 'error'
            }
    
    async def _route_through_orchestration(self, 
                                          request_text: str,
                                          user_context: Optional[UserContext],
                                          correlation_id: str) -> OrchestrationResult:
        """Route request through orchestration engine."""
        try:
            # Set timeout for orchestration
            result = await asyncio.wait_for(
                self.orchestration_engine.orchestrate_request(
                    request_text=request_text,
                    user_context=user_context,
                    correlation_id=correlation_id
                ),
                timeout=self.config.orchestration_timeout_seconds
            )
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Orchestration timeout", extra={
                'correlation_id': correlation_id,
                'timeout_seconds': self.config.orchestration_timeout_seconds
            })
            
            return OrchestrationResult(
                correlation_id=correlation_id,
                success=False,
                error_message=f"Orchestration timeout after {self.config.orchestration_timeout_seconds}s"
            )
        
        except Exception as e:
            self.logger.error(f"Orchestration execution error", extra={
                'correlation_id': correlation_id,
                'error': str(e)
            })
            
            return OrchestrationResult(
                correlation_id=correlation_id,
                success=False,
                error_message=str(e)
            )
    
    async def _route_through_fallback(self, 
                                     request_text: str,
                                     user_context: Optional[UserContext],
                                     correlation_id: str,
                                     direct_tool_fallback: Callable,
                                     start_time: float) -> Dict[str, Any]:
        """Route request through direct tool fallback."""
        self._fallback_count += 1
        
        try:
            # Execute direct tool call with timeout
            if asyncio.iscoroutinefunction(direct_tool_fallback):
                result = await asyncio.wait_for(
                    direct_tool_fallback(request_text, user_context),
                    timeout=self.config.fallback_timeout_seconds
                )
            else:
                # Handle synchronous fallback function
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, direct_tool_fallback, request_text, user_context
                    ),
                    timeout=self.config.fallback_timeout_seconds
                )
            
            # Format fallback response
            formatted_response = self._format_fallback_response(result, correlation_id)
            
            # Log successful fallback
            if self.config.enable_performance_tracking:
                self.monitoring_service.log_performance_metric(
                    operation="orchestration_middleware_route",
                    duration=(time.time() - start_time),
                    success=True,
                    additional_data={
                        'correlation_id': correlation_id,
                        'routing_method': 'fallback',
                        'fallback_reason': 'orchestration_disabled_or_failed'
                    }
                )
            
            return formatted_response
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Fallback timeout", extra={
                'correlation_id': correlation_id,
                'timeout_seconds': self.config.fallback_timeout_seconds
            })
            
            return {
                'success': False,
                'error': f"Fallback timeout after {self.config.fallback_timeout_seconds}s",
                'correlation_id': correlation_id,
                'routing_method': 'fallback_timeout'
            }
        
        except Exception as e:
            self.logger.error(f"Fallback execution error", extra={
                'correlation_id': correlation_id,
                'error': str(e)
            })
            
            return {
                'success': False,
                'error': str(e),
                'correlation_id': correlation_id,
                'routing_method': 'fallback_error'
            }
    
    def _format_orchestration_response(self, result: OrchestrationResult) -> Dict[str, Any]:
        """Format orchestration result into standard response format."""
        return {
            'success': result.success,
            'correlation_id': result.correlation_id,
            'results': result.results,
            'execution_time_ms': result.execution_time_ms,
            'tools_used': result.tools_used,
            'routing_method': 'orchestration',
            'metadata': {
                'orchestration_version': '1.0',
                'intelligent_selection': True,
                'performance_optimized': True
            }
        }
    
    def _format_fallback_response(self, result: Any, correlation_id: str) -> Dict[str, Any]:
        """Format fallback result into standard response format."""
        return {
            'success': True,
            'correlation_id': correlation_id,
            'results': [{'result': result}] if result is not None else [],
            'routing_method': 'fallback',
            'metadata': {
                'orchestration_version': '1.0',
                'intelligent_selection': False,
                'performance_optimized': False,
                'fallback_reason': 'orchestration_unavailable'
            }
        }
    
    def get_middleware_stats(self) -> Dict[str, Any]:
        """Get middleware performance statistics."""
        success_rate = (self._success_count / self._request_count) if self._request_count > 0 else 0.0
        fallback_rate = (self._fallback_count / self._request_count) if self._request_count > 0 else 0.0
        
        return {
            'enabled': self._enabled,
            'total_requests': self._request_count,
            'successful_orchestrations': self._success_count,
            'fallback_calls': self._fallback_count,
            'success_rate': success_rate,
            'fallback_rate': fallback_rate,
            'orchestration_rate': 1.0 - fallback_rate if self._request_count > 0 else 0.0
        }


def orchestration_middleware_decorator(middleware: OrchestrationMiddleware):
    """
    Decorator to add orchestration middleware to tool functions.
    
    Args:
        middleware: Orchestration middleware instance
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request parameters
            request_text = kwargs.get('request_text') or (args[0] if args else "")
            user_context = kwargs.get('user_context')
            correlation_id = kwargs.get('correlation_id')
            
            # Create fallback function
            async def direct_fallback(text: str, context: Optional[UserContext]):
                return await func(*args, **kwargs)
            
            # Route through middleware
            return await middleware.route_request(
                request_text=request_text,
                user_context=user_context,
                correlation_id=correlation_id,
                direct_tool_fallback=direct_fallback
            )
        
        return wrapper
    return decorator


class OrchestrationProxy:
    """
    Proxy class for transparent orchestration integration with existing tools.
    
    This proxy intercepts method calls and routes them through the orchestration
    middleware while maintaining the original tool interface.
    """
    
    def __init__(self, 
                 original_tool: Any,
                 middleware: OrchestrationMiddleware,
                 tool_name: str):
        """
        Initialize orchestration proxy.
        
        Args:
            original_tool: Original tool instance
            middleware: Orchestration middleware
            tool_name: Name of the tool for logging
        """
        self._original_tool = original_tool
        self._middleware = middleware
        self._tool_name = tool_name
        self._logger = logging.getLogger(f"mbti_travel_planner.orchestration_proxy.{tool_name}")
    
    def __getattr__(self, name: str):
        """Intercept method calls and route through orchestration if applicable."""
        original_attr = getattr(self._original_tool, name)
        
        # If it's a callable method, wrap it with orchestration
        if callable(original_attr):
            return self._create_orchestrated_method(name, original_attr)
        else:
            # Return non-callable attributes as-is
            return original_attr
    
    def _create_orchestrated_method(self, method_name: str, original_method: Callable):
        """Create orchestrated version of a method."""
        async def orchestrated_method(*args, **kwargs):
            # Check if this method should be orchestrated
            if self._should_orchestrate_method(method_name):
                # Extract request information for orchestration
                request_text = self._extract_request_text(method_name, args, kwargs)
                user_context = self._extract_user_context(args, kwargs)
                correlation_id = kwargs.get('correlation_id')
                
                # Create fallback to original method
                async def original_fallback(text: str, context: Optional[UserContext]):
                    if asyncio.iscoroutinefunction(original_method):
                        return await original_method(*args, **kwargs)
                    else:
                        return original_method(*args, **kwargs)
                
                # Route through middleware
                return await self._middleware.route_request(
                    request_text=request_text,
                    user_context=user_context,
                    correlation_id=correlation_id,
                    direct_tool_fallback=original_fallback
                )
            else:
                # Call original method directly for non-orchestrated methods
                if asyncio.iscoroutinefunction(original_method):
                    return await original_method(*args, **kwargs)
                else:
                    return original_method(*args, **kwargs)
        
        return orchestrated_method
    
    def _should_orchestrate_method(self, method_name: str) -> bool:
        """Determine if a method should be orchestrated."""
        # Orchestrate main tool methods but not utility methods
        orchestrated_methods = {
            'search_restaurants_by_district',
            'search_restaurants_by_meal_type', 
            'search_restaurants_combined',
            'recommend_restaurants',
            'analyze_restaurant_sentiment'
        }
        
        return method_name in orchestrated_methods
    
    def _extract_request_text(self, method_name: str, args: tuple, kwargs: dict) -> str:
        """Extract request text from method arguments."""
        # Create a descriptive request text based on method and parameters
        if method_name == 'search_restaurants_by_district':
            districts = kwargs.get('districts', args[0] if args else [])
            return f"Search restaurants in districts: {districts}"
        
        elif method_name == 'search_restaurants_by_meal_type':
            meal_types = kwargs.get('meal_types', args[0] if args else [])
            return f"Search restaurants for meal types: {meal_types}"
        
        elif method_name == 'search_restaurants_combined':
            districts = kwargs.get('districts', [])
            meal_types = kwargs.get('meal_types', [])
            return f"Search restaurants with districts: {districts}, meal types: {meal_types}"
        
        elif method_name == 'recommend_restaurants':
            restaurants = kwargs.get('restaurants', args[0] if args else [])
            return f"Recommend restaurants from {len(restaurants) if restaurants else 0} candidates"
        
        elif method_name == 'analyze_restaurant_sentiment':
            restaurants = kwargs.get('restaurants', args[0] if args else [])
            return f"Analyze sentiment for {len(restaurants) if restaurants else 0} restaurants"
        
        else:
            return f"Execute {method_name} with {len(args)} args and {len(kwargs)} kwargs"
    
    def _extract_user_context(self, args: tuple, kwargs: dict) -> Optional[UserContext]:
        """Extract user context from method arguments."""
        # Look for user context in kwargs
        user_context = kwargs.get('user_context')
        if user_context:
            return user_context
        
        # Try to construct user context from available parameters
        user_id = kwargs.get('user_id')
        session_id = kwargs.get('session_id')
        mbti_type = kwargs.get('mbti_type')
        
        if any([user_id, session_id, mbti_type]):
            return UserContext(
                user_id=user_id,
                session_id=session_id,
                mbti_type=mbti_type
            )
        
        return None