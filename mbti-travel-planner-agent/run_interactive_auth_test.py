#!/usr/bin/env python3
"""
Interactive Authentication Test Runner for MBTI Travel Planner Agent
This script demonstrates the interactive Cognito authentication with default username
and password prompt, then runs a simplified workflow test using the JWT token.
"""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the interactive authentication service
from services.interactive_auth_service import InteractiveAuthService, AuthenticationTestHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InteractiveAuthTestRunner:
    """Test runner that demonstrates interactive Cognito authentication."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.interactive_auth = InteractiveAuthService()
        self.test_results = {}
        self.start_time = time.time()
        
        logger.info("Interactive Authentication Test Runner initialized")
        logger.info(f"Default test user: {self.interactive_auth.default_username}")
    
    async def run_authentication_demo(self):
        """Run the interactive authentication demonstration."""
        print("\n" + "=" * 80)
        print("INTERACTIVE COGNITO AUTHENTICATION DEMONSTRATION")
        print("=" * 80)
        
        try:
            # Step 1: Test authentication helper
            print("\n🔧 Testing Authentication System Components...")
            auth_helper = AuthenticationTestHelper(self.interactive_auth)
            test_results = await auth_helper.test_authentication_flow()
            
            # Print test report
            print("\n" + auth_helper.generate_test_report(test_results))
            
            # Step 2: Demonstrate JWT token usage
            if self.interactive_auth.is_authenticated():
                await self.demonstrate_jwt_usage()
            
            # Step 3: Show user information
            await self.show_user_information()
            
            return True
            
        except Exception as e:
            logger.error(f"Authentication demo failed: {e}")
            return False
    
    async def demonstrate_jwt_usage(self):
        """Demonstrate how to use the JWT token for API calls."""
        print("\n" + "=" * 60)
        print("JWT TOKEN USAGE DEMONSTRATION")
        print("=" * 60)
        
        try:
            # Get current JWT token
            jwt_token = await self.interactive_auth.get_jwt_token()
            
            # Show token information (safely)
            token_parts = jwt_token.split('.')
            print(f"✅ JWT Token obtained successfully")
            print(f"📊 Token structure: {len(token_parts)} parts (header.payload.signature)")
            print(f"🔑 Token length: {len(jwt_token)} characters")
            print(f"🕒 Token expires: {self.interactive_auth.token_expiry}")
            
            # Show authentication headers
            headers = self.interactive_auth.get_authentication_headers()
            print(f"\n📋 Authentication Headers:")
            for key, value in headers.items():
                if key == 'Authorization':
                    # Show only the Bearer prefix for security
                    print(f"  {key}: Bearer [JWT_TOKEN_HIDDEN]")
                else:
                    print(f"  {key}: {value}")
            
            # Demonstrate token refresh capability
            if self.interactive_auth.refresh_token:
                print(f"\n🔄 Refresh token available: Yes")
                print(f"💡 Token can be automatically refreshed when needed")
            else:
                print(f"\n🔄 Refresh token available: No")
                print(f"⚠️  Will need to re-authenticate when token expires")
            
        except Exception as e:
            logger.error(f"JWT demonstration failed: {e}")
    
    async def show_user_information(self):
        """Show current user authentication information."""
        print("\n" + "=" * 60)
        print("USER AUTHENTICATION INFORMATION")
        print("=" * 60)
        
        user_info = self.interactive_auth.get_user_info()
        
        print(f"👤 Username: {user_info['username']}")
        print(f"🔐 Authenticated: {user_info['authenticated']}")
        print(f"🕒 Token Expiry: {user_info['token_expiry']}")
        print(f"🔄 Has Refresh Token: {user_info['has_refresh_token']}")
        
        # Show authentication status
        if self.interactive_auth.is_authenticated():
            print(f"✅ Authentication Status: ACTIVE")
            
            # Calculate time until expiry
            if self.interactive_auth.token_expiry:
                time_until_expiry = self.interactive_auth.token_expiry - datetime.utcnow()
                minutes_left = int(time_until_expiry.total_seconds() / 60)
                print(f"⏰ Time until token expires: {minutes_left} minutes")
        else:
            print(f"❌ Authentication Status: EXPIRED/INVALID")
    
    async def simulate_api_workflow(self):
        """Simulate a simple API workflow using the JWT token."""
        print("\n" + "=" * 60)
        print("SIMULATED API WORKFLOW")
        print("=" * 60)
        
        if not self.interactive_auth.is_authenticated():
            print("❌ Cannot simulate workflow: Not authenticated")
            return
        
        try:
            # Simulate multiple API calls
            api_calls = [
                "Restaurant Search - Central District",
                "Restaurant Search - Tsim Sha Tsui", 
                "Restaurant Search - Causeway Bay",
                "Restaurant Reasoning - Sentiment Analysis",
                "Restaurant Reasoning - MBTI Matching"
            ]
            
            print(f"🚀 Simulating {len(api_calls)} API calls...")
            
            for i, call_name in enumerate(api_calls, 1):
                print(f"\n📡 API Call {i}: {call_name}")
                
                # Get fresh JWT token (handles refresh automatically)
                jwt_token = await self.interactive_auth.get_jwt_token()
                
                # Simulate API call delay
                await asyncio.sleep(0.5)
                
                # Show success
                print(f"   ✅ Success - JWT token valid and used")
                print(f"   🔑 Token length: {len(jwt_token)} chars")
            
            print(f"\n🎉 All {len(api_calls)} API calls completed successfully!")
            
        except Exception as e:
            logger.error(f"API workflow simulation failed: {e}")
    
    async def cleanup(self):
        """Clean up authentication and show summary."""
        print("\n" + "=" * 60)
        print("CLEANUP AND SUMMARY")
        print("=" * 60)
        
        # Show session summary
        total_time = time.time() - self.start_time
        print(f"📊 Total session time: {total_time:.2f} seconds")
        
        if self.interactive_auth.is_authenticated():
            print(f"👤 Authenticated user: {self.interactive_auth.username}")
            print(f"🔐 Authentication successful: Yes")
        else:
            print(f"🔐 Authentication successful: No")
        
        # Logout and cleanup
        print(f"\n🔓 Logging out and cleaning up...")
        await self.interactive_auth.logout()
        print(f"✅ Cleanup completed")


async def main():
    """Main function to run the interactive authentication demonstration."""
    print("🚀 MBTI Travel Planner Agent - Interactive Authentication Demo")
    print("=" * 80)
    print("This demo shows how to use interactive Cognito authentication")
    print("with the default test user and password prompts.")
    print("=" * 80)
    
    runner = InteractiveAuthTestRunner()
    
    try:
        # Run authentication demo
        auth_success = await runner.run_authentication_demo()
        
        if auth_success:
            # Run simulated workflow
            await runner.simulate_api_workflow()
        
        # Cleanup
        await runner.cleanup()
        
        # Final status
        if auth_success:
            print("\n🎉 Interactive authentication demo completed successfully!")
            return 0
        else:
            print("\n❌ Interactive authentication demo failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        await runner.cleanup()
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        await runner.cleanup()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)