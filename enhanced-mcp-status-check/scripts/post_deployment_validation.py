#!/usr/bin/env python3
"""
Post-Deployment Validation and Monitoring Script

This script performs comprehensive validation and monitoring after deployment
of the Enhanced MCP Status Check System.
"""

import os
import sys
import json
import yaml
import time
import logging
import argparse
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.config_loader import ConfigLoader
from models.dual_health_models import DualHealthCheckResult


class PostDeploymentValidator:
    """Handles post-deployment validation and monitoring."""
    
    def __init__(self, config_path: str, validation_config_path: str = None):
        """Initialize the post-deployment validator.
        
        Args:
            config_path: Path to main configuration file
            validation_config_path: Path to validation configuration file
        """
        self.config_path = config_path
        self.validation_config_path = validation_config_path or "config/examples/validation_config.yaml"
        self.validation_id = f"post-deploy-validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Setup logging
        self.setup_logging()
        
        # Load configurations
        self.config = self.load_configuration()
        self.validation_config = self.load_validation_configuration()
        
        # Initialize services
        self.health_service = None
        self.metrics_collector = DualMetricsCollector()
        
        # Validation state
        self.validation_results = {
            "validation_id": self.validation_id,
            "start_time": None,
            "end_time": None,
            "overall_success": False,
            "test_results": {},
            "performance_metrics": {},
            "issues_found": [],
            "recommendations": []
        }
        
    def setup_logging(self):
        """Setup validation logging."""
        log_dir = Path("logs/post_deployment")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"post_deployment_validation_{self.validation_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting post-deployment validation: {self.validation_id}")
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load main system configuration."""
        try:
            config_loader = ConfigLoader()
            config = config_loader.load_config(self.config_path)
            self.logger.info("Main configuration loaded successfully")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load main configuration: {e}")
            raise
            
    def load_validation_configuration(self) -> Dict[str, Any]:
        """Load validation configuration."""
        try:
            with open(self.validation_config_path, 'r') as f:
                validation_config = yaml.safe_load(f)
            self.logger.info("Validation configuration loaded successfully")
            return validation_config
        except Exception as e:
            self.logger.warning(f"Failed to load validation configuration: {e}")
            return self.get_default_validation_config()
            
    def get_default_validation_config(self) -> Dict[str, Any]:
        """Get default validation configuration."""
        return {
            "validation_tests": {
                "api_endpoints": {
                    "enabled": True,
                    "timeout_seconds": 30,
                    "expected_status_codes": [200],
                    "endpoints": [
                        "/status/health",
                        "/status/metrics",
                        "/status/dual-check",
                        "/status/config"
                    ]
                },
                "dual_health_checks": {
                    "enabled": True,
                    "timeout_seconds": 60,
                    "min_success_rate": 0.95,
                    "max_response_time_ms": 5000
                },
                "circuit_breaker": {
                    "enabled": True,
                    "test_failure_scenarios": True,
                    "recovery_validation": True
                },
                "authentication": {
                    "enabled": True,
                    "test_valid_tokens": True,
                    "test_invalid_tokens": True
                },
                "performance": {
                    "enabled": True,
                    "load_test_duration_minutes": 10,
                    "concurrent_requests": 10,
                    "acceptable_response_time_ms": 2000
                }
            },
            "monitoring_validation": {
                "metrics_collection": {
                    "enabled": True,
                    "collection_interval_seconds": 30,
                    "validation_duration_minutes": 15
                },
                "alerting": {
                    "enabled": True,
                    "test_alert_generation": True,
                    "test_notification_delivery": True
                },
                "dashboards": {
                    "enabled": True,
                    "test_data_display": True,
                    "test_real_time_updates": True
                }
            },
            "success_criteria": {
                "min_overall_success_rate": 0.95,
                "max_average_response_time_ms": 3000,
                "max_error_rate": 0.05,
                "required_uptime_percentage": 99.0
            }
        }
        
    async def validate_api_endpoints(self) -> Dict[str, Any]:
        """Validate API endpoints are working correctly.
        
        Returns:
            Validation results for API endpoints
        """
        self.logger.info("Validating API endpoints...")
        
        api_config = self.validation_config['validation_tests']['api_endpoints']
        if not api_config['enabled']:
            return {"skipped": True, "reason": "API endpoint validation disabled"}
            
        results = {
            "test_name": "api_endpoints",
            "success": True,
            "endpoints_tested": 0,
            "endpoints_passed": 0,
            "endpoint_results": {},
            "issues": []
        }
        
        # Get API base URL
        api_host = self.config.get('api', {}).get('host', 'localhost')
        api_port = self.config.get('api', {}).get('port', 8080)
        base_url = f"http://{api_host}:{api_port}"
        
        timeout = aiohttp.ClientTimeout(total=api_config['timeout_seconds'])
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for endpoint in api_config['endpoints']:
                url = f"{base_url}{endpoint}"
                results['endpoints_tested'] += 1
                
                try:
                    start_time = time.time()
                    async with session.get(url) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        endpoint_result = {
                            "url": url,
                            "status_code": response.status,
                            "response_time_ms": response_time,
                            "success": response.status in api_config['expected_status_codes']
                        }
                        
                        if endpoint_result['success']:
                            results['endpoints_passed'] += 1
                            self.logger.info(f"✅ {endpoint}: {response.status} ({response_time:.1f}ms)")
                        else:
                            results['success'] = False
                            issue = f"Endpoint {endpoint} returned status {response.status}"
                            results['issues'].append(issue)
                            self.logger.error(f"❌ {endpoint}: {response.status}")
                            
                        results['endpoint_results'][endpoint] = endpoint_result
                        
                except Exception as e:
                    results['success'] = False
                    issue = f"Endpoint {endpoint} failed: {str(e)}"
                    results['issues'].append(issue)
                    self.logger.error(f"❌ {endpoint}: {str(e)}")
                    
                    results['endpoint_results'][endpoint] = {
                        "url": url,
                        "error": str(e),
                        "success": False
                    }
                    
        self.logger.info(f"API endpoints validation: {results['endpoints_passed']}/{results['endpoints_tested']} passed")
        return results
        
    async def validate_dual_health_checks(self) -> Dict[str, Any]:
        """Validate dual health check functionality.
        
        Returns:
            Validation results for dual health checks
        """
        self.logger.info("Validating dual health check functionality...")
        
        dual_config = self.validation_config['validation_tests']['dual_health_checks']
        if not dual_config['enabled']:
            return {"skipped": True, "reason": "Dual health check validation disabled"}
            
        results = {
            "test_name": "dual_health_checks",
            "success": True,
            "servers_tested": 0,
            "servers_passed": 0,
            "server_results": {},
            "performance_metrics": {},
            "issues": []
        }
        
        # Initialize health service
        if not self.health_service:
            self.health_service = EnhancedHealthCheckService(self.config)
            
        servers = self.config.get('enhanced_status_check_system', {}).get('servers', [])
        
        for server in servers:
            server_name = server.get('server_name', 'unknown')
            results['servers_tested'] += 1
            
            try:
                # Create server configuration
                from models.dual_health_models import EnhancedServerConfig
                
                server_config = EnhancedServerConfig(
                    server_name=server_name,
                    mcp_endpoint_url=server.get('mcp_endpoint_url', ''),
                    rest_health_endpoint_url=server.get('rest_health_endpoint_url', ''),
                    mcp_enabled=server.get('mcp_enabled', True),
                    rest_enabled=server.get('rest_enabled', True),
                    mcp_timeout_seconds=server.get('mcp_timeout_seconds', 10),
                    rest_timeout_seconds=server.get('rest_timeout_seconds', 8)
                )
                
                # Perform dual health check
                start_time = time.time()
                health_result = await self.health_service.perform_dual_health_check(server_config)
                check_duration = (time.time() - start_time) * 1000
                
                server_result = {
                    "server_name": server_name,
                    "overall_success": health_result.overall_success,
                    "mcp_success": health_result.mcp_success,
                    "rest_success": health_result.rest_success,
                    "combined_response_time_ms": health_result.combined_response_time_ms,
                    "check_duration_ms": check_duration,
                    "health_score": health_result.health_score
                }
                
                # Check success criteria
                success_rate_ok = health_result.overall_success
                response_time_ok = health_result.combined_response_time_ms <= dual_config['max_response_time_ms']
                
                if success_rate_ok and response_time_ok:
                    results['servers_passed'] += 1
                    self.logger.info(f"✅ {server_name}: Dual health check passed")
                else:
                    results['success'] = False
                    issue = f"Server {server_name} failed dual health check criteria"
                    results['issues'].append(issue)
                    self.logger.error(f"❌ {server_name}: Dual health check failed")
                    
                results['server_results'][server_name] = server_result
                
            except Exception as e:
                results['success'] = False
                issue = f"Server {server_name} dual health check error: {str(e)}"
                results['issues'].append(issue)
                self.logger.error(f"❌ {server_name}: {str(e)}")
                
                results['server_results'][server_name] = {
                    "server_name": server_name,
                    "error": str(e),
                    "success": False
                }
                
        # Calculate performance metrics
        if results['server_results']:
            response_times = [r.get('combined_response_time_ms', 0) for r in results['server_results'].values() if 'combined_response_time_ms' in r]
            if response_times:
                results['performance_metrics'] = {
                    "average_response_time_ms": sum(response_times) / len(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times)
                }
                
        self.logger.info(f"Dual health checks validation: {results['servers_passed']}/{results['servers_tested']} passed")
        return results
        
    async def validate_circuit_breaker(self) -> Dict[str, Any]:
        """Validate circuit breaker functionality.
        
        Returns:
            Validation results for circuit breaker
        """
        self.logger.info("Validating circuit breaker functionality...")
        
        cb_config = self.validation_config['validation_tests']['circuit_breaker']
        if not cb_config['enabled']:
            return {"skipped": True, "reason": "Circuit breaker validation disabled"}
            
        results = {
            "test_name": "circuit_breaker",
            "success": True,
            "tests_performed": [],
            "issues": []
        }
        
        try:
            # Test circuit breaker states
            from services.enhanced_circuit_breaker import EnhancedCircuitBreaker
            
            circuit_breaker = EnhancedCircuitBreaker()
            
            # Test normal operation
            test_server = "test-server"
            
            # Simulate successful requests
            for _ in range(5):
                await circuit_breaker.record_success(test_server, "mcp")
                await circuit_breaker.record_success(test_server, "rest")
                
            state = await circuit_breaker.get_circuit_state(test_server)
            
            if state.overall_state == "CLOSED":
                results['tests_performed'].append("normal_operation_passed")
                self.logger.info("✅ Circuit breaker normal operation test passed")
            else:
                results['success'] = False
                results['issues'].append("Circuit breaker should be CLOSED under normal operation")
                
            # Test failure scenarios if enabled
            if cb_config.get('test_failure_scenarios', False):
                # Simulate failures
                for _ in range(10):
                    await circuit_breaker.record_failure(test_server, "mcp")
                    
                state = await circuit_breaker.get_circuit_state(test_server)
                
                if state.mcp_state == "OPEN":
                    results['tests_performed'].append("failure_detection_passed")
                    self.logger.info("✅ Circuit breaker failure detection test passed")
                else:
                    results['success'] = False
                    results['issues'].append("Circuit breaker should open after consecutive failures")
                    
            # Test recovery if enabled
            if cb_config.get('recovery_validation', False):
                # Wait for recovery timeout
                await asyncio.sleep(2)
                
                # Simulate successful request
                await circuit_breaker.record_success(test_server, "mcp")
                
                state = await circuit_breaker.get_circuit_state(test_server)
                
                if state.mcp_state in ["HALF_OPEN", "CLOSED"]:
                    results['tests_performed'].append("recovery_validation_passed")
                    self.logger.info("✅ Circuit breaker recovery test passed")
                else:
                    results['success'] = False
                    results['issues'].append("Circuit breaker should recover after successful requests")
                    
        except Exception as e:
            results['success'] = False
            results['issues'].append(f"Circuit breaker validation error: {str(e)}")
            self.logger.error(f"❌ Circuit breaker validation error: {e}")
            
        return results
        
    async def validate_performance(self) -> Dict[str, Any]:
        """Validate system performance under load.
        
        Returns:
            Validation results for performance
        """
        self.logger.info("Validating system performance...")
        
        perf_config = self.validation_config['validation_tests']['performance']
        if not perf_config['enabled']:
            return {"skipped": True, "reason": "Performance validation disabled"}
 