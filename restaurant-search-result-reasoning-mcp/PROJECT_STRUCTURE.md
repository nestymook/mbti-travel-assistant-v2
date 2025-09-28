# Restaurant Search Result Reasoning MCP Server - Project Structure

This project provides intelligent restaurant recommendation services based on sentiment analysis using the Model Context Protocol (MCP) and AWS Bedrock AgentCore.

## Directory Structure

```
restaurant-search-result-reasoning-mcp/
├── __init__.py                                 # Package initialization
├── requirements.txt                            # Python dependencies
├── restaurant_reasoning_mcp_server.py          # Main FastMCP server
├── PROJECT_STRUCTURE.md                        # This file
├── models/                                     # Data models
│   ├── __init__.py
│   ├── restaurant_models.py                    # Restaurant and sentiment models
│   ├── validation_models.py                    # Validation and config models
│   └── auth_models.py                          # Authentication models
├── services/                                   # Business logic services
│   ├── __init__.py
│   ├── sentiment_service.py                    # Sentiment analysis logic
│   ├── recommendation_service.py               # Recommendation algorithms
│   ├── validation_service.py                   # Data validation
│   └── restaurant_reasoning_service.py         # Core reasoning service
├── src/                                        # Additional source code
│   └── __init__.py
└── tests/                                      # Test suite
    ├── __init__.py
    ├── test_sentiment_service.py               # Sentiment service tests
    ├── test_recommendation_service.py          # Recommendation tests
    ├── test_validation_service.py              # Validation tests
    ├── test_restaurant_reasoning_service.py    # Reasoning service tests
    └── test_reasoning_mcp_tools.py             # MCP tool tests
```

## Key Components

### Models
- **restaurant_models.py**: Sentiment, Restaurant, and RecommendationResult data models
- **validation_models.py**: ValidationResult, ValidationError, and ReasoningConfig models
- **auth_models.py**: Authentication models (CognitoConfig, JWTClaims, UserContext)

### Services
- **sentiment_service.py**: Core sentiment analysis functionality
- **recommendation_service.py**: Restaurant ranking algorithms
- **validation_service.py**: Restaurant data validator
- **restaurant_reasoning_service.py**: Main business logic service

### Main Server
- **restaurant_reasoning_mcp_server.py**: FastMCP server with reasoning tools

### Tests
- Comprehensive unit tests for all services and components
- MCP tool integration tests
- End-to-end reasoning workflow tests

## Dependencies

- mcp>=1.10.0: Model Context Protocol framework
- bedrock-agentcore: AWS Bedrock AgentCore SDK
- bedrock-agentcore-starter-toolkit: AgentCore development toolkit
- pydantic>=2.0.0: Data validation and serialization
- Additional dependencies for authentication and web services

## Implementation Status

This project structure is set up as part of task 1. Individual components will be implemented in subsequent tasks according to the implementation plan.