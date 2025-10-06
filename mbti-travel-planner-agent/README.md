# MBTI Travel Planner Agent - AgentCore Integration

A travel planning agent that uses Amazon Nova Pro foundation model with direct AgentCore Runtime API integration for restaurant search and recommendation capabilities. This agent calls deployed AgentCore agents directly using the AgentCore Runtime API, eliminating the need for HTTP gateway intermediaries.

## 🚀 Features

- **Amazon Nova Pro Model**: Uses `amazon.nova-pro-v1:0` for enhanced reasoning capabilities
- **AgentCore Runtime Integration**: Direct API calls to deployed AgentCore agents
- **Environment-Aware Configuration**: Supports development, staging, and production environments
- **Comprehensive Error Handling**: Circuit breaker patterns and graceful fallback responses
- **Advanced Logging & Monitoring**: Structured logging with performance metrics and observability
- **JWT Authentication**: Automatic token management with Cognito integration
- **Performance Optimizations**: Connection pooling, caching, and parallel execution

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                MBTI Travel Planner Agent                       │
│                (Amazon Nova Pro Model)                         │
└─────────────────┬───────────────────────────────────────────────┘
                  │ AgentCore Runtime API
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              AgentCore Runtime Platform                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ restaurant_     │ restaurant_     │ Authentication &            │
│ search_agent    │ reasoning_agent │ Monitoring                  │
│ (mN8bgq2Y1j)    │ (MSns5D6SLE)    │ (JWT + Observability)       │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Key Components

1. **AgentCore Runtime Client** (`services/agentcore_runtime_client.py`)
   - Manages connections to target AgentCore agents
   - JWT authentication with automatic token refresh
   - Connection pooling and retry logic with exponential backoff
   - Circuit breaker pattern for resilience

2. **Authentication Manager** (`services/authentication_manager.py`)
   - Cognito JWT token management
   - Automatic token refresh with expiry checking
   - Thread-safe token caching
   - Authentication error handling

3. **AgentCore Tools** (`services/restaurant_search_tool.py`, `services/restaurant_reasoning_tool.py`)
   - Restaurant search using AgentCore agents
   - Restaurant reasoning with MBTI analysis
   - Central district workflow orchestration
   - Backward compatibility with existing interfaces

4. **Error Handling** (`services/agentcore_error_handler.py`)
   - Circuit breaker patterns
   - Graceful fallback mechanisms
   - Comprehensive error categorization
   - Retry logic with configurable backoff

5. **Configuration Management** (`config/agentcore_environment_config.py`)
   - Environment-specific AgentCore agent ARNs
   - Cognito authentication settings
   - Performance optimization parameters
   - Validation and defaults

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- AWS CLI configured with appropriate permissions
- Access to Amazon Bedrock Nova Pro model
- Docker (for containerized deployment)

### Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `bedrock-agentcore`: AgentCore SDK
- `strands-agents`: Agent framework
- `boto3`: AWS SDK for AgentCore Runtime API
- `pydantic`: Data validation and serialization
- `structlog`: Structured logging
- `aiohttp`: Async HTTP client for performance
- `pyjwt`: JWT token handling

## ⚙️ Configuration

### Environment Variables

The agent supports three deployment environments with different AgentCore configurations:

#### Development Environment
```bash
ENVIRONMENT=development
RESTAURANT_SEARCH_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-dev
RESTAURANT_REASONING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_agent-dev
COGNITO_USER_POOL_ID=us-east-1_KePRX24Bn
COGNITO_CLIENT_ID=1ofgeckef3po4i3us4j1m4chvd
LOG_LEVEL=DEBUG
```

#### Staging Environment
```bash
ENVIRONMENT=staging
RESTAURANT_SEARCH_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-staging
RESTAURANT_REASONING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_agent-staging
COGNITO_CLIENT_SECRET=your-cognito-client-secret
AGENTCORE_TIMEOUT=45
LOG_LEVEL=INFO
```

#### Production Environment
```bash
ENVIRONMENT=production
RESTAURANT_SEARCH_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j
RESTAURANT_REASONING_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE
COGNITO_CLIENT_SECRET=your-production-client-secret
AGENTCORE_TIMEOUT=60
AGENTCORE_MAX_RETRIES=3
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_RESPONSE_CACHING=true
LOG_LEVEL=INFO
```

### Configuration Files

- **Environment Settings**: `config/environments/agentcore_{environment}.env`
- **AgentCore Configuration**: `config/agentcore_environment_config.py`
- **Cognito Configuration**: `config/cognito_config.json`
- **AgentCore Deployment**: `.bedrock_agentcore.yaml`
- **Example Configuration**: `config/agentcore_config_example.py`

For complete environment variable documentation, see [AGENTCORE_CONFIG_README.md](config/AGENTCORE_CONFIG_README.md).

## 🚀 Deployment

### Quick Start

1. **Validate Configuration**
   ```bash
   python config/validate_agentcore_config.py production
   ```

2. **Test AgentCore Integration**
   ```bash
   python test_agentcore_integration.py
   ```

3. **Deploy Agent**
   ```bash
   agentcore deploy
   ```

### Manual Deployment

1. **Set Environment Variables**
   ```bash
   export ENVIRONMENT=production
   export COGNITO_CLIENT_SECRET=your-client-secret
   ```

2. **Deploy with AgentCore**
   ```bash
   agentcore deploy
   ```

3. **Verify Deployment**
   ```bash
   agentcore invoke '{"prompt": "Find restaurants in Central district"}'
   ```

### Docker Deployment

```dockerfile
FROM --platform=linux/arm64 python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "main.py"]
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/test_agentcore_runtime_client.py -v
python -m pytest tests/test_authentication_manager.py -v
python -m pytest tests/test_restaurant_search_tool.py -v
python -m pytest tests/test_restaurant_reasoning_tool.py -v
python -m pytest tests/test_agentcore_error_handler.py -v
```

### Integration Tests
```bash
python -m pytest tests/test_agentcore_integration.py -v
python -m pytest tests/test_central_district_workflow_agentcore.py -v
python -m pytest tests/test_agentcore_monitoring_integration.py -v
```

### End-to-End Testing
```bash
python test_agentcore_integration.py
python examples/central_district_workflow_agentcore_demo.py
```

## 📊 Monitoring & Observability

### Logging

The agent provides comprehensive structured logging with multiple levels:

- **DEBUG**: Detailed AgentCore API request/response information
- **INFO**: General operational information and agent invocations
- **WARNING**: Non-critical issues, fallbacks, and circuit breaker activations
- **ERROR**: Error conditions requiring attention
- **CRITICAL**: System failures and authentication issues

### Health Checks

Background health monitoring includes:
- AgentCore agent connectivity checks
- JWT token validation and refresh
- Circuit breaker status monitoring
- Performance metrics collection

### Metrics

Production deployments collect:
- AgentCore agent invocation times
- Success/failure rates by agent
- Authentication token refresh frequency
- Circuit breaker activation counts
- Connection pool utilization
- Response caching hit rates

## 🔧 Development

### Local Development Setup

1. **Configure Development Environment**
   ```bash
   export ENVIRONMENT=development
   export LOG_LEVEL=DEBUG
   export COGNITO_CLIENT_SECRET=your-dev-client-secret
   ```

2. **Test AgentCore Connectivity**
   ```bash
   python test_agentcore_integration.py
   ```

3. **Run Agent Locally**
   ```bash
   python main.py
   ```

4. **Run Development Examples**
   ```bash
   python examples/agentcore_client_demo.py
   python examples/restaurant_search_tool_demo.py
   ```

### Adding New Tools

1. **Create Tool Class** in `services/` (e.g., `new_tool.py`)
2. **Implement AgentCore Integration** using `AgentCoreRuntimeClient`
3. **Update Configuration** in `config/agentcore_environment_config.py`
4. **Add Tests** in `tests/test_new_tool.py`
5. **Create Demo** in `examples/new_tool_demo.py`

### Error Handling

All errors are categorized and handled with circuit breaker patterns:

```python
from services.agentcore_error_handler import AgentCoreErrorHandler

error_handler = AgentCoreErrorHandler("restaurant_search_tool")
result = await error_handler.handle_agent_error(
    error=exception,
    agent_arn="arn:aws:bedrock-agentcore:...",
    context={"operation": "search_restaurants"},
    fallback_response={"restaurants": [], "error": "Service temporarily unavailable"}
)
```

## 📚 API Reference

### AgentCore Restaurant Tools

#### Restaurant Search Tool
```python
from services.restaurant_search_tool import RestaurantSearchTool

search_tool = RestaurantSearchTool(runtime_client)
result = await search_tool.search_restaurants(
    districts=["Central district"],
    meal_types=["lunch", "dinner"]
)
```

#### Restaurant Reasoning Tool
```python
from services.restaurant_reasoning_tool import RestaurantReasoningTool

reasoning_tool = RestaurantReasoningTool(runtime_client)
recommendations = await reasoning_tool.get_recommendations(
    restaurants=restaurant_data,
    mbti_type="ENFP",
    preferences={"cuisine": "Asian", "price_range": "moderate"}
)
```

### Central District Workflow
```python
from services.central_district_workflow import CentralDistrictWorkflow

workflow = CentralDistrictWorkflow(search_tool, reasoning_tool)
result = await workflow.execute_workflow(
    mbti_type="ENFP",
    preferences={"meal_type": "lunch"}
)
```

## 🔒 Security

### Authentication

- Cognito JWT token authentication with automatic refresh
- Secure token storage and thread-safe refresh logic
- AgentCore Runtime API authentication
- Client secret management

### Network Security

- HTTPS-only communication with AgentCore Runtime API
- Connection pooling with secure defaults
- Request timeout limits and circuit breaker patterns
- TLS encryption for all agent communications

### Data Privacy

- No sensitive data in logs (JWT tokens masked)
- Secure credential management with environment variables
- Proper error message sanitization
- Compliance with AWS security best practices

## 🐛 Troubleshooting

### Common Issues

#### AgentCore Connection Errors
```bash
# Check AgentCore agent connectivity
python test_agentcore_integration.py

# Validate configuration
python config/validate_agentcore_config.py production

# Test specific agent
agentcore invoke --agent-arn arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j '{"prompt": "test"}'
```

#### Authentication Failures
```bash
# Verify Cognito configuration
python -c "from services.authentication_manager import AuthenticationManager; from config.agentcore_environment_config import get_cognito_config; auth = AuthenticationManager(get_cognito_config('production')); print('Auth configured')"

# Test JWT token refresh
python examples/agentcore_client_demo.py
```

#### Configuration Issues
```bash
# Validate all AgentCore configuration
python config/validate_agentcore_config.py development

# Test environment configuration loading
python -c "from config.agentcore_environment_config import get_agentcore_config; print(get_agentcore_config('development'))"
```

### Debug Mode

Enable debug logging for detailed troubleshooting:
```bash
export LOG_LEVEL=DEBUG
export ENABLE_AGENTCORE_REQUEST_TRACING=true
export ENABLE_JWT_DEBUG_LOGGING=true
python main.py
```

## 📈 Performance

### Optimization Features

- AgentCore Runtime API connection pooling
- Response caching for repeated queries
- Parallel agent execution where possible
- Optimized JWT token refresh to minimize overhead
- Circuit breaker patterns for resilience

### Performance Monitoring

Production deployments include:
- AgentCore agent invocation time tracking
- Success/failure rates by agent
- Authentication token refresh monitoring
- Circuit breaker activation tracking
- Connection pool utilization metrics
- Response cache hit rates

## 🔄 Migration from HTTP Gateway

This agent has been updated from HTTP gateway integration to direct AgentCore Runtime API integration:

### Removed Dependencies
- HTTP gateway client libraries
- Gateway-specific authentication
- HTTP endpoint configuration

### Added Dependencies
- AgentCore Runtime API client
- Enhanced JWT authentication with Cognito
- Circuit breaker and resilience patterns

### Migration Benefits
- Native AgentCore ecosystem integration
- Better performance with direct agent calls
- Enhanced error handling and resilience
- Comprehensive observability and monitoring
- Automatic authentication token management

For detailed migration instructions, see [AGENTCORE_MIGRATION_GUIDE.md](AGENTCORE_MIGRATION_GUIDE.md).

## 📝 License

This project is part of the Amazon Bedrock AgentCore samples repository.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review configuration documentation
3. Run validation scripts
4. Check logs for detailed error information

---

**Last Updated**: October 6, 2025  
**Version**: 3.0.0 (AgentCore Runtime Integration)  
**Model**: Amazon Nova Pro v1.0  
**Architecture**: AgentCore Runtime API → Direct Agent Calls  
**Target Agents**: 
- `restaurant_search_agent-mN8bgq2Y1j`
- `restaurant_search_result_reasoning_agent-MSns5D6SLE`