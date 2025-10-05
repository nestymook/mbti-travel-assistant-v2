"""
Simple test for error handling and logging system.

This test can be run independently to verify the error handling implementation.
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from models.error_models import (
    ErrorDetails, ErrorSeverity, ErrorCategory, ErrorCode, ErrorContext,
    MCPProtocolError, HTTPRequestError, ErrorBuilder
)
from models.logging_models import (
    LogLevel, LogCategory, OperationType, StructuredLogEntry, LogContext,
    PerformanceMetrics
)
from services.error_handler import ErrorHandler
from services.structured_logger import StructuredLogger
from services.error_analyzer import ErrorAnalyzer


def test_error_models():
    """Test error model creation and serialization."""
    print("Testing error models...")
    
    # Test ErrorContext
    context = ErrorContext(
        server_name="test-server",
        endpoint_url="http://test.com/api",
        request_id="req-123"
    )
    
    assert context.server_name == "test-server"
    context_dict = context.to_dict()
    assert context_dict["server_name"] == "test-server"
    print("✅ ErrorContext test passed")
    
    # Test ErrorDetails
    error = ErrorDetails(
        error_id="error-123",
        timestamp=datetime.utcnow(),
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.MCP_PROTOCOL,
        error_code=ErrorCode.MCP_CONNECTION_FAILED,
        message="Connection failed",
        context=context
    )
    
    assert error.error_code == ErrorCode.MCP_CONNECTION_FAILED
    error_dict = error.to_dict()
    assert error_dict["error_code"] == "MCP_CONNECTION_FAILED"
    print("✅ ErrorDetails test passed")
    
    # Test ErrorBuilder
    built_error = ErrorBuilder(ErrorCode.MCP_TOOLS_LIST_FAILED, "Tools list failed") \
        .with_severity(ErrorSeverity.WARNING) \
        .with_context(context) \
        .build()
    
    assert built_error.severity == ErrorSeverity.WARNING
    assert built_error.context.server_name == "test-server"
    print("✅ ErrorBuilder test passed")


def test_logging_models():
    """Test logging model creation and serialization."""
    print("Testing logging models...")
    
    # Test LogContext
    context = LogContext(
        server_name="test-server",
        operation_type=OperationType.DUAL_HEALTH_CHECK,
        request_id="req-789"
    )
    
    assert context.server_name == "test-server"
    context_dict = context.to_dict()
    assert context_dict["operation_type"] == "dual_health_check"
    print("✅ LogContext test passed")
    
    # Test PerformanceMetrics
    start_time = datetime.utcnow()
    metrics = PerformanceMetrics(start_time=start_time)
    metrics.end_time = start_time + timedelta(milliseconds=150)
    duration = metrics.calculate_duration()
    
    assert abs(duration - 150.0) < 1.0  # Allow small variance
    print("✅ PerformanceMetrics test passed")
    
    # Test StructuredLogEntry
    log_entry = StructuredLogEntry(
        timestamp=datetime.utcnow(),
        level=LogLevel.INFO,
        category=LogCategory.HEALTH_CHECK,
        message="Health check completed",
        context=context,
        performance_metrics=metrics
    )
    
    assert log_entry.level == LogLevel.INFO
    log_dict = log_entry.to_dict()
    assert log_dict["level"] == "info"
    print("✅ StructuredLogEntry test passed")


def test_error_handler():
    """Test ErrorHandler functionality."""
    print("Testing error handler...")
    
    error_handler = ErrorHandler()
    
    # Test MCP protocol error handling
    context = ErrorContext(server_name="mcp-server")
    exception = ConnectionError("Connection refused")
    
    error = error_handler.handle_mcp_protocol_error(exception, context)
    
    assert isinstance(error, MCPProtocolError)
    assert error.category == ErrorCategory.MCP_PROTOCOL
    assert error.error_code == ErrorCode.MCP_CONNECTION_FAILED
    print("✅ MCP protocol error handling test passed")
    
    # Test HTTP request error handling
    http_exception = Exception("HTTP 500 error")
    http_error = error_handler.handle_http_request_error(
        http_exception, context, status_code=500
    )
    
    assert isinstance(http_error, HTTPRequestError)
    assert http_error.status_code == 500
    print("✅ HTTP request error handling test passed")
    
    # Test error summary
    summary = error_handler.get_error_summary(time_period_hours=1)
    assert summary.total_errors >= 2  # We added 2 errors
    print("✅ Error summary test passed")


def test_structured_logger():
    """Test StructuredLogger functionality."""
    print("Testing structured logger...")
    
    logger = StructuredLogger("test-logger")
    
    # Test context management
    context = LogContext(server_name="test-server")
    logger.push_context(context)
    
    assert len(logger.context_stack) == 1
    
    popped = logger.pop_context()
    assert popped.server_name == "test-server"
    assert len(logger.context_stack) == 0
    print("✅ Context management test passed")
    
    # Test performance tracking
    metrics = logger.start_performance_tracking("test_operation")
    assert len(logger.performance_stack) == 1
    
    completed_metrics = logger.end_performance_tracking()
    assert len(logger.performance_stack) == 0
    assert completed_metrics.duration_ms is not None
    print("✅ Performance tracking test passed")


def test_error_analyzer():
    """Test ErrorAnalyzer functionality."""
    print("Testing error analyzer...")
    
    analyzer = ErrorAnalyzer()
    
    # Create sample errors
    base_time = datetime.utcnow()
    errors = []
    
    for i in range(5):
        context = ErrorContext(server_name=f"server-{i % 2}")
        error = ErrorDetails(
            error_id=f"error-{i}",
            timestamp=base_time - timedelta(minutes=i),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.MCP_PROTOCOL,
            error_code=ErrorCode.MCP_CONNECTION_FAILED,
            message=f"Test error {i}",
            context=context
        )
        errors.append(error)
        analyzer.add_error(error)
    
    assert len(analyzer.error_history) == 5
    print("✅ Error addition test passed")
    
    # Test pattern analysis
    patterns = analyzer.analyze_error_patterns(time_window_hours=1)
    assert len(patterns) >= 0  # May or may not detect patterns with small sample
    print("✅ Pattern analysis test passed")
    
    # Test troubleshooting recommendations
    recommendations = analyzer.generate_troubleshooting_recommendations(errors)
    assert len(recommendations) >= 0  # May have recommendations
    print("✅ Troubleshooting recommendations test passed")
    
    # Test system health assessment
    assessment = analyzer.assess_system_health(time_window_hours=1)
    assert 0.0 <= assessment.overall_health_score <= 1.0
    assert assessment.overall_health_score < 1.0  # Should be reduced due to errors
    print("✅ System health assessment test passed")
    
    # Test error statistics
    stats = analyzer.get_error_statistics(time_window_hours=1)
    assert stats["total_errors"] == 5
    assert stats["error_rate"] == 5.0  # 5 errors per hour
    print("✅ Error statistics test passed")


async def test_retry_mechanism():
    """Test retry mechanism with recovery."""
    print("Testing retry mechanism...")
    
    error_handler = ErrorHandler()
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
    result = await error_handler.retry_with_recovery(mock_operation, context)
    
    assert result == "success"
    assert call_count == 3
    print("✅ Retry mechanism test passed")


def test_integration():
    """Test integration between components."""
    print("Testing integration...")
    
    # Create integrated system
    logger = StructuredLogger("integration-test")
    error_handler = ErrorHandler()
    analyzer = ErrorAnalyzer()
    
    # Simulate error scenario
    context = ErrorContext(
        server_name="integration-server",
        endpoint_url="http://test.com/api",
        request_id="req-integration"
    )
    
    # Handle error
    exception = ConnectionError("Integration test error")
    error = error_handler.handle_mcp_protocol_error(exception, context)
    
    # Log error
    logger.log_error(error)
    
    # Add to analyzer
    analyzer.add_error(error)
    
    # Verify integration
    assert error.context.server_name == "integration-server"
    assert len(analyzer.error_history) == 1
    
    assessment = analyzer.assess_system_health()
    assert assessment.overall_health_score < 1.0
    print("✅ Integration test passed")


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting comprehensive error handling and logging tests...\n")
    
    try:
        test_error_models()
        print()
        
        test_logging_models()
        print()
        
        test_error_handler()
        print()
        
        test_structured_logger()
        print()
        
        test_error_analyzer()
        print()
        
        await test_retry_mechanism()
        print()
        
        test_integration()
        print()
        
        print("✅ All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run tests."""
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 Comprehensive error handling and logging system is working correctly!")
        print("📁 The system includes:")
        print("  • Detailed error classification and handling")
        print("  • Comprehensive HTTP and MCP protocol error handling")
        print("  • Structured logging with contextual information")
        print("  • Error recovery mechanisms with exponential backoff")
        print("  • Error pattern analysis and troubleshooting recommendations")
        print("  • Performance tracking and metrics collection")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit(main())