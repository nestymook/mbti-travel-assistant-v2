# MBTI Knowledge Base Implementation - Step-by-Step Success Guide

**Date:** September 29, 2025  
**Project:** MBTI Travel Assistant with Amazon Nova Pro Parsing  
**Account ID:** 209803798463  
**Region:** us-east-1  
**Final Status:** ✅ COMPLETE SUCCESS

---

## 🎯 **OVERVIEW**

This document provides a complete step-by-step breakdown of successfully implementing an Amazon Bedrock Knowledge Base with:
- **Amazon Nova Pro Foundation Model** for intelligent document parsing
- **No Chunking Strategy** (complete document processing)
- **Amazon Titan Embeddings G1** for vector generation
- **OpenSearch Serverless** with FAISS engine for vector storage
- **183 MBTI tourist attraction documents** processed successfully

---

## 📋 **STEP-BY-STEP IMPLEMENTATION**

### **STEP 1: PERMISSIONS VERIFICATION & ACCOUNT SETUP**

#### **1.1 Verified User Identity and Role**
```bash
aws sts get-caller-identity
```
**✅ Result:**
- **User:** `nestymook`
- **Account:** `209803798463`
- **Role:** `arn:aws:sts::209803798463:assumed-role/AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5/nestymook`

#### **1.2 Confirmed Existing IAM Policies**
```bash
aws iam list-attached-role-policies --role-name AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5
```
**✅ Result - 10 Policies Attached:**
1. `AmazonEC2ContainerRegistryFullAccess`
2. `AmazonSSMFullAccess`
3. `IAMFullAccess`
4. `AmazonSNSFullAccess`
5. `AmazonS3FullAccess`
6. `CloudWatchFullAccessV2`
7. `AmazonBedrockFullAccess` ⭐ (Critical for Knowledge Base)
8. `AmazonDynamoDBFullAccess_v2`
9. `AWSCloudFormationFullAccess`
10. `AWSLambda_FullAccess`

#### **1.3 Tested OpenSearch Permissions**
```bash
# Verified OpenSearch domain access
aws opensearch list-domain-names --region us-east-1

# Verified OpenSearch Serverless access
aws opensearchserverless list-collections --region us-east-1
```
**✅ Result:** Both commands successful - confirmed full OpenSearch permissions

---

### **STEP 2: OPENSEARCH SERVERLESS SECURITY POLICIES**

#### **2.1 Created Encryption Security Policy**
```bash
# Created encryption policy file
cat > encryption_policy.json << EOF
{
    "Rules": [
        {
            "ResourceType": "collection",
            "Resource": ["collection/bedrock-knowledge-base-d2fm65"]
        }
    ],
    "AWSOwnedKey": true
}
EOF

# Applied encryption policy
aws opensearchserverless create-security-policy \
    --name bedrock-kb-encrypt \
    --type encryption \
    --policy file://encryption_policy.json \
    --region us-east-1
```
**✅ Result:**
- **Policy Name:** `bedrock-kb-encrypt`
- **Policy Version:** `MTc1OTE1MDgwMzA3Ml8x`
- **Status:** ACTIVE

#### **2.2 Created Network Security Policy**
```bash
# Created network policy file
cat > network_policy.json << EOF
[
    {
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": ["collection/bedrock-knowledge-base-d2fm65"]
            },
            {
                "ResourceType": "dashboard",
                "Resource": ["collection/bedrock-knowledge-base-d2fm65"]
            }
        ],
        "AllowFromPublic": true
    }
]
EOF

# Applied network policy
aws opensearchserverless create-security-policy \
    --name bedrock-kb-network \
    --type network \
    --policy file://network_policy.json \
    --region us-east-1
```
**✅ Result:**
- **Policy Name:** `bedrock-kb-network`
- **Policy Version:** `MTc1OTE1MDgyMjcwNl8x`
- **Public Access:** Enabled

#### **2.3 Created Initial Data Access Policy**
```bash
# Created data access policy file
cat > data_access_policy.json << EOF
[
    {
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": ["collection/bedrock-knowledge-base-d2fm65"],
                "Permission": [
                    "aoss:CreateCollectionItems",
                    "aoss:DeleteCollectionItems",
                    "aoss:UpdateCollectionItems",
                    "aoss:DescribeCollectionItems"
                ]
            },
            {
                "ResourceType": "index",
                "Resource": ["index/bedrock-knowledge-base-d2fm65/*"],
                "Permission": [
                    "aoss:CreateIndex",
                    "aoss:DeleteIndex",
                    "aoss:UpdateIndex",
                    "aoss:DescribeIndex",
                    "aoss:ReadDocument",
                    "aoss:WriteDocument"
                ]
            }
        ],
        "Principal": ["arn:aws:sts::209803798463:assumed-role/AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5/nestymook"]
    }
]
EOF

# Applied data access policy
aws opensearchserverless create-access-policy \
    --name bedrock-kb-access \
    --type data \
    --policy file://data_access_policy.json \
    --region us-east-1
```
**✅ Result:**
- **Policy Name:** `bedrock-kb-access`
- **Policy Version:** `MTc1OTE1MDg0NDYwN18x`
- **Permissions:** Full CRUD access for user

---

### **STEP 3: OPENSEARCH SERVERLESS COLLECTION CREATION**

#### **3.1 Created Vector Search Collection**
```bash
aws opensearchserverless create-collection \
    --name bedrock-knowledge-base-d2fm65 \
    --type VECTORSEARCH \
    --region us-east-1
```
**✅ Result:**
- **Collection Name:** `bedrock-knowledge-base-d2fm65`
- **Collection ID:** `r481xgx08tn06w6kcc1i`
- **Type:** VECTORSEARCH
- **ARN:** `arn:aws:aoss:us-east-1:209803798463:collection/r481xgx08tn06w6kcc1i`
- **Endpoint:** `https://r481xgx08tn06w6kcc1i.us-east-1.aoss.amazonaws.com`
- **Status:** ACTIVE

---

### **STEP 4: IAM SERVICE ROLE FOR BEDROCK KNOWLEDGE BASE**

#### **4.1 Created Bedrock Service Role**
```bash
# Created trust policy for Bedrock service
cat > kb_trust_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Created the service role
aws iam create-role \
    --role-name MBTIKnowledgeBaseRole-NovaProParsing \
    --assume-role-policy-document file://kb_trust_policy.json \
    --description "Service role for MBTI Knowledge Base with Nova Pro parsing"
```
**✅ Result:**
- **Role Name:** `MBTIKnowledgeBaseRole-NovaProParsing`
- **Role ARN:** `arn:aws:iam::209803798463:role/MBTIKnowledgeBaseRole-NovaProParsing`
- **Role ID:** `AROATBWKH4675UTI5IVLD`

#### **4.2 Attached S3 Access Policy to Service Role**
```bash
# Created S3 access policy
cat > kb_s3_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
                "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1/*"
            ]
        }
    ]
}
EOF

# Attached S3 policy to role
aws iam put-role-policy \
    --role-name MBTIKnowledgeBaseRole-NovaProParsing \
    --policy-name S3AccessPolicy \
    --policy-document file://kb_s3_policy.json
```
**✅ Result:** S3 access policy successfully attached

#### **4.3 Attached OpenSearch Access Policy to Service Role**
```bash
# Created OpenSearch access policy
cat > kb_opensearch_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "aoss:APIAccessAll"
            ],
            "Resource": "arn:aws:aoss:us-east-1:209803798463:collection/r481xgx08tn06w6kcc1i"
        }
    ]
}
EOF

# Attached OpenSearch policy to role
aws iam put-role-policy \
    --role-name MBTIKnowledgeBaseRole-NovaProParsing \
    --policy-name OpenSearchAccessPolicy \
    --policy-document file://kb_opensearch_policy.json
```
**✅ Result:** OpenSearch access policy successfully attached

#### **4.4 Attached Bedrock Model Access Policy to Service Role**
```bash
# Created Bedrock model access policy
cat > kb_bedrock_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
            ]
        }
    ]
}
EOF

# Attached Bedrock policy to role
aws iam put-role-policy \
    --role-name MBTIKnowledgeBaseRole-NovaProParsing \
    --policy-name BedrockModelAccessPolicy \
    --policy-document file://kb_bedrock_policy.json
```
**✅ Result:** Bedrock model access policy successfully attached

#### **4.5 Updated OpenSearch Data Access Policy to Include Service Role**
```bash
# Updated data access policy to include service role
cat > updated_data_access_policy.json << EOF
[
    {
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": ["collection/bedrock-knowledge-base-d2fm65"],
                "Permission": [
                    "aoss:CreateCollectionItems",
                    "aoss:DeleteCollectionItems",
                    "aoss:UpdateCollectionItems",
                    "aoss:DescribeCollectionItems"
                ]
            },
            {
                "ResourceType": "index",
                "Resource": ["index/bedrock-knowledge-base-d2fm65/*"],
                "Permission": [
                    "aoss:CreateIndex",
                    "aoss:DeleteIndex",
                    "aoss:UpdateIndex",
                    "aoss:DescribeIndex",
                    "aoss:ReadDocument",
                    "aoss:WriteDocument"
                ]
            }
        ],
        "Principal": [
            "arn:aws:sts::209803798463:assumed-role/AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5/nestymook",
            "arn:aws:iam::209803798463:role/MBTIKnowledgeBaseRole-NovaProParsing"
        ]
    }
]
EOF

# Updated the access policy
aws opensearchserverless update-access-policy \
    --name bedrock-kb-access \
    --type data \
    --policy-version "MTc1OTE1MDg0NDYwN18x" \
    --policy file://updated_data_access_policy.json \
    --region us-east-1
```
**✅ Result:**
- **New Policy Version:** `MTc1OTE1MTQ5NjM4NV8y`
- **Added Principal:** Service role for Bedrock access

---

### **STEP 5: OPENSEARCH INDEX CREATION WITH FAISS ENGINE**

#### **5.1 Installed Required Python Dependencies**
```bash
pip install requests-aws4auth
```
**✅ Result:** AWS authentication library installed successfully

#### **5.2 Created Python Script for Index Creation**
```python
# Created create_opensearch_index_faiss.py
#!/usr/bin/env python3
import boto3
import json
import requests
from requests_aws4auth import AWS4Auth

def create_opensearch_index():
    # AWS credentials and region
    region = 'us-east-1'
    service = 'aoss'
    
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
    
    # OpenSearch Serverless endpoint
    host = 'https://r481xgx08tn06w6kcc1i.us-east-1.aoss.amazonaws.com'
    index_name = 'bedrock-knowledge-base-default-index'
    
    # Index configuration with FAISS engine (required by Bedrock)
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
                    "dimension": 1536,  # Titan embeddings dimension
                    "method": {
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "faiss",  # Required by Bedrock
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
    url = f"{host}/{index_name}"
    headers = {'Content-Type': 'application/json'}
    
    response = requests.put(
        url,
        auth=awsauth,
        headers=headers,
        data=json.dumps(index_config)
    )
    
    print(f"Index creation response: {response.status_code}")
    print(f"Response body: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    success = create_opensearch_index()
    if success:
        print("✅ OpenSearch index created successfully!")
    else:
        print("❌ Failed to create OpenSearch index")
```

#### **5.3 Executed Index Creation Script**
```bash
python create_opensearch_index_faiss.py
```
**✅ Result:**
- **Index Name:** `bedrock-knowledge-base-default-index`
- **Engine:** FAISS (required by Bedrock)
- **Vector Dimension:** 1536 (matches Titan embeddings)
- **Response:** `{"acknowledged":true,"shards_acknowledged":true}`
- **Status Code:** 200 (Success)

---

### **STEP 6: BEDROCK KNOWLEDGE BASE CREATION**

#### **6.1 Created Knowledge Base Configuration Files**
```bash
# Created knowledge base configuration
cat > kb_knowledge_config.json << EOF
{
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
        "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
    }
}
EOF

# Created storage configuration
cat > kb_storage_config_auto.json << EOF
{
    "type": "OPENSEARCH_SERVERLESS",
    "opensearchServerlessConfiguration": {
        "collectionArn": "arn:aws:aoss:us-east-1:209803798463:collection/r481xgx08tn06w6kcc1i",
        "vectorIndexName": "bedrock-knowledge-base-default-index",
        "fieldMapping": {
            "vectorField": "bedrock-knowledge-base-default-vector",
            "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
            "metadataField": "AMAZON_BEDROCK_METADATA"
        }
    }
}
EOF
```

#### **6.2 Created Bedrock Knowledge Base**
```bash
aws bedrock-agent create-knowledge-base \
    --name "MBTI-NovaProParsing-KnowledgeBase" \
    --description "MBTI Knowledge Base with Nova Pro parsing, no chunking, Titan embeddings, and OpenSearch Serverless" \
    --role-arn "arn:aws:iam::209803798463:role/MBTIKnowledgeBaseRole-NovaProParsing" \
    --knowledge-base-configuration file://kb_knowledge_config.json \
    --storage-configuration file://kb_storage_config_auto.json \
    --region us-east-1
```
**✅ Result:**
- **Knowledge Base Name:** `MBTI-NovaProParsing-KnowledgeBase`
- **Knowledge Base ID:** `1FJ1VHU5OW`
- **Knowledge Base ARN:** `arn:aws:bedrock:us-east-1:209803798463:knowledge-base/1FJ1VHU5OW`
- **Embedding Model:** Amazon Titan Embeddings G1
- **Vector Store:** OpenSearch Serverless
- **Status:** CREATING → ACTIVE

---

### **STEP 7: DATA SOURCE CREATION WITH NOVA PRO PARSING**

#### **7.1 Created Data Source Configuration with Nova Pro**
```bash
# Created data source configuration with Nova Pro parsing
cat > data_source_config.json << EOF
{
    "name": "MBTI-S3-NovaProParsing-DataSource",
    "description": "S3 data source with Nova Pro parsing and no chunking",
    "dataSourceConfiguration": {
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1"
        }
    },
    "dataDeletionPolicy": "RETAIN",
    "vectorIngestionConfiguration": {
        "parsingConfiguration": {
            "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
            "bedrockFoundationModelConfiguration": {
                "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0",
                "parsingPrompt": {
                    "parsingPromptText": "Extract and preserve all text content from this document, maintaining the original structure and formatting. Include all MBTI personality information, location details, operating hours, and any metadata present in the document."
                }
            }
        },
        "chunkingConfiguration": {
            "chunkingStrategy": "NONE"
        }
    }
}
EOF
```

#### **7.2 Created Data Source**
```bash
aws bedrock-agent create-data-source \
    --knowledge-base-id "1FJ1VHU5OW" \
    --cli-input-json file://data_source_config.json \
    --region us-east-1
```
**✅ Result:**
- **Data Source Name:** `MBTI-S3-NovaProParsing-DataSource`
- **Data Source ID:** `HBOBHF8WHN`
- **S3 Bucket:** `s3://mbti-knowledgebase-209803798463-us-east-1`
- **Parsing Strategy:** BEDROCK_FOUNDATION_MODEL
- **Parsing Model:** Amazon Nova Pro v1.0
- **Chunking Strategy:** NONE (complete document processing)
- **Status:** AVAILABLE

---

### **STEP 8: INGESTION JOB EXECUTION**

#### **8.1 Started Ingestion Job**
```bash
aws bedrock-agent start-ingestion-job \
    --knowledge-base-id "1FJ1VHU5OW" \
    --data-source-id "HBOBHF8WHN" \
    --region us-east-1
```
**✅ Result:**
- **Ingestion Job ID:** `UN3HTA5OYG`
- **Status:** STARTING → IN_PROGRESS
- **Documents Scanned:** 183
- **Documents to Process:** 183 MBTI tourist attraction files

#### **8.2 Monitored Ingestion Progress**
```bash
aws bedrock-agent get-ingestion-job \
    --knowledge-base-id "1FJ1VHU5OW" \
    --data-source-id "HBOBHF8WHN" \
    --ingestion-job-id "UN3HTA5OYG" \
    --region us-east-1
```
**✅ Result:**
- **Status:** IN_PROGRESS → COMPLETE
- **Documents Scanned:** 183
- **Documents Indexed:** 183
- **Documents Failed:** 0
- **Processing:** All MBTI files successfully processed with Nova Pro

---

## 🎉 **FINAL SUCCESS SUMMARY**

### **✅ All Components Successfully Created:**

| **Component** | **Name/ID** | **Status** | **Key Features** |
|---------------|-------------|------------|------------------|
| **OpenSearch Serverless Collection** | `bedrock-knowledge-base-d2fm65` | ✅ ACTIVE | Vector search, FAISS engine |
| **Collection ID** | `r481xgx08tn06w6kcc1i` | ✅ ACTIVE | Endpoint: `https://r481xgx08tn06w6kcc1i.us-east-1.aoss.amazonaws.com` |
| **Security Policies** | 3 policies | ✅ ACTIVE | Encryption, Network, Data Access |
| **IAM Service Role** | `MBTIKnowledgeBaseRole-NovaProParsing` | ✅ ACTIVE | S3, OpenSearch, Bedrock access |
| **OpenSearch Index** | `bedrock-knowledge-base-default-index` | ✅ ACTIVE | FAISS engine, 1536 dimensions |
| **Bedrock Knowledge Base** | `1FJ1VHU5OW` | ✅ ACTIVE | Titan embeddings, OpenSearch Serverless |
| **Data Source** | `HBOBHF8WHN` | ✅ AVAILABLE | Nova Pro parsing, no chunking |
| **Ingestion Job** | `UN3HTA5OYG` | ✅ COMPLETE | 183/183 documents processed successfully |

### **✅ Key Technical Achievements:**

1. **✅ Amazon Nova Pro Parsing:** Advanced foundation model for intelligent document processing
2. **✅ No Chunking Strategy:** Complete document processing for better context preservation
3. **✅ Titan Embeddings G1:** High-quality 1536-dimension vector embeddings
4. **✅ OpenSearch Serverless:** Scalable, managed vector storage with FAISS engine
5. **✅ Custom Parsing Prompt:** Optimized for MBTI personality and location data extraction
6. **✅ Comprehensive Security:** Proper IAM roles and OpenSearch Serverless policies
7. **✅ 100% Success Rate:** All 183 documents processed without errors

### **✅ Final Resource Information:**

- **Knowledge Base ID:** `1FJ1VHU5OW`
- **Data Source ID:** `HBOBHF8WHN`
- **Collection Endpoint:** `https://r481xgx08tn06w6kcc1i.us-east-1.aoss.amazonaws.com`
- **S3 Bucket:** `s3://mbti-knowledgebase-209803798463-us-east-1`
- **Embedding Model:** `amazon.titan-embed-text-v1`
- **Parsing Model:** `amazon.nova-pro-v1:0`
- **Vector Engine:** FAISS
- **Document Count:** 183 MBTI files

---

## 🔧 **VERIFICATION COMMANDS**

### **Check Knowledge Base Status:**
```bash
aws bedrock-agent get-knowledge-base --knowledge-base-id "1FJ1VHU5OW" --region us-east-1
```

### **Query Knowledge Base:**
```bash
aws bedrock-agent-runtime retrieve \
    --knowledge-base-id "1FJ1VHU5OW" \
    --retrieval-query '{"text": "INFJ personality attractions in Hong Kong"}' \
    --region us-east-1
```

### **Check Ingestion Status:**
```bash
aws bedrock-agent get-ingestion-job \
    --knowledge-base-id "1FJ1VHU5OW" \
    --data-source-id "HBOBHF8WHN" \
    --ingestion-job-id "UN3HTA5OYG" \
    --region us-east-1
```

---

## ✅ **PROJECT STATUS: COMPLETE SUCCESS**

**The MBTI Knowledge Base with Amazon Nova Pro parsing has been successfully implemented and is fully operational!**

All 183 MBTI tourist attraction documents have been processed using Amazon Nova Pro foundation model with no chunking strategy, embedded using Amazon Titan Embeddings G1, and stored in OpenSearch Serverless with FAISS engine for optimal performance.

**🎉 Ready for production use!**