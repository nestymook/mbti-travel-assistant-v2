# Comprehensive Error Handling and Logging Guide

This guide provides detailed information about the comprehensive error handling and logging system implemented for the enhanced MCP status check system.

## Overview

The error handling and logging system provides:

- **Detailed Error Classification**: Categorizes errors by type, severity, and context
- **Comprehensive HTTP Error Handling**: Handles all HTTP status codes and connection issues
- **MCP Protocol Error Handling**: Specialized handling for JSON-RPC and MCP-specific errors
- **Structured Logging**: JSON-based logging with contextual information
- **Error Recovery Mechanisms**: Automatic retry with exponential backoff
- **Error Analysis**: Pattern detection and troubleshooting recommendations
- **Performance Tracking**: Built-in performance metrics collection

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Error Handling System                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Error Models   │  │ Logging Models  │  │   Services  │  │
│  │                 │  │                 │  │             │  │
│  │ • ErrorDetails  │  │ • LogEntry      │  │ • Handler   │  │
│  │ • ErrorContext  │  │ • LogContext    │  │ • Logger    │  │
│  │ • ErrorCode     │  │ • Metrics       │  │ • Analyzer  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Error Models

### Error Classification

Errors are classified using multiple dimensions:

#### Error Severity
- `CRITICAL`: System-threatening errors requiring immediate attention
- `ERROR`: Significant errors that impact functionality
- `WARNING`: Issues that may lead to errors if not addressed
- `INFO`: Informational messages for tracking

#### Error Categories
- `MCP_PROTOCOL`: JSON-RPC and MCP-specific errors
- `HTTP_REQUEST`: HTTP status codes and connection errors
- `AUTHENTICATION`: Token and credential-related errors
- `NETWORK`: DNS, connectivity, and network-related errors
- `VALIDATION`: Data validation and schema errors
- `CONFIGURATION`: Configuration and setup errors
- `TIMEOUT`: Request and operation timeouts
- `CIRCUIT_BREAKER`: Circuit breaker state changes
- `AGGREGATION`: Result aggregation errors
- `SYSTEM`: General system errors

#### Error Codes

Specific error codes for detailed classification:

**MCP Protocol Errors:**
- `MCP_INVALID_JSONRPC`: Invalid JSON-RPC 2.0 format
- `MCP_TOOLS_LIST_FAILED`: tools/list request failed
- `MCP_RESPONSE_INVALID`: Invalid response format
- `MCP_TOOLS_MISSING`: Expected tools not found
- `MCP_CONNECTION_FAILED`: Connection to MCP server failed

**HTTP Request Errors:**
- `HTTP_STATUS_ERROR`: HTTP error status codes (4xx, 5xx)
- `HTTP_CONNECTION_ERROR`: Connection establishment failed
- `HTTP_TIMEOUT`: Request timeout
- `HTTP_RESPONSE_INVALID`: Invalid response format
- `HTTP_SSL_ERROR`: SSL/TLS certificate errors

**Authentication Errors:**
- `AUTH_TOKEN_INVALID`: Invalid authentication token
- `AUTH_TOKEN_EXPIRED`: Expired authentication token
- `AUTH_CREDENTIALS_MISSING`: Missing credentials
- `AUTH_PERMISSION_DENIED`: Insufficient permissions
- `AUTH_REFRESH_FAILED`: Token refresh failed

### Error Context

Every error includes contextual information:

```python
from enhanced_mcp_status_check.models.error_models import ErrorContext

context = ErrorContext(
    server_name="restaurant-search-mcp",
    endpoint_url="http://localhost:8080/mcp",
    request_id="req_20231201_143022",
    operation="dual_health_check",
    user_id="user_123",
    session_id="session_456",
    additional_data={
        "retry_count": 2,
        "timeout_seconds": 10
    }
)
```

## Error Handling

### ErrorHandler Service

The `ErrorHandler` service provides comprehensive error handling:

```python
from enhanced_mcp_status_check.services.error_handler import ErrorHandler
from enhanced_mcp_status_check.models.error_models import ErrorContext

# Initialize error handler
error_handler = ErrorHandler()

# Handle MCP protocol error
context = ErrorContext(server_name="mcp-server")
try:
    # MCP operation that might fail
    pass
except Exception as e:
    error = error_handler.handle_mcp_protocol_error(
        e, context, {"method": "tools/list", "id": "req-123"}
    )
    print(f"MCP Error: {error.message}")
```

### Error Recovery

Automatic retry with exponential backoff:

```python
# Retry operation with recovery strategy
async def risky_operation():
    # Operation that might fail
    pass

result = await error_handler.retry_with_recovery(
    risky_operation, 
    context,
    operation_args=(),
    operation_kwargs={}
)
```

### Error Callbacks

Register callbacks for specific error types:

```python
def on_connection_failed(error):
    print(f"Connection failed: {error.message}")
    # Implement custom recovery logic

error_handler.register_error_callback(
    ErrorCode.MCP_CONNECTION_FAILED,
    on_connection_failed
)
```

## Structured Logging

### Logger Configuration

```python
from enhanced_mcp_status_check.services.structured_logger import configure_logging
from enhanced_mcp_status_check.models.logging_models import LogLevel

# Configure global logging
logger = configure_logging(
    log_level=LogLevel.INFO,
    file_path="logs/dual_monitoring.log",
    console_output=True,
    json_format=True
)
```

### Logging Operations

#### Health Check Logging
```python
logger.log_health_check(
    server_name="restaurant-search-mcp",
    check_type="dual",
    success=True,
    response_time_ms=125.5,
    status_code=200
)
```

#### MCP Protocol Logging
```python
logger.log_mcp_protocol(
    method="tools/list",
    request_id="req-123",
    success=True,
    tools_count=5,
    validation_errors=[]
)
```

#### HTTP Request Logging
```python
logger.log_http_request(
    method="GET",
    url="http://localhost:8080/status/health",
    status_code=200,
    response_size_bytes=256,
    success=True
)
```

#### Authentication Logging
```python
logger.log_authentication(
    auth_method="jwt",
    success=True,
    token_type="bearer",
    expires_in_seconds=3600
)
```

### Context Management

Use context managers for automatic context handling:

```python
from enhanced_mcp_status_check.models.logging_models import LogContext, OperationType

context = LogContext(
    server_name="test-server",
    operation_type=OperationType.DUAL_HEALTH_CHECK,
    request_id="req-456"
)

with LoggingContextManager(logger, context):
    logger.info("Operation started")
    # All logs within this block will include the context
    logger.info("Operation completed")
```

### Performance Tracking

Track operation performance automatically:

```python
with PerformanceTrackingContextManager(logger, "health_check"):
    # Perform health check operation
    await perform_health_check()
    # Performance metrics are automatically logged
```

## Error Analysis

### ErrorAnalyzer Service

The `ErrorAnalyzer` provides comprehensive error analysis:

```python
from enhanced_mcp_status_check.services.error_analyzer import ErrorAnalyzer

analyzer = ErrorAnalyzer()

# Add errors for analysis
analyzer.add_error(error)

# Analyze error patterns
patterns = analyzer.analyze_error_patterns(time_window_hours=24)

# Generate troubleshooting recommendations
recommendations = analyzer.generate_troubleshooting_recommendations(errors)

# Perform system health assessment
assessment = analyzer.assess_system_health(time_window_hours=24)
```

### Pattern Detection

The analyzer detects various error patterns:

#### Frequency Patterns
High-frequency errors indicating system issues:
```python
# Detects when error frequency exceeds thresholds
freq_patterns = [p for p in patterns if p.pattern_type == "frequency"]
```

#### Sequence Patterns
Error sequences indicating cascading failures:
```python
# Detects error sequences within time windows
seq_patterns = [p for p in patterns if p.pattern_type == "sequence"]
```

#### Correlation Patterns
Correlated errors across servers:
```python
# Detects correlated errors on same server
corr_patterns = [p for p in patterns if p.pattern_type == "correlation"]
```

#### Temporal Patterns
Time-based error patterns:
```python
# Detects errors clustered in specific time periods
temp_patterns = [p for p in patterns if p.pattern_type == "temporal"]
```

### Troubleshooting Recommendations

Automatic generation of troubleshooting recommendations:

```python
# Get recommendations for specific errors
recommendations = analyzer.generate_troubleshooting_recommendations(errors)

for rec in recommendations:
    print(f"Priority: {rec.priority}")
    print(f"Title: {rec.title}")
    print(f"Description: {rec.description}")
    print(f"Steps: {rec.steps}")
    print(f"Estimated time: {rec.estimated_time_minutes} minutes")
```

### System Health Assessment

Comprehensive system health evaluation:

```python
assessment = analyzer.assess_system_health()

print(f"Overall Health Score: {assessment.overall_health_score:.2f}")
print(f"Critical Issues: {len(assessment.critical_issues)}")
print(f"Warnings: {len(assessment.warnings)}")
print(f"Recommendations: {len(assessment.recommendations)}")
```

## Integration Examples

### Complete Error Handling Flow

```python
import asyncio
from enhanced_mcp_status_check.services.error_handler import ErrorHandler
from enhanced_mcp_status_check.services.structured_logger import StructuredLogger
from enhanced_mcp_status_check.services.error_analyzer import ErrorAnalyzer
from enhanced_mcp_status_check.models.error_models import ErrorContext
from enhanced_mcp_status_check.models.logging_models import LogContext, OperationType

async def dual_health_check_with_error_handling(server_name: str):
    # Initialize components
    logger = StructuredLogger("dual-monitoring")
    error_handler = ErrorHandler()
    analyzer = ErrorAnalyzer()
    
    # Create contexts
    log_context = LogContext(
        server_name=server_name,
        operation_type=OperationType.DUAL_HEALTH_CHECK
    )
    
    error_context = ErrorContext(
        server_name=server_name,
        operation="dual_health_check"
    )
    
    with logger.push_context(log_context):
        try:
            logger.info(f"Starting dual health check for {server_name}")
            
            # Perform health check with retry
            result = await error_handler.retry_with_recovery(
                perform_health_check,
                error_context,
                operation_args=(server_name,)
            )
            
            logger.log_health_check(
                server_name=server_name,
                check_type="dual",
                success=True,
                response_time_ms=result.get("response_time", 0)
            )
            
            return result
            
        except Exception as e:
            # Handle any remaining errors
            error = error_handler.handle_mcp_protocol_error(e, error_context)
            logger.log_error(error)
            analyzer.add_error(error)
            
            # Generate recommendations
            recommendations = analyzer.generate_troubleshooting_recommendations([error])
            
            return {
                "success": False,
                "error": error.message,
                "recommendations": [r.title for r in recommendations[:3]]
            }

async def perform_health_check(server_name: str):
    # Simulate health check operation
    # This would contain actual MCP and REST health check logic
    pass
```

### Error Pattern Analysis

```python
def analyze_system_errors():
    analyzer = ErrorAnalyzer()
    
    # Load historical errors (from database, logs, etc.)
    errors = load_historical_errors()
    
    for error in errors:
        analyzer.add_error(error)
    
    # Analyze patterns
    patterns = analyzer.analyze_error_patterns(time_window_hours=168)  # 1 week
    
    # Generate report
    assessment = analyzer.assess_system_health(time_window_hours=24)
    
    # Create actionable report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "health_score": assessment.overall_health_score,
        "critical_patterns": [
            p.to_dict() for p in patterns 
            if p.confidence_score > 0.8 and p.frequency >= 10
        ],
        "immediate_actions": [
            r.to_dict() for r in assessment.recommendations
            if r.priority == "high" and r.category == "immediate"
        ],
        "server_health": assessment.server_health_scores
    }
    
    return report
```

## Configuration

### Error Handler Configuration

```python
from enhanced_mcp_status_check.services.error_handler import ErrorRecoveryStrategy

# Configure recovery strategies for different error categories
recovery_strategies = {
    ErrorCategory.MCP_PROTOCOL: ErrorRecoveryStrategy(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        backoff_multiplier=2.0
    ),
    ErrorCategory.HTTP_REQUEST: ErrorRecoveryStrategy(
        max_retries=3,
        base_delay=0.5,
        max_delay=15.0,
        backoff_multiplier=1.5
    ),
    ErrorCategory.NETWORK: ErrorRecoveryStrategy(
        max_retries=5,
        base_delay=2.0,
        max_delay=60.0,
        backoff_multiplier=2.0
    )
}

error_handler = ErrorHandler()
error_handler.recovery_strategies.update(recovery_strategies)
```

### Logger Configuration

```python
from enhanced_mcp_status_check.services.structured_logger import (
    StructuredLogger, FileLogOutput, LogFormatter
)

# Create custom logger with multiple outputs
logger = StructuredLogger("custom-monitoring")

# Add file output for errors only
error_file_output = FileLogOutput("logs/errors.log", max_size_mb=50)
error_formatter = LogFormatter("json")
logger.add_output(error_file_output, error_formatter)

# Add separate file for performance metrics
metrics_file_output = FileLogOutput("logs/metrics.log", max_size_mb=100)
metrics_formatter = LogFormatter("structured")
logger.add_output(metrics_file_output, metrics_formatter)

# Set log level
logger.set_log_level(LogLevel.INFO)
```

## Best Practices

### Error Handling Best Practices

1. **Always Provide Context**: Include relevant context information with every error
2. **Use Appropriate Severity**: Choose the correct severity level for each error
3. **Include Recovery Suggestions**: Provide actionable recovery suggestions
4. **Log Before Throwing**: Log errors before re-throwing or handling them
5. **Use Specific Error Codes**: Use specific error codes rather than generic ones

### Logging Best Practices

1. **Use Structured Logging**: Always use structured logging for better analysis
2. **Include Performance Metrics**: Track performance for all operations
3. **Use Context Managers**: Use context managers for automatic context handling
4. **Log at Appropriate Levels**: Use appropriate log levels for different types of information
5. **Include Correlation IDs**: Use correlation IDs to track related operations

### Analysis Best Practices

1. **Regular Analysis**: Perform regular error pattern analysis
2. **Act on Recommendations**: Implement troubleshooting recommendations promptly
3. **Monitor Trends**: Track error trends over time
4. **Update Thresholds**: Adjust pattern detection thresholds based on system behavior
5. **Document Patterns**: Document recurring patterns and their solutions

## Troubleshooting

### Common Issues

#### High Memory Usage
If the error handler is using too much memory:
- Reduce error history size: `error_handler.error_history.maxlen = 500`
- Clear analysis cache regularly: `analyzer._clear_analysis_cache()`
- Use file-based logging instead of in-memory buffering

#### Performance Impact
If error handling is impacting performance:
- Reduce retry attempts for non-critical operations
- Use asynchronous logging
- Implement sampling for high-frequency operations
- Cache analysis results

#### Missing Error Context
If errors lack sufficient context:
- Always create ErrorContext with relevant information
- Use context managers for automatic context propagation
- Include operation-specific data in additional_data
- Set up proper correlation ID tracking

### Debugging

Enable debug logging to troubleshoot issues:

```python
logger.set_log_level(LogLevel.DEBUG)
logger.debug("Debug information", LogCategory.SYSTEM)
```

Use the error analyzer to identify patterns:

```python
# Get detailed error statistics
stats = analyzer.get_error_statistics(time_window_hours=1)
print(json.dumps(stats, indent=2))

# Analyze specific error patterns
patterns = analyzer.analyze_error_patterns()
for pattern in patterns:
    print(f"Pattern: {pattern.description}")
    print(f"Confidence: {pattern.confidence_score}")
    print(f"Recommendations: {pattern.recommended_actions}")
```

## API Reference

### Error Models
- `ErrorDetails`: Base error information
- `ErrorContext`: Error context information
- `MCPProtocolError`: MCP-specific error details
- `HTTPRequestError`: HTTP-specific error details
- `AuthenticationError`: Authentication-specific error details
- `NetworkError`: Network-specific error details
- `ValidationError`: Validation-specific error details

### Logging Models
- `StructuredLogEntry`: Base log entry
- `LogContext`: Logging context information
- `PerformanceMetrics`: Performance tracking data
- `HealthCheckLogEntry`: Health check specific log entry
- `MCPProtocolLogEntry`: MCP protocol specific log entry
- `HTTPRequestLogEntry`: HTTP request specific log entry

### Services
- `ErrorHandler`: Main error handling service
- `StructuredLogger`: Structured logging service
- `ErrorAnalyzer`: Error analysis and pattern detection service

For detailed API documentation, see the individual module docstrings and type hints.