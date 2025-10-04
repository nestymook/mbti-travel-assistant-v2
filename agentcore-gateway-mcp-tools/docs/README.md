# AgentCore Gateway MCP Tools - Documentation

## Overview

This directory contains comprehensive documentation for the AgentCore Gateway MCP Tools, a RESTful API Gateway that exposes restaurant search and reasoning MCP tools through HTTP endpoints with JWT authentication.

## Documentation Structure

### 📚 Core Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [API Documentation](API_DOCUMENTATION.md) | Complete API reference with endpoints, schemas, and examples | Developers, Integrators |
| [Deployment Guide](DEPLOYMENT_GUIDE.md) | Step-by-step deployment instructions for AgentCore Runtime | DevOps, System Administrators |
| [Authentication Guide](AUTHENTICATION_GUIDE.md) | JWT authentication setup and token management | Developers, Security Teams |
| [Integration Examples](INTEGRATION_EXAMPLES.md) | Code examples for various programming languages and frameworks | Developers |
| [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) | Common issues, diagnostic tools, and solutions | All Users |

### 🔧 Technical Specifications

| File | Description | Format |
|------|-------------|---------|
| [openapi.yaml](openapi.yaml) | OpenAPI 3.0 specification for API documentation | YAML |
| [Tool Metadata System](TOOL_METADATA_SYSTEM.md) | Foundation model integration metadata | Markdown |
| [Error Handling System](ERROR_HANDLING_SYSTEM.md) | Comprehensive error handling documentation | Markdown |
| [Observability System](OBSERVABILITY_SYSTEM.md) | Monitoring and logging implementation | Markdown |

## Quick Start

### 1. For Developers

```bash
# 1. Read the API documentation
open API_DOCUMENTATION.md

# 2. Check integration examples for your language
open INTEGRATION_EXAMPLES.md

# 3. Set up authentication
open AUTHENTICATION_GUIDE.md
```

### 2. For DevOps Teams

```bash
# 1. Follow deployment guide
open DEPLOYMENT_GUIDE.md

# 2. Set up monitoring
open OBSERVABILITY_SYSTEM.md

# 3. Prepare troubleshooting tools
open TROUBLESHOOTING_GUIDE.md
```

### 3. For System Integrators

```bash
# 1. Review API specification
open openapi.yaml

# 2. Understand authentication flow
open AUTHENTICATION_GUIDE.md

# 3. Implement error handling
open ERROR_HANDLING_SYSTEM.md
```

## API Overview

The AgentCore Gateway provides the following capabilities:

### 🔍 Restaurant Search
- **District Search**: Find restaurants in specific Hong Kong districts
- **Meal Type Search**: Search by breakfast, lunch, or dinner availability
- **Combined Search**: Filter by both district and meal type

### 🧠 Restaurant Reasoning
- **Recommendations**: Get intelligent recommendations based on sentiment analysis
- **Sentiment Analysis**: Analyze customer satisfaction patterns

### 🛠️ System Features
- **Health Monitoring**: Service health checks and status
- **Tool Metadata**: Foundation model integration information
- **Metrics**: Operational statistics and performance data

## Authentication

All API endpoints require JWT authentication using AWS Cognito User Pool:

- **User Pool ID**: `us-east-1_KePRX24Bn`
- **Client ID**: `1ofgeckef3po4i3us4j1m4chvd`
- **Region**: `us-east-1`

```http
Authorization: Bearer <jwt_token>
```

## Base URLs

- **Production**: `https://your-gateway.amazonaws.com`
- **Development**: `http://localhost:8080`

## Interactive Documentation

The API provides interactive documentation through:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## Code Examples

### Python
```python
from agentcore_client import AgentCoreGatewayClient

client = AgentCoreGatewayClient(
    base_url='https://your-gateway.amazonaws.com',
    jwt_token='your_jwt_token'
)

# Search restaurants
results = await client.search_by_district(['Central district'])

# Get recommendations
recommendations = await client.get_recommendations(
    restaurants=results.data.restaurants,
    ranking_method='sentiment_likes'
)
```

### JavaScript/TypeScript
```typescript
import { AgentCoreGatewayClient } from './agentcore-client';

const client = new AgentCoreGatewayClient(
  'https://your-gateway.amazonaws.com',
  'your_jwt_token'
);

// Search restaurants
const results = await client.searchByDistrict(['Central district']);

// Get recommendations
const recommendations = await client.getRecommendations(
  results.data.restaurants,
  'sentiment_likes'
);
```

### cURL
```bash
# Search restaurants by district
curl -X POST "https://your-gateway.amazonaws.com/api/v1/restaurants/search/district" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"districts": ["Central district"]}'

# Get recommendations
curl -X POST "https://your-gateway.amazonaws.com/api/v1/restaurants/recommend" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "restaurants": [...],
    "ranking_method": "sentiment_likes"
  }'
```

## Error Handling

All API responses follow a consistent error format:

```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid district names provided",
    "details": {
      "invalid_districts": ["NonExistent District"],
      "available_districts": ["Central district", "Admiralty"]
    },
    "timestamp": "2025-01-03T10:30:00Z",
    "request_id": "req_12345"
  }
}
```

## Rate Limiting

- **Rate Limit**: 100 requests per minute per user
- **Burst Limit**: 20 requests per 10 seconds
- **Headers**: Rate limit information included in responses

## Available Districts

The API supports the following Hong Kong districts:

- Central district
- Admiralty
- Causeway Bay
- Wan Chai
- Tsim Sha Tsui
- Mong Kok
- Yau Ma Tei
- Jordan

## Meal Types

The API recognizes three meal types based on operating hours:

- **Breakfast**: 07:00-11:29
- **Lunch**: 11:30-17:29
- **Dinner**: 17:30-22:30

## Foundation Model Integration

The Gateway provides comprehensive tool metadata for AI model integration:

```bash
# Get tool metadata
curl -X GET "https://your-gateway.amazonaws.com/tools/metadata"
```

This endpoint returns detailed information about:
- Tool descriptions and purposes
- Parameter schemas and validation rules
- Response formats and examples
- MBTI personality integration guidance
- Use case scenarios

## Monitoring and Observability

### Health Checks
```bash
# Check service health
curl -X GET "https://your-gateway.amazonaws.com/health"
```

### Metrics
```bash
# Get operational metrics
curl -X GET "https://your-gateway.amazonaws.com/metrics"
```

### Logging
- **CloudWatch Logs**: Structured application logs
- **Access Logs**: Request/response logging
- **Error Logs**: Detailed error information
- **Performance Logs**: Response time and throughput metrics

## Testing

### Unit Tests
```bash
# Run unit tests
python -m pytest tests/unit/ -v
```

### Integration Tests
```bash
# Run integration tests
python -m pytest tests/integration/ -v
```

### Load Testing
```bash
# Run load tests
python tests/load_test.py --url https://your-gateway.amazonaws.com --token YOUR_TOKEN
```

## Development Tools

### Token Validation
```bash
# Validate JWT token
python scripts/validate_jwt_token.py --token YOUR_TOKEN
```

### Health Check Script
```bash
# Comprehensive health check
./scripts/health_check.sh
```

### Log Analysis
```bash
# Analyze application logs
python scripts/analyze_logs.py /path/to/logfile
```

## Deployment

### Prerequisites
- AWS Account with appropriate permissions
- Docker with ARM64 support
- AWS CLI configured
- AgentCore CLI installed

### Quick Deployment
```bash
# Clone repository
git clone https://github.com/your-org/agentcore-gateway-mcp-tools.git
cd agentcore-gateway-mcp-tools

# Deploy using automation script
python scripts/deploy_agentcore.py
```

### Manual Deployment
```bash
# Build ARM64 container
docker build --platform linux/arm64 -t agentcore-gateway-mcp-tools .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag agentcore-gateway-mcp-tools:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agentcore-gateway-mcp-tools:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/agentcore-gateway-mcp-tools:latest

# Deploy to AgentCore
agentcore launch --config .bedrock_agentcore.yaml
```

## Support and Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check JWT token validity and expiration
   - Verify Cognito User Pool configuration
   - See [Authentication Guide](AUTHENTICATION_GUIDE.md)

2. **API Request Failures**
   - Validate request parameters against schema
   - Check district names and meal types
   - See [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)

3. **Service Unavailable Errors**
   - Check MCP server connectivity
   - Verify network configuration
   - Implement retry logic with exponential backoff

### Debug Tools

- **Token Decoder**: Validate and inspect JWT tokens
- **Health Check**: Comprehensive service health validation
- **Load Tester**: Performance and stress testing
- **Log Analyzer**: Pattern analysis and error detection

### Getting Help

1. **Documentation**: Start with the relevant guide above
2. **Troubleshooting**: Check the [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
3. **Examples**: Review [Integration Examples](INTEGRATION_EXAMPLES.md)
4. **API Reference**: Consult [API Documentation](API_DOCUMENTATION.md)

## Contributing

### Documentation Updates

1. Update the relevant markdown files
2. Regenerate OpenAPI specification if needed
3. Test all code examples
4. Update version numbers and timestamps

### Code Examples

1. Ensure all examples are tested and working
2. Include error handling in examples
3. Provide both sync and async versions where applicable
4. Add comments explaining key concepts

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-03 | Initial release with complete documentation |

## License

This documentation is licensed under the MIT License. See the LICENSE file for details.

---

**Last Updated**: January 3, 2025  
**Documentation Version**: 1.0.0  
**API Version**: 1.0.0  
**AgentCore Runtime**: Compatible with latest version