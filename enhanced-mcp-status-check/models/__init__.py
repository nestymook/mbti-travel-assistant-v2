"""
Enhanced MCP Status Check Data Models

This module provides comprehensive data models for dual health checking
using both MCP tools/list requests and RESTful API health checks.
"""

from .dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig,
    MCPToolsListRequest,
    MCPToolsListResponse,
    MCPValidationResult,
    RESTHealthCheckResponse,
    RESTValidationResult,
    AggregationConfig,
    PriorityConfig,
    CombinedHealthMetrics,
    ServerStatus,
    EnhancedCircuitBreakerState
)

from .metrics_models import (
    MCPMetrics,
    RESTMetrics,
    CombinedMetrics,
    MetricsAggregationReport,
    MetricDataPoint,
    MetricSeries,
    MetricType,
    TimeWindow
)

__all__ = [
    'DualHealthCheckResult',
    'MCPHealthCheckResult', 
    'RESTHealthCheckResult',
    'EnhancedServerConfig',
    'MCPToolsListRequest',
    'MCPToolsListResponse',
    'MCPValidationResult',
    'RESTHealthCheckResponse',
    'RESTValidationResult',
    'AggregationConfig',
    'PriorityConfig',
    'CombinedHealthMetrics',
    'ServerStatus',
    'EnhancedCircuitBreakerState',
    'MCPMetrics',
    'RESTMetrics',
    'CombinedMetrics',
    'MetricsAggregationReport',
    'MetricDataPoint',
    'MetricSeries',
    'MetricType',
    'TimeWindow'
]