# Amazon Bedrock AgentCore - Developer Guide

This steering document provides comprehensive guidance for developing, deploying, and operating AI agents using Amazon Bedrock AgentCore based on the official developer guide.

## AgentCore Overview

Amazon Bedrock AgentCore is a framework-agnostic and model-agnostic platform that enables developers to deploy and operate advanced AI agents securely at scale. It provides a comprehensive set of services for building production-ready AI applications.

### Core Components

#### AgentCore Runtime
- **Purpose**: Secure, serverless runtime for deploying and scaling AI agents
- **Features**: Auto-scaling, built-in security, observability
- **Architecture**: Supports `linux/arm64` containers (required for production)
- **Deployment**: Managed through AWS CodeBuild for cross-platform building

#### AgentCore Gateway
- **Purpose**: Automatically converts APIs, Lambda functions, and services into MCP-compatible tools
- **Integration**: Seamless tool integration with existing AWS services
- **Protocol**: Model Context Protocol (MCP) support
- **Authentication**: OAuth 2.0, JWT, and custom authentication patterns

#### AgentCore Memory
- **Purpose**: Fully-managed memory infrastructure for personalized agent experiences
- **Features**: Persistent memory, session management, context retention
- **Integration**: Works with all supported frameworks and models

#### AgentCore Identity
- **Purpose**: Seamless agent identity and access management
- **Features**: OAuth 2.0, token exchange, workload identity
- **Security**: KMS encryption, token vault, data protection
- **Integration**: AWS services and third-party identity providers

#### Built-in Tools
- **Code Interpreter**: Code execution and data analysis capabilities
- **Browser Tool**: Web applications and secure browsing functionality
- **Custom Tools**: Framework for building domain-specific tools

#### AgentCore Observability
- **Monitoring**: CloudWatch metrics and dashboards
- **Tracing**: X-Ray integration for performance monitoring
- **Debugging**: Session traces and agent transparency
- **Metrics**: Runtime performance and operational insights

## Framework Support

AgentCore supports multiple popular AI frameworks:

### Strands Agents
```python
from strands import Agent
from bedrock_agentcore import AgentCoreRuntime

# Framework-specific integration patterns
agent = Agent(runtime=AgentCoreRuntime())
```

### CrewAI
```python
from crewai import Agent, Task, Crew
from bedrock_agentcore_starter_toolkit import AgentCoreIntegration

# CrewAI with AgentCore integration
crew = Crew(agents=[agent], tasks=[task], runtime=AgentCoreIntegration())
```

### LangGraph
```python
from langgraph import StateGraph
from langchain_aws import BedrockLLM

# LangGraph with Bedrock integration
graph = StateGraph(llm=BedrockLLM(), runtime="agentcore")
```

### LlamaIndex
```python
from llama_index import ServiceContext
from bedrock_agentcore import AgentCoreServiceContext

# LlamaIndex with AgentCore
service_context = AgentCoreServiceContext()
```

## Authentication and Authorization

### OAuth 2.0 Integration
AgentCore supports industry-standard OAuth 2.0 flows:

```python
# OAuth 2.0 configuration
auth_config = {
    "oauth2": {
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "authorization_url": "https://auth.example.com/oauth/authorize",
        "token_url": "https://auth.example.com/oauth/token"
    }
}
```

### JWT Token Exchange
```python
# JWT authentication configuration
jwt_config = {
    "customJWTAuthorizer": {
        "allowedClients": ["client-id-1", "client-id-2"],
        "discoveryUrl": "https://your-domain.auth.region.amazoncognito.com/.well-known/openid-configuration"
    }
}
```

### Workload Identity
```python
# Workload identity setup
identity_config = {
    "workload_identity": {
        "service_account": "agent-service-account",
        "role_arn": "arn:aws:iam::account:role/AgentCoreRole"
    }
}
```

## Model Context Protocol (MCP) Integration

### MCP Server Development
```python
from mcp import server
from mcp.server.fastmcp import FastMCP

# Create MCP server with tools
mcp_server = FastMCP("agent-name")

@mcp_server.tool()
def search_tool(query: str) -> dict:
    """Search tool implementation."""
    return {"results": "search results"}

# Configure for AgentCore
mcp_server.run(
    transport="streamable-http",
    stateless_http=True
)
```

### MCP Client Integration
```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Connect to AgentCore MCP endpoint
async with streamablehttp_client(mcp_url, headers) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("tool_name", parameters)
```

## Gateway Tool Architecture

### API to MCP Conversion
AgentCore Gateway automatically converts existing APIs into MCP-compatible tools:

```yaml
# Gateway configuration
gateway:
  apis:
    - name: "restaurant-api"
      endpoint: "https://api.example.com/restaurants"
      methods: ["GET", "POST"]
      authentication: "bearer"
      mcp_tools:
        - name: "search_restaurants"
          method: "GET"
          path: "/search"
```

### Lambda Function Integration
```python
# Lambda function as MCP tool
import json
from bedrock_agentcore import gateway_decorator

@gateway_decorator.mcp_tool()
def lambda_handler(event, context):
    """Lambda function exposed as MCP tool."""
    return {
        'statusCode': 200,
        'body': json.dumps('Tool response')
    }
```

## Observability and Monitoring

### CloudWatch Integration
```python
# CloudWatch metrics configuration
observability_config = {
    "cloudwatch": {
        "metrics": True,
        "logs": True,
        "dashboard": "AgentCore-Dashboard"
    }
}
```

### X-Ray Tracing
```python
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture('agent_operation')
def agent_function():
    """Function with X-Ray tracing."""
    pass
```

### Custom Metrics
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Custom agent metrics
cloudwatch.put_metric_data(
    Namespace='AgentCore/Custom',
    MetricData=[
        {
            'MetricName': 'ToolInvocations',
            'Value': 1,
            'Unit': 'Count'
        }
    ]
)
```

## Security Best Practices

### Data Protection
- **Encryption**: KMS encryption for data at rest and in transit
- **Token Vault**: Secure storage for authentication tokens
- **Network Security**: VPC endpoints and private connections

### IAM Configuration
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:*",
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        }
    ]
}
```

### Private Network Access
```yaml
# VPC configuration for private access
network:
  mode: "PRIVATE"
  vpc_config:
    vpc_id: "vpc-12345678"
    subnet_ids: ["subnet-12345678", "subnet-87654321"]
    security_group_ids: ["sg-12345678"]
```

## Deployment Patterns

### Container Requirements

**CRITICAL**: Amazon Bedrock AgentCore Runtime **REQUIRES** `linux/arm64` architecture. This is not optional.

### Supported ARM64 Base Images
```dockerfile
# Option 1: Official Python ARM64 (recommended)
FROM --platform=linux/arm64 python:3.12-slim

# Option 2: UV Python package manager (faster builds)
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Option 3: Alpine Linux (smaller size)
FROM --platform=linux/arm64 python:3.12-alpine

# Option 4: Ubuntu-based
FROM --platform=linux/arm64 ubuntu:22.04
```

### Complete Dockerfile Example
```dockerfile
# REQUIRED: ARM64 platform for Amazon Bedrock AgentCore Runtime
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Configure UV for container environment
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1

# Install dependencies
COPY requirements.txt requirements.txt
RUN uv pip install -r requirements.txt

# Install observability tools
RUN uv pip install aws-opentelemetry-distro>=0.10.1

# Set AWS region environment variables
ENV AWS_REGION=us-east-1
ENV AWS_DEFAULT_REGION=us-east-1
ENV DOCKER_CONTAINER=1

# Create non-root user for security
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

# Expose MCP server ports
EXPOSE 8080
EXPOSE 8000

# Copy application code
COPY . .

# Start MCP server with observability
CMD ["opentelemetry-instrument", "python", "-m", "restaurant_mcp_server"]
```

### AgentCore Configuration
```yaml
# .bedrock_agentcore.yaml
name: "my-agent"
platform: "linux/arm64"
container_runtime: "docker"
network_mode: "PUBLIC"
observability:
  enabled: true
authentication:
  type: "jwt"
  config:
    discovery_url: "https://cognito-domain/.well-known/openid-configuration"
```

### Deployment Automation
```python
import boto3
from bedrock_agentcore_starter_toolkit import AgentCoreDeployer

# Automated deployment
deployer = AgentCoreDeployer(
    agent_name="my-agent",
    container_uri="account.dkr.ecr.region.amazonaws.com/my-agent:latest",
    platform="linux/arm64"
)

deployment = deployer.deploy()
print(f"Agent ARN: {deployment.agent_arn}")
```

## Advanced Features

### Custom Domain Configuration
```python
# CloudFront and Route 53 integration
domain_config = {
    "custom_domain": {
        "domain_name": "agents.example.com",
        "certificate_arn": "arn:aws:acm:region:account:certificate/cert-id",
        "route53_zone_id": "Z1234567890"
    }
}
```

### Multi-Agent Workflows
```python
from bedrock_agentcore import AgentOrchestrator

# Orchestrate multiple agents
orchestrator = AgentOrchestrator()
orchestrator.add_agent("search-agent", search_agent_arn)
orchestrator.add_agent("analysis-agent", analysis_agent_arn)

# Define workflow
workflow = orchestrator.create_workflow([
    ("search-agent", "search_restaurants"),
    ("analysis-agent", "analyze_results")
])
```

### Session Management
```python
# Session-based agent interactions
from bedrock_agentcore import SessionManager

session_manager = SessionManager()
session = session_manager.create_session(
    agent_arn=agent_arn,
    user_id="user-123",
    session_config={
        "memory_enabled": True,
        "context_window": 10
    }
)
```

## Performance Optimization

### Caching Strategies
```python
# Agent response caching
cache_config = {
    "response_cache": {
        "enabled": True,
        "ttl": 300,  # 5 minutes
        "backend": "redis"
    }
}
```

### Resource Management
```yaml
# Resource allocation
resources:
  cpu: "1 vCPU"
  memory: "2 GB"
  scaling:
    min_instances: 1
    max_instances: 10
    target_utilization: 70
```

### Cost Optimization
- Use appropriate instance sizing
- Implement request batching
- Leverage caching for repeated operations
- Monitor and optimize model usage

## Troubleshooting Guide

### Common Issues

#### Authentication Failures
```python
# Debug authentication issues
def debug_auth(discovery_url):
    """Debug JWT authentication configuration."""
    import requests
    response = requests.get(discovery_url)
    print(f"Discovery URL status: {response.status_code}")
    print(f"JWKS endpoint: {response.json().get('jwks_uri')}")
```

#### Container Build Issues
```bash
# Check CodeBuild logs
aws logs describe-log-groups --log-group-name-prefix "/aws/codebuild"

# Validate Dockerfile
docker build --platform linux/arm64 -t test-image .
```

#### MCP Protocol Issues
```python
# Test MCP connectivity
async def test_mcp_connection(mcp_url):
    """Test MCP server connectivity."""
    try:
        async with streamablehttp_client(mcp_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return True
    except Exception as e:
        print(f"MCP connection failed: {e}")
        return False
```

## Integration Examples

### Industry Use Cases

#### Customer Support Assistant
```python
# Customer support agent with knowledge base
support_agent = {
    "tools": [
        "knowledge_base_search",
        "ticket_creation",
        "escalation_routing"
    ],
    "memory": {
        "conversation_history": True,
        "customer_context": True
    }
}
```

#### Healthcare Appointment Agent
```python
# FHIR-based healthcare scheduling
healthcare_agent = {
    "tools": [
        "fhir_patient_search",
        "appointment_scheduling",
        "provider_availability"
    ],
    "compliance": {
        "hipaa": True,
        "audit_logging": True
    }
}
```

#### Financial Planning Assistant
```python
# Financial analysis and planning
finance_agent = {
    "tools": [
        "portfolio_analysis",
        "risk_assessment",
        "market_data_retrieval"
    ],
    "security": {
        "pci_compliance": True,
        "data_encryption": True
    }
}
```

## Best Practices

### Development Workflow
1. **Local Development**: Test agents locally before deployment
2. **Validation**: Use configuration validation tools
3. **Incremental Deployment**: Deploy to staging first
4. **Monitoring**: Set up comprehensive observability

### Security Guidelines
1. **Least Privilege**: Use minimal required permissions
2. **Authentication**: Always use authentication in production
3. **Encryption**: Encrypt sensitive data and communications
4. **Audit Logging**: Enable comprehensive audit trails

### Performance Guidelines
1. **Resource Sizing**: Right-size containers and compute resources
2. **Caching**: Implement appropriate caching strategies
3. **Batching**: Use request batching for efficiency
4. **Monitoring**: Continuously monitor performance metrics

### Operational Excellence
1. **Automation**: Automate deployment and operations
2. **Documentation**: Maintain comprehensive documentation
3. **Testing**: Implement thorough testing strategies
4. **Disaster Recovery**: Plan for failure scenarios

## Reference Architecture

### Multi-Tier Agent Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │  Foundation     │    │   Data Sources  │
│                 │    │  Models         │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│   API Gateway   │    │  AgentCore      │    │   Databases     │
│                 │    │  Runtime        │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│   AgentCore     │    │  MCP Tools      │    │   External APIs │
│   Gateway       │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│   Identity &    │    │  Observability  │    │   File Storage  │
│   Auth          │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Network Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        VPC                                  │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Public        │    │   Private       │                │
│  │   Subnets       │    │   Subnets       │                │
│  │                 │    │                 │                │
│  │  ┌───────────┐  │    │  ┌───────────┐  │                │
│  │  │ AgentCore │  │    │  │ Database  │  │                │
│  │  │ Gateway   │  │    │  │ Services  │  │                │
│  │  └───────────┘  │    │  └───────────┘  │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started Checklist

### Prerequisites
- [ ] AWS account with appropriate permissions
- [ ] Bedrock model access enabled
- [ ] Docker installed for local development
- [ ] Python 3.10+ environment

### Setup Steps
1. [ ] Install AgentCore SDK: `pip install bedrock-agentcore`
2. [ ] Configure AWS credentials: `aws configure`
3. [ ] Create agent project structure
4. [ ] Implement MCP server with tools
5. [ ] Create Dockerfile with ARM64 platform
6. [ ] Configure AgentCore YAML file
7. [ ] Set up authentication (Cognito/JWT)
8. [ ] Deploy using AgentCore toolkit
9. [ ] Test deployment and functionality
10. [ ] Set up monitoring and observability

### Validation Commands
```bash
# Validate AWS setup
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Validate AgentCore permissions
aws bedrock-agentcore list-agent-runtimes --region us-east-1

# Test local MCP server
python mcp_server.py --test

# Deploy agent
python deploy_agent.py

# Test deployed agent
python test_agent.py
```

---

**Last Updated**: September 27, 2025  
**Version**: 1.0.0  
**Source**: Amazon Bedrock AgentCore Developer Guide  
**Keywords**: AgentCore, authentication, observability, MCP, gateway tools, identity management, OAuth 2.0, JWT, code interpreter, browser tool, monitoring, CloudWatch, X-Ray, security, deployment

### Problem diagnose commands
**How to list all installed agents**: aws bedrock-agentcore-control list-agent-runtimes

## Invoke Bedrock AgentCore Runtime
### **Important concepts**
- The URL format is a combination of: 
    - https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/
    - agent arn with URL encode, such as urllib.parse.quote(f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{self.agent_id}", safe='')
    - /invocations?qualifier=DEFAULT
- The service class must contain function annotated with @app.entrypoint to handle the invocation

### **Sample Code**
**Note**: Please replace header with JWT for __Cognitos Authentication__

import requests
import json
import urllib.parse

jwt_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."  # Your JWT
session_id = "unique-session-123"
user_id = "test@mbti-travel.com"

agent_base_url = "https://bedrock-agentcore.us-east-1.amazonaws.com"
agent_id = "mbti_travel_planner_agent-JPTzWT3IZp"
# URL encode the agent ARN
agent_arn = urllib.parse.quote(f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{agent_id}", safe='')
agent_endpoint = f"{agent_base_url}/runtimes/{agent_arn}/invocations?qualifier=DEFAULT"

headers = {
    "Authorization": f"Bearer {jwt_token}",
    "X-Amzn-Bedrock-AgentCore-Runtime-User-Id": user_id,
    "Content-Type": "application/json"
}
body = {
    "prompt": "Explain machine learning in simple terms",
    "sessionId": session_id,
    "enableTrace": True
}

response = requests.post(agent_endpoint, headers=headers, json=body, stream=True)
if response.status_code == 200:
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            chunk = json.loads(line[6:])  # Parse SSE data
            if "completion" in chunk:
                print(chunk["completion"]["bytes"].decode("utf-8"), end="")
            elif "trace" in chunk:
                print(f"Trace: {chunk['trace']}")
else:
    print(f"Error: {response.status_code} - {response.text}")