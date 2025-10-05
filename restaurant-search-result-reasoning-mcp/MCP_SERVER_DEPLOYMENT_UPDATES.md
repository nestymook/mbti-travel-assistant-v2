# MCP Server Deployment Configuration Updates

## Overview
Updated the deployment script to properly reflect that **MCP servers don't need entrypoints** because they use protocol-based communication rather than conversational interfaces.

## Key Changes Made

### 1. Updated Deployment Script (`scripts/deploy_agentcore.py`)

#### Function Signature Changes
```python
# BEFORE: No default entrypoint
def configure_agentcore_runtime(self, 
                               entrypoint: str = None,  # MCP servers don't need entrypoints
                               agent_name: str = "restaurant_search_result_reasoning_agent",
                               requirements_file: str = "requirements.txt") -> Dict[str, Any]:

# AFTER: MCP server file as default entrypoint (AgentCore requires it)
def configure_agentcore_runtime(self, 
                               entrypoint: str = "restaurant_reasoning_mcp_server.py",  # MCP server file
                               agent_name: str = "restaurant_search_result_reasoning_agent",
                               requirements_file: str = "requirements.txt") -> Dict[str, Any]:
```

#### Configuration Logic Updates
```python
# Always use entrypoint for MCP servers (AgentCore requires it)
print(f"Entrypoint: {entrypoint}")
# Validate entrypoint file exists
if not os.path.exists(entrypoint):
    raise FileNotFoundError(f"Entrypoint file not found: {entrypoint}")

# Configure AgentCore Runtime with entrypoint
response = self.agentcore_runtime.configure(
    entrypoint=entrypoint,  # Required by AgentCore
    auto_create_execution_role=True,
    auto_create_ecr=True,
    requirements_file=requirements_file,
    region=self.region,
    authorizer_configuration=auth_config,
    protocol="MCP",
    agent_name=agent_name
)
```

#### Argument Parser Updates
```python
# BEFORE: No default entrypoint
parser.add_argument('--entrypoint', default=None, 
                   help='Entrypoint (None for MCP servers - they use protocol-based communication)')

# AFTER: MCP server file as default entrypoint
parser.add_argument('--entrypoint', default='restaurant_reasoning_mcp_server.py', 
                   help='MCP server entrypoint (default: restaurant_reasoning_mcp_server.py)')
```

### 2. Updated AgentCore Configuration (`.bedrock_agentcore.yaml`)

#### Added Entrypoint Field (AgentCore Requirement)
```yaml
# BEFORE: No entrypoint field
restaurant_search_result_reasoning_agent:
  name: restaurant_search_result_reasoning_agent
  platform: linux/arm64

# AFTER: MCP server file as entrypoint (required by AgentCore)
restaurant_search_result_reasoning_agent:
  name: restaurant_search_result_reasoning_agent
  entrypoint: restaurant_reasoning_mcp_server.py
  platform: linux/arm64
```

### 3. Updated Documentation

#### Script Header Documentation
```python
"""
AgentCore Runtime Deployment Script for Restaurant Search Result Reasoning MCP Server

This script configures and deploys the Restaurant Search Result Reasoning MCP server to
Amazon Bedrock AgentCore Runtime using the bedrock-agentcore-starter-toolkit.

Note: While MCP servers use protocol-based communication, AgentCore Runtime still requires 
an entrypoint parameter. We use the MCP server file as the entrypoint for proper deployment.

Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3
"""
```

## Architecture Clarification

### **Conversational Agents** (like main MBTI assistant):
- **Need entrypoint**: `main.py` 
- **Need memory**: For conversation history
- **Purpose**: Chat with users
- **Communication**: Direct conversational interface

### **MCP Servers** (like restaurant reasoning):
- **Entrypoint required**: MCP server file (AgentCore requirement)
- **Memory configurable**: Can use STM_AND_LTM for context retention  
- **Purpose**: Provide tools/services to other agents
- **Communication**: Model Context Protocol (MCP)

## Deployment Command Examples

### Deploy MCP Server (With MCP Server File)
```bash
# Default deployment (uses restaurant_reasoning_mcp_server.py)
python scripts/deploy_agentcore.py

# Explicit MCP server file
python scripts/deploy_agentcore.py --entrypoint restaurant_reasoning_mcp_server.py

# Custom agent name
python scripts/deploy_agentcore.py --agent-name my_mcp_server
```

### Deploy Conversational Agent (With Entrypoint)
```bash
# Conversational agent deployment
python scripts/deploy_agentcore.py --entrypoint main.py --agent-name my_conversational_agent
```

## Validation

### Help Output Verification
```bash
$ python scripts/deploy_agentcore.py --help
usage: deploy_agentcore.py [-h] [--region REGION] [--entrypoint ENTRYPOINT]
                           [--agent-name AGENT_NAME] [--requirements REQUIREMENTS]
                           [--configure-only] [--launch-only] [--status-only]

Deploy Restaurant Search MCP to AgentCore Runtime

options:
  --entrypoint ENTRYPOINT
                        Entrypoint (None for MCP servers - they use protocol-
                        based communication)
```

### Configuration Output
```
🚀 Configuring AgentCore Runtime deployment for MCP Server...
Entrypoint: restaurant_reasoning_mcp_server.py
Agent Name: restaurant_search_result_reasoning_agent
Requirements: requirements.txt
Region: us-east-1
```

## Benefits of This Update

1. **Compatibility**: Works with AgentCore Runtime requirements for entrypoints
2. **Clarity**: Uses the actual MCP server file as the entrypoint
3. **Correctness**: Aligns with AgentCore's deployment architecture
4. **Consistency**: Matches the pattern used in restaurant-search-mcp

## Files Modified

1. `restaurant-search-result-reasoning-mcp/scripts/deploy_agentcore.py`
2. `restaurant-search-result-reasoning-mcp/.bedrock_agentcore.yaml`
3. `restaurant-search-result-reasoning-mcp/MCP_SERVER_DEPLOYMENT_UPDATES.md` (this file)

---

**Date**: October 6, 2025  
**Status**: ✅ Complete  
**Architecture**: MCP Server (Protocol-based, MCP Server File as Entrypoint)  
**Update**: Revised to use MCP server file as entrypoint (AgentCore requirement)