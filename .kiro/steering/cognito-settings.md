# Cognito Authentication Settings

This document contains the Cognito User Pool configuration for MBTI Travel Assistant authentication and OIDC integration.

## ⚠️ CRITICAL URL FORMAT REQUIREMENT

**AgentCore requires OIDC discovery URLs to end with `openid-configuration` (with hyphens, NOT underscores)**

- ✅ **CORRECT:** `/.well-known/openid-configuration`
- ❌ **WRONG:** `/.well-known/openid_configuration`

**AgentCore validation regex:** `.+/\.well-known/openid-configuration$`

Any URL not matching this exact pattern will cause AgentCore deployment failures.

## Primary User Pool (New - Recommended)

### User Pool Information
- **User Pool ID:** `us-east-1_KePRX24Bn`
- **User Pool Name:** `mbti-travel-oidc-pool`
- **Region:** `us-east-1`
- **Domain:** `mbti-travel-oidc-334662794`
- **Account ID:** `209803798463`

### App Client Information
- **Client ID:** `1ofgeckef3po4i3us4j1m4chvd`
- **Client Secret:** `t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9`
- **Client Name:** `mbti-travel-oidc-client`

**⚠️ IMPORTANT: Client Secret Usage**
- Client secret is REQUIRED for authentication flows
- Must calculate SECRET_HASH for all authentication requests
- SECRET_HASH = Base64(HMAC-SHA256(client_secret, username + client_id))

**Python SECRET_HASH Calculation:**
```python
import hmac
import hashlib
import base64

def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

# Usage
secret_hash = calculate_secret_hash(
    "test@mbti-travel.com", 
    "1ofgeckef3po4i3us4j1m4chvd", 
    "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9"


### Test User Account
- **Email:** `test@mbti-travel.com`
- **Password:** `TestPass1234!`
- **Status:** Active (permanent password set)
- **Username:** `c4680438-7051-700f-4302-a4113cdea6ca` (auto-generated)

## OIDC Endpoints

### Standard Format (WORKING - Use This)
```
Issuer: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn
Discovery: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
JWKS: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json
```

### Domain Format (NOT WORKING - Avoid)
```
Issuer: https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com
Discovery: https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration (404 ERROR)
JWKS: https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/jwks.json
```

### ⚠️ URL Format Validation
**Before using any OIDC URL, verify it ends with the correct pattern:**
```bash
# Test URL format compliance
echo "https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration" | grep -E '\.well-known/openid-configuration$'
# Should return the URL if correct, nothing if wrong format
```

## OAuth Configuration

### Supported Flows
- **OAuth Flows:** Authorization Code (`code`)
- **Scopes:** `openid`, `email`, `profile`
- **Identity Providers:** `COGNITO`

### URLs
- **Callback URL:** `https://example.com/callback`
- **Logout URL:** `https://example.com/logout`

### Token Settings
- **Refresh Token Validity:** 30 days
- **Auth Session Validity:** 3 minutes
- **Token Revocation:** Enabled

## Legacy User Pool (Has OIDC Issues)

### User Pool Information
- **User Pool ID:** `us-east-1_78QaUenG5`
- **User Pool Name:** `User pool - fjh9tf`
- **Region:** `us-east-1`
- **Domain:** `us-east-178qaueng5`

### App Client Information
- **Client ID:** `4kglrgv7r8pmvveaqi1an0rc0k`
- **Client Name:** `mbti-travel-oidc-pool`

### Known Issues
- OIDC discovery endpoint returns 400 BadRequest
- JWKS endpoint works correctly (returns 200)
- Standard format endpoints have compatibility issues

## AgentCore Integration

### JWT Authentication Configuration
```yaml
authentication:
  type: "jwt"
  config:
    customJWTAuthorizer:
      allowedClients: ["1ofgeckef3po4i3us4j1m4chvd"]
      discoveryUrl: "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
```

### ⚠️ CRITICAL: AgentCore URL Format Requirements
**AgentCore has strict regex validation for `discoveryUrl` that requires:**
- URL must end with `/.well-known/openid-configuration` (with hyphens)
- Pattern: `.+/\.well-known/openid-configuration$`
- URLs with underscores (`openid_configuration`) will fail validation

**Correct Format Examples (WORKING):**
```
✅ https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
```

**Incorrect Format (will fail):**
```
❌ https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid_configuration (underscores)
❌ https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration (domain format returns 404)
❌ Any URL not ending with the exact pattern above
```

### Environment Variables
```bash
# Primary User Pool (Recommended)
COGNITO_USER_POOL_ID=us-east-1_KePRX24Bn
COGNITO_CLIENT_ID=1ofgeckef3po4i3us4j1m4chvd
COGNITO_CLIENT_SECRET=t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9
COGNITO_REGION=us-east-1
COGNITO_DOMAIN=mbti-travel-oidc-334662794

# OIDC Endpoints (WORKING - Use Standard Format)
OIDC_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn
OIDC_DISCOVERY_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration
JWKS_URL=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json
```

## Security Configuration

### Password Policy
- **Minimum Length:** 8 characters
- **Require Uppercase:** Yes
- **Require Lowercase:** Yes
- **Require Numbers:** Yes
- **Require Symbols:** Yes
- **Temporary Password Validity:** 7 days

### User Settings
- **Username Attributes:** Email
- **Auto Verified Attributes:** Email
- **MFA Configuration:** OFF
- **Deletion Protection:** INACTIVE (new pool), ACTIVE (legacy pool)

## User Pool Creation Commands

### Complete Setup from Scratch
These commands create the entire Cognito setup that resulted in our current working configuration:

#### 1. Create User Pool
```bash
aws cognito-idp create-user-pool \
  --pool-name "mbti-travel-oidc-pool" \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 8,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true,
      "TemporaryPasswordValidityDays": 7
    }
  }' \
  --auto-verified-attributes email \
  --username-attributes email \
  --verification-message-template '{
    "DefaultEmailOption": "CONFIRM_WITH_CODE"
  }' \
  --admin-create-user-config '{
    "AllowAdminCreateUserOnly": false,
    "UnusedAccountValidityDays": 7
  }' \
  --user-pool-tags '{
    "Project": "MBTI-Travel-Assistant",
    "Environment": "Production",
    "Purpose": "OIDC-Authentication"
  }' \
  --deletion-protection INACTIVE \
  --region us-east-1
```

**Expected Output:**
```json
{
    "UserPool": {
        "Id": "us-east-1_KePRX24Bn",
        "Name": "mbti-travel-oidc-pool",
        "Policies": {...},
        "CreationDate": "2025-10-04T...",
        "LastModifiedDate": "2025-10-04T..."
    }
}
```

#### 2. Create App Client
```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id "us-east-1_KePRX24Bn" \
  --client-name "mbti-travel-oidc-client" \
  --generate-secret \
  --supported-identity-providers COGNITO \
  --callback-urls "https://example.com/callback" \
  --logout-urls "https://example.com/logout" \
  --allowed-o-auth-flows code \
  --allowed-o-auth-scopes openid email profile \
  --allowed-o-auth-flows-user-pool-client \
  --explicit-auth-flows ADMIN_NO_SRP_AUTH ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --refresh-token-validity 30 \
  --access-token-validity 60 \
  --id-token-validity 60 \
  --token-validity-units '{
    "RefreshToken": "days",
    "AccessToken": "minutes", 
    "IdToken": "minutes"
  }' \
  --prevent-user-existence-errors ENABLED \
  --enable-token-revocation \
  --region us-east-1
```

**Expected Output:**
```json
{
    "UserPoolClient": {
        "UserPoolId": "us-east-1_KePRX24Bn",
        "ClientName": "mbti-travel-oidc-client",
        "ClientId": "1ofgeckef3po4i3us4j1m4chvd",
        "ClientSecret": "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
        "CreationDate": "2025-10-04T...",
        "LastModifiedDate": "2025-10-04T..."
    }
}
```

#### 3. Create User Pool Domain
```bash
aws cognito-idp create-user-pool-domain \
  --domain "mbti-travel-oidc-334662794" \
  --user-pool-id "us-east-1_KePRX24Bn" \
  --region us-east-1
```

**Expected Output:**
```json
{
    "CloudFrontDomain": "mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com"
}
```

#### 4. Create Test User
```bash
# Create user with temporary password
aws cognito-idp admin-create-user \
  --user-pool-id "us-east-1_KePRX24Bn" \
  --username "test@mbti-travel.com" \
  --user-attributes \
    Name=email,Value=test@mbti-travel.com \
    Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS \
  --region us-east-1

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id "us-east-1_KePRX24Bn" \
  --username "test@mbti-travel.com" \
  --password "TestPass1234!" \
  --permanent \
  --region us-east-1
```

**Expected Output:**
```json
{
    "User": {
        "Username": "c4680438-7051-700f-4302-a4113cdea6ca",
        "Attributes": [
            {
                "Name": "sub",
                "Value": "c4680438-7051-700f-4302-a4113cdea6ca"
            },
            {
                "Name": "email_verified",
                "Value": "true"
            },
            {
                "Name": "email",
                "Value": "test@mbti-travel.com"
            }
        ],
        "UserCreateDate": "2025-10-04T...",
        "UserLastModifiedDate": "2025-10-04T...",
        "Enabled": true,
        "UserStatus": "CONFIRMED"
    }
}
```

#### 5. Verify OIDC Endpoints
```bash
# Wait 5-10 minutes for domain propagation, then test
curl -s "https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration" | jq .

curl -s "https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/jwks.json" | jq .
```

## AWS CLI Commands

### Verify User Pool
```bash
aws cognito-idp describe-user-pool --user-pool-id us-east-1_KePRX24Bn --region us-east-1
```

### List App Clients
```bash
aws cognito-idp list-user-pool-clients --user-pool-id us-east-1_KePRX24Bn --region us-east-1
```

### Test User Authentication
```bash
aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_KePRX24Bn \
  --client-id 1ofgeckef3po4i3us4j1m4chvd \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=test@mbti-travel.com,PASSWORD=TestPass1234! \
  --region us-east-1
```

## Troubleshooting

### ⚠️ CRITICAL: USER_PASSWORD_AUTH Flow Not Enabled Error

**Problem:** `InvalidParameterException: USER_PASSWORD_AUTH flow not enabled for this client`

**Root Cause:** Cognito app client doesn't have the required authentication flows enabled.

**Solution:** Update the app client to enable the required auth flows using AWS CLI:

```bash
# Enable required authentication flows
aws cognito-idp update-user-pool-client \
  --user-pool-id us-east-1_KePRX24Bn \
  --client-id 1ofgeckef3po4i3us4j1m4chvd \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_ADMIN_USER_PASSWORD_AUTH \
  --region us-east-1
```

**Important Notes:**
- Use only `ALLOW_` prefixed auth flows (new format)
- Cannot mix legacy auth flows (without `ALLOW_` prefix) with new format
- Required flows for JWT authentication:
  - `ALLOW_USER_PASSWORD_AUTH`: For username/password authentication
  - `ALLOW_USER_SRP_AUTH`: For SRP authentication
  - `ALLOW_REFRESH_TOKEN_AUTH`: For token refresh
  - `ALLOW_ADMIN_USER_PASSWORD_AUTH`: For admin authentication

**Verification:**
```bash
# Check current auth flows
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_KePRX24Bn \
  --client-id 1ofgeckef3po4i3us4j1m4chvd \
  --region us-east-1 \
  --query 'UserPoolClient.ExplicitAuthFlows'
```

### ⚠️ CRITICAL: URL Format Issues
**Problem:** AgentCore `customJWTAuthorizer` validation fails with regex pattern errors.
**Root Cause:** AgentCore has strict validation requiring URLs to end with `openid-configuration` (hyphens).
**Solution:** **Always ensure OIDC discovery URLs end with `/.well-known/openid-configuration`**

### URL Format Validation Steps
1. **Validate URL Format First**
```bash
# Test the discovery URL format - MUST end with openid-configuration
curl -s "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
curl -s "https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration"

# Verify AgentCore regex pattern compliance
echo "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration" | grep -E '\.well-known/openid-configuration$'
```

### OIDC Discovery Issues
- Use domain-based endpoints instead of standard format
- Wait 5-10 minutes after domain creation for full provisioning
- JWKS endpoint typically works immediately
- Standard format may return 400 BadRequest for some User Pools

### Common Error Responses
```json
{
  "code": "BadRequest",
  "message": "The server did not understand the operation that was requested.",
  "type": "client"
}
```

### Validation Commands
```bash
# Test OIDC Discovery (CORRECT FORMAT - standard Cognito format)
curl -s "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"

# Test JWKS
curl -s "https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/jwks.json"

# Validate AgentCore URL Format Compliance
echo "URL Format Check:"
echo "✅ CORRECT: /.well-known/openid-configuration (hyphens)"
echo "❌ WRONG:   /.well-known/openid_configuration (underscores)"

# Test regex pattern that AgentCore uses
test_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
if echo "$test_url" | grep -qE '\.well-known/openid-configuration$'; then
    echo "✅ URL passes AgentCore validation"
else
    echo "❌ URL fails AgentCore validation"
fi
```

## Notes

- **Created:** October 4, 2025
- **Domain Provisioning:** May take 5-10 minutes for full availability
- **Recommended Use:** Use the new User Pool (`us-east-1_KePRX24Bn`) for all new integrations
- **Legacy Support:** Keep legacy pool for existing integrations until migration is complete
- **Test Account:** Available for development and testing purposes
- **⚠️ CRITICAL:** Always verify OIDC URLs end with `openid-configuration` (hyphens) before AgentCore deployment

## Integration Examples

### Python JWT Validation
```python
import jwt
import requests

# Get JWKS
jwks_url = "https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()

# Validate token
def validate_token(token):
    try:
        decoded = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="1ofgeckef3po4i3us4j1m4chvd",
            issuer="https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com"
        )
        return decoded
    except jwt.InvalidTokenError:
        return None
```

### FastAPI Integration
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    decoded = validate_token(token.credentials)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded
```

## AgentCore Deployment Validation

### Pre-Deployment URL Validation
**Always run this validation before deploying to AgentCore:**

```bash
#!/bin/bash
# validate_oidc_urls.sh

DISCOVERY_URL="https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration"

echo "🔍 Validating OIDC URL format for AgentCore compatibility..."

# Check URL format
if echo "$DISCOVERY_URL" | grep -qE '\.well-known/openid-configuration$'; then
    echo "✅ URL format is correct: ends with openid-configuration (hyphens)"
else
    echo "❌ URL format is WRONG: must end with openid-configuration (hyphens)"
    exit 1
fi

# Test URL accessibility
if curl -s -f "$DISCOVERY_URL" > /dev/null; then
    echo "✅ OIDC discovery endpoint is accessible"
else
    echo "❌ OIDC discovery endpoint is not accessible"
    exit 1
fi

echo "🎉 All validations passed! URL is ready for AgentCore deployment."
```

### AgentCore Configuration Validation
```python
import re

def validate_agentcore_discovery_url(url):
    """Validate OIDC discovery URL for AgentCore compatibility."""
    
    # AgentCore regex pattern
    pattern = r'.+/\.well-known/openid-configuration$'
    
    if re.match(pattern, url):
        print(f"✅ URL passes AgentCore validation: {url}")
        return True
    else:
        print(f"❌ URL fails AgentCore validation: {url}")
        print("   Must end with: /.well-known/openid-configuration")
        return False

# Test URLs
test_urls = [
    "https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration",  # ✅ Correct
    "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration",      # ✅ Correct
    "https://example.com/.well-known/openid_configuration",  # ❌ Wrong (underscores)
]

for url in test_urls:
    validate_agentcore_discovery_url(url)
```