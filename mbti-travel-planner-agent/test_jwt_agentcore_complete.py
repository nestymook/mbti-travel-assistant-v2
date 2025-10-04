#!/usr/bin/env python3
"""
Complete JWT Authentication Test for AgentCore

This script demonstrates the complete JWT authentication flow with AgentCore:
1. Prompts for password (secure)
2. Generates Cognito access token
3. Tests AgentCore invocation with JWT
4. Validates the complete end-to-end flow

Based on the successful JWT authentication implementation.
"""

import json
import getpass
import boto3
import subprocess
import sys
import base64
from datetime import datetime, timezone
from pathlib import Path
from botocore.exceptions import ClientError


class AgentCoreJWTTester:
    """Complete JWT authentication tester for AgentCore."""
    
    def __init__(self):
        """Initialize the tester."""
        self.config = None
        self.cognito_client = None
        self.access_token = None
        
    def load_configuration(self):
        """Load Cognito configuration."""
        try:
            config_file = Path("cognito_config.json")
            if not config_file.exists():
                print("❌ cognito_config.json not found")
                return False
            
            with open(config_file) as f:
                self.config = json.load(f)
            
            print("✅ Configuration loaded successfully")
            print(f"   User Pool ID: {self.config['user_pool']['user_pool_id']}")
            print(f"   Client ID: {self.config['app_client']['client_id']}")
            print(f"   Region: {self.config['region']}")
            
            # Initialize Cognito client
            self.cognito_client = boto3.client(
                'cognito-idp', 
                region_name=self.config['region']
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            return False
    
    def prompt_for_credentials(self):
        """Prompt user for credentials securely."""
        print(f"\n🔐 Authentication Required")
        print("=" * 40)
        
        # Prompt for username
        default_username = "test@mbti-travel.com"
        username = input(f"Username (default: {default_username}): ").strip()
        if not username:
            username = default_username
        
        # Prompt for password securely
        password = getpass.getpass(f"Password for {username}: ")
        
        if not password:
            print("❌ Password cannot be empty")
            return None, None
        
        return username, password
    
    def authenticate_with_cognito(self, username, password):
        """Authenticate with Cognito and get access token."""
        try:
            print(f"\n🔐 Authenticating with Cognito...")
            
            # Use admin authentication for reliable token generation
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.config['user_pool']['user_pool_id'],
                ClientId=self.config['app_client']['client_id'],
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            if 'AuthenticationResult' not in response:
                print("❌ Authentication failed - no tokens returned")
                return False
            
            tokens = response['AuthenticationResult']
            self.access_token = tokens['AccessToken']
            id_token = tokens.get('IdToken')
            
            print("✅ Authentication successful!")
            print(f"   Access token length: {len(self.access_token)}")
            if id_token:
                print(f"   ID token length: {len(id_token)}")
            
            # Save tokens for CLI usage
            with open("access_token.txt", "w") as f:
                f.write(self.access_token)
            
            with open("fresh_jwt.txt", "w") as f:
                f.write(self.access_token)
            
            print("✅ Tokens saved to access_token.txt and fresh_jwt.txt")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            print(f"❌ Cognito authentication failed: {error_code}")
            print(f"   Error: {error_message}")
            
            if error_code == 'NotAuthorizedException':
                print("\n💡 Possible solutions:")
                print("   - Check username and password")
                print("   - Verify user exists in Cognito User Pool")
                print("   - Ensure user account is confirmed")
            elif error_code == 'InvalidParameterException':
                print("\n💡 Possible solutions:")
                print("   - Check if ADMIN_USER_PASSWORD_AUTH is enabled")
                print("   - Verify app client configuration")
            
            return False
            
        except Exception as e:
            print(f"❌ Unexpected authentication error: {e}")
            return False
    
    def analyze_access_token(self):
        """Analyze the access token structure."""
        if not self.access_token:
            return False
        
        try:
            print(f"\n🔍 Analyzing Access Token...")
            
            # Decode JWT payload (without verification)
            parts = self.access_token.split('.')
            if len(parts) != 3:
                print("❌ Invalid JWT format")
                return False
            
            # Decode payload
            payload_part = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_part) % 4
            if padding != 4:
                payload_part += '=' * padding
            
            payload = json.loads(base64.urlsafe_b64decode(payload_part))
            
            print("✅ Token analysis:")
            print(f"   Token use: {payload.get('token_use', 'MISSING')}")
            print(f"   Client ID: {payload.get('client_id', 'MISSING')}")
            print(f"   Subject: {payload.get('sub', 'MISSING')}")
            print(f"   Issuer: {payload.get('iss', 'MISSING')}")
            print(f"   Audience: {payload.get('aud', 'MISSING (OK for AgentCore)')}")
            print(f"   Scope: {payload.get('scope', 'MISSING')}")
            
            # Check expiration
            if 'exp' in payload:
                exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
                current_time = datetime.now(timezone.utc)
                
                if current_time < exp_time:
                    time_left = exp_time - current_time
                    print(f"   Expires: {exp_time} (in {time_left})")
                    print("✅ Token is valid and not expired")
                else:
                    print(f"   Expires: {exp_time} (EXPIRED)")
                    print("❌ Token is expired")
                    return False
            
            # Validate for AgentCore
            if payload.get('token_use') != 'access':
                print("⚠️  Warning: Not an access token (should be 'access' for AgentCore)")
            
            if not payload.get('client_id'):
                print("❌ Missing client_id claim (required for AgentCore)")
                return False
            
            print("✅ Token is suitable for AgentCore authentication")
            return True
            
        except Exception as e:
            print(f"❌ Error analyzing token: {e}")
            return False
    
    def test_agentcore_invocation(self):
        """Test AgentCore invocation with JWT token."""
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            print(f"\n🚀 Testing AgentCore Invocation...")
            
            # Prepare test payload
            test_payload = {
                "prompt": "Hello! This is a JWT authentication test. Please respond briefly."
            }
            
            # Use AgentCore CLI with bearer token
            cmd = [
                "agentcore", "invoke",
                "--bearer-token", self.access_token,
                json.dumps(test_payload)
            ]
            
            print(f"   Command: agentcore invoke --bearer-token [TOKEN] '{json.dumps(test_payload)}'")
            print(f"   Executing...")
            
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                print("✅ AgentCore invocation successful!")
                
                # Parse and display response
                try:
                    # The output might contain extra info, look for the JSON response
                    output_lines = result.stdout.strip().split('\n')
                    
                    # Find the response JSON (usually the last line or contains "result")
                    response_json = None
                    for line in reversed(output_lines):
                        if line.strip().startswith('{') and '"result"' in line:
                            response_json = line.strip()
                            break
                    
                    if response_json:
                        response = json.loads(response_json)
                        agent_response = response.get('result', {})
                        
                        if isinstance(agent_response, dict) and 'content' in agent_response:
                            # Nova Pro format
                            content = agent_response['content']
                            if isinstance(content, list) and len(content) > 0:
                                text_content = content[0].get('text', 'No text content')
                                print(f"   Agent Response: {text_content[:200]}...")
                            else:
                                print(f"   Agent Response: {content}")
                        else:
                            print(f"   Agent Response: {str(agent_response)[:200]}...")
                    else:
                        print(f"   Raw Output: {result.stdout[:300]}...")
                    
                except json.JSONDecodeError:
                    print(f"   Raw Output: {result.stdout[:300]}...")
                
                return True
            else:
                print(f"❌ AgentCore invocation failed (exit code: {result.returncode})")
                print(f"   Error: {result.stderr}")
                
                # Analyze common errors
                if "403" in result.stderr:
                    print("\n💡 403 Forbidden - Possible issues:")
                    print("   - JWT token validation failed")
                    print("   - Check AgentCore JWT configuration")
                    print("   - Verify allowedClients in .bedrock_agentcore.yaml")
                elif "424" in result.stderr:
                    print("\n💡 424 Failed Dependency - Possible issues:")
                    print("   - Model access issue (check Bedrock model permissions)")
                    print("   - AgentCore runtime dependency failure")
                elif "401" in result.stderr:
                    print("\n💡 401 Unauthorized - Possible issues:")
                    print("   - Token expired or invalid")
                    print("   - Authentication configuration mismatch")
                
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ AgentCore invocation timed out (60s)")
            return False
        except Exception as e:
            print(f"❌ Error testing AgentCore invocation: {e}")
            return False
    
    def check_agentcore_status(self):
        """Check AgentCore deployment status."""
        try:
            print(f"\n📊 Checking AgentCore Status...")
            
            result = subprocess.run(
                ["agentcore", "status"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ AgentCore status check successful")
                
                # Extract key information
                output = result.stdout
                if "Ready - Agent deployed and endpoint available" in output:
                    print("✅ Agent is deployed and ready")
                elif "READY" in output:
                    print("✅ Agent endpoint is ready")
                else:
                    print("⚠️  Agent status unclear")
                
                # Look for memory status
                if "Memory is active" in output or "STM" in output:
                    print("✅ Memory management is active")
                
                return True
            else:
                print(f"❌ AgentCore status check failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking AgentCore status: {e}")
            return False
    
    def run_complete_test(self):
        """Run the complete JWT authentication test."""
        print("🧪 AgentCore JWT Authentication - Complete Test")
        print("=" * 55)
        print("This test validates the complete JWT authentication flow:")
        print("1. Load Cognito configuration")
        print("2. Prompt for credentials securely")
        print("3. Authenticate with Cognito")
        print("4. Generate access token")
        print("5. Analyze token structure")
        print("6. Test AgentCore invocation")
        print()
        
        # Step 1: Load configuration
        if not self.load_configuration():
            return False
        
        # Step 2: Prompt for credentials
        username, password = self.prompt_for_credentials()
        if not username or not password:
            return False
        
        # Step 3: Authenticate with Cognito
        if not self.authenticate_with_cognito(username, password):
            return False
        
        # Step 4: Analyze token
        if not self.analyze_access_token():
            return False
        
        # Step 5: Test AgentCore invocation
        if not self.test_agentcore_invocation():
            return False
        
        print(f"\n🎉 Complete JWT Authentication Test PASSED!")
        print("=" * 45)
        print("✅ All components working correctly:")
        print("   - Cognito authentication")
        print("   - JWT token generation")
        print("   - AgentCore JWT validation")
        print("   - End-to-end agent invocation")
        print()
        print("💡 Your AgentCore JWT authentication is production-ready!")
        
        return True


def main():
    """Main function."""
    tester = AgentCoreJWTTester()
    
    try:
        success = tester.run_complete_test()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())