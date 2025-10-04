#!/usr/bin/env python3
"""
Demonstration of the comprehensive error handling system.

This script shows how different types of errors are handled and converted
to user-friendly messages with appropriate fallback responses.
"""

import asyncio
import json
from unittest.mock import patch, AsyncMock, Mock
from services.gateway_http_client import GatewayHTTPClient, Environment
from services.error_handler import (
    ErrorHandler, ErrorContext, GatewayConnectionError, GatewayServiceError,
    GatewayValidationError, GatewayAuthenticationError, GatewayTimeoutError,
    GatewayRateLimitError, handle_gateway_error, create_fallback_response
)


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_error_response(response, title="Error Response"):
    """Pretty print an error response."""
    print(f"\n{title}:")
    print(f"  Success: {response.get('success', 'N/A')}")
    
    if 'error' in response:
        error = response['error']
        print(f"  Error Type: {error.get('type', 'N/A')}")
        print(f"  User Message: {error.get('message', 'N/A')}")
        print(f"  Fallback: {error.get('fallback', 'N/A')}")
        print(f"  Suggestions: {len(error.get('suggestions', []))} provided")
        if error.get('retry_after'):
            print(f"  Retry After: {error['retry_after']} seconds")
        if error.get('support_reference'):
            print(f"  Support Reference: {error['support_reference']}")
    
    if response.get('fallback'):
        print(f"  Fallback Response: True")
        print(f"  Alternative Help: {len(response.get('alternative_help', []))} options")


async def demo_validation_errors():
    """Demonstrate validation error handling."""
    print_section("VALIDATION ERROR HANDLING")
    
    client = GatewayHTTPClient(environment=Environment.DEVELOPMENT)
    
    print("1. Empty districts list:")
    result = await client.search_restaurants_by_district([])
    print_error_response(result)
    
    print("\n2. Invalid meal types:")
    result = await client.search_restaurants_by_meal_type(["invalid_meal", "also_invalid"])
    print_error_response(result)
    
    print("\n3. Missing required fields in restaurant data:")
    invalid_restaurants = [
        {"id": "1"},  # Missing name and sentiment
        {"name": "Test"}  # Missing id and sentiment
    ]
    result = await client.recommend_restaurants(invalid_restaurants)
    print_error_response(result)
    
    print("\n4. Invalid ranking method:")
    valid_restaurants = [{
        "id": "1",
        "name": "Test Restaurant",
        "sentiment": {"likes": 10, "dislikes": 2, "neutral": 3}
    }]
    result = await client.recommend_restaurants(valid_restaurants, "invalid_method")
    print_error_response(result)


async def demo_connection_errors():
    """Demonstrate connection error handling."""
    print_section("CONNECTION ERROR HANDLING")
    
    client = GatewayHTTPClient(environment=Environment.DEVELOPMENT)
    
    print("Simulating connection failure...")
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Connection refused")
        
        result = await client.search_restaurants_by_district(["Central"])
        print_error_response(result, "Connection Error Response")


async def demo_service_errors():
    """Demonstrate service error handling."""
    print_section("SERVICE ERROR HANDLING")
    
    client = GatewayHTTPClient(environment=Environment.DEVELOPMENT)
    
    # Mock different HTTP status codes
    status_codes = [401, 429, 500, 503]
    error_messages = {
        401: "Authentication failed",
        429: "Rate limit exceeded",
        500: "Internal server error",
        503: "Service unavailable"
    }
    
    for status_code in status_codes:
        print(f"\n{status_code} Error Simulation:")
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Create mock response
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.reason_phrase = error_messages[status_code]
            mock_response.headers = {"Retry-After": "60"} if status_code == 429 else {}
            mock_response.json.return_value = {
                "error": {"message": error_messages[status_code]}
            }
            
            # Create HTTPStatusError
            from httpx import HTTPStatusError, Request
            mock_response.raise_for_status.side_effect = HTTPStatusError(
                message=f"HTTP {status_code}",
                request=Mock(spec=Request),
                response=mock_response
            )
            
            mock_client.post.return_value = mock_response
            
            result = await client.search_restaurants_by_district(["Central"])
            print_error_response(result, f"HTTP {status_code} Response")


def demo_fallback_responses():
    """Demonstrate fallback response creation."""
    print_section("FALLBACK RESPONSE CREATION")
    
    operations = [
        "search_restaurants_by_district",
        "recommend_restaurants", 
        "search_restaurants_combined",
        "unknown_operation"
    ]
    
    for operation in operations:
        print(f"\nFallback for '{operation}':")
        response = create_fallback_response(operation)
        print_error_response(response, f"Fallback Response")
        
        # Show suggestions
        if response.get('suggestions'):
            print(f"  Suggestions provided:")
            for i, suggestion in enumerate(response['suggestions'][:3], 1):
                print(f"    {i}. {suggestion}")
    
    print("\nFallback with partial data:")
    partial_data = {
        "restaurants": [
            {"name": "Partial Restaurant", "district": "Central"}
        ]
    }
    response = create_fallback_response("search_restaurants_by_district", partial_data)
    print_error_response(response, "Fallback with Partial Data")
    print(f"  Partial Data: {response.get('partial_data', {})}")


def demo_error_classification():
    """Demonstrate error classification and severity assignment."""
    print_section("ERROR CLASSIFICATION & SEVERITY")
    
    handler = ErrorHandler("demo")
    
    # Test different error types
    test_errors = [
        (ConnectionError("Network unreachable"), "Connection Error"),
        (ValueError("Invalid input format"), "Validation Error"),
        (TimeoutError("Request timed out"), "Timeout Error"),
        (Exception("Unauthorized access"), "Authentication Error"),
        (RuntimeError("Unexpected failure"), "Unexpected Error")
    ]
    
    for error, description in test_errors:
        print(f"\n{description}:")
        category = handler._classify_error(error)
        print(f"  Original Error: {type(error).__name__}: {error}")
        print(f"  Classified As: {category.value}")
        
        # Create context and handle error
        context = handler.create_error_context(
            operation="demo_operation",
            user_id="demo_user"
        )
        
        response = handler.handle_error(error, context)
        print(f"  Severity: {response.details.get('severity', 'N/A')}")
        print(f"  User Message: {response.user_message}")


def demo_logging_and_monitoring():
    """Demonstrate logging and monitoring features."""
    print_section("LOGGING & MONITORING")
    
    handler = ErrorHandler("demo")
    
    print("Performance Monitoring:")
    context = ErrorContext(
        operation="slow_operation",
        user_id="user123",
        environment="production"
    )
    
    # Simulate performance logging
    handler.log_performance_issue(
        operation="restaurant_search",
        duration=7.5,
        threshold=5.0,
        context=context
    )
    print("  ✓ Performance issue logged (7.5s > 5.0s threshold)")
    
    print("\nError Context Creation:")
    context = handler.create_error_context(
        operation="demo_operation",
        user_id="user456",
        session_id="session789",
        environment="development",
        additional_data={"request_size": 1024, "retry_count": 2}
    )
    
    print(f"  Operation: {context.operation}")
    print(f"  User ID: {context.user_id}")
    print(f"  Session ID: {context.session_id}")
    print(f"  Environment: {context.environment}")
    print(f"  Additional Data: {context.additional_data}")
    print(f"  Timestamp: {context.timestamp}")
    
    print("\nSupport Reference Generation:")
    reference = handler._generate_support_reference(context)
    print(f"  Support Reference: {reference}")


def demo_user_friendly_messages():
    """Demonstrate user-friendly message generation."""
    print_section("USER-FRIENDLY MESSAGES")
    
    # Show different error categories and their user messages
    error_scenarios = [
        (GatewayConnectionError("Network timeout"), "Connection Issue"),
        (GatewayServiceError("API error", status_code=500), "Service Issue"),
        (GatewayValidationError("Invalid format"), "Validation Issue"),
        (GatewayAuthenticationError("Token expired"), "Authentication Issue"),
        (GatewayTimeoutError("Request timeout", timeout_duration=30), "Timeout Issue"),
        (GatewayRateLimitError("Too many requests", retry_after=60), "Rate Limit Issue")
    ]
    
    for error, scenario in error_scenarios:
        print(f"\n{scenario}:")
        response = handle_gateway_error(
            error=error,
            operation="restaurant_search",
            user_id="demo_user"
        )
        
        print(f"  Technical Error: {error}")
        print(f"  User Message: {response['error']['message']}")
        print(f"  Fallback: {response['error']['fallback']}")
        print(f"  Suggestions: {response['error']['suggestions'][0] if response['error']['suggestions'] else 'None'}")


async def main():
    """Run all demonstrations."""
    print("🍽️  MBTI Travel Planner - Comprehensive Error Handling Demo")
    print("=" * 60)
    print("This demo shows how errors are handled and converted to user-friendly messages.")
    
    try:
        # Run all demonstrations
        await demo_validation_errors()
        await demo_connection_errors()
        await demo_service_errors()
        demo_fallback_responses()
        demo_error_classification()
        demo_logging_and_monitoring()
        demo_user_friendly_messages()
        
        print_section("DEMO COMPLETE")
        print("✅ All error handling scenarios demonstrated successfully!")
        print("\nKey Features Shown:")
        print("  ✓ Comprehensive error classification")
        print("  ✓ User-friendly message generation")
        print("  ✓ Fallback response creation")
        print("  ✓ Structured logging with context")
        print("  ✓ Performance monitoring")
        print("  ✓ Support reference generation")
        print("  ✓ Severity-based error handling")
        print("  ✓ Environment-aware error responses")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())