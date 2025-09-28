# MBTI Travel Assistant MCP - Project Structure

## Overview

This project implements the MBTI Travel Assistant as a BedrockAgentCore runtime service that receives HTTP requests from web servers and uses an internal LLM agent to orchestrate MCP client calls to existing MCP servers for restaurant search and sentiment analysis.

## Directory Structure

```
mbti_travel_assistant_mcp/
├── __init__.py                     # Package initialization
├── main.py                         # BedrockAgentCore runtime entrypoint
├── requirements.txt                # Python dependencies
├── Dockerfile                      # ARM64 container configuration
├── .bedrock_agentcore.yaml        # AgentCore configuration
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore patterns
├── .dockerignore                   # Docker ignore patterns
├── PROJECT_STRUCTURE.md            # This file
├── README.md                       # Project documentation
│
├── config/                         # Configuration management
│   ├── __init__.py
│   └── settings.py                 # Application settings and environment variables
│
├── models/                         # Data models and schemas
│   ├── __init__.py
│   ├── restaurant_models.py        # Restaurant and sentiment data models
│   ├── request_models.py           # HTTP request/response models
│   └── auth_models.py              # Authentication models
│
├── services/                       # Business logic services
│   ├── __init__.py
│   ├── mcp_client_manager.py       # MCP client connection management
│   ├── restaurant_agent.py         # Internal LLM agent with Strands
│   ├── auth_service.py             # JWT authentication handler
│   ├── response_formatter.py       # JSON response formatting
│   ├── cache_service.py            # Response caching service
│   └── error_handler.py            # Error handling and resilience
│
├── scripts/                        # Deployment and utility scripts
│   ├── __init__.py
│   ├── deploy_agentcore.py         # AgentCore deployment script
│   ├── setup_cognito.py            # Cognito User Pool setup
│   └── health_check.py             # Health check utilities
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── test_mcp_client_manager.py  # MCP client tests
│   ├── test_restaurant_agent.py    # Agent tests
│   ├── test_auth_service.py        # Authentication tests
│   ├── test_response_formatter.py  # Response formatting tests
│   ├── test_integration.py         # Integration tests
│   └── test_e2e.py                 # End-to-end tests
│
└── docs/                           # Documentation
    ├── __init__.py
    ├── API_REFERENCE.md            # API documentation
    ├── DEPLOYMENT_GUIDE.md         # Deployment instructions
    ├── INTEGRATION_EXAMPLES.md     # Usage examples
    └── TROUBLESHOOTING.md          # Troubleshooting guide
```

## Key Components

### Core Files

- **`main.py`**: BedrockAgentCore runtime entrypoint with @app.entrypoint decorator
- **`requirements.txt`**: Python dependencies including bedrock-agentcore, strands-agents, and MCP client libraries
- **`Dockerfile`**: ARM64 container configuration required for AgentCore Runtime
- **`.bedrock_agentcore.yaml`**: AgentCore configuration with authentication and observability settings

### Configuration (`config/`)

- **`settings.py`**: Centralized configuration management using Pydantic BaseSettings
- Environment-specific settings for MCP endpoints, authentication, caching, and runtime parameters

### Data Models (`models/`)

- **`restaurant_models.py`**: Restaurant, Sentiment, and OperatingHours data classes
- **`request_models.py`**: HTTP request/response models for frontend integration
- **`auth_models.py`**: JWT authentication and user context models

### Services (`services/`)

- **`mcp_client_manager.py`**: Manages MCP client connections to search and reasoning MCP servers
- **`restaurant_agent.py`**: Internal LLM agent using Strands framework for orchestration
- **`auth_service.py`**: JWT token validation and Cognito integration
- **`response_formatter.py`**: Formats responses for frontend consumption
- **`cache_service.py`**: Response caching with TTL and invalidation
- **`error_handler.py`**: Comprehensive error handling and retry logic

### Testing (`tests/`)

- Unit tests for individual components with 90%+ coverage
- Integration tests with actual MCP server connections
- End-to-end tests for complete workflow validation
- Performance and load testing capabilities

### Documentation (`docs/`)

- API reference documentation
- Deployment and integration guides
- Troubleshooting and operational guides

## Architecture Patterns

### BedrockAgentCore Runtime Pattern

The application follows the standard AgentCore runtime pattern:

1. **HTTP Entrypoint**: `@app.entrypoint` decorator receives structured payloads
2. **Internal LLM Agent**: Strands Agent processes requests and orchestrates MCP calls
3. **MCP Client Integration**: Agent acts as MCP client to external MCP servers
4. **Structured Response**: JSON responses optimized for frontend consumption

### MCP Client Architecture

The internal LLM agent acts as an MCP client to communicate with existing MCP servers:

- **Search MCP Server**: `restaurant-search-mcp` for restaurant discovery
- **Reasoning MCP Server**: `restaurant-reasoning-mcp` for sentiment analysis and recommendations

### Authentication Flow

1. Web servers send HTTP requests with JWT tokens
2. JWT validation against Cognito User Pool
3. Authenticated context passed to internal LLM agent
4. MCP client calls include appropriate authentication

## Development Workflow

### Local Development

1. Copy `.env.example` to `.env` and configure settings
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `python main.py`
4. Test endpoints: `curl -X POST http://localhost:8080/invocations`

### Testing

1. Unit tests: `pytest tests/test_*.py`
2. Integration tests: `pytest tests/test_integration.py`
3. Coverage report: `pytest --cov=mbti_travel_assistant_mcp`

### Deployment

1. Build ARM64 container: `docker build --platform linux/arm64 -t mbti-travel-assistant .`
2. Deploy to AgentCore: `python scripts/deploy_agentcore.py`
3. Test deployment: `python tests/test_e2e.py`

## Dependencies

### Core Dependencies

- `bedrock-agentcore`: AgentCore SDK for runtime implementation
- `strands-agents`: Internal LLM agent framework
- `mcp>=1.9.0`: Model Context Protocol client library
- `boto3`: AWS SDK for Cognito integration
- `httpx`: HTTP client for MCP connections

### Framework Dependencies

- `pydantic`: Data validation and settings management
- `PyJWT`: JWT token validation
- `redis`: Caching backend
- `structlog`: Structured logging

### Development Dependencies

- `pytest`: Testing framework
- `black`: Code formatting
- `flake8`: Linting
- `mypy`: Type checking

## Configuration Management

The application uses environment-based configuration with Pydantic BaseSettings:

- Development: `.env` file with local settings
- Staging/Production: Environment variables in container/runtime
- Secrets: AWS Secrets Manager integration for sensitive data

## Security Considerations

- JWT token validation with Cognito User Pool integration
- Secure MCP client authentication
- Input validation and sanitization
- Comprehensive audit logging
- Container security with non-root user

## Monitoring and Observability

- OpenTelemetry integration for tracing
- CloudWatch metrics and dashboards
- Structured logging with correlation IDs
- Health check endpoints for monitoring
- Performance metrics collection

## Deployment Requirements

- **Platform**: ARM64 architecture required for AgentCore Runtime
- **Container**: Docker with multi-stage builds
- **Authentication**: Cognito User Pool configuration
- **Networking**: Public or private network modes supported
- **Observability**: CloudWatch and X-Ray integration