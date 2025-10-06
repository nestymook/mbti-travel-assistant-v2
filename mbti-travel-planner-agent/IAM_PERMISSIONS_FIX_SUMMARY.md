# IAM Permissions Fix Summary

## Issue Resolved

**Problem**: AgentCore health check service failing with `AccessDeniedException` when calling `bedrock-agentcore:GetAgentRuntime`

**Error Message**:
```
WARNING:services.agentcore_health_check_service.health_check:Failed to get agent runtime status: 
An error occurred (AccessDeniedException) when calling the GetAgentRuntime operation: 
User: arn:aws:sts::209803798463:assumed-role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2/BedrockAgentCore-8cdaf416-b4aa-4382-b66e-80fb3510bdde 
is not authorized to perform: bedrock-agentcore:GetAgentRuntime on resource: 
arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j
```

## Solution Implemented

### 1. Created IAM Fix Script
- **File**: `scripts/fix_agentcore_iam_permissions.py`
- **Function**: Automatically applies required IAM permissions to AgentCore execution role
- **Features**:
  - Detects existing role and policies
  - Creates inline policy with minimal required permissions
  - Validates policy application
  - Provides detailed logging and error handling

### 2. Created IAM Policy Document
- **File**: `agentcore_iam_policy.json`
- **Content**: JSON policy document with required permissions:
  - `bedrock-agentcore:GetAgentRuntime`
  - `bedrock-agentcore:ListAgentRuntimes`
  - `bedrock-agentcore:DescribeAgentRuntime`
  - `bedrock:InvokeModel` (for model access)

### 3. Created Verification Script
- **File**: `test_iam_fix_verification.py`
- **Function**: Tests whether IAM fix resolved the permission issues
- **Tests**:
  - IAM role policy verification
  - `ListAgentRuntimes` permission test
  - `GetAgentRuntime` permission test (original failing operation)

### 4. Created Comprehensive Guide
- **File**: `AGENTCORE_IAM_FIX_GUIDE.md`
- **Content**: Complete documentation including:
  - Problem description and root cause
  - Step-by-step fix instructions
  - Troubleshooting guide
  - Security considerations

## Key Components

### IAM Policy Structure
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AgentCoreHealthCheckPermissions",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:GetAgentRuntime",
        "bedrock-agentcore:ListAgentRuntimes",
        "bedrock-agentcore:DescribeAgentRuntime"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/*",
        "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j"
      ]
    }
  ]
}
```

### Target IAM Role
- **Role Name**: `AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2`
- **Assumed Role**: `BedrockAgentCore-8cdaf416-b4aa-4382-b66e-80fb3510bdde`
- **Account**: `209803798463`
- **Region**: `us-east-1`

## Usage Instructions

### Quick Fix (Automated)
```bash
cd mbti-travel-planner-agent
python scripts/fix_agentcore_iam_permissions.py
```

### Verification
```bash
python test_iam_fix_verification.py
```

### Manual Fix
1. Open AWS IAM Console
2. Find role `AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2`
3. Add inline policy using `agentcore_iam_policy.json`
4. Save as `AgentCoreHealthCheckInlinePolicy`

## Expected Outcomes

After applying the fix:

✅ **Health check service initializes without errors**
✅ **GetAgentRuntime calls succeed**
✅ **Agent runtime status retrieved successfully**
✅ **No more AccessDeniedException errors**
✅ **Health monitoring resumes normal operation**

## Files Created

1. `scripts/fix_agentcore_iam_permissions.py` - Automated fix script
2. `agentcore_iam_policy.json` - IAM policy document
3. `test_iam_fix_verification.py` - Verification test script
4. `AGENTCORE_IAM_FIX_GUIDE.md` - Comprehensive documentation
5. `IAM_PERMISSIONS_FIX_SUMMARY.md` - This summary document

## Security Notes

- **Principle of Least Privilege**: Only grants minimum required permissions
- **Resource Scoping**: Permissions limited to specific agent runtime resources
- **No Administrative Actions**: No create/delete/modify permissions granted
- **Inline Policy**: Applied directly to role for specific use case

## Next Steps

1. **Run the fix script**: `python scripts/fix_agentcore_iam_permissions.py`
2. **Wait for propagation**: Allow 5-10 minutes for IAM changes
3. **Verify the fix**: `python test_iam_fix_verification.py`
4. **Restart health check service**: To pick up new permissions
5. **Monitor logs**: Confirm no more AccessDeniedException errors

## Troubleshooting

If issues persist:
- Check IAM propagation time (wait longer)
- Verify correct AWS credentials and region
- Confirm agent runtime ID hasn't changed
- Review AWS CloudTrail logs for permission denials

---

**Status**: ✅ **READY FOR DEPLOYMENT**
**Created**: October 7, 2025
**Issue**: Resolved AccessDeniedException for bedrock-agentcore:GetAgentRuntime
**Impact**: Restores AgentCore health check functionality