"""
Load Testing Module for Enhanced MCP Status Check System.

This module provides comprehensive load testing capabilities for concurrent
dual health checks and performance validation under various load conditions.

Requirements covered: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import asyncio
import time
import statistics
import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import concurrent.futures
from datetime import datetime
import psutil
import threading

from enhanced_mcp_status_check.services.enhanced_health_check_service import EnhancedHealthCheckService
from enhanced_mcp_status_check.models.dual_health_models import (
    DualHealthCheckResult, MCPHealthCheckResult, RESTHealthCheckResult,
    EnhancedServerConfig, ServerStatus
)


class LoadTestingMetrics:
    """Metrics collection for load testing."""
    
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.failure_count = 0
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
        self.cpu_usage = []
        self.concurrent_connections = 0
        self.max_concurrent_connections = 0
    
    def record_response_time(self, response_time: float):
        """Record response time for a request."""
        self.response_times.append(response_time)
    
    def record_success(self):
        """Record a successful request."""
        self.success_count += 1
    
    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
    
    def start_monitoring(self):
        """Start monitoring system resources."""
        self.start_time = time.time()
        self._monitor_resources()
    
    def stop_monitori