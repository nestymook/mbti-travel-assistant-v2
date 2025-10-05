"""
Enhanced Circuit Breaker Example

This example demonstrates how to use the Enhanced Circuit Breaker with dual path support
for intelligent traffic routing and path availability determination.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_circuit_breaker import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig,
    PathType
)
from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    ServerStatus,
    EnhancedCircuitBreakerState
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedCircuitBreakerDemo:
    """Demonstration of Enhanced Circuit Breaker functionality."""
    
    def __init__(self):
        """Initialize the demo with circuit breaker configuration."""
        # Create circuit breaker configuration
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=30,
            mcp_failure_threshold=2,
            rest_failure_threshold=2,
            require_both_paths_healthy=False,
            recovery_timeout_seconds=15,
            half_open_max_requests=3,
            failure_history_window_minutes=5
        )
        
        # Initialize circuit breaker
        self.circuit_breaker = EnhancedCircuitBreaker(self.config)
        
        # Test servers
        self.servers = [
            "restaurant-search-mcp",
            "restaurant-reasoning-mcp",
            "mbti-travel-assistant"
        ]
    
    async def demonstrate_basic_functionality(self):
        """Demonstrate basic circuit breaker functionality."""
        logger.info("=== Basic Circuit Breaker Functionality ===")
        
        server_name = self.servers[0]
        
        # 1. Test healthy server
        logger.info(f"Testing healthy server: {server_name}")
        
        healthy_result = self._create_healthy_dual_result(server_name)
        state = await self.circuit_breaker.evaluate_circuit_state(server_name, healthy_result)
        
        logger.info(f"Healthy server state: {state}")
        
        # Check traffic allowance
        mcp_allowed = await self.circuit_breaker.should_allow_mcp_traffic(server_name)
        rest_allowed = await self.circuit_breaker.should_allow_rest_traffic(server_name)
        available_paths = await self.circuit_breaker.get_available_paths(server_name)
        
        logger.info(f"MCP traffic allowed: {mcp_allowed}")
        logger.info(f"REST traffic allowed: {rest_allowed}")
        logger.info(f"Available paths: {available_paths}")
        
        # 2. Test failing server
        logger.info(f"\nTesting failing server: {server_name}")
        
        failing_result = self._create_failing_dual_result(server_name)
        
        # Trigger multiple failures
        for i in range(3):
            state = await self.circuit_breaker.evaluate_circuit_state(server_name, failing_result)
            logger.info(f"Failure {i+1} - Circuit state: {state}")
        
        # Check traffic allowance after failures
        mcp_allowed = await self.circuit_breaker.should_allow_mcp_traffic(server_name)
        rest_allowed = await self.circuit_breaker.should_allow_rest_traffic(server_name)
        available_paths = await self.circuit_breaker.get_available_paths(server_name)
        
        logger.info(f"After failures - MCP traffic allowed: {mcp_allowed}")
        logger.info(f"After failures - REST traffic allowed: {rest_allowed}")
        logger.info(f"After failures - Available paths: {available_paths}")
    
    async def demonstrate_dual_path_scenarios(self):
        """Demonstrate dual path monitoring scenarios."""
        logger.info("\n=== Dual Path Monitoring Scenarios ===")
        
        server_name = self.servers[1]
        
        # Scenario 1: MCP fails, REST succeeds
        logger.info(f"Scenario 1: MCP fails, REST succeeds - {server_name}")
        
        mixed_result_1 = self._create_mixed_dual_result(server_name, mcp_success=False, rest_success=True)
        
        for i in range(3):
            state = await self.circuit_breaker.evaluate_circuit_state(server_name, mixed_result_1)
            logger.info(f"Mixed result 1 - iteration {i+1}: {state}")
        
        available_paths = await self.circuit_breaker.get_available_paths(server_name)
        logger.info(f"Available paths after MCP failures: {available_paths}")
        
        # Reset for next scenario
        await self.circuit_breaker.reset_circuit_breaker(server_name)
        
        # Scenario 2: MCP succeeds, REST fails
        logger.info(f"\nScenario 2: MCP succeeds, REST fails - {server_name}")
        
        mixed_result_2 = self._create_mixed_dual_result(server_name, mcp_success=True, rest_success=False)
        
        for i in range(3):
            state = await self.circuit_breaker.evaluate_circuit_state(server_name, mixed_result_2)
            logger.info(f"Mixed result 2 - iteration {i+1}: {state}")
        
        available_paths = await self.circuit_breaker.get_available_paths(server_name)
        logger.info(f"Available paths after REST failures: {available_paths}")
    
    async def demonstrate_recovery_scenarios(self):
        """Demonstrate circuit breaker recovery scenarios."""
        logger.info("\n=== Recovery Scenarios ===")
        
        server_name = self.servers[2]
        
        # 1. Open circuit with failures
        logger.info(f"Opening circuit for {server_name}")
        
        failing_result = self._create_failing_dual_result(server_name)
        
        for i in range(3):
            await self.circuit_breaker.evaluate_circuit_state(server_name, failing_result)
        
        state = await self.circuit_breaker.get_circuit_breaker_state(server_name)
        logger.info(f"Circuit opened - MCP state: {state['mcp_path']['state']}")
        logger.info(f"Circuit opened - REST state: {state['rest_path']['state']}")
        
        # 2. Simulate timeout to half-open
        logger.info("\nSimulating timeout transition to half-open")
        
        # Manually adjust opened time to simulate timeout
        server_states = self.circuit_breaker.server_states[server_name]
        for path_state in server_states.values():
            if path_state.opened_time:
                path_state.opened_time = datetime.now() - timedelta(seconds=35)
        
        # Trigger state check
        await self.circuit_breaker.evaluate_circuit_state(server_name, failing_result)
        
        state = await self.circuit_breaker.get_circuit_breaker_state(server_name)
        logger.info(f"After timeout - MCP state: {state['mcp_path']['state']}")
        logger.info(f"After timeout - REST state: {state['rest_path']['state']}")
        
        # 3. Recovery with successful requests
        logger.info("\nRecovering with successful requests")
        
        healthy_result = self._create_healthy_dual_result(server_name)
        
        for i in range(3):
            state_enum = await self.circuit_breaker.evaluate_circuit_state(server_name, healthy_result)
            logger.info(f"Recovery attempt {i+1}: {state_enum}")
        
        final_state = await self.circuit_breaker.get_circuit_breaker_state(server_name)
        logger.info(f"Final recovery - MCP state: {final_state['mcp_path']['state']}")
        logger.info(f"Final recovery - REST state: {final_state['rest_path']['state']}")
    
    async def demonstrate_traffic_routing_decisions(self):
        """Demonstrate intelligent traffic routing decisions."""
        logger.info("\n=== Traffic Routing Decisions ===")
        
        # Create different server scenarios
        scenarios = [
            ("healthy-server", "both_healthy"),
            ("mcp-only-server", "mcp_only"),
            ("rest-only-server", "rest_only"),
            ("unhealthy-server", "both_failed")
        ]
        
        for server_name, scenario_type in scenarios:
            logger.info(f"\nScenario: {scenario_type} ({server_name})")
            
            if scenario_type == "both_healthy":
                result = self._create_healthy_dual_result(server_name)
            elif scenario_type == "mcp_only":
                result = self._create_mixed_dual_result(server_name, mcp_success=True, rest_success=False)
                # Trigger REST failures
                for _ in range(3):
                    await self.circuit_breaker.evaluate_circuit_state(server_name, result)
            elif scenario_type == "rest_only":
                result = self._create_mixed_dual_result(server_name, mcp_success=False, rest_success=True)
                # Trigger MCP failures
                for _ in range(3):
                    await self.circuit_breaker.evaluate_circuit_state(server_name, result)
            else:  # both_failed
                result = self._create_failing_dual_result(server_name)
                # Trigger both failures
                for _ in range(3):
                    await self.circuit_breaker.evaluate_circuit_state(server_name, result)
            
            # Get routing decisions
            mcp_allowed = await self.circuit_breaker.should_allow_mcp_traffic(server_name)
            rest_allowed = await self.circuit_breaker.should_allow_rest_traffic(server_name)
            available_paths = await self.circuit_breaker.get_available_paths(server_name)
            
            logger.info(f"  MCP traffic allowed: {mcp_allowed}")
            logger.info(f"  REST traffic allowed: {rest_allowed}")
            logger.info(f"  Available paths: {available_paths}")
            
            # Routing recommendation
            if "both" in available_paths:
                recommendation = "Route to both MCP and REST for redundancy"
            elif "mcp" in available_paths:
                recommendation = "Route to MCP only, REST is unavailable"
            elif "rest" in available_paths:
                recommendation = "Route to REST only, MCP is unavailable"
            else:
                recommendation = "No paths available, use fallback or cached data"
            
            logger.info(f"  Routing recommendation: {recommendation}")
    
    async def demonstrate_metrics_and_monitoring(self):
        """Demonstrate metrics collection and monitoring."""
        logger.info("\n=== Metrics and Monitoring ===")
        
        # Create various server states
        test_servers = ["server-1", "server-2", "server-3", "server-4"]
        
        # Server 1: Healthy
        healthy_result = self._create_healthy_dual_result(test_servers[0])
        await self.circuit_breaker.evaluate_circuit_state(test_servers[0], healthy_result)
        
        # Server 2: MCP failed
        mcp_failed_result = self._create_mixed_dual_result(test_servers[1], mcp_success=False, rest_success=True)
        for _ in range(3):
            await self.circuit_breaker.evaluate_circuit_state(test_servers[1], mcp_failed_result)
        
        # Server 3: REST failed
        rest_failed_result = self._create_mixed_dual_result(test_servers[2], mcp_success=True, rest_success=False)
        for _ in range(3):
            await self.circuit_breaker.evaluate_circuit_state(test_servers[2], rest_failed_result)
        
        # Server 4: Both failed
        both_failed_result = self._create_failing_dual_result(test_servers[3])
        for _ in range(3):
            await self.circuit_breaker.evaluate_circuit_state(test_servers[3], both_failed_result)
        
        # Get overall metrics
        metrics = await self.circuit_breaker.get_circuit_breaker_metrics()
        
        logger.info("Overall Circuit Breaker Metrics:")
        logger.info(f"  Total servers: {metrics['total_servers']}")
        logger.info(f"  MCP circuits open: {metrics['mcp_circuits_open']}")
        logger.info(f"  REST circuits open: {metrics['rest_circuits_open']}")
        logger.info(f"  Both paths available: {metrics['both_paths_available']}")
        logger.info(f"  No paths available: {metrics['no_paths_available']}")
        logger.info(f"  MCP availability rate: {metrics['mcp_availability_rate']:.2%}")
        logger.info(f"  REST availability rate: {metrics['rest_availability_rate']:.2%}")
        logger.info(f"  Dual path availability rate: {metrics['dual_path_availability_rate']:.2%}")
        
        # Get detailed state for each server
        logger.info("\nDetailed Server States:")
        for server_name in test_servers:
            state = await self.circuit_breaker.get_circuit_breaker_state(server_name)
            logger.info(f"  {server_name}:")
            logger.info(f"    Overall state: {state['overall_state']}")
            logger.info(f"    MCP state: {state['mcp_path']['state']}")
            logger.info(f"    REST state: {state['rest_path']['state']}")
            logger.info(f"    Available paths: {state['available_paths']}")
    
    async def demonstrate_configuration_scenarios(self):
        """Demonstrate different configuration scenarios."""
        logger.info("\n=== Configuration Scenarios ===")
        
        # Scenario 1: Strict mode (require both paths healthy)
        logger.info("Scenario 1: Strict mode (require_both_paths_healthy=True)")
        
        strict_config = CircuitBreakerConfig(
            failure_threshold=2,
            mcp_failure_threshold=1,
            rest_failure_threshold=1,
            require_both_paths_healthy=True
        )
        
        strict_cb = EnhancedCircuitBreaker(strict_config)
        server_name = "strict-test-server"
        
        # Test mixed result in strict mode
        mixed_result = self._create_mixed_dual_result(server_name, mcp_success=True, rest_success=False)
        state = await strict_cb.evaluate_circuit_state(server_name, mixed_result)
        
        logger.info(f"  Mixed result in strict mode: {state}")
        available_paths = await strict_cb.get_available_paths(server_name)
        logger.info(f"  Available paths in strict mode: {available_paths}")
        
        # Scenario 2: Permissive mode (default)
        logger.info("\nScenario 2: Permissive mode (require_both_paths_healthy=False)")
        
        permissive_cb = EnhancedCircuitBreaker(self.config)
        
        # Test same mixed result in permissive mode
        state = await permissive_cb.evaluate_circuit_state(server_name, mixed_result)
        
        logger.info(f"  Mixed result in permissive mode: {state}")
        available_paths = await permissive_cb.get_available_paths(server_name)
        logger.info(f"  Available paths in permissive mode: {available_paths}")
    
    def _create_healthy_dual_result(self, server_name: str) -> DualHealthCheckResult:
        """Create a healthy dual health check result."""
        timestamp = datetime.now()
        
        mcp_result = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            success=True,
            response_time_ms=150.0,
            tools_count=5
        )
        
        rest_result = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            success=True,
            response_time_ms=120.0,
            status_code=200
        )
        
        return DualHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=mcp_result,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=5,
            rest_result=rest_result,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            available_paths=["mcp", "rest", "both"]
        )
    
    def _create_failing_dual_result(self, server_name: str) -> DualHealthCheckResult:
        """Create a failing dual health check result."""
        timestamp = datetime.now()
        
        mcp_result = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            success=False,
            response_time_ms=5000.0,
            connection_error="Connection timeout"
        )
        
        rest_result = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            success=False,
            response_time_ms=5000.0,
            status_code=500,
            http_error="Internal server error"
        )
        
        return DualHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=mcp_result,
            mcp_success=False,
            mcp_response_time_ms=5000.0,
            mcp_error_message="Connection timeout",
            rest_result=rest_result,
            rest_success=False,
            rest_response_time_ms=5000.0,
            rest_status_code=500,
            rest_error_message="Internal server error",
            available_paths=["none"]
        )
    
    def _create_mixed_dual_result(
        self, 
        server_name: str, 
        mcp_success: bool, 
        rest_success: bool
    ) -> DualHealthCheckResult:
        """Create a mixed dual health check result."""
        timestamp = datetime.now()
        
        if mcp_success:
            mcp_result = MCPHealthCheckResult(
                server_name=server_name,
                timestamp=timestamp,
                success=True,
                response_time_ms=150.0,
                tools_count=5
            )
            mcp_error_message = None
        else:
            mcp_result = MCPHealthCheckResult(
                server_name=server_name,
                timestamp=timestamp,
                success=False,
                response_time_ms=5000.0,
                connection_error="MCP connection failed"
            )
            mcp_error_message = "MCP connection failed"
        
        if rest_success:
            rest_result = RESTHealthCheckResult(
                server_name=server_name,
                timestamp=timestamp,
                success=True,
                response_time_ms=120.0,
                status_code=200
            )
            rest_error_message = None
        else:
            rest_result = RESTHealthCheckResult(
                server_name=server_name,
                timestamp=timestamp,
                success=False,
                response_time_ms=5000.0,
                status_code=503,
                http_error="Service unavailable"
            )
            rest_error_message = "Service unavailable"
        
        # Determine overall status
        if mcp_success and rest_success:
            overall_status = ServerStatus.HEALTHY
            overall_success = True
        elif mcp_success or rest_success:
            overall_status = ServerStatus.DEGRADED
            overall_success = False
        else:
            overall_status = ServerStatus.UNHEALTHY
            overall_success = False
        
        return DualHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            overall_status=overall_status,
            overall_success=overall_success,
            mcp_result=mcp_result,
            mcp_success=mcp_success,
            mcp_response_time_ms=mcp_result.response_time_ms,
            mcp_tools_count=mcp_result.tools_count,
            mcp_error_message=mcp_error_message,
            rest_result=rest_result,
            rest_success=rest_success,
            rest_response_time_ms=rest_result.response_time_ms,
            rest_status_code=rest_result.status_code,
            rest_error_message=rest_error_message
        )
    
    async def run_all_demonstrations(self):
        """Run all circuit breaker demonstrations."""
        logger.info("Starting Enhanced Circuit Breaker Demonstrations")
        logger.info("=" * 60)
        
        try:
            await self.demonstrate_basic_functionality()
            await self.demonstrate_dual_path_scenarios()
            await self.demonstrate_recovery_scenarios()
            await self.demonstrate_traffic_routing_decisions()
            await self.demonstrate_metrics_and_monitoring()
            await self.demonstrate_configuration_scenarios()
            
            logger.info("\n" + "=" * 60)
            logger.info("All demonstrations completed successfully!")
            
        except Exception as e:
            logger.error(f"Demonstration failed: {e}")
            raise


async def main():
    """Main function to run the enhanced circuit breaker demo."""
    demo = EnhancedCircuitBreakerDemo()
    await demo.run_all_demonstrations()


if __name__ == "__main__":
    asyncio.run(main())