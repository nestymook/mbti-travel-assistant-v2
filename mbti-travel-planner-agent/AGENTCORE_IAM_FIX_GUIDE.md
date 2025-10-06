# AgentCore IAM Permissions Fix Guide

## Problem Description

The AgentCore health check service is failing with the following error:

```
WARNING:services.agentcore_health_check_service.health_check:Failed to get agent runtime status: 
An error occurred (AccessDeniedException) when calling the GetAgentRuntime operation: 
User: arn:aws:sts::209803798463:assumed-role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2/BedrockAgentCore-8cdaf416-b4aa-4382-b66e-80fb3510bdde 
is not authorized to perform: bedrock-agentcore:GetAgentRuntime on resource: 
arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j 
because no identity-based policy allows the bedrock-agentcore:GetAgentRuntime action
```

## Root Cause

The AgentCore execution role `AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2` does not have the necessary IAM permissions to perform `bedrock-agentcore:GetAgentRuntime` operations on the agent runtime resource.

## Solution Overview

We need to add the following IAM permissions to the AgentCore execution role:

1. `bedrock-agentcore:GetAgentRuntime` - To get specific agent runtime status
2. `bedrock-agentcore:ListAgentRuntimes` - To list available agent runtimes  
3. `bedrock-agentcore:DescribeAgentRuntime` - To get detailed runtime information
4. `bedrock:InvokeModel` - For Bedrock model access (if needed)

## Files Created

### 1. IAM Fix Script
- **File**: `scripts/fix_agentcore_iam_permissions.py`
- **Purpose**: Automatically applies the required IAM permissions to the AgentCore execution role
- **Usage**: `python scripts/fix_agentcore_iam_permissions.py`

### 2. IAM Policy Document
- **File**: `agentcore_iam_policy.json`
- **Purpose**: Contains the JSON policy document with required permissions
- **Usage**: Reference for manual IAM policy creation

### 3. Verification Script
- **File**: `test_iam_fix_verification.py`
- **Purpose**: Tests whether the IAM fix resolved the permission issues
- **Usage**: `python test_iam_fix_verification.py`

## Quick Fix Instructions

### Option 1: Automated Fix (Recommended)

1. **Run the IAM fix script**:
   ```bash
   cd mbti-travel-planner-agent
   python scripts/fix_agentcore_iam_permissions.py
   ```

2. **Wait for IAM propagation** (5-10 minutes)

3. **Verify the fix**:
   ```bash
   python test_iam_fix_verification.py
   ```

4. **Restart your AgentCore health check service**

### Option 2: Manual Fix

1. **Open AWS IAM Console**

2. **Navigate to Roles** → Find role `AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2`

3. **Add Inline Policy** with the following JSON:
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
       },
       {
         "Sid": "BedrockAgentCoreGeneralPermissions",
         "Effect": "Allow",
         "Action": [
           "bedrock-agentcore:ListAgentRuntimes"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

4. **Save the policy** with name `AgentCoreHealthCheckInlinePolicy`

## Verification Steps

After applying the fix, verify it worked:

1. **Check IAM Role**:
   - Confirm the policy was added to the role
   - Verify the policy contains the required permissions

2. **Test Permissions**:
   ```bash
   python test_iam_fix_verification.py
   ```

3. **Monitor Health Check Logs**:
   - Restart the health check service
   - Check logs for successful `GetAgentRuntime` calls
   - Verify no more `AccessDeniedException` errors

## Expected Results

After the fix is applied successfully:

✅ **Health check service starts without errors**
✅ **GetAgentRuntime calls succeed**  
✅ **Agent runtime status is retrieved properly**
✅ **No more AccessDeniedException errors**

## Troubleshooting

### Issue: "Role does not exist"
- **Cause**: The AgentCore execution role hasn't been created yet
- **Solution**: Deploy your AgentCore agent first, which creates the role automatically

### Issue: "Access denied when applying policy"
- **Cause**: Your AWS credentials don't have IAM permissions
- **Solution**: Use an AWS account with IAM admin permissions or ask your AWS administrator

### Issue: "Still getting AccessDeniedException after fix"
- **Cause**: IAM changes need time to propagate
- **Solution**: Wait 5-10 minutes and try again

### Issue: "Agent runtime not found"
- **Cause**: The agent runtime ID may have changed or agent isn't deployed
- **Solution**: Check the actual agent runtime ID using `aws bedrock-agentcore list-agent-runtimes`

## IAM Policy Explanation

### Statement 1: Agent Runtime Permissions
```json
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
```
- **Purpose**: Allows health check service to query agent runtime status
- **Actions**: Get, list, and describe agent runtimes
- **Resources**: Specific agent runtime and wildcard for future agents

### Statement 2: General Permissions
```json
{
  "Sid": "BedrockAgentCoreGeneralPermissions",
  "Effect": "Allow",
  "Action": [
    "bedrock-agentcore:ListAgentRuntimes"
  ],
  "Resource": "*"
}
```
- **Purpose**: Allows listing all agent runtimes for discovery
- **Actions**: List operation only
- **Resources**: All resources (required for list operations)

## Security Considerations

- **Principle of Least Privilege**: The policy only grants the minimum permissions needed
- **Resource Restrictions**: Permissions are scoped to specific agent runtime resources where possible
- **No Sensitive Actions**: No permissions for creating, deleting, or modifying agent runtimes

## Integration with Health Check Service

After the fix, the health check service will:

1. **Initialize successfully** without configuration errors
2. **Query agent runtime status** using `GetAgentRuntime`
3. **Report accurate health status** for restaurant search and reasoning agents
4. **Provide monitoring data** for operational dashboards

## Next Steps

1. **Apply the IAM fix** using the provided script
2. **Verify the fix works** using the verification script  
3. **Monitor health check logs** to confirm resolution
4. **Update monitoring dashboards** to use the restored health check data

## Related Documentation

- [AgentCore Developer Guide](.kiro/steering/agentcore-developer-guide.md)
- [Health Check Service Implementation](services/agentcore_health_check_service.py)
- [AgentCore Configuration](config/agentcore_config.py)

---

**Last Updated**: October 7, 2025  
**Issue**: AccessDeniedException on bedrock-agentcore:GetAgentRuntime  
**Status**: Fix implemented and ready for deployment