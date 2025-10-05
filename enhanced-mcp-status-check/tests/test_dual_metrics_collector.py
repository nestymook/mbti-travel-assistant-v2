"""
Tests for Enhanced MCP Status Check Dual Metrics Collector

This module contains comprehensive tests for the DualMetricsCollector class
and related metrics functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from models import (
    DualHealthCheckResult, MCPHealthCheckResult, RESTHealthCheckResult,
    ServerStatus, MCPValidationResult, RESTValidationResult,
    MCPMetrics, RESTMetrics, CombinedMetrics, TimeWindow,
    MetricsAggregationReport, MetricDataPoint, MetricSeries, MetricType
)
from services.dual_metrics_collector import DualMetricsCollector


class TestDualMetricsCollector:
    """Test cases for DualMetricsCollector class."""
    
    @pytest.fixture
    def collector(self):
        """Create a DualMetricsCollector instance for testing."""
        return DualMetricsCollector(retention_period=timedelta(hours=1))
    
    @pytest.fixture
    def sample_mcp_result(self):
        """Create a sample MCP health check result."""
        return MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=150.0,
            tools_count=5,
            expected_tools_found=["tool1", "tool2", "tool3"],
            missing_tools=["tool4"],
            validation_result=MCPValidationResult(
                is_valid=True,
                tools_count=5,
                expected_tools_found=["tool1", "tool2", "tool3"],
                missing_tools=["tool4"],
                validation_errors=[]
            ),
            request_id="test-request-123"
        )
    
    @pytest.fixture
    def sample_rest_result(self):
        """Create a sample REST health check result."""
        return RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=120.0,
            status_code=200,
            response_body={"status": "healthy", "uptime": 3600},
            health_endpoint_url="http://test-server/health",
            validation_result=RESTValidationResult(
                is_valid=True,
                http_status_valid=True,
                response_format_valid=True,
                health_indicators_present=True,
                validation_errors=[]
            )
        )
    
    @pytest.fixture
    def sample_dual_result(self, sample_mcp_result, sample_rest_result):
        """Create a sample dual health check result."""
        return DualHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=sample_mcp_result,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=5,
            rest_result=sample_rest_result,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            combined_response_time_ms=135.0,
            health_score=0.95,
            available_paths=["mcp", "rest"]
        )
    
    def test_initialization(self, collector):
        """Test DualMetricsCollector initialization."""
        assert collector.retention_period == timedelta(hours=1)
        assert len(collector.get_all_server_names()) == 0
        assert collector._shutdown_event is not None
    
    def test_record_mcp_health_check_result(self, collector, sample_mcp_result):
        """Test recording MCP health check result."""
        collector.record_mcp_health_check_result(sample_mcp_result)
        
        # Verify metrics were created
        mcp_metrics = collector.get_mcp_metrics("test-server")
        assert mcp_metrics is not None
        assert mcp_metrics.server_name == "test-server"
        assert mcp_metrics.success_count == 1
        assert mcp_metrics.total_requests == 1
        assert mcp_metrics.validation_success_count == 1
        
        # Verify response time was recorded
        assert len(mcp_metrics.response_times.data_points) == 1
        assert mcp_metrics.response_times.data_points[0].value == 150.0
        
        # Verify tool metrics were recorded
        assert len(mcp_metrics.tools_count_series.data_points) == 1
        assert mcp_metrics.tools_count_series.data_points[0].value == 5.0
    
    def test_record_rest_health_check_result(self, collector, sample_rest_result):
        """Test recording REST health check result."""
        collector.record_rest_health_check_result(sample_rest_result)
        
        # Verify metrics were created
        rest_metrics = collector.get_rest_metrics("test-server")
        assert rest_metrics is not None
        assert rest_metrics.server_name == "test-server"
        assert rest_metrics.success_count == 1
        assert rest_metrics.total_requests == 1
        assert rest_metrics.health_endpoint_available_count == 1
        
        # Verify response time was recorded
        assert len(rest_metrics.response_times.data_points) == 1
        assert rest_metrics.response_times.data_points[0].value == 120.0
        
        # Verify status code was recorded
        assert rest_metrics.status_code_counts[200] == 1
    
    def test_record_dual_health_check_result(self, collector, sample_dual_result):
        """Test recording dual health check result."""
        collector.record_dual_health_check_result(sample_dual_result)
        
        # Verify all metrics were created
        mcp_metrics = collector.get_mcp_metrics("test-server")
        rest_metrics = collector.get_rest_metrics("test-server")
        combined_metrics = collector.get_combined_metrics("test-server")
        
        assert mcp_metrics is not None
        assert rest_metrics is not None
        assert combined_metrics is not None
        
        # Verify MCP metrics
        assert mcp_metrics.success_count == 1
        assert len(mcp_metrics.response_times.data_points) == 1
        
        # Verify REST metrics
        assert rest_metrics.success_count == 1
        assert len(rest_metrics.response_times.data_points) == 1
        
        # Verify combined metrics
        assert combined_metrics.overall_availability_count == 1
        assert len(combined_metrics.combined_response_times.data_points) == 1
    
    def test_record_failure_scenarios(self, collector):
        """Test recording various failure scenarios."""
        # MCP failure with connection error
        mcp_failure = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            connection_error="Connection refused"
        )
        collector.record_mcp_health_check_result(mcp_failure)
        
        mcp_metrics = collector.get_mcp_metrics("test-server")
        assert mcp_metrics.failure_count == 1
        assert mcp_metrics.connection_errors == 1
        
        # REST failure with HTTP error
        rest_failure = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=3000.0,
            status_code=500,
            http_error="Internal Server Error"
        )
        collector.record_rest_health_check_result(rest_failure)
        
        rest_metrics = collector.get_rest_metrics("test-server")
        assert rest_metrics.failure_count == 1
        assert rest_metrics.http_errors == 1
        assert rest_metrics.status_code_counts[500] == 1
    
    def test_generate_aggregation_report(self, collector, sample_dual_result):
        """Test generating aggregation report."""
        # Record some metrics
        collector.record_dual_health_check_result(sample_dual_result)
        
        # Generate report
        report = collector.generate_aggregation_report("test-server", TimeWindow.LAST_HOUR)
        
        assert report is not None
        assert report.server_name == "test-server"
        assert report.time_window == TimeWindow.LAST_HOUR
        assert report.mcp_success_rate == 1.0
        assert report.rest_success_rate == 1.0
        assert report.combined_success_rate == 1.0
        assert report.mcp_average_response_time == 150.0
        assert report.rest_average_response_time == 120.0
    
    def test_generate_aggregation_report_nonexistent_server(self, collector):
        """Test generating report for non-existent server."""
        report = collector.generate_aggregation_report("nonexistent-server")
        assert report is None
    
    def test_generate_all_servers_report(self, sample_mcp_result, sample_rest_result):
        """Test generating reports for all servers."""
        # Create a fresh collector for this test
        collector = DualMetricsCollector(retention_period=timedelta(hours=1))
        
        # Create dual results for multiple servers
        dual_result1 = DualHealthCheckResult(
            server_name="server1",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=sample_mcp_result,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=5,
            rest_result=sample_rest_result,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            combined_response_time_ms=135.0,
            health_score=0.95,
            available_paths=["mcp", "rest"]
        )
        dual_result1.mcp_result.server_name = "server1"
        dual_result1.rest_result.server_name = "server1"
        
        dual_result2 = DualHealthCheckResult(
            server_name="server2",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=sample_mcp_result,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=5,
            rest_result=sample_rest_result,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            combined_response_time_ms=135.0,
            health_score=0.95,
            available_paths=["mcp", "rest"]
        )
        dual_result2.mcp_result.server_name = "server2"
        dual_result2.rest_result.server_name = "server2"
        
        collector.record_dual_health_check_result(dual_result1)
        collector.record_dual_health_check_result(dual_result2)
        
        # Generate reports
        reports = collector.generate_all_servers_report(TimeWindow.LAST_HOUR)
        
        assert len(reports) == 2
        server_names = {report.server_name for report in reports}
        assert server_names == {"server1", "server2"}
    
    def test_get_metrics_summary(self, collector, sample_dual_result):
        """Test getting metrics summary."""
        collector.record_dual_health_check_result(sample_dual_result)
        
        summary = collector.get_metrics_summary()
        
        assert summary["total_servers_monitored"] == 1
        assert summary["mcp_servers_count"] == 1
        assert summary["rest_servers_count"] == 1
        assert summary["combined_servers_count"] == 1
        assert "test-server" in summary["servers"]
        
        server_summary = summary["servers"]["test-server"]
        assert server_summary["mcp_enabled"] is True
        assert server_summary["rest_enabled"] is True
        assert server_summary["mcp_total_requests"] == 1
        assert server_summary["rest_total_requests"] == 1
    
    def test_cleanup_old_metrics(self, collector):
        """Test cleanup of old metrics."""
        # Create metrics with old timestamps
        old_timestamp = datetime.now() - timedelta(hours=2)
        
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=old_timestamp,
            success=True,
            response_time_ms=100.0
        )
        collector.record_mcp_health_check_result(mcp_result)
        
        # Verify metrics exist
        mcp_metrics = collector.get_mcp_metrics("test-server")
        assert len(mcp_metrics.response_times.data_points) == 1
        
        # Manually set old timestamp on data point
        mcp_metrics.response_times.data_points[0].timestamp = old_timestamp
        
        # Run cleanup
        collector.cleanup_old_metrics()
        
        # Verify old data was removed
        assert len(mcp_metrics.response_times.data_points) == 0
    
    def test_reset_metrics(self, sample_mcp_result, sample_rest_result):
        """Test resetting metrics."""
        # Create a fresh collector for this test
        collector = DualMetricsCollector(retention_period=timedelta(hours=1))
        
        # Create dual results for multiple servers
        dual_result1 = DualHealthCheckResult(
            server_name="server1",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=sample_mcp_result,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=5,
            rest_result=sample_rest_result,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            combined_response_time_ms=135.0,
            health_score=0.95,
            available_paths=["mcp", "rest"]
        )
        dual_result1.mcp_result.server_name = "server1"
        dual_result1.rest_result.server_name = "server1"
        
        dual_result2 = DualHealthCheckResult(
            server_name="server2",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=sample_mcp_result,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=5,
            rest_result=sample_rest_result,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            combined_response_time_ms=135.0,
            health_score=0.95,
            available_paths=["mcp", "rest"]
        )
        dual_result2.mcp_result.server_name = "server2"
        dual_result2.rest_result.server_name = "server2"
        
        collector.record_dual_health_check_result(dual_result1)
        collector.record_dual_health_check_result(dual_result2)
        
        assert len(collector.get_all_server_names()) == 2
        
        # Reset specific server
        collector.reset_metrics("server1")
        assert "server1" not in collector.get_all_server_names()
        assert "server2" in collector.get_all_server_names()
        
        # Reset all servers
        collector.reset_metrics()
        assert len(collector.get_all_server_names()) == 0
    
    def test_export_import_metrics_data(self, collector, sample_dual_result):
        """Test exporting and importing metrics data."""
        # Record some metrics
        collector.record_dual_health_check_result(sample_dual_result)
        
        # Export data
        export_data = collector.export_metrics_data()
        
        assert "mcp_metrics" in export_data
        assert "rest_metrics" in export_data
        assert "combined_metrics" in export_data
        assert "test-server" in export_data["mcp_metrics"]
        
        # Reset metrics
        collector.reset_metrics()
        assert len(collector.get_all_server_names()) == 0
        
        # Import data
        collector.import_metrics_data(export_data)
        
        # Verify data was restored
        assert len(collector.get_all_server_names()) == 1
        mcp_metrics = collector.get_mcp_metrics("test-server")
        assert mcp_metrics is not None
        assert mcp_metrics.success_count == 1
    
    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, collector):
        """Test start and stop lifecycle."""
        # Start collector
        await collector.start()
        assert collector._cleanup_task is not None
        assert not collector._cleanup_task.done()
        
        # Stop collector
        await collector.stop()
        assert collector._shutdown_event.is_set()
    
    def test_multiple_metrics_aggregation(self, collector):
        """Test aggregation with multiple data points."""
        server_name = "test-server"
        
        # Record multiple MCP results
        for i in range(5):
            mcp_result = MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=i < 4,  # 4 successes, 1 failure
                response_time_ms=100.0 + i * 10,  # 100, 110, 120, 130, 140
                tools_count=5 + i
            )
            collector.record_mcp_health_check_result(mcp_result)
        
        # Record multiple REST results
        for i in range(5):
            rest_result = RESTHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=i < 3,  # 3 successes, 2 failures
                response_time_ms=80.0 + i * 15,  # 80, 95, 110, 125, 140
                status_code=200 if i < 3 else 500
            )
            collector.record_rest_health_check_result(rest_result)
        
        # Verify aggregated metrics
        mcp_metrics = collector.get_mcp_metrics(server_name)
        rest_metrics = collector.get_rest_metrics(server_name)
        
        assert mcp_metrics.success_count == 4
        assert mcp_metrics.failure_count == 1
        assert mcp_metrics.get_success_rate() == 0.8
        
        assert rest_metrics.success_count == 3
        assert rest_metrics.failure_count == 2
        assert rest_metrics.get_success_rate() == 0.6
        
        # Test response time calculations
        assert mcp_metrics.get_average_response_time() == 120.0  # (100+110+120+130+140)/5
        assert rest_metrics.get_average_response_time() == 110.0  # (80+95+110+125+140)/5
    
    def test_error_type_tracking(self, collector):
        """Test tracking of different error types."""
        server_name = "test-server"
        
        # Record different MCP error types
        mcp_connection_error = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=0.0,
            connection_error="Connection refused"
        )
        collector.record_mcp_health_check_result(mcp_connection_error)
        
        mcp_timeout_error = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            mcp_error={"code": -32000, "message": "Request timeout"}
        )
        collector.record_mcp_health_check_result(mcp_timeout_error)
        
        mcp_protocol_error = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=100.0,
            mcp_error={"code": -32600, "message": "Invalid Request"}
        )
        collector.record_mcp_health_check_result(mcp_protocol_error)
        
        # Record different REST error types
        rest_connection_error = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=0.0,
            connection_error="Connection refused"
        )
        collector.record_rest_health_check_result(rest_connection_error)
        
        rest_timeout_error = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=10000.0,
            http_error="Request timeout"
        )
        collector.record_rest_health_check_result(rest_timeout_error)
        
        rest_http_error = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=200.0,
            status_code=500,
            http_error="Internal Server Error"
        )
        collector.record_rest_health_check_result(rest_http_error)
        
        # Verify error tracking
        mcp_metrics = collector.get_mcp_metrics(server_name)
        rest_metrics = collector.get_rest_metrics(server_name)
        
        assert mcp_metrics.connection_errors == 1
        assert mcp_metrics.timeout_errors == 1
        assert mcp_metrics.protocol_errors == 1
        
        assert rest_metrics.connection_errors == 1
        assert rest_metrics.timeout_errors == 1
        assert rest_metrics.http_errors == 1
        
        # Verify error breakdown in report
        report = collector.generate_aggregation_report(server_name)
        assert report.error_breakdown["mcp_connection_errors"] == 1
        assert report.error_breakdown["mcp_timeout_errors"] == 1
        assert report.error_breakdown["mcp_protocol_errors"] == 1
        assert report.error_breakdown["rest_connection_errors"] == 1
        assert report.error_breakdown["rest_timeout_errors"] == 1
        assert report.error_breakdown["rest_http_errors"] == 1


class TestMetricsModels:
    """Test cases for metrics model classes."""
    
    def test_metric_data_point(self):
        """Test MetricDataPoint functionality."""
        timestamp = datetime.now()
        data_point = MetricDataPoint(
            timestamp=timestamp,
            value=123.45,
            labels={"server": "test", "type": "response_time"}
        )
        
        # Test serialization
        data_dict = data_point.to_dict()
        assert data_dict["timestamp"] == timestamp.isoformat()
        assert data_dict["value"] == 123.45
        assert data_dict["labels"]["server"] == "test"
        
        # Test deserialization
        restored = MetricDataPoint.from_dict(data_dict)
        assert restored.timestamp == timestamp
        assert restored.value == 123.45
        assert restored.labels == {"server": "test", "type": "response_time"}
    
    def test_metric_series(self):
        """Test MetricSeries functionality."""
        series = MetricSeries(
            metric_name="test_metric",
            metric_type=MetricType.RESPONSE_TIME,
            server_name="test-server",
            monitoring_method="mcp"
        )
        
        # Add data points
        series.add_data_point(100.0, {"status": "success"})
        series.add_data_point(150.0, {"status": "success"})
        series.add_data_point(200.0, {"status": "failure"})
        
        assert len(series.data_points) == 3
        
        # Test time window filtering
        recent_points = series.get_data_points_in_window(TimeWindow.LAST_HOUR)
        assert len(recent_points) == 3  # All points should be recent
        
        # Test average calculation
        average = series.calculate_average(TimeWindow.LAST_HOUR)
        assert average == 150.0  # (100 + 150 + 200) / 3
        
        # Test percentile calculation
        p50 = series.calculate_percentile(TimeWindow.LAST_HOUR, 50.0)
        assert p50 == 150.0  # Median value
        
        p95 = series.calculate_percentile(TimeWindow.LAST_HOUR, 95.0)
        assert p95 == 150.0  # 95th percentile (with 3 values, 95% index is 1.9, so index 1 = 150.0)
    
    def test_mcp_metrics(self):
        """Test MCPMetrics functionality."""
        metrics = MCPMetrics(server_name="test-server")
        
        # Record various metrics
        metrics.record_response_time(100.0)
        metrics.record_response_time(150.0)
        metrics.record_success()
        metrics.record_success()
        metrics.record_failure("connection")
        metrics.record_tools_count(5)
        metrics.record_expected_tools_found(4)
        metrics.record_missing_tools(1)
        metrics.record_validation_result(True)
        
        # Test calculations
        assert metrics.get_success_rate() == 2/3  # 2 successes out of 3 total
        assert metrics.get_failure_rate() == 1/3  # 1 failure out of 3 total
        assert metrics.get_validation_success_rate() == 1.0  # 1 success out of 1 validation
        assert metrics.connection_errors == 1
        
        # Test serialization
        data_dict = metrics.to_dict()
        assert data_dict["server_name"] == "test-server"
        assert data_dict["success_count"] == 2
        assert data_dict["failure_count"] == 1
        
        # Test deserialization
        restored = MCPMetrics.from_dict(data_dict)
        assert restored.server_name == "test-server"
        assert restored.success_count == 2
        assert restored.failure_count == 1
    
    def test_rest_metrics(self):
        """Test RESTMetrics functionality."""
        metrics = RESTMetrics(server_name="test-server")
        
        # Record various metrics
        metrics.record_response_time(80.0)
        metrics.record_response_time(120.0)
        metrics.record_success()
        metrics.record_failure("http")
        metrics.record_status_code(200)
        metrics.record_status_code(200)
        metrics.record_status_code(500)
        metrics.record_health_endpoint_availability(True)
        metrics.record_health_endpoint_availability(False)
        metrics.record_response_body_validation(True)
        
        # Test calculations
        assert metrics.get_success_rate() == 0.5  # 1 success out of 2 total
        assert metrics.get_failure_rate() == 0.5  # 1 failure out of 2 total
        assert metrics.get_health_endpoint_availability_rate() == 0.5  # 1 available out of 2 checks
        assert metrics.get_response_body_validation_rate() == 1.0  # 1 valid out of 1 validation
        assert metrics.http_errors == 1
        
        # Test status code tracking
        assert metrics.status_code_counts[200] == 2
        assert metrics.status_code_counts[500] == 1
        
        # Test most common status codes
        top_codes = metrics.get_most_common_status_codes(2)
        assert len(top_codes) == 2
        assert top_codes[0] == (200, 2)  # Most common
        assert top_codes[1] == (500, 1)  # Second most common
    
    def test_combined_metrics(self):
        """Test CombinedMetrics functionality."""
        mcp_metrics = MCPMetrics(server_name="test-server")
        rest_metrics = RESTMetrics(server_name="test-server")
        
        # Add some data to individual metrics
        mcp_metrics.record_success()
        mcp_metrics.record_success()
        rest_metrics.record_success()
        rest_metrics.record_failure()
        
        combined_metrics = CombinedMetrics(
            server_name="test-server",
            mcp_metrics=mcp_metrics,
            rest_metrics=rest_metrics
        )
        
        # Record combined metrics
        combined_metrics.record_combined_response_time(100.0, 80.0)
        combined_metrics.record_overall_availability(True)
        combined_metrics.record_overall_availability(False)
        
        # Test calculations
        combined_success_rate = combined_metrics.get_combined_success_rate()
        assert combined_success_rate == 0.75  # 3 successes out of 4 total (2 MCP + 2 REST)
        
        availability_rate = combined_metrics.get_overall_availability_rate()
        assert availability_rate == 0.5  # 1 available out of 2 checks
        
        # Test combined response time
        avg_combined_time = combined_metrics.get_combined_average_response_time()
        assert avg_combined_time == 90.0  # (100 + 80) / 2
    
    def test_metrics_aggregation_report(self):
        """Test MetricsAggregationReport functionality."""
        timestamp = datetime.now()
        report = MetricsAggregationReport(
            server_name="test-server",
            report_timestamp=timestamp,
            time_window=TimeWindow.LAST_HOUR,
            mcp_success_rate=0.95,
            mcp_average_response_time=120.0,
            mcp_p95_response_time=200.0,
            mcp_tools_availability_rate=0.98,
            rest_success_rate=0.90,
            rest_average_response_time=100.0,
            rest_p95_response_time=180.0,
            rest_endpoint_availability_rate=0.99,
            combined_success_rate=0.92,
            combined_average_response_time=110.0,
            overall_availability_rate=0.97,
            top_http_status_codes=[(200, 95), (500, 3), (404, 2)],
            error_breakdown={"connection_errors": 1, "timeout_errors": 2}
        )
        
        # Test serialization
        data_dict = report.to_dict()
        assert data_dict["server_name"] == "test-server"
        assert data_dict["report_timestamp"] == timestamp.isoformat()
        assert data_dict["time_window"] == "1h"
        assert data_dict["mcp_success_rate"] == 0.95
        assert data_dict["top_http_status_codes"] == [(200, 95), (500, 3), (404, 2)]
        
        # Test deserialization
        restored = MetricsAggregationReport.from_dict(data_dict)
        assert restored.server_name == "test-server"
        assert restored.report_timestamp == timestamp
        assert restored.time_window == TimeWindow.LAST_HOUR
        assert restored.mcp_success_rate == 0.95