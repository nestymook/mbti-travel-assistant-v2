"""
Tests for tool metadata API endpoints.

This module contains comprehensive tests for the tool metadata REST API endpoints,
ensuring proper authentication, error handling, and response formatting.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from unittest.mock import Mock, patch, AsyncMock
from api.tool_metadata_endpoints import router
from middleware.auth_middleware import get_current_user
from models.tool_metadata_models import (
    ToolsMetadataResponse,
    ToolMetadata,
    ToolCategory,
    MBTIPersonalityType,
    ParameterType,
    ParameterSchema,
    ResponseSchema
)
from services.tool_metadata_service import ToolMetadataService


# Mock user for testing
def mock_get_current_user():
    return {
        "username": "test_user",
        "user_id": "user_123",
        "email": "test@example.com"
    }


# Create test app with dependency override
app = FastAPI()

# Override the auth dependency for testing
app.dependency_overrides[get_current_user] = mock_get_current_user

app.include_router(router)

# Create test client
client = TestClient(app)


class TestToolMetadataEndpoints:
    """Test cases for tool metadata API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user = {
            "username": "test_user",
            "user_id": "user_123",
            "email": "test@example.com"
        }
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_all_tools_metadata_success(self, mock_service):
        """Test successful retrieval of all tools metadata."""
        # Mock service response
        mock_metadata = ToolsMetadataResponse(
            tools=[],
            total_tools=5,
            categories=[ToolCategory.SEARCH, ToolCategory.ANALYSIS, ToolCategory.RECOMMENDATION],
            supported_mbti_types=[MBTIPersonalityType.ENFP, MBTIPersonalityType.INTJ],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        mock_service.get_all_tools_metadata.return_value = mock_metadata
        
        # Make request
        response = client.get("/tools/metadata")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["total_tools"] == 5
        assert data["version"] == "1.0.0"
        assert len(data["categories"]) == 3
        assert len(data["supported_mbti_types"]) == 2
        
        # Verify service was called
        mock_service.get_all_tools_metadata.assert_called_once()
    
    def test_get_all_tools_metadata_unauthenticated(self):
        """Test unauthenticated request to get all tools metadata."""
        # Create a new app without auth override for this test
        test_app = FastAPI()
        test_app.include_router(router)
        test_client = TestClient(test_app)
        
        # Make request without authentication
        response = test_client.get("/tools/metadata")
        
        # Should fail due to authentication
        assert response.status_code == 401
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_all_tools_metadata_service_error(self, mock_service):
        """Test service error when getting all tools metadata."""
        # Mock service error
        mock_service.get_all_tools_metadata.side_effect = Exception("Service error")
        
        # Make request
        response = client.get("/tools/metadata")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "Failed to generate tools metadata"
        assert data["detail"]["type"] == "MetadataGenerationError"
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_tool_metadata_success(self, mock_service):
        """Test successful retrieval of specific tool metadata."""
        # Mock service response
        mock_tool = ToolMetadata(
            name="search_restaurants_by_district",
            display_name="Search Restaurants by District",
            category=ToolCategory.SEARCH,
            description="Test description",
            purpose="Test purpose",
            parameters={
                "districts": ParameterSchema(
                    type=ParameterType.ARRAY,
                    description="Test parameter",
                    required=True
                )
            },
            response_schema=ResponseSchema(
                type=ParameterType.OBJECT,
                description="Test response"
            ),
            use_cases=[],
            mbti_integration=[],
            examples=[],
            endpoint="/api/v1/restaurants/search/district",
            http_method="POST"
        )
        mock_service.get_tool_metadata.return_value = mock_tool
        
        # Make request
        response = client.get("/tools/metadata/search_restaurants_by_district")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "search_restaurants_by_district"
        assert data["display_name"] == "Search Restaurants by District"
        assert data["category"] == "search"
        assert data["endpoint"] == "/api/v1/restaurants/search/district"
        
        # Verify service was called
        mock_service.get_tool_metadata.assert_called_once_with("search_restaurants_by_district")
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_tool_metadata_not_found(self, mock_service):
        """Test retrieval of non-existent tool metadata."""
        # Mock service error
        mock_service.get_tool_metadata.side_effect = ValueError("Tool 'invalid_tool' not found")
        
        # Make request
        response = client.get("/tools/metadata/invalid_tool")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "Tool not found"
        assert data["detail"]["type"] == "ToolNotFoundError"
        assert "available_tools" in data["detail"]
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_tools_by_category_success(self, mock_service):
        """Test successful retrieval of tools by category."""
        # Mock service response
        mock_metadata = ToolsMetadataResponse(
            tools=[
                ToolMetadata(
                    name="search_restaurants_by_district",
                    display_name="Search Restaurants by District",
                    category=ToolCategory.SEARCH,
                    description="Test description",
                    purpose="Test purpose",
                    parameters={},
                    response_schema=ResponseSchema(
                        type=ParameterType.OBJECT,
                        description="Test response"
                    ),
                    use_cases=[],
                    mbti_integration=[],
                    examples=[],
                    endpoint="/api/v1/restaurants/search/district",
                    http_method="POST"
                )
            ],
            total_tools=3,
            categories=[ToolCategory.SEARCH],
            supported_mbti_types=[MBTIPersonalityType.ENFP],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        mock_service.get_all_tools_metadata.return_value = mock_metadata
        
        # Make request
        response = client.get("/tools/metadata/categories/search")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["tools"][0]["category"] == "search"
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_tools_by_category_not_found(self, mock_service):
        """Test retrieval of tools by non-existent category."""
        # Mock service response with no matching tools
        mock_metadata = ToolsMetadataResponse(
            tools=[
                ToolMetadata(
                    name="search_restaurants_by_district",
                    display_name="Search Restaurants by District",
                    category=ToolCategory.SEARCH,
                    description="Test description",
                    purpose="Test purpose",
                    parameters={},
                    response_schema=ResponseSchema(
                        type=ParameterType.OBJECT,
                        description="Test response"
                    ),
                    use_cases=[],
                    mbti_integration=[],
                    examples=[],
                    endpoint="/api/v1/restaurants/search/district",
                    http_method="POST"
                )
            ],
            total_tools=1,
            categories=[ToolCategory.SEARCH],
            supported_mbti_types=[MBTIPersonalityType.ENFP],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        mock_service.get_all_tools_metadata.return_value = mock_metadata
        
        # Make request for non-existent category
        response = client.get("/tools/metadata/categories/invalid_category")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "Category not found"
        assert data["detail"]["type"] == "CategoryNotFoundError"
        assert "available_categories" in data["detail"]
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_tools_for_mbti_type_success(self, mock_service):
        """Test successful retrieval of tools for MBTI type."""
        # Mock service response
        mock_metadata = ToolsMetadataResponse(
            tools=[],
            total_tools=5,
            categories=[ToolCategory.SEARCH],
            supported_mbti_types=[MBTIPersonalityType.ENFP, MBTIPersonalityType.INTJ],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        mock_service.get_all_tools_metadata.return_value = mock_metadata
        
        # Make request
        response = client.get("/tools/metadata/mbti/ENFP")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["supported_mbti_types"] == ["ENFP"]
    
    @patch('api.tool_metadata_endpoints.tool_metadata_service')
    def test_get_tools_for_mbti_type_invalid(self, mock_service):
        """Test retrieval of tools for invalid MBTI type."""
        # Mock service response
        mock_metadata = ToolsMetadataResponse(
            tools=[],
            total_tools=5,
            categories=[ToolCategory.SEARCH],
            supported_mbti_types=[MBTIPersonalityType.ENFP, MBTIPersonalityType.INTJ],
            version="1.0.0",
            last_updated="2025-01-03T10:30:00Z"
        )
        mock_service.get_all_tools_metadata.return_value = mock_metadata
        
        # Make request with invalid MBTI type
        response = client.get("/tools/metadata/mbti/INVALID")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "MBTI type not supported"
        assert data["detail"]["type"] == "MBTITypeNotFoundError"
        assert "supported_types" in data["detail"]
    
    def test_metadata_health_check_success(self):
        """Test successful health check."""
        with patch('api.tool_metadata_endpoints.tool_metadata_service') as mock_service:
            # Mock service response
            mock_metadata = ToolsMetadataResponse(
                tools=[],
                total_tools=5,
                categories=[ToolCategory.SEARCH, ToolCategory.ANALYSIS, ToolCategory.RECOMMENDATION],
                supported_mbti_types=[MBTIPersonalityType.ENFP, MBTIPersonalityType.INTJ],
                version="1.0.0",
                last_updated="2025-01-03T10:30:00Z"
            )
            mock_service.get_all_tools_metadata.return_value = mock_metadata
            
            # Make request
            response = client.get("/tools/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "tool_metadata_service"
            assert data["tools_available"] == 5
            assert data["categories"] == 3
            assert data["mbti_types_supported"] == 2
            assert data["version"] == "1.0.0"
    
    def test_metadata_health_check_failure(self):
        """Test health check failure."""
        with patch('api.tool_metadata_endpoints.tool_metadata_service') as mock_service:
            # Mock service error
            mock_service.get_all_tools_metadata.side_effect = Exception("Service error")
            
            # Make request
            response = client.get("/tools/health")
            
            # Verify error response
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["service"] == "tool_metadata_service"
            assert "error" in data


class TestToolMetadataEndpointsIntegration:
    """Integration tests for tool metadata endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user = {
            "username": "test_user",
            "user_id": "user_123",
            "email": "test@example.com"
        }
    
    def test_real_service_integration(self):
        """Test endpoints with real service integration."""
        # Test get all tools metadata
        response = client.get("/tools/metadata")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tools"] == 5
        assert len(data["tools"]) == 5
        
        # Test get specific tool
        response = client.get("/tools/metadata/search_restaurants_by_district")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "search_restaurants_by_district"
        
        # Test get tools by category
        response = client.get("/tools/metadata/categories/search")
        assert response.status_code == 200
        data = response.json()
        assert all(tool["category"] == "search" for tool in data["tools"])
        
        # Test get tools for MBTI type
        response = client.get("/tools/metadata/mbti/ENFP")
        assert response.status_code == 200
        data = response.json()
        assert data["supported_mbti_types"] == ["ENFP"]
    
    def test_error_handling_consistency(self):
        """Test consistent error handling across endpoints."""
        # Test 404 errors
        not_found_tests = [
            ("/tools/metadata/invalid_tool", "ToolNotFoundError"),
            ("/tools/metadata/categories/invalid_category", "CategoryNotFoundError"),
            ("/tools/metadata/mbti/INVALID", "MBTITypeNotFoundError")
        ]
        
        for endpoint, error_type in not_found_tests:
            response = client.get(endpoint)
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["type"] == error_type
            assert "error" in data["detail"]
            assert "message" in data["detail"]
    
    def test_health_check_no_auth_required(self):
        """Test that health check doesn't require authentication."""
        # Create app without auth override
        test_app = FastAPI()
        test_app.include_router(router)
        test_client = TestClient(test_app)
        
        # Make request without authentication
        response = test_client.get("/tools/health")
        
        # Should succeed (health check bypasses auth)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_response_format_consistency(self):
        """Test that all endpoints return consistent response formats."""
        # Test all metadata endpoints
        endpoints = [
            "/tools/metadata",
            "/tools/metadata/categories/search",
            "/tools/metadata/mbti/ENFP"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            
            # All should have these fields
            assert "tools" in data
            assert "total_tools" in data
            assert "categories" in data
            assert "supported_mbti_types" in data
            assert "version" in data
            assert "last_updated" in data
            
            # Validate data types
            assert isinstance(data["tools"], list)
            assert isinstance(data["total_tools"], int)
            assert isinstance(data["categories"], list)
            assert isinstance(data["supported_mbti_types"], list)
            assert isinstance(data["version"], str)
            assert isinstance(data["last_updated"], str)
    
    def test_case_insensitive_mbti_types(self):
        """Test that MBTI type endpoints handle case variations."""
        # Test different case variations
        case_variations = ["enfp", "ENFP", "Enfp", "eNfP"]
        
        for variation in case_variations:
            response = client.get(f"/tools/metadata/mbti/{variation}")
            assert response.status_code == 200
            data = response.json()
            assert data["supported_mbti_types"] == ["ENFP"]  # Should always return uppercase