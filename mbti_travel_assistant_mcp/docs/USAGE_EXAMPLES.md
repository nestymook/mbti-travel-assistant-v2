# MBTI Travel Assistant MCP - Usage Examples

## Overview

This document provides comprehensive usage examples for integrating the MBTI Travel Assistant MCP into web applications. It includes sample code for different programming languages, error handling patterns, and retry logic implementations.

## Table of Contents

1. [JavaScript/Node.js Examples](#javascriptnodejs-examples)
2. [Python Examples](#python-examples)
3. [React Frontend Examples](#react-frontend-examples)
4. [Vue.js Frontend Examples](#vuejs-frontend-examples)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Retry Logic Examples](#retry-logic-examples)
7. [Authentication Examples](#authentication-examples)
8. [Caching Strategies](#caching-strategies)
9. [Performance Optimization](#performance-optimization)
10. [Testing Examples](#testing-examples)

## JavaScript/Node.js Examples

### Basic Client Setup

```javascript
const axios = require('axios');

class MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider) {
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'MBTITravelApp/1.0.0'
      }
    });
    
    this.authTokenProvider = authTokenProvider;
    this.setupInterceptors();
  }
  
  setupInterceptors() {
    // Request interceptor for authentication
    this.client.interceptors.request.use(async (config) => {
      const token = await this.authTokenProvider();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }
}
```
### Simple Restaurant Recommendation Request

```javascript
async function getRestaurantRecommendation(client, district, mealTime) {
  try {
    const response = await client.client.post('/invocations', {
      district: district,
      meal_time: mealTime
    });
    
    return response.data;
  } catch (error) {
    throw new Error(`Failed to get recommendation: ${error.message}`);
  }
}

// Usage example
const client = new MBTITravelAssistantClient(
  'https://your-agentcore-endpoint.amazonaws.com',
  () => getJWTToken() // Your token provider function
);

const recommendation = await getRestaurantRecommendation(
  client, 
  'Central district', 
  'breakfast'
);

console.log('Recommended restaurant:', recommendation.recommendation.name);
console.log('Alternative options:', recommendation.candidates.length);
```

### Natural Language Query Example

```javascript
async function searchWithNaturalLanguage(client, query) {
  try {
    const response = await client.client.post('/invocations', {
      natural_language_query: query
    });
    
    return response.data;
  } catch (error) {
    throw new Error(`Natural language search failed: ${error.message}`);
  }
}

// Usage examples
const queries = [
  "Find me a good breakfast place in Central with reasonable prices",
  "I want Italian food for dinner in Causeway Bay",
  "Show me lunch options near Admiralty that are highly rated",
  "Find vegetarian restaurants in Tsim Sha Tsui for dinner"
];

for (const query of queries) {
  try {
    const result = await searchWithNaturalLanguage(client, query);
    console.log(`Query: ${query}`);
    console.log(`Recommendation: ${result.recommendation?.name || 'None'}`);
    console.log(`Candidates: ${result.candidates.length}`);
    console.log('---');
  } catch (error) {
    console.error(`Query failed: ${query}`, error.message);
  }
}
```

### Advanced Request with User Context

```javascript
async function getPersonalizedRecommendation(client, request) {
  try {
    const response = await client.client.post('/invocations', {
      district: request.district,
      meal_time: request.mealTime,
      natural_language_query: request.query,
      user_context: {
        user_id: request.userId,
        preferences: request.preferences,
        dietary_restrictions: request.dietaryRestrictions,
        price_preference: request.pricePreference
      }
    });
    
    return response.data;
  } catch (error) {
    throw new Error(`Personalized recommendation failed: ${error.message}`);
  }
}

// Usage example
const personalizedRequest = {
  district: 'Central district',
  mealTime: 'lunch',
  query: 'Find me a healthy lunch option',
  userId: 'user123',
  preferences: {
    cuisine_types: ['Asian', 'Western'],
    ambiance: 'casual'
  },
  dietaryRestrictions: ['vegetarian'],
  pricePreference: '$$'
};

const personalizedResult = await getPersonalizedRecommendation(
  client, 
  personalizedRequest
);
```

## Python Examples

### Basic Python Client

```python
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RestaurantRecommendationRequest:
    district: Optional[str] = None
    meal_time: Optional[str] = None
    natural_language_query: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None

class MBTITravelAssistantClient:
    def __init__(self, base_url: str, auth_token_provider):
        self.base_url = base_url
        self.auth_token_provider = auth_token_provider
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with JWT token."""
        token = await self.auth_token_provider()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'MBTITravelApp-Python/1.0.0'
        }
    
    async def get_restaurant_recommendation(
        self, 
        request: RestaurantRecommendationRequest
    ) -> Dict[str, Any]:
        """Get restaurant recommendation from the API."""
        headers = await self.get_auth_headers()
        
        payload = {}
        if request.district:
            payload['district'] = request.district
        if request.meal_time:
            payload['meal_time'] = request.meal_time
        if request.natural_language_query:
            payload['natural_language_query'] = request.natural_language_query
        if request.user_context:
            payload['user_context'] = request.user_context
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f'{self.base_url}/invocations',
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(f"API Error {response.status}: {error_data}")

# Usage example
async def main():
    async def get_jwt_token():
        # Your JWT token retrieval logic
        return "your_jwt_token_here"
    
    client = MBTITravelAssistantClient(
        'https://your-agentcore-endpoint.amazonaws.com',
        get_jwt_token
    )
    
    # Simple district and meal time search
    request = RestaurantRecommendationRequest(
        district='Central district',
        meal_time='breakfast'
    )
    
    try:
        result = await client.get_restaurant_recommendation(request)
        print(f"Recommended: {result['recommendation']['name']}")
        print(f"Candidates: {len(result['candidates'])}")
        print(f"Processing time: {result['metadata']['processing_time_ms']}ms")
    except Exception as e:
        print(f"Error: {e}")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

### Python with Retry Logic

```python
import asyncio
import random
from typing import Optional, Callable, Any

class RetryableClient(MBTITravelAssistantClient):
    def __init__(self, base_url: str, auth_token_provider, max_retries: int = 3):
        super().__init__(base_url, auth_token_provider)
        self.max_retries = max_retries
    
    async def get_restaurant_recommendation_with_retry(
        self, 
        request: RestaurantRecommendationRequest
    ) -> Dict[str, Any]:
        """Get restaurant recommendation with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                return await self.get_restaurant_recommendation(request)
            except Exception as e:
                last_exception = e
                
                # Don't retry on client errors (4xx)
                if hasattr(e, 'status') and 400 <= e.status < 500:
                    raise e
                
                if attempt < self.max_retries:
                    # Exponential backoff with jitter
                    delay = min(2 ** (attempt - 1) + random.uniform(0, 1), 10)
                    print(f"Attempt {attempt} failed, retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    print(f"All {self.max_retries} attempts failed")
        
        raise last_exception

# Usage example with retry
async def example_with_retry():
    client = RetryableClient(
        'https://your-agentcore-endpoint.amazonaws.com',
        lambda: "your_jwt_token_here",
        max_retries=3
    )
    
    request = RestaurantRecommendationRequest(
        natural_language_query="Find me a good lunch place in Admiralty"
    )
    
    try:
        result = await client.get_restaurant_recommendation_with_retry(request)
        print("Success after retries:", result['recommendation']['name'])
    except Exception as e:
        print(f"Failed after all retries: {e}")
```

## React Frontend Examples

### React Hook for Restaurant Recommendations

```javascript
import { useState, useEffect, useCallback } from 'react';

// Custom hook for restaurant recommendations
function useRestaurantRecommendation() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchRecommendation = useCallback(async (request) => {
    setLoading(true);
    setError(null);
    
    try {
      const client = new MBTITravelAssistantClient(
        process.env.REACT_APP_API_BASE_URL,
        () => getAuthToken() // Your auth token provider
      );
      
      const result = await client.client.post('/invocations', request);
      setData(result.data);
    } catch (err) {
      setError(err.response?.data?.error || { message: err.message });
    } finally {
      setLoading(false);
    }
  }, []);
  
  return { data, loading, error, fetchRecommendation };
}

// Restaurant recommendation component
function RestaurantRecommendations() {
  const { data, loading, error, fetchRecommendation } = useRestaurantRecommendation();
  const [searchParams, setSearchParams] = useState({
    district: '',
    meal_time: '',
    natural_language_query: ''
  });
  
  const handleSearch = (e) => {
    e.preventDefault();
    
    const request = {};
    if (searchParams.district) request.district = searchParams.district;
    if (searchParams.meal_time) request.meal_time = searchParams.meal_time;
    if (searchParams.natural_language_query) {
      request.natural_language_query = searchParams.natural_language_query;
    }
    
    fetchRecommendation(request);
  };
  
  return (
    <div className="restaurant-recommendations">
      <form onSubmit={handleSearch} className="search-form">
        <div className="form-group">
          <label htmlFor="district">District:</label>
          <select
            id="district"
            value={searchParams.district}
            onChange={(e) => setSearchParams(prev => ({
              ...prev,
              district: e.target.value
            }))}
          >
            <option value="">Select District</option>
            <option value="Central district">Central</option>
            <option value="Admiralty">Admiralty</option>
            <option value="Causeway Bay">Causeway Bay</option>
            <option value="Tsim Sha Tsui">Tsim Sha Tsui</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="meal_time">Meal Time:</label>
          <select
            id="meal_time"
            value={searchParams.meal_time}
            onChange={(e) => setSearchParams(prev => ({
              ...prev,
              meal_time: e.target.value
            }))}
          >
            <option value="">Any Time</option>
            <option value="breakfast">Breakfast</option>
            <option value="lunch">Lunch</option>
            <option value="dinner">Dinner</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="query">Natural Language Query:</label>
          <input
            type="text"
            id="query"
            placeholder="e.g., Find me a good Italian restaurant"
            value={searchParams.natural_language_query}
            onChange={(e) => setSearchParams(prev => ({
              ...prev,
              natural_language_query: e.target.value
            }))}
          />
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Find Restaurants'}
        </button>
      </form>
      
      {error && (
        <div className="error-message">
          <h3>Error: {error.error_type || 'Unknown Error'}</h3>
          <p>{error.message}</p>
          {error.suggested_actions && (
            <ul>
              {error.suggested_actions.map((action, index) => (
                <li key={index}>{action}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      
      {data && (
        <div className="results">
          {data.recommendation && (
            <div className="recommendation">
              <h2>Recommended Restaurant</h2>
              <RestaurantCard restaurant={data.recommendation} isRecommended={true} />
            </div>
          )}
          
          {data.candidates && data.candidates.length > 0 && (
            <div className="candidates">
              <h3>Other Great Options</h3>
              <div className="restaurant-grid">
                {data.candidates.map(restaurant => (
                  <RestaurantCard 
                    key={restaurant.id} 
                    restaurant={restaurant} 
                    isRecommended={false} 
                  />
                ))}
              </div>
            </div>
          )}
          
          {data.metadata && (
            <div className="metadata">
              <p>Found {data.metadata.total_found} restaurants</p>
              <p>Processing time: {data.metadata.processing_time_ms}ms</p>
              {data.metadata.cache_hit && <p>✓ Served from cache</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Restaurant card component
function RestaurantCard({ restaurant, isRecommended }) {
  const formatOperatingHours = (hours) => {
    return Object.entries(hours).map(([day, times]) => (
      <div key={day} className="hours-day">
        <span className="day">{day.charAt(0).toUpperCase() + day.slice(1)}:</span>
        <span className="times">{times.join(', ')}</span>
      </div>
    ));
  };
  
  return (
    <div className={`restaurant-card ${isRecommended ? 'recommended' : ''}`}>
      {isRecommended && <div className="recommended-badge">Recommended</div>}
      
      <h3>{restaurant.name}</h3>
      <p className="address">{restaurant.address}</p>
      <p className="district">{restaurant.district}</p>
      
      <div className="meal-types">
        {restaurant.meal_type.map(type => (
          <span key={type} className="meal-type-tag">{type}</span>
        ))}
      </div>
      
      <div className="sentiment">
        <div className="sentiment-bar">
          <div 
            className="positive-bar" 
            style={{ width: `${restaurant.sentiment.positive_percentage}%` }}
          ></div>
        </div>
        <p>{restaurant.sentiment.positive_percentage.toFixed(1)}% positive 
           ({restaurant.sentiment.total_responses} reviews)</p>
      </div>
      
      <div className="price-range">
        <span className="price">{restaurant.price_range}</span>
        <span className="category">{restaurant.location_category}</span>
      </div>
      
      <div className="operating-hours">
        <h4>Operating Hours:</h4>
        {formatOperatingHours(restaurant.operating_hours)}
      </div>
      
      {restaurant.metadata && (
        <div className="additional-info">
          {restaurant.metadata.cuisine_type && (
            <p>Cuisine: {restaurant.metadata.cuisine_type}</p>
          )}
          {restaurant.metadata.rating && (
            <p>Rating: {restaurant.metadata.rating}/5 
               ({restaurant.metadata.review_count} reviews)</p>
          )}
        </div>
      )}
    </div>
  );
}

export default RestaurantRecommendations;
```

### React Context for API Client

```javascript
import React, { createContext, useContext, useMemo } from 'react';

// Create context for API client
const APIClientContext = createContext(null);

// Provider component
export function APIClientProvider({ children, baseURL, authTokenProvider }) {
  const client = useMemo(() => {
    return new MBTITravelAssistantClient(baseURL, authTokenProvider);
  }, [baseURL, authTokenProvider]);
  
  return (
    <APIClientContext.Provider value={client}>
      {children}
    </APIClientContext.Provider>
  );
}

// Hook to use API client
export function useAPIClient() {
  const client = useContext(APIClientContext);
  if (!client) {
    throw new Error('useAPIClient must be used within APIClientProvider');
  }
  return client;
}

// Usage in App component
function App() {
  const getAuthToken = useCallback(async () => {
    // Your authentication logic here
    return localStorage.getItem('jwt_token');
  }, []);
  
  return (
    <APIClientProvider 
      baseURL={process.env.REACT_APP_API_BASE_URL}
      authTokenProvider={getAuthToken}
    >
      <div className="App">
        <header className="App-header">
          <h1>MBTI Travel Assistant</h1>
        </header>
        <main>
          <RestaurantRecommendations />
        </main>
      </div>
    </APIClientProvider>
  );
}
```

## Vue.js Frontend Examples

### Vue 3 Composition API Example

```javascript
import { ref, reactive, computed } from 'vue';

// Composable for restaurant recommendations
export function useRestaurantRecommendation() {
  const data = ref(null);
  const loading = ref(false);
  const error = ref(null);
  
  const searchParams = reactive({
    district: '',
    meal_time: '',
    natural_language_query: ''
  });
  
  const hasValidParams = computed(() => {
    return searchParams.district || searchParams.natural_language_query;
  });
  
  const fetchRecommendation = async () => {
    if (!hasValidParams.value) {
      error.value = { message: 'Please provide either district or natural language query' };
      return;
    }
    
    loading.value = true;
    error.value = null;
    
    try {
      const client = new MBTITravelAssistantClient(
        process.env.VUE_APP_API_BASE_URL,
        () => getAuthToken()
      );
      
      const request = {};
      if (searchParams.district) request.district = searchParams.district;
      if (searchParams.meal_time) request.meal_time = searchParams.meal_time;
      if (searchParams.natural_language_query) {
        request.natural_language_query = searchParams.natural_language_query;
      }
      
      const response = await client.client.post('/invocations', request);
      data.value = response.data;
    } catch (err) {
      error.value = err.response?.data?.error || { message: err.message };
    } finally {
      loading.value = false;
    }
  };
  
  const clearResults = () => {
    data.value = null;
    error.value = null;
  };
  
  return {
    data,
    loading,
    error,
    searchParams,
    hasValidParams,
    fetchRecommendation,
    clearResults
  };
}
```

### Vue Component Template

```vue
<template>
  <div class="restaurant-recommendations">
    <form @submit.prevent="fetchRecommendation" class="search-form">
      <div class="form-group">
        <label for="district">District:</label>
        <select id="district" v-model="searchParams.district">
          <option value="">Select District</option>
          <option value="Central district">Central</option>
          <option value="Admiralty">Admiralty</option>
          <option value="Causeway Bay">Causeway Bay</option>
          <option value="Tsim Sha Tsui">Tsim Sha Tsui</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="meal_time">Meal Time:</label>
        <select id="meal_time" v-model="searchParams.meal_time">
          <option value="">Any Time</option>
          <option value="breakfast">Breakfast</option>
          <option value="lunch">Lunch</option>
          <option value="dinner">Dinner</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="query">Natural Language Query:</label>
        <input
          type="text"
          id="query"
          v-model="searchParams.natural_language_query"
          placeholder="e.g., Find me a good Italian restaurant"
        />
      </div>
      
      <button type="submit" :disabled="loading || !hasValidParams">
        {{ loading ? 'Searching...' : 'Find Restaurants' }}
      </button>
      
      <button type="button" @click="clearResults" v-if="data || error">
        Clear Results
      </button>
    </form>
    
    <!-- Error Display -->
    <div v-if="error" class="error-message">
      <h3>Error: {{ error.error_type || 'Unknown Error' }}</h3>
      <p>{{ error.message }}</p>
      <ul v-if="error.suggested_actions">
        <li v-for="action in error.suggested_actions" :key="action">
          {{ action }}
        </li>
      </ul>
    </div>
    
    <!-- Results Display -->
    <div v-if="data" class="results">
      <!-- Recommended Restaurant -->
      <div v-if="data.recommendation" class="recommendation">
        <h2>Recommended Restaurant</h2>
        <RestaurantCard :restaurant="data.recommendation" :is-recommended="true" />
      </div>
      
      <!-- Candidate Restaurants -->
      <div v-if="data.candidates && data.candidates.length > 0" class="candidates">
        <h3>Other Great Options</h3>
        <div class="restaurant-grid">
          <RestaurantCard
            v-for="restaurant in data.candidates"
            :key="restaurant.id"
            :restaurant="restaurant"
            :is-recommended="false"
          />
        </div>
      </div>
      
      <!-- Metadata -->
      <div v-if="data.metadata" class="metadata">
        <p>Found {{ data.metadata.total_found }} restaurants</p>
        <p>Processing time: {{ data.metadata.processing_time_ms }}ms</p>
        <p v-if="data.metadata.cache_hit">✓ Served from cache</p>
      </div>
    </div>
  </div>
</template>

<script>
import { useRestaurantRecommendation } from '@/composables/useRestaurantRecommendation';
import RestaurantCard from '@/components/RestaurantCard.vue';

export default {
  name: 'RestaurantRecommendations',
  components: {
    RestaurantCard
  },
  setup() {
    const {
      data,
      loading,
      error,
      searchParams,
      hasValidParams,
      fetchRecommendation,
      clearResults
    } = useRestaurantRecommendation();
    
    return {
      data,
      loading,
      error,
      searchParams,
      hasValidParams,
      fetchRecommendation,
      clearResults
    };
  }
};
</script>
```

## Error Handling Patterns

### Comprehensive Error Handler

```javascript
class APIErrorHandler {
  static handleError(error) {
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data;
      const errorInfo = errorData.error || {};
      
      switch (errorInfo.error_code) {
        case 'AUTH_FAILED':
          return this.handleAuthError(errorInfo);
        case 'VALIDATION_FAILED':
          return this.handleValidationError(errorInfo);
        case 'RATE_LIMIT_EXCEEDED':
          return this.handleRateLimitError(errorInfo);
        case 'MCP_SERVICE_UNAVAILABLE':
          return this.handleServiceUnavailableError(errorInfo);
        default:
          return this.handleGenericError(errorInfo);
      }
    } else if (error.request) {
      // Network error
      return {
        type: 'network_error',
        message: 'Network error - please check your connection',
        userMessage: 'Unable to connect to the service. Please check your internet connection.',
        retry: true
      };
    } else {
      // Request setup error
      return {
        type: 'client_error',
        message: error.message,
        userMessage: 'An unexpected error occurred. Please try again.',
        retry: false
      };
    }
  }
  
  static handleAuthError(errorInfo) {
    return {
      type: 'authentication_error',
      message: errorInfo.message,
      userMessage: 'Authentication failed. Please log in again.',
      retry: false,
      action: 'redirect_to_login'
    };
  }
  
  static handleValidationError(errorInfo) {
    return {
      type: 'validation_error',
      message: errorInfo.message,
      userMessage: 'Please check your input and try again.',
      retry: false,
      suggestedActions: errorInfo.suggested_actions
    };
  }
  
  static handleRateLimitError(errorInfo) {
    return {
      type: 'rate_limit_error',
      message: errorInfo.message,
      userMessage: 'Too many requests. Please wait a moment before trying again.',
      retry: true,
      retryAfter: 60 // seconds
    };
  }
  
  static handleServiceUnavailableError(errorInfo) {
    return {
      type: 'service_unavailable',
      message: errorInfo.message,
      userMessage: 'The restaurant service is temporarily unavailable. Please try again later.',
      retry: true,
      retryAfter: 30
    };
  }
  
  static handleGenericError(errorInfo) {
    return {
      type: 'generic_error',
      message: errorInfo.message || 'An unknown error occurred',
      userMessage: 'Something went wrong. Please try again.',
      retry: true
    };
  }
}

// Usage in client
class EnhancedMBTIClient extends MBTITravelAssistantClient {
  async getRestaurantRecommendationWithErrorHandling(request) {
    try {
      return await this.client.post('/invocations', request);
    } catch (error) {
      const handledError = APIErrorHandler.handleError(error);
      
      // Log error for monitoring
      console.error('API Error:', {
        type: handledError.type,
        message: handledError.message,
        originalError: error
      });
      
      // Throw enhanced error
      const enhancedError = new Error(handledError.userMessage);
      enhancedError.type = handledError.type;
      enhancedError.canRetry = handledError.retry;
      enhancedError.retryAfter = handledError.retryAfter;
      enhancedError.suggestedActions = handledError.suggestedActions;
      enhancedError.action = handledError.action;
      
      throw enhancedError;
    }
  }
}
```

## Retry Logic Examples

### Exponential Backoff with Jitter

```javascript
class RetryManager {
  constructor(maxRetries = 3, baseDelay = 1000, maxDelay = 10000) {
    this.maxRetries = maxRetries;
    this.baseDelay = baseDelay;
    this.maxDelay = maxDelay;
  }
  
  async executeWithRetry(operation, context = {}) {
    let lastError;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        
        // Don't retry on client errors (4xx) except 429
        if (error.response?.status >= 400 && 
            error.response?.status < 500 && 
            error.response?.status !== 429) {
          throw error;
        }
        
        if (attempt < this.maxRetries) {
          const delay = this.calculateDelay(attempt, error);
          console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`, {
            error: error.message,
            context
          });
          await this.sleep(delay);
        }
      }
    }
    
    console.error(`All ${this.maxRetries} attempts failed`, { 
      lastError: lastError.message,
      context 
    });
    throw lastError;
  }
  
  calculateDelay(attempt, error) {
    // Use server-provided retry-after if available
    if (error.response?.headers['retry-after']) {
      return parseInt(error.response.headers['retry-after']) * 1000;
    }
    
    // Exponential backoff with jitter
    const exponentialDelay = Math.min(
      this.baseDelay * Math.pow(2, attempt - 1),
      this.maxDelay
    );
    
    // Add jitter (±25%)
    const jitter = exponentialDelay * 0.25 * (Math.random() * 2 - 1);
    return Math.max(0, exponentialDelay + jitter);
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Usage with restaurant client
class ReliableMBTIClient extends MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider, retryConfig = {}) {
    super(baseURL, authTokenProvider);
    this.retryManager = new RetryManager(
      retryConfig.maxRetries || 3,
      retryConfig.baseDelay || 1000,
      retryConfig.maxDelay || 10000
    );
  }
  
  async getRestaurantRecommendationReliably(request) {
    return this.retryManager.executeWithRetry(
      () => this.client.post('/invocations', request),
      { request: JSON.stringify(request) }
    );
  }
}

// Example usage
const reliableClient = new ReliableMBTIClient(
  'https://your-endpoint.amazonaws.com',
  () => getAuthToken(),
  { maxRetries: 5, baseDelay: 500, maxDelay: 15000 }
);

try {
  const result = await reliableClient.getRestaurantRecommendationReliably({
    district: 'Central district',
    meal_time: 'lunch'
  });
  console.log('Success:', result.data);
} catch (error) {
  console.error('Failed after all retries:', error.message);
}
```

## Authentication Examples

### JWT Token Management

```javascript
class JWTTokenManager {
  constructor(cognitoConfig) {
    this.cognitoConfig = cognitoConfig;
    this.token = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
    this.refreshPromise = null;
  }
  
  async getValidToken() {
    // Return cached token if still valid
    if (this.token && this.isTokenValid()) {
      return this.token;
    }
    
    // If refresh is already in progress, wait for it
    if (this.refreshPromise) {
      return this.refreshPromise;
    }
    
    // Start token refresh
    this.refreshPromise = this.refreshTokenIfNeeded();
    
    try {
      const token = await this.refreshPromise;
      return token;
    } finally {
      this.refreshPromise = null;
    }
  }
  
  isTokenValid() {
    if (!this.token || !this.tokenExpiry) {
      return false;
    }
    
    // Check if token expires in the next 5 minutes
    const fiveMinutesFromNow = Date.now() + (5 * 60 * 1000);
    return this.tokenExpiry > fiveMinutesFromNow;
  }
  
  async refreshTokenIfNeeded() {
    if (this.refreshToken) {
      return this.refreshWithRefreshToken();
    } else {
      return this.authenticateUser();
    }
  }
  
  async refreshWithRefreshToken() {
    try {
      const response = await fetch(`${this.cognitoConfig.tokenEndpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'refresh_token',
          refresh_token: this.refreshToken,
          client_id: this.cognitoConfig.clientId
        })
      });
      
      if (!response.ok) {
        throw new Error('Token refresh failed');
      }
      
      const tokenData = await response.json();
      this.updateTokens(tokenData);
      return this.token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Fall back to full authentication
      return this.authenticateUser();
    }
  }
  
  async authenticateUser() {
    // Implement your authentication logic here
    // This could be OAuth flow, username/password, etc.
    throw new Error('User authentication required');
  }
  
  updateTokens(tokenData) {
    this.token = tokenData.access_token;
    this.refreshToken = tokenData.refresh_token || this.refreshToken;
    
    // Calculate expiry time
    if (tokenData.expires_in) {
      this.tokenExpiry = Date.now() + (tokenData.expires_in * 1000);
    }
    
    // Store tokens securely (consider using secure storage)
    localStorage.setItem('access_token', this.token);
    if (this.refreshToken) {
      localStorage.setItem('refresh_token', this.refreshToken);
    }
  }
  
  clearTokens() {
    this.token = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

// Usage with MBTI client
const tokenManager = new JWTTokenManager({
  tokenEndpoint: 'https://your-cognito-domain.auth.region.amazoncognito.com/oauth2/token',
  clientId: 'your-cognito-client-id'
});

const authenticatedClient = new MBTITravelAssistantClient(
  'https://your-endpoint.amazonaws.com',
  () => tokenManager.getValidToken()
);
```

## Caching Strategies

### Client-Side Caching

```javascript
class CachedMBTIClient extends MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider, cacheConfig = {}) {
    super(baseURL, authTokenProvider);
    this.cache = new Map();
    this.cacheTTL = cacheConfig.ttl || 5 * 60 * 1000; // 5 minutes default
    this.maxCacheSize = cacheConfig.maxSize || 100;
  }
  
  generateCacheKey(request) {
    // Create deterministic cache key from request parameters
    const keyParts = [
      request.district || 'any',
      request.meal_time || 'any',
      request.natural_language_query || 'none'
    ];
    return keyParts.join('|');
  }
  
  getCachedResponse(cacheKey) {
    const cached = this.cache.get(cacheKey);
    if (!cached) {
      return null;
    }
    
    // Check if cache entry is still valid
    if (Date.now() > cached.expiry) {
      this.cache.delete(cacheKey);
      return null;
    }
    
    return cached.data;
  }
  
  setCachedResponse(cacheKey, data) {
    // Implement LRU eviction if cache is full
    if (this.cache.size >= this.maxCacheSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(cacheKey, {
      data: data,
      expiry: Date.now() + this.cacheTTL,
      timestamp: Date.now()
    });
  }
  
  async getRestaurantRecommendationCached(request) {
    const cacheKey = this.generateCacheKey(request);
    
    // Try to get from cache first
    const cachedResponse = this.getCachedResponse(cacheKey);
    if (cachedResponse) {
      console.log('Cache hit for key:', cacheKey);
      return {
        data: cachedResponse,
        fromCache: true
      };
    }
    
    // Fetch from API
    console.log('Cache miss for key:', cacheKey);
    const response = await this.client.post('/invocations', request);
    
    // Cache successful responses only
    if (response.status === 200 && !response.data.error) {
      this.setCachedResponse(cacheKey, response.data);
    }
    
    return {
      data: response.data,
      fromCache: false
    };
  }
  
  clearCache() {
    this.cache.clear();
  }
  
  getCacheStats() {
    const entries = Array.from(this.cache.values());
    const now = Date.now();
    const validEntries = entries.filter(entry => entry.expiry > now);
    
    return {
      totalEntries: this.cache.size,
      validEntries: validEntries.length,
      expiredEntries: entries.length - validEntries.length,
      oldestEntry: entries.length > 0 ? Math.min(...entries.map(e => e.timestamp)) : null,
      newestEntry: entries.length > 0 ? Math.max(...entries.map(e => e.timestamp)) : null
    };
  }
}

// Usage example
const cachedClient = new CachedMBTIClient(
  'https://your-endpoint.amazonaws.com',
  () => getAuthToken(),
  { ttl: 10 * 60 * 1000, maxSize: 50 } // 10 minutes, max 50 entries
);

// Make requests
const result1 = await cachedClient.getRestaurantRecommendationCached({
  district: 'Central district',
  meal_time: 'breakfast'
});

// This will be served from cache
const result2 = await cachedClient.getRestaurantRecommendationCached({
  district: 'Central district',
  meal_time: 'breakfast'
});

console.log('Cache stats:', cachedClient.getCacheStats());
```

## Performance Optimization

### Request Batching

```javascript
class BatchedMBTIClient extends MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider, batchConfig = {}) {
    super(baseURL, authTokenProvider);
    this.batchSize = batchConfig.batchSize || 5;
    this.batchTimeout = batchConfig.batchTimeout || 100; // ms
    this.pendingRequests = [];
    this.batchTimer = null;
  }
  
  async getRestaurantRecommendationBatched(request) {
    return new Promise((resolve, reject) => {
      // Add request to pending batch
      this.pendingRequests.push({
        request,
        resolve,
        reject,
        timestamp: Date.now()
      });
      
      // Process batch if it's full
      if (this.pendingRequests.length >= this.batchSize) {
        this.processBatch();
      } else {
        // Set timer to process batch after timeout
        this.scheduleBatchProcessing();
      }
    });
  }
  
  scheduleBatchProcessing() {
    if (this.batchTimer) {
      return; // Timer already scheduled
    }
    
    this.batchTimer = setTimeout(() => {
      this.processBatch();
    }, this.batchTimeout);
  }
  
  async processBatch() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }
    
    if (this.pendingRequests.length === 0) {
      return;
    }
    
    const batch = this.pendingRequests.splice(0, this.batchSize);
    
    // Process requests in parallel
    const promises = batch.map(async ({ request, resolve, reject }) => {
      try {
        const response = await this.client.post('/invocations', request);
        resolve(response);
      } catch (error) {
        reject(error);
      }
    });
    
    // Wait for all requests in batch to complete
    await Promise.allSettled(promises);
    
    // Process remaining requests if any
    if (this.pendingRequests.length > 0) {
      this.scheduleBatchProcessing();
    }
  }
}
```

### Connection Pooling

```javascript
class PooledMBTIClient extends MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider, poolConfig = {}) {
    super(baseURL, authTokenProvider);
    
    // Configure axios with connection pooling
    this.client.defaults.httpAgent = new require('http').Agent({
      keepAlive: true,
      maxSockets: poolConfig.maxSockets || 10,
      maxFreeSockets: poolConfig.maxFreeSockets || 5,
      timeout: poolConfig.timeout || 60000,
      freeSocketTimeout: poolConfig.freeSocketTimeout || 30000
    });
    
    this.client.defaults.httpsAgent = new require('https').Agent({
      keepAlive: true,
      maxSockets: poolConfig.maxSockets || 10,
      maxFreeSockets: poolConfig.maxFreeSockets || 5,
      timeout: poolConfig.timeout || 60000,
      freeSocketTimeout: poolConfig.freeSocketTimeout || 30000
    });
  }
}
```

## Testing Examples

### Unit Tests with Jest

```javascript
// __tests__/mbti-client.test.js
import axios from 'axios';
import { MBTITravelAssistantClient } from '../src/mbti-client';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

describe('MBTITravelAssistantClient', () => {
  let client;
  let mockAuthTokenProvider;
  
  beforeEach(() => {
    mockAuthTokenProvider = jest.fn().mockResolvedValue('mock-jwt-token');
    client = new MBTITravelAssistantClient(
      'https://test-endpoint.com',
      mockAuthTokenProvider
    );
    
    // Reset axios mock
    mockedAxios.create.mockReturnValue({
      post: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
      }
    });
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  describe('getRestaurantRecommendation', () => {
    it('should make successful API call with district and meal_time', async () => {
      const mockResponse = {
        data: {
          recommendation: {
            id: 'rest_001',
            name: 'Test Restaurant',
            district: 'Central district'
          },
          candidates: [],
          metadata: {
            total_found: 1,
            processing_time_ms: 1000
          }
        }
      };
      
      client.client.post.mockResolvedValue(mockResponse);
      
      const result = await client.getRestaurantRecommendation({
        district: 'Central district',
        meal_time: 'breakfast'
      });
      
      expect(client.client.post).toHaveBeenCalledWith('/invocations', {
        district: 'Central district',
        meal_time: 'breakfast'
      });
      
      expect(result).toEqual(mockResponse.data);
    });
    
    it('should handle API errors gracefully', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              error_type: 'validation_error',
              message: 'Invalid district name',
              error_code: 'VALIDATION_FAILED'
            }
          }
        }
      };
      
      client.client.post.mockRejectedValue(mockError);
      
      await expect(client.getRestaurantRecommendation({
        district: 'Invalid District'
      })).rejects.toThrow('Failed to get recommendation');
    });
    
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      networkError.request = {};
      
      client.client.post.mockRejectedValue(networkError);
      
      await expect(client.getRestaurantRecommendation({
        district: 'Central district'
      })).rejects.toThrow('Failed to get recommendation');
    });
  });
  
  describe('authentication', () => {
    it('should call auth token provider', async () => {
      client.client.post.mockResolvedValue({ data: {} });
      
      await client.getRestaurantRecommendation({
        district: 'Central district'
      });
      
      expect(mockAuthTokenProvider).toHaveBeenCalled();
    });
  });
});
```

### Integration Tests

```javascript
// __tests__/integration.test.js
import { MBTITravelAssistantClient } from '../src/mbti-client';

describe('MBTI Travel Assistant Integration Tests', () => {
  let client;
  
  beforeAll(() => {
    // Use real endpoint for integration tests
    client = new MBTITravelAssistantClient(
      process.env.TEST_API_ENDPOINT || 'https://test-endpoint.com',
      () => process.env.TEST_JWT_TOKEN || 'test-token'
    );
  });
  
  describe('Restaurant Recommendations', () => {
    it('should get recommendations for Central district breakfast', async () => {
      const result = await client.getRestaurantRecommendation({
        district: 'Central district',
        meal_time: 'breakfast'
      });
      
      expect(result).toHaveProperty('recommendation');
      expect(result).toHaveProperty('candidates');
      expect(result).toHaveProperty('metadata');
      
      if (result.recommendation) {
        expect(result.recommendation).toHaveProperty('id');
        expect(result.recommendation).toHaveProperty('name');
        expect(result.recommendation).toHaveProperty('district');
      }
      
      expect(Array.isArray(result.candidates)).toBe(true);
      expect(result.candidates.length).toBeLessThanOrEqual(19);
      
      expect(result.metadata).toHaveProperty('processing_time_ms');
      expect(typeof result.metadata.processing_time_ms).toBe('number');
    }, 10000); // 10 second timeout
    
    it('should handle natural language queries', async () => {
      const result = await client.getRestaurantRecommendation({
        natural_language_query: 'Find me a good lunch place in Admiralty'
      });
      
      expect(result).toHaveProperty('recommendation');
      expect(result).toHaveProperty('candidates');
      expect(result.metadata.search_criteria).toHaveProperty('natural_language_query');
    }, 10000);
  });
  
  describe('Error Handling', () => {
    it('should handle validation errors', async () => {
      await expect(client.getRestaurantRecommendation({
        meal_time: 'invalid_meal'
      })).rejects.toThrow();
    });
    
    it('should handle empty requests', async () => {
      await expect(client.getRestaurantRecommendation({}))
        .rejects.toThrow();
    });
  });
});
```

### Performance Tests

```javascript
// __tests__/performance.test.js
import { MBTITravelAssistantClient } from '../src/mbti-client';

describe('Performance Tests', () => {
  let client;
  
  beforeAll(() => {
    client = new MBTITravelAssistantClient(
      process.env.TEST_API_ENDPOINT,
      () => process.env.TEST_JWT_TOKEN
    );
  });
  
  it('should respond within 5 seconds', async () => {
    const startTime = Date.now();
    
    await client.getRestaurantRecommendation({
      district: 'Central district',
      meal_time: 'lunch'
    });
    
    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(5000); // 5 seconds
  });
  
  it('should handle concurrent requests', async () => {
    const requests = Array.from({ length: 10 }, (_, i) => 
      client.getRestaurantRecommendation({
        district: 'Central district',
        meal_time: i % 2 === 0 ? 'breakfast' : 'lunch'
      })
    );
    
    const startTime = Date.now();
    const results = await Promise.all(requests);
    const totalTime = Date.now() - startTime;
    
    expect(results).toHaveLength(10);
    expect(totalTime).toBeLessThan(10000); // Should complete within 10 seconds
    
    // All requests should succeed
    results.forEach(result => {
      expect(result).toHaveProperty('metadata');
    });
  });
});
```

---

This comprehensive usage examples document provides practical implementation patterns for integrating the MBTI Travel Assistant MCP into various web applications, with proper error handling, retry logic, and performance optimization strategies.