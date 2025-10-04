# Restaurant Reasoning MCP Server - Usage Examples & Integration Patterns

This document provides comprehensive examples for integrating and using the Restaurant Reasoning MCP server with BedrockAgentCoreApp entrypoints and various client applications.

## Table of Contents

1. [BedrockAgentCoreApp Integration](#bedrockagentcoreapp-integration)
2. [MCP Tool Parameter Formats](#mcp-tool-parameter-formats)
3. [Sample Queries and Expected Outputs](#sample-queries-and-expected-outputs)
4. [Error Handling Examples](#error-handling-examples)
5. [Integration Patterns](#integration-patterns)
6. [Performance Optimization](#performance-optimization)

## BedrockAgentCoreApp Integration

### Basic Entrypoint Setup

The following example shows how to integrate the reasoning MCP tools with a BedrockAgentCoreApp entrypoint:
```py
thon
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
import json

# Create BedrockAgentCore application
app = BedrockAgentCoreApp()

@app.entrypoint
def restaurant_reasoning_entrypoint(payload: dict) -> str:
    """
    Main entrypoint for restaurant reasoning requests.
    
    Processes user prompts and restaurant data through Strands Agent
    with reasoning MCP tools integration.
    """
    try:
        # Extract user prompt from AgentCore payload
        user_prompt = payload.get("input", {}).get("prompt", "")
        
        if not user_prompt:
            return json.dumps({
                "error": "No user prompt provided",
                "message": "Please provide a prompt in the format: {'input': {'prompt': 'your question'}}"
            })
        
        # Initialize Strands Agent with reasoning tools
        agent = Agent(
            model_id="amazon.nova-pro-v1:0",
            model_parameters={
                "temperature": 0.1,
                "max_tokens": 2048,
                "top_p": 0.9
            },
            system_prompt="""You are a restaurant recommendation expert that analyzes 
            sentiment data to provide intelligent recommendations. You have access to 
            reasoning tools that can analyze restaurant lists and provide data-driven 
            recommendations based on customer satisfaction metrics.
            
            When users provide restaurant data or ask for recommendations, use the 
            appropriate MCP tools to analyze sentiment and provide helpful, 
            data-driven recommendations with clear explanations.""",
            tools=[
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ]
        )
        
        # Process user message through agent
        response = agent.invoke(user_prompt)
        
        return json.dumps({
            "response": response,
            "status": "success"
        })
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "error",
            "message": "Failed to process restaurant reasoning request"
        })

if __name__ == "__main__":
    app.run()
```### A
dvanced Entrypoint with Data Extraction

```python
import json
import re
from typing import List, Dict, Any

@app.entrypoint  
def advanced_reasoning_entrypoint(payload: dict) -> str:
    """
    Advanced entrypoint that can extract restaurant data from various formats
    and route to appropriate reasoning tools.
    """
    try:
        user_input = payload.get("input", {})
        prompt = user_input.get("prompt", "")
        restaurant_data = user_input.get("restaurant_data", [])
        
        # Extract restaurant data from prompt if embedded as JSON
        if not restaurant_data and "restaurants" in prompt.lower():
            restaurant_data = extract_restaurant_data_from_prompt(prompt)
        
        # Determine intent and route to appropriate processing
        intent = classify_user_intent(prompt)
        
        agent = Agent(
            model_id="amazon.nova-pro-v1:0",
            system_prompt=get_system_prompt_for_intent(intent),
            tools=get_tools_for_intent(intent)
        )
        
        # Enhance prompt with extracted data context
        enhanced_prompt = enhance_prompt_with_context(prompt, restaurant_data, intent)
        
        response = agent.invoke(enhanced_prompt)
        
        return format_response(response, intent, restaurant_data)
        
    except Exception as e:
        return handle_entrypoint_error(e, payload)

def extract_restaurant_data_from_prompt(prompt: str) -> List[Dict]:
    """Extract JSON restaurant data embedded in user prompts."""
    try:
        # Look for JSON arrays in the prompt
        json_pattern = r'\[.*?\]'
        matches = re.findall(json_pattern, prompt, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list) and len(data) > 0:
                    # Validate first item looks like restaurant data
                    first_item = data[0]
                    if isinstance(first_item, dict) and 'sentiment' in first_item:
                        return data
            except json.JSONDecodeError:
                continue
                
        return []
    except Exception:
        return []

def classify_user_intent(prompt: str) -> str:
    """Classify user intent for appropriate tool routing."""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ['recommend', 'suggest', 'best', 'choose', 'pick']):
        return 'recommendation'
    elif any(word in prompt_lower for word in ['analyze', 'analysis', 'sentiment', 'statistics']):
        return 'analysis'
    elif any(word in prompt_lower for word in ['compare', 'rank', 'order', 'sort']):
        return 'ranking'
    else:
        return 'general'
```## 
MCP Tool Parameter Formats

### Restaurant Data Input Format

The reasoning MCP tools expect restaurant data in the following standardized format:

```python
# Complete restaurant object structure
restaurant_object = {
    # Required fields
    "id": "unique_restaurant_identifier",
    "name": "Restaurant Name",
    "sentiment": {
        "likes": 45,      # Non-negative integer
        "dislikes": 5,    # Non-negative integer  
        "neutral": 10     # Non-negative integer
    },
    
    # Optional but recommended fields
    "district": "Central",
    "address": "123 Queen's Road Central, Hong Kong",
    "cuisine_type": "Cantonese",
    "price_range": "$$",
    "operating_hours": {
        "Mon - Fri": ["07:00-11:30", "12:00-15:00", "18:00-22:30"],
        "Sat - Sun": ["08:00-11:30", "12:00-15:00", "18:00-23:00"],
        "Public Holiday": ["08:00-11:30", "12:00-15:00", "18:00-22:30"]
    },
    
    # Additional metadata (optional)
    "meal_type": ["breakfast", "lunch", "dinner"],
    "location_category": "business_district",
    "metadata": {
        "data_quality": "high",
        "version": "1.0",
        "quality_score": 0.95
    }
}

# Minimal valid restaurant object
minimal_restaurant = {
    "id": "rest_001",
    "name": "Golden Dragon",
    "sentiment": {
        "likes": 30,
        "dislikes": 5,
        "neutral": 8
    }
}
```

### Tool Parameter Examples

#### recommend_restaurants Tool

```python
# Basic recommendation request
{
    "restaurants": [
        {
            "id": "rest_001",
            "name": "Golden Dragon Restaurant",
            "sentiment": {"likes": 45, "dislikes": 5, "neutral": 10},
            "district": "Central",
            "cuisine_type": "Cantonese"
        },
        {
            "id": "rest_002", 
            "name": "Harbour View Cafe",
            "sentiment": {"likes": 32, "dislikes": 8, "neutral": 15},
            "district": "Tsim Sha Tsui",
            "cuisine_type": "International"
        }
    ],
    "ranking_method": "sentiment_likes"  # or "combined_sentiment"
}

# Large dataset recommendation
{
    "restaurants": [
        # ... array of 50+ restaurant objects
    ],
    "ranking_method": "combined_sentiment"
}
```

#### analyze_restaurant_sentiment Tool

```python
# Sentiment analysis request
{
    "restaurants": [
        {
            "id": "rest_001",
            "name": "Restaurant A",
            "sentiment": {"likes": 25, "dislikes": 10, "neutral": 5}
        },
        {
            "id": "rest_002",
            "name": "Restaurant B", 
            "sentiment": {"likes": 40, "dislikes": 3, "neutral": 12}
        }
    ]
}
```## Sam
ple Queries and Expected Outputs

### Recommendation Queries

#### Query 1: Basic Recommendation Request
**User Input:**
```
"Analyze these restaurants and recommend the best one based on customer satisfaction: 
[
  {\"id\": \"r1\", \"name\": \"Golden Dragon\", \"sentiment\": {\"likes\": 45, \"dislikes\": 5, \"neutral\": 10}},
  {\"id\": \"r2\", \"name\": \"Harbour Cafe\", \"sentiment\": {\"likes\": 32, \"dislikes\": 8, \"neutral\": 15}},
  {\"id\": \"r3\", \"name\": \"Spice Garden\", \"sentiment\": {\"likes\": 28, \"dislikes\": 12, \"neutral\": 20}}
]"
```

**Expected MCP Tool Call:**
```python
recommend_restaurants(
    restaurants=[
        {"id": "r1", "name": "Golden Dragon", "sentiment": {"likes": 45, "dislikes": 5, "neutral": 10}},
        {"id": "r2", "name": "Harbour Cafe", "sentiment": {"likes": 32, "dislikes": 8, "neutral": 15}},
        {"id": "r3", "name": "Spice Garden", "sentiment": {"likes": 28, "dislikes": 12, "neutral": 20}}
    ],
    ranking_method="sentiment_likes"
)
```

**Expected Response Structure:**
```json
{
    "candidates": [
        {
            "id": "r1",
            "name": "Golden Dragon", 
            "sentiment": {"likes": 45, "dislikes": 5, "neutral": 10},
            "sentiment_score": 75.0
        },
        {
            "id": "r2", 
            "name": "Harbour Cafe",
            "sentiment": {"likes": 32, "dislikes": 8, "neutral": 15},
            "sentiment_score": 58.2
        },
        {
            "id": "r3",
            "name": "Spice Garden", 
            "sentiment": {"likes": 28, "dislikes": 12, "neutral": 20},
            "sentiment_score": 46.7
        }
    ],
    "recommendation": {
        "id": "r1",
        "name": "Golden Dragon",
        "sentiment": {"likes": 45, "dislikes": 5, "neutral": 10},
        "sentiment_score": 75.0
    },
    "ranking_method": "sentiment_likes",
    "analysis_summary": {
        "total_restaurants": 3,
        "candidates_selected": 3,
        "average_likes": 35.0,
        "top_sentiment_score": 75.0,
        "recommendation_reason": "Randomly selected from top candidates based on sentiment likes"
    }
}
```

**Expected Conversational Response:**
```
I analyzed the 3 restaurants based on customer satisfaction metrics and found some great options!

🍽️ **My Recommendation: Golden Dragon**
👍 Customer Sentiment: 45 likes, 5 dislikes, 10 neutral (75.0% satisfaction)
📊 This restaurant has the highest number of customer likes and excellent overall satisfaction.

**Top Candidates Ranked by Customer Likes:**
1. Golden Dragon - 45 likes (75.0% satisfaction)
2. Harbour Cafe - 32 likes (58.2% satisfaction)  
3. Spice Garden - 28 likes (46.7% satisfaction)

Golden Dragon stands out with the most positive customer feedback. Would you like me to analyze these restaurants using a different ranking method or provide more details about any of them?
```

#### Query 2: Combined Sentiment Analysis
**User Input:**
```
"Which restaurant has the most balanced positive feedback including neutral responses?"
```

**Expected MCP Tool Call:**
```python
recommend_restaurants(
    restaurants=extracted_restaurant_data,
    ranking_method="combined_sentiment"
)
```

**Expected Response:**
```
Based on combined positive sentiment analysis (including neutral feedback as potentially positive):

🍽️ **My Recommendation: Spice Garden**
👍 Combined Positive Score: 80.0% (48 positive responses out of 60 total)
📊 This restaurant has the most balanced positive experience when including neutral feedback.

**Rankings by Combined Positive Sentiment:**
1. Spice Garden - 80.0% combined positive (28 likes + 20 neutral)
2. Golden Dragon - 91.7% combined positive (45 likes + 10 neutral)  
3. Harbour Cafe - 85.5% combined positive (32 likes + 15 neutral)

The combined sentiment method reveals that while Golden Dragon has the highest percentage, Spice Garden shows strong balanced satisfaction across all feedback types.
```### Analy
sis Queries

#### Query 3: Pure Sentiment Analysis
**User Input:**
```
"What are the sentiment patterns in these restaurants? Show me the statistics."
```

**Expected MCP Tool Call:**
```python
analyze_restaurant_sentiment(restaurants=extracted_restaurant_data)
```

**Expected Response Structure:**
```json
{
    "sentiment_analysis": {
        "total_restaurants": 3,
        "average_likes": 35.0,
        "average_dislikes": 8.3,
        "average_neutral": 15.0,
        "overall_satisfaction_rate": 59.8,
        "sentiment_distribution": {
            "high_satisfaction": 1,
            "medium_satisfaction": 2, 
            "low_satisfaction": 0
        },
        "top_performers": [
            {"name": "Golden Dragon", "likes_percentage": 75.0, "total_responses": 60},
            {"name": "Harbour Cafe", "likes_percentage": 58.2, "total_responses": 55},
            {"name": "Spice Garden", "likes_percentage": 46.7, "total_responses": 60}
        ],
        "insights": {
            "most_liked": "Golden Dragon",
            "most_responses": "Golden Dragon, Spice Garden (tied at 60 responses)",
            "average_response_rate": 58.3,
            "satisfaction_trend": "Generally positive with 1 high-performing restaurant"
        }
    }
}
```

**Expected Conversational Response:**
```
Here's the sentiment analysis for your restaurant dataset:

📊 **Overall Statistics:**
- Total Restaurants Analyzed: 3
- Average Customer Likes: 35.0 per restaurant
- Average Dislikes: 8.3 per restaurant
- Average Neutral Responses: 15.0 per restaurant
- Overall Satisfaction Rate: 59.8%

🏆 **Performance Distribution:**
- High Satisfaction (>70%): 1 restaurant
- Medium Satisfaction (40-70%): 2 restaurants  
- Low Satisfaction (<40%): 0 restaurants

⭐ **Top Performers:**
1. Golden Dragon: 75.0% satisfaction (45 likes out of 60 responses)
2. Harbour Cafe: 58.2% satisfaction (32 likes out of 55 responses)
3. Spice Garden: 46.7% satisfaction (28 likes out of 60 responses)

💡 **Key Insights:**
- Golden Dragon is the clear leader in customer satisfaction
- All restaurants maintain above-average satisfaction rates
- Good engagement levels with an average of 58.3 responses per restaurant
- No restaurants show concerning satisfaction levels

Would you like me to dive deeper into any specific restaurant's performance or compare them using different metrics?
```

## Error Handling Examples

### Invalid Restaurant Data

#### Missing Required Fields
**Input:**
```python
{
    "restaurants": [
        {"name": "Restaurant A"},  # Missing id and sentiment
        {"id": "r2", "sentiment": {"likes": 10}}  # Missing name and sentiment fields
    ],
    "ranking_method": "sentiment_likes"
}
```

**Expected Error Response:**
```json
{
    "error": {
        "type": "ValidationError",
        "message": "Invalid restaurant data structure",
        "details": {
            "invalid_restaurants": [
                {
                    "index": 0,
                    "errors": ["Missing required field: id", "Missing required field: sentiment"],
                    "restaurant_name": "Restaurant A"
                },
                {
                    "index": 1, 
                    "errors": ["Missing required field: name", "Missing sentiment field: dislikes", "Missing sentiment field: neutral"],
                    "restaurant_id": "r2"
                }
            ],
            "valid_count": 0,
            "total_count": 2
        }
    }
}
```

**Conversational Error Response:**
```
I found some issues with the restaurant data you provided:

❌ **Data Validation Errors:**
- Restaurant 1 (Restaurant A): Missing required fields - id, sentiment data
- Restaurant 2 (ID: r2): Missing name and complete sentiment data (dislikes, neutral)

📋 **Required Format:**
Each restaurant must include:
- `id`: Unique identifier
- `name`: Restaurant name  
- `sentiment`: Object with `likes`, `dislikes`, and `neutral` (all non-negative integers)

**Example of correct format:**
```json
{
    "id": "rest_001",
    "name": "Restaurant Name",
    "sentiment": {"likes": 30, "dislikes": 5, "neutral": 8}
}
```

Please check your data format and try again. I'm here to help if you need assistance formatting the restaurant data correctly!
```###
# Zero Sentiment Responses
**Input:**
```python
{
    "restaurants": [
        {"id": "r1", "name": "New Restaurant", "sentiment": {"likes": 0, "dislikes": 0, "neutral": 0}},
        {"id": "r2", "name": "Popular Place", "sentiment": {"likes": 25, "dislikes": 3, "neutral": 7}}
    ],
    "ranking_method": "sentiment_likes"
}
```

**Expected Warning Response:**
```json
{
    "candidates": [
        {
            "id": "r2",
            "name": "Popular Place",
            "sentiment": {"likes": 25, "dislikes": 3, "neutral": 7}
        }
    ],
    "recommendation": {
        "id": "r2", 
        "name": "Popular Place",
        "sentiment": {"likes": 25, "dislikes": 3, "neutral": 7}
    },
    "ranking_method": "sentiment_likes",
    "warnings": [
        {
            "restaurant_id": "r1",
            "restaurant_name": "New Restaurant", 
            "message": "Restaurant excluded due to zero sentiment responses"
        }
    ],
    "analysis_summary": {
        "total_restaurants": 2,
        "excluded_restaurants": 1,
        "candidates_selected": 1,
        "exclusion_reason": "Zero sentiment responses"
    }
}
```

#### Invalid Ranking Method
**Input:**
```python
{
    "restaurants": [...],
    "ranking_method": "invalid_method"
}
```

**Expected Error Response:**
```json
{
    "error": {
        "type": "InvalidParameterError",
        "message": "Invalid ranking method specified",
        "details": {
            "provided_method": "invalid_method",
            "valid_methods": ["sentiment_likes", "combined_sentiment"],
            "default_method": "sentiment_likes"
        }
    }
}
```

### System Errors

#### Authentication Failure
**Expected Error Response:**
```json
{
    "error": {
        "type": "AuthenticationError",
        "message": "JWT token validation failed",
        "details": {
            "error_code": "TOKEN_EXPIRED",
            "suggested_action": "Please refresh your authentication token and try again"
        }
    }
}
```

#### MCP Server Unavailable
**Expected Error Response:**
```json
{
    "error": {
        "type": "ServiceUnavailableError", 
        "message": "Restaurant reasoning MCP server is temporarily unavailable",
        "details": {
            "retry_after": 30,
            "suggested_action": "Please try again in a few moments"
        }
    }
}
```

## Integration Patterns

### Pattern 1: Direct MCP Client Integration

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import json

class RestaurantReasoningClient:
    """Direct MCP client for restaurant reasoning tools."""
    
    def __init__(self, mcp_server_url: str, auth_token: str = None):
        self.mcp_server_url = mcp_server_url
        self.auth_token = auth_token
        
    async def get_recommendations(self, restaurants: list, ranking_method: str = "sentiment_likes"):
        """Get restaurant recommendations using MCP tools."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        async with streamablehttp_client(self.mcp_server_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call recommend_restaurants tool
                result = await session.call_tool(
                    "recommend_restaurants",
                    {
                        "restaurants": restaurants,
                        "ranking_method": ranking_method
                    }
                )
                
                return json.loads(result.content[0].text)
    
    async def analyze_sentiment(self, restaurants: list):
        """Analyze restaurant sentiment using MCP tools."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        async with streamablehttp_client(self.mcp_server_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "analyze_restaurant_sentiment",
                    {"restaurants": restaurants}
                )
                
                return json.loads(result.content[0].text)

# Usage example
async def main():
    client = RestaurantReasoningClient(
        mcp_server_url="https://your-agentcore-runtime-url/mcp",
        auth_token="your-jwt-token"
    )
    
    restaurants = [
        {"id": "r1", "name": "Test Restaurant", "sentiment": {"likes": 30, "dislikes": 5, "neutral": 10}}
    ]
    
    # Get recommendations
    recommendations = await client.get_recommendations(restaurants, "sentiment_likes")
    print(f"Recommendation: {recommendations['recommendation']['name']}")
    
    # Analyze sentiment
    analysis = await client.analyze_sentiment(restaurants)
    print(f"Average satisfaction: {analysis['sentiment_analysis']['overall_satisfaction_rate']}%")

if __name__ == "__main__":
    asyncio.run(main())
```#
## Pattern 2: Foundation Model Integration

```python
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
import json

class RestaurantReasoningAgent:
    """Foundation model agent with reasoning capabilities."""
    
    def __init__(self):
        self.agent = Agent(
            model_id="amazon.nova-pro-v1:0",
            model_parameters={
                "temperature": 0.1,
                "max_tokens": 2048,
                "top_p": 0.9
            },
            system_prompt=self._get_system_prompt(),
            tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an expert restaurant recommendation assistant with advanced 
        sentiment analysis capabilities. You can process restaurant data and provide 
        intelligent recommendations based on customer satisfaction metrics.

        Available Tools:
        1. recommend_restaurants: Analyzes restaurants and provides top candidates plus one recommendation
        2. analyze_restaurant_sentiment: Provides detailed sentiment statistics and insights

        When users provide restaurant data:
        - Use recommend_restaurants for recommendation requests
        - Use analyze_restaurant_sentiment for pure analysis requests
        - Always explain your reasoning and methodology
        - Provide clear, actionable insights
        - Format responses in a conversational, helpful manner"""
    
    def process_query(self, user_query: str, restaurant_data: list = None) -> str:
        """Process user query with optional restaurant data."""
        
        # Enhance query with restaurant data context if provided
        if restaurant_data:
            enhanced_query = f"""
            User Query: {user_query}
            
            Restaurant Data: {json.dumps(restaurant_data, indent=2)}
            
            Please analyze this data and respond to the user's request.
            """
        else:
            enhanced_query = user_query
        
        response = self.agent.invoke(enhanced_query)
        return response

# Usage in BedrockAgentCoreApp
app = BedrockAgentCoreApp()
reasoning_agent = RestaurantReasoningAgent()

@app.entrypoint
def reasoning_entrypoint(payload: dict) -> str:
    """Entrypoint with integrated reasoning agent."""
    try:
        user_input = payload.get("input", {})
        prompt = user_input.get("prompt", "")
        restaurant_data = user_input.get("restaurant_data", [])
        
        # Process through reasoning agent
        response = reasoning_agent.process_query(prompt, restaurant_data)
        
        return json.dumps({
            "response": response,
            "status": "success",
            "metadata": {
                "restaurants_processed": len(restaurant_data),
                "agent_model": "amazon-nova-pro",
                "reasoning_tools_available": True
            }
        })
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "status": "error",
            "message": "Failed to process reasoning request"
        })
```

### Pattern 3: Batch Processing Integration

```python
import asyncio
from typing import List, Dict
import json

class BatchReasoningProcessor:
    """Batch processor for multiple restaurant datasets."""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        
    async def process_multiple_datasets(self, datasets: List[Dict]) -> List[Dict]:
        """Process multiple restaurant datasets concurrently."""
        
        tasks = []
        for dataset in datasets:
            task = self._process_single_dataset(dataset)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "dataset_id": datasets[i].get("id", f"dataset_{i}"),
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append({
                    "dataset_id": datasets[i].get("id", f"dataset_{i}"),
                    "status": "success",
                    "result": result
                })
        
        return processed_results
    
    async def _process_single_dataset(self, dataset: Dict) -> Dict:
        """Process a single restaurant dataset."""
        restaurants = dataset.get("restaurants", [])
        ranking_method = dataset.get("ranking_method", "sentiment_likes")
        
        # Get recommendations
        recommendations = await self.mcp_client.get_recommendations(
            restaurants, ranking_method
        )
        
        # Get sentiment analysis
        analysis = await self.mcp_client.analyze_sentiment(restaurants)
        
        return {
            "recommendations": recommendations,
            "sentiment_analysis": analysis,
            "dataset_metadata": {
                "restaurant_count": len(restaurants),
                "ranking_method": ranking_method
            }
        }

# Usage example
async def batch_processing_example():
    client = RestaurantReasoningClient("https://your-mcp-server", "auth-token")
    processor = BatchReasoningProcessor(client)
    
    datasets = [
        {
            "id": "central_district",
            "restaurants": [...],  # Central district restaurants
            "ranking_method": "sentiment_likes"
        },
        {
            "id": "tsim_sha_tsui", 
            "restaurants": [...],  # TST restaurants
            "ranking_method": "combined_sentiment"
        }
    ]
    
    results = await processor.process_multiple_datasets(datasets)
    
    for result in results:
        print(f"Dataset {result['dataset_id']}: {result['status']}")
        if result['status'] == 'success':
            rec = result['result']['recommendations']['recommendation']
            print(f"  Recommended: {rec['name']}")
```## P
erformance Optimization

### Optimization Strategies

#### 1. Data Preprocessing
```python
def optimize_restaurant_data(restaurants: List[Dict]) -> List[Dict]:
    """Optimize restaurant data for better processing performance."""
    
    optimized = []
    for restaurant in restaurants:
        # Validate and clean data
        if not validate_restaurant_structure(restaurant):
            continue
            
        # Remove unnecessary fields for processing
        optimized_restaurant = {
            "id": restaurant["id"],
            "name": restaurant["name"],
            "sentiment": restaurant["sentiment"]
        }
        
        # Add optional fields only if present and valid
        for field in ["district", "cuisine_type", "price_range"]:
            if field in restaurant and restaurant[field]:
                optimized_restaurant[field] = restaurant[field]
        
        optimized.append(optimized_restaurant)
    
    return optimized

def validate_restaurant_structure(restaurant: Dict) -> bool:
    """Quick validation for restaurant structure."""
    required_fields = ["id", "name", "sentiment"]
    
    for field in required_fields:
        if field not in restaurant:
            return False
    
    sentiment = restaurant["sentiment"]
    sentiment_fields = ["likes", "dislikes", "neutral"]
    
    for field in sentiment_fields:
        if field not in sentiment or not isinstance(sentiment[field], int) or sentiment[field] < 0:
            return False
    
    return True
```

#### 2. Caching Strategy
```python
import hashlib
import json
from functools import lru_cache

class CachedReasoningClient:
    """MCP client with response caching for improved performance."""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self._cache = {}
    
    def _generate_cache_key(self, restaurants: List[Dict], ranking_method: str) -> str:
        """Generate cache key for restaurant data and method."""
        # Create deterministic hash of restaurant data
        data_str = json.dumps(restaurants, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{ranking_method}_{data_hash}"
    
    async def get_recommendations_cached(self, restaurants: List[Dict], ranking_method: str):
        """Get recommendations with caching."""
        cache_key = self._generate_cache_key(restaurants, ranking_method)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get fresh result
        result = await self.mcp_client.get_recommendations(restaurants, ranking_method)
        
        # Cache result (with size limit)
        if len(self._cache) < 100:  # Limit cache size
            self._cache[cache_key] = result
        
        return result
    
    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()
```

#### 3. Batch Size Optimization
```python
class OptimizedBatchProcessor:
    """Optimized batch processor with size limits and parallel processing."""
    
    def __init__(self, mcp_client, max_batch_size: int = 50, max_concurrent: int = 5):
        self.mcp_client = mcp_client
        self.max_batch_size = max_batch_size
        self.max_concurrent = max_concurrent
    
    async def process_large_dataset(self, restaurants: List[Dict], ranking_method: str):
        """Process large restaurant datasets efficiently."""
        
        # Split into optimal batch sizes
        batches = self._create_batches(restaurants, self.max_batch_size)
        
        # Process batches with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_batch(batch):
            async with semaphore:
                return await self.mcp_client.get_recommendations(batch, ranking_method)
        
        # Execute batches
        batch_tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Combine results
        return self._combine_batch_results(batch_results)
    
    def _create_batches(self, restaurants: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Split restaurants into optimal batch sizes."""
        batches = []
        for i in range(0, len(restaurants), batch_size):
            batch = restaurants[i:i + batch_size]
            batches.append(batch)
        return batches
    
    def _combine_batch_results(self, batch_results: List[Dict]) -> Dict:
        """Combine multiple batch results into single result."""
        all_candidates = []
        
        for result in batch_results:
            all_candidates.extend(result.get("candidates", []))
        
        # Re-rank combined candidates
        if all_candidates:
            # Sort by sentiment score (assuming it's included)
            all_candidates.sort(key=lambda r: r.get("sentiment_score", 0), reverse=True)
            
            # Select top 20 and random recommendation
            top_candidates = all_candidates[:20]
            recommendation = random.choice(top_candidates) if top_candidates else None
            
            return {
                "candidates": top_candidates,
                "recommendation": recommendation,
                "ranking_method": batch_results[0].get("ranking_method", "sentiment_likes"),
                "analysis_summary": {
                    "total_restaurants": len(all_candidates),
                    "candidates_selected": len(top_candidates),
                    "batch_count": len(batch_results)
                }
            }
        
        return {"candidates": [], "recommendation": None}
```

### Performance Monitoring

```python
import time
from typing import Dict, Any

class PerformanceMonitor:
    """Monitor and log performance metrics for reasoning operations."""
    
    def __init__(self):
        self.metrics = {}
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations."""
        return TimingContext(self, operation_name)
    
    def record_metric(self, name: str, value: Any, metadata: Dict = None):
        """Record a performance metric."""
        timestamp = time.time()
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "timestamp": timestamp,
            "metadata": metadata or {}
        })
    
    def get_performance_summary(self) -> Dict:
        """Get summary of performance metrics."""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                numeric_values = [v["value"] for v in values if isinstance(v["value"], (int, float))]
                
                if numeric_values:
                    summary[metric_name] = {
                        "count": len(numeric_values),
                        "average": sum(numeric_values) / len(numeric_values),
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "latest": numeric_values[-1]
                    }
        
        return summary

class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_metric(
                f"{self.operation_name}_duration",
                duration,
                {"unit": "seconds"}
            )

# Usage example
monitor = PerformanceMonitor()

async def monitored_recommendation_request(restaurants, ranking_method):
    """Example of monitored reasoning request."""
    
    with monitor.time_operation("recommendation_request"):
        # Record input metrics
        monitor.record_metric("input_restaurant_count", len(restaurants))
        monitor.record_metric("ranking_method", ranking_method)
        
        # Make request
        result = await mcp_client.get_recommendations(restaurants, ranking_method)
        
        # Record output metrics
        monitor.record_metric("output_candidate_count", len(result.get("candidates", [])))
        monitor.record_metric("recommendation_generated", bool(result.get("recommendation")))
    
    return result

# Get performance summary
summary = monitor.get_performance_summary()
print(f"Average request time: {summary.get('recommendation_request_duration', {}).get('average', 0):.3f}s")
```

---

This comprehensive usage guide provides detailed examples for integrating the Restaurant Reasoning MCP server with various applications and optimization strategies for production use. The examples cover everything from basic BedrockAgentCoreApp integration to advanced batch processing and performance monitoring patterns.