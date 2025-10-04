#!/usr/bin/env python3
"""
FastAPI authentication integration test.

This script tests the authentication middleware integration with FastAPI
without requiring actual JWT tokens from Cognito.
"""

import sys
import os
sys.path.insert(0, '.')

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime, timezone

from middleware.auth_middleware import AuthenticationMiddleware, get_current_user
from middleware.jwt_validator import UserContext


def create_test_app():
    """Create a test FastAPI application with authentication."""
    app = FastAPI(title="Test App")
    
    # Add authentication middleware
    app.add_middleware(
        AuthenticationMiddleware,
        bypass_paths=["/health", "/docs", "/"]
    )
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    @app.get("/")
    async def root():
        return {"message": "root"}
    
    @app.get("/protected")
    async def protected(current_user: UserContext = Depends(get_current_user)):
        return {
            "message": "protected endpoint",
            "user_id": current_user.user_id,
            "username": current_user.username
        }
    
    return app


def test_bypass_endpoints():
    """Test that bypass endpoints work without authentication."""
    print("Testing bypass endpoints...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health endpoint bypasses authentication")
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "root"
    print("✓ Root endpoint bypasses authentication")


def test_protected_endpoint_no_auth():
    """Test that protected endpoints require authentication."""
    print("\nTesting protected endpoint without authentication...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Test protected endpoint without auth
    response = client.get("/protected")
    assert response.status_code == 401
    assert "Authorization header required" in response.json()["error"]["message"]
    print("✓ Protected endpoint requires authentication")


def test_protected_endpoint_invalid_auth():
    """Test protected endpoint with invalid authentication."""
    print("\nTesting protected endpoint with invalid authentication...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Test with invalid authorization format
    response = client.get(
        "/protected",
        headers={"Authorization": "Invalid format"}
    )
    assert response.status_code == 401
    assert "Invalid authorization header format" in response.json()["error"]["message"]
    print("✓ Invalid authorization format rejected")
    
    # Test with empty token
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer "}
    )
    assert response.status_code == 401
    assert "JWT token is required" in response.json()["error"]["message"]
    print("✓ Empty token rejected")


@patch('middleware.auth_middleware.jwt_validator.validate_token')
def test_protected_endpoint_valid_auth(mock_validate):
    """Test protected endpoint with valid authentication."""
    print("\nTesting protected endpoint with valid authentication...")
    
    # Mock successful token validation
    mock_user = UserContext(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        token_claims={"sub": "test-user-123", "token_use": "access"},
        authenticated_at=datetime.now(timezone.utc)
    )
    mock_validate.return_value = mock_user
    
    app = create_test_app()
    client = TestClient(app)
    
    # Test protected endpoint with valid token
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer valid-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "protected endpoint"
    assert data["user_id"] == "test-user-123"
    assert data["username"] == "testuser"
    
    # Verify the token was validated
    mock_validate.assert_called_once_with("valid-token")
    
    print("✓ Valid authentication works correctly")


def test_main_app_integration():
    """Test integration with the main application."""
    print("\nTesting main application integration...")
    
    try:
        from main import app
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✓ Main app health endpoint works")
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "AgentCore Gateway" in response.json()["service"]
        print("✓ Main app root endpoint works")
        
        # Test auth test endpoint without token
        response = client.get("/auth/test")
        assert response.status_code == 401
        print("✓ Main app auth test endpoint requires authentication")
        
        return True
        
    except Exception as e:
        print(f"✗ Main app integration test failed: {e}")
        return False


def main():
    """Run all FastAPI authentication tests."""
    print("Running FastAPI authentication integration tests...\n")
    
    try:
        test_bypass_endpoints()
        test_protected_endpoint_no_auth()
        test_protected_endpoint_invalid_auth()
        test_protected_endpoint_valid_auth()
        
        if test_main_app_integration():
            print("\n✅ All FastAPI authentication integration tests passed!")
            print("\nAuthentication middleware is properly integrated with FastAPI.")
            print("Key integration features verified:")
            print("- Middleware properly intercepts requests")
            print("- Bypass paths work correctly")
            print("- Authentication errors are handled properly")
            print("- Valid authentication flows work")
            print("- Main application integration works")
            
            return True
        else:
            print("\n❌ Main app integration test failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)