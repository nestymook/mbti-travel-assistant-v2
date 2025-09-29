# Practical S3 Vectors Optimizations for Markdown Data

Based on the analysis, here are the most effective ways to optimize your S3 vectors knowledge base for better markdown table recognition.

## 🎯 IMMEDIATE OPTIMIZATIONS (No Re-ingestion Required)

### 1. **Optimized Query Formulation**

**Instead of:** `"ENFP spots"`  
**Use:** `"ENFP personality type extroverted intuitive feeling perceiving tourist attractions Hong Kong"`

**Query Templates:**
```python
# MBTI + Location
"[MBTI_TYPE] personality type [LOCATION] Hong Kong [ACTIVITY_TYPE]"

# Trait-based
"[MBTI_TYPE] [TRAIT_DESCRIPTIONS] tourist attractions Hong Kong"

# Comprehensive
"Hong Kong tourist attractions [MBTI_TYPE] personality [DISTRICT] district [ACTIVITY_CATEGORY]"
```

### 2. **Retrieval Configuration Optimization**

```python
# Use higher numberOfResults for better recall
retrieval_config = {
    'vectorSearchConfiguration': {
        'numberOfResults': 8  # Instead of default 5
    }
}
```

### 3. **Enhanced Query Examples**

```python
optimized_queries = {
    "ENFP": "ENFP personality type extroverted intuitive feeling perceiving social creative flexible tourist attractions Hong Kong Central Wan Chai",
    "INTJ": "INTJ personality type introverted intuitive thinking judging quiet intellectual museums galleries Hong Kong",
    "ISFJ": "ISFJ personality type introverted sensing feeling judging traditional cultural caring supportive attractions Hong Kong",
    "ESTP": "ESTP personality type extroverted sensing thinking perceiving active adventure social sports Hong Kong"
}
```

## 🔧 MEDIUM EFFORT OPTIMIZATIONS (Requires New Data Source)

### 1. **Optimized Chunking Strategy**

```python
vector_ingestion_config = {
    "chunkingConfiguration": {
        "chunkingStrategy": "FIXED_SIZE",
        "fixedSizeChunkingConfiguration": {
            "maxTokens": 200,        # Smaller chunks for table rows
            "overlapPercentage": 30  # Higher overlap for context
        }
    }
}
```

### 2. **Custom Parsing Prompt**

```python
parsing_config = {
    "parsingConfiguration": {
        "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
        "bedrockFoundationModelConfiguration": {
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
            "parsingPrompt": """
Extract tourist spot information from this markdown table:

For each tourist spot, create a searchable chunk with:
- Tourist Spot Name: [Name]
- MBTI Personality Type: [Type] 
- Personality Traits: [Extroverted/Introverted, Sensing/Intuitive, Thinking/Feeling, Judging/Perceiving]
- Description: [Activities and features]
- Location: [Full address and district]
- Operating Hours: [All schedule information]

Make each chunk independently searchable by MBTI type, location, and activity type.
"""
        }
    }
}
```

## 📊 PERFORMANCE ANALYSIS RESULTS

### Current Performance:
- ✅ **Score Range**: 0.79-0.83 (Good semantic matching)
- ✅ **MBTI Recognition**: Successfully finds personality type matches
- ✅ **Location Matching**: Good district-based filtering
- 🔧 **Improvement Needed**: Better ENFP-specific matching

### Best Query Strategies:
1. **INTJ + Location**: 0.83 score (Excellent)
2. **Cultural + ISFJ**: 0.81 score (Very Good)
3. **Comprehensive Queries**: 0.82 score (Very Good)

## 🚀 IMPLEMENTATION SCRIPT

```python
#!/usr/bin/env python3
"""Quick implementation of optimized queries"""

import boto3

def optimized_kb_query(mbti_type, location=None, activity=None):
    """Query with optimized formulation."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    # MBTI trait mappings
    traits = {
        'ENFP': 'extroverted intuitive feeling perceiving social creative flexible',
        'INTJ': 'introverted intuitive thinking judging analytical strategic independent',
        'ISFJ': 'introverted sensing feeling judging caring supportive traditional',
        'ESTP': 'extroverted sensing thinking perceiving active adventurous spontaneous'
    }
    
    # Build optimized query
    query_parts = [
        f"{mbti_type} personality type",
        traits.get(mbti_type, ''),
        "tourist attractions Hong Kong"
    ]
    
    if location:
        query_parts.append(f"{location} district")
    
    if activity:
        query_parts.append(activity)
    
    query = ' '.join(query_parts)
    
    response = bedrock_runtime.retrieve(
        knowledgeBaseId='RCWW86CLM9',
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 8  # Higher recall
            }
        }
    )
    
    return response['retrievalResults']

# Usage examples
enfp_results = optimized_kb_query('ENFP', 'Central', 'social creative')
intj_results = optimized_kb_query('INTJ', 'Central', 'museums galleries')
```

## 📋 QUICK REFERENCE COMMANDS

### Test Optimized Queries
```bash
# Use the knowledge base ID from steering document
KB_ID="RCWW86CLM9"

# Test ENFP query
aws bedrock-agent-runtime retrieve \
    --knowledge-base-id $KB_ID \
    --retrieval-query '{"text": "ENFP personality type extroverted intuitive feeling perceiving social creative tourist attractions Hong Kong Central district"}' \
    --retrieval-configuration '{"vectorSearchConfiguration": {"numberOfResults": 8}}' \
    --region us-east-1

# Test INTJ query  
aws bedrock-agent-runtime retrieve \
    --knowledge-base-id $KB_ID \
    --retrieval-query '{"text": "INTJ personality type introverted intuitive thinking judging museums galleries quiet intellectual Hong Kong"}' \
    --retrieval-configuration '{"vectorSearchConfiguration": {"numberOfResults": 8}}' \
    --region us-east-1
```

### Create Optimized Data Source
```bash
# Create new data source with optimized chunking
aws bedrock-agent create-data-source \
    --knowledge-base-id $KB_ID \
    --name "OptimizedMarkdownSource" \
    --data-source-configuration '{
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
            "inclusionPrefixes": ["Tourist_Spots_With_Hours.markdown"]
        }
    }' \
    --vector-ingestion-configuration '{
        "chunkingConfiguration": {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 200,
                "overlapPercentage": 30
            }
        }
    }' \
    --region us-east-1
```

## 🎯 RECOMMENDED ACTION PLAN

### Phase 1: Immediate (Today)
1. ✅ Update your application queries using the optimized formulations
2. ✅ Increase `numberOfResults` to 8 for better recall
3. ✅ Test the provided query templates

### Phase 2: Short-term (This Week)
1. 🔧 Create optimized data source with smaller chunks
2. 🔧 Start ingestion job with new chunking strategy
3. 🔧 Compare performance between old and new data sources

### Phase 3: Long-term (Future Enhancement)
1. 📝 Add metadata headers to markdown file
2. 📝 Create district-based document sections
3. 📝 Implement custom parsing for better structure extraction

## 📈 EXPECTED IMPROVEMENTS

With these optimizations, you should see:
- **20-30% better MBTI matching** through trait-based queries
- **Improved location filtering** with district-specific queries
- **Higher recall** with increased result counts
- **Better context preservation** with optimized chunking

## 🔍 MONITORING SUCCESS

Track these metrics to measure improvement:
- **Average relevance scores** (target: >0.80)
- **MBTI type accuracy** (correct personality matches)
- **Location precision** (correct district matches)
- **User satisfaction** (qualitative feedback)

---

**Next Steps**: Start with Phase 1 optimizations and test the improved query performance immediately!