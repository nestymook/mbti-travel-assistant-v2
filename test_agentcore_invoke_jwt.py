#!/usr/bin/env python3
"""
AgentCore Runtime Invoke Test with JWT Authentication

Test the AgentCore Runtime using the proper invoke endpoint with JWT authentication.
"""

import asyncio
import httpx
import json
import getpass
import boto3
from typing import Dict, Any

async def test_agentcore_invoke():
    """Test AgentCore Runtime using the invoke endpoint with JWT."""
    
    # Get JWT token
    print("🔐 Getting JWT token...")
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    username = input("Enter username (default: test@mbti-travel.com): ").strip()
    if not username:
        username = "test@mbti-travel.com"
    
    password = getpass.getpass(f"Enter password for {username}: ")
    
    try:
        response = cognito_client.initiate_auth(
            ClientId="1ofgeckef3po4i3us4j1m4chvd",
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        print("✅ JWT authentication successful")
        
    except Exception as e:
        print(f"❌ JWT authentication failed: {e}")
        return
    
    # Test AgentCore invoke endpoint
    invoke_url = "https://bedrock-agentcore.us-east-1.amazonaws.com/runtime/main-DUQgnrHqCl/invocations"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Test different prompts
    test_prompts = [
        "Hello, can you help me search for restaurants?",
        "Search for restaurants in Central district",
        "Find restaurants that serve breakfast",
        "What restaurant tools do you have available?"
    ]
    
    async with httpx.AsyncClient(timeout=60) as client:
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🔍 Test {i}: {prompt}")
            
            try:
                payload = {
                    "prompt": prompt,
                    "sessionId": f"test-session-{i}",
                    "enableTrace": True
                }
                
                response = await client.post(invoke_url, json=payload, headers=headers)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)[:500]}...")
                else:
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"Request error: {e}")
            
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_agentcore_invoke())