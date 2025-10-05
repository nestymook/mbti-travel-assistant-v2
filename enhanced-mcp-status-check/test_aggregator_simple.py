#!/usr/bin/env python3
"""
Simple test script for Health Result Aggregator

This script provides a basic test of the Health Result Aggregator functionality
without requiring pytest fixtures.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from services.health_result_aggregator import HealthResultAggregator
from models.dual_health_models import (
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    DualHealthCheckResult,
    CombinedHealthMetrics,
    AggregationConfig,
    PriorityConfig,
    ServerStatus,
    MCPValidationResult,
    RESTValidationResult
)


def create_successful_mcp_result():
    """Create a successful MCP health check result."""
    validation_result = MCPValidationResult(
        is_valid=True,
        tools_count=3,
        expected_tools_found=["search_restaurants", "recommend_restaurants", "analyze_sentiment"],
        missing_tools=[],
        validation_errors=[],
        tool_schemas_valid=True
    )
    
    return MCPHealthCheckResult(
        server_name="test-server",
        timestamp=datetime.now(),
        success=True,
        response_time_ms=150.0,
        tools_count=3,
        expected_tools_found=["search_restaurants", "recommend_restaurants", "analyze_sentiment"],
        missing_tools=[],
        validation_result=validation_result,
        request_id="test-request-123",
        jsonrpc_version="2.0"
    )


def create_failed_mcp_result():
    """Create a failed MCP health check result."""
    return MCPHealthCheckResult(
        server_name="test-server",
        timestamp=datetime.now(),
        success=False,
        response_time_ms=5000.0,
        connection_error="Connection timeout",
        request_id="test-request-456"
    )


def create_successful_rest_result():
    """Create a successful REST health check result."""
    validation_result = RESTValidationResult(
        is_valid=True,
        http_status_valid=True,
        response_format_valid=True,
        health_indicators_present=True,
        validation_errors=[],
        server_metrics={"uptime": 3600, "memory_usage": 0.65}
    )
    
    return RESTHealthCheckResult(
        server_name="test-server",
        timestamp=datetime.now(),
        success=True,
        response_time_ms=120.0,
        status_code=200,
        response_body={"status": "healthy", "uptime": 3600},
        health_endpoint_url="http://test-server/status/health",
        validation_result=validation_result,
        server_metrics={"uptime": 3600, "memory_usage": 0.65}
    )


def create_failed_rest_result():
    """Create a failed REST health check result."""
    return RESTHealthCheckResult(
        server_name="test-server",
        timestamp=datetime.now(),
        success=False,
        response_time_ms=8000.0,
        status_code=503,
        health_endpoint_url="http://test-server/status/health",
        http_error="HTTP 503: Service Unavailable"
    )


def test_status_determination():
    """Test status determination logic."""
    print("Testing status determination...")
    
    aggregator = HealthResultAggregator()
    priority_config = PriorityConfig()
    
    # Test both successful
    status = aggregator.determine_overall_status(
        mcp_success=True,
        rest_success=True,
        priority_config=priority_config
    )
    assert status == ServerStatus.HEALTHY, f"Expected HEALTHY, got {status}"
    print("✓ Both successful returns HEALTHY")
    
    # Test both failed
    status = aggregator.determine_overall_status(
        mcp_success=False,
        rest_success=False,
        priority_config=priority_config
    )
    assert status == ServerStatus.UNHEALTHY, f"Expected UNHEALTHY, got {status}"
    print("✓ Both failed returns UNHEALTHY")
    
    # Test mixed results
    status = aggregator.determine_overall_status(
        mcp_success=True,
        rest_success=False,
        priority_config=priority_config
    )
    assert status == ServerStatus.DEGRADED, f"Expected DEGRADED, got {status}"
    print("✓ Mixed results returns DEGRADED")


def test_health_score_calculation():
    """Test health score calculation."""
    print("\nTesting health score calculation...")
    
    aggregator = HealthResultAggregator()
    config = AggregationConfig(
        priority_config=PriorityConfig(mcp_priority_weight=0.6, rest_priority_weight=0.4)
    )
    
    successful_mcp = create_successful_mcp_result()
    successful_rest = create_successful_rest_result()
    failed_mcp = create_failed_mcp_result()
    failed_rest = create_failed_rest_result()
    
    # Test both successful
    score = aggregator.calculate_health_score(
        mcp_result=successful_mcp,
        rest_result=successful_rest,
        aggregation_config=config
    )
    assert 0.8 <= score <= 1.0, f"Expected high score (0.8-1.0), got {score}"
    print(f"✓ Both successful returns high score: {score:.3f}")
    
    # Test both failed
    score = aggregator.calculate_health_score(
        mcp_result=failed_mcp,
        rest_result=failed_rest,
        aggregation_config=config
    )
    assert score == 0.0, f"Expected 0.0, got {score}"
    print(f"✓ Both failed returns zero score: {score}")
    
    # Test mixed results
    score = aggregator.calculate_health_score(
        mcp_result=successful_mcp,
        rest_result=failed_rest,
        aggregation_config=config
    )
    assert 0.0 < score < 1.0, f"Expected score between 0 and 1, got {score}"
    print(f"✓ Mixed results returns weighted score: {score:.3f}")


def test_combined_metrics():
    """Test combined metrics creation."""
    print("\nTesting combined metrics...")
    
    aggregator = HealthResultAggregator()
    successful_mcp = create_successful_mcp_result()
    successful_rest = create_successful_rest_result()
    
    metrics = aggregator.create_combined_metrics(
        mcp_result=successful_mcp,
        rest_result=successful_rest
    )
    
    assert isinstance(metrics, CombinedHealthMetrics), "Should return CombinedHealthMetrics"
    assert metrics.mcp_response_time_ms == successful_mcp.response_time_ms
    assert metrics.rest_response_time_ms == successful_rest.response_time_ms
    assert metrics.combined_response_time_ms > 0
    assert metrics.mcp_success_rate == 1.0
    assert metrics.rest_success_rate == 1.0
    assert metrics.combined_success_rate == 1.0
    print("✓ Combined metrics created successfully")


def test_available_paths():
    """Test available paths determination."""
    print("\nTesting available paths...")
    
    aggregator = HealthResultAggregator()
    successful_mcp = create_successful_mcp_result()
    successful_rest = create_successful_rest_result()
    failed_mcp = create_failed_mcp_result()
    failed_rest = create_failed_rest_result()
    
    # Test both successful
    paths = aggregator.determine_available_paths(
        mcp_result=successful_mcp,
        rest_result=successful_rest
    )
    assert "mcp" in paths and "rest" in paths and "both" in paths
    print("✓ Both successful returns both paths")
    
    # Test MCP only
    paths = aggregator.determine_available_paths(
        mcp_result=successful_mcp,
        rest_result=failed_rest
    )
    assert "mcp" in paths and "rest" not in paths and "both" not in paths
    print("✓ MCP only returns MCP path")
    
    # Test both failed
    paths = aggregator.determine_available_paths(
        mcp_result=failed_mcp,
        rest_result=failed_rest
    )
    assert "none" in paths
    print("✓ Both failed returns none path")


def test_dual_result_aggregation():
    """Test complete dual result aggregation."""
    print("\nTesting dual result aggregation...")
    
    aggregator = HealthResultAggregator()
    successful_mcp = create_successful_mcp_result()
    successful_rest = create_successful_rest_result()
    failed_mcp = create_failed_mcp_result()
    failed_rest = create_failed_rest_result()
    
    # Test successful aggregation
    result = aggregator.aggregate_dual_results(
        mcp_result=successful_mcp,
        rest_result=successful_rest
    )
    
    assert isinstance(result, DualHealthCheckResult)
    assert result.server_name == "test-server"
    assert result.overall_status == ServerStatus.HEALTHY
    assert result.overall_success is True
    assert result.mcp_success is True
    assert result.rest_success is True
    assert result.health_score > 0.8
    assert "both" in result.available_paths
    assert result.combined_metrics is not None
    print("✓ Successful aggregation works correctly")
    
    # Test failed aggregation
    result = aggregator.aggregate_dual_results(
        mcp_result=failed_mcp,
        rest_result=failed_rest
    )
    
    assert result.overall_status == ServerStatus.UNHEALTHY
    assert result.overall_success is False
    assert result.mcp_success is False
    assert result.rest_success is False
    assert result.health_score == 0.0
    assert "none" in result.available_paths
    print("✓ Failed aggregation works correctly")
    
    # Test mixed aggregation
    result = aggregator.aggregate_dual_results(
        mcp_result=successful_mcp,
        rest_result=failed_rest
    )
    
    assert result.overall_status == ServerStatus.DEGRADED
    assert result.overall_success is False
    assert result.mcp_success is True
    assert result.rest_success is False
    assert 0.0 < result.health_score < 1.0
    assert "mcp" in result.available_paths
    print("✓ Mixed aggregation works correctly")


def test_configuration_validation():
    """Test configuration validation."""
    print("\nTesting configuration validation...")
    
    aggregator = HealthResultAggregator()
    
    # Test valid config
    valid_config = AggregationConfig(
        priority_config=PriorityConfig(mcp_priority_weight=0.7, rest_priority_weight=0.3)
    )
    errors = aggregator.validate_aggregation_rules(valid_config)
    assert len(errors) == 0, f"Valid config should have no errors, got: {errors}"
    print("✓ Valid configuration passes validation")
    
    # Test invalid config
    invalid_config = AggregationConfig(
        priority_config=PriorityConfig(mcp_priority_weight=0.8, rest_priority_weight=0.5)  # Sum > 1.0
    )
    errors = aggregator.validate_aggregation_rules(invalid_config)
    assert len(errors) > 0, "Invalid config should have errors"
    print("✓ Invalid configuration fails validation")


def test_aggregation_summary():
    """Test aggregation summary creation."""
    print("\nTesting aggregation summary...")
    
    aggregator = HealthResultAggregator()
    
    # Create mixed dual results
    dual_results = [
        DualHealthCheckResult(
            server_name="server1",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            health_score=0.9,
            combined_response_time_ms=150.0,
            mcp_success=True,
            rest_success=True,
            available_paths=["both"]
        ),
        DualHealthCheckResult(
            server_name="server2",
            timestamp=datetime.now(),
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            health_score=0.6,
            combined_response_time_ms=300.0,
            mcp_success=True,
            rest_success=False,
            available_paths=["mcp"]
        ),
        DualHealthCheckResult(
            server_name="server3",
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            health_score=0.0,
            combined_response_time_ms=5000.0,
            mcp_success=False,
            rest_success=False,
            available_paths=["none"]
        )
    ]
    
    summary = aggregator.create_aggregation_summary(dual_results)
    
    assert summary["total_servers"] == 3
    assert summary["healthy_servers"] == 1
    assert summary["degraded_servers"] == 1
    assert summary["unhealthy_servers"] == 1
    assert summary["unknown_servers"] == 0
    assert 0.4 <= summary["average_health_score"] <= 0.6
    assert summary["mcp_success_rate"] == 2/3  # 2 out of 3 succeeded
    assert summary["rest_success_rate"] == 1/3  # 1 out of 3 succeeded
    assert summary["combined_success_rate"] == 1/3  # 1 out of 3 overall success
    print("✓ Aggregation summary created correctly")


def main():
    """Run all tests."""
    print("Running Health Result Aggregator Tests")
    print("=" * 50)
    
    try:
        test_status_determination()
        test_health_score_calculation()
        test_combined_metrics()
        test_available_paths()
        test_dual_result_aggregation()
        test_configuration_validation()
        test_aggregation_summary()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("Health Result Aggregator implementation is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())