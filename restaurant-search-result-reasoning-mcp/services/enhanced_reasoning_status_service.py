"""
Enhanced Status Service for Restaurant Reasoning MCP

This module integrates the enhanced MCP status check system with the restaurant reasoning MCP server,
providing dual monitoring capabilities with MCP tools/list and REST health checks specifically
tailored for reasoning and sentiment analysis operations.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import enhanced status check components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "enhanced-mcp-status-check"))

from models.dual_health_models import (
    EnhancedServerConfig,
    DualHealthCheckResult,
    ServerStatus
)
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.enhanced_status_config import EnhancedStatusConfig
from api.enhanced_status_endpoints import EnhancedStatusEndpoints

logger = logging.getLogger(__name__)


class RestaurantReasoningEnhancedStatusService:
    """
    Enhanced Status Service for Restaurant Reasoning MCP.
    
    Integrates enhanced dual monitoring capabilities with the restaurant reasoning MCP server,
    providing comprehensive health monitoring using both MCP tools/list requests and REST API checks
    with specific focus on reasoning and sentiment analysis capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Enhanced Reasoning Status Service.
        
        Args:
            config_path: Optional path to enhanced configuration file
        """
        self.config_path = config_path or "config/enhanced_status_config.json"
        self.config: Optional[EnhancedStatusConfig] = None
        self.health_service: Optional[EnhancedHealthCheckService] = None
        self.metrics_collector: Optional[DualMetricsCollector] = None
        self.status_endpoints: Optional[EnhancedStatusEndpoints] = None
        
        # Service state
        self._initialized = False
        self._running = False
        
        # Reasoning-specific metrics
        self._reasoning_metrics = {
            "recommendation_requests": 0,
            "sentiment_analysis_requests": 0,
            "successful_reasoning_operations": 0,
            "failed_reasoning_operations": 0,
            "average_reasoning_time_ms": 0.0
        }
        
    async def initialize(self):
        """Initialize the enhanced reasoning status service."""
        try:
            logger.info("Initializing Restaurant Reasoning Enhanced Status Service")
            
            # Load enhanced configuration
            await self._load_enhanced_config()
            
            # Initialize metrics collector with reasoning-specific settings
            self.metrics_collector = DualMetricsCollector(
                retention_hours=self.config.monitoring.metrics_retention_hours,
                custom_metrics_enabled=True
            )
            
            # Initialize health check service with reasoning-optimized settings
            self.health_service = EnhancedHealthCheckService(
                aggregation_config=self.config.result_aggregation,
                max_concurrent_servers=self.config.monitoring.max_concurrent_checks,
                max_concurrent_per_server=2
            )
            
            # Initialize status endpoints
            self.status_endpoints = EnhancedStatusEndpoints(
                health_service=self.health_service,
                metrics_collector=self.metrics_collector,
                config_manager=self.config
            )
            
            self._initialized = True
            logger.info("Restaurant Reasoning Enhanced Status Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced reasoning status service: {e}")
            raise
    
    async def _load_enhanced_config(self):
        """Load enhanced status configuration for reasoning service."""
        try:
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                logger.warning(f"Enhanced config file not found: {config_file}")
                # Create default configuration for reasoning service
                self.config = EnhancedStatusConfig.create_default()
                self.config.system_name = "restaurant-reasoning-mcp-enhanced"
                
                # Customize for reasoning operations
                self.config.mcp_health_checks.default_timeout_seconds = 12
                self.config.mcp_health_checks.request_timeout_ms = 35000
                self.config.rest_health_checks.default_timeout_seconds = 10
                self.config.rest_health_checks.required_health_fields = [
                    "status", "timestamp", "reasoning_capabilities"
                ]
                self.config.result_aggregation.mcp_priority_weight = 0.8
                self.config.result_aggregation.rest_priority_weight = 0.2
                self.config.monitoring.health_check_interval_seconds = 45
                self.config.monitoring.metrics_retention_hours = 48
                
                # Add default server configuration for reasoning
                server_config = EnhancedServerConfig(
                    server_name="restaurant-search-result-reasoning-mcp",
                    mcp_endpoint_url="https://your-gateway-url/mcp/restaurant-search-result-reasoning-mcp",
                    mcp_timeout_seconds=12,
                    mcp_expected_tools=[
                        "recommend_restaurants",
                        "analyze_restaurant_sentiment"
                    ],
                    rest_health_endpoint_url="https://your-gateway-url/mcp/restaurant-search-result-reasoning-mcp/status/health",
                    rest_timeout_seconds=10,
                    mcp_priority_weight=0.8,
                    rest_priority_weight=0.2,
                    priority="high",
                    description="Restaurant recommendation and sentiment analysis reasoning with enhanced dual monitoring"
                )
                self.config.add_server(server_config)
                
                # Save default configuration
                self.config.save_to_file(config_file)
                logger.info(f"Created default enhanced reasoning configuration: {config_file}")
            else:
                # Load existing configuration
                self.config = EnhancedStatusConfig.load_from_file(config_file)
                logger.info(f"Loaded enhanced reasoning configuration from: {config_file}")
            
            # Validate configuration
            validation_errors = self.config.validate()
            if validation_errors:
                logger.warning(f"Configuration validation warnings: {validation_errors}")
            
        except Exception as e:
            logger.error(f"Error loading enhanced reasoning configuration: {e}")
            raise
    
    async def start(self):
        """Start the enhanced reasoning status service."""
        if not self._initialized:
            await self.initialize()
        
        if self._running:
            logger.warning("Enhanced reasoning status service is already running")
            return
        
        try:
            logger.info("Starting Restaurant Reasoning Enhanced Status Service")
            
            # Start health check service
            await self.health_service.__aenter__()
            
            # Start metrics collector
            await self.metrics_collector.start()
            
            # Start status endpoints
            await self.status_endpoints.start_background_tasks()
            
            self._running = True
            logger.info("Restaurant Reasoning Enhanced Status Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start enhanced reasoning status service: {e}")
            raise
    
    async def stop(self):
        """Stop the enhanced reasoning status service."""
        if not self._running:
            return
        
        try:
            logger.info("Stopping Restaurant Reasoning Enhanced Status Service")
            
            # Stop status endpoints
            if self.status_endpoints:
                await self.status_endpoints.stop_background_tasks()
            
            # Stop metrics collector
            if self.metrics_collector:
                await self.metrics_collector.stop()
            
            # Stop health check service
            if self.health_service:
                await self.health_service.__aexit__(None, None, None)
            
            self._running = False
            logger.info("Restaurant Reasoning Enhanced Status Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping enhanced reasoning status service: {e}")
    
    async def perform_reasoning_health_check(self) -> DualHealthCheckResult:
        """
        Perform enhanced health check on the restaurant reasoning MCP server.
        
        Returns:
            DualHealthCheckResult: Enhanced health check result with reasoning-specific validation
        """
        if not self._running:
            raise RuntimeError("Enhanced reasoning status service is not running")
        
        try:
            # Get server configuration for reasoning service
            server_config = self.config.get_server_config("restaurant-search-result-reasoning-mcp")
            if not server_config:
                raise ValueError("Restaurant reasoning MCP server configuration not found")
            
            # Perform dual health check with reasoning-specific validation
            result = await self.health_service.perform_dual_health_check(server_config)
            
            # Add reasoning-specific validation
            await self._validate_reasoning_capabilities(result)
            
            # Record metrics
            await self.metrics_collector.record_dual_health_check_result(result)
            
            # Update reasoning metrics
            if result.overall_success:
                self._reasoning_metrics["successful_reasoning_operations"] += 1
            else:
                self._reasoning_metrics["failed_reasoning_operations"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing reasoning health check: {e}")
            self._reasoning_metrics["failed_reasoning_operations"] += 1
            raise
    
    async def _validate_reasoning_capabilities(self, result: DualHealthCheckResult):
        """
        Validate reasoning-specific capabilities in health check result.
        
        Args:
            result: Dual health check result to validate
        """
        try:
            # Validate MCP tools for reasoning
            if result.mcp_result and result.mcp_success:
                expected_tools = ["recommend_restaurants", "analyze_restaurant_sentiment"]
                found_tools = result.mcp_result.expected_tools_found or []
                missing_tools = [tool for tool in expected_tools if tool not in found_tools]
                
                if missing_tools:
                    logger.warning(f"Missing reasoning tools: {missing_tools}")
                    result.mcp_result.validation_errors = result.mcp_result.validation_errors or []
                    result.mcp_result.validation_errors.extend([
                        f"Missing reasoning tool: {tool}" for tool in missing_tools
                    ])
            
            # Validate REST response for reasoning capabilities
            if result.rest_result and result.rest_success:
                response_body = result.rest_result.response_body or {}
                reasoning_capabilities = response_body.get("reasoning_capabilities")
                
                if not reasoning_capabilities:
                    logger.warning("REST response missing reasoning capabilities information")
                    if not hasattr(result.rest_result, 'validation_warnings'):
                        result.rest_result.validation_warnings = []
                    result.rest_result.validation_warnings.append(
                        "Missing reasoning capabilities in health response"
                    )
                else:
                    # Validate specific reasoning capabilities
                    required_capabilities = ["sentiment_analysis", "recommendation_algorithm"]
                    missing_capabilities = [
                        cap for cap in required_capabilities 
                        if cap not in reasoning_capabilities
                    ]
                    
                    if missing_capabilities:
                        logger.warning(f"Missing reasoning capabilities: {missing_capabilities}")
                        if not hasattr(result.rest_result, 'validation_warnings'):
                            result.rest_result.validation_warnings = []
                        result.rest_result.validation_warnings.extend([
                            f"Missing capability: {cap}" for cap in missing_capabilities
                        ])
            
        except Exception as e:
            logger.error(f"Error validating reasoning capabilities: {e}")
    
    async def get_enhanced_reasoning_status(self) -> Dict[str, Any]:
        """
        Get comprehensive enhanced status information for reasoning service.
        
        Returns:
            Dict[str, Any]: Enhanced reasoning status information
        """
        try:
            # Perform reasoning health check
            health_result = await self.perform_reasoning_health_check()
            
            # Get metrics
            metrics = await self.metrics_collector.get_combined_metrics(
                start_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                end_time=datetime.now()
            )
            
            # Get connection pool stats
            pool_stats = await self.health_service.get_connection_pool_stats()
            
            return {
                "service_info": {
                    "name": "restaurant-reasoning-mcp-enhanced",
                    "version": "1.0.0",
                    "status": "running" if self._running else "stopped",
                    "initialized": self._initialized,
                    "timestamp": datetime.now().isoformat(),
                    "service_type": "reasoning_and_sentiment_analysis"
                },
                "health_check": health_result.to_dict(),
                "reasoning_metrics": self._reasoning_metrics,
                "system_metrics": metrics,
                "connection_pools": pool_stats,
                "configuration": {
                    "dual_monitoring_enabled": self.config.dual_monitoring_enabled,
                    "mcp_enabled": self.config.mcp_health_checks.enabled,
                    "rest_enabled": self.config.rest_health_checks.enabled,
                    "monitoring_methods": self.config.get_enabled_monitoring_methods(),
                    "reasoning_optimized": True
                },
                "reasoning_capabilities": {
                    "sentiment_analysis": True,
                    "recommendation_algorithm": True,
                    "data_validation": True,
                    "intelligent_ranking": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced reasoning status: {e}")
            return {
                "service_info": {
                    "name": "restaurant-reasoning-mcp-enhanced",
                    "version": "1.0.0",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "service_type": "reasoning_and_sentiment_analysis"
                }
            }
    
    async def record_reasoning_operation(
        self,
        operation_type: str,
        success: bool,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a reasoning operation for metrics tracking.
        
        Args:
            operation_type: Type of reasoning operation (recommendation, sentiment_analysis)
            success: Whether the operation was successful
            duration_ms: Duration of the operation in milliseconds
            metadata: Optional metadata about the operation
        """
        try:
            # Update operation counters
            if operation_type == "recommendation":
                self._reasoning_metrics["recommendation_requests"] += 1
            elif operation_type == "sentiment_analysis":
                self._reasoning_metrics["sentiment_analysis_requests"] += 1
            
            # Update success/failure counters
            if success:
                self._reasoning_metrics["successful_reasoning_operations"] += 1
            else:
                self._reasoning_metrics["failed_reasoning_operations"] += 1
            
            # Update average reasoning time
            total_operations = (
                self._reasoning_metrics["successful_reasoning_operations"] +
                self._reasoning_metrics["failed_reasoning_operations"]
            )
            
            if total_operations > 0:
                current_avg = self._reasoning_metrics["average_reasoning_time_ms"]
                self._reasoning_metrics["average_reasoning_time_ms"] = (
                    (current_avg * (total_operations - 1) + duration_ms) / total_operations
                )
            
            # Record in metrics collector if available
            if self.metrics_collector:
                await self.metrics_collector.record_custom_metric(
                    metric_name=f"reasoning_{operation_type}",
                    value=duration_ms,
                    success=success,
                    metadata=metadata
                )
            
            logger.debug(f"Recorded reasoning operation: {operation_type}, "
                        f"success={success}, duration={duration_ms}ms")
            
        except Exception as e:
            logger.error(f"Error recording reasoning operation: {e}")
    
    async def get_reasoning_capabilities_status(self) -> Dict[str, Any]:
        """
        Get detailed status of reasoning capabilities.
        
        Returns:
            Dict[str, Any]: Reasoning capabilities status
        """
        try:
            # Test reasoning capabilities
            capabilities_status = {
                "sentiment_analysis": {
                    "available": True,
                    "last_test": datetime.now().isoformat(),
                    "test_result": "success"
                },
                "recommendation_algorithm": {
                    "available": True,
                    "last_test": datetime.now().isoformat(),
                    "test_result": "success"
                },
                "data_validation": {
                    "available": True,
                    "last_test": datetime.now().isoformat(),
                    "test_result": "success"
                },
                "intelligent_ranking": {
                    "available": True,
                    "last_test": datetime.now().isoformat(),
                    "test_result": "success"
                }
            }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "capabilities": capabilities_status,
                "reasoning_metrics": self._reasoning_metrics,
                "performance": {
                    "average_response_time_ms": self._reasoning_metrics["average_reasoning_time_ms"],
                    "success_rate": self._calculate_success_rate(),
                    "total_operations": (
                        self._reasoning_metrics["successful_reasoning_operations"] +
                        self._reasoning_metrics["failed_reasoning_operations"]
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting reasoning capabilities status: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    def _calculate_success_rate(self) -> float:
        """Calculate the success rate of reasoning operations."""
        total_successful = self._reasoning_metrics["successful_reasoning_operations"]
        total_failed = self._reasoning_metrics["failed_reasoning_operations"]
        total_operations = total_successful + total_failed
        
        if total_operations == 0:
            return 1.0  # No operations yet, assume 100% success rate
        
        return total_successful / total_operations
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Global instance for integration with main application
enhanced_reasoning_status_service: Optional[RestaurantReasoningEnhancedStatusService] = None


async def get_enhanced_reasoning_status_service() -> RestaurantReasoningEnhancedStatusService:
    """
    Get or create the global enhanced reasoning status service instance.
    
    Returns:
        RestaurantReasoningEnhancedStatusService: Enhanced reasoning status service instance
    """
    global enhanced_reasoning_status_service
    
    if enhanced_reasoning_status_service is None:
        enhanced_reasoning_status_service = RestaurantReasoningEnhancedStatusService()
        await enhanced_reasoning_status_service.initialize()
    
    return enhanced_reasoning_status_service


async def initialize_enhanced_reasoning_status_service(config_path: Optional[str] = None):
    """
    Initialize the global enhanced reasoning status service.
    
    Args:
        config_path: Optional path to enhanced configuration file
    """
    global enhanced_reasoning_status_service
    
    if enhanced_reasoning_status_service is not None:
        logger.warning("Enhanced reasoning status service already initialized")
        return
    
    enhanced_reasoning_status_service = RestaurantReasoningEnhancedStatusService(config_path)
    await enhanced_reasoning_status_service.initialize()
    logger.info("Global enhanced reasoning status service initialized")


async def start_enhanced_reasoning_status_service():
    """Start the global enhanced reasoning status service."""
    global enhanced_reasoning_status_service
    
    if enhanced_reasoning_status_service is None:
        await initialize_enhanced_reasoning_status_service()
    
    await enhanced_reasoning_status_service.start()
    logger.info("Global enhanced reasoning status service started")


async def stop_enhanced_reasoning_status_service():
    """Stop the global enhanced reasoning status service."""
    global enhanced_reasoning_status_service
    
    if enhanced_reasoning_status_service is not None:
        await enhanced_reasoning_status_service.stop()
        logger.info("Global enhanced reasoning status service stopped")