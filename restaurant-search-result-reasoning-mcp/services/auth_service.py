"""
Authentication service for Cognito integration with SRP authentication flow.
Adapted for restaurant reasoning MCP server.
"""

import json
import base64
import hashlib
import hmac
import secrets
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
import jwt
import requests
from jwt.algorithms import RSAAlgorithm

try:
    from fastapi.responses import JSONResponse
except ImportError:
    # Fallback for testing without FastAPI
    class JSONResponse:
        def __init__(self, status_code: int, content: dict):
            self.status_code = status_code
            self.content = content
            self.body = json.dumps(content).encode()
            self.headers = {}


@dataclass
class AuthenticationTokens:
    """Container for authentication tokens from Cognito."""
    id_token: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    
    def __init__(self, error_type: str, error_code: str, message: str, 
                 details: str, suggested_action: str):
        """
        Initialize authentication error.
        
        Args:
            error_type: Type of error
            error_code: Specific error code
            message: Error message
            details: Additional error details
            suggested_action: Suggested action to resolve error
        """
        super().__init__(message)
        self.error_type = error_type
        self.error_code = error_code
        self.message = message
        self.details = details
        self.suggested_action = suggested_action


@dataclass
class JWTClaims:
    """Container for JWT token claims."""
    user_id: str
    username: str
    email: str
    client_id: str
    token_use: str
    exp: int
    iat: int
    iss: str
    aud: str


@dataclass
class UserContext:
    """Container for authenticated user context."""
    user_id: str
    username: str
    email: str
    authenticated: bool
    token_claims: JWTClaims
    session_id: Optional[str] = None


class CognitoAuthenticator:
    """
    Cognito authentication service using SRP (Secure Remote Password) protocol.
    
    Handles user authentication, token management, and session validation
    for AWS Cognito User Pools in the restaurant reasoning MCP server.
    """
    
    def __init__(self, user_pool_id: str, client_id: str, region: str):
        """
        Initialize the Cognito authenticator.
        
        Args:
            user_pool_id: AWS Cognito User Pool ID
            client_id: Cognito App Client ID
            region: AWS region
        """
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        
    def authenticate_user(self, username: str, password: str) -> AuthenticationTokens:
        """
        Authenticate user using SRP authentication flow.
        
        Args:
            username: User's username or email
            password: User's password
            
        Returns:
            AuthenticationTokens containing JWT tokens
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Step 1: Initiate SRP authentication
            srp_a, big_a = self._generate_srp_a()
            
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'SRP_A': big_a
                }
            )
            
            if response['ChallengeName'] != 'PASSWORD_VERIFIER':
                raise AuthenticationError(
                    error_type="SRP_CHALLENGE_ERROR",
                    error_code="UNEXPECTED_CHALLENGE",
                    message=f"Unexpected challenge: {response['ChallengeName']}",
                    details=f"Expected PASSWORD_VERIFIER, got {response['ChallengeName']}",
                    suggested_action="Check user status and authentication flow configuration"
                )
            
            # Step 2: Calculate SRP response
            challenge_params = response['ChallengeParameters']
            srp_b = challenge_params['SRP_B']
            salt = challenge_params['SALT']
            secret_block = challenge_params['SECRET_BLOCK']
            
            password_claim = self._calculate_password_claim(
                username, password, srp_a, srp_b, salt, secret_block
            )
            
            # Step 3: Respond to PASSWORD_VERIFIER challenge
            auth_response = self.cognito_client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName='PASSWORD_VERIFIER',
                Session=response['Session'],
                ChallengeResponses={
                    'PASSWORD_CLAIM_SIGNATURE': password_claim['signature'],
                    'PASSWORD_CLAIM_SECRET_BLOCK': secret_block,
                    'TIMESTAMP': password_claim['timestamp'],
                    'USERNAME': username
                }
            )
            
            # Handle potential NEW_PASSWORD_REQUIRED challenge
            if 'ChallengeName' in auth_response and auth_response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
                raise AuthenticationError(
                    error_type="PASSWORD_CHANGE_REQUIRED",
                    error_code="NEW_PASSWORD_REQUIRED",
                    message="User must change password before authentication",
                    details="User is in FORCE_CHANGE_PASSWORD status",
                    suggested_action="Use change_password method or AWS Console to set new password"
                )
            
            # Extract tokens from successful authentication
            auth_result = auth_response['AuthenticationResult']
            
            return AuthenticationTokens(
                id_token=auth_result['IdToken'],
                access_token=auth_result['AccessToken'],
                refresh_token=auth_result['RefreshToken'],
                expires_in=auth_result['ExpiresIn'],
                token_type=auth_result['TokenType']
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError(
                    error_type="AUTHENTICATION_FAILED",
                    error_code=error_code,
                    message="Invalid username or password",
                    details=error_message,
                    suggested_action="Verify credentials and user status"
                )
            elif error_code == 'UserNotFoundException':
                raise AuthenticationError(
                    error_type="USER_NOT_FOUND",
                    error_code=error_code,
                    message="User does not exist",
                    details=error_message,
                    suggested_action="Check username or create user account"
                )
            elif error_code == 'UserNotConfirmedException':
                raise AuthenticationError(
                    error_type="USER_NOT_CONFIRMED",
                    error_code=error_code,
                    message="User account not confirmed",
                    details=error_message,
                    suggested_action="Confirm user account via email or SMS"
                )
            else:
                raise AuthenticationError(
                    error_type="COGNITO_ERROR",
                    error_code=error_code,
                    message=f"Cognito authentication error: {error_message}",
                    details=str(e),
                    suggested_action="Check Cognito configuration and user status"
                )
        except Exception as e:
            raise AuthenticationError(
                error_type="AUTHENTICATION_ERROR",
                error_code="UNKNOWN_ERROR",
                message=f"Authentication failed: {str(e)}",
                details=str(e),
                suggested_action="Check network connectivity and service availability"
            )
    
    def refresh_token(self, refresh_token: str) -> AuthenticationTokens:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            AuthenticationTokens with new access token
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            auth_result = response['AuthenticationResult']
            
            return AuthenticationTokens(
                id_token=auth_result['IdToken'],
                access_token=auth_result['AccessToken'],
                refresh_token=refresh_token,  # Refresh token doesn't change
                expires_in=auth_result['ExpiresIn'],
                token_type=auth_result['TokenType']
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            raise AuthenticationError(
                error_type="TOKEN_REFRESH_FAILED",
                error_code=error_code,
                message=f"Token refresh failed: {error_message}",
                details=str(e),
                suggested_action="Re-authenticate user to obtain new tokens"
            )
    
    def validate_user_session(self, access_token: str) -> UserContext:
        """
        Validate user session using access token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            UserContext with user information
            
        Raises:
            AuthenticationError: If token validation fails
        """
        try:
            response = self.cognito_client.get_user(
                AccessToken=access_token
            )
            
            # Extract user attributes
            user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            # Decode token to get claims (without verification for user context)
            decoded_token = jwt.decode(access_token, options={"verify_signature": False})
            
            jwt_claims = JWTClaims(
                user_id=decoded_token.get('sub', ''),
                username=decoded_token.get('username', ''),
                email=user_attributes.get('email', ''),
                client_id=decoded_token.get('client_id', ''),
                token_use=decoded_token.get('token_use', ''),
                exp=decoded_token.get('exp', 0),
                iat=decoded_token.get('iat', 0),
                iss=decoded_token.get('iss', ''),
                aud=decoded_token.get('aud', '')
            )
            
            return UserContext(
                user_id=jwt_claims.user_id,
                username=jwt_claims.username,
                email=jwt_claims.email,
                authenticated=True,
                token_claims=jwt_claims
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            raise AuthenticationError(
                error_type="SESSION_VALIDATION_FAILED",
                error_code=error_code,
                message=f"Session validation failed: {error_message}",
                details=str(e),
                suggested_action="Re-authenticate to obtain valid access token"
            )
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Get detailed user information using access token.
        
        Args:
            access_token: Valid JWT access token
            
        Returns:
            Dictionary containing user information
            
        Raises:
            AuthenticationError: If user info retrieval fails
        """
        try:
            response = self.cognito_client.get_user(
                AccessToken=access_token
            )
            
            user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            return {
                'username': response['Username'],
                'user_attributes': user_attributes,
                'user_mfa_settings': response.get('UserMFASettingList', []),
                'preferred_mfa_setting': response.get('PreferredMfaSetting', None)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            raise AuthenticationError(
                error_type="USER_INFO_RETRIEVAL_FAILED",
                error_code=error_code,
                message=f"User info retrieval failed: {error_message}",
                details=str(e),
                suggested_action="Verify access token validity"
            )
    
    def _generate_srp_a(self) -> Tuple[int, str]:
        """
        Generate SRP 'a' value and corresponding 'A' value.
        
        Returns:
            Tuple of (a, A) where a is private and A is public
        """
        # SRP-6a parameters for Cognito
        N = int(
            "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
            "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
            "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
            "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
            "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
            "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
            "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
            "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
            "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
            "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
            "15728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64"
            "ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7"
            "ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6B"
            "F12FFA06D98A0864D87602733EC86A64521F2B18177B200C"
            "BBE117577A615D6C770988C0BAD946E208E24FA074E5AB31"
            "43DB5BFCE0FD108E4B82D120A93AD2CAFFFFFFFFFFFFFFFF", 16
        )
        g = 2
        
        # Generate random 'a' value
        a = secrets.randbits(1024)
        
        # Calculate A = g^a mod N
        big_a = pow(g, a, N)
        
        return a, hex(big_a)[2:].upper()
    
    def _calculate_password_claim(self, username: str, password: str, 
                                 srp_a: int, srp_b: str, salt: str, 
                                 secret_block: str) -> Dict[str, str]:
        """
        Calculate SRP password claim signature.
        
        Args:
            username: User's username
            password: User's password
            srp_a: Private SRP 'a' value
            srp_b: Public SRP 'B' value from server
            salt: Salt value from server
            secret_block: Secret block from server
            
        Returns:
            Dictionary with signature and timestamp
        """
        # SRP-6a parameters
        N = int(
            "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
            "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
            "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
            "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
            "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
            "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
            "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
            "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
            "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
            "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
            "15728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64"
            "ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7"
            "ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6B"
            "F12FFA06D98A0864D87602733EC86A64521F2B18177B200C"
            "BBE117577A615D6C770988C0BAD946E208E24FA074E5AB31"
            "43DB5BFCE0FD108E4B82D120A93AD2CAFFFFFFFFFFFFFFFF", 16
        )
        g = 2
        k = int(hashlib.sha256(f"{N:x}{g:x}".encode()).hexdigest(), 16)
        
        # Convert hex strings to integers
        big_b = int(srp_b, 16)
        salt_int = int(salt, 16)
        
        # Calculate u = H(A | B)
        big_a = pow(g, srp_a, N)
        u_hash = hashlib.sha256(f"{big_a:x}{big_b:x}".encode()).hexdigest()
        u = int(u_hash, 16)
        
        # Calculate x = H(salt | H(username | ":" | password))
        username_password = f"{username}:{password}"
        username_password_hash = hashlib.sha256(username_password.encode()).hexdigest()
        x_hash = hashlib.sha256(f"{salt_int:x}{username_password_hash}".encode()).hexdigest()
        x = int(x_hash, 16)
        
        # Calculate S = (B - k * g^x)^(a + u * x) mod N
        s = pow(big_b - k * pow(g, x, N), srp_a + u * x, N)
        
        # Calculate K = H(S)
        k_hash = hashlib.sha256(f"{s:x}".encode()).hexdigest()
        
        # Create timestamp
        timestamp = datetime.now(timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y')
        
        # Calculate signature
        message = f"{self.user_pool_id}{username}{secret_block}{timestamp}"
        signature = base64.b64encode(
            hmac.new(k_hash.encode(), message.encode(), hashlib.sha256).digest()
        ).decode()
        
        return {
            'signature': signature,
            'timestamp': timestamp
        }


class TokenValidator:
    """
    JWT token validator for Cognito tokens with JWKS key management.
    
    Handles token signature verification, claims validation, and JWKS key caching
    for the restaurant reasoning MCP server.
    """
    
    def __init__(self, cognito_config: Dict):
        """
        Initialize the token validator.
        
        Args:
            cognito_config: Dictionary containing Cognito configuration
        """
        self.user_pool_id = cognito_config['user_pool_id']
        self.client_id = cognito_config['client_id']
        self.region = cognito_config['region']
        self.discovery_url = cognito_config['discovery_url']
        
        # JWKS configuration
        self.jwks_cache = {}
        self.jwks_cache_expiry = None
        self.jwks_cache_ttl = 3600  # 1 hour
        
        # Derive JWKS URL from discovery URL
        self.jwks_url = self.discovery_url.replace('/.well-known/openid-configuration', '/.well-known/jwks.json')
        self.issuer_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
    
    async def validate_jwt_token(self, token: str) -> JWTClaims:
        """
        Validate JWT token signature and claims.
        
        Args:
            token: JWT token string
            
        Returns:
            JWTClaims object with validated claims
            
        Raises:
            AuthenticationError: If token validation fails
        """
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                raise AuthenticationError(
                    error_type="TOKEN_VALIDATION_ERROR",
                    error_code="MISSING_KEY_ID",
                    message="Token header missing key ID (kid)",
                    details="JWT token header must contain 'kid' field",
                    suggested_action="Verify token format and Cognito configuration"
                )
            
            # Get signing key
            signing_key = await self.get_signing_key(kid)
            
            # Verify token signature and decode claims
            decoded_token = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.issuer_url,
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': True,
                    'verify_iss': True
                }
            )
            
            # Extract and validate claims
            claims = JWTClaims(
                user_id=decoded_token.get('sub', ''),
                username=decoded_token.get('username', ''),
                email=decoded_token.get('email', ''),
                client_id=decoded_token.get('client_id', ''),
                token_use=decoded_token.get('token_use', ''),
                exp=decoded_token.get('exp', 0),
                iat=decoded_token.get('iat', 0),
                iss=decoded_token.get('iss', ''),
                aud=decoded_token.get('aud', '')
            )
            
            # Validate token use
            if claims.token_use not in ['access', 'id']:
                raise AuthenticationError(
                    error_type="TOKEN_VALIDATION_ERROR",
                    error_code="INVALID_TOKEN_USE",
                    message=f"Invalid token use: {claims.token_use}",
                    details="Token must be either 'access' or 'id' token",
                    suggested_action="Use appropriate token type for authentication"
                )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError(
                error_type="TOKEN_EXPIRED",
                error_code="EXPIRED_SIGNATURE",
                message="JWT token has expired",
                details="Token expiration time (exp) has passed",
                suggested_action="Refresh token or re-authenticate"
            )
        except jwt.InvalidAudienceError:
            raise AuthenticationError(
                error_type="TOKEN_VALIDATION_ERROR",
                error_code="INVALID_AUDIENCE",
                message="JWT token audience mismatch",
                details=f"Expected audience: {self.client_id}",
                suggested_action="Verify token was issued for correct client"
            )
        except jwt.InvalidIssuerError:
            raise AuthenticationError(
                error_type="TOKEN_VALIDATION_ERROR",
                error_code="INVALID_ISSUER",
                message="JWT token issuer mismatch",
                details=f"Expected issuer: {self.issuer_url}",
                suggested_action="Verify token was issued by correct Cognito User Pool"
            )
        except jwt.InvalidSignatureError:
            raise AuthenticationError(
                error_type="TOKEN_VALIDATION_ERROR",
                error_code="INVALID_SIGNATURE",
                message="JWT token signature verification failed",
                details="Token signature does not match expected value",
                suggested_action="Verify token integrity and JWKS configuration"
            )
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(
                error_type="TOKEN_VALIDATION_ERROR",
                error_code="INVALID_TOKEN",
                message=f"JWT token validation failed: {str(e)}",
                details=str(e),
                suggested_action="Verify token format and content"
            )
        except Exception as e:
            raise AuthenticationError(
                error_type="TOKEN_VALIDATION_ERROR",
                error_code="VALIDATION_ERROR",
                message=f"Token validation error: {str(e)}",
                details=str(e),
                suggested_action="Check network connectivity and service availability"
            )
    
    async def get_signing_key(self, kid: str) -> str:
        """
        Get signing key for token verification.
        
        Args:
            kid: Key ID from token header
            
        Returns:
            RSA public key for signature verification
            
        Raises:
            AuthenticationError: If key retrieval fails
        """
        try:
            # Check cache first
            if self._is_cache_valid() and kid in self.jwks_cache:
                return self.jwks_cache[kid]
            
            # Fetch JWKS from Cognito
            await self._refresh_jwks_cache()
            
            if kid not in self.jwks_cache:
                raise AuthenticationError(
                    error_type="KEY_NOT_FOUND",
                    error_code="SIGNING_KEY_NOT_FOUND",
                    message=f"Signing key not found for kid: {kid}",
                    details="Key ID not present in JWKS",
                    suggested_action="Verify token validity and JWKS endpoint"
                )
            
            return self.jwks_cache[kid]
            
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(
                error_type="KEY_RETRIEVAL_ERROR",
                error_code="JWKS_ERROR",
                message=f"Failed to retrieve signing key: {str(e)}",
                details=str(e),
                suggested_action="Check network connectivity and JWKS endpoint"
            )
    
    def extract_claims(self, token: str) -> Dict:
        """
        Extract claims from JWT token without verification.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary containing token claims
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            raise AuthenticationError(
                error_type="TOKEN_DECODE_ERROR",
                error_code="DECODE_ERROR",
                message=f"Failed to decode token: {str(e)}",
                details=str(e),
                suggested_action="Verify token format"
            )
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without full validation.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired, False otherwise
        """
        try:
            claims = self.extract_claims(token)
            exp = claims.get('exp', 0)
            current_time = datetime.now(timezone.utc).timestamp()
            return current_time >= exp
        except Exception:
            return True  # Assume expired if we can't decode
    
    async def _refresh_jwks_cache(self) -> None:
        """Refresh JWKS cache from Cognito endpoint."""
        try:
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            
            jwks_data = response.json()
            
            # Process keys and cache them
            self.jwks_cache = {}
            for key_data in jwks_data.get('keys', []):
                kid = key_data.get('kid')
                if kid and key_data.get('kty') == 'RSA':
                    # Convert JWK to PEM format
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))
                    self.jwks_cache[kid] = public_key
            
            # Update cache expiry
            self.jwks_cache_expiry = datetime.now(timezone.utc).timestamp() + self.jwks_cache_ttl
            
        except requests.RequestException as e:
            raise AuthenticationError(
                error_type="JWKS_FETCH_ERROR",
                error_code="NETWORK_ERROR",
                message=f"Failed to fetch JWKS: {str(e)}",
                details=str(e),
                suggested_action="Check network connectivity and JWKS URL"
            )
        except Exception as e:
            raise AuthenticationError(
                error_type="JWKS_PROCESSING_ERROR",
                error_code="PROCESSING_ERROR",
                message=f"Failed to process JWKS: {str(e)}",
                details=str(e),
                suggested_action="Verify JWKS format and content"
            )
    
    def _is_cache_valid(self) -> bool:
        """Check if JWKS cache is still valid."""
        if self.jwks_cache_expiry is None:
            return False
        
        current_time = datetime.now(timezone.utc).timestamp()
        return current_time < self.jwks_cache_expiry


class JWKSManager:
    """
    JWKS (JSON Web Key Set) manager for handling Cognito public keys.
    
    Manages key fetching, caching, and rotation for JWT token validation
    in the restaurant reasoning MCP server.
    """
    
    def __init__(self, discovery_url: str, cache_ttl: int = 3600):
        """
        Initialize JWKS manager.
        
        Args:
            discovery_url: Cognito discovery URL
            cache_ttl: Cache time-to-live in seconds
        """
        self.discovery_url = discovery_url
        self.cache_ttl = cache_ttl
        self.jwks_url = discovery_url.replace('/.well-known/openid-configuration', '/.well-known/jwks.json')
        
        # Key cache
        self.keys_cache = {}
        self.cache_expiry = None
    
    async def get_key(self, kid: str) -> str:
        """
        Get public key by key ID.
        
        Args:
            kid: Key ID
            
        Returns:
            RSA public key
            
        Raises:
            AuthenticationError: If key not found or fetch fails
        """
        # Check cache first
        if self._is_cache_valid() and kid in self.keys_cache:
            return self.keys_cache[kid]
        
        # Refresh cache
        await self._refresh_cache()
        
        if kid not in self.keys_cache:
            raise AuthenticationError(
                error_type="KEY_NOT_FOUND",
                error_code="JWKS_KEY_NOT_FOUND",
                message=f"Key ID {kid} not found in JWKS",
                details="The requested key ID is not available in the key set",
                suggested_action="Verify token validity and key rotation"
            )
        
        return self.keys_cache[kid]
    
    async def _refresh_cache(self) -> None:
        """Refresh JWKS cache from endpoint."""
        try:
            response = requests.get(self.jwks_url, timeout=10)
            response.raise_for_status()
            
            jwks_data = response.json()
            
            # Process and cache keys
            self.keys_cache = {}
            for key_data in jwks_data.get('keys', []):
                kid = key_data.get('kid')
                if kid and key_data.get('kty') == 'RSA':
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))
                    self.keys_cache[kid] = public_key
            
            # Update cache expiry
            self.cache_expiry = datetime.now(timezone.utc).timestamp() + self.cache_ttl
            
        except Exception as e:
            raise AuthenticationError(
                error_type="JWKS_FETCH_ERROR",
                error_code="CACHE_REFRESH_FAILED",
                message=f"Failed to refresh JWKS cache: {str(e)}",
                details=str(e),
                suggested_action="Check network connectivity and JWKS endpoint"
            )
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self.cache_expiry is None:
            return False
        
        current_time = datetime.now(timezone.utc).timestamp()
        return current_time < self.cache_expiry


# Export main classes
__all__ = [
    'CognitoAuthenticator',
    'TokenValidator',
    'JWKSManager',
    'AuthenticationTokens',
    'AuthenticationError',
    'JWTClaims',
    'UserContext'
]