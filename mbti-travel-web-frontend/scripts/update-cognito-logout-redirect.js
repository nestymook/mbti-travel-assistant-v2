#!/usr/bin/env node

/**
 * Update Cognito User Pool Client with custom login page logout redirect
 */

import { CognitoIdentityProviderClient, UpdateUserPoolClientCommand } from '@aws-sdk/client-cognito-identity-provider';

async function updateCognitoLogoutRedirect() {
  const client = new CognitoIdentityProviderClient({ region: 'us-east-1' });
  
  const userPoolId = 'us-east-1_KePRX24Bn';
  const clientId = '1ofgeckef3po4i3us4j1m4chvd';
  const cloudfrontUrl = 'https://d39ank8zud5pbg.cloudfront.net';
  
  try {
    console.log('Updating Cognito User Pool Client logout redirect...');
    
    const command = new UpdateUserPoolClientCommand({
      UserPoolId: userPoolId,
      ClientId: clientId,
      CallbackURLs: [
        `${cloudfrontUrl}/`,
        `${cloudfrontUrl}/auth/callback`
      ],
      LogoutURLs: [
        `${cloudfrontUrl}/`  // Redirect to home page on logout (will redirect to login if not authenticated)
      ],
      AllowedOAuthFlows: ['code'],
      AllowedOAuthScopes: ['email', 'openid', 'profile'],
      AllowedOAuthFlowsUserPoolClient: true,
      SupportedIdentityProviders: ['COGNITO'],
      ExplicitAuthFlows: [
        'ALLOW_USER_PASSWORD_AUTH',
        'ALLOW_USER_SRP_AUTH',
        'ALLOW_REFRESH_TOKEN_AUTH'
      ],
      PreventUserExistenceErrors: 'ENABLED',
      EnableTokenRevocation: true,
      EnablePropagateAdditionalUserContextData: false
    });

    const response = await client.send(command);
    console.log('✅ Successfully updated Cognito User Pool Client');
    console.log('📋 Updated configuration:');
    console.log(`   - Callback URLs: ${cloudfrontUrl}/, ${cloudfrontUrl}/auth/callback`);
    console.log(`   - Logout URLs: ${cloudfrontUrl}/`);
    console.log('🔄 Users will now be redirected to the home page after logout');
    
  } catch (error) {
    console.error('❌ Failed to update Cognito User Pool Client:', error);
    
    if (error.name === 'InvalidParameterException') {
      console.error('💡 Check that the URLs are valid and the client configuration is correct');
    } else if (error.name === 'ResourceNotFoundException') {
      console.error('💡 Check that the User Pool ID and Client ID are correct');
    } else if (error.name === 'UnauthorizedOperation') {
      console.error('💡 Check that your AWS credentials have the necessary permissions');
    }
    
    process.exit(1);
  }
}

// Run the update
updateCognitoLogoutRedirect().catch(console.error);