"""
AgentCore Runtime Client Demo

This script demonstrates how to use the AgentCore Runtime client infrastructure
for making calls to deployed AgentCore agents.
"""

import asyncio
import json
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.agentcore_runtime_client import (
    AgentCoreRuntimeClient,
    RetryConfig,
    CircuitBreakerConfig,
    ConnectionConfig
)
from services.authentication_manager import AuthenticationManager
from config.agentcore_config import load_agentcore_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_agentcore_client():
    """Demonstrate AgentCore Runtime client usage."""
    
    print("🚀 AgentCore Runtime Client Demo")
    print("=" * 50)
    
    try:
        # Load configuration
        print("\n📋 Loading configuration...")
        config = load_agentcore_config('development')
        print(f"✅ Configuration loaded for environment: {config.environment}")
        print(f"   - Restaurant Search Agent: {config.agentcore.restaurant_search_agent_arn}")
        print(f"   - Restaurant Reasoning Agent: {config.agentcore.restaurant_reasoning_agent_arn}")
        print(f"   - Region: {config.agentcore.region}")
        print(f"   - Timeout: {config.agentcore.timeout_seconds}s")
        print(f"   - Max Retries: {config.agentcore.max_retries}")
        
        # Create authentication manager
        print("\n🔐 Setting up authentication...")
        auth_manager = AuthenticationManager(config.cognito)
        print(f"✅ Authentication manager created for user pool: {config.cognito.user_pool_id}")
        
        # Test authentication (this will use test user credentials)
        print("\n🔑 Testing authentication...")
        try:
            auth_result = await auth_manager.test_authentication()
            if auth_result["success"]:
                print("✅ Authentication test successful!")
                print(f"   - Token obtained: {auth_result['token_obtained']}")
                print(f"   - Token valid: {auth_result['token_valid']}")
                if "token_claims" in auth_result:
                    claims = auth_result["token_claims"]
                    print(f"   - User: {claims.get('email', 'N/A')}")
            else:
                print(f"❌ Authentication test failed: {auth_result.get('error', 'Unknown error')}")
                print("   Note: This is expected in demo mode without real credentials")
        except Exception as e:
            print(f"❌ Authentication test failed: {str(e)}")
            print("   Note: This is expected in demo mode without real credentials")
        
        # Create runtime client
        print("\n🔧 Creating AgentCore Runtime client...")
        
        # Configure retry behavior
        retry_config = RetryConfig(
            max_retries=config.agentcore.max_retries,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Configure circuit breaker
        circuit_breaker_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            half_open_max_calls=3
        )
        
        # Configure connections
        connection_config = ConnectionConfig(
            timeout_seconds=config.agentcore.timeout_seconds,
            max_connections=config.performance.max_connections,
            max_connections_per_host=config.performance.max_connections_per_host,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        async with AgentCoreRuntimeClient(
            region=config.agentcore.region,
            retry_config=retry_config,
            circuit_breaker_config=circuit_breaker_config,
            connection_config=connection_config
        ) as runtime_client:
            
            print("✅ AgentCore Runtime client created successfully!")
            
            # Get health status
            print("\n🏥 Checking client health...")
            health = runtime_client.get_health_status()
            print(f"   - Healthy: {health.is_healthy}")
            print(f"   - Error count: {health.error_count}")
            print(f"   - Circuit breaker state: {health.circuit_breaker_state.value}")
            print(f"   - Max connections: {health.connection_pool_status['total_connections']}")
            
            # Get performance metrics
            print("\n📊 Performance metrics...")
            metrics = runtime_client.get_performance_metrics()
            print(f"   - Total calls: {metrics['total_calls']}")
            print(f"   - Total errors: {metrics['total_errors']}")
            print(f"   - Error rate: {metrics['error_rate']:.2%}")
            print(f"   - Average response time: {metrics['average_response_time_ms']:.2f}ms")
            
            # Demonstrate agent invocation (this will fail without real credentials)
            print("\n🤖 Testing agent invocation...")
            try:
                response = await runtime_client.invoke_agent(
                    agent_arn=config.agentcore.restaurant_search_agent_arn,
                    input_text="Find restaurants in Central district that serve breakfast"
                )
                
                print("✅ Agent invocation successful!")
                print(f"   - Response: {response.output_text[:100]}...")
                print(f"   - Session ID: {response.session_id}")
                print(f"   - Execution time: {response.execution_time_ms}ms")
                
            except Exception as e:
                print(f"❌ Agent invocation failed: {str(e)}")
                print("   Note: This is expected in demo mode without real AWS credentials")
            
            # Final health check
            print("\n🏥 Final health check...")
            final_health = runtime_client.get_health_status()
            final_metrics = runtime_client.get_performance_metrics()
            
            print(f"   - Final health status: {final_health.is_healthy}")
            print(f"   - Total calls made: {final_metrics['total_calls']}")
            print(f"   - Total errors: {final_metrics['total_errors']}")
            
        print("\n✅ Demo completed successfully!")
        print("   - AgentCore Runtime client closed and resources cleaned up")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        logger.exception("Demo failed")


def demo_configuration():
    """Demonstrate configuration loading and validation."""
    
    print("\n📋 Configuration Demo")
    print("=" * 30)
    
    try:
        # Load configuration
        config = load_agentcore_config('development')
        
        # Get configuration manager
        from config.agentcore_config import get_config_manager
        config_manager = get_config_manager()
        
        # Show configuration summary
        summary = config_manager.get_configuration_summary()
        print("\n📊 Configuration Summary:")
        print(json.dumps(summary, indent=2))
        
        # Validate configuration
        issues = config_manager.validate_configuration(config)
        if issues:
            print(f"\n⚠️  Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✅ Configuration validation passed!")
        
        # Show environment detection
        detected_env = config_manager.detect_environment()
        print(f"\n🌍 Detected environment: {detected_env}")
        
        # Show default agent ARNs
        print(f"\n🤖 Default agent ARNs for {detected_env}:")
        if detected_env in config_manager.DEFAULT_AGENT_ARNS:
            default_arns = config_manager.DEFAULT_AGENT_ARNS[detected_env]
            for agent_type, arn in default_arns.items():
                print(f"   - {agent_type}: {arn}")
        
    except Exception as e:
        print(f"❌ Configuration demo failed: {str(e)}")
        logger.exception("Configuration demo failed")


async def main():
    """Main demo function."""
    
    print("🎯 MBTI Travel Planner - AgentCore Integration Demo")
    print("=" * 60)
    
    # Configuration demo
    demo_configuration()
    
    # Runtime client demo
    await demo_agentcore_client()
    
    print("\n🎉 All demos completed!")
    print("\nNext steps:")
    print("1. Configure AWS credentials for real agent calls")
    print("2. Set up service account password for authentication")
    print("3. Deploy and test with actual AgentCore agents")
    print("4. Integrate with MBTI Travel Planner workflows")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())