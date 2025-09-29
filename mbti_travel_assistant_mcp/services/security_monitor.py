"""
Comprehensive Security Monitor for MBTI Travel Assistant MCP.

This module provides centralized security monitoring, threat detection,
and incident response coordination for the MBTI Travel Assistant system.
Implements requirements 8.4, 8.6, and 8.7 from the specification.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from threading import Lock
import hashlib
import ipaddress
import re

from models.auth_models import UserContext
from services.audit_logger import get_audit_logger, AuditEventType
from services.security_event_correlator import SecurityEventCorrelator, ThreatPattern, ThreatLevel
from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity
from services.request_validator import ValidationViolation, ValidationSeverity


# Configure logging
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)


@dataclass
class SecurityMetrics:
    """Security metrics for monitoring dashboard."""
    total_requests: int = 0
    authenticated_requests: int = 0
    failed_authentications: int = 0
    blocked_requests: int = 0
    security_violations: int = 0
    validation_failures: int = 0
    threat_patterns_detected: int = 0
    unique_users: int = 0
    unique_ips: int = 0
    time_period: str = ""
    last_updated: str = ""


@dataclass
class SecurityAlert:
    """Security alert for immediate attention."""
    alert_id: str
    alert_type: str
    severity: ErrorSeverity
    title: str
    description: str
    affected_resources: List[str]
    threat_indicators: List[str]
    recommended_actions: List[str]
    created_at: str
    status: str = "open"


@dataclass
class UserSecurityProfile:
    """Security profile for user behavior analysis."""
    user_id: str
    username: str
    first_seen: str
    last_seen: str
    total_requests: int
    failed_attempts: int
    successful_logins: int
    unique_ips: Set[str]
    suspicious_activities: int
    risk_score: float
    status: str = "active"


class SecurityMonitor:
    """
    Comprehensive security monitoring and threat detection system.
    
    Provides centralized security monitoring, threat detection, incident response,
    and security metrics collection for the MBTI Travel Assistant MCP system.
    """
    
    def __init__(self, enable_real_time_monitoring: bool = True,
                 enable_automated_response: bool = True,
                 enable_threat_correlation: bool = True,
                 max_failed_attempts: int = 5,
                 lockout_duration: int = 300,
                 monitoring_window_hours: int = 24):
        """
        Initialize security monitor.
        
        Args:
            enable_real_time_monitoring: Whether to enable real-time monitoring
            enable_automated_response: Whether to enable automated responses
            enable_threat_correlation: Whether to enable threat correlation
            max_failed_attempts: Maximum failed attempts before lockout
            lockout_duration: Lockout duration in seconds
            monitoring_window_hours: Time window for monitoring analysis
        """
        self.enable_real_time_monitoring = enable_real_time_monitoring
        self.enable_automated_response = enable_automated_response
        self.enable_threat_correlation = enable_threat_correlation
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = lockout_duration
        self.monitoring_window_hours = monitoring_window_hours
        
        # Thread safety
        self._lock = Lock()
        
        # Initialize components
        self.audit_logger = get_audit_logger()
        self.security_correlator = SecurityEventCorrelator() if enable_threat_correlation else None
        
        # Security state tracking
        self._security_metrics = SecurityMetrics()
        self._security_alerts = {}  # alert_id -> SecurityAlert
        self._user_profiles = {}  # user_id -> UserSecurityProfile
        self._blocked_ips = {}  # ip -> block_until_timestamp
        self._failed_attempts = defaultdict(deque)  # ip -> deque of timestamps
        self._recent_events = deque(maxlen=10000)  # Recent security events
        
        # Threat detection patterns
        self._suspicious_patterns = {
            'user_agents': [
                r'bot', r'crawler', r'spider', r'scraper', r'scanner',
                r'curl', r'wget', r'python-requests', r'postman',
                r'nikto', r'sqlmap', r'nmap', r'masscan', r'burp'
            ],
            'paths': [
                r'/admin', r'/wp-admin', r'/phpmyadmin', r'/config',
                r'/\.env', r'/\.git', r'/backup', r'/test', r'/debug'
            ],
            'parameters': [
                r'<script', r'javascript:', r'vbscript:', r'onload=',
                r'union.*select', r'drop.*table', r'exec.*xp_',
                r'\.\./\.\./\.\.'
            ]
        }
        
        # Compile patterns for performance
        self._compiled_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in self._suspicious_patterns.items()
        }
        
        logger.info("Security monitor initialized")
    
    def monitor_authentication_attempt(self, success: bool, user_context: Optional[UserContext],
                                     request_context: Dict[str, Any],
                                     auth_details: Optional[Dict[str, Any]] = None) -> None:
        """
        Monitor authentication attempt and update security metrics.
        
        Args:
            success: Whether authentication was successful
            user_context: User context information
            request_context: Request context information
            auth_details: Additional authentication details
        """
        try:
            with self._lock:
                # Update metrics
                self._security_metrics.total_requests += 1
                if success:
                    self._security_metrics.authenticated_requests += 1
                else:
                    self._security_metrics.failed_authentications += 1
                
                # Extract context information
                client_ip = request_context.get('client_ip', 'unknown')
                user_agent = request_context.get('user_agent', 'unknown')
                path = request_context.get('path', 'unknown')
                
                # Update unique counters
                if client_ip != 'unknown':
                    self._security_metrics.unique_ips = len(set([client_ip] + 
                        [event.get('client_ip') for event in self._recent_events 
                         if event.get('client_ip') != 'unknown']))
                
                if user_context and user_context.user_id:
                    self._update_user_security_profile(user_context, success, client_ip)
                
                # Handle failed attempts
                if not success:
                    self._handle_failed_authentication(client_ip, user_context, request_context)
                
                # Detect suspicious patterns
                if self.enable_real_time_monitoring:
                    self._detect_suspicious_activity(user_context, request_context, success)
                
                # Log authentication event
                self._log_authentication_event(success, user_context, request_context, auth_details)
                
                # Update last updated timestamp
                self._security_metrics.last_updated = datetime.now(timezone.utc).isoformat()
        
        except Exception as e:
            logger.error(f"Failed to monitor authentication attempt: {e}")
    
    def monitor_request_validation(self, validation_result: Any, user_context: Optional[UserContext],
                                 request_context: Dict[str, Any]) -> None:
        """
        Monitor request validation results for security violations.
        
        Args:
            validation_result: Result from request validation
            user_context: User context information
            request_context: Request context information
        """
        try:
            with self._lock:
                # Check if validation failed
                if not validation_result.is_valid:
                    self._security_metrics.validation_failures += 1
                    
                    # Check for security violations
                    critical_violations = [
                        v for v in validation_result.violations
                        if v.severity == ValidationSeverity.CRITICAL
                    ]
                    
                    if critical_violations:
                        self._security_metrics.security_violations += 1
                        
                        # Create security alert
                        self._create_security_alert(
                            "validation_security_violation",
                            ErrorSeverity.HIGH,
                            "Critical Validation Violations Detected",
                            f"Detected {len(critical_violations)} critical validation violations",
                            [request_context.get('path', 'unknown')],
                            [v.message for v in critical_violations],
                            ["review_request_payload", "investigate_user_activity", "consider_ip_blocking"]
                        )
                
                # Process security events from validation
                for security_event in validation_result.security_events:
                    self._process_security_event(security_event, user_context, request_context)
                
                # Log validation monitoring
                self.audit_logger.log_authentication_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    user_context=user_context,
                    request_context=request_context,
                    outcome="validation_monitored",
                    details={
                        'is_valid': validation_result.is_valid,
                        'violations_count': len(validation_result.violations),
                        'security_events_count': len(validation_result.security_events),
                        'validation_time_ms': validation_result.validation_time_ms
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed to monitor request validation: {e}")
    
    def monitor_mcp_tool_access(self, tool_name: str, parameters: Dict[str, Any],
                              user_context: UserContext, request_context: Dict[str, Any],
                              execution_result: Optional[Dict[str, Any]] = None) -> None:
        """
        Monitor MCP tool access for security and audit purposes.
        
        Args:
            tool_name: Name of MCP tool accessed
            parameters: Tool parameters (sanitized)
            user_context: User context information
            request_context: Request context information
            execution_result: Tool execution result
        """
        try:
            with self._lock:
                # Log MCP tool access
                self.audit_logger.log_mcp_tool_access(
                    tool_name=tool_name,
                    user_context=user_context,
                    request_context=request_context,
                    parameters=parameters,
                    outcome="success" if execution_result and execution_result.get('success') else "unknown",
                    duration_ms=execution_result.get('duration_ms') if execution_result else None
                )
                
                # Check for suspicious tool usage patterns
                if self.enable_real_time_monitoring:
                    self._detect_suspicious_tool_usage(tool_name, parameters, user_context, request_context)
                
                # Update user profile
                if user_context.user_id in self._user_profiles:
                    profile = self._user_profiles[user_context.user_id]
                    profile.total_requests += 1
                    profile.last_seen = datetime.now(timezone.utc).isoformat()
        
        except Exception as e:
            logger.error(f"Failed to monitor MCP tool access: {e}")
    
    def process_security_event(self, security_event: SecurityEvent,
                             user_context: Optional[UserContext] = None,
                             request_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Process security event and trigger appropriate responses.
        
        Args:
            security_event: Security event to process
            user_context: User context information
            request_context: Request context information
        """
        try:
            with self._lock:
                # Add to recent events
                event_data = asdict(security_event)
                if user_context:
                    event_data['user_context'] = user_context.to_dict()
                if request_context:
                    event_data['request_context'] = request_context
                
                self._recent_events.append(event_data)
                
                # Update metrics
                self._security_metrics.security_violations += 1
                
                # Process with correlator if enabled
                if self.security_correlator:
                    threat_patterns = self.security_correlator.process_security_event(security_event)
                    
                    if threat_patterns:
                        self._security_metrics.threat_patterns_detected += len(threat_patterns)
                        
                        # Create alerts for high-severity patterns
                        for pattern in threat_patterns:
                            if pattern.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                                self._create_threat_pattern_alert(pattern)
                
                # Automated response if enabled
                if self.enable_automated_response:
                    self._trigger_automated_response(security_event, user_context, request_context)
                
                # Log security event
                security_logger.warning(f"SECURITY_EVENT: {json.dumps(event_data, default=str)}")
        
        except Exception as e:
            logger.error(f"Failed to process security event: {e}")
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        """
        Check if IP address is currently blocked.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if IP is blocked
        """
        try:
            with self._lock:
                if client_ip in self._blocked_ips:
                    block_until = self._blocked_ips[client_ip]
                    current_time = datetime.now(timezone.utc).timestamp()
                    
                    if current_time < block_until:
                        return True
                    else:
                        # Remove expired block
                        del self._blocked_ips[client_ip]
                        return False
                
                return False
        
        except Exception as e:
            logger.error(f"Failed to check IP block status: {e}")
            return False
    
    def get_security_metrics(self, time_period: str = "24h") -> SecurityMetrics:
        """
        Get current security metrics.
        
        Args:
            time_period: Time period for metrics
            
        Returns:
            Security metrics object
        """
        try:
            with self._lock:
                metrics = SecurityMetrics(
                    total_requests=self._security_metrics.total_requests,
                    authenticated_requests=self._security_metrics.authenticated_requests,
                    failed_authentications=self._security_metrics.failed_authentications,
                    blocked_requests=len(self._blocked_ips),
                    security_violations=self._security_metrics.security_violations,
                    validation_failures=self._security_metrics.validation_failures,
                    threat_patterns_detected=self._security_metrics.threat_patterns_detected,
                    unique_users=len(self._user_profiles),
                    unique_ips=self._security_metrics.unique_ips,
                    time_period=time_period,
                    last_updated=self._security_metrics.last_updated
                )
                
                return metrics
        
        except Exception as e:
            logger.error(f"Failed to get security metrics: {e}")
            return SecurityMetrics(time_period=time_period)
    
    def get_security_alerts(self, severity_filter: Optional[ErrorSeverity] = None,
                          status_filter: Optional[str] = None,
                          limit: int = 50) -> List[SecurityAlert]:
        """
        Get security alerts with optional filtering.
        
        Args:
            severity_filter: Optional severity filter
            status_filter: Optional status filter
            limit: Maximum number of alerts to return
            
        Returns:
            List of security alerts
        """
        try:
            with self._lock:
                alerts = list(self._security_alerts.values())
                
                # Apply filters
                if severity_filter:
                    alerts = [a for a in alerts if a.severity == severity_filter]
                
                if status_filter:
                    alerts = [a for a in alerts if a.status == status_filter]
                
                # Sort by creation time (newest first)
                alerts.sort(key=lambda x: x.created_at, reverse=True)
                
                return alerts[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get security alerts: {e}")
            return []
    
    def get_user_security_profiles(self, risk_threshold: float = 0.5,
                                 limit: int = 100) -> List[UserSecurityProfile]:
        """
        Get user security profiles with optional risk filtering.
        
        Args:
            risk_threshold: Minimum risk score to include
            limit: Maximum number of profiles to return
            
        Returns:
            List of user security profiles
        """
        try:
            with self._lock:
                profiles = [
                    profile for profile in self._user_profiles.values()
                    if profile.risk_score >= risk_threshold
                ]
                
                # Sort by risk score (highest first)
                profiles.sort(key=lambda x: x.risk_score, reverse=True)
                
                return profiles[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get user security profiles: {e}")
            return []
    
    def get_threat_patterns(self, threat_level: Optional[ThreatLevel] = None,
                          limit: int = 20) -> List[ThreatPattern]:
        """
        Get detected threat patterns.
        
        Args:
            threat_level: Optional threat level filter
            limit: Maximum number of patterns to return
            
        Returns:
            List of threat patterns
        """
        try:
            if self.security_correlator:
                return self.security_correlator.get_threat_patterns(
                    threat_level=threat_level,
                    limit=limit
                )
            else:
                return []
        
        except Exception as e:
            logger.error(f"Failed to get threat patterns: {e}")
            return []
    
    def _handle_failed_authentication(self, client_ip: str, user_context: Optional[UserContext],
                                    request_context: Dict[str, Any]) -> None:
        """Handle failed authentication attempt."""
        current_time = datetime.now(timezone.utc).timestamp()
        
        # Add failed attempt
        self._failed_attempts[client_ip].append(current_time)
        
        # Clean old attempts
        cutoff_time = current_time - self.lockout_duration
        while (self._failed_attempts[client_ip] and 
               self._failed_attempts[client_ip][0] < cutoff_time):
            self._failed_attempts[client_ip].popleft()
        
        # Check if should block IP
        if len(self._failed_attempts[client_ip]) >= self.max_failed_attempts:
            self._blocked_ips[client_ip] = current_time + self.lockout_duration
            self._security_metrics.blocked_requests += 1
            
            # Create security event
            security_event = SecurityEvent(
                event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
                severity=ErrorSeverity.HIGH,
                timestamp=datetime.now(timezone.utc).isoformat(),
                client_ip=client_ip,
                user_agent=request_context.get('user_agent'),
                path=request_context.get('path'),
                error_message=f"IP blocked due to {len(self._failed_attempts[client_ip])} failed attempts",
                additional_data={
                    'lockout_duration': self.lockout_duration,
                    'failed_attempts': len(self._failed_attempts[client_ip])
                }
            )
            
            self.process_security_event(security_event, user_context, request_context)
    
    def _update_user_security_profile(self, user_context: UserContext, success: bool, client_ip: str) -> None:
        """Update user security profile."""
        user_id = user_context.user_id
        current_time = datetime.now(timezone.utc).isoformat()
        
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserSecurityProfile(
                user_id=user_id,
                username=user_context.username,
                first_seen=current_time,
                last_seen=current_time,
                total_requests=0,
                failed_attempts=0,
                successful_logins=0,
                unique_ips=set(),
                suspicious_activities=0,
                risk_score=0.0
            )
        
        profile = self._user_profiles[user_id]
        profile.total_requests += 1
        profile.last_seen = current_time
        profile.unique_ips.add(client_ip)
        
        if success:
            profile.successful_logins += 1
        else:
            profile.failed_attempts += 1
        
        # Calculate risk score
        profile.risk_score = self._calculate_user_risk_score(profile)
        
        # Update unique users count
        self._security_metrics.unique_users = len(self._user_profiles)
    
    def _calculate_user_risk_score(self, profile: UserSecurityProfile) -> float:
        """Calculate user risk score based on behavior."""
        risk_score = 0.0
        
        # Failed attempts ratio
        if profile.total_requests > 0:
            failure_rate = profile.failed_attempts / profile.total_requests
            risk_score += failure_rate * 0.4
        
        # Suspicious activities
        if profile.total_requests > 0:
            suspicious_rate = profile.suspicious_activities / profile.total_requests
            risk_score += suspicious_rate * 0.3
        
        # Multiple IPs (potential account sharing or compromise)
        if len(profile.unique_ips) > 5:
            risk_score += min(0.2, len(profile.unique_ips) * 0.02)
        
        # Recent activity pattern
        try:
            last_seen = datetime.fromisoformat(profile.last_seen.replace('Z', '+00:00'))
            hours_since_last = (datetime.now(timezone.utc) - last_seen).total_seconds() / 3600
            
            if hours_since_last > 168:  # More than a week
                risk_score += 0.1
        except:
            pass
        
        return min(1.0, risk_score)
    
    def _detect_suspicious_activity(self, user_context: Optional[UserContext],
                                  request_context: Dict[str, Any], success: bool) -> None:
        """Detect suspicious activity patterns."""
        client_ip = request_context.get('client_ip', '')
        user_agent = request_context.get('user_agent', '')
        path = request_context.get('path', '')
        
        suspicious_indicators = []
        
        # Check user agent patterns
        for pattern in self._compiled_patterns['user_agents']:
            if pattern.search(user_agent):
                suspicious_indicators.append(f"Suspicious user agent: {pattern.pattern}")
        
        # Check path patterns
        for pattern in self._compiled_patterns['paths']:
            if pattern.search(path):
                suspicious_indicators.append(f"Suspicious path access: {pattern.pattern}")
        
        # Check for private IP in public context
        try:
            ip = ipaddress.ip_address(client_ip)
            if ip.is_private and not self._is_allowed_private_ip(client_ip):
                suspicious_indicators.append("Private IP in public context")
        except ValueError:
            pass
        
        # Check for rapid requests from same IP
        recent_requests = [
            event for event in self._recent_events
            if (event.get('client_ip') == client_ip and
                (datetime.now(timezone.utc) - 
                 datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00'))).total_seconds() < 60)
        ]
        
        if len(recent_requests) > 20:  # More than 20 requests per minute
            suspicious_indicators.append(f"Rapid requests: {len(recent_requests)} in last minute")
        
        # Create security events for suspicious indicators
        for indicator in suspicious_indicators:
            security_event = SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.now(timezone.utc).isoformat(),
                client_ip=client_ip,
                user_agent=user_agent,
                path=path,
                user_id=user_context.user_id if user_context else None,
                error_message=indicator,
                additional_data={'success': success}
            )
            
            self.process_security_event(security_event, user_context, request_context)
            
            # Update user profile
            if user_context and user_context.user_id in self._user_profiles:
                self._user_profiles[user_context.user_id].suspicious_activities += 1
    
    def _detect_suspicious_tool_usage(self, tool_name: str, parameters: Dict[str, Any],
                                    user_context: UserContext, request_context: Dict[str, Any]) -> None:
        """Detect suspicious MCP tool usage patterns."""
        suspicious_indicators = []
        
        # Check for parameter injection attempts
        param_str = json.dumps(parameters, default=str).lower()
        
        for pattern in self._compiled_patterns['parameters']:
            if pattern.search(param_str):
                suspicious_indicators.append(f"Suspicious parameter pattern: {pattern.pattern}")
        
        # Check for excessive parameter sizes
        if len(param_str) > 10000:
            suspicious_indicators.append(f"Excessive parameter size: {len(param_str)}")
        
        # Check for unusual tool usage patterns
        user_recent_tools = [
            event for event in self._recent_events
            if (event.get('user_context', {}).get('user_id') == user_context.user_id and
                'mcp_tool' in event.get('event_type', ''))
        ]
        
        if len(user_recent_tools) > 50:  # More than 50 tool calls recently
            suspicious_indicators.append(f"Excessive tool usage: {len(user_recent_tools)} recent calls")
        
        # Create security events
        for indicator in suspicious_indicators:
            security_event = SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.now(timezone.utc).isoformat(),
                client_ip=request_context.get('client_ip'),
                user_id=user_context.user_id,
                error_message=f"Suspicious MCP tool usage: {indicator}",
                additional_data={
                    'tool_name': tool_name,
                    'parameter_size': len(param_str)
                }
            )
            
            self.process_security_event(security_event, user_context, request_context)
    
    def _create_security_alert(self, alert_type: str, severity: ErrorSeverity,
                             title: str, description: str, affected_resources: List[str],
                             threat_indicators: List[str], recommended_actions: List[str]) -> str:
        """Create security alert."""
        alert_id = hashlib.md5(f"{alert_type}:{title}:{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            affected_resources=affected_resources,
            threat_indicators=threat_indicators,
            recommended_actions=recommended_actions,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        self._security_alerts[alert_id] = alert
        
        # Log alert creation
        security_logger.critical(f"SECURITY_ALERT: {json.dumps(asdict(alert), default=str)}")
        
        return alert_id
    
    def _create_threat_pattern_alert(self, threat_pattern: ThreatPattern) -> str:
        """Create alert from threat pattern."""
        return self._create_security_alert(
            alert_type="threat_pattern_detected",
            severity=ErrorSeverity.HIGH if threat_pattern.threat_level == ThreatLevel.HIGH else ErrorSeverity.CRITICAL,
            title=f"Threat Pattern Detected: {threat_pattern.description}",
            description=f"Security correlator detected threat pattern with {threat_pattern.confidence_score:.2f} confidence",
            affected_resources=list(threat_pattern.affected_users) + list(threat_pattern.affected_ips),
            threat_indicators=threat_pattern.indicators,
            recommended_actions=threat_pattern.recommended_actions
        )
    
    def _trigger_automated_response(self, security_event: SecurityEvent,
                                  user_context: Optional[UserContext],
                                  request_context: Optional[Dict[str, Any]]) -> None:
        """Trigger automated response to security event."""
        try:
            # Block IP for high-severity events
            if (security_event.severity == ErrorSeverity.CRITICAL and 
                security_event.client_ip and 
                security_event.client_ip not in self._blocked_ips):
                
                current_time = datetime.now(timezone.utc).timestamp()
                self._blocked_ips[security_event.client_ip] = current_time + self.lockout_duration
                
                logger.warning(f"Automatically blocked IP {security_event.client_ip} due to critical security event")
            
            # Additional automated responses can be added here
            # - Rate limiting
            # - User account suspension
            # - Alert notifications
            # - Integration with external security systems
            
        except Exception as e:
            logger.error(f"Failed to trigger automated response: {e}")
    
    def _log_authentication_event(self, success: bool, user_context: Optional[UserContext],
                                request_context: Dict[str, Any], auth_details: Optional[Dict[str, Any]]) -> None:
        """Log authentication event for audit purposes."""
        try:
            event_type = AuditEventType.USER_LOGIN if success else AuditEventType.SECURITY_VIOLATION
            
            details = {
                'authentication_success': success,
                'client_ip': request_context.get('client_ip'),
                'user_agent': request_context.get('user_agent'),
                'path': request_context.get('path'),
                'method': request_context.get('method')
            }
            
            if auth_details:
                details.update(auth_details)
            
            self.audit_logger.log_authentication_event(
                event_type=event_type,
                user_context=user_context,
                request_context=request_context,
                outcome="success" if success else "failure",
                details=details
            )
        
        except Exception as e:
            logger.error(f"Failed to log authentication event: {e}")
    
    def _is_allowed_private_ip(self, ip: str) -> bool:
        """Check if private IP is allowed."""
        allowed_ranges = [
            '10.0.0.0/8',      # Internal VPC
            '172.16.0.0/12',   # Docker networks
            '192.168.0.0/16'   # Local networks
        ]
        
        try:
            ip_addr = ipaddress.ip_address(ip)
            for range_str in allowed_ranges:
                if ip_addr in ipaddress.ip_network(range_str):
                    return True
        except ValueError:
            pass
        
        return False


# Global security monitor instance
_security_monitor = None
_monitor_lock = None


def get_security_monitor() -> SecurityMonitor:
    """Get global security monitor instance."""
    global _security_monitor, _monitor_lock
    
    if _monitor_lock is None:
        import threading
        _monitor_lock = threading.Lock()
    
    with _monitor_lock:
        if _security_monitor is None:
            _security_monitor = SecurityMonitor()
        
        return _security_monitor


# Export main classes
__all__ = [
    'SecurityMonitor',
    'SecurityMetrics',
    'SecurityAlert',
    'UserSecurityProfile',
    'get_security_monitor'
]