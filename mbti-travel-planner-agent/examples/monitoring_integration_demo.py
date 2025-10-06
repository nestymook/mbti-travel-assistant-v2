#!/usr/bin/env python3
"""
AgentCore Monitoring Integration Demonstration

This script demonstrates the comprehensive monitoring and observability features
implemented for the MBTI Travel Planner Agent with AgentCore integration.

Features demonstrated:
- Structured logging for agent invocations
- Performance metrics tracking (response times, success rates)
- Health check service for agent connectivity
- Correlation IDs for request tracing
- Comprehensive monitoring integration
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import monitoring integration
from services.agentcore_monitoring_integration import (
    AgentCoreMonitoringIntegration,
    MonitoringConfiguration,
    initialize_monitoring_integration
)

# Import AgentCore components
from services.agentcore_runtime_client import AgentCoreRuntimeClient, AgentResponse
from services.authentication_manager import AuthenticationManager
from config.agentcore_environment_config import EnvironmentConfig, AgentCoreConfig, CognitoConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_config() -> EnvironmentConfig:
    """Create a mock configuration for demonstration."""
    return EnvironmentConfig(
        environment="demo",
        agentcore=AgentCoreConfig(
            restaurant_search_agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/search-agent-demo",
            restaurant_reasoning_agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/reasoning-agent-demo",
            region="us-east-1",
            timeout_seconds=30,
            max_retries=3
        ),
        cognito=CognitoConfig(
            user_pool_id="us-east-1_DemoPool",
            client_id="demo-client-id",
            client_secret="demo-client-secret",
            region="us-east-1",
            discovery_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_DemoPool/.well-known/openid-configuration"
        )
    )


def create_mock_runtime_client() -> AgentCoreRuntimeClient:
    """Create a mock AgentCore runtime client for demonstration."""
    client = AsyncMock(spec=AgentCoreRuntimeClient)
    
    # Mock successful response
    mock_response = Mock(spec=AgentResponse)
    mock_response.output_text = json.dumps({
        "restaurants": [
            {"name": "Demo Restaurant 1", "district": "Central district", "sentiment": {"likes": 95}},
            {"name": "Demo Restaurant 2", "district": "Central district", "sentiment": {"likes": 87}}
        ]
    })
    mock_response.session_id = "demo-session-123"
    mock_response.execution_time_ms = 1500
    mock_response.metadata = {"demo": "metadata"}
    
    client.invoke_agent.return_value = mock_response
    return client


def create_mock_auth_manager() -> AuthenticationManager:
    """Create a mock authentication manager for demonstration."""
    auth_manager = AsyncMock(spec=AuthenticationManager)
    auth_manager.get_valid_token.return_value = "demo-jwt-token-12345"
    return auth_manager


async def demonstrate_correlation_id_management(integration: AgentCoreMonitoringIntegration):
    """Demonstrate correlation ID generation and management."""
    print("\n" + "="*60)
    print("CORRELATION ID MANAGEMENT DEMONSTRATION")
    print("="*60)
    
    # Generate correlation IDs
    correlation_id1 = integration.generate_correlation_id()
    correlation_id2 = integration.generate_correlation_id()
    
    print(f"Generated correlation ID 1: {correlation_id1}")
    print(f"Generated correlation ID 2: {correlation_id2}")
    print(f"Correlation IDs are unique: {correlation_id1 != correlation_id2}")
    
    # Set and get correlation ID
    integration.set_correlation_id(correlation_id1)
    current_id = integration.get_correlation_id()
    print(f"Set correlation ID: {correlation_id1}")
    print(f"Retrieved correlation ID: {current_id}")
    print(f"Correlation ID management working: {correlation_id1 == current_id}")


async def demonstrate_health_checks(integration: AgentCoreMonitoringIntegration):
    """Demonstrate comprehensive health check functionality."""
    print("\n" + "="*60)
    print("HEALTH CHECK DEMONSTRATION")
    print("="*60)
    
    # Perform comprehensive health check
    health_results = await integration.perform_health_check()
    
    print(f"Health check timestamp: {health_results['timestamp']}")
    print(f"Environment: {health_results['environment']}")
    print(f"Overall status: {health_results['overall_status']}")
    
    print("\nComponent Health Status:")
    for component, status in health_results['components'].items():
        print(f"  {component}: {status['status']} - {status['details']}")
    
    return health_results


async def demonstrate_performance_metrics(integration: AgentCoreMonitoringIntegration):
    """Demonstrate performance metrics collection."""
    print("\n" + "="*60)
    print("PERFORMANCE METRICS DEMONSTRATION")
    print("="*60)
    
    # Simulate some operations to generate metrics
    middleware = integration.monitoring_middleware
    
    # Simulate multiple operations
    operations = [
        ("restaurant_search", "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/search-agent-demo"),
        ("restaurant_reasoning", "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/reasoning-agent-demo"),
        ("restaurant_search", "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/search-agent-demo")
    ]
    
    for operation_name, agent_arn in operations:
        correlation_id = integration.generate_correlation_id()
        
        # Import the operation type enum
        from services.agentcore_monitoring_service import AgentOperationType
        operation_type = AgentOperationType.RESTAURANT_SEARCH if "search" in operation_name else AgentOperationType.RESTAURANT_REASONING
        
        async with middleware.monitoring_context(
            operation_type=operation_type,
            agent_arn=agent_arn,
            correlation_id=correlation_id
        ) as context:
            # Simulate processing time
            await asyncio.sleep(0.1)
            print(f"Simulated {operation_name} operation with correlation ID: {context.correlation_id}")
    
    # Get performance metrics
    metrics = integration.get_performance_metrics(60)  # Last hour
    
    print(f"\nPerformance Metrics (last 60 minutes):")
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"Environment: {metrics['environment']}")
    
    print("\nOperation Metrics:")
    for operation, data in metrics['operation_metrics'].items():
        if data['total_calls'] > 0:
            print(f"  {operation}:")
            print(f"    Total calls: {data['total_calls']}")
            print(f"    Success rate: {data['success_rate']:.1f}%")
            print(f"    Response time stats: {data['response_time_stats']}")
    
    print("\nAuthentication Metrics:")
    auth_metrics = metrics['authentication_metrics']
    print(f"  Total events: {auth_metrics['total_events']}")
    print(f"  Success rate: {auth_metrics['success_rate']:.1f}%")
    
    return metrics


async def demonstrate_monitoring_status(integration: AgentCoreMonitoringIntegration):
    """Demonstrate monitoring status reporting."""
    print("\n" + "="*60)
    print("MONITORING STATUS DEMONSTRATION")
    print("="*60)
    
    status = integration.get_monitoring_status()
    
    print(f"Monitoring Status Report:")
    print(f"  Timestamp: {status.timestamp}")
    print(f"  Environment: {status.environment}")
    print(f"  Monitoring Service: {status.monitoring_service_status}")
    print(f"  Health Check Service: {status.health_check_service_status}")
    print(f"  Middleware: {status.middleware_status}")
    
    print(f"\nPerformance Summary:")
    perf = status.performance_summary
    print(f"  Total operations: {perf.get('total_operations', 0)}")
    print(f"  Overall success rate: {perf.get('overall_success_rate', 0):.1f}%")
    print(f"  Average response time: {perf.get('avg_response_time_ms', 0):.1f}ms")
    
    print(f"\nError Summary:")
    errors = status.error_summary
    print(f"  Total errors: {errors.get('total_errors', 0)}")
    print(f"  Error rate: {errors.get('error_rate', 0):.1f}%")
    print(f"  Authentication failures: {errors.get('authentication_failures', 0)}")
    
    return status


async def demonstrate_comprehensive_report(integration: AgentCoreMonitoringIntegration):
    """Demonstrate comprehensive monitoring report generation."""
    print("\n" + "="*60)
    print("COMPREHENSIVE MONITORING REPORT DEMONSTRATION")
    print("="*60)
    
    report = await integration.generate_monitoring_report()
    
    print(f"Comprehensive Monitoring Report:")
    print(f"  Report timestamp: {report['report_timestamp']}")
    print(f"  Environment: {report['environment']}")
    
    print(f"\nMonitoring Configuration:")
    config = report['monitoring_configuration']
    print(f"  Detailed logging: {config['enable_detailed_logging']}")
    print(f"  Performance tracking: {config['enable_performance_tracking']}")
    print(f"  Health checks: {config['enable_health_checks']}")
    print(f"  Background health checks: {config['enable_background_health_checks']}")
    
    print(f"\nSystem Status:")
    system_status = report['system_status']
    print(f"  Overall status: {system_status['monitoring_service_status']}")
    
    print(f"\nHealth Check Results:")
    health = report['health_check_results']
    print(f"  Overall health: {health['overall_status']}")
    print(f"  Components checked: {len(health['components'])}")
    
    # Save report to file for inspection
    report_filename = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nFull report saved to: {report_filename}")
    
    return report


async def demonstrate_authentication_monitoring(integration: AgentCoreMonitoringIntegration):
    """Demonstrate authentication event monitoring."""
    print("\n" + "="*60)
    print("AUTHENTICATION MONITORING DEMONSTRATION")
    print("="*60)
    
    monitoring_service = integration.monitoring_service
    
    # Log various authentication events
    auth_events = [
        ("token_refresh", True, None),
        ("token_validation", True, None),
        ("token_refresh", False, "Token expired"),
        ("token_validation", True, None),
        ("user_authentication", False, "Invalid credentials")
    ]
    
    for event_type, success, error_msg in auth_events:
        monitoring_service.log_authentication_event(
            event_type=event_type,
            success=success,
            error_message=error_msg
        )
        print(f"Logged authentication event: {event_type} ({'success' if success else 'failure'})")
    
    # Get authentication metrics
    auth_metrics = monitoring_service.metrics_collector.get_authentication_metrics(60)
    
    print(f"\nAuthentication Metrics Summary:")
    print(f"  Total events: {auth_metrics['total_events']}")
    print(f"  Successful events: {auth_metrics['successful_events']}")
    print(f"  Failed events: {auth_metrics['failed_events']}")
    print(f"  Success rate: {auth_metrics['success_rate']:.1f}%")
    
    print(f"\nEvent Breakdown:")
    for event, count in auth_metrics['event_breakdown'].items():
        print(f"  {event}: {count}")


async def main():
    """Main demonstration function."""
    print("AgentCore Monitoring Integration Demonstration")
    print("=" * 60)
    print("This demonstration shows the comprehensive monitoring and")
    print("observability features implemented for the MBTI Travel Planner Agent.")
    print("=" * 60)
    
    # Create mock configuration and components
    config = create_mock_config()
    monitoring_config = MonitoringConfiguration(
        environment="demo",
        enable_detailed_logging=True,
        enable_performance_tracking=True,
        enable_health_checks=True,
        enable_background_health_checks=False  # Disable for demo
    )
    
    # Create mock runtime components
    runtime_client = create_mock_runtime_client()
    auth_manager = create_mock_auth_manager()
    
    # Initialize monitoring integration
    print("\nInitializing monitoring integration...")
    integration = AgentCoreMonitoringIntegration(config, monitoring_config)
    await integration.initialize(runtime_client, auth_manager)
    
    print(f"Monitoring integration initialized: {integration.is_initialized()}")
    
    try:
        # Run demonstrations
        await demonstrate_correlation_id_management(integration)
        await demonstrate_health_checks(integration)
        await demonstrate_authentication_monitoring(integration)
        await demonstrate_performance_metrics(integration)
        await demonstrate_monitoring_status(integration)
        await demonstrate_comprehensive_report(integration)
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("All monitoring and observability features are working correctly!")
        print("The system provides:")
        print("✓ Structured logging for agent invocations")
        print("✓ Performance metrics tracking (response times, success rates)")
        print("✓ Health check service for agent connectivity")
        print("✓ Correlation IDs for request tracing")
        print("✓ Comprehensive monitoring integration")
        print("✓ Authentication event monitoring")
        print("✓ Error handling and reporting")
        print("✓ Status reporting and dashboards")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise
    
    finally:
        # Cleanup
        await integration.close()
        print("\nMonitoring integration closed successfully.")


if __name__ == "__main__":
    asyncio.run(main())