#!/usr/bin/env python3
"""
Manual AgentCore OIDC Configuration Update Guide

This script provides step-by-step instructions for manually updating
AgentCore with the new OIDC configuration.
"""

import json
import yaml
from pathlib import Path

def load_configurations():
    """Load current configurations."""
    # Load AgentCore config
    with open('.bedrock_agentcore.yaml', 'r') as f:
        agentcore_config = yaml.safe_load(f)
    
    # Load OIDC config
    with open('cognito_oidc_config.json', 'r') as f:
        oidc_config = json.load(f)
    
    return agentcore_config, oidc_config

def main():
    """Generate manual update instructions."""
    try:
        agentcore_config, oidc_config = load_configurations()
        
        agent_config = agentcore_config['agents']['mbti_travel_assistant_mcp']
        agent_id = agent_config['bedrock_agentcore']['agent_id']
        agent_arn = agent_config['bedrock_agentcore']['agent_arn']
        
        user_pool_id = oidc_config['user_pool']['user_pool_id']
        client_id = oidc_config['app_client']['client_id']
        discovery_url = oidc_config['oidc_configuration']['discovery_url']
        
        print("=" * 80)
        print("AGENTCORE OIDC CONFIGURATION UPDATE - MANUAL INSTRUCTIONS")
        print("=" * 80)
        print()
        
        print("CURRENT CONFIGURATION:")
        print(f"  Agent ID: {agent_id}")
        print(f"  Agent ARN: {agent_arn}")
        print()
        
        print("NEW OIDC CONFIGURATION:")
        print(f"  User Pool ID: {user_pool_id}")
        print(f"  Client ID: {client_id}")
        print(f"  Discovery URL: {discovery_url}")
        print()
        
        print("STEP 1: Verify OIDC Discovery Endpoint")
        print("---------------------------------------")
        print("Test the OIDC discovery endpoint:")
        print(f"curl {discovery_url}")
        print()
        print("Expected: JSON response with issuer, jwks_uri, etc.")
        print()
        
        print("STEP 2: Update AgentCore via AWS Console")
        print("----------------------------------------")
        print("1. Open AWS Console and navigate to Amazon Bedrock")
        print("2. Go to AgentCore section")
        print("3. Find your agent:")
        print(f"   - Agent ID: {agent_id}")
        print("4. Click on the agent to open configuration")
        print("5. Navigate to Authentication/Authorization settings")
        print("6. Update the JWT Authorizer configuration:")
        print(f"   - Allowed Clients: {client_id}")
        print(f"   - Discovery URL: {discovery_url}")
        print("7. Save and deploy the configuration")
        print()
        
        print("STEP 3: Alternative - AWS CLI Method")
        print("------------------------------------")
        print("If AWS CLI supports AgentCore operations, try:")
        print()
        print("# Check available commands")
        print("aws bedrock-agentcore help")
        print()
        print("# Update agent configuration (if supported)")
        print(f"aws bedrock-agentcore update-agent-runtime \\")
        print(f"  --agent-id {agent_id} \\")
        print(f"  --region us-east-1 \\")
        print(f"  --authorizer-configuration '{{")
        print(f"    \"customJWTAuthorizer\": {{")
        print(f"      \"allowedClients\": [\"{client_id}\"],")
        print(f"      \"discoveryUrl\": \"{discovery_url}\"")
        print(f"    }}")
        print(f"  }}' \\")
        print(f"  --no-cli-pager")
        print()
        
        print("STEP 4: Test the Updated Configuration")
        print("--------------------------------------")
        print("After updating AgentCore:")
        print("1. Wait 2-3 minutes for changes to propagate")
        print("2. Test authentication using the frontend:")
        print("   - Login with: test@mbti-travel.com / TestPass1234!")
        print("   - Try generating an itinerary")
        print("3. Check CloudWatch logs for any remaining 403 errors")
        print()
        
        print("STEP 5: Verification")
        print("--------------------")
        print("Successful update indicators:")
        print("- No more 403 Forbidden errors in Lambda logs")
        print("- AgentCore accepts ID tokens from new User Pool")
        print("- Itinerary generation works end-to-end")
        print()
        
        print("TROUBLESHOOTING:")
        print("----------------")
        print("If you still get 403 errors:")
        print("1. Verify the Discovery URL is accessible")
        print("2. Check that the Client ID matches exactly")
        print("3. Ensure OAuth scopes include: openid, email, profile")
        print("4. Verify the User Pool has the correct domain configuration")
        print("5. Check AgentCore logs for specific error messages")
        print()
        
        print("CONFIGURATION FILES UPDATED:")
        print("----------------------------")
        print("- .bedrock_agentcore.yaml (already updated)")
        print("- Frontend .env.production (already updated)")
        print()
        
        print("=" * 80)
        print("Manual update instructions generated successfully!")
        print("Follow the steps above to complete the AgentCore OIDC configuration.")
        print("=" * 80)
        
        # Save instructions to file
        instructions = f"""
AgentCore OIDC Configuration Update Instructions
Generated: {json.dumps({"timestamp": "2025-09-30"}, indent=2)}

Agent Information:
- Agent ID: {agent_id}
- Agent ARN: {agent_arn}

OIDC Configuration:
- User Pool ID: {user_pool_id}
- Client ID: {client_id}
- Discovery URL: {discovery_url}

Follow the manual steps printed above to complete the update.
"""
        
        with open('agentcore_update_instructions.txt', 'w') as f:
            f.write(instructions)
        
        print(f"Instructions saved to: agentcore_update_instructions.txt")
        
    except Exception as e:
        print(f"Error generating instructions: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())