"""
Audit logging service for MBTI Travel Assistant MCP.

This module provides comprehensive audit logging for authentication events,
user activities, and system operations with structured logging and compliance support.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import uuid
import re
from threading import Lock

from models.auth_models import UserContext, JWTClaims
from config.settings import settings


class AuditEventType(Enum):
    """Types of audit events for compliance logging."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    TOKEN_VALIDATION = "token_validation"
    TOKEN_REFRESH = "token_refresh"
    AUTHORIZATION_CHECK = "authorization_check"
    MCP_TOOL_ACCESS = "mcp_tool_access"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_ERROR = "system_error"


class AuditLevel(Enum):
    """Audit logging levels for different compliance requirements."""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AuditEvent:
    """Structured audit event for compliance logging."""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    session_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    outcome: str = "success"
    details: Optional[Dict[str, Any]] = None
    risk_level: str = "low"
    compliance_tags: Optional[List[str]] = None


@dataclass
class UserActivity:
    """User activity tracking for audit purposes."""
    user_id: str
    username: str
    session_id: str
    activity_type: str
    timestamp: str
    resource_accessed: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    outcome: str = "success"
    duration_ms: Optional[int] = None


class AuditLogger:
    """
    Comprehensive audit logging service for authentication and user activities.
    
    Provides structured audit logging with compliance support, user activity tracking,
    and security event correlation. Implements requirements 6.6 and 6.8.
    """
    
    def __init__(self, audit_level: AuditLevel = AuditLevel.DETAILED,
                 enable_file_logging: bool = True,
                 enable_structured_logging: bool = True,
                 log_retention_days: int = 90):
        """
        Initialize audit logger.
        
        Args:
            audit_level: Level of audit detail to capture
            enable_file_logging: Whether to enable file-based audit logs
            enable_structured_logging: Whether to use structured JSON logging
            log_retention_days: Number of days to retain audit logs
        """
        self.audit_level = audit_level
        self.enable_file_logging = enable_file_logging
        self.enable_structured_logging = enable_structured_logging
        self.log_retention_days = log_retention_days
        
        # Configure audit logger
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Configure security audit logger
        self.security_logger = logging.getLogger('security_audit')
        self.security_logger.setLevel(logging.WARNING)
        
        # Setup file handlers if enabled
        if self.enable_file_logging:
            self._setup_file_handlers()
        
        # User activity tracking
        self._user_activities = {}  # session_id -> List[UserActivity]
        
        self.logger.info("Audit logger initialized with level: %s", audit_level.value)
    
    def log_authentication_event(self, event_type: AuditEventType,
                                user_context: Optional[UserContext] = None,
                                request_context: Optional[Dict[str, Any]] = None,
                                outcome: str = "success",
                                details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log authentication-related audit event.
        
        Args:
            event_type: Type of authentication event
            user_context: User context information
            request_context: Request context information
            outcome: Event outcome (success, failure, error)
            details: Additional event details
            
        Returns:
            Event ID for correlation
        """
        try:
            event_id = self._generate_event_id()
            
            # Extract user information
            user_id = user_context.user_id if user_context else None
            username = user_context.username if user_context else None
            session_id = user_context.session_id if user_context else None
            
            # Extract request information
            client_ip = request_context.get('client_ip') if request_context else None
            user_agent = request_context.get('user_agent') if request_context else None
            resource = request_context.get('path') if request_context else None
            action = request_context.get('method') if request_context else None
            
            # Determine risk level
            risk_level = self._assess_risk_level(event_type, outcome, details)
            
            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=user_id,
                username=username,
                session_id=session_id,
                client_ip=client_ip,
                user_agent=self._sanitize_user_agent(user_agent),
                resource=resource,
                action=action,
                outcome=outcome,
                details=self._sanitize_details(details),
                risk_level=risk_level,
                compliance_tags=self._get_compliance_tags(event_type)
            )
            
            # Log the event
            self._log_audit_event(audit_event)
            
            # Track user activity if applicable
            if user_context and session_id:
                self._track_user_activity(user_context, event_type, request_context, outcome)
            
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to log authentication event: {e}")
            return ""
    
    def log_token_validation_event(self, token_claims: Optional[JWTClaims] = None,
                                 request_context: Optional[Dict[str, Any]] = None,
                                 validation_result: str = "success",
                                 error_details: Optional[str] = None) -> str:
        """
        Log JWT token validation audit event.
        
        Args:
            token_claims: JWT token claims
            request_context: Request context information
            validation_result: Validation result (success, expired, invalid, etc.)
            error_details: Error details if validation failed
            
        Returns:
            Event ID for correlation
        """
        try:
            event_id = self._generate_event_id()
            
            # Extract token information (sanitized)
            details = {}
            if token_claims:
                details.update({
                    'token_type': token_claims.token_use,
                    'token_exp': token_claims.exp,
                    'token_iat': token_claims.iat,
                    'client_id': token_claims.client_id,
                    'issuer': token_claims.iss,
                    'audience': token_claims.aud
                })
            
            if error_details:
                details['error'] = error_details
            
            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                event_type=AuditEventType.TOKEN_VALIDATION,
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=token_claims.user_id if token_claims else None,
                username=token_claims.username if token_claims else None,
                client_ip=request_context.get('client_ip') if request_context else None,
                user_agent=self._sanitize_user_agent(
                    request_context.get('user_agent') if request_context else None
                ),
                resource=request_context.get('path') if request_context else None,
                action="token_validation",
                outcome=validation_result,
                details=details,
                risk_level=self._assess_token_risk_level(validation_result, error_details),
                compliance_tags=['authentication', 'token_validation']
            )
            
            # Log the event
            self._log_audit_event(audit_event)
            
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to log token validation event: {e}")
            return ""
    
    def log_mcp_tool_access(self, tool_name: str, user_context: UserContext,
                          request_context: Dict[str, Any],
                          parameters: Optional[Dict[str, Any]] = None,
                          outcome: str = "success",
                          duration_ms: Optional[int] = None) -> str:
        """
        Log MCP tool access for audit trail.
        
        Args:
            tool_name: Name of MCP tool accessed
            user_context: User context information
            request_context: Request context information
            parameters: Tool parameters (will be sanitized)
            outcome: Access outcome
            duration_ms: Tool execution duration
            
        Returns:
            Event ID for correlation
        """
        try:
            event_id = self._generate_event_id()
            
            # Sanitize parameters
            sanitized_params = self._sanitize_tool_parameters(parameters or {})
            
            # Create details
            details = {
                'tool_name': tool_name,
                'parameters': sanitized_params,
                'execution_time_ms': duration_ms
            }
            
            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                event_type=AuditEventType.MCP_TOOL_ACCESS,
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=user_context.user_id,
                username=user_context.username,
                session_id=user_context.session_id,
                client_ip=request_context.get('client_ip'),
                user_agent=self._sanitize_user_agent(request_context.get('user_agent')),
                resource=f"mcp_tool:{tool_name}",
                action="invoke",
                outcome=outcome,
                details=details,
                risk_level=self._assess_tool_risk_level(tool_name, outcome),
                compliance_tags=['data_access', 'mcp_tool', 'user_activity']
            )
            
            # Log the event
            self._log_audit_event(audit_event)
            
            # Track user activity
            self._track_user_activity(
                user_context, AuditEventType.MCP_TOOL_ACCESS,
                request_context, outcome, duration_ms
            )
            
            return event_id
            
        except Exception as e:
            self.logger.error(f"Failed to log MCP tool access: {e}")
            return ""
    
    def log_security_violation(self, violation_type: str, user_context: Optional[UserContext],
                             request_context: Dict[str, Any],
                             violation_details: Dict[str, Any]) -> str:
        """
        Log security violation for compliance and monitoring.
        
        Args:
            violation_type: Type of security violation
            user_context: User context if available
            request_context: Request context information
            violation_details: Details about the violation
            
        Returns:
            Event ID for correlation
        """
        try:
            event_id = self._generate_event_id()
            
            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                event_type=AuditEventType.SECURITY_VIOLATION,
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=user_context.user_id if user_context else None,
                username=user_context.username if user_context else None,
                session_id=user_context.session_id if user_context else None,
                client_ip=request_context.get('client_ip'),
                user_agent=self._sanitize_user_agent(request_context.get('user_agent')),
                resource=request_context.get('path'),
                action=violation_type,
                outcome="violation",
                details=self._sanitize_details(violation_details),
                risk_level="high",
                compliance_tags=['security', 'violation', 'incident']
            )
            
            # Log to security audit logger with higher severity
            self._log_security_audit_event(audit_event)
            
            return event_id
            
        except Exception as e:
            self.security_logger.error(f"Failed to log security violation: {e}")
            return ""
    
    def get_user_activity_summary(self, user_id: str, 
                                time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Get user activity summary for audit reporting.
        
        Args:
            user_id: User ID to get activity for
            time_range_hours: Time range in hours
            
        Returns:
            User activity summary
        """
        try:
            # In a production system, this would query a persistent audit store
            # For now, return summary from in-memory tracking
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            
            activities = []
            for session_activities in self._user_activities.values():
                for activity in session_activities:
                    if (activity.user_id == user_id and 
                        datetime.fromisoformat(activity.timestamp.replace('Z', '+00:00')) > cutoff_time):
                        activities.append(activity)
            
            # Create summary
            summary = {
                'user_id': user_id,
                'time_range_hours': time_range_hours,
                'total_activities': len(activities),
                'activity_types': {},
                'resources_accessed': set(),
                'success_rate': 0.0,
                'average_duration_ms': 0.0
            }
            
            if activities:
                # Count activity types
                for activity in activities:
                    activity_type = activity.activity_type
                    summary['activity_types'][activity_type] = summary['activity_types'].get(activity_type, 0) + 1
                    
                    if activity.resource_accessed:
                        summary['resources_accessed'].add(activity.resource_accessed)
                
                # Calculate success rate
                successful = sum(1 for a in activities if a.outcome == 'success')
                summary['success_rate'] = successful / len(activities) * 100
                
                # Calculate average duration
                durations = [a.duration_ms for a in activities if a.duration_ms is not None]
                if durations:
                    summary['average_duration_ms'] = sum(durations) / len(durations)
                
                # Convert set to list for JSON serialization
                summary['resources_accessed'] = list(summary['resources_accessed'])
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get user activity summary: {e}")
            return {'error': str(e)}
    
    def export_audit_logs(self, start_time: datetime, end_time: datetime,
                         event_types: Optional[List[AuditEventType]] = None,
                         user_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Export audit logs for compliance reporting.
        
        Args:
            start_time: Start time for export
            end_time: End time for export
            event_types: Optional filter by event types
            user_ids: Optional filter by user IDs
            
        Returns:
            List of audit events
        """
        try:
            # In a production system, this would query a persistent audit store
            # For now, return placeholder for the interface
            
            export_info = {
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'event_types_filter': [et.value for et in event_types] if event_types else None,
                'user_ids_filter': user_ids,
                'note': 'Audit log export functionality requires persistent storage implementation'
            }
            
            self.logger.info(f"Audit log export requested: {json.dumps(export_info)}")
            
            return [export_info]
            
        except Exception as e:
            self.logger.error(f"Failed to export audit logs: {e}")
            return []
    
    def _log_audit_event(self, audit_event: AuditEvent) -> None:
        """Log audit event with appropriate formatting."""
        try:
            if self.enable_structured_logging:
                # Log as structured JSON
                log_entry = asdict(audit_event)
                self.logger.info(json.dumps(log_entry, default=str))
            else:
                # Log as formatted text
                log_message = (
                    f"AUDIT: {audit_event.event_type.value} | "
                    f"User: {audit_event.username or 'unknown'} | "
                    f"Outcome: {audit_event.outcome} | "
                    f"Resource: {audit_event.resource or 'N/A'} | "
                    f"Risk: {audit_event.risk_level}"
                )
                self.logger.info(log_message)
        
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
    def _log_security_audit_event(self, audit_event: AuditEvent) -> None:
        """Log security audit event with higher severity."""
        try:
            log_entry = asdict(audit_event)
            self.security_logger.warning(json.dumps(log_entry, default=str))
        
        except Exception as e:
            self.security_logger.error(f"Failed to log security audit event: {e}")
    
    def _track_user_activity(self, user_context: UserContext, event_type: AuditEventType,
                           request_context: Optional[Dict[str, Any]] = None,
                           outcome: str = "success", duration_ms: Optional[int] = None) -> None:
        """Track user activity for session analysis."""
        try:
            if not user_context.session_id:
                return
            
            activity = UserActivity(
                user_id=user_context.user_id,
                username=user_context.username,
                session_id=user_context.session_id,
                activity_type=event_type.value,
                timestamp=datetime.now(timezone.utc).isoformat(),
                resource_accessed=request_context.get('path') if request_context else None,
                parameters=self._sanitize_tool_parameters(
                    request_context.get('parameters', {}) if request_context else {}
                ),
                outcome=outcome,
                duration_ms=duration_ms
            )
            
            if user_context.session_id not in self._user_activities:
                self._user_activities[user_context.session_id] = []
            
            self._user_activities[user_context.session_id].append(activity)
            
            # Limit activity history per session
            if len(self._user_activities[user_context.session_id]) > 1000:
                self._user_activities[user_context.session_id] = \
                    self._user_activities[user_context.session_id][-500:]
        
        except Exception as e:
            self.logger.error(f"Failed to track user activity: {e}")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID for audit correlation."""
        return str(uuid.uuid4())
    
    def _assess_risk_level(self, event_type: AuditEventType, outcome: str,
                          details: Optional[Dict[str, Any]]) -> str:
        """Assess risk level for audit event."""
        # High risk events
        if event_type in [AuditEventType.SECURITY_VIOLATION, AuditEventType.SYSTEM_ERROR]:
            return "high"
        
        # Medium risk for failures
        if outcome in ["failure", "error", "violation"]:
            return "medium"
        
        # Check for suspicious patterns in details
        if details:
            suspicious_indicators = ['brute_force', 'suspicious', 'blocked', 'violation']
            for indicator in suspicious_indicators:
                if any(indicator in str(value).lower() for value in details.values()):
                    return "medium"
        
        return "low"
    
    def _assess_token_risk_level(self, validation_result: str, error_details: Optional[str]) -> str:
        """Assess risk level for token validation events."""
        high_risk_results = ['invalid_signature', 'malformed', 'suspicious']
        medium_risk_results = ['expired', 'invalid_audience', 'invalid_issuer']
        
        if validation_result in high_risk_results:
            return "high"
        elif validation_result in medium_risk_results:
            return "medium"
        elif error_details and any(risk in error_details.lower() for risk in high_risk_results):
            return "high"
        
        return "low"
    
    def _assess_tool_risk_level(self, tool_name: str, outcome: str) -> str:
        """Assess risk level for MCP tool access."""
        # High-risk tools that access sensitive data
        high_risk_tools = ['admin', 'config', 'user_data', 'system']
        
        if any(risk_tool in tool_name.lower() for risk_tool in high_risk_tools):
            return "medium"
        
        if outcome != "success":
            return "medium"
        
        return "low"
    
    def _get_compliance_tags(self, event_type: AuditEventType) -> List[str]:
        """Get compliance tags for audit event."""
        base_tags = ['audit', 'compliance']
        
        event_tags = {
            AuditEventType.USER_LOGIN: ['authentication', 'access_control'],
            AuditEventType.USER_LOGOUT: ['authentication', 'session_management'],
            AuditEventType.TOKEN_VALIDATION: ['authentication', 'token_management'],
            AuditEventType.TOKEN_REFRESH: ['authentication', 'token_management'],
            AuditEventType.AUTHORIZATION_CHECK: ['authorization', 'access_control'],
            AuditEventType.MCP_TOOL_ACCESS: ['data_access', 'user_activity'],
            AuditEventType.DATA_ACCESS: ['data_access', 'privacy'],
            AuditEventType.CONFIGURATION_CHANGE: ['configuration', 'system_change'],
            AuditEventType.SECURITY_VIOLATION: ['security', 'incident'],
            AuditEventType.SYSTEM_ERROR: ['system', 'error']
        }
        
        return base_tags + event_tags.get(event_type, [])
    
    def _sanitize_user_agent(self, user_agent: Optional[str]) -> Optional[str]:
        """Sanitize user agent for audit logging."""
        if not user_agent:
            return None
        
        # Limit length and remove potentially malicious content
        sanitized = user_agent[:200]
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        return sanitized
    
    def _sanitize_details(self, details: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Sanitize details dictionary for audit logging."""
        if not details:
            return None
        
        sanitized = {}
        for key, value in details.items():
            # Redact sensitive keys
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + '...[TRUNCATED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_tool_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize tool parameters for audit logging."""
        sanitized = {}
        
        for key, value in parameters.items():
            # Redact sensitive parameter names
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key', 'auth']):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, str) and len(value) > 200:
                sanitized[key] = value[:200] + '...[TRUNCATED]'
            elif isinstance(value, (list, dict)) and len(str(value)) > 500:
                sanitized[key] = '[LARGE_OBJECT_TRUNCATED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _setup_file_handlers(self) -> None:
        """Setup file handlers for audit logging."""
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.join(os.getcwd(), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Setup audit log file handler
            audit_file = os.path.join(log_dir, 'audit.log')
            audit_handler = logging.FileHandler(audit_file)
            audit_handler.setLevel(logging.INFO)
            
            # Setup security audit log file handler
            security_file = os.path.join(log_dir, 'security_audit.log')
            security_handler = logging.FileHandler(security_file)
            security_handler.setLevel(logging.WARNING)
            
            # Create formatters
            if self.enable_structured_logging:
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            audit_handler.setFormatter(formatter)
            security_handler.setFormatter(formatter)
            
            # Add handlers to loggers
            self.logger.addHandler(audit_handler)
            self.security_logger.addHandler(security_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to setup file handlers: {e}")


# Global audit logger instance
_audit_logger = None
_audit_lock = Lock()


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    
    with _audit_lock:
        if _audit_logger is None:
            _audit_logger = AuditLogger()
        
        return _audit_logger


# Export main classes
__all__ = [
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'AuditLevel',
    'UserActivity',
    'get_audit_logger'
]