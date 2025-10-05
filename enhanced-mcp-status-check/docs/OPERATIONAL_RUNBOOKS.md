# Enhanced MCP Status Check System - Operational Runbooks

This document provides comprehensive operational runbooks for managing the Enhanced MCP Status Check System in production environments.

## Table of Contents

1. [System Overview](#system-overview)
2. [Deployment Procedures](#deployment-procedures)
3. [Monitoring and Alerting](#monitoring-and-alerting)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Emergency Procedures](#emergency-procedures)
7. [Performance Optimization](#performance-optimization)
8. [Security Operations](#security-operations)

## System Overview

### Architecture Components

- **Enhanced Health Check Service**: Core orchestrator for dual monitoring
- **MCP Health Check Client**: Handles MCP tools/list requests
- **REST Health Check Client**: Handles HTTP health checks
- **Health Result Aggregator**: Combines dual monitoring results
- **Enhanced Circuit Breaker**: Intelligent failure detection
- **Dual Metrics Collector**: Comprehensive metrics collection
- **API Endpoints**: REST API for status monitoring
- **Console Integration**: Dashboard and alerting interface

### Key Metrics

- **Overall Health Status**: HEALTHY, DEGRADED, UNHEALTHY
- **Response Times**: MCP, REST, and combined response times
- **Success Rates**: Individual and combined success rates
- **Tool Availability**: MCP tools/list validation results
- **Circuit Breaker States**: Per-server and per-path states

## Deployment Procedures

### Pre-Deployment Checklist

```bash
# 1. Verify prerequisites
python3 scripts/deploy_enhanced_status_check.py --validate-only --environment staging

# 2. Check system resources
df -h  # Disk space
free -m  # Memory
ps aux | grep enhanced-mcp  # Running processes

# 3. Backup current configuration
cp -r config/ backups/config-$(date +%Y%m%d-%H%M%S)/

# 4. Test connectivity to monitored servers
curl -f https://server1.example.com/status/health
curl -f https://server2.example.com/mcp
```

### Staging Deployment

```bash
# 1. Deploy to staging environment
python3 scripts/deploy_enhanced_status_check.py \
  --environment staging \
  --config config/examples/staging_deployment_config.yaml

# 2. Validate staging deployment
python3 scripts/validate_deployment.py --environment staging

# 3. Run integration tests
python3 -m pytest tests/test_comprehensive_integration.py -v

# 4. Monitor staging for 30 minutes
python3 scripts/monitoring/collect_metrics.py --environment staging
```

### Production Deployment

```bash
# 1. Final staging validation
python3 scripts/validate_deployment.py --environment staging --comprehensive

# 2. Create production backup
python3 scripts/backup_production.py

# 3. Deploy to production (gradual rollout)
python3 scripts/deploy_enhanced_status_check.py \
  --environment production \
  --config config/examples/production_config.yaml \
  --gradual-rollout

# 4. Monitor deployment progress
tail -f logs/deployment/deployment_*.log

# 5. Validate production deployment
python3 scripts/validate_deployment.py --environment production
```

### Rollback Procedures

```bash
# 1. Immediate rollback (if deployment fails)
python3 scripts/rollback_deployment.py --immediate

# 2. Gradual rollback (if issues discovered later)
python3 scripts/rollback_deployment.py --gradual

# 3. Verify rollback success
python3 scripts/validate_deployment.py --environment production
```

## Monitoring and Alerting

### Key Monitoring Commands

```bash
# Check overall system health
curl -s http://localhost:8080/status/health | jq .

# Get detailed server status
curl -s http://localhost:8080/status/servers/restaurant-search-mcp | jq .

# View metrics
curl -s http://localhost:8080/status/metrics | jq .

# Check dual monitoring results
curl -s http://localhost:8080/status/dual-check | jq .
```

### Alert Response Procedures

#### Critical Alert: Server Completely Down

**Alert**: `server_down`
**Severity**: Critical
**Condition**: Both MCP and REST health checks failed

**Response Steps**:

1. **Immediate Assessment** (0-5 minutes)
   ```bash
   # Check server status
   curl -f https://server.example.com/status/health
   curl -f https://server.example.com/mcp
   
   # Check network connectivity
   ping server.example.com
   nslookup server.example.com
   ```

2. **Escalation** (5-10 minutes)
   ```bash
   # Check server logs
   ssh server.example.com "tail -100 /var/log/mcp-server.log"
   
   # Check system resources
   ssh server.example.com "top -n 1"
   ssh server.example.com "df -h"
   ```

3. **Recovery Actions** (10-30 minutes)
   ```bash
   # Restart MCP server
   ssh server.example.com "systemctl restart mcp-server"
   
   # Verify recovery
   python3 scripts/validate_deployment.py --server restaurant-search-mcp
   ```

#### Warning Alert: Dual Monitoring Degraded

**Alert**: `dual_monitoring_degraded`
**Severity**: Warning
**Condition**: One monitoring method failed

**Response Steps**:

1. **Identify Failed Path** (0-2 minutes)
   ```bash
   # Check which monitoring method failed
   curl -s http://localhost:8080/status/servers/server-name | jq '.mcp_success, .rest_success'
   ```

2. **Investigate Failure** (2-10 minutes)
   ```bash
   # If MCP failed
   curl -f https://server.example.com/mcp
   
   # If REST failed
   curl -f https://server.example.com/status/health
   ```

3. **Monitor for Recovery** (10-30 minutes)
   ```bash
   # Watch for automatic recovery
   watch -n 30 "curl -s http://localhost:8080/status/servers/server-name | jq '.overall_status'"
   ```

### Dashboard Monitoring

#### Key Dashboard Metrics

1. **Server Health Grid**
   - Overall status per server
   - MCP vs REST success rates
   - Response time trends

2. **Response Time Charts**
   - MCP response times
   - REST response times
   - Combined response times

3. **Success Rate Trends**
   - Overall success rate
   - MCP success rate
   - REST success rate

4. **Circuit Breaker Status**
   - Open/closed states
   - Failure counts
   - Recovery attempts

## Troubleshooting

### Common Issues and Solutions

#### Issue: High Response Times

**Symptoms**:
- Response times > 5000ms
- Timeout errors in logs
- Degraded user experience

**Diagnosis**:
```bash
# Check current response times
curl -s http://localhost:8080/status/metrics | jq '.response_times'

# Check server load
ssh server.example.com "uptime"
ssh server.example.com "iostat -x 1 5"
```

**Solutions**:
```bash
# Increase timeout values
vim config/examples/production_config.yaml
# Update mcp_timeout_seconds and rest_timeout_seconds

# Restart with new configuration
python3 scripts/deploy_enhanced_status_check.py --config-only

# Monitor improvement
watch -n 10 "curl -s http://localhost:8080/status/metrics | jq '.response_times'"
```

#### Issue: MCP Tools Missing

**Symptoms**:
- `mcp_tools_missing` alert
- MCP success but missing expected tools
- Tool validation failures

**Diagnosis**:
```bash
# Check MCP tools/list response
curl -X POST https://server.example.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Compare with expected tools
cat config/examples/production_config.yaml | grep -A 10 mcp_expected_tools
```

**Solutions**:
```bash
# Update expected tools list
vim config/examples/production_config.yaml

# Or restart MCP server to reload tools
ssh server.example.com "systemctl restart mcp-server"
```

#### Issue: Authentication Failures

**Symptoms**:
- 401/403 errors in logs
- JWT validation failures
- Authentication timeouts

**Diagnosis**:
```bash
# Check JWT token validity
python3 scripts/test_jwt_auth.py --server restaurant-search-mcp

# Verify OIDC discovery endpoint
curl -s https://cognito-idp.us-east-1.amazonaws.com/us-east-1_POOL/.well-known/openid-configuration
```

**Solutions**:
```bash
# Refresh JWT tokens
python3 scripts/refresh_auth_tokens.py

# Update authentication configuration
vim config/examples/production_config.yaml
# Update discoveryUrl and allowedClients
```

### Log Analysis

#### Key Log Locations

```bash
# Deployment logs
tail -f logs/deployment/deployment_*.log

# Monitoring logs
tail -f logs/monitoring/monitoring_*.log

# Application logs
tail -f logs/enhanced_status_check.log

# Error logs
tail -f logs/errors.log
```

#### Log Analysis Commands

```bash
# Find authentication errors
grep -i "auth" logs/enhanced_status_check.log | tail -20

# Find timeout errors
grep -i "timeout" logs/enhanced_status_check.log | tail -20

# Find MCP protocol errors
grep -i "mcp" logs/enhanced_status_check.log | grep -i "error" | tail -20

# Analyze response time patterns
grep "response_time" logs/enhanced_status_check.log | awk '{print $NF}' | sort -n
```

## Maintenance Procedures

### Daily Maintenance

```bash
# 1. Check system health
python3 scripts/daily_health_check.py

# 2. Review overnight alerts
grep "$(date -d yesterday +%Y-%m-%d)" logs/alerts.log

# 3. Check disk space
df -h | grep -E "(80%|90%|95%)"

# 4. Verify backup integrity
python3 scripts/verify_backups.py
```

### Weekly Maintenance

```bash
# 1. Rotate logs
logrotate config/logrotate.conf

# 2. Clean old metrics data
find data/metrics -name "*.json" -mtime +30 -delete

# 3. Update configuration if needed
python3 scripts/update_config.py --check-updates

# 4. Performance analysis
python3 scripts/weekly_performance_report.py
```

### Monthly Maintenance

```bash
# 1. Security updates
python3 scripts/security_update_check.py

# 2. Configuration review
python3 scripts/config_audit.py

# 3. Performance optimization
python3 scripts/performance_optimization.py

# 4. Disaster recovery test
python3 scripts/dr_test.py --dry-run
```

## Emergency Procedures

### System-Wide Outage

**Immediate Actions** (0-15 minutes):

1. **Assess Impact**
   ```bash
   # Check all monitored servers
   python3 scripts/emergency_health_check.py --all-servers
   
   # Check network connectivity
   python3 scripts/network_connectivity_test.py
   ```

2. **Enable Emergency Mode**
   ```bash
   # Switch to emergency configuration
   cp config/emergency_config.yaml config/current_config.yaml
   
   # Restart with minimal monitoring
   python3 scripts/emergency_restart.py
   ```

3. **Notify Stakeholders**
   ```bash
   # Send emergency notification
   python3 scripts/emergency_notification.py --outage
   ```

**Recovery Actions** (15-60 minutes):

1. **Identify Root Cause**
   ```bash
   # Analyze logs for patterns
   python3 scripts/log_analysis.py --emergency
   
   # Check external dependencies
   python3 scripts/dependency_check.py
   ```

2. **Implement Fix**
   ```bash
   # Apply emergency fix
   python3 scripts/apply_emergency_fix.py
   
   # Validate fix
   python3 scripts/validate_emergency_fix.py
   ```

3. **Gradual Recovery**
   ```bash
   # Gradually restore full monitoring
   python3 scripts/gradual_recovery.py
   
   # Monitor recovery progress
   watch -n 30 "python3 scripts/recovery_status.py"
   ```

### Data Corruption

**Immediate Actions**:

1. **Stop Data Collection**
   ```bash
   # Stop metrics collection
   pkill -f collect_metrics.py
   
   # Backup corrupted data
   cp -r data/metrics data/corrupted-$(date +%Y%m%d-%H%M%S)
   ```

2. **Restore from Backup**
   ```bash
   # Restore latest clean backup
   python3 scripts/restore_data_backup.py --latest
   
   # Verify data integrity
   python3 scripts/verify_data_integrity.py
   ```

3. **Resume Operations**
   ```bash
   # Restart data collection
   python3 scripts/start_metrics_collection.py
   
   # Monitor for issues
   tail -f logs/metrics_collection.log
   ```

## Performance Optimization

### Performance Monitoring

```bash
# Check current performance metrics
curl -s http://localhost:8080/status/performance | jq .

# Analyze response time trends
python3 scripts/analyze_response_times.py --last-24h

# Check resource utilization
python3 scripts/resource_utilization.py
```

### Optimization Procedures

#### Connection Pool Optimization

```bash
# Analyze connection pool usage
python3 scripts/analyze_connection_pools.py

# Optimize pool sizes
vim config/examples/production_config.yaml
# Update connection_pool_size based on analysis

# Apply changes
python3 scripts/deploy_enhanced_status_check.py --config-only
```

#### Timeout Optimization

```bash
# Analyze timeout patterns
python3 scripts/analyze_timeouts.py --last-week

# Optimize timeout values
python3 scripts/optimize_timeouts.py --recommend

# Test optimized values in staging
python3 scripts/test_timeout_optimization.py --environment staging
```

#### Caching Optimization

```bash
# Enable response caching
vim config/examples/production_config.yaml
# Add caching configuration

# Monitor cache hit rates
python3 scripts/monitor_cache_performance.py
```

## Security Operations

### Security Monitoring

```bash
# Check authentication logs
grep -i "auth" logs/enhanced_status_check.log | grep -i "fail"

# Monitor for suspicious activity
python3 scripts/security_monitor.py --check-anomalies

# Verify JWT token integrity
python3 scripts/verify_jwt_tokens.py
```

### Security Incident Response

#### Unauthorized Access Attempt

1. **Immediate Actions**
   ```bash
   # Block suspicious IPs
   python3 scripts/block_suspicious_ips.py
   
   # Rotate authentication tokens
   python3 scripts/rotate_auth_tokens.py
   ```

2. **Investigation**
   ```bash
   # Analyze access logs
   python3 scripts/analyze_access_logs.py --suspicious
   
   # Check for data breaches
   python3 scripts/check_data_integrity.py
   ```

3. **Recovery**
   ```bash
   # Update security configuration
   python3 scripts/update_security_config.py
   
   # Notify security team
   python3 scripts/security_notification.py --incident
   ```

### Regular Security Tasks

#### Weekly Security Review

```bash
# Check for security updates
python3 scripts/security_update_check.py

# Review access logs
python3 scripts/weekly_security_review.py

# Validate authentication configuration
python3 scripts/validate_auth_config.py
```

#### Monthly Security Audit

```bash
# Full security audit
python3 scripts/security_audit.py --comprehensive

# Update security policies
python3 scripts/update_security_policies.py

# Test incident response procedures
python3 scripts/test_incident_response.py --dry-run
```

## Contact Information

### Escalation Matrix

| Severity | Contact | Response Time |
|----------|---------|---------------|
| Critical | On-call Engineer | 15 minutes |
| High | Team Lead | 1 hour |
| Medium | Development Team | 4 hours |
| Low | Support Team | 24 hours |

### Key Contacts

- **On-call Engineer**: +1-555-0123
- **Team Lead**: team-lead@example.com
- **DevOps Team**: devops@example.com
- **Security Team**: security@example.com

### Communication Channels

- **Slack**: #enhanced-mcp-status-alerts
- **Email**: enhanced-mcp-alerts@example.com
- **PagerDuty**: Enhanced MCP Status Service

---

**Document Version**: 1.0  
**Last Updated**: $(date +%Y-%m-%d)  
**Next Review**: $(date -d "+3 months" +%Y-%m-%d)