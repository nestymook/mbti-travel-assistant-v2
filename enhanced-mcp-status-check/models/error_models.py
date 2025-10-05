"""
Error models for enhanced MCP status check system.

This module defines comprehensive error models for categorizing, tracking,
and reporting errors in dual monitoring operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import traceback
import json


class ErrorSeverity(Enum):
    """Error severity levels for categorization."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorCategory(Enum):
    """Error categories for classification."""
    MCP_PROTOCOL = "mcp_protocol"
    HTTP_REQUEST = "http_request"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    CIRCUIT_BREAKER = "circuit_breaker"
    AGGREGATION = "aggregation"
    SYSTEM = "system"


class ErrorCode(Enum):
    """Specific error codes for detailed classification."""
    # MCP Protocol Errors
    MCP_INVALID_JSONRPC = "MCP_INVALID_JSONRPC"
    MCP_TOOLS_LIST_FAILED = "MCP_TOOLS_LIST_FAILED"
    MCP_RESPONSE_INVALID = "MCP_RESPONSE_INVALID"
    MCP_TOOLS_MISSING = "MCP_TOOLS_MISSING"
    MCP_CONNECTION_FAILED = "MCP_CONNECTION_FAILED"
    
    # HTTP Request Errors
    HTTP_STATUS_ERROR = "HTTP_STATUS_ERROR"
    HTTP_CONNECTION_ERROR = "HTTP_CONNECTION_ERROR"
    HTTP_TIMEOUT = "HTTP_TIMEOUT"
    HTTP_RESPONSE_INVALID = "HTTP_RESPONSE_INVALID"
    HTTP_SSL_ERROR = "HTTP_SSL_ERROR"
    
    # Authentication Errors
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_CREDENTIALS_MISSING = "AUTH_CREDENTIALS_MISSING"
    AUTH_PERMISSION_DENIED = "AUTH_PERMISSION_DENIED"
    AUTH_REFRESH_FAILED = "AUTH_REFRESH_FAILED"
    
    # Network Errors
    NETWORK_DNS_RESOLUTION = "NETWORK_DNS_RESOLUTION"
    NETWORK_CONNECTION_REFUSED = "NETWORK_CONNECTION_REFUSED"
    NETWORK_UNREACHABLE = "NETWORK_UNREACHABLE"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    
    # Validation Errors
    VALIDATION_CONFIG_INVALID = "VALIDATION_CONFIG_INVALID"
    VALIDATION_RESPONSE_SCHEMA = "VALIDATION_RESPONSE_SCHEMA"
    VALIDATION_PARAMETER_MISSING = "VALIDATION_PARAMETER_MISSING"
    
    # Configuration Errors
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID_FORMAT = "CONFIG_INVALID_FORMAT"
    CONFIG_VALIDATION_FAILED = "CONFIG_VALIDATION_FAILED"
    
    # Timeout Errors
    TIMEOUT_MCP_REQUEST = "TIMEOUT_MCP_REQUEST"
    TIMEOUT_HTTP_REQUEST = "TIMEOUT_HTTP_REQUEST"
    TIMEOUT_AGGREGATION = "TIMEOUT_AGGREGATION"
    
    # Circuit Breaker Errors
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    CIRCUIT_BREAKER_HALF_OPEN_FAILED = "CIRCUIT_BREAKER_HALF_OPEN_FAILED"
    
    # Aggregation Errors
    AGGREGATION_FAILED = "AGGREGATION_FAILED"
    AGGREGATION_PARTIAL_RESULTS = "AGGREGATION_PARTIAL_RESULTS"
    
    # System Errors
    SYSTEM_RESOURCE_EXHAUSTED = "SYSTEM_RESOURCE_EXHAUSTED"
    SYSTEM_INTERNAL_ERROR = "SYSTEM_INTERNAL_ERROR"


@dataclass
class ErrorContext:
    """Context information for error tracking."""
    server_name: Optional[str] = None
    endpoint_url: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "server_name": self.server_name,
            "endpoint_url": self.endpoint_url,
            "request_id": self.request_id,
            "operation": self.operation,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "additional_data": self.additional_data
        }


@dataclass
class ErrorDetails:
    """Detailed error information."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    error_code: ErrorCode
    message: str
    description: Optional[str] = None
    context: Optional[ErrorContext] = None
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    retry_count: int = 0
    is_recoverable: bool = True
    recovery_suggestions: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "error_code": self.error_code.value,
            "message": self.message,
            "description": self.description,
            "context": self.context.to_dict() if self.context else None,
            "exception_type": self.exception_type,
            "stack_trace": self.stack_trace,
            "retry_count": self.retry_count,
            "is_recoverable": self.is_recoverable,
            "recovery_suggestions": self.recovery_suggestions,
            "related_errors": self.related_errors
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class MCPProtocolError(ErrorDetails):
    """Specific error for MCP protocol failures."""
    jsonrpc_version: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None
    jsonrpc_error: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Set category to MCP protocol."""
        self.category = ErrorCategory.MCP_PROTOCOL


@dataclass
class HTTPRequestError(ErrorDetails):
    """Specific error for HTTP request failures."""
    status_code: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    
    def __post_init__(self):
        """Set category to HTTP request."""
        self.category = ErrorCategory.HTTP_REQUEST


@dataclass
class AuthenticationError(ErrorDetails):
    """Specific error for authentication failures."""
    auth_type: Optional[str] = None
    token_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set category to authentication."""
        self.category = ErrorCategory.AUTHENTICATION


@dataclass
class NetworkError(ErrorDetails):
    """Specific error for network failures."""
    host: Optional[str] = None
    port: Optional[int] = None
    dns_resolution_time: Optional[float] = None
    connection_time: Optional[float] = None
    
    def __post_init__(self):
        """Set category to network."""
        self.category = ErrorCategory.NETWORK


@dataclass
class ValidationError(ErrorDetails):
    """Specific error for validation failures."""
    field_name: Optional[str] = None
    expected_type: Optional[str] = None
    actual_value: Optional[Any] = None
    validation_rule: Optional[str] = None
    
    def __post_init__(self):
        """Set category to validation."""
        self.category = ErrorCategory.VALIDATION


@dataclass
class ErrorSummary:
    """Summary of errors for reporting."""
    total_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_category: Dict[str, int]
    errors_by_code: Dict[str, int]
    most_common_errors: List[Dict[str, Any]]
    error_rate: float
    recovery_rate: float
    time_period: Dict[str, datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_errors": self.total_errors,
            "errors_by_severity": self.errors_by_severity,
            "errors_by_category": self.errors_by_category,
            "errors_by_code": self.errors_by_code,
            "most_common_errors": self.most_common_errors,
            "error_rate": self.error_rate,
            "recovery_rate": self.recovery_rate,
            "time_period": {
                "start": self.time_period["start"].isoformat(),
                "end": self.time_period["end"].isoformat()
            }
        }


class ErrorBuilder:
    """Builder class for creating error objects."""
    
    def __init__(self, error_code: ErrorCode, message: str):
        """Initialize error builder."""
        self.error_code = error_code
        self.message = message
        self.severity = ErrorSeverity.ERROR
        self.category = self._get_category_from_code(error_code)
        self.description = None
        self.context = None
        self.exception = None
        self.retry_count = 0
        self.recovery_suggestions = []
    
    def _get_category_from_code(self, error_code: ErrorCode) -> ErrorCategory:
        """Get category from error code."""
        code_str = error_code.value
        if code_str.startswith("MCP_"):
            return ErrorCategory.MCP_PROTOCOL
        elif code_str.startswith("HTTP_"):
            return ErrorCategory.HTTP_REQUEST
        elif code_str.startswith("AUTH_"):
            return ErrorCategory.AUTHENTICATION
        elif code_str.startswith("NETWORK_"):
            return ErrorCategory.NETWORK
        elif code_str.startswith("VALIDATION_"):
            return ErrorCategory.VALIDATION
        elif code_str.startswith("CONFIG_"):
            return ErrorCategory.CONFIGURATION
        elif code_str.startswith("TIMEOUT_"):
            return ErrorCategory.TIMEOUT
        elif code_str.startswith("CIRCUIT_"):
            return ErrorCategory.CIRCUIT_BREAKER
        elif code_str.startswith("AGGREGATION_"):
            return ErrorCategory.AGGREGATION
        else:
            return ErrorCategory.SYSTEM
    
    def with_severity(self, severity: ErrorSeverity) -> 'ErrorBuilder':
        """Set error severity."""
        self.severity = severity
        return self
    
    def with_description(self, description: str) -> 'ErrorBuilder':
        """Set error description."""
        self.description = description
        return self
    
    def with_context(self, context: ErrorContext) -> 'ErrorBuilder':
        """Set error context."""
        self.context = context
        return self
    
    def with_exception(self, exception: Exception) -> 'ErrorBuilder':
        """Set exception information."""
        self.exception = exception
        return self
    
    def with_retry_count(self, retry_count: int) -> 'ErrorBuilder':
        """Set retry count."""
        self.retry_count = retry_count
        return self
    
    def with_recovery_suggestions(self, suggestions: List[str]) -> 'ErrorBuilder':
        """Set recovery suggestions."""
        self.recovery_suggestions = suggestions
        return self
    
    def build(self) -> ErrorDetails:
        """Build the error object."""
        import uuid
        
        error_details = ErrorDetails(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=self.severity,
            category=self.category,
            error_code=self.error_code,
            message=self.message,
            description=self.description,
            context=self.context,
            retry_count=self.retry_count,
            recovery_suggestions=self.recovery_suggestions
        )
        
        if self.exception:
            error_details.exception_type = type(self.exception).__name__
            error_details.stack_trace = traceback.format_exc()
        
        return error_details
    
    def build_mcp_error(self, **kwargs) -> MCPProtocolError:
        """Build MCP protocol error."""
        base_error = self.build()
        return MCPProtocolError(
            error_id=base_error.error_id,
            timestamp=base_error.timestamp,
            severity=base_error.severity,
            category=ErrorCategory.MCP_PROTOCOL,
            error_code=base_error.error_code,
            message=base_error.message,
            description=base_error.description,
            context=base_error.context,
            exception_type=base_error.exception_type,
            stack_trace=base_error.stack_trace,
            retry_count=base_error.retry_count,
            recovery_suggestions=base_error.recovery_suggestions,
            **kwargs
        )
    
    def build_http_error(self, **kwargs) -> HTTPRequestError:
        """Build HTTP request error."""
        base_error = self.build()
        return HTTPRequestError(
            error_id=base_error.error_id,
            timestamp=base_error.timestamp,
            severity=base_error.severity,
            category=ErrorCategory.HTTP_REQUEST,
            error_code=base_error.error_code,
            message=base_error.message,
            description=base_error.description,
            context=base_error.context,
            exception_type=base_error.exception_type,
            stack_trace=base_error.stack_trace,
            retry_count=base_error.retry_count,
            recovery_suggestions=base_error.recovery_suggestions,
            **kwargs
        )