"""
Backward Compatibility Layer

This module provides backward compatibility features for the orchestration system,
ensuring existing tool interfaces continue to work while enabling gradual migration
to the new orchestration-based approach.

Features:
- Maintain existing tool interface compatibility
- Feature flags for gradual orchestration rollout
- Migration path for existing tool usage patterns
- Compatibility monitoring and metrics
"""

import logging
import os
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .agentcore_monitoring_service import AgentCoreMonitoringService
from .orchestration_middleware import OrchestrationMiddleware, OrchestrationProxy


class CompatibilityMode(Enum):
    """Compatibility modes for orchestration rollout."""
    LEGACY_ONLY = "legacy_only"  # Use only legacy tools, no orchestration
    HYBRID = "hybrid"  # Use orchestration with fallback to legacy
    ORCHESTRATION_PREFERRED = "orchestration_preferred"  # Prefer orchestration, fallback to legacy
    ORCHESTRATION_ONLY = "orchestration_only"  # Use only orchestration, no legacy fallback


@dataclass
class CompatibilityConfig:
    """Configuration for backward compatibility features."""
    mode: CompatibilityMode = CompatibilityMode.HYBRID
    enable_feature_flags: bool = True
    enable_migration_tracking: bool = True
    enable_compatibility_metrics: bool = True
    legacy_tool_timeout_seconds: int = 30
    orchestration_adoption_percentage: float = 50.0  # Percentage of requests to route through orchestration
    
    # Feature flags for gradual rollout
    enable_orchestration_for_search: bool = True
    enable_orchestration_for_reasoning: bool = True
    enable_orchestration_for_combined: bool = False
    
    # Migration settings
    track_performance_comparison: bool = True
    log_compatibility_issues: bool = True
    alert_on_fallback_failures: bool = True


class BackwardCompatibilityManager:
    """
    Manager for backward compatibility features and gradual orchestration rollout.
    
    This manager handles:
    - Feature flag management for gradual rollout
    - Tool interface compatibility
    - Migration tracking and metrics
    - Performance comparison between legacy and orchestration
    """
    
    def __init__(self, 
                 config: Optional[CompatibilityConfig] = None,
                 monitoring_service: Optional[AgentCoreMonitoringService] = None,
                 environment: str = "production"):
        """
        Initialize backward compatibility manager.
        
        Args:
            config: Compatibility configuration
            monitoring_service: Monitoring service for metrics
            environment: Environment name
        """
        self.config = config or CompatibilityConfig()
        self.monitoring_service = monitoring_service
        self.environment = environment
        self.logger = logging.getLogger("mbti_travel_planner.backward_compatibility")
        
        # Load feature flags from environment variables
        self._load_feature_flags_from_env()
        
        # Compatibility tracking
        self._legacy_call_count = 0
        self._orchestration_call_count = 0
        self._fallback_count = 0
        self._compatibility_issues = []
        
        self.logger.info(f"Backward compatibility manager initialized in {self.config.mode.value} mode")
    
    def _load_feature_flags_from_env(self):
        """Load feature flags from environment variables."""
        # Override config with environment variables if present
        if os.getenv('ORCHESTRATION_MODE'):
            try:
                self.config.mode = CompatibilityMode(os.getenv('ORCHESTRATION_MODE'))
            except ValueError:
                self.logger.warning(f"Invalid orchestration mode in environment: {os.getenv('ORCHESTRATION_MODE')}")
        
        if os.getenv('ORCHESTRATION_ADOPTION_PERCENTAGE'):
            try:
                self.config.orchestration_adoption_percentage = float(os.getenv('ORCHESTRATION_ADOPTION_PERCENTAGE'))
            except ValueError:
                self.logger.warning(f"Invalid adoption percentage in environment: {os.getenv('ORCHESTRATION_ADOPTION_PERCENTAGE')}")
        
        # Feature-specific flags
        self.config.enable_orchestration_for_search = os.getenv('ENABLE_ORCHESTRATION_SEARCH', 'true').lower() == 'true'
        self.config.enable_orchestration_for_reasoning = os.getenv('ENABLE_ORCHESTRATION_REASONING', 'true').lower() == 'true'
        self.config.enable_orchestration_for_combined = os.getenv('ENABLE_ORCHESTRATION_COMBINED', 'false').lower() == 'true'
        
        self.logger.info(f"Feature flags loaded - Search: {self.config.enable_orchestration_for_search}, "
                        f"Reasoning: {self.config.enable_orchestration_for_reasoning}, "
                        f"Combined: {self.config.enable_orchestration_for_combined}")
    
    def should_use_orchestration(self, tool_type: str, request_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if orchestration should be used for a specific tool type and request.
        
        Args:
            tool_type: Type of tool (search, reasoning, combined)
            request_context: Optional request context for decision making
            
        Returns:
            True if orchestration should be used, False for legacy tools
        """
        # Check compatibility mode
        if self.config.mode == CompatibilityMode.LEGACY_ONLY:
            return False
        elif self.config.mode == CompatibilityMode.ORCHESTRATION_ONLY:
            return True
        
        # For hybrid modes, check feature flags and adoption percentage
        if self.config.mode in [CompatibilityMode.HYBRID, CompatibilityMode.ORCHESTRATION_PREFERRED]:
            # Check tool-specific feature flags
            if tool_type == 'search' and not self.config.enable_orchestration_for_search:
                return False
            elif tool_type == 'reasoning' and not self.config.enable_orchestration_for_reasoning:
                return False
            elif tool_type == 'combined' and not self.config.enable_orchestration_for_combined:
                return False
            
            # Check adoption percentage (simple hash-based distribution)
            if request_context:
                request_hash = hash(str(request_context)) % 100
                return request_hash < self.config.orchestration_adoption_percentage
            else:
                # Default to adoption percentage
                import random
                return random.random() * 100 < self.config.orchestration_adoption_percentage
        
        return False
    
    def create_compatible_tool(self, 
                              legacy_tool: Any,
                              orchestration_middleware: Optional[OrchestrationMiddleware],
                              tool_type: str) -> Any:
        """
        Create a compatible tool that can use either legacy or orchestration approach.
        
        Args:
            legacy_tool: Original legacy tool instance
            orchestration_middleware: Orchestration middleware (if available)
            tool_type: Type of tool for feature flag checking
            
        Returns:
            Compatible tool instance
        """
        if not orchestration_middleware or self.config.mode == CompatibilityMode.LEGACY_ONLY:
            # Return legacy tool as-is
            self.logger.debug(f"Using legacy tool for {tool_type}")
            return legacy_tool
        
        # Create compatibility wrapper
        return CompatibleToolWrapper(
            legacy_tool=legacy_tool,
            orchestration_middleware=orchestration_middleware,
            compatibility_manager=self,
            tool_type=tool_type
        )
    
    def track_legacy_call(self, tool_type: str, method_name: str, success: bool, duration_ms: float):
        """Track legacy tool call for compatibility metrics."""
        self._legacy_call_count += 1
        
        if self.config.enable_compatibility_metrics and self.monitoring_service:
            try:
                self.monitoring_service.log_performance_metric(
                    operation=f"legacy_tool_call_{tool_type}_{method_name}",
                    duration=duration_ms / 1000.0,
                    success=success,
                    additional_data={
                        'tool_type': tool_type,
                        'method_name': method_name,
                        'compatibility_mode': self.config.mode.value,
                        'call_type': 'legacy'
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to log legacy call metrics: {e}")
    
    def track_orchestration_call(self, tool_type: str, method_name: str, success: bool, duration_ms: float):
        """Track orchestration call for compatibility metrics."""
        self._orchestration_call_count += 1
        
        if self.config.enable_compatibility_metrics and self.monitoring_service:
            try:
                self.monitoring_service.log_performance_metric(
                    operation=f"orchestration_call_{tool_type}_{method_name}",
                    duration=duration_ms / 1000.0,
                    success=success,
                    additional_data={
                        'tool_type': tool_type,
                        'method_name': method_name,
                        'compatibility_mode': self.config.mode.value,
                        'call_type': 'orchestration'
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to log orchestration call metrics: {e}")
    
    def track_fallback(self, tool_type: str, method_name: str, reason: str):
        """Track fallback from orchestration to legacy."""
        self._fallback_count += 1
        
        if self.config.log_compatibility_issues:
            self.logger.warning(f"Fallback to legacy tool: {tool_type}.{method_name} - {reason}")
        
        if self.config.enable_compatibility_metrics and self.monitoring_service:
            try:
                self.monitoring_service.log_performance_metric(
                    operation=f"orchestration_fallback_{tool_type}_{method_name}",
                    duration=0.0,
                    success=False,
                    error_type="orchestration_fallback",
                    additional_data={
                        'tool_type': tool_type,
                        'method_name': method_name,
                        'fallback_reason': reason,
                        'compatibility_mode': self.config.mode.value
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to log fallback metrics: {e}")
    
    def get_compatibility_stats(self) -> Dict[str, Any]:
        """Get compatibility and migration statistics."""
        total_calls = self._legacy_call_count + self._orchestration_call_count
        
        return {
            'compatibility_mode': self.config.mode.value,
            'total_calls': total_calls,
            'legacy_calls': self._legacy_call_count,
            'orchestration_calls': self._orchestration_call_count,
            'fallback_calls': self._fallback_count,
            'orchestration_adoption_rate': (self._orchestration_call_count / total_calls) if total_calls > 0 else 0.0,
            'fallback_rate': (self._fallback_count / self._orchestration_call_count) if self._orchestration_call_count > 0 else 0.0,
            'feature_flags': {
                'search_orchestration': self.config.enable_orchestration_for_search,
                'reasoning_orchestration': self.config.enable_orchestration_for_reasoning,
                'combined_orchestration': self.config.enable_orchestration_for_combined
            },
            'target_adoption_percentage': self.config.orchestration_adoption_percentage
        }


class CompatibleToolWrapper:
    """
    Wrapper that provides backward compatibility while enabling orchestration.
    
    This wrapper maintains the exact same interface as legacy tools while
    intelligently routing calls through orchestration or legacy implementation
    based on feature flags and compatibility settings.
    """
    
    def __init__(self, 
                 legacy_tool: Any,
                 orchestration_middleware: OrchestrationMiddleware,
                 compatibility_manager: BackwardCompatibilityManager,
                 tool_type: str):
        """
        Initialize compatible tool wrapper.
        
        Args:
            legacy_tool: Original legacy tool
            orchestration_middleware: Orchestration middleware
            compatibility_manager: Compatibility manager
            tool_type: Type of tool for feature flag checking
        """
        self._legacy_tool = legacy_tool
        self._orchestration_middleware = orchestration_middleware
        self._compatibility_manager = compatibility_manager
        self._tool_type = tool_type
        self._logger = logging.getLogger(f"mbti_travel_planner.compatible_tool.{tool_type}")
        
        # Create orchestration proxy for this tool
        self._orchestration_proxy = OrchestrationProxy(
            original_tool=legacy_tool,
            middleware=orchestration_middleware,
            tool_name=f"{tool_type}_tool"
        )
    
    def __getattr__(self, name: str):
        """Route method calls through compatibility layer."""
        # Get the method from both legacy and orchestration implementations
        legacy_method = getattr(self._legacy_tool, name)
        
        if not callable(legacy_method):
            # Return non-callable attributes from legacy tool
            return legacy_method
        
        # Create compatible method that can route to either implementation
        return self._create_compatible_method(name, legacy_method)
    
    def _create_compatible_method(self, method_name: str, legacy_method: Callable):
        """Create a method that routes between legacy and orchestration implementations."""
        async def compatible_method(*args, **kwargs):
            import time
            import asyncio
            
            # Determine routing based on compatibility settings
            request_context = {
                'method_name': method_name,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            
            use_orchestration = self._compatibility_manager.should_use_orchestration(
                self._tool_type, request_context
            )
            
            if use_orchestration:
                # Try orchestration first
                try:
                    start_time = time.time()
                    
                    # Get orchestration method
                    orchestration_method = getattr(self._orchestration_proxy, method_name)
                    
                    # Execute orchestration method
                    if asyncio.iscoroutinefunction(orchestration_method):
                        result = await orchestration_method(*args, **kwargs)
                    else:
                        result = orchestration_method(*args, **kwargs)
                    
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Track successful orchestration call
                    self._compatibility_manager.track_orchestration_call(
                        self._tool_type, method_name, True, duration_ms
                    )
                    
                    return result
                
                except Exception as e:
                    # Orchestration failed, track and fallback to legacy
                    self._compatibility_manager.track_fallback(
                        self._tool_type, method_name, f"orchestration_error: {str(e)}"
                    )
                    
                    self._logger.warning(f"Orchestration failed for {method_name}, falling back to legacy: {e}")
                    
                    # Fall through to legacy execution
            
            # Execute legacy method
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(legacy_method):
                    result = await legacy_method(*args, **kwargs)
                else:
                    result = legacy_method(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Track successful legacy call
                self._compatibility_manager.track_legacy_call(
                    self._tool_type, method_name, True, duration_ms
                )
                
                return result
            
            except Exception as e:
                # Track failed legacy call
                self._compatibility_manager.track_legacy_call(
                    self._tool_type, method_name, False, 0
                )
                
                self._logger.error(f"Legacy method {method_name} failed: {e}")
                raise
        
        return compatible_method


def create_migration_report(compatibility_manager: BackwardCompatibilityManager) -> Dict[str, Any]:
    """
    Create a migration report showing orchestration adoption progress.
    
    Args:
        compatibility_manager: Compatibility manager instance
        
    Returns:
        Migration report with statistics and recommendations
    """
    stats = compatibility_manager.get_compatibility_stats()
    
    # Calculate migration progress
    adoption_rate = stats['orchestration_adoption_rate']
    target_rate = stats['target_adoption_percentage'] / 100.0
    
    migration_progress = min(adoption_rate / target_rate, 1.0) if target_rate > 0 else 0.0
    
    # Generate recommendations
    recommendations = []
    
    if adoption_rate < 0.1:
        recommendations.append("Consider enabling orchestration for more tool types")
    elif adoption_rate < 0.5:
        recommendations.append("Gradually increase orchestration adoption percentage")
    elif adoption_rate > 0.9:
        recommendations.append("Consider switching to orchestration-only mode")
    
    if stats['fallback_rate'] > 0.1:
        recommendations.append("High fallback rate detected - investigate orchestration issues")
    
    return {
        'migration_progress': migration_progress,
        'adoption_rate': adoption_rate,
        'target_rate': target_rate,
        'statistics': stats,
        'recommendations': recommendations,
        'next_steps': _generate_next_steps(stats),
        'report_timestamp': time.time()
    }


def _generate_next_steps(stats: Dict[str, Any]) -> List[str]:
    """Generate next steps for migration based on current statistics."""
    next_steps = []
    
    mode = stats['compatibility_mode']
    adoption_rate = stats['orchestration_adoption_rate']
    
    if mode == 'legacy_only':
        next_steps.append("Switch to hybrid mode to begin orchestration testing")
    elif mode == 'hybrid':
        if adoption_rate < 0.25:
            next_steps.append("Increase orchestration adoption percentage to 25%")
        elif adoption_rate < 0.50:
            next_steps.append("Increase orchestration adoption percentage to 50%")
        elif adoption_rate < 0.75:
            next_steps.append("Increase orchestration adoption percentage to 75%")
        else:
            next_steps.append("Consider switching to orchestration-preferred mode")
    elif mode == 'orchestration_preferred':
        if adoption_rate > 0.95 and stats['fallback_rate'] < 0.05:
            next_steps.append("Consider switching to orchestration-only mode")
        else:
            next_steps.append("Monitor performance and reduce fallback rate")
    
    return next_steps