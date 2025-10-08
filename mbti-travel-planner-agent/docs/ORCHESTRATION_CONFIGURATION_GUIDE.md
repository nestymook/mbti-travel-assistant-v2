# Tool Orchestration Configuration Guide

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Environment-Specific Configuration](#environment-specific-configuration)
4. [Runtime Configuration Management](#runtime-configuration-management)
5. [Configuration Validation](#configuration-validation)
6. [Advanced Configuration Options](#advanced-configuration-options)
7. [Troubleshooting](#troubleshooting)

## Overview

The Tool Orchestration System uses a hierarchical configuration approach that supports:

- **Base Configuration**: Default settings for all environments
- **Environment Overrides**: Environment-specific customizations
- **Runtime Updates**: Hot-reloading of configuration changes
- **Validation**: Automatic validation of configuration changes
- **Rollback**: Automatic rollback on invalid configurations

## Configuration Structure

### Base Configuration File

**Location**: `config/orchestration_config.yaml`

```yaml
# Tool Orchestration System Configuration
orchestration:
  # Intent Analysis Configuration
  intent_analysis:
    # Minimum confidence threshold for intent classification
    confidence_threshold: 0.8
    
    # NLP model used for intent analysis
    nlp_model: "intent-classifier-v1"
    
    # Parameter extraction settings
    parameter_extraction:
      enabled: true
      timeout: 5s
      max_parameters: 20
      
    # Context analysis settings
    context_analysis:
      enabled: true
      history_window: 10
      mbti_weight: 0.3
      preference_weight: 0.4
      
  # Tool Selection Configuration
  tool_selection:
    # Algorithm used for tool ranking
    ranking_algorithm: "weighted_performance"
    
    # Weights for different selection criteria
    performance_weight: 0.4
    health_weight: 0.3
    capability_weight: 0.3
    
    # Number of fallback tools to identify
    fallback_count: 2
    
    # Tool selection timeout
    selection_timeout: 2s
    
    # Cache settings for tool selection
    cache:
      enabled: true
      ttl: 300s
      max_entries: 1000
      
  # Workflow Engine Configuration
  workflow_engine:
    # Maximum concurrent workflows
    max_concurrent_workflows: 50
    
    # Default timeout for workflow steps
    step_timeout: 30s
    
    # Overall workflow timeout
    workflow_timeout: 120s
    
    # Retry policy for failed steps
    retry_policy:
      max_retries: 3
      backoff_multiplier: 2
      max_backoff: 60s
      retry_on_timeout: true
      
    # Parallel execution settings
    parallel_execution:
      enabled: true
      max_parallel_steps: 5
      
  # Performance Monitoring Configuration
  performance_monitoring:
    # Enable metrics collection
    metrics_collection: true
    
    # Health check interval for tools
    health_check_interval: 30s
    
    # Performance metrics time window
    performance_window: 300s
    
    # Alert thresholds
    alert_thresholds:
      error_rate: 0.1
      response_time: 10s
      availability: 0.95
      
    # Metrics retention
    metrics_retention:
      detailed: 24h
      aggregated: 30d
      
  # Error Handling Configuration
  error_handling:
    # Enable structured error handling
    structured_errors: true
    
    # Error recovery strategies
    recovery_strategies:
      tool_failure: "fallback"
      timeout: "retry"
      authentication: "refresh"
      
    # Circuit breaker settings
    circuit_breaker:
      enabled: true
      failure_threshold: 5
      recovery_timeout: 60s
      
  # Logging Configuration
  logging:
    # Log level for orchestration events
    level: "INFO"
    
    # Enable structured logging
    structured: true
    
    # Log correlation IDs
    correlation_ids: true
    
    # Log performance metrics
    performance_logs: true

# Tool-Specific Configuration
tools:
  # Restaurant Search Tool Configuration
  restaurant_search:
    # Tool priority (1 = highest)
    priority: 1
    
    # Tool capabilities
    capabilities:
      - "search_by_district"
      - "search_by_meal_type"
      - "combined_search"
      
    # MCP endpoint configuration
    mcp_endpoint: "https://restaurant-search-mcp.example.com"
    
    # Health check configuration
    health_check:
      endpoint: "/health"
      interval: 30s
      timeout: 5s
      
    # Performance configuration
    performance:
      timeout: 15s
      retry_count: 3
      circuit_breaker:
        enabled: true
        failure_threshold: 3
        
    # Authentication configuration
    authentication:
      type: "jwt"
      token_refresh_interval: 3600s
      
  # Restaurant Reasoning Tool Configuration
  restaurant_reasoning:
    priority: 1
    capabilities:
      - "recommend_restaurants"
      - "analyze_sentiment"
    mcp_endpoint: "https://restaurant-reasoning-mcp.example.com"
    health_check:
      endpoint: "/health"
      interval: 30s
      timeout: 5s
    performance:
      timeout: 20s
      retry_count: 3
      circuit_breaker:
        enabled: true
        failure_threshold: 3
    authentication:
      type: "jwt"
      token_refresh_interval: 3600s

# Integration Configuration
integration:
  # AgentCore integration settings
  agentcore:
    # Monitoring service integration
    monitoring:
      enabled: true
      endpoint: "https://monitoring.agentcore.aws.com"
      metrics_interval: 60s
      
    # Authentication manager integration
    authentication:
      enabled: true
      token_refresh_interval: 3600s
      
  # External services integration
  external_services:
    # Knowledge base integration
    knowledge_base:
      enabled: false
      endpoint: "https://kb.example.com"
      
    # Analytics service integration
    analytics:
      enabled: true
      endpoint: "https://analytics.example.com"
      batch_size: 100
      flush_interval: 300s

# Security Configuration
security:
  # JWT validation settings
  jwt:
    # Required issuer
    issuer: "https://auth.mbti-travel-planner.com"
    
    # Required audience
    audience: "orchestration-api"
    
    # Token validation settings
    validation:
      verify_signature: true
      verify_expiration: true
      verify_audience: true
      verify_issuer: true
      
  # Rate limiting configuration
  rate_limiting:
    enabled: true
    
    # Default rate limits
    default_limits:
      requests_per_minute: 100
      requests_per_hour: 1000
      
    # Endpoint-specific limits
    endpoint_limits:
      "/orchestrate": 
        requests_per_minute: 50
      "/tools":
        requests_per_minute: 200
        
  # Input validation settings
  input_validation:
    enabled: true
    max_request_size: 1048576  # 1MB
    sanitize_inputs: true
    
# Development and Debugging Configuration
development:
  # Enable debug mode
  debug_mode: false
  
  # Enable request tracing
  request_tracing: false
  
  # Mock tool responses for testing
  mock_tools: false
  
  # Detailed error responses
  detailed_errors: false
```

## Environment-Specific Configuration

### Development Environment

**Location**: `config/environments/orchestration_development.yaml`

```yaml
orchestration:
  intent_analysis:
    # Lower confidence threshold for testing
    confidence_threshold: 0.6
    
  tool_selection:
    # Faster selection for development
    selection_timeout: 1s
    
  workflow_engine:
    # Shorter timeouts for faster feedback
    step_timeout: 10s
    workflow_timeout: 60s
    
  performance_monitoring:
    # More frequent health checks
    health_check_interval: 10s
    
    # Lower alert thresholds for testing
    alert_thresholds:
      error_rate: 0.2
      response_time: 5s
      
  logging:
    # Debug level logging
    level: "DEBUG"
    
    # Enable detailed error responses
    detailed_errors: true

tools:
  restaurant_search:
    # Shorter timeouts for development
    performance:
      timeout: 5s
      
  restaurant_reasoning:
    performance:
      timeout: 8s

development:
  # Enable debug features
  debug_mode: true
  request_tracing: true
  detailed_errors: true
```

### Staging Environment

**Location**: `config/environments/orchestration_staging.yaml`

```yaml
orchestration:
  intent_analysis:
    # Production-like confidence threshold
    confidence_threshold: 0.85
    
  workflow_engine:
    # Production-like timeouts
    step_timeout: 25s
    workflow_timeout: 100s
    
  performance_monitoring:
    # Production-like monitoring intervals
    health_check_interval: 20s
    
    # Stricter alert thresholds
    alert_thresholds:
      error_rate: 0.05
      response_time: 8s
      
  logging:
    # Info level logging
    level: "INFO"

security:
  rate_limiting:
    # Stricter rate limits for staging
    default_limits:
      requests_per_minute: 80
      requests_per_hour: 800
```

### Production Environment

**Location**: `config/environments/orchestration_production.yaml`

```yaml
orchestration:
  intent_analysis:
    # High confidence threshold for production
    confidence_threshold: 0.9
    
  tool_selection:
    # Production performance weights
    performance_weight: 0.5
    health_weight: 0.3
    capability_weight: 0.2
    
  workflow_engine:
    # Production capacity
    max_concurrent_workflows: 100
    
  performance_monitoring:
    # Production monitoring intervals
    health_check_interval: 60s
    
    # Strict production thresholds
    alert_thresholds:
      error_rate: 0.02
      response_time: 5s
      availability: 0.99
      
    # Extended metrics retention
    metrics_retention:
      detailed: 72h
      aggregated: 90d
      
  logging:
    # Warning level for production
    level: "WARN"
    
    # Disable detailed errors in production
    detailed_errors: false

security:
  rate_limiting:
    # Production rate limits
    default_limits:
      requests_per_minute: 200
      requests_per_hour: 2000
      
    endpoint_limits:
      "/orchestrate":
        requests_per_minute: 100
        requests_per_hour: 1000

development:
  # Disable debug features in production
  debug_mode: false
  request_tracing: false
  mock_tools: false
```

## Runtime Configuration Management

### Configuration Manager

The `RuntimeConfigManager` provides hot-reloading capabilities:

```python
from config.runtime_config_manager import RuntimeConfigManager

# Initialize configuration manager
config_manager = RuntimeConfigManager()

# Update configuration at runtime
config_manager.update_config({
    "orchestration.tool_selection.performance_weight": 0.5,
    "orchestration.performance_monitoring.health_check_interval": "45s",
    "tools.restaurant_search.performance.timeout": 20
})

# Validate configuration changes
validation_result = config_manager.validate_config()
if not validation_result.is_valid:
    print(f"Configuration validation failed: {validation_result.errors}")
    config_manager.rollback()
else:
    print("Configuration updated successfully")

# Get current configuration
current_config = config_manager.get_config()
print(f"Current performance weight: {current_config.orchestration.tool_selection.performance_weight}")
```

### Configuration API

Update configuration via REST API:

```bash
# Update tool selection weights
curl -X PUT https://api.mbti-travel-planner.com/orchestration/v1/config \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "orchestration": {
      "tool_selection": {
        "performance_weight": 0.5,
        "health_weight": 0.3,
        "capability_weight": 0.2
      }
    }
  }'

# Update tool timeout
curl -X PUT https://api.mbti-travel-planner.com/orchestration/v1/config \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tools": {
      "restaurant_search": {
        "performance": {
          "timeout": 25
        }
      }
    }
  }'
```

### Configuration Validation

The system automatically validates configuration changes:

```python
class ConfigValidator:
    def validate_orchestration_config(self, config: dict) -> ValidationResult:
        """Validate orchestration configuration."""
        errors = []
        
        # Validate confidence threshold
        confidence = config.get("orchestration", {}).get("intent_analysis", {}).get("confidence_threshold")
        if confidence is not None and (confidence < 0 or confidence > 1):
            errors.append("confidence_threshold must be between 0 and 1")
            
        # Validate weights sum to 1
        tool_selection = config.get("orchestration", {}).get("tool_selection", {})
        weights = [
            tool_selection.get("performance_weight", 0),
            tool_selection.get("health_weight", 0),
            tool_selection.get("capability_weight", 0)
        ]
        if abs(sum(weights) - 1.0) > 0.01:
            errors.append("Tool selection weights must sum to 1.0")
            
        # Validate timeout values
        timeouts = self._extract_timeout_values(config)
        for path, timeout in timeouts.items():
            if timeout <= 0:
                errors.append(f"Timeout at {path} must be positive")
                
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

## Configuration Validation

### Validation Rules

1. **Confidence Thresholds**: Must be between 0.0 and 1.0
2. **Weights**: Tool selection weights must sum to 1.0
3. **Timeouts**: All timeout values must be positive
4. **Intervals**: Monitoring intervals must be positive
5. **Thresholds**: Alert thresholds must be within valid ranges
6. **Endpoints**: MCP endpoints must be valid URLs
7. **Capabilities**: Tool capabilities must be non-empty arrays

### Validation Examples

```yaml
# Valid configuration
orchestration:
  intent_analysis:
    confidence_threshold: 0.8  # ✓ Valid (0.0 - 1.0)
  tool_selection:
    performance_weight: 0.4    # ✓ Valid
    health_weight: 0.3         # ✓ Valid  
    capability_weight: 0.3     # ✓ Valid (sum = 1.0)

# Invalid configuration
orchestration:
  intent_analysis:
    confidence_threshold: 1.5  # ✗ Invalid (> 1.0)
  tool_selection:
    performance_weight: 0.5    # ✗ Invalid
    health_weight: 0.3         # ✗ Invalid
    capability_weight: 0.3     # ✗ Invalid (sum = 1.1)
```

## Advanced Configuration Options

### Custom Tool Selection Algorithms

```yaml
orchestration:
  tool_selection:
    # Use custom algorithm
    ranking_algorithm: "custom_ml_ranking"
    
    # Custom algorithm configuration
    custom_algorithm_config:
      model_path: "/models/tool_ranking_model.pkl"
      feature_weights:
        performance_history: 0.3
        user_preference_match: 0.25
        tool_availability: 0.2
        response_time: 0.15
        success_rate: 0.1
```

### Advanced Workflow Configuration

```yaml
orchestration:
  workflow_engine:
    # Custom workflow templates
    workflow_templates:
      "ADVANCED_SEARCH_AND_RECOMMEND":
        steps:
          - name: "parallel_search"
            type: "parallel"
            tools: ["restaurant_search", "cuisine_search"]
          - name: "aggregate_results"
            type: "aggregation"
            strategy: "weighted_merge"
          - name: "mbti_recommendation"
            type: "sequential"
            tools: ["restaurant_reasoning"]
            
    # Workflow optimization settings
    optimization:
      enabled: true
      cache_intermediate_results: true
      parallel_execution_threshold: 2
```

### Performance Tuning Configuration

```yaml
orchestration:
  performance_monitoring:
    # Advanced metrics collection
    advanced_metrics:
      enabled: true
      collect_detailed_traces: true
      sample_rate: 0.1
      
    # Performance optimization
    optimization:
      auto_scaling:
        enabled: true
        min_instances: 2
        max_instances: 10
        target_cpu_utilization: 70
        
      connection_pooling:
        enabled: true
        pool_size: 20
        max_overflow: 10
        
      caching:
        response_cache:
          enabled: true
          ttl: 300s
          max_size: 1000
        metadata_cache:
          enabled: true
          ttl: 3600s
          max_size: 500
```

## Troubleshooting

### Common Configuration Issues

#### 1. Configuration Validation Failures

**Problem**: Configuration updates are rejected with validation errors.

**Solution**: Check validation rules and fix configuration values:

```bash
# Check current configuration
curl -X GET https://api.mbti-travel-planner.com/orchestration/v1/config \
  -H "Authorization: Bearer <jwt_token>"

# Validate configuration before applying
curl -X POST https://api.mbti-travel-planner.com/orchestration/v1/config/validate \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"orchestration": {"intent_analysis": {"confidence_threshold": 0.8}}}'
```

#### 2. Tool Selection Weight Issues

**Problem**: Tool selection weights don't sum to 1.0.

**Solution**: Ensure weights sum exactly to 1.0:

```yaml
# Correct configuration
tool_selection:
  performance_weight: 0.4
  health_weight: 0.3
  capability_weight: 0.3  # Sum = 1.0 ✓

# Incorrect configuration  
tool_selection:
  performance_weight: 0.5
  health_weight: 0.3
  capability_weight: 0.3  # Sum = 1.1 ✗
```

#### 3. Environment Configuration Override Issues

**Problem**: Environment-specific settings not being applied.

**Solution**: Check environment variable and file precedence:

```bash
# Set environment
export ORCHESTRATION_ENV=production

# Verify configuration loading
python -c "
from config.orchestration_config import OrchestrationConfig
config = OrchestrationConfig()
print(f'Environment: {config.environment}')
print(f'Confidence threshold: {config.orchestration.intent_analysis.confidence_threshold}')
"
```

#### 4. Runtime Configuration Update Failures

**Problem**: Configuration updates fail to apply at runtime.

**Solution**: Check configuration manager status and rollback if needed:

```python
from config.runtime_config_manager import RuntimeConfigManager

config_manager = RuntimeConfigManager()

# Check if configuration is locked
if config_manager.is_locked():
    print("Configuration is locked, waiting for unlock...")
    config_manager.wait_for_unlock()

# Check for pending rollbacks
if config_manager.has_pending_rollback():
    print("Pending rollback detected, applying...")
    config_manager.apply_rollback()
```

### Configuration Debugging

#### Enable Debug Logging

```yaml
orchestration:
  logging:
    level: "DEBUG"
    
development:
  debug_mode: true
  request_tracing: true
```

#### Configuration Validation Script

```python
#!/usr/bin/env python3
"""Configuration validation script."""

import yaml
from config.orchestration_config import OrchestrationConfig
from config.config_validator import ConfigValidator

def validate_config_file(config_path: str):
    """Validate configuration file."""
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        validator = ConfigValidator()
        result = validator.validate_orchestration_config(config_data)
        
        if result.is_valid:
            print(f"✓ Configuration file {config_path} is valid")
        else:
            print(f"✗ Configuration file {config_path} has errors:")
            for error in result.errors:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"✗ Failed to validate {config_path}: {e}")

if __name__ == "__main__":
    validate_config_file("config/orchestration_config.yaml")
    validate_config_file("config/environments/orchestration_production.yaml")
```

### Performance Configuration Tuning

#### High-Load Configuration

```yaml
orchestration:
  workflow_engine:
    max_concurrent_workflows: 200
    
  performance_monitoring:
    health_check_interval: 120s
    
tools:
  restaurant_search:
    performance:
      timeout: 30s
      circuit_breaker:
        failure_threshold: 10
        
  restaurant_reasoning:
    performance:
      timeout: 45s
      circuit_breaker:
        failure_threshold: 10
```

#### Low-Latency Configuration

```yaml
orchestration:
  tool_selection:
    selection_timeout: 0.5s
    cache:
      enabled: true
      ttl: 60s
      
  workflow_engine:
    step_timeout: 10s
    
tools:
  restaurant_search:
    performance:
      timeout: 5s
      
  restaurant_reasoning:
    performance:
      timeout: 8s
```

---

**Configuration Guide Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Maintained By**: MBTI Travel Planner Agent Team