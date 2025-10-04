"""
MBTI Travel Planner Agent with Amazon Nova Pro Model and Gateway HTTP Tools

This agent uses Amazon Nova Pro foundation model (amazon.nova-pro-v1:0) with enhanced
reasoning capabilities, combined with restaurant search and reasoning functionality
through HTTP API calls to the deployed agentcore-gateway-mcp-tools service.

Model Configuration:
- Model: amazon.nova-pro-v1:0
- Temperature: 0.1 (for consistent, focused responses)
- Max Tokens: 2048 (sufficient for detailed travel planning)
- Timeout: 60 seconds (Nova Pro supports up to 60 minutes)

Architecture:
- HTTP Client: Direct API calls to agentcore-gateway-mcp-tools
- Environment-based Configuration: Automatic endpoint detection
- Comprehensive Error Handling: User-friendly error messages and fallbacks
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent

# Import HTTP client services and tools
from services.gateway_http_client import GatewayHTTPClient, GatewayError
from services.gateway_tools import (
    create_restaurant_search_tools, 
    create_restaurant_recommendation_tools,
    create_central_district_workflow_tools
)
from services.error_handler import ErrorHandler, ErrorContext, ErrorSeverity
from services.logging_service import initialize_logging_service, get_logging_service
from services.health_check_service import initialize_health_check_service, get_health_check_service
from config.gateway_config import get_gateway_config

# Initialize comprehensive logging and monitoring
current_environment = os.getenv('ENVIRONMENT', 'production')
log_level = os.getenv('LOG_LEVEL', 'INFO')

# Initialize logging service with environment-specific configuration
logging_service = initialize_logging_service(
    service_name="mbti_travel_planner_agent",
    log_level=log_level,
    log_dir=os.getenv('LOG_DIR', './logs'),
    enable_file_logging=os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true',
    enable_json_logging=os.getenv('ENABLE_JSON_LOGGING', 'true').lower() == 'true'
)

# Initialize health check service
health_check_service = initialize_health_check_service(
    environment=current_environment,
    check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '300')),  # 5 minutes
    enable_background_checks=os.getenv('ENABLE_BACKGROUND_HEALTH_CHECKS', 'true').lower() == 'true'
)

# Configure basic logging for compatibility
logging.basicConfig(level=getattr(logging, log_level.upper()))
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# Initialize HTTP client and error handler
http_client = None
error_handler = ErrorHandler("mbti_travel_planner_agent")

# Gateway service availability
GATEWAY_AVAILABLE = False

# Start background health checks
health_check_service.start_background_checks()

# Log initialization
logger.info(f"MBTI Travel Planner Agent initializing in {current_environment} environment")
logger.info(f"Logging level: {log_level}, File logging enabled: {logging_service.enable_file_logging}")
logger.info(f"Health checks enabled: {health_check_service.enable_background_checks}")

def initialize_http_client():
    """Initialize HTTP client for gateway communication."""
    global http_client, GATEWAY_AVAILABLE
    
    try:
        # Get gateway configuration for current environment
        gateway_config = get_gateway_config(current_environment)
        
        # Get authentication token from environment if available
        auth_token = os.getenv('GATEWAY_AUTH_TOKEN')
        
        # Initialize HTTP client
        http_client = GatewayHTTPClient(
            environment=current_environment,
            base_url=gateway_config.base_url,
            timeout=gateway_config.timeout,
            auth_token=auth_token
        )
        
        logger.info(f"HTTP client initialized for {current_environment} environment")
        logger.info(f"Gateway URL: {gateway_config.base_url}")
        
        # Log successful initialization
        logging_service.log_performance_metric(
            operation="initialize_http_client",
            duration=0.1,  # Initialization is typically fast
            success=True,
            additional_data={
                "environment": current_environment,
                "base_url": gateway_config.base_url,
                "timeout": gateway_config.timeout
            }
        )
        
        GATEWAY_AVAILABLE = True
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize HTTP client: {e}")
        
        # Log initialization failure
        logging_service.log_error(
            error=e,
            operation="initialize_http_client",
            context={
                "environment": current_environment,
                "error_type": type(e).__name__
            }
        )
        
        logging_service.log_performance_metric(
            operation="initialize_http_client",
            duration=0.1,
            success=False,
            error_type=type(e).__name__,
            additional_data={"environment": current_environment}
        )
        
        GATEWAY_AVAILABLE = False
        return False

async def test_gateway_connectivity():
    """Test connectivity to the gateway service using health checks."""
    if not http_client:
        logger.warning("HTTP client not available for connectivity test")
        return False
    
    try:
        # Perform health check on gateway
        health_result = await health_check_service.check_endpoint_health("gateway_health")
        
        if health_result.status == "healthy":
            logger.info("Gateway connectivity test passed")
            logging_service.log_performance_metric(
                operation="gateway_connectivity_test",
                duration=health_result.response_time_ms / 1000.0,
                success=True,
                additional_data={
                    "endpoint": health_result.endpoint,
                    "response_time_ms": health_result.response_time_ms
                }
            )
            return True
        else:
            logger.warning(f"Gateway connectivity test failed: {health_result.error_message}")
            logging_service.log_performance_metric(
                operation="gateway_connectivity_test",
                duration=health_result.response_time_ms / 1000.0,
                success=False,
                error_type="unhealthy_response",
                additional_data={
                    "endpoint": health_result.endpoint,
                    "status": health_result.status,
                    "error_message": health_result.error_message
                }
            )
            return False
        
    except Exception as e:
        logger.warning(f"Gateway connectivity test failed: {e}")
        logging_service.log_error(
            error=e,
            operation="gateway_connectivity_test",
            context={"environment": current_environment}
        )
        return False

# Initialize HTTP client on startup
initialize_http_client()

# Test gateway connectivity asynchronously (will be done during first request)
# We can't run async code at module level, so we'll test during first invocation


def create_gateway_tools() -> List:
    """Create restaurant search and recommendation tools using Gateway HTTP client."""
    if not GATEWAY_AVAILABLE:
        logger.warning("Gateway not available, returning empty tools list")
        return []
    
    tools = []
    
    try:
        # Get authentication token from environment
        auth_token = os.getenv('GATEWAY_AUTH_TOKEN')
        
        # Create restaurant search tools
        search_tools = create_restaurant_search_tools(
            environment=current_environment,
            auth_token=auth_token
        )
        
        # Create restaurant recommendation tools
        recommendation_tools = create_restaurant_recommendation_tools(
            environment=current_environment,
            auth_token=auth_token
        )
        
        # Create Central district workflow tools
        central_workflow_tools = create_central_district_workflow_tools(
            environment=current_environment,
            auth_token=auth_token
        )
        
        # Combine all tools
        tools.extend(search_tools)
        tools.extend(recommendation_tools)
        tools.extend(central_workflow_tools)
        
        logger.info(f"Created {len(tools)} gateway HTTP tools")
        
        # Log successful tool creation
        logging_service.log_performance_metric(
            operation="create_gateway_tools",
            duration=0.1,  # Tool creation is typically fast
            success=True,
            additional_data={
                "tools_count": len(tools),
                "environment": current_environment
            }
        )
        
        return tools
        
    except Exception as e:
        logger.error(f"Failed to create gateway tools: {e}")
        
        # Log tool creation failure
        logging_service.log_error(
            error=e,
            operation="create_gateway_tools",
            context={
                "environment": current_environment,
                "error_type": type(e).__name__
            }
        )
        
        logging_service.log_performance_metric(
            operation="create_gateway_tools",
            duration=0.1,
            success=False,
            error_type=type(e).__name__,
            additional_data={"environment": current_environment}
        )
        
        return []


# Create agent with all gateway HTTP tools
def create_agent_with_tools():
    """Create the agent with all available gateway HTTP tools."""
    tools = []
    
    if GATEWAY_AVAILABLE:
        # Add gateway HTTP tools
        gateway_tools = create_gateway_tools()
        tools.extend(gateway_tools)
        
        logger.info(f"Created agent with {len(tools)} gateway HTTP tools")
    else:
        logger.info("Created agent without gateway tools (service not available)")
    
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
        logging_service.log_performance_metric(
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
        logging_service.log_error(
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
        
        logging_service.log_performance_metric(
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
    logger.info("MBTI Travel Planner Agent initialized successfully with Nova Pro model and Gateway HTTP tools")
except RuntimeError as e:
    logger.error(f"Agent initialization failed: {e}")
    agent = None
    AGENT_AVAILABLE = False


@app.entrypoint
def invoke(payload): 
    """
    MBTI Travel Planner Agent entrypoint with Nova Pro model and Gateway HTTP integration.
    
    This agent uses Amazon Nova Pro foundation model (amazon.nova-pro-v1:0) and connects 
    to the agentcore-gateway-mcp-tools service via HTTP API calls to provide:
    - Restaurant search by district and meal type via Gateway HTTP API
    - Restaurant sentiment analysis and recommendations via Gateway HTTP API
    - MBTI-based travel planning assistance with Nova Pro's enhanced reasoning
    - General travel planning questions with comprehensive error handling
    """
    import time
    import asyncio
    
    start_time = time.time()
    
    try:
        user_message = payload.get("prompt", "Hello! I'm your MBTI Travel Planner powered by Amazon Nova Pro with access to restaurant search and reasoning tools via Gateway HTTP API. How can I help you find the perfect restaurants and plan your trip?")
        
        logger.info(f"Processing request: {user_message[:100]}...")
        
        # Log request metrics
        logging_service.log_performance_metric(
            operation="request_received",
            duration=0.001,  # Immediate
            success=True,
            additional_data={
                "message_length": len(user_message),
                "agent_available": AGENT_AVAILABLE,
                "gateway_available": GATEWAY_AVAILABLE,
                "environment": current_environment
            }
        )
        
        # Test gateway connectivity on first request if not done yet
        if GATEWAY_AVAILABLE and not hasattr(invoke, '_connectivity_tested'):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                connectivity_result = loop.run_until_complete(test_gateway_connectivity())
                loop.close()
                invoke._connectivity_tested = True
                
                if not connectivity_result:
                    logger.warning("Gateway connectivity test failed, but continuing with request")
            except Exception as e:
                logger.warning(f"Could not test gateway connectivity: {e}")
        
        # Create error context for comprehensive logging
        context = {
            "operation": "invoke",
            "environment": current_environment,
            "message_length": len(user_message),
            "agent_available": AGENT_AVAILABLE,
            "gateway_available": GATEWAY_AVAILABLE,
            "start_time": start_time
        }
        
        # Check agent availability (Nova Pro model)
        if not AGENT_AVAILABLE or agent is None:
            duration = time.time() - start_time
            logger.error("Agent not available - Nova Pro model initialization failed")
            
            # Log agent unavailability
            logging_service.log_error(
                error=RuntimeError("Agent not available"),
                operation="invoke",
                context=context
            )
            
            logging_service.log_performance_metric(
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
        
        # Check Gateway availability and provide appropriate response
        if not GATEWAY_AVAILABLE:
            duration = time.time() - start_time
            logger.warning("Gateway tools not available - providing basic Nova Pro response")
            
            # Log gateway unavailability
            logging_service.log_performance_metric(
                operation="invoke",
                duration=duration,
                success=True,  # Request succeeded, but with limited functionality
                additional_data=dict(context, **{"gateway_unavailable": True})
            )
            
            return {
                "result": {
                    "role": "assistant", 
                    "content": [{
                        "text": "I'm your MBTI Travel Planner assistant powered by Amazon Nova Pro. However, my restaurant search and reasoning tools are currently unavailable. I can still help with general travel planning questions using Nova Pro's enhanced reasoning capabilities. Please let me know how I can assist you!"
                    }]
                }
            }
        
        # Process with the agent (Nova Pro + Gateway HTTP tools)
        result = agent(user_message)
        
        # Calculate total processing time
        duration = time.time() - start_time
        
        logger.info(f"Request processed successfully with Nova Pro model and Gateway HTTP tools ({duration:.2f}s)")
        
        # Log successful request processing
        logging_service.log_performance_metric(
            operation="invoke",
            duration=duration,
            success=True,
            additional_data=dict(context, **{
                "response_length": len(str(result.message)) if result.message else 0,
                "processing_time": duration
            })
        )
        
        return {"result": result.message}
        
    except GatewayError as e:
        duration = time.time() - start_time
        logger.error(f"Gateway error: {e}")
        
        # Log gateway error
        logging_service.log_error(
            error=e,
            operation="invoke",
            context=dict(context, **{"duration": duration})
        )
        
        logging_service.log_performance_metric(
            operation="invoke",
            duration=duration,
            success=False,
            error_type="gateway_error",
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
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error processing request with Nova Pro model: {e}")
        
        # Log unexpected error with full stack trace
        logging_service.log_error(
            error=e,
            operation="invoke",
            context=dict(context, **{"duration": duration}),
            include_stack_trace=True
        )
        
        logging_service.log_performance_metric(
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