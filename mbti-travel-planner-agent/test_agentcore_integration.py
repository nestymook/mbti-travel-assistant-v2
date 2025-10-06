#!/usr/bin/env python3
"""
Test script for AgentCore integration validation.

This script tests the main agent's integration with AgentCore agents
to ensure proper configuration and connectivity.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agentcore_configuration():
    """Test AgentCore configuration loading."""
    try:
        from config.agentcore_environment_config import get_agentcore_config
        
        # Test configuration loading for different environments
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            try:
                config = get_agentcore_config(env)
                logger.info(f"✅ {env.capitalize()} configuration loaded successfully")
                logger.info(f"   Search Agent ARN: {config.agentcore.restaurant_search_agent_arn}")
                logger.info(f"   Reasoning Agent ARN: {config.agentcore.restaurant_reasoning_agent_arn}")
                logger.info(f"   Region: {config.agentcore.region}")
                logger.info(f"   Timeout: {config.agentcore.timeout_seconds}s")
                logger.info(f"   Max Retries: {config.agentcore.max_retries}")
            except Exception as e:
                logger.error(f"❌ Failed to load {env} configuration: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


async def test_agentcore_client_initialization():
    """Test AgentCore Runtime client initialization."""
    try:
        from config.agentcore_environment_config import get_agentcore_config
        from services.agentcore_runtime_client import AgentCoreRuntimeClient
        from services.authentication_manager import AuthenticationManager
        
        # Load configuration
        config = get_agentcore_config('development')
        
        # Initialize authentication manager
        auth_manager = AuthenticationManager(config.cognito)
        logger.info("✅ Authentication manager initialized")
        
        # Initialize AgentCore Runtime client
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region,
            timeout_seconds=config.agentcore.timeout_seconds,
            max_retries=config.agentcore.max_retries
        )
        logger.info("✅ AgentCore Runtime client initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Client initialization test failed: {e}")
        return False


async def test_tool_creation():
    """Test AgentCore tool creation."""
    try:
        from config.agentcore_environment_config import get_agentcore_config
        from services.agentcore_runtime_client import AgentCoreRuntimeClient
        from services.authentication_manager import AuthenticationManager
        from services.restaurant_search_tool import create_restaurant_search_tools
        from services.restaurant_reasoning_tool import create_restaurant_reasoning_tools
        
        # Load configuration
        config = get_agentcore_config('development')
        
        # Initialize components
        auth_manager = AuthenticationManager(config.cognito)
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region,
            timeout_seconds=config.agentcore.timeout_seconds,
            max_retries=config.agentcore.max_retries
        )
        
        # Create restaurant search tools
        search_tools = create_restaurant_search_tools(
            runtime_client=runtime_client,
            search_agent_arn=config.agentcore.restaurant_search_agent_arn,
            auth_manager=auth_manager
        )
        logger.info(f"✅ Created {len(search_tools)} restaurant search tools")
        
        # Create restaurant reasoning tools
        reasoning_tools = create_restaurant_reasoning_tools(
            runtime_client=runtime_client,
            reasoning_agent_arn=config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        logger.info(f"✅ Created {len(reasoning_tools)} restaurant reasoning tools")
        
        total_tools = len(search_tools) + len(reasoning_tools)
        logger.info(f"✅ Total AgentCore tools created: {total_tools}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Tool creation test failed: {e}")
        return False


async def test_health_check_service():
    """Test AgentCore health check service."""
    try:
        from config.agentcore_environment_config import get_agentcore_config
        from services.agentcore_health_check_service import AgentCoreHealthCheckService
        
        # Load configuration
        config = get_agentcore_config('development')
        
        # Initialize health check service
        health_service = AgentCoreHealthCheckService(
            config=config,
            enable_background_checks=False  # Disable for testing
        )
        logger.info("✅ AgentCore health check service initialized")
        
        # Test listing agent runtimes
        agent_runtimes = await health_service.list_agent_runtimes()
        logger.info(f"✅ Listed {len(agent_runtimes)} agent runtimes")
        
        # Test overall health status
        overall_status = health_service.get_overall_health_status()
        logger.info(f"✅ Overall health status: {overall_status['overall_status']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Health check service test failed: {e}")
        return False


async def test_main_agent_initialization():
    """Test main agent initialization with AgentCore tools."""
    try:
        # Set environment for testing
        os.environ['ENVIRONMENT'] = 'development'
        
        # Test creating an agent with tools directly
        from config.agentcore_environment_config import get_agentcore_config
        from services.agentcore_runtime_client import AgentCoreRuntimeClient
        from services.authentication_manager import AuthenticationManager
        from services.restaurant_search_tool import create_restaurant_search_tools
        from services.restaurant_reasoning_tool import create_restaurant_reasoning_tools
        from strands import Agent
        
        # Load configuration
        config = get_agentcore_config('development')
        
        # Initialize components
        auth_manager = AuthenticationManager(config.cognito)
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region,
            timeout_seconds=config.agentcore.timeout_seconds,
            max_retries=config.agentcore.max_retries
        )
        
        # Create tools
        search_tools = create_restaurant_search_tools(
            runtime_client=runtime_client,
            search_agent_arn=config.agentcore.restaurant_search_agent_arn,
            auth_manager=auth_manager
        )
        
        reasoning_tools = create_restaurant_reasoning_tools(
            runtime_client=runtime_client,
            reasoning_agent_arn=config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        # Combine tools
        all_tools = search_tools + reasoning_tools
        
        # Create agent
        agent = Agent(
            model=os.getenv('AGENT_MODEL', 'amazon.nova-pro-v1:0'),
            tools=all_tools,
            temperature=float(os.getenv('AGENT_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('AGENT_MAX_TOKENS', '2048')),
            timeout=int(os.getenv('AGENT_TIMEOUT', '60'))
        )
        
        if agent is None:
            logger.error("❌ Failed to create agent")
            return False
        
        logger.info("✅ Main agent created successfully with AgentCore tools")
        logger.info(f"   Agent model: {os.getenv('AGENT_MODEL', 'amazon.nova-pro-v1:0')}")
        logger.info(f"   Tools available: {len(all_tools)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Main agent initialization test failed: {e}")
        return False


async def run_all_tests():
    """Run all AgentCore integration tests."""
    logger.info("🚀 Starting AgentCore Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration Loading", test_agentcore_configuration),
        ("Client Initialization", test_agentcore_client_initialization),
        ("Tool Creation", test_tool_creation),
        ("Health Check Service", test_health_check_service),
        ("Main Agent Initialization", test_main_agent_initialization)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running test: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! AgentCore integration is working correctly.")
        return True
    else:
        logger.error(f"💥 {total - passed} test(s) failed. Please check the configuration and dependencies.")
        return False


if __name__ == "__main__":
    try:
        # Run tests
        success = asyncio.run(run_all_tests())
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test runner failed: {e}")
        sys.exit(1)