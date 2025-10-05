#!/usr/bin/env python3
"""
Example usage of enhanced MCP status check data models.

This script demonstrates how to create, validate, and serialize
the enhanced data models for dual health checking.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.dual_health_models import (
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
from models.validation_utils import (
    ConfigurationValidator,
    validate_configuration_data
)


def create_sample_server_config() -> EnhancedServerConfig:
    """Create a sample enhanced server configuration."""
    print("Creating sample server configuration...")
    
    config = EnhancedServerConfig(
        server_name="restaurant-search-mcp",
        mcp_endpoint_url="https://api.example.com/mcp",
        rest_health_endpoint_url="https://api.example.com/status/health",
        mcp_enabled=True,
        mcp_timeout_seconds=15,
        mcp_expected_tools=[
            "search_restaurants_by_district",
            "recommend_restaurants",
            "analyze_restaurant_sentiment"
        ],
        mcp_retry_attempts=3,
        rest_enabled=True,
        rest_timeout_seconds=10,
        rest_retry_attempts=2,
        jwt_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.example.token",
        auth_headers={
            "Authorization": "Bearer example-token",
            "X-API-Key": "api-key-12345"
        },
        mcp_priority_weight=0.7,
        rest_priority_weight=0.3,
        require_both_success=False
    )
    
    print(f"✓ Created config for server: {config.server_name}")
    return config


def validate_server_config(config: EnhancedServerConfig) -> bool:
    """Validate the server configuration."""
    print("\nValidating server configuration...")
    
    errors = ConfigurationValidator.validate_enhanced_server_config(config)
    
    if errors:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ Configuration validation passed")
        return True


def create_sample_mcp_result() -> MCPHealthCheckResult:
    """Create a sample MCP health check result."""
    print("\nCreating sample MCP health check result...")
    
    # Create MCP tools/list response
    tools_response = MCPToolsListResponse(
        jsonrpc="2.0",
        id="mcp-health-check-123",
        result={
            "tools": [
                {
                    "name": "search_restaurants_by_district",
                    "description": "Search for restaurants in specific districts",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "districts": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                {
                    "name": "recommend_restaurants",
                    "description": "Get restaurant recommendations with sentiment analysis",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "restaurants": {"type": "array"}
                        }
                    }
                }
            ]
        }
    )
    
    # Create validation result
    validation_result = MCPValidationResult(
        is_valid=True,
        tools_count=2,
        expected_tools_found=["search_restaurants_by_district", "recommend_restaurants"],
        missing_tools=[],
        validation_errors=[],
        tool_schemas_valid=True
    )
    
    # Create MCP health check result
    mcp_result = MCPHealthCheckResult(
        server_name="restaurant-search-mcp",
        timestamp=datetime.now(),
        success=True,
        response_time_ms=145.5,
        tools_list_response=tools_response,
        tools_count=2,
        expected_tools_found=["search_restaurants_by_district", "recommend_restaurants"],
        missing_tools=[],
        validation_result=validation_result,
        request_id="mcp-health-check-123",
        jsonrpc_version="2.0"
    )
    
    print(f"✓ Created MCP result with {mcp_result.tools_count} tools")
    return mcp_result


def create_sample_rest_result() -> RESTHealthCheckResult:
    """Create a sample REST health check result."""
    print("\nCreating sample REST health check result...")
    
    # Create REST validation result
    validation_result = RESTValidationResult(
        is_valid=True,
        http_status_valid=True,
        response_format_valid=True,
        health_indicators_present=True,
        validation_errors=[],
        server_metrics={
            "uptime_seconds": 86400,
            "memory_usage_mb": 256,
            "cpu_usage_percent": 15.5
        }
    )
    
    # Create REST health check result
    rest_result = RESTHealthCheckResult(
        server_name="restaurant-search-mcp",
        timestamp=datetime.now(),
        success=True,
        response_time_ms=98.2,
        status_code=200,
        response_body={
            "status": "healthy",
            "uptime": "1 day",
            "version": "1.0.0",
            "services": {
                "database": "healthy",
                "cache": "healthy",
                "external_api": "healthy"
            }
        },
        health_endpoint_url="https://api.example.com/status/health",
        validation_result=validation_result,
        server_metrics={
            "response_time_p95": 120.0,
            "error_rate": 0.01,
            "throughput_rps": 50.0
        },
        circuit_breaker_states={
            "database": "CLOSED",
            "external_api": "CLOSED"
        },
        system_health={
            "memory_usage": 0.65,
            "cpu_usage": 0.15,
            "disk_usage": 0.45
        }
    )
    
    print(f"✓ Created REST result with status code {rest_result.status_code}")
    return rest_result


def create_dual_health_result(mcp_result: MCPHealthCheckResult, 
                            rest_result: RESTHealthCheckResult) -> DualHealthCheckResult:
    """Create a dual health check result combining MCP and REST results."""
    print("\nCreating dual health check result...")
    
    # Create combined metrics
    combined_metrics = CombinedHealthMetrics(
        mcp_response_time_ms=mcp_result.response_time_ms,
        rest_response_time_ms=rest_result.response_time_ms,
        combined_response_time_ms=(mcp_result.response_time_ms + rest_result.response_time_ms) / 2,
        mcp_success_rate=1.0,
        rest_success_rate=1.0,
        combined_success_rate=1.0,
        tools_available_count=mcp_result.tools_count or 0,
        tools_expected_count=len(mcp_result.expected_tools_found),
        tools_availability_percentage=100.0,
        http_status_codes={200: 1},
        health_endpoint_availability=1.0
    )
    
    # Create dual health check result
    dual_result = DualHealthCheckResult(
        server_name="restaurant-search-mcp",
        timestamp=datetime.now(),
        overall_status=ServerStatus.HEALTHY,
        overall_success=True,
        mcp_result=mcp_result,
        mcp_success=mcp_result.success,
        mcp_response_time_ms=mcp_result.response_time_ms,
        mcp_tools_count=mcp_result.tools_count,
        rest_result=rest_result,
        rest_success=rest_result.success,
        rest_response_time_ms=rest_result.response_time_ms,
        rest_status_code=rest_result.status_code,
        combined_response_time_ms=combined_metrics.combined_response_time_ms,
        health_score=0.95,
        available_paths=["both"],
        combined_metrics=combined_metrics
    )
    
    print(f"✓ Created dual result with overall status: {dual_result.overall_status.value}")
    return dual_result


def demonstrate_serialization(dual_result: DualHealthCheckResult):
    """Demonstrate serialization and deserialization."""
    print("\nDemonstrating serialization...")
    
    # Serialize to dictionary
    data_dict = dual_result.to_dict()
    print(f"✓ Serialized to dictionary with {len(data_dict)} fields")
    
    # Serialize to JSON
    json_str = dual_result.to_json()
    print(f"✓ Serialized to JSON string ({len(json_str)} characters)")
    
    # Deserialize from dictionary
    restored_result = DualHealthCheckResult.from_dict(data_dict)
    print(f"✓ Deserialized from dictionary")
    
    # Verify data integrity
    assert restored_result.server_name == dual_result.server_name
    assert restored_result.overall_status == dual_result.overall_status
    assert restored_result.health_score == dual_result.health_score
    print("✓ Data integrity verified after serialization round-trip")


def demonstrate_priority_config():
    """Demonstrate priority configuration."""
    print("\nDemonstrating priority configuration...")
    
    # Create priority config
    priority_config = PriorityConfig(
        mcp_priority_weight=0.8,
        rest_priority_weight=0.2,
        require_both_success_for_healthy=True,
        degraded_on_single_failure=True
    )
    
    # Validate priority config
    errors = priority_config.validate()
    if errors:
        print("❌ Priority config validation failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Priority config validation passed")
    
    # Create aggregation config
    aggregation_config = AggregationConfig(
        priority_config=priority_config,
        health_score_calculation="weighted_average",
        failure_threshold=0.3,
        degraded_threshold=0.7
    )
    
    # Validate aggregation config
    errors = aggregation_config.validate()
    if errors:
        print("❌ Aggregation config validation failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Aggregation config validation passed")
    
    print(f"✓ MCP weight: {priority_config.mcp_priority_weight}")
    print(f"✓ REST weight: {priority_config.rest_priority_weight}")


def main():
    """Main demonstration function."""
    print("Enhanced MCP Status Check Data Models Example")
    print("=" * 50)
    
    try:
        # Create and validate server configuration
        config = create_sample_server_config()
        if not validate_server_config(config):
            return 1
        
        # Create sample health check results
        mcp_result = create_sample_mcp_result()
        rest_result = create_sample_rest_result()
        
        # Create dual health check result
        dual_result = create_dual_health_result(mcp_result, rest_result)
        
        # Demonstrate serialization
        demonstrate_serialization(dual_result)
        
        # Demonstrate priority configuration
        demonstrate_priority_config()
        
        print("\n" + "=" * 50)
        print("✅ All demonstrations completed successfully!")
        
        # Print summary
        print(f"\nSummary:")
        print(f"  Server: {dual_result.server_name}")
        print(f"  Overall Status: {dual_result.overall_status.value}")
        print(f"  Health Score: {dual_result.health_score}")
        print(f"  MCP Success: {dual_result.mcp_success}")
        print(f"  REST Success: {dual_result.rest_success}")
        print(f"  Available Paths: {', '.join(dual_result.available_paths)}")
        print(f"  Combined Response Time: {dual_result.combined_response_time_ms:.1f}ms")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())