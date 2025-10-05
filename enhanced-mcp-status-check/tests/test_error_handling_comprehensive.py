"""
Comprehensive tests for error handling and logging system.

This module tests all aspects of the error handling and logging implementation
including error classification, recovery mechanisms, structured logging, and analysis.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from ..models.error_models import (
    ErrorDetails, ErrorSeverity, ErrorCategory, ErrorCode, ErrorContext,
    MCPProtocolError, HTTPRequestError, AuthenticationError, NetworkError,
    ValidationError, ErrorBuilder
)
from ..models.logging_models import (
    LogLevel, LogCategory, OperationType, StructuredLogEntry, LogContext,
    PerformanceMetrics, SecurityContext, HealthCheckLogEntry
)
from ..services.error_handler import ErrorHandler, ErrorRecoveryStrategy
from ..services.structured_logger import StructuredLogger, LogFormatter, FileLogOutput
from ..services.error_analyzer import ErrorAnalyzer, ErrorPattern, TroubleshootingRecommendation


class TestErrorModels:
    """Test error model classes."""
    
    def test_error_context_creation(self):
        """Test ErrorContext creation and serialization."""
        context = ErrorContext(
            server_name="test-server",
            endpoint_url="http://test.com/api",
            request_id="req-123",
            operation="health_check",
            additional_data={"key": "value"}
        )
        
        assert context.server_name == "test-server"
        assert context.endpoint_url == "http://test.com/api"
        assert context.request_id == "req-123"
        
        context_dict = context.to_dict()
        assert context_dict["server_name"] == "test-server"
        assert context_dict["additional_data"]["key"] == "value"
    
    def test_error_details_creation(self):
        """Test ErrorDetails creation and serialization."""
        context = ErrorContext(server_name="test-server")
        
        error = ErrorDetails(
            error_id="error-123",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.MCP_PROTOCOL,
            error_code=ErrorCode.MCP_CONNECTION_FAILED,
            message="Connection failed",
            context=context,
            retry_count=2,
            recovery_suggestions=["Check network", "Restart service"]
        )
        
        assert error.error_id == "error-123"
        assert error.severity == ErrorSeverity.ERROR
        assert error.category == ErrorCategory.MCP_PROTOCOL
        assert error.retry_count == 2
        assert len(error.recovery_suggestions) == 2
        
        error_dict = error.to_dict()
        assert error_dict["error_code"] == "MCP_CONNECTION_FAILED"
        assert error_dict["context"]["server_name"] == "test-server"
    
    def test_error_builder(self):
        """Test ErrorBuilder functionality."""
        context = ErrorContext(server_name="test-server")
        
        error = ErrorBuilder(ErrorCode.MCP_TOOLS_LIST_FAILED, "Tools list failed") \
            .with_severity(ErrorSeverity.WARNING) \
            .with_context(context) \
            .with_retry_count(1) \
            .with_recovery_suggestions(["Retry request"]) \
            .build()
        
        assert error.error_code == ErrorCode.MCP_TOOLS_LIST_FAILED
        assert error.severity == ErrorSeverity.WARNING
        assert error.context.server_name == "test-server"
        assert error.retry_count == 1
        assert "Retry request" in error.recovery_suggestions
    
    def test_mcp_protocol_error(self):
        """Test MCPProtocolError specific fields."""
        context = ErrorContext(server_name="mcp-server")
        
        error = ErrorBuilder(ErrorCode.MCP_INVALID_JSONRPC, "Invalid JSON-RPC") \
            .with_context(context) \
            .build_mcp_error(
                jsonrpc_version="2.0",
                method="tools/list",
                request_id="req-456",
                jsonrpc_error={"code": -32600, "message": "Invalid Request"}
            )
        
        assert isinstance(error, MCPProtocolError)
        assert error.category == ErrorCategory.MCP_PROTOCOL
        assert error.jsonrpc_version == "2.0"
        assert error.method == "tools/list"
        assert error.request_id == "req-456"
        assert error.jsonrpc_error["code"] == -32600
    
    def test_http_request_error(self):
        """Test HTTPRequestError specific fields."""
        context = ErrorContext(endpoint_url="http://api.test.com/health")
        
        error = ErrorBuilder(ErrorCode.HTTP_STATUS_ERROR, "HTTP 500 error") \
            .with_context(context) \
            .build_http_error(
                status_code=500,
                response_headers={"Content-Type": "application/json"},
                response_body='{"error": "Internal Server Error"}',
                request_method="GET",
                request_url="http://api.test.com/health"
            )
        
        assert isinstance(error, HTTPRequestError)
        assert error.category == ErrorCategory.HTTP_REQUEST
        assert error.status_code == 500
        assert error.request_method == "GET"
        assert error.response_headers["Content-Type"] == "application/json"


class TestLoggingModels:
    """Test logging model classes."""
    
    def test_log_context_creation(self):
        """Test LogContext creation and serialization."""
        context = LogContext(
            server_name="test-server",
            operation_type=OperationType.DUAL_HEALTH_CHECK,
            request_id="req-789",
            additional_fields={"custom": "data"}
        )
        
        assert context.server_name == "test-server"
        assert context.operation_type == OperationType.DUAL_HEALTH_CHECK
        
        context_dict = context.to_dict()
        assert context_dict["operation_type"] == "dual_health_check"
        assert context_dict["custom"] == "data"
    
    def test_performance_metrics(self):
        """Test PerformanceMetrics calculation."""
        start_time = datetime.utcnow()
        metrics = PerformanceMetrics(start_time=start_time)
        
        # Simulate some processing time
        metrics.end_time = start_time + timedelta(milliseconds=150)
        duration = metrics.calculate_duration()
        
        assert duration == pytest.approx(150.0, rel=1e-2)
        assert metrics.duration_ms == pytest.approx(150.0, rel=1e-2)
    
    def test_structured_log_entry(self):
        """Test StructuredLogEntry creation and serialization."""
        context = LogContext(server_name="test-server")
        metrics = PerformanceMetrics(start_time=datetime.utcnow())
        
        log_entry = StructuredLogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            category=LogCategory.HEALTH_CHECK,
            message="Health check completed",
            context=context,
            performance_metrics=metrics,
            tags=["health", "monitoring"]
        )
        
        assert log_entry.level == LogLevel.INFO
        assert log_entry.category == LogCategory.HEALTH_CHECK
        assert len(log_entry.tags) == 2
        
        log_dict = log_entry.to_dict()
        assert log_dict["level"] == "info"
        assert log_dict["category"] == "health_check"
        assert log_dict["context"]["server_name"] == "test-server"
    
    def test_health_check_log_entry(self):
        """Test HealthCheckLogEntry specific functionality."""
        log_entry = HealthCheckLogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            category=LogCategory.HEALTH_CHECK,
            message="Health check succeeded",
            server_name="test-server",
            check_type="dual",
            success=True,
            response_time_ms=125.5,
            status_code=200
        )
        
        assert log_entry.server_name == "test-server"
        assert log_entry.check_type == "dual"
        assert log_entry.success is True
        assert log_entry.response_time_ms == 125.5
        assert log_entry.context.server_name == "test-server"
        assert log_entry.context.additional_fields["success"] is True


class TestErrorHandler:
    """Test ErrorHandler functionality."""
    
    @pytest.fixture
    def error_handler(self):
        """Create ErrorHandler instance for testing."""
        return ErrorHandler()
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock()
    
    def test_error_recovery_strategy(self):
        """Test ErrorRecoveryStrategy calculations."""
        strategy = ErrorRecoveryStrategy(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0
        )
        
        # Test delay calculations
        assert strategy.calculate_delay(0) == 1.0
        assert strategy.calculate_delay(1) == 2.0
        assert strategy.calculate_delay(2) == 4.0
        assert strategy.calculate_delay(10) == 10.0  # Max delay
        
        # Test retry decisions
        error = ErrorDetails(
            error_id="test",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.NETWORK,
            error_code=ErrorCode.NETWORK_TIMEOUT,
            message="Timeout",
            is_recoverable=True
        )
        
        assert strategy.should_retry(error, 0) is True
        assert strategy.should_retry(error, 2) is True
        assert strategy.should_retry(error, 3) is False  # Max retries reached
        
        # Test non-recoverable error
        error.is_recoverable = False
        assert strategy.should_retry(error, 0) is False
    
    def test_mcp_protocol_error_handling(self, error_handler):
        """Test MCP protocol error handling."""
        context = ErrorContext(
            server_name="mcp-server",
            endpoint_url="http://mcp.test.com"
        )
        
        exception = ConnectionError("Connection refused")
        jsonrpc_data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "req-123"
        }
        
        error = error_handler.handle_mcp_protocol_error(
            exception, context, jsonrpc_data
        )
        
        assert isinstance(error, MCPProtocolError)
        assert error.category == ErrorCategory.MCP_PROTOCOL
        assert error.error_code == ErrorCode.MCP_CONNECTION_FAILED
        assert error.jsonrpc_version == "2.0"
        assert error.method == "tools/list"
        assert len(error.recovery_suggestions) > 0
    
    def test_http_request_error_handling(self, error_handler):
        """Test HTTP request error handling."""
        context = ErrorContext(
            server_name="http-server",
            endpoint_url="http://api.test.com/health"
        )
        
        exception = Exception("HTTP 500 Internal Server Error")
        
        error = error_handler.handle_http_request_error(
            exception, context, status_code=500
        )
        
        assert isinstance(error, HTTPRequestError)
        assert error.category == ErrorCategory.HTTP_REQUEST
        assert error.error_code == ErrorCode.HTTP_STATUS_ERROR
        assert error.status_code == 500
        assert len(error.recovery_suggestions) > 0
    
    def test_authentication_error_handling(self, error_handler):
        """Test authentication error handling."""
        context = ErrorContext(server_name="auth-server")
        exception = Exception("Token expired")
        auth_data = {
            "auth_type": "jwt",
            "token_type": "bearer",
            "expires_at": datetime.utcnow() - timedelta(hours=1)
        }
        
        error = error_handler.handle_authentication_error(
            exception, context, auth_data
        )
        
        assert isinstance(error, AuthenticationError)
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.error_code == ErrorCode.AUTH_TOKEN_EXPIRED
        assert error.auth_type == "jwt"
        assert error.token_type == "bearer"
    
    def test_network_error_handling(self, error_handler):
        """Test network error handling."""
        context = ErrorContext(server_name="network-server")
        exception = Exception("Name resolution failed")
        network_data = {
            "host": "test.example.com",
            "port": 8080,
            "dns_time": 5.2
        }
        
        error = error_handler.handle_network_error(
            exception, context, network_data
        )
        
        assert isinstance(error, NetworkError)
        assert error.category == ErrorCategory.NETWORK
        assert error.error_code == ErrorCode.NETWORK_DNS_RESOLUTION
        assert error.host == "test.example.com"
        assert error.port == 8080
        assert error.dns_resolution_time == 5.2
    
    def test_validation_error_handling(self, error_handler):
        """Test validation error handling."""
        context = ErrorContext(server_name="validation-server")
        exception = Exception("Missing required field")
        validation_data = {
            "field_name": "server_name",
            "expected_type": "string",
            "actual_value": None,
            "validation_rule": "required"
        }
        
        error = error_handler.handle_validation_error(
            exception, context, validation_data
        )
        
        assert isinstance(error, ValidationError)
        assert error.category == ErrorCategory.VALIDATION
        assert error.error_code == ErrorCode.VALIDATION_PARAMETER_MISSING
        assert error.field_name == "server_name"
        assert error.expected_type == "string"
    
    @pytest.mark.asyncio
    async def test_retry_with_recovery(self, error_handler):
        """Test retry mechanism with recovery strategy."""
        context = ErrorContext(server_name="retry-server")
        
        # Mock operation that fails twice then succeeds
        call_count = 0
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Connection failed")
            return "success"
        
        # Should succeed after retries
        result = await error_handler.retry_with_recovery(
            mock_operation, context
        )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_with_recovery_max_retries(self, error_handler):
        """Test retry mechanism reaching max retries."""
        context = ErrorContext(server_name="retry-server")
        
        # Mock operation that always fails
        async def mock_operation():
            raise ConnectionError("Connection failed")
        
        # Should raise exception after max retries
        with pytest.raises(Exception, match="Operation failed after .* retries"):
            await error_handler.retry_with_recovery(
                mock_operation, context
            )
    
    def test_error_callback_registration(self, error_handler):
        """Test error callback registration and triggering."""
        callback_called = False
        callback_error = None
        
        def test_callback(error: ErrorDetails):
            nonlocal callback_called, callback_error
            callback_called = True
            callback_error = error
        
        # Register callback
        error_handler.register_error_callback(
            ErrorCode.MCP_CONNECTION_FAILED, test_callback
        )
        
        # Trigger error
        context = ErrorContext(server_name="callback-server")
        exception = ConnectionError("Test error")
        
        error = error_handler.handle_mcp_protocol_error(exception, context)
        
        assert callback_called is True
        assert callback_error == error
    
    def test_error_summary_generation(self, error_handler):
        """Test error summary generation."""
        # Add some test errors
        context = ErrorContext(server_name="summary-server")
        
        for i in range(5):
            exception = Exception(f"Test error {i}")
            error_handler.handle_mcp_protocol_error(exception, context)
        
        for i in range(3):
            exception = Exception(f"HTTP error {i}")
            error_handler.handle_http_request_error(exception, context, status_code=500)
        
        summary = error_handler.get_error_summary(time_period_hours=1)
        
        assert summary.total_errors == 8
        assert summary.error_rate == 8.0  # 8 errors per hour
        assert len(summary.errors_by_category) >= 2
        assert "mcp_protocol" in summary.errors_by_category
        assert "http_request" in summary.errors_by_category


class TestStructuredLogger:
    """Test StructuredLogger functionality."""
    
    @pytest.fixture
    def logger(self):
        """Create StructuredLogger instance for testing."""
        return StructuredLogger("test-logger")
    
    def test_log_formatter_json(self):
        """Test JSON log formatting."""
        formatter = LogFormatter("json")
        
        log_entry = StructuredLogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            category=LogCategory.HEALTH_CHECK,
            message="Test message"
        )
        
        formatted = formatter.format(log_entry)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "info"
        assert parsed["category"] == "health_check"
        assert parsed["message"] == "Test message"
    
    def test_log_formatter_text(self):
        """Test text log formatting."""
        formatter = LogFormatter("text")
        
        log_entry = StructuredLogEntry(
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            level=LogLevel.ERROR,
            category=LogCategory.MCP_PROTOCOL,
            message="Test error message"
        )
        
        formatted = formatter.format(log_entry)
        
        assert "2023-01-01 12:00:00" in formatted
        assert "[ERROR]" in formatted
        assert "mcp_protocol" in formatted
        assert "Test error message" in formatted
    
    def test_context_stack_management(self, logger):
        """Test context stack push/pop operations."""
        context1 = LogContext(server_name="server1")
        context2 = LogContext(server_name="server2")
        
        # Push contexts
        logger.push_context(context1)
        logger.push_context(context2)
        
        assert len(logger.context_stack) == 2
        assert logger.context_stack[-1].server_name == "server2"
        
        # Pop contexts
        popped = logger.pop_context()
        assert popped.server_name == "server2"
        assert len(logger.context_stack) == 1
        
        popped = logger.pop_context()
        assert popped.server_name == "server1"
        assert len(logger.context_stack) == 0
    
    def test_performance_tracking(self, logger):
        """Test performance tracking functionality."""
        # Start tracking
        metrics = logger.start_performance_tracking("test_operation")
        assert len(logger.performance_stack) == 1
        assert metrics.start_time is not None
        
        # End tracking
        completed_metrics = logger.end_performance_tracking()
        assert len(logger.performance_stack) == 0
        assert completed_metrics.end_time is not None
        assert completed_metrics.duration_ms is not None
        assert completed_metrics.duration_ms >= 0
    
    def test_health_check_logging(self, logger):
        """Test health check specific logging."""
        with patch.object(logger, '_write_log_entry') as mock_write:
            logger.log_health_check(
                server_name="test-server",
                check_type="dual",
                success=True,
                response_time_ms=150.5,
                status_code=200
            )
            
            mock_write.assert_called_once()
            log_entry = mock_write.call_args[0][0]
            
            assert isinstance(log_entry, HealthCheckLogEntry)
            assert log_entry.server_name == "test-server"
            assert log_entry.check_type == "dual"
            assert log_entry.success is True
            assert log_entry.response_time_ms == 150.5
    
    def test_error_logging(self, logger):
        """Test error logging functionality."""
        context = ErrorContext(server_name="error-server")
        error = ErrorDetails(
            error_id="error-123",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.MCP_PROTOCOL,
            error_code=ErrorCode.MCP_CONNECTION_FAILED,
            message="Connection failed",
            context=context
        )
        
        with patch.object(logger, '_write_log_entry') as mock_write:
            logger.log_error(error)
            
            mock_write.assert_called_once()
            log_entry = mock_write.call_args[0][0]
            
            assert log_entry.level == LogLevel.ERROR
            assert log_entry.message == "Connection failed"
            assert log_entry.error_details is not None
            assert "mcp_protocol" in log_entry.tags
            assert "MCP_CONNECTION_FAILED" in log_entry.tags


class TestErrorAnalyzer:
    """Test ErrorAnalyzer functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create ErrorAnalyzer instance for testing."""
        return ErrorAnalyzer()
    
    @pytest.fixture
    def sample_errors(self):
        """Create sample errors for testing."""
        errors = []
        base_time = datetime.utcnow()
        
        # Create various types of errors
        for i in range(10):
            context = ErrorContext(server_name=f"server-{i % 3}")
            error = ErrorDetails(
                error_id=f"error-{i}",
                timestamp=base_time - timedelta(minutes=i * 5),
                severity=ErrorSeverity.ERROR if i % 2 == 0 else ErrorSeverity.WARNING,
                category=ErrorCategory.MCP_PROTOCOL if i % 2 == 0 else ErrorCategory.HTTP_REQUEST,
                error_code=ErrorCode.MCP_CONNECTION_FAILED if i % 2 == 0 else ErrorCode.HTTP_CONNECTION_ERROR,
                message=f"Test error {i}",
                context=context
            )
            errors.append(error)
        
        return errors
    
    def test_error_addition(self, analyzer, sample_errors):
        """Test adding errors to analyzer."""
        for error in sample_errors:
            analyzer.add_error(error)
        
        assert len(analyzer.error_history) == 10
    
    def test_frequency_pattern_detection(self, analyzer):
        """Test detection of high-frequency error patterns."""
        # Create multiple errors of the same type
        base_time = datetime.utcnow()
        context = ErrorContext(server_name="frequent-server")
        
        for i in range(8):
            error = ErrorDetails(
                error_id=f"freq-error-{i}",
                timestamp=base_time - timedelta(minutes=i),
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.MCP_PROTOCOL,
                error_code=ErrorCode.MCP_CONNECTION_FAILED,
                message=f"Frequent error {i}",
                context=context
            )
            analyzer.add_error(error)
        
        patterns = analyzer.analyze_error_patterns(time_window_hours=1)
        
        # Should detect frequency pattern
        freq_patterns = [p for p in patterns if p.pattern_type == "frequency"]
        assert len(freq_patterns) >= 1
        
        freq_pattern = freq_patterns[0]
        assert freq_pattern.frequency >= 5
        assert ErrorCode.MCP_CONNECTION_FAILED in freq_pattern.error_codes
        assert "frequent-server" in freq_pattern.servers_affected
    
    def test_sequence_pattern_detection(self, analyzer):
        """Test detection of error sequence patterns."""
        # Create sequence of errors within short time window
        base_time = datetime.utcnow()
        context = ErrorContext(server_name="sequence-server")
        
        error_codes = [
            ErrorCode.MCP_CONNECTION_FAILED,
            ErrorCode.MCP_TOOLS_LIST_FAILED,
            ErrorCode.MCP_RESPONSE_INVALID,
            ErrorCode.MCP_TOOLS_MISSING
        ]
        
        for i, code in enumerate(error_codes):
            error = ErrorDetails(
                error_id=f"seq-error-{i}",
                timestamp=base_time - timedelta(seconds=i * 30),
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.MCP_PROTOCOL,
                error_code=code,
                message=f"Sequence error {i}",
                context=context
            )
            analyzer.add_error(error)
        
        patterns = analyzer.analyze_error_patterns(time_window_hours=1)
        
        # Should detect sequence pattern
        seq_patterns = [p for p in patterns if p.pattern_type == "sequence"]
        assert len(seq_patterns) >= 1
        
        seq_pattern = seq_patterns[0]
        assert seq_pattern.frequency >= 3
        assert len(seq_pattern.error_codes) >= 3
    
    def test_troubleshooting_recommendations(self, analyzer, sample_errors):
        """Test generation of troubleshooting recommendations."""
        for error in sample_errors:
            analyzer.add_error(error)
        
        recommendations = analyzer.generate_troubleshooting_recommendations(sample_errors)
        
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert rec.recommendation_id is not None
            assert rec.title is not None
            assert rec.priority in ["high", "medium", "low"]
            assert rec.category in ["immediate", "preventive", "monitoring"]
            assert len(rec.steps) > 0
    
    def test_system_health_assessment(self, analyzer, sample_errors):
        """Test comprehensive system health assessment."""
        for error in sample_errors:
            analyzer.add_error(error)
        
        assessment = analyzer.assess_system_health(time_window_hours=1)
        
        assert assessment.assessment_id is not None
        assert 0.0 <= assessment.overall_health_score <= 1.0
        assert isinstance(assessment.critical_issues, list)
        assert isinstance(assessment.warnings, list)
        assert isinstance(assessment.recommendations, list)
        assert isinstance(assessment.error_patterns, list)
        assert isinstance(assessment.server_health_scores, dict)
        assert isinstance(assessment.trend_analysis, dict)
    
    def test_error_statistics(self, analyzer, sample_errors):
        """Test error statistics generation."""
        for error in sample_errors:
            analyzer.add_error(error)
        
        stats = analyzer.get_error_statistics(time_window_hours=1)
        
        assert stats["total_errors"] == 10
        assert stats["error_rate"] == 10.0  # 10 errors per hour
        assert len(stats["most_common_errors"]) > 0
        assert isinstance(stats["server_error_distribution"], dict)
        assert isinstance(stats["hourly_error_counts"], list)
        assert 0.0 <= stats["recovery_rate"] <= 1.0


class TestIntegration:
    """Integration tests for error handling and logging system."""
    
    @pytest.fixture
    def integrated_system(self):
        """Create integrated error handling and logging system."""
        logger = StructuredLogger("integration-test")
        error_handler = ErrorHandler(logger.logger if hasattr(logger, 'logger') else None)
        analyzer = ErrorAnalyzer()
        
        return {
            "logger": logger,
            "error_handler": error_handler,
            "analyzer": analyzer
        }
    
    def test_end_to_end_error_flow(self, integrated_system):
        """Test complete error handling flow."""
        logger = integrated_system["logger"]
        error_handler = integrated_system["error_handler"]
        analyzer = integrated_system["analyzer"]
        
        # Simulate error scenario
        context = ErrorContext(
            server_name="integration-server",
            endpoint_url="http://test.com/api",
            request_id="req-integration"
        )
        
        # Handle MCP error
        exception = ConnectionError("Integration test error")
        error = error_handler.handle_mcp_protocol_error(exception, context)
        
        # Log the error
        logger.log_error(error)
        
        # Add to analyzer
        analyzer.add_error(error)
        
        # Verify error was processed correctly
        assert error.error_code == ErrorCode.MCP_CONNECTION_FAILED
        assert error.context.server_name == "integration-server"
        
        # Verify analyzer has the error
        assert len(analyzer.error_history) == 1
        
        # Generate assessment
        assessment = analyzer.assess_system_health()
        assert assessment.overall_health_score < 1.0  # Should be reduced due to error
    
    @pytest.mark.asyncio
    async def test_retry_with_logging(self, integrated_system):
        """Test retry mechanism with comprehensive logging."""
        logger = integrated_system["logger"]
        error_handler = integrated_system["error_handler"]
        
        context = ErrorContext(server_name="retry-integration-server")
        
        # Mock operation with logging
        attempt_count = 0
        async def mock_operation_with_logging():
            nonlocal attempt_count
            attempt_count += 1
            
            logger.info(f"Attempt {attempt_count}", LogCategory.SYSTEM)
            
            if attempt_count <= 2:
                raise ConnectionError(f"Attempt {attempt_count} failed")
            
            logger.info("Operation succeeded", LogCategory.SYSTEM)
            return f"success_after_{attempt_count}_attempts"
        
        # Execute with retry
        result = await error_handler.retry_with_recovery(
            mock_operation_with_logging, context
        )
        
        assert result == "success_after_3_attempts"
        assert attempt_count == 3
    
    def test_pattern_analysis_with_recommendations(self, integrated_system):
        """Test pattern analysis leading to specific recommendations."""
        error_handler = integrated_system["error_handler"]
        analyzer = integrated_system["analyzer"]
        
        # Create pattern of authentication errors
        context = ErrorContext(server_name="auth-pattern-server")
        
        for i in range(6):
            exception = Exception("Token expired")
            auth_data = {"auth_type": "jwt", "token_type": "bearer"}
            
            error = error_handler.handle_authentication_error(
                exception, context, auth_data
            )
            analyzer.add_error(error)
        
        # Analyze patterns
        patterns = analyzer.analyze_error_patterns()
        recommendations = analyzer.generate_troubleshooting_recommendations(
            analyzer.error_history
        )
        
        # Should detect authentication pattern
        auth_patterns = [p for p in patterns if ErrorCode.AUTH_TOKEN_EXPIRED in p.error_codes]
        assert len(auth_patterns) > 0
        
        # Should have authentication-related recommendations
        auth_recommendations = [r for r in recommendations if "token" in r.title.lower()]
        assert len(auth_recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])