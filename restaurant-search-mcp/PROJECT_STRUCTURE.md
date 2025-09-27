# Restaurant Search MCP - Project Structure

## 📁 Directory Organization

```
restaurant-search-mcp/
├── src/                              # Source code
│   ├── main.py                       # BedrockAgentCoreApp entrypoint
│   ├── restaurant_mcp_server.py      # FastMCP server implementation
│   ├── services/                     # Business logic services
│   │   ├── __init__.py
│   │   ├── restaurant_service.py     # Restaurant search logic
│   │   ├── district_service.py       # Geographic data management
│   │   ├── time_service.py           # Meal time classification
│   │   ├── data_access.py            # S3 data access layer
│   │   ├── auth_service.py           # Authentication utilities
│   │   ├── auth_middleware.py        # Authentication middleware
│   │   └── security_monitor.py       # Security monitoring
│   └── models/                       # Data models
│       ├── __init__.py
│       └── restaurant_models.py      # Restaurant data structures
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── test_auth_prompt.py           # Authentication testing
│   ├── test_deployed_agent_toolkit.py # Agent deployment testing
│   └── test_mcp_endpoint_invoke.py   # MCP endpoint testing
├── scripts/                          # Deployment and utility scripts
│   ├── execute_deployment.py         # Complete deployment workflow
│   ├── deploy_agentcore.py          # AgentCore deployment operations
│   ├── setup_cognito.py             # Cognito authentication setup
│   ├── create_test_user_cli.py      # Test user management
│   └── debug_auth.py                # Authentication troubleshooting
├── docs/                            # Documentation
│   ├── README.md                    # Documentation index
│   ├── DEPLOYMENT_GUIDE.md          # Deployment instructions
│   ├── TESTING_GUIDE.md             # Testing documentation
│   ├── KIRO_MCP_TESTING_GUIDE.md    # Kiro MCP integration guide
│   └── COGNITO_SETUP_GUIDE.md       # Authentication setup
├── config/                          # Configuration files
│   └── cognito_config.json          # Cognito configuration (generated)
├── requirements.txt                 # Python dependencies
├── README.md                        # Project overview
├── .bedrock_agentcore.yaml          # AgentCore configuration
└── PROJECT_STRUCTURE.md             # This file
```

## 🎯 Key Benefits of This Structure

### 1. **Modular Organization**
- Clear separation of concerns
- Easy to navigate and maintain
- Scalable for additional features

### 2. **Template Ready**
- Can be copied to create new MCP apps
- Consistent structure across projects
- Reusable components

### 3. **Development Friendly**
- Proper Python package structure
- Clear import paths
- Organized test suite

### 4. **Deployment Ready**
- All deployment scripts in `/scripts/`
- Configuration files in `/config/`
- Documentation in `/docs/`

## 🔧 Import Path Updates

### Updated Import Statements
```python
# Old imports (root level)
from services.restaurant_service import RestaurantService
from models.restaurant_models import Restaurant

# New imports (organized structure)
from src.services.restaurant_service import RestaurantService
from src.models.restaurant_models import Restaurant
```

### Python Path Configuration
Add to your Python path or use relative imports:
```python
import sys
sys.path.append('.')  # Add project root to path
```

## 🚀 Usage After Reorganization

### Running from Project Root
```bash
cd restaurant-search-mcp

# Run deployment
python scripts/execute_deployment.py

# Run tests
python tests/test_auth_prompt.py
python tests/test_deployed_agent_toolkit.py

# Run MCP server locally
python src/restaurant_mcp_server.py
```

### Running BedrockAgentCoreApp
```bash
cd restaurant-search-mcp
python src/main.py
```

## 📋 Configuration Updates Needed

### 1. Update .bedrock_agentcore.yaml
```yaml
# Update entrypoint path
entrypoint: src/main.py  # Changed from main.py
```

### 2. Update MCP Configuration
```json
{
  "mcpServers": {
    "restaurant-search-mcp": {
      "command": "python",
      "args": ["src/restaurant_mcp_server.py"],  // Updated path
      "cwd": "restaurant-search-mcp",            // Updated working directory
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### 3. Update Deployment Scripts
- Update file paths in deployment scripts
- Adjust working directories
- Update import statements

## 🎯 Template Creation Benefits

### Easy Replication
```bash
# Create new MCP app
cp -r restaurant-search-mcp my-new-mcp-app

# Customize for new domain
cd my-new-mcp-app
# Update src/main.py with new tools
# Update src/services/ with new business logic
# Update config/ with new configurations
```

### Consistent Structure
- Same directory layout for all MCP apps
- Standardized deployment process
- Reusable documentation templates

### Scalable Development
- Add new services in `src/services/`
- Add new models in `src/models/`
- Add new tests in `tests/`
- Add new scripts in `scripts/`

---

**Structure Created**: September 27, 2025  
**Status**: ✅ Ready for Template Use  
**Next Action**: Update configuration files and test the new structure