"""
Unit tests for Request Validator.

Tests request payload validation, sanitization, and security violation detection
for the MBTI Travel Assistant MCP system.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from services.request_validator import (
    RequestValidator, ValidationResult, ValidationViolation, ValidationSeverity,
    ValidationRuleType, get_request_validator
)
from models.auth_models import UserContext, JWTClaims
from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity


class TestRequestValidator:
    """Test cases for Request Validator."""
    
    @pytest.fixture
    def request_validator(self):
        """Create request validator for testing."""
        return RequestValidator(
            enable_security_monitoring=True,
            enable_audit_logging=True,
            max_payload_size=1024,
            max_string_length=100
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
    
    def test_validate_mbti_request_valid(self, request_validator, user_context, request_context):
        """Test validation of valid MBTI request."""
        payload = {
            'MBTI_personality': 'INFJ',
            'user_preferences': {
                'budget': 'medium',
                'interests': ['culture', 'food']
            }
        }
        
        result = request_validator.validate_mbti_request(payload, user_context, request_context)
        
        assert result.is_valid is True
        assert result.sanitized_payload['MBTI_personality'] == 'INFJ'
        assert len(result.violations) == 0
        assert len(result.security_events) == 0
        assert result.validation_time_ms > 0
    
    def test_validate_mbti_request_missing_required_field(self, request_validator, user_context, request_context):
        """Test validation with missing required field."""
        payload = {
            'user_preferences': {
                'budget': 'medium'
            }
        }
        
        result = request_validator.validate_mbti_request(payload, user_context, request_context)
        
        assert result.is_valid is False
        assert len(result.violations) > 0
        
        # Check for missing field violation
        missing_field_violations = [
            v for v in result.violations 
            if v.rule_id == "required_field_missing" and v.field_path == "MBTI_personality"
        ]
        assert len(missing_field_violations) == 1
        assert missing_field_violations[0].severity == ValidationSeverity.ERROR
    
    def test_validate_mbti_request_invalid_personality(self, request_validator, user_context, request_context):
        """Test validation with invalid MBTI personality."""
        payload = {
            'MBTI_personality': 'INVALID'
        }
        
        result = request_validator.validate_mbti_request(payload, user_context, request_context)
        
        assert result.is_valid is False
        
        # Check for MBTI validation violations
        mbti_violations = [
            v for v in result.violations 
            if v.field_path == "MBTI_personality"
        ]
        assert len(mbti_violations) > 0
    
    def test_validate_mbti_request_malicious_payload(self, request_validator, user_context, request_context):
        """Test validation with malicious payload."""
        payload = {
            'MBTI_personality': 'INFJ',
            'malicious_field': '<script>alert("xss")</script>',
            'sql_injection': "'; DROP TABLE users; --"
        }
        
        result = request_validator.validate_mbti_request(payload, user_context, request_context)
        
        assert result.is_valid is False
        assert len(result.security_events) > 0
        
        # Check for security violations
        critical_violations = [
            v for v in result.violations 
            if v.severity == ValidationSeverity.CRITICAL
        ]
        assert len(critical_violations) > 0
        
        # Check that malicious content was sanitized
        assert '<script>' not in str(result.sanitized_payload)
    
    def test_validate_mbti_request_oversized_payload(self, request_validator, user_context, request_context):
        """Test validation with oversized payload."""
        # Create large payload
        large_data = 'x' * 2000  # Exceeds max_payload_size of 1024
        payload = {
            'MBTI_personality': 'INFJ',
            'large_field': large_data
        }
        
        result = request_validator.validate_mbti_request(payload, user_context, request_context)
        
        assert result.is_valid is False
        
        # Check for size violation
        size_violations = [
            v for v in result.violations 
            if v.rule_id == "payload_size_limit"
        ]
        assert len(size_violations) == 1
        assert size_violations[0].severity == ValidationSeverity.ERROR
    
    def test_validate_mcp_parameters_restaurant_search(self, request_validator, user_context, request_context):
        """Test validation of restaurant search parameters."""
        parameters = {
            'districts': ['Central district', 'Admiralty'],
            'meal_types': ['breakfast', 'lunch']
        }
        
        result = request_validator.validate_mcp_parameters(
            'search_restaurants_by_district', parameters, user_context, request_context
        )
        
        assert result.is_valid is True
        assert result.sanitized_payload['districts'] == ['Central district', 'Admiralty']
        assert result.sanitized_payload['meal_types'] == ['breakfast', 'lunch']
    
    def test_validate_mcp_parameters_invalid_meal_types(self, request_validator, user_context, request_context):
        """Test validation with invalid meal types."""
        parameters = {
            'meal_types': ['breakfast', 'invalid_meal', 'lunch']
        }
        
        result = request_validator.validate_mcp_parameters(
            'search_restaurants_by_meal_type', parameters, user_context, request_context
        )
        
        assert result.is_valid is True  # Should still be valid, just with warnings
        assert 'invalid_meal' not in result.sanitized_payload['meal_types']
        
        # Check for validation warnings
        meal_type_violations = [
            v for v in result.violations 
            if v.rule_id == "meal_type_invalid"
        ]
        assert len(meal_type_violations) == 1
    
    def test_validate_mcp_parameters_too_many_districts(self, request_validator, user_context, request_context):
        """Test validation with too many districts."""
        parameters = {
            'districts': [f'District_{i}' for i in range(25)]  # Exceeds limit of 20
        }
        
        result = request_validator.validate_mcp_parameters(
            'search_restaurants_by_district', parameters, user_context, request_context
        )
        
        assert result.is_valid is True  # Should be valid but with warnings
        assert len(result.sanitized_payload['districts']) == 20  # Should be truncated
        
        # Check for size violation
        size_violations = [
            v for v in result.violations 
            if v.rule_id == "districts_too_many"
        ]
        assert len(size_violations) == 1
    
    def test_validate_mcp_parameters_restaurant_recommendation(self, request_validator, user_context, request_context):
        """Test validation of restaurant recommendation parameters."""
        parameters = {
            'restaurants': [
                {'id': 'rest_1', 'name': 'Restaurant 1'},
                {'id': 'rest_2', 'name': 'Restaurant 2'}
            ],
            'ranking_method': 'sentiment_likes'
        }
        
        result = request_validator.validate_mcp_parameters(
            'recommend_restaurants', parameters, user_context, request_context
        )
        
        assert result.is_valid is True
        assert result.sanitized_payload['ranking_method'] == 'sentiment_likes'
        assert len(result.sanitized_payload['restaurants']) == 2
    
    def test_validate_mcp_parameters_invalid_ranking_method(self, request_validator, user_context, request_context):
        """Test validation with invalid ranking method."""
        parameters = {
            'restaurants': [{'id': 'rest_1', 'name': 'Restaurant 1'}],
            'ranking_method': 'invalid_method'
        }
        
        result = request_validator.validate_mcp_parameters(
            'recommend_restaurants', parameters, user_context, request_context
        )
        
        assert result.is_valid is True  # Should be valid with default value
        assert result.sanitized_payload['ranking_method'] == 'sentiment_likes'  # Default
        
        # Check for validation warning
        ranking_violations = [
            v for v in result.violations 
            if v.rule_id == "ranking_method_invalid"
        ]
        assert len(ranking_violations) == 1
    
    def test_sanitize_sensitive_data(self, request_validator):
        """Test sanitization of sensitive data."""
        data = {
            'username': 'testuser',
            'password': 'secret123',
            'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'api_key': 'sk-1234567890',
            'normal_field': 'normal_value',
            'nested': {
                'authorization': 'Bearer token123',
                'public_data': 'visible'
            },
            'long_string': 'x' * 1500  # Very long string
        }
        
        sanitized = request_validator.sanitize_sensitive_data(data)
        
        # Check that sensitive fields are redacted
        assert sanitized['password'] == '***REDACTED***'
        assert sanitized['jwt_token'] == '***REDACTED***'
        assert sanitized['api_key'] == '***REDACTED***'
        assert sanitized['nested']['authorization'] == '***REDACTED***'
        
        # Check that normal fields are preserved
        assert sanitized['username'] == 'testuser'
        assert sanitized['normal_field'] == 'normal_value'
        assert sanitized['nested']['public_data'] == 'visible'
        
        # Check that long strings are truncated
        assert len(sanitized['long_string']) <= 1003  # 1000 + '...[TRUNCATED]'
        assert sanitized['long_string'].endswith('...[TRUNCATED]')
    
    def test_detect_security_violations(self, request_validator, request_context):
        """Test security violation detection."""
        malicious_payload = {
            'field1': '<script>alert("xss")</script>',
            'field2': "'; DROP TABLE users; --",
            'field3': 'UNION SELECT * FROM passwords',
            'field4': '../../../etc/passwd',
            'field5': 'normal_value'
        }
        
        security_events = request_validator.detect_security_violations(malicious_payload, request_context)
        
        assert len(security_events) > 0
        
        # Check for malicious payload events
        malicious_events = [
            event for event in security_events 
            if event.event_type == SecurityEventType.MALICIOUS_PAYLOAD
        ]
        assert len(malicious_events) > 0
        
        # Check event details
        for event in malicious_events:
            assert event.severity == ErrorSeverity.HIGH
            assert event.client_ip == request_context['client_ip']
            assert 'Malicious pattern detected' in event.error_message
    
    def test_detect_security_violations_large_payload(self, request_validator, request_context):
        """Test detection of unusually large payload."""
        large_payload = {
            'large_field': 'x' * 60000  # Very large payload
        }
        
        security_events = request_validator.detect_security_violations(large_payload, request_context)
        
        # Check for suspicious activity event
        large_payload_events = [
            event for event in security_events 
            if 'large payload' in event.error_message.lower()
        ]
        assert len(large_payload_events) > 0
        assert large_payload_events[0].severity == ErrorSeverity.MEDIUM
    
    def test_detect_security_violations_excessive_nesting(self, request_validator, request_context):
        """Test detection of excessive payload nesting."""
        # Create deeply nested payload
        nested_payload = {}
        current = nested_payload
        for i in range(15):  # Exceeds limit of 10
            current['nested'] = {}
            current = current['nested']
        current['value'] = 'deep_value'
        
        security_events = request_validator.detect_security_violations(nested_payload, request_context)
        
        # Check for excessive nesting event
        nesting_events = [
            event for event in security_events 
            if 'nesting depth' in event.error_message.lower()
        ]
        assert len(nesting_events) > 0
        assert nesting_events[0].severity == ErrorSeverity.MEDIUM
    
    def test_string_field_validation_length_exceeded(self, request_validator):
        """Test string field validation with length exceeded."""
        long_string = 'x' * 150  # Exceeds max_string_length of 100
        
        violations, security_events, sanitized_value = request_validator._validate_string_field(
            'test_field', long_string, 'test_context'
        )
        
        # Check for length violation
        length_violations = [
            v for v in violations 
            if v.rule_id == "string_length_exceeded"
        ]
        assert len(length_violations) == 1
        assert length_violations[0].severity == ValidationSeverity.WARNING
        
        # Check that value was truncated
        assert len(sanitized_value) == 100
    
    def test_string_field_validation_html_sanitization(self, request_validator):
        """Test HTML content sanitization."""
        html_string = '<div>Hello <script>alert("xss")</script> World</div>'
        
        violations, security_events, sanitized_value = request_validator._validate_string_field(
            'test_field', html_string, 'test_context'
        )
        
        # Check that HTML was escaped
        assert '&lt;' in sanitized_value
        assert '&gt;' in sanitized_value
        assert '<script>' not in sanitized_value
        
        # Check for sanitization violation
        html_violations = [
            v for v in violations 
            if v.rule_id == "html_content_sanitized"
        ]
        assert len(html_violations) == 1
    
    def test_mbti_personality_validation_valid(self, request_validator):
        """Test MBTI personality validation with valid values."""
        valid_types = ['INTJ', 'INFP', 'ENFJ', 'ESTP']
        
        for mbti_type in valid_types:
            violations, security_events = request_validator._validate_mbti_personality(mbti_type)
            assert len(violations) == 0
            assert len(security_events) == 0
    
    def test_mbti_personality_validation_invalid_length(self, request_validator):
        """Test MBTI personality validation with invalid length."""
        violations, security_events = request_validator._validate_mbti_personality('INF')
        
        length_violations = [
            v for v in violations 
            if v.rule_id == "mbti_invalid_length"
        ]
        assert len(length_violations) == 1
        assert length_violations[0].severity == ValidationSeverity.ERROR
    
    def test_mbti_personality_validation_invalid_type(self, request_validator):
        """Test MBTI personality validation with invalid type."""
        violations, security_events = request_validator._validate_mbti_personality(123)
        
        type_violations = [
            v for v in violations 
            if v.rule_id == "mbti_invalid_type"
        ]
        assert len(type_violations) == 1
        assert type_violations[0].severity == ValidationSeverity.ERROR
    
    def test_mbti_personality_validation_invalid_value(self, request_validator):
        """Test MBTI personality validation with invalid value."""
        violations, security_events = request_validator._validate_mbti_personality('XXXX')
        
        value_violations = [
            v for v in violations 
            if v.rule_id == "mbti_invalid_value"
        ]
        assert len(value_violations) == 1
        assert value_violations[0].severity == ValidationSeverity.ERROR
    
    def test_get_request_validator_singleton(self):
        """Test that get_request_validator returns singleton instance."""
        validator1 = get_request_validator()
        validator2 = get_request_validator()
        
        assert validator1 is validator2
        assert isinstance(validator1, RequestValidator)


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating validation result."""
        violations = [
            ValidationViolation(
                rule_id="test_rule",
                field_path="test_field",
                violation_type="test_violation",
                severity=ValidationSeverity.WARNING,
                message="Test violation message"
            )
        ]
        
        security_events = [
            SecurityEvent(
                event_type=SecurityEventType.MALICIOUS_PAYLOAD,
                severity=ErrorSeverity.HIGH,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_message="Test security event"
            )
        ]
        
        result = ValidationResult(
            is_valid=False,
            sanitized_payload={'field': 'value'},
            violations=violations,
            security_events=security_events,
            validation_time_ms=150
        )
        
        assert result.is_valid is False
        assert result.sanitized_payload == {'field': 'value'}
        assert len(result.violations) == 1
        assert len(result.security_events) == 1
        assert result.validation_time_ms == 150


class TestValidationViolation:
    """Test cases for ValidationViolation dataclass."""
    
    def test_validation_violation_creation(self):
        """Test creating validation violation."""
        violation = ValidationViolation(
            rule_id="test_rule",
            field_path="test.field",
            violation_type="format_error",
            severity=ValidationSeverity.ERROR,
            message="Invalid format",
            original_value="invalid_value",
            sanitized_value="sanitized_value"
        )
        
        assert violation.rule_id == "test_rule"
        assert violation.field_path == "test.field"
        assert violation.violation_type == "format_error"
        assert violation.severity == ValidationSeverity.ERROR
        assert violation.message == "Invalid format"
        assert violation.original_value == "invalid_value"
        assert violation.sanitized_value == "sanitized_value"
        assert violation.timestamp is not None
    
    def test_validation_violation_auto_timestamp(self):
        """Test automatic timestamp generation."""
        violation = ValidationViolation(
            rule_id="test_rule",
            field_path="test_field",
            violation_type="test_violation",
            severity=ValidationSeverity.INFO,
            message="Test message"
        )
        
        # Check that timestamp was automatically set
        assert violation.timestamp is not None
        
        # Parse timestamp to ensure it's valid
        timestamp = datetime.fromisoformat(violation.timestamp.replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)


if __name__ == "__main__":
    pytest.main([__file__])