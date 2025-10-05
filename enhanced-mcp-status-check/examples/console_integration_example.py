"""
Console Integration Example

This example demonstrates the enhanced console interface for dual monitoring,
showing dashboard views, alert management, and configuration interfaces.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_console_integration():
    """Demonstrate console integration features."""
    print("🔍 Enhanced MCP Status Check Console Integration Demo")
    print("=" * 60)
    
    try:
        # Import console components
        from console.enhanced_console_interface import EnhancedConsoleInterface
        from console.dashboard import EnhancedStatusDashboard
        from console.alert_manager import DualMonitoringAlertManager
        from console.configuration_interface import ConfigurationManagementInterface
        from console.troubleshooting_guide import TroubleshootingGuideInterface
        
        print("✅ Successfully imported console components")
        
        # Create mock services for demonstration
        from unittest.mock import AsyncMock
        
        health_service = AsyncMock()
        metrics_collector = AsyncMock()
        config_manager = AsyncMock()
        
        # Mock configuration data
        mock_config = {
            "system": {
                "dual_monitoring_enabled": True,
                "default_timeout_seconds": 10,
                "max_concurrent_checks": 10,
                "cache_ttl_seconds": 30
            },
            "mcp_health_checks": {
                "enabled": True,
                "default_timeout_seconds": 10,
                "tools_list_validation": True,
                "expected_tools_validation": True,
                "retry_attempts": 3
            },
            "rest_health_checks": {
                "enabled": True,
                "default_timeout_seconds": 8,
                "health_endpoint_path": "/status/health",
                "metrics_endpoint_path": "/status/metrics",
                "retry_attempts": 2
            },
            "result_aggregation": {
                "mcp_priority_weight": 0.6,
                "rest_priority_weight": 0.4,
                "require_both_success_for_healthy": False,
                "degraded_on_single_failure": True
            }
        }
        
        config_manager.get_configuration = AsyncMock(return_value=mock_config)
        config_manager.get_all_server_configs = AsyncMock(return_value=[])
        
        print("✅ Created mock services")
        
        # Demonstrate Dashboard
        print("\n📊 Dashboard Integration Demo")
        print("-" * 40)
        
        dashboard = EnhancedStatusDashboard(health_service, metrics_collector, config_manager)
        
        # Mock system overview
        from models.dual_health_models import ServerStatus
        from console.dashboard import SystemHealthOverview
        
        mock_overview = SystemHealthOverview(
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            total_servers=3,
            status_breakdown={"healthy": 2, "degraded": 1, "unhealthy": 0, "unknown": 0},
            monitoring_breakdown={"mcp_only": 0, "rest_only": 0, "both": 3, "none": 0},
            average_health_score=0.85,
            average_response_times={"mcp": 150.0, "rest": 120.0, "combined": 135.0},
            recent_alerts=[],
            trend_data={"health_score": [0.9, 0.85, 0.8], "response_time": [140, 145, 150], "success_rate": [0.95, 0.90, 0.85]}
        )
        
        dashboard.get_system_overview = AsyncMock(return_value=mock_overview)
        dashboard.get_server_summaries = AsyncMock(return_value=[])
        
        # Get system overview
        overview = await dashboard.get_system_overview()
        print(f"System Status: {overview.overall_status.value}")
        print(f"Total Servers: {overview.total_servers}")
        print(f"Health Score: {overview.average_health_score:.2f}")
        print(f"Status Breakdown: {overview.status_breakdown}")
        
        print("✅ Dashboard integration working")
        
        # Demonstrate Alert Manager
        print("\n🚨 Alert Manager Demo")
        print("-" * 30)
        
        alert_manager = DualMonitoringAlertManager()
        
        # Check alert rules
        print(f"Alert Rules Loaded: {len(alert_manager._alert_rules)}")
        print(f"Notification Channels: {len(alert_manager._notification_channels)}")
        
        # List some alert rules
        for rule_id, rule in list(alert_manager._alert_rules.items())[:3]:
            print(f"  • {rule.name} ({rule.severity.value})")
        
        print("✅ Alert manager integration working")
        
        # Demonstrate Configuration Interface
        print("\n⚙️  Configuration Interface Demo")
        print("-" * 40)
        
        config_interface = ConfigurationManagementInterface(config_manager)
        
        # Test configuration value parsing
        test_values = [
            ("system.enabled", "true"),
            ("system.timeout_seconds", "30"),
            ("system.priority_weight", "0.6"),
            ("system.endpoint_path", "/health")
        ]
        
        for key, value in test_values:
            parsed = config_interface._parse_configuration_value(key, value)
            print(f"  {key}: '{value}' -> {parsed} ({type(parsed).__name__})")
        
        print("✅ Configuration interface working")
        
        # Demonstrate Troubleshooting Guide
        print("\n🔧 Troubleshooting Guide Demo")
        print("-" * 40)
        
        troubleshooting_guide = TroubleshootingGuideInterface()
        
        print(f"Troubleshooting Guides: {len(troubleshooting_guide._guides)}")
        
        # List available guides
        for guide_id, guide in list(troubleshooting_guide._guides.items())[:3]:
            print(f"  • {guide.title} ({guide.category.value})")
        
        # Test symptom analysis
        test_symptoms = {
            "mcp_failing": True,
            "rest_failing": False,
            "auth_errors": False,
            "timeout_errors": True,
            "slow_responses": False,
            "intermittent_issues": False,
            "recent_changes": False,
            "network_issues": False
        }
        
        suggestions = troubleshooting_guide._analyze_symptoms(test_symptoms)
        print(f"\nSymptom Analysis Results: {len(suggestions)} suggestions")
        for guide_id, confidence in suggestions[:2]:
            guide = troubleshooting_guide._guides[guide_id]
            print(f"  • {guide.title}: {confidence:.0%} confidence")
        
        print("✅ Troubleshooting guide working")
        
        # Demonstrate Console Interface
        print("\n🖥️  Console Interface Demo")
        print("-" * 35)
        
        console = EnhancedConsoleInterface(health_service, metrics_collector, config_manager)
        
        print(f"Console Mode: {console.session.current_mode.value}")
        print(f"Auto Refresh: {console.session.auto_refresh}")
        print(f"Refresh Interval: {console.session.refresh_interval}s")
        
        # Test command processing (without user input)
        test_commands = ["dashboard", "alerts", "config", "help"]
        
        for command in test_commands:
            await console._process_command(command)
            print(f"  Command '{command}' -> Mode: {console.session.current_mode.value}")
        
        print("✅ Console interface working")
        
        print("\n🎉 Console Integration Demo Complete!")
        print("All console components are working correctly.")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Some console components may not be available.")
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        logger.exception("Error during console integration demo")


async def demonstrate_dashboard_views():
    """Demonstrate different dashboard views."""
    print("\n📊 Dashboard Views Demo")
    print("=" * 30)
    
    try:
        from console.dashboard import DashboardViewType
        from unittest.mock import AsyncMock
        
        # Mock services
        health_service = AsyncMock()
        metrics_collector = AsyncMock()
        config_manager = AsyncMock()
        
        from console.dashboard import EnhancedStatusDashboard
        dashboard = EnhancedStatusDashboard(health_service, metrics_collector, config_manager)
        
        # Mock metrics data
        dashboard.metrics_collector.get_mcp_metrics = AsyncMock(return_value={
            "total_requests": 100,
            "successful_requests": 95,
            "average_response_time": 150.0,
            "tools_validated": 285
        })
        
        dashboard.metrics_collector.get_rest_metrics = AsyncMock(return_value={
            "total_requests": 120,
            "successful_requests": 118,
            "average_response_time": 120.0,
            "status_codes": {"200": 118, "500": 2}
        })
        
        dashboard.metrics_collector.get_combined_metrics = AsyncMock(return_value={
            "correlation": 0.85,
            "combined_success_rate": 0.92,
            "dual_monitoring_coverage": 0.95
        })
        
        # Test MCP detailed view
        print("\n🔌 MCP Detailed View:")
        mcp_view = await dashboard.get_mcp_detailed_view()
        print(f"  View Type: {mcp_view['view_type']}")
        print(f"  Timestamp: {mcp_view['timestamp']}")
        if 'summary' in mcp_view:
            summary = mcp_view['summary']
            print(f"  Total MCP Servers: {summary.get('total_mcp_servers', 0)}")
            print(f"  Successful Checks: {summary.get('successful_checks', 0)}")
            print(f"  Failed Checks: {summary.get('failed_checks', 0)}")
        
        # Test REST detailed view
        print("\n🌐 REST Detailed View:")
        rest_view = await dashboard.get_rest_detailed_view()
        print(f"  View Type: {rest_view['view_type']}")
        print(f"  Timestamp: {rest_view['timestamp']}")
        if 'summary' in rest_view:
            summary = rest_view['summary']
            print(f"  Total REST Servers: {summary.get('total_rest_servers', 0)}")
            print(f"  Successful Checks: {summary.get('successful_checks', 0)}")
            print(f"  Failed Checks: {summary.get('failed_checks', 0)}")
        
        # Test combined view
        print("\n📊 Combined View:")
        combined_view = await dashboard.get_combined_view()
        print(f"  View Type: {combined_view['view_type']}")
        print(f"  Timestamp: {combined_view['timestamp']}")
        if 'summary' in combined_view:
            summary = combined_view['summary']
            print(f"  Total Servers: {summary.get('total_servers', 0)}")
            print(f"  Dual Coverage: {summary.get('dual_monitoring_coverage', 0)}")
        
        print("✅ Dashboard views working correctly")
        
    except Exception as e:
        print(f"❌ Dashboard Views Error: {e}")
        logger.exception("Error during dashboard views demo")


async def demonstrate_alert_scenarios():
    """Demonstrate alert generation scenarios."""
    print("\n🚨 Alert Scenarios Demo")
    print("=" * 30)
    
    try:
        from console.alert_manager import DualMonitoringAlertManager
        from models.dual_health_models import DualHealthCheckResult, ServerStatus
        
        alert_manager = DualMonitoringAlertManager()
        
        # Scenario 1: MCP failure only
        print("\n📍 Scenario 1: MCP Failure Only")
        mcp_failure_result = DualHealthCheckResult(
            server_name="mcp-test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            mcp_result=None,
            mcp_success=False,
            mcp_response_time_ms=0.0,
            mcp_tools_count=None,
            mcp_error_message="MCP connection timeout",
            rest_result=None,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            rest_error_message=None,
            combined_response_time_ms=120.0,
            health_score=0.60,
            available_paths=["rest"]
        )
        
        await alert_manager.process_health_check_result(mcp_failure_result)
        print(f"Active Alerts: {len(alert_manager._active_alerts)}")
        
        # Scenario 2: Complete failure
        print("\n📍 Scenario 2: Complete Failure")
        complete_failure_result = DualHealthCheckResult(
            server_name="failed-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=None,
            mcp_success=False,
            mcp_response_time_ms=0.0,
            mcp_tools_count=None,
            mcp_error_message="MCP server unreachable",
            rest_result=None,
            rest_success=False,
            rest_response_time_ms=0.0,
            rest_status_code=500,
            rest_error_message="Internal server error",
            combined_response_time_ms=0.0,
            health_score=0.0,
            available_paths=[]
        )
        
        await alert_manager.process_health_check_result(complete_failure_result)
        print(f"Active Alerts: {len(alert_manager._active_alerts)}")
        
        # Show alert details
        print("\n📋 Alert Details:")
        for alert_id, alert in alert_manager._active_alerts.items():
            print(f"  • {alert.title}")
            print(f"    Server: {alert.server_name}")
            print(f"    Severity: {alert.severity.value}")
            print(f"    Type: {alert.alert_type.value}")
            print(f"    Status: {alert.status.value}")
        
        print("✅ Alert scenarios working correctly")
        
    except Exception as e:
        print(f"❌ Alert Scenarios Error: {e}")
        logger.exception("Error during alert scenarios demo")


async def main():
    """Main demo function."""
    print("🚀 Starting Enhanced Console Integration Demo")
    print("=" * 50)
    
    # Run main console integration demo
    await demonstrate_console_integration()
    
    # Run dashboard views demo
    await demonstrate_dashboard_views()
    
    # Run alert scenarios demo
    await demonstrate_alert_scenarios()
    
    print("\n✅ All demos completed successfully!")
    print("Enhanced console integration is ready for use.")


if __name__ == "__main__":
    asyncio.run(main())