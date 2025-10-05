"""
Simple Alert Manager for testing
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any
from datetime import datetime


class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(Enum):
    MCP_FAILURE = "mcp_failure"
    REST_FAILURE = "rest_failure"
    DUAL_FAILURE = "dual_failure"
    DEGRADED_SERVICE = "degraded_service"
    RECOVERY = "recovery"


class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    alert_id: str
    server_name: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DualMonitoringAlertManager:
    """Simple alert manager for testing."""
    
    def __init__(self):
        self._alert_rules = {}
        self._active_alerts = {}
        self._alert_history = []
        self._notification_channels = {}
        
        # Initialize with some basic rules
        self._initialize_default_rules()
        self._initialize_default_channels()
    
    def _initialize_default_rules(self):
        """Initialize basic alert rules."""
        self._alert_rules = {
            "mcp_failure_critical": {
                "name": "MCP Health Check Failure",
                "severity": AlertSeverity.HIGH,
                "type": AlertType.MCP_FAILURE
            },
            "rest_failure_critical": {
                "name": "REST Health Check Failure", 
                "severity": AlertSeverity.HIGH,
                "type": AlertType.REST_FAILURE
            },
            "dual_failure_critical": {
                "name": "Dual Monitoring Failure",
                "severity": AlertSeverity.CRITICAL,
                "type": AlertType.DUAL_FAILURE
            }
        }
    
    def _initialize_default_channels(self):
        """Initialize notification channels."""
        self._notification_channels = {
            "console": {"type": "console", "enabled": True}
        }
    
    async def process_health_check_result(self, result):
        """Process health check result and generate alerts."""
        # Simple alert generation logic
        if not result.mcp_success and not result.rest_success:
            alert = Alert(
                alert_id=f"alert_{len(self._alert_history)}",
                server_name=result.server_name,
                alert_type=AlertType.DUAL_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title=f"Complete Monitoring Failure - {result.server_name}",
                message="Both MCP and REST health checks failed"
            )
            self._active_alerts[alert.alert_id] = alert
            self._alert_history.append(alert)
    
    async def get_active_alerts(self):
        """Get active alerts."""
        return list(self._active_alerts.values())
    
    async def get_alert_history(self, start_time, end_time):
        """Get alert history."""
        return [
            alert for alert in self._alert_history
            if start_time <= alert.created_at <= end_time
        ]
    
    async def acknowledge_alert(self, alert_id, acknowledged_by):
        """Acknowledge an alert."""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            return True
        return False
    
    async def resolve_alert(self, alert_id, resolution_notes):
        """Resolve an alert."""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].status = AlertStatus.RESOLVED
            return True
        return False