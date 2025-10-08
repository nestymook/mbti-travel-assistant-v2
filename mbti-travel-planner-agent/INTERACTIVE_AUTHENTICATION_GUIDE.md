# Interactive Cognito Authentication Guide

This guide explains how to use the interactive Cognito authentication system with the MBTI Travel Planner Agent tests.

## Overview

The interactive authentication system provides a user-friendly way to authenticate with AWS Cognito during testing. It prompts for credentials and manages JWT tokens automatically throughout the test workflow.

## Features

- **Default Test User**: Automatically suggests `test@mbti-travel.com` as the default username
- **Secure Password Input**: Uses `getpass` for hidden password entry
- **JWT Token Management**: Automatically handles token refresh and expiration
- **Authentication Validation**: Validates JWT token format and expiration
- **Session Management**: Maintains authentication state throughout the test session
- **Automatic Cleanup**: Logs out and cleans up tokens when tests complete

## Quick Start

### 1. Run Interactive Authentication Demo

```bash
cd mbti-travel-planner-agent
python run_interactive_auth_test.py
```

This will:
- Prompt for Cognito credentials (default: `test@mbti-travel.com`)
- Test the authentication system
- Demonstrate JWT token usage
- Show user information
- Simulate API workflow
- Clean up automatically

### 2. Run Comprehensive Test with Interactive Auth

```bash
cd mbti-travel-planner-agent
python test_three_day_workflow_comprehensive.py
```

This will:
- Start with interactive Cognito authentication
- Use the JWT token throughout all tests
- Test restaurant search and reasoning agents
- Validate complete three-day workflow
- Generate comprehensive test report

## Authentication Flow

### Step 1: Credential Prompt
```
COGNITO AUTHENTICATION REQUIRED
============================================================
Username (default: test@mbti-travel.com): [ENTER for default]
Password: [hidden input]
✅ Credentials entered successfully
```

### Step 2: Authentication Process
```
🔐 Authenticating user: test@mbti-travel.com
✅ Authentication successful for test@mbti-travel.com
🕒 Token expires at: 2025-01-10 15:30:45 UTC
⚡ Authentication time: 1.234 seconds
```

### Step 3: JWT Token Usage
```
✅ JWT token obtained successfully
📊 Token structure: 3 parts (header.payload.signature)
🔑 Token length: 1847 characters
🕒 Token expires: 2025-01-10T15:30:45.123456
```

## Configuration

### Cognito Configuration File
The system uses `config/cognito_config.json`:

```json
{
    "user_pool_id": "us-east-1_KePRX24Bn",
    "client_id": "1ofgeckef3po4i3us4j1m4chvd",
    "client_secret": "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
    "region": "us-east-1"
}
```

### Test User Account
- **Username**: `test@mbti-travel.com`
- **Password**: `TestPass1234!` (or your configured password)
- **Status**: Active with permanent password

## Usage in Tests

### Basic Authentication
```python
from services.interactive_auth_service import InteractiveAuthService

# Initialize authentication service
auth_service = InteractiveAuthService()

# Authenticate interactively (prompts for credentials)
auth_info = await auth_service.authenticate_user()

# Get JWT token for API calls
jwt_token = await auth_service.get_jwt_token()

# Get authentication headers
headers = auth_service.get_authentication_headers()
```

### Advanced Usage
```python
# Check authentication status
if auth_service.is_authenticated():
    print("User is authenticated")

# Get user information
user_info = auth_service.get_user_info()
print(f"Username: {user_info['username']}")

# Refresh token automatically
jwt_token = await auth_service.get_jwt_token()  # Handles refresh

# Logout and cleanup
await auth_service.logout()
```

## Test Integration

### Restaurant Search Tool
```python
# Create search tool with interactive auth
search_tool = RestaurantSearchTool(
    runtime_client=agentcore_client,
    agent_arn=config.restaurant_search_agent_arn,
    auth_manager=None  # Use interactive auth directly
)

# Set JWT token from interactive auth
search_tool.jwt_token = await interactive_auth.get_jwt_token()

# Use the tool
results = await search_tool.search_restaurants_by_district(["Central district"])
```

### Restaurant Reasoning Tool
```python
# Create reasoning tool with interactive auth
reasoning_tool = RestaurantReasoningTool(
    runtime_client=agentcore_client,
    agent_arn=config.restaurant_reasoning_agent_arn,
    auth_manager=None  # Use interactive auth directly
)

# Set JWT token from interactive auth
reasoning_tool.jwt_token = await interactive_auth.get_jwt_token()

# Use the tool
recommendations = await reasoning_tool.recommend_restaurants(restaurants, "sentiment_likes")
```

## Error Handling

### Common Errors and Solutions

#### Invalid Credentials
```
❌ Authentication failed: Invalid username or password
```
**Solution**: Check username and password, ensure test user account is active

#### Token Expired
```
🔄 JWT token expired, refreshing...
✅ JWT token refreshed successfully
```
**Solution**: Automatic - the system handles token refresh

#### Network Issues
```
❌ Failed to authenticate: Network connection error
```
**Solution**: Check internet connection and AWS region accessibility

#### Configuration Issues
```
❌ Failed to load Cognito configuration: Missing required fields
```
**Solution**: Ensure `config/cognito_config.json` exists with all required fields

## Security Features

### Token Security
- JWT tokens are never logged in full
- Passwords are hidden during input using `getpass`
- Tokens are automatically cleared on logout
- Refresh tokens are securely managed

### Validation
- JWT token format validation
- Token expiration checking
- Automatic token refresh
- Authentication state verification

## Troubleshooting

### Debug Mode
Enable debug logging for detailed authentication flow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Token Validation
```python
# Validate token format
is_valid = auth_service.validate_token_format(jwt_token)
print(f"Token format valid: {is_valid}")

# Check expiration
is_authenticated = auth_service.is_authenticated()
print(f"Currently authenticated: {is_authenticated}")
```

### Configuration Validation
```python
# Load and validate configuration
config = auth_service.load_cognito_config()
print(f"Configuration loaded: {config}")

# Initialize Cognito client
auth_service.initialize_cognito_client()
print("Cognito client initialized successfully")
```

## Best Practices

1. **Always use default username**: Press ENTER to use `test@mbti-travel.com`
2. **Secure password handling**: Never hardcode passwords in scripts
3. **Token refresh**: Let the system handle automatic token refresh
4. **Proper cleanup**: Always call `logout()` when tests complete
5. **Error handling**: Wrap authentication calls in try-catch blocks
6. **Session management**: Reuse authentication throughout test session

## Integration Examples

See the following files for complete examples:
- `run_interactive_auth_test.py` - Basic authentication demo
- `test_three_day_workflow_comprehensive.py` - Full workflow integration
- `services/interactive_auth_service.py` - Implementation details

## Support

For issues with interactive authentication:
1. Check Cognito configuration in `config/cognito_config.json`
2. Verify test user account status in AWS Cognito console
3. Ensure network connectivity to AWS services
4. Review authentication logs for detailed error information