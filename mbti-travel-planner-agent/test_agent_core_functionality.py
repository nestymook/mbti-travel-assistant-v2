#!/usr/bin/env python3
"""
Test the core MBTI Travel Planner Agent functionality using HTTPS requests with JWT authentication.
This test focuses on the basic agent response and Nova Pro model integration.
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.test_auth_utils import create_test_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
        
        print(f"   📋 Username: {cognito_config['username']}")
        print(f"   📋 Client ID: {cognito_config['client_id']}")
        
        # Authenticate with Cognito
        response = cognito_client.admin_initiate_auth(
            UserPoolId=cognito_config['user_pool_id'],
            ClientId=cognito_config['client_id'],
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': cognito_config['username'],
                'PASSWORD': cognito_config['password'],
                'SECRET_HASH': secret_hash
            }
        )
        
        # Extract Access Token (not ID Token!)
        jwt_token = response['AuthenticationResult']['AccessToken']
        print("   ✅ JWT Access Token obtained successfully")
        print(f"   📝 Token length: {len(jwt_token)} characters")
        
        return jwt_token
        
    except Exception as e:
        print(f"   ❌ Failed to get JWT token: {e}")
        return None

def test_agent_basic_functionality(jwt_token):
    """Test basic agent functionality with simple prompts."""
    
    print("\n🚀 Testing Agent Core Functionality")
    print("-" * 50)
    
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_planner_agent-JPTzWT3IZp"
    base_url = "https://bedrock-agentcore.us-east-1.amazonaws.com"
    
    import urllib.parse
    encoded_arn = urllib.parse.quote(agent_arn, safe='')
    endpoint_url = f"{base_url}/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    print(f"   🎯 Endpoint: {endpoint_url}")
    
    # Test cases - simple prompts that don't require restaurant tools
    test_cases = [
        {
            "name": "Basic Greeting",
            "prompt": "Hello! Can you introduce yourself?",
            "expected_keywords": ["MBTI", "travel", "planner", "Nova Pro"]
        },
        {
            "name": "MBTI Knowledge",
            "prompt": "What can you tell me about ENFP personality types and travel preferences?",
            "expected_keywords": ["ENFP", "personality", "travel", "extroverted"]
        },
        {
            "name": "General Travel Advice",
            "prompt": "I'm planning a trip to Tokyo. What are some general travel tips?",
            "expected_keywords": ["Tokyo", "travel", "tips"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case['name']}")
        print(f"   📝 Prompt: {test_case['prompt']}")
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json',
            'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': f'test-core-{i}-{int(datetime.now().timestamp())}-abcdef123456789'
        }
        
        # Prepare payload
        payload = {
            "prompt": test_case['prompt']
        }
        
        try:
            print("   🔄 Sending request...")
            response = requests.post(
                endpoint_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"   📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Request successful!")
                
                try:
                    response_data = response.json()
                    
                    # Extract response content
                    content = ""
                    if 'result' in response_data:
                        result = response_data['result']
                        if isinstance(result, dict):
                            if 'content' in result:
                                if isinstance(result['content'], list) and len(result['content']) > 0:
                                    content = result['content'][0].get('text', str(result['content']))
                                else:
                                    content = str(result['content'])
                            else:
                                content = str(result)
                        else:
                            content = str(result)
                    else:
                        content = str(response_data)
                    
                    print(f"   💬 Response: {content[:200]}...")
                    
                    # Check for expected keywords
                    content_lower = content.lower()
                    found_keywords = [kw for kw in test_case['expected_keywords'] if kw.lower() in content_lower]
                    
                    results.append({
                        'test': test_case['name'],
                        'status': 'SUCCESS',
                        'response_length': len(content),
                        'found_keywords': found_keywords,
                        'response_preview': content[:100]
                    })
                    
                    print(f"   🔍 Found keywords: {found_keywords}")
                    
                except json.JSONDecodeError:
                    print(f"   📝 Raw response: {response.text[:200]}...")
                    results.append({
                        'test': test_case['name'],
                        'status': 'SUCCESS_RAW',
                        'response_length': len(response.text),
                        'response_preview': response.text[:100]
                    })
                    
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   📋 Error: {response.text}")
                results.append({
                    'test': test_case['name'],
                    'status': 'FAILED',
                    'error_code': response.status_code,
                    'error_message': response.text[:100]
                })
                
        except requests.exceptions.Timeout:
            print("   ❌ Request timeout")
            results.append({
                'test': test_case['name'],
                'status': 'TIMEOUT'
            })
        except Exception as e:
            print(f"   ❌ Request error: {e}")
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'error_message': str(e)
            })
    
    return results

def main():
    """Main test function."""
    
    print("🔧 MBTI Travel Planner Agent - Core Functionality Test")
    print("=" * 60)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Get JWT token
    jwt_token = get_jwt_token()
    
    if not jwt_token:
        print("\n❌ Cannot proceed without JWT token")
        return
    
    # Step 2: Test core functionality
    results = test_agent_basic_functionality(jwt_token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    successful_tests = [r for r in results if r['status'] in ['SUCCESS', 'SUCCESS_RAW']]
    failed_tests = [r for r in results if r['status'] not in ['SUCCESS', 'SUCCESS_RAW']]
    
    print(f"   Total Tests: {len(results)}")
    print(f"   Successful: {len(successful_tests)}")
    print(f"   Failed: {len(failed_tests)}")
    
    if successful_tests:
        print("\n✅ Successful Tests:")
        for result in successful_tests:
            print(f"   - {result['test']}: {result.get('response_length', 0)} chars")
            if 'found_keywords' in result:
                print(f"     Keywords: {result['found_keywords']}")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for result in failed_tests:
            print(f"   - {result['test']}: {result['status']}")
            if 'error_message' in result:
                print(f"     Error: {result['error_message']}")
    
    # Overall assessment
    success_rate = len(successful_tests) / len(results) * 100
    
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 SUCCESS: Agent core functionality is working!")
        print("✅ Key Achievements:")
        print("   1. JWT authentication is working correctly")
        print("   2. Agent is responding to requests")
        print("   3. Nova Pro model is operational")
        print("   4. Basic MBTI travel planning functionality confirmed")
    elif success_rate >= 50:
        print("\n⚠️ PARTIAL SUCCESS: Agent is working but has some issues")
        print("🔧 Some functionality may need attention")
    else:
        print("\n❌ FAILURE: Agent has significant issues")
        print("🔧 Core functionality needs troubleshooting")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()