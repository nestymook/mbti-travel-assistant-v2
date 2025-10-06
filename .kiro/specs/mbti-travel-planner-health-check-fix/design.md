# Design Document

## Overview

This design addresses the critical bug in the MBTI Travel Planner Agent where the `AgentCoreHealthCheckService` fails to initialize due to a missing `get_connection_config()` method on the `EnvironmentConfig` class. The fix involves adding this method to provide proper connection configuration for the AgentCore Runtime client used by the health check service.

The solution maintains consistency with existing configuration patterns while ensuring the health monitoring system can function properly to monitor the restaurant search and reasoning agents.

## Architecture

### Current Architecture Issue

```
AgentCoreHealthCheckService
    ↓ calls
EnvironmentConfig.get_connection_config()  ← MISSING METHOD
    ↓ should return
ConnectionConfig object
    ↓ used by
AgentCoreRuntimeClient initialization
```

### Target Architecture

```
AgentCoreHealthCheckService
    ↓ calls
EnvironmentConfig.get_connection_config()  ← NEW METHOD
    ↓ returns
ConnectionConfig(
    timeout_seconds=agentcore.timeout_seconds,
    max_connections=performance.max_connections,
    max_connections_per_host=performance.max_connections_per_host,
    keepalive_timeout=30,
    enable_cleanup_closed=True
)
    ↓ used by
AgentCoreRuntimeClient initialization ✓
```

## Components and Interfaces

### 1. EnvironmentConfig Enhancement

**Location:** `config/agentcore_environment_config.py`

**New Method:**
```python
def get_connection_config(self) -> 'ConnectionConfig':
    """
    Get connection configuration for AgentCore Runtime client.
    
    Returns:
        ConnectionConfig object with settings from environment configuration
    """
```

**Implementation Details:**
- Import `ConnectionConfig` from `services.agentcore_runtime_client`
- Use lazy import to avoid circular dependencies
- Map environment config values to connection config parameters
- Apply validation to ensure values are within acceptable ranges

### 2. ConnectionConfig Mapping

**Configuration Mapping:**
- `timeout_seconds` ← `agentcore.timeout_seconds`
- `max_connections` ← `performance.max_connections`
- `max_connections_per_host` ← `performance.max_connections_per_host`
- `keepalive_timeout` ← Fixed value of 30 seconds (reasonable default)
- `enable_cleanup_closed` ← Fixed value of True (recommended setting)

### 3. Error Handling Integration

**Validation Points:**
- Timeout values must be positive and reasonable (1-300 seconds)
- Connection pool values must be positive
- Max connections per host must not exceed total max connections
- Log configuration values for debugging

## Data Models

### ConnectionConfig Structure
```python
@dataclass
class ConnectionConfig:
    timeout_seconds: int = 30
    max_connections: int = 100
    max_connections_per_host: int = 10
    keepalive_timeout: int = 30
    enable_cleanup_closed: bool = True
```

### Environment Configuration Integration
```python
class EnvironmentConfig:
    # ... existing fields ...
    
    def get_connection_config(self) -> ConnectionConfig:
        """Create ConnectionConfig from environment settings."""
        # Import here to avoid circular dependency
        from services.agentcore_runtime_client import ConnectionConfig
        
        return ConnectionConfig(
            timeout_seconds=self.agentcore.timeout_seconds,
            max_connections=self.performance.max_connections,
            max_connections_per_host=self.performance.max_connections_per_host,
            keepalive_timeout=30,  # Reasonable default
            enable_cleanup_closed=True  # Recommended setting
        )
```

## Error Handling

### 1. Import Error Handling
```python
def get_connection_config(self) -> 'ConnectionConfig':
    try:
        from services.agentcore_runtime_client import ConnectionConfig
    except ImportError as e:
        logger.error(f"Failed to import ConnectionConfig: {e}")
        raise ConfigurationError(f"ConnectionConfig not available: {e}")
```

### 2. Validation Error Handling
```python
def get_connection_config(self) -> 'ConnectionConfig':
    # Validate timeout
    if self.agentcore.timeout_seconds <= 0 or self.agentcore.timeout_seconds > 300:
        raise ValueError(f"Invalid timeout: {self.agentcore.timeout_seconds}. Must be 1-300 seconds.")
    
    # Validate connection pool settings
    if self.performance.max_connections <= 0:
        raise ValueError(f"Invalid max_connections: {self.performance.max_connections}. Must be positive.")
    
    if self.performance.max_connections_per_host > self.performance.max_connections:
        raise ValueError(
            f"max_connections_per_host ({self.performance.max_connections_per_host}) "
            f"cannot exceed max_connections ({self.performance.max_connections})"
        )
```

### 3. Logging and Debugging
```python
def get_connection_config(self) -> 'ConnectionConfig':
    config = ConnectionConfig(...)
    
    logger.debug(
        f"Created connection config: timeout={config.timeout_seconds}s, "
        f"max_conn={config.max_connections}, "
        f"max_conn_per_host={config.max_connections_per_host}"
    )
    
    return config
```

## Testing Strategy

### 1. Unit Tests
- Test `get_connection_config()` method with valid configuration
- Test error handling for invalid timeout values
- Test error handling for invalid connection pool settings
- Test that returned `ConnectionConfig` has expected values
- Test lazy import functionality

### 2. Integration Tests
- Test that `AgentCoreHealthCheckService` initializes successfully
- Test that health checks can run without configuration errors
- Test that connection configuration works with actual `AgentCoreRuntimeClient`
- Test configuration loading in different environments

### 3. Error Scenario Tests
- Test behavior when `ConnectionConfig` import fails
- Test behavior with missing performance configuration
- Test behavior with invalid configuration values
- Test error message clarity and helpfulness

## Implementation Approach

### Phase 1: Core Implementation
1. Add the `get_connection_config()` method to `EnvironmentConfig` class
2. Implement proper lazy importing to avoid circular dependencies
3. Add basic validation for configuration values
4. Add logging for debugging purposes

### Phase 2: Error Handling
1. Add comprehensive validation for all configuration parameters
2. Implement clear error messages for common configuration issues
3. Add proper exception handling for import errors
4. Test error scenarios and edge cases

### Phase 3: Integration Testing
1. Test with actual `AgentCoreHealthCheckService` initialization
2. Verify health checks work properly with the new configuration
3. Test in different environments (development, staging, production)
4. Validate that existing functionality remains unaffected

## Backward Compatibility

### Existing Code Impact
- No changes to existing `EnvironmentConfig` properties or methods
- No changes to existing configuration loading logic
- No changes to existing `ConnectionConfig` usage patterns
- New method is additive and doesn't modify existing behavior

### Migration Considerations
- No migration required for existing deployments
- Configuration files remain unchanged
- Environment variables remain unchanged
- Existing runtime client instances continue to work

## Performance Considerations

### Lazy Import Strategy
- Import `ConnectionConfig` only when needed to avoid circular dependencies
- Cache import result to avoid repeated import overhead
- Minimal performance impact on configuration loading

### Configuration Caching
- `ConnectionConfig` objects are lightweight and can be created on-demand
- No need for complex caching since configuration is typically loaded once
- Configuration validation happens at creation time, not repeatedly

## Security Considerations

### Configuration Validation
- Validate timeout values to prevent extremely long timeouts that could cause resource exhaustion
- Validate connection pool sizes to prevent resource exhaustion
- Log configuration values (but not sensitive data) for audit purposes

### Error Information
- Error messages should be helpful but not expose sensitive configuration details
- Log detailed error information for debugging while providing user-friendly messages
- Ensure error handling doesn't leak internal implementation details

## Monitoring and Observability

### Logging Strategy
- Log successful connection configuration creation at DEBUG level
- Log configuration validation errors at ERROR level
- Include relevant configuration values in log messages for debugging
- Use structured logging for better observability

### Health Check Integration
- Once fixed, health checks should provide proper status for restaurant agents
- Health check failures should be distinguishable from configuration errors
- Monitor health check success rates after the fix is deployed

## Deployment Strategy

### Development Environment
1. Deploy fix to development environment first
2. Verify health checks work properly
3. Test with different configuration scenarios
4. Validate that existing functionality is unaffected

### Staging Environment
1. Deploy to staging after development validation
2. Run comprehensive integration tests
3. Monitor health check service behavior
4. Validate performance impact

### Production Environment
1. Deploy during maintenance window if possible
2. Monitor health check service startup
3. Verify that restaurant agent monitoring resumes
4. Monitor for any unexpected side effects

This design provides a focused, minimal-impact solution to fix the critical health check initialization error while maintaining system stability and backward compatibility.