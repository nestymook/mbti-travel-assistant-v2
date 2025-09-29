# OpenSearch Knowledge Base Testing Guide

This guide provides comprehensive instructions for testing the Amazon Bedrock Knowledge Base with OpenSearch Serverless vector storage for the MBTI Travel Assistant.

## 📋 **Knowledge Base Configuration**

### **Current Setup**
- **Knowledge Base ID**: `1FJ1VHU5OW`
- **Name**: `MBTI-Travel-Assistant-KB`
- **Vector Storage**: OpenSearch Serverless
- **Embedding Model**: `amazon.titan-embed-text-v2:0`
- **AWS Region**: `us-east-1`
- **Data Source**: S3 Bucket with MBTI-categorized tourist attractions

### **Data Structure**
```
s3://mbti-knowledgebase-209803798463-us-east-1/
├── hong_kong_island/
│   ├── admiralty/
│   ├── causeway_bay/
│   ├── central_district/
│   ├── mid_levels/
│   ├── sheung_wan/
│   ├── the_peak/
│   └── wan_chai/
├── kowloon/
│   ├── tsim_sha_tsui/
│   ├── wong_tai_sin/
│   └── yau_ma_tei/
├── new_territories/
│   └── sha_tin/
└── islands/
    └── lantau/
```

Each directory contains MBTI-prefixed markdown files (e.g., `INFJ_Man_Mo_Temple.md`, `ENTJ_Central_District.md`).

---

## 🚀 **Quick Start Testing**

### **1. Prerequisites**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check Knowledge Base access
aws bedrock-agent get-knowledge-base --knowledge-base-id 1FJ1VHU5OW --region us-east-1

# Verify Python dependencies
pip install boto3 pandas
```

### **2. Basic Knowledge Base Query Test**
```bash
cd mbti_travel_assistant_mcp/tests
python -c "
import boto3
client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
response = client.retrieve(
    knowledgeBaseId='1FJ1VHU5OW',
    retrievalQuery={'text': 'INFJ quiet contemplative places Hong Kong'},
    retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 5}}
)
print(f'Found {len(response[\"retrievalResults\"])} results')
for result in response['retrievalResults']:
    print(f'- {result[\"location\"][\"s3Location\"][\"uri\"].split(\"/\")[-1]} (Score: {result[\"score\"]:.4f})')
"
```

---

## 🧪 **Comprehensive Testing Methods**

### **Method 1: Single MBTI Type Testing** ⭐ **RECOMMENDED**

#### **Run Individual MBTI Type Test**
```bash
cd mbti_travel_assistant_mcp/tests

# Test specific MBTI type
python test_single_mbti_type.py INFJ
python test_single_mbti_type.py ENTJ
python test_single_mbti_type.py ISFP

# Using CLI runner
python run_mbti_tests.py --type INFJ
python run_mbti_tests.py --type ENTJ
```

#### **Expected Results**
- **INFJ**: ~13 attractions (quiet, contemplative, cultural venues)
- **ENTJ**: ~11 attractions (business districts, leadership venues)
- **ISFP**: ~11 attractions (artistic, aesthetic, creative spaces)
- **INTJ**: ~11 attractions (strategic, intellectual, systematic venues)

### **Method 2: Comprehensive All-Types Testing**

#### **Run All 16 MBTI Types** (Long execution ~30-40 minutes)
```bash
cd mbti_travel_assistant_mcp/tests
python run_mbti_tests.py --comprehensive
```

#### **Expected Coverage**
- **Total MBTI Types**: 16
- **Total Attractions**: ~180-200 unique attractions
- **Geographic Distribution**: Hong Kong Island (60%), Kowloon (30%), New Territories (8%), Islands (2%)

### **Method 3: Direct Knowledge Base API Testing**

#### **Create Test Script**
```python
#!/usr/bin/env python3
"""Direct Knowledge Base API Test"""

import boto3
import json
from typing import List, Dict

def test_knowledge_base_direct():
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    test_queries = [
        "INFJ quiet contemplative places Hong Kong",
        "ENTJ business leadership venues Central District",
        "ISFP artistic creative galleries museums",
        "INTJ strategic analytical intellectual spaces",
        "temples spiritual meditation Hong Kong",
        "museums art galleries cultural attractions",
        "Central District business financial venues",
        "Tsim Sha Tsui tourist attractions"
    ]
    
    results = {}
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        
        response = client.retrieve(
            knowledgeBaseId='1FJ1VHU5OW',
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 10
                }
            }
        )
        
        results[query] = {
            'count': len(response['retrievalResults']),
            'top_results': [
                {
                    'filename': result['location']['s3Location']['uri'].split('/')[-1],
                    'score': result['score']
                }
                for result in response['retrievalResults'][:3]
            ]
        }
        
        print(f"  Found: {results[query]['count']} results")
        for i, result in enumerate(results[query]['top_results'], 1):
            print(f"    {i}. {result['filename']} (Score: {result['score']:.4f})")
        print()
    
    return results

if __name__ == "__main__":
    results = test_knowledge_base_direct()
    
    # Save results
    with open('direct_kb_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✅ Direct Knowledge Base test completed!")
    print("Results saved to: direct_kb_test_results.json")
```

---

## 📊 **Test Validation Criteria**

### **Success Metrics**

#### **Query Response Quality**
- ✅ **Response Time**: < 5 seconds per query
- ✅ **Relevance Score**: > 0.3 for top results
- ✅ **MBTI Accuracy**: Results match queried personality type
- ✅ **Geographic Coverage**: All Hong Kong areas represented

#### **MBTI Type Coverage**
- ✅ **Analysts (NT)**: INTJ, INTP, ENTJ, ENTP
- ✅ **Diplomats (NF)**: INFJ, INFP, ENFJ, ENFP  
- ✅ **Sentinels (SJ)**: ISTJ, ISFJ, ESTJ, ESFJ
- ✅ **Explorers (SP)**: ISTP, ISFP, ESTP, ESFP

#### **Content Quality**
- ✅ **File Naming**: Proper MBTI prefix (e.g., `INFJ_`, `ENTJ_`)
- ✅ **Content Structure**: Markdown format with metadata
- ✅ **Geographic Data**: Area and district information
- ✅ **Attraction Details**: Address, hours, contact information

### **Performance Benchmarks**

| Test Type | Expected Time | Expected Results |
|-----------|---------------|------------------|
| Single MBTI Type | 30-120 seconds | 8-15 attractions |
| Direct API Query | 2-5 seconds | 5-30 results |
| Comprehensive Test | 30-40 minutes | 180-200 attractions |
| Geographic Filter | 10-30 seconds | 3-8 results |

---

## 🔧 **Advanced Testing Scenarios**

### **Scenario 1: Geographic Filtering**
```python
# Test geographic filtering
test_cases = [
    {
        "query": "INFJ Central District quiet venues",
        "expected_area": "Hong Kong Island",
        "expected_district": "Central District"
    },
    {
        "query": "ENTJ Tsim Sha Tsui business centers",
        "expected_area": "Kowloon", 
        "expected_district": "Tsim Sha Tsui"
    }
]
```

### **Scenario 2: Multi-Personality Queries**
```python
# Test queries that might match multiple MBTI types
ambiguous_queries = [
    "museums Hong Kong cultural attractions",
    "peaceful quiet spaces meditation",
    "business professional networking venues",
    "artistic creative cultural experiences"
]
```

### **Scenario 3: Negative Testing**
```python
# Test queries that should return no or few results
negative_queries = [
    "ZZZZ invalid personality type",
    "restaurants food dining Hong Kong",  # Should return few results
    "shopping malls retail stores",       # Should return few results
    "nightlife bars clubs entertainment"  # Should return few results
]
```

### **Scenario 4: Stress Testing**
```python
# Test with high query volume
import concurrent.futures
import time

def stress_test_knowledge_base():
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    queries = [f"INFJ attractions Hong Kong {i}" for i in range(50)]
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for query in queries:
            future = executor.submit(
                client.retrieve,
                knowledgeBaseId='1FJ1VHU5OW',
                retrievalQuery={'text': query},
                retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 5}}
            )
            futures.append(future)
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    
    print(f"Stress test completed: {len(results)} queries in {end_time - start_time:.2f} seconds")
    print(f"Average response time: {(end_time - start_time) / len(results):.2f} seconds per query")
```

---

## 🐛 **Troubleshooting Guide**

### **Common Issues and Solutions**

#### **Issue 1: "Knowledge Base not found"**
```bash
# Verify Knowledge Base exists
aws bedrock-agent get-knowledge-base --knowledge-base-id 1FJ1VHU5OW --region us-east-1

# Check your AWS region
aws configure get region
```

#### **Issue 2: "Access Denied"**
```bash
# Check IAM permissions
aws iam get-user
aws sts get-caller-identity

# Required permissions:
# - bedrock:InvokeModel
# - bedrock-agent-runtime:Retrieve
# - bedrock-agent:GetKnowledgeBase
```

#### **Issue 3: "No results returned"**
```python
# Debug query with verbose output
response = client.retrieve(
    knowledgeBaseId='1FJ1VHU5OW',
    retrievalQuery={'text': 'your_query_here'},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 50,  # Increase result count
            'overrideSearchType': 'HYBRID'  # Try hybrid search
        }
    }
)

print(f"Total results: {len(response['retrievalResults'])}")
for result in response['retrievalResults']:
    print(f"Score: {result['score']:.4f} - {result['location']['s3Location']['uri']}")
```

#### **Issue 4: "Low relevance scores"**
- **Cause**: Query doesn't match document content well
- **Solution**: Try more specific MBTI-related keywords
- **Example**: Instead of "quiet places", use "INFJ quiet contemplative spaces"

#### **Issue 5: "Timeout errors"**
```python
# Add retry logic
import time
from botocore.exceptions import ClientError

def query_with_retry(client, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.retrieve(
                knowledgeBaseId='1FJ1VHU5OW',
                retrievalQuery={'text': query},
                retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 10}}
            )
            return response
        except ClientError as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying in 2 seconds...")
                time.sleep(2)
            else:
                raise e
```

---

## 📈 **Performance Monitoring**

### **Metrics to Track**

#### **Response Time Metrics**
```python
import time
import statistics

def measure_performance():
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    queries = [
        "INFJ quiet contemplative places",
        "ENTJ business leadership venues", 
        "ISFP artistic creative spaces",
        "INTJ strategic analytical venues"
    ]
    
    response_times = []
    
    for query in queries:
        start_time = time.time()
        
        response = client.retrieve(
            knowledgeBaseId='1FJ1VHU5OW',
            retrievalQuery={'text': query},
            retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 10}}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        response_times.append(response_time)
        
        print(f"Query: '{query}' - Time: {response_time:.2f}s - Results: {len(response['retrievalResults'])}")
    
    print(f"\nPerformance Summary:")
    print(f"Average response time: {statistics.mean(response_times):.2f}s")
    print(f"Min response time: {min(response_times):.2f}s")
    print(f"Max response time: {max(response_times):.2f}s")
    print(f"Median response time: {statistics.median(response_times):.2f}s")

if __name__ == "__main__":
    measure_performance()
```

#### **Result Quality Metrics**
```python
def analyze_result_quality():
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    # Test MBTI-specific queries
    mbti_queries = {
        'INFJ': 'INFJ quiet contemplative cultural spaces Hong Kong',
        'ENTJ': 'ENTJ business leadership strategic venues Hong Kong',
        'ISFP': 'ISFP artistic creative aesthetic attractions Hong Kong',
        'INTJ': 'INTJ analytical systematic intellectual venues Hong Kong'
    }
    
    quality_metrics = {}
    
    for mbti_type, query in mbti_queries.items():
        response = client.retrieve(
            knowledgeBaseId='1FJ1VHU5OW',
            retrievalQuery={'text': query},
            retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 20}}
        )
        
        results = response['retrievalResults']
        
        # Count MBTI-matching results
        matching_results = [
            r for r in results 
            if r['location']['s3Location']['uri'].split('/')[-1].startswith(f'{mbti_type}_')
        ]
        
        # Calculate quality metrics
        total_results = len(results)
        matching_count = len(matching_results)
        accuracy = (matching_count / total_results) * 100 if total_results > 0 else 0
        avg_score = sum(r['score'] for r in results) / total_results if total_results > 0 else 0
        
        quality_metrics[mbti_type] = {
            'total_results': total_results,
            'matching_results': matching_count,
            'accuracy_percentage': accuracy,
            'average_score': avg_score,
            'top_score': results[0]['score'] if results else 0
        }
        
        print(f"{mbti_type} Query Results:")
        print(f"  Total results: {total_results}")
        print(f"  MBTI-matching: {matching_count}")
        print(f"  Accuracy: {accuracy:.1f}%")
        print(f"  Average score: {avg_score:.4f}")
        print(f"  Top score: {results[0]['score']:.4f}" if results else "  No results")
        print()
    
    return quality_metrics
```

---

## 📝 **Test Report Template**

### **Knowledge Base Test Report**

**Test Date**: `YYYY-MM-DD`  
**Tester**: `Your Name`  
**Knowledge Base ID**: `1FJ1VHU5OW`  
**Test Duration**: `X minutes`

#### **Test Summary**
- ✅/❌ **Basic Connectivity**: Knowledge Base accessible
- ✅/❌ **MBTI Type Coverage**: All 16 types tested
- ✅/❌ **Geographic Coverage**: All areas represented  
- ✅/❌ **Performance**: Response times < 5 seconds
- ✅/❌ **Accuracy**: MBTI matching > 80%

#### **Detailed Results**

| MBTI Type | Documents Found | Avg Score | Response Time | Status |
|-----------|----------------|-----------|---------------|---------|
| INFJ | 13 | 0.4521 | 2.3s | ✅ |
| ENTJ | 11 | 0.4233 | 2.1s | ✅ |
| ISFP | 11 | 0.4456 | 2.5s | ✅ |
| INTJ | 11 | 0.4334 | 2.2s | ✅ |
| ... | ... | ... | ... | ... |

#### **Issues Identified**
1. Issue description and resolution
2. Performance bottlenecks
3. Data quality concerns

#### **Recommendations**
1. Optimization suggestions
2. Additional test scenarios
3. Monitoring improvements

---

## 🚀 **Automated Testing Scripts**

### **Daily Health Check Script**
```bash
#!/bin/bash
# daily_kb_health_check.sh

echo "🔍 Daily Knowledge Base Health Check - $(date)"
echo "================================================"

cd /path/to/mbti_travel_assistant_mcp/tests

# Test basic connectivity
echo "Testing basic connectivity..."
python -c "
import boto3
try:
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    response = client.retrieve(
        knowledgeBaseId='1FJ1VHU5OW',
        retrievalQuery={'text': 'test query'},
        retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': 1}}
    )
    print('✅ Knowledge Base accessible')
except Exception as e:
    print(f'❌ Knowledge Base error: {e}')
"

# Test sample MBTI types
echo "Testing sample MBTI types..."
python test_single_mbti_type.py INFJ > /dev/null 2>&1 && echo "✅ INFJ test passed" || echo "❌ INFJ test failed"
python test_single_mbti_type.py ENTJ > /dev/null 2>&1 && echo "✅ ENTJ test passed" || echo "❌ ENTJ test failed"

echo "Health check completed at $(date)"
```

### **Weekly Comprehensive Test**
```bash
#!/bin/bash
# weekly_comprehensive_test.sh

echo "📊 Weekly Comprehensive Knowledge Base Test - $(date)"
echo "====================================================="

cd /path/to/mbti_travel_assistant_mcp/tests

# Run comprehensive test
echo "Running comprehensive MBTI test..."
python run_mbti_tests.py --comprehensive > weekly_test_$(date +%Y%m%d).log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Weekly comprehensive test completed successfully"
    echo "📄 Results saved to: weekly_test_$(date +%Y%m%d).log"
else
    echo "❌ Weekly comprehensive test failed"
    echo "📄 Check log file: weekly_test_$(date +%Y%m%d).log"
fi
```

---

## 📚 **Additional Resources**

### **AWS Documentation**
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [Bedrock Agent Runtime API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_Retrieve.html)

### **Related Files**
- `tests/test_single_mbti_type.py` - Individual MBTI type testing
- `tests/test_mbti_prompts_comprehensive.py` - All types testing
- `tests/run_mbti_tests.py` - CLI test runner
- `services/mbti_prompt_loader.py` - MBTI prompt management
- `mbti_prompts/` - MBTI personality type prompts

### **Configuration Files**
- `config/settings.py` - Application settings
- `.bedrock_agentcore.yaml` - AgentCore configuration
- `requirements.txt` - Python dependencies

---

## 🎯 **Quick Test Commands**

```bash
# Navigate to test directory
cd mbti_travel_assistant_mcp/tests

# List available MBTI types
python run_mbti_tests.py --list-types

# Test specific MBTI type
python run_mbti_tests.py --type INFJ

# Test multiple types quickly
for type in INFJ ENTJ ISFP INTJ; do
    echo "Testing $type..."
    python test_single_mbti_type.py $type
done

# Check test results
ls -la results/

# View latest test result
cat results/infj_test_results.json | jq '.test_cases.test_case_1.count'
```

This comprehensive guide provides everything needed to test the OpenSearch Knowledge Base effectively. The tests validate MBTI personality type matching, geographic filtering, performance metrics, and data quality across all 16 personality types and Hong Kong tourist attractions.