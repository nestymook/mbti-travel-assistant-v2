"""
Health Check Service

This module provides comprehensive health checking capabilities for the
MBTI Travel Assistant MCP service, including dependency health checks,
system resource monitoring, and health status reporting.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import psutil

from .mcp_client_manager import MCPClientManager
from .cache_service import CacheService
from .cloudwatch_monitor import CloudWatchMonitor

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['status'] = self.status.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""
    overall_status: HealthStatus
    checks: List[HealthCheckResult]
    system_info: Dict[str, Any]
    uptime_seconds: float
    timestamp: datetime
    environment: str
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "overall_status": self.overall_status.value,
            "checks": [check.to_dict() for check in self.checks],
            "system_info": self.system_info,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment,
            "version": self.version
        }


class HealthChecker:
    """
    Comprehensive health checking service for MBTI Travel Assistant.
    
    Performs health checks on all system dependencies including MCP servers,
    cache, authentication, and system resources.
    """
    
    def __init__(
        self,
        mcp_client_manager: MCPClientManager,
        cache_service: CacheService,
        cloudwatch_monitor: Optional[CloudWatchMonitor] = None,
        environment: str = "development"
    ):
        """
        Initialize health checker.
        
        Args:
            mcp_client_manager: MCP client manager instance
            cache_service: Cache service instance
            cloudwatch_monitor: Optional CloudWatch monitor
            environment: Environment name
        """
        self.mcp_client_manager = mcp_client_manager
        self.cache_service = cache_service
        self.cloudwatch_monitor = cloudwatch_monitor
        self.environment = environment
        self.start_time = datetime.now()
        
        # Health check configuration
        self.check_timeout = 10.0  # seconds
        self.critical_checks = {
            "mcp_search_server",
            "mcp_reasoning_server",
            "system_resources"
        }
        
        logger.info(f"Initialized HealthChecker for {environment}")
    
    async def perform_health_check(self, include_detailed: bool = False) -> SystemHealthReport:
        """
        Perform comprehensive health check.
        
        Args:
            include_detailed: Include detailed system information
            
        Returns:
            System health report
        """
        logger.info("Starting comprehensive health check")
        start_time = time.time()
        
        # Perform all health checks
        checks = await self._run_all_checks()
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        # Collect system information
        system_info = self._collect_system_info(include_detailed)
        
        # Calculate uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Create health report
        report = SystemHealthReport(
            overall_status=overall_status,
            checks=checks,
            system_info=system_info,
            uptime_seconds=uptime_seconds,
            timestamp=datetime.now(),
            environment=self.environment
        )
        
        # Send metrics to CloudWatch if available
        if self.cloudwatch_monitor:
            await self._send_health_metrics(report)
        
        duration = time.time() - start_time
        logger.info(f"Health check completed in {duration:.2f}s - Status: {overall_status.value}")
        
        return report
    
    async def _run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks concurrently"""
        check_tasks = [
            self._check_mcp_search_server(),
            self._check_mcp_reasoning_server(),
            self._check_cache_service(),
            self._check_system_resources(),
            self._check_memory_usage(),
            self._check_disk_space(),
            self._check_network_connectivity()
        ]
        
        # Add optional checks
        if self.cloudwatch_monitor:
            check_tasks.append(self._check_cloudwatch_connectivity())
        
        # Run checks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*check_tasks, return_exceptions=True),
                timeout=self.check_timeout * 2
            )
            
            # Process results and handle exceptions
            checks = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    check_name = f"check_{i}"
                    checks.append(HealthCheckResult(
                        name=check_name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Check failed with exception: {str(result)}",
                        duration_ms=0.0,
                        timestamp=datetime.now()
                    ))
                else:
                    checks.append(result)
            
            return checks
            
        except asyncio.TimeoutError:
            logger.error("Health checks timed out")
            return [HealthCheckResult(
                name="health_check_timeout",
                status=HealthStatus.UNHEALTHY,
                message="Health checks timed out",
                duration_ms=self.check_timeout * 2 * 1000,
                timestamp=datetime.now()
            )]
    
    async def _check_mcp_search_server(self) -> HealthCheckResult:
        """Check MCP search server health"""
        start_time = time.time()
        
        try:
            # Test connection to search MCP server
            result = await asyncio.wait_for(
                self.mcp_client_manager.test_search_connection(),
                timeout=self.check_timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result:
                return HealthCheckResult(
                    name="mcp_search_server",
                    status=HealthStatus.HEALTHY,
                    message="Search MCP server is responding",
                    duration_ms=duration_ms,
                    timestamp=datetime.now(),
                    metadata={"endpoint": self.mcp_client_manager.search_endpoint}
                )
            else:
                return HealthCheckResult(
                    name="mcp_search_server",
                    status=HealthStatus.UNHEALTHY,
                    message="Search MCP server is not responding",
                    duration_ms=duration_ms,
                    timestamp=datetime.now()
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name="mcp_search_server",
                status=HealthStatus.UNHEALTHY,
                message="Search MCP server connection timed out",
                duration_ms=self.check_timeout * 1000,
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheckResult(
                name="mcp_search_server",
                status=HealthStatus.UNHEALTHY,
                message=f"Search MCP server check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _check_mcp_reasoning_server(self) -> HealthCheckResult:
        """Check MCP reasoning server health"""
        start_time = time.time()
        
        try:
            # Test connection to reasoning MCP server
            result = await asyncio.wait_for(
                self.mcp_client_manager.test_reasoning_connection(),
                timeout=self.check_timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result:
                return HealthCheckResult(
                    name="mcp_reasoning_server",
                    status=HealthStatus.HEALTHY,
                    message="Reasoning MCP server is responding",
                    duration_ms=duration_ms,
                    timestamp=datetime.now(),
                    metadata={"endpoint": self.mcp_client_manager.reasoning_endpoint}
                )
            else:
                return HealthCheckResult(
                    name="mcp_reasoning_server",
                    status=HealthStatus.UNHEALTHY,
                    message="Reasoning MCP server is not responding",
                    duration_ms=duration_ms,
                    timestamp=datetime.now()
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name="mcp_reasoning_server",
                status=HealthStatus.UNHEALTHY,
                message="Reasoning MCP server connection timed out",
                duration_ms=self.check_timeout * 1000,
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheckResult(
                name="mcp_reasoning_server",
                status=HealthStatus.UNHEALTHY,
                message=f"Reasoning MCP server check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _check_cache_service(self) -> HealthCheckResult:
        """Check cache service health"""
        start_time = time.time()
        
        try:
            # Test cache operations
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.now().isoformat()}
            
            # Test set operation
            await self.cache_service.set(test_key, test_value, ttl=60)
            
            # Test get operation
            retrieved_value = await self.cache_service.get(test_key)
            
            # Test delete operation
            await self.cache_service.delete(test_key)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if retrieved_value == test_value:
                return HealthCheckResult(
                    name="cache_service",
                    status=HealthStatus.HEALTHY,
                    message="Cache service is working correctly",
                    duration_ms=duration_ms,
                    timestamp=datetime.now(),
                    metadata={"cache_type": type(self.cache_service).__name__}
                )
            else:
                return HealthCheckResult(
                    name="cache_service",
                    status=HealthStatus.DEGRADED,
                    message="Cache service returned incorrect data",
                    duration_ms=duration_ms,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="cache_service",
                status=HealthStatus.UNHEALTHY,
                message=f"Cache service check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 70:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Elevated memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 95:
                status = HealthStatus.UNHEALTHY
                messages.append(f"High disk usage: {disk.percent:.1f}%")
            elif disk.percent > 80:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                messages.append(f"Elevated disk usage: {disk.percent:.1f}%")
            
            message = "; ".join(messages) if messages else "System resources are healthy"
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"System resource check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _check_memory_usage(self) -> HealthCheckResult:
        """Check detailed memory usage"""
        start_time = time.time()
        
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check for memory leaks (simplified)
            process_memory_mb = process_memory.rss / (1024 * 1024)
            
            status = HealthStatus.HEALTHY
            if process_memory_mb > 1024:  # 1GB
                status = HealthStatus.DEGRADED
            if process_memory_mb > 2048:  # 2GB
                status = HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                name="memory_usage",
                status=status,
                message=f"Process memory usage: {process_memory_mb:.1f}MB",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                metadata={
                    "process_memory_mb": process_memory_mb,
                    "system_memory_percent": memory.percent,
                    "system_memory_available_gb": memory.available / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.UNKNOWN,
                message=f"Memory usage check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check disk space availability"""
        start_time = time.time()
        
        try:
            disk = psutil.disk_usage('/')
            duration_ms = (time.time() - start_time) * 1000
            
            free_gb = disk.free / (1024**3)
            used_percent = (disk.used / disk.total) * 100
            
            status = HealthStatus.HEALTHY
            if used_percent > 95:
                status = HealthStatus.UNHEALTHY
            elif used_percent > 85:
                status = HealthStatus.DEGRADED
            
            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=f"Disk usage: {used_percent:.1f}%, {free_gb:.1f}GB free",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                metadata={
                    "used_percent": used_percent,
                    "free_gb": free_gb,
                    "total_gb": disk.total / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Disk space check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity"""
        start_time = time.time()
        
        try:
            # Test external connectivity
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get('https://httpbin.org/status/200') as response:
                    if response.status == 200:
                        duration_ms = (time.time() - start_time) * 1000
                        return HealthCheckResult(
                            name="network_connectivity",
                            status=HealthStatus.HEALTHY,
                            message="Network connectivity is working",
                            duration_ms=duration_ms,
                            timestamp=datetime.now()
                        )
                    else:
                        return HealthCheckResult(
                            name="network_connectivity",
                            status=HealthStatus.DEGRADED,
                            message=f"Network test returned status {response.status}",
                            duration_ms=(time.time() - start_time) * 1000,
                            timestamp=datetime.now()
                        )
                        
        except Exception as e:
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Network connectivity check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _check_cloudwatch_connectivity(self) -> HealthCheckResult:
        """Check CloudWatch connectivity"""
        start_time = time.time()
        
        try:
            # Test CloudWatch connectivity by listing metrics
            metrics = self.cloudwatch_monitor.cloudwatch.list_metrics(
                Namespace=self.cloudwatch_monitor.namespace,
                MaxRecords=1
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name="cloudwatch_connectivity",
                status=HealthStatus.HEALTHY,
                message="CloudWatch connectivity is working",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                metadata={"namespace": self.cloudwatch_monitor.namespace}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="cloudwatch_connectivity",
                status=HealthStatus.DEGRADED,
                message=f"CloudWatch connectivity check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    def _determine_overall_status(self, checks: List[HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status"""
        if not checks:
            return HealthStatus.UNKNOWN
        
        # Check critical components first
        critical_unhealthy = False
        critical_degraded = False
        
        for check in checks:
            if check.name in self.critical_checks:
                if check.status == HealthStatus.UNHEALTHY:
                    critical_unhealthy = True
                elif check.status == HealthStatus.DEGRADED:
                    critical_degraded = True
        
        # If any critical component is unhealthy, system is unhealthy
        if critical_unhealthy:
            return HealthStatus.UNHEALTHY
        
        # Count status types
        status_counts = {status: 0 for status in HealthStatus}
        for check in checks:
            status_counts[check.status] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0 or critical_degraded:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.UNKNOWN] > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _collect_system_info(self, include_detailed: bool = False) -> Dict[str, Any]:
        """Collect system information"""
        try:
            info = {
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                "platform": psutil.sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
            if include_detailed:
                info.update({
                    "network_interfaces": list(psutil.net_if_addrs().keys()),
                    "process_count": len(psutil.pids()),
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                })
            
            return info
            
        except Exception as e:
            logger.warning(f"Failed to collect system info: {e}")
            return {"error": str(e)}
    
    async def _send_health_metrics(self, report: SystemHealthReport):
        """Send health metrics to CloudWatch"""
        try:
            # Send overall health status as metric
            health_value = {
                HealthStatus.HEALTHY: 1.0,
                HealthStatus.DEGRADED: 0.5,
                HealthStatus.UNHEALTHY: 0.0,
                HealthStatus.UNKNOWN: -1.0
            }.get(report.overall_status, -1.0)
            
            await asyncio.to_thread(
                self.cloudwatch_monitor.put_metric,
                "HealthStatus",
                health_value,
                self.cloudwatch_monitor.MetricUnit.COUNT,
                {"Environment": self.environment}
            )
            
            # Send individual check metrics
            for check in report.checks:
                check_value = {
                    HealthStatus.HEALTHY: 1.0,
                    HealthStatus.DEGRADED: 0.5,
                    HealthStatus.UNHEALTHY: 0.0,
                    HealthStatus.UNKNOWN: -1.0
                }.get(check.status, -1.0)
                
                await asyncio.to_thread(
                    self.cloudwatch_monitor.put_metric,
                    f"HealthCheck_{check.name}",
                    check_value,
                    self.cloudwatch_monitor.MetricUnit.COUNT,
                    {"Environment": self.environment}
                )
                
                # Send check duration
                await asyncio.to_thread(
                    self.cloudwatch_monitor.put_metric,
                    f"HealthCheckDuration_{check.name}",
                    check.duration_ms,
                    self.cloudwatch_monitor.MetricUnit.MILLISECONDS,
                    {"Environment": self.environment}
                )
            
        except Exception as e:
            logger.warning(f"Failed to send health metrics to CloudWatch: {e}")
    
    async def get_quick_health_status(self) -> Dict[str, Any]:
        """Get quick health status without full checks"""
        try:
            # Basic system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            
            # Determine quick status
            if cpu_percent > 90 or memory.percent > 90:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 70 or memory.percent > 70:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return {
                "status": status.value,
                "uptime_seconds": uptime_seconds,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }