"""
Structured logging service for enhanced MCP status check system.

This service provides comprehensive structured logging for dual monitoring operations
with support for multiple output formats and log aggregation.
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TextIO
from collections import deque
import threading
import asyncio

from models.logging_models import (
    LogLevel, LogCategory, OperationType, StructuredLogEntry, LogContext,
    PerformanceMetrics, SecurityContext, HealthCheckLogEntry, MCPProtocolLogEntry,
    HTTPRequestLogEntry, AuthenticationLogEntry, CircuitBreakerLogEntry,
    MetricsLogEntry, LogEntryBuilder
)
from models.error_models import ErrorDetails


class LogFormatter:
    """Custom log formatter for structured logging."""
    
    def __init__(self, format_type: str = "json"):
        """Initialize log formatter."""
        self.format_type = format_type
    
    def format(self, log_entry: StructuredLogEntry) -> str:
        """Format log entry based on format type."""
        if self.format_type == "json":
            return self._format_json(log_entry)
        elif self.format_type == "text":
            return self._format_text(log_entry)
        elif self.format_type == "structured":
            return self._format_structured(log_entry)
        else:
            return self._format_json(log_entry)
    
    def _format_json(self, log_entry: StructuredLogEntry) -> str:
        """Format as JSON."""
        return log_entry.to_json()
    
    def _format_text(self, log_entry: StructuredLogEntry) -> str:
        """Format as human-readable text."""
        timestamp = log_entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = log_entry.level.value.upper()
        category = log_entry.category.value
        message = log_entry.message
        
        base_format = f"{timestamp} [{level}] {category}: {message}"
        
        if log_entry.context and log_entry.context.server_name:
            base_format += f" (server: {log_entry.context.server_name})"
        
        if log_entry.performance_metrics and log_entry.performance_metrics.duration_ms:
            base_format += f" (duration: {log_entry.performance_metrics.duration_ms:.2f}ms)"
        
        if log_entry.error_details:
            base_format += f" (error: {log_entry.error_details.get('error_code', 'unknown')})"
        
        return base_format
    
    def _format_structured(self, log_entry: StructuredLogEntry) -> str:
        """Format as structured key-value pairs."""
        parts = [
            f"timestamp={log_entry.timestamp.isoformat()}",
            f"level={log_entry.level.value}",
            f"category={log_entry.category.value}",
            f"message=\"{log_entry.message}\""
        ]
        
        if log_entry.context:
            context_dict = log_entry.context.to_dict()
            for key, value in context_dict.items():
                if value is not None:
                    parts.append(f"{key}={value}")
        
        if log_entry.performance_metrics:
            metrics_dict = log_entry.performance_metrics.to_dict()
            for key, value in metrics_dict.items():
                if value is not None:
                    parts.append(f"perf_{key}={value}")
        
        if log_entry.tags:
            parts.append(f"tags={','.join(log_entry.tags)}")
        
        return " ".join(parts)


class LogOutput:
    """Base class for log outputs."""
    
    def write(self, formatted_log: str):
        """Write formatted log entry."""
        raise NotImplementedError
    
    def flush(self):
        """Flush any buffered logs."""
        pass
    
    def close(self):
        """Close the log output."""
        pass


class FileLogOutput(LogOutput):
    """File-based log output."""
    
    def __init__(self, file_path: Union[str, Path], max_size_mb: int = 100, 
                 backup_count: int = 5):
        """Initialize file log output."""
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler
        self.handler = logging.handlers.RotatingFileHandler(
            self.file_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        self.handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Create logger for this output
        self.logger = logging.getLogger(f"file_output_{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False
    
    def write(self, formatted_log: str):
        """Write to file."""
        self.logger.info(formatted_log)
    
    def flush(self):
        """Flush file handler."""
        self.handler.flush()
    
    def close(self):
        """Close file handler."""
        self.handler.close()


class ConsoleLogOutput(LogOutput):
    """Console-based log output."""
    
    def __init__(self, stream: TextIO = None):
        """Initialize console log output."""
        self.stream = stream or sys.stdout
    
    def write(self, formatted_log: str):
        """Write to console."""
        print(formatted_log, file=self.stream)
    
    def flush(self):
        """Flush console stream."""
        self.stream.flush()


class BufferedLogOutput(LogOutput):
    """In-memory buffered log output."""
    
    def __init__(self, max_entries: int = 1000):
        """Initialize buffered log output."""
        self.buffer = deque(maxlen=max_entries)
        self.lock = threading.Lock()
    
    def write(self, formatted_log: str):
        """Write to buffer."""
        with self.lock:
            self.buffer.append({
                "timestamp": datetime.utcnow().isoformat(),
                "log": formatted_log
            })
    
    def get_logs(self, count: Optional[int] = None) -> List[str]:
        """Get logs from buffer."""
        with self.lock:
            if count:
                return list(self.buffer)[-count:]
            return list(self.buffer)
    
    def clear(self):
        """Clear buffer."""
        with self.lock:
            self.buffer.clear()


class StructuredLogger:
    """Comprehensive structured logger for dual monitoring operations."""
    
    def __init__(self, name: str = "enhanced_mcp_status_check"):
        """Initialize structured logger."""
        self.name = name
        self.outputs: List[LogOutput] = []
        self.formatters: Dict[LogOutput, LogFormatter] = {}
        self.log_level = LogLevel.INFO
        self.context_stack: List[LogContext] = []
        self.performance_stack: List[PerformanceMetrics] = []
        self.security_context: Optional[SecurityContext] = None
        
        # Default console output
        console_output = ConsoleLogOutput()
        self.add_output(console_output, LogFormatter("text"))
    
    def add_output(self, output: LogOutput, formatter: LogFormatter):
        """Add log output with formatter."""
        self.outputs.append(output)
        self.formatters[output] = formatter
    
    def add_file_output(self, file_path: Union[str, Path], format_type: str = "json",
                       max_size_mb: int = 100, backup_count: int = 5):
        """Add file output."""
        file_output = FileLogOutput(file_path, max_size_mb, backup_count)
        formatter = LogFormatter(format_type)
        self.add_output(file_output, formatter)
    
    def add_buffered_output(self, max_entries: int = 1000, format_type: str = "json"):
        """Add buffered output."""
        buffered_output = BufferedLogOutput(max_entries)
        formatter = LogFormatter(format_type)
        self.add_output(buffered_output, formatter)
        return buffered_output
    
    def set_log_level(self, level: LogLevel):
        """Set minimum log level."""
        self.log_level = level
    
    def push_context(self, context: LogContext):
        """Push context onto stack."""
        self.context_stack.append(context)
    
    def pop_context(self) -> Optional[LogContext]:
        """Pop context from stack."""
        return self.context_stack.pop() if self.context_stack else None
    
    def set_security_context(self, security_context: SecurityContext):
        """Set security context."""
        self.security_context = security_context
    
    def start_performance_tracking(self, operation: str) -> PerformanceMetrics:
        """Start performance tracking."""
        metrics = PerformanceMetrics(start_time=datetime.utcnow())
        self.performance_stack.append(metrics)
        return metrics
    
    def end_performance_tracking(self) -> Optional[PerformanceMetrics]:
        """End performance tracking."""
        if self.performance_stack:
            metrics = self.performance_stack.pop()
            metrics.end_time = datetime.utcnow()
            metrics.calculate_duration()
            return metrics
        return None
    
    def log(self, level: LogLevel, category: LogCategory, message: str,
            context: Optional[LogContext] = None, 
            performance_metrics: Optional[PerformanceMetrics] = None,
            error_details: Optional[Dict[str, Any]] = None,
            tags: Optional[List[str]] = None):
        """Log structured entry."""
        if level.value < self.log_level.value:
            return
        
        # Use context from stack if not provided
        if not context and self.context_stack:
            context = self.context_stack[-1]
        
        # Use performance metrics from stack if not provided
        if not performance_metrics and self.performance_stack:
            performance_metrics = self.performance_stack[-1]
        
        log_entry = StructuredLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=category,
            message=message,
            context=context,
            performance_metrics=performance_metrics,
            security_context=self.security_context,
            error_details=error_details,
            tags=tags or []
        )
        
        self._write_log_entry(log_entry)
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log debug message."""
        self.log(LogLevel.DEBUG, category, message, **kwargs)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log info message."""
        self.log(LogLevel.INFO, category, message, **kwargs)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log warning message."""
        self.log(LogLevel.WARNING, category, message, **kwargs)
    
    def error(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log error message."""
        self.log(LogLevel.ERROR, category, message, **kwargs)
    
    def critical(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log critical message."""
        self.log(LogLevel.CRITICAL, category, message, **kwargs)
    
    def log_health_check(self, server_name: str, check_type: str, success: bool,
                        response_time_ms: float, status_code: Optional[int] = None,
                        error_message: Optional[str] = None):
        """Log health check operation."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Health check {'succeeded' if success else 'failed'} for {server_name}"
        
        log_entry = HealthCheckLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=LogCategory.HEALTH_CHECK,
            message=message,
            server_name=server_name,
            check_type=check_type,
            success=success,
            response_time_ms=response_time_ms,
            status_code=status_code,
            error_message=error_message
        )
        
        self._write_log_entry(log_entry)
    
    def log_mcp_protocol(self, method: str, request_id: str, success: bool,
                        tools_count: Optional[int] = None,
                        validation_errors: Optional[List[str]] = None):
        """Log MCP protocol operation."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"MCP {method} {'succeeded' if success else 'failed'}"
        
        log_entry = MCPProtocolLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=LogCategory.MCP_PROTOCOL,
            message=message,
            method=method,
            request_id=request_id,
            tools_count=tools_count,
            validation_errors=validation_errors or []
        )
        
        self._write_log_entry(log_entry)
    
    def log_http_request(self, method: str, url: str, status_code: Optional[int] = None,
                        response_size_bytes: Optional[int] = None,
                        success: bool = True):
        """Log HTTP request operation."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"HTTP {method} {url} {'succeeded' if success else 'failed'}"
        
        log_entry = HTTPRequestLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=LogCategory.HTTP_REQUEST,
            message=message,
            method=method,
            url=url,
            status_code=status_code,
            response_size_bytes=response_size_bytes
        )
        
        self._write_log_entry(log_entry)
    
    def log_authentication(self, auth_method: str, success: bool,
                          token_type: Optional[str] = None,
                          expires_in_seconds: Optional[int] = None,
                          failure_reason: Optional[str] = None):
        """Log authentication operation."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Authentication {'succeeded' if success else 'failed'} using {auth_method}"
        
        log_entry = AuthenticationLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=LogCategory.AUTHENTICATION,
            message=message,
            auth_method=auth_method,
            success=success,
            token_type=token_type,
            expires_in_seconds=expires_in_seconds,
            failure_reason=failure_reason
        )
        
        self._write_log_entry(log_entry)
    
    def log_circuit_breaker(self, server_name: str, state: str, failure_count: int,
                           success_count: int, last_failure_time: Optional[datetime] = None):
        """Log circuit breaker operation."""
        level = LogLevel.WARNING if state == "open" else LogLevel.INFO
        message = f"Circuit breaker for {server_name} is {state}"
        
        log_entry = CircuitBreakerLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=LogCategory.CIRCUIT_BREAKER,
            message=message,
            server_name=server_name,
            state=state,
            failure_count=failure_count,
            success_count=success_count,
            last_failure_time=last_failure_time
        )
        
        self._write_log_entry(log_entry)
    
    def log_metrics(self, metric_name: str, metric_value: Union[int, float],
                   metric_type: str = "gauge", labels: Optional[Dict[str, str]] = None):
        """Log metrics collection."""
        message = f"Metric {metric_name} = {metric_value}"
        
        log_entry = MetricsLogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.DEBUG,
            category=LogCategory.METRICS,
            message=message,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            labels=labels or {}
        )
        
        self._write_log_entry(log_entry)
    
    def log_error(self, error: ErrorDetails):
        """Log error details."""
        level_mapping = {
            "critical": LogLevel.CRITICAL,
            "error": LogLevel.ERROR,
            "warning": LogLevel.WARNING,
            "info": LogLevel.INFO
        }
        
        level = level_mapping.get(error.severity.value, LogLevel.ERROR)
        
        self.log(
            level=level,
            category=LogCategory.SYSTEM,
            message=error.message,
            context=error.context,
            error_details=error.to_dict(),
            tags=[error.category.value, error.error_code.value]
        )
    
    def _write_log_entry(self, log_entry: StructuredLogEntry):
        """Write log entry to all outputs."""
        for output in self.outputs:
            try:
                formatter = self.formatters[output]
                formatted_log = formatter.format(log_entry)
                output.write(formatted_log)
            except Exception as e:
                # Fallback to console if output fails
                print(f"Log output failed: {e}", file=sys.stderr)
    
    def flush_all(self):
        """Flush all outputs."""
        for output in self.outputs:
            try:
                output.flush()
            except Exception:
                pass
    
    def close_all(self):
        """Close all outputs."""
        for output in self.outputs:
            try:
                output.close()
            except Exception:
                pass


class LoggingContextManager:
    """Context manager for structured logging."""
    
    def __init__(self, logger: StructuredLogger, context: LogContext):
        """Initialize context manager."""
        self.logger = logger
        self.context = context
    
    def __enter__(self):
        """Enter context."""
        self.logger.push_context(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        self.logger.pop_context()


class PerformanceTrackingContextManager:
    """Context manager for performance tracking."""
    
    def __init__(self, logger: StructuredLogger, operation: str):
        """Initialize performance tracking."""
        self.logger = logger
        self.operation = operation
        self.metrics = None
    
    def __enter__(self):
        """Start performance tracking."""
        self.metrics = self.logger.start_performance_tracking(self.operation)
        return self.metrics
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End performance tracking."""
        self.logger.end_performance_tracking()


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "enhanced_mcp_status_check") -> StructuredLogger:
    """Get global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    return _global_logger


def configure_logging(log_level: LogLevel = LogLevel.INFO,
                     file_path: Optional[Union[str, Path]] = None,
                     console_output: bool = True,
                     json_format: bool = True):
    """Configure global logging."""
    logger = get_logger()
    logger.set_log_level(log_level)
    
    # Clear existing outputs
    logger.outputs.clear()
    logger.formatters.clear()
    
    # Add console output if requested
    if console_output:
        console_output_obj = ConsoleLogOutput()
        formatter = LogFormatter("text" if not json_format else "json")
        logger.add_output(console_output_obj, formatter)
    
    # Add file output if requested
    if file_path:
        logger.add_file_output(file_path, "json" if json_format else "text")
    
    return logger