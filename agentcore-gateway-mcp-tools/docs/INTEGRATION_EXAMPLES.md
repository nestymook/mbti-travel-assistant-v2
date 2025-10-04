# AgentCore Gateway MCP Tools - Integration Examples

## Overview

This document provides comprehensive integration examples for client applications using the AgentCore Gateway MCP Tools API. Examples cover various programming languages, frameworks, and integration patterns.

## Table of Contents

1. [Authentication Setup](#authentication-setup)
2. [Python Integration](#python-integration)
3. [JavaScript/TypeScript Integration](#javascripttypescript-integration)
4. [React Application Integration](#react-application-integration)
5. [Node.js Backend Integration](#nodejs-backend-integration)
6. [Mobile Application Integration](#mobile-application-integration)
7. [Foundation Model Integration](#foundation-model-integration)
8. [Error Handling Patterns](#error-handling-patterns)
9. [Performance Optimization](#performance-optimization)
10. [Testing Strategies](#testing-strategies)

## Authentication Setup

### AWS Cognito Configuration

First, configure AWS Cognito for JWT token generation:

```javascript
// AWS Amplify configuration
import { Amplify, Auth } from 'aws-amplify';

Amplify.configure({
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_KePRX24Bn',
    userPoolWebClientId: '1ofgeckef3po4i3us4j1m4chvd',
    oauth: {
      domain: 'your-cognito-domain.auth.us-east-1.amazoncognito.com',
      scope: ['openid', 'profile', 'email'],
      redirectSignIn: 'https://your-app.com/callback',
      redirectSignOut: 'https://your-app.com/logout',
      responseType: 'code'
    }
  }
});

// Get JWT token
async function getJWTToken() {
  try {
    const session = await Auth.currentSession();
    return session.getIdToken().getJwtToken();
  } catch (error) {
    console.error('Failed to get JWT token:', error);
    throw error;
  }
}
```

### Manual JWT Token Handling

```python
# Python JWT token validation
import jwt
import requests
from typing import Dict, Any

class CognitoJWTValidator:
    def __init__(self, user_pool_id: str, client_id: str, region: str):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    
    def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS from Cognito."""
        response = requests.get(self.jwks_url)
        response.raise_for_status()
        return response.json()
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token against Cognito."""
        jwks = self.get_jwks()
        
        # Decode and validate token
        decoded_token = jwt.decode(
            token,
            jwks,
            algorithms=['RS256'],
            audience=self.client_id,
            issuer=self.issuer
        )
        
        return decoded_token

# Usage
validator = CognitoJWTValidator(
    user_pool_id='us-east-1_KePRX24Bn',
    client_id='1ofgeckef3po4i3us4j1m4chvd',
    region='us-east-1'
)

token_data = validator.validate_token(jwt_token)
```

## Python Integration

### Complete Python Client Library

```python
import requests
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class RankingMethod(Enum):
    SENTIMENT_LIKES = "sentiment_likes"
    COMBINED_SENTIMENT = "combined_sentiment"

class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"

@dataclass
class Restaurant:
    id: str
    name: str
    district: Optional[str] = None
    sentiment: Optional[Dict[str, int]] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    operating_hours: Optional[Dict[str, str]] = None

@dataclass
class SearchResponse:
    restaurants: List[Restaurant]
    total_count: int
    metadata: Dict[str, Any]

@dataclass
class RecommendationResponse:
    recommendation: Restaurant
    candidates: List[Restaurant]
    analysis_summary: Dict[str, Any]

class AgentCoreGatewayClient:
    """Complete Python client for AgentCore Gateway MCP Tools."""
    
    def __init__(self, base_url: str, jwt_token: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'AgentCoreGatewayClient/1.0.0'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired JWT token")
            elif response.status_code == 400:
                error_data = response.json().get('error', {})
                raise ValidationError(f"Validation error: {error_data.get('message', str(e))}")
            elif response.status_code == 503:
                raise ServiceUnavailableError("MCP server temporarily unavailable")
            else:
                raise APIError(f"HTTP {response.status_code}: {str(e)}")
        
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timeout after {self.timeout} seconds")
        
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def search_by_district(self, districts: List[str]) -> SearchResponse:
        """Search restaurants by district."""
        data = {'districts': districts}
        response = self._make_request('POST', '/api/v1/restaurants/search/district', data)
        
        restaurants = [
            Restaurant(**restaurant_data) 
            for restaurant_data in response['data']['restaurants']
        ]
        
        return SearchResponse(
            restaurants=restaurants,
            total_count=response['data']['total_count'],
            metadata=response['metadata']
        )
    
    def search_by_meal_type(self, meal_types: List[MealType]) -> SearchResponse:
        """Search restaurants by meal type."""
        meal_type_values = [meal_type.value for meal_type in meal_types]
        data = {'meal_types': meal_type_values}
        response = self._make_request('POST', '/api/v1/restaurants/search/meal-type', data)
        
        restaurants = [
            Restaurant(**restaurant_data) 
            for restaurant_data in response['data']['restaurants']
        ]
        
        return SearchResponse(
            restaurants=restaurants,
            total_count=response['data']['total_count'],
            metadata=response['metadata']
        )
    
    def search_combined(self, districts: Optional[List[str]] = None, 
                       meal_types: Optional[List[MealType]] = None) -> SearchResponse:
        """Search restaurants with combined filters."""
        data = {}
        if districts:
            data['districts'] = districts
        if meal_types:
            data['meal_types'] = [meal_type.value for meal_type in meal_types]
        
        response = self._make_request('POST', '/api/v1/restaurants/search/combined', data)
        
        restaurants = [
            Restaurant(**restaurant_data) 
            for restaurant_data in response['data']['restaurants']
        ]
        
        return SearchResponse(
            restaurants=restaurants,
            total_count=response['data']['total_count'],
            metadata=response['metadata']
        )
    
    def get_recommendations(self, restaurants: List[Restaurant], 
                          ranking_method: RankingMethod = RankingMethod.SENTIMENT_LIKES) -> RecommendationResponse:
        """Get restaurant recommendations."""
        restaurant_data = [
            {
                'id': r.id,
                'name': r.name,
                'sentiment': r.sentiment,
                'district': r.district,
                'cuisine_type': r.cuisine_type
            }
            for r in restaurants
        ]
        
        data = {
            'restaurants': restaurant_data,
            'ranking_method': ranking_method.value
        }
        
        response = self._make_request('POST', '/api/v1/restaurants/recommend', data)
        
        return RecommendationResponse(
            recommendation=Restaurant(**response['data']['recommendation']),
            candidates=[Restaurant(**candidate) for candidate in response['data']['candidates']],
            analysis_summary=response['data']['analysis_summary']
        )
    
    def analyze_sentiment(self, restaurants: List[Restaurant]) -> Dict[str, Any]:
        """Analyze restaurant sentiment data."""
        restaurant_data = [
            {
                'id': r.id,
                'name': r.name,
                'sentiment': r.sentiment
            }
            for r in restaurants
        ]
        
        data = {'restaurants': restaurant_data}
        response = self._make_request('POST', '/api/v1/restaurants/analyze', data)
        
        return response['data']
    
    def get_tool_metadata(self) -> Dict[str, Any]:
        """Get tool metadata for foundation models."""
        response = self._make_request('GET', '/tools/metadata')
        return response['data']
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        # Health endpoint doesn't require authentication
        temp_session = requests.Session()
        response = temp_session.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

# Custom exceptions
class APIError(Exception):
    """Base API error."""
    pass

class AuthenticationError(APIError):
    """Authentication failed."""
    pass

class ValidationError(APIError):
    """Request validation failed."""
    pass

class ServiceUnavailableError(APIError):
    """Service temporarily unavailable."""
    pass

# Usage example
async def main():
    # Initialize client
    client = AgentCoreGatewayClient(
        base_url='https://your-gateway.amazonaws.com',
        jwt_token='your_jwt_token_here'
    )
    
    try:
        # Search restaurants
        search_result = client.search_by_district(['Central district', 'Admiralty'])
        print(f"Found {search_result.total_count} restaurants")
        
        # Get recommendations
        recommendations = client.get_recommendations(
            restaurants=search_result.restaurants,
            ranking_method=RankingMethod.SENTIMENT_LIKES
        )
        
        print(f"Top recommendation: {recommendations.recommendation.name}")
        
        # Analyze sentiment
        sentiment_analysis = client.analyze_sentiment(search_result.restaurants)
        print(f"Average satisfaction: {sentiment_analysis['sentiment_analysis']['average_likes']}")
        
    except AuthenticationError:
        print("Authentication failed - check JWT token")
    except ValidationError as e:
        print(f"Validation error: {e}")
    except ServiceUnavailableError:
        print("Service temporarily unavailable - try again later")

if __name__ == "__main__":
    asyncio.run(main())
```

### Async Python Client

```python
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional

class AsyncAgentCoreGatewayClient:
    """Async Python client for high-performance applications."""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    async def _make_request(self, session: aiohttp.ClientSession, 
                           method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make async HTTP request."""
        url = f"{self.base_url}{endpoint}"
        
        async with session.request(method, url, json=data, headers=self.headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_text
                )
    
    async def search_by_district_async(self, districts: List[str]) -> Dict[str, Any]:
        """Async search by district."""
        async with aiohttp.ClientSession() as session:
            data = {'districts': districts}
            return await self._make_request(session, 'POST', '/api/v1/restaurants/search/district', data)
    
    async def batch_search(self, search_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform multiple searches concurrently."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for request in search_requests:
                if 'districts' in request:
                    task = self._make_request(
                        session, 'POST', '/api/v1/restaurants/search/district', 
                        {'districts': request['districts']}
                    )
                elif 'meal_types' in request:
                    task = self._make_request(
                        session, 'POST', '/api/v1/restaurants/search/meal-type',
                        {'meal_types': request['meal_types']}
                    )
                tasks.append(task)
            
            return await asyncio.gather(*tasks)

# Usage
async def batch_search_example():
    client = AsyncAgentCoreGatewayClient(
        base_url='https://your-gateway.amazonaws.com',
        jwt_token='your_jwt_token'
    )
    
    search_requests = [
        {'districts': ['Central district']},
        {'districts': ['Admiralty']},
        {'meal_types': ['breakfast']},
        {'meal_types': ['lunch']}
    ]
    
    results = await client.batch_search(search_requests)
    
    for i, result in enumerate(results):
        print(f"Search {i+1}: {result['data']['total_count']} restaurants found")
```

## JavaScript/TypeScript Integration

### TypeScript Client Library

```typescript
// types.ts
export interface Restaurant {
  id: string;
  name: string;
  district?: string;
  sentiment?: {
    likes: number;
    dislikes: number;
    neutral: number;
  };
  cuisine_type?: string;
  address?: string;
  operating_hours?: Record<string, string>;
}

export interface SearchResponse {
  success: boolean;
  data: {
    restaurants: Restaurant[];
    total_count: number;
    districts_searched?: string[];
    meal_types_searched?: string[];
  };
  metadata: {
    search_type: string;
    timestamp: string;
    processing_time_ms: number;
  };
}

export interface RecommendationResponse {
  success: boolean;
  data: {
    recommendation: Restaurant;
    candidates: Restaurant[];
    ranking_method: string;
    analysis_summary: {
      total_restaurants: number;
      average_sentiment_score: number;
      recommendation_confidence: string;
    };
  };
}

export interface APIError {
  success: false;
  error: {
    type: string;
    message: string;
    details?: Record<string, any>;
    timestamp: string;
    request_id?: string;
  };
}

export type MealType = 'breakfast' | 'lunch' | 'dinner';
export type RankingMethod = 'sentiment_likes' | 'combined_sentiment';

// client.ts
export class AgentCoreGatewayClient {
  private baseUrl: string;
  private jwtToken: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string, jwtToken: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.jwtToken = jwtToken;
    this.defaultHeaders = {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new APIClientError(
        data.error?.message || `HTTP ${response.status}`,
        response.status,
        data
      );
    }

    return data;
  }

  async searchByDistrict(districts: string[]): Promise<SearchResponse> {
    return this.makeRequest<SearchResponse>('/api/v1/restaurants/search/district', {
      method: 'POST',
      body: JSON.stringify({ districts })
    });
  }

  async searchByMealType(mealTypes: MealType[]): Promise<SearchResponse> {
    return this.makeRequest<SearchResponse>('/api/v1/restaurants/search/meal-type', {
      method: 'POST',
      body: JSON.stringify({ meal_types: mealTypes })
    });
  }

  async searchCombined(
    districts?: string[],
    mealTypes?: MealType[]
  ): Promise<SearchResponse> {
    const body: any = {};
    if (districts) body.districts = districts;
    if (mealTypes) body.meal_types = mealTypes;

    return this.makeRequest<SearchResponse>('/api/v1/restaurants/search/combined', {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }

  async getRecommendations(
    restaurants: Restaurant[],
    rankingMethod: RankingMethod = 'sentiment_likes'
  ): Promise<RecommendationResponse> {
    return this.makeRequest<RecommendationResponse>('/api/v1/restaurants/recommend', {
      method: 'POST',
      body: JSON.stringify({
        restaurants,
        ranking_method: rankingMethod
      })
    });
  }

  async analyzeSentiment(restaurants: Restaurant[]): Promise<any> {
    return this.makeRequest('/api/v1/restaurants/analyze', {
      method: 'POST',
      body: JSON.stringify({ restaurants })
    });
  }

  async getToolMetadata(): Promise<any> {
    return this.makeRequest('/tools/metadata');
  }

  async healthCheck(): Promise<any> {
    // Health endpoint doesn't require authentication
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  // Utility methods
  updateToken(newToken: string): void {
    this.jwtToken = newToken;
    this.defaultHeaders['Authorization'] = `Bearer ${newToken}`;
  }

  async refreshTokenAndRetry<T>(
    operation: () => Promise<T>,
    tokenRefreshFn: () => Promise<string>
  ): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      if (error instanceof APIClientError && error.status === 401) {
        // Token expired, refresh and retry
        const newToken = await tokenRefreshFn();
        this.updateToken(newToken);
        return operation();
      }
      throw error;
    }
  }
}

export class APIClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIClientError';
  }
}

// Usage example
async function example() {
  const client = new AgentCoreGatewayClient(
    'https://your-gateway.amazonaws.com',
    'your_jwt_token'
  );

  try {
    // Search restaurants
    const searchResult = await client.searchByDistrict(['Central district']);
    console.log(`Found ${searchResult.data.total_count} restaurants`);

    // Get recommendations
    const recommendations = await client.getRecommendations(
      searchResult.data.restaurants,
      'sentiment_likes'
    );
    
    console.log(`Top recommendation: ${recommendations.data.recommendation.name}`);

  } catch (error) {
    if (error instanceof APIClientError) {
      console.error(`API Error ${error.status}: ${error.message}`);
      console.error('Response:', error.response);
    } else {
      console.error('Unexpected error:', error);
    }
  }
}
```

## React Application Integration

### React Hook for API Integration

```typescript
// hooks/useAgentCoreGateway.ts
import { useState, useEffect, useCallback } from 'react';
import { AgentCoreGatewayClient, Restaurant, SearchResponse } from '../services/agentCoreClient';

interface UseAgentCoreGatewayOptions {
  baseUrl: string;
  getToken: () => Promise<string>;
}

export function useAgentCoreGateway({ baseUrl, getToken }: UseAgentCoreGatewayOptions) {
  const [client, setClient] = useState<AgentCoreGatewayClient | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize client
  useEffect(() => {
    const initializeClient = async () => {
      try {
        const token = await getToken();
        const newClient = new AgentCoreGatewayClient(baseUrl, token);
        setClient(newClient);
      } catch (err) {
        setError('Failed to initialize API client');
      }
    };

    initializeClient();
  }, [baseUrl, getToken]);

  // Generic API call wrapper
  const makeApiCall = useCallback(async <T>(
    operation: (client: AgentCoreGatewayClient) => Promise<T>
  ): Promise<T | null> => {
    if (!client) {
      setError('Client not initialized');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await operation(client);
      return result;
    } catch (err) {
      if (err instanceof APIClientError && err.status === 401) {
        // Token expired, refresh client
        try {
          const newToken = await getToken();
          client.updateToken(newToken);
          return await operation(client);
        } catch (refreshErr) {
          setError('Authentication failed');
          return null;
        }
      } else {
        setError(err instanceof Error ? err.message : 'Unknown error');
        return null;
      }
    } finally {
      setLoading(false);
    }
  }, [client, getToken]);

  // Specific API methods
  const searchByDistrict = useCallback((districts: string[]) => 
    makeApiCall(client => client.searchByDistrict(districts))
  , [makeApiCall]);

  const getRecommendations = useCallback((restaurants: Restaurant[]) =>
    makeApiCall(client => client.getRecommendations(restaurants))
  , [makeApiCall]);

  const searchByMealType = useCallback((mealTypes: string[]) =>
    makeApiCall(client => client.searchByMealType(mealTypes as any))
  , [makeApiCall]);

  return {
    client,
    loading,
    error,
    searchByDistrict,
    getRecommendations,
    searchByMealType,
    makeApiCall
  };
}

// components/RestaurantSearch.tsx
import React, { useState } from 'react';
import { useAgentCoreGateway } from '../hooks/useAgentCoreGateway';
import { Auth } from 'aws-amplify';

const HONG_KONG_DISTRICTS = [
  'Central district', 'Admiralty', 'Causeway Bay', 'Wan Chai',
  'Tsim Sha Tsui', 'Mong Kok', 'Yau Ma Tei', 'Jordan'
];

export function RestaurantSearch() {
  const [selectedDistricts, setSelectedDistricts] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<any>(null);

  const { searchByDistrict, getRecommendations, loading, error } = useAgentCoreGateway({
    baseUrl: process.env.REACT_APP_GATEWAY_URL || '',
    getToken: async () => {
      const session = await Auth.currentSession();
      return session.getIdToken().getJwtToken();
    }
  });

  const handleSearch = async () => {
    if (selectedDistricts.length === 0) return;

    const results = await searchByDistrict(selectedDistricts);
    if (results) {
      setSearchResults(results);
    }
  };

  const handleGetRecommendations = async () => {
    if (!searchResults?.data?.restaurants) return;

    const recommendations = await getRecommendations(searchResults.data.restaurants);
    if (recommendations) {
      console.log('Top recommendation:', recommendations.data.recommendation);
    }
  };

  return (
    <div className="restaurant-search">
      <h2>Restaurant Search</h2>
      
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}

      <div className="district-selection">
        <h3>Select Districts:</h3>
        {HONG_KONG_DISTRICTS.map(district => (
          <label key={district}>
            <input
              type="checkbox"
              checked={selectedDistricts.includes(district)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedDistricts([...selectedDistricts, district]);
                } else {
                  setSelectedDistricts(selectedDistricts.filter(d => d !== district));
                }
              }}
            />
            {district}
          </label>
        ))}
      </div>

      <button 
        onClick={handleSearch} 
        disabled={loading || selectedDistricts.length === 0}
      >
        {loading ? 'Searching...' : 'Search Restaurants'}
      </button>

      {searchResults && (
        <div className="search-results">
          <h3>Search Results</h3>
          <p>Found {searchResults.data.total_count} restaurants</p>
          
          <button onClick={handleGetRecommendations} disabled={loading}>
            Get Recommendations
          </button>

          <div className="restaurant-list">
            {searchResults.data.restaurants.slice(0, 10).map((restaurant: any) => (
              <div key={restaurant.id} className="restaurant-card">
                <h4>{restaurant.name}</h4>
                <p>District: {restaurant.district}</p>
                <p>Cuisine: {restaurant.cuisine_type}</p>
                {restaurant.sentiment && (
                  <p>
                    Likes: {restaurant.sentiment.likes}, 
                    Dislikes: {restaurant.sentiment.dislikes}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

## Node.js Backend Integration

### Express.js Middleware Integration

```javascript
// middleware/agentCoreProxy.js
const { AgentCoreGatewayClient } = require('../services/agentCoreClient');
const jwt = require('jsonwebtoken');

class AgentCoreProxyMiddleware {
  constructor(gatewayUrl, cognitoConfig) {
    this.gatewayUrl = gatewayUrl;
    this.cognitoConfig = cognitoConfig;
    this.clientCache = new Map();
  }

  // Middleware to extract and validate JWT token
  authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
      return res.status(401).json({ error: 'Access token required' });
    }

    // Validate token (simplified - in production, verify against Cognito JWKS)
    try {
      const decoded = jwt.decode(token);
      req.user = decoded;
      req.jwtToken = token;
      next();
    } catch (error) {
      return res.status(403).json({ error: 'Invalid token' });
    }
  };

  // Get or create client for user
  getClientForUser = (userId, jwtToken) => {
    if (!this.clientCache.has(userId)) {
      const client = new AgentCoreGatewayClient(this.gatewayUrl, jwtToken);
      this.clientCache.set(userId, client);
    }
    return this.clientCache.get(userId);
  };

  // Proxy restaurant search requests
  proxyRestaurantSearch = async (req, res) => {
    try {
      const client = this.getClientForUser(req.user.sub, req.jwtToken);
      const { searchType, ...searchParams } = req.body;

      let result;
      switch (searchType) {
        case 'district':
          result = await client.searchByDistrict(searchParams.districts);
          break;
        case 'meal-type':
          result = await client.searchByMealType(searchParams.mealTypes);
          break;
        case 'combined':
          result = await client.searchCombined(
            searchParams.districts,
            searchParams.mealTypes
          );
          break;
        default:
          return res.status(400).json({ error: 'Invalid search type' });
      }

      res.json(result);
    } catch (error) {
      console.error('Proxy error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  };

  // Proxy recommendation requests
  proxyRecommendations = async (req, res) => {
    try {
      const client = this.getClientForUser(req.user.sub, req.jwtToken);
      const { restaurants, rankingMethod } = req.body;

      const result = await client.getRecommendations(restaurants, rankingMethod);
      res.json(result);
    } catch (error) {
      console.error('Recommendation proxy error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  };
}

module.exports = AgentCoreProxyMiddleware;

// routes/restaurants.js
const express = require('express');
const AgentCoreProxyMiddleware = require('../middleware/agentCoreProxy');

const router = express.Router();

const proxyMiddleware = new AgentCoreProxyMiddleware(
  process.env.AGENTCORE_GATEWAY_URL,
  {
    userPoolId: process.env.COGNITO_USER_POOL_ID,
    clientId: process.env.COGNITO_CLIENT_ID,
    region: process.env.AWS_REGION
  }
);

// Apply authentication middleware
router.use(proxyMiddleware.authenticateToken);

// Restaurant search endpoints
router.post('/search', proxyMiddleware.proxyRestaurantSearch);
router.post('/recommend', proxyMiddleware.proxyRecommendations);

// Custom endpoint combining search and recommendations
router.post('/search-and-recommend', async (req, res) => {
  try {
    const client = proxyMiddleware.getClientForUser(req.user.sub, req.jwtToken);
    const { districts, mealTypes, rankingMethod } = req.body;

    // First search
    const searchResult = await client.searchCombined(districts, mealTypes);
    
    // Then get recommendations
    const recommendations = await client.getRecommendations(
      searchResult.data.restaurants,
      rankingMethod
    );

    res.json({
      search: searchResult,
      recommendations: recommendations
    });
  } catch (error) {
    console.error('Combined search error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;

// app.js
const express = require('express');
const cors = require('cors');
const restaurantRoutes = require('./routes/restaurants');

const app = express();

app.use(cors());
app.use(express.json());

// Restaurant API routes
app.use('/api/restaurants', restaurantRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Mobile Application Integration

### React Native Integration

```typescript
// services/AgentCoreGatewayService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Auth } from 'aws-amplify';

interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number;
}

export class MobileAgentCoreGatewayService {
  private baseUrl: string;
  private cachePrefix = 'agentcore_cache_';
  private defaultCacheTTL = 5 * 60 * 1000; // 5 minutes

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async getAuthToken(): Promise<string> {
    try {
      const session = await Auth.currentSession();
      return session.getIdToken().getJwtToken();
    } catch (error) {
      throw new Error('Authentication required');
    }
  }

  private async getCachedData(key: string): Promise<any | null> {
    try {
      const cached = await AsyncStorage.getItem(`${this.cachePrefix}${key}`);
      if (!cached) return null;

      const entry: CacheEntry = JSON.parse(cached);
      const now = Date.now();

      if (now - entry.timestamp > entry.ttl) {
        await AsyncStorage.removeItem(`${this.cachePrefix}${key}`);
        return null;
      }

      return entry.data;
    } catch (error) {
      return null;
    }
  }

  private async setCachedData(key: string, data: any, ttl: number = this.defaultCacheTTL): Promise<void> {
    try {
      const entry: CacheEntry = {
        data,
        timestamp: Date.now(),
        ttl
      };
      await AsyncStorage.setItem(`${this.cachePrefix}${key}`, JSON.stringify(entry));
    } catch (error) {
      // Cache write failed, continue without caching
      console.warn('Cache write failed:', error);
    }
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const token = await this.getAuthToken();
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async searchRestaurantsByDistrict(districts: string[], useCache: boolean = true): Promise<any> {
    const cacheKey = `search_district_${districts.sort().join('_')}`;
    
    if (useCache) {
      const cached = await this.getCachedData(cacheKey);
      if (cached) return cached;
    }

    const result = await this.makeRequest('/api/v1/restaurants/search/district', {
      method: 'POST',
      body: JSON.stringify({ districts })
    });

    if (useCache) {
      await this.setCachedData(cacheKey, result);
    }

    return result;
  }

  async getRecommendations(restaurants: any[], rankingMethod: string = 'sentiment_likes'): Promise<any> {
    return this.makeRequest('/api/v1/restaurants/recommend', {
      method: 'POST',
      body: JSON.stringify({
        restaurants,
        ranking_method: rankingMethod
      })
    });
  }

  async clearCache(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(this.cachePrefix));
      await AsyncStorage.multiRemove(cacheKeys);
    } catch (error) {
      console.warn('Cache clear failed:', error);
    }
  }
}

// hooks/useRestaurantSearch.ts
import { useState, useEffect } from 'react';
import { MobileAgentCoreGatewayService } from '../services/AgentCoreGatewayService';

export function useRestaurantSearch(gatewayUrl: string) {
  const [service] = useState(() => new MobileAgentCoreGatewayService(gatewayUrl));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<any>(null);

  const searchByDistrict = async (districts: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const results = await service.searchRestaurantsByDistrict(districts);
      setSearchResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendations = async (restaurants: any[]) => {
    setLoading(true);
    setError(null);

    try {
      const recommendations = await service.getRecommendations(restaurants);
      return recommendations;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Recommendations failed');
      return null;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    searchResults,
    searchByDistrict,
    getRecommendations,
    clearCache: service.clearCache
  };
}

// components/RestaurantSearchScreen.tsx
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { useRestaurantSearch } from '../hooks/useRestaurantSearch';

const DISTRICTS = [
  'Central district', 'Admiralty', 'Causeway Bay', 'Wan Chai',
  'Tsim Sha Tsui', 'Mong Kok'
];

export function RestaurantSearchScreen() {
  const [selectedDistricts, setSelectedDistricts] = useState<string[]>([]);
  const { loading, error, searchResults, searchByDistrict, getRecommendations } = useRestaurantSearch(
    process.env.EXPO_PUBLIC_GATEWAY_URL || ''
  );

  const toggleDistrict = (district: string) => {
    setSelectedDistricts(prev => 
      prev.includes(district)
        ? prev.filter(d => d !== district)
        : [...prev, district]
    );
  };

  const handleSearch = () => {
    if (selectedDistricts.length > 0) {
      searchByDistrict(selectedDistricts);
    }
  };

  const handleGetRecommendations = async () => {
    if (searchResults?.data?.restaurants) {
      const recommendations = await getRecommendations(searchResults.data.restaurants);
      if (recommendations) {
        // Navigate to recommendations screen or show modal
        console.log('Top recommendation:', recommendations.data.recommendation);
      }
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Restaurant Search</Text>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <Text style={styles.sectionTitle}>Select Districts:</Text>
      <View style={styles.districtContainer}>
        {DISTRICTS.map(district => (
          <TouchableOpacity
            key={district}
            style={[
              styles.districtButton,
              selectedDistricts.includes(district) && styles.selectedDistrict
            ]}
            onPress={() => toggleDistrict(district)}
          >
            <Text style={[
              styles.districtText,
              selectedDistricts.includes(district) && styles.selectedDistrictText
            ]}>
              {district}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity
        style={[styles.searchButton, loading && styles.disabledButton]}
        onPress={handleSearch}
        disabled={loading || selectedDistricts.length === 0}
      >
        <Text style={styles.searchButtonText}>
          {loading ? 'Searching...' : 'Search Restaurants'}
        </Text>
      </TouchableOpacity>

      {searchResults && (
        <View style={styles.resultsContainer}>
          <Text style={styles.resultsTitle}>
            Found {searchResults.data.total_count} restaurants
          </Text>
          
          <TouchableOpacity
            style={styles.recommendButton}
            onPress={handleGetRecommendations}
            disabled={loading}
          >
            <Text style={styles.recommendButtonText}>Get Recommendations</Text>
          </TouchableOpacity>

          <FlatList
            data={searchResults.data.restaurants.slice(0, 20)}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <View style={styles.restaurantCard}>
                <Text style={styles.restaurantName}>{item.name}</Text>
                <Text style={styles.restaurantDistrict}>{item.district}</Text>
                <Text style={styles.restaurantCuisine}>{item.cuisine_type}</Text>
                {item.sentiment && (
                  <Text style={styles.restaurantSentiment}>
                    👍 {item.sentiment.likes} 👎 {item.sentiment.dislikes}
                  </Text>
                )}
              </View>
            )}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff'
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16
  },
  errorText: {
    color: '#c62828'
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12
  },
  districtContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16
  },
  districtButton: {
    backgroundColor: '#f5f5f5',
    padding: 8,
    margin: 4,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ddd'
  },
  selectedDistrict: {
    backgroundColor: '#2196f3',
    borderColor: '#2196f3'
  },
  districtText: {
    color: '#333'
  },
  selectedDistrictText: {
    color: '#fff'
  },
  searchButton: {
    backgroundColor: '#2196f3',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 16
  },
  disabledButton: {
    backgroundColor: '#ccc'
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600'
  },
  resultsContainer: {
    flex: 1
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12
  },
  recommendButton: {
    backgroundColor: '#4caf50',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 16
  },
  recommendButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600'
  },
  restaurantCard: {
    backgroundColor: '#f9f9f9',
    padding: 12,
    marginBottom: 8,
    borderRadius: 8
  },
  restaurantName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4
  },
  restaurantDistrict: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2
  },
  restaurantCuisine: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4
  },
  restaurantSentiment: {
    fontSize: 12,
    color: '#888'
  }
});
```

This completes the first part of the integration examples. Let me continue with the remaining sections.## Fou
ndation Model Integration

### OpenAI GPT Integration

```python
# foundation_model_integration.py
import openai
import json
from typing import List, Dict, Any
from agentcore_client import AgentCoreGatewayClient

class RestaurantAssistantWithGPT:
    """Foundation model integration with AgentCore Gateway."""
    
    def __init__(self, openai_api_key: str, gateway_url: str, jwt_token: str):
        openai.api_key = openai_api_key
        self.gateway_client = AgentCoreGatewayClient(gateway_url, jwt_token)
        self.tool_metadata = None
    
    async def initialize(self):
        """Initialize with tool metadata from Gateway."""
        self.tool_metadata = await self.gateway_client.get_tool_metadata()
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Convert Gateway tools to OpenAI function definitions."""
        if not self.tool_metadata:
            return []
        
        functions = []
        for tool in self.tool_metadata['data']['tools']:
            function_def = {
                "name": tool['name'],
                "description": tool['description'],
                "parameters": {
                    "type": "object",
                    "properties": tool['parameters'],
                    "required": [
                        param for param, config in tool['parameters'].items()
                        if config.get('required', False)
                    ]
                }
            }
            functions.append(function_def)
        
        return functions
    
    async def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gateway function based on function name."""
        if function_name == "search_restaurants_by_district":
            return await self.gateway_client.search_by_district(arguments['districts'])
        elif function_name == "search_restaurants_by_meal_type":
            return await self.gateway_client.search_by_meal_type(arguments['meal_types'])
        elif function_name == "search_restaurants_combined":
            return await self.gateway_client.search_combined(
                arguments.get('districts'),
                arguments.get('meal_types')
            )
        elif function_name == "recommend_restaurants":
            return await self.gateway_client.get_recommendations(
                arguments['restaurants'],
                arguments.get('ranking_method', 'sentiment_likes')
            )
        elif function_name == "analyze_restaurant_sentiment":
            return await self.gateway_client.analyze_sentiment(arguments['restaurants'])
        else:
            raise ValueError(f"Unknown function: {function_name}")
    
    async def chat_with_tools(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Chat with GPT using Gateway tools."""
        if conversation_history is None:
            conversation_history = []
        
        # Add system message with tool context
        system_message = {
            "role": "system",
            "content": """You are a helpful restaurant assistant for Hong Kong. You have access to restaurant search and recommendation tools. 
            
Available districts: Central district, Admiralty, Causeway Bay, Wan Chai, Tsim Sha Tsui, Mong Kok, Yau Ma Tei, Jordan.
Available meal types: breakfast (07:00-11:29), lunch (11:30-17:29), dinner (17:30-22:30).

Use the tools to help users find restaurants and get recommendations based on their preferences."""
        }
        
        messages = [system_message] + conversation_history + [{"role": "user", "content": user_message}]
        
        # Get function definitions
        functions = self.get_function_definitions()
        
        # Call GPT with function calling
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=messages,
            functions=functions,
            function_call="auto"
        )
        
        message = response.choices[0].message
        
        # Check if GPT wants to call a function
        if message.get("function_call"):
            function_name = message["function_call"]["name"]
            function_args = json.loads(message["function_call"]["arguments"])
            
            # Execute the function
            function_result = await self.execute_function(function_name, function_args)
            
            # Add function call and result to conversation
            messages.append(message)
            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(function_result)
            })
            
            # Get final response from GPT
            final_response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages
            )
            
            return final_response.choices[0].message.content
        else:
            return message.content

# Usage example
async def main():
    assistant = RestaurantAssistantWithGPT(
        openai_api_key="your_openai_key",
        gateway_url="https://your-gateway.amazonaws.com",
        jwt_token="your_jwt_token"
    )
    
    await assistant.initialize()
    
    # Example conversation
    response = await assistant.chat_with_tools(
        "I'm looking for good Cantonese restaurants in Central district for lunch. Can you help me find some and give me recommendations?"
    )
    
    print(response)
```

### Anthropic Claude Integration

```python
# claude_integration.py
import anthropic
from typing import List, Dict, Any
from agentcore_client import AgentCoreGatewayClient

class RestaurantAssistantWithClaude:
    """Claude integration with AgentCore Gateway tools."""
    
    def __init__(self, anthropic_api_key: str, gateway_url: str, jwt_token: str):
        self.claude = anthropic.Anthropic(api_key=anthropic_api_key)
        self.gateway_client = AgentCoreGatewayClient(gateway_url, jwt_token)
        self.tool_metadata = None
    
    async def initialize(self):
        """Initialize with tool metadata."""
        self.tool_metadata = await self.gateway_client.get_tool_metadata()
    
    def get_claude_tools(self) -> List[Dict[str, Any]]:
        """Convert Gateway tools to Claude tool format."""
        if not self.tool_metadata:
            return []
        
        claude_tools = []
        for tool in self.tool_metadata['data']['tools']:
            claude_tool = {
                "name": tool['name'],
                "description": tool['description'],
                "input_schema": {
                    "type": "object",
                    "properties": tool['parameters'],
                    "required": [
                        param for param, config in tool['parameters'].items()
                        if config.get('required', False)
                    ]
                }
            }
            claude_tools.append(claude_tool)
        
        return claude_tools
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gateway tool."""
        if tool_name == "search_restaurants_by_district":
            return await self.gateway_client.search_by_district(tool_input['districts'])
        elif tool_name == "search_restaurants_by_meal_type":
            return await self.gateway_client.search_by_meal_type(tool_input['meal_types'])
        elif tool_name == "search_restaurants_combined":
            return await self.gateway_client.search_combined(
                tool_input.get('districts'),
                tool_input.get('meal_types')
            )
        elif tool_name == "recommend_restaurants":
            return await self.gateway_client.get_recommendations(
                tool_input['restaurants'],
                tool_input.get('ranking_method', 'sentiment_likes')
            )
        elif tool_name == "analyze_restaurant_sentiment":
            return await self.gateway_client.analyze_sentiment(tool_input['restaurants'])
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def chat_with_tools(self, user_message: str) -> str:
        """Chat with Claude using Gateway tools."""
        system_prompt = """You are a helpful restaurant assistant for Hong Kong. You have access to restaurant search and recommendation tools.

Available Hong Kong districts: Central district, Admiralty, Causeway Bay, Wan Chai, Tsim Sha Tsui, Mong Kok, Yau Ma Tei, Jordan.
Meal types: breakfast (07:00-11:29), lunch (11:30-17:29), dinner (17:30-22:30).

Use the available tools to help users find restaurants and get personalized recommendations."""
        
        tools = self.get_claude_tools()
        
        response = self.claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            system=system_prompt,
            tools=tools,
            messages=[{"role": "user", "content": user_message}]
        )
        
        # Handle tool use
        if response.stop_reason == "tool_use":
            tool_use = response.content[-1]
            if tool_use.type == "tool_use":
                tool_result = await self.execute_tool(tool_use.name, tool_use.input)
                
                # Continue conversation with tool result
                follow_up = self.claude.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    system=system_prompt,
                    tools=tools,
                    messages=[
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": response.content},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use.id,
                                    "content": json.dumps(tool_result)
                                }
                            ]
                        }
                    ]
                )
                return follow_up.content[0].text
        
        return response.content[0].text

# Usage
async def claude_example():
    assistant = RestaurantAssistantWithClaude(
        anthropic_api_key="your_anthropic_key",
        gateway_url="https://your-gateway.amazonaws.com",
        jwt_token="your_jwt_token"
    )
    
    await assistant.initialize()
    
    response = await assistant.chat_with_tools(
        "I want to find highly-rated dim sum restaurants in Tsim Sha Tsui for brunch. Can you search and recommend the best ones?"
    )
    
    print(response)
```

## Error Handling Patterns

### Comprehensive Error Handling

```python
# error_handling.py
import asyncio
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

class ErrorType(Enum):
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"
    NETWORK = "network"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class APIError:
    type: ErrorType
    message: str
    status_code: Optional[int] = None
    details: Optional[dict] = None
    retry_after: Optional[int] = None

class RetryStrategy:
    """Configurable retry strategy for API calls."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def should_retry(self, error: APIError, attempt: int) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.max_retries:
            return False
        
        # Retry on specific error types
        retryable_errors = {
            ErrorType.SERVICE_UNAVAILABLE,
            ErrorType.NETWORK,
            ErrorType.TIMEOUT
        }
        
        return error.type in retryable_errors
    
    def get_delay(self, attempt: int, error: APIError) -> float:
        """Calculate delay before retry."""
        if error.retry_after:
            return min(error.retry_after, self.max_delay)
        
        # Exponential backoff
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)

class ResilientAgentCoreClient:
    """AgentCore client with comprehensive error handling and retry logic."""
    
    def __init__(self, base_url: str, jwt_token: str, retry_strategy: Optional[RetryStrategy] = None):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.retry_strategy = retry_strategy or RetryStrategy()
        self.logger = logging.getLogger(__name__)
    
    def _parse_error(self, response_data: dict, status_code: int) -> APIError:
        """Parse API error response."""
        error_info = response_data.get('error', {})
        error_type = self._classify_error(status_code, error_info)
        
        return APIError(
            type=error_type,
            message=error_info.get('message', f'HTTP {status_code}'),
            status_code=status_code,
            details=error_info.get('details'),
            retry_after=response_data.get('retry_after')
        )
    
    def _classify_error(self, status_code: int, error_info: dict) -> ErrorType:
        """Classify error type based on status code and error info."""
        if status_code == 401:
            return ErrorType.AUTHENTICATION
        elif status_code == 400:
            return ErrorType.VALIDATION
        elif status_code == 429:
            return ErrorType.RATE_LIMIT
        elif status_code == 503:
            return ErrorType.SERVICE_UNAVAILABLE
        elif status_code >= 500:
            return ErrorType.SERVICE_UNAVAILABLE
        else:
            return ErrorType.UNKNOWN
    
    async def _make_request_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with retry logic."""
        last_error = None
        
        for attempt in range(self.retry_strategy.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            
            except Exception as e:
                # Convert to APIError if needed
                if isinstance(e, APIError):
                    error = e
                else:
                    error = APIError(
                        type=ErrorType.UNKNOWN,
                        message=str(e)
                    )
                
                last_error = error
                
                # Check if we should retry
                if not self.retry_strategy.should_retry(error, attempt):
                    break
                
                # Calculate delay and wait
                delay = self.retry_strategy.get_delay(attempt, error)
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {error.message}"
                )
                await asyncio.sleep(delay)
        
        # All retries exhausted
        self.logger.error(f"Request failed after {self.retry_strategy.max_retries + 1} attempts")
        raise last_error
    
    async def search_by_district_resilient(self, districts: list) -> dict:
        """Resilient district search with error handling."""
        async def _search():
            # Implement actual API call here
            # This is a placeholder for the actual implementation
            pass
        
        return await self._make_request_with_retry(_search)

class CircuitBreaker:
    """Circuit breaker pattern for API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def on_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return False
        
        return (asyncio.get_event_loop().time() - self.last_failure_time) >= self.recovery_timeout

# Usage example
async def error_handling_example():
    # Configure retry strategy
    retry_strategy = RetryStrategy(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0
    )
    
    # Create resilient client
    client = ResilientAgentCoreClient(
        base_url="https://your-gateway.amazonaws.com",
        jwt_token="your_jwt_token",
        retry_strategy=retry_strategy
    )
    
    try:
        # This will automatically retry on transient failures
        results = await client.search_by_district_resilient(['Central district'])
        print("Search successful:", results)
        
    except APIError as e:
        if e.type == ErrorType.AUTHENTICATION:
            print("Authentication failed - refresh token required")
        elif e.type == ErrorType.VALIDATION:
            print(f"Validation error: {e.message}")
            if e.details:
                print("Details:", e.details)
        elif e.type == ErrorType.RATE_LIMIT:
            print(f"Rate limited - retry after {e.retry_after} seconds")
        elif e.type == ErrorType.SERVICE_UNAVAILABLE:
            print("Service temporarily unavailable")
        else:
            print(f"Unexpected error: {e.message}")
```

## Performance Optimization

### Caching and Batching Strategies

```python
# performance_optimization.py
import asyncio
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: float
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl

class InMemoryCache:
    """In-memory cache with TTL support."""
    
    def __init__(self, default_ttl: float = 300):  # 5 minutes
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from parameters."""
        params_str = json.dumps(params, sort_keys=True)
        return f"{prefix}:{hashlib.md5(params_str.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        entry = self.cache.get(key)
        if entry and not entry.is_expired():
            return entry.data
        elif entry:
            # Remove expired entry
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set cached value."""
        ttl = ttl or self.default_ttl
        self.cache[key] = CacheEntry(
            data=value,
            timestamp=time.time(),
            ttl=ttl
        )
    
    def clear_expired(self) -> None:
        """Clear expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]

class BatchProcessor:
    """Batch multiple requests for efficiency."""
    
    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests: Dict[str, List[Tuple[Dict, asyncio.Future]]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
    
    async def add_request(self, request_type: str, params: Dict[str, Any]) -> Any:
        """Add request to batch."""
        future = asyncio.Future()
        self.pending_requests[request_type].append((params, future))
        
        # Start batch timer if not already running
        if request_type not in self.batch_timers:
            self.batch_timers[request_type] = asyncio.create_task(
                self._batch_timer(request_type)
            )
        
        # Process batch if it's full
        if len(self.pending_requests[request_type]) >= self.batch_size:
            await self._process_batch(request_type)
        
        return await future
    
    async def _batch_timer(self, request_type: str) -> None:
        """Timer to process batch after timeout."""
        await asyncio.sleep(self.batch_timeout)
        if request_type in self.pending_requests and self.pending_requests[request_type]:
            await self._process_batch(request_type)
    
    async def _process_batch(self, request_type: str) -> None:
        """Process batched requests."""
        if request_type not in self.pending_requests:
            return
        
        requests = self.pending_requests[request_type]
        if not requests:
            return
        
        # Clear pending requests
        self.pending_requests[request_type] = []
        
        # Cancel timer
        if request_type in self.batch_timers:
            self.batch_timers[request_type].cancel()
            del self.batch_timers[request_type]
        
        # Process batch (implement specific logic for each request type)
        try:
            results = await self._execute_batch(request_type, requests)
            
            # Resolve futures with results
            for i, (params, future) in enumerate(requests):
                if i < len(results):
                    future.set_result(results[i])
                else:
                    future.set_exception(Exception("Batch processing failed"))
        
        except Exception as e:
            # Reject all futures
            for params, future in requests:
                future.set_exception(e)
    
    async def _execute_batch(self, request_type: str, requests: List[Tuple[Dict, asyncio.Future]]) -> List[Any]:
        """Execute batched requests - implement specific logic."""
        # This would contain the actual batch execution logic
        # For now, return empty results
        return [None] * len(requests)

class OptimizedAgentCoreClient:
    """Performance-optimized AgentCore client."""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.cache = InMemoryCache()
        self.batch_processor = BatchProcessor()
        self.connection_pool = None  # Would use aiohttp.ClientSession
    
    async def search_by_district_cached(self, districts: List[str]) -> Dict[str, Any]:
        """Search with caching."""
        cache_key = self.cache._generate_key("district_search", {"districts": sorted(districts)})
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Make API call
        result = await self._make_api_call("/api/v1/restaurants/search/district", {
            "districts": districts
        })
        
        # Cache result (shorter TTL for search results)
        self.cache.set(cache_key, result, ttl=180)  # 3 minutes
        
        return result
    
    async def get_recommendations_batched(self, restaurants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get recommendations using batching."""
        return await self.batch_processor.add_request("recommendations", {
            "restaurants": restaurants,
            "ranking_method": "sentiment_likes"
        })
    
    async def _make_api_call(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call with connection pooling."""
        # Implementation would use aiohttp.ClientSession for connection pooling
        # This is a placeholder
        pass
    
    async def warm_cache(self, common_districts: List[str]) -> None:
        """Pre-warm cache with common searches."""
        tasks = []
        for district in common_districts:
            task = self.search_by_district_cached([district])
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_entries = len(self.cache.cache)
        expired_entries = sum(1 for entry in self.cache.cache.values() if entry.is_expired())
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_hit_rate": getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1)
        }

# Usage example
async def performance_example():
    client = OptimizedAgentCoreClient(
        base_url="https://your-gateway.amazonaws.com",
        jwt_token="your_jwt_token"
    )
    
    # Warm cache with common searches
    common_districts = ["Central district", "Admiralty", "Causeway Bay"]
    await client.warm_cache(common_districts)
    
    # Subsequent searches will be cached
    start_time = time.time()
    result1 = await client.search_by_district_cached(["Central district"])
    cached_time = time.time() - start_time
    
    start_time = time.time()
    result2 = await client.search_by_district_cached(["Central district"])  # Should be cached
    second_time = time.time() - start_time
    
    print(f"First request: {cached_time:.3f}s")
    print(f"Cached request: {second_time:.3f}s")
    print(f"Cache stats: {client.get_cache_stats()}")
```

## Testing Strategies

### Comprehensive Testing Framework

```python
# test_integration.py
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

class MockAgentCoreGateway:
    """Mock Gateway for testing."""
    
    def __init__(self):
        self.call_count = 0
        self.last_request = None
    
    async def search_by_district(self, districts: List[str]) -> Dict[str, Any]:
        self.call_count += 1
        self.last_request = {"method": "search_by_district", "districts": districts}
        
        return {
            "success": True,
            "data": {
                "restaurants": [
                    {
                        "id": f"rest_{i}",
                        "name": f"Restaurant {i}",
                        "district": districts[0] if districts else "Central district",
                        "sentiment": {"likes": 80 + i, "dislikes": 10, "neutral": 10}
                    }
                    for i in range(5)
                ],
                "total_count": 5,
                "districts_searched": districts
            },
            "metadata": {
                "search_type": "district",
                "timestamp": "2025-01-03T10:30:00Z",
                "processing_time_ms": 150
            }
        }
    
    async def get_recommendations(self, restaurants: List[Dict], ranking_method: str = "sentiment_likes") -> Dict[str, Any]:
        self.call_count += 1
        self.last_request = {"method": "get_recommendations", "restaurants": len(restaurants)}
        
        return {
            "success": True,
            "data": {
                "recommendation": restaurants[0] if restaurants else {},
                "candidates": restaurants[:3],
                "ranking_method": ranking_method,
                "analysis_summary": {
                    "total_restaurants": len(restaurants),
                    "average_sentiment_score": 0.85,
                    "recommendation_confidence": "high"
                }
            }
        }

@pytest.fixture
def mock_gateway():
    return MockAgentCoreGateway()

@pytest.fixture
def sample_restaurants():
    return [
        {
            "id": "rest_001",
            "name": "Great Restaurant",
            "district": "Central district",
            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
        },
        {
            "id": "rest_002", 
            "name": "Good Restaurant",
            "district": "Admiralty",
            "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10}
        }
    ]

class TestAgentCoreIntegration:
    """Integration tests for AgentCore Gateway client."""
    
    @pytest.mark.asyncio
    async def test_search_by_district_success(self, mock_gateway):
        """Test successful district search."""
        districts = ["Central district", "Admiralty"]
        result = await mock_gateway.search_by_district(districts)
        
        assert result["success"] is True
        assert result["data"]["total_count"] == 5
        assert result["data"]["districts_searched"] == districts
        assert len(result["data"]["restaurants"]) == 5
        assert mock_gateway.call_count == 1
    
    @pytest.mark.asyncio
    async def test_get_recommendations_success(self, mock_gateway, sample_restaurants):
        """Test successful recommendations."""
        result = await mock_gateway.get_recommendations(sample_restaurants)
        
        assert result["success"] is True
        assert result["data"]["recommendation"]["id"] == "rest_001"
        assert len(result["data"]["candidates"]) == 2
        assert result["data"]["analysis_summary"]["total_restaurants"] == 2
    
    @pytest.mark.asyncio
    async def test_search_and_recommend_workflow(self, mock_gateway):
        """Test complete search and recommend workflow."""
        # Search restaurants
        search_result = await mock_gateway.search_by_district(["Central district"])
        assert search_result["success"] is True
        
        # Get recommendations
        restaurants = search_result["data"]["restaurants"]
        recommend_result = await mock_gateway.get_recommendations(restaurants)
        assert recommend_result["success"] is True
        
        # Verify workflow
        assert mock_gateway.call_count == 2
        assert recommend_result["data"]["recommendation"]["name"] == "Restaurant 0"

class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test authentication error handling."""
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = Mock()
            mock_response.status = 401
            mock_response.json = AsyncMock(return_value={
                "success": False,
                "error": {
                    "type": "AuthenticationError",
                    "message": "Invalid JWT token"
                }
            })
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Test that authentication error is properly handled
            # Implementation would depend on actual client code
    
    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Test validation error handling."""
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = Mock()
            mock_response.status = 400
            mock_response.json = AsyncMock(return_value={
                "success": False,
                "error": {
                    "type": "ValidationError",
                    "message": "Invalid district names",
                    "details": {
                        "invalid_districts": ["NonExistent District"]
                    }
                }
            })
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Test validation error handling
    
    @pytest.mark.asyncio
    async def test_service_unavailable_retry(self):
        """Test service unavailable with retry logic."""
        call_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            if call_count < 3:
                mock_response.status = 503
                mock_response.json = AsyncMock(return_value={
                    "success": False,
                    "error": {
                        "type": "ServiceUnavailableError",
                        "message": "Service temporarily unavailable"
                    }
                })
            else:
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "success": True,
                    "data": {"restaurants": []}
                })
            
            return mock_response
        
        with patch('aiohttp.ClientSession.request', side_effect=mock_request):
            # Test retry logic implementation

class TestPerformanceOptimization:
    """Test performance optimization features."""
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self):
        """Test caching functionality."""
        from performance_optimization import InMemoryCache
        
        cache = InMemoryCache(default_ttl=1.0)  # 1 second TTL
        
        # Test cache set/get
        cache.set("test_key", {"data": "test"})
        result = cache.get("test_key")
        assert result == {"data": "test"}
        
        # Test TTL expiration
        await asyncio.sleep(1.1)
        expired_result = cache.get("test_key")
        assert expired_result is None
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing functionality."""
        from performance_optimization import BatchProcessor
        
        batch_processor = BatchProcessor(batch_size=3, batch_timeout=0.1)
        
        # Add requests to batch
        tasks = []
        for i in range(5):
            task = batch_processor.add_request("test_type", {"param": i})
            tasks.append(task)
        
        # Wait for batch processing
        # Implementation would depend on actual batch processor

class TestMobileIntegration:
    """Test mobile-specific integration features."""
    
    def test_offline_cache_behavior(self):
        """Test offline caching for mobile apps."""
        # Test AsyncStorage caching behavior
        pass
    
    def test_network_retry_mobile(self):
        """Test network retry logic for mobile networks."""
        # Test mobile-specific retry strategies
        pass

# Load testing
class TestLoadPerformance:
    """Load testing for performance validation."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_gateway):
        """Test handling of concurrent requests."""
        districts = ["Central district"]
        
        # Create 100 concurrent requests
        tasks = []
        for _ in range(100):
            task = mock_gateway.search_by_district(districts)
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        assert len(results) == 100
        assert all(result["success"] for result in results)
        assert mock_gateway.call_count == 100
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self):
        """Test rate limiting handling."""
        # Test rate limiting scenarios
        pass

# Integration test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test configuration
pytest_plugins = ["pytest_asyncio"]

# Run tests with: pytest test_integration.py -v
```

---

**Last Updated**: January 3, 2025  
**Version**: 1.0.0  
**Coverage**: Complete integration examples for Python, JavaScript/TypeScript, React, Node.js, Mobile, Foundation Models, Error Handling, Performance Optimization, and Testing