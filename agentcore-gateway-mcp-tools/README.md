# AgentCore Gateway for MCP Tools

Amazon Bedrock AgentCore Gateway that exposes restaurant search and reasoning MCP tools through RESTful HTTP endpoints with JWT authentication.

## Overview

This Gateway service acts as a protocol translator, converting HTTP requests to MCP tool calls while maintaining JWT authentication, comprehensive logging, and error handling. It leverages existing MCP servers without requiring modifications to their implementations.

## Features

- RESTful API endpoints for all MCP tools
- JWT authentication using AWS Cognito
- Automatic retry logic with exponential backoff
- Comprehensive error handling and validation
- Tool metadata for foundation model integration
- CloudWatch metrics and observability
- ARM64 container support for AgentCore Runtime

## Architecture

The Gateway exposes the following MCP servers:
- **restaurant-search-mcp**: District and meal type search functionality
- **restaurant-search-result-reasoning-mcp**: Restaurant recommendation and sentiment analysis

## API Endpoints

### Restaurant Search
- `POST /api/v1/restaurants/search/district` - Search by district
- `POST /api/v1/restaurants/search/meal-type` - Search by meal type
- `POST /api/v1/restaurants/search/combined` - Combined search

### Restaurant Reasoning
- `POST /api/v1/restaurants/recommend` - Get restaurant recommendations
- `POST /api/v1/restaurants/analyze` - Analyze restaurant sentiment

### System Endpoints
- `GET /health` - Health check
- `GET /metrics` - Operational metrics
- `GET /tools/metadata` - Tool descriptions for foundation models

## Quick Start

1. Build the ARM64 container:
   ```bash
   docker build --platform linux/arm64 -t agentcore-gateway .
   ```

2. Deploy to AgentCore:
   ```bash
   python scripts/deploy_agentcore.py
   ```

3. Test the deployment:
   ```bash
   python tests/test_gateway_endpoints.py
   ```

## Configuration

The service uses the same Cognito User Pool configuration as existing MCP servers:
- User Pool ID: `us-east-1_KePRX24Bn`
- Client ID: `1ofgeckef3po4i3us4j1m4chvd`
- Region: `us-east-1`

## Development

See the individual component documentation in the `docs/` directory for detailed development guidelines.