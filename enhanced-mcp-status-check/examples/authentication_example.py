"""
Authentication Example for Enhanced MCP Status Check

This example demonstrates how to use the authentication service
for secure MCP and REST health checks with various authentication methods.
"""

import asyncio
import json
from datetime import datetime, timedelta

from models.auth_models import (
    AuthenticationType,
    AuthenticationConfig,
    JWTTokenInfo
)
from models.dual_health_models import EnhancedServerConfig
from services.authentication_service import AuthenticationService
from services.mcp_health_check_client import MCPHealthCheckClient
from services.rest_health_check_client import RESTHealthCheckClient


async def demonstrate_jwt_authentication():
    """Demonstrate JWT authentication with token refresh."""
    print("=== JWT Authentication Example ===")
    
    # Create JWT authentication configuration
    jwt_config = AuthenticationConfig(
        auth_type=AuthenticationType.JWT,
        jwt_discovery_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration",
        jwt_client_id="1ofgeckef3po4i3us4j1m4chvd",
        jwt_client_secret="t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
        jwt_scope=["openid", "email"],
        auto_refresh_enabled=True,
        refresh_buffer_seconds=300
    )
    
    async with AuthenticationService() as auth_service:
        # Authenticate and get headers
        result = await auth_service.authenticate("restaurant-search-mcp", jwt_config)
        
        if result.success:
            print(f"✅ JWT Authentication successful")
            print(f"   Token expires at: {result.expires_at}")
            print(f"   Auth headers: {list(result.auth_headers.keys())}")
            
            # Demonstrate token refresh
            print("\n--- Token Refresh ---")
            refresh_result = await auth_service.refresh_token_if_needed("restaurant-search-mcp", jwt_config)
            
            if refresh_result.success:
                print("✅ Token refresh check completed")
            else:
                print(f"❌ Token refresh failed: {refresh_result.error_message}")
        else:
            print(f"❌ JWT Authentication failed: {result.error_message}")


async def demonstrate_bearer_token_authentication():
    """Demonstrate bearer token authentication."""
    print("\n=== Bearer Token Authentication Example ===")
    
    # Create bearer token configuration
    bearer_config = AuthenticationConfig(
        auth_type=AuthenticationType.BEARER_TOKEN,
        bearer_token="your-bearer-token-here"
    )
    
    async with AuthenticationService() as auth_service:
        result = await auth_service.authenticate("test-server", bearer_config)
        
        if result.success:
            print("✅ Bearer token authentication successful")
            print(f"   Auth headers: {result.auth_headers}")
        else:
            print(f"❌ Bearer token authentication failed: {result.error_message}")


async def demonstrate_api_key_authentication():
    """Demonstrate API key authentication."""
    print("\n=== API Key Authentication Example ===")
    
    # Create API key configuration
    api_key_config = AuthenticationConfig(
        auth_type=AuthenticationType.API_KEY,
        api_key="your-api-key-here",
        api_key_header="X-API-Key"
    )
    
    async with AuthenticationService() as auth_service:
        result = await auth_service.authenticate("api-server", api_key_config)
        
        if result.success:
            print("✅ API key authentication successful")
            print(f"   Auth headers: {result.auth_headers}")
        else:
            print(f"❌ API key authentication failed: {result.error_message}")


async def demonstrate_basic_authentication():
    """Demonstrate basic authentication."""
    print("\n=== Basic Authentication Example ===")
    
    # Create basic auth configuration
    basic_config = AuthenticationConfig(
        auth_type=AuthenticationType.BASIC_AUTH,
        username="testuser",
        password="testpass"
    )
    
    async with AuthenticationService() as auth_service:
        result = await auth_service.authenticate("basic-server", basic_config)
        
        if result.success:
            print("✅ Basic authentication successful")
            print(f"   Auth headers: {list(result.auth_headers.keys())}")
        else:
            print(f"❌ Basic authentication failed: {result.error_message}")


async def demonstrate_oauth2_authentication():
    """Demonstrate OAuth2 client credentials flow."""
    print("\n=== OAuth2 Authentication Example ===")
    
    # Create OAuth2 configuration
    oauth2_config = AuthenticationConfig(
        auth_type=AuthenticationType.OAUTH2,
        oauth2_token_url="https://auth.example.com/oauth/token",
        oauth2_client_id="your-client-id",
        oauth2_client_secret="your-client-secret",
        oauth2_scope=["read", "write"],
        auto_refresh_enabled=True
    )
    
    async with AuthenticationService() as auth_service:
        result = await auth_service.authenticate("oauth2-server", oauth2_config)
        
        if result.success:
            print("✅ OAuth2 authentication successful")
            print(f"   Token expires at: {result.expires_at}")
            print(f"   Auth headers: {list(result.auth_headers.keys())}")
        else:
            print(f"❌ OAuth2 authentication failed: {result.error_message}")


async def demonstrate_custom_headers_authentication():
    """Demonstrate custom headers authentication."""
    print("\n=== Custom Headers Authentication Example ===")
    
    # Create custom headers configuration
    custom_config = AuthenticationConfig(
        auth_type=AuthenticationType.CUSTOM_HEADER,
        custom_headers={
            "X-Custom-Auth": "custom-auth-value",
            "X-Request-ID": "12345",
            "X-Client-Version": "1.0.0"
        }
    )
    
    async with AuthenticationService() as auth_service:
        result = await auth_service.authenticate("custom-server", custom_config)
        
        if result.success:
            print("✅ Custom headers authentication successful")
            print(f"   Auth headers: {result.auth_headers}")
        else:
            print(f"❌ Custom headers authentication failed: {result.error_message}")


async def demonstrate_mcp_health_check_with_auth():
    """Demonstrate MCP health check with authentication."""
    print("\n=== MCP Health Check with Authentication ===")
    
    # Create server configuration with authentication
    auth_config = AuthenticationConfig(
        auth_type=AuthenticationType.BEARER_TOKEN,
        bearer_token="mcp-server-token"
    )
    
    server_config = EnhancedServerConfig(
        server_name="restaurant-search-mcp",
        mcp_endpoint_url="https://your-mcp-server.com/mcp",
        rest_health_endpoint_url="https://your-mcp-server.com/status/health",
        mcp_expected_tools=["search_restaurants_by_district", "recommend_restaurants"],
        auth_config=auth_config
    )
    
    async with AuthenticationService() as auth_service:
        async with MCPHealthCheckClient(auth_service=auth_service) as mcp_client:
            try:
                result = await mcp_client.perform_mcp_health_check(server_config)
                
                if result.success:
                    print("✅ MCP health check with authentication successful")
                    print(f"   Tools found: {result.tools_count}")
                    print(f"   Response time: {result.response_time_ms:.2f}ms")
                else:
                    print(f"❌ MCP health check failed: {result.connection_error or 'Unknown error'}")
            
            except Exception as e:
                print(f"❌ MCP health check error: {str(e)}")


async def demonstrate_rest_health_check_with_auth():
    """Demonstrate REST health check with authentication."""
    print("\n=== REST Health Check with Authentication ===")
    
    # Create server configuration with authentication
    auth_config = AuthenticationConfig(
        auth_type=AuthenticationType.API_KEY,
        api_key="rest-api-key",
        api_key_header="X-API-Key"
    )
    
    server_config = EnhancedServerConfig(
        server_name="restaurant-reasoning-mcp",
        mcp_endpoint_url="https://your-mcp-server.com/mcp",
        rest_health_endpoint_url="https://your-mcp-server.com/status/health",
        auth_config=auth_config
    )
    
    async with AuthenticationService() as auth_service:
        async with RESTHealthCheckClient(auth_service=auth_service) as rest_client:
            try:
                result = await rest_client.perform_rest_health_check(server_config)
                
                if result.success:
                    print("✅ REST health check with authentication successful")
                    print(f"   Status code: {result.status_code}")
                    print(f"   Response time: {result.response_time_ms:.2f}ms")
                else:
                    print(f"❌ REST health check failed: {result.http_error or result.connection_error}")
            
            except Exception as e:
                print(f"❌ REST health check error: {str(e)}")


async def demonstrate_authentication_metrics():
    """Demonstrate authentication metrics collection."""
    print("\n=== Authentication Metrics Example ===")
    
    async with AuthenticationService() as auth_service:
        # Perform several authentication attempts
        configs = [
            AuthenticationConfig(auth_type=AuthenticationType.BEARER_TOKEN, bearer_token="token1"),
            AuthenticationConfig(auth_type=AuthenticationType.API_KEY, api_key="key1", api_key_header="X-API-Key"),
            AuthenticationConfig(auth_type=AuthenticationType.JWT),  # This will fail
        ]
        
        for i, config in enumerate(configs):
            await auth_service.authenticate(f"server-{i}", config)
        
        # Get and display metrics
        metrics = auth_service.get_metrics()
        print(f"Total authentication attempts: {metrics.total_auth_attempts}")
        print(f"Successful attempts: {metrics.successful_auth_attempts}")
        print(f"Failed attempts: {metrics.failed_auth_attempts}")
        print(f"Success rate: {metrics.get_auth_success_rate():.1f}%")
        
        if metrics.auth_errors_by_type:
            print("Error types:")
            for error_type, count in metrics.auth_errors_by_type.items():
                print(f"  {error_type}: {count}")


async def demonstrate_credential_management():
    """Demonstrate secure credential management."""
    print("\n=== Credential Management Example ===")
    
    async with AuthenticationService() as auth_service:
        # Store some tokens for different servers
        token1 = JWTTokenInfo(
            token="server1-token",
            expires_at=datetime.now() + timedelta(hours=1),
            scopes=["read", "write"]
        )
        
        token2 = JWTTokenInfo(
            token="server2-token",
            expires_at=datetime.now() - timedelta(minutes=5),  # Expired
            scopes=["read"]
        )
        
        auth_service._credential_store.store_token("server1", token1)
        auth_service._credential_store.store_token("server2", token2)
        
        # List authenticated servers
        servers = auth_service.list_authenticated_servers()
        print(f"Authenticated servers: {servers}")
        
        # Cleanup expired tokens
        removed_count = auth_service.cleanup_expired_tokens()
        print(f"Expired tokens removed: {removed_count}")
        
        # List servers after cleanup
        servers_after = auth_service.list_authenticated_servers()
        print(f"Servers after cleanup: {servers_after}")
        
        # Clear all credentials
        auth_service.clear_credentials()
        print("All credentials cleared")


async def demonstrate_concurrent_authentication():
    """Demonstrate concurrent authentication handling."""
    print("\n=== Concurrent Authentication Example ===")
    
    async with AuthenticationService() as auth_service:
        # Create multiple authentication tasks
        config = AuthenticationConfig(
            auth_type=AuthenticationType.BEARER_TOKEN,
            bearer_token="concurrent-test-token"
        )
        
        # Run concurrent authentications
        tasks = [
            auth_service.authenticate(f"server-{i}", config)
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Check results
        successful = sum(1 for result in results if result.success)
        print(f"Concurrent authentications: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")


async def main():
    """Run all authentication examples."""
    print("Enhanced MCP Status Check - Authentication Examples")
    print("=" * 60)
    
    # Run authentication method examples
    await demonstrate_bearer_token_authentication()
    await demonstrate_api_key_authentication()
    await demonstrate_basic_authentication()
    await demonstrate_custom_headers_authentication()
    
    # Note: JWT and OAuth2 examples require actual endpoints
    # Uncomment these if you have valid endpoints configured
    # await demonstrate_jwt_authentication()
    # await demonstrate_oauth2_authentication()
    
    # Run health check examples (these will fail without actual servers)
    # await demonstrate_mcp_health_check_with_auth()
    # await demonstrate_rest_health_check_with_auth()
    
    # Run utility examples
    await demonstrate_authentication_metrics()
    await demonstrate_credential_management()
    await demonstrate_concurrent_authentication()
    
    print("\n" + "=" * 60)
    print("Authentication examples completed!")


if __name__ == "__main__":
    asyncio.run(main())