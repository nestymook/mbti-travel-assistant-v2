#!/usr/bin/env python3
"""
Alerting and Notification System

This module provides comprehensive alerting and notification capabilities
for the MBTI Travel Assistant MCP service, including real-time monitoring,
alert escalation, and multi-channel notifications.
"""

import asyncio
import logging
import json
import smtplib
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


@dataclass
class AlertEvent:
    """Alert event data structure"""
    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    description: str
    timestamp: datetime
    source: str
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    dimensions: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['severity'] = self.severity.value
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        if self.acknowledged_at:
            result['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            result['resolved_at'] = self.resolved_at.isoformat()
        return result


@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    name: str
    type: str  # 'email', 'slack', 'sns', 'webhook', 'pagerduty'
    config: Dict[str, Any]
    enabled: bool = True
    severity_filter: List[AlertSeverity] = None
    
    def should_notify(self, severity: AlertSeverity) -> bool:
        """Check if this channel should be notified for given severity"""
        if not self.enabled:
            return False
        
        if self.severity_filter is None:
            return True
        
        return severity in self.severity_filter


class NotificationFormatter:
    """Formats alert notifications for different channels"""
    
    @staticmethod
    def format_email(alert: AlertEvent) -> Dict[str, str]:
        """Format alert for email notification"""
        subject = f"[{alert.severity.value.upper()}] {alert.name} - MBTI Travel Assistant"
        
        body = f"""
Alert: {alert.name}
Severity: {alert.severity.value.upper()}
Status: {alert.status.value.upper()}
Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
Source: {alert.source}

Message: {alert.message}

Description: {alert.description}
"""
        
        if alert.metric_name and alert.current_value is not None:
            body += f"\nMetric: {alert.metric_name}\nCurrent Value: {alert.current_value}"
            if alert.threshold is not None:
                body += f"\nThreshold: {alert.threshold}"
        
        if alert.dimensions:
            body += f"\nDimensions: {json.dumps(alert.dimensions, indent=2)}"
        
        return {
            "subject": subject,
            "body": body
        }
    
    @staticmethod
    def format_slack(alert: AlertEvent) -> Dict[str, Any]:
        """Format alert for Slack notification"""
        color_map = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.INFO: "good",
            AlertSeverity.DEBUG: "#439FE0"
        }
        
        fields = [
            {
                "title": "Severity",
                "value": alert.severity.value.upper(),
                "short": True
            },
            {
                "title": "Status",
                "value": alert.status.value.upper(),
                "short": True
            },
            {
                "title": "Source",
                "value": alert.source,
                "short": True
            },
            {
                "title": "Timestamp",
                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                "short": True
            }
        ]
        
        if alert.metric_name and alert.current_value is not None:
            fields.append({
                "title": "Metric",
                "value": f"{alert.metric_name}: {alert.current_value}",
                "short": True
            })
            
            if alert.threshold is not None:
                fields.append({
                    "title": "Threshold",
                    "value": str(alert.threshold),
                    "short": True
                })
        
        return {
            "text": f"Alert: {alert.name}",
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "good"),
                    "title": alert.name,
                    "text": alert.message,
                    "fields": fields,
                    "footer": "MBTI Travel Assistant MCP",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }
    
    @staticmethod
    def format_webhook(alert: AlertEvent) -> Dict[str, Any]:
        """Format alert for webhook notification"""
        return {
            "alert": alert.to_dict(),
            "event_type": "alert",
            "service": "mbti-travel-assistant-mcp"
        }


class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        """
        Initialize email notifier.
        
        Args:
            smtp_config: SMTP configuration
        """
        self.smtp_host = smtp_config.get("host", "localhost")
        self.smtp_port = smtp_config.get("port", 587)
        self.smtp_username = smtp_config.get("username")
        self.smtp_password = smtp_config.get("password")
        self.from_email = smtp_config.get("from_email", "alerts@example.com")
        self.use_tls = smtp_config.get("use_tls", True)
    
    async def send_notification(self, alert: AlertEvent, recipients: List[str]):
        """Send email notification"""
        try:
            formatted = NotificationFormatter.format_email(alert)
            
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = formatted['subject']
            
            msg.attach(MimeText(formatted['body'], 'plain'))
            
            # Send email in thread to avoid blocking
            await asyncio.to_thread(self._send_email, msg, recipients)
            
            logger.info(f"Email notification sent for alert: {alert.name}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise
    
    def _send_email(self, msg: MimeMultipart, recipients: List[str]):
        """Send email using SMTP"""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg, to_addrs=recipients)


class SlackNotifier:
    """Slack notification handler"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url
    
    async def send_notification(self, alert: AlertEvent, channel: Optional[str] = None):
        """Send Slack notification"""
        try:
            formatted = NotificationFormatter.format_slack(alert)
            
            if channel:
                formatted['channel'] = channel
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=formatted,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert: {alert.name}")
                    else:
                        logger.error(f"Slack notification failed with status: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            raise


class SNSNotifier:
    """AWS SNS notification handler"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize SNS notifier.
        
        Args:
            region: AWS region
        """
        self.sns_client = boto3.client('sns', region_name=region)
    
    async def send_notification(self, alert: AlertEvent, topic_arn: str):
        """Send SNS notification"""
        try:
            formatted = NotificationFormatter.format_email(alert)
            
            message = {
                "default": formatted['body'],
                "email": formatted['body'],
                "sms": f"Alert: {alert.name} - {alert.message}"
            }
            
            await asyncio.to_thread(
                self.sns_client.publish,
                TopicArn=topic_arn,
                Subject=formatted['subject'],
                Message=json.dumps(message),
                MessageStructure='json'
            )
            
            logger.info(f"SNS notification sent for alert: {alert.name}")
            
        except Exception as e:
            logger.error(f"Failed to send SNS notification: {e}")
            raise


class WebhookNotifier:
    """Generic webhook notification handler"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        """
        Initialize webhook notifier.
        
        Args:
            webhook_url: Webhook URL
            headers: Optional HTTP headers
        """
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    async def send_notification(self, alert: AlertEvent):
        """Send webhook notification"""
        try:
            formatted = NotificationFormatter.format_webhook(alert)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=formatted,
                    headers=self.headers
                ) as response:
                    if 200 <= response.status < 300:
                        logger.info(f"Webhook notification sent for alert: {alert.name}")
                    else:
                        logger.error(f"Webhook notification failed with status: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            raise


class AlertingSystem:
    """
    Comprehensive alerting and notification system.
    
    Manages alert lifecycle, notification routing, and escalation policies
    for the MBTI Travel Assistant MCP service.
    """
    
    def __init__(self, environment: str = "development"):
        """
        Initialize alerting system.
        
        Args:
            environment: Environment name
        """
        self.environment = environment
        self.active_alerts: Dict[str, AlertEvent] = {}
        self.alert_history: List[AlertEvent] = []
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.notifiers: Dict[str, Any] = {}
        self.escalation_policies: Dict[str, Dict[str, Any]] = {}
        
        # Alert suppression
        self.suppression_rules: List[Dict[str, Any]] = []
        self.maintenance_windows: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized AlertingSystem for {environment}")
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel"""
        self.notification_channels[channel.name] = channel
        
        # Initialize notifier based on channel type
        if channel.type == "email" and channel.name not in self.notifiers:
            self.notifiers[channel.name] = EmailNotifier(channel.config)
        elif channel.type == "slack" and channel.name not in self.notifiers:
            self.notifiers[channel.name] = SlackNotifier(channel.config["webhook_url"])
        elif channel.type == "sns" and channel.name not in self.notifiers:
            self.notifiers[channel.name] = SNSNotifier(channel.config.get("region", "us-east-1"))
        elif channel.type == "webhook" and channel.name not in self.notifiers:
            self.notifiers[channel.name] = WebhookNotifier(
                channel.config["url"],
                channel.config.get("headers")
            )
        
        logger.info(f"Added notification channel: {channel.name} ({channel.type})")
    
    def add_escalation_policy(
        self,
        name: str,
        severity_levels: List[AlertSeverity],
        escalation_steps: List[Dict[str, Any]]
    ):
        """
        Add an escalation policy.
        
        Args:
            name: Policy name
            severity_levels: Alert severities this policy applies to
            escalation_steps: List of escalation steps with timing and channels
        """
        self.escalation_policies[name] = {
            "severity_levels": severity_levels,
            "steps": escalation_steps
        }
        
        logger.info(f"Added escalation policy: {name}")
    
    def add_suppression_rule(
        self,
        name: str,
        conditions: Dict[str, Any],
        duration_minutes: int
    ):
        """
        Add an alert suppression rule.
        
        Args:
            name: Rule name
            conditions: Conditions for suppression
            duration_minutes: Suppression duration
        """
        rule = {
            "name": name,
            "conditions": conditions,
            "duration_minutes": duration_minutes,
            "created_at": datetime.now()
        }
        
        self.suppression_rules.append(rule)
        logger.info(f"Added suppression rule: {name}")
    
    def add_maintenance_window(
        self,
        name: str,
        start_time: datetime,
        end_time: datetime,
        affected_services: List[str]
    ):
        """
        Add a maintenance window.
        
        Args:
            name: Maintenance window name
            start_time: Start time
            end_time: End time
            affected_services: List of affected services
        """
        window = {
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "affected_services": affected_services
        }
        
        self.maintenance_windows.append(window)
        logger.info(f"Added maintenance window: {name}")
    
    async def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        description: str,
        source: str,
        metric_name: Optional[str] = None,
        current_value: Optional[float] = None,
        threshold: Optional[float] = None,
        dimensions: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertEvent:
        """
        Trigger a new alert.
        
        Args:
            name: Alert name
            severity: Alert severity
            message: Alert message
            description: Detailed description
            source: Alert source
            metric_name: Optional metric name
            current_value: Optional current metric value
            threshold: Optional threshold value
            dimensions: Optional dimensions
            metadata: Optional metadata
            
        Returns:
            Created alert event
        """
        alert_id = f"{name}_{source}_{int(datetime.now().timestamp())}"
        
        alert = AlertEvent(
            id=alert_id,
            name=name,
            severity=severity,
            status=AlertStatus.ACTIVE,
            message=message,
            description=description,
            timestamp=datetime.now(),
            source=source,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            dimensions=dimensions,
            metadata=metadata
        )
        
        # Check if alert should be suppressed
        if self._should_suppress_alert(alert):
            alert.status = AlertStatus.SUPPRESSED
            logger.info(f"Alert suppressed: {alert.name}")
            return alert
        
        # Check maintenance windows
        if self._is_in_maintenance_window(alert):
            alert.status = AlertStatus.SUPPRESSED
            logger.info(f"Alert suppressed due to maintenance window: {alert.name}")
            return alert
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Alert triggered: {alert.name} - {alert.message}")
        
        # Send notifications
        await self._send_notifications(alert)
        
        # Start escalation if applicable
        await self._start_escalation(alert)
        
        return alert
    
    async def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """
        Resolve an active alert.
        
        Args:
            alert_id: Alert ID
            resolved_by: Optional user who resolved the alert
            
        Returns:
            True if alert was resolved, False if not found
        """
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        
        if resolved_by:
            alert.metadata = alert.metadata or {}
            alert.metadata["resolved_by"] = resolved_by
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        logger.info(f"Alert resolved: {alert.name}")
        
        # Send resolution notifications
        await self._send_resolution_notifications(alert)
        
        return True
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an active alert.
        
        Args:
            alert_id: Alert ID
            acknowledged_by: User who acknowledged the alert
            
        Returns:
            True if alert was acknowledged, False if not found
        """
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        
        logger.info(f"Alert acknowledged by {acknowledged_by}: {alert.name}")
        
        return True
    
    def _should_suppress_alert(self, alert: AlertEvent) -> bool:
        """Check if alert should be suppressed based on rules"""
        for rule in self.suppression_rules:
            # Check if rule is still active
            rule_age = datetime.now() - rule["created_at"]
            if rule_age.total_seconds() > rule["duration_minutes"] * 60:
                continue
            
            # Check conditions
            conditions = rule["conditions"]
            
            if "name" in conditions and alert.name != conditions["name"]:
                continue
            
            if "source" in conditions and alert.source != conditions["source"]:
                continue
            
            if "severity" in conditions and alert.severity.value not in conditions["severity"]:
                continue
            
            # All conditions match
            return True
        
        return False
    
    def _is_in_maintenance_window(self, alert: AlertEvent) -> bool:
        """Check if alert is within a maintenance window"""
        now = datetime.now()
        
        for window in self.maintenance_windows:
            if window["start_time"] <= now <= window["end_time"]:
                # Check if alert source is affected
                if alert.source in window["affected_services"]:
                    return True
        
        return False
    
    async def _send_notifications(self, alert: AlertEvent):
        """Send notifications for an alert"""
        for channel_name, channel in self.notification_channels.items():
            if not channel.should_notify(alert.severity):
                continue
            
            try:
                notifier = self.notifiers.get(channel_name)
                if not notifier:
                    logger.warning(f"No notifier found for channel: {channel_name}")
                    continue
                
                if channel.type == "email":
                    recipients = channel.config.get("recipients", [])
                    if recipients:
                        await notifier.send_notification(alert, recipients)
                
                elif channel.type == "slack":
                    slack_channel = channel.config.get("channel")
                    await notifier.send_notification(alert, slack_channel)
                
                elif channel.type == "sns":
                    topic_arn = channel.config.get("topic_arn")
                    if topic_arn:
                        await notifier.send_notification(alert, topic_arn)
                
                elif channel.type == "webhook":
                    await notifier.send_notification(alert)
                
            except Exception as e:
                logger.error(f"Failed to send notification via {channel_name}: {e}")
    
    async def _send_resolution_notifications(self, alert: AlertEvent):
        """Send resolution notifications"""
        # Create a resolution message
        resolution_alert = AlertEvent(
            id=f"{alert.id}_resolved",
            name=f"{alert.name} - RESOLVED",
            severity=AlertSeverity.INFO,
            status=AlertStatus.RESOLVED,
            message=f"Alert resolved: {alert.message}",
            description=f"The alert '{alert.name}' has been resolved.",
            timestamp=datetime.now(),
            source=alert.source,
            metadata={"original_alert_id": alert.id}
        )
        
        await self._send_notifications(resolution_alert)
    
    async def _start_escalation(self, alert: AlertEvent):
        """Start escalation process for an alert"""
        # Find applicable escalation policy
        escalation_policy = None
        for policy_name, policy in self.escalation_policies.items():
            if alert.severity in policy["severity_levels"]:
                escalation_policy = policy
                break
        
        if not escalation_policy:
            return
        
        # Schedule escalation steps
        for i, step in enumerate(escalation_policy["steps"]):
            delay_minutes = step.get("delay_minutes", 0)
            
            if delay_minutes > 0:
                # Schedule escalation step
                asyncio.create_task(
                    self._execute_escalation_step(alert, step, delay_minutes)
                )
    
    async def _execute_escalation_step(
        self,
        alert: AlertEvent,
        step: Dict[str, Any],
        delay_minutes: int
    ):
        """Execute an escalation step"""
        await asyncio.sleep(delay_minutes * 60)
        
        # Check if alert is still active
        if alert.id not in self.active_alerts:
            return
        
        # Check if alert has been acknowledged
        if self.active_alerts[alert.id].status == AlertStatus.ACKNOWLEDGED:
            return
        
        logger.warning(f"Escalating alert: {alert.name}")
        
        # Send escalation notifications
        escalation_channels = step.get("channels", [])
        for channel_name in escalation_channels:
            if channel_name in self.notification_channels:
                channel = self.notification_channels[channel_name]
                notifier = self.notifiers.get(channel_name)
                
                if notifier and channel.type == "email":
                    recipients = channel.config.get("recipients", [])
                    if recipients:
                        # Create escalation alert
                        escalation_alert = AlertEvent(
                            id=f"{alert.id}_escalation",
                            name=f"ESCALATED: {alert.name}",
                            severity=AlertSeverity.CRITICAL,
                            status=AlertStatus.ACTIVE,
                            message=f"Escalated alert: {alert.message}",
                            description=f"Alert has been escalated after {delay_minutes} minutes without acknowledgment.",
                            timestamp=datetime.now(),
                            source=alert.source
                        )
                        
                        await notifier.send_notification(escalation_alert, recipients)
    
    def get_active_alerts(self) -> List[AlertEvent]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[AlertEvent]:
        """Get alert history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics"""
        recent_alerts = self.get_alert_history(hours)
        
        # Count by severity
        severity_counts = {severity.value: 0 for severity in AlertSeverity}
        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1
        
        # Count by status
        status_counts = {status.value: 0 for status in AlertStatus}
        for alert in recent_alerts:
            status_counts[alert.status.value] += 1
        
        # Count by source
        source_counts = {}
        for alert in recent_alerts:
            source_counts[alert.source] = source_counts.get(alert.source, 0) + 1
        
        return {
            "time_range_hours": hours,
            "total_alerts": len(recent_alerts),
            "active_alerts": len(self.active_alerts),
            "severity_counts": severity_counts,
            "status_counts": status_counts,
            "source_counts": source_counts
        }
    
    def cleanup_old_alerts(self, days: int = 7):
        """Clean up old alerts from history"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        original_count = len(self.alert_history)
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        cleaned_count = original_count - len(self.alert_history)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old alerts")
    
    def export_alerts(self, format: str = "json") -> str:
        """Export alerts in specified format"""
        data = {
            "active_alerts": [alert.to_dict() for alert in self.get_active_alerts()],
            "recent_alerts": [alert.to_dict() for alert in self.get_alert_history()],
            "statistics": self.get_alert_statistics(),
            "export_timestamp": datetime.now().isoformat()
        }
        
        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")