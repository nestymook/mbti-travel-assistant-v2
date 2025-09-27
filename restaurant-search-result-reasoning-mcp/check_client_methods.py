#!/usr/bin/env python3
"""
Check available methods on the bedrock-agentcore client.
"""

import boto3

def check_client_methods():
    """Check available methods on the bedrock-agentcore client."""
    
    try:
        client = boto3.client('bedrock-agentcore', region_name='us-east-1')
        
        print("Available methods on bedrock-agentcore client:")
        methods = [method for method in dir(client) if not method.startswith('_')]
        
        for method in sorted(methods):
            print(f"  - {method}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_client_methods()