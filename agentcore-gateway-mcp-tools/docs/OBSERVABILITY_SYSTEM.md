# Observability System Implementation

This document describes the comprehensive observability and monitoring system implemented for the AgentCore Gateway MCP Tools.

## Overview

The observability system provides comprehensive monitoring, logging, and metrics collection for the AgentCore Gateway, including:

- **Structured logging** with user context and performance metrics
- **CloudWatch metrics integration** for request counts and latency
- **Security event logging** for authentication failures and security events
- **Health check endpoint** with MCP server connectivity verification
- **Metrics endpoints** with operational statistics
- **Comprehensive test coverage** for all observability features

## Components

### 1. ObservabilityService (`services/observability_service.py`)

The core service that handles all observability features:

#### Key Features:
- **Request Tracking**: Logs request start/end with performance metrics
- **Security Event Logging**: Tracks authentication events and security incidents
- **MCP Server Call Tracking**: Monitors MCP server interactions
- **CloudWatch Integration**: Sends metrics to AWS CloudWatch
- **Health Monitoring**: Provides comprehensive health status
- **Operational Statistics**: Collects and reports system metrics

#### Data Models:
- `PerformanceMetrics`: Request performance data
- `SecurityEvent`: Security event information
- `OperationalStats`: System operational statistics

#### Key Methods:
- `log_request_start()`: Log request initiation
- `log_request_end()`: Log request completion with metrics
- `log_security_event()`: Log security events
- `log_mcp_server_call()`: Log MCP server interactions
- `get_health_status()`: Get comprehensive health status
- `get_operational_stats()`: Get operational statistics

### 2. ObservabilityMiddleware (`middleware/observability_middleware.py`)

Automatic request tracking middleware that:

#### Features:
- **Automatic Request Tracking**: Tracks all incoming requests
- **User Context Extraction**: Captures authenticated user information
- **Performance Metrics**: Measures request duration and MCP calls
- **Error Handling**: Categorizes and logs different error types
- **Security Event Detection**: Automatically logs authentication events

#### Error Handling:
- Authentication failures → `AUTH_FAILURE` events
- Token expiration → `TOKEN_EXPIRED` events
- Invalid tokens → `TOKEN_INVALID` events
- Forbidden access → `UNAUTHORIZED_ACCESS` events
- Rate limiting → `RATE_LIMIT_EXCEEDED` events

#### Helper Functions:
- `add_mcp_server_call_tracking()`: Track successful MCP calls
- `add_mcp_server_error_tracking()`: Track failed MCP calls

### 3. Observability Endpoints (`api/observability_endpoints.py`)

RESTful endpoints for monitoring and metrics:

#### Endpoints:

##### `/health`
- **Purpose**: Comprehensive health check for AgentCore Runtime
- **Features**: 
  - Overall service health status
  - MCP server connectivity verification
  - Uptime and version information
  - Observability system status
- **Response Codes**: 200 (healthy/degraded), 503 (unhealthy)

##### `/metrics`
- **Purpose**: Operational metrics and statistics
- **Features**:
  - Request counts and success rates
  - Authentication failure statistics
  - MCP server interaction counts
  - System uptime and performance
  - CloudWatch integration status

##### `/metrics/performance`
- **Purpose**: Detailed performance metrics
- **Features**:
  - Request duration statistics (avg, min, max, percentiles)
  - Endpoint-specific performance breakdown
  - MCP server call statistics
  - Configurable history limit

##### `/metrics/security`
- **Purpose**: Security event metrics
- **Features**:
  - Security event type breakdown
  - Endpoint-specific security statistics
  - Authentication failure counts
  - Recent security event analysis

##### `/metrics/mcp`
- **Purpose**: MCP server metrics
- **Features**:
  - Server health status
  - Response time statistics
  - Server availability metrics
  - Connection failure tracking

## Security Event Types

The system tracks the following security events:

- `AUTH_SUCCESS`: Successful authentication
- `AUTH_FAILURE`: Authentication failure
- `TOKEN_EXPIRED`: Expired JWT token
- `TOKEN_INVALID`: Invalid JWT token
- `UNAUTHORIZED_ACCESS`: Forbidden access attempt
- `RATE_LIMIT_EXCEEDED`: Rate limit violations

## CloudWatch Integration

### Metrics Sent to CloudWatch:

#### Performance Metrics:
- `RequestDuration`: Request processing time (milliseconds)
- `RequestCount`: Number of requests
- `MCPServerCalls`: Number of MCP server calls
- `MCPServerDuration`: MCP server call duration

#### Security Metrics:
- `SecurityEvents`: Security event occurrences

#### MCP Metrics:
- `MCPToolCalls`: MCP tool invocations
- `MCPToolDuration`: MCP tool execution time

### Dimensions:
- `Endpoint`: API endpoint path
- `Method`: HTTP method
- `StatusCode`: HTTP response code
- `EventType`: Security event type
- `ServerName`: MCP server name
- `ToolName`: MCP tool name
- `Success`: Operation success status

## Configuration

### Environment Variables:
- `ENABLE_METRICS`: Enable/disable metrics collection (default: true)
- `ENABLE_TRACING`: Enable/disable tracing (default: true)
- `OTEL_SERVICE_NAME`: Service name for observability (default: agentcore-gateway-mcp-tools)
- `AWS_REGION`: AWS region for CloudWatch (default: us-east-1)

### Settings:
- `max_history_size`: Maximum number of metrics to keep in memory (default: 1000)
- `metrics_namespace`: CloudWatch metrics namespace (default: AgentCore/{service_name})

## Usage Examples

### Basic Health Check:
```bash
curl http://localhost:8080/health
```

### Get Operational Metrics:
```bash
curl http://localhost:8080/metrics
```

### Get Performance Metrics:
```bash
curl http://localhost:8080/metrics/performance?limit=50
```

### Get Security Metrics:
```bash
curl http://localhost:8080/metrics/security
```

### Get MCP Server Metrics:
```bash
curl http://localhost:8080/metrics/mcp
```

## Integration with Main Application

The observability system is integrated into the main FastAPI application:

```python
# Add observability middleware (first to track all requests)
app.add_middleware(
    ObservabilityMiddleware,
    bypass_paths=settings.app.bypass_paths
)

# Include observability endpoints
app.include_router(observability_router)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    get_observability_service()
    await get_mcp_client_manager()

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_mcp_client_manager()
    shutdown_observability_service()
```

## Testing

### Test Coverage:
- **Unit Tests**: `tests/test_observability_service.py` (25 tests)
- **Middleware Tests**: `tests/test_observability_middleware.py` (15+ tests)
- **Endpoint Tests**: `tests/test_observability_endpoints.py` (15+ tests)
- **Integration Tests**: `tests/test_observability_integration.py` (15+ tests)

### Test Categories:
- Service initialization and configuration
- Request tracking and performance metrics
- Security event logging
- Health status monitoring
- CloudWatch metrics integration
- Error handling and edge cases
- End-to-end observability workflows

### Running Tests:
```bash
# Run all observability tests
python -m pytest tests/test_observability_*.py -v

# Run specific test category
python -m pytest tests/test_observability_service.py -v

# Run with coverage
python -m pytest tests/test_observability_*.py --cov=services.observability_service --cov=middleware.observability_middleware --cov=api.observability_endpoints
```

## Performance Considerations

### Memory Management:
- **History Limits**: Automatic trimming of performance and security event history
- **Configurable Limits**: Adjustable `max_history_size` parameter
- **Efficient Storage**: Lightweight data structures for metrics

### Async Operations:
- **Non-blocking CloudWatch**: Metrics sent asynchronously
- **Error Resilience**: Graceful handling of CloudWatch failures
- **Event Loop Safety**: Proper handling of async operations in tests

### Resource Usage:
- **Minimal Overhead**: Lightweight middleware with minimal request latency impact
- **Optional CloudWatch**: Can operate without CloudWatch for development
- **Efficient Logging**: Structured logging with JSON output

## Troubleshooting

### Common Issues:

#### CloudWatch Connection Failures:
- Check AWS credentials and permissions
- Verify `AmazonCloudWatchFullAccess` policy
- Check network connectivity to CloudWatch

#### Missing Metrics:
- Verify `ENABLE_METRICS=true` environment variable
- Check CloudWatch client initialization logs
- Ensure proper AWS region configuration

#### High Memory Usage:
- Reduce `max_history_size` setting
- Monitor performance history growth
- Check for memory leaks in long-running processes

### Debug Logging:
Enable debug logging to troubleshoot issues:
```bash
export LOG_LEVEL=DEBUG
```

## Future Enhancements

### Planned Features:
- **Distributed Tracing**: OpenTelemetry integration for request tracing
- **Custom Dashboards**: Pre-built CloudWatch dashboards
- **Alerting**: CloudWatch alarms for critical metrics
- **Prometheus Integration**: Alternative metrics backend
- **Performance Profiling**: Detailed performance analysis tools

### Extensibility:
- **Custom Metrics**: Easy addition of new metric types
- **Plugin Architecture**: Support for additional observability backends
- **Event Hooks**: Customizable event handling and processing

## Compliance and Security

### Data Privacy:
- **PII Handling**: Careful handling of user information in logs
- **Data Retention**: Configurable retention policies for metrics
- **Encryption**: All data encrypted in transit and at rest

### Security:
- **Access Control**: Metrics endpoints respect authentication bypass paths
- **Audit Logging**: Comprehensive security event logging
- **Monitoring**: Real-time security event detection and alerting

---

**Implementation Status**: ✅ Complete  
**Test Coverage**: ✅ Comprehensive  
**Documentation**: ✅ Complete  
**Integration**: ✅ Fully Integrated