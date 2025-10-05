# Enhanced MCP Status Check - Configuration Management System

This directory contains the comprehensive configuration management system for the enhanced MCP status check system. The system provides dual monitoring configuration, hot-reloading, validation, and migration capabilities.

## Overview

The configuration management system supports:

- **Dual Monitoring Configuration**: Separate settings for MCP tools/list and REST health checks
- **Hot-Reloading**: Automatic configuration reloading when files change
- **Validation**: Comprehensive validation with custom rules
- **Migration**: Automatic migration from legacy configuration formats
- **Multiple Formats**: Support for JSON and YAML configuration files
- **Backward Compatibility**: Maintains compatibility with existing configurations

## Core Components

### 1. Enhanced Status Configuration (`enhanced_status_config.py`)

Main configuration classes that define the structure and validation for the enhanced MCP status check system.

**Key Classes:**
- `EnhancedStatusConfig`: Main configuration container
- `MCPHealthCheckConfig`: MCP-specific health check settings
- `RESTHealthCheckConfig`: REST-specific health check settings
- `ResultAggregationConfig`: Settings for combining MCP and REST results
- `CircuitBreakerConfig`: Enhanced circuit breaker configuration
- `MonitoringConfig`: General monitoring and performance settings

**Example Usage:**
```python
from config.enhanced_status_config import EnhancedStatusConfig
from models.dual_health_models import EnhancedServerConfig

# Create default configuration
config = EnhancedStatusConfig.create_default()

# Customize settings
config.system_name = "production-monitor"
config.mcp_health_checks.default_timeout_seconds = 15
config.rest_health_checks.auth_type = "bearer"

# Add servers
server = EnhancedServerConfig(
    server_name="restaurant-api",
    mcp_endpoint_url="https://api.example.com/mcp",
    rest_health_endpoint_url="https://api.example.com/status/health"
)
config.add_server(server)

# Save configuration
config.save_to_file("config.json")
```

### 2. Configuration Loader (`config_loader.py`)

Provides configuration loading, hot-reloading, and migration functionality.

**Key Classes:**
- `ConfigLoader`: Main configuration loader with hot-reloading
- `ConfigFileWatcher`: File system watcher for configuration changes
- `ConfigMigrator`: Utilities for migrating legacy configurations

**Example Usage:**
```python
from config.config_loader import ConfigLoader

# Load configuration with hot-reloading
loader = ConfigLoader("config.json")
config = loader.load_config(enable_hot_reload=True)

# Add reload callback
def on_config_change(new_config):
    print(f"Configuration updated: {new_config.system_name}")

loader.add_reload_callback(on_config_change)

# Configuration will automatically reload when file changes
```

### 3. Configuration Validator (`config_validator.py`)

Comprehensive validation system with built-in and custom validation rules.

**Key Classes:**
- `ConfigValidator`: Main validator with pluggable rules
- `ValidationResult`: Detailed validation results with errors, warnings, and info
- Built-in validation rules for URLs, timeouts, security, performance, etc.

**Example Usage:**
```python
from config.config_validator import ConfigValidator

# Create validator
validator = ConfigValidator()

# Validate configuration
result = validator.validate(config)

if result.is_valid:
    print("Configuration is valid!")
else:
    print(f"Validation failed with {len(result.errors)} errors:")
    for error in result.errors:
        print(f"  - {error}")

# Add custom validation rule
def validate_naming_convention(config):
    result = ValidationResult(True, [], [], [])
    for server in config.servers:
        if not server.server_name.endswith("-prod"):
            result.add_warning(f"Server {server.server_name} should end with '-prod'")
    return result

custom_rule = create_custom_validation_rule(
    "naming_convention",
    "Validates server naming convention",
    validate_naming_convention
)
validator.add_rule(custom_rule)
```

## Configuration Structure

### Enhanced Configuration Format

```json
{
  "system_name": "enhanced-mcp-status-check",
  "version": "1.0.0",
  "dual_monitoring_enabled": true,
  
  "mcp_health_checks": {
    "enabled": true,
    "default_timeout_seconds": 10,
    "default_retry_attempts": 3,
    "tools_list_validation": true,
    "expected_tools_validation": true,
    "default_expected_tools": ["search_restaurants", "recommend_restaurants"],
    "jwt_auth_enabled": false,
    "jwt_discovery_url": null
  },
  
  "rest_health_checks": {
    "enabled": true,
    "default_timeout_seconds": 8,
    "default_retry_attempts": 2,
    "health_endpoint_path": "/status/health",
    "metrics_endpoint_path": "/status/metrics",
    "auth_type": "none"
  },
  
  "result_aggregation": {
    "mcp_priority_weight": 0.6,
    "rest_priority_weight": 0.4,
    "require_both_success_for_healthy": false,
    "degraded_on_single_failure": true,
    "health_score_calculation": "weighted_average"
  },
  
  "circuit_breaker": {
    "enabled": true,
    "failure_threshold": 5,
    "recovery_timeout_seconds": 60,
    "independent_circuit_breakers": true
  },
  
  "monitoring": {
    "enabled": true,
    "health_check_interval_seconds": 30,
    "concurrent_health_checks": true,
    "max_concurrent_checks": 10
  },
  
  "servers": [
    {
      "server_name": "restaurant-search-mcp",
      "mcp_endpoint_url": "http://localhost:8080/mcp",
      "rest_health_endpoint_url": "http://localhost:8080/status/health",
      "mcp_enabled": true,
      "rest_enabled": true,
      "mcp_timeout_seconds": 10,
      "rest_timeout_seconds": 8,
      "mcp_expected_tools": ["search_restaurants_by_district"],
      "mcp_priority_weight": 0.6,
      "rest_priority_weight": 0.4
    }
  ]
}
```

### Legacy Configuration Migration

The system automatically detects and migrates legacy configuration formats:

**Legacy Format:**
```json
{
  "system": {"name": "old-system"},
  "mcp": {"enabled": true, "timeout": 10},
  "rest": {"enabled": true, "timeout": 8},
  "servers": [
    {"name": "server1", "mcp_url": "http://localhost:8080/mcp"}
  ]
}
```

**Migrated to Enhanced Format:**
```json
{
  "system_name": "old-system",
  "mcp_health_checks": {"enabled": true, "default_timeout_seconds": 10},
  "rest_health_checks": {"enabled": true, "default_timeout_seconds": 8},
  "servers": [
    {
      "server_name": "server1",
      "mcp_endpoint_url": "http://localhost:8080/mcp"
    }
  ]
}
```

## Configuration Examples

### Development Configuration

```yaml
system_name: enhanced-mcp-status-check-dev
version: 1.0.0
dual_monitoring_enabled: true

mcp_health_checks:
  enabled: true
  default_timeout_seconds: 5
  jwt_auth_enabled: false

rest_health_checks:
  enabled: true
  default_timeout_seconds: 3
  auth_type: none

monitoring:
  health_check_interval_seconds: 10
  concurrent_health_checks: false

servers:
  - server_name: restaurant-search-dev
    mcp_endpoint_url: http://localhost:8080/mcp
    rest_health_endpoint_url: http://localhost:8080/status/health
```

### Production Configuration

```yaml
system_name: enhanced-mcp-status-check-prod
version: 1.0.0
dual_monitoring_enabled: true

mcp_health_checks:
  enabled: true
  default_timeout_seconds: 15
  jwt_auth_enabled: true
  jwt_discovery_url: https://auth.example.com/.well-known/openid-configuration

rest_health_checks:
  enabled: true
  default_timeout_seconds: 12
  auth_type: bearer

result_aggregation:
  mcp_priority_weight: 0.7
  rest_priority_weight: 0.3
  require_both_success_for_healthy: true

monitoring:
  health_check_interval_seconds: 30
  concurrent_health_checks: true
  max_concurrent_checks: 20

servers:
  - server_name: restaurant-search-prod
    mcp_endpoint_url: https://restaurant-api.example.com/mcp
    rest_health_endpoint_url: https://restaurant-api.example.com/status/health
    mcp_timeout_seconds: 20
    rest_timeout_seconds: 15
```

## Validation Rules

The configuration validator includes several built-in validation rules:

### URL Validation Rule
- Validates MCP and REST endpoint URLs
- Checks for proper URL format and protocol
- Warns about insecure HTTP URLs in production

### Timeout Validation Rule
- Ensures timeout values are reasonable
- Warns about very high or very low timeouts
- Validates server-specific timeout overrides

### Security Validation Rule
- Validates JWT authentication configuration
- Checks for insecure protocols
- Validates authentication token formats

### Performance Validation Rule
- Validates connection pool sizes
- Checks concurrent execution settings
- Warns about excessive retry attempts

### Server Configuration Rule
- Validates server configurations are complete
- Checks for duplicate server names
- Ensures required URLs are provided for enabled methods

### Monitoring Interval Rule
- Validates health check intervals are reasonable
- Compares intervals to timeout values
- Warns about very frequent or infrequent checks

## Hot-Reloading

The configuration system supports automatic reloading when configuration files change:

```python
from config.config_loader import ConfigLoader

# Enable hot-reloading
loader = ConfigLoader("config.json")
config = loader.load_config(enable_hot_reload=True)

# Add callback for configuration changes
def handle_config_change(new_config):
    print(f"Configuration reloaded: {new_config.system_name}")
    # Update application with new configuration

loader.add_reload_callback(handle_config_change)

# Configuration will automatically reload when file changes
# Callbacks will be called with the new configuration
```

## Migration Utilities

### Automatic Migration

```python
from config.config_loader import ConfigLoader

# Automatic migration during loading
loader = ConfigLoader("legacy_config.json")
config = loader.load_config()  # Automatically migrates if legacy format detected
```

### Manual Migration

```python
from config.config_loader import migrate_legacy_config_file

# Migrate specific files
migrated_config = migrate_legacy_config_file(
    "legacy_config.json",
    "enhanced_config.json"
)
```

### Migration Detection

```python
from config.config_loader import ConfigMigrator

# Check if configuration is legacy format
with open("config.json") as f:
    data = json.load(f)

if ConfigMigrator.detect_legacy_format(data):
    print("Legacy configuration detected")
    enhanced_data = ConfigMigrator.migrate_legacy_config(data)
```

## Error Handling

The configuration system provides comprehensive error handling:

### Configuration Errors
- `ConfigurationError`: Base exception for configuration issues
- `ConfigValidationError`: Specific validation failures with detailed error lists

### Validation Results
- `ValidationResult`: Contains errors, warnings, and informational messages
- Detailed error reporting with specific field and rule information

### Example Error Handling

```python
from config.enhanced_status_config import ConfigValidationError
from config.config_loader import ConfigLoader

try:
    loader = ConfigLoader("config.json")
    config = loader.load_config()
except ConfigValidationError as e:
    print(f"Configuration validation failed: {e}")
    for error in e.errors:
        print(f"  - {error}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Best Practices

### Configuration Organization
1. Use environment-specific configuration files (dev, staging, prod)
2. Keep sensitive information in environment variables
3. Use YAML for human-readable configurations
4. Use JSON for programmatic configurations

### Validation
1. Always validate configurations before deployment
2. Add custom validation rules for business-specific requirements
3. Use warnings for non-critical issues
4. Implement comprehensive error handling

### Hot-Reloading
1. Use hot-reloading in development environments
2. Be cautious with hot-reloading in production
3. Implement proper error handling for reload failures
4. Test configuration changes thoroughly

### Migration
1. Always backup configurations before migration
2. Test migrated configurations thoroughly
3. Validate migrated configurations
4. Keep migration logs for troubleshooting

## Testing

The configuration system includes comprehensive tests:

```bash
# Run configuration tests
python -m pytest tests/test_enhanced_status_config.py -v
python -m pytest tests/test_config_loader.py -v
python -m pytest tests/test_config_validator.py -v

# Run all configuration tests
python -m pytest tests/test_*config* -v
```

## Examples

See the `examples/` directory for comprehensive examples:

- `config_management_example.py`: Complete configuration management demonstration
- `default_config.json`: Default configuration template
- `production_config.yaml`: Production configuration example
- `legacy_config.json`: Legacy configuration format example

## Requirements

The configuration system requires:

- `pyyaml>=6.0.0`: YAML configuration support
- `watchdog>=3.0.0`: File system watching for hot-reloading
- `pytest>=7.0.0`: Testing framework (development)

Install requirements:
```bash
pip install -r requirements.txt
```

## Integration

To integrate the configuration system into your application:

1. **Import the configuration classes:**
```python
from config.enhanced_status_config import EnhancedStatusConfig
from config.config_loader import ConfigLoader
from config.config_validator import ConfigValidator
```

2. **Load and validate configuration:**
```python
# Load configuration
loader = ConfigLoader("config.json")
config = loader.load_config(enable_hot_reload=True)

# Validate configuration
validator = ConfigValidator()
result = validator.validate(config)
if not result.is_valid:
    raise ConfigValidationError("Invalid configuration", result.errors)
```

3. **Use configuration in your application:**
```python
# Access configuration settings
mcp_timeout = config.mcp_health_checks.default_timeout_seconds
rest_timeout = config.rest_health_checks.default_timeout_seconds

# Get server configurations
for server in config.servers:
    print(f"Monitoring server: {server.server_name}")
```

4. **Handle configuration changes:**
```python
def on_config_reload(new_config):
    # Update application with new configuration
    update_health_check_settings(new_config)
    restart_monitoring_services(new_config)

loader.add_reload_callback(on_config_reload)
```

This configuration management system provides a robust, flexible, and comprehensive solution for managing enhanced MCP status check configurations with dual monitoring capabilities.