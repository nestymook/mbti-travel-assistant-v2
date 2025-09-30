# 🔍 Auth Debug - Quick Reference

## 🚀 Quick Access
**Debug Page**: `https://d39ank8zud5pbg.cloudfront.net/debug-auth.html`
**OAuth Test**: `https://d39ank8zud5pbg.cloudfront.net/oauth-test.html`

## 🔧 Common Troubleshooting Steps

### 1. **Login Not Working**
```
1. Go to debug page
2. Look for error parameters in URL
3. Check if storage is empty
4. Clear storage and retry
```

### 2. **Stuck on "Authenticating..."**
```
1. Check debug page for authorization code
2. Look for JavaScript errors in console
3. Verify network requests in DevTools
4. Try manual token exchange on OAuth test page
```

### 3. **"Session Expired" Issues**
```
1. Check token expiration in localStorage
2. Look for refresh tokens
3. Clear storage and re-login
4. Check if tokens are being properly refreshed
```

## 📊 What to Look For

### ✅ **Good Signs**
- Authorization code in URL: `?code=eyJhbGci...`
- Tokens in localStorage: `aws-amplify-cache`
- No error parameters
- User data present

### ❌ **Problem Signs**
- Error in URL: `?error=access_denied`
- Empty localStorage/sessionStorage
- Expired tokens
- Missing refresh tokens

## 🛠️ Quick Actions

| Action | When to Use |
|--------|-------------|
| **Clear All Storage** | Corrupted tokens, fresh start needed |
| **Go to Main App** | Test if issues resolved |
| **Go to Login** | Retry authentication |
| **Refresh Page** | Update debug information |

## 🚨 Emergency Reset
```
1. Go to debug page
2. Click "Clear All Storage"
3. Go to login page
4. Complete fresh login
5. Check debug page again
```

## 📱 Browser DevTools Checklist
- **Console**: JavaScript errors?
- **Network**: Failed requests?
- **Application**: Storage contents?
- **Security**: CORS issues?

## 🔗 Quick Links
- [Full Debug Guide](DEBUG_AUTH_PAGE_GUIDE.md)
- [OAuth Fix Summary](COGNITO_OAUTH_FIX_SUMMARY.md)
- [Main App](https://d39ank8zud5pbg.cloudfront.net/)
- [Login Page](https://d39ank8zud5pbg.cloudfront.net/login)