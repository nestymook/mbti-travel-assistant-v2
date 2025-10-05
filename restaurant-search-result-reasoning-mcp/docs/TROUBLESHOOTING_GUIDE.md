# Restaurant Reasoning MCP Server - Troubleshooting Guide

## Common Issues and Solutions

### 1. Server Startup Issues

#### Problem: Module Import Errors
```
ModuleNotFoundError: No module named 'services.restaurant_reasoning_service'
```

**Solution:**
```bash
# Set Python path
export PYTHONPATH=/path/to/restaurant-search-result-reasoning-mcp

# Or use absolute imports
cd restaurant-search-result-reasoning-mcp
python -m restaurant_reasoning_mcp_server
```

#### Problem: FastMCP AttributeError
```
AttributeError: 'FastMCP' object has no attribute 'app'
```

**Solution:**
This indicates incorrect FastMCP API usage. Ensure you're using:
```python
# Correct
mcp = FastMCP("server-name")
@mcp.custom_route("/path", methods=["GET"])

# Incorrect  
@mcp.app.get("/path")  # FastMCP doesn't expose .app directly
```

#### Problem: Pydantic Schema Generation Error
```
PydanticInvalidForJsonSchema: Cannot generate a JsonSchema for core_schema.IsInstanceSchema (<class 'starlette.requests.Request'>)
```

**Solution:**
Remove FastAPI-specific parameters from MCP tool functions:
```python
# Incorrect
@mcp.tool()
def my_tool(data: str, request: Request = None):
    pass

# Correct
@mcp.tool()
def my_tool(data: str):
    pass
```

### 2. Authentication Issues

#### Problem: JWT Token Validation Fails
```
Authentication failed: Invalid token signature
```

**Solutions:**
1. **Check Cognito Configuration:**
```bash
python -c "
from services.auth_service import AuthService
auth = AuthService()
print(auth.get_config())
"
```

2. **Verify Discovery URL:**
```bash
curl https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
```

3. **Test with Authentication Disabled:**
```bash
export REQUIRE_AUTHENTICATION=false
python restaurant_reasoning_mcp_server.py
```

#### Problem: Cognito Configuration Not Found
```
Failed to load Cognito configuration: [Errno 2] No such file or directory: 'cognito_config.json'
```

**Solution:**
Create cognito_config.json file:
```json
{
    "user_pool": {
        "user_pool_id": "us-east-1_KePRX24Bn"
    },
    "app_client": {
        "client_id": "26k0pnja579pdpb1pt6savs27e"
    },
    "region": "us-east-1",
    "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
}
```

### 3. Docker Issues

#### Problem: ARM64 Platform Build Fails
```
ERROR: failed to solve: no match for platform in manifest
```

**Solutions:**
1. **Enable Docker BuildKit:**
```bash
export DOCKER_BUILDKIT=1
docker build --platform linux/arm64 .
```

2. **Use Buildx for Cross-Platform:**
```bash
docker buildx create --use
docker buildx build --platform linux/arm64 .
```

3. **Check Docker Desktop Settings:**
- Enable "Use containerd for pulling and storing images"
- Enable experimental features

#### Problem: Container Startup Fails
```
python: can't open file '/app/restaurant_reasoning_mcp_server.py': [Errno 2] No such file or directory
```

**Solution:**
Check Dockerfile COPY commands and working directory:
```dockerfile
WORKDIR /app
COPY . .
CMD ["python", "-m", "restaurant_reasoning_mcp_server"]
```

#### Problem: Port Binding Issues
```
docker: Error response from daemon: port is already allocated
```

**Solution:**
```bash
# Check what's using the port
netstat -tulpn | grep :8080

# Use different port
docker run -p 8081:8080 restaurant-reasoning-mcp

# Or stop conflicting container
docker ps
docker stop <container_id>
```

### 4. MCP Tool Issues

#### Problem: Tool Schema Validation Fails
```
ValidationError: 1 validation error for restaurants
```

**Solution:**
Ensure restaurant data matches required schema:
```python
# Required fields
restaurant = {
    "id": "string",           # Required
    "name": "string",         # Required  
    "sentiment": {            # Required
        "likes": 0,           # Required, integer ≥ 0
        "dislikes": 0,        # Required, integer ≥ 0
        "neutral": 0          # Required, integer ≥ 0
    }
}
```

#### Problem: Empty Restaurant List
```
Validation failed: Restaurant list cannot be empty
```

**Solution:**
Provide at least one restaurant:
```python
restaurants = [
    {
        "id": "test_001",
        "name": "Test Restaurant",
        "sentiment": {"likes": 10, "dislikes": 2, "neutral": 5}
    }
]
```

#### Problem: Invalid Ranking Method
```
Invalid ranking method: invalid_method
```

**Solution:**
Use supported ranking methods:
```python
# Supported methods
ranking_method = "sentiment_likes"      # Rank by likes count
ranking_method = "combined_positive"    # Rank by (likes - dislikes)
```

### 5. Deployment Issues

#### Problem: AgentCore Deployment Fails
```
ERROR: Failed to deploy agent to AgentCore
```

**Solutions:**
1. **Check AWS Credentials:**
```bash
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1
```

2. **Verify Permissions:**
Required IAM permissions:
- `BedrockAgentCoreFullAccess`
- `AmazonBedrockFullAccess`
- `AmazonS3FullAccess`
- `CloudWatchFullAccess`

3. **Check Region:**
```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
```

#### Problem: Container Build in CodeBuild Fails
```
Build failed in CodeBuild: ARM64 platform not supported
```

**Solution:**
Ensure Dockerfile specifies ARM64 platform:
```dockerfile
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim
```

### 6. Testing Issues

#### Problem: Test Authentication Fails
```
Authentication test failed: No test credentials provided
```

**Solution:**
Set test credentials:
```bash
export TEST_USERNAME=your_test_user
export TEST_PASSWORD=your_test_password

# Or use interactive prompt
python tests/test_reasoning_deployment.py
```

#### Problem: MCP Client Connection Fails
```
ConnectionError: Failed to connect to MCP server
```

**Solutions:**
1. **Check Server Status:**
```bash
curl http://localhost:8080/health
```

2. **Verify MCP URL:**
```python
# Local testing
mcp_url = "http://localhost:8080"

# AgentCore testing  
mcp_url = "https://your-agent-url.amazonaws.com"
```

3. **Check Authentication Headers:**
```python
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
```

### 7. Performance Issues

#### Problem: High Memory Usage
```
Container killed: Out of memory
```

**Solutions:**
1. **Limit Restaurant Count:**
```python
# Process in batches
batch_size = 100
for i in range(0, len(restaurants), batch_size):
    batch = restaurants[i:i+batch_size]
    result = recommend_restaurants(batch)
```

2. **Increase Container Memory:**
```bash
docker run -m 2g restaurant-reasoning-mcp
```

#### Problem: Slow Response Times
```
Request timeout after 30 seconds
```

**Solutions:**
1. **Optimize Data Processing:**
```python
# Use efficient ranking algorithms
# Cache repeated calculations
# Minimize data copying
```

2. **Increase Timeout:**
```python
# In client code
timeout = 60  # seconds
```

## Debugging Commands

### Server Health Check
```bash
# Local server
curl http://localhost:8080/health

# Check response
curl -v http://localhost:8080/health
```

### Authentication Debug
```bash
# Test auth service
python -c "
from services.auth_service import AuthService
auth = AuthService()
print('Config:', auth.get_config())
print('Status:', auth.validate_config())
"
```

### MCP Tool Testing
```bash
# Test tool import
python -c "
import restaurant_reasoning_mcp_server
print('Tools loaded successfully')
"

# Test tool execution
python -c "
from restaurant_reasoning_mcp_server import recommend_restaurants
test_data = [{'id': 'test', 'name': 'Test', 'sentiment': {'likes': 10, 'dislikes': 2, 'neutral': 5}}]
result = recommend_restaurants(test_data)
print('Tool execution successful')
"
```

### Container Debugging
```bash
# Run container interactively
docker run -it --entrypoint /bin/bash restaurant-reasoning-mcp

# Check container logs
docker logs <container_id>

# Inspect container
docker inspect <container_id>
```

### Network Debugging
```bash
# Check port availability
netstat -tulpn | grep :8080

# Test network connectivity
telnet localhost 8080

# Check Docker network
docker network ls
docker network inspect bridge
```

## Log Analysis

### Server Logs
```bash
# View server logs
tail -f /var/log/restaurant-reasoning-mcp.log

# Filter by level
grep "ERROR" /var/log/restaurant-reasoning-mcp.log
grep "WARNING" /var/log/restaurant-reasoning-mcp.log
```

### Docker Logs
```bash
# Container logs
docker logs -f <container_id>

# With timestamps
docker logs -t <container_id>

# Last N lines
docker logs --tail 100 <container_id>
```

### AWS CloudWatch Logs
```bash
# View AgentCore logs
aws logs tail /aws/bedrock-agentcore/runtimes/<agent-id> --follow

# Filter logs
aws logs filter-log-events \
  --log-group-name /aws/bedrock-agentcore/runtimes/<agent-id> \
  --filter-pattern "ERROR"
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region for services |
| `AWS_DEFAULT_REGION` | `us-east-1` | Default AWS region |
| `REQUIRE_AUTHENTICATION` | `true` | Enable/disable JWT authentication |
| `PYTHONPATH` | - | Python module search path |
| `DOCKER_CONTAINER` | `1` | Indicates running in Docker |
| `TEST_USERNAME` | - | Test user for authentication |
| `TEST_PASSWORD` | - | Test password for authentication |

## Getting Help

### Log Collection
When reporting issues, include:

1. **Server logs:**
```bash
python restaurant_reasoning_mcp_server.py > server.log 2>&1
```

2. **System information:**
```bash
python --version
docker --version
uname -a
```

3. **Configuration:**
```bash
env | grep -E "(AWS|PYTHON|DOCKER)"
```

### Support Channels
- GitHub Issues: For bug reports and feature requests
- Documentation: Check README.md and docs/ directory
- AWS Support: For AgentCore-specific issues

---

**Last Updated**: September 28, 2025  
**Version**: 1.0.0