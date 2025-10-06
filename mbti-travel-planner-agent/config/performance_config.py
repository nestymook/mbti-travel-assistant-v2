"""
Performance Optimization Configuration

This module provides configuration classes and factory functions for all
performance optimization features in the MBTI Travel Planner Agent.

Features:
- Response caching configuration
- Connection pooling configuration  
- Parallel execution configuration
- Optimized token refresh configuration
- Environment-specific performance tuning
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

from services.response_cache import CacheConfig, CacheEvictionPolicy
from services.connection_pool_manager import ConnectionConfig
from services.parallel_execution_service import ExecutionConfig, ExecutionStrategy
from services.optimized_token_refresh import RefreshConfig, RefreshStrategy


class PerformanceProfile(Enum):
    """Performance optimization profiles for different use cases."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_THROUGHPUT = "high_throughput"
    LOW_LATENCY = "low_latency"
    RESOURCE_CONSTRAINED = "resource_constrained"


@dataclass
class PerformanceOptimizationConfig:
    """Comprehensive configuration for all performance optimizations."""
    
    # Feature flags
    enable_response_caching: bool = True
    enable_connection_pooling: bool = True
    enable_parallel_execution: bool = True
    enable_optimized_token_refresh: bool = True
    
    # Service configurations
    cache_config: CacheConfig = field(default_factory=CacheConfig)
    connection_config: ConnectionConfig = field(default_factory=ConnectionConfig)
    execution_config: ExecutionConfig = field(default_factory=ExecutionConfig)
    refresh_config: RefreshConfig = field(default_factory=RefreshConfig)
    
    # Performance monitoring
    enable_performance_monitoring: bool = True
    performance_metrics_interval_seconds: int = 60
    
    # Environment-specific settings
    profile: PerformanceProfile = PerformanceProfile.PRODUCTION
    
    @classmethod
    def from_environment(cls, profile: Optional[PerformanceProfile] = None) -> 'PerformanceOptimizationConfig':
        """
        Create configuration from environment variables.
        
        Args:
            profile: Performance profile to use
            
        Returns:
            PerformanceOptimizationConfig instance
        """
        # Determine profile from environment or parameter
        if profile is None:
            env_profile = os.getenv('PERFORMANCE_PROFILE', 'production').lower()
            try:
                profile = PerformanceProfile(env_profile)
            except ValueError:
                profile = PerformanceProfile.PRODUCTION
        
        # Create base configuration
        config = cls._create_profile_config(profile)
        
        # Override with environment variables
        config._apply_environment_overrides()
        
        return config
    
    @classmethod
    def _create_profile_config(cls, profile: PerformanceProfile) -> 'PerformanceOptimizationConfig':
        """Create configuration for specific performance profile."""
        
        if profile == PerformanceProfile.DEVELOPMENT:
            return cls._create_development_config()
        elif profile == PerformanceProfile.TESTING:
            return cls._create_testing_config()
        elif profile == PerformanceProfile.STAGING:
            return cls._create_staging_config()
        elif profile == PerformanceProfile.PRODUCTION:
            return cls._create_production_config()
        elif profile == PerformanceProfile.HIGH_THROUGHPUT:
            return cls._create_high_throughput_config()
        elif profile == PerformanceProfile.LOW_LATENCY:
            return cls._create_low_latency_config()
        elif profile == PerformanceProfile.RESOURCE_CONSTRAINED:
            return cls._create_resource_constrained_config()
        else:
            return cls._create_production_config()
    
    @classmethod
    def _create_development_config(cls) -> 'PerformanceOptimizationConfig':
        """Create configuration optimized for development."""
        return cls(
            profile=PerformanceProfile.DEVELOPMENT,
            enable_response_caching=True,
            enable_connection_pooling=False,  # Simpler debugging
            enable_parallel_execution=True,
            enable_optimized_token_refresh=True,
            
            cache_config=CacheConfig(
                default_ttl_seconds=60,  # Short TTL for development
                max_cache_size=50,
                cleanup_interval_seconds=30,
                enable_statistics=True
            ),
            
            connection_config=ConnectionConfig(
                max_connections_per_pool=2,
                min_connections_per_pool=1,
                health_check_interval_seconds=30
            ),
            
            execution_config=ExecutionConfig(
                strategy=ExecutionStrategy.BEST_EFFORT,
                max_concurrent_tasks=3,
                default_timeout_seconds=30,
                enable_retries=True
            ),
            
            refresh_config=RefreshConfig(
                strategy=RefreshStrategy.REACTIVE,
                background_refresh_enabled=False,
                enable_usage_prediction=False
            ),
            
            enable_performance_monitoring=True,
            performance_metrics_interval_seconds=30
        )
    
    @classmethod
    def _create_testing_config(cls) -> 'PerformanceOptimizationConfig':
        """Create configuration optimized for testing."""
        return cls(
            profile=PerformanceProfile.TESTING,
            enable_response_caching=False,  # Avoid test interference
            enable_connection_pooling=False,
            enable_parallel_execution=True,
            enable_optimized_token_refresh=False,  # Use mocks instead
            
            execution_config=ExecutionConfig(
                strategy=ExecutionStrategy.FAIL_FAST,
                max_concurrent_tasks=2,
                default_timeout_seconds=10,
                enable_retries=False  # Faster test execution
            ),
            
            enable_performance_monitoring=False
        )
    
    @classmethod
    def _create_staging_config(cls) -> 'PerformanceOptimizationConfig':
        """Create configuration optimized for staging environment."""
        return cls(
            profile=PerformanceProfile.STAGING,
            enable_response_caching=True,
            enable_connection_pooling=True,
            enable_parallel_execution=True,
            enable_optimized_token_refresh=True,
            
            cache_config=CacheConfig(
                default_ttl_seconds=300,  # 5 minutes
                max_cache_size=200,
                cleanup_interval_seconds=60,
                enable_statistics=True
            ),
            
            connection_config=ConnectionConfig(
                max_connections_per_pool=5,
                min_connections_per_pool=2,
                health_check_interval_seconds=60
            ),
            
            execution_config=ExecutionConfig(
                strategy=ExecutionStrategy.BEST_EFFORT,
                max_concurrent_tasks=5,
                default_timeout_seconds=45,
                enable_retries=True
            ),
            
            refresh_config=RefreshConfig(
                strategy=RefreshStrategy.PROACTIVE,
                proactive_refresh_threshold_seconds=300,
                background_refresh_enabled=True,
                enable_usage_prediction=True
            ),
            
            enable_performance_monitoring=True,
            performance_metrics_interval_seconds=60
        )
    
    @classmethod
    def _create_production_config(cls) -> 'PerformanceOptimizationConfig':
        """Create configuration optimized for production."""
        return cls(
            profile=PerformanceProfile.PRODUCTION,
            enable_response_caching=True,
            enable_connection_pooling=True,
            enable_parallel_execution=True,
            enable_optimized_token_refresh=True,
            
            cache_config=CacheConfig(
                default_ttl_seconds=600,  # 10 minutes
                max_cache_size=1000,
                eviction_policy=CacheEvictionPolicy.LRU,
                cleanup_interval_seconds=120,
                enable_statistics=True,
                operation_ttl_overrides={
                    "search_restaurants_by_district": 900,  # 15 minutes
                    "search_restaurants_by_meal_type": 1200,  # 20 minutes
                    "search_restaurants_combined": 900,  # 15 minutes
                    "get_recommendations": 600,  # 10 minutes
                    "analyze_restaurant_sentiment": 1800,  # 30 minutes
                }
            ),
            
            connection_config=ConnectionConfig(
                max_connections_per_pool=10,
                min_connections_per_pool=3,
                max_idle_time_seconds=300,
                health_check_interval_seconds=120,
                enable_health_monitoring=True
            ),
            
            execution_config=ExecutionConfig(
                strategy=ExecutionStrategy.BEST_EFFORT,
                max_concurrent_tasks=10,
                default_timeout_seconds=60,
                enable_retries=True,
                max_retries_per_task=2
            ),
            
            refresh_config=RefreshConfig(
                strategy=RefreshStrategy.PROACTIVE,
                proactive_refresh_threshold_seconds=300,
                background_refresh_enabled=True,
                background_refresh_interval_seconds=60,
                enable_usage_prediction=True,
                refresh_rate_limit_per_minute=10
            ),
            
            enable_performance_monitoring=True,
            performance_metrics_interval_seconds=60
        )
    
    @classmethod
    def _create_high_throughput_config(cls) -> 'PerformanceOptimizationConfig':
        """Create configuration optimized for high throughput scenarios."""
        return cls(
            profile=PerformanceProfile.HIGH_THROUGHPUT,
            enable_response_caching=True,
            enable_connection_pooling=True,
            enable_parallel_execution=True,
            enable_optimized_token_refresh=True,
            
            cache_config=CacheConfig(
                default_ttl_seconds=1800,  # 30 minutes - longer caching
                max_cache_size=2000,  # Larger cache
                eviction_policy=CacheEvictionPolicy.LRU,
                cleanup_interval_seconds=300,
                enable_statistics=True
            ),
            
            connection_config=ConnectionConfig(
                max_connections_per_pool=20,  # More connections
                min_connections_per_pool=5,
                max_idle_time_seconds=600,
                health_check_interval_seconds=180
            ),
            
            execution_config=ExecutionConfig(
                strategy=ExecutionStrategy.BEST_EFFORT,
                max_concurrent_tasks=20,  # Higher concurrency
                default_timeout_seconds=90,
                enable_retries=True,
                max_retries_per_task=3
            ),
            
            refresh_config=RefreshConfig(
                strategy=RefreshStrategy.POOLED,  # Token pooling
                token_pool_size=5,
                background_refresh_enabled=True,
                background_refresh_interval_seconds=30,
                enable_usage_prediction=True,
                refresh_rate_limit_per_minute=20
            ),
            
            enable_performance_monitoring=True,
            performance_metrics_interval_seconds=30
        )
    
    @classmethod
    def _create_low_latency_config(cls) -> 'PerformanceOptimizationConfig':
        """Create configuration optimized for low latency."""
        return cls(
            profile=PerformanceProfile.LOW_LATENCY,
            enable_response_caching=True,
            enable_connection_pooling=True,
            enable_parallel_execution=True,
            enable_optimized_token_refresh=True,
            
            cache_config=CacheConfig(
                default_ttl_seconds=300,  # Shorter TTL for freshness
                max_cache_size=500,
                eviction_policy=CacheEvictionPolicy.LRU,
                cleanup_interval_seconds=60,
                enable_statistics=True
            ),
            
            connection_config=ConnectionConfig(
                max_connections_per_pool=15,
                min_connections_per_pool=5,  # Keep connections warm
                max_idle_time_seconds=180,
                connection_timeout_seconds=10,  # Faster timeouts
                health_check_interval_seconds=60
            ),
            
            execution_config=ExecutionConfig(
                strategy=ExecutionStrategy.FAIL_FAST,  # Fail fast for low latency
                max_concurrent_tasks=15,
                default_timeout_seconds=30,  # Shorter timeouts
                enable_retries=True,
                max_retries_per_task=1,  # Fewer retries
                retry_delay_seconds=0.5
            ),
            
            refresh_config=RefreshConfig(
                strategy=RefreshStrategy.PREDICTIVE,  # Predictive refresh
                proactive_refresh_threshold_seconds=600,  # Refresh earlier
                background_refresh_enabled=True,
                background_refresh_interval_seconds=30,
                enable_usage_prediction=True
            ),
            
            enable_performance_monitoring=True,
            performance_metrics_interval_seconds=30
        )
    
    @classmethod
    def _create_resource_constrained_config(cls) -> 'PerformanceOptimizationConfig':
        """Create configuration optimized for resource-constrained environments."""
        return cls(
            profile=PerformanceProfile.RESOURCE_CONSTRAINED,
            enable_response_caching=True,  # Caching helps reduce load
            enable_connection_pooling=False,  # Reduce memory usage
            enable_parallel_execution=False,  # Reduce CPU usage
            enable_optimized_token_refresh=True,
            
            cache_config=CacheConfig(
                default_ttl_seconds=900,  # Longer TTL to reduce refreshes
                max_cache_size=100,  # Smaller cache
                eviction_policy=CacheEvictionPolicy.LRU,
                cleanup_interval_seconds=300,
                enable_statistics=False  # Reduce overhead
            ),
            
            execution_config=ExecutionConfig(
                strategy=ExecutionStrategy.BEST_EFFORT,
                max_concurrent_tasks=2,  # Lower concurrency
                default_timeout_seconds=120,  # Longer timeouts
                enable_retries=True,
                max_retries_per_task=1
            ),
            
            refresh_config=RefreshConfig(
                strategy=RefreshStrategy.REACTIVE,  # Simpler strategy
                background_refresh_enabled=False,  # Reduce background tasks
                enable_usage_prediction=False,
                refresh_rate_limit_per_minute=5
            ),
            
            enable_performance_monitoring=False,  # Reduce overhead
            performance_metrics_interval_seconds=300
        )
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides to configuration."""
        # Feature flags
        self.enable_response_caching = self._get_bool_env(
            'ENABLE_RESPONSE_CACHING', self.enable_response_caching
        )
        self.enable_connection_pooling = self._get_bool_env(
            'ENABLE_CONNECTION_POOLING', self.enable_connection_pooling
        )
        self.enable_parallel_execution = self._get_bool_env(
            'ENABLE_PARALLEL_EXECUTION', self.enable_parallel_execution
        )
        self.enable_optimized_token_refresh = self._get_bool_env(
            'ENABLE_OPTIMIZED_TOKEN_REFRESH', self.enable_optimized_token_refresh
        )
        
        # Cache configuration overrides
        if hasattr(self.cache_config, 'default_ttl_seconds'):
            self.cache_config.default_ttl_seconds = self._get_int_env(
                'CACHE_DEFAULT_TTL_SECONDS', self.cache_config.default_ttl_seconds
            )
        
        if hasattr(self.cache_config, 'max_cache_size'):
            self.cache_config.max_cache_size = self._get_int_env(
                'CACHE_MAX_SIZE', self.cache_config.max_cache_size
            )
        
        # Connection configuration overrides
        if hasattr(self.connection_config, 'max_connections_per_pool'):
            self.connection_config.max_connections_per_pool = self._get_int_env(
                'MAX_CONNECTIONS_PER_POOL', self.connection_config.max_connections_per_pool
            )
        
        # Execution configuration overrides
        if hasattr(self.execution_config, 'max_concurrent_tasks'):
            self.execution_config.max_concurrent_tasks = self._get_int_env(
                'MAX_CONCURRENT_TASKS', self.execution_config.max_concurrent_tasks
            )
        
        # Performance monitoring
        self.enable_performance_monitoring = self._get_bool_env(
            'ENABLE_PERFORMANCE_MONITORING', self.enable_performance_monitoring
        )
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "profile": self.profile.value,
            "feature_flags": {
                "enable_response_caching": self.enable_response_caching,
                "enable_connection_pooling": self.enable_connection_pooling,
                "enable_parallel_execution": self.enable_parallel_execution,
                "enable_optimized_token_refresh": self.enable_optimized_token_refresh,
            },
            "cache_config": {
                "default_ttl_seconds": self.cache_config.default_ttl_seconds,
                "max_cache_size": self.cache_config.max_cache_size,
                "eviction_policy": self.cache_config.eviction_policy.value,
            },
            "connection_config": {
                "max_connections_per_pool": self.connection_config.max_connections_per_pool,
                "min_connections_per_pool": self.connection_config.min_connections_per_pool,
                "health_check_interval_seconds": self.connection_config.health_check_interval_seconds,
            },
            "execution_config": {
                "strategy": self.execution_config.strategy.value,
                "max_concurrent_tasks": self.execution_config.max_concurrent_tasks,
                "default_timeout_seconds": self.execution_config.default_timeout_seconds,
            },
            "refresh_config": {
                "strategy": self.refresh_config.strategy.value,
                "background_refresh_enabled": self.refresh_config.background_refresh_enabled,
                "enable_usage_prediction": self.refresh_config.enable_usage_prediction,
            },
            "monitoring": {
                "enable_performance_monitoring": self.enable_performance_monitoring,
                "performance_metrics_interval_seconds": self.performance_metrics_interval_seconds,
            }
        }


def get_performance_config(profile: Optional[PerformanceProfile] = None) -> PerformanceOptimizationConfig:
    """
    Get performance optimization configuration.
    
    Args:
        profile: Optional performance profile
        
    Returns:
        PerformanceOptimizationConfig instance
    """
    return PerformanceOptimizationConfig.from_environment(profile)


def create_agentcore_client_with_optimizations(
    config: PerformanceOptimizationConfig,
    region: str = "us-east-1"
) -> 'AgentCoreRuntimeClient':
    """
    Create AgentCore runtime client with performance optimizations.
    
    Args:
        config: Performance optimization configuration
        region: AWS region
        
    Returns:
        Configured AgentCoreRuntimeClient
    """
    from services.agentcore_runtime_client import AgentCoreRuntimeClient
    
    return AgentCoreRuntimeClient(
        region=region,
        enable_caching=config.enable_response_caching,
        enable_connection_pooling=config.enable_connection_pooling,
        enable_parallel_execution=config.enable_parallel_execution,
        cache_config=config.cache_config if config.enable_response_caching else None,
        pool_config=config.connection_config if config.enable_connection_pooling else None,
        execution_config=config.execution_config if config.enable_parallel_execution else None
    )


# Export main classes and functions
__all__ = [
    'PerformanceOptimizationConfig',
    'PerformanceProfile',
    'get_performance_config',
    'create_agentcore_client_with_optimizations'
]