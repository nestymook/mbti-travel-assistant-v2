# Integration Patterns for Restaurant Search MCP

This document provides comprehensive integration patterns for using the Restaurant Search MCP system with various applications and frameworks.

## Table of Contents

1. [Web Application Integration](#web-application-integration)
2. [Mobile App Integration](#mobile-app-integration)
3. [Chatbot Integration](#chatbot-integration)
4. [API Gateway Integration](#api-gateway-integration)
5. [Microservices Integration](#microservices-integration)
6. [Testing Integration](#testing-integration)

## Web Application Integration

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
import aiohttp
import json

app = FastAPI(title="Restaurant Search API")
security = HTTPBearer()

class RestaurantSearchRequest(BaseModel):
    districts: Optional[List[str]] = None
    meal_types: Optional[List[str]] = None
    query: Optional[str] = None

class RestaurantSearchResponse(BaseModel):
    success: bool
    restaurants: List[dict]
    total_count: int

class MCPClient:
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    async def search_restaurants(self, request: RestaurantSearchRequest) -> dict:
        if request.query:
            # Use entrypoint for natural language
            payload = {"input": {"prompt": request.query}}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/entrypoint",
                    headers=self.headers,
                    json=payload
                ) as response:
                    return await response.json()
        else:
            # Use MCP tools directly
            tool_name = "search_restaurants_combined"
            parameters = {
                "districts": request.districts,
                "meal_types": request.meal_types
            }
            
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/mcp",
                    headers=self.headers,
                    json=mcp_request
                ) as response:
                    return await response.json()

# Initialize MCP client
mcp_client = MCPClient(
    base_url="https://your-gateway-url",
    jwt_token="your-jwt-token"
)

@app.post("/api/restaurants/search", response_model=RestaurantSearchResponse)
async def search_restaurants(
    request: RestaurantSearchRequest,
    token: str = Depends(security)
):
    try:
        result = await mcp_client.search_restaurants(request)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Parse response based on type
        if 'result' in result:
            # MCP tool response
            restaurant_data = json.loads(result['result']['content'])
        else:
            # Entrypoint response
            restaurant_data = json.loads(result['response'])
        
        return RestaurantSearchResponse(
            success=restaurant_data['success'],
            restaurants=restaurant_data.get('restaurants', []),
            total_count=restaurant_data.get('restaurant_count', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/health")
async def get_health():
    """Get system health status."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{mcp_client.base_url}/status/health",
            headers=mcp_client.headers
        ) as response:
            return await response.json()
```

## Mobile App Integration

### React Native Integration

```javascript
// RestaurantSearchService.js
class RestaurantSearchService {
  constructor(baseUrl, jwtToken) {
    this.baseUrl = baseUrl;
    this.jwtToken = jwtToken;
    this.headers = {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    };
  }

  async searchRestaurants(query, options = {}) {
    try {
      const payload = {
        input: {
          prompt: this.enhanceQuery(query, options)
        }
      };

      const response = await fetch(`${this.baseUrl}/entrypoint`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Search failed');
      }

      return this.formatMobileResponse(result);
    } catch (error) {
      return {
        success: false,
        error: error.message,
        restaurants: []
      };
    }
  }

  enhanceQuery(query, options) {
    let enhancedQuery = query;
    
    if (options.location) {
      enhancedQuery += ` near ${options.location.district}`;
    }
    
    if (options.priceRange) {
      enhancedQuery += ` in ${options.priceRange} price range`;
    }
    
    return enhancedQuery;
  }

  formatMobileResponse(result) {
    const data = JSON.parse(result.response);
    
    return {
      success: data.success,
      restaurants: data.restaurants.map(restaurant => ({
        id: restaurant.id,
        name: restaurant.name,
        address: restaurant.address,
        cuisine: restaurant.meal_type,
        priceRange: restaurant.price_range,
        rating: this.calculateRating(restaurant.sentiment),
        isOpenNow: this.checkIfOpenNow(restaurant.operating_hours)
      })),
      totalCount: data.restaurant_count
    };
  }

  calculateRating(sentiment) {
    const total = sentiment.likes + sentiment.dislikes + sentiment.neutral;
    return total > 0 ? (sentiment.likes / total) * 5 : 0;
  }

  checkIfOpenNow(operatingHours) {
    const now = new Date();
    const currentTime = now.getHours() * 100 + now.getMinutes();
    
    // Simplified check for current day
    const todayHours = now.getDay() < 6 ? 
      operatingHours.mon_fri : operatingHours.sat_sun;
    
    return todayHours.some(timeRange => {
      const [start, end] = timeRange.split(' - ').map(time => {
        const [hours, minutes] = time.split(':').map(Number);
        return hours * 100 + minutes;
      });
      return currentTime >= start && currentTime <= end;
    });
  }
}

// Usage in React Native component
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TextInput, Button } from 'react-native';

const RestaurantSearchScreen = () => {
  const [query, setQuery] = useState('');
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const searchService = new RestaurantSearchService(
    'https://your-gateway-url',
    'your-jwt-token'
  );

  const handleSearch = async () => {
    setLoading(true);
    try {
      const result = await searchService.searchRestaurants(query, {
        location: { district: 'Central district' },
        priceRange: 'moderate'
      });
      
      if (result.success) {
        setRestaurants(result.restaurants);
      } else {
        console.error('Search failed:', result.error);
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View>
      <TextInput
        value={query}
        onChangeText={setQuery}
        placeholder="Search for restaurants..."
      />
      <Button title="Search" onPress={handleSearch} disabled={loading} />
      
      <FlatList
        data={restaurants}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View>
            <Text>{item.name}</Text>
            <Text>{item.address}</Text>
            <Text>Rating: {item.rating.toFixed(1)}/5</Text>
            <Text>{item.isOpenNow ? 'Open Now' : 'Closed'}</Text>
          </View>
        )}
      />
    </View>
  );
};
```

## Chatbot Integration

### Discord Bot Integration

```python
import discord
from discord.ext import commands
import aiohttp
import json

class RestaurantBot(commands.Cog):
    def __init__(self, bot, mcp_base_url: str, jwt_token: str):
        self.bot = bot
        self.mcp_base_url = mcp_base_url
        self.jwt_token = jwt_token
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    @commands.command(name='restaurants')
    async def search_restaurants(self, ctx, *, query: str):
        """Search for restaurants using natural language."""
        try:
            # Call MCP entrypoint
            payload = {"input": {"prompt": query}}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_base_url}/entrypoint",
                    headers=self.headers,
                    json=payload
                ) as response:
                    result = await response.json()
            
            if 'error' in result:
                await ctx.send(f"Sorry, I encountered an error: {result['error']}")
                return
            
            # Parse response
            data = json.loads(result['response'])
            
            if not data['success']:
                await ctx.send(f"Search failed: {data.get('error', 'Unknown error')}")
                return
            
            restaurants = data['restaurants'][:5]  # Limit to 5 results
            
            if not restaurants:
                await ctx.send("No restaurants found matching your criteria.")
                return
            
            # Format response
            embed = discord.Embed(
                title=f"Found {data['restaurant_count']} restaurants",
                color=0x00ff00
            )
            
            for restaurant in restaurants:
                rating = self.calculate_rating(restaurant['sentiment'])
                embed.add_field(
                    name=restaurant['name'],
                    value=f"📍 {restaurant['address']}\n"
                          f"🍽️ {', '.join(restaurant['meal_type'])}\n"
                          f"💰 {restaurant['price_range']}\n"
                          f"⭐ {rating:.1f}/5",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
    
    @commands.command(name='status')
    async def check_status(self, ctx):
        """Check system status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_base_url}/status/health",
                    headers=self.headers
                ) as response:
                    result = await response.json()
            
            if result['success']:
                health_data = result['data']
                embed = discord.Embed(
                    title="System Status",
                    color=0x00ff00 if health_data['overall_health_percentage'] > 80 else 0xff0000
                )
                embed.add_field(
                    name="Health",
                    value=f"{health_data['overall_health_percentage']:.1f}%",
                    inline=True
                )
                embed.add_field(
                    name="Servers",
                    value=f"{health_data['healthy_servers']}/{health_data['total_servers']}",
                    inline=True
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("Unable to retrieve system status.")
                
        except Exception as e:
            await ctx.send(f"Status check failed: {str(e)}")
    
    def calculate_rating(self, sentiment):
        total = sentiment['likes'] + sentiment['dislikes'] + sentiment['neutral']
        return (sentiment['likes'] / total) * 5 if total > 0 else 0

# Bot setup
bot = commands.Bot(command_prefix='!')
restaurant_cog = RestaurantBot(
    bot,
    mcp_base_url="https://your-gateway-url",
    jwt_token="your-jwt-token"
)
bot.add_cog(restaurant_cog)

# Usage: !restaurants find breakfast places in Central district
# Usage: !status
```

## Testing Integration

### Pytest Integration

```python
import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock

class TestRestaurantSearchIntegration:
    """Integration tests for Restaurant Search MCP."""
    
    @pytest.fixture
    def mcp_client(self):
        """Create MCP client for testing."""
        return MCPClient(
            base_url="https://test-gateway-url",
            jwt_token="test-jwt-token"
        )
    
    @pytest.mark.asyncio
    async def test_district_search_integration(self, mcp_client):
        """Test district search integration."""
        request = RestaurantSearchRequest(
            districts=["Central district"]
        )
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "result": {
                    "content": json.dumps({
                        "success": True,
                        "restaurants": [
                            {
                                "id": "test_001",
                                "name": "Test Restaurant",
                                "district": "Central district"
                            }
                        ],
                        "restaurant_count": 1
                    })
                }
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await mcp_client.search_restaurants(request)
            
            assert "result" in result
            restaurant_data = json.loads(result["result"]["content"])
            assert restaurant_data["success"] is True
            assert restaurant_data["restaurant_count"] == 1
    
    @pytest.mark.asyncio
    async def test_natural_language_search_integration(self, mcp_client):
        """Test natural language search integration."""
        request = RestaurantSearchRequest(
            query="Find breakfast places in Central district"
        )
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "response": json.dumps({
                    "success": True,
                    "restaurants": [],
                    "restaurant_count": 0
                })
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await mcp_client.search_restaurants(request)
            
            assert "response" in result
            data = json.loads(result["response"])
            assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_status_monitoring_integration(self):
        """Test status monitoring integration."""
        headers = {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "overall_health_percentage": 100.0,
                    "total_servers": 1,
                    "healthy_servers": 1
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://test-gateway-url/status/health",
                    headers=headers
                ) as response:
                    result = await response.json()
            
            assert result["success"] is True
            assert result["data"]["overall_health_percentage"] == 100.0

# Run tests
# pytest test_integration.py -v
```

This comprehensive integration patterns document provides practical examples for integrating the Restaurant Search MCP system with various applications and frameworks, including web applications, mobile apps, chatbots, and testing frameworks.