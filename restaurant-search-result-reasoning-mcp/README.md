# Restaurant Sentiment Analysis & Reasoning MCP Server

A specialized Model Context Protocol (MCP) server that provides intelligent restaurant sentiment analysis and data-driven recommendation capabilities, integrated with Amazon Bedrock AgentCore Runtime. This server focuses on reasoning about restaurant data rather than searching for it, taking restaurant lists as input and applying sophisticated sentiment analysis algorithms to identify top candidates and provide personalized recommendations.

## 🎯 Overview

This reasoning server transforms raw restaurant data into intelligent insights through:

### Core Reasoning Capabilities
- **Advanced Sentiment Analysis**: Processes customer feedback (likes, dislikes, neutral) to calculate satisfaction scores
- **Multi-Algorithm Ranking**: Two distinct ranking methods for different recommendation strategies
- **Intelligent Candidate Selection**: Identifies top 20 restaurants from any size dataset
- **Random Recommendation Engine**: Provides unbiased selection from top candidates
- **Data-Driven Insights**: Generates analysis summaries and reasoning explanations

### Key Differentiators
- **Reasoning-Focused**: Analyzes existing data rather than searching external sources
- **Algorithm Transparency**: Clear explanation of ranking methods and selection criteria  
- **Flexible Input**: Accepts restaurant data from any source (search APIs, files, databases)
- **Conversational AI Ready**: Designed for natural language interaction through foundation models
- **Production-Grade**: Enterprise authentication, monitoring, and deployment capabilities

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker with ARM64 support
- AWS CLI configured with appropriate credentials
- Required AWS permissions: `BedrockAgentCoreFullAccess`, `AmazonBedrockFullAccess`

### Local Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd restaurant-search-result-reasoning-mcp
pip install -r requirements.txt

# Run locally
python restaurant_reasoning_mcp_server.py
```

### Docker Deployment
```bash
# Build ARM64 container (required for AgentCore)
docker build --platform linux/arm64 -t restaurant-reasoning-mcp .

# Run container
docker run -p 8080:8080 \
  -e AWS_REGION=us-east-1 \
  -e REQUIRE_AUTHENTICATION=true \
  restaurant-reasoning-mcp
```

### AWS AgentCore Deployment
```bash
# Deploy to AWS AgentCore
python deploy_reasoning_agentcore.py

# Test deployment
python tests/test_reasoning_deployment.py
```

## 🛠️ Core Reasoning Features

### MCP Reasoning Tools

#### 1. `recommend_restaurants` - Intelligent Recommendation Engine
Analyzes restaurant sentiment data and provides intelligent recommendations using advanced ranking algorithms.

**Purpose**: Transform restaurant lists into actionable recommendations based on customer satisfaction metrics.

**Parameters:**
- `restaurants` (List[Dict]): Restaurant objects with sentiment data (required)
- `ranking_method` (str): Ranking algorithm - "sentiment_likes" or "combined_sentiment" (default: "sentiment_likes")

**Ranking Methods Explained:**

**Sentiment Likes Method (`sentiment_likes`)**
- **Algorithm**: Ranks by highest absolute number of customer likes
- **Best For**: Finding most popular restaurants with strong positive feedback
- **Formula**: `restaurants.sort(key=lambda r: r.sentiment.likes, reverse=True)`
- **Use Case**: "Show me the restaurants customers love most"

**Combined Sentiment Method (`combined_sentiment`)**  
- **Algorithm**: Ranks by combined positive sentiment percentage (likes + neutral)
- **Best For**: Balanced view including neutral feedback as potential positive
- **Formula**: `(likes + neutral) / total_responses * 100`
- **Use Case**: "Find restaurants with overall positive customer experience"

**Example Usage:**
```python
# Sample restaurant data with sentiment
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
        "sentiment": {"likes": 28, "dislikes": 12, "neutral": 20},
        "district": "Causeway Bay",
        "address": "789 Hennessy Road", 
        "cuisine_type": "Indian",
        "price_range": "$"
    }
]

# Get recommendations using sentiment likes method
result = recommend_restaurants(restaurants, "sentiment_likes")

# Expected response structure:
{
    "candidates": [
        # Top 20 restaurants ranked by selected method
        {"id": "rest_001", "name": "Golden Dragon Restaurant", ...},
        {"id": "rest_002", "name": "Harbour View Cafe", ...},
        # ... up to 20 restaurants
    ],
    "recommendation": {
        # Single randomly selected restaurant from top candidates
        "id": "rest_001", 
        "name": "Golden Dragon Restaurant",
        "sentiment": {"likes": 45, "dislikes": 5, "neutral": 10},
        # ... complete restaurant data
    },
    "ranking_method": "sentiment_likes",
    "analysis_summary": {
        "total_restaurants": 3,
        "candidates_selected": 3,
        "average_likes": 35.0,
        "top_sentiment_score": 75.0,
        "recommendation_reason": "Randomly selected from top candidates"
    }
}
```

#### 2. `analyze_restaurant_sentiment` - Pure Sentiment Analysis
Analyzes sentiment data for restaurants without providing recommendations, focusing on data insights.

**Purpose**: Understand sentiment patterns and statistics across restaurant datasets.

**Parameters:**
- `restaurants` (List[Dict]): Restaurant objects with sentiment data

**Example Usage:**
```python
# Analyze sentiment patterns without recommendations
analysis = analyze_restaurant_sentiment(restaurants)

# Expected response:
{
    "sentiment_analysis": {
        "total_restaurants": 3,
        "average_likes": 35.0,
        "average_dislikes": 8.3,
        "average_neutral": 15.0,
        "sentiment_distribution": {
            "high_satisfaction": 1,  # >70% likes
            "medium_satisfaction": 2, # 40-70% likes  
            "low_satisfaction": 0    # <40% likes
        },
        "top_performers": [
            {"name": "Golden Dragon Restaurant", "likes_percentage": 75.0},
            {"name": "Harbour View Cafe", "likes_percentage": 58.2}
        ]
    }
}
```

### Restaurant Data Format

Each restaurant object must include:
```json
{
    "id": "unique_identifier",
    "name": "Restaurant Name",
    "sentiment": {
        "likes": 45,
        "dislikes": 5, 
        "neutral": 10
    },
    "district": "Central",
    "address": "123 Street Address",
    "cuisine_type": "Cantonese",
    "price_range": "$$"
}
```

## 🏗️ Architecture

### Core Components

- **RestaurantReasoningService**: Main business logic for sentiment analysis
- **RecommendationService**: Ranking and recommendation algorithms  
- **SentimentService**: Sentiment data processing and validation
- **ValidationService**: Input validation and error handling
- **AuthenticationMiddleware**: JWT-based security (Cognito integration)

### Natural Language Query Examples

The reasoning server is designed to work with foundation models that process natural language queries and convert them to MCP tool calls:

#### Recommendation Queries
```
User: "Analyze these restaurants and recommend the best one based on customer satisfaction"
→ Foundation Model calls: recommend_restaurants(restaurants, "sentiment_likes")

User: "Which restaurant has the most balanced positive feedback including neutral responses?"  
→ Foundation Model calls: recommend_restaurants(restaurants, "combined_sentiment")

User: "Give me the top restaurant choices from this list"
→ Foundation Model calls: recommend_restaurants(restaurants, "sentiment_likes")
```

#### Analysis Queries  
```
User: "What are the sentiment patterns in these restaurants?"
→ Foundation Model calls: analyze_restaurant_sentiment(restaurants)

User: "Show me the customer satisfaction statistics for these places"
→ Foundation Model calls: analyze_restaurant_sentiment(restaurants)

User: "How do these restaurants compare in terms of customer feedback?"
→ Foundation Model calls: analyze_restaurant_sentiment(restaurants)
```

### Algorithm Deep Dive

#### Sentiment Likes Algorithm
```python
def rank_by_sentiment_likes(restaurants):
    """
    Primary ranking: Absolute likes count
    Tie-breaker: Total response count (engagement)
    
    Logic: Restaurants with more likes are more popular
    Best for: Finding crowd favorites
    """
    return sorted(restaurants, 
                 key=lambda r: (r.sentiment.likes, r.sentiment.total_responses()),
                 reverse=True)
```

#### Combined Sentiment Algorithm  
```python
def rank_by_combined_sentiment(restaurants):
    """
    Primary ranking: (likes + neutral) percentage
    Tie-breaker: Absolute likes count
    
    Logic: Neutral feedback often indicates satisfaction
    Best for: Balanced positive experience assessment
    """
    def combined_score(restaurant):
        sentiment = restaurant.sentiment
        total = sentiment.total_responses()
        return (sentiment.likes + sentiment.neutral) / total if total > 0 else 0
    
    return sorted(restaurants,
                 key=lambda r: (combined_score(r), r.sentiment.likes), 
                 reverse=True)
```

#### Candidate Selection & Recommendation
```python
def select_candidates_and_recommend(ranked_restaurants, count=20):
    """
    1. Select top N restaurants (default 20)
    2. If fewer than N available, use all
    3. Randomly select 1 from candidates for recommendation
    4. Return both candidate list and single recommendation
    """
    candidates = ranked_restaurants[:count]
    recommendation = random.choice(candidates) if candidates else None
    return candidates, recommendation
```

## 🔐 Security Features

### Authentication
- **JWT Authentication**: Secure token validation via Amazon Cognito
- **Configurable Auth**: Can be disabled for testing via `REQUIRE_AUTHENTICATION=false`
- **Bypass Paths**: Health check and metrics endpoints bypass authentication

### Configuration
```python
# Authentication configuration
auth_config = AuthenticationConfig(
    cognito_config={
        'user_pool_id': 'us-east-1_KePRX24Bn',
        'client_id': '1ofgeckef3po4i3us4j1m4chvd',
        'region': 'us-east-1',
        'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/...'
    },
    bypass_paths=['/health', '/metrics', '/docs'],
    require_authentication=True
)
```

## 📊 Monitoring & Health Checks

### Health Check Endpoint
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
    "status": "healthy",
    "service": "restaurant-reasoning-mcp",
    "version": "1.0.0",
    "timestamp": "2025-09-28T13:45:00.000Z",
    "components": {
        "reasoning_service": "operational",
        "authentication": "configured"
    }
}
```

### Metrics Endpoint
```bash
curl http://localhost:8080/metrics
```

**Response:**
```json
{
    "service": "restaurant-reasoning-mcp",
    "metrics": {
        "uptime": "operational",
        "tools_available": 2,
        "authentication_enabled": true
    },
    "timestamp": "2025-09-28T13:45:00.000Z"
}
```

## 🧪 Testing

### Comprehensive Test Suite
```bash
# Run all tests
python tests/run_comprehensive_tests.py

# Individual test categories
python -m pytest tests/test_reasoning_mcp_tools.py      # MCP tool tests
python -m pytest tests/test_restaurant_reasoning_service.py  # Service tests
python -m pytest tests/test_auth_service.py            # Authentication tests
python -m pytest tests/test_reasoning_deployment.py    # Deployment tests
```

### Test Data Generation
```bash
# Generate test restaurant data
python tests/generate_test_data.py
```

### Integration Testing
```bash
# Test deployed reasoning server
python tests/test_reasoning_integration.py

# Test with authentication
python tests/test_reasoning_e2e_auth.py
```

## 🐳 Docker Configuration

### Dockerfile Features
- **ARM64 Platform**: Required for Amazon Bedrock AgentCore Runtime
- **UV Package Manager**: Fast Python dependency installation
- **OpenTelemetry**: Built-in observability instrumentation
- **Non-root User**: Security best practices
- **Multi-stage Build**: Optimized container size

### Environment Variables
```bash
# Required
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

# Optional
REQUIRE_AUTHENTICATION=true
PYTHONPATH=/app
DOCKER_CONTAINER=1
```

### Build Commands
```bash
# Local build (cross-platform)
docker build --platform linux/arm64 -t restaurant-reasoning-mcp .

# Production build with BuildKit
docker buildx build --platform linux/arm64 -t restaurant-reasoning-mcp .

# Multi-platform build
docker buildx build --platform linux/arm64,linux/amd64 -t restaurant-reasoning-mcp .
```

## 🔧 Troubleshooting Guide

### Reasoning-Specific Issues

#### 1. Invalid Restaurant Data Format
**Problem**: "Missing required field" or "Invalid sentiment structure" errors
**Symptoms**: 
- Tool returns validation errors
- Empty recommendation results
- JSON parsing failures

**Solution**:
```python
# Validate restaurant data format
def validate_restaurant_format(restaurant):
    required_fields = ['id', 'name', 'sentiment']
    for field in required_fields:
        if field not in restaurant:
            print(f"Missing required field: {field}")
            return False
    
    # Validate sentiment structure
    sentiment = restaurant['sentiment']
    sentiment_fields = ['likes', 'dislikes', 'neutral']
    for field in sentiment_fields:
        if field not in sentiment:
            print(f"Missing sentiment field: {field}")
            return False
        if not isinstance(sentiment[field], int) or sentiment[field] < 0:
            print(f"Invalid sentiment {field}: must be non-negative integer")
            return False
    
    return True

# Test your data
restaurants = [{"id": "test", "name": "Test Restaurant", "sentiment": {"likes": 10, "dislikes": 2, "neutral": 5}}]
for restaurant in restaurants:
    if not validate_restaurant_format(restaurant):
        print(f"Invalid restaurant: {restaurant}")
```

#### 2. Empty or No Valid Candidates
**Problem**: "No valid candidates available" error
**Symptoms**:
- Recommendation returns empty results
- All restaurants filtered out during validation

**Diagnosis & Solutions**:
```python
# Check if restaurants have sentiment data
def diagnose_empty_candidates(restaurants):
    print(f"Total restaurants provided: {len(restaurants)}")
    
    valid_count = 0
    for i, restaurant in enumerate(restaurants):
        try:
            sentiment = restaurant.get('sentiment', {})
            total_responses = sentiment.get('likes', 0) + sentiment.get('dislikes', 0) + sentiment.get('neutral', 0)
            
            if total_responses == 0:
                print(f"Restaurant {i}: No sentiment responses (likes=0, dislikes=0, neutral=0)")
            else:
                valid_count += 1
                print(f"Restaurant {i}: Valid ({total_responses} total responses)")
                
        except Exception as e:
            print(f"Restaurant {i}: Error - {e}")
    
    print(f"Valid restaurants: {valid_count}/{len(restaurants)}")
    return valid_count > 0

# Test your data
diagnose_empty_candidates(your_restaurants)
```

#### 3. Ranking Method Issues
**Problem**: Unexpected ranking results or "Invalid ranking method" errors
**Symptoms**:
- Results don't match expected order
- Ranking method parameter rejected

**Solutions**:
```python
# Valid ranking methods
VALID_RANKING_METHODS = ["sentiment_likes", "combined_sentiment"]

# Test ranking methods
def test_ranking_methods(restaurants):
    for method in VALID_RANKING_METHODS:
        try:
            result = recommend_restaurants(restaurants, method)
            print(f"✅ {method}: Success - {len(result['candidates'])} candidates")
        except Exception as e:
            print(f"❌ {method}: Error - {e}")

# Debug ranking results
def debug_ranking(restaurants, method="sentiment_likes"):
    print(f"Ranking by: {method}")
    
    for restaurant in restaurants:
        sentiment = restaurant['sentiment']
        likes = sentiment['likes']
        total = likes + sentiment['dislikes'] + sentiment['neutral']
        
        if method == "sentiment_likes":
            score = likes
        else:  # combined_sentiment
            score = (likes + sentiment['neutral']) / total * 100 if total > 0 else 0
            
        print(f"{restaurant['name']}: Score={score}, Likes={likes}, Total={total}")
```

#### 4. Sentiment Analysis Calculation Errors
**Problem**: Incorrect percentage calculations or division by zero
**Symptoms**:
- Unexpected sentiment percentages
- Mathematical errors in analysis

**Solutions**:
```python
# Validate sentiment calculations
def validate_sentiment_calculations(restaurants):
    for restaurant in restaurants:
        sentiment = restaurant['sentiment']
        likes = sentiment['likes']
        dislikes = sentiment['dislikes'] 
        neutral = sentiment['neutral']
        total = likes + dislikes + neutral
        
        if total == 0:
            print(f"⚠️  {restaurant['name']}: Zero total responses - will be excluded")
            continue
            
        likes_pct = (likes / total) * 100
        combined_pct = ((likes + neutral) / total) * 100
        
        print(f"✅ {restaurant['name']}:")
        print(f"   Likes: {likes}/{total} ({likes_pct:.1f}%)")
        print(f"   Combined Positive: {likes + neutral}/{total} ({combined_pct:.1f}%)")

validate_sentiment_calculations(your_restaurants)
```

### General System Issues

#### 5. Import and Module Errors
**Problem**: Module import failures
**Solution**: 
```bash
# Set Python path
export PYTHONPATH=/path/to/restaurant-search-result-reasoning-mcp

# Test imports
python -c "import restaurant_reasoning_mcp_server; print('✅ Server import OK')"
python -c "from services.restaurant_reasoning_service import RestaurantReasoningService; print('✅ Service import OK')"
python -c "from models.restaurant_models import Restaurant, Sentiment; print('✅ Models import OK')"
```

#### 6. Authentication Failures
**Problem**: JWT token validation errors
**Solution**:
```bash
# Check Cognito configuration
python -c "from services.auth_service import AuthService; AuthService().validate_config()"

# Test with auth disabled for debugging
export REQUIRE_AUTHENTICATION=false
python restaurant_reasoning_mcp_server.py

# Validate JWT token manually
python -c "
from services.auth_service import TokenValidator
validator = TokenValidator()
# Test with your token
result = validator.validate_token('your-jwt-token-here')
print(f'Token valid: {result.is_valid}')
"
```

#### 7. Docker ARM64 Build Issues
**Problem**: Platform compatibility errors for AgentCore deployment
**Solution**:
```bash
# Enable Docker BuildKit
export DOCKER_BUILDKIT=1

# Build with explicit ARM64 platform (required for AgentCore)
docker build --platform linux/arm64 -t restaurant-reasoning-mcp .

# Test multi-platform build
docker buildx create --use
docker buildx build --platform linux/arm64,linux/amd64 -t restaurant-reasoning-mcp .

# Verify platform
docker inspect restaurant-reasoning-mcp | grep Architecture
```

#### 8. MCP Tool Registration Issues
**Problem**: Tools not appearing or schema generation failures
**Solution**:
```python
# Test MCP tool registration
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test-server")

# Verify tools are registered
@mcp.tool()
def test_tool(message: str) -> str:
    return f"Echo: {message}"

# Check tool schemas
print("Registered tools:")
for tool_name in mcp._tools:
    print(f"- {tool_name}")

# Avoid FastAPI-specific parameters in tool functions
# ❌ Don't do this:
# def bad_tool(request: Request, data: str) -> str:
#     return data

# ✅ Do this instead:
# def good_tool(data: str) -> str:
#     return data
```

### Performance Troubleshooting

#### 9. Slow Response Times
**Problem**: Tool execution takes too long
**Diagnosis**:
```python
import time

def benchmark_reasoning(restaurants, iterations=10):
    """Benchmark reasoning performance"""
    
    methods = ["sentiment_likes", "combined_sentiment"]
    
    for method in methods:
        times = []
        for i in range(iterations):
            start = time.time()
            try:
                result = recommend_restaurants(restaurants, method)
                end = time.time()
                times.append(end - start)
            except Exception as e:
                print(f"Error in iteration {i}: {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"{method}: Avg {avg_time:.3f}s ({len(restaurants)} restaurants)")

# Test with your data
benchmark_reasoning(your_restaurants)
```

**Optimization Tips**:
- Batch process multiple restaurants in single requests
- Use appropriate data structures for large datasets
- Consider caching for repeated queries
- Monitor memory usage with large restaurant lists

### Debugging Commands

```bash
# Complete system health check
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import restaurant_reasoning_mcp_server
    print('✅ Server module: OK')
except Exception as e:
    print(f'❌ Server module: {e}')

try:
    from services.restaurant_reasoning_service import RestaurantReasoningService
    service = RestaurantReasoningService()
    print('✅ Reasoning service: OK')
except Exception as e:
    print(f'❌ Reasoning service: {e}')

try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP('test')
    print('✅ FastMCP: OK')
except Exception as e:
    print(f'❌ FastMCP: {e}')
"

# Test reasoning with sample data
python -c "
from services.restaurant_reasoning_service import RestaurantReasoningService

service = RestaurantReasoningService()
test_restaurants = [
    {
        'id': 'test1',
        'name': 'Test Restaurant',
        'sentiment': {'likes': 10, 'dislikes': 2, 'neutral': 3}
    }
]

try:
    result = service.analyze_and_recommend(test_restaurants, 'sentiment_likes')
    print('✅ Reasoning test: OK')
    print(f'Candidates: {len(result.candidates)}')
    print(f'Recommendation: {result.recommendation.name}')
except Exception as e:
    print(f'❌ Reasoning test: {e}')
"

# Validate authentication configuration
python -c "
try:
    from services.auth_service import AuthService
    auth = AuthService()
    config = auth.get_config()
    print('✅ Auth config loaded')
    print(f'User Pool ID: {config.get(\"user_pool_id\", \"Not set\")}')
    print(f'Client ID: {config.get(\"client_id\", \"Not set\")}')
except Exception as e:
    print(f'❌ Auth config: {e}')
"
```

## 📁 Project Structure

```
restaurant-search-result-reasoning-mcp/
├── restaurant_reasoning_mcp_server.py   # Main MCP server
├── deploy_reasoning_agentcore.py        # AgentCore deployment
├── Dockerfile                           # ARM64 container config
├── requirements.txt                     # Python dependencies
├── cognito_config.json                  # Authentication config
├── .bedrock_agentcore.yaml             # AgentCore configuration
├── services/                           # Business logic
│   ├── restaurant_reasoning_service.py # Main reasoning engine
│   ├── recommendation_service.py       # Recommendation algorithms
│   ├── sentiment_service.py           # Sentiment analysis
│   ├── validation_service.py          # Input validation
│   ├── auth_service.py                # Authentication
│   ├── auth_middleware.py             # Auth middleware
│   ├── auth_error_handler.py          # Error handling
│   └── security_monitor.py            # Security monitoring
├── models/                             # Data models
│   ├── restaurant_models.py           # Restaurant/sentiment models
│   ├── validation_models.py           # Validation models
│   └── auth_models.py                 # Authentication models
├── tests/                              # Comprehensive test suite
│   ├── run_comprehensive_tests.py     # Test runner
│   ├── test_reasoning_mcp_tools.py    # MCP tool tests
│   ├── test_restaurant_reasoning_service.py # Service tests
│   ├── test_reasoning_deployment.py   # Deployment tests
│   ├── test_reasoning_integration.py  # Integration tests
│   ├── test_auth_*.py                 # Authentication tests
│   └── generate_test_data.py          # Test data generation
└── docs/                               # Documentation
    └── API_REFERENCE.md               # Detailed API docs
```

## 🔄 Development Workflow

### 1. Local Development
```bash
# Setup environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run server locally
python restaurant_reasoning_mcp_server.py

# Test in another terminal
python tests/test_reasoning_mcp_tools.py
```

### 2. Docker Testing
```bash
# Build and test container
docker build --platform linux/arm64 -t reasoning-test .
docker run -p 8080:8080 reasoning-test

# Test container
curl http://localhost:8080/health
```

### 3. AWS Deployment
```bash
# Deploy to AgentCore
python deploy_reasoning_agentcore.py

# Validate deployment
python tests/test_reasoning_deployment.py
```

## 📈 Performance Considerations

### Optimization Tips
- **Batch Processing**: Process multiple restaurants in single requests
- **Caching**: Implement response caching for repeated queries
- **Async Processing**: Use async patterns for I/O operations
- **Resource Limits**: Configure appropriate memory/CPU limits

### Scaling Guidelines
- **Horizontal Scaling**: AgentCore handles auto-scaling
- **Memory Usage**: ~100MB base + ~1MB per 100 restaurants
- **CPU Usage**: Minimal for sentiment calculations
- **Network**: Optimize for batch requests vs individual calls

## 🔗 Integration Examples

### Kiro IDE Integration
```python
# Use MCP tools directly in Kiro
restaurants = [
    {"id": "r1", "name": "Restaurant A", "sentiment": {"likes": 50, "dislikes": 5, "neutral": 10}},
    {"id": "r2", "name": "Restaurant B", "sentiment": {"likes": 30, "dislikes": 15, "neutral": 8}}
]

# Get recommendations
recommendations = mcp_restaurant_search_mcp_search_restaurants_combined(
    districts=None,
    meal_types=None
)

# Analyze with reasoning
analysis = recommend_restaurants(restaurants, "sentiment_likes")
```

### Foundation Model Integration
```python
# Natural language queries processed by foundation models
# "Analyze these restaurants and recommend the best one based on customer satisfaction"
# "Which restaurant has the most positive sentiment?"
# "Rank these restaurants by customer likes"
```

## 📚 Additional Resources

- **[Usage Examples & Integration Patterns](docs/USAGE_EXAMPLES.md)** - Comprehensive integration guide with BedrockAgentCoreApp
- **[API Reference](docs/API_REFERENCE.md)** - Detailed API documentation  
- **[Authentication Usage Examples](docs/AUTHENTICATION_USAGE_EXAMPLES.md)** - Authentication integration patterns
- **[Cognito Setup Guide](docs/COGNITO_SETUP_GUIDE.md)** - Step-by-step authentication setup
- **[Integration Examples](docs/INTEGRATION_EXAMPLES.md)** - Framework-specific integration patterns
- **[Troubleshooting Guide](docs/TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions

---

**Project Status**: ✅ Production Ready  
**Last Updated**: September 28, 2025  
**Version**: 1.0.0  
**Platform**: linux/arm64 (AgentCore Compatible)