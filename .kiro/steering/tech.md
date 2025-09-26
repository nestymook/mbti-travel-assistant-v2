# Technology Stack

## Core Technologies

- **Python 3.10+**: Primary programming language
- **AWS Services**: Bedrock, Bedrock AgentCore, Lambda, CloudFormation, IAM
- **Docker/Finch**: Containerization for local development

## Key Dependencies

### Agent Frameworks
- `bedrock-agentcore`: Core AgentCore SDK
- `bedrock-agentcore-starter-toolkit`: Development toolkit
- `strands-agents`: Strands agent framework
- `langchain[aws]`: LangChain with AWS integrations
- `langgraph`: LangGraph for agent workflows
- `crewai`: CrewAI framework support

### Development Tools
- `boto3`: AWS SDK for Python
- `uv`: Fast Python package manager
- `mcp>=1.9.0`: Model Context Protocol
- `jupyter`: Notebook environment for tutorials
- `pandas`: Data manipulation
- `opentelemetry-instrumentation-langchain`: Observability

## Common Commands

### Local Development
```bash
# Install dependencies
pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit

# Run agent locally
python my_agent.py

# Test local agent
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'
```

### Deployment
```bash
# Configure and deploy
agentcore configure -e my_agent.py
agentcore launch

# Test deployed agent
agentcore invoke '{"prompt": "tell me a joke"}'
```

### Prerequisites
- AWS account with configured credentials (`aws configure`)
- Model access: Anthropic Claude 4.0 in Bedrock console
- Required IAM policies: `BedrockAgentCoreFullAccess`, `AmazonBedrockFullAccess`

## Build System

Most examples use standard Python packaging with `requirements.txt`. Some advanced examples use:
- `pyproject.toml` with `uv` for dependency management
- Docker for containerized deployments
- CloudFormation/CDK for infrastructure as code