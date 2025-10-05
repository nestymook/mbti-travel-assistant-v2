"""
Enhanced REST API Endpoints Example

This example demonstrates how to use the enhanced REST API endpoints
for dual monitoring with MCP and REST health checks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
import aiohttp
import json

from api.enhanced_status_endpoints import (
    create_enhanced_status_app,
    EnhancedStatusEndpoints,
    HealthCheckRequest
)
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.enhanced_status_config import EnhancedStatusConfig
from models.dual_health_models import (
    EnhancedServerConfig,
    AggregationConfig,
    PriorityConfig
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedAPIExample:
    """
    Example class demonstrating enhanced REST API endpoints usage.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize API example.
        
        Args:
            base_url: Base URL for the API server
        """
        self.base_url = base_url
        self.session: aiohttp.ClientSession = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def demonstrate_system_health_endpoint(self):
        """Demonstrate enhanced /status/health endpoint."""
        logger.info("=== Enhanced System Health Endpoint ===")
        
        # Basic system health check
        url = f"{self.base_url}/status/health"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"System Status: {data['overall_status']}")
                logger.info(f"Total Servers: {data['total_servers']}")
                logger.info(f"Healthy: {data['healthy_servers']}, "
                           f"Degraded: {data['degraded_servers']}, "
                           f"Unhealthy: {data['unhealthy_servers']}")
                logger.info(f"Average Health Score: {data['average_health_score']:.3f}")
                logger.info(f"Average Response Time: {data['average_response_time_ms']:.2f}ms")
                
                if data.get('servers'):
                    logger.info("Server Details:")
                    for server in data['servers']:
                        logger.info(f"  - {server['server_name']}: {server['status']} "
                                   f"(Score: {server['health_score']:.3f})")
            else:
                logger.error(f"Failed to get system health: {response.status}")
        
        # Force new health check
        url = f"{self.base_url}/status/health?force_check=true&timeout=60"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Forced check completed at: {data['last_check_timestamp']}")
            else:
                logger.error(f"Failed to force health check: {response.status}")
    
    async def demonstrate_server_status_endpoint(self, server_name: str = "test-server-1"):
        """Demonstrate enhanced /status/servers/{server_name} endpoint."""
        logger.info(f"=== Enhanced Server Status Endpoint for {server_name} ===")
        
        url = f"{self.base_url}/status/servers/{server_name}"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Server: {data['server_name']}")
                logger.info(f"Status: {data['status']}")
                logger.info(f"Success: {data['success']}")
                logger.info(f"Health Score: {data['health_score']:.3f}")
                logger.info(f"Available Paths: {data['available_paths']}")
                
                # MCP Results
                if data.get('mcp_result'):
                    mcp = data['mcp_result']
                    logger.info(f"MCP Check: Success={mcp['success']}, "
                               f"Response Time={mcp['response_time_ms']:.2f}ms")
                    if mcp.get('tools_count'):
                        logger.info(f"  Tools Available: {mcp['tools_count']}")
                    if mcp.get('expected_tools_found'):
                        logger.info(f"  Expected Tools Found: {mcp['expected_tools_found']}")
                
                # REST Results
                if data.get('rest_result'):
                    rest = data['rest_result']
                    logger.info(f"REST Check: Success={rest['success']}, "
                               f"Status Code={rest.get('status_code')}, "
                               f"Response Time={rest['response_time_ms']:.2f}ms")
                
                # Combined Metrics
                if data.get('combined_metrics'):
                    metrics = data['combined_metrics']
                    logger.info(f"Combined Response Time: {metrics['combined_response_time_ms']:.2f}ms")
                    logger.info(f"Tools Availability: {metrics['tools_availability_percentage']:.1f}%")
                
                if data.get('error_message'):
                    logger.warning(f"Error: {data['error_message']}")
            
            elif response.status == 404:
                logger.error(f"Server '{server_name}' not found")
            else:
                logger.error(f"Failed to get server status: {response.status}")
    
    async def demonstrate_metrics_endpoint(self):
        """Demonstrate enhanced /status/metrics endpoint."""
        logger.info("=== Enhanced Metrics Endpoint ===")
        
        # Get metrics for last hour with server breakdown
        url = f"{self.base_url}/status/metrics?time_range=3600&include_server_breakdown=true"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                # MCP Metrics
                mcp_metrics = data['mcp_metrics']
                logger.info("MCP Metrics:")
                logger.info(f"  Total Requests: {mcp_metrics.get('total_requests', 0)}")
                logger.info(f"  Successful: {mcp_metrics.get('successful_requests', 0)}")
                logger.info(f"  Failed: {mcp_metrics.get('failed_requests', 0)}")
                logger.info(f"  Avg Response Time: {mcp_metrics.get('average_response_time_ms', 0):.2f}ms")
                
                # REST Metrics
                rest_metrics = data['rest_metrics']
                logger.info("REST Metrics:")
                logger.info(f"  Total Requests: {rest_metrics.get('total_requests', 0)}")
                logger.info(f"  Successful: {rest_metrics.get('successful_requests', 0)}")
                logger.info(f"  Failed: {rest_metrics.get('failed_requests', 0)}")
                logger.info(f"  Avg Response Time: {rest_metrics.get('average_response_time_ms', 0):.2f}ms")
                
                # Combined Metrics
                combined_metrics = data['combined_metrics']
                logger.info("Combined Metrics:")
                logger.info(f"  Total Dual Checks: {combined_metrics.get('total_dual_checks', 0)}")
                logger.info(f"  Both Successful: {combined_metrics.get('both_successful', 0)}")
                logger.info(f"  MCP Only: {combined_metrics.get('mcp_only_successful', 0)}")
                logger.info(f"  REST Only: {combined_metrics.get('rest_only_successful', 0)}")
                
                # Server Breakdown
                if data.get('server_metrics'):
                    logger.info("Per-Server Metrics:")
                    for server_name, server_metrics in data['server_metrics'].items():
                        logger.info(f"  {server_name}:")
                        mcp_server = server_metrics.get('mcp_metrics', {})
                        rest_server = server_metrics.get('rest_metrics', {})
                        logger.info(f"    MCP Success Rate: {mcp_server.get('success_rate', 0):.2f}")
                        logger.info(f"    REST Success Rate: {rest_server.get('success_rate', 0):.2f}")
            else:
                logger.error(f"Failed to get metrics: {response.status}")
    
    async def demonstrate_dual_check_endpoint(self):
        """Demonstrate enhanced /status/dual-check endpoint."""
        logger.info("=== Enhanced Dual Check Endpoint ===")
        
        # Trigger manual dual health check
        request_data = {
            "server_names": ["test-server-1", "test-server-2"],
            "timeout_seconds": 30,
            "include_mcp": True,
            "include_rest": True
        }
        
        url = f"{self.base_url}/status/dual-check"
        async with self.session.post(url, json=request_data) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Check ID: {data['check_id']}")
                logger.info(f"Timestamp: {data['timestamp']}")
                
                # Summary
                summary = data['summary']
                logger.info("Summary:")
                logger.info(f"  Total Servers: {summary['total_servers']}")
                logger.info(f"  Healthy: {summary['healthy_servers']}")
                logger.info(f"  Degraded: {summary['degraded_servers']}")
                logger.info(f"  Unhealthy: {summary['unhealthy_servers']}")
                logger.info(f"  Average Health Score: {summary['average_health_score']:.3f}")
                
                # Individual Server Results
                logger.info("Server Results:")
                for server in data['servers']:
                    logger.info(f"  {server['server_name']}: {server['status']} "
                               f"(Score: {server['health_score']:.3f})")
            else:
                logger.error(f"Failed to trigger dual check: {response.status}")
        
        # Trigger check with only MCP monitoring
        request_data_mcp_only = {
            "timeout_seconds": 20,
            "include_mcp": True,
            "include_rest": False
        }
        
        async with self.session.post(url, json=request_data_mcp_only) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"MCP-only check completed: {data['check_id']}")
                logger.info(f"Servers checked: {len(data['servers'])}")
            else:
                logger.error(f"Failed to trigger MCP-only check: {response.status}")
    
    async def demonstrate_config_endpoint(self):
        """Demonstrate enhanced /status/config endpoint."""
        logger.info("=== Enhanced Configuration Endpoint ===")
        
        # Get current configuration
        url = f"{self.base_url}/status/config"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Enhanced Monitoring Enabled: {data['enhanced_monitoring_enabled']}")
                
                # MCP Configuration
                mcp_config = data['mcp_health_checks']
                logger.info("MCP Health Checks:")
                logger.info(f"  Enabled: {mcp_config.get('enabled')}")
                logger.info(f"  Default Timeout: {mcp_config.get('default_timeout_seconds')}s")
                logger.info(f"  Tools Validation: {mcp_config.get('tools_list_validation')}")
                
                # REST Configuration
                rest_config = data['rest_health_checks']
                logger.info("REST Health Checks:")
                logger.info(f"  Enabled: {rest_config.get('enabled')}")
                logger.info(f"  Default Timeout: {rest_config.get('default_timeout_seconds')}s")
                logger.info(f"  Health Endpoint Path: {rest_config.get('health_endpoint_path')}")
                
                # Aggregation Configuration
                aggregation = data['result_aggregation']
                logger.info("Result Aggregation:")
                logger.info(f"  MCP Priority Weight: {aggregation.get('mcp_priority_weight')}")
                logger.info(f"  REST Priority Weight: {aggregation.get('rest_priority_weight')}")
                
                # Server Configurations
                logger.info(f"Configured Servers: {len(data['servers'])}")
                for server in data['servers']:
                    logger.info(f"  - {server['server_name']}")
                    logger.info(f"    MCP Enabled: {server.get('mcp_enabled')}")
                    logger.info(f"    REST Enabled: {server.get('rest_enabled')}")
            else:
                logger.error(f"Failed to get configuration: {response.status}")
        
        # Update configuration
        config_update = {
            "mcp_health_checks": {
                "default_timeout_seconds": 15
            },
            "rest_health_checks": {
                "default_timeout_seconds": 10
            }
        }
        
        async with self.session.put(url, json=config_update) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Configuration update: {data['message']}")
                logger.info(f"Updated fields: {data['updated_fields']}")
            else:
                logger.error(f"Failed to update configuration: {response.status}")
    
    async def demonstrate_legacy_endpoints(self):
        """Demonstrate legacy endpoints for backward compatibility."""
        logger.info("=== Legacy Endpoints (Backward Compatibility) ===")
        
        # Legacy /health endpoint
        url = f"{self.base_url}/health"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info("Legacy /health endpoint:")
                logger.info(f"  Status: {data['status']}")
                logger.info(f"  Healthy: {data['healthy']}")
                logger.info(f"  Total Servers: {data['servers']['total']}")
                logger.info(f"  Healthy Servers: {data['servers']['healthy']}")
            else:
                logger.error(f"Failed to get legacy health: {response.status}")
        
        # Legacy /status endpoint
        url = f"{self.base_url}/status"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info("Legacy /status endpoint:")
                logger.info(f"  Overall Status: {data['overall_status']}")
                logger.info(f"  Server Count: {len(data['servers'])}")
                
                for server_name, server_data in data['servers'].items():
                    logger.info(f"  {server_name}: {server_data['status']} "
                               f"(Healthy: {server_data['healthy']})")
            else:
                logger.error(f"Failed to get legacy status: {response.status}")
    
    async def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all endpoints."""
        logger.info("Starting comprehensive enhanced API demonstration...")
        
        try:
            await self.demonstrate_system_health_endpoint()
            await asyncio.sleep(1)
            
            await self.demonstrate_server_status_endpoint()
            await asyncio.sleep(1)
            
            await self.demonstrate_metrics_endpoint()
            await asyncio.sleep(1)
            
            await self.demonstrate_dual_check_endpoint()
            await asyncio.sleep(1)
            
            await self.demonstrate_config_endpoint()
            await asyncio.sleep(1)
            
            await self.demonstrate_legacy_endpoints()
            
            logger.info("Comprehensive demonstration completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during demonstration: {e}")


async def create_sample_server():
    """Create a sample server for demonstration."""
    logger.info("Creating sample enhanced status check server...")
    
    # Create sample server configurations
    server_configs = [
        EnhancedServerConfig(
            server_name="test-server-1",
            mcp_endpoint_url="http://localhost:8001/mcp",
            rest_health_endpoint_url="http://localhost:8001/status/health",
            mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
            mcp_timeout_seconds=10,
            rest_timeout_seconds=8
        ),
        EnhancedServerConfig(
            server_name="test-server-2",
            mcp_endpoint_url="http://localhost:8002/mcp",
            rest_health_endpoint_url="http://localhost:8002/status/health",
            mcp_expected_tools=["analyze_sentiment"],
            mcp_timeout_seconds=12,
            rest_timeout_seconds=6
        )
    ]
    
    # Create aggregation configuration
    priority_config = PriorityConfig(
        mcp_priority_weight=0.6,
        rest_priority_weight=0.4,
        require_both_success_for_healthy=False,
        degraded_on_single_failure=True
    )
    
    aggregation_config = AggregationConfig(
        priority_config=priority_config,
        health_score_calculation="weighted_average",
        failure_threshold=0.5,
        degraded_threshold=0.7
    )
    
    # Create services (mocked for demonstration)
    config_manager = EnhancedStatusConfig()
    await config_manager.load_server_configs(server_configs)
    
    health_service = EnhancedHealthCheckService(aggregation_config=aggregation_config)
    metrics_collector = DualMetricsCollector()
    
    # Create FastAPI app
    app = create_enhanced_status_app(
        health_service=health_service,
        metrics_collector=metrics_collector,
        config_manager=config_manager
    )
    
    logger.info("Sample server created successfully!")
    return app


async def main():
    """Main demonstration function."""
    logger.info("Enhanced MCP Status Check API Endpoints Demonstration")
    logger.info("=" * 60)
    
    # Note: This example assumes a running server
    # In a real scenario, you would start the server first
    
    async with EnhancedAPIExample() as demo:
        await demo.run_comprehensive_demo()


if __name__ == "__main__":
    asyncio.run(main())