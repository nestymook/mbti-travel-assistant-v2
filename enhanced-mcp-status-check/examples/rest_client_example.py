"""
REST Health Check Client Example

This example demonstrates how to use the REST Health Check Client
for performing HTTP health checks on MCP server endpoints.
"""

import asyncio
import json
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rest_health_check_client import RESTHealthCheckClient
from models.dual_health_models import EnhancedServerConfig


async def basic_rest_health_check_example():
    """Basic example of REST health check."""
    print("=== Basic REST Health Check Example ===")
    
    # Create server configuration
    server_config = EnhancedServerConfig(
        server_name="example-server",
        mcp_endpoint_url="http://localhost:8080/mcp",
        rest_health_endpoint_url="http://localhost:8080/status/health",
        rest_enabled=True,
        rest_timeout_seconds=10,
        rest_retry_attempts=3,
        jwt_token="your-jwt-token-here",
        auth_headers={"X-API-Key": "your-api-key"}
    )
    
    # Create REST health check client
    async with RESTHealthCheckClient() as client:
        try:
            # Perform health check
            result = await client.perform_rest_health_check(server_config)
            
            print(f"Server: {result.server_name}")
            print(f"Success: {result.success}")
            print(f"Status Code: {result.status_code}")
            print(f"Response Time: {result.response_time_ms:.2f}ms")
            
            if result.success:
                print("✅ Health check passed!")
                if result.server_metrics:
                    print(f"Server Metrics: {json.dumps(result.server_metrics, indent=2)}")
            else:
                print("❌ Health check failed!")
                if result.http_error:
                    print(f"HTTP Error: {result.http_error}")
                if result.connection_error:
                    print(f"Connection Error: {result.connection_error}")
                    
        except Exception as e:
            print(f"Error performing health check: {e}")


async def multiple_servers_example():
    """Example of checking multiple servers concurrently."""
    print("\n=== Multiple Servers Health Check Example ===")
    
    # Create multiple server configurations
    server_configs = [
        EnhancedServerConfig(
            server_name="restaurant-search-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            rest_enabled=True
        ),
        EnhancedServerConfig(
            server_name="restaurant-reasoning-server",
            mcp_endpoint_url="http://localhost:8081/mcp",
            rest_health_endpoint_url="http://localhost:8081/status/health",
            rest_enabled=True
        ),
        EnhancedServerConfig(
            server_name="mbti-travel-server",
            mcp_endpoint_url="http://localhost:8082/mcp",
            rest_health_endpoint_url="http://localhost:8082/status/health",
            rest_enabled=True
        )
    ]
    
    # Create REST health check client
    async with RESTHealthCheckClient() as client:
        try:
            # Check multiple servers concurrently
            results = await client.check_multiple_servers_rest(
                server_configs, 
                max_concurrent=3
            )
            
            print(f"Checked {len(results)} servers:")
            for result in results:
                status_icon = "✅" if result.success else "❌"
                print(f"{status_icon} {result.server_name}: "
                      f"{'HEALTHY' if result.success else 'UNHEALTHY'} "
                      f"({result.response_time_ms:.2f}ms)")
                
                if not result.success:
                    if result.http_error:
                        print(f"   HTTP Error: {result.http_error}")
                    if result.connection_error:
                        print(f"   Connection Error: {result.connection_error}")
                        
        except Exception as e:
            print(f"Error checking multiple servers: {e}")


async def retry_logic_example():
    """Example demonstrating retry logic with exponential backoff."""
    print("\n=== Retry Logic Example ===")
    
    async with RESTHealthCheckClient() as client:
        try:
            # This will likely fail and demonstrate retry logic
            response = await client.perform_rest_health_check_with_retry(
                health_endpoint_url="http://localhost:9999/status/health",  # Non-existent server
                timeout=2,
                max_retries=3,
                backoff_factor=1.0
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Time: {response.response_time_ms:.2f}ms")
            
        except Exception as e:
            print(f"All retry attempts failed: {e}")
            print("This demonstrates the retry logic with exponential backoff")


def validation_example():
    """Example of response validation."""
    print("\n=== Response Validation Example ===")
    
    client = RESTHealthCheckClient()
    
    # Example of healthy response
    from models.dual_health_models import RESTHealthCheckResponse
    
    healthy_response = RESTHealthCheckResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "uptime": 3600,
                "memory_usage": 0.75,
                "cpu_usage": 0.25,
                "request_count": 1000,
                "error_count": 5
            },
            "circuit_breaker": {
                "state": "CLOSED",
                "failure_count": 0
            }
        },
        response_time_ms=45.0,
        url="http://localhost:8080/status/health"
    )
    
    # Validate the response
    validation_result = client.validate_rest_response(healthy_response)
    
    print("Healthy Response Validation:")
    print(f"  Valid: {validation_result.is_valid}")
    print(f"  HTTP Status Valid: {validation_result.http_status_valid}")
    print(f"  Response Format Valid: {validation_result.response_format_valid}")
    print(f"  Health Indicators Present: {validation_result.health_indicators_present}")
    print(f"  Validation Errors: {validation_result.validation_errors}")
    
    # Example of unhealthy response
    unhealthy_response = RESTHealthCheckResponse(
        status_code=503,
        headers={"Content-Type": "application/json"},
        body={
            "status": "unhealthy",
            "error": "Database connection failed",
            "timestamp": datetime.now().isoformat()
        },
        response_time_ms=1200.0,
        url="http://localhost:8080/status/health"
    )
    
    # Validate the unhealthy response
    validation_result = client.validate_rest_response(unhealthy_response)
    
    print("\nUnhealthy Response Validation:")
    print(f"  Valid: {validation_result.is_valid}")
    print(f"  HTTP Status Valid: {validation_result.http_status_valid}")
    print(f"  Response Format Valid: {validation_result.response_format_valid}")
    print(f"  Health Indicators Present: {validation_result.health_indicators_present}")
    print(f"  Validation Errors: {validation_result.validation_errors}")
    
    # Determine health status
    health_status = client.determine_health_status(unhealthy_response, validation_result)
    print(f"  Determined Health Status: {health_status}")


def metrics_extraction_example():
    """Example of extracting health metrics."""
    print("\n=== Metrics Extraction Example ===")
    
    client = RESTHealthCheckClient()
    
    # Example response body with various metric patterns
    response_body = {
        "status": "healthy",
        "uptime": 7200,  # 2 hours
        "memory": 0.68,
        "cpu_usage": 0.15,
        "requests": 5000,
        "errors": 12,
        "metrics": {
            "avg_response_time": 85.5,
            "active_connections": 25,
            "cache_hit_rate": 0.92
        },
        "stats": {
            "database_connections": 8,
            "queue_size": 3
        },
        "system": {
            "version": "1.2.3",
            "environment": "production"
        }
    }
    
    # Extract metrics
    metrics = client.extract_health_metrics(response_body)
    
    print("Extracted Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")


async def main():
    """Run all examples."""
    print("REST Health Check Client Examples")
    print("=" * 50)
    
    # Run validation and metrics examples (synchronous)
    validation_example()
    metrics_extraction_example()
    
    # Run async examples
    await basic_rest_health_check_example()
    await multiple_servers_example()
    await retry_logic_example()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: Some examples may fail if the target servers are not running.")
    print("This is expected and demonstrates error handling capabilities.")


if __name__ == "__main__":
    asyncio.run(main())