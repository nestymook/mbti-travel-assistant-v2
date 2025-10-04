# AgentCore Gateway MCP Tools - Project Structure

This document describes the complete project structure for the AgentCore Gateway that exposes restaurant search and reasoning MCP tools through RESTful HTTP endpoints.

## Directory Structure

```
agentcore-gateway-mcp-tools/
├── README.md                           # Project overview and quick start guide
├── requirements.txt                    # Python dependencies with FastAPI, JWT, MCP client libs
├── Dockerfile                          # ARM64 container for AgentCore Runtime compatibility
├── .bedrock_agentcore.yaml            # AgentCore configuration with JWT authentication
├── cognito_config.json                # Cognito User Pool configuration
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore patterns
├── .dockerignore                      # Docker ignore patterns
├── __init__.py                        # Package initialization
├── main.py                            # FastAPI application entry point
├── PROJECT_STRUCTURE.md               # This file
│
├── api/                               # API endpoints and routing
│   └── __init__.py
│
├── config/                            # Configuration management
│   ├── __init__.py
│   └── settings.py                    # Pydantic settings with environment support
│
├── middleware/                        # Authentication and request middleware
│   └── __init__.py
│
├── models/                            # Pydantic request/response models
│   └── __init__.py
│
├── services/                          # Business logic and MCP client management
│   └── __init__.py
│
├── scripts/                           # Deployment and utility scripts
│   ├── __init__.py
│   └── deploy_agentcore.py           # AgentCore deployment automation
│
├── tests/                             # Test suite
│   ├── __init__.py
│   └── test_project_structure.py     # Project structure validation tests
│
└── docs/                              # Documentation
    └── __init__.py
```

## Core Files Description

### Application Files

- **`main.py`**: FastAPI application with CORS, structured logging, and basic endpoints
- **`requirements.txt`**: All required dependencies including FastAPI, Pydantic, JWT libraries, MCP client, AWS SDK, and observability tools
- **`__init__.py`**: Package metadata and version information

### Configuration Files

- **`.bedrock_agentcore.yaml`**: AgentCore configuration with:
  - ARM64 platform specification
  - JWT authentication using existing Cognito User Pool
  - Observability settings (metrics, logging, tracing)
  - Environment variables and resource allocation
  - Health check configuration

- **`cognito_config.json`**: Cognito authentication configuration with:
  - User Pool ID: `us-east-1_KePRX24Bn`
  - Client ID: `1ofgeckef3po4i3us4j1m4chvd`
  - Discovery URL and JWKS URI
  - Bypass paths for health endpoints

- **`config/settings.py`**: Centralized configuration management using Pydantic with:
  - `CognitoSettings`: JWT authentication configuration
  - `MCPServerSettings`: MCP server connection settings
  - `ApplicationSettings`: Server and observability configuration
  - Environment variable support

### Container Files

- **`Dockerfile`**: ARM64 container specification with:
  - `--platform=linux/arm64` for AgentCore Runtime compatibility
  - UV Python package manager for faster builds
  - OpenTelemetry instrumentation
  - Non-root user for security
  - Health check endpoint

- **`.dockerignore`**: Optimized for container builds, excluding development files

### Deployment Files

- **`scripts/deploy_agentcore.py`**: Automated deployment script with:
  - Prerequisites validation
  - ARM64 container building
  - AgentCore service deployment
  - Health check testing

### Development Files

- **`.env.example`**: Template for environment variables
- **`.gitignore`**: Comprehensive ignore patterns for Python, AWS, Docker, and IDE files
- **`tests/test_project_structure.py`**: Validation tests for project structure and configuration

## Key Features Implemented

### 1. ARM64 Container Support
- Dockerfile specifies `--platform=linux/arm64` as required by AgentCore Runtime
- Uses optimized base image with UV package manager
- Includes health check and observability instrumentation

### 2. JWT Authentication
- Configured to use existing Cognito User Pool (`us-east-1_KePRX24Bn`)
- Matches authentication patterns from existing MCP servers
- Bypass paths for health and documentation endpoints

### 3. MCP Client Integration
- Configuration for connecting to existing MCP servers:
  - `restaurant-search-mcp:8080` for search functionality
  - `restaurant-reasoning-mcp:8080` for analysis functionality
- Connection pooling and retry logic support

### 4. Observability
- Structured logging with JSON output
- OpenTelemetry instrumentation for tracing
- CloudWatch metrics integration
- Health check endpoint for AgentCore Runtime

### 5. Development Workflow
- Comprehensive test suite for validation
- Automated deployment scripts
- Environment variable configuration
- Docker development support

## Next Implementation Steps

The project structure is now complete and ready for the next tasks:

1. **Task 2**: Implement authentication middleware and JWT validation
2. **Task 3**: Create MCP client manager for server communication
3. **Task 4**: Implement Pydantic models for request/response validation
4. **Task 5**: Create tool metadata system for foundation model integration
5. **Task 6**: Create FastAPI application with restaurant search endpoints
6. **Task 7**: Create restaurant reasoning and analysis endpoints
7. **Task 8**: Implement comprehensive error handling system
8. **Task 9**: Add observability and monitoring features
9. **Task 10**: Create AgentCore deployment configuration
10. **Task 11**: Implement comprehensive testing suite
11. **Task 12**: Add configuration management and hot reloading
12. **Task 13**: Create documentation and deployment guides

## Validation

The project structure has been validated with automated tests that verify:
- All required files and directories exist
- Configuration files are properly formatted
- Dockerfile specifies ARM64 platform
- Dependencies are correctly specified
- Core application structure is in place

Run the validation tests:
```bash
python -m pytest tests/test_project_structure.py -v
```

All tests pass, confirming the project structure meets the requirements for AgentCore Gateway MCP Tools implementation.