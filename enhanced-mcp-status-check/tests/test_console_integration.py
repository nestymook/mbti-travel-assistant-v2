"""
Test Enhanced Console Integration

Tests for the enhanced console interface, dashboard views, alert management,
configuration interface, and troubleshooting guides.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any

from console.enhanced_console_interface import (
    EnhancedConsoleInterface,
    ConsoleMode,
    ConsoleSession
)
from console.dashboard import (
    EnhancedStatusDashboard,
    DashboardViewType,
    ServerHealthSummary,
    SystemHealthOverview
)
from console.alert_manager import (
    DualMonitoringAlertManager,
    Alert,
    AlertRule,
    AlertType,
    AlertSeverity,
    AlertStatus
)
from console.configuration_interface import ConfigurationManagementInterface
from console.troubleshooting_guide import TroubleshootingGuideInterface
from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    ServerStatus,
    EnhancedServerConfig
)


class TestEnhancedConsoleInterface:
    """Test Enhanced Console Interface."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        health_service = AsyncMock()
        metrics_collector = AsyncMock()
        config_manager = AsyncMock()
        
        return health_service, metrics_collector, config_manager
    
    @pytest.fixture
    def console_interface(self, mock_services):
        """Create console interface for testing."""
        health_service, metrics_collector, config_manager = mock_services
        return EnhancedConsoleInterface(health_service, metrics_collector, config_manager)
    
    @pytest.mark.asyncio
    async def test_console_initialization(self, console_interface):
        """Test console interface initialization."""
        assert console_interface.session.current_mode == ConsoleMode.DASHBOARD
        assert console_interface.session.auto_refresh is True
        assert console_interface.session.refresh_interval == 30
        assert isinstance(console_interface.dashboard, EnhancedStatusDashboard)
        assert isinstance(console_interface.alert_manager, DualMonitoringAlertManager)
        assert isinstance(console_interface.config_interface, ConfigurationManagementInterface)
        assert isinstance(console_interface.troubleshooting_guide, TroubleshootingGuideInterface)
    
    @pytest.mark.asyncio
    async def test_mode_switching_commands(self, console_interface):
        """Test console mode switching commands."""
        # Test dashboard mode
        await console_interface._process_command("dashboard")
        assert console_interface.session.current_mode == ConsoleMode.DASHBOARD
        
        # Test alerts mode
        await console_interface._process_command("alerts")
        assert console_interface.session.current_mode == ConsoleMode.ALERTS
        
        # Test configuration mode
        await console_interface._process_command("config")
        assert console_interface.session.current_mode == ConsoleMode.CONFIGURATION
        
        # Test troubleshooting mode
        await console_interface._process_command("troubleshoot")
        assert console_interface.session.current_mode == ConsoleMode.TROUBLESHOOTING
        
        # Test monitoring mode
        await console_interface._process_command("monitoring")
        assert console_interface.session.current_mode == ConsoleMode.MONITORING
        
        # Test help mode
        await console_interface._process_command("help")
        assert console_interface.session.current_mode == ConsoleMode.HELP
    
    @pytest.mark.asyncio
    async def test_utility_commands(self, console_interface):
        """Test utility commands."""
        # Test auto-refresh toggle
        await console_interface._process_command("auto-refresh off")
        assert console_interface.session.auto_refresh is False
        
        await console_interface._process_command("auto-refresh on")
        assert console_interface.session.auto_refresh is True
        
        # Test quit command
        await console_interface._process_command("quit")
        assert console_interface._running is False
    
    @pytest.mark.asyncio
    async def test_display_quick_status(self, console_interface):
        """Test quick status display."""
        # Mock system overview
        mock_overview = SystemHealthOverview(
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            total_servers=3,
            status_breakdown={"healthy": 2, "degraded": 1, "unhealthy": 0, "unknown": 0},
            monitoring_breakdown={"mcp_only": 0, "rest_only": 0, "both": 3, "none": 0},
            average_health_score=0.85,
            average_response_times={"mcp": 150.0, "rest": 120.0, "combined": 135.0},
            recent_alerts=[],
            trend_data={"health_score": [], "response_time": [], "success_rate": []}
        )
        
        console_interface.dashboard.get_system_overview = AsyncMock(return_value=mock_overview)
        
        # Test quick status display
        with patch('builtins.print') as mock_print:
            await console_interface._display_quick_status()
            mock_print.assert_called()
    
    @pytest.mark.asyncio
    async def test_alert_management_commands(self, console_interface):
        """Test alert management commands."""
        # Mock alert manager methods
        console_interface.alert_manager.acknowledge_alert = AsyncMock(return_value=True)
        console_interface.alert_manager.resolve_alert = AsyncMock(return_value=True)
        
        # Test acknowledge alert
        await console_interface._acknowledge_alert("test-alert-id")
        console_interface.alert_manager.acknowledge_alert.assert_called_once_with(
            "test-alert-id", "console_user"
        )
        
        # Test resolve alert
        await console_interface._resolve_alert("test-alert-id")
        console_interface.alert_manager.resolve_alert.assert_called_once_with(
            "test-alert-id", "Resolved via console"
        )
    
    @pytest.mark.asyncio
    async def test_configuration_commands(self, console_interface):
        """Test configuration management commands."""
        # Mock configuration interface
        console_interface.config_interface.set_configuration_value = AsyncMock(return_value=True)
        
        # Test set configuration
        await console_interface._set_configuration("test.setting", "test_value")
        console_interface.config_interface.set_configuration_value.assert_called_once_with(
            "test.setting", "test_value"
        )


class TestEnhancedStatusDashboard:
    """Test Enhanced Status Dashboard."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        health_service = AsyncMock()
        metrics_collector = AsyncMock()
        config_manager = AsyncMock()
        
        return health_service, metrics_collector, config_manager
    
    @pytest.fixture
    def dashboard(self, mock_services):
        """Create dashboard for testing."""
        health_service, metrics_collector, config_manager = mock_services
        return EnhancedStatusDashboard(health_service, metrics_collector, config_manager)
    
    @pytest.mark.asyncio
    async def test_system_overview_generation(self, dashboard):
        """Test system overview generation."""
        # Mock server configurations
        mock_configs = [
            EnhancedServerConfig(
                server_name="test-server-1",
                mcp_endpoint_url="http://localhost:8001",
                rest_health_endpoint_url="http://localhost:8001/health"
            ),
            EnhancedServerConfig(
                server_name="test-server-2",
                mcp_endpoint_url="http://localhost:8002",
                rest_health_endpoint_url="http://localhost:8002/health"
            )
        ]
        
        # Mock dual health check results
        mock_results = [
            DualHealthCheckResult(
                server_name="test-server-1",
                timestamp=datetime.now(),
                overall_status=ServerStatus.HEALTHY,
                overall_success=True,
                mcp_result=None,
                mcp_success=True,
                mcp_response_time_ms=150.0,
                mcp_tools_count=3,
                mcp_error_message=None,
                rest_result=None,
                rest_success=True,
                rest_response_time_ms=120.0,
                rest_status_code=200,
                rest_error_message=None,
                combined_response_time_ms=135.0,
                health_score=0.95,
                available_paths=["mcp", "rest"]
            ),
            DualHealthCheckResult(
                server_name="test-server-2",
                timestamp=datetime.now(),
                overall_status=ServerStatus.DEGRADED,
                overall_success=False,
                mcp_result=None,
                mcp_success=False,
                mcp_response_time_ms=0.0,
                mcp_tools_count=None,
                mcp_error_message="Connection failed",
                rest_result=None,
                rest_success=True,
                rest_response_time_ms=110.0,
                rest_status_code=200,
                rest_error_message=None,
                combined_response_time_ms=110.0,
                health_score=0.60,
                available_paths=["rest"]
            )
        ]
        
        # Configure mocks
        dashboard.config_manager.get_all_server_configs = AsyncMock(return_value=mock_configs)
        dashboard.health_service.check_multiple_servers_dual = AsyncMock(return_value=mock_results)
        dashboard._get_recent_alerts = AsyncMock(return_value=[])
        dashboard._get_trend_data = AsyncMock(return_value={
            "health_score": [0.9, 0.85, 0.8],
            "response_time": [140, 145, 150],
            "success_rate": [0.95, 0.90, 0.85]
        })
        
        # Test system overview generation
        overview = await dashboard.get_system_overview()
        
        assert overview.total_servers == 2
        assert overview.overall_status == ServerStatus.DEGRADED  # One degraded server
        assert overview.status_breakdown["healthy"] == 1
        assert overview.status_breakdown["degraded"] == 1
        assert overview.monitoring_breakdown["both"] == 1
        assert overview.monitoring_breakdown["rest_only"] == 1
        assert overview.average_health_score == 0.775  # (0.95 + 0.60) / 2
    
    @pytest.mark.asyncio
    async def test_server_summaries_generation(self, dashboard):
        """Test server summaries generation."""
        # Mock similar to above but test server summaries specifically
        mock_configs = [
            EnhancedServerConfig(
                server_name="test-server",
                mcp_endpoint_url="http://localhost:8001",
                rest_health_endpoint_url="http://localhost:8001/health"
            )
        ]
        
        mock_results = [
            DualHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                overall_status=ServerStatus.HEALTHY,
                overall_success=True,
                mcp_result=None,
                mcp_success=True,
                mcp_response_time_ms=150.0,
                mcp_tools_count=3,
                mcp_error_message=None,
                rest_result=None,
                rest_success=True,
                rest_response_time_ms=120.0,
                rest_status_code=200,
                rest_error_message=None,
                combined_response_time_ms=135.0,
                health_score=0.95,
                available_paths=["mcp", "rest"]
            )
        ]
        
        dashboard.config_manager.get_all_server_configs = AsyncMock(return_value=mock_configs)
        dashboard.health_service.check_multiple_servers_dual = AsyncMock(return_value=mock_results)
        
        # Test server summaries
        summaries = await dashboard.get_server_summaries()
        
        assert len(summaries) == 1
        summary = summaries[0]
        assert summary.server_name == "test-server"
        assert summary.overall_status == ServerStatus.HEALTHY
        assert summary.mcp_status == "SUCCESS"
        assert summary.rest_status == "SUCCESS"
        assert summary.health_score == 0.95
        assert "mcp" in summary.response_times
        assert "rest" in summary.response_times
        assert "combined" in summary.response_times
    
    @pytest.mark.asyncio
    async def test_mcp_detailed_view(self, dashboard):
        """Test MCP detailed view generation."""
        # Mock server summaries for MCP
        mock_summaries = [
            ServerHealthSummary(
                server_name="mcp-server",
                overall_status=ServerStatus.HEALTHY,
                mcp_status="SUCCESS",
                rest_status=None,
                health_score=0.90,
                last_check=datetime.now(),
                response_times={"mcp": 150.0, "combined": 150.0},
                available_paths=["mcp"],
                error_summary=None
            )
        ]
        
        dashboard.get_server_summaries = AsyncMock(return_value=mock_summaries)
        dashboard.metrics_collector.get_mcp_metrics = AsyncMock(return_value={
            "total_requests": 100,
            "successful_requests": 95,
            "average_response_time": 150.0
        })
        
        # Test MCP detailed view
        mcp_view = await dashboard.get_mcp_detailed_view()
        
        assert mcp_view["view_type"] == "mcp_detailed"
        assert mcp_view["summary"]["total_mcp_servers"] == 1
        assert mcp_view["summary"]["successful_checks"] == 1
        assert mcp_view["summary"]["failed_checks"] == 0
        assert len(mcp_view["servers"]) == 1
        assert mcp_view["servers"][0]["server_name"] == "mcp-server"
        assert mcp_view["servers"][0]["status"] == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_rest_detailed_view(self, dashboard):
        """Test REST detailed view generation."""
        # Mock server summaries for REST
        mock_summaries = [
            ServerHealthSummary(
                server_name="rest-server",
                overall_status=ServerStatus.HEALTHY,
                mcp_status=None,
                rest_status="SUCCESS",
                health_score=0.90,
                last_check=datetime.now(),
                response_times={"rest": 120.0, "combined": 120.0},
                available_paths=["rest"],
                error_summary=None
            )
        ]
        
        dashboard.get_server_summaries = AsyncMock(return_value=mock_summaries)
        dashboard.metrics_collector.get_rest_metrics = AsyncMock(return_value={
            "total_requests": 100,
            "successful_requests": 98,
            "average_response_time": 120.0
        })
        
        # Test REST detailed view
        rest_view = await dashboard.get_rest_detailed_view()
        
        assert rest_view["view_type"] == "rest_detailed"
        assert rest_view["summary"]["total_rest_servers"] == 1
        assert rest_view["summary"]["successful_checks"] == 1
        assert rest_view["summary"]["failed_checks"] == 0
        assert len(rest_view["servers"]) == 1
        assert rest_view["servers"][0]["server_name"] == "rest-server"
        assert rest_view["servers"][0]["status"] == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_combined_view(self, dashboard):
        """Test combined view generation."""
        # Mock both MCP and REST views
        dashboard.get_mcp_detailed_view = AsyncMock(return_value={
            "view_type": "mcp_detailed",
            "summary": {"total_mcp_servers": 2, "successful_checks": 1, "failed_checks": 1},
            "servers": [],
            "metrics": {}
        })
        
        dashboard.get_rest_detailed_view = AsyncMock(return_value={
            "view_type": "rest_detailed",
            "summary": {"total_rest_servers": 2, "successful_checks": 2, "failed_checks": 0},
            "servers": [],
            "metrics": {}
        })
        
        dashboard.get_server_summaries = AsyncMock(return_value=[])
        dashboard.metrics_collector.get_combined_metrics = AsyncMock(return_value={
            "correlation": 0.85,
            "combined_success_rate": 0.75
        })
        
        # Test combined view
        combined_view = await dashboard.get_combined_view()
        
        assert combined_view["view_type"] == "combined"
        assert "mcp_summary" in combined_view["summary"]
        assert "rest_summary" in combined_view["summary"]
        assert "metrics" in combined_view
        assert "comparison" in combined_view


class TestDualMonitoringAlertManager:
    """Test Dual Monitoring Alert Manager."""
    
    @pytest.fixture
    def alert_manager(self):
        """Create alert manager for testing."""
        return DualMonitoringAlertManager()
    
    @pytest.fixture
    def sample_dual_result(self):
        """Create sample dual health check result."""
        return DualHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=None,
            mcp_success=False,
            mcp_response_time_ms=0.0,
            mcp_tools_count=None,
            mcp_error_message="Connection failed",
            rest_result=None,
            rest_success=False,
            rest_response_time_ms=0.0,
            rest_status_code=None,
            rest_error_message="HTTP 500 error",
            combined_response_time_ms=0.0,
            health_score=0.0,
            available_paths=[]
        )
    
    def test_alert_manager_initialization(self, alert_manager):
        """Test alert manager initialization."""
        assert len(alert_manager._alert_rules) > 0
        assert len(alert_manager._notification_channels) > 0
        assert "mcp_failure_critical" in alert_manager._alert_rules
        assert "rest_failure_critical" in alert_manager._alert_rules
        assert "dual_failure_critical" in alert_manager._alert_rules
    
    def test_alert_rule_matching(self, alert_manager, sample_dual_result):
        """Test alert rule condition matching."""
        # Test MCP failure rule
        mcp_rule = alert_manager._alert_rules["mcp_failure_critical"]
        assert mcp_rule.matches_condition(sample_dual_result) is True
        
        # Test REST failure rule
        rest_rule = alert_manager._alert_rules["rest_failure_critical"]
        assert rest_rule.matches_condition(sample_dual_result) is True
        
        # Test dual failure rule
        dual_rule = alert_manager._alert_rules["dual_failure_critical"]
        assert dual_rule.matches_condition(sample_dual_result) is True
    
    @pytest.mark.asyncio
    async def test_alert_generation(self, alert_manager, sample_dual_result):
        """Test alert generation from health check results."""
        # Process health check result
        await alert_manager.process_health_check_result(sample_dual_result)
        
        # Check that alerts were generated
        assert len(alert_manager._active_alerts) > 0
        assert len(alert_manager._alert_history) > 0
        
        # Check alert details
        alerts = list(alert_manager._active_alerts.values())
        dual_failure_alert = next(
            (alert for alert in alerts if alert.alert_type == AlertType.DUAL_FAILURE),
            None
        )
        
        assert dual_failure_alert is not None
        assert dual_failure_alert.server_name == "test-server"
        assert dual_failure_alert.severity == AlertSeverity.CRITICAL
        assert dual_failure_alert.status == AlertStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_alert_acknowledgment(self, alert_manager, sample_dual_result):
        """Test alert acknowledgment."""
        # Generate alert
        await alert_manager.process_health_check_result(sample_dual_result)
        
        # Get alert ID
        alert_id = list(alert_manager._active_alerts.keys())[0]
        
        # Acknowledge alert
        success = await alert_manager.acknowledge_alert(alert_id, "test_user")
        
        assert success is True
        alert = alert_manager._active_alerts[alert_id]
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == "test_user"
        assert alert.acknowledged_at is not None
    
    @pytest.mark.asyncio
    async def test_alert_resolution(self, alert_manager, sample_dual_result):
        """Test alert resolution."""
        # Generate alert
        await alert_manager.process_health_check_result(sample_dual_result)
        
        # Get alert ID
        alert_id = list(alert_manager._active_alerts.keys())[0]
        
        # Resolve alert
        success = await alert_manager.resolve_alert(alert_id, "Issue resolved")
        
        assert success is True
        alert = alert_manager._active_alerts[alert_id]
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolution_notes == "Issue resolved"
        assert alert.resolved_at is not None
    
    @pytest.mark.asyncio
    async def test_notification_sending(self, alert_manager):
        """Test notification sending."""
        # Create test alert
        alert = Alert(
            alert_id="test-alert",
            rule_id="test-rule",
            server_name="test-server",
            alert_type=AlertType.DUAL_FAILURE,
            severity=AlertSeverity.CRITICAL,
            title="Test Alert",
            message="Test alert message",
            details={"test": "data"}
        )
        
        # Get console notification channel
        console_channel = alert_manager._notification_channels["console"]
        
        # Test notification sending
        success = await console_channel.send_notification(alert)
        assert success is True


class TestConfigurationManagementInterface:
    """Test Configuration Management Interface."""
    
    @pytest.fixture
    def config_interface(self):
        """Create configuration interface for testing."""
        mock_config_manager = AsyncMock()
        return ConfigurationManagementInterface(mock_config_manager)
    
    @pytest.mark.asyncio
    async def test_configuration_overview_display(self, config_interface):
        """Test configuration overview display."""
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
        
        config_interface.config_manager.get_configuration = AsyncMock(return_value=mock_config)
        config_interface.config_manager.get_all_server_configs = AsyncMock(return_value=[])
        
        # Test configuration overview display
        with patch('builtins.print') as mock_print:
            await config_interface.display_configuration_overview()
            mock_print.assert_called()
    
    def test_configuration_value_parsing(self, config_interface):
        """Test configuration value parsing."""
        # Test boolean parsing
        assert config_interface._parse_configuration_value("enabled", "true") is True
        assert config_interface._parse_configuration_value("enabled", "false") is False
        
        # Test integer parsing
        assert config_interface._parse_configuration_value("timeout_seconds", "30") == 30
        
        # Test float parsing
        assert config_interface._parse_configuration_value("priority_weight", "0.6") == 0.6
        
        # Test string parsing
        assert config_interface._parse_configuration_value("endpoint_path", "/health") == "/health"
    
    @pytest.mark.asyncio
    async def test_configuration_value_setting(self, config_interface):
        """Test setting configuration values."""
        # Test setting configuration value
        success = await config_interface.set_configuration_value("test.setting", "test_value")
        assert success is True
        assert "test.setting" in config_interface._unsaved_changes
        assert config_interface._unsaved_changes["test.setting"] == "test_value"


class TestTroubleshootingGuideInterface:
    """Test Troubleshooting Guide Interface."""
    
    @pytest.fixture
    def troubleshooting_guide(self):
        """Create troubleshooting guide interface for testing."""
        return TroubleshootingGuideInterface()
    
    def test_troubleshooting_guide_initialization(self, troubleshooting_guide):
        """Test troubleshooting guide initialization."""
        assert len(troubleshooting_guide._guides) > 0
        assert "mcp_connection_failure" in troubleshooting_guide._guides
        assert "rest_health_failure" in troubleshooting_guide._guides
        assert "authentication_issues" in troubleshooting_guide._guides
        assert "network_connectivity" in troubleshooting_guide._guides
        assert "configuration_issues" in troubleshooting_guide._guides
        assert "performance_issues" in troubleshooting_guide._guides
    
    @pytest.mark.asyncio
    async def test_troubleshooting_menu_display(self, troubleshooting_guide):
        """Test troubleshooting menu display."""
        with patch('builtins.print') as mock_print:
            guide_map = await troubleshooting_guide.display_troubleshooting_menu()
            mock_print.assert_called()
            assert isinstance(guide_map, dict)
            assert len(guide_map) > 0
    
    def test_symptom_analysis(self, troubleshooting_guide):
        """Test symptom analysis for guide suggestions."""
        # Test MCP failure symptoms
        mcp_symptoms = {
            "mcp_failing": True,
            "rest_failing": False,
            "auth_errors": False,
            "timeout_errors": False,
            "slow_responses": False,
            "intermittent_issues": False,
            "recent_changes": False,
            "network_issues": False
        }
        
        suggestions = troubleshooting_guide._analyze_symptoms(mcp_symptoms)
        assert len(suggestions) > 0
        
        # Should suggest MCP-related guide
        top_suggestion = suggestions[0]
        assert "mcp" in top_suggestion[0]
        assert top_suggestion[1] > 0  # Confidence score
    
    @pytest.mark.asyncio
    async def test_diagnostic_wizard_symptom_collection(self, troubleshooting_guide):
        """Test diagnostic wizard symptom collection."""
        # Mock user input for symptom collection
        with patch.object(troubleshooting_guide, '_get_user_confirmation') as mock_input:
            mock_input.side_effect = [True, False, False, True, False, False, False, False]
            
            symptoms = await troubleshooting_guide._collect_symptoms()
            
            assert symptoms["mcp_failing"] is True
            assert symptoms["rest_failing"] is False
            assert symptoms["timeout_errors"] is True
    
    @pytest.mark.asyncio
    async def test_common_issues_faq_display(self, troubleshooting_guide):
        """Test common issues FAQ display."""
        with patch('builtins.print') as mock_print:
            await troubleshooting_guide.display_common_issues_faq()
            mock_print.assert_called()


# Integration tests
class TestConsoleIntegration:
    """Test console integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_dashboard_workflow(self):
        """Test complete dashboard workflow."""
        # Mock all required services
        health_service = AsyncMock()
        metrics_collector = AsyncMock()
        config_manager = AsyncMock()
        
        # Create console interface
        console = EnhancedConsoleInterface(health_service, metrics_collector, config_manager)
        
        # Mock system overview data
        mock_overview = SystemHealthOverview(
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            total_servers=2,
            status_breakdown={"healthy": 2, "degraded": 0, "unhealthy": 0, "unknown": 0},
            monitoring_breakdown={"mcp_only": 0, "rest_only": 0, "both": 2, "none": 0},
            average_health_score=0.90,
            average_response_times={"mcp": 150.0, "rest": 120.0, "combined": 135.0},
            recent_alerts=[],
            trend_data={"health_score": [], "response_time": [], "success_rate": []}
        )
        
        console.dashboard.get_system_overview = AsyncMock(return_value=mock_overview)
        console.dashboard.get_server_summaries = AsyncMock(return_value=[])
        
        # Test dashboard display
        with patch('builtins.print') as mock_print:
            await console._display_dashboard_view()
            mock_print.assert_called()
    
    @pytest.mark.asyncio
    async def test_alert_workflow_integration(self):
        """Test alert generation and management workflow."""
        # Create alert manager
        alert_manager = DualMonitoringAlertManager()
        
        # Create failing health check result
        failing_result = DualHealthCheckResult(
            server_name="failing-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=None,
            mcp_success=False,
            mcp_response_time_ms=0.0,
            mcp_tools_count=None,
            mcp_error_message="MCP connection failed",
            rest_result=None,
            rest_success=False,
            rest_response_time_ms=0.0,
            rest_status_code=500,
            rest_error_message="Internal server error",
            combined_response_time_ms=0.0,
            health_score=0.0,
            available_paths=[]
        )
        
        # Process health check result
        await alert_manager.process_health_check_result(failing_result)
        
        # Verify alerts were generated
        assert len(alert_manager._active_alerts) > 0
        
        # Test alert acknowledgment workflow
        alert_id = list(alert_manager._active_alerts.keys())[0]
        success = await alert_manager.acknowledge_alert(alert_id, "test_user")
        assert success is True
        
        # Test alert resolution workflow
        success = await alert_manager.resolve_alert(alert_id, "Issue resolved")
        assert success is True
    
    @pytest.mark.asyncio
    async def test_configuration_management_workflow(self):
        """Test configuration management workflow."""
        # Mock configuration manager
        config_manager = AsyncMock()
        config_manager.get_configuration = AsyncMock(return_value={
            "system": {"dual_monitoring_enabled": True},
            "mcp_health_checks": {"enabled": True},
            "rest_health_checks": {"enabled": True},
            "result_aggregation": {"mcp_priority_weight": 0.6}
        })
        config_manager.get_all_server_configs = AsyncMock(return_value=[])
        
        # Create configuration interface
        config_interface = ConfigurationManagementInterface(config_manager)
        
        # Test configuration overview
        with patch('builtins.print') as mock_print:
            await config_interface.display_configuration_overview()
            mock_print.assert_called()
        
        # Test setting configuration value
        success = await config_interface.set_configuration_value("test.setting", "true")
        assert success is True
        assert config_interface._unsaved_changes["test.setting"] is True


if __name__ == "__main__":
    pytest.main([__file__])