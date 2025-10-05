#!/usr/bin/env python3
"""
Health Result Aggregator Example

This example demonstrates how to use the Health Result Aggregator to combine
dual health check results from MCP tools/list requests and REST API health checks.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from services.health_result_aggregator import HealthResultAggregator
from models.dual_health_models import (
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    AggregationConfig,
    PriorityConfig,
    MCPValidationResult,
    RESTValidationResult
)


def create_example_mcp_results():
    """Create example MCP health check results for different scenarios."""
    
    # Successful MCP result
    successful_validation = MCPValidationResult(
        is_valid=True,
        tools_count=4,
        expected_tools_found=["search_restaurants", "recommend_restaurants", "analyze_sentiment", "get_districts"],
        missing_tools=[],
        validation_errors=[],
        tool_schemas_valid=True
    )
    
    successful_mcp = MCPHealthCheckResult(
        server_name="restaurant-search-mcp",
        timestamp=datetime.now(),
        success=True,
        response_time_ms=180.0,
        tools_count=4,
        expected_tools_found=["search_restaurants", "recommend_restaurants", "analyze_sentiment", "get_districts"],
        missing_tools=[],
        validation_result=successful_validation,
        request_id="mcp-req-001",
        jsonrpc_version="2.0"
    )
    
    # Degraded MCP result (missing some tools)
    degraded_validation = MCPValidationResult(
        is_valid=False,
        tools_count=2,
        expected_tools_found=["search_restaurants"],
        missing_tools=["recommend_restaurants", "analyze_sentiment"],
        validation_errors=["Missing expected tools"],
        tool_schemas_valid=True
    )
    
    degraded_mcp = MCPHealthCheckResult(
        server_name="restaurant-reasoning-mcp",
        timestamp=datetime.now(),
        success=False,
        response_time_ms=2500.0,
        tools_count=2,
        expected_tools_found=["search_restaurants"],
        missing_tools=["recommend_restaurants", "analyze_sentiment"],
        validation_result=degraded_validation,
        request_id="mcp-req-002",
        jsonrpc_version="2.0"
    )
    
    # Failed MCP result
    failed_mcp = MCPHealthCheckResult(
        server_name="mbti-travel-assistant-mcp",
        timestamp=datetime.now(),
        success=False,
        response_time_ms=10000.0,
        connection_error="Connection timeout after 10 seconds",
        request_id="mcp-req-003"
    )
    
    return [successful_mcp, degraded_mcp, failed_mcp]


def create_example_rest_results():
    """Create example REST health check results for different scenarios."""
    
    # Successful REST result
    successful_validation = RESTValidationResult(
        is_valid=True,
        http_status_valid=True,
        response_format_valid=True,
        health_indicators_present=True,
        validation_errors=[],
        server_metrics={"uptime": 7200, "memory_usage": 0.45, "cpu_usage": 0.25}
    )
    
    successful_rest = RESTHealthCheckResult(
        server_name="restaurant-search-mcp",
        timestamp=datetime.now(),
        success=True,
        response_time_ms=95.0,
        status_code=200,
        response_body={
            "status": "healthy",
            "uptime": 7200,
            "memory_usage": 0.45,
            "cpu_usage": 0.25,
            "active_connections": 12
        },
        health_endpoint_url="http://restaurant-search-mcp:8080/status/health",
        validation_result=successful_validation,
        server_metrics={"uptime": 7200, "memory_usage": 0.45, "cpu_usage": 0.25}
    )
    
    # Degraded REST result
    degraded_validation = RESTValidationResult(
        is_valid=True,
        http_status_valid=True,
        response_format_valid=True,
        health_indicators_present=True,
        validation_errors=[],
        server_metrics={"uptime": 3600, "memory_usage": 0.85, "cpu_usage": 0.75}
    )
    
    degraded_rest = RESTHealthCheckResult(
        server_name="restaurant-reasoning-mcp",
        timestamp=datetime.now(),
        success=True,
        response_time_ms=450.0,
        status_code=200,
        response_body={
            "status": "degraded",
            "uptime": 3600,
            "memory_usage": 0.85,
            "cpu_usage": 0.75,
            "warnings": ["High memory usage", "High CPU usage"]
        },
        health_endpoint_url="http://restaurant-reasoning-mcp:8080/status/health",
        validation_result=degraded_validation,
        server_metrics={"uptime": 3600, "memory_usage": 0.85, "cpu_usage": 0.75}
    )
    
    # Failed REST result
    failed_rest = RESTHealthCheckResult(
        server_name="mbti-travel-assistant-mcp",
        timestamp=datetime.now(),
        success=False,
        response_time_ms=5000.0,
        status_code=503,
        health_endpoint_url="http://mbti-travel-assistant-mcp:8080/status/health",
        http_error="HTTP 503: Service Unavailable"
    )
    
    return [successful_rest, degraded_rest, failed_rest]


def demonstrate_basic_aggregation():
    """Demonstrate basic dual result aggregation."""
    print("=== Basic Dual Result Aggregation ===")
    
    aggregator = HealthResultAggregator()
    mcp_results = create_example_mcp_results()
    rest_results = create_example_rest_results()
    
    # Aggregate results for each server
    for i, (mcp_result, rest_result) in enumerate(zip(mcp_results, rest_results)):
        print(f"\nServer {i+1}: {mcp_result.server_name}")
        print(f"MCP Success: {mcp_result.success}, REST Success: {rest_result.success}")
        
        dual_result = aggregator.aggregate_dual_results(
            mcp_result=mcp_result,
            rest_result=rest_result
        )
        
        print(f"Overall Status: {dual_result.overall_status.value}")
        print(f"Health Score: {dual_result.health_score:.3f}")
        print(f"Available Paths: {', '.join(dual_result.available_paths)}")
        print(f"Combined Response Time: {dual_result.combined_response_time_ms:.1f}ms")
        
        if dual_result.mcp_error_message:
            print(f"MCP Error: {dual_result.mcp_error_message}")
        if dual_result.rest_error_message:
            print(f"REST Error: {dual_result.rest_error_message}")


def demonstrate_custom_configuration():
    """Demonstrate aggregation with custom configuration."""
    print("\n\n=== Custom Configuration Aggregation ===")
    
    # Create custom configuration with MCP priority
    priority_config = PriorityConfig(
        mcp_priority_weight=0.8,
        rest_priority_weight=0.2,
        require_both_success_for_healthy=False,
        degraded_on_single_failure=False  # More permissive
    )
    
    custom_config = AggregationConfig(
        priority_config=priority_config,
        health_score_calculation="weighted_average",
        failure_threshold=0.3,
        degraded_threshold=0.6
    )
    
    aggregator = HealthResultAggregator()
    mcp_results = create_example_mcp_results()
    rest_results = create_example_rest_results()
    
    print("Using MCP-prioritized configuration (80% MCP, 20% REST)")
    print("More permissive settings (degraded_on_single_failure=False)")
    
    for i, (mcp_result, rest_result) in enumerate(zip(mcp_results, rest_results)):
        print(f"\nServer {i+1}: {mcp_result.server_name}")
        
        dual_result = aggregator.aggregate_dual_results(
            mcp_result=mcp_result,
            rest_result=rest_result,
            aggregation_config=custom_config
        )
        
        print(f"Overall Status: {dual_result.overall_status.value}")
        print(f"Health Score: {dual_result.health_score:.3f}")
        print(f"Available Paths: {', '.join(dual_result.available_paths)}")


def demonstrate_different_calculation_methods():
    """Demonstrate different health score calculation methods."""
    print("\n\n=== Different Calculation Methods ===")
    
    aggregator = HealthResultAggregator()
    mcp_result = create_example_mcp_results()[0]  # Successful
    rest_result = create_example_rest_results()[1]  # Degraded
    
    methods = ["weighted_average", "minimum", "maximum"]
    
    for method in methods:
        config = AggregationConfig(
            priority_config=PriorityConfig(),
            health_score_calculation=method
        )
        
        dual_result = aggregator.aggregate_dual_results(
            mcp_result=mcp_result,
            rest_result=rest_result,
            aggregation_config=config
        )
        
        print(f"{method.replace('_', ' ').title()}: {dual_result.health_score:.3f}")


def demonstrate_aggregation_summary():
    """Demonstrate aggregation summary creation."""
    print("\n\n=== Aggregation Summary ===")
    
    aggregator = HealthResultAggregator()
    mcp_results = create_example_mcp_results()
    rest_results = create_example_rest_results()
    
    # Create dual results
    dual_results = []
    for mcp_result, rest_result in zip(mcp_results, rest_results):
        dual_result = aggregator.aggregate_dual_results(
            mcp_result=mcp_result,
            rest_result=rest_result
        )
        dual_results.append(dual_result)
    
    # Create summary
    summary = aggregator.create_aggregation_summary(dual_results)
    
    print("Summary Statistics:")
    print(f"Total Servers: {summary['total_servers']}")
    print(f"Healthy: {summary['healthy_servers']}")
    print(f"Degraded: {summary['degraded_servers']}")
    print(f"Unhealthy: {summary['unhealthy_servers']}")
    print(f"Unknown: {summary['unknown_servers']}")
    print(f"Average Health Score: {summary['average_health_score']:.3f}")
    print(f"Average Response Time: {summary['average_response_time_ms']:.1f}ms")
    print(f"MCP Success Rate: {summary['mcp_success_rate']:.1%}")
    print(f"REST Success Rate: {summary['rest_success_rate']:.1%}")
    print(f"Combined Success Rate: {summary['combined_success_rate']:.1%}")


def demonstrate_json_serialization():
    """Demonstrate JSON serialization of results."""
    print("\n\n=== JSON Serialization ===")
    
    aggregator = HealthResultAggregator()
    mcp_result = create_example_mcp_results()[0]
    rest_result = create_example_rest_results()[0]
    
    dual_result = aggregator.aggregate_dual_results(
        mcp_result=mcp_result,
        rest_result=rest_result
    )
    
    # Convert to JSON
    result_dict = dual_result.to_dict()
    result_json = json.dumps(result_dict, indent=2, default=str)
    
    print("Dual Health Check Result as JSON:")
    print(result_json[:500] + "..." if len(result_json) > 500 else result_json)


def demonstrate_edge_cases():
    """Demonstrate edge case handling."""
    print("\n\n=== Edge Cases ===")
    
    aggregator = HealthResultAggregator()
    
    # Case 1: MCP only
    print("Case 1: MCP result only")
    mcp_only_result = aggregator.aggregate_dual_results(
        mcp_result=create_example_mcp_results()[0],
        rest_result=None
    )
    print(f"Status: {mcp_only_result.overall_status.value}")
    print(f"Health Score: {mcp_only_result.health_score:.3f}")
    print(f"Available Paths: {', '.join(mcp_only_result.available_paths)}")
    
    # Case 2: REST only
    print("\nCase 2: REST result only")
    rest_only_result = aggregator.aggregate_dual_results(
        mcp_result=None,
        rest_result=create_example_rest_results()[0]
    )
    print(f"Status: {rest_only_result.overall_status.value}")
    print(f"Health Score: {rest_only_result.health_score:.3f}")
    print(f"Available Paths: {', '.join(rest_only_result.available_paths)}")
    
    # Case 3: No results
    print("\nCase 3: No results")
    no_results = aggregator.aggregate_dual_results(
        mcp_result=None,
        rest_result=None
    )
    print(f"Status: {no_results.overall_status.value}")
    print(f"Health Score: {no_results.health_score:.3f}")
    print(f"Available Paths: {', '.join(no_results.available_paths)}")


def main():
    """Run all demonstration examples."""
    print("Health Result Aggregator Examples")
    print("=" * 50)
    
    try:
        demonstrate_basic_aggregation()
        demonstrate_custom_configuration()
        demonstrate_different_calculation_methods()
        demonstrate_aggregation_summary()
        demonstrate_json_serialization()
        demonstrate_edge_cases()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())