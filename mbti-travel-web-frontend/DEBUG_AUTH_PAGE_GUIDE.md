# Auth Debug Page - User Guide

## 🔍 Overview

The Auth Debug page (`https://d39ank8zud5pbg.cloudfront.net/debug-auth.html`) is a powerful diagnostic tool designed to help troubleshoot authentication issues with the MBTI Travel Planner application.

## 🚀 How to Access

**URL**: `https://d39ank8zud5pbg.cloudfront.net/debug-auth.html`

You can access this page:
1. **Directly** - Navigate to the URL above
2. **From OAuth Test Page** - Click the "Debug Auth State" button
3. **From Main App** - Add `/debug-auth.html` to the domain

## 📊 What the Debug Page Shows

### 1. **Current URL Information**
Displays comprehensive details about the current page URL:

```
Full URL: https://d39ank8zud5pbg.cloudfront.net/debug-auth.html?code=abc123&state=xyz789
Pathname: /debug-auth.html
Search: ?code=abc123&state=xyz789
Hash: #access_token=token123
```

**What to Look For**:
- ✅ **Authorization Code** (`code` parameter) - Indicates successful OAuth redirect
- ❌ **Error Parameters** (`error`, `error_description`) - Shows OAuth failures
- 🔍 **State Parameter** - Used for CSRF protection
- 📍 **Hash Parameters** - Some OAuth flows use hash instead of query parameters

### 2. **URL Parameters Section**
Shows all query string parameters in an organized format:

```
code: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
state: randomStateString123
```

**Common Parameters**:
- `code` - Authorization code from successful OAuth flow
- `error` - Error type (e.g., `access_denied`, `invalid_request`)
- `error_description` - Human-readable error description
- `state` - CSRF protection token

### 3. **Local Storage Contents**
Displays all items stored in browser's localStorage:

```
aws-amplify-cache: {"tokens":{"accessToken":"...", "idToken":"..."}}
mbti-travel-user-preferences: {"theme":"light","language":"en"}
```

**Key Items to Check**:
- `aws-amplify-cache` - Amplify authentication tokens
- `aws-amplify-federatedInfo` - Federated identity information
- Application-specific storage keys

### 4. **Session Storage Contents**
Shows temporary session data:

```
oauth-state: randomStateString123
redirect-after-login: /itinerary/ENFP
```

**Important Items**:
- OAuth state information
- Temporary authentication data
- Redirect URLs

## 🛠️ How to Use for Troubleshooting

### Scenario 1: Login Not Working

**Steps**:
1. Try to log in normally
2. If login fails, go to debug page
3. **Check for**:
   - Error parameters in URL
   - Missing authorization code
   - Empty storage sections

**What You Might See**:
```
URL Parameters:
error: access_denied
error_description: User denied the request

Local Storage: (empty)
Session Storage: (empty)
```

**Solution**: User cancelled login or there's a Cognito configuration issue.

### Scenario 2: Successful Login But App Doesn't Recognize User

**Steps**:
1. Complete login flow
2. Go to debug page
3. **Check for**:
   - Authorization code in URL
   - Tokens in localStorage
   - User data in storage

**What You Might See**:
```
URL Parameters:
code: eyJhbGciOiJSUzI1NiIs...

Local Storage:
aws-amplify-cache: {"tokens":{"accessToken":"valid-token"}}

Session Storage: (empty)
```

**Solution**: Tokens are present but app state might not be updated. Try refreshing the main app.

### Scenario 3: Callback URL Issues

**Steps**:
1. After OAuth redirect
2. Check debug page immediately
3. **Look for**:
   - Correct domain in URL
   - Proper callback path
   - Expected parameters

**What You Might See**:
```
Full URL: https://wrong-domain.com/debug-auth.html?code=123
```

**Solution**: Callback URL mismatch in Cognito configuration.

### Scenario 4: Token Expiration Issues

**Steps**:
1. After some time using the app
2. When authentication seems to fail
3. **Check for**:
   - Expired tokens in localStorage
   - Missing refresh tokens

**What You Might See**:
```
Local Storage:
aws-amplify-cache: {"tokens":{"accessToken":"expired-token","refreshToken":null}}
```

**Solution**: Token refresh mechanism not working properly.

## 🔧 Available Actions

### 1. **Go to Main App**
- **Purpose**: Navigate back to the main application
- **When to Use**: After debugging, to test if issues are resolved

### 2. **Go to Login**
- **Purpose**: Navigate to the login page
- **When to Use**: To retry authentication process

### 3. **Clear All Storage**
- **Purpose**: Remove all stored authentication data
- **When to Use**: When tokens are corrupted or you need a fresh start
- **⚠️ Warning**: This will log you out completely

### 4. **Refresh Page**
- **Purpose**: Reload the debug page with current state
- **When to Use**: To see updated information after changes

## 📱 Real-Time Updates

The debug page automatically refreshes every 5 seconds to show:
- Updated storage contents
- New URL parameters (if page is redirected)
- Current authentication state

## 🔍 Advanced Debugging Techniques

### 1. **Monitor During OAuth Flow**
1. Open debug page in one tab
2. Start login process in another tab
3. Watch debug page for real-time updates
4. Observe how storage changes during authentication

### 2. **Compare Working vs Non-Working States**
1. Take screenshots of debug page when working
2. Compare with debug page when not working
3. Identify differences in storage or URL parameters

### 3. **Check Browser Developer Tools**
While on debug page:
1. Open browser DevTools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for failed requests
4. Check Application tab for detailed storage inspection

## 🚨 Common Issues and Solutions

### Issue: Empty Storage After Login
**Symptoms**: No tokens in localStorage/sessionStorage
**Possible Causes**:
- OAuth callback not processed correctly
- JavaScript errors preventing token storage
- CORS issues blocking token requests

**Solution**: Check browser console for errors, verify CORS configuration

### Issue: Authorization Code Present But No Tokens
**Symptoms**: `code` parameter in URL but no tokens in storage
**Possible Causes**:
- Token exchange failed
- Network connectivity issues
- Incorrect Cognito configuration

**Solution**: Use OAuth test page to manually test token exchange

### Issue: Tokens Present But App Shows "Not Logged In"
**Symptoms**: Valid tokens in storage but app doesn't recognize user
**Possible Causes**:
- App state not synchronized with storage
- Token format issues
- App logic errors

**Solution**: Refresh main app, check token validity

### Issue: Frequent "Session Expired" Messages
**Symptoms**: Tokens disappear frequently
**Possible Causes**:
- Short token expiration times
- Refresh token mechanism not working
- Browser clearing storage

**Solution**: Check token expiration times, verify refresh logic

## 📋 Debug Checklist

When troubleshooting authentication issues:

- [ ] **Check URL for OAuth parameters**
  - [ ] Authorization code present?
  - [ ] Error parameters present?
  - [ ] Correct callback domain?

- [ ] **Verify Storage Contents**
  - [ ] AWS Amplify tokens present?
  - [ ] Tokens not expired?
  - [ ] User data available?

- [ ] **Test Actions**
  - [ ] Clear storage and retry login
  - [ ] Check browser console for errors
  - [ ] Try different browser/incognito mode

- [ ] **Network Verification**
  - [ ] Check network requests in DevTools
  - [ ] Verify CORS headers
  - [ ] Confirm API endpoints accessible

## 🔗 Related Tools

- **OAuth Test Page**: `https://d39ank8zud5pbg.cloudfront.net/oauth-test.html`
  - More comprehensive OAuth flow testing
  - Manual token exchange testing
  - Configuration validation

- **Main Login Page**: `https://d39ank8zud5pbg.cloudfront.net/login`
  - Standard login interface
  - Production authentication flow

## 💡 Pro Tips

1. **Bookmark the Debug Page** - Keep it handy for quick troubleshooting
2. **Use Multiple Tabs** - Monitor debug page while testing login in another tab
3. **Take Screenshots** - Document working vs broken states for comparison
4. **Check Mobile** - Authentication issues might be device-specific
5. **Test Incognito Mode** - Eliminates browser cache/extension interference

## 🆘 When to Use Each Debug Tool

| Issue Type | Use Debug Auth Page | Use OAuth Test Page |
|------------|-------------------|-------------------|
| Login button not working | ✅ | ❌ |
| OAuth redirect issues | ✅ | ✅ |
| Token exchange problems | ❌ | ✅ |
| Storage/state issues | ✅ | ❌ |
| Configuration validation | ❌ | ✅ |
| General troubleshooting | ✅ | ✅ |

The Auth Debug page is your first stop for authentication troubleshooting - it provides a clear view of what's happening behind the scenes with your authentication state.