# AgentCore Gateway MCP Tools - Authentication Guide

## Overview

The AgentCore Gateway for MCP Tools uses JWT (JSON Web Token) authentication through AWS Cognito User Pool. This guide provides comprehensive information on authentication setup, token management, and security best practices.

## Table of Contents

1. [Authentication Architecture](#authentication-architecture)
2. [AWS Cognito Configuration](#aws-cognito-configuration)
3. [JWT Token Structure](#jwt-token-structure)
4. [Authentication Flow](#authentication-flow)
5. [Token Validation Process](#token-validation-process)
6. [Client Implementation](#client-implementation)
7. [Error Handling](#error-handling)
8. [Security Best Practices](#security-best-practices)
9. [Troubleshooting](#troubleshooting)

## Authentication Architecture

### High-Level Architecture

```mermaid
sequenceDiagram
    participant Client as Client Application
    participant Cognito as AWS Cognito
    participant Gateway as AgentCore Gateway
    participant MCP as MCP Servers

    Client->>Cognito: 1. Authenticate (username/password)
    Cognito->>Client: 2. Return JWT tokens (ID, Access, Refresh)
    Client->>Gateway: 3. API Request with JWT ID token
    Gateway->>Gateway: 4. Validate JWT token
    Gateway->>Cognito: 5. Verify token signature (JWKS)
    Gateway->>MCP: 6. Forward request to MCP server
    MCP->>Gateway: 7. Return response
    Gateway->>Client: 8. Return API response
```

### Authentication Components

1. **AWS Cognito User Pool**: Manages user identities and issues JWT tokens
2. **JWT Middleware**: Validates tokens and extracts user context
3. **JWKS Endpoint**: Provides public keys for token signature verification
4. **User Context**: Extracted user information passed to MCP servers

## AWS Cognito Configuration

### Current Configuration

The AgentCore Gateway uses the following Cognito User Pool configuration:

```json
{
  "user_pool_id": "us-east-1_KePRX24Bn",
  "client_id": "1ofgeckef3po4i3us4j1m4chvd",
  "client_secret": "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
  "region": "us-east-1",
  "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration",
  "jwks_uri": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json",
  "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
  "algorithms": ["RS256"],
  "audience": "1ofgeckef3po4i3us4j1m4chvd"
}
```

### Discovery Endpoint

The OpenID Connect discovery endpoint provides configuration information:

```bash
curl -X GET "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
```

**Response**:
```json
{
  "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
  "jwks_uri": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json",
  "authorization_endpoint": "https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/authorize",
  "token_endpoint": "https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/token",
  "userinfo_endpoint": "https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/userInfo",
  "supported_identity_providers": ["COGNITO"],
  "subject_types_supported": ["public"],
  "response_types_supported": ["code", "token"],
  "scopes_supported": ["openid", "email", "profile"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "id_token_signing_alg_values_supported": ["RS256"]
}
```

## JWT Token Structure

### ID Token Claims

The JWT ID token contains the following claims:

```json
{
  "sub": "user-uuid-here",
  "aud": "1ofgeckef3po4i3us4j1m4chvd",
  "cognito:groups": ["admin", "user"],
  "email_verified": true,
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
  "cognito:username": "john.doe",
  "given_name": "John",
  "family_name": "Doe",
  "aud": "1ofgeckef3po4i3us4j1m4chvd",
  "event_id": "event-uuid",
  "token_use": "id",
  "auth_time": 1641201600,
  "exp": 1641205200,
  "iat": 1641201600,
  "email": "john.doe@example.com"
}
```

### Token Types

1. **ID Token**: Contains user identity information (used for Gateway authentication)
2. **Access Token**: Used for accessing Cognito User Pool APIs
3. **Refresh Token**: Used to obtain new ID and Access tokens

### Token Validation Requirements

The Gateway validates the following token properties:

- **Signature**: Verified using Cognito's public keys (JWKS)
- **Issuer**: Must match the expected Cognito User Pool issuer
- **Audience**: Must match the configured client ID
- **Expiration**: Token must not be expired
- **Not Before**: Token must be valid (if nbf claim present)

## Authentication Flow

### 1. User Registration/Login

#### Using AWS Amplify (Recommended)

```javascript
import { Auth } from 'aws-amplify';

// Configure Amplify
Auth.configure({
  region: 'us-east-1',
  userPoolId: 'us-east-1_KePRX24Bn',
  userPoolWebClientId: '1ofgeckef3po4i3us4j1m4chvd',
  oauth: {
    domain: 'your-domain.auth.us-east-1.amazoncognito.com',
    scope: ['openid', 'email', 'profile'],
    redirectSignIn: 'https://your-app.com/callback',
    redirectSignOut: 'https://your-app.com/logout',
    responseType: 'code'
  }
});

// Sign in user
async function signIn(username, password) {
  try {
    const user = await Auth.signIn(username, password);
    console.log('Sign in successful:', user);
    return user;
  } catch (error) {
    console.error('Sign in failed:', error);
    throw error;
  }
}

// Get current session and JWT token
async function getCurrentToken() {
  try {
    const session = await Auth.currentSession();
    const idToken = session.getIdToken().getJwtToken();
    return idToken;
  } catch (error) {
    console.error('Failed to get token:', error);
    throw error;
  }
}
```

#### Using Direct Cognito API

```python
import boto3
import base64
import hashlib
import hmac
from botocore.exceptions import ClientError

class CognitoAuthenticator:
    def __init__(self, user_pool_id, client_id, client_secret=None):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    def _calculate_secret_hash(self, username):
        """Calculate secret hash for client authentication."""
        if not self.client_secret:
            return None
        
        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def authenticate_user(self, username, password):
        """Authenticate user and return tokens."""
        auth_params = {
            'USERNAME': username,
            'PASSWORD': password
        }
        
        if self.client_secret:
            auth_params['SECRET_HASH'] = self._calculate_secret_hash(username)
        
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters=auth_params
            )
            
            return {
                'id_token': response['AuthenticationResult']['IdToken'],
                'access_token': response['AuthenticationResult']['AccessToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise Exception('Invalid username or password')
            elif error_code == 'UserNotConfirmedException':
                raise Exception('User account not confirmed')
            else:
                raise Exception(f'Authentication failed: {error_code}')
    
    def refresh_tokens(self, refresh_token, username):
        """Refresh ID and Access tokens using refresh token."""
        auth_params = {
            'REFRESH_TOKEN': refresh_token
        }
        
        if self.client_secret:
            auth_params['SECRET_HASH'] = self._calculate_secret_hash(username)
        
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters=auth_params
            )
            
            return {
                'id_token': response['AuthenticationResult']['IdToken'],
                'access_token': response['AuthenticationResult']['AccessToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            }
        
        except ClientError as e:
            raise Exception(f'Token refresh failed: {e.response["Error"]["Code"]}')

# Usage
authenticator = CognitoAuthenticator(
    user_pool_id='us-east-1_KePRX24Bn',
    client_id='1ofgeckef3po4i3us4j1m4chvd'
)

tokens = authenticator.authenticate_user('username', 'password')
id_token = tokens['id_token']
```

### 2. Making Authenticated Requests

#### HTTP Header Format

All API requests must include the JWT ID token in the Authorization header:

```http
Authorization: Bearer <jwt_id_token>
Content-Type: application/json
```

#### Example Request

```bash
curl -X POST "https://your-gateway.amazonaws.com/api/v1/restaurants/search/district" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "districts": ["Central district", "Admiralty"]
  }'
```

## Token Validation Process

### Gateway Token Validation

The Gateway performs the following validation steps:

1. **Extract Token**: Extract JWT token from Authorization header
2. **Decode Header**: Decode JWT header to get key ID (kid)
3. **Fetch JWKS**: Retrieve public keys from Cognito JWKS endpoint
4. **Verify Signature**: Verify token signature using appropriate public key
5. **Validate Claims**: Check issuer, audience, expiration, and other claims
6. **Extract User Context**: Extract user information for request context

### Implementation Example

```python
import jwt
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class JWTValidator:
    def __init__(self, user_pool_id: str, client_id: str, region: str):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        self.jwks_url = f"{self.issuer}/.well-known/jwks.json"
        self._jwks_cache = None
        self._jwks_cache_time = None
    
    def _get_jwks(self) -> Dict[str, Any]:
        """Fetch and cache JWKS from Cognito."""
        now = datetime.now(timezone.utc)
        
        # Cache JWKS for 1 hour
        if (self._jwks_cache is None or 
            self._jwks_cache_time is None or 
            (now - self._jwks_cache_time).total_seconds() > 3600):
            
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cache_time = now
        
        return self._jwks_cache
    
    def _get_public_key(self, kid: str) -> str:
        """Get public key for given key ID."""
        jwks = self._get_jwks()
        
        for key in jwks['keys']:
            if key['kid'] == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        
        raise ValueError(f"Public key not found for kid: {kid}")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return claims."""
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if not kid:
                raise ValueError("Token header missing 'kid' claim")
            
            # Get public key
            public_key = self._get_public_key(kid)
            
            # Validate and decode token
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.issuer,
                options={
                    'verify_exp': True,
                    'verify_aud': True,
                    'verify_iss': True,
                    'verify_signature': True
                }
            )
            
            # Additional validation
            self._validate_token_claims(decoded_token)
            
            return decoded_token
        
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidAudienceError:
            raise ValueError("Invalid token audience")
        except jwt.InvalidIssuerError:
            raise ValueError("Invalid token issuer")
        except jwt.InvalidSignatureError:
            raise ValueError("Invalid token signature")
        except Exception as e:
            raise ValueError(f"Token validation failed: {str(e)}")
    
    def _validate_token_claims(self, claims: Dict[str, Any]) -> None:
        """Perform additional claim validation."""
        # Verify token use
        if claims.get('token_use') != 'id':
            raise ValueError("Token is not an ID token")
        
        # Verify authentication time (optional)
        auth_time = claims.get('auth_time')
        if auth_time:
            # Token should not be older than 24 hours
            now = datetime.now(timezone.utc).timestamp()
            if now - auth_time > 86400:  # 24 hours
                raise ValueError("Token authentication time too old")
    
    def extract_user_context(self, claims: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user context from token claims."""
        return {
            'user_id': claims.get('sub'),
            'username': claims.get('cognito:username'),
            'email': claims.get('email'),
            'email_verified': claims.get('email_verified', False),
            'groups': claims.get('cognito:groups', []),
            'given_name': claims.get('given_name'),
            'family_name': claims.get('family_name'),
            'auth_time': claims.get('auth_time'),
            'token_issued_at': claims.get('iat'),
            'token_expires_at': claims.get('exp')
        }

# Usage in middleware
validator = JWTValidator(
    user_pool_id='us-east-1_KePRX24Bn',
    client_id='1ofgeckef3po4i3us4j1m4chvd',
    region='us-east-1'
)

def authenticate_request(authorization_header: str) -> Dict[str, Any]:
    """Authenticate request and return user context."""
    if not authorization_header:
        raise ValueError("Authorization header required")
    
    if not authorization_header.startswith('Bearer '):
        raise ValueError("Invalid authorization header format")
    
    token = authorization_header[7:]  # Remove 'Bearer ' prefix
    
    # Validate token
    claims = validator.validate_token(token)
    
    # Extract user context
    user_context = validator.extract_user_context(claims)
    
    return user_context
```

## Client Implementation

### JavaScript/TypeScript Client

```typescript
interface AuthConfig {
  userPoolId: string;
  clientId: string;
  region: string;
}

interface TokenSet {
  idToken: string;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

class CognitoAuthClient {
  private config: AuthConfig;
  private tokenSet: TokenSet | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  constructor(config: AuthConfig) {
    this.config = config;
  }

  async signIn(username: string, password: string): Promise<TokenSet> {
    const response = await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        AuthFlow: 'USER_PASSWORD_AUTH',
        AuthParameters: {
          USERNAME: username,
          PASSWORD: password
        }
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Authentication failed: ${error.message}`);
    }

    const data = await response.json();
    const authResult = data.AuthenticationResult;

    this.tokenSet = {
      idToken: authResult.IdToken,
      accessToken: authResult.AccessToken,
      refreshToken: authResult.RefreshToken,
      expiresIn: authResult.ExpiresIn
    };

    // Set up automatic token refresh
    this.scheduleTokenRefresh();

    return this.tokenSet;
  }

  async refreshTokens(): Promise<TokenSet> {
    if (!this.tokenSet?.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`https://cognito-idp.${this.config.region}.amazonaws.com/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
      },
      body: JSON.stringify({
        ClientId: this.config.clientId,
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        AuthParameters: {
          REFRESH_TOKEN: this.tokenSet.refreshToken
        }
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Token refresh failed: ${error.message}`);
    }

    const data = await response.json();
    const authResult = data.AuthenticationResult;

    this.tokenSet = {
      ...this.tokenSet,
      idToken: authResult.IdToken,
      accessToken: authResult.AccessToken,
      expiresIn: authResult.ExpiresIn
    };

    this.scheduleTokenRefresh();
    return this.tokenSet;
  }

  private scheduleTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (this.tokenSet) {
      // Refresh token 5 minutes before expiration
      const refreshTime = (this.tokenSet.expiresIn - 300) * 1000;
      this.refreshTimer = setTimeout(() => {
        this.refreshTokens().catch(console.error);
      }, refreshTime);
    }
  }

  getCurrentToken(): string | null {
    return this.tokenSet?.idToken || null;
  }

  signOut(): void {
    this.tokenSet = null;
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }
}

// Usage
const authClient = new CognitoAuthClient({
  userPoolId: 'us-east-1_KePRX24Bn',
  clientId: '1ofgeckef3po4i3us4j1m4chvd',
  region: 'us-east-1'
});

// Sign in and get tokens
const tokens = await authClient.signIn('username', 'password');

// Use ID token for API requests
const idToken = authClient.getCurrentToken();
```

### React Hook for Authentication

```typescript
import { useState, useEffect, useCallback } from 'react';
import { CognitoAuthClient } from './CognitoAuthClient';

interface UseAuthOptions {
  userPoolId: string;
  clientId: string;
  region: string;
}

export function useAuth({ userPoolId, clientId, region }: UseAuthOptions) {
  const [authClient] = useState(() => new CognitoAuthClient({ userPoolId, clientId, region }));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const signIn = useCallback(async (username: string, password: string) => {
    setLoading(true);
    setError(null);

    try {
      await authClient.signIn(username, password);
      setIsAuthenticated(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, [authClient]);

  const signOut = useCallback(() => {
    authClient.signOut();
    setIsAuthenticated(false);
    setError(null);
  }, [authClient]);

  const getToken = useCallback(() => {
    return authClient.getCurrentToken();
  }, [authClient]);

  // Check authentication status on mount
  useEffect(() => {
    const token = authClient.getCurrentToken();
    setIsAuthenticated(!!token);
  }, [authClient]);

  return {
    isAuthenticated,
    loading,
    error,
    signIn,
    signOut,
    getToken
  };
}
```

## Error Handling

### Authentication Error Types

1. **Missing Token** (401 Unauthorized)
2. **Invalid Token** (401 Unauthorized)
3. **Expired Token** (401 Unauthorized)
4. **Invalid Signature** (401 Unauthorized)
5. **Invalid Audience** (401 Unauthorized)
6. **Invalid Issuer** (401 Unauthorized)

### Error Response Format

```json
{
  "success": false,
  "error": {
    "type": "AuthenticationError",
    "message": "Invalid or expired JWT token",
    "details": {
      "error_code": "TOKEN_EXPIRED",
      "token_validation_failed": true,
      "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
    },
    "timestamp": "2025-01-03T10:30:00Z",
    "request_id": "req_12345"
  }
}
```

### Client Error Handling

```typescript
class AuthenticatedAPIClient {
  private authClient: CognitoAuthClient;
  private baseUrl: string;

  constructor(authClient: CognitoAuthClient, baseUrl: string) {
    this.authClient = authClient;
    this.baseUrl = baseUrl;
  }

  async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.authClient.getCurrentToken();
    
    if (!token) {
      throw new Error('No authentication token available');
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (response.status === 401) {
      // Token expired or invalid, try to refresh
      try {
        await this.authClient.refreshTokens();
        const newToken = this.authClient.getCurrentToken();
        
        // Retry request with new token
        const retryResponse = await fetch(`${this.baseUrl}${endpoint}`, {
          ...options,
          headers: {
            'Authorization': `Bearer ${newToken}`,
            'Content-Type': 'application/json',
            ...options.headers
          }
        });

        if (!retryResponse.ok) {
          throw new Error(`Request failed: ${retryResponse.status}`);
        }

        return retryResponse.json();
      } catch (refreshError) {
        // Refresh failed, user needs to sign in again
        this.authClient.signOut();
        throw new Error('Authentication expired, please sign in again');
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `Request failed: ${response.status}`);
    }

    return response.json();
  }
}
```

## Security Best Practices

### Token Security

1. **Secure Storage**:
   - Store tokens in secure storage (iOS Keychain, Android Keystore)
   - Use HttpOnly cookies for web applications when possible
   - Never store tokens in localStorage for sensitive applications

2. **Token Transmission**:
   - Always use HTTPS for token transmission
   - Include tokens only in Authorization headers
   - Never include tokens in URL parameters or query strings

3. **Token Lifecycle**:
   - Implement automatic token refresh
   - Clear tokens on application logout
   - Handle token expiration gracefully

### Implementation Security

```typescript
// Secure token storage for React Native
import * as Keychain from 'react-native-keychain';

class SecureTokenStorage {
  private static readonly TOKEN_KEY = 'agentcore_auth_tokens';

  static async storeTokens(tokens: TokenSet): Promise<void> {
    await Keychain.setInternetCredentials(
      this.TOKEN_KEY,
      'tokens',
      JSON.stringify(tokens)
    );
  }

  static async getTokens(): Promise<TokenSet | null> {
    try {
      const credentials = await Keychain.getInternetCredentials(this.TOKEN_KEY);
      if (credentials) {
        return JSON.parse(credentials.password);
      }
    } catch (error) {
      console.error('Failed to retrieve tokens:', error);
    }
    return null;
  }

  static async clearTokens(): Promise<void> {
    await Keychain.resetInternetCredentials(this.TOKEN_KEY);
  }
}
```

### Network Security

1. **Certificate Pinning**: Implement certificate pinning for production apps
2. **Request Validation**: Validate all request parameters
3. **Rate Limiting**: Implement client-side rate limiting
4. **Timeout Configuration**: Set appropriate request timeouts

## Troubleshooting

### Common Issues

#### 1. Token Validation Failures

**Symptoms**: 401 Unauthorized responses with token validation errors

**Causes**:
- Expired tokens
- Invalid token signature
- Incorrect audience or issuer
- Clock skew between client and server

**Solutions**:
```bash
# Check token expiration
echo "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." | base64 -d | jq .exp

# Verify Cognito configuration
curl -X GET "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"

# Test token validation
python scripts/validate_jwt_token.py --token YOUR_TOKEN
```

#### 2. JWKS Retrieval Issues

**Symptoms**: Token validation fails with "Unable to find a signing key"

**Causes**:
- Network connectivity issues
- JWKS endpoint unavailable
- Incorrect JWKS URL

**Solutions**:
```bash
# Test JWKS endpoint
curl -X GET "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json"

# Verify key ID in token header
echo "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IktFWV9JRCJ9" | base64 -d | jq .kid
```

#### 3. Authentication Flow Issues

**Symptoms**: Unable to obtain tokens from Cognito

**Causes**:
- Incorrect client configuration
- User not confirmed
- Invalid credentials
- Client secret mismatch

**Solutions**:
```python
# Test authentication flow
authenticator = CognitoAuthenticator(
    user_pool_id='us-east-1_KePRX24Bn',
    client_id='1ofgeckef3po4i3us4j1m4chvd'
)

try:
    tokens = authenticator.authenticate_user('username', 'password')
    print("Authentication successful")
except Exception as e:
    print(f"Authentication failed: {e}")
```

### Debug Tools

#### Token Decoder

```python
import jwt
import json

def decode_token_debug(token: str) -> None:
    """Debug JWT token without verification."""
    try:
        # Decode header
        header = jwt.get_unverified_header(token)
        print("Token Header:")
        print(json.dumps(header, indent=2))
        
        # Decode payload
        payload = jwt.decode(token, options={"verify_signature": False})
        print("\nToken Payload:")
        print(json.dumps(payload, indent=2))
        
        # Check expiration
        import time
        exp = payload.get('exp')
        if exp:
            exp_time = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(exp))
            current_time = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
            print(f"\nToken expires: {exp_time}")
            print(f"Current time:  {current_time}")
            print(f"Token expired: {exp < time.time()}")
        
    except Exception as e:
        print(f"Token decode failed: {e}")

# Usage
decode_token_debug("your_jwt_token_here")
```

#### Authentication Test Script

```bash
#!/bin/bash
# test_auth.sh - Test authentication flow

USER_POOL_ID="us-east-1_KePRX24Bn"
CLIENT_ID="1ofgeckef3po4i3us4j1m4chvd"
GATEWAY_URL="https://your-gateway.amazonaws.com"

echo "Testing Cognito configuration..."
curl -s "https://cognito-idp.us-east-1.amazonaws.com/${USER_POOL_ID}/.well-known/openid-configuration" | jq .

echo -e "\nTesting JWKS endpoint..."
curl -s "https://cognito-idp.us-east-1.amazonaws.com/${USER_POOL_ID}/.well-known/jwks.json" | jq .

echo -e "\nTesting Gateway health (no auth required)..."
curl -s "${GATEWAY_URL}/health" | jq .

echo -e "\nTesting authenticated endpoint (requires valid token)..."
read -p "Enter JWT token: " JWT_TOKEN
curl -s -X POST "${GATEWAY_URL}/api/v1/restaurants/search/district" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"districts": ["Central district"]}' | jq .
```

---

**Last Updated**: January 3, 2025  
**Version**: 1.0.0  
**Cognito User Pool**: us-east-1_KePRX24Bn  
**Client ID**: 1ofgeckef3po4i3us4j1m4chvd