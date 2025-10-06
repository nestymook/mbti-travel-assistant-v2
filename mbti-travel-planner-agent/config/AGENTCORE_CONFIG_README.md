# AgentCore Configuration System

This document describes the environment-based configuration system for AgentCore integration in the MBTI Travel Planner Agent.

## Overview

The AgentCore configuration system provides:

- **Environment-specific configuration loading** for development, staging, and production
- **Validation of required configuration parameters** with clear error messages
- **Configuration models** for AgentCore and Cognito settings with type safety
- **Automatic environment detection** from various sources
- **Comprehensive validation utilities** for configuration verification

## Configuration Models

### AgentCoreConfig

Configuration for AgentCore integration:

```python
@dataclass
class AgentCoreConfig:
    restaurant_search_agent_arn: str      # ARN of restaurant search agent
    restaurant_reasoning_agent_arn: str   # ARN of restaurant reasoning agent
    region: str = "us-east-1"             # AWS region
    timeout_seconds: int = 30             # Request timeout
    max_retries: int = 3                  # Maximum retry attempts
```

### CognitoConfig

Cognito authentication configuration:

```python
@dataclass
class CognitoConfig:
    user_pool_id: str                     # Cognito user pool ID
    client_id: str                        # Cognito app client ID
    client_secret: str                    # Cognito app client secret
    region: str = "us-east-1"             # Cognito region
    discovery_url: str = ""               # OIDC discovery URL
```

### PerformanceConfig

Performance optimization settings:

```python
@dataclass
class PerformanceConfig:
    enable_caching: bool = True           # Enable response caching
    cache_ttl_seconds: int = 300          # Cache time-to-live
    enable_connection_pooling: bool = True # Enable connection pooling
    max_connections: int = 100            # Maximum total connections
    max_connections_per_host: int = 10    # Maximum connections per host
    enable_parallel_execution: bool = True # Enable parallel agent calls
```

### MonitoringConfig

Monitoring and observability settings:

```python
@dataclass
class MonitoringConfig:
    enable_metrics: bool = True           # Enable metrics collection
    enable_tracing: bool = True           # Enable request tracing
    enable_health_checks: bool = True     # Enable health checks
    health_check_interval_seconds: int = 60 # Health check interval
    metrics_namespace: str = "AgentCore/MBTI-Travel-Planner" # CloudWatch namespace
```

### EnvironmentConfig

Complete environment-specific configuration:

```python
@dataclass
class EnvironmentConfig:
    environment: str                      # Environment name (development/staging/production)
    agentcore: AgentCoreConfig           # AgentCore settings
    cognito: CognitoConfig               # Cognito settings
    performance: PerformanceConfig       # Performance settings
    monitoring: MonitoringConfig         # Monitoring settings
    debug_mode: bool = False             # Debug mode flag
```

## Environment Files

### File Locations

The system looks for environment files in the following order:

1. `config/environments/agentcore_{environment}.env`
2. `config/environments/{environment}.env`
3. `.env.agentcore.{environment}`
4. `.env.{environment}`
5. `agentcore_{environment}.env`
6. `{environment}.env`

### Environment Variables

#### Required Variables

```bash
# Cognito Configuration (Required)
COGNITO_USER_POOL_ID=us-east-1_KePRX24Bn
COGNITO_CLIENT_ID=1ofgeckef3po4i3us4j1m4chvd
COGNITO_CLIENT_SECRET=t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9
```

#### Optional Variables (with defaults)

```bash
# Environment Detection
ENVIRONMENT=development                   # Environment name
AWS_ENVIRONMENT=development              # Alternative environment variable
DEPLOYMENT_STAGE=development             # Alternative environment variable

# AgentCore Configuration
AGENTCORE_REGION=us-east-1              # AWS region
AGENTCORE_TIMEOUT=30                    # Request timeout in seconds
AGENTCORE_MAX_RETRIES=3                 # Maximum retry attempts

# Agent ARNs (uses defaults if not specified)
RESTAURANT_SEARCH_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j
RESTAURANT_REASONING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE

# Cognito Configuration
COGNITO_REGION=us-east-1                # Cognito region
COGNITO_DISCOVERY_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration

# Performance Configuration
PERFORMANCE_ENABLE_CACHING=true         # Enable response caching
PERFORMANCE_CACHE_TTL=300               # Cache TTL in seconds
PERFORMANCE_MAX_CONNECTIONS=100         # Maximum total connections
PERFORMANCE_MAX_CONNECTIONS_PER_HOST=10 # Maximum connections per host
PERFORMANCE_ENABLE_PARALLEL=true        # Enable parallel execution

# Monitoring Configuration
MONITORING_ENABLE_METRICS=true          # Enable metrics collection
MONITORING_ENABLE_TRACING=true          # Enable request tracing
MONITORING_ENABLE_HEALTH_CHECKS=true    # Enable health checks
MONITORING_HEALTH_CHECK_INTERVAL=60     # Health check interval in seconds
MONITORING_METRICS_NAMESPACE=AgentCore/MBTI-Travel-Planner # CloudWatch namespace

# Debug Configuration
DEBUG_MODE=false                        # Enable debug mode
```

## Usage Examples

### Basic Usage

```python
from config.agentcore_environment_config import load_agentcore_environment_config

# Load configuration for current environment (auto-detected)
config = load_agentcore_environment_config()

print(f"Environment: {config.environment}")
print(f"Search Agent ARN: {config.agentcore.restaurant_search_agent_arn}")
print(f"Cognito User Pool: {config.cognito.user_pool_id}")
```

### Specific Environment

```python
# Load configuration for specific environment
dev_config = load_agentcore_environment_config(environment='development')
prod_config = load_agentcore_environment_config(environment='production')
```

### Configuration Manager

```python
from config.agentcore_environment_config import get_agentcore_config_manager

# Get configuration manager instance
config_manager = get_agentcore_config_manager()

# Load configuration
config = config_manager.load_config('staging')

# Get configuration summary
summary = config_manager.get_configuration_summary()

# Validate configuration
issues = config_manager.validate_configuration(config)
```

### Validation

```python
from config.agentcore_environment_config import validate_agentcore_environment

# Validate environment variables
issues = validate_agentcore_environment()

if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"  - {issue}")
```

## Environment Detection

The system automatically detects the environment using the following priority order:

1. `ENVIRONMENT` environment variable
2. `AWS_ENVIRONMENT` environment variable
3. `DEPLOYMENT_STAGE` environment variable
4. Local development indicators:
   - `LOCAL_DEVELOPMENT` environment variable
   - `DEBUG` environment variable
   - `.env.development` file exists
5. Staging indicators:
   - `STAGING` environment variable
   - `.env.staging` file exists
6. Production indicators:
   - `PRODUCTION` environment variable
   - `.env.production` file exists
7. Default to `development`

## Default Agent ARNs

The system provides default agent ARNs for each environment:

### Development & Production
- **Search Agent**: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j`
- **Reasoning Agent**: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE`

### Staging
- **Search Agent**: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-staging`
- **Reasoning Agent**: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-staging`

## Validation

### Configuration Validation

The system validates:

- **ARN Format**: Ensures agent ARNs follow correct format
- **Required Fields**: Checks all required configuration values are present
- **Value Ranges**: Validates timeouts, retry counts, and other numeric values
- **URL Formats**: Validates Cognito discovery URLs
- **Cross-field Validation**: Ensures configuration consistency

### Environment File Validation

```bash
# Validate all environments
python config/validate_agentcore_config.py

# Validate specific environment
python config/validate_agentcore_config.py --environment development

# Quiet mode (errors only)
python config/validate_agentcore_config.py --quiet
```

### Validation Report

The validation utility provides a comprehensive report:

```
AgentCore Configuration Validation Report
========================================

📁 Environment Files:
  ✅ development: OK
  ✅ staging: OK
  ✅ production: OK

🔧 Environment Variables:
  ✅ All environment variables valid

⚙️  Configuration Validation:
  ✅ development: OK
  ✅ staging: OK
  ✅ production: OK

📊 Summary:
  🎉 All validations passed!
```

## Error Handling

The configuration system provides detailed error messages for common issues:

### Missing Required Variables
```
Required configuration value missing: COGNITO_USER_POOL_ID
```

### Invalid Values
```
AGENTCORE_TIMEOUT must be between 1-300, got: 500
```

### Invalid ARN Format
```
Invalid restaurant search agent ARN: invalid-arn-format
```

### Configuration Validation Errors
```
AgentCore configuration validation failed:
  - Restaurant search agent ARN is required
  - Invalid discovery URL format: http://invalid-url
```

## Integration with AgentCore Runtime Client

The configuration system integrates seamlessly with the AgentCore Runtime Client:

```python
from config.agentcore_environment_config import load_agentcore_environment_config
from services.agentcore_runtime_client import AgentCoreRuntimeClient

# Load configuration
config = load_agentcore_environment_config()

# Create runtime client with configuration
runtime_client = AgentCoreRuntimeClient(
    cognito_config=config.cognito,
    region=config.agentcore.region
)

# Use agent ARNs from configuration
search_arn = config.agentcore.restaurant_search_agent_arn
reasoning_arn = config.agentcore.restaurant_reasoning_agent_arn
```

## Best Practices

### 1. Environment-Specific Settings

- Use different timeouts for different environments
- Enable debug mode only in development
- Use appropriate connection pool sizes for expected load

### 2. Security

- Never commit secrets to version control
- Use environment variables for sensitive configuration
- Validate configuration on startup

### 3. Monitoring

- Enable metrics and tracing in production
- Use environment-specific CloudWatch namespaces
- Set appropriate health check intervals

### 4. Performance

- Enable caching in production
- Use parallel execution for better performance
- Configure connection pooling based on expected load

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check environment file exists and is readable
   - Verify environment detection is working correctly
   - Check for syntax errors in environment files

2. **Validation errors**
   - Run validation utility to identify specific issues
   - Check required environment variables are set
   - Verify ARN formats are correct

3. **Authentication issues**
   - Verify Cognito configuration is correct
   - Check discovery URL format
   - Ensure client secret is correct

### Debug Mode

Enable debug mode to get detailed logging:

```bash
DEBUG_MODE=true python your_application.py
```

This will provide detailed information about:
- Environment detection process
- Configuration loading steps
- Validation results
- Default value usage

## Migration from HTTP Gateway

### Configuration Changes Required

When migrating from HTTP Gateway to AgentCore integration:

**Remove these variables:**
```bash
GATEWAY_BASE_URL=...
GATEWAY_AUTH_TOKEN=...
GATEWAY_TIMEOUT=...
GATEWAY_MAX_RETRIES=...
GATEWAY_AUTH_REQUIRED=...
```

**Add these variables:**
```bash
RESTAURANT_SEARCH_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j
RESTAURANT_REASONING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE
COGNITO_CLIENT_SECRET=your-client-secret-here
```

### File Migration

1. **Rename environment files:**
   ```bash
   mv config/environments/production.env config/environments/agentcore_production.env
   mv config/environments/staging.env config/environments/agentcore_staging.env
   mv config/environments/development.env config/environments/agentcore_development.env
   ```

2. **Update configuration loading in code:**
   ```python
   # Old way
   from config.gateway_config import get_gateway_config
   config = get_gateway_config('production')
   
   # New way
   from config.agentcore_environment_config import load_agentcore_environment_config
   config = load_agentcore_environment_config('production')
   ```

## Files

- `agentcore_environment_config.py` - Main configuration system
- `validate_agentcore_config.py` - Configuration validation utility
- `agentcore_config_example.py` - Usage examples
- `environments/agentcore_development.env` - Development configuration
- `environments/agentcore_staging.env` - Staging configuration
- `environments/agentcore_production.env` - Production configuration
- `cognito_config.json` - Cognito authentication configuration
- `AGENTCORE_CONFIG_README.md` - This documentation

---

**Last Updated**: October 6, 2025  
**Version**: 3.0.0 (AgentCore Runtime Integration)  
**Scope**: Comprehensive configuration system for AgentCore integration