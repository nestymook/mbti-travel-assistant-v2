#!/usr/bin/env python3
"""
Validation Script for Interactive Authentication Service
This script validates that the interactive authentication system is properly configured
and working correctly before running the comprehensive tests.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the interactive authentication service
from services.interactive_auth_service import InteractiveAuthService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthenticationValidator:
    """Validator for the interactive authentication system."""
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_results = {}
        
    def validate_config_file(self) -> bool:
        """Validate that the Cognito configuration file exists and is valid."""
        try:
            config_path = "config/cognito_config.json"
            
            if not os.path.exists(config_path):
                logger.error(f"❌ Configuration file not found: {config_path}")
                return False
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            required_fields = ['user_pool_id', 'client_id', 'region']
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                logger.error(f"❌ Missing required configuration fields: {missing_fields}")
                return False
            
            logger.info("✅ Configuration file validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            return False
    
    def validate_service_initialization(self) -> bool:
        """Validate that the interactive authentication service can be initialized."""
        try:
            auth_service = InteractiveAuthService()
            
            # Test configuration loading
            config = auth_service.load_cognito_config()
            if not config:
                logger.error("❌ Failed to load Cognito configuration")
                return False
            
            # Test Cognito client initialization
            auth_service.initialize_cognito_client()
            if not auth_service.cognito_client:
                logger.error("❌ Failed to initialize Cognito client")
                return False
            
            logger.info("✅ Service initialization validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service initialization validation failed: {e}")
            return False
    
    async def validate_authentication_flow(self) -> bool:
        """Validate the authentication flow (requires user interaction)."""
        try:
            print("\n" + "=" * 60)
            print("AUTHENTICATION FLOW VALIDATION")
            print("=" * 60)
            print("This will test the complete authentication flow.")
            print("You will be prompted for Cognito credentials.")
            
            # Ask user if they want to proceed
            proceed = input("\nProceed with authentication test? (y/N): ").strip().lower()
            if proceed != 'y':
                logger.info("⚠️  Authentication flow validation skipped by user")
                return True  # Not a failure, just skipped
            
            auth_service = InteractiveAuthService()
            
            # Test authentication
            auth_info = await auth_service.authenticate_user()
            if not auth_info or not auth_info.get('jwt_token'):
                logger.error("❌ Authentication failed - no JWT token received")
                return False
            
            # Test JWT token validation
            jwt_token = auth_info['jwt_token']
            if not auth_service.validate_token_format(jwt_token):
                logger.error("❌ JWT token format validation failed")
                return False
            
            # Test token refresh capability
            if auth_service.refresh_token:
                try:
                    refreshed_token = await auth_service.refresh_jwt_token()
                    if not refreshed_token:
                        logger.warning("⚠️  Token refresh test failed")
                except Exception as e:
                    logger.warning(f"⚠️  Token refresh test failed: {e}")
            
            # Test authentication headers
            headers = auth_service.get_authentication_headers()
            if 'Authorization' not in headers or 'Bearer' not in headers['Authorization']:
                logger.error("❌ Authentication headers validation failed")
                return False
            
            # Test user info
            user_info = auth_service.get_user_info()
            if not user_info.get('username') or not user_info.get('authenticated'):
                logger.error("❌ User info validation failed")
                return False
            
            # Cleanup
            await auth_service.logout()
            
            logger.info("✅ Authentication flow validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authentication flow validation failed: {e}")
            return False
    
    def validate_dependencies(self) -> bool:
        """Validate that all required dependencies are available."""
        try:
            # Test required imports
            import boto3
            import getpass
            from botocore.exceptions import ClientError, NoCredentialsError
            
            # Test AWS credentials
            try:
                session = boto3.Session()
                credentials = session.get_credentials()
                if not credentials:
                    logger.error("❌ AWS credentials not configured")
                    return False
            except Exception as e:
                logger.error(f"❌ AWS credentials validation failed: {e}")
                return False
            
            logger.info("✅ Dependencies validation passed")
            return True
            
        except ImportError as e:
            logger.error(f"❌ Missing required dependency: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Dependencies validation failed: {e}")
            return False
    
    async def run_validation(self) -> dict:
        """Run all validation checks."""
        print("🔍 INTERACTIVE AUTHENTICATION SYSTEM VALIDATION")
        print("=" * 60)
        
        validations = {
            'config_file': self.validate_config_file(),
            'dependencies': self.validate_dependencies(),
            'service_initialization': self.validate_service_initialization(),
            'authentication_flow': await self.validate_authentication_flow()
        }
        
        # Summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for validation_name, result in validations.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {validation_name.replace('_', ' ').title()}")
            if not result:
                all_passed = False
        
        print(f"\n{'✅ ALL VALIDATIONS PASSED' if all_passed else '❌ SOME VALIDATIONS FAILED'}")
        
        if all_passed:
            print("\n🎉 Interactive authentication system is ready for use!")
            print("You can now run:")
            print("  • python run_interactive_auth_test.py")
            print("  • python test_three_day_workflow_comprehensive.py")
        else:
            print("\n⚠️  Please fix the failed validations before proceeding.")
        
        return {
            'all_passed': all_passed,
            'validations': validations,
            'timestamp': datetime.utcnow().isoformat()
        }


async def main():
    """Main validation function."""
    validator = AuthenticationValidator()
    
    try:
        results = await validator.run_validation()
        return 0 if results['all_passed'] else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)