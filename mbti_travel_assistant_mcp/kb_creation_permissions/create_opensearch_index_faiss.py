#!/usr/bin/env python3
"""
Create OpenSearch Serverless Index for Bedrock Knowledge Base with FAISS engine
"""

import boto3
import json
import requests
from requests_aws4auth import AWS4Auth

def delete_and_create_index():
    """Delete existing index and create new one with FAISS engine."""
    
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
    
    # Delete existing index
    delete_url = f"{collection_endpoint}/{index_name}"
    try:
        delete_response = requests.delete(delete_url, auth=awsauth, timeout=30)
        print(f"Delete response: {delete_response.status_code}")
    except Exception as e:
        print(f"Delete error (may not exist): {e}")
    
    # Index configuration with FAISS engine
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
                        "engine": "faiss",
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
            print(f"✅ Successfully created index with FAISS engine: {index_name}")
            return True
        else:
            print(f"❌ Failed to create index: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return False

if __name__ == "__main__":
    delete_and_create_index()