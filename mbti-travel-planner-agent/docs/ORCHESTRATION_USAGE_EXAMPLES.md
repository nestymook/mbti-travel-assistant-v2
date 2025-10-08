# Tool Orchestration Usage Examples

## Table of Contents

1. [Basic Usage Examples](#basic-usage-examples)
2. [Advanced Orchestration Scenarios](#advanced-orchestration-scenarios)
3. [Integration Examples](#integration-examples)
4. [Error Handling Examples](#error-handling-examples)
5. [Performance Optimization Examples](#performance-optimization-examples)
6. [Custom Tool Integration](#custom-tool-integration)

## Basic Usage Examples

### Example 1: Simple Restaurant Search

This example shows how to orchestrate a basic restaurant search by location.

```python
from services.tool_orchestration_engine import ToolOrchestrationEngine
from models.orchestration_types import UserRequest, UserContext

# Initialize orchestration engine
orchestration_engine = ToolOrchestrationEngine()

# Create user request
user_request = UserRequest(
    text="Find restaurants in Central district",
    user_id="user-123",
    session_id="session-456",
    context=UserContext(
        mbti_type="ENFP",
        preferences={
            "cuisine_types": ["Asian", "Italian"],
            "price_range": "moderate"
        }
    )
)

# Process request through orchestration
result = await orchestration_engine.orchestrate_request(user_request)

print(f"Response: {result.response}")
print(f"Tools used: {[tool.tool_name for tool in result.tools_used]}")
print(f"Execution time: {result.execution_metadata.total_execution_time}s")
```

**Expected Output:**
```
Response: I found 12 restaurants in Central district that match your preferences...
Tools used: ['search_restaurants_by_district']
Execution time: 1.2s
```

### Example 2: Restaurant Search with Recommendations

This example demonstrates a multi-step workflow combining search and recommendation tools.

```python
# Create request for search and recommendations
user_request = UserRequest(
    text="Find good lunch places in Central district and recommend the best ones for an ENFP",
    user_id="user-123",
    session_id="session-456",
    context=UserContext(
        mbti_type="ENFP",
        preferences={
            "meal_types": ["lunch"],
            "atmosphere": "lively",
            "social_dining": True
        }
    )
)

# Process with orchestration
result = await orchestration_engine.orchestrate_request(user_request)

# Access detailed workflow information
workflow_result = result.workflow_result
print(f"Workflow type: {workflow_result.workflow_type}")
print(f"Steps executed: {len(workflow_result.steps)}")

for step in workflow_result.steps:
    print(f"Step: {step.step_id}")
    print(f"Tool: {step.tool_id}")
    print(f"Execution time: {step.execution_time}s")
    print(f"Success: {step.success}")
```

**Expected Output:**
```
Workflow type: SEARCH_AND_RECOMMEND
Steps executed: 2
Step: search_restaurants
Tool: restaurant_search
Execution time: 1.1s
Success: True
Step: recommend_restaurants
Tool: restaurant_reasoning
Execution time: 0.9s
Success: True
```

### Example 3: Context-Aware Tool Selection

This example shows how the orchestration system considers user context and conversation history.

```python
# Create user context with conversation history
conversation_history = [
    {
        "timestamp": "2025-10-08T09:00:00Z",
        "request": "What's good for breakfast in Admiralty?",
        "response": "Here are some great breakfast spots in Admiralty..."
    },
    {
        "timestamp": "2025-10-08T09:30:00Z", 
        "request": "Any vegetarian options?",
        "response": "Yes, several restaurants offer vegetarian menus..."
    }
]

user_context = UserContext(
    mbti_type="INFJ",
    preferences={
        "dietary_restrictions": ["vegetarian"],
        "atmosphere": "quiet",
        "group_size": 2
    },
    conversation_history=conversation_history
)

user_request = UserRequest(
    text="Now I need lunch recommendations",
    user_id="user-123",
    session_id="session-456",
    context=user_context
)

# The orchestration engine will consider:
# 1. Previous location preference (Admiralty)
# 2. Dietary restrictions (vegetarian)
# 3. MBTI type preferences (INFJ - quiet atmosphere)
# 4. Meal type progression (breakfast -> lunch)

result = await orchestration_engine.orchestrate_request(user_request)

# Check how context influenced tool selection
intent_trace = result.trace.intent
print(f"Inferred parameters: {intent_trace.parameters}")
print(f"Context influence: {intent_trace.context_influence}")
```

**Expected Output:**
```
Inferred parameters: {
  'meal_types': ['lunch'],
  'districts': ['Admiralty'],
  'dietary_restrictions': ['vegetarian'],
  'atmosphere': 'quiet'
}
Context influence: {
  'location_from_history': 0.8,
  'dietary_from_preferences': 1.0,
  'mbti_atmosphere_match': 0.9
}
```

## Advanced Orchestration Scenarios

### Example 4: Multi-Criteria Search with Result Aggregation

This example shows how to orchestrate multiple search tools and aggregate results.

```python
from services.workflow_engine import WorkflowEngine
from models.orchestration_types import Workflow, WorkflowStep

# Create custom workflow for comprehensive search
workflow = Workflow(
    id="comprehensive_restaurant_search",
    steps=[
        WorkflowStep(
            id="district_search",
            tool_id="restaurant_search",
            tool_name="search_restaurants_by_district",
            input_mapping={
                "districts": "user_request.districts",
                "meal_types": "user_request.meal_types"
            },
            output_mapping={
                "restaurants": "district_results"
            }
        ),
        WorkflowStep(
            id="cuisine_search", 
            tool_id="restaurant_search",
            tool_name="search_restaurants_combined",
            input_mapping={
                "districts": "user_request.districts",
                "cuisine_types": "user_request.cuisine_types"
            },
            output_mapping={
                "restaurants": "cuisine_results"
            }
        ),
        WorkflowStep(
            id="aggregate_results",
            tool_id="result_aggregator",
            tool_name="merge_restaurant_results",
            input_mapping={
                "result_sets": ["district_results", "cuisine_results"],
                "merge_strategy": "weighted_union"
            },
            output_mapping={
                "restaurants": "aggregated_results"
            }
        ),
        WorkflowStep(
            id="mbti_recommendations",
            tool_id="restaurant_reasoning",
            tool_name="recommend_restaurants",
            input_mapping={
                "restaurants": "aggregated_results",
                "mbti_type": "user_context.mbti_type",
                "preferences": "user_context.preferences"
            },
            output_mapping={
                "recommendations": "final_recommendations"
            }
        )
    ],
    execution_strategy="sequential_with_parallel_search"
)

# Execute custom workflow
workflow_engine = WorkflowEngine()
execution_context = ExecutionContext(
    user_request=user_request,
    user_context=user_context
)

workflow_result = await workflow_engine.execute_workflow(workflow, execution_context)

print(f"Workflow completed: {workflow_result.success}")
print(f"Total execution time: {workflow_result.execution_time}s")
print(f"Final recommendations: {len(workflow_result.result['final_recommendations'])}")
```

### Example 5: Iterative Refinement Workflow

This example demonstrates an iterative refinement approach for complex queries.

```python
from services.iterative_refinement_engine import IterativeRefinementEngine

# Create iterative refinement workflow
refinement_engine = IterativeRefinementEngine()

user_request = UserRequest(
    text="I want a romantic dinner place that's not too expensive but has good ambiance",
    user_id="user-123",
    session_id="session-456",
    context=UserContext(
        mbti_type="ISFP",
        preferences={
            "occasion": "romantic_dinner",
            "budget": "moderate",
            "atmosphere": "intimate"
        }
    )
)

# Execute iterative refinement
refinement_result = await refinement_engine.refine_search(user_request)

print("Refinement iterations:")
for i, iteration in enumerate(refinement_result.iterations):
    print(f"Iteration {i+1}:")
    print(f"  Query refinement: {iteration.refined_query}")
    print(f"  Results count: {iteration.results_count}")
    print(f"  Satisfaction score: {iteration.satisfaction_score}")
    print(f"  Refinement strategy: {iteration.refinement_strategy}")

print(f"Final results: {len(refinement_result.final_results)}")
print(f"Total refinement time: {refinement_result.total_time}s")
```

**Expected Output:**
```
Refinement iterations:
Iteration 1:
  Query refinement: romantic dinner + moderate budget + intimate atmosphere
  Results count: 45
  Satisfaction score: 0.6
  Refinement strategy: add_location_filter
Iteration 2:
  Query refinement: + Central/Admiralty districts
  Results count: 18
  Satisfaction score: 0.8
  Refinement strategy: add_cuisine_preference
Iteration 3:
  Query refinement: + Italian/French cuisine
  Results count: 8
  Satisfaction score: 0.95
  Refinement strategy: satisfied
Final results: 8
Total refinement time: 4.2s
```

### Example 6: Parallel Tool Execution

This example shows how to execute multiple tools in parallel for faster results.

```python
from services.parallel_execution_service import ParallelExecutionService

# Create parallel execution service
parallel_service = ParallelExecutionService()

# Define parallel tool executions
parallel_tasks = [
    {
        "task_id": "search_by_location",
        "tool_id": "restaurant_search",
        "tool_name": "search_restaurants_by_district",
        "parameters": {
            "districts": ["Central district", "Admiralty"],
            "meal_types": ["lunch"]
        }
    },
    {
        "task_id": "search_by_cuisine",
        "tool_id": "restaurant_search", 
        "tool_name": "search_restaurants_combined",
        "parameters": {
            "cuisine_types": ["Italian", "Japanese"],
            "meal_types": ["lunch"]
        }
    },
    {
        "task_id": "get_trending",
        "tool_id": "restaurant_reasoning",
        "tool_name": "analyze_restaurant_sentiment",
        "parameters": {
            "analysis_type": "trending_restaurants",
            "time_window": "7d"
        }
    }
]

# Execute tasks in parallel
parallel_results = await parallel_service.execute_parallel(parallel_tasks)

print("Parallel execution results:")
for task_id, result in parallel_results.items():
    print(f"Task: {task_id}")
    print(f"  Success: {result.success}")
    print(f"  Execution time: {result.execution_time}s")
    print(f"  Results count: {len(result.data) if result.data else 0}")

# Aggregate results from parallel executions
aggregated_results = parallel_service.aggregate_results(parallel_results)
print(f"Total unique restaurants found: {len(aggregated_results.unique_restaurants)}")
```

## Integration Examples

### Example 7: AgentCore Monitoring Integration

This example shows how orchestration integrates with AgentCore monitoring.

```python
from services.agentcore_monitoring_service import AgentCoreMonitoringService
from services.tool_orchestration_engine import ToolOrchestrationEngine

# Initialize with monitoring integration
monitoring_service = AgentCoreMonitoringService()
orchestration_engine = ToolOrchestrationEngine(
    monitoring_service=monitoring_service
)

# Process request with full monitoring
user_request = UserRequest(
    text="Find sushi restaurants in Causeway Bay",
    user_id="user-123",
    session_id="session-456"
)

# The orchestration engine automatically logs metrics
result = await orchestration_engine.orchestrate_request(user_request)

# Access monitoring data
monitoring_data = await monitoring_service.get_request_metrics(
    request_id=result.request_id
)

print("Monitoring metrics:")
print(f"Request ID: {monitoring_data.request_id}")
print(f"Total execution time: {monitoring_data.total_time}s")
print(f"Tool invocations: {monitoring_data.tool_invocations}")
print(f"Cache hits: {monitoring_data.cache_hits}")
print(f"Cache misses: {monitoring_data.cache_misses}")

# Custom metrics logging
await monitoring_service.log_custom_metric(
    metric_name="user_satisfaction",
    value=0.95,
    tags={
        "user_id": "user-123",
        "session_id": "session-456",
        "mbti_type": "ENFP"
    }
)
```

### Example 8: Authentication Manager Integration

This example demonstrates integration with the authentication manager.

```python
from services.authentication_manager import AuthenticationManager
from services.tool_orchestration_engine import ToolOrchestrationEngine

# Initialize with authentication
auth_manager = AuthenticationManager()
orchestration_engine = ToolOrchestrationEngine(
    auth_manager=auth_manager
)

# Create authenticated request
user_request = UserRequest(
    text="Find premium restaurants in Central district",
    user_id="user-123",
    session_id="session-456",
    context=UserContext(
        user_role="premium_user",
        subscription_level="gold"
    )
)

# The orchestration engine handles authentication automatically
try:
    result = await orchestration_engine.orchestrate_request(user_request)
    print(f"Authenticated request successful: {result.success}")
    
    # Access user-specific tools based on subscription
    available_tools = await orchestration_engine.get_user_available_tools(
        user_id="user-123"
    )
    print(f"Available tools for user: {[tool.name for tool in available_tools]}")
    
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    # Handle authentication refresh
    await auth_manager.refresh_user_token("user-123")
```

### Example 9: Error Handler Integration

This example shows integration with the error handling system.

```python
from services.error_handler import ErrorHandler
from services.orchestration_error_handler import OrchestrationErrorHandler

# Initialize error handling
base_error_handler = ErrorHandler()
orchestration_error_handler = OrchestrationErrorHandler(base_error_handler)

# Configure orchestration engine with error handling
orchestration_engine = ToolOrchestrationEngine(
    error_handler=orchestration_error_handler
)

user_request = UserRequest(
    text="Find restaurants in NonExistentDistrict",
    user_id="user-123",
    session_id="session-456"
)

try:
    result = await orchestration_engine.orchestrate_request(user_request)
except OrchestrationError as e:
    # Error is automatically handled by the orchestration error handler
    error_response = await orchestration_error_handler.handle_orchestration_error(
        error=e,
        context=OrchestrationContext(
            user_request=user_request,
            attempted_tools=["restaurant_search"],
            execution_stage="tool_selection"
        )
    )
    
    print(f"Error handled: {error_response.error_type}")
    print(f"Fallback suggestion: {error_response.fallback_suggestion}")
    print(f"User message: {error_response.user_message}")
```

## Error Handling Examples

### Example 10: Tool Failure with Fallback

This example demonstrates how the system handles tool failures with automatic fallbacks.

```python
from services.tool_orchestration_engine import ToolOrchestrationEngine
from models.orchestration_types import ToolFailureError

# Simulate tool failure scenario
user_request = UserRequest(
    text="Find restaurants in Central district",
    user_id="user-123",
    session_id="session-456"
)

# The orchestration engine automatically handles tool failures
result = await orchestration_engine.orchestrate_request(user_request)

if result.had_failures:
    print("Tool failures occurred:")
    for failure in result.failures:
        print(f"Failed tool: {failure.tool_id}")
        print(f"Failure reason: {failure.reason}")
        print(f"Fallback used: {failure.fallback_tool_id}")
        print(f"Fallback success: {failure.fallback_success}")

print(f"Final result success: {result.success}")
print(f"Response quality: {result.response_quality}")
```

### Example 11: Timeout Handling with Retry

This example shows how timeouts are handled with automatic retries.

```python
from services.workflow_engine import WorkflowEngine
from models.orchestration_types import RetryPolicy

# Configure retry policy for timeout handling
retry_policy = RetryPolicy(
    max_retries=3,
    backoff_multiplier=2,
    max_backoff=60,
    retry_on_timeout=True,
    retry_on_error=True
)

workflow_engine = WorkflowEngine(retry_policy=retry_policy)

# Create workflow step that might timeout
workflow_step = WorkflowStep(
    id="search_restaurants",
    tool_id="restaurant_search",
    tool_name="search_restaurants_by_district",
    timeout=5,  # Short timeout for demonstration
    retry_policy=retry_policy
)

try:
    step_result = await workflow_engine.execute_step(
        step=workflow_step,
        context=execution_context
    )
    
    print(f"Step completed after {step_result.retry_count} retries")
    print(f"Total execution time: {step_result.total_execution_time}s")
    
except TimeoutError as e:
    print(f"Step failed after all retries: {e}")
    # Fallback to alternative tool or graceful degradation
```

### Example 12: Circuit Breaker Pattern

This example demonstrates the circuit breaker pattern for handling repeated tool failures.

```python
from services.circuit_breaker import CircuitBreaker
from services.tool_registry import ToolRegistry

# Configure circuit breaker for tools
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    half_open_max_calls=3
)

tool_registry = ToolRegistry(circuit_breaker=circuit_breaker)

# Register tool with circuit breaker
await tool_registry.register_tool_with_circuit_breaker(
    tool_id="restaurant_search",
    circuit_breaker_config={
        "failure_threshold": 3,
        "recovery_timeout": 30
    }
)

# Tool invocation with circuit breaker protection
try:
    tool_result = await tool_registry.invoke_tool_with_protection(
        tool_id="restaurant_search",
        tool_name="search_restaurants_by_district",
        parameters={"districts": ["Central district"]}
    )
    
    print(f"Tool invocation successful: {tool_result.success}")
    
except CircuitBreakerOpenError as e:
    print(f"Circuit breaker is open for tool: {e.tool_id}")
    print(f"Estimated recovery time: {e.recovery_time}s")
    
    # Use fallback tool or cached results
    fallback_result = await tool_registry.get_cached_result(
        tool_id="restaurant_search",
        parameters={"districts": ["Central district"]}
    )
    
    if fallback_result:
        print("Using cached result as fallback")
```

## Performance Optimization Examples

### Example 13: Response Caching

This example shows how to implement and use response caching for better performance.

```python
from services.response_cache import ResponseCache
from services.tool_orchestration_engine import ToolOrchestrationEngine

# Initialize with caching
response_cache = ResponseCache(
    cache_size=1000,
    default_ttl=300,  # 5 minutes
    cache_strategy="lru"
)

orchestration_engine = ToolOrchestrationEngine(
    response_cache=response_cache
)

# First request - will be cached
user_request = UserRequest(
    text="Find Italian restaurants in Central district",
    user_id="user-123",
    session_id="session-456"
)

start_time = time.time()
result1 = await orchestration_engine.orchestrate_request(user_request)
first_request_time = time.time() - start_time

print(f"First request time: {first_request_time:.2f}s")
print(f"Cache hit: {result1.cache_hit}")

# Second identical request - should hit cache
start_time = time.time()
result2 = await orchestration_engine.orchestrate_request(user_request)
second_request_time = time.time() - start_time

print(f"Second request time: {second_request_time:.2f}s")
print(f"Cache hit: {result2.cache_hit}")
print(f"Performance improvement: {(first_request_time / second_request_time):.1f}x")

# Cache statistics
cache_stats = response_cache.get_statistics()
print(f"Cache hit rate: {cache_stats.hit_rate:.2%}")
print(f"Cache size: {cache_stats.current_size}/{cache_stats.max_size}")
```

### Example 14: Connection Pool Management

This example demonstrates connection pooling for better resource utilization.

```python
from services.connection_pool_manager import ConnectionPoolManager
from services.tool_orchestration_engine import ToolOrchestrationEngine

# Configure connection pooling
connection_pool = ConnectionPoolManager(
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600
)

orchestration_engine = ToolOrchestrationEngine(
    connection_pool=connection_pool
)

# Multiple concurrent requests will reuse connections
import asyncio

async def process_request(request_id: int):
    user_request = UserRequest(
        text=f"Find restaurants for request {request_id}",
        user_id=f"user-{request_id}",
        session_id=f"session-{request_id}"
    )
    
    result = await orchestration_engine.orchestrate_request(user_request)
    return result

# Process multiple requests concurrently
concurrent_requests = [
    process_request(i) for i in range(10)
]

results = await asyncio.gather(*concurrent_requests)

print(f"Processed {len(results)} concurrent requests")

# Check connection pool statistics
pool_stats = connection_pool.get_statistics()
print(f"Active connections: {pool_stats.active_connections}")
print(f"Pool utilization: {pool_stats.utilization:.2%}")
print(f"Connection reuse rate: {pool_stats.reuse_rate:.2%}")
```

### Example 15: Performance Monitoring and Optimization

This example shows how to monitor and optimize orchestration performance.

```python
from services.performance_monitor import PerformanceMonitor
from services.performance_optimizer import PerformanceOptimizer

# Initialize performance monitoring
performance_monitor = PerformanceMonitor()
performance_optimizer = PerformanceOptimizer(performance_monitor)

orchestration_engine = ToolOrchestrationEngine(
    performance_monitor=performance_monitor,
    performance_optimizer=performance_optimizer
)

# Process requests with performance monitoring
for i in range(100):
    user_request = UserRequest(
        text=f"Find restaurants - request {i}",
        user_id=f"user-{i % 10}",  # 10 different users
        session_id=f"session-{i}"
    )
    
    result = await orchestration_engine.orchestrate_request(user_request)

# Analyze performance metrics
performance_report = performance_monitor.generate_report()

print("Performance Report:")
print(f"Average response time: {performance_report.avg_response_time:.2f}s")
print(f"95th percentile: {performance_report.p95_response_time:.2f}s")
print(f"Success rate: {performance_report.success_rate:.2%}")
print(f"Cache hit rate: {performance_report.cache_hit_rate:.2%}")

# Get optimization recommendations
optimization_recommendations = performance_optimizer.get_recommendations()

print("\nOptimization Recommendations:")
for recommendation in optimization_recommendations:
    print(f"- {recommendation.category}: {recommendation.description}")
    print(f"  Expected improvement: {recommendation.expected_improvement}")
    print(f"  Implementation effort: {recommendation.effort_level}")
```

## Custom Tool Integration

### Example 16: Registering a Custom Tool

This example shows how to register and integrate a custom tool with the orchestration system.

```python
from services.tool_registry import ToolRegistry
from models.orchestration_types import ToolMetadata, ToolCapability

# Define custom tool metadata
custom_tool_metadata = ToolMetadata(
    tool_id="custom_cuisine_analyzer",
    name="Cuisine Preference Analyzer",
    description="Analyzes user preferences to suggest cuisine types",
    capabilities=[
        ToolCapability(
            name="analyze_cuisine_preferences",
            description="Analyze user MBTI and history for cuisine preferences",
            required_parameters=["mbti_type", "user_history"],
            optional_parameters=["dietary_restrictions", "cultural_background"]
        )
    ],
    mcp_endpoint="https://custom-tool.example.com/mcp",
    performance_characteristics={
        "average_response_time": 0.8,
        "success_rate": 0.96,
        "throughput_limit": 100
    },
    health_check_endpoint="/health"
)

# Register the custom tool
tool_registry = ToolRegistry()
await tool_registry.register_tool(custom_tool_metadata)

print(f"Custom tool registered: {custom_tool_metadata.tool_id}")

# Verify tool registration
registered_tools = await tool_registry.list_tools()
custom_tool = next(
    (tool for tool in registered_tools if tool.tool_id == "custom_cuisine_analyzer"),
    None
)

if custom_tool:
    print(f"Tool status: {custom_tool.status}")
    print(f"Capabilities: {[cap.name for cap in custom_tool.capabilities]}")
```

### Example 17: Custom Workflow Template

This example demonstrates creating a custom workflow template for specific use cases.

```python
from services.workflow_templates import WorkflowTemplateManager
from models.orchestration_types import WorkflowTemplate, WorkflowStep

# Define custom workflow template
custom_workflow_template = WorkflowTemplate(
    template_id="mbti_personalized_dining",
    name="MBTI Personalized Dining Recommendations",
    description="Comprehensive dining recommendations based on MBTI personality",
    steps=[
        WorkflowStep(
            id="analyze_personality",
            tool_id="custom_cuisine_analyzer",
            tool_name="analyze_cuisine_preferences",
            input_mapping={
                "mbti_type": "user_context.mbti_type",
                "user_history": "user_context.conversation_history"
            },
            output_mapping={
                "cuisine_preferences": "personality_cuisine_prefs"
            }
        ),
        WorkflowStep(
            id="search_by_preferences",
            tool_id="restaurant_search",
            tool_name="search_restaurants_combined",
            input_mapping={
                "cuisine_types": "personality_cuisine_prefs.recommended_cuisines",
                "districts": "user_request.districts",
                "meal_types": "user_request.meal_types"
            },
            output_mapping={
                "restaurants": "preference_matched_restaurants"
            }
        ),
        WorkflowStep(
            id="mbti_recommendation",
            tool_id="restaurant_reasoning",
            tool_name="recommend_restaurants",
            input_mapping={
                "restaurants": "preference_matched_restaurants",
                "mbti_type": "user_context.mbti_type",
                "ranking_method": "mbti_optimized"
            },
            output_mapping={
                "recommendations": "final_mbti_recommendations"
            }
        )
    ],
    execution_strategy="sequential",
    estimated_duration=3.5
)

# Register the workflow template
workflow_manager = WorkflowTemplateManager()
await workflow_manager.register_template(custom_workflow_template)

# Use the custom workflow template
user_request = UserRequest(
    text="I want dining recommendations that match my personality",
    user_id="user-123",
    session_id="session-456",
    context=UserContext(
        mbti_type="ENFP",
        preferences={"adventure_level": "high"}
    )
)

# The orchestration engine will automatically select the custom workflow
result = await orchestration_engine.orchestrate_request(user_request)

print(f"Used workflow template: {result.workflow_template_id}")
print(f"Personality analysis: {result.trace.steps[0].output}")
print(f"Final recommendations: {len(result.result['final_mbti_recommendations'])}")
```

### Example 18: Tool Performance Monitoring

This example shows how to monitor custom tool performance and health.

```python
from services.tool_health_monitor import ToolHealthMonitor
from services.performance_monitor import PerformanceMonitor

# Initialize monitoring for custom tool
tool_health_monitor = ToolHealthMonitor()
performance_monitor = PerformanceMonitor()

# Register health monitoring for custom tool
await tool_health_monitor.register_tool_monitoring(
    tool_id="custom_cuisine_analyzer",
    health_check_config={
        "endpoint": "/health",
        "interval": 30,
        "timeout": 5,
        "expected_response_time": 1.0
    }
)

# Monitor tool performance over time
for i in range(50):
    # Simulate tool usage
    start_time = time.time()
    
    try:
        # Tool invocation would happen here
        execution_time = random.uniform(0.5, 2.0)  # Simulated execution time
        success = random.random() > 0.05  # 95% success rate
        
        # Record performance metrics
        await performance_monitor.record_tool_invocation(
            tool_id="custom_cuisine_analyzer",
            execution_time=execution_time,
            success=success,
            response_size=1024
        )
        
    except Exception as e:
        await performance_monitor.record_tool_error(
            tool_id="custom_cuisine_analyzer",
            error_type=type(e).__name__,
            error_message=str(e)
        )

# Generate performance report for custom tool
tool_performance = await performance_monitor.get_tool_performance(
    tool_id="custom_cuisine_analyzer",
    time_window="1h"
)

print("Custom Tool Performance Report:")
print(f"Total invocations: {tool_performance.total_invocations}")
print(f"Success rate: {tool_performance.success_rate:.2%}")
print(f"Average response time: {tool_performance.avg_response_time:.2f}s")
print(f"95th percentile: {tool_performance.p95_response_time:.2f}s")

# Check tool health status
health_status = await tool_health_monitor.get_tool_health(
    tool_id="custom_cuisine_analyzer"
)

print(f"Tool health status: {health_status.status}")
print(f"Last health check: {health_status.last_check}")
print(f"Health score: {health_status.health_score:.2f}")
```

---

**Usage Examples Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Maintained By**: MBTI Travel Planner Agent Team