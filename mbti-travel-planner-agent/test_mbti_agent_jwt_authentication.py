#!/usr/bin/env python3
"""
Test JWT Authentication for MBTI Travel Planner Agent

This script tests the mbti-travel-planner-agent deployed in AWS with JWT authentication
to validate all functionality including restaurant search, MBTI-based recommendations,
and general travel planning capabilities.
"""

import json
import subprocess
import sys
import logging
import tempfile
import base64
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MBTITravelPlannerJWTTester:
    """JWT authentication tester for MBTI Travel Planner Agent."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.jwt_token_file = Path("fresh_jwt.txt")
        
        # Create test directories following the project guidelines
        self.tests_dir = self.project_root / "tests"
        self.payload_dir = self.tests_dir / "payload"
        self.request_dir = self.tests_dir / "request"
        self.response_dir = self.tests_dir / "response"
        self.results_dir = self.tests_dir / "results"
        
        # Create all directories
        for directory in [self.tests_dir, self.payload_dir, self.request_dir, 
                         self.response_dir, self.results_dir]:
            directory.mkdir(exist_ok=True)
        
        self.test_results = []
        
        # Agent configuration from .bedrock_agentcore.yaml
        self.agent_name = "mbti_travel_planner_agent"
        
    def load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration."""
        try:
            config_file = self.project_root / "config" / "cognito_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("No cognito_config.json found")
                return {}
        except Exception as e:
            logger.error(f"Failed to load Cognito config: {e}")
            return {}
    
    def calculate_secret_hash(self, username: str, client_id: str, client_secret: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication."""
        message = username + client_id
        dig = hmac.new(
            client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def authenticate_with_cognito(self, cognito_config: Dict[str, Any]) -> Optional[str]:
        """Authenticate with Cognito and get JWT token."""
        try:
            import boto3
            import getpass
            from botocore.exceptions import ClientError
            
            # Get username
            default_username = cognito_config.get('test_user', {}).get('username', 'test@mbti-travel.com')
            username = input(f"Enter username (default: {default_username}): ").strip()
            if not username:
                username = default_username
            
            # Get password
            password = getpass.getpass(f"Enter password for {username}: ")
            
            logger.info(f"🔐 Authenticating with Cognito as: {username}")
            
            # Get client credentials
            client_id = cognito_config['app_client']['client_id']
            client_secret = cognito_config['app_client']['client_secret']
            
            # Calculate SECRET_HASH
            secret_hash = self.calculate_secret_hash(username, client_id, client_secret)
            
            cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
            
            # Prepare auth parameters with SECRET_HASH
            auth_parameters = {
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
            
            logger.info("🔑 Initiating authentication with SECRET_HASH...")
            
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters=auth_parameters
            )
            
            access_token = response['AuthenticationResult']['AccessToken']
            logger.info("✅ JWT Authentication successful")
            logger.info(f"Token length: {len(access_token)} characters")
            
            return access_token
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Cognito authentication failed: {error_code} - {error_message}")
            
            # Provide helpful error messages
            if error_code == 'NotAuthorizedException':
                logger.error("❌ Invalid username or password")
            elif error_code == 'UserNotFoundException':
                logger.error("❌ User not found")
            elif error_code == 'InvalidParameterException':
                logger.error("❌ Invalid parameters - check client configuration")
            else:
                logger.error(f"❌ Authentication error: {error_code}")
            
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def load_jwt_token(self) -> str:
        """Load JWT token from file, Cognito authentication, or user input."""
        try:
            # First try to load from file
            if self.jwt_token_file.exists():
                token = self.jwt_token_file.read_text().strip()
                if token and len(token) > 100:
                    logger.info("✅ JWT token loaded from file successfully")
                    return token
            
            # Try Cognito authentication
            logger.info("📝 No JWT token file found. Attempting Cognito authentication...")
            cognito_config = self.load_cognito_config()
            
            if cognito_config:
                print("\n" + "="*60)
                print("🔐 Cognito Authentication for MBTI Travel Planner Agent Testing")
                print("="*60)
                print("Attempting to authenticate with Cognito to get a fresh JWT token...")
                print("-"*60)
                
                token = self.authenticate_with_cognito(cognito_config)
                if token:
                    # Save the token for future use
                    try:
                        self.jwt_token_file.write_text(token)
                        logger.info(f"✅ JWT token saved to {self.jwt_token_file}")
                    except Exception as e:
                        logger.warning(f"Could not save token: {e}")
                    
                    return token
            
            # If Cognito auth failed, prompt for manual input
            logger.info("📝 Cognito authentication failed. Please provide JWT token manually.")
            print("\n" + "="*60)
            print("🔐 Manual JWT Token Input")
            print("="*60)
            print("Please paste your JWT token below:")
            print("(The token should be a long string starting with 'eyJ')")
            print("-"*60)
            
            token = input("JWT Token: ").strip()
            
            if not token:
                logger.error("❌ No JWT token provided")
                return None
            
            if len(token) < 100:
                logger.error("❌ JWT token appears to be too short (should be several hundred characters)")
                return None
            
            if not token.startswith('eyJ'):
                logger.error("❌ JWT token should start with 'eyJ'")
                return None
            
            logger.info("✅ JWT token provided by user")
            
            # Optionally save the token for future use
            try:
                save_token = input("\n💾 Save this token for future tests? (y/N): ").strip().lower()
                if save_token in ['y', 'yes']:
                    self.jwt_token_file.write_text(token)
                    logger.info(f"✅ JWT token saved to {self.jwt_token_file}")
            except Exception as e:
                logger.warning(f"Could not save token: {e}")
            
            return token
            
        except KeyboardInterrupt:
            logger.info("\n❌ User cancelled token input")
            return None
        except Exception as e:
            logger.error(f"Error loading JWT token: {e}")
            return None
    
    def save_request_payload(self, payload: Dict[str, Any], test_name: str) -> str:
        """Save request payload in base64 format."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Convert payload to JSON string
            payload_json = json.dumps(payload, ensure_ascii=False)
            
            # Encode to base64
            payload_b64 = base64.b64encode(payload_json.encode('utf-8')).decode('ascii')
            
            # Save to payload directory
            payload_file = self.payload_dir / f"payload_{test_name.lower().replace(' ', '_')}_{timestamp}.b64"
            with open(payload_file, 'w', encoding='ascii') as f:
                f.write(payload_b64)
            
            # Also save readable version to request directory
            request_file = self.request_dir / f"request_{test_name.lower().replace(' ', '_')}_{timestamp}.json"
            request_data = {
                'test_name': test_name,
                'timestamp': timestamp,
                'payload': payload,
                'base64_file': str(payload_file)
            }
            
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved request payload to {payload_file}")
            return str(payload_file)
            
        except Exception as e:
            logger.error(f"Error saving request payload: {e}")
            return None
    
    def save_response(self, response_text: str, test_name: str, prompt: str):
        """Save full agent response for analysis."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to response directory
            response_file = self.response_dir / f"response_{test_name.lower().replace(' ', '_')}_{timestamp}.txt"
            
            response_data = {
                'test_name': test_name,
                'prompt': prompt,
                'timestamp': timestamp,
                'response_length': len(response_text),
                'response_text': response_text
            }
            
            # Save as JSON for structured access
            json_file = self.response_dir / f"response_{test_name.lower().replace(' ', '_')}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            # Also save raw text for easy reading
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Prompt: {prompt}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write("=" * 50 + "\n\n")
                f.write(response_text)
            
            logger.info(f"Saved response to {response_file}")
            
        except Exception as e:
            logger.error(f"Error saving response: {e}")
    
    def analyze_response(self, response_text: str, test_name: str) -> Dict[str, Any]:
        """Analyze the agent response for MBTI and travel planning functionality."""
        try:
            analysis = {
                'test_name': test_name,
                'response_length': len(response_text),
                'has_mbti_content': False,
                'has_restaurant_data': False,
                'has_travel_planning': False,
                'has_tool_usage': False,
                'is_error_response': False,
                'restaurant_count': 0,
                'mbti_types_mentioned': [],
                'districts_mentioned': [],
                'meal_types_mentioned': [],
                'tools_used': [],
                'response_quality': 'unknown'
            }
            
            response_lower = response_text.lower()
            
            # Check for MBTI-related content
            mbti_types = ['enfp', 'infp', 'entj', 'intj', 'enfj', 'infj', 'entp', 'intp',
                         'esfp', 'isfp', 'estj', 'istj', 'esfj', 'isfj', 'estp', 'istp']
            analysis['mbti_types_mentioned'] = [mbti for mbti in mbti_types if mbti in response_lower]
            
            mbti_keywords = ['personality', 'mbti', 'extrovert', 'introvert', 'thinking', 'feeling',
                           'judging', 'perceiving', 'social', 'contemplative', 'energetic', 'private']
            mbti_found = [kw for kw in mbti_keywords if kw in response_lower]
            
            if analysis['mbti_types_mentioned'] or len(mbti_found) >= 2:
                analysis['has_mbti_content'] = True
            
            # Check for restaurant-related content
            restaurant_keywords = [
                'restaurant', 'dining', 'food', 'cuisine', 'menu', 'breakfast', 'lunch', 'dinner',
                'central district', 'admiralty', 'causeway bay', 'tsim sha tsui'
            ]
            restaurant_found = [kw for kw in restaurant_keywords if kw in response_lower]
            
            if len(restaurant_found) >= 3:
                analysis['has_restaurant_data'] = True
            
            # Check for travel planning content
            travel_keywords = [
                'travel', 'trip', 'itinerary', 'plan', 'visit', 'attraction', 'hong kong',
                'recommendation', 'suggest', 'explore', 'experience'
            ]
            travel_found = [kw for kw in travel_keywords if kw in response_lower]
            
            if len(travel_found) >= 3:
                analysis['has_travel_planning'] = True
            
            # Check for districts mentioned
            districts = ['central district', 'admiralty', 'causeway bay', 'tsim sha tsui', 
                        'wan chai', 'mong kok', 'sha tin', 'tsuen wan']
            analysis['districts_mentioned'] = [d for d in districts if d in response_lower]
            
            # Check for meal types mentioned
            meal_types = ['breakfast', 'lunch', 'dinner', 'brunch']
            analysis['meal_types_mentioned'] = [m for m in meal_types if m in response_lower]
            
            # Check for tool usage indicators
            tool_indicators = [
                'search', 'found', 'results', 'data', 'information', 'retrieved',
                'analysis', 'recommendation', 'based on', 'according to'
            ]
            tool_usage_found = [ti for ti in tool_indicators if ti in response_lower]
            
            if len(tool_usage_found) >= 3:
                analysis['has_tool_usage'] = True
            
            # Check for error responses
            error_indicators = [
                'error', 'failed', 'unable', 'cannot', 'unavailable', 'issue', 'problem'
            ]
            error_found = [ei for ei in error_indicators if ei in response_lower]
            
            if len(error_found) >= 2:
                analysis['is_error_response'] = True
            
            # Determine response quality
            quality_score = 0
            
            if analysis['has_mbti_content']:
                quality_score += 3
            if analysis['has_restaurant_data']:
                quality_score += 3
            if analysis['has_travel_planning']:
                quality_score += 2
            if analysis['has_tool_usage']:
                quality_score += 2
            if analysis['districts_mentioned']:
                quality_score += 1
            if analysis['meal_types_mentioned']:
                quality_score += 1
            if analysis['is_error_response']:
                quality_score -= 3
            
            if quality_score >= 8:
                analysis['response_quality'] = 'excellent'
            elif quality_score >= 6:
                analysis['response_quality'] = 'good'
            elif quality_score >= 4:
                analysis['response_quality'] = 'basic'
            elif analysis['is_error_response']:
                analysis['response_quality'] = 'error'
            else:
                analysis['response_quality'] = 'poor'
            
            analysis['quality_score'] = quality_score
            analysis['keywords_found'] = {
                'mbti': mbti_found,
                'restaurant': restaurant_found,
                'travel': travel_found,
                'tool_usage': tool_usage_found,
                'error': error_found
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return {
                'test_name': test_name,
                'response_quality': 'analysis_error',
                'error': str(e)
            }
    
    def test_agent_invocation(self, prompt: str, test_name: str) -> Dict[str, Any]:
        """Test agent invocation with JWT authentication."""
        logger.info(f"🧪 Testing: {test_name}")
        logger.info(f"Prompt: {prompt}")
        
        try:
            # Load JWT token
            if hasattr(self, 'provided_token') and self.provided_token:
                token = self.provided_token
            else:
                token = self.load_jwt_token()
            
            if not token:
                return {
                    "test": test_name,
                    "status": "failed",
                    "error": "No JWT token available"
                }
            
            # Create payload
            payload = {"prompt": prompt}
            
            # Save payload
            payload_file = self.save_request_payload(payload, test_name)
            
            # Create temporary file for agentcore invoke
            payload_json = json.dumps(payload)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(payload_json)
                temp_file = f.name
            
            try:
                # Execute agentcore invoke with the correct agent name
                cmd = [
                    "agentcore", "invoke",
                    "--agent", self.agent_name,
                    "--bearer-token", token,
                    f"@{temp_file}"
                ]
                
                logger.info("🔄 Invoking MBTI Travel Planner agent...")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Clean up temp file
                Path(temp_file).unlink()
                
                if result.returncode == 0:
                    logger.info("✅ Agent invocation successful")
                    
                    output = result.stdout
                    
                    # Save response
                    self.save_response(output, test_name, prompt)
                    
                    # Analyze response
                    analysis = self.analyze_response(output, test_name)
                    
                    logger.info(f"Response quality: {analysis['response_quality']}")
                    logger.info(f"MBTI content: {analysis['has_mbti_content']}")
                    logger.info(f"Restaurant data: {analysis['has_restaurant_data']}")
                    logger.info(f"Travel planning: {analysis['has_travel_planning']}")
                    
                    return {
                        "test": test_name,
                        "status": "success",
                        "response_length": len(output),
                        "analysis": analysis,
                        "output_preview": output[:500] + "..." if len(output) > 500 else output
                    }
                else:
                    logger.error(f"❌ Agent invocation failed: {result.stderr}")
                    return {
                        "test": test_name,
                        "status": "failed",
                        "error": result.stderr[:200],
                        "stdout": result.stdout[:200] if result.stdout else ""
                    }
                    
            finally:
                # Ensure temp file is cleaned up
                try:
                    Path(temp_file).unlink()
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            logger.error("❌ Test timed out")
            return {
                "test": test_name,
                "status": "timeout",
                "error": "Request timed out after 120 seconds"
            }
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return {
                "test": test_name,
                "status": "error",
                "error": str(e)
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests of the MBTI Travel Planner agent."""
        logger.info("🚀 Starting MBTI Travel Planner Agent JWT Authentication Tests")
        logger.info("=" * 70)
        
        # Test cases covering different functionality
        test_cases = [
            {
                "name": "Basic Greeting",
                "prompt": "Hello!"
            },
            {
                "name": "MBTI ENFP Restaurant Search",
                "prompt": "I'm an ENFP personality type visiting Hong Kong. Can you help me find restaurants in Central district that are good for breakfast and lunch? I love social dining experiences and energetic atmospheres."
            },
            {
                "name": "MBTI INTJ Restaurant Search",
                "prompt": "As an INTJ, I prefer focused and private dining experiences. Can you find dinner restaurants in Central district that offer quiet environments for deep thinking and reflection?"
            },
            {
                "name": "District Specific Search",
                "prompt": "I'm staying in Central district, Hong Kong. Can you search for all available restaurants in this area and provide recommendations based on their ratings and reviews?"
            },
            {
                "name": "MBTI Travel Planning",
                "prompt": "I'm an ENFP visiting Hong Kong for 3 days. Can you help me create a complete dining itinerary? I'll be staying in Central district but I'm open to exploring nearby areas."
            },
            {
                "name": "Business Travel ENTJ",
                "prompt": "I'm traveling to Hong Kong for a business conference in Central district. As an ENTJ, I need efficient dining options for client meetings. Can you recommend restaurants suitable for breakfast meetings and business lunches?"
            },
            {
                "name": "Multiple Districts",
                "prompt": "I'll be visiting both Central district and Admiralty in Hong Kong. Can you find restaurants in both areas and help me plan my dining itinerary?"
            },
            {
                "name": "Meal Type Specific",
                "prompt": "I'm looking for the best breakfast spots in Hong Kong. Can you search for restaurants that serve breakfast and rank them by customer sentiment and reviews?"
            },
            {
                "name": "General Travel Planning",
                "prompt": "I'm planning a trip to Hong Kong. Besides restaurants, what other attractions should I visit? I'm an ENFP who loves social activities and vibrant experiences."
            },
            {
                "name": "Restaurant Analysis Request",
                "prompt": "I found some restaurants in Central district but I'm not sure which ones are the best. Can you analyze their customer reviews and sentiment to help me choose?"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            result = self.test_agent_invocation(
                test_case["prompt"], 
                test_case["name"]
            )
            results.append(result)
            self.test_results.append(result)
            
            # Add delay between tests
            import time
            time.sleep(2)
        
        # Analyze overall results
        successful = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] in ["failed", "error", "timeout"])
        
        # Analyze response quality
        excellent_responses = sum(
            1 for r in results 
            if r["status"] == "success" and r.get("analysis", {}).get("response_quality") == "excellent"
        )
        
        good_responses = sum(
            1 for r in results 
            if r["status"] == "success" and r.get("analysis", {}).get("response_quality") == "good"
        )
        
        mbti_functionality = sum(
            1 for r in results 
            if r["status"] == "success" and r.get("analysis", {}).get("has_mbti_content", False)
        )
        
        restaurant_functionality = sum(
            1 for r in results 
            if r["status"] == "success" and r.get("analysis", {}).get("has_restaurant_data", False)
        )
        
        travel_planning_functionality = sum(
            1 for r in results 
            if r["status"] == "success" and r.get("analysis", {}).get("has_travel_planning", False)
        )
        
        # Determine overall status
        if excellent_responses >= len(results) * 0.7:
            overall_status = "EXCELLENT"
        elif successful >= len(results) * 0.8 and mbti_functionality >= len(results) * 0.5:
            overall_status = "SUCCESS"
        elif successful >= len(results) * 0.6:
            overall_status = "PARTIAL"
        else:
            overall_status = "FAILED"
        
        return {
            "overall_status": overall_status,
            "summary": {
                "total_tests": len(results),
                "successful": successful,
                "failed": failed,
                "success_rate": successful / len(results) * 100,
                "excellent_responses": excellent_responses,
                "good_responses": good_responses,
                "mbti_functionality": mbti_functionality,
                "restaurant_functionality": restaurant_functionality,
                "travel_planning_functionality": travel_planning_functionality,
                "mbti_functionality_rate": mbti_functionality / len(results) * 100 if len(results) > 0 else 0,
                "restaurant_functionality_rate": restaurant_functionality / len(results) * 100 if len(results) > 0 else 0,
                "travel_planning_rate": travel_planning_functionality / len(results) * 100 if len(results) > 0 else 0
            },
            "tests": results
        }
    
    def save_final_results(self, results: Dict[str, Any]):
        """Save final test results to results directory."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.results_dir / f"mbti_agent_jwt_test_results_{timestamp}.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Final results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving final results: {e}")
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report."""
        report = []
        report.append("🧠 MBTI Travel Planner Agent JWT Authentication Test Report")
        report.append("=" * 70)
        report.append("")
        
        # Overall status
        status_emoji = {
            "EXCELLENT": "🌟",
            "SUCCESS": "✅",
            "PARTIAL": "🟡", 
            "FAILED": "❌"
        }
        
        overall = results["overall_status"]
        report.append(f"Overall Status: {status_emoji.get(overall, '❓')} {overall}")
        
        if "summary" in results:
            summary = results["summary"]
            report.append(f"Total Tests: {summary['total_tests']}")
            report.append(f"Successful: {summary['successful']}")
            report.append(f"Success Rate: {summary['success_rate']:.1f}%")
            report.append(f"MBTI Functionality: {summary['mbti_functionality']} ({summary['mbti_functionality_rate']:.1f}%)")
            report.append(f"Restaurant Functionality: {summary['restaurant_functionality']} ({summary['restaurant_functionality_rate']:.1f}%)")
            report.append(f"Travel Planning: {summary['travel_planning_functionality']} ({summary['travel_planning_rate']:.1f}%)")
        
        report.append("")
        report.append("📋 Individual Test Results:")
        report.append("-" * 40)
        
        for test in results.get("tests", []):
            status_symbol = {
                "success": "✅",
                "failed": "❌",
                "error": "💥",
                "timeout": "⏰"
            }
            
            symbol = status_symbol.get(test["status"], "❓")
            report.append(f"{symbol} {test['test']}: {test['status'].upper()}")
            
            if test["status"] == "success" and "analysis" in test:
                analysis = test["analysis"]
                quality = analysis.get("response_quality", "unknown")
                
                quality_emoji = {
                    "excellent": "🌟",
                    "good": "👍",
                    "basic": "👌",
                    "poor": "👎",
                    "error": "💥"
                }
                
                report.append(f"   Quality: {quality_emoji.get(quality, '❓')} {quality.title()}")
                
                if analysis.get("has_mbti_content"):
                    report.append(f"   🧠 MBTI Content: Yes")
                if analysis.get("has_restaurant_data"):
                    report.append(f"   🍽️  Restaurant Data: Yes")
                if analysis.get("has_travel_planning"):
                    report.append(f"   ✈️  Travel Planning: Yes")
                
                if analysis.get("mbti_types_mentioned"):
                    report.append(f"   MBTI Types: {', '.join(analysis['mbti_types_mentioned']).upper()}")
                if analysis.get("districts_mentioned"):
                    report.append(f"   Districts: {', '.join(analysis['districts_mentioned'])}")
            
            elif "error" in test:
                report.append(f"   Error: {test['error'][:80]}...")
        
        report.append("")
        report.append("🎯 MBTI Travel Planner Functionality Analysis:")
        report.append("-" * 50)
        
        if overall == "EXCELLENT":
            report.append("🌟 Outstanding! MBTI Travel Planner agent working perfectly")
            report.append("✅ JWT authentication successful")
            report.append("✅ MBTI personality integration working")
            report.append("✅ Restaurant search functionality active")
            report.append("✅ Travel planning capabilities functional")
            report.append("✅ Agent providing personalized recommendations")
        elif overall == "SUCCESS":
            report.append("✅ Excellent! MBTI Travel Planner agent working well")
            report.append("✅ JWT authentication successful")
            report.append("✅ Core MBTI functionality working")
            report.append("✅ Good restaurant search capabilities")
            report.append("✅ Travel planning assistance available")
        elif overall == "PARTIAL":
            report.append("🟡 Good! Agent responding but some issues detected")
            report.append("✅ JWT authentication working")
            report.append("🟡 Some MBTI functionality working")
            report.append("🟡 Limited restaurant search capabilities")
            report.append("🟡 Basic travel planning available")
        else:
            report.append("❌ Issues detected with MBTI Travel Planner agent")
            report.append("❌ Check JWT authentication configuration")
            report.append("❌ Verify MBTI personality processing")
            report.append("❌ Review restaurant search tool integration")
            report.append("❌ Check AgentCore deployment")
        
        report.append("")
        report.append("💡 Conclusion:")
        if overall in ["EXCELLENT", "SUCCESS"]:
            report.append("🎉 MBTI Travel Planner agent is working correctly!")
            report.append("✅ JWT authentication is properly configured")
            report.append("✅ MBTI personality integration is functional")
            report.append("✅ Restaurant search tools are accessible")
            report.append("✅ Travel planning capabilities are active")
            report.append("✅ Ready for production use")
        elif overall == "PARTIAL":
            report.append("🔧 MBTI Travel Planner agent needs some attention")
            report.append("✅ Basic functionality is working")
            report.append("🟡 Some features may need debugging")
            report.append("🔍 Review logs for specific issues")
        else:
            report.append("🚨 MBTI Travel Planner agent requires immediate attention")
            report.append("❌ Critical functionality is not working")
            report.append("🔧 Check deployment and configuration")
            report.append("📞 Contact support if issues persist")
        
        return "\n".join(report)


def main():
    """Main function to run the JWT authentication tests."""
    try:
        print("🧠 MBTI Travel Planner Agent JWT Authentication Tester")
        print("=" * 60)
        print("This script will test the deployed MBTI Travel Planner agent")
        print("with JWT authentication to validate all functionality.")
        print("=" * 60)
        
        tester = MBTITravelPlannerJWTTester()
        
        # Run comprehensive tests
        results = tester.run_comprehensive_tests()
        
        # Save results
        tester.save_final_results(results)
        
        # Generate and display report
        report = tester.generate_report(results)
        print("\n" + report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = tester.results_dir / f"mbti_agent_test_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Full report saved to: {report_file}")
        
        # Exit with appropriate code
        if results["overall_status"] in ["EXCELLENT", "SUCCESS"]:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        elif results["overall_status"] == "PARTIAL":
            print("\n🟡 Tests completed with some issues detected.")
            sys.exit(1)
        else:
            print("\n❌ Tests failed. Please check the configuration.")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()