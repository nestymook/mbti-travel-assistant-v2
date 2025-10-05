"""
Comprehensive error handling service for enhanced MCP status check system.

This service provides detailed error handling for MCP protocol failures,
HTTP error handling for REST checks, error categorization, and recovery mechanisms.
"""

import asyncio
import json
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Type
from collections import defaultdict, deque
import logging

from models.error_models import (
    ErrorDetails, ErrorSeverity, ErrorCategory, ErrorCode, ErrorContext,
    MCPProtocolError, HTTPRequestError, AuthenticationError, NetworkError,
    ValidationError, ErrorSummary, ErrorBuilder
)
from models.logging_models import LogLevel, LogCategory, StructuredLogEntry


class ErrorRecoveryStrategy:
    """Strategy for error recovery."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_multiplier: float = 2.0):
        """Initialize recovery strategy."""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
    
    def calculate_delay(self, retry_count: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.base_delay * (self.backoff_multiplier ** retry_count)
        return min(delay, self.max_delay)
    
    def should_retry(self, error: ErrorDetails, retry_count: int) -> bool:
        """Determine if error should be retried."""
        if retry_count >= self.max_retries:
            return False
        
        # Don't retry authentication errors
        if error.category == ErrorCategory.AUTHENTICATION:
            return False
        
        # Don't retry validation errors
        if error.category == ErrorCategory.VALIDATION:
            return False
        
        # Don't retry configuration errors
        if error.category == ErrorCategory.CONFIGURATION:
            return False
        
        return error.is_recoverable


class ErrorHandler:
    """Comprehensive error handler for dual monitoring operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler."""
        self.logger = logger or logging.getLogger(__name__)
        self.error_history: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recovery_strategies: Dict[ErrorCategory, ErrorRecoveryStrategy] = {
            ErrorCategory.MCP_PROTOCOL: ErrorRecoveryStrategy(max_retries=3, base_delay=1.0),
            ErrorCategory.HTTP_REQUEST: ErrorRecoveryStrategy(max_retries=3, base_delay=0.5),
            ErrorCategory.NETWORK: ErrorRecoveryStrategy(max_retries=5, base_delay=2.0),
            ErrorCategory.TIMEOUT: ErrorRecoveryStrategy(max_retries=2, base_delay=1.0),
            ErrorCategory.CIRCUIT_BREAKER: ErrorRecoveryStrategy(max_retries=1, base_delay=5.0),
        }
        self.error_callbacks: Dict[ErrorCode, List[Callable]] = defaultdict(list)
    
    def handle_mcp_protocol_error(self, exception: Exception, context: ErrorContext,
                                 jsonrpc_data: Optional[Dict[str, Any]] = None) -> MCPProtocolError:
        """Handle MCP protocol specific errors."""
        error_code = self._classify_mcp_error(exception, jsonrpc_data)
        
        error = ErrorBuilder(error_code, str(exception)) \
            .with_severity(self._get_severity_for_code(error_code)) \
            .with_context(context) \
            .with_exception(exception) \
            .with_recovery_suggestions(self._get_mcp_recovery_suggestions(error_code)) \
            .build_mcp_error(
                jsonrpc_version=jsonrpc_data.get("jsonrpc") if jsonrpc_data else None,
                method=jsonrpc_data.get("method") if jsonrpc_data else None,
                request_id=jsonrpc_data.get("id") if jsonrpc_data else None,
                jsonrpc_error=jsonrpc_data.get("error") if jsonrpc_data else None
            )
        
        self._record_error(error)
        self._trigger_callbacks(error)
        
        return error
    
    def handle_http_request_error(self, exception: Exception, context: ErrorContext,
                                 status_code: Optional[int] = None,
                                 response_data: Optional[Dict[str, Any]] = None) -> HTTPRequestError:
        """Handle HTTP request specific errors."""
        error_code = self._classify_http_error(exception, status_code)
        
        error = ErrorBuilder(error_code, str(exception)) \
            .with_severity(self._get_severity_for_code(error_code)) \
            .with_context(context) \
            .with_exception(exception) \
            .with_recovery_suggestions(self._get_http_recovery_suggestions(error_code, status_code)) \
            .build_http_error(
                status_code=status_code,
                response_headers=response_data.get("headers") if response_data else None,
                response_body=response_data.get("body") if response_data else None,
                request_method=context.additional_data.get("method"),
                request_url=context.endpoint_url
            )
        
        self._record_error(error)
        self._trigger_callbacks(error)
        
        return error
    
    def handle_authentication_error(self, exception: Exception, context: ErrorContext,
                                   auth_data: Optional[Dict[str, Any]] = None) -> AuthenticationError:
        """Handle authentication specific errors."""
        error_code = self._classify_auth_error(exception, auth_data)
        
        error = ErrorBuilder(error_code, str(exception)) \
            .with_severity(ErrorSeverity.ERROR) \
            .with_context(context) \
            .with_exception(exception) \
            .with_recovery_suggestions(self._get_auth_recovery_suggestions(error_code)) \
            .build()
        
        auth_error = AuthenticationError(
            error_id=error.error_id,
            timestamp=error.timestamp,
            severity=error.severity,
            category=ErrorCategory.AUTHENTICATION,
            error_code=error.error_code,
            message=error.message,
            description=error.description,
            context=error.context,
            exception_type=error.exception_type,
            stack_trace=error.stack_trace,
            retry_count=error.retry_count,
            recovery_suggestions=error.recovery_suggestions,
            auth_type=auth_data.get("auth_type") if auth_data else None,
            token_type=auth_data.get("token_type") if auth_data else None,
            expires_at=auth_data.get("expires_at") if auth_data else None
        )
        
        self._record_error(auth_error)
        self._trigger_callbacks(auth_error)
        
        return auth_error
    
    def handle_network_error(self, exception: Exception, context: ErrorContext,
                           network_data: Optional[Dict[str, Any]] = None) -> NetworkError:
        """Handle network specific errors."""
        error_code = self._classify_network_error(exception)
        
        error = ErrorBuilder(error_code, str(exception)) \
            .with_severity(self._get_severity_for_code(error_code)) \
            .with_context(context) \
            .with_exception(exception) \
            .with_recovery_suggestions(self._get_network_recovery_suggestions(error_code)) \
            .build()
        
        network_error = NetworkError(
            error_id=error.error_id,
            timestamp=error.timestamp,
            severity=error.severity,
            category=ErrorCategory.NETWORK,
            error_code=error.error_code,
            message=error.message,
            description=error.description,
            context=error.context,
            exception_type=error.exception_type,
            stack_trace=error.stack_trace,
            retry_count=error.retry_count,
            recovery_suggestions=error.recovery_suggestions,
            host=network_data.get("host") if network_data else None,
            port=network_data.get("port") if network_data else None,
            dns_resolution_time=network_data.get("dns_time") if network_data else None,
            connection_time=network_data.get("connection_time") if network_data else None
        )
        
        self._record_error(network_error)
        self._trigger_callbacks(network_error)
        
        return network_error
    
    def handle_validation_error(self, exception: Exception, context: ErrorContext,
                              validation_data: Optional[Dict[str, Any]] = None) -> ValidationError:
        """Handle validation specific errors."""
        error_code = self._classify_validation_error(exception, validation_data)
        
        error = ErrorBuilder(error_code, str(exception)) \
            .with_severity(ErrorSeverity.WARNING) \
            .with_context(context) \
            .with_exception(exception) \
            .with_recovery_suggestions(self._get_validation_recovery_suggestions(error_code)) \
            .build()
        
        validation_error = ValidationError(
            error_id=error.error_id,
            timestamp=error.timestamp,
            severity=error.severity,
            category=ErrorCategory.VALIDATION,
            error_code=error.error_code,
            message=error.message,
            description=error.description,
            context=error.context,
            exception_type=error.exception_type,
            stack_trace=error.stack_trace,
            retry_count=error.retry_count,
            recovery_suggestions=error.recovery_suggestions,
            field_name=validation_data.get("field_name") if validation_data else None,
            expected_type=validation_data.get("expected_type") if validation_data else None,
            actual_value=validation_data.get("actual_value") if validation_data else None,
            validation_rule=validation_data.get("validation_rule") if validation_data else None
        )
        
        self._record_error(validation_error)
        self._trigger_callbacks(validation_error)
        
        return validation_error
    
    async def retry_with_recovery(self, operation: Callable, error_context: ErrorContext,
                                 operation_args: tuple = (), operation_kwargs: dict = None) -> Any:
        """Retry operation with error recovery strategy."""
        operation_kwargs = operation_kwargs or {}
        last_error = None
        retry_count = 0
        
        while True:
            try:
                return await operation(*operation_args, **operation_kwargs)
            except Exception as e:
                # Handle the error and get error details
                operation_name = str(operation).lower()
                if "mcp" in operation_name or error_context.operation == "mcp_health_check":
                    error = self.handle_mcp_protocol_error(e, error_context)
                elif "http" in operation_name or error_context.operation == "rest_health_check":
                    error = self.handle_http_request_error(e, error_context)
                elif isinstance(e, ConnectionError):
                    # Default to network error for connection issues
                    error = self.handle_network_error(e, error_context)
                else:
                    error = ErrorBuilder(ErrorCode.SYSTEM_INTERNAL_ERROR, str(e)) \
                        .with_context(error_context) \
                        .with_exception(e) \
                        .build()
                    self._record_error(error)
                
                last_error = error
                
                # Check if we should retry
                strategy = self.recovery_strategies.get(error.category)
                if not strategy or not strategy.should_retry(error, retry_count):
                    break
                
                # Calculate delay and wait
                delay = strategy.calculate_delay(retry_count)
                self.logger.warning(f"Retrying operation after {delay}s (attempt {retry_count + 1})")
                await asyncio.sleep(delay)
                
                retry_count += 1
                error.retry_count = retry_count
        
        # If we get here, all retries failed
        if last_error:
            raise Exception(f"Operation failed after {retry_count} retries: {last_error.message}")
        else:
            raise Exception("Operation failed with unknown error")
    
    def register_error_callback(self, error_code: ErrorCode, callback: Callable[[ErrorDetails], None]):
        """Register callback for specific error code."""
        self.error_callbacks[error_code].append(callback)
    
    def get_error_summary(self, time_period_hours: int = 24) -> ErrorSummary:
        """Get error summary for specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_period_hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        if not recent_errors:
            return ErrorSummary(
                total_errors=0,
                errors_by_severity={},
                errors_by_category={},
                errors_by_code={},
                most_common_errors=[],
                error_rate=0.0,
                recovery_rate=0.0,
                time_period={"start": cutoff_time, "end": datetime.utcnow()}
            )
        
        # Count errors by various dimensions
        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)
        code_counts = defaultdict(int)
        
        recoverable_errors = 0
        
        for error in recent_errors:
            severity_counts[error.severity.value] += 1
            category_counts[error.category.value] += 1
            code_counts[error.error_code.value] += 1
            
            if error.is_recoverable:
                recoverable_errors += 1
        
        # Find most common errors
        most_common = sorted(code_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_errors = [{"error_code": code, "count": count} for code, count in most_common]
        
        return ErrorSummary(
            total_errors=len(recent_errors),
            errors_by_severity=dict(severity_counts),
            errors_by_category=dict(category_counts),
            errors_by_code=dict(code_counts),
            most_common_errors=most_common_errors,
            error_rate=len(recent_errors) / time_period_hours,
            recovery_rate=recoverable_errors / len(recent_errors) if recent_errors else 0.0,
            time_period={"start": cutoff_time, "end": datetime.utcnow()}
        )
    
    def _classify_mcp_error(self, exception: Exception, jsonrpc_data: Optional[Dict[str, Any]]) -> ErrorCode:
        """Classify MCP protocol error."""
        exception_str = str(exception).lower()
        
        if "jsonrpc" in exception_str or "json-rpc" in exception_str:
            return ErrorCode.MCP_INVALID_JSONRPC
        elif "tools" in exception_str and "list" in exception_str:
            return ErrorCode.MCP_TOOLS_LIST_FAILED
        elif "response" in exception_str and "invalid" in exception_str:
            return ErrorCode.MCP_RESPONSE_INVALID
        elif "missing" in exception_str and "tool" in exception_str:
            return ErrorCode.MCP_TOOLS_MISSING
        elif "connection" in exception_str:
            return ErrorCode.MCP_CONNECTION_FAILED
        else:
            return ErrorCode.MCP_CONNECTION_FAILED
    
    def _classify_http_error(self, exception: Exception, status_code: Optional[int]) -> ErrorCode:
        """Classify HTTP request error."""
        if status_code:
            if 400 <= status_code < 500:
                return ErrorCode.HTTP_STATUS_ERROR
            elif status_code >= 500:
                return ErrorCode.HTTP_STATUS_ERROR
        
        exception_str = str(exception).lower()
        
        if "timeout" in exception_str:
            return ErrorCode.HTTP_TIMEOUT
        elif "connection" in exception_str:
            return ErrorCode.HTTP_CONNECTION_ERROR
        elif "ssl" in exception_str or "tls" in exception_str:
            return ErrorCode.HTTP_SSL_ERROR
        elif "response" in exception_str:
            return ErrorCode.HTTP_RESPONSE_INVALID
        else:
            return ErrorCode.HTTP_CONNECTION_ERROR
    
    def _classify_auth_error(self, exception: Exception, auth_data: Optional[Dict[str, Any]]) -> ErrorCode:
        """Classify authentication error."""
        exception_str = str(exception).lower()
        
        if "token" in exception_str and "invalid" in exception_str:
            return ErrorCode.AUTH_TOKEN_INVALID
        elif "token" in exception_str and "expired" in exception_str:
            return ErrorCode.AUTH_TOKEN_EXPIRED
        elif "credentials" in exception_str or "missing" in exception_str:
            return ErrorCode.AUTH_CREDENTIALS_MISSING
        elif "permission" in exception_str or "denied" in exception_str:
            return ErrorCode.AUTH_PERMISSION_DENIED
        elif "refresh" in exception_str:
            return ErrorCode.AUTH_REFRESH_FAILED
        else:
            return ErrorCode.AUTH_TOKEN_INVALID
    
    def _classify_network_error(self, exception: Exception) -> ErrorCode:
        """Classify network error."""
        exception_str = str(exception).lower()
        
        if "dns" in exception_str or "name resolution" in exception_str:
            return ErrorCode.NETWORK_DNS_RESOLUTION
        elif "connection refused" in exception_str:
            return ErrorCode.NETWORK_CONNECTION_REFUSED
        elif "unreachable" in exception_str:
            return ErrorCode.NETWORK_UNREACHABLE
        elif "timeout" in exception_str:
            return ErrorCode.NETWORK_TIMEOUT
        else:
            return ErrorCode.NETWORK_CONNECTION_REFUSED
    
    def _classify_validation_error(self, exception: Exception, 
                                 validation_data: Optional[Dict[str, Any]]) -> ErrorCode:
        """Classify validation error."""
        exception_str = str(exception).lower()
        
        if "config" in exception_str:
            return ErrorCode.VALIDATION_CONFIG_INVALID
        elif "schema" in exception_str or "response" in exception_str:
            return ErrorCode.VALIDATION_RESPONSE_SCHEMA
        elif "parameter" in exception_str or "missing" in exception_str:
            return ErrorCode.VALIDATION_PARAMETER_MISSING
        else:
            return ErrorCode.VALIDATION_RESPONSE_SCHEMA
    
    def _get_severity_for_code(self, error_code: ErrorCode) -> ErrorSeverity:
        """Get severity level for error code."""
        critical_codes = {
            ErrorCode.SYSTEM_RESOURCE_EXHAUSTED,
            ErrorCode.SYSTEM_INTERNAL_ERROR
        }
        
        error_codes = {
            ErrorCode.MCP_CONNECTION_FAILED,
            ErrorCode.HTTP_CONNECTION_ERROR,
            ErrorCode.AUTH_PERMISSION_DENIED,
            ErrorCode.NETWORK_UNREACHABLE
        }
        
        warning_codes = {
            ErrorCode.MCP_TOOLS_MISSING,
            ErrorCode.HTTP_STATUS_ERROR,
            ErrorCode.AUTH_TOKEN_EXPIRED,
            ErrorCode.VALIDATION_RESPONSE_SCHEMA
        }
        
        if error_code in critical_codes:
            return ErrorSeverity.CRITICAL
        elif error_code in error_codes:
            return ErrorSeverity.ERROR
        elif error_code in warning_codes:
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR
    
    def _get_mcp_recovery_suggestions(self, error_code: ErrorCode) -> List[str]:
        """Get recovery suggestions for MCP errors."""
        suggestions = {
            ErrorCode.MCP_INVALID_JSONRPC: [
                "Verify JSON-RPC 2.0 request format",
                "Check request structure and required fields",
                "Validate JSON syntax"
            ],
            ErrorCode.MCP_TOOLS_LIST_FAILED: [
                "Check MCP server availability",
                "Verify tools/list endpoint is implemented",
                "Review server logs for errors"
            ],
            ErrorCode.MCP_RESPONSE_INVALID: [
                "Validate response schema",
                "Check for missing required fields",
                "Review server implementation"
            ],
            ErrorCode.MCP_TOOLS_MISSING: [
                "Verify expected tools are configured",
                "Check tool registration in server",
                "Update expected tools list"
            ],
            ErrorCode.MCP_CONNECTION_FAILED: [
                "Check network connectivity",
                "Verify server endpoint URL",
                "Review authentication credentials"
            ]
        }
        return suggestions.get(error_code, ["Contact system administrator"])
    
    def _get_http_recovery_suggestions(self, error_code: ErrorCode, 
                                     status_code: Optional[int]) -> List[str]:
        """Get recovery suggestions for HTTP errors."""
        if status_code:
            if status_code == 401:
                return ["Check authentication credentials", "Refresh access token"]
            elif status_code == 403:
                return ["Verify permissions", "Check authorization headers"]
            elif status_code == 404:
                return ["Verify endpoint URL", "Check API documentation"]
            elif status_code >= 500:
                return ["Server error - retry later", "Check server status"]
        
        suggestions = {
            ErrorCode.HTTP_CONNECTION_ERROR: [
                "Check network connectivity",
                "Verify server is running",
                "Review firewall settings"
            ],
            ErrorCode.HTTP_TIMEOUT: [
                "Increase timeout value",
                "Check server performance",
                "Review network latency"
            ],
            ErrorCode.HTTP_SSL_ERROR: [
                "Verify SSL certificate",
                "Check certificate chain",
                "Update certificate store"
            ]
        }
        return suggestions.get(error_code, ["Contact system administrator"])
    
    def _get_auth_recovery_suggestions(self, error_code: ErrorCode) -> List[str]:
        """Get recovery suggestions for authentication errors."""
        suggestions = {
            ErrorCode.AUTH_TOKEN_INVALID: [
                "Obtain new access token",
                "Verify token format",
                "Check token signing"
            ],
            ErrorCode.AUTH_TOKEN_EXPIRED: [
                "Refresh access token",
                "Re-authenticate user",
                "Check token expiration time"
            ],
            ErrorCode.AUTH_CREDENTIALS_MISSING: [
                "Provide authentication credentials",
                "Check configuration",
                "Verify credential format"
            ],
            ErrorCode.AUTH_PERMISSION_DENIED: [
                "Check user permissions",
                "Verify role assignments",
                "Contact administrator"
            ]
        }
        return suggestions.get(error_code, ["Contact system administrator"])
    
    def _get_network_recovery_suggestions(self, error_code: ErrorCode) -> List[str]:
        """Get recovery suggestions for network errors."""
        suggestions = {
            ErrorCode.NETWORK_DNS_RESOLUTION: [
                "Check DNS configuration",
                "Verify hostname spelling",
                "Try alternative DNS servers"
            ],
            ErrorCode.NETWORK_CONNECTION_REFUSED: [
                "Check if service is running",
                "Verify port number",
                "Review firewall rules"
            ],
            ErrorCode.NETWORK_UNREACHABLE: [
                "Check network connectivity",
                "Verify routing configuration",
                "Test with ping/traceroute"
            ],
            ErrorCode.NETWORK_TIMEOUT: [
                "Increase timeout value",
                "Check network latency",
                "Verify server responsiveness"
            ]
        }
        return suggestions.get(error_code, ["Contact network administrator"])
    
    def _get_validation_recovery_suggestions(self, error_code: ErrorCode) -> List[str]:
        """Get recovery suggestions for validation errors."""
        suggestions = {
            ErrorCode.VALIDATION_CONFIG_INVALID: [
                "Review configuration format",
                "Check required fields",
                "Validate against schema"
            ],
            ErrorCode.VALIDATION_RESPONSE_SCHEMA: [
                "Check response format",
                "Verify required fields",
                "Review API documentation"
            ],
            ErrorCode.VALIDATION_PARAMETER_MISSING: [
                "Provide required parameters",
                "Check parameter names",
                "Review API specification"
            ]
        }
        return suggestions.get(error_code, ["Review documentation"])
    
    def _record_error(self, error: ErrorDetails):
        """Record error in history."""
        self.error_history.append(error)
        self.error_counts[error.error_code.value] += 1
        
        # Log the error
        log_entry = StructuredLogEntry(
            timestamp=error.timestamp,
            level=LogLevel.ERROR if error.severity == ErrorSeverity.ERROR else LogLevel.WARNING,
            category=LogCategory.SYSTEM,
            message=error.message,
            error_details=error.to_dict()
        )
        
        self.logger.error(log_entry.to_json())
    
    def _trigger_callbacks(self, error: ErrorDetails):
        """Trigger registered callbacks for error."""
        callbacks = self.error_callbacks.get(error.error_code, [])
        for callback in callbacks:
            try:
                callback(error)
            except Exception as e:
                self.logger.error(f"Error callback failed: {e}")