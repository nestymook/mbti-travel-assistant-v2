#!/usr/bin/env python3
"""
Create OpenSearch Serverless Index for Bedrock Knowledge Base
"""

import boto3
import json
import requests
from requests_aws4auth import AWS4Auth

def create_opensearch_index():
    """Create the OpenSearch index for Bedrock Knowledge Base."""
    
    # AWS configuration
    region = 'us-east-1'
    service = 'aoss'
    collection_endpoint = 'https://r481xgx08tn06w6kcc1i.us-east-1.aoss.amazonaws.com'
    index_name = 'bedrock-knowledge-base-default-index'
    
    # Get AWS credentials
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # Create AWS4Auth object
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token
    )
    
    # Index configuration
    index_config = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "text"
                }
            }
        }
    }
    
    # Create the index
    url = f"{collection_endpoint}/{index_name}"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.put(
            url,
            auth=awsauth,
            headers=headers,
            data=json.dumps(index_config),
            timeout=30
        )
        
        print(f"Index creation response: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code in [200, 201]:
            print(f"✅ Successfully created index: {index_name}")
            return True
        else:
            print(f"❌ Failed to create index: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return False

if __name__ == "__main__":
    create_opensearch_index()