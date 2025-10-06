"""
AgentCore Error Handling System Demonstration

This script demonstrates the comprehensive error handling system for AgentCore integration,
including circuit breaker patterns, retry logic, and graceful fallback mechanisms.
"""

import asyncio
import logging
import time
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import error handling components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.agentcore_error_handler import (
    AgentCoreErrorHandler,
    AgentCoreError,
    AgentInvocationError,
    AuthenticationError,
    AgentTimeoutError,
    AgentUnavailableError,
    CircuitBreakerOpenError,
    RetryConfig,
    CircuitBreakerConfig,
    get_agentcore_error_handler
)


class ErrorHandlingDemo:
    """Demonstration of AgentCore error handling capabilities."""
    
    def __init__(self):
        # Configure error handler with demo settings
        retry_config = RetryConfig(max_retries=2, base_delay=0.5)
        cb_config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5)
        
        self.error_handler = AgentCoreErrorHandler(retry_config, cb_config)
        self.logger = logging.getLogger("demo")
    
    async def demo_successful_call(self):
        """Demonstrate successful agent call with error protection."""
        print("\n=== Demo 1: Successful Agent Call ===")
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123:runtime/demo-agent"
        context = self.error_handler.create_error_context(
            agent_arn=agent_arn,
            operation="demo_successful_call",
            user_id="demo_user"
        )
        
        async def successful_agent_call():
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"output": "Restaurant search completed successfully", "restaurants": []}
        
        try:
            result = await self.error_handler.execute_with_protection(
                successful_agent_call, context
            )
            print(f"✅ Success: {result['output']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_retry_with_eventual_success(self):
        """Demonstrate retry logic with eventual success."""
        print("\n=== Demo 2: Retry Logic with Eventual Success ===")
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123:runtime/retry-demo-agent"
        context = self.error_handler.create_error_context(
            agent_arn=agent_arn,
            operation="demo_retry_success",
            user_id="demo_user"
        )
        
        call_count = 0
        
        async def eventually_successful_call():
            nonlocal call_count
            call_count += 1
            print(f"  Attempt {call_count}")
            
            if call_count < 2:
                raise AgentInvocationError(
                    "Temporary service unavailable",
                    agent_arn,
                    status_code=503,
                    retryable=True
                )
            
            return {"output": "Success after retry", "restaurants": []}
        
        try:
            result = await self.error_handler.execute_with_protection(
                eventually_successful_call, context
            )
            print(f"✅ Success after {call_count} attempts: {result['output']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def demo_circuit_breaker_opening(self):
        """Demonstrate circuit breaker opening after repeated failures."""
        print("\n=== Demo 3: Circuit Breaker Opening ===")
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123:runtime/failing-agent"
        
        async def always_failing_call():
            raise AgentInvocationError(
                "Agent is down for maintenance",
                agent_arn,
                status_code=503,
                retryable=True
            )
        
        # Make multiple failing calls to trigger circuit breaker
        for i in range(4):
            context = self.error_handler.create_error_context(
                agent_arn=agent_arn,
                operation=f"demo_circuit_breaker_call_{i+1}",
                user_id="demo_user"
            )
            
            try:
                await self.error_handler.execute_with_protection(
                    always_failing_call, context
                )
            except CircuitBreakerOpenError as e:
                print(f"🔴 Circuit breaker opened: {e}")
                break
            except Exception as e:
                print(f"  Call {i+1} failed: {type(e).__name__}")
        
        # Show circuit breaker stats
        stats = self.error_handler.get_circuit_breaker_stats(agent_arn)
        print(f"Circuit breaker state: {stats['state']}")
        print(f"Failure count: {stats['failure_count']}")
    
    async def demo_fallback_responses(self):
        """Demonstrate fallback response generation."""
        print("\n=== Demo 4: Fallback Response Generation ===")
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123:runtime/restaurant-search"
        context = self.error_handler.create_error_context(
            agent_arn=agent_arn,
            operation="search_restaurants",
            user_id="demo_user",
            session_id="demo_session"
        )
        
        # Create fallback for restaurant search
        fallback = self.error_handler.create_fallback_response(
            "search_restaurants", context
        )
        
        print("🔄 Fallback response generated:")
        print(f"  Message: {fallback['message']}")
        print(f"  Suggestions: {len(fallback['data']['suggestions'])} districts")
        print(f"  Alternative actions: {len(fallback['alternative_actions'])} options")
        
        # Create fallback with partial data
        partial_data = {"partial_restaurants": [{"name": "Partial Restaurant"}]}
        fallback_with_data = self.error_handler.create_fallback_response(
            "search_restaurants", context, partial_data
        )
        
        print("\n🔄 Fallback with partial data:")
        print(f"  Has partial data: {'partial_data' in fallback_with_data}")
        print(f"  Message includes 'limited information': {'limited information' in fallback_with_data['message']}")
    
    async def demo_different_error_types(self):
        """Demonstrate handling of different error types."""
        print("\n=== Demo 5: Different Error Types ===")
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123:runtime/error-demo-agent"
        
        error_scenarios = [
            ("Authentication Error", AuthenticationError("JWT token expired", "JWT")),
            ("Timeout Error", AgentTimeoutError("Request timed out", 30, agent_arn)),
            ("Agent Unavailable", AgentUnavailableError("Agent is down", agent_arn, 60)),
            ("Generic Error", Exception("Unexpected error occurred"))
        ]
        
        for scenario_name, error in error_scenarios:
            context = self.error_handler.create_error_context(
                agent_arn=agent_arn,
                operation=f"demo_{scenario_name.lower().replace(' ', '_')}",
                user_id="demo_user"
            )
            
            async def error_call():
                raise error
            
            try:
                await self.error_handler.execute_with_protection(error_call, context)
            except Exception as e:
                error_type = type(e).__name__
                retryable = getattr(e, 'retryable', False) if hasattr(e, 'retryable') else False
                print(f"  {scenario_name}: {error_type} (retryable: {retryable})")
    
    async def demo_circuit_breaker_recovery(self):
        """Demonstrate circuit breaker recovery after timeout."""
        print("\n=== Demo 6: Circuit Breaker Recovery ===")
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123:runtime/recovery-agent"
        
        # First, open the circuit breaker
        async def failing_call():
            raise AgentInvocationError("Service failure", agent_arn, 500)
        
        print("Opening circuit breaker...")
        for i in range(3):
            context = self.error_handler.create_error_context(
                agent_arn=agent_arn,
                operation=f"failing_call_{i+1}",
                user_id="demo_user"
            )
            
            try:
                await self.error_handler.execute_with_protection(failing_call, context)
            except Exception:
                pass
        
        stats = self.error_handler.get_circuit_breaker_stats(agent_arn)
        print(f"Circuit breaker state: {stats['state']}")
        
        # Reset circuit breaker for demo purposes
        print("Resetting circuit breaker...")
        self.error_handler.reset_circuit_breaker(agent_arn)
        
        stats = self.error_handler.get_circuit_breaker_stats(agent_arn)
        print(f"Circuit breaker state after reset: {stats['state']}")
        
        # Now demonstrate successful call
        async def successful_call():
            return {"output": "Service recovered", "status": "healthy"}
        
        context = self.error_handler.create_error_context(
            agent_arn=agent_arn,
            operation="recovery_test",
            user_id="demo_user"
        )
        
        try:
            result = await self.error_handler.execute_with_protection(successful_call, context)
            print(f"✅ Recovery successful: {result['output']}")
        except Exception as e:
            print(f"❌ Recovery failed: {e}")
    
    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring capabilities."""
        print("\n=== Demo 7: Performance Monitoring ===")
        
        agent_arn = "arn:aws:bedrock-agentcore:us-east-1:123:runtime/perf-agent"
        
        # Simulate various call patterns
        scenarios = [
            ("fast_call", 0.1, True),
            ("slow_call", 1.0, True),
            ("failing_call", 0.5, False),
            ("timeout_call", 2.0, False)
        ]
        
        for scenario_name, delay, should_succeed in scenarios:
            context = self.error_handler.create_error_context(
                agent_arn=agent_arn,
                operation=scenario_name,
                user_id="demo_user"
            )
            
            async def timed_call():
                await asyncio.sleep(delay)
                if should_succeed:
                    return {"output": f"{scenario_name} completed"}
                else:
                    raise AgentInvocationError(f"{scenario_name} failed", agent_arn)
            
            start_time = time.time()
            try:
                result = await self.error_handler.execute_with_protection(timed_call, context)
                duration = time.time() - start_time
                print(f"  ✅ {scenario_name}: {duration:.2f}s")
            except Exception as e:
                duration = time.time() - start_time
                print(f"  ❌ {scenario_name}: {duration:.2f}s - {type(e).__name__}")
        
        # Show circuit breaker stats
        stats = self.error_handler.get_circuit_breaker_stats(agent_arn)
        if stats.get('state') != 'not_initialized':
            print(f"\nAgent stats:")
            print(f"  State: {stats['state']}")
            print(f"  Failures: {stats['failure_count']}")
            print(f"  Successes: {stats['success_count']}")
    
    async def run_all_demos(self):
        """Run all demonstration scenarios."""
        print("🚀 AgentCore Error Handling System Demo")
        print("=" * 50)
        
        demos = [
            self.demo_successful_call,
            self.demo_retry_with_eventual_success,
            self.demo_circuit_breaker_opening,
            self.demo_fallback_responses,
            self.demo_different_error_types,
            self.demo_circuit_breaker_recovery,
            self.demo_performance_monitoring
        ]
        
        for demo in demos:
            try:
                await demo()
                await asyncio.sleep(0.5)  # Brief pause between demos
            except Exception as e:
                print(f"❌ Demo error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ All demos completed!")


async def main():
    """Run the error handling demonstration."""
    demo = ErrorHandlingDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    asyncio.run(main())