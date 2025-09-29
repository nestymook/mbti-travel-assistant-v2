# Knowledge Base Testing - Quick Start Guide

This directory contains comprehensive testing tools for the MBTI Travel Assistant OpenSearch Knowledge Base.

## 🚀 **Quick Test Commands**

### **Windows Users**
```powershell
# PowerShell (Recommended)
.\run_kb_tests.ps1

# Command Prompt
run_kb_tests.bat

# Specific test types
.\run_kb_tests.ps1 -TestType mbti
.\run_kb_tests.ps1 -TestType connectivity
```

### **Python Direct**
```bash
# Quick comprehensive test
python test_knowledge_base_quick.py

# Specific test types
python test_knowledge_base_quick.py connectivity
python test_knowledge_base_quick.py mbti
python test_knowledge_base_quick.py geographic
python test_knowledge_base_quick.py performance
```

### **MBTI Personality Tests**
```bash
cd tests/

# Test individual MBTI types
python test_single_mbti_type.py INFJ
python test_single_mbti_type.py ENTJ

# Use CLI runner
python run_mbti_tests.py --type ISFP
python run_mbti_tests.py --list-types

# Comprehensive all-types test (30-40 minutes)
python run_mbti_tests.py --comprehensive
```

---

## 📋 **Test Types Available**

| Test Type | Description | Duration | Purpose |
|-----------|-------------|----------|---------|
| **connectivity** | Basic KB access test | 5 seconds | Verify KB is accessible |
| **mbti** | MBTI personality queries | 30 seconds | Test personality matching |
| **geographic** | Location-based filtering | 20 seconds | Test geographic queries |
| **performance** | Response time testing | 45 seconds | Measure performance |
| **all** | Complete test suite | 2 minutes | Comprehensive validation |

---

## 📊 **Expected Results**

### **Connectivity Test**
- ✅ Knowledge Base accessible
- ✅ Response time < 5 seconds

### **MBTI Tests**
- ✅ **INFJ**: ~13 attractions (quiet, contemplative venues)
- ✅ **ENTJ**: ~11 attractions (business, leadership venues)  
- ✅ **ISFP**: ~11 attractions (artistic, creative spaces)
- ✅ **INTJ**: ~11 attractions (strategic, analytical venues)

### **Geographic Tests**
- ✅ **Central District**: Business and financial venues
- ✅ **Tsim Sha Tsui**: Museums and cultural attractions
- ✅ **Hong Kong Island**: Mixed attraction types
- ✅ **Kowloon**: Tourist and cultural venues

### **Performance Benchmarks**
- ✅ Average response time: < 3 seconds
- ✅ Query success rate: > 95%
- ✅ Result relevance: > 80% accuracy

---

## 🔧 **Prerequisites**

### **Required Software**
```bash
# Python 3.8+
python --version

# AWS SDK
pip install boto3

# Optional: AWS CLI for credential verification
aws --version
```

### **AWS Configuration**
```bash
# Configure AWS credentials (one of these methods)
aws configure
# OR set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### **Knowledge Base Access**
- **Knowledge Base ID**: `1FJ1VHU5OW`
- **Region**: `us-east-1`
- **Required Permissions**: `bedrock-agent-runtime:Retrieve`

---

## 📁 **File Structure**

```
mbti_travel_assistant_mcp/
├── OPENSEARCH_KNOWLEDGE_BASE_TESTING_GUIDE.md  📖 Comprehensive guide
├── TESTING_QUICK_START.md                      📋 This file
├── test_knowledge_base_quick.py                🐍 Quick test script
├── run_kb_tests.ps1                           🔧 PowerShell runner
├── run_kb_tests.bat                           🔧 Batch runner
├── tests/
│   ├── test_single_mbti_type.py               🧠 Individual MBTI tests
│   ├── test_mbti_prompts_comprehensive.py     📊 All MBTI types
│   ├── run_mbti_tests.py                      🚀 CLI test runner
│   └── results/                               📄 Test results
├── services/
│   └── mbti_prompt_loader.py                  🔧 MBTI prompt utility
└── mbti_prompts/                              📝 MBTI prompt files
    ├── INFJ.json
    ├── ENTJ.json
    └── [14 other types].json
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **"Knowledge Base not found"**
```bash
# Verify KB exists
aws bedrock-agent get-knowledge-base --knowledge-base-id 1FJ1VHU5OW --region us-east-1
```

#### **"Access Denied"**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify region
aws configure get region
```

#### **"No results returned"**
- Try different query terms
- Check if data ingestion is complete
- Verify S3 bucket has content

#### **"Import errors"**
```bash
# Install missing dependencies
pip install boto3 pandas

# Check Python path
python -c "import sys; print(sys.path)"
```

### **Getting Help**
1. Check the comprehensive guide: `OPENSEARCH_KNOWLEDGE_BASE_TESTING_GUIDE.md`
2. Review test logs and error messages
3. Verify AWS permissions and configuration
4. Test with simpler queries first

---

## 📈 **Monitoring and Results**

### **Test Results Location**
- **Quick tests**: `*test_results*.json` files in current directory
- **MBTI tests**: `tests/results/` directory
- **Logs**: Console output and error messages

### **Result Analysis**
```bash
# View latest quick test results
cat quick_kb_test_results_*.json | jq '.tests.mbti_queries'

# View MBTI test results
cat tests/results/infj_test_results.json | jq '.test_cases.test_case_1.count'

# Check performance metrics
cat quick_kb_test_results_*.json | jq '.tests.performance.avg_response_time'
```

### **Success Criteria**
- ✅ All connectivity tests pass
- ✅ MBTI accuracy > 80%
- ✅ Response times < 5 seconds
- ✅ Geographic filtering works correctly
- ✅ No critical errors in logs

---

## 🎯 **Next Steps**

After successful testing:

1. **Production Deployment**: Use validated KB configuration
2. **Integration Testing**: Test with MCP server and AgentCore
3. **Performance Optimization**: Monitor and tune based on results
4. **Automated Monitoring**: Set up regular health checks
5. **Documentation**: Update based on test findings

---

## 📞 **Support**

For issues or questions:
- Review the comprehensive testing guide
- Check AWS Bedrock documentation
- Verify Knowledge Base configuration
- Test with minimal queries first

**Happy Testing!** 🎉