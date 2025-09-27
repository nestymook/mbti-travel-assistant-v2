# Script Cleanup Recommendations

## 🧹 Overview

This document identifies redundant scripts and provides recommendations for cleanup to maintain a clean, maintainable codebase.

## 📊 Current Script Analysis

### 🟢 Essential Scripts (Keep)

#### Deployment Scripts
1. **`execute_deployment.py`** ⭐ **PRIMARY**
   - Complete deployment workflow
   - Prerequisites validation
   - Status monitoring
   - **Action**: Keep as main deployment script

2. **`deploy_agentcore.py`** ⭐ **CORE**
   - AgentCore configuration and deployment
   - Status checking functionality
   - **Action**: Keep for granular control

3. **`setup_cognito.py`**
   - Cognito User Pool setup
   - **Action**: Keep for authentication setup

#### Testing Scripts
1. **`test_auth_prompt.py`** ⭐ **PRIMARY**
   - Authentication testing with secure prompts
   - Token validation
   - **Action**: Keep as main auth test

2. **`test_mcp_endpoint_invoke.py`** ⭐ **PRIMARY**
   - Proper MCP endpoint testing
   - Runtime.invoke() method testing
   - **Action**: Keep as main MCP test

3. **`test_deployed_agent_toolkit.py`** 🟡 **LEGACY**
   - Comprehensive agent testing (legacy approach)
   - Status verification
   - **Action**: Keep but note authentication mismatch issues

3. **`test_simple_auth.py`**
   - Basic authentication validation
   - **Action**: Keep for simple testing

#### Utility Scripts
1. **`create_test_user_cli.py`**
   - Test user management
   - **Action**: Keep for user setup

2. **`debug_auth.py`**
   - Authentication debugging
   - **Action**: Keep for troubleshooting

### 🟡 Redundant Scripts (Consider Removing)

#### Duplicate Deployment Scripts
1. **`deploy_conversational_agent.py`**
   - **Issue**: Overlaps with `execute_deployment.py`
   - **Recommendation**: Remove or merge functionality

2. **`test_entrypoint_deployment.py`**
   - **Issue**: Similar to main deployment scripts
   - **Recommendation**: Remove if not adding unique value

#### Duplicate Testing Scripts
1. **`test_conversational_agent.py`**
   - **Issue**: Superseded by `test_deployed_agent_toolkit.py`
   - **Recommendation**: Remove

2. **`test_deployed_conversational_agent.py`**
   - **Issue**: Redundant with toolkit test
   - **Recommendation**: Remove

3. **`test_agentcore_simple.py`**
   - **Issue**: Similar to other auth tests
   - **Recommendation**: Remove or consolidate

4. **`test_agentcore_final.py`**
   - **Issue**: Overlaps with toolkit test
   - **Recommendation**: Remove

5. **`test_agentcore_with_auth.py`**
   - **Issue**: Functionality covered by newer tests
   - **Recommendation**: Remove

6. **`test_agentcore_invoke.py`**
   - **Issue**: Specific invoke testing, covered elsewhere
   - **Recommendation**: Remove

7. **`test_agentcore_direct.py`**
   - **Issue**: Direct API testing, not needed
   - **Recommendation**: Remove

8. **`test_deployed_mcp.py`**
   - **Issue**: Older MCP testing approach
   - **Recommendation**: Remove

#### Legacy Scripts
1. **`fix_cognito_auth_flow.py`**
   - **Issue**: One-time fix script
   - **Recommendation**: Remove after confirming not needed

2. **`update_test_user.py`**
   - **Issue**: User management, may be needed
   - **Recommendation**: Keep but review usage

3. **`update_test_user_password.py`**
   - **Issue**: Password management utility
   - **Recommendation**: Keep for maintenance

### 🔴 Test Directory Scripts (Organize)

#### Move to `/tests/` Directory
1. **`tests/test_mcp_with_toolkit.py`** - Keep
2. **`tests/test_entrypoint_basic.py`** - Review and possibly remove
3. **`tests/test_entrypoint_integration.py`** - Review and possibly remove
4. **`tests/run_entrypoint_tests.py`** - Keep if used
5. **`tests/run_authentication_tests.py`** - Keep if used

## 🎯 Recommended Actions

### Phase 1: Immediate Cleanup (Safe Removals)

#### Remove Redundant Test Scripts
```bash
# These can be safely removed as functionality is covered elsewhere
rm test_conversational_agent.py
rm test_deployed_conversational_agent.py
rm test_agentcore_simple.py
rm test_agentcore_final.py
rm test_agentcore_with_auth.py
rm test_agentcore_invoke.py
rm test_agentcore_direct.py
rm test_deployed_mcp.py
```

#### Remove Duplicate Deployment Scripts
```bash
# Remove if functionality is fully covered by execute_deployment.py
rm deploy_conversational_agent.py  # Review first
rm test_entrypoint_deployment.py   # Review first
```

### Phase 2: Consolidation

#### Create Unified Test Suite
```bash
# Consolidate remaining tests into organized structure
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/deployment

# Move tests to appropriate directories
mv test_auth_prompt.py tests/unit/
mv test_simple_auth.py tests/unit/
mv test_deployed_agent_toolkit.py tests/integration/
```

#### Update Documentation
- Update README.md with simplified script list
- Create clear usage documentation
- Remove references to deleted scripts

### Phase 3: Optimization

#### Streamline Remaining Scripts
1. **Merge similar functionality** where appropriate
2. **Standardize interfaces** (consistent CLI arguments)
3. **Improve error handling** across all scripts
4. **Add comprehensive logging**

## 📋 Recommended Final Script Structure

### Core Scripts (Root Directory)
```
execute_deployment.py          # Main deployment script
deploy_agentcore.py           # AgentCore operations
setup_cognito.py              # Authentication setup
create_test_user_cli.py       # User management
debug_auth.py                 # Troubleshooting
```

### Test Scripts (`/tests/` Directory)
```
tests/
├── unit/
│   ├── test_auth_prompt.py           # Authentication testing
│   └── test_simple_auth.py           # Basic auth validation
├── integration/
│   └── test_deployed_agent_toolkit.py # Full agent testing
└── deployment/
    └── test_deployment_validation.py  # Deployment verification
```

### Utility Scripts (`/utils/` Directory)
```
utils/
├── update_test_user.py               # User management
├── update_test_user_password.py      # Password management
└── fix_cognito_auth_flow.py          # Maintenance scripts
```

## 🔍 Verification Steps

### Before Cleanup
1. **Document current functionality** of each script
2. **Test all scripts** to understand their purpose
3. **Check dependencies** between scripts
4. **Backup important scripts** before deletion

### After Cleanup
1. **Test remaining scripts** to ensure functionality
2. **Update documentation** to reflect changes
3. **Verify CI/CD pipelines** still work
4. **Update README.md** with new structure

## 📈 Benefits of Cleanup

### Maintainability
- Fewer scripts to maintain
- Clear purpose for each script
- Reduced code duplication

### User Experience
- Clearer documentation
- Easier to find the right script
- Consistent interfaces

### Development Efficiency
- Faster onboarding for new developers
- Reduced confusion about which script to use
- Better test organization

## 🚨 Risks and Mitigation

### Potential Risks
- Accidentally removing needed functionality
- Breaking existing workflows
- Loss of historical context

### Mitigation Strategies
- **Gradual cleanup** in phases
- **Thorough testing** before removal
- **Git history preservation**
- **Documentation updates**

---

**Cleanup Plan Created**: September 27, 2025  
**Status**: Recommendations Ready  
**Next Action**: Review and approve cleanup plan