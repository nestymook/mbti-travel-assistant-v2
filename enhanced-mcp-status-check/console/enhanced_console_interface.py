"""
Enhanced Console Interface

This module provides the main console interface for dual monitoring results,
integrating dashboard views, alert management, and configuration management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import sys
import os

from console.dashboard import EnhancedStatusDashboard, DashboardViewType
from console.alert_manager import DualMonitoringAlertManager, AlertSeverity, AlertStatus
from console.configuration_interface import ConfigurationManagementInterface
from console.troubleshooting_guide import TroubleshootingGuideInterface
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.enhanced_status_config import EnhancedStatusConfig


logger = logging.getLogger(__name__)


class ConsoleMode(Enum):
    """Console interface modes."""
    DASHBOARD = "dashboard"
    ALERTS = "alerts"
    CONFIGURATION = "configuration"
    TROUBLESHOOTING = "troubleshooting"
    MONITORING = "monitoring"
    HELP = "help"


@dataclass
class ConsoleSession:
    """Console session state."""
    session_id: str
    current_mode: ConsoleMode
    current_view: Optional[str]
    auto_refresh: bool
    refresh_interval: int
    filters: Dict[str, Any]
    started_at: datetime
    last_activity: datetime


class EnhancedConsoleInterface:
    """
    Enhanced Console Interface for dual monitoring system.
    
    Provides comprehensive console interface for viewing dual monitoring results,
    managing alerts, configuring settings, and accessing troubleshooting guides.
    """
    
    def __init__(
        self,
        health_service: EnhancedHealthCheckService,
        metrics_collector: DualMetricsCollector,
        config_manager: EnhancedStatusConfig
    ):
        """
        Initialize Enhanced Console Interface.
        
        Args:
            health_service: Enhanced health check service
            metrics_collector: Dual metrics collector
            config_manager: Enhanced status configuration manager
        """
        self.health_service = health_service
        self.metrics_collector = metrics_collector
        self.config_manager = config_manager
        
        # Initialize components
        self.dashboard = EnhancedStatusDashboard(
            health_service, metrics_collector, config_manager
        )
        self.alert_manager = DualMonitoringAlertManager()
        self.config_interface = ConfigurationManagementInterface(config_manager)
        self.troubleshooting_guide = TroubleshootingGuideInterface()
        
        # Console state
        self.session = ConsoleSession(
            session_id="console_session",
            current_mode=ConsoleMode.DASHBOARD,
            current_view=None,
            auto_refresh=True,
            refresh_interval=30,
            filters={},
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
    
    async def start_console(self):
        """Start the enhanced console interface."""
        try:
            self._running = True
            
            # Display welcome message
            self._display_welcome()
            
            # Start background tasks
            if self.session.auto_refresh:
                refresh_task = asyncio.create_task(self._auto_refresh_loop())
                self._background_tasks.append(refresh_task)
            
            # Start main console loop
            await self._main_console_loop()
            
        except KeyboardInterrupt:
            print("\n\nShutting down console interface...")
        except Exception as e:
            logger.error(f"Console interface error: {e}")
            print(f"Console error: {e}")
        finally:
            await self._cleanup()
    
    def _display_welcome(self):
        """Display welcome message and initial status."""
        print("=" * 80)
        print("🔍 Enhanced MCP Status Check Console Interface")
        print("=" * 80)
        print(f"Started at: {self.session.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current mode: {self.session.current_mode.value}")
        print(f"Auto-refresh: {'ON' if self.session.auto_refresh else 'OFF'} ({self.session.refresh_interval}s)")
        print("\nType 'help' for available commands")
        print("-" * 80)
    
    async def _main_console_loop(self):
        """Main console interaction loop."""
        while self._running:
            try:
                # Update last activity
                self.session.last_activity = datetime.now()
                
                # Display current view
                await self._display_current_view()
                
                # Get user input
                command = await self._get_user_input()
                
                if command:
                    await self._process_command(command)
                
                # Small delay to prevent busy loop
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Console loop error: {e}")
                print(f"Error: {e}")
    
    async def _display_current_view(self):
        """Display the current console view."""
        try:
            if self.session.current_mode == ConsoleMode.DASHBOARD:
                await self._display_dashboard_view()
            elif self.session.current_mode == ConsoleMode.ALERTS:
                await self._display_alerts_view()
            elif self.session.current_mode == ConsoleMode.CONFIGURATION:
                await self._display_configuration_view()
            elif self.session.current_mode == ConsoleMode.TROUBLESHOOTING:
                await self._display_troubleshooting_view()
            elif self.session.current_mode == ConsoleMode.MONITORING:
                await self._display_monitoring_view()
            elif self.session.current_mode == ConsoleMode.HELP:
                self._display_help_view()
            
        except Exception as e:
            logger.error(f"Error displaying view: {e}")
            print(f"Display error: {e}")
    
    async def _display_dashboard_view(self):
        """Display dashboard view."""
        print("\n" + "=" * 80)
        print("📊 DUAL MONITORING DASHBOARD")
        print("=" * 80)
        
        # Get system overview
        overview = await self.dashboard.get_system_overview()
        
        # Display system status
        status_icon = self._get_status_icon(overview.overall_status.value)
        print(f"\n🌐 System Status: {status_icon} {overview.overall_status.value.upper()}")
        print(f"📈 Health Score: {overview.average_health_score:.2f}")
        print(f"🖥️  Total Servers: {overview.total_servers}")
        print(f"⏱️  Last Updated: {overview.timestamp.strftime('%H:%M:%S')}")
        
        # Display status breakdown
        print(f"\n📊 Status Breakdown:")
        for status, count in overview.status_breakdown.items():
            icon = self._get_status_icon(status)
            print(f"  {icon} {status.title()}: {count}")
        
        # Display monitoring breakdown
        print(f"\n🔍 Monitoring Coverage:")
        for method, count in overview.monitoring_breakdown.items():
            print(f"  • {method.replace('_', ' ').title()}: {count}")
        
        # Display response times
        print(f"\n⚡ Average Response Times:")
        for method, time_ms in overview.average_response_times.items():
            print(f"  • {method.upper()}: {time_ms:.0f}ms")
        
        # Display recent alerts
        if overview.recent_alerts:
            print(f"\n🚨 Recent Alerts ({len(overview.recent_alerts)}):")
            for alert in overview.recent_alerts[:3]:  # Show top 3
                severity_icon = self._get_alert_severity_icon(alert.get("severity", "info"))
                print(f"  {severity_icon} {alert.get('message', 'Unknown alert')}")
        
        # Display server grid
        await self._display_server_grid()
    
    async def _display_server_grid(self):
        """Display server status grid."""
        print(f"\n🖥️  SERVER STATUS GRID")
        print("-" * 80)
        
        # Get server summaries
        summaries = await self.dashboard.get_server_summaries()
        
        if not summaries:
            print("No servers configured for monitoring")
            return
        
        # Display header
        print(f"{'Server':<20} {'Status':<12} {'MCP':<8} {'REST':<8} {'Score':<6} {'Paths':<15}")
        print("-" * 80)
        
        # Display servers
        for summary in summaries:
            status_icon = self._get_status_icon(summary.overall_status.value)
            mcp_status = "✅" if summary.mcp_status == "SUCCESS" else "❌" if summary.mcp_status == "FAILED" else "➖"
            rest_status = "✅" if summary.rest_status == "SUCCESS" else "❌" if summary.rest_status == "FAILED" else "➖"
            paths = ",".join(summary.available_paths) if summary.available_paths else "none"
            
            print(f"{summary.server_name:<20} {status_icon} {summary.overall_status.value:<8} {mcp_status:<8} {rest_status:<8} {summary.health_score:.2f:<6} {paths:<15}")
    
    async def _display_alerts_view(self):
        """Display alerts view."""
        print("\n" + "=" * 80)
        print("🚨 ALERT MANAGEMENT")
        print("=" * 80)
        
        # Get active alerts
        active_alerts = await self.alert_manager.get_active_alerts()
        
        if not active_alerts:
            print("\n✅ No active alerts")
        else:
            print(f"\n🔔 Active Alerts ({len(active_alerts)}):")
            print("-" * 80)
            
            for alert in active_alerts:
                severity_icon = self._get_alert_severity_icon(alert.severity.value)
                age = datetime.now() - alert.created_at
                age_str = self._format_duration(age)
                
                print(f"{severity_icon} [{alert.severity.value.upper()}] {alert.title}")
                print(f"   Server: {alert.server_name} | Age: {age_str}")
                print(f"   {alert.message}")
                if alert.details:
                    print(f"   Details: {json.dumps(alert.details, indent=2)}")
                print()
        
        # Display alert statistics
        await self._display_alert_statistics()
    
    async def _display_alert_statistics(self):
        """Display alert statistics."""
        print("\n📊 Alert Statistics (Last 24h):")
        print("-" * 40)
        
        # Get alert history
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        alert_history = await self.alert_manager.get_alert_history(start_time, end_time)
        
        if not alert_history:
            print("No alerts in the last 24 hours")
            return
        
        # Count by severity
        severity_counts = {}
        type_counts = {}
        
        for alert in alert_history:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            type_counts[alert.alert_type.value] = type_counts.get(alert.alert_type.value, 0) + 1
        
        print("By Severity:")
        for severity, count in severity_counts.items():
            icon = self._get_alert_severity_icon(severity)
            print(f"  {icon} {severity.title()}: {count}")
        
        print("\nBy Type:")
        for alert_type, count in type_counts.items():
            print(f"  • {alert_type.replace('_', ' ').title()}: {count}")
    
    async def _display_configuration_view(self):
        """Display configuration management view."""
        print("\n" + "=" * 80)
        print("⚙️  CONFIGURATION MANAGEMENT")
        print("=" * 80)
        
        await self.config_interface.display_configuration_overview()
    
    async def _display_troubleshooting_view(self):
        """Display troubleshooting guide view."""
        print("\n" + "=" * 80)
        print("🔧 TROUBLESHOOTING GUIDE")
        print("=" * 80)
        
        await self.troubleshooting_guide.display_troubleshooting_menu()
    
    async def _display_monitoring_view(self):
        """Display detailed monitoring view."""
        print("\n" + "=" * 80)
        print("📈 DETAILED MONITORING")
        print("=" * 80)
        
        # Display MCP and REST detailed views
        print("\n🔌 MCP Monitoring Details:")
        mcp_view = await self.dashboard.get_mcp_detailed_view()
        self._display_monitoring_details(mcp_view, "MCP")
        
        print("\n🌐 REST Monitoring Details:")
        rest_view = await self.dashboard.get_rest_detailed_view()
        self._display_monitoring_details(rest_view, "REST")
    
    def _display_monitoring_details(self, view_data: Dict[str, Any], protocol: str):
        """Display monitoring details for a specific protocol."""
        if "error" in view_data:
            print(f"❌ Error getting {protocol} data: {view_data['error']}")
            return
        
        summary = view_data.get("summary", {})
        servers = view_data.get("servers", [])
        
        print(f"  Total Servers: {summary.get('total_' + protocol.lower() + '_servers', 0)}")
        print(f"  Successful: {summary.get('successful_checks', 0)}")
        print(f"  Failed: {summary.get('failed_checks', 0)}")
        print(f"  Avg Response Time: {summary.get('average_response_time', 0):.0f}ms")
        
        if servers:
            print(f"\n  Server Details:")
            for server in servers[:5]:  # Show top 5
                status_icon = "✅" if server.get("status") == "SUCCESS" else "❌"
                print(f"    {status_icon} {server.get('server_name', 'Unknown')}: {server.get('response_time_ms', 0):.0f}ms")
    
    def _display_help_view(self):
        """Display help information."""
        print("\n" + "=" * 80)
        print("❓ HELP - Available Commands")
        print("=" * 80)
        
        commands = [
            ("dashboard", "Switch to dashboard view"),
            ("alerts", "Switch to alerts management"),
            ("config", "Switch to configuration management"),
            ("troubleshoot", "Switch to troubleshooting guide"),
            ("monitoring", "Switch to detailed monitoring view"),
            ("refresh", "Refresh current view"),
            ("auto-refresh on/off", "Toggle auto-refresh"),
            ("filter <type> <value>", "Apply filters to current view"),
            ("clear", "Clear screen"),
            ("status", "Show quick system status"),
            ("help", "Show this help message"),
            ("quit", "Exit console interface")
        ]
        
        print("\nCommands:")
        for command, description in commands:
            print(f"  {command:<20} - {description}")
        
        print("\nNavigation:")
        print("  • Use arrow keys for history")
        print("  • Ctrl+C to interrupt operations")
        print("  • Tab completion available for commands")
    
    async def _get_user_input(self) -> Optional[str]:
        """Get user input with async support."""
        try:
            # Simple input for now - could be enhanced with readline/prompt_toolkit
            prompt = f"\n[{self.session.current_mode.value}]> "
            
            # Use asyncio to handle input without blocking
            loop = asyncio.get_event_loop()
            command = await loop.run_in_executor(None, input, prompt)
            
            return command.strip() if command else None
            
        except EOFError:
            return "quit"
        except Exception as e:
            logger.error(f"Error getting user input: {e}")
            return None
    
    async def _process_command(self, command: str):
        """Process user command."""
        try:
            parts = command.lower().split()
            if not parts:
                return
            
            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Mode switching commands
            if cmd in ["dashboard", "dash", "d"]:
                self.session.current_mode = ConsoleMode.DASHBOARD
                print("Switched to dashboard view")
            
            elif cmd in ["alerts", "alert", "a"]:
                self.session.current_mode = ConsoleMode.ALERTS
                print("Switched to alerts view")
            
            elif cmd in ["config", "configuration", "c"]:
                self.session.current_mode = ConsoleMode.CONFIGURATION
                print("Switched to configuration view")
            
            elif cmd in ["troubleshoot", "trouble", "t"]:
                self.session.current_mode = ConsoleMode.TROUBLESHOOTING
                print("Switched to troubleshooting view")
            
            elif cmd in ["monitoring", "monitor", "m"]:
                self.session.current_mode = ConsoleMode.MONITORING
                print("Switched to monitoring view")
            
            elif cmd in ["help", "h", "?"]:
                self.session.current_mode = ConsoleMode.HELP
            
            # Utility commands
            elif cmd in ["refresh", "r"]:
                print("Refreshing view...")
                # Force refresh by clearing cache
                await self.dashboard.get_system_overview(force_refresh=True)
            
            elif cmd == "auto-refresh":
                if args and args[0] in ["on", "off"]:
                    self.session.auto_refresh = args[0] == "on"
                    print(f"Auto-refresh {'enabled' if self.session.auto_refresh else 'disabled'}")
                else:
                    print(f"Auto-refresh is {'ON' if self.session.auto_refresh else 'OFF'}")
            
            elif cmd == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
            
            elif cmd == "status":
                await self._display_quick_status()
            
            elif cmd in ["quit", "exit", "q"]:
                self._running = False
                print("Goodbye!")
            
            # Alert management commands
            elif cmd == "ack" and args:
                await self._acknowledge_alert(args[0])
            
            elif cmd == "resolve" and args:
                await self._resolve_alert(args[0])
            
            # Configuration commands
            elif cmd == "set" and len(args) >= 2:
                await self._set_configuration(args[0], " ".join(args[1:]))
            
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
                
        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}")
            print(f"Command error: {e}")
    
    async def _display_quick_status(self):
        """Display quick system status."""
        overview = await self.dashboard.get_system_overview()
        status_icon = self._get_status_icon(overview.overall_status.value)
        
        print(f"\n🔍 Quick Status: {status_icon} {overview.overall_status.value}")
        print(f"   Servers: {overview.total_servers} | Health: {overview.average_health_score:.2f}")
        print(f"   Updated: {overview.timestamp.strftime('%H:%M:%S')}")
    
    async def _acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        try:
            success = await self.alert_manager.acknowledge_alert(alert_id, "console_user")
            if success:
                print(f"✅ Alert {alert_id} acknowledged")
            else:
                print(f"❌ Failed to acknowledge alert {alert_id}")
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
    
    async def _resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        try:
            success = await self.alert_manager.resolve_alert(alert_id, "Resolved via console")
            if success:
                print(f"✅ Alert {alert_id} resolved")
            else:
                print(f"❌ Failed to resolve alert {alert_id}")
        except Exception as e:
            print(f"Error resolving alert: {e}")
    
    async def _set_configuration(self, key: str, value: str):
        """Set configuration value."""
        try:
            success = await self.config_interface.set_configuration_value(key, value)
            if success:
                print(f"✅ Configuration updated: {key} = {value}")
            else:
                print(f"❌ Failed to update configuration: {key}")
        except Exception as e:
            print(f"Error setting configuration: {e}")
    
    async def _auto_refresh_loop(self):
        """Auto-refresh loop for dashboard updates."""
        while self._running and self.session.auto_refresh:
            try:
                await asyncio.sleep(self.session.refresh_interval)
                
                if self.session.current_mode == ConsoleMode.DASHBOARD:
                    # Clear screen and refresh dashboard
                    os.system('cls' if os.name == 'nt' else 'clear')
                    await self._display_current_view()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-refresh error: {e}")
    
    def _get_status_icon(self, status: str) -> str:
        """Get status icon for display."""
        icons = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴",
            "unknown": "⚪"
        }
        return icons.get(status.lower(), "⚪")
    
    def _get_alert_severity_icon(self, severity: str) -> str:
        """Get alert severity icon."""
        icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "info": "ℹ️"
        }
        return icons.get(severity.lower(), "⚪")
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    async def _cleanup(self):
        """Cleanup resources."""
        self._running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        print("Console interface stopped")


# Console entry point
async def main():
    """Main entry point for console interface."""
    try:
        # Initialize services (would normally be injected)
        from services.enhanced_health_check_service import EnhancedHealthCheckService
        from services.dual_metrics_collector import DualMetricsCollector
        from config.enhanced_status_config import EnhancedStatusConfig
        
        config_manager = EnhancedStatusConfig()
        await config_manager.load_configuration()
        
        health_service = EnhancedHealthCheckService(config_manager)
        metrics_collector = DualMetricsCollector()
        
        # Start console interface
        console = EnhancedConsoleInterface(health_service, metrics_collector, config_manager)
        await console.start_console()
        
    except Exception as e:
        print(f"Failed to start console interface: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())