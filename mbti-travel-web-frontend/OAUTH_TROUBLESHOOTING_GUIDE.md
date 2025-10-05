# OAuth "No Authorization Code" Troubleshooting Guide

## 🚨 **Issue Confirmed**
You're experiencing the "No authorization code found in URL" error, which means the OAuth flow is not completing successfully. The user is not being redirected back to your application with the authorization code after login.

## 🔍 **Root Cause Analysis**

### **What Should Happen:**
1. User clicks "Sign In" → Redirects to Cognito
2. User authenticates → Cognito validates credentials  
3. Cognito redirects back → URL contains `?code=abc123...`
4. Frontend processes code → Exchanges for tokens

### **What's Actually Happening:**
- User clicks "Sign In" ✅
- Redirects to Cognito ❓
- User authenticates ❓
- **Redirect back fails** ❌ ← **This is where it's breaking**

## 🧪 **Diagnostic Tools**

### **Primary Diagnostic Tool**
**URL**: `https://d39ank8zud5pbg.cloudfront.net/oauth-diagnostic.html`

This tool will help you identify exactly where the OAuth flow is breaking by testing each step individually.

### **Step-by-Step Testing Process**

#### **Step 1: Test Cognito Domain**
- Verifies that Cognito domain is accessible
- Tests: `https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com`

#### **Step 2: Test OIDC Configuration**
- Verifies OAuth endpoints are working
- Tests: `/.well-known/openid-configuration`

#### **Step 3: Generate Login URL**
- Creates proper OAuth login URL
- Verifies all parameters are correct

#### **Step 4: Test in New Tab**
- Opens login in separate tab
- Monitors for callback in original tab

#### **Step 5: Monitor for Callback**
- Real-time monitoring for OAuth parameters
- Detects both success and error callbacks

#### **Step 6: Direct Redirect Test**
- Tests full redirect flow in same tab
- Most comprehensive test

## 🔧 **Most Likely Causes**

### **1. Callback URL Mismatch (Most Common)**

**Issue**: Cognito is redirecting to wrong URL or URL format doesn't match

**Check**: Your current callback URLs in Cognito:
```
✅ https://d39ank8zud5pbg.cloudfront.net/
✅ https://d39ank8zud5pbg.cloudfront.net/auth/callback
```

**Potential Problems**:
- Trailing slash issues
- HTTP vs HTTPS mismatch
- Domain case sensitivity
- URL encoding issues

**Test**: Use diagnostic tool Step 3 to verify exact URL format

### **2. Browser Security/Privacy Settings**

**Issue**: Browser blocking redirects or cookies

**Symptoms**:
- Works in incognito mode but not regular mode
- Works in different browser
- Console shows security errors

**Solutions**:
- Test in incognito/private mode
- Disable ad blockers temporarily
- Check browser console for security errors
- Try different browser (Chrome, Firefox, Safari)

### **3. Network/Firewall Issues**

**Issue**: Corporate firewall or network blocking OAuth redirects

**Symptoms**:
- Works on mobile data but not office WiFi
- Timeout errors during redirect
- Network requests fail in browser DevTools

**Solutions**:
- Test on different network (mobile hotspot)
- Check with IT department about OAuth/Cognito domains
- Test from different location

### **4. Cognito Configuration Issues**

**Issue**: Cognito User Pool Client misconfigured

**Check These Settings**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_KePRX24Bn \
  --client-id 26k0pnja579pdpb1pt6savs27e \
  --region us-east-1
```

**Verify**:
- ✅ `AllowedOAuthFlows`: `["code"]`
- ✅ `AllowedOAuthScopes`: `["email", "openid", "profile"]`
- ✅ `AllowedOAuthFlowsUserPoolClient`: `true`
- ✅ `CallbackURLs`: Correct URLs
- ✅ `SupportedIdentityProviders`: `["COGNITO"]`

### **5. CloudFront/CORS Issues**

**Issue**: CloudFront blocking or modifying OAuth redirects

**Recently Fixed**: CORS headers policy applied
**Status**: Should be working now

**Verify**: Check if recent CloudFront changes have propagated (wait 10-15 minutes)

### **6. JavaScript Errors**

**Issue**: Frontend JavaScript errors preventing OAuth processing

**Check**:
- Browser console for JavaScript errors
- Network tab for failed requests
- Any ad blockers interfering with scripts

## 🧪 **Immediate Testing Steps**

### **Quick Test 1: Manual URL Test**
Copy and paste this URL directly in browser:
```
https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/login?client_id=26k0pnja579pdpb1pt6savs27e&response_type=code&scope=email+openid+profile&redirect_uri=https://d39ank8zud5pbg.cloudfront.net/
```

**Expected**: Should redirect to Cognito login page
**If fails**: Domain/configuration issue

### **Quick Test 2: Incognito Mode**
1. Open incognito/private browser window
2. Go to: `https://d39ank8zud5pbg.cloudfront.net/oauth-diagnostic.html`
3. Run Step 6 (Direct Redirect Test)

**If works in incognito**: Browser cache/extension issue
**If still fails**: Configuration issue

### **Quick Test 3: Different Browser**
Test the same flow in:
- Chrome
- Firefox  
- Safari
- Edge

**If works in one browser**: Browser-specific issue
**If fails in all**: Configuration issue

## 📊 **Diagnostic Results Interpretation**

### **All Tests Pass But Still No Code**
- **Likely**: Browser security settings
- **Solution**: Try incognito mode, different browser
- **Check**: Browser console for security errors

### **Domain/Well-Known Tests Fail**
- **Likely**: Network/firewall blocking Cognito
- **Solution**: Try different network, contact IT
- **Check**: Corporate firewall settings

### **Login URL Generation Fails**
- **Likely**: Configuration error in frontend
- **Solution**: Check environment variables
- **Check**: `.env.production` file

### **New Tab Opens But No Callback**
- **Likely**: Callback URL mismatch
- **Solution**: Verify exact callback URL format
- **Check**: Cognito User Pool Client settings

### **Direct Redirect Fails**
- **Likely**: Cognito configuration issue
- **Solution**: Verify User Pool Client settings
- **Check**: OAuth flows and scopes

## 🛠️ **Advanced Debugging**

### **Browser DevTools Investigation**

#### **Network Tab**:
1. Open DevTools (F12)
2. Go to Network tab
3. Start OAuth flow
4. Look for:
   - Failed requests (red entries)
   - Redirect chains
   - CORS errors
   - Timeout errors

#### **Console Tab**:
1. Look for JavaScript errors
2. Check for security warnings
3. Monitor during OAuth flow
4. Note any error messages

#### **Application Tab**:
1. Check Local Storage for tokens
2. Verify Session Storage
3. Check Cookies
4. Look for stored OAuth state

### **Cognito Domain Direct Test**

Test these URLs directly in browser:

#### **1. Well-Known Configuration**:
```
https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/.well-known/openid-configuration
```
**Expected**: JSON configuration response

#### **2. Authorization Endpoint**:
```
https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/oauth2/authorize?client_id=26k0pnja579pdpb1pt6savs27e&response_type=code&redirect_uri=https://d39ank8zud5pbg.cloudfront.net/
```
**Expected**: Redirect to login page

#### **3. Login Page**:
```
https://mbti-travel-oidc-334662794.auth.us-east-1.amazoncognito.com/login?client_id=26k0pnja579pdpb1pt6savs27e&response_type=code&scope=email+openid+profile&redirect_uri=https://d39ank8zud5pbg.cloudfront.net/
```
**Expected**: Cognito login form

## 🚀 **Next Steps**

### **Immediate Actions**:
1. **Use Diagnostic Tool**: `https://d39ank8zud5pbg.cloudfront.net/oauth-diagnostic.html`
2. **Test in Incognito Mode**: Rule out browser issues
3. **Try Different Browser**: Identify browser-specific problems
4. **Check Browser Console**: Look for JavaScript errors

### **If Still Failing**:
1. **Test Manual URLs**: Verify Cognito domain accessibility
2. **Check Network**: Try different network/location
3. **Verify Configuration**: Double-check Cognito settings
4. **Contact Support**: If all else fails

### **Success Indicators**:
- ✅ Diagnostic tool shows all tests passing
- ✅ Manual login URL redirects to Cognito
- ✅ After login, URL contains `?code=` parameter
- ✅ No JavaScript errors in browser console

## 📞 **Getting Help**

If the diagnostic tool doesn't identify the issue:

1. **Run Full Diagnostic**: Complete all 6 steps
2. **Screenshot Results**: Capture any error messages
3. **Browser Console**: Copy any error messages
4. **Network Tab**: Note any failed requests
5. **Test Environment**: Note browser, OS, network type

The diagnostic tool at `https://d39ank8zud5pbg.cloudfront.net/oauth-diagnostic.html` will help pinpoint exactly where the OAuth flow is breaking!