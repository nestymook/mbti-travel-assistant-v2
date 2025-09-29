"""
Tests for Comprehensive Error Monitor

This module tests the comprehensive error logging and monitoring capabilities
including structured logging, error correlation, alerting, and performance monitoring.
"""

import pytest
import asyncio
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from services.comprehensive_error_monitor import (
    ComprehensiveErrorMonitor,
    ErrorSeverity,
    AlertType,
    ErrorEvent,
    PerformanceMetric,
    Alert,
    MonitoringConfig
)


class TestComprehensiveErrorMonitor:
    """Test cases for ComprehensiveErrorMonitor."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def monitor_config(self):
        """Create monitoring configuration for testing."""
        return MonitoringConfig(
            error_rate_threshold=5.0,
            response_time_threshold_ms=1000.0,
            cache_miss_rate_threshold=30.0,
            memory_usage_threshold_mb=100.0,
            alert_cooldown_minutes=1,
            log_retention_days=7,
            enable_structured_logging=True,
            enable_performance_tracking=True,
            enable_alerting=True
        )
    
    @pytest.fixture
    def error_monitor(self, temp_log_dir, monitor_config):
        """Create ComprehensiveErrorMonitor instance for testing."""
        return ComprehensiveErrorMonitor(
            config=monitor_config,
            log_directory=temp_log_dir
        )
    
    @pytest.mark.asyncio
    async def test_error_logging_basic(self, error_monitor):
        """Test basic error logging functionality."""
        test_error = ValueError("Test validation error")
        
        error_id = await error_monitor.log_error(
            service_name="test_service",
            operation_name="test_operation",
            error=test_error,
            context={"key": "value"},
            correlation_id="test-correlation-123",
            user_id="user-456",
            request_id="req-789",
            response_time_ms=150.0,
            retry_count=1
        )
        
        assert error_id is not None
        assert len(error_monitor._error_events) == 1
        
        error_event = error_monitor._error_events[0]
        assert error_event.id == error_id
        assert error_event.service_name == "test_service"
        assert error_event.operation_name == "test_operation"
        assert error_event.error_type == "ValueError"
        assert error_event.error_message == "Test validation error"
        assert error_event.severity == ErrorSeverity.MEDIUM
        assert error_event.context == {"key": "value"}
        assert error_event.correlation_id == "test-correlation-123"
        assert error_event.user_id == "user-456"
        assert error_event.request_id == "req-789"
        assert error_event.response_time_ms == 150.0
        assert error_event.retry_count == 1
    
    def test_error_severity_classification(self, error_monitor):
        """Test error severity classification."""
        # Critical errors
        auth_error = Exception("Authentication failed")
        assert error_monitor._classify_error_severity(auth_error) == ErrorSeverity.CRITICAL
        
        security_error = Exception("Security violation detected")
        assert error_monitor._classify_error_severity(security_error) == ErrorSeverity.CRITICAL
        
        # High severity errors
        connection_error = ConnectionError("Connection timeout")
        assert error_monitor._classify_error_severity(connection_error) == ErrorSeverity.HIGH
        
        service_error = Exception("Service unavailable")
        assert error_monitor._classify_error_severity(service_error) == ErrorSeverity.HIGH
        
        # Medium severity errors
        validation_error = ValueError("Invalid input format")
        assert error_monitor._classify_error_severity(validation_error) == ErrorSeverity.MEDIUM
        
        # Low severity errors
        generic_error = Exception("Generic error")
        assert error_monitor._classify_error_severity(generic_error) == ErrorSeverity.LOW
    
    @pytest.mark.asyncio
    async def test_performance_metric_logging(self, error_monitor):
        """Test performance metric logging."""
        await error_monitor.log_performance_metric(
            service_name="test_service",
            operation_name="test_operation",
            response_time_ms=250.0,
            success=True
        )
        
        assert len(error_monitor._performance_metrics) == 1
        
        metric = error_monitor._performance_metrics[0]
        assert metric.service_name == "test_service"
        assert metric.operation_name == "test_operation"
        assert metric.response_time_ms == 250.0
        assert metric.success is True
        assert metric.error_type is None
        
        # Check service metrics were updated
        assert "test_service" in error_monitor._service_metrics
        service_metrics = error_monitor._service_metrics["test_service"]
        assert service_metrics["total_operations"] == 1
        assert service_metrics["successful_operations"] == 1
        assert service_metrics["avg_response_time_ms"] == 250.0
    
    @pytest.mark.asyncio
    async def test_error_correlation_detection(self, error_monitor):
        """Test error correlation detection."""
        correlation_id = "test-correlation-123"
        
        # Log multiple errors with same correlation ID
        error1 = Exception("First error")
        error2 = Exception("Second error")
        
        await error_monitor.log_error(
            service_name="service1",
            operation_name="operation1",
            error=error1,
            correlation_id=correlation_id
        )
        
        await error_monitor.log_error(
            service_name="service2",
            operation_name="operation2",
            error=error2,
            correlation_id=correlation_id
        )
        
        # Check correlation was detected
        assert correlation_id in error_monitor._error_correlations
        assert len(error_monitor._error_correlations[correlation_id]) == 2
    
    @pytest.mark.asyncio
    async def test_alert_creation_error_rate(self, error_monitor):
        """Test alert creation for high error rate."""
        # Add alert handler to capture alerts
        alerts_captured = []
        
        def alert_handler(alert):
            alerts_captured.append(alert)
        
        error_monitor.add_alert_handler(alert_handler)
        
        # Log multiple errors to trigger error rate alert
        for i in range(10):
            await error_monitor.log_error(
                service_name="test_service",
                operation_name="test_operation",
                error=Exception(f"Error {i}")
            )
        
        # Check alert was created
        assert len(alerts_captured) > 0
        alert = alerts_captured[0]
        assert alert.alert_type == AlertType.ERROR_RATE_HIGH
        assert alert.service_name == "test_service"
        assert alert.severity == ErrorSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_alert_creation_critical_error(self, error_monitor):
        """Test alert creation for critical errors."""
        alerts_captured = []
        
        def alert_handler(alert):
            alerts_captured.append(alert)
        
        error_monitor.add_alert_handler(alert_handler)
        
        # Log critical error
        critical_error = Exception("Authentication failed")
        await error_monitor.log_error(
            service_name="test_service",
            operation_name="test_operation",
            error=critical_error
        )
        
        # Check critical alert was created
        assert len(alerts_captured) > 0
        alert = alerts_captured[0]
        assert alert.alert_type == AlertType.SERVICE_DOWN
        assert alert.severity == ErrorSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_alert_creation_high_response_time(self, error_monitor):
        """Test alert creation for high response time."""
        alerts_captured = []
        
        def alert_handler(alert):
            alerts_captured.append(alert)
        
        error_monitor.add_alert_handler(alert_handler)
        
        # Log performance metric with high response time
        await error_monitor.log_performance_metric(
            service_name="test_service",
            operation_name="test_operation",
            response_time_ms=2000.0,  # Above threshold
            success=True
        )
        
        # Check response time alert was created
        assert len(alerts_captured) > 0
        alert = alerts_captured[0]
        assert alert.alert_type == AlertType.RESPONSE_TIME_HIGH
        assert alert.severity == ErrorSeverity.MEDIUM
    
    @pytest.mark.asyncio
    async def test_alert_cooldown(self, error_monitor):
        """Test alert cooldown functionality."""
        alerts_captured = []
        
        def alert_handler(alert):
            alerts_captured.append(alert)
        
        error_monitor.add_alert_handler(alert_handler)
        
        # Log critical error twice quickly
        critical_error = Exception("Authentication failed")
        
        await error_monitor.log_error(
            service_name="test_service",
            operation_name="test_operation",
            error=critical_error
        )
        
        await error_monitor.log_error(
            service_name="test_service",
            operation_name="test_operation",
            error=critical_error
        )
        
        # Should only have one alert due to cooldown
        service_down_alerts = [
            alert for alert in alerts_captured
            if alert.alert_type == AlertType.SERVICE_DOWN
        ]
        assert len(service_down_alerts) == 1
    
    @pytest.mark.asyncio
    async def test_error_pattern_detection(self, error_monitor):
        """Test error pattern detection and alerting."""
        # Start monitoring
        await error_monitor.start()
        
        try:
            alerts_captured = []
            
            def alert_handler(alert):
                alerts_captured.append(alert)
            
            error_monitor.add_alert_handler(alert_handler)
            
            # Log repeated errors to create pattern
            for i in range(5):
                await error_monitor.log_error(
                    service_name="test_service",
                    operation_name="test_operation",
                    error=ValueError("Validation error")
                )
            
            # Trigger pattern check manually
            await error_monitor._check_pattern_alerts()
            
            # Check if pattern alert was created
            pattern_alerts = [
                alert for alert in alerts_captured
                if "pattern detected" in alert.title.lower()
            ]
            assert len(pattern_alerts) > 0
            
        finally:
            await error_monitor.stop()
    
    def test_error_summary_generation(self, error_monitor):
        """Test error summary generation."""
        # Add some test errors
        now = datetime.now()
        
        # Recent error (within last hour)
        recent_error = ErrorEvent(
            id="recent-1",
            timestamp=now - timedelta(minutes=30),
            service_name="service1",
            operation_name="operation1",
            error_type="ValueError",
            error_message="Recent error",
            severity=ErrorSeverity.MEDIUM,
            stack_trace=None,
            context={},
            correlation_id=None,
            user_id=None,
            request_id=None,
            response_time_ms=100.0
        )
        
        # Old error (more than a day ago)
        old_error = ErrorEvent(
            id="old-1",
            timestamp=now - timedelta(days=2),
            service_name="service2",
            operation_name="operation2",
            error_type="ConnectionError",
            error_message="Old error",
            severity=ErrorSeverity.HIGH,
            stack_trace=None,
            context={},
            correlation_id=None,
            user_id=None,
            request_id=None,
            response_time_ms=200.0
        )
        
        error_monitor._error_events = [recent_error, old_error]
        
        # Generate summary
        summary = error_monitor.get_error_summary()
        
        assert summary["total_errors"] == 2
        assert summary["recent_errors_1h"] == 1
        assert summary["daily_errors_24h"] == 1
        assert summary["error_by_severity"][ErrorSeverity.MEDIUM.value] == 1
        assert summary["error_by_severity"][ErrorSeverity.HIGH.value] == 1
        assert "service1" in summary["error_by_service"]
        assert "service2" in summary["error_by_service"]
    
    def test_service_health_report(self, error_monitor):
        """Test service health report generation."""
        # Add some test data
        error_monitor._service_metrics = {
            "service1": {
                "total_errors": 5,
                "error_types": {"ValueError": 3, "ConnectionError": 2},
                "severity_counts": {
                    "low": 1,
                    "medium": 2,
                    "high": 2,
                    "critical": 0
                },
                "total_operations": 100,
                "successful_operations": 95,
                "avg_response_time_ms": 150.0
            }
        }
        
        # Add test alert
        test_alert = Alert(
            id="alert-1",
            timestamp=datetime.now(),
            alert_type=AlertType.ERROR_RATE_HIGH,
            severity=ErrorSeverity.HIGH,
            title="High error rate",
            description="Error rate exceeded threshold",
            service_name="service1",
            threshold_value=5.0,
            current_value=10.0
        )
        error_monitor._alerts = [test_alert]
        
        # Generate health report
        report = error_monitor.get_service_health_report()
        
        assert "services" in report
        assert "alerts" in report
        assert "performance_summary" in report
        assert "error_patterns" in report
        
        assert "service1" in report["services"]
        assert report["alerts"]["total"] == 1
        assert len(report["alerts"]["active"]) == 1
    
    def test_alert_acknowledgment_and_resolution(self, error_monitor):
        """Test alert acknowledgment and resolution."""
        # Create test alert
        test_alert = Alert(
            id="alert-1",
            timestamp=datetime.now(),
            alert_type=AlertType.ERROR_RATE_HIGH,
            severity=ErrorSeverity.HIGH,
            title="High error rate",
            description="Error rate exceeded threshold",
            service_name="service1",
            threshold_value=5.0,
            current_value=10.0
        )
        error_monitor._alerts = [test_alert]
        
        # Test acknowledgment
        result = error_monitor.acknowledge_alert("alert-1")
        assert result is True
        assert test_alert.acknowledged is True
        
        # Test resolution
        result = error_monitor.resolve_alert("alert-1")
        assert result is True
        assert test_alert.resolved is True
        
        # Test non-existent alert
        result = error_monitor.acknowledge_alert("non-existent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_log_persistence(self, error_monitor, temp_log_dir):
        """Test log persistence to files."""
        # Add some test data
        await error_monitor.log_error(
            service_name="test_service",
            operation_name="test_operation",
            error=Exception("Test error")
        )
        
        await error_monitor.log_performance_metric(
            service_name="test_service",
            operation_name="test_operation",
            response_time_ms=100.0,
            success=True
        )
        
        # Persist logs
        await error_monitor._persist_logs()
        
        # Check files were created
        log_dir = Path(temp_log_dir)
        today = datetime.now().strftime('%Y%m%d')
        
        error_log_file = log_dir / f"error_events_{today}.json"
        metrics_log_file = log_dir / f"performance_metrics_{today}.json"
        alerts_log_file = log_dir / f"alerts_{today}.json"
        
        assert error_log_file.exists()
        assert metrics_log_file.exists()
        assert alerts_log_file.exists()
        
        # Check file contents
        with open(error_log_file, 'r') as f:
            error_data = json.load(f)
            assert len(error_data) == 1
            assert error_data[0]["service_name"] == "test_service"
        
        with open(metrics_log_file, 'r') as f:
            metrics_data = json.load(f)
            assert len(metrics_data) == 1
            assert metrics_data[0]["service_name"] == "test_service"
    
    @pytest.mark.asyncio
    async def test_background_tasks_lifecycle(self, error_monitor):
        """Test background tasks start and stop correctly."""
        # Start monitor
        await error_monitor.start()
        
        assert error_monitor._monitoring_task is not None
        assert error_monitor._cleanup_task is not None
        assert not error_monitor._monitoring_task.done()
        assert not error_monitor._cleanup_task.done()
        
        # Stop monitor
        await error_monitor.stop()
        
        assert error_monitor._monitoring_task.done()
        assert error_monitor._cleanup_task.done()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, error_monitor):
        """Test cleanup of old error events and metrics."""
        now = datetime.now()
        
        # Add old error event
        old_error = ErrorEvent(
            id="old-1",
            timestamp=now - timedelta(days=10),
            service_name="service1",
            operation_name="operation1",
            error_type="ValueError",
            error_message="Old error",
            severity=ErrorSeverity.LOW,
            stack_trace=None,
            context={},
            correlation_id=None,
            user_id=None,
            request_id=None,
            response_time_ms=100.0
        )
        
        # Add recent error event
        recent_error = ErrorEvent(
            id="recent-1",
            timestamp=now - timedelta(hours=1),
            service_name="service1",
            operation_name="operation1",
            error_type="ValueError",
            error_message="Recent error",
            severity=ErrorSeverity.LOW,
            stack_trace=None,
            context={},
            correlation_id=None,
            user_id=None,
            request_id=None,
            response_time_ms=100.0
        )
        
        error_monitor._error_events = [old_error, recent_error]
        
        # Run cleanup
        await error_monitor._cleanup_old_errors()
        
        # Check old error was removed
        assert len(error_monitor._error_events) == 1
        assert error_monitor._error_events[0].id == "recent-1"


class TestMonitoringConfig:
    """Test cases for MonitoringConfig."""
    
    def test_default_config(self):
        """Test default monitoring configuration."""
        config = MonitoringConfig()
        
        assert config.error_rate_threshold == 10.0
        assert config.response_time_threshold_ms == 5000.0
        assert config.cache_miss_rate_threshold == 50.0
        assert config.memory_usage_threshold_mb == 500.0
        assert config.alert_cooldown_minutes == 15
        assert config.log_retention_days == 30
        assert config.enable_structured_logging is True
        assert config.enable_performance_tracking is True
        assert config.enable_alerting is True
    
    def test_custom_config(self):
        """Test custom monitoring configuration."""
        config = MonitoringConfig(
            error_rate_threshold=5.0,
            response_time_threshold_ms=1000.0,
            cache_miss_rate_threshold=25.0,
            memory_usage_threshold_mb=200.0,
            alert_cooldown_minutes=5,
            log_retention_days=14,
            enable_structured_logging=False,
            enable_performance_tracking=False,
            enable_alerting=False
        )
        
        assert config.error_rate_threshold == 5.0
        assert config.response_time_threshold_ms == 1000.0
        assert config.cache_miss_rate_threshold == 25.0
        assert config.memory_usage_threshold_mb == 200.0
        assert config.alert_cooldown_minutes == 5
        assert config.log_retention_days == 14
        assert config.enable_structured_logging is False
        assert config.enable_performance_tracking is False
        assert config.enable_alerting is False


if __name__ == "__main__":
    pytest.main([__file__])