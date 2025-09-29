"""
Request Payload Validation and Sanitization Service for MBTI Travel Assistant MCP.

This module provides comprehensive request payload validation, sanitization,
and security monitoring for incoming HTTP requests and MCP tool invocations.
Implements requirements 8.4, 8.6, 8.7, and 8.8 from the specification.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import html
import urllib.parse
import ipaddress

from models.auth_models import UserContext
from services.audit_logger import get_audit_logger, AuditEventType
from services.security_event_correlator import SecurityEventCorrelator
from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity


# Configure logging
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationRuleType(Enum):
    """Types of validation rules."""
    FORMAT = "format"
    LENGTH = "length"
    CONTENT = "content"
    SECURITY = "security"
    BUSINESS = "business"


@dataclass
class ValidationRule:
    """Validation rule definition."""
    rule_id: str
    rule_type: ValidationRuleType
    field_path: str
    description: str
    severity: ValidationSeverity
    enabled: bool = True


@dataclass
class ValidationViolation:
    """Validation violation result."""
    rule_id: str
    field_path: str
    violation_type: str
    severity: ValidationSeverity
    message: str
    original_value: Optional[str] = None
    sanitized_value: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class ValidationResult:
    """Result of payload validation."""
    is_valid: bool
    sanitized_payload: Dict[str, Any]
    violations: List[ValidationViolation]
    security_events: List[SecurityEvent]
    validation_time_ms: int


class RequestValidator:
    """
    Comprehensive request payload validation and sanitization service.
    
    Provides validation of HTTP request payloads, MCP tool parameters,
    security violation detection, and data sanitization for the MBTI
    Travel Assistant MCP system.
    """
    
    def __init__(self, enable_security_monitoring: bool = True,
                 enable_audit_logging: bool = True,
                 max_payload_size: int = 1024 * 1024,  # 1MB
                 max_string_length: int = 10000):
        """
        Initialize request validator.
        
        Args:
            enable_security_monitoring: Whether to enable security monitoring
            enable_audit_logging: Whether to enable audit logging
            max_payload_size: Maximum payload size in bytes
            max_string_length: Maximum string field length
        """
        self.enable_security_monitoring = enable_security_monitoring
        self.enable_audit_logging = enable_audit_logging
        self.max_payload_size = max_payload_size
        self.max_string_length = max_string_length
        
        # Initialize components
        self.audit_logger = get_audit_logger() if enable_audit_logging else None
        self.security_correlator = SecurityEventCorrelator() if enable_security_monitoring else None
        
        # Initialize validation rules
        self.validation_rules = self._initialize_validation_rules()
        
        # Security patterns
        self.malicious_patterns = [
            # SQL Injection patterns
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\'|\"|;|--|\*|\/\*|\*\/)',
            
            # XSS patterns
            r'(<script[^>]*>.*?</script>)',
            r'(javascript:|vbscript:|onload=|onerror=|onclick=)',
            r'(<iframe|<object|<embed|<applet)',
            
            # Command injection patterns
            r'(\||&|;|\$\(|\`)',
            r'(rm\s|del\s|format\s|shutdown\s)',
            
            # Path traversal patterns
            r'(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)',
            
            # LDAP injection patterns
            r'(\*|\(|\)|&|\||!)',
            
            # NoSQL injection patterns
            r'(\$where|\$ne|\$gt|\$lt|\$regex)',
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]
        
        logger.info("Request validator initialized")
    
    def validate_mbti_request(self, payload: Dict[str, Any],
                            user_context: Optional[UserContext] = None,
                            request_context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate MBTI itinerary request payload.
        
        Args:
            payload: Request payload to validate
            user_context: User context for audit logging
            request_context: Request context information
            
        Returns:
            ValidationResult with validation outcome
        """
        start_time = datetime.now()
        
        try:
            violations = []
            security_events = []
            sanitized_payload = {}
            
            # Validate payload size
            payload_size = len(json.dumps(payload).encode('utf-8'))
            if payload_size > self.max_payload_size:
                violations.append(ValidationViolation(
                    rule_id="payload_size_limit",
                    field_path="root",
                    violation_type="size_exceeded",
                    severity=ValidationSeverity.ERROR,
                    message=f"Payload size {payload_size} exceeds limit {self.max_payload_size}"
                ))
            
            # Validate required fields
            required_fields = ['MBTI_personality']
            for field in required_fields:
                if field not in payload:
                    violations.append(ValidationViolation(
                        rule_id="required_field_missing",
                        field_path=field,
                        violation_type="missing_field",
                        severity=ValidationSeverity.ERROR,
                        message=f"Required field '{field}' is missing"
                    ))
            
            # Validate and sanitize each field
            for field_path, value in payload.items():
                field_violations, field_security_events, sanitized_value = self._validate_field(
                    field_path, value, "mbti_request"
                )
                
                violations.extend(field_violations)
                security_events.extend(field_security_events)
                sanitized_payload[field_path] = sanitized_value
            
            # Specific MBTI personality validation
            if 'MBTI_personality' in payload:
                mbti_violations, mbti_events = self._validate_mbti_personality(
                    payload['MBTI_personality']
                )
                violations.extend(mbti_violations)
                security_events.extend(mbti_events)
            
            # Determine if validation passed
            is_valid = not any(v.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                             for v in violations)
            
            # Calculate validation time
            validation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log validation results
            self._log_validation_results(
                "mbti_request", is_valid, violations, security_events,
                user_context, request_context
            )
            
            return ValidationResult(
                is_valid=is_valid,
                sanitized_payload=sanitized_payload,
                violations=violations,
                security_events=security_events,
                validation_time_ms=validation_time_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to validate MBTI request: {e}")
            
            # Return failed validation result
            validation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ValidationResult(
                is_valid=False,
                sanitized_payload={},
                violations=[ValidationViolation(
                    rule_id="validation_error",
                    field_path="root",
                    violation_type="system_error",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation system error: {str(e)}"
                )],
                security_events=[],
                validation_time_ms=validation_time_ms
            )
    
    def validate_mcp_parameters(self, tool_name: str, parameters: Dict[str, Any],
                              user_context: Optional[UserContext] = None,
                              request_context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate MCP tool parameters.
        
        Args:
            tool_name: Name of MCP tool
            parameters: Tool parameters to validate
            user_context: User context for audit logging
            request_context: Request context information
            
        Returns:
            ValidationResult with validation outcome
        """
        start_time = datetime.now()
        
        try:
            violations = []
            security_events = []
            sanitized_parameters = {}
            
            # Validate parameters based on tool type
            if tool_name in ['search_restaurants_by_district', 'search_restaurants_by_meal_type']:
                violations, security_events, sanitized_parameters = self._validate_restaurant_search_params(
                    parameters
                )
            elif tool_name == 'recommend_restaurants':
                violations, security_events, sanitized_parameters = self._validate_restaurant_recommendation_params(
                    parameters
                )
            else:
                # Generic parameter validation
                for param_name, param_value in parameters.items():
                    field_violations, field_security_events, sanitized_value = self._validate_field(
                        param_name, param_value, "mcp_parameter"
                    )
                    
                    violations.extend(field_violations)
                    security_events.extend(field_security_events)
                    sanitized_parameters[param_name] = sanitized_value
            
            # Determine if validation passed
            is_valid = not any(v.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                             for v in violations)
            
            # Calculate validation time
            validation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log validation results
            self._log_validation_results(
                f"mcp_tool:{tool_name}", is_valid, violations, security_events,
                user_context, request_context
            )
            
            return ValidationResult(
                is_valid=is_valid,
                sanitized_payload=sanitized_parameters,
                violations=violations,
                security_events=security_events,
                validation_time_ms=validation_time_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to validate MCP parameters for {tool_name}: {e}")
            
            validation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ValidationResult(
                is_valid=False,
                sanitized_payload={},
                violations=[ValidationViolation(
                    rule_id="validation_error",
                    field_path="root",
                    violation_type="system_error",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"MCP parameter validation error: {str(e)}"
                )],
                security_events=[],
                validation_time_ms=validation_time_ms
            )
    
    def sanitize_sensitive_data(self, data: Dict[str, Any],
                              sensitive_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sanitize sensitive data for logging and audit purposes.
        
        Args:
            data: Data dictionary to sanitize
            sensitive_fields: List of sensitive field names
            
        Returns:
            Sanitized data dictionary
        """
        if sensitive_fields is None:
            sensitive_fields = [
                'password', 'token', 'secret', 'key', 'auth', 'credential',
                'jwt', 'bearer', 'authorization', 'session', 'cookie'
            ]
        
        sanitized = {}
        
        for key, value in data.items():
            # Check if field is sensitive
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self.sanitize_sensitive_data(value, sensitive_fields)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    self.sanitize_sensitive_data(item, sensitive_fields) if isinstance(item, dict)
                    else '***REDACTED***' if any(sensitive in str(item).lower() for sensitive in sensitive_fields)
                    else item
                    for item in value
                ]
            elif isinstance(value, str) and len(value) > 1000:
                # Truncate very long strings
                sanitized[key] = value[:1000] + '...[TRUNCATED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def detect_security_violations(self, payload: Dict[str, Any],
                                 request_context: Optional[Dict[str, Any]] = None) -> List[SecurityEvent]:
        """
        Detect security violations in request payload.
        
        Args:
            payload: Request payload to analyze
            request_context: Request context information
            
        Returns:
            List of detected security events
        """
        security_events = []
        
        try:
            # Check for malicious patterns in payload
            payload_str = json.dumps(payload, default=str).lower()
            
            for i, pattern in enumerate(self.compiled_patterns):
                matches = pattern.findall(payload_str)
                if matches:
                    security_events.append(SecurityEvent(
                        event_type=SecurityEventType.MALICIOUS_PAYLOAD,
                        severity=ErrorSeverity.HIGH,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        client_ip=request_context.get('client_ip') if request_context else None,
                        user_agent=request_context.get('user_agent') if request_context else None,
                        path=request_context.get('path') if request_context else None,
                        error_message=f"Malicious pattern detected: {matches[0][:50]}",
                        additional_data={
                            'pattern_index': i,
                            'matches_count': len(matches),
                            'payload_size': len(payload_str)
                        }
                    ))
            
            # Check for suspicious payload characteristics
            if len(payload_str) > 50000:  # Very large payload
                security_events.append(SecurityEvent(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    severity=ErrorSeverity.MEDIUM,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    client_ip=request_context.get('client_ip') if request_context else None,
                    error_message=f"Unusually large payload: {len(payload_str)} characters",
                    additional_data={'payload_size': len(payload_str)}
                ))
            
            # Check for excessive nesting
            max_depth = self._get_dict_depth(payload)
            if max_depth > 10:
                security_events.append(SecurityEvent(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    severity=ErrorSeverity.MEDIUM,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    client_ip=request_context.get('client_ip') if request_context else None,
                    error_message=f"Excessive payload nesting depth: {max_depth}",
                    additional_data={'nesting_depth': max_depth}
                ))
            
        except Exception as e:
            logger.error(f"Failed to detect security violations: {e}")
        
        return security_events
    
    def _validate_field(self, field_path: str, value: Any, 
                       context: str) -> Tuple[List[ValidationViolation], List[SecurityEvent], Any]:
        """Validate individual field value."""
        violations = []
        security_events = []
        sanitized_value = value
        
        try:
            # Type-specific validation
            if isinstance(value, str):
                violations, security_events, sanitized_value = self._validate_string_field(
                    field_path, value, context
                )
            elif isinstance(value, dict):
                violations, security_events, sanitized_value = self._validate_dict_field(
                    field_path, value, context
                )
            elif isinstance(value, list):
                violations, security_events, sanitized_value = self._validate_list_field(
                    field_path, value, context
                )
            elif isinstance(value, (int, float)):
                violations, security_events, sanitized_value = self._validate_numeric_field(
                    field_path, value, context
                )
            
        except Exception as e:
            violations.append(ValidationViolation(
                rule_id="field_validation_error",
                field_path=field_path,
                violation_type="validation_error",
                severity=ValidationSeverity.ERROR,
                message=f"Field validation error: {str(e)}",
                original_value=str(value)[:100]
            ))
        
        return violations, security_events, sanitized_value
    
    def _validate_string_field(self, field_path: str, value: str, 
                             context: str) -> Tuple[List[ValidationViolation], List[SecurityEvent], str]:
        """Validate string field."""
        violations = []
        security_events = []
        sanitized_value = value
        
        # Length validation
        if len(value) > self.max_string_length:
            violations.append(ValidationViolation(
                rule_id="string_length_exceeded",
                field_path=field_path,
                violation_type="length_exceeded",
                severity=ValidationSeverity.WARNING,
                message=f"String length {len(value)} exceeds maximum {self.max_string_length}",
                original_value=value[:100] + "..." if len(value) > 100 else value
            ))
            # Truncate the value
            sanitized_value = value[:self.max_string_length]
        
        # Security pattern detection
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(value):
                violations.append(ValidationViolation(
                    rule_id="malicious_pattern_detected",
                    field_path=field_path,
                    violation_type="security_violation",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Malicious pattern detected in field {field_path}",
                    original_value=value[:100] + "..." if len(value) > 100 else value
                ))
                
                security_events.append(SecurityEvent(
                    event_type=SecurityEventType.MALICIOUS_PAYLOAD,
                    severity=ErrorSeverity.HIGH,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error_message=f"Malicious pattern in field {field_path}",
                    additional_data={
                        'field_path': field_path,
                        'pattern_index': i,
                        'context': context
                    }
                ))
                
                # Sanitize the value by removing malicious content
                sanitized_value = pattern.sub('[REMOVED]', sanitized_value)
        
        # HTML/XML sanitization
        if '<' in value or '>' in value:
            sanitized_value = html.escape(sanitized_value)
            if sanitized_value != value:
                violations.append(ValidationViolation(
                    rule_id="html_content_sanitized",
                    field_path=field_path,
                    violation_type="content_sanitized",
                    severity=ValidationSeverity.INFO,
                    message="HTML content was sanitized",
                    original_value=value[:100] + "..." if len(value) > 100 else value,
                    sanitized_value=sanitized_value[:100] + "..." if len(sanitized_value) > 100 else sanitized_value
                ))
        
        # URL encoding for suspicious characters
        suspicious_chars = ['%', '&', '=', '+', '#']
        if any(char in value for char in suspicious_chars):
            url_encoded = urllib.parse.quote(value, safe='')
            if url_encoded != value:
                violations.append(ValidationViolation(
                    rule_id="suspicious_chars_encoded",
                    field_path=field_path,
                    violation_type="content_sanitized",
                    severity=ValidationSeverity.INFO,
                    message="Suspicious characters were URL encoded",
                    original_value=value[:100] + "..." if len(value) > 100 else value,
                    sanitized_value=url_encoded[:100] + "..." if len(url_encoded) > 100 else url_encoded
                ))
                sanitized_value = url_encoded
        
        return violations, security_events, sanitized_value
    
    def _validate_dict_field(self, field_path: str, value: Dict[str, Any], 
                           context: str) -> Tuple[List[ValidationViolation], List[SecurityEvent], Dict[str, Any]]:
        """Validate dictionary field."""
        violations = []
        security_events = []
        sanitized_value = {}
        
        # Validate dictionary size
        if len(value) > 100:  # Arbitrary limit
            violations.append(ValidationViolation(
                rule_id="dict_size_exceeded",
                field_path=field_path,
                violation_type="size_exceeded",
                severity=ValidationSeverity.WARNING,
                message=f"Dictionary has {len(value)} keys, which may be excessive"
            ))
        
        # Recursively validate nested fields
        for key, nested_value in value.items():
            nested_path = f"{field_path}.{key}"
            nested_violations, nested_events, nested_sanitized = self._validate_field(
                nested_path, nested_value, context
            )
            
            violations.extend(nested_violations)
            security_events.extend(nested_events)
            sanitized_value[key] = nested_sanitized
        
        return violations, security_events, sanitized_value
    
    def _validate_list_field(self, field_path: str, value: List[Any], 
                           context: str) -> Tuple[List[ValidationViolation], List[SecurityEvent], List[Any]]:
        """Validate list field."""
        violations = []
        security_events = []
        sanitized_value = []
        
        # Validate list size
        if len(value) > 1000:  # Arbitrary limit
            violations.append(ValidationViolation(
                rule_id="list_size_exceeded",
                field_path=field_path,
                violation_type="size_exceeded",
                severity=ValidationSeverity.WARNING,
                message=f"List has {len(value)} items, which may be excessive"
            ))
        
        # Validate list items
        for i, item in enumerate(value):
            item_path = f"{field_path}[{i}]"
            item_violations, item_events, item_sanitized = self._validate_field(
                item_path, item, context
            )
            
            violations.extend(item_violations)
            security_events.extend(item_events)
            sanitized_value.append(item_sanitized)
        
        return violations, security_events, sanitized_value
    
    def _validate_numeric_field(self, field_path: str, value: Union[int, float], 
                              context: str) -> Tuple[List[ValidationViolation], List[SecurityEvent], Union[int, float]]:
        """Validate numeric field."""
        violations = []
        security_events = []
        sanitized_value = value
        
        # Range validation (context-specific)
        if context == "mbti_request":
            # No specific numeric validation for MBTI requests currently
            pass
        elif context == "mcp_parameter":
            # Validate reasonable ranges for MCP parameters
            if isinstance(value, int) and (value < -1000000 or value > 1000000):
                violations.append(ValidationViolation(
                    rule_id="numeric_range_exceeded",
                    field_path=field_path,
                    violation_type="range_exceeded",
                    severity=ValidationSeverity.WARNING,
                    message=f"Numeric value {value} is outside reasonable range",
                    original_value=str(value)
                ))
                # Clamp the value
                sanitized_value = max(-1000000, min(1000000, value))
        
        return violations, security_events, sanitized_value
    
    def _validate_mbti_personality(self, mbti_value: str) -> Tuple[List[ValidationViolation], List[SecurityEvent]]:
        """Validate MBTI personality parameter."""
        violations = []
        security_events = []
        
        # MBTI format validation
        valid_mbti_types = [
            'INTJ', 'INTP', 'ENTJ', 'ENTP',
            'INFJ', 'INFP', 'ENFJ', 'ENFP',
            'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
            'ISTP', 'ISFP', 'ESTP', 'ESFP'
        ]
        
        if not isinstance(mbti_value, str):
            violations.append(ValidationViolation(
                rule_id="mbti_invalid_type",
                field_path="MBTI_personality",
                violation_type="type_error",
                severity=ValidationSeverity.ERROR,
                message="MBTI personality must be a string",
                original_value=str(mbti_value)
            ))
        elif len(mbti_value) != 4:
            violations.append(ValidationViolation(
                rule_id="mbti_invalid_length",
                field_path="MBTI_personality",
                violation_type="format_error",
                severity=ValidationSeverity.ERROR,
                message="MBTI personality must be exactly 4 characters",
                original_value=mbti_value
            ))
        elif mbti_value.upper() not in valid_mbti_types:
            violations.append(ValidationViolation(
                rule_id="mbti_invalid_value",
                field_path="MBTI_personality",
                violation_type="value_error",
                severity=ValidationSeverity.ERROR,
                message=f"Invalid MBTI personality type: {mbti_value}",
                original_value=mbti_value
            ))
        
        return violations, security_events
    
    def _validate_restaurant_search_params(self, parameters: Dict[str, Any]) -> Tuple[List[ValidationViolation], List[SecurityEvent], Dict[str, Any]]:
        """Validate restaurant search parameters."""
        violations = []
        security_events = []
        sanitized_params = {}
        
        # Validate districts parameter
        if 'districts' in parameters:
            districts = parameters['districts']
            if not isinstance(districts, list):
                violations.append(ValidationViolation(
                    rule_id="districts_invalid_type",
                    field_path="districts",
                    violation_type="type_error",
                    severity=ValidationSeverity.ERROR,
                    message="Districts parameter must be a list",
                    original_value=str(districts)
                ))
            elif len(districts) > 20:  # Reasonable limit
                violations.append(ValidationViolation(
                    rule_id="districts_too_many",
                    field_path="districts",
                    violation_type="size_exceeded",
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many districts specified: {len(districts)}",
                    original_value=str(districts)
                ))
                sanitized_params['districts'] = districts[:20]
            else:
                sanitized_params['districts'] = districts
        
        # Validate meal_types parameter
        if 'meal_types' in parameters:
            meal_types = parameters['meal_types']
            valid_meal_types = ['breakfast', 'lunch', 'dinner']
            
            if not isinstance(meal_types, list):
                violations.append(ValidationViolation(
                    rule_id="meal_types_invalid_type",
                    field_path="meal_types",
                    violation_type="type_error",
                    severity=ValidationSeverity.ERROR,
                    message="Meal types parameter must be a list",
                    original_value=str(meal_types)
                ))
            else:
                sanitized_meal_types = []
                for meal_type in meal_types:
                    if meal_type in valid_meal_types:
                        sanitized_meal_types.append(meal_type)
                    else:
                        violations.append(ValidationViolation(
                            rule_id="meal_type_invalid",
                            field_path="meal_types",
                            violation_type="value_error",
                            severity=ValidationSeverity.WARNING,
                            message=f"Invalid meal type: {meal_type}",
                            original_value=meal_type
                        ))
                
                sanitized_params['meal_types'] = sanitized_meal_types
        
        # Copy other parameters with basic validation
        for key, value in parameters.items():
            if key not in ['districts', 'meal_types']:
                field_violations, field_events, sanitized_value = self._validate_field(
                    key, value, "mcp_parameter"
                )
                violations.extend(field_violations)
                security_events.extend(field_events)
                sanitized_params[key] = sanitized_value
        
        return violations, security_events, sanitized_params
    
    def _validate_restaurant_recommendation_params(self, parameters: Dict[str, Any]) -> Tuple[List[ValidationViolation], List[SecurityEvent], Dict[str, Any]]:
        """Validate restaurant recommendation parameters."""
        violations = []
        security_events = []
        sanitized_params = {}
        
        # Validate restaurants parameter
        if 'restaurants' in parameters:
            restaurants = parameters['restaurants']
            if not isinstance(restaurants, list):
                violations.append(ValidationViolation(
                    rule_id="restaurants_invalid_type",
                    field_path="restaurants",
                    violation_type="type_error",
                    severity=ValidationSeverity.ERROR,
                    message="Restaurants parameter must be a list",
                    original_value=str(restaurants)[:100]
                ))
            elif len(restaurants) > 100:  # Reasonable limit
                violations.append(ValidationViolation(
                    rule_id="restaurants_too_many",
                    field_path="restaurants",
                    violation_type="size_exceeded",
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many restaurants specified: {len(restaurants)}",
                    original_value=f"List with {len(restaurants)} items"
                ))
                sanitized_params['restaurants'] = restaurants[:100]
            else:
                sanitized_params['restaurants'] = restaurants
        
        # Validate ranking_method parameter
        if 'ranking_method' in parameters:
            ranking_method = parameters['ranking_method']
            valid_methods = ['sentiment_likes', 'combined_sentiment']
            
            if ranking_method not in valid_methods:
                violations.append(ValidationViolation(
                    rule_id="ranking_method_invalid",
                    field_path="ranking_method",
                    violation_type="value_error",
                    severity=ValidationSeverity.WARNING,
                    message=f"Invalid ranking method: {ranking_method}",
                    original_value=ranking_method
                ))
                sanitized_params['ranking_method'] = 'sentiment_likes'  # Default
            else:
                sanitized_params['ranking_method'] = ranking_method
        
        # Copy other parameters with basic validation
        for key, value in parameters.items():
            if key not in ['restaurants', 'ranking_method']:
                field_violations, field_events, sanitized_value = self._validate_field(
                    key, value, "mcp_parameter"
                )
                violations.extend(field_violations)
                security_events.extend(field_events)
                sanitized_params[key] = sanitized_value
        
        return violations, security_events, sanitized_params
    
    def _get_dict_depth(self, d: Dict[str, Any], depth: int = 0) -> int:
        """Get maximum depth of nested dictionary."""
        if not isinstance(d, dict):
            return depth
        
        max_depth = depth
        for value in d.values():
            if isinstance(value, dict):
                max_depth = max(max_depth, self._get_dict_depth(value, depth + 1))
        
        return max_depth
    
    def _log_validation_results(self, validation_type: str, is_valid: bool,
                              violations: List[ValidationViolation],
                              security_events: List[SecurityEvent],
                              user_context: Optional[UserContext] = None,
                              request_context: Optional[Dict[str, Any]] = None) -> None:
        """Log validation results for audit and monitoring."""
        try:
            # Log to audit logger
            if self.audit_logger:
                event_type = AuditEventType.DATA_ACCESS if is_valid else AuditEventType.SECURITY_VIOLATION
                
                details = {
                    'validation_type': validation_type,
                    'is_valid': is_valid,
                    'violations_count': len(violations),
                    'security_events_count': len(security_events),
                    'violations': [
                        {
                            'rule_id': v.rule_id,
                            'field_path': v.field_path,
                            'severity': v.severity.value,
                            'message': v.message
                        }
                        for v in violations
                    ]
                }
                
                self.audit_logger.log_authentication_event(
                    event_type=event_type,
                    user_context=user_context,
                    request_context=request_context,
                    outcome="success" if is_valid else "validation_failed",
                    details=details
                )
            
            # Process security events
            if self.security_correlator and security_events:
                for security_event in security_events:
                    self.security_correlator.process_security_event(security_event)
            
            # Log summary
            if violations or security_events:
                logger.warning(
                    f"Validation completed for {validation_type}: "
                    f"valid={is_valid}, violations={len(violations)}, "
                    f"security_events={len(security_events)}"
                )
            else:
                logger.debug(f"Validation passed for {validation_type}")
        
        except Exception as e:
            logger.error(f"Failed to log validation results: {e}")
    
    def _initialize_validation_rules(self) -> Dict[str, ValidationRule]:
        """Initialize validation rules."""
        rules = {}
        
        # Basic validation rules
        basic_rules = [
            ValidationRule(
                rule_id="payload_size_limit",
                rule_type=ValidationRuleType.LENGTH,
                field_path="root",
                description="Payload size must not exceed maximum limit",
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                rule_id="string_length_limit",
                rule_type=ValidationRuleType.LENGTH,
                field_path="*",
                description="String fields must not exceed maximum length",
                severity=ValidationSeverity.WARNING
            ),
            ValidationRule(
                rule_id="malicious_pattern_detection",
                rule_type=ValidationRuleType.SECURITY,
                field_path="*",
                description="Detect malicious patterns in input data",
                severity=ValidationSeverity.CRITICAL
            ),
            ValidationRule(
                rule_id="mbti_format_validation",
                rule_type=ValidationRuleType.FORMAT,
                field_path="MBTI_personality",
                description="MBTI personality must be valid 4-character code",
                severity=ValidationSeverity.ERROR
            )
        ]
        
        for rule in basic_rules:
            rules[rule.rule_id] = rule
        
        return rules


# Global request validator instance
_request_validator = None
_validator_lock = None


def get_request_validator() -> RequestValidator:
    """Get global request validator instance."""
    global _request_validator, _validator_lock
    
    if _validator_lock is None:
        import threading
        _validator_lock = threading.Lock()
    
    with _validator_lock:
        if _request_validator is None:
            _request_validator = RequestValidator()
        
        return _request_validator


# Export main classes
__all__ = [
    'RequestValidator',
    'ValidationResult',
    'ValidationViolation',
    'ValidationRule',
    'ValidationSeverity',
    'ValidationRuleType',
    'get_request_validator'
]