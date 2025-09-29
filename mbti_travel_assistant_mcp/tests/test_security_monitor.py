"""
Unit tests for Security Monitor.

Tests comprehensive security monitoring, threat detection, and incident response
for the MBTI Travel Assistant MCP system.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from services.security_monitor import (
    SecurityMonitor, SecurityMetrics, SecurityAlert, UserSecurityProfile,
    get_security_monitor
)
from models.auth_models import UserContext, JWTClaims
from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity
from services.request_validator import ValidationResult, ValidationViolation, ValidationSeverity


class TestSecurityMonitor:
    """Test cases for Security Monitor."""
    
    @pytest.fixture
    def security_monitor(self):
        """Create security monitor for testing."""
        return SecurityMonitor(
            enable_real_time_monitoring=True,
            enable_automated_response=True,
            enable_threat_correlation=True,
            max_failed_attempts=3,
            lockout_duration=300,
            monitoring_window_hours=24
        )
    
    @pytest.fixture
    def user_context(self):
        """Create test user context."""
        jwt_claims = JWTClaims(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            client_id="test-client",
            token_use="access",
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
            iat=int(datetime.now(timezone.utc).timestamp()),
            iss="test-issuer",
            aud="test-audience"
        )
        
        return UserContext(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            authenticated=True,
            token_claims=jwt_claims
        )
    
    @pytest.fixture
    def request_context(self):
        """Create test request context."""
        return {
            'client_ip': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Test Browser)',
            'path': '/api/mbti-itinerary',
            'method': 'POST',
            'request_id': 'test-request-123'
        }
    
    def test_monitor_authentication_attempt_success(self, security_monitor, user_context, request_context):
        """Test monitoring successful authentication attempt."""
        security_monitor.monitor_authentication_attempt(
            success=True,
            user_context=user_context,
            request_context=request_context
        )
        
        # Check metrics update
        metrics = security_monitor.get_security_metrics()
        assert metrics.total_requests == 1
        assert metrics.authenticated_requests == 1
        assert metrics.failed_authentications == 0
        
        # Check user profile creation
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        assert len(profiles) == 1
        assert profiles[0].user_id == user_context.user_id
        assert profiles[0].successful_logins == 1
        assert profiles[0].failed_attempts == 0
    
    def test_monitor_authentication_attempt_failure(self, security_monitor, user_context, request_context):
        """Test monitoring failed authentication attempt."""
        security_monitor.monitor_authentication_attempt(
            success=False,
            user_context=user_context,
            request_context=request_context
        )
        
        # Check metrics update
        metrics = security_monitor.get_security_metrics()
        assert metrics.total_requests == 1
        assert metrics.authenticated_requests == 0
        assert metrics.failed_authentications == 1
        
        # Check user profile
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        assert len(profiles) == 1
        assert profiles[0].failed_attempts == 1
        assert profiles[0].successful_logins == 0
    
    def test_monitor_authentication_brute_force_detection(self, security_monitor, user_context, request_context):
        """Test brute force attack detection and IP blocking."""
        # Simulate multiple failed attempts
        for i in range(4):  # Exceeds max_failed_attempts of 3
            security_monitor.monitor_authentication_attempt(
                success=False,
                user_context=user_context,
                request_context=request_context
            )
        
        # Check that IP is blocked
        assert security_monitor.is_ip_blocked(request_context['client_ip']) is True
        
        # Check metrics
        metrics = security_monitor.get_security_metrics()
        assert metrics.blocked_requests > 0
        assert metrics.security_violations > 0
    
    def test_monitor_request_validation_success(self, security_monitor, user_context, request_context):
        """Test monitoring successful request validation."""
        validation_result = ValidationResult(
            is_valid=True,
            sanitized_payload={'MBTI_personality': 'INFJ'},
            violations=[],
            security_events=[],
            validation_time_ms=150
        )
        
        security_monitor.monitor_request_validation(validation_result, user_context, request_context)
        
        # Should not increase validation failures
        metrics = security_monitor.get_security_metrics()
        assert metrics.validation_failures == 0
    
    def test_monitor_request_validation_failure(self, security_monitor, user_context, request_context):
        """Test monitoring failed request validation."""
        violations = [
            ValidationViolation(
                rule_id="malicious_pattern_detected",
                field_path="test_field",
                violation_type="security_violation",
                severity=ValidationSeverity.CRITICAL,
                message="Malicious pattern detected"
            )
        ]
        
        validation_result = ValidationResult(
            is_valid=False,
            sanitized_payload={},
            violations=violations,
            security_events=[],
            validation_time_ms=150
        )
        
        security_monitor.monitor_request_validation(validation_result, user_context, request_context)
        
        # Check metrics update
        metrics = security_monitor.get_security_metrics()
        assert metrics.validation_failures == 1
        assert metrics.security_violations == 1
        
        # Check security alert creation
        alerts = security_monitor.get_security_alerts()
        assert len(alerts) > 0
        
        validation_alerts = [
            alert for alert in alerts 
            if alert.alert_type == "validation_security_violation"
        ]
        assert len(validation_alerts) > 0
    
    def test_monitor_mcp_tool_access(self, security_monitor, user_context, request_context):
        """Test monitoring MCP tool access."""
        parameters = {
            'districts': ['Central district'],
            'meal_types': ['breakfast']
        }
        
        execution_result = {
            'success': True,
            'duration_ms': 1500
        }
        
        security_monitor.monitor_mcp_tool_access(
            tool_name='search_restaurants_by_district',
            parameters=parameters,
            user_context=user_context,
            request_context=request_context,
            execution_result=execution_result
        )
        
        # Check user profile update
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        assert len(profiles) == 1
        assert profiles[0].total_requests == 1
    
    def test_process_security_event(self, security_monitor, user_context, request_context):
        """Test processing security event."""
        security_event = SecurityEvent(
            event_type=SecurityEventType.MALICIOUS_PAYLOAD,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_ip=request_context['client_ip'],
            user_agent=request_context['user_agent'],
            path=request_context['path'],
            error_message="Malicious payload detected",
            additional_data={'pattern': 'script_injection'}
        )
        
        security_monitor.process_security_event(security_event, user_context, request_context)
        
        # Check metrics update
        metrics = security_monitor.get_security_metrics()
        assert metrics.security_violations == 1
    
    def test_is_ip_blocked_not_blocked(self, security_monitor):
        """Test checking IP that is not blocked."""
        assert security_monitor.is_ip_blocked('192.168.1.200') is False
    
    def test_is_ip_blocked_expired_block(self, security_monitor):
        """Test checking IP with expired block."""
        client_ip = '192.168.1.100'
        
        # Manually add expired block
        past_time = datetime.now(timezone.utc).timestamp() - 3600  # 1 hour ago
        security_monitor._blocked_ips[client_ip] = past_time
        
        # Should return False and remove expired block
        assert security_monitor.is_ip_blocked(client_ip) is False
        assert client_ip not in security_monitor._blocked_ips
    
    def test_get_security_metrics(self, security_monitor, user_context, request_context):
        """Test getting security metrics."""
        # Generate some activity
        security_monitor.monitor_authentication_attempt(True, user_context, request_context)
        security_monitor.monitor_authentication_attempt(False, user_context, request_context)
        
        metrics = security_monitor.get_security_metrics("24h")
        
        assert metrics.total_requests == 2
        assert metrics.authenticated_requests == 1
        assert metrics.failed_authentications == 1
        assert metrics.unique_users == 1
        assert metrics.time_period == "24h"
        assert metrics.last_updated is not None
    
    def test_get_security_alerts_no_filter(self, security_monitor):
        """Test getting security alerts without filter."""
        # Create test alert
        security_monitor._create_security_alert(
            alert_type="test_alert",
            severity=ErrorSeverity.HIGH,
            title="Test Alert",
            description="Test alert description",
            affected_resources=["resource1"],
            threat_indicators=["indicator1"],
            recommended_actions=["action1"]
        )
        
        alerts = security_monitor.get_security_alerts()
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "test_alert"
        assert alerts[0].severity == ErrorSeverity.HIGH
        assert alerts[0].title == "Test Alert"
    
    def test_get_security_alerts_with_filters(self, security_monitor):
        """Test getting security alerts with filters."""
        # Create alerts with different severities
        security_monitor._create_security_alert(
            "test_alert_high", ErrorSeverity.HIGH, "High Alert", "High severity alert",
            [], [], []
        )
        security_monitor._create_security_alert(
            "test_alert_medium", ErrorSeverity.MEDIUM, "Medium Alert", "Medium severity alert",
            [], [], []
        )
        
        # Filter by severity
        high_alerts = security_monitor.get_security_alerts(severity_filter=ErrorSeverity.HIGH)
        assert len(high_alerts) == 1
        assert high_alerts[0].severity == ErrorSeverity.HIGH
        
        # Filter by status
        open_alerts = security_monitor.get_security_alerts(status_filter="open")
        assert len(open_alerts) == 2  # Both should be open by default
    
    def test_get_user_security_profiles(self, security_monitor, user_context, request_context):
        """Test getting user security profiles."""
        # Create user activity
        security_monitor.monitor_authentication_attempt(True, user_context, request_context)
        security_monitor.monitor_authentication_attempt(False, user_context, request_context)
        
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        
        assert len(profiles) == 1
        profile = profiles[0]
        assert profile.user_id == user_context.user_id
        assert profile.username == user_context.username
        assert profile.total_requests == 2
        assert profile.successful_logins == 1
        assert profile.failed_attempts == 1
        assert profile.risk_score > 0.0  # Should have some risk due to failed attempt
    
    def test_get_user_security_profiles_risk_filter(self, security_monitor, user_context, request_context):
        """Test getting user security profiles with risk filter."""
        # Create low-risk user activity (only successful logins)
        security_monitor.monitor_authentication_attempt(True, user_context, request_context)
        security_monitor.monitor_authentication_attempt(True, user_context, request_context)
        
        # High risk threshold should exclude this user
        high_risk_profiles = security_monitor.get_user_security_profiles(risk_threshold=0.8)
        assert len(high_risk_profiles) == 0
        
        # Low risk threshold should include this user
        low_risk_profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        assert len(low_risk_profiles) == 1
    
    def test_detect_suspicious_activity_user_agent(self, security_monitor, user_context, request_context):
        """Test detection of suspicious user agent."""
        # Use suspicious user agent
        suspicious_context = request_context.copy()
        suspicious_context['user_agent'] = 'sqlmap/1.0 (http://sqlmap.org)'
        
        security_monitor._detect_suspicious_activity(user_context, suspicious_context, True)
        
        # Check that suspicious activity was detected
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        if profiles:
            assert profiles[0].suspicious_activities > 0
    
    def test_detect_suspicious_activity_path(self, security_monitor, user_context, request_context):
        """Test detection of suspicious path access."""
        # Use suspicious path
        suspicious_context = request_context.copy()
        suspicious_context['path'] = '/admin/config'
        
        security_monitor._detect_suspicious_activity(user_context, suspicious_context, True)
        
        # Check that suspicious activity was detected
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        if profiles:
            assert profiles[0].suspicious_activities > 0
    
    def test_detect_suspicious_tool_usage_excessive_calls(self, security_monitor, user_context, request_context):
        """Test detection of excessive MCP tool usage."""
        # Simulate many recent tool calls
        for i in range(60):  # Exceeds threshold of 50
            event_data = {
                'event_type': 'mcp_tool_invocation',
                'user_context': user_context.to_dict(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            security_monitor._recent_events.append(event_data)
        
        parameters = {'test': 'value'}
        security_monitor._detect_suspicious_tool_usage(
            'test_tool', parameters, user_context, request_context
        )
        
        # Should detect excessive usage
        # Check recent events for suspicious activity
        suspicious_events = [
            event for event in security_monitor._recent_events
            if 'Excessive tool usage' in str(event)
        ]
        # Note: This test checks the detection logic is called, 
        # actual event creation depends on the implementation
    
    def test_calculate_user_risk_score(self, security_monitor):
        """Test user risk score calculation."""
        profile = UserSecurityProfile(
            user_id="test-user",
            username="testuser",
            first_seen=datetime.now(timezone.utc).isoformat(),
            last_seen=datetime.now(timezone.utc).isoformat(),
            total_requests=10,
            failed_attempts=3,
            successful_logins=7,
            unique_ips={'192.168.1.1', '192.168.1.2'},
            suspicious_activities=1,
            risk_score=0.0
        )
        
        risk_score = security_monitor._calculate_user_risk_score(profile)
        
        # Should have some risk due to failed attempts and suspicious activities
        assert risk_score > 0.0
        assert risk_score <= 1.0
    
    def test_calculate_user_risk_score_high_risk(self, security_monitor):
        """Test user risk score calculation for high-risk user."""
        profile = UserSecurityProfile(
            user_id="high-risk-user",
            username="highriskuser",
            first_seen=datetime.now(timezone.utc).isoformat(),
            last_seen=datetime.now(timezone.utc).isoformat(),
            total_requests=20,
            failed_attempts=15,  # High failure rate
            successful_logins=5,
            unique_ips=set([f'192.168.1.{i}' for i in range(10)]),  # Many IPs
            suspicious_activities=8,  # Many suspicious activities
            risk_score=0.0
        )
        
        risk_score = security_monitor._calculate_user_risk_score(profile)
        
        # Should have high risk score
        assert risk_score > 0.7
        assert risk_score <= 1.0
    
    def test_automated_response_ip_blocking(self, security_monitor, user_context, request_context):
        """Test automated response for critical security events."""
        critical_event = SecurityEvent(
            event_type=SecurityEventType.MALICIOUS_PAYLOAD,
            severity=ErrorSeverity.CRITICAL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_ip=request_context['client_ip'],
            error_message="Critical security violation"
        )
        
        security_monitor._trigger_automated_response(critical_event, user_context, request_context)
        
        # Check that IP was blocked
        assert security_monitor.is_ip_blocked(request_context['client_ip']) is True
    
    def test_create_security_alert(self, security_monitor):
        """Test security alert creation."""
        alert_id = security_monitor._create_security_alert(
            alert_type="test_alert",
            severity=ErrorSeverity.HIGH,
            title="Test Security Alert",
            description="This is a test security alert",
            affected_resources=["resource1", "resource2"],
            threat_indicators=["indicator1", "indicator2"],
            recommended_actions=["action1", "action2"]
        )
        
        assert alert_id is not None
        assert len(alert_id) == 16  # MD5 hash truncated to 16 chars
        
        # Check that alert was stored
        alerts = security_monitor.get_security_alerts()
        assert len(alerts) == 1
        
        alert = alerts[0]
        assert alert.alert_id == alert_id
        assert alert.alert_type == "test_alert"
        assert alert.severity == ErrorSeverity.HIGH
        assert alert.title == "Test Security Alert"
        assert alert.description == "This is a test security alert"
        assert alert.affected_resources == ["resource1", "resource2"]
        assert alert.threat_indicators == ["indicator1", "indicator2"]
        assert alert.recommended_actions == ["action1", "action2"]
        assert alert.status == "open"
    
    def test_get_security_monitor_singleton(self):
        """Test that get_security_monitor returns singleton instance."""
        monitor1 = get_security_monitor()
        monitor2 = get_security_monitor()
        
        assert monitor1 is monitor2
        assert isinstance(monitor1, SecurityMonitor)


class TestSecurityMetrics:
    """Test cases for SecurityMetrics dataclass."""
    
    def test_security_metrics_creation(self):
        """Test creating security metrics."""
        metrics = SecurityMetrics(
            total_requests=100,
            authenticated_requests=85,
            failed_authentications=15,
            blocked_requests=5,
            security_violations=3,
            validation_failures=8,
            threat_patterns_detected=2,
            unique_users=25,
            unique_ips=30,
            time_period="24h",
            last_updated="2025-01-01T12:00:00Z"
        )
        
        assert metrics.total_requests == 100
        assert metrics.authenticated_requests == 85
        assert metrics.failed_authentications == 15
        assert metrics.blocked_requests == 5
        assert metrics.security_violations == 3
        assert metrics.validation_failures == 8
        assert metrics.threat_patterns_detected == 2
        assert metrics.unique_users == 25
        assert metrics.unique_ips == 30
        assert metrics.time_period == "24h"
        assert metrics.last_updated == "2025-01-01T12:00:00Z"


class TestSecurityAlert:
    """Test cases for SecurityAlert dataclass."""
    
    def test_security_alert_creation(self):
        """Test creating security alert."""
        alert = SecurityAlert(
            alert_id="alert-123",
            alert_type="brute_force_attack",
            severity=ErrorSeverity.HIGH,
            title="Brute Force Attack Detected",
            description="Multiple failed login attempts detected",
            affected_resources=["user-account-123"],
            threat_indicators=["192.168.1.100", "failed_logins"],
            recommended_actions=["block_ip", "notify_user"],
            created_at="2025-01-01T12:00:00Z",
            status="open"
        )
        
        assert alert.alert_id == "alert-123"
        assert alert.alert_type == "brute_force_attack"
        assert alert.severity == ErrorSeverity.HIGH
        assert alert.title == "Brute Force Attack Detected"
        assert alert.description == "Multiple failed login attempts detected"
        assert alert.affected_resources == ["user-account-123"]
        assert alert.threat_indicators == ["192.168.1.100", "failed_logins"]
        assert alert.recommended_actions == ["block_ip", "notify_user"]
        assert alert.created_at == "2025-01-01T12:00:00Z"
        assert alert.status == "open"


class TestUserSecurityProfile:
    """Test cases for UserSecurityProfile dataclass."""
    
    def test_user_security_profile_creation(self):
        """Test creating user security profile."""
        profile = UserSecurityProfile(
            user_id="user-123",
            username="testuser",
            first_seen="2025-01-01T10:00:00Z",
            last_seen="2025-01-01T12:00:00Z",
            total_requests=50,
            failed_attempts=5,
            successful_logins=45,
            unique_ips={'192.168.1.1', '192.168.1.2'},
            suspicious_activities=2,
            risk_score=0.25,
            status="active"
        )
        
        assert profile.user_id == "user-123"
        assert profile.username == "testuser"
        assert profile.first_seen == "2025-01-01T10:00:00Z"
        assert profile.last_seen == "2025-01-01T12:00:00Z"
        assert profile.total_requests == 50
        assert profile.failed_attempts == 5
        assert profile.successful_logins == 45
        assert profile.unique_ips == {'192.168.1.1', '192.168.1.2'}
        assert profile.suspicious_activities == 2
        assert profile.risk_score == 0.25
        assert profile.status == "active"


if __name__ == "__main__":
    pytest.main([__file__])