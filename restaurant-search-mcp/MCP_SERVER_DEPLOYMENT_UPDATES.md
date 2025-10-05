# MCP Server Deployment Configuration Updates - Restaurant Search MCP

## Overview
Updated the deployment script and configuration to properly reflect that **MCP servers don't need entrypoints** because they use protocol-based communication rather than conversational interfaces.

## Key Changes Made

### 1. Updated Deployment Script (`scripts/deploy_agentcore.py`)

#### Function Signature Changes
```python
# BEFORE: Required entrypoint parameter
def configure_agentcore_runtime(self, 
                               entrypoint: str = "main.py",
                               agent_name: str = "restaurant_search_agent",
                               requirements_file: str = "requirements.txt") -> Dict[str, Any]:

# AFTER: Optional entrypoint parameter (None for MCP servers)
def configure_agentcore_runtime(self, 
                               entrypoint: str = None,  # MCP servers don't need entrypoints
                               agent_name: str = "restaurant_search_agent",
                               requirements_file: str = "requirements.txt") -> Dict[str, Any]:
```

#### Configuration Logic Updates
```python
# Only add entrypoint if it's specified (not needed for MCP servers)
if entrypoint:
    config_params["entrypoint"] = entrypoint
    # Validate entrypoint file exists if specified
    if not os.path.exists(entrypoint):
        raise FileNotFoundError(f"Entrypoint file not found: {entrypoint}")
else:
    print("Entrypoint: None (MCP Server - protocol-based communication)")
```

#### Argument Parser Updates
```python
# BEFORE: Default entrypoint specified
parser.add_argument('--entrypoint', default='main.py', 
                   help='BedrockAgentCoreApp entrypoint (default: main.py)')

# AFTER: No default entrypoint for MCP servers
parser.add_argument('--entrypoint', default=None, 
                   help='Entrypoint (None for MCP servers - they use protocol-based communication)')
```

### 2. Updated AgentCore Configuration (`.bedrock_agentcore.yaml`)

#### Removed Entrypoint Field from MCP Server
```yaml
# BEFORE: Had entrypoint field for MCP server
restaurant_search_mcp:
  name: restaurant_search_mcp
  entrypoint: C:/MBTI_Travel_Assistant/restaurant-search-mcp/main.py
  platform: linux/arm64

# AFTER: No entrypoint field for MCP server (protocol-based communication)
restaurant_search_agent:
  name: restaurant_search_agent
  platform: linux/arm64
```

#### Updated Default Agent
```yaml
# BEFORE: Pointed to conversational agent
default_agent: restaurant_search_conversational_agent

# AFTER: Points to MCP server (matches deployment script default)
default_agent: restaurant_search_agent
```

#### Kept Conversational Agent Configuration
```yaml
# Conversational agent still has entrypoint (needed for chat interface)
restaurant_search_conversational_agent:
  name: restaurant_search_conversational_agent
  entrypoint: C:/MBTI_Travel_Assistant/restaurant-search-mcp/main.py
  # ... rest of config
```

### 3. Updated Documentation

#### Script Header Documentation
```python
"""
AgentCore Runtime Deployment Script for Restaurant Search MCP Server

This script configures and deploys the Restaurant Search MCP server to
Amazon Bedrock AgentCore Runtime using the bedrock-agentcore-starter-toolkit.

Note: MCP servers use protocol-based communication and do not require entrypoints.
They expose tools via the Model Context Protocol rather than conversational interfaces.

Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3
"""
```

## Architecture Clarification

### **MCP Server** (`restaurant_search_agent`):
- **No entrypoint needed**: Protocol-based communication
- **Protocol**: MCP
- **Purpose**: Provide restaurant search tools to other agents
- **Memory**: STM_ONLY (stateless tool provider)

### **Conversational Agent** (`restaurant_search_conversational_agent`):
- **Need entrypoint**: `main.py` 
- **Protocol**: HTTP
- **Purpose**: Chat interface for restaurant search
- **Memory**: STM_AND_LTM (conversation history)

## Deployment Command Examples

### Deploy MCP Server (No Entrypoint)
```bash
# Default deployment (no entrypoint specified)
python scripts/deploy_agentcore.py

# Explicit no entrypoint
python scripts/deploy_agentcore.py --entrypoint None

# Custom agent name
python scripts/deploy_agentcore.py --agent-name my_mcp_server
```

### Deploy Conversational Agent (With Entrypoint)
```bash
# Conversational agent deployment
python scripts/deploy_agentcore.py --entrypoint main.py --agent-name restaurant_search_conversational_agent
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
  --agent-name AGENT_NAME
                        Agent name (default: restaurant_search_agent)
```

### Configuration Output
```
🚀 Configuring AgentCore Runtime deployment for MCP Server...
Entrypoint: None (MCP Server - protocol-based communication)
Agent Name: restaurant_search_agent
Requirements: requirements.txt
Region: us-east-1
```

## Configuration Structure

The `.bedrock_agentcore.yaml` now supports both deployment patterns:

```yaml
default_agent: restaurant_search_agent  # MCP Server (default)
agents:
  # MCP Server - No entrypoint needed
  restaurant_search_agent:
    name: restaurant_search_agent
    platform: linux/arm64
    protocol_configuration:
      server_protocol: MCP
    memory:
      mode: STM_ONLY  # Stateless
  
  # Conversational Agent - Entrypoint required
  restaurant_search_conversational_agent:
    name: restaurant_search_conversational_agent
    entrypoint: C:/MBTI_Travel_Assistant/restaurant-search-mcp/main.py
    platform: linux/arm64
    protocol_configuration:
      server_protocol: HTTP
    memory:
      mode: STM_AND_LTM  # Conversation history
```

## Benefits of This Update

1. **Clarity**: Makes it clear that MCP servers don't need entrypoints
2. **Flexibility**: Supports both MCP servers and conversational agents in same project
3. **Correctness**: Aligns with AgentCore's protocol-based architecture for MCP
4. **Consistency**: Matches the pattern established in restaurant-search-result-reasoning-mcp

## Files Modified

1. `restaurant-search-mcp/scripts/deploy_agentcore.py`
2. `restaurant-search-mcp/.bedrock_agentcore.yaml`
3. `restaurant-search-mcp/MCP_SERVER_DEPLOYMENT_UPDATES.md` (this file)

## Comparison with Other Projects

| **Project** | **Type** | **Entrypoint** | **Protocol** | **Memory** |
|-------------|----------|----------------|--------------|------------|
| `restaurant-search-mcp` (MCP) | MCP Server | ❌ None | MCP | STM_ONLY |
| `restaurant-search-mcp` (Conv) | Conversational | ✅ main.py | HTTP | STM_AND_LTM |
| `restaurant-search-result-reasoning-mcp` | MCP Server | ❌ None | MCP | STM_AND_LTM |
| `mbti_travel_assistant_mcp` | Conversational | ✅ main.py | HTTP | STM_AND_LTM |

---

**Date**: October 6, 2025  
**Status**: ✅ Complete  
**Architecture**: MCP Server (Protocol-based, No Entrypoint Required)  
**Consistency**: ✅ Matches restaurant-search-result-reasoning-mcp pattern