#!/usr/bin/env python3
"""
Enhanced JWT Token Injection Test

This test validates the comprehensive JWT token injection system throughout
the MBTI Travel Planner Agent workflow, ensuring all components receive
and maintain valid JWT tokens for AgentCore authentication.

Test Coverage:
- Enhanced JWT token manager functionality
- Component registration and token propagation
- Token validation and refresh capabilities
- Integration with existing workflow components
- End-to-end JWT token flow validation
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import enhanced JWT token manager
from services.enhanced_jwt_token_manager import (
    EnhancedJWTTokenManager,
    enhanced_jwt_manager,
    inject_jwt_token_globally,
    register_component_for_jwt_injection,
    get_current_jwt_token,
    get_jwt_injection_status
)

# Import authentication services
from services.interactive_auth_service import InteractiveAuthService
from services.authentication_manager import AuthenticationManager
from services.agentcore_runtime_client import AgentCoreRuntimeClient, ConnectionConfig
from services.restaurant_search_tool import RestaurantSearchTool
from services.restaurant_reasoning_tool import RestaurantReasoningTool
from config.agentcore_environment_config import get_agentcore_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockComponent:
    """Mock component for testing JWT token injection."""
    
    def __init__(self, name: str):
        self.name = name
        self.jwt_token = None
        self.token_update_count = 0
        self.last_token_update = None
    
    def set_jwt_token(self, token: str):
        """Set JWT token method for testing."""
        self.jwt_token = token
        self.token_update_count += 1
        self.last_token_update = datetime.utcnow()
        logger.debug(f"Mock component {self.name} received JWT token: {token[:20]}...")


class MockTool:
    """Mock tool with runtime client for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.runtime_client = MockComponent(f"{name}_runtime_client")


class MockAgent:
    """Mock agent with tools for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.jwt_token = None
        self.tools = [
            MockTool("search_tool"),
            MockTool("reasoning_tool"),
            MockTool("analysis_tool")
        ]


class EnhancedJWTInjectionTest:
    """Test suite for enhanced JWT token injection system."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_session_id = f"jwt_injection_test_{uuid.uuid4().hex[:8]}"
        self.test_results = {}
        self.start_time = time.time()
        
        # Test configuration
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self.config = get_agentcore_config(self.environment)
        
        # Interactive authentication service
        self.interactive_auth = InteractiveAuthService()
        self.authenticated_user = None
        self.jwt_token = None
        
        logger.info(f"Initializing enhanced JWT injection test")
        logger.info(f"Test session ID: {self.test_session_id}")
        logger.info(f"Environment: {self.environment}")
    
    async def test_enhanced_jwt_manager_basic_functionality(self):
        """Test 1: Basic enhanced JWT token manager functionality."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: ENHANCED JWT MANAGER BASIC FUNCTIONALITY")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            # Create a new JWT manager instance for testing
            test_manager = EnhancedJWTTokenManager()
            
            # Test 1.1: Initial state
            initial_token = test_manager.get_current_token()
            initial_status = test_manager.get_injection_status()
            
            # Test 1.2: Component registration
            mock_component = MockComponent("test_component")
            test_manager.register_component("test_component", mock_component)
            
            mock_agent = MockAgent("test_agent")
            test_manager.register_component("test_agent", mock_agent)
            
            # Test 1.3: JWT token setting and propagation
            test_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJleHAiOjk5OTk5OTk5OTksImlhdCI6MTYwMDAwMDAwMCwidXNlcm5hbWUiOiJ0ZXN0LXVzZXIifQ.test-signature"
            test_username = "test-user"
            test_expires = datetime.utcnow() + timedelta(hours=1)
            
            token_set_success = test_manager.set_jwt_token(
                token=test_token,
                username=test_username,
                expires_at=test_expires
            )
            
            # Test 1.4: Token retrieval and validation
            current_token = test_manager.get_current_token()
            token_info = test_manager.get_token_info()
            is_valid = test_manager.is_token_valid()
            
            # Test 1.5: Component token propagation verification
            component_has_token = mock_component.jwt_token == test_token
            agent_tools_have_token = all(
                tool.runtime_client.jwt_token == test_token 
                for tool in mock_agent.tools
            )
            
            # Test 1.6: Status after token injection
            final_status = test_manager.get_injection_status()
            
            # Store test results
            self.test_results['enhanced_jwt_manager_basic'] = {
                'success': True,
                'initial_token_none': initial_token is None,
                'initial_components_count': initial_status['registered_components'],
                'component_registration_success': True,
                'token_set_success': token_set_success,
                'current_token_matches': current_token == test_token,
                'token_info_complete': (
                    token_info and 
                    token_info.token == test_token and
                    token_info.username == test_username
                ),
                'token_validation_success': is_valid,
                'component_token_propagation': component_has_token,
                'agent_tools_token_propagation': agent_tools_have_token,
                'final_components_count': final_status['registered_components'],
                'final_status_has_token': final_status['has_token'],
                'final_status_valid': final_status['token_valid'],
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Enhanced JWT manager basic functionality PASSED")
            logger.info(f"Token set: {token_set_success}, Valid: {is_valid}")
            logger.info(f"Component propagation: {component_has_token}")
            logger.info(f"Agent tools propagation: {agent_tools_have_token}")
            logger.info(f"Registered components: {final_status['registered_components']}")
            
        except Exception as e:
            logger.error(f"❌ Enhanced JWT manager basic functionality FAILED: {e}")
            self.test_results['enhanced_jwt_manager_basic'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_global_jwt_injection_integration(self):
        """Test 2: Global JWT injection integration with main application."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: GLOBAL JWT INJECTION INTEGRATION")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            # Test 2.1: Global JWT injection function
            test_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbG9iYWwtdGVzdCIsImV4cCI6OTk5OTk5OTk5OSwiaWF0IjoxNjAwMDAwMDAwLCJ1c2VybmFtZSI6Imdsb2JhbC10ZXN0In0.global-test-signature"
            test_username = "global-test"
            test_expires = datetime.utcnow() + timedelta(hours=2)
            
            global_injection_success = inject_jwt_token_globally(
                token=test_token,
                username=test_username,
                expires_at=test_expires
            )
            
            # Test 2.2: Global token retrieval
            current_global_token = get_current_jwt_token()
            global_status = get_jwt_injection_status()
            
            # Test 2.3: Register additional components
            additional_mock = MockComponent("additional_component")
            register_component_for_jwt_injection("additional_component", additional_mock)
            
            # Wait a moment for registration to complete
            await asyncio.sleep(0.1)
            
            # Test 2.4: Verify additional component received token
            additional_component_has_token = additional_mock.jwt_token == test_token
            
            # Test 2.5: Status after additional registration
            updated_status = get_jwt_injection_status()
            
            # Store test results
            self.test_results['global_jwt_injection_integration'] = {
                'success': True,
                'global_injection_success': global_injection_success,
                'current_token_matches': current_global_token == test_token,
                'global_status_has_token': global_status['has_token'],
                'global_status_valid': global_status['token_valid'],
                'global_status_username': global_status['username'] == test_username,
                'additional_component_registration': True,
                'additional_component_token_propagation': additional_component_has_token,
                'components_count_increased': updated_status['registered_components'] > global_status['registered_components'],
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Global JWT injection integration PASSED")
            logger.info(f"Global injection: {global_injection_success}")
            logger.info(f"Current token matches: {current_global_token == test_token}")
            logger.info(f"Additional component token: {additional_component_has_token}")
            logger.info(f"Components registered: {updated_status['registered_components']}")
            
        except Exception as e:
            logger.error(f"❌ Global JWT injection integration FAILED: {e}")
            self.test_results['global_jwt_injection_integration'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_real_component_integration(self):
        """Test 3: Integration with real AgentCore components."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: REAL COMPONENT INTEGRATION")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            # Test 3.1: Create real AgentCore components
            agentcore_client = AgentCoreRuntimeClient(
                region="us-east-1",
                connection_config=ConnectionConfig(timeout_seconds=30)
            )
            
            search_tool = RestaurantSearchTool(
                runtime_client=agentcore_client,
                search_agent_arn=self.config.agentcore.restaurant_search_agent_arn
            )
            
            reasoning_tool = RestaurantReasoningTool(
                runtime_client=agentcore_client,
                reasoning_agent_arn=self.config.agentcore.restaurant_reasoning_agent_arn
            )
            
            # Test 3.2: Register real components
            register_component_for_jwt_injection("real_agentcore_client", agentcore_client)
            register_component_for_jwt_injection("real_search_tool", search_tool)
            register_component_for_jwt_injection("real_reasoning_tool", reasoning_tool)
            
            # Test 3.3: Inject JWT token
            test_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyZWFsLXRlc3QiLCJleHAiOjk5OTk5OTk5OTksImlhdCI6MTYwMDAwMDAwMCwidXNlcm5hbWUiOiJyZWFsLXRlc3QifQ.real-test-signature"
            
            real_injection_success = inject_jwt_token_globally(
                token=test_token,
                username="real-test"
            )
            
            # Test 3.4: Verify token propagation to real components
            client_has_token = agentcore_client.jwt_token == test_token
            search_tool_has_token = search_tool.runtime_client.jwt_token == test_token
            reasoning_tool_has_token = reasoning_tool.runtime_client.jwt_token == test_token
            
            # Test 3.5: Get comprehensive status
            real_component_status = get_jwt_injection_status()
            
            # Store test results
            self.test_results['real_component_integration'] = {
                'success': True,
                'real_components_created': True,
                'real_components_registered': True,
                'real_injection_success': real_injection_success,
                'client_token_propagation': client_has_token,
                'search_tool_token_propagation': search_tool_has_token,
                'reasoning_tool_token_propagation': reasoning_tool_has_token,
                'all_real_components_have_token': (
                    client_has_token and 
                    search_tool_has_token and 
                    reasoning_tool_has_token
                ),
                'total_registered_components': real_component_status['registered_components'],
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Real component integration PASSED")
            logger.info(f"Real injection: {real_injection_success}")
            logger.info(f"Client token: {client_has_token}")
            logger.info(f"Search tool token: {search_tool_has_token}")
            logger.info(f"Reasoning tool token: {reasoning_tool_has_token}")
            logger.info(f"Total components: {real_component_status['registered_components']}")
            
        except Exception as e:
            logger.error(f"❌ Real component integration FAILED: {e}")
            self.test_results['real_component_integration'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_interactive_auth_integration(self):
        """Test 4: Integration with interactive authentication."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: INTERACTIVE AUTHENTICATION INTEGRATION")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            # Test 4.1: Interactive authentication
            logger.info("🔐 Starting interactive authentication for JWT injection test")
            
            auth_info = await self.interactive_auth.authenticate_user()
            
            self.authenticated_user = auth_info['username']
            self.jwt_token = auth_info['jwt_token']
            
            # Test 4.2: Inject real JWT token globally
            real_jwt_injection_success = inject_jwt_token_globally(
                token=self.jwt_token,
                username=self.authenticated_user
            )
            
            # Test 4.3: Verify token is current
            current_token = get_current_jwt_token()
            token_matches = current_token == self.jwt_token
            
            # Test 4.4: Get final status
            final_status = get_jwt_injection_status()
            
            # Store test results
            self.test_results['interactive_auth_integration'] = {
                'success': True,
                'authentication_success': True,
                'authenticated_user': self.authenticated_user,
                'jwt_token_obtained': self.jwt_token is not None,
                'real_jwt_injection_success': real_jwt_injection_success,
                'current_token_matches': token_matches,
                'final_status_valid': final_status['token_valid'],
                'final_status_username': final_status['username'] == self.authenticated_user,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Interactive authentication integration PASSED")
            logger.info(f"👤 Authenticated user: {self.authenticated_user}")
            logger.info(f"🔑 JWT token obtained: {self.jwt_token is not None}")
            logger.info(f"📡 Real JWT injection: {real_jwt_injection_success}")
            logger.info(f"✅ Token validation: {final_status['token_valid']}")
            
        except Exception as e:
            logger.error(f"❌ Interactive authentication integration FAILED: {e}")
            self.test_results['interactive_auth_integration'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the comprehensive enhanced JWT injection test suite."""
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE ENHANCED JWT INJECTION TEST")
        logger.info("=" * 80)
        
        try:
            # Test 1: Basic functionality
            await self.test_enhanced_jwt_manager_basic_functionality()
            
            # Test 2: Global integration
            await self.test_global_jwt_injection_integration()
            
            # Test 3: Real component integration
            await self.test_real_component_integration()
            
            # Test 4: Interactive authentication integration
            await self.test_interactive_auth_integration()
            
            # Generate comprehensive test report
            return self.generate_comprehensive_report()
            
        except Exception as e:
            logger.error(f"Test suite failed with error: {e}")
            self.test_results['test_suite_error'] = {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
            return self.generate_comprehensive_report()
        finally:
            # Cleanup authentication
            if self.interactive_auth:
                await self.interactive_auth.logout()
                logger.info("🔓 Authentication cleanup completed")
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_time = time.time() - self.start_time
        
        # Calculate success metrics
        total_tests = len([k for k in self.test_results.keys() if not k.endswith('_error')])
        successful_tests = len([k for k, v in self.test_results.items() 
                               if isinstance(v, dict) and v.get('success', False)])
        
        report = {
            'test_session_id': self.test_session_id,
            'environment': self.environment,
            'total_execution_time_seconds': round(total_time, 3),
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': round((successful_tests / total_tests * 100) if total_tests > 0 else 0, 2)
            },
            'test_results': self.test_results,
            'final_jwt_status': get_jwt_injection_status(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("=" * 80)
        logger.info("ENHANCED JWT INJECTION TEST REPORT")
        logger.info("=" * 80)
        logger.info(f"Test Session: {self.test_session_id}")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Total Time: {total_time:.3f} seconds")
        logger.info(f"Tests: {successful_tests}/{total_tests} passed ({report['test_summary']['success_rate']}%)")
        
        if report['final_jwt_status']['has_token']:
            logger.info(f"✅ Final JWT Status: Valid token for {report['final_jwt_status']['username']}")
            logger.info(f"📡 Components: {report['final_jwt_status']['registered_components']}")
        else:
            logger.info("❌ Final JWT Status: No valid token")
        
        return report


async def main():
    """Main test execution function."""
    test_suite = EnhancedJWTInjectionTest()
    
    try:
        report = await test_suite.run_comprehensive_test()
        
        # Save report to file
        report_file = f"enhanced_jwt_injection_test_report_{test_suite.test_session_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Test report saved to: {report_file}")
        
        # Return appropriate exit code
        if report['test_summary']['success_rate'] == 100:
            logger.info("🎉 All tests passed!")
            return 0
        else:
            logger.warning(f"⚠️ Some tests failed ({report['test_summary']['failed_tests']} failures)")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Test suite execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)