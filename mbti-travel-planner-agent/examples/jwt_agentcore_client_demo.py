#!/usr/bin/env python3
"""
JWT AgentCore Client Demo

This script demonstrates how to use the updated AgentCore Runtime Client
with JWT authentication instead of boto3.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.agentcore_runtime_client import (
    create_agentcore_client_with_jwt,
    create_agentcore_client_with_auth_manager
)
from services.authentication_manager import AuthenticationManager, CognitoConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_jwt_client():
    """Demonstrate JWT-based AgentCore client usage."""
    
    # Example 1: Using direct JWT token
    logger.info("=== Demo 1: Direct JWT Token ===")
    
    # In a real scenario, you would get this token from authentication
    jwt_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."  # Your actual JWT token
    
    try:
        # Create client with JWT token
        client = create_agentcore_client_with_jwt(
            jwt_token=jwt_token,
            region="us-east-1"
        )
        
        # Example agent invocation
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_planner_agent-JPTzWT3IZp"
        
        response = await client.invoke_agent(
            agent_arn=agent_arn,
            input_text="Hello! Can you help me find restaurants in Central district?",
            session_id="demo_session_12345"
        )
        
        logger.info(f"Response: {response.output_text[:200]}...")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Demo 1 failed: {e}")
    
    # Example 2: Using Authentication Manager
    logger.info("=== Demo 2: Authentication Manager ===")
    
    try:
        # Load Cognito configuration
        cognito_config = CognitoConfig(
            user_pool_id="us-east-1_KePRX24Bn",
            client_id="1ofgeckef3po4i3us4j1m4chvd",
            client_secret="t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
            region="us-east-1",
            test_user_email="test@mbti-travel.com",
            test_user_password="TestPass1234!"
        )
        
        # Create authentication manager
        auth_manager = AuthenticationManager(cognito_config)
        
        # Create client with authentication manager
        client = create_agentcore_client_with_auth_manager(
            authentication_manager=auth_manager,
            region="us-east-1"
        )
        
        # Example agent invocation with automatic token management
        response = await client.invoke_agent(
            agent_arn=agent_arn,
            input_text="I'm an ENFP personality type. Can you recommend restaurants that would suit me?",
            session_id="demo_session_67890"
        )
        
        logger.info(f"Response: {response.output_text[:200]}...")
        
        # Get performance metrics
        metrics = client.get_performance_metrics()
        logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Demo 2 failed: {e}")


async def demo_streaming():
    """Demonstrate streaming response with JWT authentication."""
    logger.info("=== Demo 3: Streaming Response ===")
    
    try:
        # Create authentication manager
        cognito_config = CognitoConfig(
            user_pool_id="us-east-1_KePRX24Bn",
            client_id="1ofgeckef3po4i3us4j1m4chvd",
            client_secret="t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
            region="us-east-1"
        )
        
        auth_manager = AuthenticationManager(cognito_config)
        
        # Create client
        client = create_agentcore_client_with_auth_manager(
            authentication_manager=auth_manager,
            region="us-east-1"
        )
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_planner_agent-JPTzWT3IZp"
        
        logger.info("Starting streaming response...")
        
        async for chunk in client.invoke_agent_with_streaming(
            agent_arn=agent_arn,
            input_text="Tell me about the best dim sum restaurants in Hong Kong",
            session_id="streaming_demo_session"
        ):
            if chunk.chunk_text:
                print(chunk.chunk_text, end='', flush=True)
            
            if chunk.is_final:
                print("\n[Streaming complete]")
                break
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Streaming demo failed: {e}")


def main():
    """Main demo function."""
    logger.info("🚀 Starting JWT AgentCore Client Demo")
    
    try:
        # Run demos
        asyncio.run(demo_jwt_client())
        asyncio.run(demo_streaming())
        
        logger.info("✅ Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()