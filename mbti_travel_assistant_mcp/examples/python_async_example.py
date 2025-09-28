#!/usr/bin/env python3
"""
Python Async Example for MBTI Travel Assistant MCP

This example demonstrates how to use the MBTI Travel Assistant API
with Python's asyncio for concurrent requests and proper error handling.
"""

import asyncio
import aiohttp
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RestaurantRequest:
    """Request model for restaurant recommendations."""
    district: Optional[str] = None
    meal_time: Optional[str] = None
    natural_language_query: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class APIResponse:
    """Response model for API calls."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None

class MBTITravelAssistantAsyncClient:
    """Async client for MBTI Travel Assistant API."""
    
    def __init__(self, base_url: str, auth_token_provider, timeout: int = 10):
        self.base_url = base_url
        self.auth_token_provider = auth_token_provider
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'MBTITravelApp-Python-Async/1.0.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        try:
            token = await self.auth_token_provider()
            return {'Authorization': f'Bearer {token}'}
        except Exception as e:
            logger.error(f"Failed to get auth token: {e}")
            return {}
    
    async def get_restaurant_recommendation(
        self, 
        request: RestaurantRequest
    ) -> APIResponse:
        """Get restaurant recommendation from API."""
        start_time = time.time()
        
        try:
            headers = await self._get_auth_headers()
            payload = request.to_dict()
            
            logger.info(f"Making API request: {payload}")
            
            async with self.session.post(
                f'{self.base_url}/invocations',
                headers=headers,
                json=payload
            ) as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"API request successful ({response_time_ms}ms)")
                    return APIResponse(
                        success=True,
                        data=data,
                        response_time_ms=response_time_ms
                    )
                else:
                    error_data = await response.json()
                    logger.error(f"API request failed: {response.status} - {error_data}")
                    return APIResponse(
                        success=False,
                        error=error_data.get('error', {'message': f'HTTP {response.status}'}),
                        response_time_ms=response_time_ms
                    )
                    
        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"API request timeout after {response_time_ms}ms")
            return APIResponse(
                success=False,
                error={
                    'error_type': 'timeout_error',
                    'message': 'Request timed out',
                    'error_code': 'TIMEOUT'
                },
                response_time_ms=response_time_ms
            )
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"API request error: {e}")
            return APIResponse(
                success=False,
                error={
                    'error_type': 'client_error',
                    'message': str(e),
                    'error_code': 'CLIENT_ERROR'
                },
                response_time_ms=response_time_ms
            )
    
    async def get_health_status(self) -> APIResponse:
        """Get health status of the service."""
        start_time = time.time()
        
        try:
            async with self.session.get(f'{self.base_url}/health') as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    data = await response.json()
                    return APIResponse(
                        success=True,
                        data=data,
                        response_time_ms=response_time_ms
                    )
                else:
                    return APIResponse(
                        success=False,
                        error={'message': f'Health check failed: HTTP {response.status}'},
                        response_time_ms=response_time_ms
                    )
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return APIResponse(
                success=False,
                error={'message': f'Health check error: {str(e)}'},
                response_time_ms=response_time_ms
            )

class RetryableAsyncClient(MBTITravelAssistantAsyncClient):
    """Client with retry logic for handling transient failures."""
    
    def __init__(self, base_url: str, auth_token_provider, timeout: int = 10, max_retries: int = 3):
        super().__init__(base_url, auth_token_provider, timeout)
        self.max_retries = max_retries
    
    async def get_restaurant_recommendation_with_retry(
        self, 
        request: RestaurantRequest
    ) -> APIResponse:
        """Get restaurant recommendation with retry logic."""
        last_response = None
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Attempt {attempt}/{self.max_retries}")
            
            response = await self.get_restaurant_recommendation(request)
            
            if response.success:
                return response
            
            last_response = response
            
            # Don't retry on client errors (4xx) except rate limiting
            if response.error and response.error.get('error_code') in ['VALIDATION_FAILED', 'AUTH_FAILED']:
                logger.info("Not retrying client error")
                break
            
            if attempt < self.max_retries:
                # Exponential backoff with jitter
                delay = min(2 ** (attempt - 1) + (time.time() % 1), 10)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
        
        logger.error(f"All {self.max_retries} attempts failed")
        return last_response

async def mock_auth_token_provider() -> str:
    """Mock authentication token provider."""
    # In a real application, this would:
    # 1. Check if current token is valid
    # 2. Refresh token if needed
    # 3. Return valid JWT token
    import os
    return os.getenv('JWT_TOKEN', 'mock-jwt-token')

async def demonstrate_basic_usage():
    """Demonstrate basic API usage."""
    print("🚀 Basic Usage Example\n")
    
    async with MBTITravelAssistantAsyncClient(
        base_url='https://your-endpoint.amazonaws.com',
        auth_token_provider=mock_auth_token_provider
    ) as client:
        
        # Example 1: Health check
        print("1. Checking service health...")
        health_response = await client.get_health_status()
        
        if health_response.success:
            print(f"✓ Service is healthy ({health_response.response_time_ms}ms)")
            print(f"  Status: {health_response.data.get('status')}")
            print(f"  Environment: {health_response.data.get('environment')}")
        else:
            print(f"❌ Health check failed: {health_response.error.get('message')}")
        print()
        
        # Example 2: District and meal time search
        print("2. Getting breakfast recommendations in Central district...")
        request = RestaurantRequest(
            district='Central district',
            meal_time='breakfast'
        )
        
        response = await client.get_restaurant_recommendation(request)
        
        if response.success:
            data = response.data
            print(f"✓ Request successful ({response.response_time_ms}ms)")
            
            if data.get('recommendation'):
                rec = data['recommendation']
                print(f"  Recommended: {rec['name']}")
                print(f"  Address: {rec['address']}")
                print(f"  Sentiment: {rec['sentiment']['positive_percentage']:.1f}% positive")
            
            print(f"  Found {len(data.get('candidates', []))} alternatives")
            print(f"  Cache hit: {data.get('metadata', {}).get('cache_hit', False)}")
        else:
            print(f"❌ Request failed: {response.error.get('message')}")
        print()
        
        # Example 3: Natural language query
        print("3. Natural language search...")
        nl_request = RestaurantRequest(
            natural_language_query="Find me a good Italian restaurant for dinner in Causeway Bay"
        )
        
        nl_response = await client.get_restaurant_recommendation(nl_request)
        
        if nl_response.success:
            data = nl_response.data
            print(f"✓ Natural language search successful ({nl_response.response_time_ms}ms)")
            
            if data.get('recommendation'):
                rec = data['recommendation']
                print(f"  Recommended: {rec['name']}")
                print(f"  District: {rec['district']}")
                cuisine = rec.get('metadata', {}).get('cuisine_type', 'Not specified')
                print(f"  Cuisine: {cuisine}")
        else:
            print(f"❌ Natural language search failed: {nl_response.error.get('message')}")

async def demonstrate_concurrent_requests():
    """Demonstrate concurrent API requests."""
    print("🔄 Concurrent Requests Example\n")
    
    # Define multiple search requests
    requests = [
        RestaurantRequest(district='Central district', meal_time='breakfast'),
        RestaurantRequest(district='Admiralty', meal_time='lunch'),
        RestaurantRequest(district='Causeway Bay', meal_time='dinner'),
        RestaurantRequest(natural_language_query='Find me sushi in Tsim Sha Tsui'),
        RestaurantRequest(natural_language_query='Good dim sum restaurant in Wan Chai')
    ]
    
    async with MBTITravelAssistantAsyncClient(
        base_url='https://your-endpoint.amazonaws.com',
        auth_token_provider=mock_auth_token_provider
    ) as client:
        
        start_time = time.time()
        
        # Execute all requests concurrently
        tasks = [
            client.get_restaurant_recommendation(request) 
            for request in requests
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        print(f"Completed {len(requests)} requests in {total_time:.2f} seconds")
        print()
        
        # Process results
        successful_requests = 0
        total_response_time = 0
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"Request {i+1}: ❌ Exception - {response}")
            elif response.success:
                successful_requests += 1
                total_response_time += response.response_time_ms
                
                rec_name = response.data.get('recommendation', {}).get('name', 'None')
                candidates_count = len(response.data.get('candidates', []))
                
                print(f"Request {i+1}: ✓ Success ({response.response_time_ms}ms)")
                print(f"  Recommended: {rec_name}")
                print(f"  Alternatives: {candidates_count}")
            else:
                error_msg = response.error.get('message', 'Unknown error')
                print(f"Request {i+1}: ❌ Failed - {error_msg}")
        
        if successful_requests > 0:
            avg_response_time = total_response_time / successful_requests
            print(f"\nSummary:")
            print(f"  Successful requests: {successful_requests}/{len(requests)}")
            print(f"  Average response time: {avg_response_time:.0f}ms")
            print(f"  Success rate: {successful_requests/len(requests)*100:.1f}%")

async def demonstrate_retry_logic():
    """Demonstrate retry logic for handling failures."""
    print("🔄 Retry Logic Example\n")
    
    async with RetryableAsyncClient(
        base_url='https://your-endpoint.amazonaws.com',
        auth_token_provider=mock_auth_token_provider,
        max_retries=3
    ) as client:
        
        # Test with a request that might fail
        request = RestaurantRequest(
            district='Central district',
            meal_time='breakfast'
        )
        
        print("Making request with retry logic...")
        response = await client.get_restaurant_recommendation_with_retry(request)
        
        if response.success:
            print(f"✓ Request successful after retries ({response.response_time_ms}ms)")
            rec_name = response.data.get('recommendation', {}).get('name', 'None')
            print(f"  Recommended: {rec_name}")
        else:
            print(f"❌ Request failed after all retries")
            print(f"  Error: {response.error.get('message')}")
            print(f"  Error type: {response.error.get('error_type')}")

async def demonstrate_error_handling():
    """Demonstrate comprehensive error handling."""
    print("⚠️ Error Handling Examples\n")
    
    async with MBTITravelAssistantAsyncClient(
        base_url='https://your-endpoint.amazonaws.com',
        auth_token_provider=mock_auth_token_provider
    ) as client:
        
        # Test cases for different error scenarios
        test_cases = [
            {
                'name': 'Validation Error',
                'request': RestaurantRequest(meal_time='invalid_meal'),
                'expected_error': 'validation_error'
            },
            {
                'name': 'Empty Request',
                'request': RestaurantRequest(),
                'expected_error': 'validation_error'
            },
            {
                'name': 'Valid Request',
                'request': RestaurantRequest(district='Central district', meal_time='breakfast'),
                'expected_error': None
            }
        ]
        
        for test_case in test_cases:
            print(f"Testing: {test_case['name']}")
            
            response = await client.get_restaurant_recommendation(test_case['request'])
            
            if response.success:
                print(f"  ✓ Success - Got recommendation")
            else:
                error = response.error
                print(f"  ❌ Error: {error.get('message')}")
                print(f"     Type: {error.get('error_type')}")
                print(f"     Code: {error.get('error_code')}")
                
                if error.get('suggested_actions'):
                    print("     Suggested actions:")
                    for action in error['suggested_actions']:
                        print(f"       - {action}")
            
            print()

async def performance_benchmark():
    """Run performance benchmark."""
    print("📊 Performance Benchmark\n")
    
    async with MBTITravelAssistantAsyncClient(
        base_url='https://your-endpoint.amazonaws.com',
        auth_token_provider=mock_auth_token_provider
    ) as client:
        
        # Benchmark parameters
        num_requests = 10
        concurrent_requests = 5
        
        print(f"Running {num_requests} requests with {concurrent_requests} concurrent connections...")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request(request_id: int) -> Dict[str, Any]:
            async with semaphore:
                request = RestaurantRequest(
                    district='Central district',
                    meal_time=['breakfast', 'lunch', 'dinner'][request_id % 3]
                )
                
                start_time = time.time()
                response = await client.get_restaurant_recommendation(request)
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'success': response.success,
                    'response_time_ms': int((end_time - start_time) * 1000),
                    'api_response_time_ms': response.response_time_ms
                }
        
        # Execute benchmark
        start_time = time.time()
        tasks = [make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time_ms'] for r in successful_requests]
            api_response_times = [r['api_response_time_ms'] for r in successful_requests if r['api_response_time_ms']]
            
            print(f"Results:")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Successful requests: {len(successful_requests)}/{num_requests}")
            print(f"  Failed requests: {len(failed_requests)}")
            print(f"  Success rate: {len(successful_requests)/num_requests*100:.1f}%")
            print(f"  Requests per second: {num_requests/total_time:.1f}")
            print()
            print(f"Response times (client-side):")
            print(f"  Min: {min(response_times)}ms")
            print(f"  Max: {max(response_times)}ms")
            print(f"  Average: {sum(response_times)/len(response_times):.0f}ms")
            
            if api_response_times:
                print(f"API response times (server-side):")
                print(f"  Min: {min(api_response_times)}ms")
                print(f"  Max: {max(api_response_times)}ms")
                print(f"  Average: {sum(api_response_times)/len(api_response_times):.0f}ms")

async def main():
    """Main function to run all examples."""
    print("🍽️ MBTI Travel Assistant - Python Async Examples")
    print("=" * 60)
    print()
    
    examples = [
        ("Basic Usage", demonstrate_basic_usage),
        ("Concurrent Requests", demonstrate_concurrent_requests),
        ("Retry Logic", demonstrate_retry_logic),
        ("Error Handling", demonstrate_error_handling),
        ("Performance Benchmark", performance_benchmark)
    ]
    
    for name, example_func in examples:
        try:
            print(f"Running: {name}")
            print("-" * 40)
            await example_func()
            print()
        except Exception as e:
            print(f"❌ Example '{name}' failed: {e}")
            logger.exception(f"Example '{name}' failed")
            print()

if __name__ == "__main__":
    # Set up environment
    import os
    
    # You can set these environment variables:
    # export API_BASE_URL="https://your-endpoint.amazonaws.com"
    # export JWT_TOKEN="your-jwt-token"
    
    if not os.getenv('API_BASE_URL'):
        print("⚠️ API_BASE_URL environment variable not set, using placeholder")
    
    if not os.getenv('JWT_TOKEN'):
        print("⚠️ JWT_TOKEN environment variable not set, using mock token")
    
    print()
    
    # Run examples
    asyncio.run(main())