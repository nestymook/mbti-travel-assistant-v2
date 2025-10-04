# Deployment and Testing Scripts

This directory contains comprehensive deployment and testing scripts for the mbti-travel-planner-agent. These scripts validate gateway connectivity, deployment configuration, end-to-end functionality, and ongoing health monitoring.

## Scripts Overview

### 1. Gateway Connectivity Test (`test_gateway_connectivity.py`)
Tests gateway connectivity and endpoint availability.

**Features:**
- Basic connectivity testing
- Health endpoint validation
- Restaurant API endpoint testing
- Performance metrics collection
- Authentication testing support

**Usage:**
```bash
# Test production environment
python scripts/test_gateway_connectivity.py

# Test specific environment with verbose output
python scripts/test_gateway_connectivity.py --environment staging --verbose

# Save results to specific file
python scripts/test_gateway_connectivity.py --output connectivity_test.json
```

### 2. Deployment Validation (`validate_deployment.py`)
Comprehensive deployment validation that verifies all components work correctly.

**Features:**
- Configuration validation
- Gateway connectivity testing
- Tool functionality validation
- Nova Pro model integration testing
- End-to-end workflow validation
- Health monitoring validation

**Usage:**
```bash
# Validate production deployment
python scripts/validate_deployment.py

# Validate with verbose logging
python scripts/validate_deployment.py --environment production --verbose

# Quiet mode (no summary output)
python scripts/validate_deployment.py --quiet
```

### 3. Central District E2E Test (`test_central_district_e2e.py`)
End-to-end testing of Central district search functionality.

**Features:**
- Complete search workflow testing
- Meal type filtering validation
- Error scenario testing
- Performance benchmarking
- User experience simulation

**Usage:**
```bash
# Run E2E tests for production
python scripts/test_central_district_e2e.py

# Test development environment
python scripts/test_central_district_e2e.py --environment development

# Verbose output with custom result file
python scripts/test_central_district_e2e.py --verbose --output e2e_results.json
```

### 4. Health Monitoring (`monitor_agent_health.py`)
Continuous health and performance monitoring.

**Features:**
- Real-time health monitoring
- Performance metrics collection
- Alert generation
- Dashboard display
- Historical data tracking

**Usage:**
```bash
# Single health check
python scripts/monitor_agent_health.py --single-check

# Continuous monitoring with dashboard
python scripts/monitor_agent_health.py --interval 30

# Monitor for specific duration
python scripts/monitor_agent_health.py --duration 300 --interval 10

# Background monitoring without dashboard
python scripts/monitor_agent_health.py --no-dashboard --interval 60
```

### 5. Master Test Runner (`run_deployment_tests.py`)
Orchestrates all deployment and testing scripts.

**Features:**
- Run all tests in sequence or parallel
- Aggregate results from all scripts
- Comprehensive deployment reporting
- Support for specific test selection

**Usage:**
```bash
# Run all tests sequentially
python scripts/run_deployment_tests.py

# Run all tests in parallel (faster)
python scripts/run_deployment_tests.py --parallel

# Run specific tests only
python scripts/run_deployment_tests.py --tests connectivity validation

# Test staging environment with verbose output
python scripts/run_deployment_tests.py --environment staging --verbose
```

## Common Command Line Options

All scripts support these common options:

- `--environment, -e`: Environment to test (`development`, `staging`, `production`)
- `--verbose, -v`: Enable verbose logging
- `--quiet, -q`: Suppress summary output
- `--output, -o`: Specify output file for results

## Environment Configuration

The scripts automatically load environment-specific configuration from:
- `config/environments/gateway.json`: Gateway endpoints and settings
- `config/environments/*.env`: Environment variables
- `.bedrock_agentcore.yaml`: AgentCore deployment configuration

### Supported Environments

1. **Development**: Local development environment
   - Gateway URL: `http://localhost:8080`
   - No authentication required
   - Fast timeouts for quick testing

2. **Staging**: Staging environment for testing
   - Gateway URL: `https://agentcore-gateway-mcp-tools-staging.bedrock-agentcore.us-east-1.amazonaws.com`
   - JWT authentication required
   - Moderate timeouts

3. **Production**: Production environment
   - Gateway URL: `https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com`
   - JWT authentication required
   - Extended timeouts and monitoring

## Test Results

All scripts save detailed results to JSON files in the `tests/results/` directory:

- `gateway_connectivity_test_<env>_<timestamp>.json`
- `deployment_validation_<env>_<timestamp>.json`
- `central_district_e2e_test_<env>_<timestamp>.json`
- `agent_health_report_<env>_<timestamp>.json`
- `deployment_test_results_<env>_<timestamp>.json`

### Result File Structure

```json
{
  "timestamp": "2025-01-04T10:30:00Z",
  "environment": "production",
  "summary": {
    "overall_success": true,
    "success_rate_percent": 100.0,
    "total_tests": 4,
    "successful_tests": 4
  },
  "detailed_results": {
    // Test-specific results
  }
}
```

## Exit Codes

All scripts use standard exit codes:
- `0`: Success (all tests passed)
- `1`: Failure (one or more tests failed)
- `130`: Interrupted by user (Ctrl+C)

## Monitoring and Alerting

The health monitoring script supports configurable alert rules:

### Default Alert Rules

1. **High Response Time**: Triggers when response time > 30 seconds
2. **Service Unavailable**: Triggers when service health is "unhealthy"
3. **High Error Rate**: Triggers when error rate > 50%
4. **Low Success Rate**: Triggers when success rate < 80%

### Alert Severities

- **Info**: Informational alerts
- **Warning**: Issues that need attention
- **Critical**: Serious issues requiring immediate action

## Performance Thresholds

### Response Time Thresholds
- **Healthy**: < 15 seconds
- **Degraded**: 15-30 seconds
- **Unhealthy**: > 30 seconds

### Success Rate Thresholds
- **Healthy**: > 95%
- **Degraded**: 80-95%
- **Unhealthy**: < 80%

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Check network connectivity
   - Verify gateway URL configuration
   - Increase timeout values if needed

2. **Authentication Failures**
   - Verify JWT token configuration
   - Check Cognito settings
   - Ensure proper permissions

3. **Test Failures**
   - Review detailed error messages in result files
   - Check gateway service status
   - Verify environment configuration

### Debug Mode

Enable verbose logging for detailed troubleshooting:
```bash
python scripts/<script_name>.py --verbose
```

### Log Files

Scripts log to both console and the logging service. Check:
- Console output for immediate feedback
- `logs/` directory for persistent logs
- Result files for detailed test data

## Integration with CI/CD

These scripts are designed for integration with CI/CD pipelines:

### Example CI/CD Usage

```bash
# Pre-deployment validation
python scripts/validate_deployment.py --environment staging --quiet
if [ $? -ne 0 ]; then
  echo "Deployment validation failed"
  exit 1
fi

# Post-deployment testing
python scripts/run_deployment_tests.py --environment production --parallel
if [ $? -ne 0 ]; then
  echo "Post-deployment tests failed"
  exit 1
fi

# Continuous monitoring setup
nohup python scripts/monitor_agent_health.py --no-dashboard --interval 300 &
```

### Docker Integration

Scripts can be run in Docker containers:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Run deployment validation
CMD ["python", "scripts/validate_deployment.py"]
```

## Best Practices

1. **Pre-Deployment**: Always run `validate_deployment.py` before deploying
2. **Post-Deployment**: Run `run_deployment_tests.py` to verify deployment
3. **Continuous Monitoring**: Use `monitor_agent_health.py` for ongoing health checks
4. **Environment Testing**: Test each environment (dev → staging → production)
5. **Result Archival**: Save and archive test results for historical analysis

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Review health monitoring reports
2. **Monthly**: Analyze performance trends
3. **Quarterly**: Update alert thresholds based on performance data
4. **As Needed**: Update scripts for new features or requirements

### Script Updates

When updating the agent or gateway:
1. Review and update environment configurations
2. Adjust performance thresholds if needed
3. Add new test scenarios for new features
4. Update alert rules for new monitoring requirements

## Contributing

When adding new tests or modifying existing scripts:

1. Follow the existing code structure and patterns
2. Add comprehensive error handling
3. Include detailed logging and result reporting
4. Update this README with new features
5. Test thoroughly across all environments

## Dependencies

Required Python packages:
- `httpx`: HTTP client for API testing
- `pydantic`: Data validation
- `psutil`: System metrics collection
- `asyncio`: Asynchronous operations
- Standard library modules for JSON, logging, etc.

Install dependencies:
```bash
pip install -r requirements.txt
```