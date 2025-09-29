# MBTI Travel Assistant - Usage Examples and Integration Guide

## Overview

This document provides comprehensive usage examples for integrating the MBTI Travel Assistant into web applications. The service generates complete 3-day travel itineraries based on MBTI personality types, including tourist spots and restaurant recommendations.

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
      timeout: 15000, // 15 seconds for itinerary generation
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

### Simple MBTI Itinerary Request

```javascript
async function generateMBTIItinerary(client, mbtiPersonality) {
  try {
    const response = await client.client.post('/invocations', {
      MBTI_personality: mbtiPersonality
    });
    
    return response.data;
  } catch (error) {
    throw new Error(`Failed to generate itinerary: ${error.message}`);
  }
}

// Usage example
const client = new MBTITravelAssistantClient(
  'https://your-agentcore-endpoint.amazonaws.com',
  () => getJWTToken() // Your token provider function
);

const itinerary = await generateMBTIItinerary(client, 'INFJ');

console.log('3-Day Itinerary Generated:');
console.log(`MBTI Type: ${itinerary.metadata.MBTI_personality}`);
console.log(`Processing Time: ${itinerary.metadata.processing_time_ms}ms`);
console.log(`Tourist Spots Found: ${itinerary.metadata.total_spots_found}`);
console.log(`Restaurants Found: ${itinerary.metadata.total_restaurants_found}`);

// Display day-by-day itinerary
Object.entries(itinerary.main_itinerary).forEach(([day, dayData]) => {
  console.log(`\n${day.toUpperCase()}:`);
  console.log(`  Morning: ${dayData.morning_session?.name} (MBTI Match: ${dayData.morning_session?.MBTI_match})`);
  console.log(`  Breakfast: ${dayData.breakfast?.name}`);
  console.log(`  Afternoon: ${dayData.afternoon_session?.name} (MBTI Match: ${dayData.afternoon_session?.MBTI_match})`);
  console.log(`  Lunch: ${dayData.lunch?.name}`);
  console.log(`  Night: ${dayData.night_session?.name} (MBTI Match: ${dayData.night_session?.MBTI_match})`);
  console.log(`  Dinner: ${dayData.dinner?.name}`);
});
```### 
Advanced Request with User Context

```javascript
async function generatePersonalizedItinerary(client, request) {
  try {
    const response = await client.client.post('/invocations', {
      MBTI_personality: request.mbtiPersonality,
      user_context: {
        user_id: request.userId,
        preferences: request.preferences
      }
    });
    
    return response.data;
  } catch (error) {
    throw new Error(`Personalized itinerary generation failed: ${error.message}`);
  }
}

// Usage example
const personalizedRequest = {
  mbtiPersonality: 'ENFP',
  userId: 'user123',
  preferences: {
    activity_level: 'high',
    cultural_interest: 'moderate',
    social_preference: 'group_activities'
  }
};

const personalizedItinerary = await generatePersonalizedItinerary(
  client, 
  personalizedRequest
);

console.log(`Personalized itinerary for ${personalizedRequest.mbtiPersonality}:`);
console.log(`Validation Status: ${personalizedItinerary.metadata.validation_status}`);
```

### Batch Processing Multiple MBTI Types

```javascript
async function generateMultipleMBTIItineraries(client, mbtiTypes) {
  const results = {};
  const errors = {};
  
  // Process in parallel with concurrency limit
  const concurrencyLimit = 3;
  const chunks = [];
  
  for (let i = 0; i < mbtiTypes.length; i += concurrencyLimit) {
    chunks.push(mbtiTypes.slice(i, i + concurrencyLimit));
  }
  
  for (const chunk of chunks) {
    const promises = chunk.map(async (mbtiType) => {
      try {
        const result = await generateMBTIItinerary(client, mbtiType);
        results[mbtiType] = result;
        console.log(`✓ Generated itinerary for ${mbtiType}`);
      } catch (error) {
        errors[mbtiType] = error.message;
        console.error(`✗ Failed to generate itinerary for ${mbtiType}: ${error.message}`);
      }
    });
    
    await Promise.all(promises);
    
    // Add delay between chunks to respect rate limits
    if (chunks.indexOf(chunk) < chunks.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  return { results, errors };
}

// Usage example
const mbtiTypes = ['INFJ', 'ENFP', 'INTJ', 'ESTP', 'ISFJ', 'ENTP'];
const batchResults = await generateMultipleMBTIItineraries(client, mbtiTypes);

console.log(`Successfully generated: ${Object.keys(batchResults.results).length} itineraries`);
console.log(`Failed: ${Object.keys(batchResults.errors).length} itineraries`);
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
class MBTIItineraryRequest:
    MBTI_personality: str
    user_context: Optional[Dict[str, Any]] = None

class MBTITravelAssistantClient:
    def __init__(self, base_url: str, auth_token_provider):
        self.base_url = base_url
        self.auth_token_provider = auth_token_provider
        self.timeout = aiohttp.ClientTimeout(total=15)  # 15 seconds for itinerary generation
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with JWT token."""
        token = await self.auth_token_provider()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'MBTITravelApp-Python/1.0.0'
        }
    
    async def generate_mbti_itinerary(
        self, 
        request: MBTIItineraryRequest
    ) -> Dict[str, Any]:
        """Generate 3-day MBTI-based itinerary."""
        headers = await self.get_auth_headers()
        
        payload = {
            'MBTI_personality': request.MBTI_personality
        }
        
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
    
    def validate_mbti_type(self, mbti_type: str) -> bool:
        """Validate MBTI personality type format."""
        valid_types = [
            'INTJ', 'INTP', 'ENTJ', 'ENTP',
            'INFJ', 'INFP', 'ENFJ', 'ENFP', 
            'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
            'ISTP', 'ISFP', 'ESTP', 'ESFP'
        ]
        return mbti_type.upper() in valid_types

# Usage example
async def main():
    async def get_jwt_token():
        # Your JWT token retrieval logic
        return "your_jwt_token_here"
    
    client = MBTITravelAssistantClient(
        'https://your-agentcore-endpoint.amazonaws.com',
        get_jwt_token
    )
    
    # Generate itinerary for INFJ personality
    request = MBTIItineraryRequest(
        MBTI_personality='INFJ',
        user_context={
            'user_id': 'user123',
            'preferences': {
                'cultural_interest': 'high',
                'social_preference': 'small_groups'
            }
        }
    )
    
    try:
        if not client.validate_mbti_type(request.MBTI_personality):
            raise ValueError(f"Invalid MBTI type: {request.MBTI_personality}")
        
        result = await client.generate_mbti_itinerary(request)
        
        print(f"Generated 3-day itinerary for {result['metadata']['MBTI_personality']}")
        print(f"Processing time: {result['metadata']['processing_time_ms']}ms")
        print(f"Tourist spots found: {result['metadata']['total_spots_found']}")
        print(f"Restaurants found: {result['metadata']['total_restaurants_found']}")
        
        # Display itinerary summary
        for day, day_data in result['main_itinerary'].items():
            print(f"\n{day.upper()}:")
            print(f"  Morning: {day_data['morning_session']['name']} "
                  f"(MBTI Match: {day_data['morning_session']['MBTI_match']})")
            print(f"  Breakfast: {day_data['breakfast']['name']}")
            print(f"  Afternoon: {day_data['afternoon_session']['name']} "
                  f"(MBTI Match: {day_data['afternoon_session']['MBTI_match']})")
            print(f"  Lunch: {day_data['lunch']['name']}")
            print(f"  Night: {day_data['night_session']['name']} "
                  f"(MBTI Match: {day_data['night_session']['MBTI_match']})")
            print(f"  Dinner: {day_data['dinner']['name']}")
            
        # Display candidate options
        if result.get('candidate_tourist_spots'):
            print(f"\nAlternative tourist spots available:")
            for day, candidates in result['candidate_tourist_spots'].items():
                print(f"  {day}: {len(candidates)} alternatives")
                
    except Exception as e:
        print(f"Error: {e}")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```#
## Python with Retry Logic and Error Handling

```python
import asyncio
import random
from typing import Optional, Callable, Any
import logging

class RetryableMBTIClient(MBTITravelAssistantClient):
    def __init__(self, base_url: str, auth_token_provider, max_retries: int = 3):
        super().__init__(base_url, auth_token_provider)
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
    
    async def generate_mbti_itinerary_with_retry(
        self, 
        request: MBTIItineraryRequest
    ) -> Dict[str, Any]:
        """Generate MBTI itinerary with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(f"Generating itinerary for {request.MBTI_personality}, attempt {attempt}")
                result = await self.generate_mbti_itinerary(request)
                
                # Log success metrics
                self.logger.info(f"Itinerary generated successfully: "
                               f"processing_time={result['metadata']['processing_time_ms']}ms, "
                               f"spots={result['metadata']['total_spots_found']}, "
                               f"restaurants={result['metadata']['total_restaurants_found']}")
                
                return result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt} failed: {str(e)}")
                
                # Don't retry on client errors (4xx) except auth failures
                if hasattr(e, 'status') and 400 <= e.status < 500 and e.status != 401:
                    self.logger.error(f"Client error, not retrying: {e}")
                    raise e
                
                if attempt < self.max_retries:
                    # Exponential backoff with jitter
                    delay = min(2 ** (attempt - 1) + random.uniform(0, 1), 10)
                    self.logger.info(f"Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_exception

# Usage example with comprehensive error handling
async def example_with_error_handling():
    logging.basicConfig(level=logging.INFO)
    
    client = RetryableMBTIClient(
        'https://your-agentcore-endpoint.amazonaws.com',
        lambda: "your_jwt_token_here",
        max_retries=3
    )
    
    mbti_types = ['INFJ', 'ENFP', 'INTJ', 'INVALID']  # Include invalid type for testing
    
    for mbti_type in mbti_types:
        request = MBTIItineraryRequest(MBTI_personality=mbti_type)
        
        try:
            if not client.validate_mbti_type(mbti_type):
                print(f"❌ Invalid MBTI type: {mbti_type}")
                continue
                
            result = await client.generate_mbti_itinerary_with_retry(request)
            
            print(f"✅ Success for {mbti_type}:")
            print(f"   Processing time: {result['metadata']['processing_time_ms']}ms")
            print(f"   Validation status: {result['metadata']['validation_status']}")
            
            # Check for partial failures
            if result.get('error'):
                print(f"   ⚠️  Partial failure: {result['error']['message']}")
            
        except Exception as e:
            print(f"❌ Failed for {mbti_type}: {str(e)}")

# Run error handling example
if __name__ == "__main__":
    asyncio.run(example_with_error_handling())
```

### Data Analysis and Insights

```python
import pandas as pd
from typing import List, Dict
import matplotlib.pyplot as plt
import seaborn as sns

class MBTIItineraryAnalyzer:
    def __init__(self, client: MBTITravelAssistantClient):
        self.client = client
    
    async def analyze_mbti_preferences(self, mbti_types: List[str]) -> Dict[str, Any]:
        """Analyze MBTI personality preferences across different types."""
        results = {}
        
        for mbti_type in mbti_types:
            try:
                request = MBTIItineraryRequest(MBTI_personality=mbti_type)
                result = await self.client.generate_mbti_itinerary(request)
                results[mbti_type] = result
            except Exception as e:
                print(f"Failed to analyze {mbti_type}: {e}")
        
        return self.extract_insights(results)
    
    def extract_insights(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Extract insights from MBTI itinerary results."""
        insights = {
            'processing_times': {},
            'mbti_match_rates': {},
            'location_categories': {},
            'district_preferences': {},
            'restaurant_sentiments': {}
        }
        
        for mbti_type, result in results.items():
            # Processing time analysis
            insights['processing_times'][mbti_type] = result['metadata']['processing_time_ms']
            
            # MBTI match rate analysis
            total_spots = 0
            matched_spots = 0
            
            for day_data in result['main_itinerary'].values():
                for session in ['morning_session', 'afternoon_session', 'night_session']:
                    if day_data.get(session):
                        total_spots += 1
                        if day_data[session].get('MBTI_match'):
                            matched_spots += 1
            
            insights['mbti_match_rates'][mbti_type] = matched_spots / total_spots if total_spots > 0 else 0
            
            # Location category analysis
            categories = {}
            districts = {}
            
            for day_data in result['main_itinerary'].values():
                for session in ['morning_session', 'afternoon_session', 'night_session']:
                    if day_data.get(session):
                        spot = day_data[session]
                        category = spot.get('location_category', 'Unknown')
                        district = spot.get('district', 'Unknown')
                        
                        categories[category] = categories.get(category, 0) + 1
                        districts[district] = districts.get(district, 0) + 1
            
            insights['location_categories'][mbti_type] = categories
            insights['district_preferences'][mbti_type] = districts
            
            # Restaurant sentiment analysis
            sentiments = []
            for day_data in result['main_itinerary'].values():
                for meal in ['breakfast', 'lunch', 'dinner']:
                    if day_data.get(meal) and day_data[meal].get('sentiment'):
                        sentiment = day_data[meal]['sentiment']
                        if sentiment.get('likes') and sentiment.get('dislikes'):
                            total = sentiment['likes'] + sentiment['dislikes'] + sentiment.get('neutral', 0)
                            positive_rate = sentiment['likes'] / total if total > 0 else 0
                            sentiments.append(positive_rate)
            
            insights['restaurant_sentiments'][mbti_type] = {
                'average_positive_rate': sum(sentiments) / len(sentiments) if sentiments else 0,
                'count': len(sentiments)
            }
        
        return insights
    
    def create_visualizations(self, insights: Dict[str, Any]):
        """Create visualizations for MBTI analysis."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Processing times
        mbti_types = list(insights['processing_times'].keys())
        processing_times = list(insights['processing_times'].values())
        
        axes[0, 0].bar(mbti_types, processing_times)
        axes[0, 0].set_title('Processing Times by MBTI Type')
        axes[0, 0].set_ylabel('Time (ms)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # MBTI match rates
        match_rates = [insights['mbti_match_rates'][mbti] * 100 for mbti in mbti_types]
        
        axes[0, 1].bar(mbti_types, match_rates)
        axes[0, 1].set_title('MBTI Match Rates')
        axes[0, 1].set_ylabel('Match Rate (%)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Restaurant sentiment analysis
        sentiment_data = []
        for mbti_type in mbti_types:
            sentiment_info = insights['restaurant_sentiments'][mbti_type]
            sentiment_data.append(sentiment_info['average_positive_rate'] * 100)
        
        axes[1, 0].bar(mbti_types, sentiment_data)
        axes[1, 0].set_title('Average Restaurant Sentiment by MBTI Type')
        axes[1, 0].set_ylabel('Positive Sentiment (%)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Location category distribution (for first MBTI type as example)
        if mbti_types:
            categories = insights['location_categories'][mbti_types[0]]
            axes[1, 1].pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
            axes[1, 1].set_title(f'Location Categories for {mbti_types[0]}')
        
        plt.tight_layout()
        plt.savefig('mbti_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

# Usage example
async def run_analysis():
    client = MBTITravelAssistantClient(
        'https://your-agentcore-endpoint.amazonaws.com',
        lambda: "your_jwt_token_here"
    )
    
    analyzer = MBTIItineraryAnalyzer(client)
    
    # Analyze different MBTI types
    mbti_types = ['INFJ', 'ENFP', 'INTJ', 'ESTP']
    insights = await analyzer.analyze_mbti_preferences(mbti_types)
    
    # Print insights
    print("MBTI Analysis Results:")
    print("=" * 50)
    
    for mbti_type in mbti_types:
        print(f"\n{mbti_type}:")
        print(f"  Processing time: {insights['processing_times'][mbti_type]}ms")
        print(f"  MBTI match rate: {insights['mbti_match_rates'][mbti_type]:.1%}")
        print(f"  Restaurant sentiment: {insights['restaurant_sentiments'][mbti_type]['average_positive_rate']:.1%}")
        
        top_categories = sorted(
            insights['location_categories'][mbti_type].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        print(f"  Top location categories: {', '.join([f'{cat}({count})' for cat, count in top_categories])}")
    
    # Create visualizations
    analyzer.create_visualizations(insights)

if __name__ == "__main__":
    asyncio.run(run_analysis())
```#
# React Frontend Examples

### React Hook for MBTI Itinerary Generation

```javascript
import { useState, useEffect, useCallback } from 'react';

// Custom hook for MBTI itinerary generation
function useMBTIItinerary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const generateItinerary = useCallback(async (mbtiPersonality, userContext = null) => {
    setLoading(true);
    setError(null);
    
    try {
      const client = new MBTITravelAssistantClient(
        process.env.REACT_APP_API_BASE_URL,
        () => getAuthToken() // Your auth token provider
      );
      
      const request = {
        MBTI_personality: mbtiPersonality
      };
      
      if (userContext) {
        request.user_context = userContext;
      }
      
      const result = await client.client.post('/invocations', request);
      setData(result.data);
    } catch (err) {
      setError(err.response?.data?.error || { message: err.message });
    } finally {
      setLoading(false);
    }
  }, []);
  
  const clearItinerary = useCallback(() => {
    setData(null);
    setError(null);
  }, []);
  
  return { data, loading, error, generateItinerary, clearItinerary };
}

// MBTI Itinerary Planner Component
function MBTIItineraryPlanner() {
  const { data, loading, error, generateItinerary, clearItinerary } = useMBTIItinerary();
  const [selectedMBTI, setSelectedMBTI] = useState('');
  const [userPreferences, setUserPreferences] = useState({
    activity_level: 'moderate',
    cultural_interest: 'moderate',
    social_preference: 'mixed'
  });
  
  const mbtiTypes = [
    { value: 'INFJ', label: 'INFJ - The Advocate', description: 'Quiet, mystical, inspiring' },
    { value: 'ENFP', label: 'ENFP - The Campaigner', description: 'Enthusiastic, creative, sociable' },
    { value: 'INTJ', label: 'INTJ - The Architect', description: 'Imaginative, strategic thinkers' },
    { value: 'ESTP', label: 'ESTP - The Entrepreneur', description: 'Smart, energetic, perceptive' },
    { value: 'ISFJ', label: 'ISFJ - The Protector', description: 'Warm-hearted, conscientious' },
    { value: 'ENTP', label: 'ENTP - The Debater', description: 'Smart, curious thinkers' },
    { value: 'ISTJ', label: 'ISTJ - The Logistician', description: 'Practical, fact-minded, reliable' },
    { value: 'ESFP', label: 'ESFP - The Entertainer', description: 'Spontaneous, energetic, enthusiastic' }
  ];
  
  const handleGenerateItinerary = (e) => {
    e.preventDefault();
    
    if (!selectedMBTI) {
      alert('Please select your MBTI personality type');
      return;
    }
    
    const userContext = {
      user_id: 'demo_user',
      preferences: userPreferences
    };
    
    generateItinerary(selectedMBTI, userContext);
  };
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <h2>Generating your personalized 3-day Hong Kong itinerary...</h2>
        <p>This may take up to 10 seconds as we match your {selectedMBTI} personality with the perfect spots!</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="error-container">
        <h2>Oops! Something went wrong</h2>
        <div className="error-details">
          <h3>Error: {error.error_type || 'Unknown Error'}</h3>
          <p>{error.message}</p>
          {error.suggested_actions && (
            <div className="suggested-actions">
              <h4>What you can try:</h4>
              <ul>
                {error.suggested_actions.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <button onClick={clearItinerary} className="retry-button">
          Try Again
        </button>
      </div>
    );
  }
  
  if (data) {
    return <ItineraryDisplay data={data} onBack={clearItinerary} />;
  }
  
  return (
    <div className="mbti-planner">
      <header className="planner-header">
        <h1>MBTI Travel Assistant</h1>
        <p>Get a personalized 3-day Hong Kong itinerary based on your personality type</p>
      </header>
      
      <form onSubmit={handleGenerateItinerary} className="planner-form">
        <div className="form-section">
          <h2>Select Your MBTI Personality Type</h2>
          <div className="mbti-grid">
            {mbtiTypes.map(type => (
              <label key={type.value} className="mbti-option">
                <input
                  type="radio"
                  name="mbti"
                  value={type.value}
                  checked={selectedMBTI === type.value}
                  onChange={(e) => setSelectedMBTI(e.target.value)}
                />
                <div className="mbti-card">
                  <h3>{type.label}</h3>
                  <p>{type.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
        
        <div className="form-section">
          <h2>Customize Your Preferences</h2>
          
          <div className="preference-group">
            <label htmlFor="activity_level">Activity Level:</label>
            <select
              id="activity_level"
              value={userPreferences.activity_level}
              onChange={(e) => setUserPreferences(prev => ({
                ...prev,
                activity_level: e.target.value
              }))}
            >
              <option value="low">Low - Relaxed pace</option>
              <option value="moderate">Moderate - Balanced</option>
              <option value="high">High - Action-packed</option>
            </select>
          </div>
          
          <div className="preference-group">
            <label htmlFor="cultural_interest">Cultural Interest:</label>
            <select
              id="cultural_interest"
              value={userPreferences.cultural_interest}
              onChange={(e) => setUserPreferences(prev => ({
                ...prev,
                cultural_interest: e.target.value
              }))}
            >
              <option value="low">Low - Modern attractions</option>
              <option value="moderate">Moderate - Mix of old and new</option>
              <option value="high">High - Traditional culture focus</option>
            </select>
          </div>
          
          <div className="preference-group">
            <label htmlFor="social_preference">Social Preference:</label>
            <select
              id="social_preference"
              value={userPreferences.social_preference}
              onChange={(e) => setUserPreferences(prev => ({
                ...prev,
                social_preference: e.target.value
              }))}
            >
              <option value="solo">Solo - Quiet, personal experiences</option>
              <option value="small_groups">Small Groups - Intimate settings</option>
              <option value="mixed">Mixed - Variety of social settings</option>
              <option value="crowds">Crowds - Bustling, energetic places</option>
            </select>
          </div>
        </div>
        
        <button type="submit" className="generate-button" disabled={!selectedMBTI}>
          Generate My 3-Day Itinerary
        </button>
      </form>
    </div>
  );
}

// Itinerary Display Component
function ItineraryDisplay({ data, onBack }) {
  const [selectedDay, setSelectedDay] = useState('day_1');
  const [showAlternatives, setShowAlternatives] = useState(false);
  
  const dayLabels = {
    day_1: 'Day 1',
    day_2: 'Day 2', 
    day_3: 'Day 3'
  };
  
  return (
    <div className="itinerary-display">
      <header className="itinerary-header">
        <button onClick={onBack} className="back-button">← Back to Planner</button>
        <div className="itinerary-title">
          <h1>Your {data.metadata.MBTI_personality} 3-Day Hong Kong Adventure</h1>
          <div className="itinerary-stats">
            <span>Generated in {data.metadata.processing_time_ms}ms</span>
            <span>{data.metadata.total_spots_found} spots found</span>
            <span>{data.metadata.total_restaurants_found} restaurants found</span>
            <span className={`validation-${data.metadata.validation_status}`}>
              {data.metadata.validation_status}
            </span>
          </div>
        </div>
      </header>
      
      <nav className="day-navigation">
        {Object.keys(dayLabels).map(day => (
          <button
            key={day}
            className={`day-tab ${selectedDay === day ? 'active' : ''}`}
            onClick={() => setSelectedDay(day)}
          >
            {dayLabels[day]}
          </button>
        ))}
        <button
          className={`alternatives-toggle ${showAlternatives ? 'active' : ''}`}
          onClick={() => setShowAlternatives(!showAlternatives)}
        >
          {showAlternatives ? 'Hide' : 'Show'} Alternatives
        </button>
      </nav>
      
      <div className="day-content">
        <DayItinerary 
          day={selectedDay}
          dayData={data.main_itinerary[selectedDay]}
          alternatives={showAlternatives ? {
            spots: data.candidate_tourist_spots?.[selectedDay] || [],
            restaurants: data.candidate_restaurants?.[selectedDay] || {}
          } : null}
        />
      </div>
    </div>
  );
}

// Day Itinerary Component
function DayItinerary({ day, dayData, alternatives }) {
  const sessions = [
    { key: 'morning_session', label: 'Morning', meal: 'breakfast', time: '07:00 - 11:59' },
    { key: 'afternoon_session', label: 'Afternoon', meal: 'lunch', time: '12:00 - 17:59' },
    { key: 'night_session', label: 'Night', meal: 'dinner', time: '18:00 - 23:59' }
  ];
  
  return (
    <div className="day-itinerary">
      {sessions.map(session => (
        <div key={session.key} className="session-block">
          <div className="session-header">
            <h2>{session.label} Session</h2>
            <span className="session-time">{session.time}</span>
          </div>
          
          <div className="session-content">
            <div className="tourist-spot">
              <TouristSpotCard spot={dayData[session.key]} />
            </div>
            
            <div className="restaurant">
              <RestaurantCard restaurant={dayData[session.meal]} mealType={session.meal} />
            </div>
          </div>
          
          {alternatives && (
            <div className="alternatives-section">
              <h3>Alternative Options</h3>
              
              {alternatives.spots.length > 0 && (
                <div className="alternative-spots">
                  <h4>Tourist Spots:</h4>
                  <div className="alternatives-grid">
                    {alternatives.spots.slice(0, 3).map(spot => (
                      <TouristSpotCard key={spot.id} spot={spot} isAlternative={true} />
                    ))}
                  </div>
                </div>
              )}
              
              {alternatives.restaurants[session.meal] && alternatives.restaurants[session.meal].length > 0 && (
                <div className="alternative-restaurants">
                  <h4>Restaurants:</h4>
                  <div className="alternatives-grid">
                    {alternatives.restaurants[session.meal].slice(0, 3).map(restaurant => (
                      <RestaurantCard 
                        key={restaurant.id} 
                        restaurant={restaurant} 
                        mealType={session.meal}
                        isAlternative={true}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// Tourist Spot Card Component
function TouristSpotCard({ spot, isAlternative = false }) {
  if (!spot) return <div className="spot-card empty">No spot assigned</div>;
  
  return (
    <div className={`spot-card ${isAlternative ? 'alternative' : ''}`}>
      <div className="spot-header">
        <h3>{spot.name}</h3>
        {spot.MBTI_match && (
          <span className="mbti-match-badge">✨ Perfect Match</span>
        )}
      </div>
      
      <p className="spot-description">{spot.description}</p>
      
      <div className="spot-details">
        <div className="detail-item">
          <strong>Address:</strong> {spot.address}
        </div>
        <div className="detail-item">
          <strong>District:</strong> {spot.district}
        </div>
        <div className="detail-item">
          <strong>Category:</strong> {spot.location_category}
        </div>
        <div className="detail-item">
          <strong>Hours:</strong> {spot.operating_hours}
        </div>
        <div className="detail-item">
          <strong>Days:</strong> {spot.operating_days}
        </div>
      </div>
    </div>
  );
}

// Restaurant Card Component
function RestaurantCard({ restaurant, mealType, isAlternative = false }) {
  if (!restaurant) return <div className="restaurant-card empty">No restaurant assigned</div>;
  
  const formatOperatingHours = (hours) => {
    if (!hours) return 'Hours not available';
    
    const today = new Date().toLocaleLowerCase().slice(0, 3) + 
                  new Date().toLocaleLowerCase().slice(3);
    const todayHours = hours[today] || hours[Object.keys(hours)[0]];
    
    return todayHours ? todayHours.join(', ') : 'Closed today';
  };
  
  const getSentimentColor = (sentiment) => {
    if (!sentiment) return '#gray';
    
    const total = sentiment.likes + sentiment.dislikes + (sentiment.neutral || 0);
    const positiveRate = sentiment.likes / total;
    
    if (positiveRate >= 0.8) return '#4CAF50';
    if (positiveRate >= 0.6) return '#FFC107';
    return '#FF5722';
  };
  
  return (
    <div className={`restaurant-card ${isAlternative ? 'alternative' : ''}`}>
      <div className="restaurant-header">
        <h3>{restaurant.name}</h3>
        <span className="meal-type-badge">{mealType}</span>
      </div>
      
      <div className="restaurant-details">
        <div className="detail-item">
          <strong>Address:</strong> {restaurant.address}
        </div>
        <div className="detail-item">
          <strong>District:</strong> {restaurant.district}
        </div>
        <div className="detail-item">
          <strong>Hours Today:</strong> {formatOperatingHours(restaurant.operating_hours)}
        </div>
      </div>
      
      {restaurant.sentiment && (
        <div className="sentiment-section">
          <div className="sentiment-bar">
            <div 
              className="sentiment-fill"
              style={{ 
                width: `${(restaurant.sentiment.likes / (restaurant.sentiment.likes + restaurant.sentiment.dislikes + (restaurant.sentiment.neutral || 0))) * 100}%`,
                backgroundColor: getSentimentColor(restaurant.sentiment)
              }}
            ></div>
          </div>
          <div className="sentiment-stats">
            <span className="likes">{restaurant.sentiment.likes} likes</span>
            <span className="dislikes">{restaurant.sentiment.dislikes} dislikes</span>
            {restaurant.sentiment.neutral > 0 && (
              <span className="neutral">{restaurant.sentiment.neutral} neutral</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default MBTIItineraryPlanner;
```##
 Error Handling Patterns

### Comprehensive Error Handler for MBTI Itinerary Generation

```javascript
class MBTIAPIErrorHandler {
  static handleError(error) {
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data;
      const errorInfo = errorData.error || {};
      
      switch (errorInfo.error_code) {
        case 'VALIDATION_FAILED':
          return this.handleValidationError(errorInfo);
        case 'AUTH_FAILED':
          return this.handleAuthError(errorInfo);
        case 'KNOWLEDGE_BASE_UNAVAILABLE':
          return this.handleKnowledgeBaseError(errorInfo);
        case 'MCP_SERVICE_UNAVAILABLE':
          return this.handleMCPServiceError(errorInfo, errorData);
        case 'SESSION_ASSIGNMENT_FAILED':
          return this.handleSessionAssignmentError(errorInfo);
        case 'RESTAURANT_ASSIGNMENT_FAILED':
          return this.handleRestaurantAssignmentError(errorInfo);
        default:
          return this.handleGenericError(errorInfo);
      }
    } else if (error.request) {
      // Network error
      return {
        type: 'network_error',
        message: 'Network error - please check your connection',
        userMessage: 'Unable to connect to the travel planning service. Please check your internet connection.',
        retry: true,
        retryAfter: 5
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
  
  static handleValidationError(errorInfo) {
    return {
      type: 'validation_error',
      message: errorInfo.message,
      userMessage: 'Please check your MBTI personality type and try again.',
      retry: false,
      suggestedActions: [
        'Ensure you selected a valid MBTI type (e.g., INFJ, ENFP)',
        'Check that the MBTI type is exactly 4 characters',
        'Try selecting from the provided list of MBTI types'
      ]
    };
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
  
  static handleKnowledgeBaseError(errorInfo) {
    return {
      type: 'knowledge_base_error',
      message: errorInfo.message,
      userMessage: 'The travel database is temporarily unavailable. Please try again in a few minutes.',
      retry: true,
      retryAfter: 60,
      suggestedActions: [
        'Wait a few minutes and try again',
        'Check if the service status page shows any issues',
        'Try a different MBTI personality type'
      ]
    };
  }
  
  static handleMCPServiceError(errorInfo, errorData) {
    // Check if we have partial success (tourist spots but no restaurants)
    const hasPartialItinerary = errorData.main_itinerary && 
      Object.keys(errorData.main_itinerary).length > 0;
    
    return {
      type: 'mcp_service_error',
      message: errorInfo.message,
      userMessage: hasPartialItinerary 
        ? 'Your itinerary was generated, but restaurant recommendations are temporarily unavailable.'
        : 'Restaurant service is temporarily unavailable. Please try again later.',
      retry: true,
      retryAfter: 30,
      partialSuccess: hasPartialItinerary,
      data: hasPartialItinerary ? errorData : null,
      suggestedActions: [
        hasPartialItinerary 
          ? 'You can still use the tourist spot recommendations'
          : 'Try again in a few minutes',
        'Check the service status page',
        'Consider using the alternative spots provided'
      ]
    };
  }
  
  static handleSessionAssignmentError(errorInfo) {
    return {
      type: 'session_assignment_error',
      message: errorInfo.message,
      userMessage: 'Unable to create a complete 3-day itinerary for your personality type.',
      retry: true,
      retryAfter: 10,
      suggestedActions: [
        'Try again - the system may find different available spots',
        'Consider trying a different MBTI personality type',
        'Check back later when more tourist spots may be available'
      ]
    };
  }
  
  static handleRestaurantAssignmentError(errorInfo) {
    return {
      type: 'restaurant_assignment_error',
      message: errorInfo.message,
      userMessage: 'Tourist spots were assigned successfully, but restaurant recommendations failed.',
      retry: true,
      retryAfter: 15,
      partialSuccess: true,
      suggestedActions: [
        'You can still use the tourist spot recommendations',
        'Try generating the itinerary again for restaurant suggestions',
        'Manually search for restaurants in the recommended districts'
      ]
    };
  }
  
  static handleGenericError(errorInfo) {
    return {
      type: 'generic_error',
      message: errorInfo.message || 'An unknown error occurred',
      userMessage: 'Something went wrong while generating your itinerary. Please try again.',
      retry: true,
      retryAfter: 10
    };
  }
}

// Enhanced client with error handling
class EnhancedMBTIClient extends MBTITravelAssistantClient {
  async generateItineraryWithErrorHandling(mbtiPersonality, userContext = null) {
    try {
      const request = { MBTI_personality: mbtiPersonality };
      if (userContext) request.user_context = userContext;
      
      const response = await this.client.post('/invocations', request);
      return { success: true, data: response.data };
      
    } catch (error) {
      const handledError = MBTIAPIErrorHandler.handleError(error);
      
      // Log error for monitoring
      console.error('MBTI Itinerary Generation Error:', {
        type: handledError.type,
        message: handledError.message,
        mbtiPersonality,
        timestamp: new Date().toISOString()
      });
      
      return {
        success: false,
        error: handledError,
        partialData: handledError.data || null
      };
    }
  }
}

// Usage example with comprehensive error handling
async function generateItineraryWithHandling(mbtiPersonality) {
  const client = new EnhancedMBTIClient(
    'https://your-agentcore-endpoint.amazonaws.com',
    () => getJWTToken()
  );
  
  const result = await client.generateItineraryWithErrorHandling(mbtiPersonality);
  
  if (result.success) {
    console.log('✅ Itinerary generated successfully');
    displayItinerary(result.data);
  } else {
    console.error('❌ Error generating itinerary:', result.error.userMessage);
    
    // Handle partial success
    if (result.error.partialSuccess && result.partialData) {
      console.log('⚠️ Showing partial results');
      displayPartialItinerary(result.partialData);
    }
    
    // Handle retry logic
    if (result.error.retry) {
      console.log(`🔄 Will retry in ${result.error.retryAfter} seconds`);
      setTimeout(() => {
        generateItineraryWithHandling(mbtiPersonality);
      }, result.error.retryAfter * 1000);
    }
    
    // Handle specific actions
    if (result.error.action === 'redirect_to_login') {
      window.location.href = '/login';
    }
    
    // Show suggested actions to user
    if (result.error.suggestedActions) {
      console.log('💡 Suggested actions:');
      result.error.suggestedActions.forEach(action => {
        console.log(`  - ${action}`);
      });
    }
  }
}
```

## Retry Logic Examples

### Advanced Retry Manager with Circuit Breaker

```javascript
class MBTIRetryManager {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 3;
    this.baseDelay = options.baseDelay || 1000;
    this.maxDelay = options.maxDelay || 10000;
    this.backoffMultiplier = options.backoffMultiplier || 2;
    this.jitterMax = options.jitterMax || 1000;
    
    // Circuit breaker state
    this.circuitBreakerState = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.failureCount = 0;
    this.failureThreshold = options.failureThreshold || 5;
    this.recoveryTimeout = options.recoveryTimeout || 60000; // 1 minute
    this.lastFailureTime = null;
  }
  
  async executeWithRetry(operation, context = {}) {
    // Check circuit breaker
    if (this.circuitBreakerState === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.recoveryTimeout) {
        this.circuitBreakerState = 'HALF_OPEN';
        console.log('Circuit breaker moving to HALF_OPEN state');
      } else {
        throw new Error('Circuit breaker is OPEN - service temporarily unavailable');
      }
    }
    
    let lastError;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const result = await operation();
        
        // Success - reset circuit breaker
        if (this.circuitBreakerState === 'HALF_OPEN') {
          this.circuitBreakerState = 'CLOSED';
          this.failureCount = 0;
          console.log('Circuit breaker reset to CLOSED state');
        }
        
        return result;
        
      } catch (error) {
        lastError = error;
        this.recordFailure();
        
        // Don't retry on client errors (4xx) except 429 and 401
        if (error.response?.status >= 400 && 
            error.response?.status < 500 && 
            ![401, 429].includes(error.response?.status)) {
          throw error;
        }
        
        if (attempt < this.maxRetries && this.circuitBreakerState !== 'OPEN') {
          const delay = this.calculateDelay(attempt, error);
          console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`, {
            error: error.message,
            context,
            circuitBreakerState: this.circuitBreakerState
          });
          await this.sleep(delay);
        }
      }
    }
    
    console.error(`All ${this.maxRetries} attempts failed`, { 
      lastError: lastError.message,
      context,
      circuitBreakerState: this.circuitBreakerState
    });
    
    throw lastError;
  }
  
  recordFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.failureCount >= this.failureThreshold) {
      this.circuitBreakerState = 'OPEN';
      console.warn(`Circuit breaker opened after ${this.failureCount} failures`);
    }
  }
  
  calculateDelay(attempt, error) {
    // Use server-provided retry-after if available
    if (error.response?.headers['retry-after']) {
      return parseInt(error.response.headers['retry-after']) * 1000;
    }
    
    // Exponential backoff with jitter
    const exponentialDelay = Math.min(
      this.baseDelay * Math.pow(this.backoffMultiplier, attempt - 1),
      this.maxDelay
    );
    
    const jitter = Math.random() * this.jitterMax;
    return exponentialDelay + jitter;
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  getCircuitBreakerStatus() {
    return {
      state: this.circuitBreakerState,
      failureCount: this.failureCount,
      lastFailureTime: this.lastFailureTime,
      timeUntilRecovery: this.circuitBreakerState === 'OPEN' 
        ? Math.max(0, this.recoveryTimeout - (Date.now() - this.lastFailureTime))
        : 0
    };
  }
}

// Usage with MBTI client
class ResilientMBTIClient extends MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider, retryOptions = {}) {
    super(baseURL, authTokenProvider);
    this.retryManager = new MBTIRetryManager(retryOptions);
  }
  
  async generateItineraryWithResilience(mbtiPersonality, userContext = null) {
    const operation = async () => {
      const request = { MBTI_personality: mbtiPersonality };
      if (userContext) request.user_context = userContext;
      
      const response = await this.client.post('/invocations', request);
      return response.data;
    };
    
    const context = {
      mbtiPersonality,
      hasUserContext: !!userContext,
      timestamp: new Date().toISOString()
    };
    
    return await this.retryManager.executeWithRetry(operation, context);
  }
  
  getServiceHealth() {
    return {
      circuitBreaker: this.retryManager.getCircuitBreakerStatus(),
      lastRequestTime: this.lastRequestTime,
      totalRequests: this.totalRequests || 0,
      successfulRequests: this.successfulRequests || 0
    };
  }
}

// Example usage with monitoring
async function demonstrateResilientClient() {
  const client = new ResilientMBTIClient(
    'https://your-agentcore-endpoint.amazonaws.com',
    () => getJWTToken(),
    {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      failureThreshold: 3,
      recoveryTimeout: 30000 // 30 seconds for demo
    }
  );
  
  const mbtiTypes = ['INFJ', 'ENFP', 'INTJ'];
  
  for (const mbtiType of mbtiTypes) {
    try {
      console.log(`\n🚀 Generating itinerary for ${mbtiType}...`);
      
      const startTime = Date.now();
      const result = await client.generateItineraryWithResilience(mbtiType);
      const endTime = Date.now();
      
      console.log(`✅ Success for ${mbtiType}:`);
      console.log(`   Processing time: ${result.metadata.processing_time_ms}ms`);
      console.log(`   Total request time: ${endTime - startTime}ms`);
      console.log(`   Validation status: ${result.metadata.validation_status}`);
      
      // Show service health
      const health = client.getServiceHealth();
      console.log(`   Circuit breaker: ${health.circuitBreaker.state}`);
      
    } catch (error) {
      console.error(`❌ Failed for ${mbtiType}: ${error.message}`);
      
      // Show circuit breaker status on failure
      const health = client.getServiceHealth();
      console.log(`   Circuit breaker: ${health.circuitBreaker.state}`);
      
      if (health.circuitBreaker.state === 'OPEN') {
        console.log(`   Recovery in: ${Math.ceil(health.circuitBreaker.timeUntilRecovery / 1000)}s`);
      }
    }
    
    // Add delay between requests
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

// Run the demonstration
demonstrateResilientClient().catch(console.error);
```## Authent
ication Examples

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
    if (this.token && this.tokenExpiry && Date.now() < this.tokenExpiry - 60000) {
      return this.token;
    }
    
    // If refresh is already in progress, wait for it
    if (this.refreshPromise) {
      return await this.refreshPromise;
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
  
  async refreshTokenIfNeeded() {
    try {
      if (this.refreshToken) {
        // Try to refresh existing token
        const newTokens = await this.refreshAccessToken();
        this.setTokens(newTokens);
        return this.token;
      } else {
        // Need to authenticate from scratch
        throw new Error('No refresh token available - user needs to log in');
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearTokens();
      throw error;
    }
  }
  
  async refreshAccessToken() {
    const response = await fetch(`${this.cognitoConfig.domain}/oauth2/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: this.cognitoConfig.clientId,
        refresh_token: this.refreshToken
      })
    });
    
    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.status}`);
    }
    
    return await response.json();
  }
  
  setTokens(tokenData) {
    this.token = tokenData.access_token;
    this.refreshToken = tokenData.refresh_token || this.refreshToken;
    
    // Decode JWT to get expiry
    if (this.token) {
      try {
        const payload = JSON.parse(atob(this.token.split('.')[1]));
        this.tokenExpiry = payload.exp * 1000; // Convert to milliseconds
      } catch (error) {
        console.error('Failed to decode JWT:', error);
        this.tokenExpiry = Date.now() + 3600000; // Default to 1 hour
      }
    }
    
    // Store in localStorage for persistence
    localStorage.setItem('jwt_token', this.token);
    localStorage.setItem('refresh_token', this.refreshToken);
    localStorage.setItem('token_expiry', this.tokenExpiry.toString());
  }
  
  loadTokensFromStorage() {
    this.token = localStorage.getItem('jwt_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    const expiry = localStorage.getItem('token_expiry');
    this.tokenExpiry = expiry ? parseInt(expiry) : null;
  }
  
  clearTokens() {
    this.token = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
    
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expiry');
  }
  
  isTokenValid() {
    return this.token && this.tokenExpiry && Date.now() < this.tokenExpiry - 60000;
  }
}

// Usage with MBTI client
class AuthenticatedMBTIClient extends MBTITravelAssistantClient {
  constructor(baseURL, cognitoConfig) {
    const tokenManager = new JWTTokenManager(cognitoConfig);
    
    // Load existing tokens on initialization
    tokenManager.loadTokensFromStorage();
    
    super(baseURL, () => tokenManager.getValidToken());
    this.tokenManager = tokenManager;
  }
  
  async login(username, password) {
    try {
      const response = await fetch(`${this.tokenManager.cognitoConfig.domain}/oauth2/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'password',
          client_id: this.tokenManager.cognitoConfig.clientId,
          username: username,
          password: password,
          scope: 'openid profile email'
        })
      });
      
      if (!response.ok) {
        throw new Error(`Login failed: ${response.status}`);
      }
      
      const tokenData = await response.json();
      this.tokenManager.setTokens(tokenData);
      
      return { success: true, message: 'Login successful' };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  }
  
  logout() {
    this.tokenManager.clearTokens();
  }
  
  isAuthenticated() {
    return this.tokenManager.isTokenValid();
  }
  
  async generateItineraryWithAuth(mbtiPersonality, userContext = null) {
    if (!this.isAuthenticated()) {
      throw new Error('User not authenticated - please log in');
    }
    
    try {
      const request = { MBTI_personality: mbtiPersonality };
      if (userContext) request.user_context = userContext;
      
      const response = await this.client.post('/invocations', request);
      return response.data;
    } catch (error) {
      // Handle auth errors specifically
      if (error.response?.status === 401) {
        console.log('Authentication failed, clearing tokens');
        this.logout();
        throw new Error('Authentication expired - please log in again');
      }
      throw error;
    }
  }
}

// Example usage
async function demonstrateAuthentication() {
  const cognitoConfig = {
    domain: 'https://your-cognito-domain.auth.region.amazoncognito.com',
    clientId: 'your-cognito-client-id'
  };
  
  const client = new AuthenticatedMBTIClient(
    'https://your-agentcore-endpoint.amazonaws.com',
    cognitoConfig
  );
  
  // Check if already authenticated
  if (!client.isAuthenticated()) {
    console.log('User not authenticated, logging in...');
    
    const loginResult = await client.login('demo_user', 'demo_password');
    
    if (!loginResult.success) {
      console.error('Login failed:', loginResult.error);
      return;
    }
    
    console.log('✅ Login successful');
  } else {
    console.log('✅ User already authenticated');
  }
  
  // Generate itinerary
  try {
    const itinerary = await client.generateItineraryWithAuth('INFJ');
    console.log('✅ Itinerary generated successfully');
    console.log(`Processing time: ${itinerary.metadata.processing_time_ms}ms`);
  } catch (error) {
    console.error('❌ Itinerary generation failed:', error.message);
    
    if (error.message.includes('log in again')) {
      console.log('Redirecting to login...');
      // Redirect to login page or show login form
    }
  }
}
```

## Testing Examples

### Unit Tests for MBTI Client

```javascript
// Using Jest testing framework
import { MBTITravelAssistantClient } from '../src/mbti-client';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

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
  
  describe('generateMBTIItinerary', () => {
    it('should generate itinerary for valid MBTI type', async () => {
      const mockResponse = {
        data: {
          main_itinerary: {
            day_1: {
              morning_session: {
                id: 'spot_001',
                name: 'Test Museum',
                MBTI_match: true
              },
              breakfast: {
                id: 'rest_001',
                name: 'Test Cafe'
              }
            }
          },
          metadata: {
            MBTI_personality: 'INFJ',
            processing_time_ms: 5000,
            validation_status: 'passed'
          }
        }
      };
      
      client.client.post.mockResolvedValue(mockResponse);
      
      const result = await client.generateMBTIItinerary('INFJ');
      
      expect(client.client.post).toHaveBeenCalledWith('/invocations', {
        MBTI_personality: 'INFJ'
      });
      
      expect(result).toEqual(mockResponse.data);
      expect(result.metadata.MBTI_personality).toBe('INFJ');
      expect(result.main_itinerary.day_1.morning_session.MBTI_match).toBe(true);
    });
    
    it('should handle validation errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              error_type: 'validation_error',
              error_code: 'VALIDATION_FAILED',
              message: 'Invalid MBTI personality format',
              suggested_actions: ['Provide valid MBTI personality type']
            }
          }
        }
      };
      
      client.client.post.mockRejectedValue(mockError);
      
      await expect(client.generateMBTIItinerary('INVALID')).rejects.toThrow();
    });
    
    it('should handle partial success with MCP errors', async () => {
      const mockResponse = {
        data: {
          main_itinerary: {
            day_1: {
              morning_session: { id: 'spot_001', name: 'Test Museum' },
              breakfast: null // Restaurant assignment failed
            }
          },
          metadata: {
            MBTI_personality: 'INFJ',
            processing_time_ms: 3000,
            validation_status: 'partial_success'
          },
          error: {
            error_type: 'mcp_service_error',
            error_code: 'MCP_SERVICE_UNAVAILABLE',
            message: 'Restaurant service unavailable'
          }
        }
      };
      
      client.client.post.mockResolvedValue(mockResponse);
      
      const result = await client.generateMBTIItinerary('INFJ');
      
      expect(result.metadata.validation_status).toBe('partial_success');
      expect(result.error).toBeDefined();
      expect(result.main_itinerary.day_1.morning_session).toBeDefined();
      expect(result.main_itinerary.day_1.breakfast).toBeNull();
    });
    
    it('should include user context when provided', async () => {
      const mockResponse = { data: { metadata: { MBTI_personality: 'ENFP' } } };
      client.client.post.mockResolvedValue(mockResponse);
      
      const userContext = {
        user_id: 'test_user',
        preferences: { activity_level: 'high' }
      };
      
      await client.generateMBTIItinerary('ENFP', userContext);
      
      expect(client.client.post).toHaveBeenCalledWith('/invocations', {
        MBTI_personality: 'ENFP',
        user_context: userContext
      });
    });
  });
  
  describe('validateMBTIType', () => {
    it('should validate correct MBTI types', () => {
      const validTypes = ['INFJ', 'ENFP', 'INTJ', 'ESTP'];
      
      validTypes.forEach(type => {
        expect(client.validateMBTIType(type)).toBe(true);
      });
    });
    
    it('should reject invalid MBTI types', () => {
      const invalidTypes = ['INVALID', 'ABC', '1234', '', null, undefined];
      
      invalidTypes.forEach(type => {
        expect(client.validateMBTIType(type)).toBe(false);
      });
    });
    
    it('should handle case insensitive validation', () => {
      expect(client.validateMBTIType('infj')).toBe(true);
      expect(client.validateMBTIType('EnFp')).toBe(true);
      expect(client.validateMBTIType('INTJ')).toBe(true);
    });
  });
});
```

### Integration Tests

```javascript
describe('MBTI Travel Assistant Integration Tests', () => {
  let client;
  
  beforeAll(() => {
    // Use real endpoint for integration tests
    client = new MBTITravelAssistantClient(
      process.env.TEST_API_ENDPOINT || 'https://test-endpoint.com',
      () => process.env.TEST_JWT_TOKEN
    );
  });
  
  describe('End-to-End Itinerary Generation', () => {
    it('should generate complete 3-day itinerary for INFJ', async () => {
      const result = await client.generateMBTIItinerary('INFJ');
      
      // Verify structure
      expect(result).toHaveProperty('main_itinerary');
      expect(result).toHaveProperty('candidate_tourist_spots');
      expect(result).toHaveProperty('candidate_restaurants');
      expect(result).toHaveProperty('metadata');
      
      // Verify 3-day structure
      expect(result.main_itinerary).toHaveProperty('day_1');
      expect(result.main_itinerary).toHaveProperty('day_2');
      expect(result.main_itinerary).toHaveProperty('day_3');
      
      // Verify each day has required sessions
      Object.values(result.main_itinerary).forEach(day => {
        expect(day).toHaveProperty('morning_session');
        expect(day).toHaveProperty('afternoon_session');
        expect(day).toHaveProperty('night_session');
        expect(day).toHaveProperty('breakfast');
        expect(day).toHaveProperty('lunch');
        expect(day).toHaveProperty('dinner');
      });
      
      // Verify metadata
      expect(result.metadata.MBTI_personality).toBe('INFJ');
      expect(result.metadata.processing_time_ms).toBeGreaterThan(0);
      expect(result.metadata.processing_time_ms).toBeLessThan(15000); // Under 15 seconds
      expect(result.metadata.validation_status).toBeDefined();
      
      // Verify MBTI matching
      let mbtiMatchCount = 0;
      Object.values(result.main_itinerary).forEach(day => {
        ['morning_session', 'afternoon_session', 'night_session'].forEach(session => {
          if (day[session]?.MBTI_match) {
            mbtiMatchCount++;
          }
        });
      });
      
      expect(mbtiMatchCount).toBeGreaterThan(0); // At least some MBTI matches
    }, 20000); // 20 second timeout
    
    it('should generate different itineraries for different MBTI types', async () => {
      const infj = await client.generateMBTIItinerary('INFJ');
      const enfp = await client.generateMBTIItinerary('ENFP');
      
      // Should have different tourist spots
      const infjSpots = Object.values(infj.main_itinerary)
        .flatMap(day => [day.morning_session, day.afternoon_session, day.night_session])
        .map(spot => spot?.id)
        .filter(Boolean);
      
      const enfpSpots = Object.values(enfp.main_itinerary)
        .flatMap(day => [day.morning_session, day.afternoon_session, day.night_session])
        .map(spot => spot?.id)
        .filter(Boolean);
      
      // Should have some different spots (not identical itineraries)
      const commonSpots = infjSpots.filter(id => enfpSpots.includes(id));
      expect(commonSpots.length).toBeLessThan(infjSpots.length);
    }, 30000);
  });
  
  describe('Error Handling Integration', () => {
    it('should handle invalid MBTI types gracefully', async () => {
      await expect(client.generateMBTIItinerary('INVALID')).rejects.toThrow();
    });
    
    it('should handle authentication errors', async () => {
      const unauthenticatedClient = new MBTITravelAssistantClient(
        process.env.TEST_API_ENDPOINT,
        () => 'invalid-token'
      );
      
      await expect(unauthenticatedClient.generateMBTIItinerary('INFJ')).rejects.toThrow();
    });
  });
  
  describe('Performance Tests', () => {
    it('should respond within acceptable time limits', async () => {
      const startTime = Date.now();
      const result = await client.generateMBTIItinerary('INTJ');
      const endTime = Date.now();
      
      const totalTime = endTime - startTime;
      expect(totalTime).toBeLessThan(15000); // Under 15 seconds
      
      // Also check reported processing time
      expect(result.metadata.processing_time_ms).toBeLessThan(12000); // Under 12 seconds server-side
    });
  });
});
```

---

**Last Updated**: January 15, 2024  
**Version**: 1.0.0  
**Compatible with**: MBTI Travel Assistant API v1.0.0  
**Requirements**: JWT authentication, MBTI personality types, 3-day itinerary generation