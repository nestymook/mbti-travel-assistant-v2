#!/usr/bin/env python3
"""
JWT Gateway Connectivity Test Script

This script tests the AgentCore gateway connectivity using JWT authentication
to diagnose why the gateway connectivity tests are failing.

Based on the findings:
1. The AgentCore deployment exists but has no authentication configured
2. The gateway hostname cannot be resolved via DNS
3. We need to test both direct AgentCore invocation and HTTP gateway access

This script will:
1. Get JWT token from Cognito
2. Test direct AgentCore invocation with JWT
3. Test HTTP gateway endpoints with JWT
4. Provide detailed diagnostics
"""

import json
import boto3
import getpass
import time
import requests
import socket
import subprocess
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from pathlib import Path


# Configuration from the AgentCore deployment
AGENTCORE_CONFIG = {
    "region": "us-east-1",
    "agent_arn": "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/agentcore_gateway_mcp_tools-UspJsMG7Fi",
    "agent_id": "agentcore_gateway_mcp_tools-UspJsMG7Fi",
    "gateway_hostname": "agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com",
    "cognito": {
        "user_pool_id": "us-east-1_KePRX24Bn",
        "client_id": "1ofgeckef3po4i3us4j1m4chvd",
        "client_secret": "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
        "region": "us-east-1"
    }
}


def get_cognito_jwt_token() -> Optional[str]:
    """
    Authenticate with Cognito and get JWT token.
    Always prompts for credentials securely.
    """
    try:
        print("🔐 Authenticating with Cognito...")
        
        # Prompt for credentials
        username = input("Enter Cognito username (default: test@mbti-travel.com): ").strip()
        if not username:
            username = "test@mbti-travel.com"
        
        password = getpass.getpass(f"Enter password for {username}: ")
        if not password:
            print("❌ Password is required")
            return None
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=AGENTCORE_CONFIG['cognito']['region'])
        
        # Authenticate user
        response = cognito_client.initiate_auth(
            ClientId=AGENTCORE_CONFIG['cognito']['client_id'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Extract JWT token
        access_token = response['AuthenticationResult']['AccessToken']
        print(f"✅ Successfully authenticated with Cognito")
        print(f"🎫 JWT Token length: {len(access_token)}")
        print(f"🎫 JWT Token preview: {access_token[:50]}...")
        
        return access_token
        
    except Exception as e:
        print(f"❌ Failed to authenticate with Cognito: {e}")
        return None


def test_dns_resolution() -> Dict[str, Any]:
    """Test DNS resolution for the gateway hostname."""
    print("🌐 Testing DNS resolution...")
    
    hostname = AGENTCORE_CONFIG['gateway_hostname']
    results = {
        "hostname": hostname,
        "resolved": False,
        "ip_addresses": [],
        "error": None
    }
    
    try:
        # Try to resolve hostname
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        results["resolved"] = True
        results["ip_addresses"] = ip_addresses
        print(f"✅ DNS resolution successful: {hostname} -> {ip_addresses}")
        
    except socket.gaierror as e:
        results["error"] = str(e)
        print(f"❌ DNS resolution failed: {e}")
        
        # Try alternative DNS servers
        print("🔍 Trying alternative DNS resolution methods...")
        
        # Try nslookup
        try:
            result = subprocess.run(['nslookup', hostname], 
                                  capture_output=True, text=True, timeout=10)
            print(f"📋 nslookup output: {result.stdout}")
            if result.stderr:
                print(f"📋 nslookup errors: {result.stderr}")
        except Exception as nslookup_e:
            print(f"⚠️ nslookup failed: {nslookup_e}")
        
        # Try with Google DNS
        try:
            result = subprocess.run(['nslookup', hostname, '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10)
            print(f"📋 nslookup (Google DNS) output: {result.stdout}")
        except Exception as google_dns_e:
            print(f"⚠️ Google DNS nslookup failed: {google_dns_e}")
    
    return results


def test_direct_agentcore_invocation(jwt_token: str) -> Dict[str, Any]:
    """Test direct AgentCore invocation using AWS SDK."""
    print("🚀 Testing direct AgentCore invocation...")
    
    results = {
        "success": False,
        "response": None,
        "error": None,
        "method": "aws_sdk"
    }
    
    try:
        # Create AgentCore client
        agentcore_client = boto3.client('bedrock-agentcore', region_name=AGENTCORE_CONFIG['region'])
        
        # Prepare test payload
        test_payload = {
            "prompt": "Hello! Can you help me find restaurants in Central district?",
            "sessionId": f"test-session-{int(time.time())}",
            "enableTrace": True
        }
        
        print(f"📤 Invoking agent: {AGENTCORE_CONFIG['agent_arn']}")
        print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
        
        # Invoke agent
        response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=AGENTCORE_CONFIG['agent_arn'],
            payload=json.dumps(test_payload).encode('utf-8')
        )
        
        # Parse response
        response_body = response['payload'].read().decode('utf-8')
        response_data = json.loads(response_body)
        
        results["success"] = True
        results["response"] = response_data
        
        print("✅ Direct AgentCore invocation successful!")
        print(f"📥 Response: {json.dumps(response_data, indent=2)[:500]}...")
        
    except Exception as e:
        results["error"] = str(e)
        print(f"❌ Direct AgentCore invocation failed: {e}")
    
    return results


def test_http_gateway_endpoints(jwt_token: str) -> Dict[str, Any]:
    """Test HTTP gateway endpoints with JWT authentication."""
    print("🌐 Testing HTTP gateway endpoints...")
    
    base_url = f"https://{AGENTCORE_CONFIG['gateway_hostname']}"
    
    results = {
        "base_url": base_url,
        "tests": {},
        "overall_success": False
    }
    
    # Test endpoints
    endpoints = {
        "health": "/health",
        "api_health": "/api/health",
        "restaurant_districts": "/api/v1/restaurants/search/district",
        "restaurant_meal_types": "/api/v1/restaurants/search/meal-type",
        "restaurant_combined": "/api/v1/restaurants/search/combined",
        "restaurant_recommend": "/api/v1/restaurants/recommend"
    }
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'MBTI-Travel-Planner-Agent/1.0'
    }
    
    successful_tests = 0
    
    for endpoint_name, endpoint_path in endpoints.items():
        print(f"🔍 Testing {endpoint_name}: {endpoint_path}")
        
        endpoint_url = f"{base_url}{endpoint_path}"
        test_result = {
            "url": endpoint_url,
            "success": False,
            "status_code": None,
            "response": None,
            "error": None,
            "response_time": None
        }
        
        try:
            start_time = time.time()
            
            # Prepare request data based on endpoint
            if endpoint_name == "restaurant_districts":
                data = {"districts": ["Central district"]}
            elif endpoint_name == "restaurant_meal_types":
                data = {"meal_types": ["breakfast"]}
            elif endpoint_name == "restaurant_combined":
                data = {"districts": ["Central district"], "meal_types": ["lunch"]}
            elif endpoint_name == "restaurant_recommend":
                data = {"restaurants": []}
            else:
                data = None
            
            # Make request
            if data:
                response = requests.post(endpoint_url, headers=headers, json=data, timeout=30)
            else:
                response = requests.get(endpoint_url, headers=headers, timeout=30)
            
            end_time = time.time()
            test_result["response_time"] = end_time - start_time
            test_result["status_code"] = response.status_code
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    test_result["response"] = response_data
                    test_result["success"] = True
                    successful_tests += 1
                    print(f"✅ {endpoint_name} successful ({response.status_code})")
                    print(f"📥 Response preview: {str(response_data)[:200]}...")
                except json.JSONDecodeError:
                    test_result["response"] = response.text
                    print(f"⚠️ {endpoint_name} returned non-JSON response")
            else:
                test_result["response"] = response.text
                print(f"❌ {endpoint_name} failed: {response.status_code}")
                print(f"📥 Error response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            test_result["error"] = str(e)
            print(f"❌ {endpoint_name} request failed: {e}")
        except Exception as e:
            test_result["error"] = str(e)
            print(f"❌ {endpoint_name} unexpected error: {e}")
        
        results["tests"][endpoint_name] = test_result
    
    results["overall_success"] = successful_tests > 0
    results["successful_tests"] = successful_tests
    results["total_tests"] = len(endpoints)
    
    return results


def test_agentcore_cli_invocation(jwt_token: str) -> Dict[str, Any]:
    """Test AgentCore CLI invocation with JWT token."""
    print("🔧 Testing AgentCore CLI invocation...")
    
    results = {
        "success": False,
        "response": None,
        "error": None,
        "method": "agentcore_cli"
    }
    
    try:
        # Create test payload
        test_payload = {
            "prompt": "Find restaurants in Central district for breakfast",
            "sessionId": f"cli-test-{int(time.time())}"
        }
        
        # Convert to base64
        import base64
        payload_json = json.dumps(test_payload)
        payload_b64 = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
        
        print(f"📤 CLI Payload: {payload_json}")
        
        # Try to find agentcore CLI
        agentcore_cmd = None
        possible_paths = [
            Path("mbti-travel-planner-agent/.venv/Scripts/agentcore.exe"),
            Path(".venv/Scripts/agentcore.exe"),
            Path(".venv/bin/agentcore"),
            "agentcore"
        ]
        
        for path in possible_paths:
            if isinstance(path, Path) and path.exists():
                agentcore_cmd = str(path)
                break
            elif isinstance(path, str):
                try:
                    subprocess.run([path, "--version"], capture_output=True, check=True)
                    agentcore_cmd = path
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        
        if not agentcore_cmd:
            results["error"] = "AgentCore CLI not found"
            print("❌ AgentCore CLI not found in expected locations")
            return results
        
        print(f"🔧 Using AgentCore CLI: {agentcore_cmd}")
        
        # Invoke with JWT
        cmd = [
            agentcore_cmd,
            "invoke",
            "--bearer-token", jwt_token,
            "--agent", AGENTCORE_CONFIG['agent_id'],
            payload_json  # Use JSON directly, not base64
        ]
        
        print(f"🚀 Running: {' '.join(cmd[:3])} --bearer-token [JWT] --agent {AGENTCORE_CONFIG['agent_id']} [PAYLOAD]")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            results["success"] = True
            results["response"] = result.stdout
            print("✅ AgentCore CLI invocation successful!")
            print(f"📥 Response: {result.stdout[:500]}...")
        else:
            results["error"] = f"CLI failed with code {result.returncode}: {result.stderr}"
            print(f"❌ AgentCore CLI failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        results["error"] = "CLI invocation timed out"
        print("⏰ AgentCore CLI invocation timed out")
    except Exception as e:
        results["error"] = str(e)
        print(f"❌ AgentCore CLI test failed: {e}")
    
    return results


def generate_diagnostic_report(dns_results: Dict[str, Any], 
                             direct_results: Dict[str, Any],
                             http_results: Dict[str, Any],
                             cli_results: Dict[str, Any],
                             jwt_token: str) -> None:
    """Generate comprehensive diagnostic report."""
    
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE GATEWAY CONNECTIVITY DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # Summary
    print("\n🎯 EXECUTIVE SUMMARY:")
    print(f"JWT Authentication:     {'✅ SUCCESS' if jwt_token else '❌ FAILED'}")
    print(f"DNS Resolution:         {'✅ SUCCESS' if dns_results['resolved'] else '❌ FAILED'}")
    print(f"Direct AgentCore:       {'✅ SUCCESS' if direct_results['success'] else '❌ FAILED'}")
    print(f"HTTP Gateway:           {'✅ SUCCESS' if http_results['overall_success'] else '❌ FAILED'}")
    print(f"AgentCore CLI:          {'✅ SUCCESS' if cli_results['success'] else '❌ FAILED'}")
    
    # Detailed findings
    print("\n🔍 DETAILED FINDINGS:")
    
    print("\n1. DNS Resolution Analysis:")
    if dns_results['resolved']:
        print(f"   ✅ Hostname resolves to: {dns_results['ip_addresses']}")
    else:
        print(f"   ❌ DNS resolution failed: {dns_results['error']}")
        print("   🔧 Possible causes:")
        print("      - AgentCore service not deployed or stopped")
        print("      - Incorrect hostname configuration")
        print("      - DNS propagation issues")
        print("      - Network connectivity problems")
    
    print("\n2. Direct AgentCore Invocation:")
    if direct_results['success']:
        print("   ✅ Direct AWS SDK invocation successful")
        print("   💡 This confirms the AgentCore runtime is deployed and accessible")
    else:
        print(f"   ❌ Direct invocation failed: {direct_results['error']}")
        print("   🔧 Possible causes:")
        print("      - AgentCore runtime not deployed")
        print("      - Incorrect ARN configuration")
        print("      - AWS permissions issues")
        print("      - Authentication problems")
    
    print("\n3. HTTP Gateway Analysis:")
    if http_results['overall_success']:
        print(f"   ✅ {http_results['successful_tests']}/{http_results['total_tests']} endpoints accessible")
        for endpoint, result in http_results['tests'].items():
            status = "✅" if result['success'] else "❌"
            print(f"      {status} {endpoint}: {result.get('status_code', 'N/A')}")
    else:
        print("   ❌ All HTTP gateway endpoints failed")
        print("   🔧 This is expected if DNS resolution fails")
        
        # Show specific errors
        for endpoint, result in http_results['tests'].items():
            if result['error']:
                print(f"      ❌ {endpoint}: {result['error']}")
    
    print("\n4. AgentCore CLI Analysis:")
    if cli_results['success']:
        print("   ✅ CLI invocation successful with JWT")
    else:
        print(f"   ❌ CLI invocation failed: {cli_results['error']}")
    
    # Root cause analysis
    print("\n🎯 ROOT CAUSE ANALYSIS:")
    
    if not dns_results['resolved']:
        print("\n🚨 PRIMARY ISSUE: DNS Resolution Failure")
        print("The AgentCore gateway hostname cannot be resolved, which indicates:")
        print("1. The AgentCore HTTP gateway may not be properly deployed")
        print("2. The service might be configured for internal access only")
        print("3. The hostname might be incorrect or the service stopped")
        
        if direct_results['success']:
            print("\n✅ POSITIVE FINDING: Direct AgentCore Access Works")
            print("Since direct AgentCore invocation works, the issue is specifically")
            print("with the HTTP gateway layer, not the underlying AgentCore runtime.")
        
    elif not http_results['overall_success']:
        print("\n🚨 PRIMARY ISSUE: HTTP Gateway Configuration")
        print("DNS resolves but HTTP endpoints are not accessible, indicating:")
        print("1. Service is running but not configured for HTTP access")
        print("2. Authentication/authorization issues")
        print("3. Firewall or security group restrictions")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not dns_results['resolved']:
        print("\n🔧 DNS Resolution Fixes:")
        print("1. Verify AgentCore deployment status:")
        print("   aws bedrock-agentcore list-agent-runtimes --region us-east-1")
        print("2. Check if HTTP gateway is enabled in AgentCore configuration")
        print("3. Verify the .bedrock_agentcore.yaml has correct network settings")
        print("4. Ensure 'server_protocol: HTTP' is configured")
        
    if direct_results['success']:
        print("\n✅ Direct Access Workaround:")
        print("Since direct AgentCore access works, you can:")
        print("1. Use AWS SDK boto3 for AgentCore invocation")
        print("2. Implement JWT authentication for direct calls")
        print("3. Bypass the HTTP gateway layer temporarily")
        
    print("\n🔄 Next Steps:")
    print("1. Check AgentCore deployment configuration")
    print("2. Verify HTTP gateway is enabled and properly configured")
    print("3. Test with direct AgentCore invocation as a workaround")
    print("4. Contact AWS support if the issue persists")
    
    # Save diagnostic report
    report = {
        "timestamp": time.time(),
        "summary": {
            "jwt_authentication": jwt_token is not None,
            "dns_resolution": dns_results['resolved'],
            "direct_agentcore": direct_results['success'],
            "http_gateway": http_results['overall_success'],
            "agentcore_cli": cli_results['success']
        },
        "details": {
            "dns_results": dns_results,
            "direct_results": direct_results,
            "http_results": http_results,
            "cli_results": cli_results
        },
        "configuration": AGENTCORE_CONFIG
    }
    
    report_file = Path("gateway_jwt_connectivity_diagnostic_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Diagnostic report saved to: {report_file}")


def main():
    """Main test function."""
    
    print("🚀 JWT Gateway Connectivity Diagnostic Test")
    print("=" * 80)
    print("This script will comprehensively test JWT authentication and gateway connectivity")
    print("to diagnose why the gateway connectivity tests are failing.")
    print("=" * 80)
    
    # Step 1: Get JWT token
    print("\n🔐 Step 1: JWT Authentication")
    jwt_token = get_cognito_jwt_token()
    if not jwt_token:
        print("❌ Cannot proceed without JWT token")
        return False
    
    # Step 2: Test DNS resolution
    print("\n🌐 Step 2: DNS Resolution Test")
    dns_results = test_dns_resolution()
    
    # Step 3: Test direct AgentCore invocation
    print("\n🚀 Step 3: Direct AgentCore Invocation Test")
    direct_results = test_direct_agentcore_invocation(jwt_token)
    
    # Step 4: Test HTTP gateway endpoints
    print("\n🌐 Step 4: HTTP Gateway Endpoints Test")
    http_results = test_http_gateway_endpoints(jwt_token)
    
    # Step 5: Test AgentCore CLI
    print("\n🔧 Step 5: AgentCore CLI Test")
    cli_results = test_agentcore_cli_invocation(jwt_token)
    
    # Step 6: Generate diagnostic report
    print("\n📊 Step 6: Generating Diagnostic Report")
    generate_diagnostic_report(dns_results, direct_results, http_results, cli_results, jwt_token)
    
    # Determine overall success
    overall_success = any([
        direct_results['success'],
        http_results['overall_success'],
        cli_results['success']
    ])
    
    print("\n" + "=" * 80)
    if overall_success:
        print("🎉 PARTIAL SUCCESS - Some connectivity methods work!")
        print("Check the diagnostic report for detailed findings and recommendations.")
    else:
        print("❌ ALL CONNECTIVITY TESTS FAILED")
        print("Check the diagnostic report for troubleshooting guidance.")
    print("=" * 80)
    
    return overall_success


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)