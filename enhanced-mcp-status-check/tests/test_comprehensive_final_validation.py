"""
Comprehensive Final Validation Test Suite for Enhanced MCP Status Check System.

This test suite provides complete validation of all dual monitoring scenarios,
load testing, compatibility testing, security testing, and performance regression testing.

Requirements covered: 1.1, 2.1, 3.1, 8.1, 9.1, 10.1
"""

import asyncio
import json
import time
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
import concurrent.futures
from datetime import datetime, timedelta

from enhanced_mcp_status_check.services.enhanced_health_check_service import EnhancedHealthCheckService
from enhanced_mcp_status_check.services.mcp_health_check_client import MCPHealthCheckClient
from enhanced_mcp_status_check.services.rest_health_check_client import RESTHealthCheckClient
from enhanced_mcp_status_check.services.health_result_aggregator import HealthResultAggregator
from enhanced_mcp_status_check.services.enhanced_circuit_breaker import EnhancedCircuitBreaker
from enhanced_mcp_status_check.services.dual_metrics_collector import DualMetricsCollector
from enhanced_mcp_status_check.services.authentication_service import AuthenticationService
from enhanced_mcp_status_check.models.dual_health_models import (
    DualHealthCheckResult, MCPHealthCheckResult, RESTHealthCheckResult,
    EnhancedServerConfig, ServerStatus
)
from enhanced_mcp_status_check.config.enhanced_status_config import EnhancedStatusConfig


class TestComprehensiveFinalValidation:
    """Comprehensive test suite for final validation of enhanced MCP status check system."""

    @pytest.fixture
    def enhanced_service(self):
        """Create enhanced health check service for testing."""
        return EnhancedHealthCheckService()

    @pytest.fixture
    def sample_server_configs(self):
        """Create sample server configurations for testing."""
        return [
            EnhancedServerConfig(
                server_name="restaurant-search-mcp",
                mcp_endpoint_url="http://localhost:8001/mcp",
                rest_health_endpoint_url="http://localhost:8001/status/health",
                mcp_enabled=True,
                rest_enabled=True,
                mcp_timeout_seconds=10,
                rest_timeout_seconds=8,
                mcp_expected_tools=["search_restaurants_by_district", "recommend_restaurants"],
                jwt_token="test-jwt-token"
            ),
            EnhancedServerConfig(
                server_name="restaurant-reasoning-mcp",
                mcp_endpoint_url="http://localhost:8002/mcp",
                rest_health_endpoint_url="http://localhost:8002/status/health",
                mcp_enabled=True,
                rest_enabled=True,
                mcp_timeout_seconds=10,
                rest_timeout_seconds=8,
                mcp_expected_tools=["analyze_restaurant_results", "provide_reasoning"],
                jwt_token="test-jwt-token"
            ),
            EnhancedServerConfig(
                server_name="mbti-travel-assistant-mcp",
                mcp_endpoint_url="http://localhost:8003/mcp",
                rest_health_endpoint_url="http://localhost:8003/status/health",
                mcp_enabled=True,
                rest_enabled=True,
                mcp_timeout_seconds=10,
                rest_timeout_seconds=8,
                mcp_expected_tools=["get_mbti_recommendations", "create_itinerary"],
                jwt_token="test-jwt-token"
            )
        ]

    @pytest.mark.asyncio
    async def test_dual_monitoring_all_success_scenario(self, enhanced_service, sample_server_configs):
        """Test dual monitoring when both MCP and REST checks succeed."""
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock successful MCP response
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=150.0,
                tools_count=2,
                expected_tools_found=["search_restaurants_by_district", "recommend_restaurants"],
                missing_tools=[],
                validation_errors=[],
                request_id="test-request-1",
                jsonrpc_version="2.0"
            )
            
            # Mock successful REST response
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=120.0,
                status_code=200,
                health_endpoint_url="http://localhost:8001/status/health",
                response_body={"status": "healthy", "uptime": 3600}
            )
            
            result = await enhanced_service.perform_dual_health_check(sample_server_configs[0])
            
            assert result.overall_success is True
            assert result.overall_status == ServerStatus.HEALTHY
            assert result.mcp_success is True
            assert result.rest_success is True
            assert result.available_paths == ["mcp", "rest"]
            assert result.health_score >= 0.9

    @pytest.mark.asyncio
    async def test_dual_monitoring_mcp_fail_rest_success_scenario(self, enhanced_service, sample_server_configs):
        """Test dual monitoring when MCP fails but REST succeeds."""
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock failed MCP response
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                tools_count=None,
                expected_tools_found=[],
                missing_tools=["search_restaurants_by_district", "recommend_restaurants"],
                validation_errors=["Connection timeout"],
                request_id="test-request-1",
                jsonrpc_version="2.0"
            )
            
            # Mock successful REST response
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=120.0,
                status_code=200,
                health_endpoint_url="http://localhost:8001/status/health",
                response_body={"status": "healthy", "uptime": 3600}
            )
            
            result = await enhanced_service.perform_dual_health_check(sample_server_configs[0])
            
            assert result.overall_success is False
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.mcp_success is False
            assert result.rest_success is True
            assert result.available_paths == ["rest"]
            assert 0.3 <= result.health_score <= 0.7

    @pytest.mark.asyncio
    async def test_dual_monitoring_mcp_success_rest_fail_scenario(self, enhanced_service, sample_server_configs):
        """Test dual monitoring when MCP succeeds but REST fails."""
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock successful MCP response
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=150.0,
                tools_count=2,
                expected_tools_found=["search_restaurants_by_district", "recommend_restaurants"],
                missing_tools=[],
                validation_errors=[],
                request_id="test-request-1",
                jsonrpc_version="2.0"
            )
            
            # Mock failed REST response
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                status_code=503,
                health_endpoint_url="http://localhost:8001/status/health",
                http_error="Service Unavailable"
            )
            
            result = await enhanced_service.perform_dual_health_check(sample_server_configs[0])
            
            assert result.overall_success is False
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.mcp_success is True
            assert result.rest_success is False
            assert result.available_paths == ["mcp"]
            assert 0.3 <= result.health_score <= 0.7

    @pytest.mark.asyncio
    async def test_dual_monitoring_both_fail_scenario(self, enhanced_service, sample_server_configs):
        """Test dual monitoring when both MCP and REST fail."""
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock failed MCP response
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                tools_count=None,
                expected_tools_found=[],
                missing_tools=["search_restaurants_by_district", "recommend_restaurants"],
                validation_errors=["Connection timeout"],
                request_id="test-request-1",
                jsonrpc_version="2.0"
            )
            
            # Mock failed REST response
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="restaurant-search-mcp",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                status_code=503,
                health_endpoint_url="http://localhost:8001/status/health",
                http_error="Service Unavailable"
            )
            
            result = await enhanced_service.perform_dual_health_check(sample_server_configs[0])
            
            assert result.overall_success is False
            assert result.overall_status == ServerStatus.UNHEALTHY
            assert result.mcp_success is False
            assert result.rest_success is False
            assert result.available_paths == []
            assert result.health_score <= 0.3

    @pytest.mark.asyncio
    async def test_load_testing_concurrent_dual_health_checks(self, enhanced_service, sample_server_configs):
        """Test load testing with concurrent dual health checks."""
        concurrent_requests = 50
        
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock responses with varying response times
            def mock_mcp_response(*args, **kwargs):
                return MCPHealthCheckResult(
                    server_name="test-server",
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=100.0 + (time.time() % 50),  # Simulate varying response times
                    tools_count=2,
                    expected_tools_found=["tool1", "tool2"],
                    missing_tools=[],
                    validation_errors=[],
                    request_id=f"test-request-{time.time()}",
                    jsonrpc_version="2.0"
                )
            
            def mock_rest_response(*args, **kwargs):
                return RESTHealthCheckResult(
                    server_name="test-server",
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=80.0 + (time.time() % 40),  # Simulate varying response times
                    status_code=200,
                    health_endpoint_url="http://localhost:8001/status/health",
                    response_body={"status": "healthy"}
                )
            
            mock_mcp.side_effect = mock_mcp_response
            mock_rest.side_effect = mock_rest_response
            
            # Execute concurrent health checks
            start_time = time.time()
            tasks = []
            
            for i in range(concurrent_requests):
                task = enhanced_service.perform_dual_health_check(sample_server_configs[0])
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Validate load testing results
            assert len(results) == concurrent_requests
            assert all(result.overall_success for result in results)
            
            # Check performance metrics
            total_time = end_time - start_time
            requests_per_second = concurrent_requests / total_time
            
            # Should handle at least 10 requests per second
            assert requests_per_second >= 10.0
            
            # Check that all requests completed within reasonable time
            assert total_time <= 30.0  # 30 seconds max for 50 concurrent requests

    @pytest.mark.asyncio
    async def test_compatibility_with_existing_monitoring_systems(self, enhanced_service):
        """Test compatibility with existing monitoring systems."""
        # Test backward compatibility with existing status check implementations
        legacy_config = {
            "servers": [
                {
                    "name": "restaurant-search-mcp",
                    "endpoint": "http://localhost:8001",
                    "timeout": 10
                }
            ]
        }
        
        # Test that enhanced system can handle legacy configuration
        enhanced_config = EnhancedStatusConfig()
        migrated_config = enhanced_config.migrate_legacy_config(legacy_config)
        
        assert migrated_config is not None
        assert len(migrated_config.servers) == 1
        assert migrated_config.servers[0].server_name == "restaurant-search-mcp"
        assert migrated_config.servers[0].mcp_enabled is True
        assert migrated_config.servers[0].rest_enabled is True

    @pytest.mark.asyncio
    async def test_security_authentication_authorization(self, enhanced_service):
        """Test security aspects including authentication and authorization."""
        auth_service = AuthenticationService()
        
        # Test JWT token validation
        valid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.test.signature"
        invalid_token = "invalid.token.here"
        
        with patch.object(auth_service, 'validate_jwt_token') as mock_validate:
            mock_validate.return_value = True
            
            # Test valid authentication
            is_valid = await auth_service.validate_request_authentication(
                {"Authorization": f"Bearer {valid_token}"}
            )
            assert is_valid is True
            
            mock_validate.return_value = False
            
            # Test invalid authentication
            is_valid = await auth_service.validate_request_authentication(
                {"Authorization": f"Bearer {invalid_token}"}
            )
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_security_bypass_attempts(self, enhanced_service):
        """Test security against bypass attempts."""
        # Test various security bypass scenarios
        bypass_attempts = [
            {"Authorization": ""},  # Empty auth
            {"Authorization": "Bearer "},  # Empty token
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Wrong auth type
            {},  # No auth header
            {"Authorization": "Bearer ../../../etc/passwd"},  # Path traversal attempt
            {"Authorization": "Bearer <script>alert('xss')</script>"},  # XSS attempt
        ]
        
        auth_service = AuthenticationService()
        
        for attempt in bypass_attempts:
            is_valid = await auth_service.validate_request_authentication(attempt)
            assert is_valid is False, f"Security bypass detected for: {attempt}"

    @pytest.mark.asyncio
    async def test_performance_regression_testing(self, enhanced_service, sample_server_configs):
        """Test performance regression to ensure system maintains performance standards."""
        # Baseline performance metrics
        baseline_metrics = {
            "single_check_max_time": 2.0,  # seconds
            "concurrent_10_max_time": 5.0,  # seconds
            "memory_usage_max_mb": 100,  # MB
            "cpu_usage_max_percent": 50  # %
        }
        
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock fast responses
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=50.0,
                tools_count=2,
                expected_tools_found=["tool1", "tool2"],
                missing_tools=[],
                validation_errors=[],
                request_id="test-request",
                jsonrpc_version="2.0"
            )
            
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=40.0,
                status_code=200,
                health_endpoint_url="http://localhost:8001/status/health",
                response_body={"status": "healthy"}
            )
            
            # Test single check performance
            start_time = time.time()
            result = await enhanced_service.perform_dual_health_check(sample_server_configs[0])
            single_check_time = time.time() - start_time
            
            assert single_check_time <= baseline_metrics["single_check_max_time"]
            assert result.overall_success is True
            
            # Test concurrent checks performance
            start_time = time.time()
            tasks = [
                enhanced_service.perform_dual_health_check(sample_server_configs[0])
                for _ in range(10)
            ]
            results = await asyncio.gather(*tasks)
            concurrent_check_time = time.time() - start_time
            
            assert concurrent_check_time <= baseline_metrics["concurrent_10_max_time"]
            assert all(result.overall_success for result in results)

    @pytest.mark.asyncio
    async def test_end_to_end_validation_complete_workflow(self, enhanced_service, sample_server_configs):
        """Test complete end-to-end validation of enhanced monitoring system."""
        # Initialize all components
        circuit_breaker = EnhancedCircuitBreaker()
        metrics_collector = DualMetricsCollector()
        
        # Test complete workflow: health check -> aggregation -> circuit breaker -> metrics
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock responses for all servers
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=150.0,
                tools_count=2,
                expected_tools_found=["tool1", "tool2"],
                missing_tools=[],
                validation_errors=[],
                request_id="test-request",
                jsonrpc_version="2.0"
            )
            
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=120.0,
                status_code=200,
                health_endpoint_url="http://localhost:8001/status/health",
                response_body={"status": "healthy"}
            )
            
            # Execute complete workflow for all servers
            all_results = []
            for config in sample_server_configs:
                # 1. Perform dual health check
                result = await enhanced_service.perform_dual_health_check(config)
                all_results.append(result)
                
                # 2. Update circuit breaker
                await circuit_breaker.evaluate_circuit_state(config.server_name, result)
                
                # 3. Collect metrics
                metrics_collector.record_dual_health_check_result(result)
            
            # Validate end-to-end results
            assert len(all_results) == len(sample_server_configs)
            assert all(result.overall_success for result in all_results)
            
            # Validate circuit breaker states
            for config in sample_server_configs:
                cb_state = await circuit_breaker.get_circuit_state(config.server_name)
                assert cb_state.overall_state == "CLOSED"
                assert cb_state.mcp_state == "CLOSED"
                assert cb_state.rest_state == "CLOSED"
            
            # Validate metrics collection
            collected_metrics = metrics_collector.get_aggregated_metrics()
            assert collected_metrics.total_checks == len(sample_server_configs)
            assert collected_metrics.successful_checks == len(sample_server_configs)
            assert collected_metrics.failed_checks == 0

    @pytest.mark.asyncio
    async def test_failure_recovery_scenarios(self, enhanced_service, sample_server_configs):
        """Test failure recovery scenarios and system resilience."""
        circuit_breaker = EnhancedCircuitBreaker()
        
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Simulate failure scenario
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                tools_count=None,
                expected_tools_found=[],
                missing_tools=["tool1", "tool2"],
                validation_errors=["Connection timeout"],
                request_id="test-request",
                jsonrpc_version="2.0"
            )
            
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                status_code=503,
                health_endpoint_url="http://localhost:8001/status/health",
                http_error="Service Unavailable"
            )
            
            # Trigger multiple failures to open circuit breaker
            for _ in range(5):
                result = await enhanced_service.perform_dual_health_check(sample_server_configs[0])
                await circuit_breaker.evaluate_circuit_state(sample_server_configs[0].server_name, result)
            
            # Verify circuit breaker opened
            cb_state = await circuit_breaker.get_circuit_state(sample_server_configs[0].server_name)
            assert cb_state.overall_state == "OPEN"
            
            # Simulate recovery
            mock_mcp.return_value = MCPHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=150.0,
                tools_count=2,
                expected_tools_found=["tool1", "tool2"],
                missing_tools=[],
                validation_errors=[],
                request_id="test-request",
                jsonrpc_version="2.0"
            )
            
            mock_rest.return_value = RESTHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=120.0,
                status_code=200,
                health_endpoint_url="http://localhost:8001/status/health",
                response_body={"status": "healthy"}
            )
            
            # Wait for circuit breaker to enter half-open state and recover
            await asyncio.sleep(1)  # Simulate time passage
            
            # Trigger successful health checks to close circuit breaker
            for _ in range(3):
                result = await enhanced_service.perform_dual_health_check(sample_server_configs[0])
                await circuit_breaker.evaluate_circuit_state(sample_server_configs[0].server_name, result)
            
            # Verify circuit breaker closed
            cb_state = await circuit_breaker.get_circuit_state(sample_server_configs[0].server_name)
            assert cb_state.overall_state == "CLOSED"

    def test_configuration_validation_comprehensive(self):
        """Test comprehensive configuration validation."""
        config = EnhancedStatusConfig()
        
        # Test valid configuration
        valid_config = {
            "dual_monitoring_enabled": True,
            "mcp_health_checks": {
                "enabled": True,
                "default_timeout_seconds": 10
            },
            "rest_health_checks": {
                "enabled": True,
                "default_timeout_seconds": 8
            },
            "servers": [
                {
                    "server_name": "test-server",
                    "mcp_endpoint_url": "http://localhost:8001/mcp",
                    "rest_health_endpoint_url": "http://localhost:8001/status/health"
                }
            ]
        }
        
        validation_result = config.validate_configuration(valid_config)
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        
        # Test invalid configuration
        invalid_config = {
            "dual_monitoring_enabled": "not_boolean",  # Invalid type
            "servers": []  # Empty servers list
        }
        
        validation_result = config.validate_configuration(invalid_config)
        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0

    @pytest.mark.asyncio
    async def test_stress_testing_high_load(self, enhanced_service, sample_server_configs):
        """Test system under high load stress conditions."""
        high_load_requests = 100
        
        with patch.object(enhanced_service.mcp_client, 'perform_health_check') as mock_mcp, \
             patch.object(enhanced_service.rest_client, 'perform_health_check') as mock_rest:
            
            # Mock responses with realistic delays
            async def mock_mcp_with_delay(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                return MCPHealthCheckResult(
                    server_name="test-server",
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=100.0,
                    tools_count=2,
                    expected_tools_found=["tool1", "tool2"],
                    missing_tools=[],
                    validation_errors=[],
                    request_id="test-request",
                    jsonrpc_version="2.0"
                )
            
            async def mock_rest_with_delay(*args, **kwargs):
                await asyncio.sleep(0.08)  # 80ms delay
                return RESTHealthCheckResult(
                    server_name="test-server",
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=80.0,
                    status_code=200,
                    health_endpoint_url="http://localhost:8001/status/health",
                    response_body={"status": "healthy"}
                )
            
            mock_mcp.side_effect = mock_mcp_with_delay
            mock_rest.side_effect = mock_rest_with_delay
            
            # Execute high load test
            start_time = time.time()
            
            # Use semaphore to limit concurrent connections
            semaphore = asyncio.Semaphore(20)  # Max 20 concurrent requests
            
            async def limited_health_check(config):
                async with semaphore:
                    return await enhanced_service.perform_dual_health_check(config)
            
            tasks = [
                limited_health_check(sample_server_configs[i % len(sample_server_configs)])
                for i in range(high_load_requests)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Validate stress test results
            successful_results = [r for r in results if isinstance(r, DualHealthCheckResult) and r.overall_success]
            failed_results = [r for r in results if not isinstance(r, DualHealthCheckResult) or not r.overall_success]
            
            success_rate = len(successful_results) / len(results)
            total_time = end_time - start_time
            
            # Should maintain at least 95% success rate under high load
            assert success_rate >= 0.95
            
            # Should complete within reasonable time (allowing for delays)
            assert total_time <= 60.0  # 60 seconds max for 100 requests with delays
            
            # Should handle at least 5 requests per second under load
            requests_per_second = high_load_requests / total_time
            assert requests_per_second >= 5.0

    def test_data_integrity_validation(self):
        """Test data integrity and validation throughout the system."""
        # Test dual health check result data integrity
        result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=2,
            rest_success=True,
            rest_response_time_ms=120.0,
            rest_status_code=200,
            combined_response_time_ms=135.0,
            health_score=0.95,
            available_paths=["mcp", "rest"]
        )
        
        # Test serialization and deserialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["server_name"] == "test-server"
        assert result_dict["overall_success"] is True
        assert result_dict["health_score"] == 0.95
        
        # Test data validation
        assert result.validate_data_integrity() is True
        
        # Test invalid data detection
        invalid_result = DualHealthCheckResult(
            server_name="",  # Invalid empty name
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_success=True,
            mcp_response_time_ms=-150.0,  # Invalid negative time
            rest_success=True,
            rest_response_time_ms=120.0,
            combined_response_time_ms=135.0,
            health_score=1.5,  # Invalid score > 1.0
            available_paths=[]
        )
        
        assert invalid_result.validate_data_integrity() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])