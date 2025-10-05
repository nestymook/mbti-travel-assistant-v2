# MBTI Travel Assistant MCP

A BedrockAgentCore runtime service that generates personalized 3-day Hong Kong travel itineraries based on MBTI personality types. The service uses Amazon Nova Pro foundation model to query knowledge bases for personality-matched tourist spots and integrates with MCP servers for restaurant recommendations.

## 🚀 **DEPLOYED TO AWS AGENTCORE** ✅

**Deployment Status**: FULLY OPERATIONAL  
**Agent ARN**: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_assistant_mcp-skv6fd785E`  
**Region**: us-east-1  
**Platform**: linux/arm64  
**Authentication**: JWT (AWS Cognito)  
**Last Deployed**: September 30, 2025  

## Overview

The MBTI Travel Assistant operates as a Bedrock AgentCore runtime that receives MBTI personality parameters and generates comprehensive 3-day travel itineraries. It combines personality-matched tourist spots from knowledge bases with intelligent restaurant recommendations through MCP integration.

### Key Features

- **🎭 MBTI Personality Processing**: Supports all 16 MBTI personality types with personalized recommendations
- **📅 3-Day Itinerary Generation**: Complete 3-day × 6-session travel itineraries (morning, afternoon, night + meals)
- **🧠 Amazon Nova Pro Integration**: Uses Nova Pro 300K foundation model for knowledge base queries
- **🏛️ Tourist Spot Matching**: Personality-matched tourist spots with MBTI compatibility scoring
- **🍽️ Restaurant Integration**: MCP client integration for intelligent restaurant recommendations
- **🔐 JWT Authentication**: Secure authentication via AWS Cognito User Pool integration
- **📊 Structured Responses**: JSON responses optimized for frontend web applications
- **⚡ Performance Optimized**: Caching, parallel processing, and connection pooling
- **🔍 Comprehensive Error Handling**: Graceful handling of failures with meaningful error messages

## Architecture

```
Web Frontend → JWT Auth → AgentCore Runtime → Nova Pro Model → Knowledge Base (Tourist Spots)
                                    ↓                              ↓
                            MBTI Processor → Itinerary Generator → MCP Clients → Restaurant MCPs
                                    ↓                              ↓
Frontend ← 3-Day Itinerary ← Response Formatter ← Session Assignment ← Restaurant Recommendations
```

### Current Deployment Architecture

```
🌐 Frontend (Vue 3 + TypeScript)
    ↓ HTTPS + JWT
🔐 AWS Cognito Authentication
    ↓ Authenticated Requests
☁️ Amazon Bedrock AgentCore Runtime
    ├── 🎭 MBTI Travel Assistant (DEPLOYED)
    │   ├── 🧠 Amazon Nova Pro 300K Model
    │   ├── 📚 OpenSearch Knowledge Base (Tourist Spots)
    │   └── 🔄 MCP Client Manager
    └── 🍽️ MCP Server Integration
        ├── 🔍 Restaurant Search MCP (DEPLOYED)
        └── 🧠 Restaurant Reasoning MCP (DEPLOYED)
```

### MCP Server Integration

The MBTI Travel Assistant acts as an MCP client to communicate with:

1. **Restaurant Search MCP Server** (`restaurant-search-mcp`): For restaurant discovery by district and meal type
2. **Restaurant Reasoning MCP Server** (`restaurant-reasoning-mcp`): For sentiment analysis and recommendations
3. **Knowledge Base Integration**: Direct queries to OpenSearch for MBTI-matched tourist spots

## Quick Start

### Prerequisites

- AWS account with configured credentials
- Bedrock model access (Anthropic Claude 3.5 Sonnet)
- Docker installed for containerization
- Python 3.12+ environment

### Installation

1. **Clone and setup**:
   ```bash
   cd mbti_travel_assistant_mcp
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure MCP endpoints**:
   ```bash
   # Update .env with your MCP server endpoints
   SEARCH_MCP_ENDPOINT=http://your-search-mcp-server:8000
   REASONING_MCP_ENDPOINT=http://your-reasoning-mcp-server:8000
   ```

### Local Development

1. **Run locally**:
   ```bash
   python main.py
   ```

2. **Test the service**:
   ```bash
   curl -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{"district": "Central district", "meal_time": "breakfast"}'
   ```

### Deployment

#### ✅ Current Production Deployment

The MBTI Travel Assistant is **DEPLOYED and OPERATIONAL** on AWS AgentCore:

```bash
# Check deployment status
python check_deployment_status.py

# Test complete workflow
python test_complete_mbti_workflow.py

# Test MBTI itinerary generation
python test_mbti_itinerary.py
```

**Deployment Details**:
- **Status**: ✅ READY (Both Agent and Endpoint)
- **Agent ARN**: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_assistant_mcp-skv6fd785E`
- **Region**: us-east-1
- **Platform**: linux/arm64 (CodeBuild deployment)
- **Authentication**: JWT with Cognito User Pool `us-east-1_KePRX24Bn`
- **Model**: Amazon Nova Pro 300K
- **Observability**: Enabled with CloudWatch and X-Ray

#### Manual Deployment (if needed)

1. **Deploy to AgentCore**:
   ```bash
   python deploy_mbti_agentcore.py
   ```

2. **Monitor deployment**:
   ```bash
   python deploy_mbti_agentcore.py --status-only
   ```

3. **Test deployment**:
   ```bash
   python test_deployed_agent.py
   ```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# MCP Client Configuration
SEARCH_MCP_ENDPOINT=http://localhost:8001
REASONING_MCP_ENDPOINT=http://localhost:8002

# Authentication
COGNITO_USER_POOL_ID=us-east-1_example123
COGNITO_REGION=us-east-1

# Agent Configuration
AGENT_MODEL=amazon.nova-pro-v1:0:300k
AGENT_TEMPERATURE=0.1

# Caching
CACHE_ENABLED=true
CACHE_TTL=1800
```

### AgentCore Configuration

The `.bedrock_agentcore.yaml` file configures:

- ARM64 platform requirement
- JWT authentication with Cognito
- Observability and monitoring
- Resource allocation and scaling

## API Reference

### Request Format

```json
{
  "district": "Central district",
  "meal_time": "breakfast"
}
```

### Response Format

```json
{
  "recommendation": {
    "id": "rest_001",
    "name": "Great Breakfast Spot",
    "address": "123 Main St",
    "district": "Central district",
    "sentiment": {
      "likes": 85,
      "dislikes": 10,
      "neutral": 5
    },
    "price_range": "$$",
    "operating_hours": {
      "monday": ["07:00-11:30"]
    }
  },
  "candidates": [
    // 19 additional restaurant objects
  ],
  "metadata": {
    "search_criteria": {
      "district": "Central district",
      "meal_time": "breakfast"
    },
    "total_found": 20,
    "timestamp": "2024-01-15T10:30:00Z",
    "processing_time_ms": 1250
  }
}
```

### Error Response Format

```json
{
  "error": {
    "error_type": "mcp_server_unavailable",
    "message": "Restaurant search service is temporarily unavailable",
    "suggested_actions": [
      "Try again in a few moments",
      "Check service status"
    ],
    "error_code": "MCP_SEARCH_001"
  }
}
```

## Development

### Project Structure

```
mbti_travel_assistant_mcp/
├── main.py                    # AgentCore runtime entrypoint
├── config/settings.py         # Configuration management
├── models/                    # Data models and schemas
├── services/                  # Business logic services
├── tests/                     # Test suite
└── docs/                      # Documentation
```

### Testing

```bash
# Unit tests
pytest tests/test_*.py

# Integration tests
pytest tests/test_integration.py

# Coverage report
pytest --cov=mbti_travel_assistant_mcp

# End-to-end tests
pytest tests/test_e2e.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Sort imports
isort .
```

## Monitoring and Observability

### Health Checks

The service provides health check endpoints:

- `/health`: Basic health status
- `/health/detailed`: Detailed component health

### Metrics

Key metrics collected:

- Request processing time
- MCP client response times
- Authentication success/failure rates
- Cache hit/miss ratios
- Error rates by category

### Logging

Structured logging with correlation IDs:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Processing restaurant request",
  "correlation_id": "req_123456",
  "district": "Central district",
  "meal_time": "breakfast",
  "processing_time_ms": 1250
}
```

## Security

### Authentication

- JWT token validation via AWS Cognito User Pool
- Token caching with TTL for performance
- Secure token extraction from Authorization headers

### Data Protection

- Input validation and sanitization
- Secure logging (no sensitive data in logs)
- Encrypted communication with MCP servers

### Container Security

- Non-root user execution
- Minimal base image (ARM64 slim)
- Security scanning in CI/CD pipeline

## Troubleshooting

### Common Issues

1. **MCP Connection Failures**:
   - Check MCP server endpoints in configuration
   - Verify network connectivity
   - Review MCP server logs

2. **Authentication Errors**:
   - Validate Cognito User Pool configuration
   - Check JWT token format and expiration
   - Verify discovery URL accessibility

3. **Performance Issues**:
   - Monitor cache hit rates
   - Check MCP server response times
   - Review resource allocation

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following PEP8 style guidelines
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Review the [API Reference](docs/API_REFERENCE.md)
- Open an issue in the repository