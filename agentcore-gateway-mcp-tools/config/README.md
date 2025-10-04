# AgentCore Gateway Native MCP Protocol Configuration

This directory contains configuration files for deploying an AWS Bedrock AgentCore Gateway that provides native MCP protocol routing to existing MCP servers without requiring protocol conversion.

## Overview

The AgentCore Gateway serves as an intelligent MCP protocol router, connecting AgentCore agents and foundation models directly to existing MCP servers through native MCP communication. This eliminates the need for HTTP-to-MCP conversion while providing load balancing, health monitoring, authentication, and observability.

## Configuration Files

### 1. `gateway-config.yaml`
**Main gateway configuration file in Kubernetes-style YAML format**

- **Purpose**: Primary configuration for the AWS Bedrock AgentCore Gateway
- **Protocol**: Native MCP protocol routing (no conversion)
- **Features**: Console integration, authentication, circuit breaker, observability
- **MCP Servers**: Configures routing to restaurant-search-mcp, restaurant-reasoning-mcp, and mbti-travel-assistant-mcp

**Key Sections**:
- `spec.mcp_servers`: Defines MCP server endpoints and tool mappings
- `spec.authentication`: JWT authentication over MCP protocol headers
- `spec.circuit_breaker`: Circuit breaker configuration for fault tolerance
- `spec.observability`: Metrics, logging, and tracing configuration

### 2. `mcp-routing-config.json`
**Detailed MCP protocol routing and tool schema configuration**

- **Purpose**: Native MCP protocol routing rules and tool metadata
- **Server Registry**: Complete MCP server definitions with tool schemas
- **Routing Rules**: Tool-to-server mapping with load balancing and retry policies
- **Schemas**: JSON schemas for all MCP tools with validation rules

**Key Sections**:
- `server_registry`: MCP server endpoints, health checks, and tool definitions
- `routing_rules.tool_routing`: Maps each tool to its target MCP server
- `definitions`: JSON schemas for Restaurant, TouristSpot, and other data models

### 3. `circuit-breaker-config.json`
**Circuit breaker configuration for MCP server fault tolerance**

- **Purpose**: Fault tolerance and resilience for MCP server connections
- **Server-Specific**: Different thresholds and timeouts per MCP server
- **States**: Closed, Open, and Half-Open circuit breaker states
- **Monitoring**: Metrics collection and alerting for circuit breaker events

**Key Features**:
- Failure detection based on MCP protocol errors and timeouts
- Automatic recovery testing in half-open state
- Fallback responses with native MCP error format
- Integration with load balancer for traffic routing

### 4. `health-check-config.json`
**Health monitoring configuration for MCP servers**

- **Purpose**: Native MCP protocol health checks and monitoring
- **Methods**: MCP ping, tools list, and functional testing
- **Aggregation**: Gateway-level health status based on server health
- **Integration**: Console and load balancer health status propagation

**Health Check Methods**:
- `mcp_ping`: Basic MCP protocol ping for responsiveness
- `mcp_tools_list`: Verify server can list available tools
- `mcp_tool_test`: Functional testing with sample tool calls

### 5. `jwt-auth-config.json`
**JWT authentication configuration for MCP protocol**

- **Purpose**: JWT authentication handled at MCP protocol level
- **Cognito Integration**: AWS Cognito User Pool validation
- **MCP Headers**: Authentication context forwarded via MCP protocol headers
- **User Context**: Extract and forward user information to MCP servers

**Authentication Flow**:
1. Extract JWT token from MCP protocol headers
2. Validate token against Cognito discovery URL
3. Extract user context from JWT claims
4. Forward authentication context to MCP servers via MCP metadata

## MCP Servers Configuration

### Restaurant Search MCP Server
- **Endpoint**: `restaurant-search-mcp:8080`
- **Protocol**: Native MCP with stdio transport
- **Tools**: 
  - `search_restaurants_by_district`
  - `search_restaurants_by_meal_type`
  - `search_restaurants_combined`
- **Authentication**: Optional (development mode)

### Restaurant Reasoning MCP Server
- **Endpoint**: `restaurant-reasoning-mcp:8080`
- **Protocol**: Native MCP with stdio transport
- **Tools**:
  - `recommend_restaurants`
  - `analyze_restaurant_sentiment`
- **Authentication**: Required

### MBTI Travel Assistant MCP Server
- **Endpoint**: `mbti-travel-assistant-mcp:8080`
- **Protocol**: Native MCP with stdio transport
- **Tools**:
  - `create_mbti_itinerary`
  - `get_personality_recommendations`
  - `analyze_travel_preferences`
- **Authentication**: Optional (development mode)

## Authentication Configuration

### Cognito User Pool Settings
```json
{
  "user_pool_id": "us-east-1_KePRX24Bn",
  "client_id": "1ofgeckef3po4i3us4j1m4chvd",
  "client_secret": "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
  "region": "us-east-1",
  "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
}
```

### MCP Protocol Authentication
- **Method**: JWT tokens in MCP protocol headers
- **Header**: `Authorization: Bearer <jwt_token>`
- **User Context**: Forwarded via `X-User-Context` header
- **Token Claims**: Forwarded via `X-Token-Claims` header

## Circuit Breaker Configuration

### Failure Thresholds
- **Restaurant Search**: 3 failures in 20 seconds
- **Restaurant Reasoning**: 5 failures in 45 seconds  
- **MBTI Travel Assistant**: 4 failures in 120 seconds

### Recovery Conditions
- **Health Check**: 2 consecutive successful health checks
- **Tool Calls**: 2 consecutive successful tool executions

### Fallback Responses
Native MCP error responses with circuit breaker context:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Service temporarily unavailable",
    "data": {
      "reason": "Circuit breaker open",
      "server": "restaurant-search-mcp",
      "retry_after": 45,
      "circuit_breaker_state": "open"
    }
  }
}
```

## Health Check Configuration

### Health Check Methods
1. **MCP Ping**: Basic responsiveness test
2. **Tools List**: Verify tool discovery functionality
3. **Functional Test**: Sample tool call with test data

### Health Status Levels
- **Healthy**: All health checks pass
- **Degraded**: Basic checks pass, functional tests may fail
- **Unhealthy**: Basic connectivity or protocol issues

### Gateway Health Aggregation
- **Healthy**: All servers healthy or degraded
- **Degraded**: Some servers unhealthy, minimum 1 healthy
- **Unhealthy**: All servers unhealthy

## Deployment Instructions

### Prerequisites
1. AWS CLI configured with appropriate permissions
2. Python 3.8+ with required dependencies
3. Access to existing MCP servers
4. Bedrock AgentCore permissions

### Validation
```bash
# Validate all configuration files
python scripts/validate_gateway_config.py
```

### Deployment
```bash
# Deploy the gateway
python scripts/deploy_gateway.py

# Deploy to specific region
python scripts/deploy_gateway.py --region us-west-2

# List existing gateways
python scripts/deploy_gateway.py --list

# Delete a gateway
python scripts/deploy_gateway.py --delete <gateway-id>
```

### AWS CLI Commands
```bash
# Create gateway using AWS CLI
aws bedrock-agentcore create-gateway \
  --gateway-name agentcore-mcp-gateway \
  --configuration file://gateway-config.yaml \
  --region us-east-1

# List gateways
aws bedrock-agentcore list-gateways --region us-east-1

# Get gateway details
aws bedrock-agentcore get-gateway \
  --gateway-id <gateway-id> \
  --region us-east-1
```

## Monitoring and Observability

### CloudWatch Metrics
- `MCPToolInvocations`: Number of MCP tool calls
- `MCPResponseTime`: Tool response time in milliseconds
- `MCPErrorRate`: Error rate for MCP tool calls
- `CircuitBreakerState`: Circuit breaker state (0=closed, 1=open, 2=half-open)

### Logging
- **Format**: JSON structured logging
- **Destination**: CloudWatch Logs
- **Log Group**: `/aws/bedrock-agentcore/gateway/mcp`
- **Includes**: Request ID, user context, MCP protocol details

### Tracing
- **Service**: X-Ray integration
- **Segments**: MCP tool calls and server interactions
- **Sampling**: 10% of requests traced

## Console Integration

### Gateway Management
- **URL**: `https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agentcore/gateways`
- **Features**: Gateway status, MCP server health, tool usage metrics
- **Monitoring**: Real-time health status and performance metrics

### MCP Server Status
- **Health Indicators**: Green (healthy), Yellow (degraded), Red (unhealthy)
- **Tool Availability**: List of available tools per server
- **Performance Metrics**: Response times and success rates

## Troubleshooting

### Common Issues

#### Gateway Creation Fails
- **Check**: AWS permissions for Bedrock AgentCore
- **Verify**: IAM role has required policies
- **Validate**: Configuration files pass validation

#### MCP Server Connectivity Issues
- **Check**: MCP server endpoints are accessible
- **Verify**: Health check configurations match server capabilities
- **Test**: Direct MCP connections to servers

#### Authentication Failures
- **Check**: Cognito User Pool configuration
- **Verify**: JWT token format and claims
- **Test**: Token validation against discovery URL

#### Circuit Breaker Issues
- **Check**: Failure thresholds and timeout settings
- **Monitor**: Circuit breaker state changes
- **Adjust**: Thresholds based on server performance

### Validation Errors
Run the validation script to identify configuration issues:
```bash
python scripts/validate_gateway_config.py
```

Common validation errors:
- Missing required configuration sections
- Invalid MCP server endpoints
- Incorrect authentication settings
- Malformed JSON/YAML syntax

### Health Check Failures
Monitor health check logs:
```bash
aws logs filter-log-events \
  --log-group-name "/aws/bedrock-agentcore/gateway/mcp" \
  --filter-pattern "health_check_failure"
```

## Security Considerations

### Authentication Security
- **HTTPS Required**: All communications use HTTPS
- **Token Validation**: Full JWT signature and claims validation
- **User Context**: Sanitized user information forwarding
- **Audit Logging**: All authentication events logged

### Network Security
- **VPC Integration**: Deploy in private subnets
- **Security Groups**: Restrict access to MCP server ports
- **CORS Configuration**: Limit allowed origins and methods

### Data Protection
- **Encryption**: Data encrypted in transit and at rest
- **Token Storage**: Secure token handling and storage
- **Log Sanitization**: Sensitive data removed from logs

## Performance Optimization

### Connection Pooling
- **Max Connections**: 20 per MCP server
- **Keep Alive**: Persistent connections enabled
- **Timeout**: 30 seconds connection timeout

### Caching
- **Tool Metadata**: 5-minute cache TTL
- **Response Cache**: 1-minute cache for cacheable responses
- **JWKS Cache**: 1-hour cache for JWT validation keys

### Load Balancing
- **Strategy**: Round-robin across healthy servers
- **Health Checks**: 30-second intervals
- **Failover**: Automatic traffic routing to healthy servers

## Backward Compatibility

### Direct MCP Access
- **Preserved**: Existing direct MCP connections continue to work
- **Coexistence**: Both direct and gateway-routed access supported
- **No Changes**: MCP servers require no modifications

### Protocol Consistency
- **Same Behavior**: Identical MCP protocol messages and responses
- **Authentication**: Consistent user context handling
- **Error Handling**: Same error responses and tool metadata

## Support and Maintenance

### Configuration Updates
- **Hot Reload**: Configuration changes applied without restart
- **Validation**: All changes validated before application
- **Rollback**: Previous configurations can be restored

### Version Management
- **Configuration Version**: Track configuration changes
- **Schema Evolution**: Support for new MCP protocol features
- **Backward Compatibility**: Maintain compatibility with existing tools

### Monitoring and Alerts
- **Health Monitoring**: Continuous health status monitoring
- **Performance Alerts**: Alerts for degraded performance
- **Error Notifications**: Immediate notification of critical errors

For additional support, refer to the AWS Bedrock AgentCore documentation or contact the development team.