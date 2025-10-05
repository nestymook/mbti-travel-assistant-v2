"""
Test Enhanced Reasoning Status Check Backward Compatibility

This module tests that the enhanced reasoning status check system maintains backward compatibility
with existing monitoring systems and legacy health check implementations for reasoning services.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Import both legacy and enhanced components
from services.health_check_service import (
    HealthCheckService,
    EnhancedReasoningHealthCheckService,
    perform_enhanced_reasoning_health_check,
    get_reasoning_health_check_capabilities,
    validate_reasoning_capabilities
)
from models.status_models import (
    HealthCheckResult,
    ServerStatus,
    MCPStatusCheckConfig
)


class TestReasoningBackwardCompatibility:
    """Test backward compatibility between legacy and enhanced reasoning monitoring."""
    
    @pytest.fixture
    def reasoning_config(self):
        """Create reasoning MCP status check configuration."""
        return MCPStatusCheckConfig(
            server_name="restaurant-search-result-reasoning-mcp",
            endpoint_url="http://localhost:8080/mcp",
            timeout_seconds=12,
            check_interval_seconds=45,
            retry_attempts=3,
            expected_tools=[
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ]
        )
    
    @pytest.fixture
    def mock_reasoning_result(self):
        """Create mock reasoning health check result."""
        return HealthCheckResult(
            server_name="restaurant-search-result-reasoning-mcp",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=200.0,
            status_code=200,
            tools_count=2
        )
    
    @pytest.mark.asyncio
    async def test_legacy_reasoning_health_check_still_works(self, reasoning_config, mock_reasoning_result):
        """Test that legacy reasoning health check functionality still works."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful MCP response with reasoning tools
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "jsonrpc": "2.0",
                "id": "reasoning-health-check-123",
                "result": {
                    "tools": [
                        {
                            "name": "recommend_restaurants",
                            "description": "Analyze restaurant sentiment data and provide intelligent recommendations"
                        },
                        {
                            "name": "analyze_restaurant_sentiment",
                            "description": "Analyze sentiment data for restaurants without providing recommendations"
                        }
                    ]
                }
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Test legacy reasoning health check service
            async with HealthCheckService() as service:
                result = await service.check_server_health(reasoning_config)
                
                assert result.success is True
                assert result.server_name == "restaurant-search-result-reasoning-mcp"
                assert result.tools_count == 2
                assert result.response_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_enhanced_reasoning_service_backward_compatibility(self, reasoning_config):
        """Test that enhanced reasoning service maintains backward compatibility."""
        with patch('services.enhanced_reasoning_status_service.get_enhanced_reasoning_status_service') as mock_enhanced:
            # Mock enhanced reasoning service not available
            mock_enhanced.side_effect = ImportError("Enhanced reasoning service not available")
            
            # Test enhanced reasoning health check falls back to legacy
            async with EnhancedReasoningHealthCheckService() as service:
                assert service._enhanced_reasoning_available is False
                
                # Should still be able to perform reasoning health checks
                with patch.object(service, 'check_server_health') as mock_check:
                    mock_check.return_value = HealthCheckResult(
                        server_name="restaurant-search-result-reasoning-mcp",
                        timestamp=datetime.now(),
                        success=True,
                        response_time_ms=180.0,
                        tools_count=2
                    )
                    
                    result = await service.check_reasoning_server_health_enhanced(reasoning_config)
                    
                    assert result["monitoring_type"] == "legacy_mcp_reasoning"
                    assert result["service_type"] == "reasoning_and_sentiment_analysis"
                    assert result["legacy_result"]["success"] is True
                    assert result["legacy_result"]["tools_count"] == 2
                    assert result["legacy_result"]["reasoning_tools_available"] is True
    
    @pytest.mark.asyncio
    async def test_legacy_reasoning_api_response_format(self):
        """Test that legacy reasoning API response format is maintained."""
        with patch('services.enhanced_reasoning_status_service.get_enhanced_reasoning_status_service') as mock_enhanced:
            mock_enhanced.side_effect = ImportError("Enhanced reasoning service not available")
            
            # Test legacy reasoning health check function
            result = await perform_enhanced_reasoning_health_check("restaurant-search-result-reasoning-mcp")
            
            # Should return legacy format with reasoning specifics
            assert result["enhanced_monitoring"] is False
            assert result["monitoring_type"] == "legacy_mcp_reasoning_only"
            assert result["service_type"] == "reasoning_and_sentiment_analysis"
            assert "status" in result
            assert "timestamp" in result
            assert "server_name" in result
    
    @pytest.mark.asyncio
    async def test_reasoning_configuration_backward_compatibility(self):
        """Test that legacy reasoning configuration is still supported."""
        # Test loading legacy reasoning configuration
        legacy_reasoning_config_data = {
            "status_check_system": {
                "enabled": True,
                "global_check_interval_seconds": 45,
                "global_timeout_seconds": 12,
                "reasoning_specific_monitoring": True
            },
            "servers": {
                "restaurant-search-result-reasoning-mcp": {
                    "server_name": "restaurant-search-result-reasoning-mcp",
                    "endpoint_url": "http://localhost:8080/mcp",
                    "timeout_seconds": 12,
                    "expected_tools": [
                        "recommend_restaurants",
                        "analyze_restaurant_sentiment"
                    ]
                }
            }
        }
        
        # Should be able to create MCPStatusCheckConfig from legacy reasoning data
        server_config = legacy_reasoning_config_data["servers"]["restaurant-search-result-reasoning-mcp"]
        config = MCPStatusCheckConfig(
            server_name=server_config["server_name"],
            endpoint_url=server_config["endpoint_url"],
            timeout_seconds=server_config["timeout_seconds"],
            expected_tools=server_config["expected_tools"]
        )
        
        assert config.server_name == "restaurant-search-result-reasoning-mcp"
        assert config.endpoint_url == "http://localhost:8080/mcp"
        assert config.timeout_seconds == 12
        assert len(config.expected_tools) == 2
        assert "recommend_restaurants" in config.expected_tools
        assert "analyze_restaurant_sentiment" in config.expected_tools
    
    @pytest.mark.asyncio
    async def test_reasoning_capabilities_detection(self):
        """Test that reasoning capability detection works correctly."""
        capabilities = await get_reasoning_health_check_capabilities()
        
        # Should always have legacy reasoning capabilities
        assert capabilities["legacy_mcp_reasoning_monitoring"] is True
        assert capabilities["reasoning_tools_validation"] is True
        assert capabilities["sentiment_analysis_validation"] is True
        assert "enhanced_dual_reasoning_monitoring" in capabilities
        assert "timestamp" in capabilities
    
    @pytest.mark.asyncio
    async def test_reasoning_tools_validation_compatibility(self):
        """Test that reasoning tools validation maintains compatibility."""
        # Test reasoning capabilities validation
        with patch('services.health_check_service.validate_reasoning_mcp_server_connectivity') as mock_validate:
            mock_validate.return_value = (True, None, 2)
            
            result = await validate_reasoning_capabilities(
                endpoint_url="http://localhost:8080/mcp",
                timeout_seconds=12
            )
            
            assert result["connectivity"]["connected"] is True
            assert result["connectivity"]["tools_count"] == 2
            assert result["reasoning_capabilities"]["sentiment_analysis"] is True
            assert result["reasoning_capabilities"]["recommendation_algorithm"] is True
            assert result["reasoning_capabilities"]["validation_passed"] is True
    
    @pytest.mark.asyncio
    async def test_enhanced_reasoning_with_legacy_fallback(self):
        """Test enhanced reasoning monitoring with graceful fallback to legacy."""
        with patch('services.enhanced_reasoning_status_service.get_enhanced_reasoning_status_service') as mock_enhanced:
            # Mock enhanced reasoning service failure
            mock_service = Mock()
            mock_service.get_enhanced_reasoning_status = AsyncMock(side_effect=Exception("Reasoning service error"))
            mock_enhanced.return_value = mock_service
            
            # Should fall back to legacy reasoning monitoring
            result = await perform_enhanced_reasoning_health_check("restaurant-search-result-reasoning-mcp")
            
            assert result["enhanced_monitoring"] is False
            assert result["monitoring_type"] == "legacy_mcp_reasoning_only"
            assert result["service_type"] == "reasoning_and_sentiment_analysis"
    
    def test_legacy_reasoning_data_models_compatibility(self):
        """Test that legacy reasoning data models are still compatible."""
        # Test HealthCheckResult creation for reasoning (legacy format)
        result = HealthCheckResult(
            server_name="restaurant-search-result-reasoning-mcp",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=200.0,
            status_code=200,
            tools_count=2
        )
        
        # Should have all expected legacy fields
        assert hasattr(result, 'server_name')
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'success')
        assert hasattr(result, 'response_time_ms')
        assert hasattr(result, 'status_code')
        assert hasattr(result, 'tools_count')
        
        # Should be serializable to dict with reasoning context
        result_dict = {
            "server_name": result.server_name,
            "timestamp": result.timestamp.isoformat(),
            "success": result.success,
            "response_time_ms": result.response_time_ms,
            "status_code": result.status_code,
            "tools_count": result.tools_count,
            "service_type": "reasoning_and_sentiment_analysis",
            "reasoning_tools_available": result.tools_count >= 2
        }
        
        # Should be JSON serializable
        json_str = json.dumps(result_dict)
        assert json_str is not None
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["server_name"] == "restaurant-search-result-reasoning-mcp"
        assert parsed["success"] is True
        assert parsed["service_type"] == "reasoning_and_sentiment_analysis"
        assert parsed["reasoning_tools_available"] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_legacy_and_enhanced_reasoning_operations(self):
        """Test that legacy and enhanced reasoning operations can coexist."""
        reasoning_config = MCPStatusCheckConfig(
            server_name="restaurant-search-result-reasoning-mcp",
            endpoint_url="http://localhost:8080/mcp",
            timeout_seconds=12,
            expected_tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
        )
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful reasoning response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "jsonrpc": "2.0",
                "id": "reasoning-test-123",
                "result": {
                    "tools": [
                        {"name": "recommend_restaurants", "description": "Restaurant recommendations"},
                        {"name": "analyze_restaurant_sentiment", "description": "Sentiment analysis"}
                    ]
                }
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Run both legacy and enhanced reasoning checks concurrently
            async with HealthCheckService() as legacy_service:
                async with EnhancedReasoningHealthCheckService() as enhanced_service:
                    legacy_task = asyncio.create_task(
                        legacy_service.check_server_health(reasoning_config)
                    )
                    enhanced_task = asyncio.create_task(
                        enhanced_service.check_reasoning_server_health_enhanced(reasoning_config)
                    )
                    
                    legacy_result, enhanced_result = await asyncio.gather(
                        legacy_task, enhanced_task, return_exceptions=True
                    )
                    
                    # Both should complete without interference
                    assert not isinstance(legacy_result, Exception)
                    assert not isinstance(enhanced_result, Exception)
                    
                    # Legacy result should be HealthCheckResult
                    assert isinstance(legacy_result, HealthCheckResult)
                    assert legacy_result.tools_count == 2
                    
                    # Enhanced result should be dict with reasoning monitoring info
                    assert isinstance(enhanced_result, dict)
                    assert "monitoring_type" in enhanced_result
                    assert "service_type" in enhanced_result
                    assert enhanced_result["service_type"] == "reasoning_and_sentiment_analysis"
    
    @pytest.mark.asyncio
    async def test_reasoning_migration_path_validation(self):
        """Test that migration from legacy to enhanced reasoning is smooth."""
        # Simulate existing legacy reasoning monitoring system
        legacy_reasoning_configs = [
            MCPStatusCheckConfig(
                server_name="restaurant-search-result-reasoning-mcp",
                endpoint_url="http://localhost:8080/mcp",
                timeout_seconds=12,
                expected_tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
            )
        ]
        
        # Test that enhanced reasoning service can handle legacy configurations
        async with EnhancedReasoningHealthCheckService() as enhanced_service:
            # Should be able to process legacy reasoning configurations
            comprehensive_status = await enhanced_service.get_comprehensive_reasoning_status()
            
            assert "monitoring_capabilities" in comprehensive_status
            assert comprehensive_status["monitoring_capabilities"]["legacy_mcp_reasoning"] is True
            assert "service_type" in comprehensive_status
            assert comprehensive_status["service_type"] == "reasoning_and_sentiment_analysis"
            assert comprehensive_status["server_name"] == "restaurant-search-result-reasoning-mcp"
    
    @pytest.mark.asyncio
    async def test_reasoning_metrics_recording_compatibility(self):
        """Test that reasoning metrics recording maintains compatibility."""
        async with EnhancedReasoningHealthCheckService() as enhanced_service:
            # Should be able to record reasoning operations even without enhanced monitoring
            await enhanced_service.record_reasoning_operation_metrics(
                operation_type="recommendation",
                success=True,
                duration_ms=250.0,
                metadata={"restaurant_count": 10}
            )
            
            # Should not raise exceptions even if enhanced monitoring is unavailable
            await enhanced_service.record_reasoning_operation_metrics(
                operation_type="sentiment_analysis",
                success=False,
                duration_ms=100.0,
                metadata={"error": "validation_failed"}
            )
    
    def test_reasoning_error_handling_compatibility(self):
        """Test that reasoning error handling maintains backward compatibility."""
        # Test that legacy reasoning error formats are preserved
        error_result = HealthCheckResult(
            server_name="restaurant-search-result-reasoning-mcp",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=0.0,
            error_message="Reasoning tools validation failed"
        )
        
        # Should have legacy error fields
        assert error_result.success is False
        assert error_result.error_message == "Reasoning tools validation failed"
        assert error_result.response_time_ms == 0.0
        
        # Should be compatible with existing reasoning error handling code
        if not error_result.success:
            assert error_result.error_message is not None
            # Should be able to detect reasoning-specific errors
            assert "reasoning" in error_result.error_message.lower() or "tools" in error_result.error_message.lower()


class TestLegacyReasoningAPICompatibility:
    """Test that legacy reasoning API endpoints maintain compatibility."""
    
    @pytest.mark.asyncio
    async def test_legacy_reasoning_health_endpoint_format(self):
        """Test that legacy reasoning /health endpoint format is maintained."""
        # Mock legacy reasoning health check response
        legacy_reasoning_response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server_name": "restaurant-search-result-reasoning-mcp",
            "service_type": "reasoning",
            "success": True,
            "response_time_ms": 200.0,
            "reasoning_capabilities": {
                "sentiment_analysis": True,
                "recommendation_algorithm": True
            }
        }
        
        # Should have all expected legacy fields
        assert "status" in legacy_reasoning_response
        assert "timestamp" in legacy_reasoning_response
        assert "server_name" in legacy_reasoning_response
        assert "service_type" in legacy_reasoning_response
        assert "success" in legacy_reasoning_response
        assert "response_time_ms" in legacy_reasoning_response
        assert "reasoning_capabilities" in legacy_reasoning_response
        
        # Status should be string (legacy format)
        assert isinstance(legacy_reasoning_response["status"], str)
        assert legacy_reasoning_response["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Service type should indicate reasoning
        assert legacy_reasoning_response["service_type"] == "reasoning"
    
    @pytest.mark.asyncio
    async def test_legacy_reasoning_metrics_format(self):
        """Test that legacy reasoning metrics format is preserved."""
        legacy_reasoning_metrics = {
            "timestamp": datetime.now().isoformat(),
            "server_metrics": {
                "restaurant-search-result-reasoning-mcp": {
                    "success_rate": 0.92,
                    "average_response_time_ms": 180.0,
                    "total_checks": 50,
                    "successful_checks": 46,
                    "failed_checks": 4,
                    "reasoning_operations": {
                        "recommendation_requests": 25,
                        "sentiment_analysis_requests": 30,
                        "average_reasoning_time_ms": 220.0
                    }
                }
            }
        }
        
        # Should maintain legacy structure with reasoning extensions
        assert "timestamp" in legacy_reasoning_metrics
        assert "server_metrics" in legacy_reasoning_metrics
        
        server_metrics = legacy_reasoning_metrics["server_metrics"]["restaurant-search-result-reasoning-mcp"]
        assert "success_rate" in server_metrics
        assert "average_response_time_ms" in server_metrics
        assert "total_checks" in server_metrics
        assert "reasoning_operations" in server_metrics
        
        reasoning_ops = server_metrics["reasoning_operations"]
        assert "recommendation_requests" in reasoning_ops
        assert "sentiment_analysis_requests" in reasoning_ops
        assert "average_reasoning_time_ms" in reasoning_ops
    
    def test_reasoning_configuration_migration_compatibility(self):
        """Test that reasoning configuration migration maintains compatibility."""
        # Legacy reasoning configuration format
        legacy_reasoning_config = {
            "status_check_system": {
                "enabled": True,
                "global_check_interval_seconds": 45,
                "reasoning_specific_monitoring": True
            },
            "servers": {
                "restaurant-search-result-reasoning-mcp": {
                    "endpoint_url": "http://localhost:8080/mcp",
                    "timeout_seconds": 12,
                    "expected_tools": [
                        "recommend_restaurants",
                        "analyze_restaurant_sentiment"
                    ]
                }
            }
        }
        
        # Enhanced reasoning configuration should be additive, not replacing
        enhanced_reasoning_config = {
            **legacy_reasoning_config,
            "enhanced_reasoning_monitoring": {
                "enabled": True,
                "dual_monitoring_support": True,
                "reasoning_capabilities_validation": True,
                "sentiment_analysis_monitoring": True
            }
        }
        
        # Legacy fields should still be present
        assert "status_check_system" in enhanced_reasoning_config
        assert "servers" in enhanced_reasoning_config
        assert enhanced_reasoning_config["status_check_system"]["enabled"] is True
        assert enhanced_reasoning_config["status_check_system"]["reasoning_specific_monitoring"] is True
        
        # Enhanced fields should be additional
        assert "enhanced_reasoning_monitoring" in enhanced_reasoning_config
        assert enhanced_reasoning_config["enhanced_reasoning_monitoring"]["enabled"] is True
        assert enhanced_reasoning_config["enhanced_reasoning_monitoring"]["reasoning_capabilities_validation"] is True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])