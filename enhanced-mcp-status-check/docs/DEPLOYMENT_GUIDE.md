# Enhanced MCP Status Check System - Deployment Guide

This guide provides comprehensive instructions for deploying the Enhanced MCP Status Check System with dual monitoring capabilities (MCP + REST).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Deployment Process](#deployment-process)
5. [Migration from Existing Systems](#migration-from-existing-systems)
6. [Validation and Testing](#validation-and-testing)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 512MB RAM, recommended 1GB+
- **Disk Space**: Minimum 100MB free space
- **Network**: Access to MCP servers and REST endpoints

### Required Python Packages

```bash
pip install aiohttp pydantic fastapi uvicorn pytest pyyaml
```

### Network Requirements

- Outbound connectivity to configured MCP servers
- Outbound connectivity to REST health endpoints
- Inbound connectivity for API endpoints (optional)

## Installation

### 1. Clone or Download the Enhanced Status Check System

```bash
# If using git
git clone <repository-url>
cd enhanced-mcp-status-check

# Or extract from archive
tar -xzf enhanced-mcp-status-check.tar.gz
cd enhanced-mcp-status-check
```

### 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install aiohttp pydantic fastapi uvicorn pytest pyyaml
```

### 3. Verify Installation

```bash
# Run basic functionality test
python test_basic_functionality.py

# Check Python path
python -c "import sys; print(sys.path)"
```

## Configuration

### 1. Create Configuration File

Choose one of the following approaches:

#### Option A: Use Example Configuration

```bash
# Copy example configuration
cp config/examples/production_config.yaml config/my_config.yaml

# Edit configuration
nano config/my_config.yaml
```

#### Option B: Create New Configuration

```yaml
# config/my_config.yaml
enhanced_status_check_system:
  dual_monitoring_enabled: true
  
  mcp_health_checks:
    enabled: true
    default_timeout_seconds: 10
    tools_list_validation: true
    expected_tools_validation: true
  
  rest_health_checks:
    enabled: true
    default_timeout_seconds: 8
    health_endpoint_path: "/status/health"
    metrics_endpoint_path: "/status/metrics"
  
  result_aggregation:
    mcp_priority_weight: 0.6
    rest_priority_weight: 0.4
    require_both_success_for_healthy: false
    degraded_on_single_failure: true
  
  servers:
    - server_name: "restaurant-search-mcp"
      mcp_endpoint_url: "http://localhost:8080/mcp"
      mcp_enabled: true
      mcp_timeout_seconds: 10
      mcp_expected_tools:
        - "search_restaurants_by_district"
        - "search_restaurants_by_meal_type"
      rest_health_endpoint_url: "http://localhost:8080/status/health"
      rest_enabled: true
      rest_timeout_seconds: 8
      auth_headers: {}
      mcp_priority_weight: 0.6
      rest_priority_weight: 0.4

api:
  host: "0.0.0.0"
  port: 8080
  workers: 1

alerts:
  email: []
  webhook_url: null
```

### 2. Validate Configuration

```bash
# Validate configuration syntax and structure
python scripts/deploy_enhanced_status_check.py --config config/my_config.yaml --validate-only
```

## Deployment Process

### 1. Pre-Deployment Checks

```bash
# Run deployment script with validation only
python scripts/deploy_enhanced_status_check.py \
  --config config/my_config.yaml \
  --environment production \
  --validate-only
```

### 2. Backup Existing Configuration (if applicable)

```bash
# Backup existing configurations
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r config/* backups/$(date +%Y%m%d_%H%M%S)/
```

### 3. Deploy Enhanced Status Check System

```bash
# Full deployment
python scripts/deploy_enhanced_status_check.py \
  --config config/my_config.yaml \
  --environment production
```

### 4. Verify Deployment

```bash
# Run deployment validation
python scripts/validate_deployment.py --config config/my_config.yaml

# Quick connectivity test
python scripts/validate_deployment.py --config config/my_config.yaml --connectivity-only
```

## Migration from Existing Systems

### Automatic Migration

The system includes automatic migration utilities for common configurations:

```bash
# Migrate from restaurant-search-mcp configuration
python scripts/migrate_configuration.py \
  config/old_restaurant_search_config.json \
  --target config/enhanced_config.yaml

# Migrate from restaurant-reasoning-mcp configuration
python scripts/migrate_configuration.py \
  config/old_reasoning_config.json \
  --target config/enhanced_config.yaml

# Migrate entire directory
python scripts/migrate_configuration.py \
  config/old_configs/ \
  --target config/enhanced_configs/
```

### Manual Migration Steps

1. **Identify Current Configuration Format**:
   ```bash
   python scripts/migrate_configuration.py config/existing_config.json --validate-only
   ```

2. **Create Backup**:
   ```bash
   cp config/existing_config.json config/existing_config.json.backup
   ```

3. **Migrate Configuration**:
   ```bash
   python scripts/migrate_configuration.py config/existing_config.json
   ```

4. **Validate Migrated Configuration**:
   ```bash
   python scripts/deploy_enhanced_status_check.py --config config/existing_config.json --validate-only
   ```

### Supported Migration Sources

- **restaurant-search-mcp**: Configurations from restaurant search MCP servers
- **restaurant-reasoning-mcp**: Configurations from restaurant reasoning MCP servers
- **legacy-status-check**: Generic legacy status check configurations

## Validation and Testing

### 1. Configuration Validation

```bash
# Validate configuration structure
python scripts/validate_deployment.py --config config/my_config.yaml --quick

# Full validation including performance tests
python scripts/validate_deployment.py --config config/my_config.yaml
```

### 2. Connectivity Testing

```bash
# Test connectivity to all configured servers
python scripts/validate_deployment.py --config config/my_config.yaml --connectivity-only
```

### 3. Integration Testing

```bash
# Run comprehensive integration tests
python test_integration_runner.py

# Run specific test categories
python -m pytest tests/test_comprehensive_integration.py -v
python -m pytest tests/test_mcp_protocol_integration.py -v
python -m pytest tests/test_rest_health_integration.py -v
```

### 4. Performance Testing

```bash
# Run performance tests
python -m pytest tests/test_performance_concurrent_integration.py -v

# Load testing (if applicable)
python examples/performance_optimization_example.py
```

## Monitoring and Alerting

### 1. Configure Monitoring

The deployment automatically creates monitoring configuration:

```json
{
  "metrics": {
    "enabled": true,
    "collection_interval": 60,
    "retention_days": 30
  },
  "alerts": {
    "enabled": true,
    "email_notifications": [],
    "webhook_url": null
  }
}
```

### 2. Setup Alerting

Edit the monitoring configuration:

```bash
nano config/monitoring_config.json
```

Add email notifications and webhook URLs:

```json
{
  "alerts": {
    "enabled": true,
    "email_notifications": [
      "admin@example.com",
      "ops-team@example.com"
    ],
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  }
}
```

### 3. Monitor Deployment

```bash
# Check deployment logs
tail -f logs/deployment/deployment_*.log

# Check validation logs
tail -f logs/validation/validation_*.log

# Monitor system performance
python examples/dual_metrics_collector_example.py
```

## Rollback Procedures

### 1. List Available Deployments

```bash
# List deployments that can be rolled back
python scripts/rollback_deployment.py --list
```

### 2. Rollback to Previous Version

```bash
# Rollback latest deployment
python scripts/rollback_deployment.py

# Rollback specific deployment
python scripts/rollback_deployment.py --deployment-id enhanced-status-20241005-143022

# Force rollback without confirmation
python scripts/rollback_deployment.py --force
```

### 3. Verify Rollback

```bash
# Validate system after rollback
python scripts/validate_deployment.py --quick

# Check rollback logs
tail -f logs/rollback/rollback_*.log
```

## Troubleshooting

### Common Issues

#### 1. Configuration Validation Errors

**Problem**: Configuration validation fails with schema errors.

**Solution**:
```bash
# Check configuration syntax
python -c "import yaml; yaml.safe_load(open('config/my_config.yaml'))"

# Validate against schema
python scripts/deploy_enhanced_status_check.py --config config/my_config.yaml --validate-only
```

#### 2. Connectivity Issues

**Problem**: Cannot connect to MCP servers or REST endpoints.

**Solution**:
```bash
# Test individual server connectivity
curl -X POST http://localhost:8080/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","id":"test"}'

# Test REST endpoint
curl http://localhost:8080/status/health

# Check network connectivity
ping hostname
telnet hostname port
```

#### 3. Service Initialization Errors

**Problem**: Enhanced health check service fails to initialize.

**Solution**:
```bash
# Check Python dependencies
pip list | grep -E "(aiohttp|pydantic|fastapi)"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Run with debug logging
python scripts/deploy_enhanced_status_check.py --config config/my_config.yaml --environment development
```

#### 4. Performance Issues

**Problem**: Health checks are slow or timing out.

**Solution**:
```bash
# Increase timeout values in configuration
nano config/my_config.yaml

# Test individual components
python examples/mcp_client_example.py
python examples/rest_client_example.py

# Check system resources
top
free -h
df -h
```

### Log Files

- **Deployment logs**: `logs/deployment/deployment_*.log`
- **Validation logs**: `logs/validation/validation_*.log`
- **Migration logs**: `logs/migration/migration_*.log`
- **Rollback logs**: `logs/rollback/rollback_*.log`

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export LOG_LEVEL=DEBUG
python scripts/deploy_enhanced_status_check.py --config config/my_config.yaml
```

## Best Practices

### 1. Configuration Management

- **Version Control**: Store configurations in version control
- **Environment Separation**: Use separate configs for dev/staging/production
- **Secrets Management**: Store sensitive data (tokens, passwords) securely
- **Validation**: Always validate configurations before deployment

### 2. Deployment Strategy

- **Staged Deployment**: Deploy to staging environment first
- **Backup Strategy**: Always backup existing configurations
- **Rollback Plan**: Have rollback procedures ready
- **Monitoring**: Monitor deployment progress and system health

### 3. Security

- **Authentication**: Use proper authentication for MCP and REST endpoints
- **Network Security**: Restrict network access where possible
- **Logging**: Enable comprehensive logging for audit trails
- **Updates**: Keep dependencies updated

### 4. Performance

- **Timeout Configuration**: Set appropriate timeout values
- **Concurrent Limits**: Configure connection limits to prevent overload
- **Resource Monitoring**: Monitor CPU, memory, and network usage
- **Optimization**: Use performance optimization features

### 5. Maintenance

- **Regular Validation**: Run validation checks regularly
- **Log Rotation**: Implement log rotation to manage disk space
- **Health Monitoring**: Monitor system health continuously
- **Documentation**: Keep deployment documentation updated

## Environment-Specific Configurations

### Development Environment

```yaml
enhanced_status_check_system:
  dual_monitoring_enabled: true
  mcp_health_checks:
    default_timeout_seconds: 5
  rest_health_checks:
    default_timeout_seconds: 3
  servers:
    - server_name: "dev-server"
      mcp_endpoint_url: "http://localhost:8080/mcp"
      rest_health_endpoint_url: "http://localhost:8080/status/health"
```

### Staging Environment

```yaml
enhanced_status_check_system:
  dual_monitoring_enabled: true
  mcp_health_checks:
    default_timeout_seconds: 8
  rest_health_checks:
    default_timeout_seconds: 6
  servers:
    - server_name: "staging-server"
      mcp_endpoint_url: "https://staging.example.com/mcp"
      rest_health_endpoint_url: "https://staging.example.com/status/health"
```

### Production Environment

```yaml
enhanced_status_check_system:
  dual_monitoring_enabled: true
  mcp_health_checks:
    default_timeout_seconds: 10
    tools_list_validation: true
    expected_tools_validation: true
  rest_health_checks:
    default_timeout_seconds: 8
  result_aggregation:
    require_both_success_for_healthy: false
    degraded_on_single_failure: true
  servers:
    - server_name: "prod-server"
      mcp_endpoint_url: "https://api.example.com/mcp"
      rest_health_endpoint_url: "https://api.example.com/status/health"
      auth_headers:
        Authorization: "Bearer ${JWT_TOKEN}"
```

## Support and Resources

### Documentation

- [Configuration Reference](CONFIG_REFERENCE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
- [Migration Guide](MIGRATION_GUIDE.md)

### Examples

- [Basic Configuration Example](examples/config_management_example.py)
- [Advanced Deployment Example](examples/enhanced_service_example.py)
- [Performance Optimization Example](examples/performance_optimization_example.py)

### Testing

- [Integration Tests](tests/test_comprehensive_integration.py)
- [Performance Tests](tests/test_performance_concurrent_integration.py)
- [Authentication Tests](tests/test_authentication_integration.py)

---

**Last Updated**: October 5, 2025  
**Version**: 1.0.0  
**Contact**: Enhanced MCP Status Check Team