"""
MBTI Travel Planner Agent with Amazon Nova Pro Model and AgentCore Integration

This agent uses Amazon Nova Pro foundation model (amazon.nova-pro-v1:0) with enhanced
reasoning capabilities, combined with restaurant search and reasoning functionality
through direct AgentCore Runtime API calls to deployed AgentCore agents.

Model Configuration:
- Model: amazon.nova-pro-v1:0
- Temperature: 0.1 (for consistent, focused responses)
- Max Tokens: 2048 (sufficient for detailed travel planning)
- Timeout: 60 seconds (Nova Pro supports up to 60 minutes)

Architecture:
- AgentCore Runtime Client: Direct API calls to AgentCore agents
- Environment-based Configuration: Automatic agent ARN detection
- Comprehensive Error Handling: User-friendly error messages and fallbacks
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent

# Import AgentCore services and tools
from services.agentcore_runtime_client import (
    AgentCoreRuntimeClient, 
    AgentCoreError, 
    ConnectionConfig
)
from services.agentcore_error_handler import RetryConfig
from services.authentication_manager import AuthenticationManager, AuthenticationError
from services.restaurant_search_tool import RestaurantSearchTool
from services.restaurant_reasoning_tool import RestaurantReasoningTool
from services.agentcore_error_handler import AgentCoreErrorHandler
from services.agentcore_monitoring_service import AgentCoreMonitoringService
from services.agentcore_health_check_service import AgentCoreHealthCheckService
from services.enhanced_jwt_token_manager import (
    enhanced_jwt_manager, 
    inject_jwt_token_globally, 
    register_component_for_jwt_injection,
    get_current_jwt_token,
    get_jwt_injection_status
)
from config.agentcore_environment_config import get_agentcore_config

# Import orchestration engine and related components
from services.tool_orchestration_engine import ToolOrchestrationEngine, OrchestrationConfig
from services.orchestration_types import UserContext, RequestType
from services.orchestration_middleware import OrchestrationMiddleware, MiddlewareConfig
from services.backward_compatibility import BackwardCompatibilityManager, CompatibilityConfig, CompatibilityMode

# Initialize comprehensive logging and monitoring
current_environment = os.getenv('ENVIRONMENT', 'production')
log_level = os.getenv('LOG_LEVEL', 'INFO')

# Initialize AgentCore monitoring service
monitoring_service = AgentCoreMonitoringService(
    environment=current_environment,
    enable_detailed_logging=os.getenv('ENABLE_DETAILED_LOGGING', 'true').lower() == 'true',
    enable_performance_tracking=os.getenv('ENABLE_PERFORMANCE_TRACKING', 'true').lower() == 'true',
    enable_health_checks=os.getenv('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true'
)

# Get AgentCore configuration first
config = get_agentcore_config(current_environment)

# Initialize AgentCore health check service
health_check_service = AgentCoreHealthCheckService(
    config=config,
    monitoring_service=monitoring_service,
    enable_background_checks=os.getenv('ENABLE_BACKGROUND_HEALTH_CHECKS', 'true').lower() == 'true'
)

# Configure basic logging for compatibility
logging.basicConfig(level=getattr(logging, log_level.upper()))
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# Initialize AgentCore components
agentcore_client = None
auth_manager = None
error_handler = AgentCoreErrorHandler("mbti_travel_planner_agent")

# Initialize orchestration engine and middleware
orchestration_engine = None
orchestration_middleware = None
compatibility_manager = None
ORCHESTRATION_AVAILABLE = False

# AgentCore service availability
AGENTCORE_AVAILABLE = False

# Start background health checks
health_check_service.start_background_checks()

# Log initialization
logger.info(f"MBTI Travel Planner Agent initializing in {current_environment} environment")
logger.info(f"Logging level: {log_level}, Performance monitoring enabled: {monitoring_service.enable_performance_tracking}")
logger.info(f"Health checks enabled: {health_check_service.enable_background_checks}")

def initialize_orchestration_engine():
    """Initialize the tool orchestration engine for intelligent tool selection."""
    global orchestration_engine, orchestration_middleware, compatibility_manager, ORCHESTRATION_AVAILABLE
    
    try:
        # Load orchestration configuration
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'orchestration_config.yaml')
        
        if os.path.exists(config_path):
            orchestration_config = OrchestrationConfig.from_yaml(config_path)
            logger.info(f"Loaded orchestration configuration from {config_path}")
        else:
            # Use default configuration
            orchestration_config = OrchestrationConfig()
            logger.info("Using default orchestration configuration")
        
        # Initialize orchestration engine
        orchestration_engine = ToolOrchestrationEngine(
            config=orchestration_config,
            environment=current_environment,
            config_path=config_path if os.path.exists(config_path) else None
        )
        
        # Initialize orchestration middleware
        middleware_config = MiddlewareConfig(
            enable_orchestration=True,
            enable_fallback_to_direct=True,
            enable_request_logging=orchestration_config.enable_metrics_collection,
            enable_performance_tracking=orchestration_config.enable_metrics_collection,
            orchestration_timeout_seconds=orchestration_config.step_timeout_seconds,
            fallback_timeout_seconds=30
        )
        
        orchestration_middleware = OrchestrationMiddleware(
            orchestration_engine=orchestration_engine,
            monitoring_service=monitoring_service,
            config=middleware_config
        )
        
        # Initialize backward compatibility manager
        compatibility_config = CompatibilityConfig(
            mode=CompatibilityMode.HYBRID,  # Start with hybrid mode for gradual rollout
            enable_feature_flags=True,
            enable_migration_tracking=True,
            enable_compatibility_metrics=True,
            orchestration_adoption_percentage=float(os.getenv('ORCHESTRATION_ADOPTION_PERCENTAGE', '50.0'))
        )
        
        compatibility_manager = BackwardCompatibilityManager(
            config=compatibility_config,
            monitoring_service=monitoring_service,
            environment=current_environment
        )
        
        logger.info("Tool orchestration engine, middleware, and compatibility manager initialized successfully")
        logger.info(f"Orchestration features - Intent analysis: {orchestration_config.enable_context_analysis}")
        logger.info(f"Performance monitoring: {orchestration_config.enable_metrics_collection}")
        logger.info(f"Circuit breaker: {orchestration_config.enable_circuit_breaker}")
        logger.info(f"Middleware - Fallback enabled: {middleware_config.enable_fallback_to_direct}")
        logger.info(f"Compatibility - Mode: {compatibility_config.mode.value}, Adoption: {compatibility_config.orchestration_adoption_percentage}%")
        
        # Log successful initialization
        try:
            monitoring_service.log_performance_metric(
                operation="initialize_orchestration_engine",
                duration=0.1,
                success=True,
                additional_data={
                    "environment": current_environment,
                    "config_path": config_path,
                    "intent_analysis_enabled": orchestration_config.enable_context_analysis,
                    "metrics_collection_enabled": orchestration_config.enable_metrics_collection,
                    "circuit_breaker_enabled": orchestration_config.enable_circuit_breaker,
                    "middleware_enabled": True,
                    "fallback_enabled": middleware_config.enable_fallback_to_direct
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log orchestration initialization metrics: {metric_error}")
        
        ORCHESTRATION_AVAILABLE = True
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize orchestration engine: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Log initialization failure
        try:
            monitoring_service.log_error(
                error=e,
                operation="initialize_orchestration_engine",
                context={
                    "environment": current_environment,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log orchestration initialization error: {metric_error}")
        
        ORCHESTRATION_AVAILABLE = False
        return False

def update_agentcore_jwt_token(jwt_token: str):
    """Update JWT token in the global AgentCore client and all tool instances using enhanced manager."""
    global agentcore_client, agent, auth_manager, orchestration_engine, monitoring_service, health_check_service
    
    # Use enhanced JWT token manager for comprehensive injection
    success = inject_jwt_token_globally(jwt_token)
    
    if success:
        logger.info("✅ JWT token updated globally using enhanced manager")
        
        # Log injection status for debugging
        status = get_jwt_injection_status()
        logger.debug(f"JWT injection status: {status}")
        
    else:
        logger.error("❌ Failed to update JWT token globally")
        
        # Fallback to legacy method
        logger.info("🔄 Attempting fallback JWT token injection...")
        
        # Update global AgentCore client
        if agentcore_client:
            agentcore_client.jwt_token = jwt_token
            logger.info("✅ JWT token updated in global AgentCore client (fallback)")
        
        # Update JWT token in agent tools if agent is available
        if agent and hasattr(agent, 'tools'):
            tools_updated = 0
            for tool in agent.tools:
                # Check if tool has a runtime_client attribute (AgentCore tools)
                if hasattr(tool, 'runtime_client') and hasattr(tool.runtime_client, 'jwt_token'):
                    tool.runtime_client.jwt_token = jwt_token
                    tools_updated += 1
                # Also check for nested tool objects (in case of wrapped tools)
                elif hasattr(tool, '_tool_obj') and hasattr(tool._tool_obj, 'runtime_client'):
                    if hasattr(tool._tool_obj.runtime_client, 'jwt_token'):
                        tool._tool_obj.runtime_client.jwt_token = jwt_token
                        tools_updated += 1
                # Check for original_tool attribute (compatibility wrapper pattern)
                elif hasattr(tool, 'original_tool') and hasattr(tool.original_tool, 'runtime_client'):
                    if hasattr(tool.original_tool.runtime_client, 'jwt_token'):
                        tool.original_tool.runtime_client.jwt_token = jwt_token
                        tools_updated += 1
            
            if tools_updated > 0:
                logger.info(f"✅ JWT token updated in {tools_updated} AgentCore tool instances (fallback)")
        
        # Update authentication manager
        if auth_manager and hasattr(auth_manager, 'set_jwt_token'):
            try:
                auth_manager.set_jwt_token(jwt_token)
                logger.info("✅ JWT token updated in authentication manager (fallback)")
            except Exception as e:
                logger.warning(f"Failed to update JWT token in auth manager: {e}")


def update_tools_jwt_token(jwt_token: str, tools_list: List = None):
    """
    Update JWT token in a specific list of tools.
    
    Args:
        jwt_token: The JWT token to set
        tools_list: List of tools to update (optional, uses global agent tools if not provided)
    """
    if tools_list is None:
        # Use global agent tools
        global agent
        if agent and hasattr(agent, 'tools'):
            tools_list = agent.tools
        else:
            logger.warning("⚠️ No tools list provided and global agent not available")
            return
    
    tools_updated = 0
    for tool in tools_list:
        # Check if tool has a runtime_client attribute (AgentCore tools)
        if hasattr(tool, 'runtime_client') and hasattr(tool.runtime_client, 'jwt_token'):
            tool.runtime_client.jwt_token = jwt_token
            tools_updated += 1
        # Also check for nested tool objects (in case of wrapped tools)
        elif hasattr(tool, '_tool_obj') and hasattr(tool._tool_obj, 'runtime_client'):
            if hasattr(tool._tool_obj.runtime_client, 'jwt_token'):
                tool._tool_obj.runtime_client.jwt_token = jwt_token
                tools_updated += 1
        # Check for original_tool attribute (compatibility wrapper pattern)
        elif hasattr(tool, 'original_tool') and hasattr(tool.original_tool, 'runtime_client'):
            if hasattr(tool.original_tool.runtime_client, 'jwt_token'):
                tool.original_tool.runtime_client.jwt_token = jwt_token
                tools_updated += 1
    
    logger.info(f"✅ JWT token updated in {tools_updated} tool instances")
    return tools_updated

def initialize_agentcore_client():
    """Initialize AgentCore Runtime client for agent communication."""
    global agentcore_client, auth_manager, AGENTCORE_AVAILABLE
    
    try:
        # Get AgentCore configuration for current environment
        agentcore_config = get_agentcore_config(current_environment)
        
        # Initialize authentication manager with proper error handling
        jwt_token = None
        try:
            auth_manager = AuthenticationManager(agentcore_config.cognito)
            logger.info("Authentication manager initialized successfully")
            
            # JWT token will be provided per request, not during initialization
            # This allows the service to handle multiple authenticated requests
            jwt_token = None
            logger.info("AgentCore client will receive JWT tokens per request")
                
        except Exception as auth_error:
            logger.warning(f"Authentication manager initialization failed: {auth_error}")
            # Continue without authentication manager for basic functionality
            auth_manager = None
        
        # Initialize AgentCore Runtime client with JWT token if available
        agentcore_client = AgentCoreRuntimeClient(
            region=agentcore_config.agentcore.region,
            jwt_token=jwt_token,  # Pass JWT token if available
            authentication_manager=auth_manager,  # Pass auth manager for token refresh
            connection_config=ConnectionConfig(
                timeout_seconds=agentcore_config.agentcore.timeout_seconds
            ),
            retry_config=RetryConfig(
                max_retries=agentcore_config.agentcore.max_retries
            )
        )
        
        logger.info(f"AgentCore Runtime client initialized for {current_environment} environment")
        logger.info(f"Region: {agentcore_config.agentcore.region}")
        logger.info(f"Timeout: {agentcore_config.agentcore.timeout_seconds}s")
        logger.info(f"Max retries: {agentcore_config.agentcore.max_retries}")
        logger.info(f"JWT token available: {jwt_token is not None}")
        logger.info(f"Restaurant Search Agent ARN: {agentcore_config.agentcore.restaurant_search_agent_arn}")
        logger.info(f"Restaurant Reasoning Agent ARN: {agentcore_config.agentcore.restaurant_reasoning_agent_arn}")
        
        # Register AgentCore client and auth manager with enhanced JWT token manager
        try:
            register_component_for_jwt_injection("agentcore_client", agentcore_client)
            if auth_manager:
                register_component_for_jwt_injection("auth_manager", auth_manager)
            logger.info("✅ AgentCore components registered with enhanced JWT token manager")
        except Exception as registration_error:
            logger.warning(f"Failed to register AgentCore components with JWT manager: {registration_error}")
        
        # Log successful initialization with proper error handling
        try:
            monitoring_service.log_performance_metric(
                operation="initialize_agentcore_client",
                duration=0.1,  # Initialization is typically fast
                success=True,
                additional_data={
                    "environment": current_environment,
                    "region": agentcore_config.agentcore.region,
                    "timeout": agentcore_config.agentcore.timeout_seconds,
                    "max_retries": agentcore_config.agentcore.max_retries,
                    "auth_manager_available": auth_manager is not None
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log performance metric: {metric_error}")
        
        AGENTCORE_AVAILABLE = True
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize AgentCore Runtime client: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Environment: {current_environment}")
        
        # Log initialization failure with proper error handling
        try:
            monitoring_service.log_error(
                error=e,
                operation="initialize_agentcore_client",
                context={
                    "environment": current_environment,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            
            monitoring_service.log_performance_metric(
                operation="initialize_agentcore_client",
                duration=0.1,
                success=False,
                error_type=type(e).__name__,
                additional_data={
                    "environment": current_environment,
                    "error_message": str(e)
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log error metrics: {metric_error}")
        
        AGENTCORE_AVAILABLE = False
        return False

async def test_agentcore_connectivity():
    """Test connectivity to the AgentCore agents using health checks."""
    if not agentcore_client:
        logger.warning("AgentCore client not available for connectivity test")
        return False
    
    try:
        # Perform health check on AgentCore agents
        health_result = await health_check_service.check_agentcore_agents_health()
        
        if health_result.overall_status == "healthy":
            logger.info("AgentCore connectivity test passed")
            monitoring_service.log_performance_metric(
                operation="agentcore_connectivity_test",
                duration=health_result.total_response_time_ms / 1000.0,
                success=True,
                additional_data={
                    "agents_checked": len(health_result.agent_results),
                    "healthy_agents": len([r for r in health_result.agent_results if r.status == "healthy"]),
                    "total_response_time_ms": health_result.total_response_time_ms
                }
            )
            return True
        else:
            logger.warning(f"AgentCore connectivity test failed: {health_result.error_summary}")
            monitoring_service.log_performance_metric(
                operation="agentcore_connectivity_test",
                duration=health_result.total_response_time_ms / 1000.0,
                success=False,
                error_type="unhealthy_response",
                additional_data={
                    "agents_checked": len(health_result.agent_results),
                    "healthy_agents": len([r for r in health_result.agent_results if r.status == "healthy"]),
                    "error_summary": health_result.error_summary
                }
            )
            return False
        
    except Exception as e:
        logger.warning(f"AgentCore connectivity test failed: {e}")
        monitoring_service.log_error(
            error=e,
            operation="agentcore_connectivity_test",
            context={"environment": current_environment}
        )
        return False

# Initialize AgentCore client on startup
initialize_agentcore_client()

# Initialize orchestration engine
initialize_orchestration_engine()

# Test AgentCore connectivity asynchronously (will be done during first request)
# We can't run async code at module level, so we'll test during first invocation


def create_agentcore_tools() -> List:
    """Create restaurant search and recommendation tools using AgentCore Runtime client."""
    if not AGENTCORE_AVAILABLE:
        logger.warning("AgentCore not available, returning empty tools list")
        return []
    
    tools = []
    
    try:
        # Get AgentCore configuration
        agentcore_config = get_agentcore_config(current_environment)
        
        # Import the create functions
        from services.restaurant_search_tool import create_restaurant_search_tools
        from services.restaurant_reasoning_tool import create_restaurant_reasoning_tools
        
        # Create restaurant search tools
        search_tools = create_restaurant_search_tools(
            runtime_client=agentcore_client,
            search_agent_arn=agentcore_config.agentcore.restaurant_search_agent_arn,
            auth_manager=auth_manager
        )
        
        # Create restaurant reasoning tools
        reasoning_tools = create_restaurant_reasoning_tools(
            runtime_client=agentcore_client,
            reasoning_agent_arn=agentcore_config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        # Store original tools for compatibility processing
        original_search_tools = search_tools
        original_reasoning_tools = reasoning_tools
        
        # Register tools with orchestration engine if available
        if ORCHESTRATION_AVAILABLE and orchestration_engine:
            register_tools_with_orchestration(search_tools + reasoning_tools)
        
        # Create compatible tools that support both legacy and orchestration approaches
        if ORCHESTRATION_AVAILABLE and compatibility_manager:
            tools = create_compatible_tools(search_tools + reasoning_tools)
        else:
            # Use original tools if orchestration not available
            tools = search_tools + reasoning_tools
        
        logger.info(f"Created {len(tools)} AgentCore tools")
        
        # Log successful tool creation
        monitoring_service.log_performance_metric(
            operation="create_agentcore_tools",
            duration=0.1,  # Tool creation is typically fast
            success=True,
            additional_data={
                "tools_count": len(tools),
                "environment": current_environment,
                "search_agent_arn": agentcore_config.agentcore.restaurant_search_agent_arn,
                "reasoning_agent_arn": agentcore_config.agentcore.restaurant_reasoning_agent_arn,
                "orchestration_available": ORCHESTRATION_AVAILABLE
            }
        )
        
        return tools
        
    except Exception as e:
        logger.error(f"Failed to create AgentCore tools: {e}")
        
        # Log tool creation failure
        monitoring_service.log_error(
            error=e,
            operation="create_agentcore_tools",
            context={
                "environment": current_environment,
                "error_type": type(e).__name__
            }
        )
        
        monitoring_service.log_performance_metric(
            operation="create_agentcore_tools",
            duration=0.1,
            success=False,
            error_type=type(e).__name__,
            additional_data={"environment": current_environment}
        )
        
        return []

def register_tools_with_orchestration(tools: List):
    """Register tools with the orchestration engine for intelligent selection."""
    if not ORCHESTRATION_AVAILABLE or not orchestration_engine:
        logger.warning("Orchestration engine not available for tool registration")
        return
    
    try:
        from services.tool_registry import ToolMetadata, ToolCapability
        
        for tool in tools:
            # Extract tool metadata for registration
            tool_name = getattr(tool, 'name', tool.__class__.__name__)
            tool_id = f"{tool_name.lower().replace(' ', '_')}_{id(tool)}"
            
            # Determine capabilities based on tool type and methods
            capabilities = []
            
            if hasattr(tool, 'search_restaurants_by_district'):
                capabilities.append(ToolCapability(
                    name="search_by_district",
                    description="Search restaurants by district/location",
                    required_parameters=["districts"],
                    optional_parameters=["meal_types"],
                    output_format="json",
                    use_cases=["location_based_search", "district_filtering"]
                ))
            
            if hasattr(tool, 'search_restaurants_by_meal_type'):
                capabilities.append(ToolCapability(
                    name="search_by_meal_type",
                    description="Search restaurants by meal type",
                    required_parameters=["meal_types"],
                    optional_parameters=["districts"],
                    output_format="json",
                    use_cases=["meal_based_search", "time_filtering"]
                ))
            
            if hasattr(tool, 'search_restaurants_combined'):
                capabilities.append(ToolCapability(
                    name="combined_search",
                    description="Combined restaurant search with multiple criteria",
                    required_parameters=[],
                    optional_parameters=["districts", "meal_types"],
                    output_format="json",
                    use_cases=["flexible_search", "multi_criteria_filtering"]
                ))
            
            if hasattr(tool, 'recommend_restaurants'):
                capabilities.append(ToolCapability(
                    name="recommend_restaurants",
                    description="Recommend restaurants from provided data",
                    required_parameters=["restaurants"],
                    optional_parameters=["ranking_method"],
                    output_format="json",
                    use_cases=["recommendation", "ranking", "sentiment_analysis"]
                ))
            
            if hasattr(tool, 'analyze_restaurant_sentiment'):
                capabilities.append(ToolCapability(
                    name="analyze_sentiment",
                    description="Analyze restaurant sentiment data",
                    required_parameters=["restaurants"],
                    optional_parameters=[],
                    output_format="json",
                    use_cases=["sentiment_analysis", "data_analysis"]
                ))
            
            # Create tool metadata
            tool_metadata = ToolMetadata(
                id=tool_id,
                name=tool_name,
                description=f"AgentCore tool for {tool_name}",
                capabilities=capabilities,
                input_schema={},  # Will be populated from tool inspection
                output_schema={},  # Will be populated from tool inspection
                performance_characteristics=None,  # Will be learned over time
                health_check_endpoint=None  # AgentCore tools use runtime health checks
            )
            
            # Register with orchestration engine
            orchestration_engine.tool_registry.register_tool(tool_metadata, tool)
            
            logger.debug(f"Registered tool with orchestration engine: {tool_name}")
        
        logger.info(f"Successfully registered {len(tools)} tools with orchestration engine")
        
        # Log successful registration
        monitoring_service.log_performance_metric(
            operation="register_tools_with_orchestration",
            duration=0.1,
            success=True,
            additional_data={
                "tools_registered": len(tools),
                "environment": current_environment
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to register tools with orchestration engine: {e}")
        
        # Log registration failure
        monitoring_service.log_error(
            error=e,
            operation="register_tools_with_orchestration",
            context={
                "environment": current_environment,
                "tools_count": len(tools),
                "error_type": type(e).__name__
            }
        )

def create_compatible_tools(original_tools: List) -> List:
    """Create compatible tools that support both legacy and orchestration approaches."""
    if not ORCHESTRATION_AVAILABLE or not compatibility_manager or not orchestration_middleware:
        logger.warning("Orchestration or compatibility manager not available, returning original tools")
        return original_tools
    
    compatible_tools = []
    
    try:
        for tool in original_tools:
            # Determine tool type based on tool methods
            tool_type = "unknown"
            
            if hasattr(tool, 'search_restaurants_by_district') or hasattr(tool, 'search_restaurants_combined'):
                tool_type = "search"
            elif hasattr(tool, 'recommend_restaurants') or hasattr(tool, 'analyze_restaurant_sentiment'):
                tool_type = "reasoning"
            
            # Create compatible tool wrapper
            compatible_tool = compatibility_manager.create_compatible_tool(
                legacy_tool=tool,
                orchestration_middleware=orchestration_middleware,
                tool_type=tool_type
            )
            
            compatible_tools.append(compatible_tool)
            
            logger.debug(f"Created compatible tool for {tool_type}: {getattr(tool, 'name', tool.__class__.__name__)}")
        
        logger.info(f"Created {len(compatible_tools)} compatible tools with backward compatibility")
        
        # Log compatible tool creation
        monitoring_service.log_performance_metric(
            operation="create_compatible_tools",
            duration=0.1,
            success=True,
            additional_data={
                "tools_count": len(compatible_tools),
                "environment": current_environment,
                "compatibility_mode": compatibility_manager.config.mode.value if compatibility_manager else "unknown",
                "orchestration_available": ORCHESTRATION_AVAILABLE
            }
        )
        
        return compatible_tools
        
    except Exception as e:
        logger.error(f"Failed to create compatible tools: {e}")
        
        # Log compatible tool creation failure
        monitoring_service.log_error(
            error=e,
            operation="create_compatible_tools",
            context={
                "environment": current_environment,
                "tools_count": len(original_tools),
                "error_type": type(e).__name__
            }
        )
        
        # Return original tools as fallback
        return original_tools

async def process_with_orchestration(user_message: str, payload: Dict[str, Any]) -> Any:
    """Process user request using orchestration engine with intelligent tool selection."""
    try:
        # Extract user context from payload if available
        user_context = None
        session_id = payload.get("sessionId")
        user_id = payload.get("userId") 
        
        if session_id or user_id:
            user_context = UserContext(
                user_id=user_id,
                session_id=session_id,
                conversation_history=[],  # Could be populated from session storage
                mbti_type=None,  # Could be extracted from user profile
                location_context=None  # Could be extracted from request
            )
        
        # Route request through orchestration middleware
        orchestration_result = await orchestration_middleware.route_request(
            request_text=user_message,
            user_context=user_context,
            correlation_id=None,  # Will be auto-generated
            direct_tool_fallback=lambda text, context: agent(text)
        )
        
        # Convert orchestration result to agent response format
        if orchestration_result.get('success', False):
            # Format orchestrated response
            results = orchestration_result.get('results', [])
            
            if results:
                # Combine results from multiple tools if needed
                combined_content = []
                
                for result in results:
                    if isinstance(result, dict) and 'result' in result:
                        tool_result = result['result']
                        if isinstance(tool_result, str):
                            combined_content.append(tool_result)
                        elif isinstance(tool_result, dict):
                            # Format structured data
                            combined_content.append(f"Tool result: {json.dumps(tool_result, indent=2)}")
                
                if combined_content:
                    response_text = "\n\n".join(combined_content)
                else:
                    response_text = "I've processed your request using intelligent tool orchestration, but no specific results were returned."
                
                # Add orchestration metadata to response
                metadata = orchestration_result.get('metadata', {})
                if metadata.get('intelligent_selection'):
                    response_text += f"\n\n*This response was generated using intelligent tool orchestration with {len(orchestration_result.get('tools_used', []))} optimally selected tools.*"
            else:
                response_text = "I've processed your request, but no results were available from the orchestrated tools."
            
            # Create agent-compatible response
            class OrchestrationResponse:
                def __init__(self, content):
                    self.message = {
                        "role": "assistant",
                        "content": [{"text": content}]
                    }
            
            return OrchestrationResponse(response_text)
        
        else:
            # Orchestration failed, the middleware should have already tried fallback
            error_message = orchestration_result.get('error', 'Unknown orchestration error')
            logger.warning(f"Orchestration processing failed: {error_message}")
            
            # Fallback to direct agent processing
            return agent(user_message)
    
    except Exception as e:
        logger.error(f"Orchestration processing error: {e}")
        
        # Log orchestration processing error
        try:
            monitoring_service.log_error(
                error=e,
                operation="process_with_orchestration",
                context={
                    "environment": current_environment,
                    "message_length": len(user_message),
                    "error_type": type(e).__name__
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log orchestration processing error: {metric_error}")
        
        # Fallback to direct agent processing
        return agent(user_message)


# Create agent with all AgentCore tools
def create_agent_with_tools():
    """Create the agent with all available AgentCore tools."""
    tools = []
    
    if AGENTCORE_AVAILABLE:
        # Add AgentCore tools with error handling
        try:
            agentcore_tools = create_agentcore_tools()
            tools.extend(agentcore_tools)
            logger.info(f"Created agent with {len(tools)} AgentCore tools")
        except Exception as tool_error:
            logger.warning(f"Failed to create AgentCore tools: {tool_error}")
            logger.info("Continuing with agent creation without AgentCore tools")
    else:
        logger.info("Created agent without AgentCore tools (service not available)")
    
    try:
        # Get model configuration from environment or use defaults
        model_name = os.getenv('AGENT_MODEL', 'amazon.nova-pro-v1:0')
        temperature = float(os.getenv('AGENT_TEMPERATURE', '0.1'))
        max_tokens = int(os.getenv('AGENT_MAX_TOKENS', '4096'))  # Increased for complex workflows
        timeout = int(os.getenv('AGENT_TIMEOUT', '60'))
        
        logger.info(f"Initializing agent with model: {model_name}")
        logger.info(f"Model parameters - Temperature: {temperature}, Max Tokens: {max_tokens}, Timeout: {timeout}s")
        
        # Create agent with Nova Pro model and tools
        # Remove problematic parameters that cause SDK errors
        agent = Agent(
            model=model_name,
            tools=tools
            # Note: Strands Agent doesn't support temperature/max_tokens in constructor
            # These should be configured at the model level or through environment variables
        )
        
        logger.info(f"Agent created successfully with Nova Pro model: {model_name}")
        logger.info(f"Agent has {len(tools)} tools available")
        
        # Register components with enhanced JWT token manager
        try:
            register_component_for_jwt_injection("agent", agent)
            register_component_for_jwt_injection("agentcore_client", agentcore_client)
            if auth_manager:
                register_component_for_jwt_injection("auth_manager", auth_manager)
            if orchestration_engine:
                register_component_for_jwt_injection("orchestration_engine", orchestration_engine)
            if monitoring_service:
                register_component_for_jwt_injection("monitoring_service", monitoring_service)
            if health_check_service:
                register_component_for_jwt_injection("health_check_service", health_check_service)
            
            # Register individual tools
            for i, tool in enumerate(tools):
                register_component_for_jwt_injection(f"tool_{i}_{type(tool).__name__}", tool)
            
            logger.info("✅ All components registered with enhanced JWT token manager")
            
        except Exception as registration_error:
            logger.warning(f"Failed to register components with JWT manager: {registration_error}")
        
        # Log successful agent creation with proper error handling
        try:
            monitoring_service.log_performance_metric(
                operation="create_agent_with_tools",
                duration=0.5,  # Agent creation typically takes some time
                success=True,
                additional_data={
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": timeout,
                    "tools_count": len(tools),
                    "agentcore_available": AGENTCORE_AVAILABLE
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log performance metric: {metric_error}")
        
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent with Nova Pro model: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("Nova Pro model may not be available in this region or configuration is invalid")
        
        # Log detailed error information with proper error handling
        try:
            monitoring_service.log_error(
                error=e,
                operation="create_agent_with_tools",
                context={
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": timeout,
                    "tools_count": len(tools),
                    "environment": current_environment,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                include_stack_trace=True
            )
            
            monitoring_service.log_performance_metric(
                operation="create_agent_with_tools",
                duration=0.5,
                success=False,
                error_type=type(e).__name__,
                additional_data={
                    "model_name": model_name,
                    "environment": current_environment,
                    "error_message": str(e)
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log error metrics: {metric_error}")
        
        raise RuntimeError(f"Agent initialization failed: Nova Pro model unavailable - {str(e)}")


# Initialize the agent with comprehensive error handling for Nova Pro model
try:
    logger.info("Starting agent initialization...")
    agent = create_agent_with_tools()
    AGENT_AVAILABLE = True
    logger.info("MBTI Travel Planner Agent initialized successfully with Nova Pro model and AgentCore tools")
    
    # Log successful initialization
    try:
        monitoring_service.log_performance_metric(
            operation="agent_initialization",
            duration=1.0,  # Agent initialization typically takes some time
            success=True,
            additional_data={
                "environment": current_environment,
                "agentcore_available": AGENTCORE_AVAILABLE,
                "agent_available": AGENT_AVAILABLE
            }
        )
    except Exception as metric_error:
        logger.warning(f"Failed to log initialization metrics: {metric_error}")
        
except RuntimeError as e:
    logger.error(f"Agent initialization failed with RuntimeError: {e}")
    agent = None
    AGENT_AVAILABLE = False
    
    # Log initialization failure
    try:
        monitoring_service.log_error(
            error=e,
            operation="agent_initialization",
            context={
                "environment": current_environment,
                "error_type": "RuntimeError",
                "error_message": str(e)
            }
        )
    except Exception as metric_error:
        logger.warning(f"Failed to log error metrics: {metric_error}")
        
except Exception as e:
    logger.error(f"Agent initialization failed with unexpected error: {e}")
    logger.error(f"Error type: {type(e).__name__}")
    agent = None
    AGENT_AVAILABLE = False
    
    # Log unexpected initialization failure
    try:
        monitoring_service.log_error(
            error=e,
            operation="agent_initialization",
            context={
                "environment": current_environment,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            include_stack_trace=True
        )
    except Exception as metric_error:
        logger.warning(f"Failed to log error metrics: {metric_error}")

# Log final initialization status
if AGENT_AVAILABLE:
    logger.info("✅ Agent initialization completed successfully")
else:
    logger.warning("⚠️ Agent initialization failed - service will run with limited functionality")

def get_orchestration_status() -> Dict[str, Any]:
    """Get current orchestration and compatibility status."""
    status = {
        "orchestration_available": ORCHESTRATION_AVAILABLE,
        "agentcore_available": AGENTCORE_AVAILABLE,
        "agent_available": AGENT_AVAILABLE,
        "environment": current_environment
    }
    
    if ORCHESTRATION_AVAILABLE and compatibility_manager:
        status["compatibility_stats"] = compatibility_manager.get_compatibility_stats()
        status["orchestration_enabled"] = orchestration_middleware.is_enabled() if orchestration_middleware else False
    
    if orchestration_middleware:
        status["middleware_stats"] = orchestration_middleware.get_middleware_stats()
    
    return status


@app.entrypoint
async def invoke(payload): 
    """
    MBTI Travel Planner Agent entrypoint with Nova Pro model and AgentCore integration.
    
    This agent uses Amazon Nova Pro foundation model (amazon.nova-pro-v1:0) and connects 
    to deployed AgentCore agents via AgentCore Runtime API calls to provide:
    - Restaurant search by district and meal type via AgentCore Runtime API
    - Restaurant sentiment analysis and recommendations via AgentCore Runtime API
    - MBTI-based travel planning assistance with Nova Pro's enhanced reasoning
    - General travel planning questions with comprehensive error handling
    """
    import time
    import asyncio
    
    start_time = time.time()
    
    try:
        user_message = payload.get("prompt", "Hello! I'm your MBTI Travel Planner powered by Amazon Nova Pro with access to restaurant search and reasoning tools via AgentCore Runtime API. How can I help you find the perfect restaurants and plan your trip?")
        
        user_message = """
You are a ##RESTAURANT recommendations advisor## that with access to MCP tools to provide advises to different people. You need to provide a ##three-day## restaurant candidate recommendations to your users.
1. For each user query, analyse the goal.
2. Please think step by step.
3. Action: If needed, call ##MCP tools## based on loaded specification.
4. Observation: Wait for tool results.
5. Repeat until resolved, then Final Answer.

##Restaurant##: Please refer dataclass Restaurant in models\restaurant_models.py

##MCP Tools##:
- search_restaurants_combined: Give a list of districts and meal type, search for Restaurant in the districts that operates at these meal types in JSON
    - Input: { restaurants: List[Dict[str, Any]] }
    - Output: JSON string containing:
        - recommendation: Single recommended restaurant from top candidates
        - candidates: List of top 20 restaurants (or all if fewer than 20)
        - ranking_method: Method used for ranking
        - analysis_summary: Statistical analysis of the restaurant data
- recommend_restaurants: Give it a list of Restaurant in JSON, it will recommends one Restaurant and provide a list of candidate Restaurant in JSON

User query: 
- I would like to have a three-day meal recommendations, each meal with one recommended and 9 candidates for me to select.
- Each meal I will provide you one or two districts for your to search in your tools.
	- First day breakfast: Wan Chai district
	- First day lunch: Wan Chai district, Central district
	- First day dinner: Central district
	- Second day breakfast: Tsim Sha Tsui district
	- Second day lunch: Tsim Sha Tsui district, Yau Ma Tei district
	- Second day dinner: Yau Ma Tei district, Mong Kok district
	- Third day breakfast: Causeway Bay district
	- Third day lunch: Causeway Bay district, Repulse Bay district
	- Third day dinner: Repulse Bay district, Admiralty district
- After get this meals, return the result in a JSON format: 
{
	[
		{
			"day": 1,
			[
				"meal_type": "breakfast",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
			[
				"meal_type": "lunch",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
			[
				"meal_type": "dinner",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
		},
		{
			"day": 2,
			[
				"meal_type": "breakfast",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
			[
				"meal_type": "lunch",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
			[
				"meal_type": "dinner",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
		},
		{
			"day": 3,
			[
				"meal_type": "breakfast",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
			[
				"meal_type": "lunch",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
			[
				"meal_type": "dinner",
				"recommendation": <Restaurant>,
				"candidates": [<Restaurant>]
			],
		},
	]
}
        """

        # Extract and update JWT token from request if available
        jwt_token = None
        try:
            # Check for JWT token in payload or environment
            jwt_token = payload.get("jwt_token") or payload.get("token")
            if not jwt_token:
                # Check environment variable (set by AgentCore or test)
                import os
                jwt_token = os.getenv('JWT_TOKEN')
            
            # Update AgentCore client with JWT token if available
            if jwt_token and agentcore_client:
                update_agentcore_jwt_token(jwt_token)
                logger.info("✅ JWT token updated from request")
                
                # Also ensure tools have the JWT token (additional safety check)
                if agent and hasattr(agent, 'tools'):
                    update_tools_jwt_token(jwt_token, agent.tools)
                    logger.debug("✅ JWT token propagated to agent tools")
                    
            elif jwt_token:
                logger.warning("⚠️ JWT token available but AgentCore client not initialized")
            else:
                logger.debug("No JWT token found in request or environment")
                
        except Exception as jwt_error:
            logger.warning(f"Failed to process JWT token: {jwt_error}")
        
        logger.info(f"Processing request: {user_message[:100]}...")
        
        # Log request metrics with proper error handling
        try:
            monitoring_service.log_performance_metric(
                operation="request_received",
                duration=0.001,  # Immediate
                success=True,
                additional_data={
                    "message_length": len(user_message),
                    "agent_available": AGENT_AVAILABLE,
                    "agentcore_available": AGENTCORE_AVAILABLE,
                    "environment": current_environment
                }
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log request metrics: {metric_error}")
        
        # Test AgentCore connectivity on first request if not done yet
        if AGENTCORE_AVAILABLE and not hasattr(invoke, '_connectivity_tested'):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                connectivity_result = loop.run_until_complete(test_agentcore_connectivity())
                loop.close()
                invoke._connectivity_tested = True
                
                if not connectivity_result:
                    logger.warning("AgentCore connectivity test failed, but continuing with request")
            except Exception as e:
                logger.warning(f"Could not test AgentCore connectivity: {e}")
        
        # Create error context for comprehensive logging
        context = {
            "operation": "invoke",
            "environment": current_environment,
            "message_length": len(user_message),
            "agent_available": AGENT_AVAILABLE,
            "agentcore_available": AGENTCORE_AVAILABLE,
            "start_time": start_time
        }
        
        # Check agent availability (Nova Pro model) with improved error handling
        if not AGENT_AVAILABLE or agent is None:
            duration = time.time() - start_time
            logger.error("Agent not available - Nova Pro model initialization failed")
            
            # Log agent unavailability with proper error handling
            try:
                monitoring_service.log_error(
                    error=RuntimeError("Agent not available"),
                    operation="invoke",
                    context=context
                )
                
                monitoring_service.log_performance_metric(
                    operation="invoke",
                    duration=duration,
                    success=False,
                    error_type="agent_unavailable",
                    additional_data=context
                )
            except Exception as metric_error:
                logger.warning(f"Failed to log agent unavailability metrics: {metric_error}")
            
            return {
                "result": {
                    "role": "assistant", 
                    "content": [{
                        "text": "I apologize, but I'm currently unable to process your request due to a model initialization issue. The Amazon Nova Pro model may not be available in this region or there was a configuration error during startup. Please contact support for assistance."
                    }]
                }
            }
        
        # Check AgentCore availability and provide appropriate response
        if not AGENTCORE_AVAILABLE:
            duration = time.time() - start_time
            logger.warning("AgentCore tools not available - providing basic Nova Pro response")
            
            # Log AgentCore unavailability with proper error handling
            try:
                monitoring_service.log_performance_metric(
                    operation="invoke",
                    duration=duration,
                    success=True,  # Request succeeded, but with limited functionality
                    additional_data=dict(context, **{"agentcore_unavailable": True})
                )
            except Exception as metric_error:
                logger.warning(f"Failed to log AgentCore unavailability metrics: {metric_error}")
            
            return {
                "result": {
                    "role": "assistant", 
                    "content": [{
                        "text": "I'm your MBTI Travel Planner assistant powered by Amazon Nova Pro. However, my restaurant search and reasoning tools are currently unavailable due to initialization issues. I can still help with general travel planning questions using Nova Pro's enhanced reasoning capabilities. Please let me know how I can assist you!"
                    }]
                }
            }
        
        # Process with orchestration if available, otherwise use agent directly
        if ORCHESTRATION_AVAILABLE and orchestration_engine:
            result = await process_with_orchestration(user_message, payload)
        else:
            # Fallback to direct agent processing
            result = agent(user_message)
        
        # Calculate total processing time
        duration = time.time() - start_time
        
        logger.info(f"Request processed successfully with Nova Pro model and AgentCore tools ({duration:.2f}s)")
        
        # Log successful request processing with proper error handling
        try:
            monitoring_service.log_performance_metric(
                operation="invoke",
                duration=duration,
                success=True,
                additional_data=dict(context, **{
                    "response_length": len(str(result.message)) if result.message else 0,
                    "processing_time": duration
                })
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log success metrics: {metric_error}")
        
        return {"result": result.message}
        
    except AgentCoreError as e:
        duration = time.time() - start_time
        logger.error(f"AgentCore error: {e}")
        
        # Log AgentCore error with proper error handling
        try:
            monitoring_service.log_error(
                error=e,
                operation="invoke",
                context=dict(context, **{"duration": duration})
            )
            
            monitoring_service.log_performance_metric(
                operation="invoke",
                duration=duration,
                success=False,
                error_type="agentcore_error",
                additional_data=dict(context, **{"error_message": str(e)})
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log AgentCore error metrics: {metric_error}")
        
        return {
            "result": {
                "role": "assistant",
                "content": [{
                    "text": f"I encountered an issue connecting to my restaurant search tools: {str(e)}. I can still help with general travel planning questions using Nova Pro's enhanced reasoning. Please let me know how I can assist you!"
                }]
            }
        }
    except AuthenticationError as e:
        duration = time.time() - start_time
        logger.error(f"Authentication error: {e}")
        
        # Log authentication error with proper error handling
        try:
            monitoring_service.log_error(
                error=e,
                operation="invoke",
                context=dict(context, **{"duration": duration})
            )
            
            monitoring_service.log_performance_metric(
                operation="invoke",
                duration=duration,
                success=False,
                error_type="authentication_error",
                additional_data=dict(context, **{"error_message": str(e)})
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log authentication error metrics: {metric_error}")
        
        return {
            "result": {
                "role": "assistant",
                "content": [{
                    "text": f"I encountered an authentication issue with my restaurant search tools: {str(e)}. I can still help with general travel planning questions using Nova Pro's enhanced reasoning. Please let me know how I can assist you!"
                }]
            }
        }
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error processing request with Nova Pro model: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Log unexpected error with full stack trace and proper error handling
        try:
            monitoring_service.log_error(
                error=e,
                operation="invoke",
                context=dict(context, **{"duration": duration}),
                include_stack_trace=True
            )
            
            monitoring_service.log_performance_metric(
                operation="invoke",
                duration=duration,
                success=False,
                error_type=type(e).__name__,
                additional_data=dict(context, **{"error_message": str(e)})
            )
        except Exception as metric_error:
            logger.warning(f"Failed to log unexpected error metrics: {metric_error}")
        
        return {
            "result": {
                "role": "assistant",
                "content": [{
                    "text": f"I apologize, but I encountered an error while processing your request: {str(e)}. Please try again or rephrase your question."
                }]
            }
        }


if __name__ == "__main__": 
    app.run()