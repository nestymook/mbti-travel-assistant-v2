#!/usr/bin/env python3
"""
Demonstration script for the authentication service.

This script shows how to use the CognitoAuthenticator and TokenValidator
classes for JWT token management and Cognito authentication.
"""

import asyncio
import json
from services.auth_service import (
    CognitoAuthenticator,
    TokenValidator,
    JWKSManager,
    AuthenticationMiddleware,
    AuthenticationError,
    create_cognito_authenticator_from_config,
    create_token_validator_from_config
)


def demo_basic_initialization():
    """Demonstrate basic initialization of authentication components."""
    print("=== Basic Initialization Demo ===")
    
    # Initialize CognitoAuthenticator
    authenticator = CognitoAuthenticator(
        user_pool_id="us-east-1_wBAxW7yd4",
        client_id="26k0pnja579pdpb1pt6savs27e",
        region="us-east-1"
    )
    print(f"✓ CognitoAuthenticator initialized for pool: {authenticator.user_pool_id}")
    
    # Initialize TokenValidator
    config = {
        'user_pool_id': 'us-east-1_wBAxW7yd4',
        'client_id': '26k0pnja579pdpb1pt6savs27e',
        'region': 'us-east-1',
        'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_wBAxW7yd4/.well-known/openid-configuration'
    }
    validator = TokenValidator(config)
    print(f"✓ TokenValidator initialized for discovery URL: {validator.discovery_url}")
    
    # Initialize JWKSManager
    jwks_manager = JWKSManager(config['discovery_url'])
    print(f"✓ JWKSManager initialized with cache TTL: {jwks_manager.cache_ttl} seconds")
    
    print()


def demo_config_file_loading():
    """Demonstrate loading authentication components from config file."""
    print("=== Config File Loading Demo ===")
    
    try:
        # Load from existing cognito_config.json
        authenticator = create_cognito_authenticator_from_config("cognito_config.json")
        print(f"✓ CognitoAuthenticator loaded from config: {authenticator.user_pool_id}")
        
        validator = create_token_validator_from_config("cognito_config.json")
        print(f"✓ TokenValidator loaded from config: {validator.client_id}")
        
    except AuthenticationError as e:
        print(f"✗ Config loading failed: {e.message}")
        print(f"  Error type: {e.error_type}")
        print(f"  Suggested action: {e.suggested_action}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print()


def demo_srp_utilities():
    """Demonstrate SRP utility functions."""
    print("=== SRP Utilities Demo ===")
    
    authenticator = CognitoAuthenticator(
        user_pool_id="us-east-1_wBAxW7yd4",
        client_id="26k0pnja579pdpb1pt6savs27e",
        region="us-east-1"
    )
    
    # Generate SRP 'a' value
    srp_a, big_a = authenticator._generate_srp_a()
    print(f"✓ Generated SRP 'a' value: {srp_a}")
    print(f"✓ Generated SRP 'A' value (first 20 chars): {big_a[:20]}...")
    
    # Calculate password claim (with dummy values)
    try:
        claim = authenticator._calculate_password_claim(
            username="demo_user",
            password="demo_password",
            srp_a=srp_a,
            srp_b="ABCDEF123456789",
            salt="123456789ABC",
            secret_block="demo_secret_block"
        )
        print(f"✓ Password claim calculated successfully")
        print(f"  Signature length: {len(claim['signature'])} characters")
        print(f"  Timestamp: {claim['timestamp']}")
    except Exception as e:
        print(f"✗ Password claim calculation failed: {e}")
    
    print()


def demo_bearer_token_utilities():
    """Demonstrate Bearer token extraction utilities."""
    print("=== Bearer Token Utilities Demo ===")
    
    middleware = AuthenticationMiddleware(None)  # Mock validator for demo
    
    # Test various token formats
    test_cases = [
        ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "Valid Bearer token"),
        ("Basic dGVzdDp0ZXN0", "Basic auth (should fail)"),
        ("Bearer ", "Empty Bearer token"),
        ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "Token without Bearer prefix"),
        ("", "Empty string")
    ]
    
    for auth_header, description in test_cases:
        token = middleware.extract_bearer_token(auth_header)
        status = "✓" if token else "✗"
        result = token if token else "None"
        print(f"{status} {description}: {result}")
    
    print()


def demo_error_handling():
    """Demonstrate error handling and error response creation."""
    print("=== Error Handling Demo ===")
    
    # Create and demonstrate AuthenticationError
    try:
        raise AuthenticationError(
            error_type="DEMO_ERROR",
            error_code="DEMO_CODE_001",
            message="This is a demonstration error",
            details="Error created for demonstration purposes",
            suggested_action="This is just a demo, no action needed"
        )
    except AuthenticationError as e:
        print(f"✓ AuthenticationError caught successfully:")
        print(f"  Type: {e.error_type}")
        print(f"  Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  Details: {e.details}")
        print(f"  Suggested Action: {e.suggested_action}")
    
    # Demonstrate error response creation
    middleware = AuthenticationMiddleware(None)
    response = middleware.create_error_response(
        "DEMO_ERROR",
        "Demo error message",
        "Demo error details"
    )
    
    print(f"✓ Error response created:")
    print(f"  Status Code: {response.status_code}")
    
    try:
        response_data = json.loads(response.body.decode())
        print(f"  Response Body: {json.dumps(response_data, indent=2)}")
    except Exception as e:
        print(f"  Response Body (raw): {response.body}")
    
    print()


async def demo_jwks_manager():
    """Demonstrate JWKS manager functionality."""
    print("=== JWKS Manager Demo ===")
    
    discovery_url = 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_wBAxW7yd4/.well-known/openid-configuration'
    jwks_manager = JWKSManager(discovery_url, cache_ttl=300)  # 5 minute cache
    
    print(f"✓ JWKS Manager initialized")
    print(f"  Discovery URL: {jwks_manager.discovery_url}")
    print(f"  JWKS URL: {jwks_manager.jwks_url}")
    print(f"  Cache TTL: {jwks_manager.cache_ttl} seconds")
    
    # Check cache status
    is_expired = jwks_manager.is_cache_expired()
    print(f"  Cache expired: {is_expired}")
    print(f"  Cached keys count: {len(jwks_manager.jwks_keys)}")
    
    # Note: We don't actually fetch JWKS in demo to avoid network calls
    print("  (Skipping actual JWKS fetch in demo mode)")
    
    print()


def main():
    """Run all demonstration functions."""
    print("🔐 Authentication Service Demonstration")
    print("=" * 50)
    print()
    
    # Run synchronous demos
    demo_basic_initialization()
    demo_config_file_loading()
    demo_srp_utilities()
    demo_bearer_token_utilities()
    demo_error_handling()
    
    # Run async demo
    asyncio.run(demo_jwks_manager())
    
    print("=" * 50)
    print("✅ Authentication service demonstration completed!")
    print()
    print("Key Features Demonstrated:")
    print("• CognitoAuthenticator for SRP authentication")
    print("• TokenValidator for JWT token validation")
    print("• JWKSManager for JWKS key management")
    print("• AuthenticationMiddleware for request processing")
    print("• Configuration utilities for easy setup")
    print("• Comprehensive error handling")
    print("• Bearer token extraction and validation")


if __name__ == "__main__":
    main()