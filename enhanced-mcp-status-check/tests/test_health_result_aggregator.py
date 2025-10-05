"""
Unit Tests for Health Result Aggregator

This module contains comprehensive unit tests for the Health Result Aggregator
with various failure scenarios and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    RESTValidationResult,
    MCPToolsListResponse
)


class TestHealthResultAggregator:
    """Test cases for Health Result Aggregator."""
    
    @pytest.fixture
    def aggregator(self):
        """Create Health Result Aggregator instance."""
        return HealthResultAggregator()
    
    @pytest.fixture
    def custom_config(self):
        """Create custom aggregation configuration."""
        priority_config = PriorityConfig(
            mcp_priority_weight=0.7,
            rest_priority_weight=0.3,
            require_both_success_for_healthy=False,
            degraded_on_single_failure=True
        )
        
        return AggregationConfig(
            priority_config=priority_config,
            health_score_calculation="weighted_average",
            failure_threshold=0.4,
            degraded_threshold=0.8
        )
    
    @pytest.fixture
    def successful_mcp_result(self):
        """Create successful MCP health check result."""
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
    
    @pytest.fixture
    def failed_mcp_result(self):
        """Create failed MCP health check result."""
        return MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            connection_error="Connection timeout",
            request_id="test-request-456"
        )
    
    @pytest.fixture
    def successful_rest_result(self):
        """Create successful REST health check result."""
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
    
    @pytest.fixture
    def failed_rest_result(self):
        """Create failed REST health check result."""
        return RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=8000.0,
            status_code=503,
            health_endpoint_url="http://test-server/status/health",
            http_error="HTTP 503: Service Unavailable"
        )


class TestStatusDetermination:
    """Test status determination logic."""
    
    def test_both_successful_returns_healthy(self, aggregator):
        """Test that both successful results return HEALTHY status."""
        priority_config = PriorityConfig()
        
        status = aggregator.determine_overall_status(
            mcp_success=True,
            rest_success=True,
            priority_config=priority_config
        )
        
        assert status == ServerStatus.HEALTHY
    
    def test_both_failed_returns_unhealthy(self, aggregator):
        """Test that both failed results return UNHEALTHY status."""
        priority_config = PriorityConfig()
        
        status = aggregator.determine_overall_status(
            mcp_success=False,
            rest_success=False,
            priority_config=priority_config
        )
        
        assert status == ServerStatus.UNHEALTHY
    
    def test_mixed_results_with_strict_mode_returns_degraded(self, aggregator):
        """Test mixed results with strict mode returns DEGRADED."""
        priority_config = PriorityConfig(
            require_both_success_for_healthy=True
        )
        
        status = aggregator.determine_overall_status(
            mcp_success=True,
            rest_success=False,
            priority_config=priority_config
        )
        
        assert status == ServerStatus.DEGRADED
    
    def test_mixed_results_with_conservative_mode_returns_degraded(self, aggregator):
        """Test mixed results with conservative mode returns DEGRADED."""
        priority_config = PriorityConfig(
            degraded_on_single_failure=True
        )
        
        status = aggregator.determine_overall_status(
            mcp_success=True,
            rest_success=False,
            priority_config=priority_config
        )
        
        assert status == ServerStatus.DEGRADED
    
    def test_mixed_results_with_mcp_priority_returns_healthy(self, aggregator):
        """Test mixed results with MCP priority returns HEALTHY when MCP succeeds."""
        priority_config = PriorityConfig(
            mcp_priority_weight=0.8,
            rest_priority_weight=0.2,
            require_both_success_for_healthy=False,
            degraded_on_single_failure=False
        )
        
        status = aggregator.determine_overall_status(
            mcp_success=True,
            rest_success=False,
            priority_config=priority_config
        )
        
        assert status == ServerStatus.HEALTHY
    
    def test_mixed_results_with_rest_priority_returns_healthy(self, aggregator):
        """Test mixed results with REST priority returns HEALTHY when REST succeeds."""
        priority_config = PriorityConfig(
            mcp_priority_weight=0.3,
            rest_priority_weight=0.7,
            require_both_success_for_healthy=False,
            degraded_on_single_failure=False
        )
        
        status = aggregator.determine_overall_status(
            mcp_success=False,
            rest_success=True,
            priority_config=priority_config
        )
        
        assert status == ServerStatus.HEALTHY


class TestHealthScoreCalculation:
    """Test health score calculation logic."""
    
    def test_both_successful_returns_high_score(self, aggregator, successful_mcp_result, successful_rest_result):
        """Test that both successful results return high health score."""
        config = AggregationConfig(
            priority_config=PriorityConfig(mcp_priority_weight=0.6, rest_priority_weight=0.4)
        )
        
        score = aggregator.calculate_health_score(
            mcp_result=successful_mcp_result,
            rest_result=successful_rest_result,
            aggregation_config=config
        )
        
        assert 0.8 <= score <= 1.0
    
    def test_both_failed_returns_zero_score(self, aggregator, failed_mcp_result, failed_rest_result):
        """Test that both failed results return zero health score."""
        config = AggregationConfig(
            priority_config=PriorityConfig(mcp_priority_weight=0.6, rest_priority_weight=0.4)
        )
        
        score = aggregator.calculate_health_score(
            mcp_result=failed_mcp_result,
            rest_result=failed_rest_result,
            aggregation_config=config
        )
        
        assert score == 0.0
    
    def test_mixed_results_returns_weighted_score(self, aggregator, successful_mcp_result, failed_rest_result):
        """Test mixed results return weighted score."""
        config = AggregationConfig(
            priority_config=PriorityConfig(mcp_priority_weight=0.7, rest_priority_weight=0.3)
        )
        
        score = aggregator.calculate_health_score(
            mcp_result=successful_mcp_result,
            rest_result=failed_rest_result,
            aggregation_config=config
        )
        
        # Should be approximately 0.7 * mcp_score + 0.3 * 0.0
        assert 0.5 <= score <= 0.8
    
    def test_minimum_calculation_method(self, aggregator, successful_mcp_result, failed_rest_result):
        """Test minimum calculation method."""
        config = AggregationConfig(
            priority_config=PriorityConfig(),
            health_score_calculation="minimum"
        )
        
        score = aggregator.calculate_health_score(
            mcp_result=successful_mcp_result,
            rest_result=failed_rest_result,
            aggregation_config=config
        )
        
        assert score == 0.0  # Minimum of success and failure
    
    def test_maximum_calculation_method(self, aggregator, successful_mcp_result, failed_rest_result):
        """Test maximum calculation method."""
        config = AggregationConfig(
            priority_config=PriorityConfig(),
            health_score_calculation="maximum"
        )
        
        score = aggregator.calculate_health_score(
            mcp_result=successful_mcp_result,
            rest_result=failed_rest_result,
            aggregation_config=config
        )
        
        assert score > 0.5  # Maximum of success and failure
    
    def test_missing_mcp_result_uses_rest_only(self, aggregator, successful_rest_result):
        """Test missing MCP result uses REST score only."""
        config = AggregationConfig(priority_config=PriorityConfig())
        
        score = aggregator.calculate_health_score(
            mcp_result=None,
            rest_result=successful_rest_result,
            aggregation_config=config
        )
        
        assert score > 0.0
    
    def test_missing_rest_result_uses_mcp_only(self, aggregator, successful_mcp_result):
        """Test missing REST result uses MCP score only."""
        config = AggregationConfig(priority_config=PriorityConfig())
        
        score = aggregator.calculate_health_score(
            mcp_result=successful_mcp_result,
            rest_result=None,
            aggregation_config=config
        )
        
        assert score > 0.0
    
    def test_both_missing_returns_zero(self, aggregator):
        """Test both missing results return zero score."""
        config = AggregationConfig(priority_config=PriorityConfig())
        
        score = aggregator.calculate_health_score(
            mcp_result=None,
            rest_result=None,
            aggregation_config=config
        )
        
        assert score == 0.0


class TestMCPScoreCalculation:
    """Test MCP-specific score calculation."""
    
    def test_successful_mcp_returns_high_score(self, aggregator, successful_mcp_result):
        """Test successful MCP result returns high score."""
        score = aggregator._calculate_mcp_score(successful_mcp_result)
        assert 0.8 <= score <= 1.0
    
    def test_failed_mcp_returns_zero_score(self, aggregator, failed_mcp_result):
        """Test failed MCP result returns zero score."""
        score = aggregator._calculate_mcp_score(failed_mcp_result)
        assert score == 0.0
    
    def test_missing_tools_penalizes_score(self, aggregator):
        """Test missing expected tools penalize the score."""
        validation_result = MCPValidationResult(
            is_valid=True,
            tools_count=2,
            expected_tools_found=["search_restaurants"],
            missing_tools=["recommend_restaurants"],
            validation_errors=[],
            tool_schemas_valid=True
        )
        
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=150.0,
            validation_result=validation_result
        )
        
        score = aggregator._calculate_mcp_score(mcp_result)
        assert 0.4 <= score <= 0.6  # Should be penalized for missing tools
    
    def test_validation_errors_penalize_score(self, aggregator):
        """Test validation errors penalize the score."""
        validation_result = MCPValidationResult(
            is_valid=False,
            tools_count=3,
            expected_tools_found=["search_restaurants"],
            missing_tools=[],
            validation_errors=["Invalid tool schema", "Missing description"],
            tool_schemas_valid=False
        )
        
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=150.0,
            validation_result=validation_result
        )
        
        score = aggregator._calculate_mcp_score(mcp_result)
        assert score < 1.0  # Should be penalized for validation errors
    
    def test_slow_response_penalizes_score(self, aggregator):
        """Test slow response time penalizes the score."""
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=8000.0  # 8 seconds - very slow
        )
        
        score = aggregator._calculate_mcp_score(mcp_result)
        assert score < 1.0  # Should be penalized for slow response


class TestRESTScoreCalculation:
    """Test REST-specific score calculation."""
    
    def test_successful_rest_returns_high_score(self, aggregator, successful_rest_result):
        """Test successful REST result returns high score."""
        score = aggregator._calculate_rest_score(successful_rest_result)
        assert 0.8 <= score <= 1.0
    
    def test_failed_rest_returns_zero_score(self, aggregator, failed_rest_result):
        """Test failed REST result returns zero score."""
        score = aggregator._calculate_rest_score(failed_rest_result)
        assert score == 0.0
    
    def test_redirect_status_penalizes_score(self, aggregator):
        """Test redirect status codes penalize the score."""
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=120.0,
            status_code=302,
            health_endpoint_url="http://test-server/status/health"
        )
        
        score = aggregator._calculate_rest_score(rest_result)
        assert 0.7 <= score <= 0.9  # Should be penalized for redirect
    
    def test_client_error_heavily_penalizes_score(self, aggregator):
        """Test client error status codes heavily penalize the score."""
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=120.0,
            status_code=404,
            health_endpoint_url="http://test-server/status/health"
        )
        
        score = aggregator._calculate_rest_score(rest_result)
        assert 0.2 <= score <= 0.4  # Should be heavily penalized
    
    def test_server_error_severely_penalizes_score(self, aggregator):
        """Test server error status codes severely penalize the score."""
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=120.0,
            status_code=500,
            health_endpoint_url="http://test-server/status/health"
        )
        
        score = aggregator._calculate_rest_score(rest_result)
        assert score <= 0.2  # Should be severely penalized
    
    def test_validation_errors_penalize_score(self, aggregator):
        """Test validation errors penalize the score."""
        validation_result = RESTValidationResult(
            is_valid=False,
            http_status_valid=True,
            response_format_valid=False,
            health_indicators_present=False,
            validation_errors=["Invalid JSON format", "Missing health indicators"]
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=120.0,
            status_code=200,
            validation_result=validation_result,
            health_endpoint_url="http://test-server/status/health"
        )
        
        score = aggregator._calculate_rest_score(rest_result)
        assert score < 1.0  # Should be penalized for validation errors
    
    def test_slow_response_penalizes_score(self, aggregator):
        """Test slow response time penalizes the score."""
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=6000.0,  # 6 seconds - slow
            status_code=200,
            health_endpoint_url="http://test-server/status/health"
        )
        
        score = aggregator._calculate_rest_score(rest_result)
        assert score < 1.0  # Should be penalized for slow response


class TestCombinedMetrics:
    """Test combined metrics creation."""
    
    def test_both_results_creates_combined_metrics(self, aggregator, successful_mcp_result, successful_rest_result):
        """Test both results create proper combined metrics."""
        metrics = aggregator.create_combined_metrics(
            mcp_result=successful_mcp_result,
            rest_result=successful_rest_result
        )
        
        assert isinstance(metrics, CombinedHealthMetrics)
        assert metrics.mcp_response_time_ms == successful_mcp_result.response_time_ms
        assert metrics.rest_response_time_ms == successful_rest_result.response_time_ms
        assert metrics.combined_response_time_ms > 0
        assert metrics.mcp_success_rate == 1.0
        assert metrics.rest_success_rate == 1.0
        assert metrics.combined_success_rate == 1.0
    
    def test_mcp_only_creates_metrics(self, aggregator, successful_mcp_result):
        """Test MCP-only result creates proper metrics."""
        metrics = aggregator.create_combined_metrics(
            mcp_result=successful_mcp_result,
            rest_result=None
        )
        
        assert metrics.mcp_response_time_ms == successful_mcp_result.response_time_ms
        assert metrics.rest_response_time_ms == 0.0
        assert metrics.combined_response_time_ms == successful_mcp_result.response_time_ms
        assert metrics.mcp_success_rate == 1.0
        assert metrics.rest_success_rate == 0.0
        assert metrics.combined_success_rate == 1.0
    
    def test_rest_only_creates_metrics(self, aggregator, successful_rest_result):
        """Test REST-only result creates proper metrics."""
        metrics = aggregator.create_combined_metrics(
            mcp_result=None,
            rest_result=successful_rest_result
        )
        
        assert metrics.mcp_response_time_ms == 0.0
        assert metrics.rest_response_time_ms == successful_rest_result.response_time_ms
        assert metrics.combined_response_time_ms == successful_rest_result.response_time_ms
        assert metrics.mcp_success_rate == 0.0
        assert metrics.rest_success_rate == 1.0
        assert metrics.combined_success_rate == 1.0
    
    def test_tool_metrics_from_mcp_result(self, aggregator, successful_mcp_result):
        """Test tool metrics are extracted from MCP result."""
        metrics = aggregator.create_combined_metrics(
            mcp_result=successful_mcp_result,
            rest_result=None
        )
        
        assert metrics.tools_available_count == 3
        assert metrics.tools_expected_count == 3
        assert metrics.tools_availability_percentage == 100.0
    
    def test_http_metrics_from_rest_result(self, aggregator, successful_rest_result):
        """Test HTTP metrics are extracted from REST result."""
        metrics = aggregator.create_combined_metrics(
            mcp_result=None,
            rest_result=successful_rest_result
        )
        
        assert 200 in metrics.http_status_codes
        assert metrics.http_status_codes[200] == 1
        assert metrics.health_endpoint_availability == 1.0


class TestAvailablePaths:
    """Test available paths determination."""
    
    def test_both_successful_returns_both_paths(self, aggregator, successful_mcp_result, successful_rest_result):
        """Test both successful results return both paths."""
        paths = aggregator.determine_available_paths(
            mcp_result=successful_mcp_result,
            rest_result=successful_rest_result
        )
        
        assert "mcp" in paths
        assert "rest" in paths
        assert "both" in paths
        assert "none" not in paths
    
    def test_mcp_only_returns_mcp_path(self, aggregator, successful_mcp_result, failed_rest_result):
        """Test MCP success only returns MCP path."""
        paths = aggregator.determine_available_paths(
            mcp_result=successful_mcp_result,
            rest_result=failed_rest_result
        )
        
        assert "mcp" in paths
        assert "rest" not in paths
        assert "both" not in paths
        assert "none" not in paths
    
    def test_rest_only_returns_rest_path(self, aggregator, failed_mcp_result, successful_rest_result):
        """Test REST success only returns REST path."""
        paths = aggregator.determine_available_paths(
            mcp_result=failed_mcp_result,
            rest_result=successful_rest_result
        )
        
        assert "mcp" not in paths
        assert "rest" in paths
        assert "both" not in paths
        assert "none" not in paths
    
    def test_both_failed_returns_none_path(self, aggregator, failed_mcp_result, failed_rest_result):
        """Test both failed results return none path."""
        paths = aggregator.determine_available_paths(
            mcp_result=failed_mcp_result,
            rest_result=failed_rest_result
        )
        
        assert "mcp" not in paths
        assert "rest" not in paths
        assert "both" not in paths
        assert "none" in paths


class TestDualResultAggregation:
    """Test complete dual result aggregation."""
    
    def test_successful_aggregation(self, aggregator, successful_mcp_result, successful_rest_result):
        """Test successful dual result aggregation."""
        result = aggregator.aggregate_dual_results(
            mcp_result=successful_mcp_result,
            rest_result=successful_rest_result
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
    
    def test_failed_aggregation(self, aggregator, failed_mcp_result, failed_rest_result):
        """Test failed dual result aggregation."""
        result = aggregator.aggregate_dual_results(
            mcp_result=failed_mcp_result,
            rest_result=failed_rest_result
        )
        
        assert result.overall_status == ServerStatus.UNHEALTHY
        assert result.overall_success is False
        assert result.mcp_success is False
        assert result.rest_success is False
        assert result.health_score == 0.0
        assert "none" in result.available_paths
        assert result.mcp_error_message is not None
        assert result.rest_error_message is not None
    
    def test_mixed_aggregation(self, aggregator, successful_mcp_result, failed_rest_result):
        """Test mixed dual result aggregation."""
        result = aggregator.aggregate_dual_results(
            mcp_result=successful_mcp_result,
            rest_result=failed_rest_result
        )
        
        assert result.overall_status == ServerStatus.DEGRADED
        assert result.overall_success is False
        assert result.mcp_success is True
        assert result.rest_success is False
        assert 0.0 < result.health_score < 1.0
        assert "mcp" in result.available_paths
        assert "rest" not in result.available_paths
    
    def test_custom_config_aggregation(self, aggregator, successful_mcp_result, failed_rest_result, custom_config):
        """Test aggregation with custom configuration."""
        result = aggregator.aggregate_dual_results(
            mcp_result=successful_mcp_result,
            rest_result=failed_rest_result,
            aggregation_config=custom_config
        )
        
        # With MCP priority weight of 0.7, should have higher health score
        assert result.health_score > 0.5
        assert result.overall_status == ServerStatus.DEGRADED
    
    def test_mcp_only_aggregation(self, aggregator, successful_mcp_result):
        """Test aggregation with MCP result only."""
        result = aggregator.aggregate_dual_results(
            mcp_result=successful_mcp_result,
            rest_result=None
        )
        
        assert result.overall_status == ServerStatus.HEALTHY
        assert result.mcp_success is True
        assert result.rest_success is False
        assert result.health_score > 0.0
        assert "mcp" in result.available_paths
    
    def test_rest_only_aggregation(self, aggregator, successful_rest_result):
        """Test aggregation with REST result only."""
        result = aggregator.aggregate_dual_results(
            mcp_result=None,
            rest_result=successful_rest_result
        )
        
        assert result.overall_status == ServerStatus.HEALTHY
        assert result.mcp_success is False
        assert result.rest_success is True
        assert result.health_score > 0.0
        assert "rest" in result.available_paths
    
    def test_no_results_aggregation(self, aggregator):
        """Test aggregation with no results."""
        result = aggregator.aggregate_dual_results(
            mcp_result=None,
            rest_result=None
        )
        
        assert result.overall_status == ServerStatus.UNHEALTHY
        assert result.overall_success is False
        assert result.health_score == 0.0
        assert "none" in result.available_paths


class TestMultipleResultsAggregation:
    """Test multiple results aggregation."""
    
    def test_multiple_successful_aggregations(self, aggregator, successful_mcp_result, successful_rest_result):
        """Test multiple successful aggregations."""
        dual_results = [
            (successful_mcp_result, successful_rest_result),
            (successful_mcp_result, successful_rest_result)
        ]
        
        results = aggregator.aggregate_multiple_dual_results(dual_results)
        
        assert len(results) == 2
        assert all(r.overall_status == ServerStatus.HEALTHY for r in results)
        assert all(r.overall_success for r in results)
    
    def test_multiple_mixed_aggregations(self, aggregator, successful_mcp_result, failed_rest_result):
        """Test multiple mixed aggregations."""
        dual_results = [
            (successful_mcp_result, failed_rest_result),
            (successful_mcp_result, failed_rest_result)
        ]
        
        results = aggregator.aggregate_multiple_dual_results(dual_results)
        
        assert len(results) == 2
        assert all(r.overall_status == ServerStatus.DEGRADED for r in results)
        assert all(not r.overall_success for r in results)
    
    def test_aggregation_with_exception_handling(self, aggregator):
        """Test aggregation handles exceptions gracefully."""
        # Create invalid results that might cause exceptions
        invalid_mcp = MCPHealthCheckResult(
            server_name="invalid-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=-1.0  # Invalid negative time
        )
        
        dual_results = [(invalid_mcp, None)]
        
        results = aggregator.aggregate_multiple_dual_results(dual_results)
        
        assert len(results) == 1
        # Should handle gracefully and create error result
        assert results[0].server_name == "invalid-server"


class TestAggregationSummary:
    """Test aggregation summary creation."""
    
    def test_summary_with_mixed_results(self, aggregator):
        """Test summary creation with mixed results."""
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
        assert summary["average_response_time_ms"] > 1000
        assert summary["mcp_success_rate"] == 2/3  # 2 out of 3 succeeded
        assert summary["rest_success_rate"] == 1/3  # 1 out of 3 succeeded
        assert summary["combined_success_rate"] == 1/3  # 1 out of 3 overall success
    
    def test_empty_summary(self, aggregator):
        """Test summary with empty results."""
        summary = aggregator.create_aggregation_summary([])
        
        assert summary["total_servers"] == 0
        assert summary["healthy_servers"] == 0
        assert summary["average_health_score"] == 0.0
        assert summary["mcp_success_rate"] == 0.0


class TestConfigurationValidation:
    """Test configuration validation."""
    
    def test_valid_config_passes_validation(self, aggregator, custom_config):
        """Test valid configuration passes validation."""
        errors = aggregator.validate_aggregation_rules(custom_config)
        assert len(errors) == 0
    
    def test_invalid_priority_weights_fail_validation(self, aggregator):
        """Test invalid priority weights fail validation."""
        priority_config = PriorityConfig(
            mcp_priority_weight=0.8,
            rest_priority_weight=0.5  # Sum > 1.0
        )
        
        config = AggregationConfig(priority_config=priority_config)
        errors = aggregator.validate_aggregation_rules(config)
        
        assert len(errors) > 0
        assert any("sum to 1.0" in error for error in errors)
    
    def test_invalid_thresholds_fail_validation(self, aggregator):
        """Test invalid thresholds fail validation."""
        config = AggregationConfig(
            priority_config=PriorityConfig(),
            failure_threshold=0.8,
            degraded_threshold=0.6  # failure > degraded
        )
        
        errors = aggregator.validate_aggregation_rules(config)
        
        assert len(errors) > 0
        assert any("less than degraded" in error for error in errors)
    
    def test_update_default_config_success(self, aggregator, custom_config):
        """Test successful default config update."""
        success = aggregator.update_default_config(custom_config)
        
        assert success is True
        assert aggregator.default_config == custom_config
    
    def test_update_default_config_failure(self, aggregator):
        """Test failed default config update with invalid config."""
        invalid_config = AggregationConfig(
            priority_config=PriorityConfig(mcp_priority_weight=2.0)  # Invalid
        )
        
        success = aggregator.update_default_config(invalid_config)
        
        assert success is False
        assert aggregator.default_config != invalid_config


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_aggregation_with_invalid_config_uses_default(self, aggregator, successful_mcp_result):
        """Test aggregation with invalid config falls back to default."""
        invalid_config = AggregationConfig(
            priority_config=PriorityConfig(mcp_priority_weight=2.0)  # Invalid
        )
        
        # Should not raise exception, should use default config
        result = aggregator.aggregate_dual_results(
            mcp_result=successful_mcp_result,
            rest_result=None,
            aggregation_config=invalid_config
        )
        
        assert isinstance(result, DualHealthCheckResult)
        assert result.overall_status != ServerStatus.UNKNOWN
    
    def test_aggregation_with_very_old_timestamps(self, aggregator):
        """Test aggregation with very old timestamps."""
        old_timestamp = datetime.now() - timedelta(days=365)
        
        mcp_result = MCPHealthCheckResult(
            server_name="old-server",
            timestamp=old_timestamp,
            success=True,
            response_time_ms=100.0
        )
        
        result = aggregator.aggregate_dual_results(
            mcp_result=mcp_result,
            rest_result=None
        )
        
        assert result.timestamp == old_timestamp
        assert result.server_name == "old-server"
    
    def test_aggregation_with_extreme_response_times(self, aggregator):
        """Test aggregation with extreme response times."""
        mcp_result = MCPHealthCheckResult(
            server_name="slow-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=60000.0  # 1 minute
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="slow-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=1.0,  # 1ms
            status_code=200,
            health_endpoint_url="http://test/health"
        )
        
        result = aggregator.aggregate_dual_results(
            mcp_result=mcp_result,
            rest_result=rest_result
        )
        
        # Should handle extreme values gracefully
        assert result.combined_response_time_ms > 0
        assert result.health_score >= 0.0
        assert result.health_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])