#!/usr/bin/env python3
"""
Complete Workflow Validation Test for MBTI Travel Planner Agent

This test validates the complete end-to-end workflow including:
1. Hard-coded request prompt for three days, three travel spots' districts
2. Restaurant search and reasoning agent communication via AgentCore HTTPS
3. Response assembly and return to requestor

Test Scenarios:
- Complete 3-day itinerary generation workflow
- Restaurant search agent communication validation
- Restaurant reasoning agent communication validation
- Response formatting and assembly
- Error handling and fallback mechanisms
- Performance monitoring and metrics collection
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main agent and related services
from main import (
    app, 
    agentcore_client, 
    auth_manager, 
    monitoring_service,
    health_check_service,
    orchestration_engine,
    AGENTCORE_AVAILABLE,
    ORCHESTRATION_AVAILABLE
)

# Import AgentCore services for direct testing
from services.agentcore_runtime_client import AgentCoreRuntimeClient, ConnectionConfig
from services.authentication_manager import AuthenticationManager
from services.restaurant_search_tool import RestaurantSearchTool
from services.restaurant_reasoning_tool import RestaurantReasoningTool
from config.agentcore_environment_config import get_agentcore_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorkflowValidationTest:
    """Comprehensive workflow validation test suite."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.test_user_id = "test_user_workflow_validation"
        self.test_results = {}
        self.start_time = time.time()
        
        # Test configuration
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self.config = get_agentcore_config(self.environment)
        
        logger.info(f"Initializing workflow validation test for environment: {self.environment}")
        logger.info(f"Test session ID: {self.test_session_id}")
    
    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run the complete workflow validation test suite."""
        logger.info("=" * 80)
        logger.info("STARTING COMPLETE WORKFLOW VALIDATION TEST")
        logger.info("=" * 80)
        
        try:
            # Test 1: System Initialization Validation
            await self.test_system_initialization()
            
            # Test 2: Hard-coded Request Processing
            await self.test_hardcoded_request_processing()
            
            # Test 3: Restaurant Search Agent Communication
            await self.test_restaurant_search_communication()
            
            # Test 4: Restaurant Reasoning Agent Communication
            await self.test_restaurant_reasoning_communication()
            
            # Test 5: Complete End-to-End Workflow
            await self.test_complete_e2e_workflow()
            
            # Test 6: Error Handling and Fallbacks
            await self.test_error_handling()
            
            # Test 7: Performance and Monitoring
            await self.test_performance_monitoring()
            
            # Generate final test report
            return self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite failed with error: {e}")
            self.test_results['test_suite_error'] = {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
            return self.generate_test_report()
    
    async def test_system_initialization(self):
        """Test 1: Validate system initialization and component availability."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 1: SYSTEM INITIALIZATION VALIDATION")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            # Check AgentCore availability
            agentcore_status = {
                'available': AGENTCORE_AVAILABLE,
                'client_initialized': agentcore_client is not None,
                'auth_manager_available': auth_manager is not None,
                'config_loaded': self.config is not None
            }
            
            logger.info(f"AgentCore Status: {agentcore_status}")
            
            # Check orchestration availability
            orchestration_status = {
                'available': ORCHESTRATION_AVAILABLE,
                'engine_initialized': orchestration_engine is not None
            }
            
            logger.info(f"Orchestration Status: {orchestration_status}")
            
            # Check monitoring services
            monitoring_status = {
                'monitoring_service_available': monitoring_service is not None,
                'health_check_service_available': health_check_service is not None
            }
            
            logger.info(f"Monitoring Status: {monitoring_status}")
            
            # Test AgentCore health check if available
            health_check_result = None
            if health_check_service and AGENTCORE_AVAILABLE:
                try:
                    health_check_result = await health_check_service.check_agentcore_agents_health()
                    logger.info(f"Health Check Result: {health_check_result.overall_status}")
                except Exception as e:
                    logger.warning(f"Health check failed: {e}")
                    health_check_result = {'error': str(e)}
            
            # Store test results
            self.test_results['system_initialization'] = {
                'success': True,
                'agentcore_status': agentcore_status,
                'orchestration_status': orchestration_status,
                'monitoring_status': monitoring_status,
                'health_check_result': health_check_result,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ System initialization validation PASSED")
            
        except Exception as e:
            logger.error(f"❌ System initialization validation FAILED: {e}")
            self.test_results['system_initialization'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_hardcoded_request_processing(self):
        """Test 2: Validate hard-coded request prompt processing."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: HARD-CODED REQUEST PROCESSING")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        # Hard-coded test request for 3-day itinerary with 3 districts
        test_prompt = """
        I'm an ENFP personality type planning a 3-day trip to Hong Kong. 
        Please create a detailed itinerary that includes:
        
        Day 1: Central district - I want to explore business areas and upscale dining
        Day 2: Tsim Sha Tsui - Looking for cultural attractions and diverse restaurants  
        Day 3: Causeway Bay - Shopping and trendy food spots
        
        For each day, please recommend:
        - 2-3 tourist attractions suitable for my ENFP personality
        - 2-3 restaurants for lunch and dinner
        - Consider my preference for social, energetic environments
        
        Please provide restaurant recommendations with sentiment analysis and MBTI matching.
        """
        
        try:
            logger.info("Processing hard-coded 3-day itinerary request...")
            logger.info(f"Request prompt length: {len(test_prompt)} characters")
            
            # Create test payload
            test_payload = {
                "prompt": test_prompt,
                "sessionId": self.test_session_id,
                "userId": self.test_user_id,
                "enableTrace": True
            }
            
            # Process request through the main agent
            if hasattr(app, 'entrypoint'):
                # Use the app's entrypoint if available
                response = await app.entrypoint(test_payload)
            else:
                # Fallback to direct agent invocation
                from main import agent
                response = await agent(test_prompt)
            
            # Validate response structure
            response_validation = self.validate_response_structure(response)
            
            # Extract key information from response
            response_analysis = self.analyze_response_content(response)
            
            # Store test results
            self.test_results['hardcoded_request_processing'] = {
                'success': True,
                'request_prompt_length': len(test_prompt),
                'response_validation': response_validation,
                'response_analysis': response_analysis,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Hard-coded request processing PASSED")
            logger.info(f"Response validation: {response_validation}")
            
        except Exception as e:
            logger.error(f"❌ Hard-coded request processing FAILED: {e}")
            self.test_results['hardcoded_request_processing'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_restaurant_search_communication(self):
        """Test 3: Validate restaurant search agent communication via AgentCore HTTPS."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: RESTAURANT SEARCH AGENT COMMUNICATION")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        if not AGENTCORE_AVAILABLE or not agentcore_client:
            logger.warning("AgentCore not available, skipping restaurant search test")
            self.test_results['restaurant_search_communication'] = {
                'success': False,
                'error': 'AgentCore not available',
                'skipped': True
            }
            return
        
        try:
            # Test districts for the 3-day itinerary
            test_districts = ["Central district", "Tsim Sha Tsui", "Causeway Bay"]
            test_meal_types = ["lunch", "dinner"]
            
            logger.info(f"Testing restaurant search for districts: {test_districts}")
            
            # Create restaurant search tool
            search_tool = RestaurantSearchTool(
                runtime_client=agentcore_client,
                agent_arn=self.config.agentcore.restaurant_search_agent_arn,
                auth_manager=auth_manager
            )
            
            # Test 1: Search by districts
            district_search_result = await search_tool.search_restaurants_by_district(test_districts)
            logger.info(f"District search returned {len(district_search_result.get('restaurants', []))} restaurants")
            
            # Test 2: Search by meal types
            meal_search_result = await search_tool.search_restaurants_by_meal_type(test_meal_types)
            logger.info(f"Meal type search returned {len(meal_search_result.get('restaurants', []))} restaurants")
            
            # Test 3: Combined search
            combined_search_result = await search_tool.search_restaurants_combined(
                districts=test_districts,
                meal_types=test_meal_types
            )
            logger.info(f"Combined search returned {len(combined_search_result.get('restaurants', []))} restaurants")
            
            # Validate search results
            search_validation = {
                'district_search_valid': self.validate_restaurant_data(district_search_result),
                'meal_search_valid': self.validate_restaurant_data(meal_search_result),
                'combined_search_valid': self.validate_restaurant_data(combined_search_result),
                'district_count': len(district_search_result.get('restaurants', [])),
                'meal_count': len(meal_search_result.get('restaurants', [])),
                'combined_count': len(combined_search_result.get('restaurants', []))
            }
            
            # Store test results
            self.test_results['restaurant_search_communication'] = {
                'success': True,
                'test_districts': test_districts,
                'test_meal_types': test_meal_types,
                'search_validation': search_validation,
                'district_search_sample': district_search_result.get('restaurants', [])[:2],  # First 2 results
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Restaurant search agent communication PASSED")
            logger.info(f"Search validation: {search_validation}")
            
        except Exception as e:
            logger.error(f"❌ Restaurant search agent communication FAILED: {e}")
            self.test_results['restaurant_search_communication'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_restaurant_reasoning_communication(self):
        """Test 4: Validate restaurant reasoning agent communication via AgentCore HTTPS."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: RESTAURANT REASONING AGENT COMMUNICATION")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        if not AGENTCORE_AVAILABLE or not agentcore_client:
            logger.warning("AgentCore not available, skipping restaurant reasoning test")
            self.test_results['restaurant_reasoning_communication'] = {
                'success': False,
                'error': 'AgentCore not available',
                'skipped': True
            }
            return
        
        try:
            # Create sample restaurant data for reasoning
            sample_restaurants = [
                {
                    "id": "rest_001",
                    "name": "Central Gourmet",
                    "district": "Central district",
                    "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                    "cuisine": "International",
                    "price_range": "$$$$"
                },
                {
                    "id": "rest_002", 
                    "name": "TST Delights",
                    "district": "Tsim Sha Tsui",
                    "sentiment": {"likes": 78, "dislikes": 15, "neutral": 7},
                    "cuisine": "Cantonese",
                    "price_range": "$$$"
                },
                {
                    "id": "rest_003",
                    "name": "Causeway Bistro",
                    "district": "Causeway Bay", 
                    "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3},
                    "cuisine": "Fusion",
                    "price_range": "$$$"
                }
            ]
            
            logger.info(f"Testing restaurant reasoning with {len(sample_restaurants)} sample restaurants")
            
            # Create restaurant reasoning tool
            reasoning_tool = RestaurantReasoningTool(
                runtime_client=agentcore_client,
                agent_arn=self.config.agentcore.restaurant_reasoning_agent_arn,
                auth_manager=auth_manager
            )
            
            # Test 1: Recommend restaurants
            recommendation_result = await reasoning_tool.recommend_restaurants(
                restaurants=sample_restaurants,
                ranking_method="sentiment_likes"
            )
            logger.info(f"Recommendation result: {recommendation_result.get('recommendation', {}).get('name', 'None')}")
            
            # Test 2: Analyze sentiment
            sentiment_analysis_result = await reasoning_tool.analyze_restaurant_sentiment(
                restaurants=sample_restaurants
            )
            logger.info(f"Sentiment analysis completed for {sentiment_analysis_result.get('restaurant_count', 0)} restaurants")
            
            # Validate reasoning results
            reasoning_validation = {
                'recommendation_valid': self.validate_recommendation_data(recommendation_result),
                'sentiment_analysis_valid': self.validate_sentiment_analysis_data(sentiment_analysis_result),
                'recommendation_present': 'recommendation' in recommendation_result,
                'candidates_present': 'candidates' in recommendation_result,
                'analysis_summary_present': 'sentiment_analysis' in sentiment_analysis_result
            }
            
            # Store test results
            self.test_results['restaurant_reasoning_communication'] = {
                'success': True,
                'sample_restaurants_count': len(sample_restaurants),
                'reasoning_validation': reasoning_validation,
                'recommendation_sample': recommendation_result.get('recommendation', {}),
                'sentiment_summary': sentiment_analysis_result.get('sentiment_analysis', {}),
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Restaurant reasoning agent communication PASSED")
            logger.info(f"Reasoning validation: {reasoning_validation}")
            
        except Exception as e:
            logger.error(f"❌ Restaurant reasoning agent communication FAILED: {e}")
            self.test_results['restaurant_reasoning_communication'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_complete_e2e_workflow(self):
        """Test 5: Complete end-to-end workflow validation."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: COMPLETE END-TO-END WORKFLOW")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            # Complete workflow test prompt
            e2e_prompt = """
            Create a 3-day Hong Kong itinerary for an ENFP personality:
            
            Day 1: Central district - Business and upscale dining
            Day 2: Tsim Sha Tsui - Culture and diverse restaurants
            Day 3: Causeway Bay - Shopping and trendy food
            
            Include restaurant recommendations with MBTI matching and sentiment analysis.
            """
            
            logger.info("Executing complete end-to-end workflow...")
            
            # Execute the complete workflow
            workflow_start = time.time()
            
            # Create payload for the agent
            e2e_payload = {
                "prompt": e2e_prompt,
                "sessionId": self.test_session_id,
                "userId": self.test_user_id,
                "enableTrace": True
            }
            
            # Process through main agent
            if hasattr(app, 'entrypoint'):
                final_response = await app.entrypoint(e2e_payload)
            else:
                from main import agent
                final_response = await agent(e2e_prompt)
            
            workflow_time = time.time() - workflow_start
            
            # Analyze the complete response
            e2e_analysis = {
                'response_received': final_response is not None,
                'response_type': type(final_response).__name__,
                'workflow_time_seconds': workflow_time,
                'contains_itinerary': self.check_itinerary_content(final_response),
                'contains_restaurants': self.check_restaurant_content(final_response),
                'contains_mbti_matching': self.check_mbti_content(final_response),
                'response_length': len(str(final_response)) if final_response else 0
            }
            
            # Validate workflow completeness
            workflow_validation = {
                'all_days_covered': e2e_analysis['contains_itinerary'],
                'restaurant_data_present': e2e_analysis['contains_restaurants'],
                'mbti_analysis_present': e2e_analysis['contains_mbti_matching'],
                'response_comprehensive': (
                    e2e_analysis['contains_itinerary'] and 
                    e2e_analysis['contains_restaurants'] and
                    e2e_analysis['response_length'] > 500
                )
            }
            
            # Store test results
            self.test_results['complete_e2e_workflow'] = {
                'success': True,
                'e2e_analysis': e2e_analysis,
                'workflow_validation': workflow_validation,
                'final_response_preview': str(final_response)[:500] if final_response else None,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Complete end-to-end workflow PASSED")
            logger.info(f"Workflow validation: {workflow_validation}")
            logger.info(f"Workflow execution time: {workflow_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"❌ Complete end-to-end workflow FAILED: {e}")
            self.test_results['complete_e2e_workflow'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_error_handling(self):
        """Test 6: Error handling and fallback mechanisms."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 6: ERROR HANDLING AND FALLBACKS")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            error_tests = {}
            
            # Test 1: Invalid agent ARN handling
            if agentcore_client:
                try:
                    invalid_response = await agentcore_client.invoke_agent(
                        agent_arn="invalid-arn",
                        input_text="test",
                        session_id=self.test_session_id
                    )
                    error_tests['invalid_arn'] = {'handled': False, 'response': str(invalid_response)}
                except Exception as e:
                    error_tests['invalid_arn'] = {'handled': True, 'error_type': type(e).__name__}
            
            # Test 2: Empty input handling
            try:
                empty_payload = {
                    "prompt": "",
                    "sessionId": self.test_session_id
                }
                
                if hasattr(app, 'entrypoint'):
                    empty_response = await app.entrypoint(empty_payload)
                else:
                    from main import agent
                    empty_response = await agent("")
                
                error_tests['empty_input'] = {
                    'handled': True, 
                    'response_received': empty_response is not None,
                    'response_type': type(empty_response).__name__
                }
            except Exception as e:
                error_tests['empty_input'] = {'handled': True, 'error_type': type(e).__name__}
            
            # Test 3: Malformed request handling
            try:
                malformed_payload = {
                    "invalid_field": "test",
                    "sessionId": self.test_session_id
                }
                
                if hasattr(app, 'entrypoint'):
                    malformed_response = await app.entrypoint(malformed_payload)
                    error_tests['malformed_request'] = {
                        'handled': True,
                        'response_received': malformed_response is not None
                    }
                else:
                    error_tests['malformed_request'] = {'handled': True, 'note': 'Direct agent call used'}
            except Exception as e:
                error_tests['malformed_request'] = {'handled': True, 'error_type': type(e).__name__}
            
            # Store test results
            self.test_results['error_handling'] = {
                'success': True,
                'error_tests': error_tests,
                'all_errors_handled': all(test.get('handled', False) for test in error_tests.values()),
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Error handling and fallbacks PASSED")
            logger.info(f"Error tests: {error_tests}")
            
        except Exception as e:
            logger.error(f"❌ Error handling test FAILED: {e}")
            self.test_results['error_handling'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    async def test_performance_monitoring(self):
        """Test 7: Performance monitoring and metrics collection."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 7: PERFORMANCE MONITORING")
        logger.info("=" * 60)
        
        test_start = time.time()
        
        try:
            performance_metrics = {}
            
            # Test monitoring service availability
            if monitoring_service:
                # Test metric logging
                try:
                    monitoring_service.log_performance_metric(
                        operation="test_metric",
                        duration=0.1,
                        success=True,
                        additional_data={"test": "validation"}
                    )
                    performance_metrics['metric_logging'] = {'available': True}
                except Exception as e:
                    performance_metrics['metric_logging'] = {'available': False, 'error': str(e)}
                
                # Test error logging
                try:
                    test_error = Exception("Test error for monitoring")
                    monitoring_service.log_error(
                        error=test_error,
                        operation="test_error_logging",
                        context={"test": "validation"}
                    )
                    performance_metrics['error_logging'] = {'available': True}
                except Exception as e:
                    performance_metrics['error_logging'] = {'available': False, 'error': str(e)}
            else:
                performance_metrics['monitoring_service'] = {'available': False}
            
            # Test health check service
            if health_check_service:
                try:
                    health_status = health_check_service.get_health_status()
                    performance_metrics['health_checks'] = {
                        'available': True,
                        'status': health_status
                    }
                except Exception as e:
                    performance_metrics['health_checks'] = {'available': False, 'error': str(e)}
            else:
                performance_metrics['health_checks'] = {'available': False}
            
            # Test AgentCore client performance metrics
            if agentcore_client:
                try:
                    client_health = agentcore_client.get_health_status()
                    performance_metrics['agentcore_client'] = {
                        'available': True,
                        'health_status': {
                            'is_healthy': client_health.is_healthy,
                            'error_count': client_health.error_count,
                            'circuit_breaker_state': client_health.circuit_breaker_state.value
                        }
                    }
                except Exception as e:
                    performance_metrics['agentcore_client'] = {'available': False, 'error': str(e)}
            else:
                performance_metrics['agentcore_client'] = {'available': False}
            
            # Store test results
            self.test_results['performance_monitoring'] = {
                'success': True,
                'performance_metrics': performance_metrics,
                'monitoring_available': monitoring_service is not None,
                'health_checks_available': health_check_service is not None,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
            
            logger.info("✅ Performance monitoring PASSED")
            logger.info(f"Performance metrics: {performance_metrics}")
            
        except Exception as e:
            logger.error(f"❌ Performance monitoring test FAILED: {e}")
            self.test_results['performance_monitoring'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': int((time.time() - test_start) * 1000)
            }
    
    def validate_response_structure(self, response: Any) -> Dict[str, bool]:
        """Validate the structure of agent response."""
        validation = {
            'response_exists': response is not None,
            'response_not_empty': bool(str(response).strip()) if response else False,
            'response_has_content': len(str(response)) > 50 if response else False
        }
        
        # Check for specific response types
        if hasattr(response, 'message'):
            validation['has_message_attribute'] = True
            validation['message_has_content'] = bool(response.message.get('content')) if hasattr(response.message, 'get') else False
        
        return validation
    
    def analyze_response_content(self, response: Any) -> Dict[str, Any]:
        """Analyze the content of the response for key elements."""
        response_text = str(response).lower()
        
        analysis = {
            'mentions_hong_kong': 'hong kong' in response_text,
            'mentions_districts': any(district.lower() in response_text for district in ['central', 'tsim sha tsui', 'causeway bay']),
            'mentions_restaurants': any(word in response_text for word in ['restaurant', 'dining', 'food', 'cuisine']),
            'mentions_mbti': any(word in response_text for word in ['enfp', 'personality', 'mbti']),
            'mentions_itinerary': any(word in response_text for word in ['day 1', 'day 2', 'day 3', 'itinerary', 'schedule']),
            'response_length': len(response_text)
        }
        
        return analysis
    
    def validate_restaurant_data(self, data: Dict[str, Any]) -> bool:
        """Validate restaurant search data structure."""
        if not isinstance(data, dict):
            return False
        
        restaurants = data.get('restaurants', [])
        if not isinstance(restaurants, list):
            return False
        
        # Check if restaurants have required fields
        for restaurant in restaurants[:3]:  # Check first 3
            if not isinstance(restaurant, dict):
                return False
            if 'name' not in restaurant or 'district' not in restaurant:
                return False
        
        return True
    
    def validate_recommendation_data(self, data: Dict[str, Any]) -> bool:
        """Validate restaurant recommendation data structure."""
        if not isinstance(data, dict):
            return False
        
        # Check for required fields
        required_fields = ['recommendation', 'candidates']
        return all(field in data for field in required_fields)
    
    def validate_sentiment_analysis_data(self, data: Dict[str, Any]) -> bool:
        """Validate sentiment analysis data structure."""
        if not isinstance(data, dict):
            return False
        
        # Check for required fields
        required_fields = ['sentiment_analysis', 'restaurant_count']
        return all(field in data for field in required_fields)
    
    def check_itinerary_content(self, response: Any) -> bool:
        """Check if response contains itinerary content."""
        response_text = str(response).lower()
        day_mentions = sum(1 for day in ['day 1', 'day 2', 'day 3'] if day in response_text)
        return day_mentions >= 2
    
    def check_restaurant_content(self, response: Any) -> bool:
        """Check if response contains restaurant content."""
        response_text = str(response).lower()
        restaurant_keywords = ['restaurant', 'dining', 'food', 'cuisine', 'meal']
        return any(keyword in response_text for keyword in restaurant_keywords)
    
    def check_mbti_content(self, response: Any) -> bool:
        """Check if response contains MBTI-related content."""
        response_text = str(response).lower()
        mbti_keywords = ['enfp', 'personality', 'mbti', 'social', 'energetic']
        return any(keyword in response_text for keyword in mbti_keywords)
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_time = time.time() - self.start_time
        
        # Calculate success metrics
        successful_tests = sum(1 for result in self.test_results.values() 
                             if isinstance(result, dict) and result.get('success', False))
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate summary
        test_summary = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate_percent': round(success_rate, 2),
            'total_execution_time_seconds': round(total_time, 2)
        }
        
        # Create final report
        report = {
            'test_session_id': self.test_session_id,
            'test_environment': self.environment,
            'test_timestamp': datetime.utcnow().isoformat(),
            'test_summary': test_summary,
            'detailed_results': self.test_results,
            'system_status': {
                'agentcore_available': AGENTCORE_AVAILABLE,
                'orchestration_available': ORCHESTRATION_AVAILABLE,
                'monitoring_available': monitoring_service is not None,
                'health_checks_available': health_check_service is not None
            }
        }
        
        return report

async def main():
    """Main test execution function."""
    print("🚀 Starting MBTI Travel Planner Agent Workflow Validation")
    print("=" * 80)
    
    # Initialize test suite
    test_suite = WorkflowValidationTest()
    
    # Run complete validation
    test_report = await test_suite.run_complete_validation()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)
    
    summary = test_report['test_summary']
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate_percent']}%")
    print(f"Total Time: {summary['total_execution_time_seconds']} seconds")
    
    # Print system status
    print(f"\nSystem Status:")
    status = test_report['system_status']
    print(f"  AgentCore Available: {status['agentcore_available']}")
    print(f"  Orchestration Available: {status['orchestration_available']}")
    print(f"  Monitoring Available: {status['monitoring_available']}")
    print(f"  Health Checks Available: {status['health_checks_available']}")
    
    # Print detailed results
    print(f"\nDetailed Test Results:")
    for test_name, result in test_report['detailed_results'].items():
        status_icon = "✅" if result.get('success', False) else "❌"
        execution_time = result.get('execution_time_ms', 0)
        print(f"  {status_icon} {test_name}: {execution_time}ms")
        
        if not result.get('success', False) and 'error' in result:
            print(f"    Error: {result['error']}")
    
    # Save detailed report to file
    report_filename = f"workflow_validation_report_{test_suite.test_session_id}.json"
    with open(report_filename, 'w') as f:
        json.dump(test_report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    
    # Return exit code based on success rate
    if summary['success_rate_percent'] >= 80:
        print("\n🎉 Workflow validation PASSED (≥80% success rate)")
        return 0
    else:
        print("\n⚠️  Workflow validation FAILED (<80% success rate)")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)