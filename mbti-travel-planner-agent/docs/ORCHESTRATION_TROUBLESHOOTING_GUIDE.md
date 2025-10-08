# Tool Orchestration Troubleshooting Guide

## Table of Contents

1. [Common Issues and Solutions](#common-issues-and-solutions)
2. [Diagnostic Tools and Commands](#diagnostic-tools-and-commands)
3. [Performance Issues](#performance-issues)
4. [Tool Integration Problems](#tool-integration-problems)
5. [Configuration Issues](#configuration-issues)
6. [Error Analysis](#error-analysis)
7. [Monitoring and Debugging](#monitoring-and-debugging)
8. [Recovery Procedures](#recovery-procedures)

## Common Issues and Solutions

### Issue 1: Tool Selection Failures

**Symptoms:**
- Orchestration requests fail with "No suitable tools found"
- Tool selection confidence scores are consistently low
- Fallback tools are not being selected

**Diagnostic Steps:**
```python
# Check tool registry status
from services.tool_registry import ToolRegistry

tool_registry = ToolRegistry()
registered_tools = await tool_registry.list_tools()

print("Registered Tools:")
for tool in registered_tools:
    print(f"- {tool.tool_id}: {tool.status} (Health: {tool.health_status})")

# Check tool capabilities
for tool in registered_tools:
    capabilities = await tool_registry.get_tool_capabilities(tool.tool_id)
    print(f"{tool.tool_id} capabilities: {[cap.name for cap in capabilities]}")
```

**Common Causes and Solutions:**

1. **Tools not registered properly**
   ```python
   # Solution: Re-register tools
   await tool_registry.register_tool(tool_metadata)
   ```

2. **Tool health checks failing**
   ```python
   # Check tool health
   health_status = await tool_registry.check_tool_health("restaurant_search")
   if health_status.status != "healthy":
       print(f"Tool health issue: {health_status.message}")
       # Restart tool or check MCP endpoint
   ```

3. **Capability mismatch**
   ```python
   # Debug intent analysis
   from services.intent_analyzer import IntentAnalyzer
   
   analyzer = IntentAnalyzer()
   intent = await analyzer.analyze_intent(user_request.text, user_request.context)
   
   print(f"Required capabilities: {intent.required_capabilities}")
   print(f"Available capabilities: {[cap for tool in registered_tools for cap in tool.capabilities]}")
   ```

### Issue 2: Workflow Execution Timeouts

**Symptoms:**
- Workflows consistently timeout
- Partial results returned
- High latency in tool responses

**Diagnostic Steps:**
```python
# Check workflow execution metrics
from services.performance_monitor import PerformanceMonitor

perf_monitor = PerformanceMonitor()
workflow_metrics = await perf_monitor.get_workflow_metrics("SEARCH_AND_RECOMMEND")

print(f"Average execution time: {workflow_metrics.avg_execution_time}s")
print(f"Timeout rate: {workflow_metrics.timeout_rate:.2%}")
print(f"Step breakdown: {workflow_metrics.step_performance}")
```

**Common Causes and Solutions:**

1. **MCP server response delays**
   ```python
   # Check MCP server response times
   mcp_metrics = await perf_monitor.get_mcp_server_metrics()
   for server, metrics in mcp_metrics.items():
       if metrics.avg_response_time > 5.0:
           print(f"Slow MCP server: {server} ({metrics.avg_response_time}s)")
   
   # Solution: Increase timeouts or optimize MCP servers
   ```

2. **Network connectivity issues**
   ```bash
   # Test MCP server connectivity
   curl -X POST https://restaurant-search-mcp.example.com/health \
     -H "Content-Type: application/json" \
     -w "Response time: %{time_total}s\n"
   ```

3. **Resource constraints**
   ```python
   # Check system resources
   import psutil
   
   cpu_usage = psutil.cpu_percent(interval=1)
   memory_usage = psutil.virtual_memory().percent
   
   if cpu_usage > 80 or memory_usage > 80:
       print(f"High resource usage - CPU: {cpu_usage}%, Memory: {memory_usage}%")
   ```

### Issue 3: Authentication Failures

**Symptoms:**
- "Authentication failed" errors
- JWT token validation failures
- Unauthorized access to tools

**Diagnostic Steps:**
```python
# Validate JWT token
from services.authentication_manager import AuthenticationManager

auth_manager = AuthenticationManager()
token_validation = await auth_manager.validate_jwt_token(jwt_token)

if not token_validation.is_valid:
    print(f"Token validation failed: {token_validation.error}")
    print(f"Token claims: {token_validation.claims}")
```

**Common Causes and Solutions:**

1. **Expired JWT tokens**
   ```python
   # Check token expiration
   import jwt
   
   try:
       decoded = jwt.decode(jwt_token, options={"verify_signature": False})
       exp_timestamp = decoded.get('exp')
       if exp_timestamp and time.time() > exp_timestamp:
           print("Token has expired")
           # Solution: Refresh token
           new_token = await auth_manager.refresh_token(refresh_token)
   except jwt.InvalidTokenError as e:
       print(f"Invalid token: {e}")
   ```

2. **Incorrect OIDC configuration**
   ```python
   # Verify OIDC discovery URL
   import requests
   
   discovery_url = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
   response = requests.get(discovery_url)
   
   if response.status_code != 200:
       print(f"OIDC discovery failed: {response.status_code}")
   else:
       config = response.json()
       print(f"JWKS URI: {config.get('jwks_uri')}")
   ```

3. **Missing permissions**
   ```python
   # Check user permissions
   user_permissions = await auth_manager.get_user_permissions(user_id)
   required_permissions = ["orchestration:read", "orchestration:write"]
   
   missing_permissions = [p for p in required_permissions if p not in user_permissions]
   if missing_permissions:
       print(f"Missing permissions: {missing_permissions}")
   ```

### Issue 4: Cache Performance Problems

**Symptoms:**
- Low cache hit rates
- Inconsistent response times
- Memory usage issues

**Diagnostic Steps:**
```python
# Check cache statistics
from services.response_cache import ResponseCache

cache = ResponseCache()
stats = cache.get_statistics()

print(f"Cache hit rate: {stats.hit_rate:.2%}")
print(f"Cache size: {stats.current_size}/{stats.max_size}")
print(f"Memory usage: {stats.memory_usage_mb}MB")
```

**Common Causes and Solutions:**

1. **Cache configuration issues**
   ```python
   # Check cache configuration
   cache_config = cache.get_configuration()
   
   if cache_config.ttl < 60:
       print("Cache TTL too low, consider increasing")
   
   if cache_config.max_size < 1000:
       print("Cache size too small, consider increasing")
   ```

2. **Cache key collisions**
   ```python
   # Analyze cache key distribution
   key_stats = cache.analyze_key_distribution()
   
   if key_stats.collision_rate > 0.1:
       print(f"High cache key collision rate: {key_stats.collision_rate:.2%}")
       # Solution: Improve cache key generation
   ```

3. **Memory pressure**
   ```python
   # Monitor cache evictions
   eviction_stats = cache.get_eviction_statistics()
   
   if eviction_stats.eviction_rate > 0.2:
       print(f"High cache eviction rate: {eviction_stats.eviction_rate:.2%}")
       # Solution: Increase cache size or optimize TTL
   ```

## Diagnostic Tools and Commands

### Health Check Commands

```python
# Comprehensive system health check
from services.orchestration_health_monitor import OrchestrationHealthMonitor

health_monitor = OrchestrationHealthMonitor()
system_health = await health_monitor.perform_comprehensive_health_check()

print(f"Overall status: {system_health.overall_status}")
for component, status in system_health.component_health.items():
    print(f"  {component}: {status.status} - {status.message}")
```

### Performance Diagnostics

```python
# Performance analysis
from services.performance_diagnostics import PerformanceDiagnostics

diagnostics = PerformanceDiagnostics()
performance_report = await diagnostics.generate_performance_report()

print("Performance Report:")
print(f"  Average response time: {performance_report.avg_response_time:.2f}s")
print(f"  95th percentile: {performance_report.p95_response_time:.2f}s")
print(f"  Error rate: {performance_report.error_rate:.2%}")
print(f"  Throughput: {performance_report.requests_per_second:.1f} req/s")

# Identify bottlenecks
bottlenecks = await diagnostics.identify_bottlenecks()
for bottleneck in bottlenecks:
    print(f"Bottleneck: {bottleneck.component} - {bottleneck.description}")
```

### Configuration Validation

```python
# Validate current configuration
from config.orchestration_config import OrchestrationConfig
from config.config_validator import ConfigValidator

config = OrchestrationConfig()
validator = ConfigValidator()
validation_result = validator.validate_orchestration_config(config.to_dict())

if not validation_result.is_valid:
    print("Configuration errors:")
    for error in validation_result.errors:
        print(f"  - {error}")

if validation_result.warnings:
    print("Configuration warnings:")
    for warning in validation_result.warnings:
        print(f"  - {warning}")
```

### Tool Connectivity Tests

```python
# Test MCP tool connectivity
from services.mcp_connectivity_tester import MCPConnectivityTester

connectivity_tester = MCPConnectivityTester()
connectivity_results = await connectivity_tester.test_all_tools()

for tool_id, result in connectivity_results.items():
    status = "✓" if result.success else "✗"
    print(f"{status} {tool_id}: {result.response_time:.2f}s")
    if not result.success:
        print(f"    Error: {result.error_message}")
```

## Performance Issues

### High Latency Troubleshooting

**Step 1: Identify the bottleneck**
```python
# Analyze request traces
from services.trace_analyzer import TraceAnalyzer

trace_analyzer = TraceAnalyzer()
slow_requests = await trace_analyzer.find_slow_requests(threshold=5.0)

for request in slow_requests:
    print(f"Request {request.id}: {request.total_time:.2f}s")
    print("  Breakdown:")
    for step in request.steps:
        print(f"    {step.name}: {step.duration:.2f}s")
```

**Step 2: Check tool performance**
```python
# Analyze tool performance
tool_performance = await perf_monitor.get_tool_performance_analysis()

for tool_id, analysis in tool_performance.items():
    if analysis.avg_response_time > 2.0:
        print(f"Slow tool: {tool_id}")
        print(f"  Average response time: {analysis.avg_response_time:.2f}s")
        print(f"  95th percentile: {analysis.p95_response_time:.2f}s")
        print(f"  Slowest operations: {analysis.slowest_operations}")
```

**Step 3: Optimize based on findings**
```python
# Apply performance optimizations
from services.performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer()
optimization_recommendations = await optimizer.analyze_and_recommend()

for recommendation in optimization_recommendations:
    print(f"Recommendation: {recommendation.title}")
    print(f"  Description: {recommendation.description}")
    print(f"  Expected improvement: {recommendation.expected_improvement}")
    print(f"  Implementation: {recommendation.implementation_steps}")
```

### Memory Usage Issues

**Diagnostic Steps:**
```python
# Memory usage analysis
import tracemalloc
import gc

# Start memory tracing
tracemalloc.start()

# Run orchestration operations
# ... perform operations ...

# Get memory statistics
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

# Get top memory consumers
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 10 memory consumers:")
for stat in top_stats[:10]:
    print(f"  {stat}")

# Force garbage collection
collected = gc.collect()
print(f"Garbage collected: {collected} objects")
```

**Memory Optimization:**
```python
# Implement memory optimization
from services.memory_optimizer import MemoryOptimizer

memory_optimizer = MemoryOptimizer()

# Configure memory limits
memory_optimizer.set_memory_limits({
    "cache_max_size": 500,  # Reduce cache size
    "workflow_history_limit": 100,  # Limit workflow history
    "connection_pool_size": 10  # Reduce connection pool
})

# Enable memory monitoring
await memory_optimizer.enable_memory_monitoring()
```

## Tool Integration Problems

### MCP Server Connection Issues

**Diagnostic Steps:**
```python
# Test MCP server connection
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def test_mcp_connection(mcp_url: str, headers: dict):
    try:
        async with streamablehttp_client(mcp_url, headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test tool listing
                tools = await session.list_tools()
                print(f"Available tools: {[tool.name for tool in tools]}")
                
                # Test tool invocation
                if tools:
                    result = await session.call_tool(
                        tools[0].name, 
                        {"test": "parameter"}
                    )
                    print(f"Tool test result: {result}")
                
                return True
    except Exception as e:
        print(f"MCP connection failed: {e}")
        return False

# Test all registered MCP servers
mcp_servers = [
    ("restaurant-search", "https://restaurant-search-mcp.example.com"),
    ("restaurant-reasoning", "https://restaurant-reasoning-mcp.example.com")
]

for server_name, server_url in mcp_servers:
    print(f"Testing {server_name}...")
    success = await test_mcp_connection(server_url, auth_headers)
    print(f"  Result: {'✓' if success else '✗'}")
```

**Common Solutions:**

1. **Network connectivity issues**
   ```bash
   # Test network connectivity
   ping restaurant-search-mcp.example.com
   telnet restaurant-search-mcp.example.com 443
   
   # Check DNS resolution
   nslookup restaurant-search-mcp.example.com
   ```

2. **Authentication problems**
   ```python
   # Verify JWT token for MCP servers
   jwt_token = await auth_manager.get_mcp_token()
   
   # Test token with MCP server
   headers = {"Authorization": f"Bearer {jwt_token}"}
   response = requests.get(f"{mcp_url}/health", headers=headers)
   
   if response.status_code == 401:
       print("Authentication failed - check JWT token")
   elif response.status_code == 403:
       print("Authorization failed - check permissions")
   ```

3. **MCP protocol version mismatch**
   ```python
   # Check MCP protocol version
   mcp_info = await session.get_server_info()
   print(f"Server MCP version: {mcp_info.protocol_version}")
   print(f"Client MCP version: {mcp.__version__}")
   
   if mcp_info.protocol_version != mcp.__version__:
       print("MCP version mismatch - update client or server")
   ```

### Tool Registration Problems

**Diagnostic Steps:**
```python
# Check tool registration status
from services.tool_registry import ToolRegistry

tool_registry = ToolRegistry()

# List all registered tools
tools = await tool_registry.list_tools()
print(f"Registered tools: {len(tools)}")

for tool in tools:
    print(f"  {tool.tool_id}: {tool.status}")
    
    # Check tool metadata
    metadata = await tool_registry.get_tool_metadata(tool.tool_id)
    print(f"    Capabilities: {[cap.name for cap in metadata.capabilities]}")
    print(f"    Health: {metadata.health_status}")
    print(f"    Last updated: {metadata.last_updated}")
```

**Solutions:**

1. **Re-register tools**
   ```python
   # Re-register tool with updated metadata
   tool_metadata = ToolMetadata(
       tool_id="restaurant_search",
       name="Restaurant Search Tool",
       description="Search for restaurants by location and meal type",
       capabilities=[...],
       mcp_endpoint="https://restaurant-search-mcp.example.com"
   )
   
   await tool_registry.register_tool(tool_metadata)
   ```

2. **Update tool capabilities**
   ```python
   # Update tool capabilities
   await tool_registry.update_tool_capabilities(
       tool_id="restaurant_search",
       capabilities=[
           ToolCapability(
               name="search_by_district",
               description="Search restaurants in specific districts",
               required_parameters=["districts"],
               optional_parameters=["meal_types"]
           )
       ]
   )
   ```

## Configuration Issues

### Environment Configuration Problems

**Diagnostic Steps:**
```python
# Check environment configuration loading
from config.orchestration_config import OrchestrationConfig

config = OrchestrationConfig()
print(f"Environment: {config.environment}")
print(f"Configuration source: {config.config_source}")

# Verify configuration values
print(f"Confidence threshold: {config.orchestration.intent_analysis.confidence_threshold}")
print(f"Tool selection weights: {config.orchestration.tool_selection}")
```

**Common Issues:**

1. **Environment variable not set**
   ```bash
   # Check environment variable
   echo $ORCHESTRATION_ENV
   
   # Set environment variable
   export ORCHESTRATION_ENV=production
   ```

2. **Configuration file not found**
   ```python
   import os
   
   config_file = f"config/environments/orchestration_{os.getenv('ORCHESTRATION_ENV', 'development')}.yaml"
   
   if not os.path.exists(config_file):
       print(f"Configuration file not found: {config_file}")
       # Create default configuration or use base config
   ```

3. **Invalid configuration values**
   ```python
   # Validate and fix configuration
   from config.config_validator import ConfigValidator
   
   validator = ConfigValidator()
   validation_result = validator.validate_orchestration_config(config.to_dict())
   
   if not validation_result.is_valid:
       print("Configuration errors found:")
       for error in validation_result.errors:
           print(f"  - {error}")
       
       # Apply automatic fixes where possible
       fixed_config = validator.apply_automatic_fixes(config.to_dict())
       config.update_from_dict(fixed_config)
   ```

### Runtime Configuration Updates

**Diagnostic Steps:**
```python
# Check runtime configuration manager
from config.runtime_config_manager import RuntimeConfigManager

config_manager = RuntimeConfigManager()

# Check if configuration is locked
if config_manager.is_locked():
    print("Configuration is locked")
    lock_info = config_manager.get_lock_info()
    print(f"  Locked by: {lock_info.locked_by}")
    print(f"  Lock time: {lock_info.lock_time}")

# Check for pending changes
pending_changes = config_manager.get_pending_changes()
if pending_changes:
    print("Pending configuration changes:")
    for change in pending_changes:
        print(f"  {change.path}: {change.old_value} -> {change.new_value}")
```

**Solutions:**

1. **Unlock configuration**
   ```python
   # Force unlock if necessary (use with caution)
   if config_manager.is_locked():
       config_manager.force_unlock()
   ```

2. **Apply pending changes**
   ```python
   # Apply pending configuration changes
   if pending_changes:
       try:
           config_manager.apply_pending_changes()
           print("Configuration changes applied successfully")
       except ConfigurationError as e:
           print(f"Failed to apply changes: {e}")
           config_manager.rollback_pending_changes()
   ```

## Error Analysis

### Error Pattern Analysis

**Analyze error patterns:**
```python
# Error pattern analysis
from services.error_analyzer import ErrorAnalyzer

error_analyzer = ErrorAnalyzer()
error_patterns = await error_analyzer.analyze_error_patterns(time_window="24h")

print("Error Pattern Analysis:")
for pattern in error_patterns:
    print(f"  Pattern: {pattern.error_type}")
    print(f"    Frequency: {pattern.frequency}")
    print(f"    Trend: {pattern.trend}")
    print(f"    Common causes: {pattern.common_causes}")
    print(f"    Recommended actions: {pattern.recommended_actions}")
```

### Error Recovery Strategies

**Implement error recovery:**
```python
# Error recovery implementation
from services.error_recovery import ErrorRecoveryManager

recovery_manager = ErrorRecoveryManager()

# Register recovery strategies
recovery_manager.register_recovery_strategy(
    error_type="ToolTimeoutError",
    strategy=RetryWithBackoffStrategy(max_retries=3, backoff_multiplier=2)
)

recovery_manager.register_recovery_strategy(
    error_type="AuthenticationError",
    strategy=TokenRefreshStrategy()
)

recovery_manager.register_recovery_strategy(
    error_type="ToolUnavailableError",
    strategy=FallbackToolStrategy()
)

# Apply recovery strategies
try:
    result = await orchestration_engine.orchestrate_request(user_request)
except OrchestrationError as e:
    recovery_result = await recovery_manager.attempt_recovery(e, user_request)
    if recovery_result.success:
        result = recovery_result.result
    else:
        # Escalate error
        await error_analyzer.escalate_error(e, recovery_result)
```

## Monitoring and Debugging

### Enable Debug Logging

```python
# Enable comprehensive debug logging
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestration_debug.log'),
        logging.StreamHandler()
    ]
)

# Enable debug mode in orchestration engine
orchestration_engine.enable_debug_mode()

# Enable request tracing
orchestration_engine.enable_request_tracing()
```

### Performance Profiling

```python
# Profile orchestration performance
import cProfile
import pstats

def profile_orchestration():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run orchestration operations
    asyncio.run(orchestration_engine.orchestrate_request(user_request))
    
    profiler.disable()
    
    # Analyze profile results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

profile_orchestration()
```

### Real-time Monitoring

```python
# Set up real-time monitoring
from services.real_time_monitor import RealTimeMonitor

monitor = RealTimeMonitor()

# Monitor key metrics
await monitor.start_monitoring([
    "orchestration.requests.rate",
    "orchestration.response_time.p95",
    "orchestration.error_rate",
    "tools.availability"
])

# Set up alerts
monitor.add_alert(
    metric="orchestration.error_rate",
    threshold=0.05,
    condition="above",
    action="send_notification"
)

# View real-time dashboard
monitor.start_dashboard(port=8080)
```

## Recovery Procedures

### System Recovery Checklist

**When orchestration system is down:**

1. **Check system health**
   ```python
   # Quick health check
   health_status = await health_monitor.quick_health_check()
   print(f"System status: {health_status.overall_status}")
   ```

2. **Verify external dependencies**
   ```bash
   # Check MCP server availability
   curl -f https://restaurant-search-mcp.example.com/health
   curl -f https://restaurant-reasoning-mcp.example.com/health
   
   # Check authentication service
   curl -f https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
   ```

3. **Restart orchestration components**
   ```python
   # Restart orchestration engine
   await orchestration_engine.restart()
   
   # Re-register tools
   await tool_registry.re_register_all_tools()
   
   # Clear caches
   await response_cache.clear_all()
   ```

4. **Verify recovery**
   ```python
   # Test basic functionality
   test_request = UserRequest(
       text="Test request",
       user_id="test-user",
       session_id="test-session"
   )
   
   try:
       result = await orchestration_engine.orchestrate_request(test_request)
       print(f"Recovery test: {'✓' if result.success else '✗'}")
   except Exception as e:
       print(f"Recovery test failed: {e}")
   ```

### Disaster Recovery

**Complete system recovery:**

1. **Backup and restore configuration**
   ```python
   # Backup current configuration
   config_backup = await config_manager.create_backup()
   
   # Restore from backup if needed
   await config_manager.restore_from_backup(backup_id="latest")
   ```

2. **Rebuild tool registry**
   ```python
   # Clear and rebuild tool registry
   await tool_registry.clear_all_tools()
   
   # Re-discover and register tools
   mcp_servers = [
       "https://restaurant-search-mcp.example.com",
       "https://restaurant-reasoning-mcp.example.com"
   ]
   
   for server_url in mcp_servers:
       await tool_registry.discover_and_register_tools(server_url)
   ```

3. **Validate system integrity**
   ```python
   # Run comprehensive system validation
   validation_result = await system_validator.validate_complete_system()
   
   if not validation_result.is_valid:
       print("System validation failed:")
       for issue in validation_result.issues:
           print(f"  - {issue}")
   else:
       print("System recovery completed successfully")
   ```

---

**Troubleshooting Guide Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Maintained By**: MBTI Travel Planner Agent Team