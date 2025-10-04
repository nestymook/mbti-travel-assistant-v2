#!/usr/bin/env python3
"""
Test JWT Authentication for Restaurant Search MCP Agent

This script tests the restaurant-search-mcp agent with JWT authentication
to identify any issues with invocation or tool usage.
"""

import json
import subprocess
import sys
import logging
import tempfile
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RestaurantMCPJWTTester:
    """JWT authentication tester for Restaurant Search MCP agent."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.jwt_token_file = Path("../mbti-travel-planner-agent/fresh_jwt.txt")
        
        # Create test directories
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
        
    def load_jwt_token(self) -> str:
        """Load JWT token from file."""
        try:
            if self.jwt_token_file.exists():
                token = self.jwt_token_file.read_text().strip()
                if token and len(token) > 100:
                    logger.info("✅ JWT token loaded successfully")
                    return token
            
            logger.error("❌ No valid JWT token found")
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
        """Analyze the agent response for restaurant functionality."""
        try:
            analysis = {
                'test_name': test_name,
                'response_length': len(response_text),
                'has_json_structure': False,
                'has_restaurant_data': False,
                'has_tool_usage': False,
                'is_error_response': False,
                'restaurant_count': 0,
                'tools_used': [],
                'districts_mentioned': [],
                'meal_types_mentioned': [],
                'response_quality': 'unknown'
            }
            
            response_lower = response_text.lower()
            
            # Check for JSON structure
            if '{' in response_text and '}' in response_text:
                analysis['has_json_structure'] = True
                
                # Try to parse JSON response
                try:
                    # Look for JSON in the response
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_part = response_text[start_idx:end_idx]
                        parsed_response = json.loads(json_part)
                        
                        # Analyze parsed JSON
                        if 'success' in parsed_response:
                            analysis['is_error_response'] = not parsed_response['success']
                        
                        if 'restaurants' in parsed_response:
                            analysis['has_restaurant_data'] = True
                            if isinstance(parsed_response['restaurants'], list):
                                analysis['restaurant_count'] = len(parsed_response['restaurants'])
                        
                        if 'query_type' in parsed_response:
                            analysis['has_tool_usage'] = True
                            query_type = parsed_response['query_type']
                            if 'district' in query_type:
                                analysis['tools_used'].append('search_restaurants_by_district')
                            elif 'meal_type' in query_type:
                                analysis['tools_used'].append('search_restaurants_by_meal_type')
                            elif 'combined' in query_type:
                                analysis['tools_used'].append('search_restaurants_combined')
                        
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from response in {test_name}")
            
            # Check for restaurant-related keywords
            restaurant_keywords = [
                'restaurant', 'dining', 'food', 'cuisine', 'menu',
                'central district', 'admiralty', 'causeway bay', 'tsim sha tsui',
                'breakfast', 'lunch', 'dinner', 'dim sum', 'cantonese'
            ]
            
            found_keywords = [kw for kw in restaurant_keywords if kw in response_lower]
            
            # Check for districts mentioned
            districts = ['central district', 'admiralty', 'causeway bay', 'tsim sha tsui', 
                        'wan chai', 'mong kok', 'sha tin', 'tsuen wan']
            analysis['districts_mentioned'] = [d for d in districts if d in response_lower]
            
            # Check for meal types mentioned
            meal_types = ['breakfast', 'lunch', 'dinner', 'brunch']
            analysis['meal_types_mentioned'] = [m for m in meal_types if m in response_lower]
            
            # Determine response quality
            if analysis['has_restaurant_data'] and analysis['restaurant_count'] > 0:
                analysis['response_quality'] = 'excellent'
            elif analysis['has_tool_usage'] and not analysis['is_error_response']:
                analysis['response_quality'] = 'good'
            elif len(found_keywords) > 3:
                analysis['response_quality'] = 'basic'
            elif analysis['is_error_response']:
                analysis['response_quality'] = 'error'
            else:
                analysis['response_quality'] = 'poor'
            
            analysis['keywords_found'] = found_keywords
            analysis['keyword_count'] = len(found_keywords)
            
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
                # Use the configured agent name
                agent_name = "restaurant_search_conversational_agent"
                
                # Execute agentcore invoke
                cmd = [
                    "agentcore", "invoke",
                    "--agent", agent_name,
                    "--bearer-token", token,
                    f"@{temp_file}"
                ]
                
                logger.info("🔄 Invoking restaurant search agent...")
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
                    logger.info(f"Restaurant count: {analysis.get('restaurant_count', 0)}")
                    logger.info(f"Tools used: {analysis.get('tools_used', [])}")
                    
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
        """Run comprehensive tests of the restaurant search agent."""
        logger.info("🚀 Starting Restaurant Search MCP JWT Authentication Tests")
        logger.info("=" * 60)
        
        # Test cases covering different functionality
        test_cases = [
            {
                "name": "Basic Restaurant Search",
                "prompt": "Find restaurants in Hong Kong"
            },
            {
                "name": "District Specific Search",
                "prompt": "Show me restaurants in Central district"
            },
            {
                "name": "Meal Type Search",
                "prompt": "I want breakfast restaurants in Hong Kong"
            },
            {
                "name": "Combined Search",
                "prompt": "Find dinner restaurants in Tsim Sha Tsui"
            },
            {
                "name": "Multiple Districts",
                "prompt": "What restaurants are in Central district and Admiralty?"
            },
            {
                "name": "Specific Cuisine Query",
                "prompt": "Where can I find dim sum restaurants in Causeway Bay?"
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
        
        tool_usage_success = sum(
            1 for r in results 
            if r["status"] == "success" and r.get("analysis", {}).get("has_tool_usage", False)
        )
        
        restaurant_data_success = sum(
            1 for r in results 
            if r["status"] == "success" and r.get("analysis", {}).get("has_restaurant_data", False)
        )
        
        # Determine overall status
        if excellent_responses >= len(results) * 0.7:
            overall_status = "EXCELLENT"
        elif successful >= len(results) * 0.8 and tool_usage_success >= len(results) * 0.6:
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
                "tool_usage_success": tool_usage_success,
                "restaurant_data_success": restaurant_data_success,
                "tool_usage_rate": tool_usage_success / len(results) * 100 if len(results) > 0 else 0,
                "restaurant_data_rate": restaurant_data_success / len(results) * 100 if len(results) > 0 else 0
            },
            "tests": results
        }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report."""
        report = []
        report.append("🍽️  Restaurant Search MCP JWT Authentication Test Report")
        report.append("=" * 60)
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
            report.append(f"Tool Usage Success: {summary['tool_usage_success']}")
            report.append(f"Tool Usage Rate: {summary['tool_usage_rate']:.1f}%")
            report.append(f"Restaurant Data Success: {summary['restaurant_data_success']}")
            report.append(f"Restaurant Data Rate: {summary['restaurant_data_rate']:.1f}%")
        
        report.append("")
        report.append("📋 Individual Test Results:")
        report.append("-" * 30)
        
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
                restaurant_count = analysis.get("restaurant_count", 0)
                tools_used = analysis.get("tools_used", [])
                
                quality_emoji = {
                    "excellent": "🌟",
                    "good": "👍",
                    "basic": "👌",
                    "poor": "👎",
                    "error": "💥"
                }
                
                report.append(f"   Quality: {quality_emoji.get(quality, '❓')} {quality.title()}")
                report.append(f"   Restaurants Found: {restaurant_count}")
                if tools_used:
                    report.append(f"   Tools Used: {', '.join(tools_used)}")
            
            elif "error" in test:
                report.append(f"   Error: {test['error'][:80]}...")
        
        report.append("")
        report.append("🎯 Restaurant MCP Functionality Analysis:")
        report.append("-" * 40)
        
        if overall == "EXCELLENT":
            report.append("🌟 Outstanding! Restaurant MCP agent working perfectly")
            report.append("✅ JWT authentication successful")
            report.append("✅ MCP tools functioning correctly")
            report.append("✅ Restaurant data retrieval working")
            report.append("✅ Agent providing detailed restaurant information")
        elif overall == "SUCCESS":
            report.append("✅ Excellent! Restaurant MCP agent working well")
            report.append("✅ JWT authentication successful")
            report.append("✅ MCP tools mostly functional")
            report.append("✅ Good restaurant search capabilities")
        elif overall == "PARTIAL":
            report.append("🟡 Good! Agent responding but some issues detected")
            report.append("✅ JWT authentication working")
            report.append("🟡 Some MCP tool functionality working")
            report.append("🟡 Limited restaurant data retrieval")
        else:
            report.append("❌ Issues detected with Restaurant MCP agent")
            report.append("❌ Check JWT authentication configuration")
            report.append("❌ Verify MCP tool deployment")
            report.append("❌ Review agent configuration")
        
        report.append("")
        report.append("💡 Conclusion:")
        if overall in ["EXCELLENT", "SUCCESS"]:
            report.append("🎉 Restaurant Search MCP agent is working correctly!")
            report.append("✅ JWT authentication is properly configured")
            report.append("✅ MCP tools are accessible and functional")
            report.append("✅ Agent can search and return restaurant data")
            report.append("✅ Ready for production use")
        else:
            report.append("⚠️  Restaurant Search MCP agent needs attention")
            report.append("- Verify agent deployment status")
            report.append("- Check JWT token validity and configuration")
            report.append("- Test MCP tool endpoints directly")
            report.append("- Review agent logs for errors")
        
        return "\n".join(report)


def main():
    """Main test execution function."""
    tester = RestaurantMCPJWTTester()
    
    try:
        # Run comprehensive tests
        results = tester.run_comprehensive_tests()
        
        # Generate and display report
        report = tester.generate_report(results)
        print(report)
        
        # Save results to file
        results_file = Path("restaurant_mcp_jwt_test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Test results saved to: {results_file}")
        
        # Save report
        report_file = Path("restaurant_mcp_jwt_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Test report saved to: {report_file}")
        
        # Return appropriate exit code
        overall_status = results.get("overall_status", "FAILED")
        return 0 if overall_status in ["EXCELLENT", "SUCCESS"] else 1
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())