# Project Structure

## Repository Organization

### Main Directories

- **`amazon-bedrock-agentcore-samples-main/`**: Core samples repository
  - **`01-tutorials/`**: Interactive learning with Jupyter notebooks
  - **`02-use-cases/`**: End-to-end practical applications
  - **`03-integrations/`**: Framework and protocol integrations

- **`config/`**: Local configuration data (Hong Kong restaurant/district data)
  - **`districts/`**: Geographic district configurations
  - **`restaurants/`**: Restaurant data organized by region
  - **`tourist_spots/`**: Tourism-related configurations

- **`tests/`**: Test suite for MCP server and deployment validation
  - **`test_mcp_deployment.py`**: Basic MCP deployment tests (no authentication)
  - **`test_authenticated_mcp.py`**: Comprehensive tests for authenticated MCP server
  - **`test_mcp_with_toolkit.py`**: Tests using bedrock-agentcore-starter-toolkit
  - **`test_restaurant_service.py`**: Unit tests for restaurant service components

### Tutorial Structure (`01-tutorials/`)

Each AgentCore component has its own subdirectory:
- `01-AgentCore-runtime/`: Runtime hosting examples
- `02-AgentCore-gateway/`: API-to-MCP tool conversion
- `03-AgentCore-identity/`: Authentication and authorization
- `04-AgentCore-memory/`: Memory management patterns
- `05-AgentCore-tools/`: Built-in tools (Code Interpreter, Browser)
- `06-AgentCore-observability/`: Monitoring and tracing
- `07-AgentCore-E2E/`: Complete end-to-end workflows

### Use Cases Structure (`02-use-cases/`)

Real-world applications including:
- `customer-support-assistant/`: Support agent implementation
- `AWS-operations-agent/`: AWS infrastructure management
- `healthcare-appointment-agent/`: FHIR-based healthcare scheduling
- `finance-personal-assistant/`: Financial planning and analysis
- `SRE-agent/`: Site reliability engineering automation

### Integration Patterns (`03-integrations/`)

- `agentic-frameworks/`: Framework-specific implementations
  - `strands-agents/`, `langchain/`, `langgraph/`, `crewai/`, etc.
- `bedrock-agent/`: Integration with existing Bedrock Agents
- `observability/`: Third-party monitoring integrations
- `ux-examples/`: User interface implementations

## File Conventions

- **`requirements.txt`**: Standard Python dependencies
- **`README.md`**: Component-specific documentation
- **`app.py`** or **`main.py`**: Primary application entry points
- **`.env.example`**: Environment variable templates
- **`utils.py`**: Shared utility functions
- **`config/`**: Configuration files and data
- **`scripts/`**: Deployment and setup automation
- **`images/`**: Documentation assets and diagrams

### Core Application Files

- **`restaurant_mcp_server.py`**: Main MCP server implementation with FastMCP
- **`deploy_agentcore.py`**: AgentCore deployment script with Cognito authentication
- **`.bedrock_agentcore.yaml`**: AgentCore configuration file
- **`cognito_config.json`**: Cognito User Pool and authentication configuration
- **`Dockerfile`**: Container configuration for ARM64 deployment

### Testing Files

- **`test_authenticated_mcp.py`**: End-to-end tests for deployed authenticated MCP server
- **`test_mcp_with_toolkit.py`**: Tests using AgentCore toolkit Runtime class
- **`test_mcp_deployment.py`**: Basic deployment validation tests
- **`mcp_test_results.json`**: Test execution results and metrics

## Development Patterns

- Each use case is self-contained with its own dependencies
- Jupyter notebooks for interactive tutorials and exploration
- Shell scripts for automated deployment and cleanup
- CloudFormation/CDK templates for infrastructure provisioning
- Docker support for containerized deployments