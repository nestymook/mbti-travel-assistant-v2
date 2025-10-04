#!/usr/bin/env python3
"""
Direct AgentCore Runtime Test

Test the deployed AgentCore Runtime directly to verify it's working.
"""

import asyncio
import httpx
import json
import getpass
import boto3
from typing import Dict, Any

async def test_runtime_direct():
    """Test the AgentCore Runtime directly."""
    
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
    
    # Test endpoints
    base_url = "https://bedrock-agentcore.us-east-1.amazonaws.com/runtime/main-DUQgnrHqCl"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Test 1: Root endpoint (should work without auth)
        print("\n🔍 Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"Root endpoint: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Root endpoint error: {e}")
        
        # Test 2: Health endpoint
        print("\n🔍 Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health", headers=headers)
            print(f"Health endpoint: {response.status_code}")
            if response.status_code == 200:
                print(f"Health: {response.json()}")
        except Exception as e:
            print(f"Health endpoint error: {e}")
        
        # Test 3: Auth test endpoint
        print("\n🔍 Testing auth endpoint...")
        try:
            response = await client.get(f"{base_url}/auth/test", headers=headers)
            print(f"Auth test: {response.status_code}")
            if response.status_code == 200:
                print(f"Auth response: {response.json()}")
        except Exception as e:
            print(f"Auth test error: {e}")
        
        # Test 4: Restaurant search
        print("\n🔍 Testing restaurant search...")
        try:
            payload = {"districts": ["Central district"]}
            response = await client.post(
                f"{base_url}/api/v1/restaurants/search/district",
                json=payload,
                headers=headers
            )
            print(f"Restaurant search: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Found {len(data.get('restaurants', []))} restaurants")
            else:
                print(f"Error response: {response.text}")
        except Exception as e:
            print(f"Restaurant search error: {e}")

if __name__ == "__main__":
    asyncio.run(test_runtime_direct())