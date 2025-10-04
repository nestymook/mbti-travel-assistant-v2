# MBTI Travel Planner Agent - HTTP Gateway Integration

A travel planning agent that uses Amazon Nova Pro foundation model with HTTP gateway integration for restaurant search and recommendation capabilities. This agent connects to the deployed agentcore-gateway-mcp-tools service instead of using direct MCP client connections.

## 🚀 Features

- **Amazon Nova Pro Model**: Uses `amazon.nova-pro-v1:0` for enhanced reasoning capabilities
- **HTTP Gateway Integration**: Direct API calls to agentcore-gateway-mcp-tools service
- **Environment-Aware Configuration**: Supports development, staging, and production environments
- **Comprehensive Error Handling**: User-friendly error messages and fallback responses
- **Advanced Logging & Monitoring**: Structured logging with performance metrics
- **Health Check System**: Background monitoring of gateway connectivity

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                MBTI Travel Planner Agent                       │
│                (Amazon Nova Pro Model)                         │
└─────────────────┬───────────────────────────────────────────────┘
                  │ HTTP API Calls
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              agentcore-gateway-mcp-tools                       │
│                    (HTTP Gateway)                              │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ Restaurant      │ Restaurant      │ Tool Metadata              │
│ Search          │ Recommendation  │ Management                 │
│ /search/district│ /recommend      │ /tools/metadata            │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Key Components

1. **HTTP Client Service** (`services/gateway_http_client.py`)
   - Handles all HTTP communication with the gateway
   - Environment-based endpoint configuration
   - Connection pooling and retry logic
   - Authentication token management

2. **Gateway Tools** (`services/gateway_tools.py`)
   - Restaurant search by district
   - Combined restaurant search (district + meal type)
   - Restaurant recommendation with sentiment analysis
   - Central district workflow integration

3. **Error Handling** (`services/error_handler.py`)
   - Comprehensive error categorization
   - User-friendly error messages
   - Fallback response generation
   - Logging integration

4. **Configuration Management** (`config/`)
   - Environment-specific settings
   - Gateway endpoint configuration
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
- `httpx`: HTTP client for gateway communication
- `pydantic`: Data validation and serialization
- `structlog`: Structured logging

## ⚙️ Configuration

### Environment Variables

The agent supports three deployment environments with different configurations:

#### Development Environment
```bash
ENVIRONMENT=development
GATEWAY_BASE_URL=http://localhost:8080
GATEWAY_AUTH_REQUIRED=false
LOG_LEVEL=DEBUG
```

#### Staging Environment
```bash
ENVIRONMENT=staging
GATEWAY_BASE_URL=https://agentcore-gateway-mcp-tools-staging.bedrock-agentcore.us-east-1.amazonaws.com
GATEWAY_AUTH_REQUIRED=true
GATEWAY_AUTH_TOKEN=your-staging-jwt-token
LOG_LEVEL=INFO
```

#### Production Environment
```bash
ENVIRONMENT=production
GATEWAY_BASE_URL=https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com
GATEWAY_AUTH_REQUIRED=true
GATEWAY_AUTH_TOKEN=your-production-jwt-token
LOG_LEVEL=INFO
ENABLE_METRICS_COLLECTION=true
```

### Configuration Files

- **Environment Settings**: `config/environments/{environment}.env`
- **Gateway Configuration**: `config/environments/gateway.json`
- **AgentCore Configuration**: `.bedrock_agentcore.yaml`
- **Example Configuration**: `config/example.env`

For complete environment variable documentation, see [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md).

## 🚀 Deployment

### Quick Start

1. **Validate Configuration**
   ```bash
   python scripts/validate_deployment_config.py production
   ```

2. **Deploy Agent**
   ```bash
   python scripts/deploy_with_http_gateway.py production
   ```

### Manual Deployment

1. **Set Environment Variables**
   ```bash
   export ENVIRONMENT=production
   export GATEWAY_AUTH_TOKEN=your-jwt-token
   ```

2. **Deploy with AgentCore**
   ```bash
   python -m bedrock_agentcore deploy
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
python -m pytest tests/test_gateway_http_client.py -v
python -m pytest tests/test_gateway_tools.py -v
python -m pytest tests/test_error_handling.py -v
```

### Integration Tests
```bash
python -m pytest tests/test_complete_workflow_integration.py -v
python -m pytest tests/test_nova_pro_integration.py -v
```

### End-to-End Testing
```bash
python test_central_district_workflow.py
python test_recommendation_functionality.py
```

## 📊 Monitoring & Observability

### Logging

The agent provides comprehensive logging with multiple levels:

- **DEBUG**: Detailed HTTP request/response information
- **INFO**: General operational information
- **WARNING**: Non-critical issues and fallbacks
- **ERROR**: Error conditions requiring attention
- **CRITICAL**: System failures

### Health Checks

Background health monitoring includes:
- Gateway connectivity checks
- HTTP endpoint availability
- Authentication token validation
- Performance metrics collection

### Metrics

Production deployments collect:
- HTTP request/response times
- Success/failure rates
- Error categorization
- Resource utilization

## 🔧 Development

### Local Development Setup

1. **Start Local Gateway** (if available)
   ```bash
   # Start local agentcore-gateway-mcp-tools instance
   cd ../agentcore-gateway-mcp-tools
   python main.py
   ```

2. **Configure Development Environment**
   ```bash
   export ENVIRONMENT=development
   export LOG_LEVEL=DEBUG
   ```

3. **Run Agent Locally**
   ```bash
   python main.py
   ```

### Adding New Tools

1. **Implement Tool Function** in `services/gateway_tools.py`
2. **Add HTTP Client Method** in `services/gateway_http_client.py`
3. **Update Configuration** in `config/environments/gateway.json`
4. **Add Tests** in `tests/`

### Error Handling

All errors are categorized and handled consistently:

```python
from services.error_handler import ErrorHandler, ErrorSeverity

error_handler = ErrorHandler("component_name")
result = error_handler.handle_error(
    error=exception,
    context={"operation": "restaurant_search"},
    severity=ErrorSeverity.WARNING
)
```

## 📚 API Reference

### Restaurant Search Tools

#### Search by District
```python
await search_restaurants_by_district_tool(districts=["Central district"])
```

#### Combined Search
```python
await search_restaurants_combined_tool(
    districts=["Central district"],
    meal_types=["lunch", "dinner"]
)
```

#### Restaurant Recommendations
```python
await recommend_restaurants_tool(
    restaurants=restaurant_data,
    ranking_method="sentiment_likes"
)
```

### Central District Workflow
```python
await central_district_workflow_tool(
    user_request="Find me good restaurants in Central for lunch"
)
```

## 🔒 Security

### Authentication

- JWT token authentication for staging/production
- Secure token storage and rotation
- Request/response validation

### Network Security

- HTTPS-only communication in production
- Connection pooling with secure defaults
- Request timeout limits

### Data Privacy

- No sensitive data in logs
- Secure credential management
- Proper error message sanitization

## 🐛 Troubleshooting

### Common Issues

#### Gateway Connection Errors
```bash
# Check gateway connectivity
python scripts/validate_deployment_config.py production

# Test specific endpoint
curl -X GET https://gateway-url/health
```

#### Authentication Failures
```bash
# Verify JWT token
export GATEWAY_AUTH_TOKEN=your-token
python -c "from services.gateway_http_client import GatewayHTTPClient; print('Token valid')"
```

#### Configuration Issues
```bash
# Validate all configuration
python scripts/validate_deployment_config.py development
```

### Debug Mode

Enable debug logging for detailed troubleshooting:
```bash
export LOG_LEVEL=DEBUG
export ENABLE_REQUEST_TRACING=true
python main.py
```

## 📈 Performance

### Optimization Features

- HTTP connection pooling
- Request/response caching
- Async HTTP operations
- Background health checks

### Performance Monitoring

Production deployments include:
- Response time tracking
- Throughput monitoring
- Error rate analysis
- Resource utilization metrics

## 🔄 Migration from MCP Client

This agent replaces the previous MCP client implementation with HTTP gateway integration:

### Removed Dependencies
- `mcp>=1.9.0`
- Direct Cognito authentication
- JWT token management complexity

### Added Dependencies
- `httpx>=0.25.0`
- `pydantic>=2.0.0`
- Simplified configuration

### Migration Benefits
- Simplified architecture
- Better error handling
- Improved monitoring
- Easier deployment

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

**Last Updated**: October 4, 2025  
**Version**: 2.0.0 (HTTP Gateway Integration)  
**Model**: Amazon Nova Pro v1.0  
**Architecture**: HTTP Gateway → MCP Tools