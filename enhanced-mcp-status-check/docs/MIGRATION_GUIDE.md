# Enhanced MCP Status Check - Migration Guide

## Overview

This migration guide helps you transition from existing status check implementations to the Enhanced MCP Status Check system. The guide covers migration from basic health checks, single-protocol monitoring, and legacy monitoring systems to the new dual monitoring approach.

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Pre-Migration Assessment](#pre-migration-assessment)
3. [Migration Scenarios](#migration-scenarios)
4. [Step-by-Step Migration](#step-by-step-migration)
5. [Configuration Migration](#configuration-migration)
6. [Data Migration](#data-migration)
7. [Testing and Validation](#testing-and-validation)
8. [Rollback Procedures](#rollback-procedures)
9. [Post-Migration Optimization](#post-migration-optimization)

## Migration Overview

### What's New in Enhanced Status Check

The Enhanced MCP Status Check system introduces several key improvements:

1. **Dual Monitoring**: Both MCP tools/list and REST health checks
2. **Intelligent Aggregation**: Smart combination of monitoring results
3. **Enhanced Circuit Breaker**: Separate circuit states for MCP and REST
4. **Comprehensive Metrics**: Detailed metrics for both monitoring methods
5. **Flexible Configuration**: Granular control over monitoring behavior
6. **Backward Compatibility**: Maintains compatibility with existing APIs

### Migration Benefits

- **Improved Reliability**: Dual monitoring provides redundancy
- **Better Insights**: More detailed health and performance metrics
- **Enhanced Alerting**: Smarter alerting based on multiple data points
- **Flexible Deployment**: Gradual migration with fallback options
- **Future-Proof**: Extensible architecture for additional monitoring methods

## Pre-Migration Assessment

### Current System Inventory

Before starting migration, assess your current monitoring setup:

#### 1. Identify Current Monitoring Systems

```bash
# List current health check endpoints
curl http://localhost:8080/status/health
curl http://localhost:8080/health
curl http://localhost:8080/healthz

# Check for existing MCP endpoints
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Identify monitoring tools in use
ps aux | grep -E "(prometheus|grafana|nagios|zabbix)"
```

#### 2. Document Current Configuration

Create an inventory of your current setup:

```json
{
  "current_monitoring": {
    "type": "rest_only|mcp_only|basic_health",
    "endpoints": [
      {
        "server_name": "restaurant-search-mcp",
        "health_endpoint": "http://localhost:8080/status/health",
        "mcp_endpoint": "http://localhost:8080/mcp",
        "monitoring_frequency": "30s",
        "alerting_configured": true
      }
    ],
    "metrics_collection": {
      "enabled": true,
      "system": "prometheus|custom|none",
      "retention_period": "7d"
    },
    "alerting": {
      "system": "slack|pagerduty|email",
      "thresholds": {
        "response_time_ms": 5000,
        "failure_rate": 0.1
      }
    }
  }
}
```

#### 3. Assess Dependencies

Identify systems that depend on your current monitoring:

- Dashboards (Grafana, custom)
- Alerting systems (PagerDuty, Slack)
- Load balancers (health check endpoints)
- Orchestration systems (Kubernetes, Docker Swarm)
- CI/CD pipelines

## Migration Scenarios

### Scenario 1: REST-Only to Dual Monitoring

**Current State**: Only REST health checks
**Target State**: MCP + REST dual monitoring

**Migration Complexity**: Medium
**Estimated Time**: 2-4 hours
**Downtime Required**: None (zero-downtime migration)

### Scenario 2: MCP-Only to Dual Monitoring

**Current State**: Only MCP tools/list checks
**Target State**: MCP + REST dual monitoring

**Migration Complexity**: Medium
**Estimated Time**: 2-4 hours
**Downtime Required**: None

### Scenario 3: Basic Health Check to Enhanced System

**Current State**: Simple health endpoints
**Target State**: Full enhanced monitoring

**Migration Complexity**: High
**Estimated Time**: 4-8 hours
**Downtime Required**: Minimal (< 5 minutes)

### Scenario 4: Legacy Monitoring System Migration

**Current State**: Custom or third-party monitoring
**Target State**: Enhanced MCP status check

**Migration Complexity**: High
**Estimated Time**: 1-2 days
**Downtime Required**: Planned maintenance window

## Step-by-Step Migration

### Phase 1: Preparation

#### 1.1 Install Enhanced Status Check System

```bash
# Clone the repository
git clone <repository-url>
cd enhanced-mcp-status-check

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m enhanced_mcp_status_check --version
```

#### 1.2 Create Migration Configuration

Create a migration-specific configuration:

```json
{
  "enhanced_status_check_system": {
    "dual_monitoring_enabled": true,
    "migration_mode": true,
    "global_settings": {
      "check_interval_seconds": 60,
      "max_concurrent_checks": 5,
      "retry_attempts": 2
    },
    "servers": [
      {
        "server_name": "restaurant-search-mcp",
        "mcp_endpoint_url": "http://localhost:8080/mcp",
        "rest_health_endpoint_url": "http://localhost:8080/status/health",
        "mcp_enabled": true,
        "rest_enabled": true,
        "migration_settings": {
          "validate_against_legacy": true,
          "legacy_endpoint": "http://localhost:8080/health"
        }
      }
    ],
    "backward_compatibility": {
      "enabled": true,
      "legacy_endpoints": ["/health", "/healthz"],
      "response_format": "legacy_compatible"
    }
  }
}
```

#### 1.3 Set Up Parallel Environment

Run the enhanced system alongside your existing monitoring:

```bash
# Start enhanced system on different port
python -m enhanced_mcp_status_check \
  --config config/migration.json \
  --port 8081 \
  --migration-mode
```

### Phase 2: Configuration Migration

#### 2.1 Convert REST-Only Configuration

**Before (Legacy REST):**
```json
{
  "health_checks": {
    "servers": [
      {
        "name": "restaurant-search",
        "url": "http://localhost:8080/health",
        "timeout": 10,
        "interval": 30
      }
    ]
  }
}
```

**After (Enhanced Dual):**
```json
{
  "enhanced_status_check_system": {
    "servers": [
      {
        "server_name": "restaurant-search",
        "mcp_endpoint_url": "http://localhost:8080/mcp",
        "rest_health_endpoint_url": "http://localhost:8080/health",
        "mcp_enabled": true,
        "rest_enabled": true,
        "rest_timeout_seconds": 10,
        "mcp_timeout_seconds": 10,
        "mcp_priority_weight": 0.6,
        "rest_priority_weight": 0.4
      }
    ],
    "global_settings": {
      "check_interval_seconds": 30
    }
  }
}
```

#### 2.2 Convert MCP-Only Configuration

**Before (Legacy MCP):**
```json
{
  "mcp_monitoring": {
    "servers": [
      {
        "name": "restaurant-search",
        "mcp_url": "http://localhost:8080/mcp",
        "expected_tools": ["search_restaurants", "recommend_restaurants"],
        "timeout": 15
      }
    ]
  }
}
```

**After (Enhanced Dual):**
```json
{
  "enhanced_status_check_system": {
    "servers": [
      {
        "server_name": "restaurant-search",
        "mcp_endpoint_url": "http://localhost:8080/mcp",
        "rest_health_endpoint_url": "http://localhost:8080/status/health",
        "mcp_enabled": true,
        "rest_enabled": true,
        "mcp_timeout_seconds": 15,
        "mcp_expected_tools": ["search_restaurants", "recommend_restaurants"],
        "mcp_priority_weight": 0.8,
        "rest_priority_weight": 0.2
      }
    ]
  }
}
```

#### 2.3 Migration Script for Configuration

```python
#!/usr/bin/env python3
"""Configuration migration script."""

import json
import argparse
from pathlib import Path

def migrate_rest_only_config(legacy_config):
    """Migrate REST-only configuration to enhanced dual monitoring."""
    enhanced_config = {
        "enhanced_status_check_system": {
            "dual_monitoring_enabled": True,
            "servers": [],
            "global_settings": {
                "check_interval_seconds": 30,
                "max_concurrent_checks": 10,
                "retry_attempts": 3
            }
        }
    }
    
    for server in legacy_config.get("health_checks", {}).get("servers", []):
        enhanced_server = {
            "server_name": server["name"],
            "mcp_endpoint_url": server["url"].replace("/health", "/mcp"),
            "rest_health_endpoint_url": server["url"],
            "mcp_enabled": True,
            "rest_enabled": True,
            "rest_timeout_seconds": server.get("timeout", 10),
            "mcp_timeout_seconds": server.get("timeout", 10),
            "mcp_priority_weight": 0.6,
            "rest_priority_weight": 0.4
        }
        
        if "interval" in server:
            enhanced_config["enhanced_status_check_system"]["global_settings"]["check_interval_seconds"] = server["interval"]
        
        enhanced_config["enhanced_status_check_system"]["servers"].append(enhanced_server)
    
    return enhanced_config

def migrate_mcp_only_config(legacy_config):
    """Migrate MCP-only configuration to enhanced dual monitoring."""
    enhanced_config = {
        "enhanced_status_check_system": {
            "dual_monitoring_enabled": True,
            "servers": [],
            "mcp_health_checks": {
                "enabled": True,
                "tools_list_validation": True,
                "expected_tools_validation": True
            },
            "rest_health_checks": {
                "enabled": True
            }
        }
    }
    
    for server in legacy_config.get("mcp_monitoring", {}).get("servers", []):
        enhanced_server = {
            "server_name": server["name"],
            "mcp_endpoint_url": server["mcp_url"],
            "rest_health_endpoint_url": server["mcp_url"].replace("/mcp", "/status/health"),
            "mcp_enabled": True,
            "rest_enabled": True,
            "mcp_timeout_seconds": server.get("timeout", 15),
            "mcp_expected_tools": server.get("expected_tools", []),
            "mcp_priority_weight": 0.8,
            "rest_priority_weight": 0.2
        }
        
        enhanced_config["enhanced_status_check_system"]["servers"].append(enhanced_server)
    
    return enhanced_config

def main():
    parser = argparse.ArgumentParser(description="Migrate legacy configuration to enhanced format")
    parser.add_argument("--input", required=True, help="Input legacy configuration file")
    parser.add_argument("--output", required=True, help="Output enhanced configuration file")
    parser.add_argument("--type", choices=["rest-only", "mcp-only", "basic"], required=True, help="Legacy configuration type")
    
    args = parser.parse_args()
    
    # Load legacy configuration
    with open(args.input, 'r') as f:
        legacy_config = json.load(f)
    
    # Migrate based on type
    if args.type == "rest-only":
        enhanced_config = migrate_rest_only_config(legacy_config)
    elif args.type == "mcp-only":
        enhanced_config = migrate_mcp_only_config(legacy_config)
    else:
        raise ValueError(f"Unsupported migration type: {args.type}")
    
    # Save enhanced configuration
    with open(args.output, 'w') as f:
        json.dump(enhanced_config, f, indent=2)
    
    print(f"Configuration migrated successfully: {args.input} -> {args.output}")

if __name__ == "__main__":
    main()
```

### Phase 3: Data Migration

#### 3.1 Migrate Historical Metrics

```python
#!/usr/bin/env python3
"""Migrate historical metrics data."""

import json
import sqlite3
from datetime import datetime, timedelta

class MetricsMigrator:
    def __init__(self, legacy_db_path, enhanced_db_path):
        self.legacy_db = sqlite3.connect(legacy_db_path)
        self.enhanced_db = sqlite3.connect(enhanced_db_path)
        self.setup_enhanced_schema()
    
    def setup_enhanced_schema(self):
        """Create enhanced metrics schema."""
        self.enhanced_db.execute("""
            CREATE TABLE IF NOT EXISTS dual_health_checks (
                id INTEGER PRIMARY KEY,
                server_name TEXT,
                timestamp DATETIME,
                overall_status TEXT,
                mcp_success BOOLEAN,
                rest_success BOOLEAN,
                mcp_response_time_ms REAL,
                rest_response_time_ms REAL,
                combined_response_time_ms REAL,
                health_score REAL
            )
        """)
    
    def migrate_rest_metrics(self):
        """Migrate REST-only metrics to dual format."""
        cursor = self.legacy_db.execute("""
            SELECT server_name, timestamp, status, response_time_ms
            FROM health_checks
            WHERE timestamp > ?
        """, (datetime.now() - timedelta(days=30),))
        
        for row in cursor:
            server_name, timestamp, status, response_time_ms = row
            
            # Convert to dual format
            self.enhanced_db.execute("""
                INSERT INTO dual_health_checks (
                    server_name, timestamp, overall_status,
                    mcp_success, rest_success,
                    mcp_response_time_ms, rest_response_time_ms,
                    combined_response_time_ms, health_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                server_name, timestamp, status,
                None, status == "healthy",  # No MCP data in legacy
                None, response_time_ms,
                response_time_ms, 1.0 if status == "healthy" else 0.0
            ))
        
        self.enhanced_db.commit()
    
    def migrate_mcp_metrics(self):
        """Migrate MCP-only metrics to dual format."""
        cursor = self.legacy_db.execute("""
            SELECT server_name, timestamp, success, response_time_ms, tools_count
            FROM mcp_checks
            WHERE timestamp > ?
        """, (datetime.now() - timedelta(days=30),))
        
        for row in cursor:
            server_name, timestamp, success, response_time_ms, tools_count = row
            
            # Convert to dual format
            self.enhanced_db.execute("""
                INSERT INTO dual_health_checks (
                    server_name, timestamp, overall_status,
                    mcp_success, rest_success,
                    mcp_response_time_ms, rest_response_time_ms,
                    combined_response_time_ms, health_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                server_name, timestamp, "healthy" if success else "unhealthy",
                success, None,  # No REST data in legacy
                response_time_ms, None,
                response_time_ms, 1.0 if success else 0.0
            ))
        
        self.enhanced_db.commit()

# Usage
migrator = MetricsMigrator("legacy_metrics.db", "enhanced_metrics.db")
migrator.migrate_rest_metrics()
```

#### 3.2 Migrate Alert Configurations

```python
#!/usr/bin/env python3
"""Migrate alerting configurations."""

def migrate_alerting_config(legacy_alerts):
    """Convert legacy alerting to enhanced format."""
    enhanced_alerts = {
        "alerting": {
            "enabled": True,
            "alert_thresholds": {},
            "notification_channels": []
        }
    }
    
    # Migrate thresholds
    if "response_time_threshold" in legacy_alerts:
        enhanced_alerts["alerting"]["alert_thresholds"]["response_time_warning_ms"] = legacy_alerts["response_time_threshold"]
        enhanced_alerts["alerting"]["alert_thresholds"]["response_time_critical_ms"] = legacy_alerts["response_time_threshold"] * 2
    
    if "failure_rate_threshold" in legacy_alerts:
        enhanced_alerts["alerting"]["alert_thresholds"]["warning_failure_rate"] = legacy_alerts["failure_rate_threshold"]
        enhanced_alerts["alerting"]["alert_thresholds"]["critical_failure_rate"] = legacy_alerts["failure_rate_threshold"] * 2
    
    # Migrate notification channels
    for channel in legacy_alerts.get("channels", []):
        if channel["type"] == "slack":
            enhanced_alerts["alerting"]["webhook_url"] = channel["webhook_url"]
        elif channel["type"] == "pagerduty":
            enhanced_alerts["alerting"]["pagerduty_integration_key"] = channel["integration_key"]
        elif channel["type"] == "email":
            enhanced_alerts["alerting"]["email_notifications"] = channel["email"]
    
    return enhanced_alerts
```

### Phase 4: Testing and Validation

#### 4.1 Parallel Testing

Run both systems in parallel to validate behavior:

```bash
#!/bin/bash
# Parallel testing script

echo "Starting parallel testing..."

# Test legacy system
echo "Testing legacy system..."
LEGACY_RESPONSE=$(curl -s http://localhost:8080/health)
LEGACY_STATUS=$(echo $LEGACY_RESPONSE | jq -r '.status')

# Test enhanced system
echo "Testing enhanced system..."
ENHANCED_RESPONSE=$(curl -s http://localhost:8081/status/health)
ENHANCED_STATUS=$(echo $ENHANCED_RESPONSE | jq -r '.status')

# Compare results
echo "Legacy Status: $LEGACY_STATUS"
echo "Enhanced Status: $ENHANCED_STATUS"

if [ "$LEGACY_STATUS" = "$ENHANCED_STATUS" ]; then
    echo "✅ Status comparison: PASS"
else
    echo "❌ Status comparison: FAIL"
    echo "Legacy: $LEGACY_RESPONSE"
    echo "Enhanced: $ENHANCED_RESPONSE"
fi

# Test response times
LEGACY_TIME=$(echo $LEGACY_RESPONSE | jq -r '.response_time_ms // 0')
ENHANCED_TIME=$(echo $ENHANCED_RESPONSE | jq -r '.overall_metrics.average_response_time_ms // 0')

echo "Legacy Response Time: ${LEGACY_TIME}ms"
echo "Enhanced Response Time: ${ENHANCED_TIME}ms"

# Validate enhanced features
echo "Testing enhanced features..."
curl -s http://localhost:8081/status/servers | jq '.servers[0].mcp_result.success'
curl -s http://localhost:8081/status/servers | jq '.servers[0].rest_result.success'
```

#### 4.2 Load Testing

```python
#!/usr/bin/env python3
"""Load testing for migration validation."""

import asyncio
import aiohttp
import time
from statistics import mean

async def test_endpoint(session, url, num_requests=100):
    """Test endpoint performance."""
    response_times = []
    success_count = 0
    
    for i in range(num_requests):
        start_time = time.time()
        try:
            async with session.get(url) as response:
                await response.text()
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                
                if response.status == 200:
                    success_count += 1
        except Exception as e:
            print(f"Request {i} failed: {e}")
    
    return {
        "success_rate": success_count / num_requests,
        "average_response_time": mean(response_times) if response_times else 0,
        "total_requests": num_requests
    }

async def compare_performance():
    """Compare legacy vs enhanced performance."""
    async with aiohttp.ClientSession() as session:
        # Test legacy system
        legacy_results = await test_endpoint(
            session, "http://localhost:8080/health"
        )
        
        # Test enhanced system
        enhanced_results = await test_endpoint(
            session, "http://localhost:8081/status/health"
        )
        
        print("Performance Comparison:")
        print(f"Legacy - Success Rate: {legacy_results['success_rate']:.2%}, Avg Response: {legacy_results['average_response_time']:.2f}ms")
        print(f"Enhanced - Success Rate: {enhanced_results['success_rate']:.2%}, Avg Response: {enhanced_results['average_response_time']:.2f}ms")

if __name__ == "__main__":
    asyncio.run(compare_performance())
```

### Phase 5: Cutover

#### 5.1 Gradual Traffic Migration

```bash
#!/bin/bash
# Gradual traffic migration script

echo "Starting gradual migration..."

# Phase 1: 10% traffic to enhanced system
echo "Phase 1: Routing 10% traffic to enhanced system"
# Update load balancer configuration
# curl -X POST http://load-balancer/config \
#   -d '{"upstream": [{"server": "localhost:8080", "weight": 90}, {"server": "localhost:8081", "weight": 10}]}'

sleep 300  # Wait 5 minutes

# Phase 2: 50% traffic
echo "Phase 2: Routing 50% traffic to enhanced system"
# curl -X POST http://load-balancer/config \
#   -d '{"upstream": [{"server": "localhost:8080", "weight": 50}, {"server": "localhost:8081", "weight": 50}]}'

sleep 300

# Phase 3: 100% traffic
echo "Phase 3: Routing 100% traffic to enhanced system"
# curl -X POST http://load-balancer/config \
#   -d '{"upstream": [{"server": "localhost:8081", "weight": 100}]}'

echo "Migration complete!"
```

#### 5.2 DNS Cutover

```bash
#!/bin/bash
# DNS cutover for complete migration

# Update DNS records to point to enhanced system
# aws route53 change-resource-record-sets \
#   --hosted-zone-id Z123456789 \
#   --change-batch '{
#     "Changes": [{
#       "Action": "UPSERT",
#       "ResourceRecordSet": {
#         "Name": "health-check.company.com",
#         "Type": "A",
#         "TTL": 60,
#         "ResourceRecords": [{"Value": "new-enhanced-server-ip"}]
#       }
#     }]
#   }'

echo "DNS updated. Waiting for propagation..."
sleep 300

# Verify DNS propagation
nslookup health-check.company.com
```

## Rollback Procedures

### Automated Rollback Script

```bash
#!/bin/bash
# Automated rollback script

ROLLBACK_REASON=${1:-"Manual rollback"}
BACKUP_CONFIG="config/backup/legacy-config.json"
LEGACY_PORT=8080
ENHANCED_PORT=8081

echo "🔄 Starting rollback procedure..."
echo "Reason: $ROLLBACK_REASON"

# Step 1: Stop enhanced system
echo "Stopping enhanced system..."
pkill -f "enhanced_mcp_status_check"

# Step 2: Restore legacy configuration
echo "Restoring legacy configuration..."
if [ -f "$BACKUP_CONFIG" ]; then
    cp "$BACKUP_CONFIG" config/current-config.json
else
    echo "❌ Backup configuration not found!"
    exit 1
fi

# Step 3: Start legacy system
echo "Starting legacy system..."
python -m legacy_health_check --config config/current-config.json --port $LEGACY_PORT &

# Step 4: Update load balancer
echo "Updating load balancer to route to legacy system..."
# curl -X POST http://load-balancer/config \
#   -d '{"upstream": [{"server": "localhost:8080", "weight": 100}]}'

# Step 5: Verify rollback
sleep 10
HEALTH_CHECK=$(curl -s http://localhost:$LEGACY_PORT/health)
if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo "✅ Rollback successful!"
    echo "Legacy system is responding normally"
else
    echo "❌ Rollback failed!"
    echo "Response: $HEALTH_CHECK"
    exit 1
fi

# Step 6: Log rollback
echo "$(date): Rollback completed - $ROLLBACK_REASON" >> logs/migration.log

echo "🎉 Rollback procedure completed successfully"
```

### Manual Rollback Checklist

1. **Stop Enhanced System**
   ```bash
   sudo systemctl stop enhanced-mcp-status-check
   ```

2. **Restore Legacy Configuration**
   ```bash
   cp config/backup/legacy-config.json config/active-config.json
   ```

3. **Start Legacy System**
   ```bash
   sudo systemctl start legacy-health-check
   ```

4. **Update Load Balancer**
   - Revert upstream configuration
   - Remove enhanced system from rotation

5. **Update DNS (if changed)**
   ```bash
   # Revert DNS changes
   aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://rollback-dns.json
   ```

6. **Verify Services**
   ```bash
   curl http://localhost:8080/health
   ```

7. **Update Monitoring**
   - Revert Prometheus configuration
   - Update Grafana dashboards
   - Restore alerting rules

## Post-Migration Optimization

### Performance Tuning

After successful migration, optimize the enhanced system:

#### 1. Adjust Check Intervals

```json
{
  "global_settings": {
    "check_interval_seconds": 15,  // Reduce for more frequent checks
    "max_concurrent_checks": 20    // Increase for better parallelism
  }
}
```

#### 2. Optimize Connection Pools

```json
{
  "mcp_health_checks": {
    "connection_pool_size": 15,
    "keep_alive_enabled": true
  },
  "rest_health_checks": {
    "connection_pool_size": 25
  }
}
```

#### 3. Fine-tune Circuit Breaker

```json
{
  "circuit_breaker": {
    "failure_threshold": 8,
    "success_threshold": 5,
    "timeout_seconds": 120
  }
}
```

### Monitoring Enhancement

#### 1. Set Up Advanced Dashboards

```yaml
# grafana-dashboard.json
{
  "dashboard": {
    "title": "Enhanced MCP Status Check",
    "panels": [
      {
        "title": "Dual Monitoring Success Rate",
        "targets": [
          {
            "expr": "rate(mcp_requests_total{status=\"success\"}[5m]) / rate(mcp_requests_total[5m])",
            "legendFormat": "MCP Success Rate"
          },
          {
            "expr": "rate(rest_requests_total{status=\"success\"}[5m]) / rate(rest_requests_total[5m])",
            "legendFormat": "REST Success Rate"
          }
        ]
      }
    ]
  }
}
```

#### 2. Configure Advanced Alerting

```yaml
# alerting-rules.yml
groups:
  - name: enhanced-mcp-status-check
    rules:
      - alert: DualMonitoringFailure
        expr: (mcp_success_rate < 0.8) AND (rest_success_rate < 0.8)
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Both MCP and REST monitoring failing for {{ $labels.server }}"
          
      - alert: SinglePathDegraded
        expr: (mcp_success_rate < 0.8) OR (rest_success_rate < 0.8)
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Single monitoring path degraded for {{ $labels.server }}"
```

### Security Hardening

#### 1. Enable Authentication

```json
{
  "authentication": {
    "jwt_enabled": true,
    "jwt_discovery_url": "https://your-auth-provider/.well-known/openid-configuration",
    "api_key_enabled": true,
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 1000
    }
  }
}
```

#### 2. Configure TLS

```json
{
  "tls": {
    "enabled": true,
    "cert_file": "/etc/ssl/certs/enhanced-status-check.crt",
    "key_file": "/etc/ssl/private/enhanced-status-check.key",
    "min_version": "1.2"
  }
}
```

## Migration Validation Checklist

### Pre-Migration
- [ ] Current system inventory completed
- [ ] Dependencies identified and documented
- [ ] Migration configuration created and tested
- [ ] Backup procedures verified
- [ ] Rollback plan tested

### During Migration
- [ ] Enhanced system running in parallel
- [ ] Configuration migrated and validated
- [ ] Historical data migrated (if required)
- [ ] Load testing completed successfully
- [ ] Gradual traffic migration executed

### Post-Migration
- [ ] All endpoints responding correctly
- [ ] Metrics collection working
- [ ] Alerting configured and tested
- [ ] Performance meets or exceeds baseline
- [ ] Documentation updated
- [ ] Team trained on new system

### 30-Day Post-Migration
- [ ] System stability confirmed
- [ ] Performance optimizations applied
- [ ] Legacy system decommissioned
- [ ] Migration lessons learned documented

## Troubleshooting Migration Issues

### Common Migration Problems

#### 1. Configuration Validation Errors

**Problem**: Enhanced system fails to start due to configuration errors.

**Solution**:
```bash
# Validate configuration
python -m enhanced_mcp_status_check.config.config_validator config/migration.json

# Check specific errors
python -c "
from enhanced_mcp_status_check.config.config_loader import ConfigLoader
try:
    config = ConfigLoader.load_config('config/migration.json')
    print('Configuration valid')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

#### 2. Endpoint Compatibility Issues

**Problem**: Legacy clients can't connect to enhanced system.

**Solution**:
```json
{
  "backward_compatibility": {
    "enabled": true,
    "legacy_endpoints": ["/health", "/healthz", "/status"],
    "response_format": "legacy_compatible"
  }
}
```

#### 3. Performance Degradation

**Problem**: Enhanced system is slower than legacy system.

**Solution**:
```json
{
  "performance_optimization": {
    "connection_pooling": true,
    "response_caching": {
      "enabled": true,
      "ttl_seconds": 30
    },
    "async_processing": true
  }
}
```

### Getting Help

If you encounter issues during migration:

1. **Check Logs**: Review detailed logs for error messages
2. **Validate Configuration**: Use built-in validation tools
3. **Test Connectivity**: Verify network connectivity to all endpoints
4. **Review Documentation**: Check troubleshooting guide
5. **Contact Support**: Reach out with specific error details

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Maintainers**: Enhanced MCP Status Check Migration Team