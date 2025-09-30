# MBTI Travel Frontend - Cognito Authentication Setup

## Authentication Configuration

The MBTI Travel Web Frontend now uses **AWS Cognito** for authentication, sharing the same User Pool as the backend MCP server.

### Cognito User Pool Details

- **User Pool Name**: `restaurant-search-mcp-pool`
- **User Pool ID**: `us-east-1_wBAxW7yd4`
- **App Client Name**: `restaurant-search-mcp-client`
- **App Client ID**: `26k0pnja579pdpb1pt6savs27e`
- **Region**: `us-east-1`

### Authentication Features

✅ **Email-based Authentication**: Users sign in with email and password  
✅ **Secure Token Management**: JWT tokens managed by AWS Cognito  
✅ **Automatic Token Refresh**: Tokens refresh automatically  
✅ **Shared User Pool**: Same pool used by backend MCP server  
✅ **Password Policy**: Strong password requirements enforced  

### Test Credentials

For testing the authentication system:

- **Email**: `test@mbti-travel.com`
- **Password**: `TestPass1234!`
- **User ID**: `d4f874e8-8061-7075-3a90-6866bc59e2d5`

### Environment Configuration

The production environment (`.env.production`) is configured with:

```bash
# Authentication Configuration (Shared Restaurant Search MCP Pool)
VITE_COGNITO_USER_POOL_ID=us-east-1_wBAxW7yd4
VITE_COGNITO_CLIENT_ID=26k0pnja579pdpb1pt6savs27e
```

### Authentication Flow

1. **User Login**: User enters email and password on login page
2. **Cognito Validation**: AWS Cognito validates credentials
3. **Token Generation**: Cognito generates JWT access and refresh tokens
4. **Token Storage**: Tokens stored securely in browser
5. **API Requests**: Tokens included in API requests for authorization
6. **Auto Refresh**: Tokens automatically refreshed when needed

### Supported Authentication Methods

- ✅ **USER_PASSWORD_AUTH**: Direct username/password authentication
- ✅ **USER_SRP_AUTH**: Secure Remote Password protocol
- ✅ **REFRESH_TOKEN_AUTH**: Token refresh capability

### Security Features

- **Password Requirements**: Minimum 8 characters with uppercase, lowercase, numbers, and symbols
- **Token Expiration**: Access tokens expire after 60 minutes
- **Refresh Tokens**: Valid for 30 days
- **Secure Storage**: Tokens stored securely in browser
- **HTTPS Only**: All authentication requests over HTTPS

### Integration with Backend

The frontend shares the same Cognito User Pool as the backend MCP server, enabling:

- **Single Sign-On**: Users authenticate once for both frontend and backend
- **Consistent User Management**: Same user accounts across all services
- **Shared Authorization**: Same JWT tokens work for all API calls
- **Unified User Experience**: Seamless authentication flow

### Fallback Authentication

If Cognito is not configured or fails, the system falls back to mock authentication for development purposes:

- Mock users are created automatically
- No real authentication is performed
- Suitable for development and testing only

### Error Handling

The authentication system handles various error scenarios:

- **Invalid Credentials**: Clear error messages for wrong email/password
- **User Not Found**: Helpful messages for non-existent users
- **Password Requirements**: Guidance on password policy violations
- **Network Errors**: Graceful handling of connectivity issues
- **Token Expiration**: Automatic token refresh or re-authentication

### Deployment Status

✅ **Frontend Deployed**: http://mbti-travel-production-209803798463.s3-website-us-east-1.amazonaws.com  
✅ **Cognito Configured**: Shared User Pool active  
✅ **Test User Created**: Ready for authentication testing  
✅ **Error Handling Fixed**: Button styling and error display corrected  

### Testing the Authentication

1. **Visit the Website**: Navigate to the deployed frontend URL
2. **Click Login**: Go to the login page
3. **Enter Credentials**: Use the test credentials above
4. **Verify Login**: Should successfully authenticate and redirect to home page
5. **Test Logout**: Verify logout functionality works correctly

### Troubleshooting

#### Common Issues

1. **"Cognito service not configured"**
   - Check environment variables are set correctly
   - Verify User Pool ID and Client ID are valid

2. **"Invalid email or password"**
   - Verify test credentials are correct
   - Check if user exists in Cognito User Pool

3. **Network errors**
   - Verify AWS region is correct (us-east-1)
   - Check internet connectivity

4. **Token refresh failures**
   - Clear browser storage and re-login
   - Check token expiration settings

#### Debug Information

To debug authentication issues:

1. Open browser developer tools
2. Check Console tab for error messages
3. Check Network tab for failed requests
4. Verify environment variables in browser

### Next Steps

1. **Create Additional Users**: Add more test users as needed
2. **User Registration**: Implement user registration flow if required
3. **Password Reset**: Add password reset functionality
4. **Profile Management**: Add user profile editing capabilities
5. **Role-Based Access**: Implement user roles and permissions

---

**Last Updated**: December 30, 2024  
**Status**: ✅ ACTIVE AND DEPLOYED  
**Authentication Method**: AWS Cognito User Pool  
**Shared with Backend**: Yes (restaurant-search-mcp-pool)