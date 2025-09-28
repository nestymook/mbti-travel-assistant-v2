# Restaurant Reasoning MCP Server - Integration Examples

## Overview

This document provides comprehensive examples of how to integrate and use the Restaurant Reasoning MCP Server in various scenarios and environments.

## MCP Client Integration

### Basic MCP Client Setup

```python
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def connect_to_reasoning_server():
    """Connect to the Restaurant Reasoning MCP Server."""
    
    # Server configuration
    mcp_url = "http://localhost:8080"  # Local development
    # mcp_url = "https://your-agent-url.amazonaws.com"  # Production
    
    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"Bearer {jwt_token}"  # If authentication enabled
    }
    
    try:
        async with streamablehttp_client(mcp_url, headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                print("Available tools:", [tool.name for tool in tools.tools])
                
                return session
                
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")
        return None

# Usage
async def main():
    session = await connect_to_reasoning_server()
    if session:
        print("Successfully connected to MCP server")
```

### Restaurant Recommendation Example

```python
async def get_restaurant_recommendations():
    """Get restaurant recommendations using MCP client."""
    
    # Sample restaurant data
    restaurants = [
        {
            "id": "rest_001",
            "name": "Golden Dragon Restaurant",
            "sentiment": {"likes": 45, "dislikes": 5, "neutral": 10},
            "district": "Central",
            "address": "123 Queen's Road Central",
            "cuisine_type": "Cantonese",
            "price_range": "$$"
        },
        {
            "id": "rest_002",
            "name": "Harbour View Cafe",
            "sentiment": {"likes": 32, "dislikes": 8, "neutral": 15},
            "district": "Tsim Sha Tsui", 
            "address": "456 Nathan Road",
            "cuisine_type": "International",
            "price_range": "$"
        },
        {
            "id": "rest_003",
            "name": "Spice Garden",
            "sentiment": {"likes": 28, "dislikes": 12, "neutral": 8},
            "district": "Causeway Bay",
            "address": "789 Hennessy Road",
            "cuisine_type": "Indian",
            "price_range": "$$"
        }
    ]
    
    mcp_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    async with streamablehttp_client(mcp_url, headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call recommendation tool
            result = await session.call_tool(
                "recommend_restaurants",
                {
                    "restaurants": restaurants,
                    "ranking_method": "sentiment_likes"
                }
            )
            
            # Parse and display results
            recommendation_data = json.loads(result.content[0].text)
            
            print("=== Restaurant Recommendations ===")
            print(f"Analysis Method: {recommendation_data['analysis']['ranking_method']}")
            print(f"Total Restaurants: {recommendation_data['analysis']['total_restaurants']}")
            
            # Top recommendation
            top_rec = recommendation_data['analysis']['top_recommendation']
            print(f"\n🏆 Top Recommendation: {top_rec['name']}")
            print(f"   Sentiment Score: {top_rec['sentiment_score']}")
            print(f"   Reasoning: {top_rec['reasoning']}")
            
            # Ranked list
            print("\n📊 Full Rankings:")
            for restaurant in recommendation_data['ranked_restaurants']:
                print(f"   {restaurant['rank']}. {restaurant['name']}")
                print(f"      Likes: {restaurant['sentiment']['likes']}, "
                      f"Dislikes: {restaurant['sentiment']['dislikes']}, "
                      f"Neutral: {restaurant['sentiment']['neutral']}")
                print(f"      Score: {restaurant['sentiment_score']}")
                print(f"      Reasoning: {restaurant['reasoning']}\n")

# Run the example
asyncio.run(get_restaurant_recommendations())
```

### Sentiment Analysis Example

```python
async def analyze_restaurant_sentiment():
    """Analyze restaurant sentiment without recommendations."""
    
    restaurants = [
        {
            "id": "rest_001",
            "name": "Popular Bistro",
            "sentiment": {"likes": 120, "dislikes": 15, "neutral": 25}
        },
        {
            "id": "rest_002", 
            "name": "Average Cafe",
            "sentiment": {"likes": 45, "dislikes": 45, "neutral": 30}
        },
        {
            "id": "rest_003",
            "name": "Struggling Diner",
            "sentiment": {"likes": 20, "dislikes": 60, "neutral": 10}
        }
    ]
    
    mcp_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    async with streamablehttp_client(mcp_url, headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call sentiment analysis tool
            result = await session.call_tool(
                "analyze_restaurant_sentiment",
                {"restaurants": restaurants}
            )
            
            # Parse results
            analysis_data = json.loads(result.content[0].text)
            
            print("=== Sentiment Analysis ===")
            summary = analysis_data['analysis']['sentiment_summary']
            print(f"Total Restaurants: {analysis_data['analysis']['total_restaurants']}")
            print(f"Total Likes: {summary['total_likes']}")
            print(f"Total Dislikes: {summary['total_dislikes']}")
            print(f"Total Neutral: {summary['total_neutral']}")
            print(f"Average Likes: {summary['average_likes']:.1f}")
            print(f"Average Dislikes: {summary['average_dislikes']:.1f}")
            
            print("\n📈 Individual Restaurant Analysis:")
            for restaurant in analysis_data['analysis']['sentiment_distribution']:
                print(f"\n{restaurant['name']}:")
                sentiment = restaurant['sentiment']
                ratio = restaurant['sentiment_ratio']
                print(f"  Sentiment: {sentiment['likes']} likes, {sentiment['dislikes']} dislikes, {sentiment['neutral']} neutral")
                print(f"  Percentages: {ratio['likes_percentage']:.1f}% likes, {ratio['dislikes_percentage']:.1f}% dislikes, {ratio['neutral_percentage']:.1f}% neutral")
            
            print("\n💡 Insights:")
            for insight in analysis_data['insights']:
                print(f"  • {insight}")

# Run the example
asyncio.run(analyze_restaurant_sentiment())
```

## Kiro IDE Integration

### Direct Tool Usage in Kiro

```python
# In Kiro IDE, you can use MCP tools directly

# Sample restaurant data
restaurants = [
    {
        "id": "kiro_001",
        "name": "Tech Cafe",
        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 15},
        "district": "Central",
        "cuisine_type": "International"
    },
    {
        "id": "kiro_002",
        "name": "Developer's Den",
        "sentiment": {"likes": 65, "dislikes": 20, "neutral": 25},
        "district": "Admiralty", 
        "cuisine_type": "Asian Fusion"
    }
]

# Get recommendations using sentiment likes method
recommendations = recommend_restaurants(restaurants, "sentiment_likes")
print("Recommendations:", recommendations)

# Get recommendations using combined positive method
recommendations_combined = recommend_restaurants(restaurants, "combined_positive")
print("Combined Positive Recommendations:", recommendations_combined)

# Analyze sentiment patterns
sentiment_analysis = analyze_restaurant_sentiment(restaurants)
print("Sentiment Analysis:", sentiment_analysis)
```

### Kiro Workflow Integration

```python
# Example Kiro workflow for restaurant analysis

def analyze_restaurant_data_workflow(restaurant_data_file: str):
    """Complete workflow for restaurant data analysis in Kiro."""
    
    # Step 1: Load restaurant data
    import json
    with open(restaurant_data_file, 'r') as f:
        restaurants = json.load(f)
    
    print(f"Loaded {len(restaurants)} restaurants for analysis")
    
    # Step 2: Validate data format
    required_fields = ['id', 'name', 'sentiment']
    for restaurant in restaurants:
        for field in required_fields:
            if field not in restaurant:
                raise ValueError(f"Missing required field '{field}' in restaurant {restaurant.get('id', 'unknown')}")
    
    # Step 3: Get recommendations using different methods
    print("\n=== Sentiment Likes Ranking ===")
    likes_recommendations = recommend_restaurants(restaurants, "sentiment_likes")
    
    print("\n=== Combined Positive Ranking ===")
    combined_recommendations = recommend_restaurants(restaurants, "combined_positive")
    
    # Step 4: Perform sentiment analysis
    print("\n=== Sentiment Analysis ===")
    sentiment_analysis = analyze_restaurant_sentiment(restaurants)
    
    # Step 5: Save results
    results = {
        "timestamp": "2025-09-28T13:45:00Z",
        "total_restaurants": len(restaurants),
        "sentiment_likes_ranking": json.loads(likes_recommendations),
        "combined_positive_ranking": json.loads(combined_recommendations),
        "sentiment_analysis": json.loads(sentiment_analysis)
    }
    
    with open("restaurant_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nAnalysis complete! Results saved to restaurant_analysis_results.json")
    return results

# Usage in Kiro
# results = analyze_restaurant_data_workflow("my_restaurants.json")
```

## Foundation Model Integration

### Natural Language Processing Examples

```python
# Example prompts that foundation models can use with the reasoning tools

# Prompt 1: Basic Recommendation
user_prompt = """
I have data for several restaurants with customer sentiment (likes, dislikes, neutral).
Please analyze this data and recommend the best restaurant:

Restaurant Data:
- Golden Dragon: 45 likes, 5 dislikes, 10 neutral
- Harbour Cafe: 32 likes, 8 dislikes, 15 neutral  
- Spice Garden: 28 likes, 12 dislikes, 8 neutral

Which restaurant would you recommend and why?
"""

# Foundation model would use: recommend_restaurants(restaurant_data, "sentiment_likes")

# Prompt 2: Comparative Analysis
user_prompt = """
Compare these restaurants based on customer satisfaction metrics.
Provide insights about sentiment patterns and customer preferences:

[Restaurant data with sentiment scores]

What trends do you see in the customer feedback?
"""

# Foundation model would use: analyze_restaurant_sentiment(restaurant_data)

# Prompt 3: Ranking Comparison
user_prompt = """
Rank these restaurants using two different methods:
1. By highest number of likes
2. By best overall sentiment (likes minus dislikes)

Explain the differences in rankings and when each method is most appropriate.
"""

# Foundation model would call both:
# recommend_restaurants(data, "sentiment_likes")
# recommend_restaurants(data, "combined_positive")
```

### Foundation Model Response Examples

```python
# Example of how a foundation model might use the tools

def foundation_model_restaurant_analysis(user_query: str, restaurant_data: list):
    """Simulate foundation model using reasoning tools."""
    
    if "recommend" in user_query.lower():
        # Use recommendation tool
        if "best overall" in user_query.lower() or "net positive" in user_query.lower():
            method = "combined_positive"
        else:
            method = "sentiment_likes"
            
        result = recommend_restaurants(restaurant_data, method)
        
        # Foundation model would generate natural language response
        response = f"""
        Based on sentiment analysis of the provided restaurants, I've analyzed the customer 
        feedback data using the {method} ranking method.
        
        {result}
        
        The top recommendation shows strong customer satisfaction with significantly more 
        positive feedback than negative. This suggests a restaurant that consistently 
        delivers good experiences to its customers.
        """
        
    elif "analyze" in user_query.lower() or "compare" in user_query.lower():
        # Use sentiment analysis tool
        result = analyze_restaurant_sentiment(restaurant_data)
        
        response = f"""
        I've performed a comprehensive sentiment analysis of the restaurant data:
        
        {result}
        
        The analysis reveals interesting patterns in customer satisfaction across 
        the restaurants, with clear differences in approval ratings and customer 
        engagement levels.
        """
    
    return response
```

## Batch Processing Examples

### Large Dataset Processing

```python
async def process_large_restaurant_dataset(restaurants: list, batch_size: int = 100):
    """Process large restaurant datasets in batches."""
    
    results = []
    total_batches = (len(restaurants) + batch_size - 1) // batch_size
    
    print(f"Processing {len(restaurants)} restaurants in {total_batches} batches")
    
    mcp_url = "http://localhost:8080"
    headers = {"Content-Type": "application/json"}
    
    async with streamablehttp_client(mcp_url, headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            for i in range(0, len(restaurants), batch_size):
                batch = restaurants[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                
                print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} restaurants)")
                
                try:
                    # Process batch
                    result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": batch,
                            "ranking_method": "sentiment_likes"
                        }
                    )
                    
                    batch_results = json.loads(result.content[0].text)
                    results.append({
                        "batch_number": batch_num,
                        "restaurant_count": len(batch),
                        "results": batch_results
                    })
                    
                except Exception as e:
                    print(f"Error processing batch {batch_num}: {e}")
                    results.append({
                        "batch_number": batch_num,
                        "restaurant_count": len(batch),
                        "error": str(e)
                    })
    
    return results

# Usage
# large_dataset = load_restaurants_from_database()  # Assume 1000+ restaurants
# batch_results = await process_large_restaurant_dataset(large_dataset, batch_size=50)
```

### Parallel Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_restaurant_analysis(restaurant_groups: list):
    """Process multiple restaurant groups in parallel."""
    
    async def analyze_group(group_name: str, restaurants: list):
        """Analyze a single group of restaurants."""
        mcp_url = "http://localhost:8080"
        headers = {"Content-Type": "application/json"}
        
        async with streamablehttp_client(mcp_url, headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Get recommendations
                rec_result = await session.call_tool(
                    "recommend_restaurants",
                    {"restaurants": restaurants, "ranking_method": "sentiment_likes"}
                )
                
                # Get sentiment analysis
                sent_result = await session.call_tool(
                    "analyze_restaurant_sentiment",
                    {"restaurants": restaurants}
                )
                
                return {
                    "group_name": group_name,
                    "restaurant_count": len(restaurants),
                    "recommendations": json.loads(rec_result.content[0].text),
                    "sentiment_analysis": json.loads(sent_result.content[0].text)
                }
    
    # Process all groups in parallel
    tasks = [
        analyze_group(group["name"], group["restaurants"]) 
        for group in restaurant_groups
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results and exceptions
    successful_results = []
    errors = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append({
                "group": restaurant_groups[i]["name"],
                "error": str(result)
            })
        else:
            successful_results.append(result)
    
    return {
        "successful_analyses": successful_results,
        "errors": errors,
        "total_groups": len(restaurant_groups),
        "successful_count": len(successful_results),
        "error_count": len(errors)
    }

# Usage example
restaurant_groups = [
    {
        "name": "Central District",
        "restaurants": central_restaurants
    },
    {
        "name": "Tsim Sha Tsui",
        "restaurants": tst_restaurants
    },
    {
        "name": "Causeway Bay", 
        "restaurants": cwb_restaurants
    }
]

# results = await parallel_restaurant_analysis(restaurant_groups)
```

## Error Handling Examples

### Robust Client Implementation

```python
import asyncio
import json
import logging
from typing import Optional, Dict, Any

class RestaurantReasoningClient:
    """Robust client for Restaurant Reasoning MCP Server."""
    
    def __init__(self, mcp_url: str, jwt_token: Optional[str] = None):
        self.mcp_url = mcp_url
        self.headers = {"Content-Type": "application/json"}
        if jwt_token:
            self.headers["Authorization"] = f"Bearer {jwt_token}"
        
        self.logger = logging.getLogger(__name__)
    
    async def get_recommendations(
        self, 
        restaurants: list, 
        ranking_method: str = "sentiment_likes",
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Get restaurant recommendations with error handling and retries."""
        
        for attempt in range(max_retries):
            try:
                async with streamablehttp_client(self.mcp_url, self.headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "recommend_restaurants",
                            {
                                "restaurants": restaurants,
                                "ranking_method": ranking_method
                            }
                        )
                        
                        return json.loads(result.content[0].text)
                        
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"error": "Invalid JSON response from server"}
                    
            except ConnectionError as e:
                self.logger.error(f"Connection error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"error": "Failed to connect to MCP server"}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"error": f"Unexpected error: {str(e)}"}
                await asyncio.sleep(1)
        
        return {"error": "Max retries exceeded"}
    
    async def analyze_sentiment(
        self, 
        restaurants: list,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Analyze restaurant sentiment with error handling."""
        
        # Validate input
        if not restaurants:
            return {"error": "Restaurant list cannot be empty"}
        
        for restaurant in restaurants:
            if not all(key in restaurant for key in ['id', 'name', 'sentiment']):
                return {"error": f"Invalid restaurant data: missing required fields"}
        
        for attempt in range(max_retries):
            try:
                async with streamablehttp_client(self.mcp_url, self.headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "analyze_restaurant_sentiment",
                            {"restaurants": restaurants}
                        )
                        
                        return json.loads(result.content[0].text)
                        
            except Exception as e:
                self.logger.error(f"Error analyzing sentiment (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"error": f"Failed to analyze sentiment: {str(e)}"}
                await asyncio.sleep(2 ** attempt)
        
        return {"error": "Max retries exceeded"}

# Usage example
async def main():
    client = RestaurantReasoningClient("http://localhost:8080")
    
    restaurants = [
        {
            "id": "test_001",
            "name": "Test Restaurant",
            "sentiment": {"likes": 50, "dislikes": 10, "neutral": 15}
        }
    ]
    
    # Get recommendations with error handling
    recommendations = await client.get_recommendations(restaurants)
    if "error" in recommendations:
        print(f"Error getting recommendations: {recommendations['error']}")
    else:
        print("Recommendations received successfully")
    
    # Analyze sentiment with error handling
    analysis = await client.analyze_sentiment(restaurants)
    if "error" in analysis:
        print(f"Error analyzing sentiment: {analysis['error']}")
    else:
        print("Sentiment analysis completed successfully")

# asyncio.run(main())
```

## Production Integration Examples

### AWS Lambda Integration

```python
import json
import asyncio
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda function using Restaurant Reasoning MCP Server."""
    
    try:
        # Extract restaurant data from event
        restaurants = event.get('restaurants', [])
        ranking_method = event.get('ranking_method', 'sentiment_likes')
        
        if not restaurants:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No restaurant data provided'})
            }
        
        # Get MCP server URL from environment
        import os
        mcp_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
        jwt_token = os.environ.get('JWT_TOKEN')
        
        # Create client and get recommendations
        client = RestaurantReasoningClient(mcp_url, jwt_token)
        
        # Run async function in Lambda
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                client.get_recommendations(restaurants, ranking_method)
            )
        finally:
            loop.close()
        
        if "error" in result:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': result['error']})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio

app = FastAPI(title="Restaurant Reasoning API")

class RestaurantInput(BaseModel):
    id: str
    name: str
    sentiment: dict
    district: Optional[str] = None
    address: Optional[str] = None

class RecommendationRequest(BaseModel):
    restaurants: List[RestaurantInput]
    ranking_method: str = "sentiment_likes"

@app.post("/recommend")
async def get_recommendations(request: RecommendationRequest):
    """Get restaurant recommendations via FastAPI."""
    
    try:
        # Convert Pydantic models to dicts
        restaurants = [restaurant.dict() for restaurant in request.restaurants]
        
        # Use MCP client
        client = RestaurantReasoningClient("http://localhost:8080")
        result = await client.get_recommendations(restaurants, request.ranking_method)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_sentiment(restaurants: List[RestaurantInput]):
    """Analyze restaurant sentiment via FastAPI."""
    
    try:
        # Convert to dicts
        restaurant_data = [restaurant.dict() for restaurant in restaurants]
        
        # Use MCP client
        client = RestaurantReasoningClient("http://localhost:8080")
        result = await client.analyze_sentiment(restaurant_data)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn integration_api:app --reload
```

---

**Last Updated**: September 28, 2025  
**Version**: 1.0.0