# Configuration Management System

The AgentCore Gateway includes a comprehensive configuration management system with hot reloading capabilities, environment-specific configurations, and validation.

## Overview

The configuration management system provides:

- **Environment-specific configurations** for development, staging, production, and test
- **Hot reloading** of configuration changes without service restart
- **Comprehensive validation** of configuration files and settings
- **MCP server configuration management** with dynamic updates
- **REST API endpoints** for configuration management
- **Change notifications** for dependent services

## Configuration Structure

### Environment Configuration

Each environment has its own configuration file in the `config/` directory:

- `config/development.json` - Development environment settings
- `config/staging.json` - Staging environment settings  
- `config/production.json` - Production environment settings
- `config/test.json` - Test environment settings

### Configuration Schema

```json
{
  "name": "development",
  "log_level": "INFO",
  "debug": true,
  "enable_hot_reload": true,
  "mcp_servers": {
    "search": {
      "name": "search",
      "url": "http://localhost:8081",
      "timeout": 30,
      "max_retries": 3,
      "retry_delay": 1.0,
      "health_check_path": "/health",
      "enabled": true,
      "tools": [
        "search_restaurants_by_district",
        "search_restaurants_by_meal_type",
        "search_restaurants_combined"
      ]
    },
    "reasoning": {
      "name": "reasoning",
      "url": "http://localhost:8082",
      "timeout": 30,
      "max_retries": 3,
      "retry_delay": 1.0,
      "health_check_path": "/health",
      "enabled": true,
      "tools": [
        "recommend_restaurants",
        "analyze_restaurant_sentiment"
      ]
    }
  }
}
```

## Configuration Fields

### Environment Settings

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `name` | string | Environment name (development, staging, production, test) | Required |
| `log_level` | string | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | "INFO" |
| `debug` | boolean | Enable debug mode | false |
| `enable_hot_reload` | boolean | Enable configuration hot reloading | true |

### MCP Server Configuration

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `name` | string | Server identifier | Required |
| `url` | string | Server URL (must start with http:// or https://) | Required |
| `timeout` | integer | Connection timeout in seconds | 30 |
| `max_retries` | integer | Maximum retry attempts | 3 |
| `retry_delay` | float | Delay between retries in seconds | 1.0 |
| `health_check_path` | string | Health check endpoint path | "/health" |
| `enabled` | boolean | Whether server is enabled | true |
| `tools` | array | List of available tools on this server | Required |

## Hot Reloading

The configuration system supports hot reloading, which automatically detects changes to configuration files and reloads them without requiring a service restart.

### How It Works

1. **File Watching**: The system watches configuration files for changes using the `watchdog` library
2. **Change Detection**: When a file is modified, the change is detected and debounced to avoid rapid reloads
3. **Validation**: The new configuration is validated before being applied
4. **Notification**: Dependent services are notified of configuration changes via callbacks
5. **Graceful Fallback**: If the new configuration is invalid, the previous valid configuration is retained

### Enabling/Disabling Hot Reload

Hot reloading can be controlled via the `enable_hot_reload` setting:

```json
{
  "enable_hot_reload": true
}
```

**Note**: Hot reloading is automatically disabled in production environments for security and stability.

## Configuration Validation

The system includes comprehensive validation to ensure configuration correctness:

### Validation Rules

#### Environment Validation
- Environment name must be one of: development, staging, production, test
- Log level must be valid (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Production environments generate warnings for debug settings

#### MCP Server Validation
- Server name cannot be empty
- URL must be valid HTTP/HTTPS format
- Timeout must be positive
- Max retries cannot be negative
- Retry delay cannot be negative
- Health check path must start with '/'
- At least one tool must be defined

#### Required Components
- Required MCP servers: 'search' and 'reasoning'
- Required tools must be present across all servers:
  - `search_restaurants_by_district`
  - `search_restaurants_by_meal_type`
  - `search_restaurants_combined`
  - `recommend_restaurants`
  - `analyze_restaurant_sentiment`

### Validation Warnings

The system generates warnings for:
- Duplicate server URLs
- Overlapping tools across servers
- Debug mode enabled in production
- Hot reload enabled in production
- Debug logging in production

## REST API Endpoints

The configuration management system exposes REST API endpoints for runtime management:

### Get Current Configuration
```http
GET /config/current
Authorization: Bearer <jwt-token>
```

Returns the currently loaded configuration.

### Reload Configuration
```http
POST /config/reload
Authorization: Bearer <jwt-token>
```

Triggers a reload of configuration from files.

### Validate Configuration
```http
GET /config/validate
Authorization: Bearer <jwt-token>
```

Validates the current configuration and tests server connectivity.

### Validate All Configurations
```http
GET /config/validate/all
Authorization: Bearer <jwt-token>
```

Validates all environment configuration files.

### Get MCP Servers
```http
GET /config/servers
Authorization: Bearer <jwt-token>
```

Returns all MCP server configurations.

### Get Specific MCP Server
```http
GET /config/servers/{server_name}
Authorization: Bearer <jwt-token>
```

Returns configuration for a specific MCP server with connectivity status.

## Environment Variables

Configuration can be overridden using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | "development" |
| `MCP_SEARCH_SERVER_URL` | Search server URL | "http://restaurant-search-mcp:8080" |
| `MCP_REASONING_SERVER_URL` | Reasoning server URL | "http://restaurant-reasoning-mcp:8080" |
| `MCP_CONNECTION_TIMEOUT` | Connection timeout | 30 |
| `MCP_MAX_RETRIES` | Maximum retries | 3 |
| `MCP_RETRY_DELAY` | Retry delay | 1.0 |

## Usage Examples

### Basic Configuration Manager Usage

```python
from services.config_manager import ConfigManager, initialize_config_manager

# Initialize global configuration manager
config = await initialize_config_manager("development")

# Get configuration manager instance
config_manager = get_config_manager()

# Get current configuration
current_config = config_manager.get_current_config()

# Get specific MCP server configuration
search_config = config_manager.get_mcp_server_config("search")

# Get all MCP servers
all_servers = config_manager.get_all_mcp_servers()
```

### Configuration Change Callbacks

```python
def on_config_change(new_config):
    print(f"Configuration changed: {new_config.name}")
    # Update dependent services

# Register callback
config_manager.add_change_callback(on_config_change)

# Remove callback
config_manager.remove_change_callback(on_config_change)
```

### Configuration Validation

```python
from services.config_validator import ConfigValidator

validator = ConfigValidator()

# Validate current configuration
is_valid, errors, warnings = await validator.validate_configuration(config)

# Validate server connectivity
is_reachable, error_msg = await validator.validate_server_connectivity(server_config)

# Validate configuration file
is_valid, errors, warnings = await validate_configuration_file("config/development.json")
```

## Best Practices

### Development Environment
- Enable debug mode and hot reloading
- Use localhost URLs for MCP servers
- Set shorter timeouts for faster feedback
- Enable detailed logging

### Staging Environment
- Disable debug mode
- Use staging server URLs
- Enable hot reloading for testing
- Use production-like timeouts

### Production Environment
- Disable debug mode and hot reloading
- Use production server URLs
- Set appropriate timeouts and retries
- Use WARNING or ERROR log levels
- Validate configuration before deployment

### Configuration File Management
- Keep configuration files in version control
- Use environment-specific files
- Validate configurations in CI/CD pipeline
- Document configuration changes
- Test configuration changes in staging first

## Troubleshooting

### Common Issues

#### Configuration Not Loading
- Check file permissions
- Verify JSON syntax
- Check environment variable `ENVIRONMENT`
- Review application logs for errors

#### Hot Reloading Not Working
- Verify `enable_hot_reload` is true
- Check file system permissions
- Ensure configuration files are in the correct directory
- Review file watcher logs

#### Validation Errors
- Check required fields are present
- Verify URL formats
- Ensure positive numeric values
- Check tool lists are complete

#### Server Connectivity Issues
- Verify server URLs are correct
- Check network connectivity
- Ensure servers are running
- Review health check endpoints

### Debugging

Enable debug logging to troubleshoot configuration issues:

```json
{
  "log_level": "DEBUG",
  "debug": true
}
```

Check application logs for configuration-related messages:
- Configuration loading events
- Validation results
- Hot reload triggers
- Server connectivity status

## Security Considerations

### Production Security
- Disable hot reloading in production
- Restrict access to configuration endpoints
- Use HTTPS for all server URLs
- Validate configuration files before deployment
- Monitor configuration changes

### Authentication
- All configuration endpoints require JWT authentication
- Use appropriate user permissions
- Log configuration access and changes
- Implement rate limiting for configuration endpoints

### File Security
- Protect configuration files with appropriate permissions
- Store sensitive values in environment variables
- Use secrets management for production credentials
- Regularly audit configuration access

## Performance Considerations

### Hot Reloading Performance
- Configuration reloads are debounced to prevent rapid changes
- File watching has minimal performance impact
- Validation is performed asynchronously
- Change notifications are non-blocking

### Memory Usage
- Configuration is cached in memory
- Old configurations are garbage collected
- File watchers use minimal resources
- Connection pools are reused

### Network Impact
- Server connectivity checks are optional
- Health checks use configured timeouts
- Connection pooling reduces overhead
- Retry logic prevents cascade failures

## Migration Guide

### Upgrading from Static Configuration

1. **Create Environment Files**: Convert existing configuration to environment-specific files
2. **Update Application Code**: Replace direct settings access with configuration manager
3. **Add Validation**: Implement configuration validation in deployment pipeline
4. **Enable Hot Reloading**: Configure hot reloading for development environments
5. **Test Thoroughly**: Validate all environments work correctly

### Configuration Schema Changes

When updating the configuration schema:

1. **Maintain Backward Compatibility**: Support old and new formats during transition
2. **Update Validation Rules**: Add new validation rules for new fields
3. **Document Changes**: Update documentation and examples
4. **Test Migration**: Verify existing configurations still work
5. **Gradual Rollout**: Deploy changes incrementally across environments