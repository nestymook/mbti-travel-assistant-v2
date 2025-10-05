"""
Enhanced Status Service for Restaurant Search MCP

This module integrates the enhanced MCP status check system with the restaurant search MCP server,
providing dual monitoring capabilities with MCP tools/list and REST health checks.
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


class RestaurantSearchEnhancedStatusService:
    """
    Enhanced Status Service for Restaurant Search MCP.
    
    Integrates enhanced dual monitoring capabilities with the restaurant search MCP server,
    providing comprehensive health monitoring using both MCP tools/list requests and REST API checks.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Enhanced Status Service.
        
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
        
    async def initialize(self):
        """Initialize the enhanced status service."""
        try:
            logger.info("Initializing Restaurant Search Enhanced Status Service")
            
            # Load enhanced configuration
            await self._load_enhanced_config()
            
            # Initialize metrics collector
            self.metrics_collector = DualMetricsCollector(
                retention_hours=self.config.monitoring.metrics_retention_hours
            )
            
            # Initialize health check service
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
            logger.info("Restaurant Search Enhanced Status Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced status service: {e}")
            raise
    
    async def _load_enhanced_config(self):
        """Load enhanced status configuration."""
        try:
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                logger.warning(f"Enhanced config file not found: {config_file}")
                # Create default configuration
                self.config = EnhancedStatusConfig.create_default()
                self.config.system_name = "restaurant-search-mcp-enhanced"
                
                # Add default server configuration
                server_config = EnhancedServerConfig(
                    server_name="restaurant-search-mcp",
                    mcp_endpoint_url="https://your-gateway-url/mcp/restaurant-search-mcp",
                    mcp_expected_tools=[
                        "search_restaurants_by_district",
                        "search_restaurants_by_meal_type",
                        "search_restaurants_combined"
                    ],
                    rest_health_endpoint_url="https://your-gateway-url/mcp/restaurant-search-mcp/status/health",
                    priority="high",
                    description="Core restaurant search functionality with enhanced dual monitoring"
                )
                self.config.add_server(server_config)
                
                # Save default configuration
                self.config.save_to_file(config_file)
                logger.info(f"Created default enhanced configuration: {config_file}")
            else:
                # Load existing configuration
                self.config = EnhancedStatusConfig.load_from_file(config_file)
                logger.info(f"Loaded enhanced configuration from: {config_file}")
            
            # Validate configuration
            validation_errors = self.config.validate()
            if validation_errors:
                logger.warning(f"Configuration validation warnings: {validation_errors}")
            
        except Exception as e:
            logger.error(f"Error loading enhanced configuration: {e}")
            raise
    
    async def start(self):
        """Start the enhanced status service."""
        if not self._initialized:
            await self.initialize()
        
        if self._running:
            logger.warning("Enhanced status service is already running")
            return
        
        try:
            logger.info("Starting Restaurant Search Enhanced Status Service")
            
            # Start health check service
            await self.health_service.__aenter__()
            
            # Start metrics collector
            await self.metrics_collector.start()
            
            # Start status endpoints
            await self.status_endpoints.start_background_tasks()
            
            self._running = True
            logger.info("Restaurant Search Enhanced Status Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start enhanced status service: {e}")
            raise
    
    async def stop(self):
        """Stop the enhanced status service."""
        if not self._running:
            return
        
        try:
            logger.info("Stopping Restaurant Search Enhanced Status Service")
            
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
            logger.info("Restaurant Search Enhanced Status Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping enhanced status service: {e}")
    
    async def perform_self_health_check(self) -> DualHealthCheckResult:
        """
        Perform enhanced health check on the restaurant search MCP server itself.
        
        Returns:
            DualHealthCheckResult: Enhanced health check result
        """
        if not self._running:
            raise RuntimeError("Enhanced status service is not running")
        
        try:
            # Get server configuration for self
            server_config = self.config.get_server_config("restaurant-search-mcp")
            if not server_config:
                raise ValueError("Restaurant search MCP server configuration not found")
            
            # Perform dual health check
            result = await self.health_service.perform_dual_health_check(server_config)
            
            # Record metrics
            await self.metrics_collector.record_dual_health_check_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing self health check: {e}")
            raise
    
    async def get_enhanced_status(self) -> Dict[str, Any]:
        """
        Get comprehensive enhanced status information.
        
        Returns:
            Dict[str, Any]: Enhanced status information
        """
        try:
            # Perform self health check
            health_result = await self.perform_self_health_check()
            
            # Get metrics
            metrics = await self.metrics_collector.get_combined_metrics(
                start_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                end_time=datetime.now()
            )
            
            # Get connection pool stats
            pool_stats = await self.health_service.get_connection_pool_stats()
            
            return {
                "service_info": {
                    "name": "restaurant-search-mcp-enhanced",
                    "version": "1.0.0",
                    "status": "running" if self._running else "stopped",
                    "initialized": self._initialized,
                    "timestamp": datetime.now().isoformat()
                },
                "health_check": health_result.to_dict(),
                "metrics": metrics,
                "connection_pools": pool_stats,
                "configuration": {
                    "dual_monitoring_enabled": self.config.dual_monitoring_enabled,
                    "mcp_enabled": self.config.mcp_health_checks.enabled,
                    "rest_enabled": self.config.rest_health_checks.enabled,
                    "monitoring_methods": self.config.get_enabled_monitoring_methods()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced status: {e}")
            return {
                "service_info": {
                    "name": "restaurant-search-mcp-enhanced",
                    "version": "1.0.0",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def update_server_configuration(
        self,
        server_name: str,
        config_updates: Dict[str, Any]
    ) -> bool:
        """
        Update server configuration at runtime.
        
        Args:
            server_name: Name of the server to update
            config_updates: Configuration updates to apply
            
        Returns:
            bool: True if update was successful
        """
        try:
            server_config = self.config.get_server_config(server_name)
            if not server_config:
                logger.error(f"Server configuration not found: {server_name}")
                return False
            
            # Apply updates
            for key, value in config_updates.items():
                if hasattr(server_config, key):
                    setattr(server_config, key, value)
                    logger.info(f"Updated {server_name}.{key} = {value}")
                else:
                    logger.warning(f"Unknown configuration key: {key}")
            
            # Validate updated configuration
            validation_errors = server_config.validate()
            if validation_errors:
                logger.error(f"Configuration validation failed: {validation_errors}")
                return False
            
            # Save updated configuration
            config_file = Path(self.config_path)
            self.config.save_to_file(config_file)
            
            logger.info(f"Successfully updated configuration for {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating server configuration: {e}")
            return False
    
    async def get_monitoring_capabilities(self) -> Dict[str, Any]:
        """
        Get information about monitoring capabilities.
        
        Returns:
            Dict[str, Any]: Monitoring capabilities information
        """
        return {
            "dual_monitoring": {
                "enabled": self.config.dual_monitoring_enabled if self.config else False,
                "description": "Concurrent MCP tools/list and REST health checks"
            },
            "mcp_monitoring": {
                "enabled": self.config.mcp_health_checks.enabled if self.config else False,
                "tools_validation": self.config.mcp_health_checks.tools_list_validation if self.config else False,
                "expected_tools": self.config.mcp_health_checks.default_expected_tools if self.config else [],
                "jwt_auth": self.config.mcp_health_checks.jwt_auth_enabled if self.config else False
            },
            "rest_monitoring": {
                "enabled": self.config.rest_health_checks.enabled if self.config else False,
                "health_endpoint": self.config.rest_health_checks.health_endpoint_path if self.config else "/status/health",
                "metrics_endpoint": self.config.rest_health_checks.metrics_endpoint_path if self.config else "/status/metrics",
                "response_validation": self.config.rest_health_checks.validate_response_format if self.config else False
            },
            "aggregation": {
                "mcp_weight": self.config.result_aggregation.mcp_priority_weight if self.config else 0.6,
                "rest_weight": self.config.result_aggregation.rest_priority_weight if self.config else 0.4,
                "calculation_method": self.config.result_aggregation.health_score_calculation if self.config else "weighted_average"
            },
            "circuit_breaker": {
                "enabled": self.config.circuit_breaker.enabled if self.config else False,
                "independent_paths": self.config.circuit_breaker.independent_circuit_breakers if self.config else False,
                "failure_threshold": self.config.circuit_breaker.failure_threshold if self.config else 5
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Global instance for integration with main application
enhanced_status_service: Optional[RestaurantSearchEnhancedStatusService] = None


async def get_enhanced_status_service() -> RestaurantSearchEnhancedStatusService:
    """
    Get or create the global enhanced status service instance.
    
    Returns:
        RestaurantSearchEnhancedStatusService: Enhanced status service instance
    """
    global enhanced_status_service
    
    if enhanced_status_service is None:
        enhanced_status_service = RestaurantSearchEnhancedStatusService()
        await enhanced_status_service.initialize()
    
    return enhanced_status_service


async def initialize_enhanced_status_service(config_path: Optional[str] = None):
    """
    Initialize the global enhanced status service.
    
    Args:
        config_path: Optional path to enhanced configuration file
    """
    global enhanced_status_service
    
    if enhanced_status_service is not None:
        logger.warning("Enhanced status service already initialized")
        return
    
    enhanced_status_service = RestaurantSearchEnhancedStatusService(config_path)
    await enhanced_status_service.initialize()
    logger.info("Global enhanced status service initialized")


async def start_enhanced_status_service():
    """Start the global enhanced status service."""
    global enhanced_status_service
    
    if enhanced_status_service is None:
        await initialize_enhanced_status_service()
    
    await enhanced_status_service.start()
    logger.info("Global enhanced status service started")


async def stop_enhanced_status_service():
    """Stop the global enhanced status service."""
    global enhanced_status_service
    
    if enhanced_status_service is not None:
        await enhanced_status_service.stop()
        logger.info("Global enhanced status service stopped")