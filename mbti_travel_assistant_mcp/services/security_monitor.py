"""
Security logging and monitoring system for authentication events.

This module provides comprehensive security event logging, audit trails,
and monitoring for suspicious authentication patterns.
"""

import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from threading import Lock
import re
import ipaddress

from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity


# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)


@dataclass
class UserSession:
    """User session information for audit logging."""
    user_id: str
    username: str
    email: str
    session_start: str
    last_activity: str
    client_ip: str
    user_agent: str
    session_id: Optional[str] = None


@dataclass
class SecurityMetrics:
    """Security metrics for monitoring dashboard."""
    total_auth_attempts: int = 0
    successful_auths: int = 0
    failed_auths: int = 0
    token_validations: int = 0
    token_failures: int = 0
    suspicious_activities: int = 0
    blocked_ips: int = 0
    unique_users: int = 0
    time_period: str = ""


@dataclass
class ThreatIndicator:
    """Threat indicator for security monitoring."""
    indicator_type: str
    value: str
    severity: ErrorSeverity
    first_seen: str
    last_seen: str
    count: int
    description: str
    source: str


class SecurityMonitor:
    """
    Comprehensive security monitoring and logging system.
    
    Provides security event logging, audit trails, threat detection,
    and monitoring for authentication-related security events.
    """
    
    def __init__(self, enable_audit_logging: bool = True,
                 enable_threat_detection: bool = True,
                 max_failed_attempts: int = 5,
                 lockout_duration: int = 300,
                 suspicious_threshold: int = 10):
        """
        Initialize security monitor.
        
        Args:
            enable_audit_logging: Whether to enable audit logging
            enable_threat_detection: Whether to enable threat detection
            max_failed_attempts: Maximum failed attempts before lockout
            lockout_duration: Lockout duration in seconds
            suspicious_threshold: Threshold for suspicious activity detection
        """
        self.enable_audit_logging = enable_audit_logging
        self.enable_threat_detection = enable_threat_detection
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = lockout_duration
        self.suspicious_threshold = suspicious_threshold
        
        # Thread-safe data structures
        self._lock = Lock()
        
        # Security monitoring state
        self._failed_attempts = defaultdict(deque)  # IP -> deque of timestamps
        self._blocked_ips = {}  # IP -> block_until_timestamp
        self._user_sessions = {}  # session_id -> UserSession
        self._threat_indicators = {}  # indicator_value -> ThreatIndicator
        self._security_metrics = SecurityMetrics()
        
        # Suspicious patterns
        self._suspicious_user_agents = [
            r'bot', r'crawler', r'spider', r'scraper', r'scanner',
            r'curl', r'wget', r'python-requests', r'postman',
            r'nikto', r'sqlmap', r'nmap', r'masscan'
        ]
        
        self._suspicious_paths = [
            r'/admin', r'/wp-admin', r'/phpmyadmin', r'/config',
            r'/\.env', r'/\.git', r'/backup', r'/test'
        ]
        
        security_logger.info("Security monitor initialized")
    
    def log_authentication_attempt(self, success: bool, user_context: Dict[str, Any],
                                 request_context: Dict[str, Any]) -> None:
        """
        Log authentication attempt for audit and monitoring.
        
        Args:
            success: Whether authentication was successful
            user_context: User context information
            request_context: Request context information
        """
        try:
            with self._lock:
                # Update metrics
                self._security_metrics.total_auth_attempts += 1
                if success:
                    self._security_metrics.successful_auths += 1
                else:
                    self._security_metrics.failed_auths += 1
                
                # Create audit log entry
                audit_entry = {
                    'event_type': 'authentication_attempt',
                    'success': success,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'user_id': user_context.get('user_id', 'unknown'),
                    'username': user_context.get('username', 'unknown'),
                    'client_ip': request_context.get('client_ip', 'unknown'),
                    'user_agent': self._sanitize_user_agent(request_context.get('user_agent', 'unknown')),
                    'path': request_context.get('path', 'unknown'),
                    'method': request_context.get('method', 'unknown'),
                    'request_id': request_context.get('request_id', 'unknown')
                }
                
                # Log to audit logger
                if self.enable_audit_logging:
                    audit_logger.info(f"AUTH_ATTEMPT: {json.dumps(audit_entry)}")
                
                # Handle failed attempts
                if not success:
                    self._handle_failed_attempt(request_context)
                else:
                    self._handle_successful_attempt(user_context, request_context)
                
                # Check for suspicious activity
                if self.enable_threat_detection:
                    self._detect_threats(user_context, request_context, success)
        
        except Exception as e:
            security_logger.error(f"Failed to log authentication attempt: {e}")
    
    def log_token_validation(self, success: bool, token_info: Dict[str, Any],
                           request_context: Dict[str, Any]) -> None:
        """
        Log JWT token validation for audit and monitoring.
        
        Args:
            success: Whether token validation was successful
            token_info: Token information (masked)
            request_context: Request context information
        """
        try:
            with self._lock:
                # Update metrics
                self._security_metrics.token_validations += 1
                if not success:
                    self._security_metrics.token_failures += 1
                
                # Create audit log entry
                audit_entry = {
                    'event_type': 'token_validation',
                    'success': success,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'token_type': token_info.get('token_type', 'unknown'),
                    'token_exp': token_info.get('exp', 0),
                    'token_iat': token_info.get('iat', 0),
                    'client_id': token_info.get('client_id', 'unknown'),
                    'user_id': token_info.get('user_id', 'unknown'),
                    'client_ip': request_context.get('client_ip', 'unknown'),
                    'path': request_context.get('path', 'unknown'),
                    'method': request_context.get('method', 'unknown'),
                    'request_id': request_context.get('request_id', 'unknown')
                }
                
                # Log to audit logger
                if self.enable_audit_logging:
                    audit_logger.info(f"TOKEN_VALIDATION: {json.dumps(audit_entry)}")
        
        except Exception as e:
            security_logger.error(f"Failed to log token validation: {e}")
    
    def log_mcp_tool_invocation(self, tool_name: str, user_context: Dict[str, Any],
                              request_context: Dict[str, Any], 
                              parameters: Dict[str, Any] = None) -> None:
        """
        Log MCP tool invocation for audit trail.
        
        Args:
            tool_name: Name of MCP tool invoked
            user_context: User context information
            request_context: Request context information
            parameters: Tool parameters (sanitized)
        """
        try:
            # Sanitize parameters to remove sensitive data
            sanitized_params = self._sanitize_parameters(parameters or {})
            
            audit_entry = {
                'event_type': 'mcp_tool_invocation',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'tool_name': tool_name,
                'user_id': user_context.get('user_id', 'unknown'),
                'username': user_context.get('username', 'unknown'),
                'client_ip': request_context.get('client_ip', 'unknown'),
                'path': request_context.get('path', 'unknown'),
                'method': request_context.get('method', 'unknown'),
                'parameters': sanitized_params,
                'request_id': request_context.get('request_id', 'unknown')
            }
            
            # Log to audit logger
            if self.enable_audit_logging:
                audit_logger.info(f"MCP_TOOL: {json.dumps(audit_entry)}")
        
        except Exception as e:
            security_logger.error(f"Failed to log MCP tool invocation: {e}")
    
    def log_security_event(self, security_event: SecurityEvent) -> None:
        """
        Log security event for monitoring and alerting.
        
        Args:
            security_event: Security event to log
        """
        try:
            # Log to security logger with appropriate level
            log_level = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(security_event.severity, logging.WARNING)
            
            security_logger.log(
                log_level,
                f"SECURITY_EVENT: {json.dumps(asdict(security_event), default=str)}"
            )
            
            # Update threat indicators
            if self.enable_threat_detection:
                self._update_threat_indicators(security_event)
        
        except Exception as e:
            security_logger.error(f"Failed to log security event: {e}")
    
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
            security_logger.error(f"Failed to check IP block status: {e}")
            return False
    
    def get_security_metrics(self, time_period: str = "1h") -> SecurityMetrics:
        """
        Get security metrics for monitoring dashboard.
        
        Args:
            time_period: Time period for metrics (1h, 24h, 7d)
            
        Returns:
            Security metrics object
        """
        try:
            with self._lock:
                metrics = SecurityMetrics(
                    total_auth_attempts=self._security_metrics.total_auth_attempts,
                    successful_auths=self._security_metrics.successful_auths,
                    failed_auths=self._security_metrics.failed_auths,
                    token_validations=self._security_metrics.token_validations,
                    token_failures=self._security_metrics.token_failures,
                    suspicious_activities=self._security_metrics.suspicious_activities,
                    blocked_ips=len(self._blocked_ips),
                    unique_users=len(self._user_sessions),
                    time_period=time_period
                )
                
                return metrics
        
        except Exception as e:
            security_logger.error(f"Failed to get security metrics: {e}")
            return SecurityMetrics(time_period=time_period)
    
    def get_threat_indicators(self, limit: int = 100) -> List[ThreatIndicator]:
        """
        Get current threat indicators.
        
        Args:
            limit: Maximum number of indicators to return
            
        Returns:
            List of threat indicators
        """
        try:
            with self._lock:
                indicators = list(self._threat_indicators.values())
                # Sort by severity and count
                indicators.sort(key=lambda x: (x.severity.value, x.count), reverse=True)
                return indicators[:limit]
        
        except Exception as e:
            security_logger.error(f"Failed to get threat indicators: {e}")
            return []
    
    def _handle_failed_attempt(self, request_context: Dict[str, Any]) -> None:
        """Handle failed authentication attempt."""
        client_ip = request_context.get('client_ip', 'unknown')
        current_time = datetime.now(timezone.utc).timestamp()
        
        # Add failed attempt
        self._failed_attempts[client_ip].append(current_time)
        
        # Clean old attempts (older than lockout duration)
        cutoff_time = current_time - self.lockout_duration
        while (self._failed_attempts[client_ip] and 
               self._failed_attempts[client_ip][0] < cutoff_time):
            self._failed_attempts[client_ip].popleft()
        
        # Check if should block IP
        if len(self._failed_attempts[client_ip]) >= self.max_failed_attempts:
            self._blocked_ips[client_ip] = current_time + self.lockout_duration
            
            # Log security event
            security_event = SecurityEvent(
                event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
                severity=ErrorSeverity.HIGH,
                timestamp=datetime.now(timezone.utc).isoformat(),
                client_ip=client_ip,
                error_message=f"IP blocked due to {len(self._failed_attempts[client_ip])} failed attempts",
                additional_data={'lockout_duration': self.lockout_duration}
            )
            
            self.log_security_event(security_event)
    
    def _handle_successful_attempt(self, user_context: Dict[str, Any],
                                 request_context: Dict[str, Any]) -> None:
        """Handle successful authentication attempt."""
        client_ip = request_context.get('client_ip', 'unknown')
        
        # Clear failed attempts for this IP
        if client_ip in self._failed_attempts:
            self._failed_attempts[client_ip].clear()
        
        # Create user session
        session_id = self._generate_session_id(user_context, request_context)
        user_session = UserSession(
            user_id=user_context.get('user_id', 'unknown'),
            username=user_context.get('username', 'unknown'),
            email=user_context.get('email', 'unknown'),
            session_start=datetime.now(timezone.utc).isoformat(),
            last_activity=datetime.now(timezone.utc).isoformat(),
            client_ip=client_ip,
            user_agent=self._sanitize_user_agent(request_context.get('user_agent', 'unknown')),
            session_id=session_id
        )
        
        self._user_sessions[session_id] = user_session
    
    def _detect_threats(self, user_context: Dict[str, Any],
                       request_context: Dict[str, Any], success: bool) -> None:
        """Detect potential security threats."""
        client_ip = request_context.get('client_ip', 'unknown')
        user_agent = request_context.get('user_agent', '')
        path = request_context.get('path', '')
        
        threats_detected = []
        
        # Check for suspicious user agents
        for pattern in self._suspicious_user_agents:
            if re.search(pattern, user_agent.lower()):
                threats_detected.append(f"Suspicious user agent: {pattern}")
        
        # Check for suspicious paths
        for pattern in self._suspicious_paths:
            if re.search(pattern, path.lower()):
                threats_detected.append(f"Suspicious path access: {pattern}")
        
        # Check for private IP ranges in public context
        try:
            ip = ipaddress.ip_address(client_ip)
            if ip.is_private and not self._is_allowed_private_ip(client_ip):
                threats_detected.append("Private IP in public context")
        except ValueError:
            pass  # Invalid IP format
        
        # Log threats
        for threat in threats_detected:
            self._security_metrics.suspicious_activities += 1
            
            security_event = SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.now(timezone.utc).isoformat(),
                client_ip=client_ip,
                user_agent=self._sanitize_user_agent(user_agent),
                path=path,
                error_message=threat,
                additional_data={'success': success}
            )
            
            self.log_security_event(security_event)
    
    def _update_threat_indicators(self, security_event: SecurityEvent) -> None:
        """Update threat indicators based on security event."""
        # Create threat indicators for various attributes
        indicators = []
        
        if security_event.client_ip and security_event.client_ip != 'unknown':
            indicators.append(('ip', security_event.client_ip))
        
        if security_event.user_agent:
            # Hash user agent for privacy
            ua_hash = hashlib.md5(security_event.user_agent.encode()).hexdigest()[:16]
            indicators.append(('user_agent_hash', ua_hash))
        
        if security_event.path:
            indicators.append(('path', security_event.path))
        
        # Update or create threat indicators
        for indicator_type, value in indicators:
            key = f"{indicator_type}:{value}"
            
            if key in self._threat_indicators:
                indicator = self._threat_indicators[key]
                indicator.count += 1
                indicator.last_seen = security_event.timestamp
                # Escalate severity if count is high
                if indicator.count > self.suspicious_threshold:
                    indicator.severity = ErrorSeverity.HIGH
            else:
                self._threat_indicators[key] = ThreatIndicator(
                    indicator_type=indicator_type,
                    value=value,
                    severity=security_event.severity,
                    first_seen=security_event.timestamp,
                    last_seen=security_event.timestamp,
                    count=1,
                    description=f"Threat indicator from {security_event.event_type.value}",
                    source="security_monitor"
                )
    
    def _sanitize_user_agent(self, user_agent: str) -> str:
        """Sanitize user agent string for logging."""
        # Limit length and remove potentially malicious content
        sanitized = user_agent[:200]  # Limit length
        sanitized = re.sub(r'[<>"\']', '', sanitized)  # Remove HTML/script chars
        return sanitized
    
    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters to remove sensitive data."""
        sanitized = {}
        
        for key, value in parameters.items():
            # Skip sensitive parameter names
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                sanitized[key] = value[:100] + '...'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _generate_session_id(self, user_context: Dict[str, Any],
                           request_context: Dict[str, Any]) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        user_id = user_context.get('user_id', 'unknown')
        client_ip = request_context.get('client_ip', 'unknown')
        
        session_data = f"{timestamp}:{user_id}:{client_ip}"
        return hashlib.sha256(session_data.encode()).hexdigest()[:16]
    
    def _is_allowed_private_ip(self, ip: str) -> bool:
        """Check if private IP is allowed (e.g., internal networks)."""
        # Define allowed private IP ranges for internal services
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
_monitor_lock = Lock()


def get_security_monitor() -> SecurityMonitor:
    """Get global security monitor instance."""
    global _security_monitor
    
    with _monitor_lock:
        if _security_monitor is None:
            _security_monitor = SecurityMonitor()
        
        return _security_monitor


# Export main classes
__all__ = [
    'SecurityMonitor',
    'UserSession',
    'SecurityMetrics',
    'ThreatIndicator',
    'get_security_monitor'
]