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
from services.agentcore_runtime_client import AgentCoreRuntimeClient, AgentCoreError
from services.authentication_manager import AuthenticationManager, AuthenticationError
from services.restaurant_search_tool import RestaurantSearchTool
from services.restaurant_reasoning_tool import RestaurantReasoningTool
from services.agentcore_error_handler import AgentCoreErrorHandler
from services.agentcore_monitoring_service import AgentCoreMonitoringService
from services.agentcore_health_check_service import AgentCoreHealthCheckService
from config.agentcore_environment_config import get_agentcore_config

# Initialize comprehensive logging and monitoring
current_environment = os.getenv('ENVIRONMENT', 'production')
log_level = os.getenv('LOG_LEVEL', 'INFO')

# Initialize AgentCore monitoring service
monitoring_service = AgentCoreMonitoringService(
    service_name="mbti_travel_planner_agent",
    environment=current_environment,
    log_level=log_level,
    enable_performance_monitoring=os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true',
    enable_request_tracing=os.getenv('ENABLE_REQUEST_TRACING', 'true').lower() == 'true'
)

# Initialize AgentCore health check service
health_check_service = AgentCoreHealthCheckService(
    environment=current_environment,
    check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '300')),  # 5 minutes
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

# AgentCore service availability
AGENTCORE_AVAILABLE = False

# Start background health checks
health_check_service.start_background_checks()

# Log initialization
logger.info(f"MBTI Travel Planner Agent initializing in {current_environment} environment")
logger.info(f"Logging level: {log_level}, Performance monitoring enabled: {monitoring_service.enable_performance_monitoring}")
logger.info(f"Health checks enabled: {health_check_service.enable_background_checks}")

def initialize_agentcore_client():
    """Initialize AgentCore Runtime client for agent communication."""
    global agentcore_client, auth_manager, AGENTCORE_AVAILABLE
    
    try:
        # Get AgentCore configuration for current environment
        agentcore_config = get_agentcore_config(current_environment)
        
        # Initialize authentication manager
        auth_manager = AuthenticationManager(agentcore_config.cognito)
        
        # Initialize AgentCore Runtime client
        agentcore_client = AgentCoreRuntimeClient(
            cognito_config=agentcore_config.cognito,
            region=agentcore_config.agentcore.region,
            timeout_seconds=agentcore_config.agentcore.timeout_seconds,
            max_retries=agentcore_config.agentcore.max_retries
        )
        
        logger.info(f"AgentCore Runtime client initialized for {current_environment} environment")
        logger.info(f"Restaurant Search Agent ARN: {agentcore_config.agentcore.restaurant_search_agent_arn}")
        logger.info(f"Restaurant Reasoning Agent ARN: {agentcore_config.agentcore.restaurant_reasoning_agent_arn}")
        
        # Log successful initialization
        monitoring_service.log_performance_metric(
            operation="initialize_agentcore_client",
            duration=0.1,  # Initialization is typically fast
            success=True,
            additional_data={
                "environment": current_environment,
                "region": agentcore_config.agentcore.region,
                "timeout": agentcore_config.agentcore.timeout_seconds,
                "max_retries": agentcore_config.agentcore.max_retries
            }
        )
        
        AGENTCORE_AVAILABLE = True
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize AgentCore Runtime client: {e}")
        
        # Log initialization failure
        monitoring_service.log_error(
            error=e,
            operation="initialize_agentcore_client",
            context={
                "environment": current_environment,
                "error_type": type(e).__name__
            }
        )
        
        monitoring_service.log_performance_metric(
            operation="initialize_agentcore_client",
            duration=0.1,
            success=False,
            error_type=type(e).__name__,
            additional_data={"environment": current_environment}
        )
        
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
        
        # Combine all tools
        tools.extend(search_tools)
        tools.extend(reasoning_tools)
        
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
                "reasoning_agent_arn": agentcore_config.agentcore.restaurant_reasoning_agent_arn
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


# Create agent with all AgentCore tools
def create_agent_with_tools():
    """Create the agent with all available AgentCore tools."""
    tools = []
    
    if AGENTCORE_AVAILABLE:
        # Add AgentCore tools
        agentcore_tools = create_agentcore_tools()
        tools.extend(agentcore_tools)
        
        logger.info(f"Created agent with {len(tools)} AgentCore tools")
    else:
        logger.info("Created agent without AgentCore tools (service not available)")
    
    try:
        # Get model configuration from environment or use defaults
        model_name = os.getenv('AGENT_MODEL', 'amazon.nova-pro-v1:0')
        temperature = float(os.getenv('AGENT_TEMPERATURE', '0.1'))
        max_tokens = int(os.getenv('AGENT_MAX_TOKENS', '2048'))
        timeout = int(os.getenv('AGENT_TIMEOUT', '60'))
        
        # Create agent with Nova Pro model and tools
        agent = Agent(
            model=model_name,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout  # Nova Pro supports up to 60 minutes
        )
        
        logger.info(f"Agent created successfully with Nova Pro model: {model_name}")
        logger.info(f"Model parameters - Temperature: {temperature}, Max Tokens: {max_tokens}, Timeout: {timeout}s")
        
        # Log successful agent creation
        monitoring_service.log_performance_metric(
            operation="create_agent_with_tools",
            duration=0.5,  # Agent creation typically takes some time
            success=True,
            additional_data={
                "model_name": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": timeout,
                "tools_count": len(tools)
            }
        )
        
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent with Nova Pro model: {e}")
        logger.error("Nova Pro model may not be available in this region or configuration is invalid")
        
        # Log detailed error information
        monitoring_service.log_error(
            error=e,
            operation="create_agent_with_tools",
            context={
                "model_name": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": timeout,
                "tools_count": len(tools),
                "environment": current_environment
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
                "environment": current_environment
            }
        )
        
        raise RuntimeError(f"Agent initialization failed: Nova Pro model unavailable - {str(e)}")


# Initialize the agent with error handling for Nova Pro model
try:
    agent = create_agent_with_tools()
    AGENT_AVAILABLE = True
    logger.info("MBTI Travel Planner Agent initialized successfully with Nova Pro model and AgentCore tools")
except RuntimeError as e:
    logger.error(f"Agent initialization failed: {e}")
    agent = None
    AGENT_AVAILABLE = False


@app.entrypoint
def invoke(payload): 
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
        
        logger.info(f"Processing request: {user_message[:100]}...")
        
        # Log request metrics
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
        
        # Check agent availability (Nova Pro model)
        if not AGENT_AVAILABLE or agent is None:
            duration = time.time() - start_time
            logger.error("Agent not available - Nova Pro model initialization failed")
            
            # Log agent unavailability
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
            
            return {
                "result": {
                    "role": "assistant", 
                    "content": [{
                        "text": "I apologize, but I'm currently unable to process your request due to a model initialization issue. The Amazon Nova Pro model may not be available in this region. Please contact support for assistance."
                    }]
                }
            }
        
        # Check AgentCore availability and provide appropriate response
        if not AGENTCORE_AVAILABLE:
            duration = time.time() - start_time
            logger.warning("AgentCore tools not available - providing basic Nova Pro response")
            
            # Log AgentCore unavailability
            monitoring_service.log_performance_metric(
                operation="invoke",
                duration=duration,
                success=True,  # Request succeeded, but with limited functionality
                additional_data=dict(context, **{"agentcore_unavailable": True})
            )
            
            return {
                "result": {
                    "role": "assistant", 
                    "content": [{
                        "text": "I'm your MBTI Travel Planner assistant powered by Amazon Nova Pro. However, my restaurant search and reasoning tools are currently unavailable. I can still help with general travel planning questions using Nova Pro's enhanced reasoning capabilities. Please let me know how I can assist you!"
                    }]
                }
            }
        
        # Process with the agent (Nova Pro + AgentCore tools)
        result = agent(user_message)
        
        # Calculate total processing time
        duration = time.time() - start_time
        
        logger.info(f"Request processed successfully with Nova Pro model and AgentCore tools ({duration:.2f}s)")
        
        # Log successful request processing
        monitoring_service.log_performance_metric(
            operation="invoke",
            duration=duration,
            success=True,
            additional_data=dict(context, **{
                "response_length": len(str(result.message)) if result.message else 0,
                "processing_time": duration
            })
        )
        
        return {"result": result.message}
        
    except AgentCoreError as e:
        duration = time.time() - start_time
        logger.error(f"AgentCore error: {e}")
        
        # Log AgentCore error
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
        
        # Log authentication error
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
        
        # Log unexpected error with full stack trace
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