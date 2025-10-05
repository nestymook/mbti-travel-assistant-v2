# Enhanced MCP Status Check - Deployment and Migration Scripts

This directory contains comprehensive deployment, migration, and utility scripts for the Enhanced MCP Status Check System with dual monitoring capabilities.

## Scripts Overview

### 🚀 Deployment Scripts

#### `deploy_enhanced_status_check.py`
**Purpose**: Main deployment script for the enhanced status check system.

**Features**:
- Prerequisites checking (Python version, packages, connectivity)
- Configuration validation
- Service deployment with dual monitoring
- API endpoints setup
- Monitoring and alerting configuration
- Deployment validation and reporting

**Usage**:
```bash
# Full deployment
python deploy_enhanced_status_check.py --config config/production.yaml --environment production

# Validation only
python deploy_enhanced_status_check.py --config config/production.yaml --validate-only

# Development environment
python deploy_enhanced_status_check.py --config config/dev.yaml --environment development
```

**Options**:
- `--config`: Configuration file path
- `--environment`: Deployment environment (development, staging, production)
- `--validate-only`: Only validate configuration, don't deploy

### 🔄 Migration Scripts

#### `migrate_configuration.py`
**Purpose**: Migrate existing status check configurations to enhanced format.

**Supported Formats**:
- `restaurant-search-mcp`: Restaurant search MCP server configurations
- `restaurant-reasoning-mcp`: Restaurant reasoning MCP server configurations
- `legacy-status-check`: Generic legacy status check configurations

**Usage**:
```bash
# Migrate single file
python migrate_configuration.py config/old_config.json --target config/new_config.yaml

# Migrate directory
python migrate_configuration.py config/old_configs/ --target config/enhanced_configs/

# Validate format only
python migrate_configuration.py config/old_config.json --validate-only

# Disable backup creation
python migrate_configuration.py config/old_config.json --no-backup
```

**Features**:
- Automatic format detection
- Field mapping and transformation
- Configuration validation
- Backup creation
- Batch migration support
- Migration reporting

### ↩️ Rollback Scripts

#### `rollback_deployment.py`
**Purpose**: Rollback enhanced status check deployments to previous configurations.

**Usage**:
```bash
# List available deployments
python rollback_deployment.py --list

# Rollback latest deployment
python rollback_deployment.py

# Rollback specific deployment
python rollback_deployment.py --deployment-id enhanced-status-20241005-143022

# Force rollback without confirmation
python rollback_deployment.py --force
```

**Features**:
- Service stopping
- Configuration restoration from backups
- Enhanced files cleanup
- Previous service restoration
- Rollback validation
- Rollback reporting

### ✅ Validation Scripts

#### `validate_deployment.py`
**Purpose**: Comprehensive validation of enhanced status check deployments.

**Usage**:
```bash
# Full validation
python validate_deployment.py --config config/production.yaml

# Quick validation (skip performance tests)
python validate_deployment.py --config config/production.yaml --quick

# Connectivity test only
python validate_deployment.py --config config/production.yaml --connectivity-only
```

**Validation Categories**:
- Configuration integrity
- Server connectivity (MCP + REST)
- Service initialization
- API endpoints accessibility
- Monitoring setup
- Performance testing

### 📊 Monitoring Setup Scripts

#### `setup_monitoring.py`
**Purpose**: Setup comprehensive monitoring and alerting for the enhanced system.

**Usage**:
```bash
# Full monitoring setup
python setup_monitoring.py --config config/production.yaml

# Test email configuration
python setup_monitoring.py --config config/production.yaml --test-email

# Test webhook configuration
python setup_monitoring.py --config config/production.yaml --test-webhook
```

**Features**:
- Metrics collection setup
- Alert rules configuration
- Email and webhook notifications
- Dashboard templates
- Log rotation setup
- Cron jobs configuration

## Script Dependencies

### Required Python Packages
```bash
pip install aiohttp pydantic fastapi uvicorn pytest pyyaml requests
```

### System Requirements
- Python 3.8+
- Network connectivity to MCP servers
- File system write permissions
- SMTP access (for email alerts)
- Webhook endpoints (for webhook alerts)

## Configuration Files

### Main Configuration
- `config/examples/production_config.yaml`: Production configuration template
- `config/examples/development_config.json`: Development configuration template
- `config/examples/default_config.json`: Default configuration template

### Generated Configurations
- `config/api_config.json`: API endpoints configuration
- `config/monitoring_config.json`: Monitoring and alerting configuration
- `config/metrics_config.json`: Metrics collection configuration
- `config/alerts_config.json`: Alert rules configuration
- `config/dashboard_config.json`: Dashboard configuration

## Log Files

### Deployment Logs
- `logs/deployment/deployment_*.log`: Deployment execution logs
- `logs/deployment/deployment_report_*.json`: Deployment reports

### Migration Logs
- `logs/migration/migration_*.log`: Migration execution logs
- `logs/migration/migration_report_*.json`: Migration reports

### Validation Logs
- `logs/validation/validation_*.log`: Validation execution logs
- `logs/validation/validation_report_*.json`: Validation reports

### Rollback Logs
- `logs/rollback/rollback_*.log`: Rollback execution logs
- `logs/rollback/rollback_report_*.json`: Rollback reports

### Monitoring Logs
- `logs/monitoring/monitoring_setup_*.log`: Monitoring setup logs
- `logs/monitoring/monitoring_setup_report_*.json`: Monitoring setup reports

## Backup Management

### Automatic Backups
All scripts create automatic backups before making changes:
- `backups/{deployment_id}/`: Deployment-specific backups
- `backups/{migration_id}/`: Migration-specific backups

### Backup Structure
```
backups/
├── enhanced-status-20241005-143022/
│   ├── enhanced_status_config_backup.py
│   ├── production_config_backup.yaml
│   └── api_config_backup.json
└── migration_20241005_144530/
    ├── old_config_backup.json
    └── legacy_settings_backup.yaml
```

## Common Workflows

### 1. Fresh Deployment
```bash
# 1. Validate configuration
python deploy_enhanced_status_check.py --config config/production.yaml --validate-only

# 2. Deploy system
python deploy_enhanced_status_check.py --config config/production.yaml --environment production

# 3. Validate deployment
python validate_deployment.py --config config/production.yaml

# 4. Setup monitoring
python setup_monitoring.py --config config/production.yaml
```

### 2. Migration from Existing System
```bash
# 1. Detect configuration format
python migrate_configuration.py config/existing_config.json --validate-only

# 2. Migrate configuration
python migrate_configuration.py config/existing_config.json --target config/enhanced_config.yaml

# 3. Deploy enhanced system
python deploy_enhanced_status_check.py --config config/enhanced_config.yaml --environment production

# 4. Validate migration
python validate_deployment.py --config config/enhanced_config.yaml
```

### 3. Rollback Procedure
```bash
# 1. List available deployments
python rollback_deployment.py --list

# 2. Rollback to previous version
python rollback_deployment.py --deployment-id enhanced-status-20241005-143022

# 3. Validate rollback
python validate_deployment.py --quick
```

### 4. Monitoring Setup
```bash
# 1. Setup monitoring system
python setup_monitoring.py --config config/production.yaml

# 2. Test email notifications
python setup_monitoring.py --config config/production.yaml --test-email

# 3. Test webhook notifications
python setup_monitoring.py --config config/production.yaml --test-webhook

# 4. Install cron jobs (manual step)
crontab config/crontab.txt
```

## Environment Variables

### Optional Environment Variables
```bash
# Logging level
export LOG_LEVEL=DEBUG

# Configuration override
export CONFIG_PATH=/path/to/config.yaml

# Backup directory
export BACKUP_DIR=/path/to/backups

# Metrics storage
export METRICS_DIR=/path/to/metrics
```

## Error Handling

### Common Issues and Solutions

#### 1. Configuration Validation Errors
```bash
# Check configuration syntax
python -c "import yaml; yaml.safe_load(open('config/my_config.yaml'))"

# Validate configuration structure
python deploy_enhanced_status_check.py --config config/my_config.yaml --validate-only
```

#### 2. Connectivity Issues
```bash
# Test individual server connectivity
python validate_deployment.py --config config/my_config.yaml --connectivity-only

# Check network connectivity
curl -X POST http://server:8080/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","id":"test"}'
```

#### 3. Permission Issues
```bash
# Check file permissions
ls -la config/
ls -la logs/

# Fix permissions
chmod 755 scripts/*.py
chmod 644 config/*.yaml
```

#### 4. Service Issues
```bash
# Check running processes
ps aux | grep python
netstat -tlnp | grep :8080

# Check logs
tail -f logs/deployment/deployment_*.log
tail -f logs/validation/validation_*.log
```

## Security Considerations

### File Permissions
- Configuration files: `644` (readable by owner and group)
- Script files: `755` (executable by owner, readable by others)
- Log files: `644` (readable by owner and group)
- Backup files: `600` (readable by owner only)

### Sensitive Data
- Store JWT tokens and passwords in environment variables
- Use secure file permissions for configuration files
- Enable log rotation to prevent log file growth
- Regularly clean up old backup files

### Network Security
- Use HTTPS for webhook notifications
- Validate SSL certificates for external connections
- Implement proper authentication for MCP and REST endpoints
- Use firewall rules to restrict access

## Performance Optimization

### Script Performance
- Use async operations for network requests
- Implement connection pooling for multiple servers
- Cache configuration data to avoid repeated parsing
- Use batch operations for multiple server operations

### Resource Management
- Limit concurrent connections to prevent overload
- Implement proper timeout handling
- Use memory-efficient data structures
- Clean up temporary files and resources

## Troubleshooting

### Debug Mode
Enable debug logging for detailed troubleshooting:
```bash
export LOG_LEVEL=DEBUG
python script_name.py --config config/my_config.yaml
```

### Log Analysis
Check specific log files for errors:
```bash
# Deployment issues
grep -i error logs/deployment/deployment_*.log

# Migration issues
grep -i error logs/migration/migration_*.log

# Validation issues
grep -i error logs/validation/validation_*.log
```

### Configuration Issues
Validate configuration files:
```bash
# YAML syntax check
python -c "import yaml; print(yaml.safe_load(open('config/my_config.yaml')))"

# JSON syntax check
python -c "import json; print(json.load(open('config/my_config.json')))"
```

## Support and Documentation

### Additional Resources
- [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)
- [Configuration Reference](../docs/CONFIG_REFERENCE.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING_GUIDE.md)
- [API Documentation](../docs/API_DOCUMENTATION.md)

### Example Configurations
- [Basic Configuration](../examples/config_management_example.py)
- [Advanced Deployment](../examples/enhanced_service_example.py)
- [Performance Optimization](../examples/performance_optimization_example.py)

### Testing
- [Integration Tests](../tests/test_comprehensive_integration.py)
- [Performance Tests](../tests/test_performance_concurrent_integration.py)
- [Authentication Tests](../tests/test_authentication_integration.py)

---

**Last Updated**: October 5, 2025  
**Version**: 1.0.0  
**Contact**: Enhanced MCP Status Check Team