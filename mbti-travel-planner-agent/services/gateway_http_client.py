"""
Gateway HTTP Client Service for AgentCore Gateway MCP Tools

This module provides HTTP client functionality to communicate with the
agentcore-gateway-mcp-tools service deployed in Bedrock AgentCore.
It replaces the complex MCP client authentication with simple HTTP API calls.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from httpx import AsyncClient, Response, RequestError, HTTPStatusError, TimeoutException

from .error_handler import (
    ErrorHandler, ErrorContext, ErrorSeverity, ErrorCategory,
    GatewayError, GatewayConnectionError, GatewayServiceError, 
    GatewayValidationError, GatewayAuthenticationError, GatewayTimeoutError,
    GatewayRateLimitError, handle_gateway_error, create_fallback_response
)
from .logging_service import get_logging_service

# Configure logging
logger = logging.getLogger(__name__)


class Environment(Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class GatewayEndpoints:
    """Gateway endpoint configuration for different environments."""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    
    @property
    def search_district_url(self) -> str:
        return f"{self.base_url}/api/v1/restaurants/search/district"
    
    @property
    def search_meal_type_url(self) -> str:
        return f"{self.base_url}/api/v1/restaurants/search/meal-type"
    
    @property
    def search_combined_url(self) -> str:
        return f"{self.base_url}/api/v1/restaurants/search/combined"
    
    @property
    def recommend_url(self) -> str:
        return f"{self.base_url}/api/v1/restaurants/recommend"
    
    @property
    def analyze_url(self) -> str:
        return f"{self.base_url}/api/v1/restaurants/analyze"
    
    @property
    def health_url(self) -> str:
        return f"{self.base_url}/health"
    
    @property
    def metrics_url(self) -> str:
        return f"{self.base_url}/metrics"


# Error classes are now imported from error_handler module


class GatewayHTTPClient:
    """
    HTTP client for communicating with AgentCore Gateway MCP Tools.
    
    This client provides async HTTP methods for restaurant search and recommendation
    endpoints with comprehensive error handling and environment-based configuration.
    """
    
    # Default gateway endpoints for different environments
    DEFAULT_ENDPOINTS = {
        Environment.DEVELOPMENT: GatewayEndpoints(
            base_url="http://localhost:8080",
            timeout=30
        ),
        Environment.STAGING: GatewayEndpoints(
            base_url="https://agentcore-gateway-mcp-tools-staging.bedrock-agentcore.us-east-1.amazonaws.com",
            timeout=45
        ),
        Environment.PRODUCTION: GatewayEndpoints(
            base_url="https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com",
            timeout=60
        )
    }
    
    def __init__(self, 
                 environment: Union[str, Environment] = None,
                 base_url: str = None,
                 timeout: int = None,
                 auth_token: str = None):
        """
        Initialize the Gateway HTTP Client.
        
        Args:
            environment: Target environment (development, staging, production)
            base_url: Override base URL (takes precedence over environment)
            timeout: Request timeout in seconds
            auth_token: JWT authentication token (optional, can be set later)
        """
        # Initialize error handler and logging service
        self.error_handler = ErrorHandler("gateway_http_client")
        self.logging_service = get_logging_service()
        # Determine environment
        if isinstance(environment, str):
            try:
                self.environment = Environment(environment.lower())
            except ValueError:
                logger.warning(f"Invalid environment '{environment}', defaulting to production")
                self.environment = Environment.PRODUCTION
        elif isinstance(environment, Environment):
            self.environment = environment
        else:
            # Auto-detect from environment variable
            env_name = os.getenv('ENVIRONMENT', 'production').lower()
            try:
                self.environment = Environment(env_name)
            except ValueError:
                logger.warning(f"Invalid ENVIRONMENT '{env_name}', defaulting to production")
                self.environment = Environment.PRODUCTION
        
        # Configure endpoints
        if base_url:
            # Custom base URL provided
            self.endpoints = GatewayEndpoints(
                base_url=base_url,
                timeout=timeout or 30
            )
        else:
            # Use default endpoints for environment
            default_config = self.DEFAULT_ENDPOINTS[self.environment]
            self.endpoints = GatewayEndpoints(
                base_url=default_config.base_url,
                timeout=timeout or default_config.timeout
            )
        
        # Authentication
        self.auth_token = auth_token or os.getenv('GATEWAY_AUTH_TOKEN')
        
        # HTTP client configuration
        self.client_config = {
            "timeout": httpx.Timeout(self.endpoints.timeout),
            "limits": httpx.Limits(max_keepalive_connections=10, max_connections=20),
            "follow_redirects": True
        }
        
        logger.info(f"Gateway HTTP Client initialized for {self.environment.value} environment")
        logger.info(f"Base URL: {self.endpoints.base_url}")
        
        # Log configuration details for debugging
        self.error_handler.logger.info(
            f"Gateway client configured: env={self.environment.value}, "
            f"base_url={self.endpoints.base_url}, timeout={self.endpoints.timeout}"
        )
    
    def set_auth_token(self, token: str) -> None:
        """Set the JWT authentication token."""
        self.auth_token = token
        logger.debug("Authentication token updated")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers including authentication if available."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MBTI-Travel-Planner-Agent/1.0"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        return headers
    
    def _handle_response(self, response: Response) -> Dict[str, Any]:
        """
        Process HTTP response and handle errors.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed JSON response data
            
        Raises:
            GatewayServiceError: For HTTP error status codes
            GatewayValidationError: For invalid response format
        """
        try:
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise GatewayValidationError(
                    message=f"Invalid JSON response: {str(e)}",
                    details={"response_text": response.text[:500]}
                )
            
            # Validate response structure
            if not isinstance(data, dict):
                raise GatewayValidationError(
                    message="Response must be a JSON object",
                    details={"response_type": type(data).__name__}
                )
            
            # Check for API-level errors
            if not data.get("success", True):
                error_info = data.get("error", {})
                error_message = error_info.get("message", "Unknown API error")
                raise GatewayServiceError(
                    message=error_message,
                    status_code=response.status_code,
                    response_data=data,
                    details={"api_error": True, "error_info": error_info}
                )
            
            return data
            
        except HTTPStatusError as e:
            # Handle HTTP status errors with enhanced error information
            try:
                error_data = e.response.json()
                error_message = error_data.get("error", {}).get("message", str(e))
            except (json.JSONDecodeError, AttributeError):
                error_message = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
                error_data = {}
            
            # Determine specific error type based on status code
            if e.response.status_code == 401:
                raise GatewayAuthenticationError(
                    message=f"Authentication failed: {error_message}",
                    auth_type="bearer_token",
                    details={"status_code": e.response.status_code, "response_data": error_data}
                )
            elif e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                raise GatewayRateLimitError(
                    message=f"Rate limit exceeded: {error_message}",
                    retry_after=int(retry_after) if retry_after else None,
                    details={"status_code": e.response.status_code, "response_data": error_data}
                )
            else:
                raise GatewayServiceError(
                    message=error_message,
                    status_code=e.response.status_code,
                    response_data=error_data,
                    details={"http_error": True}
                )
    
    def _handle_error(self, error: Exception, operation: str, 
                     context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert exceptions to user-friendly error responses using the comprehensive error handler.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            context_data: Additional context information
            
        Returns:
            Error response dictionary
        """
        # Use the comprehensive error handler
        return handle_gateway_error(
            error=error,
            operation=operation,
            environment=self.environment.value,
            additional_data=context_data or {}
        )
    
    async def _make_request(self, 
                           method: str, 
                           url: str, 
                           data: Dict[str, Any] = None,
                           operation: str = "API request") -> Dict[str, Any]:
        """
        Make an HTTP request with error handling, performance monitoring, and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            data: Request body data
            operation: Description for error handling
            
        Returns:
            Response data dictionary
        """
        headers = self._get_headers()
        start_time = time.time()
        
        # Log HTTP request
        request_id = self.logging_service.log_http_request(
            method=method,
            url=url,
            headers=headers,
            body=data,
            environment=self.environment.value
        )
        
        # Create error context for comprehensive logging
        context = self.error_handler.create_error_context(
            operation=operation,
            environment=self.environment.value,
            request_id=request_id,
            additional_data={
                "method": method,
                "url": url,
                "has_auth": bool(self.auth_token),
                "timeout": self.endpoints.timeout
            }
        )
        
        try:
            async with AsyncClient(**self.client_config) as client:
                logger.debug(f"Making {method} request to {url} [ID: {request_id}]")
                
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    raise GatewayValidationError(
                        message=f"Unsupported HTTP method: {method}",
                        details={"supported_methods": ["GET", "POST"]}
                    )
                
                # Calculate timing and response metrics
                duration = time.time() - start_time
                duration_ms = duration * 1000
                response_size = len(response.content) if response.content else 0
                
                # Log HTTP response
                self.logging_service.log_http_response(
                    request_id=request_id,
                    status_code=response.status_code,
                    response_size=response_size,
                    duration_ms=duration_ms
                )
                
                # Log performance metrics
                self.logging_service.log_performance_metric(
                    operation=operation,
                    duration=duration,
                    success=200 <= response.status_code < 400,
                    additional_data={
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "response_size": response_size,
                        "request_id": request_id
                    }
                )
                
                # Log successful request
                logger.info(f"Request completed: {method} {url} - {response.status_code} ({duration:.2f}s) [ID: {request_id}]")
                
                return self._handle_response(response)
                
        except (RequestError, TimeoutException) as e:
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Log failed HTTP response
            self.logging_service.log_http_response(
                request_id=request_id,
                status_code=0,  # No HTTP status for connection errors
                response_size=0,
                duration_ms=duration_ms,
                error_message=str(e)
            )
            
            # Log error with full context
            self.logging_service.log_error(
                error=e,
                operation=operation,
                context={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "duration": duration,
                    "timeout": self.endpoints.timeout
                }
            )
            
            logger.error(f"Network error in {operation} after {duration:.2f}s: {e} [ID: {request_id}]")
            raise GatewayConnectionError(
                message=f"Failed to connect to gateway service: {str(e)}",
                details={
                    "url": url,
                    "duration": duration,
                    "timeout": self.endpoints.timeout,
                    "error_type": type(e).__name__,
                    "request_id": request_id
                }
            )
        except TimeoutException as e:
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Log timeout HTTP response
            self.logging_service.log_http_response(
                request_id=request_id,
                status_code=408,  # Request Timeout
                response_size=0,
                duration_ms=duration_ms,
                error_message=f"Request timed out after {duration:.2f}s"
            )
            
            # Log error with full context
            self.logging_service.log_error(
                error=e,
                operation=operation,
                context={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "duration": duration,
                    "configured_timeout": self.endpoints.timeout
                }
            )
            
            logger.error(f"Timeout in {operation} after {duration:.2f}s: {e} [ID: {request_id}]")
            raise GatewayTimeoutError(
                message=f"Request timed out after {duration:.2f} seconds",
                timeout_duration=self.endpoints.timeout,
                details={
                    "url": url,
                    "duration": duration,
                    "configured_timeout": self.endpoints.timeout,
                    "request_id": request_id
                }
            )
        except (GatewayError, GatewayServiceError, GatewayValidationError, 
                GatewayAuthenticationError, GatewayRateLimitError, GatewayTimeoutError) as e:
            # Re-raise gateway-specific errors (they're already properly formatted)
            # But still log them for monitoring
            duration = time.time() - start_time
            self.logging_service.log_performance_metric(
                operation=operation,
                duration=duration,
                success=False,
                error_type=type(e).__name__,
                additional_data={"request_id": request_id}
            )
            raise
        except Exception as e:
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            # Log unexpected error HTTP response
            self.logging_service.log_http_response(
                request_id=request_id,
                status_code=500,  # Internal Server Error
                response_size=0,
                duration_ms=duration_ms,
                error_message=f"Unexpected error: {str(e)}"
            )
            
            # Log error with full context and stack trace
            self.logging_service.log_error(
                error=e,
                operation=operation,
                context={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "duration": duration,
                    "error_type": type(e).__name__
                },
                include_stack_trace=True
            )
            
            logger.error(f"Unexpected error in {operation} after {duration:.2f}s: {e} [ID: {request_id}]", exc_info=True)
            raise GatewayError(
                message=f"Unexpected error: {str(e)}",
                category=ErrorCategory.UNEXPECTED,
                severity=ErrorSeverity.HIGH,
                details={
                    "url": url,
                    "duration": duration,
                    "error_type": type(e).__name__,
                    "request_id": request_id
                }
            )
    
    async def search_restaurants_by_district(self, districts: List[str]) -> Dict[str, Any]:
        """
        Search for restaurants in specific districts.
        
        Args:
            districts: List of district names to search
            
        Returns:
            Restaurant search results with metadata
        """
        operation = "search_restaurants_by_district"
        
        try:
            # Validate input
            if not districts or not isinstance(districts, list):
                raise GatewayValidationError(
                    message="Districts must be a non-empty list",
                    field_errors={"districts": "Required field, must be a list"},
                    details={"provided_type": type(districts).__name__}
                )
            
            if not all(isinstance(d, str) and d.strip() for d in districts):
                invalid_districts = [d for d in districts if not isinstance(d, str) or not d.strip()]
                raise GatewayValidationError(
                    message="All districts must be non-empty strings",
                    field_errors={"districts": "All items must be non-empty strings"},
                    details={"invalid_districts": invalid_districts}
                )
            
            # Make request
            request_data = {"districts": districts}
            result = await self._make_request(
                method="POST",
                url=self.endpoints.search_district_url,
                data=request_data,
                operation=operation
            )
            
            logger.info(f"Successfully searched restaurants in {len(districts)} districts")
            return result
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._handle_error(e, operation, {"districts": districts})
    
    async def search_restaurants_by_meal_type(self, meal_types: List[str]) -> Dict[str, Any]:
        """
        Search for restaurants by meal type based on operating hours.
        
        Args:
            meal_types: List of meal types (breakfast, lunch, dinner)
            
        Returns:
            Restaurant search results filtered by meal availability
        """
        operation = "search_restaurants_by_meal_type"
        
        try:
            # Validate input
            if not meal_types or not isinstance(meal_types, list):
                raise GatewayValidationError(
                    message="Meal types must be a non-empty list",
                    field_errors={"meal_types": "Required field, must be a list"},
                    details={"provided_type": type(meal_types).__name__}
                )
            
            valid_meal_types = {"breakfast", "lunch", "dinner"}
            invalid_types = [mt for mt in meal_types if mt not in valid_meal_types]
            if invalid_types:
                raise GatewayValidationError(
                    message=f"Invalid meal types: {invalid_types}. Valid types are: {list(valid_meal_types)}",
                    field_errors={"meal_types": f"Invalid values: {invalid_types}"},
                    details={
                        "invalid_types": invalid_types,
                        "valid_types": list(valid_meal_types)
                    }
                )
            
            # Make request
            request_data = {"meal_types": meal_types}
            result = await self._make_request(
                method="POST",
                url=self.endpoints.search_meal_type_url,
                data=request_data,
                operation=operation
            )
            
            logger.info(f"Successfully searched restaurants for {len(meal_types)} meal types")
            return result
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._handle_error(e, operation, {"meal_types": meal_types})
    
    async def search_restaurants_combined(self, 
                                        districts: Optional[List[str]] = None,
                                        meal_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for restaurants using combined district and meal type filters.
        
        Args:
            districts: Optional list of district names
            meal_types: Optional list of meal types
            
        Returns:
            Restaurant search results matching specified criteria
        """
        operation = "search_restaurants_combined"
        
        try:
            # Validate that at least one filter is provided
            if not districts and not meal_types:
                raise GatewayValidationError(
                    message="At least one of districts or meal_types must be provided",
                    field_errors={
                        "districts": "Required when meal_types not provided",
                        "meal_types": "Required when districts not provided"
                    },
                    details={"provided_districts": bool(districts), "provided_meal_types": bool(meal_types)}
                )
            
            # Validate districts if provided
            if districts is not None:
                if not isinstance(districts, list) or not districts:
                    raise GatewayValidationError(
                        message="Districts must be a non-empty list when provided",
                        field_errors={"districts": "Must be a non-empty list"},
                        details={"provided_type": type(districts).__name__, "is_empty": not districts}
                    )
                if not all(isinstance(d, str) and d.strip() for d in districts):
                    invalid_districts = [d for d in districts if not isinstance(d, str) or not d.strip()]
                    raise GatewayValidationError(
                        message="All districts must be non-empty strings",
                        field_errors={"districts": "All items must be non-empty strings"},
                        details={"invalid_districts": invalid_districts}
                    )
            
            # Validate meal types if provided
            if meal_types is not None:
                if not isinstance(meal_types, list) or not meal_types:
                    raise GatewayValidationError(
                        message="Meal types must be a non-empty list when provided",
                        field_errors={"meal_types": "Must be a non-empty list"},
                        details={"provided_type": type(meal_types).__name__, "is_empty": not meal_types}
                    )
                
                valid_meal_types = {"breakfast", "lunch", "dinner"}
                invalid_types = [mt for mt in meal_types if mt not in valid_meal_types]
                if invalid_types:
                    raise GatewayValidationError(
                        message=f"Invalid meal types: {invalid_types}. Valid types are: {list(valid_meal_types)}",
                        field_errors={"meal_types": f"Invalid values: {invalid_types}"},
                        details={
                            "invalid_types": invalid_types,
                            "valid_types": list(valid_meal_types)
                        }
                    )
            
            # Build request data
            request_data = {}
            if districts:
                request_data["districts"] = districts
            if meal_types:
                request_data["meal_types"] = meal_types
            
            # Make request
            result = await self._make_request(
                method="POST",
                url=self.endpoints.search_combined_url,
                data=request_data,
                operation=operation
            )
            
            logger.info(f"Successfully performed combined search with {len(request_data)} filters")
            return result
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._handle_error(e, operation, {
                "districts": districts,
                "meal_types": meal_types,
                "request_data": request_data if 'request_data' in locals() else None
            })
    
    async def recommend_restaurants(self, 
                                  restaurants: List[Dict[str, Any]], 
                                  ranking_method: str = "sentiment_likes") -> Dict[str, Any]:
        """
        Get intelligent restaurant recommendations with sentiment-based ranking.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            
        Returns:
            Restaurant recommendations with analysis
        """
        operation = "recommend_restaurants"
        
        try:
            # Validate input
            if not restaurants or not isinstance(restaurants, list):
                raise GatewayValidationError(
                    message="Restaurants must be a non-empty list",
                    field_errors={"restaurants": "Required field, must be a non-empty list"},
                    details={
                        "provided_type": type(restaurants).__name__,
                        "is_empty": not restaurants if isinstance(restaurants, list) else None
                    }
                )
            
            valid_ranking_methods = {"sentiment_likes", "combined_sentiment"}
            if ranking_method not in valid_ranking_methods:
                raise GatewayValidationError(
                    message=f"Invalid ranking method: {ranking_method}. Valid methods are: {list(valid_ranking_methods)}",
                    field_errors={"ranking_method": f"Invalid value: {ranking_method}"},
                    details={
                        "provided_method": ranking_method,
                        "valid_methods": list(valid_ranking_methods)
                    }
                )
            
            # Validate restaurant data structure
            for i, restaurant in enumerate(restaurants):
                if not isinstance(restaurant, dict):
                    raise GatewayValidationError(
                        message=f"Restaurant {i} must be a dictionary",
                        field_errors={f"restaurants[{i}]": "Must be a dictionary"},
                        details={"restaurant_index": i, "provided_type": type(restaurant).__name__}
                    )
                
                # Check for required fields
                required_fields = ["id", "name", "sentiment"]
                missing_fields = [field for field in required_fields if field not in restaurant]
                if missing_fields:
                    raise GatewayValidationError(
                        message=f"Restaurant {i} missing required fields: {missing_fields}",
                        field_errors={f"restaurants[{i}]": f"Missing fields: {missing_fields}"},
                        details={
                            "restaurant_index": i,
                            "missing_fields": missing_fields,
                            "required_fields": required_fields,
                            "provided_fields": list(restaurant.keys())
                        }
                    )
                
                # Validate sentiment data
                sentiment = restaurant.get("sentiment", {})
                if not isinstance(sentiment, dict):
                    raise GatewayValidationError(
                        message=f"Restaurant {i} sentiment must be a dictionary",
                        field_errors={f"restaurants[{i}].sentiment": "Must be a dictionary"},
                        details={
                            "restaurant_index": i,
                            "sentiment_type": type(sentiment).__name__
                        }
                    )
                
                sentiment_fields = ["likes", "dislikes", "neutral"]
                missing_sentiment = [field for field in sentiment_fields if field not in sentiment]
                if missing_sentiment:
                    raise GatewayValidationError(
                        message=f"Restaurant {i} sentiment missing fields: {missing_sentiment}",
                        field_errors={f"restaurants[{i}].sentiment": f"Missing fields: {missing_sentiment}"},
                        details={
                            "restaurant_index": i,
                            "missing_sentiment_fields": missing_sentiment,
                            "required_sentiment_fields": sentiment_fields,
                            "provided_sentiment_fields": list(sentiment.keys())
                        }
                    )
            
            # Make request
            request_data = {
                "restaurants": restaurants,
                "ranking_method": ranking_method
            }
            result = await self._make_request(
                method="POST",
                url=self.endpoints.recommend_url,
                data=request_data,
                operation=operation
            )
            
            logger.info(f"Successfully generated recommendations for {len(restaurants)} restaurants")
            return result
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._handle_error(e, operation, {
                "restaurant_count": len(restaurants) if restaurants else 0,
                "ranking_method": ranking_method
            })
    
    async def analyze_restaurant_sentiment(self, restaurants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment patterns in restaurant data.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            
        Returns:
            Sentiment analysis results
        """
        operation = "analyze_restaurant_sentiment"
        
        try:
            # Validate input (similar to recommend_restaurants)
            if not restaurants or not isinstance(restaurants, list):
                raise GatewayValidationError(
                    message="Restaurants must be a non-empty list",
                    field_errors={"restaurants": "Required field, must be a non-empty list"},
                    details={
                        "provided_type": type(restaurants).__name__,
                        "is_empty": not restaurants if isinstance(restaurants, list) else None
                    }
                )
            
            # Validate restaurant data structure
            for i, restaurant in enumerate(restaurants):
                if not isinstance(restaurant, dict):
                    raise GatewayValidationError(
                        message=f"Restaurant {i} must be a dictionary",
                        field_errors={f"restaurants[{i}]": "Must be a dictionary"},
                        details={"restaurant_index": i, "provided_type": type(restaurant).__name__}
                    )
                
                # Check for required fields
                required_fields = ["id", "name", "sentiment"]
                missing_fields = [field for field in required_fields if field not in restaurant]
                if missing_fields:
                    raise GatewayValidationError(
                        message=f"Restaurant {i} missing required fields: {missing_fields}",
                        field_errors={f"restaurants[{i}]": f"Missing fields: {missing_fields}"},
                        details={
                            "restaurant_index": i,
                            "missing_fields": missing_fields,
                            "required_fields": required_fields
                        }
                    )
                
                # Validate sentiment data
                sentiment = restaurant.get("sentiment", {})
                if not isinstance(sentiment, dict):
                    raise GatewayValidationError(
                        message=f"Restaurant {i} sentiment must be a dictionary",
                        field_errors={f"restaurants[{i}].sentiment": "Must be a dictionary"},
                        details={
                            "restaurant_index": i,
                            "sentiment_type": type(sentiment).__name__
                        }
                    )
            
            # Make request
            request_data = {"restaurants": restaurants}
            result = await self._make_request(
                method="POST",
                url=self.endpoints.analyze_url,
                data=request_data,
                operation=operation
            )
            
            logger.info(f"Successfully analyzed sentiment for {len(restaurants)} restaurants")
            return result
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._handle_error(e, operation, {
                "restaurant_count": len(restaurants) if restaurants else 0
            })
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the gateway service.
        
        Returns:
            Health status information
        """
        operation = "health_check"
        
        try:
            result = await self._make_request(
                method="GET",
                url=self.endpoints.health_url,
                operation=operation
            )
            
            logger.debug("Gateway health check completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._handle_error(e, operation, {"health_check": True})
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get gateway service metrics.
        
        Returns:
            Service metrics and performance data
        """
        operation = "get_metrics"
        
        try:
            result = await self._make_request(
                method="GET",
                url=self.endpoints.metrics_url,
                operation=operation
            )
            
            logger.debug("Gateway metrics retrieved successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._handle_error(e, operation, {"metrics_request": True})


# Convenience functions for synchronous usage
def create_gateway_client(environment: str = None, 
                         base_url: str = None,
                         auth_token: str = None) -> GatewayHTTPClient:
    """
    Create a configured Gateway HTTP Client.
    
    Args:
        environment: Target environment (development, staging, production)
        base_url: Override base URL
        auth_token: JWT authentication token
        
    Returns:
        Configured GatewayHTTPClient instance
    """
    return GatewayHTTPClient(
        environment=environment,
        base_url=base_url,
        auth_token=auth_token
    )


def get_environment_config(environment: str = None) -> GatewayEndpoints:
    """
    Get endpoint configuration for a specific environment.
    
    Args:
        environment: Target environment name
        
    Returns:
        GatewayEndpoints configuration
    """
    if environment:
        try:
            env = Environment(environment.lower())
        except ValueError:
            logger.warning(f"Invalid environment '{environment}', using production")
            env = Environment.PRODUCTION
    else:
        env_name = os.getenv('ENVIRONMENT', 'production').lower()
        try:
            env = Environment(env_name)
        except ValueError:
            logger.warning(f"Invalid ENVIRONMENT '{env_name}', using production")
            env = Environment.PRODUCTION
    
    return GatewayHTTPClient.DEFAULT_ENDPOINTS[env]


# Export main classes and functions
__all__ = [
    'GatewayHTTPClient',
    'GatewayEndpoints', 
    'Environment',
    'GatewayError',
    'GatewayConnectionError',
    'GatewayServiceError',
    'GatewayValidationError',
    'GatewayAuthenticationError',
    'GatewayTimeoutError',
    'GatewayRateLimitError',
    'GatewayConfigurationError',
    'create_gateway_client',
    'get_environment_config'
]