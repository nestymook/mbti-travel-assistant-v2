# Cognito Callback and Sign-out URLs Configuration

## 🎯 **Correct URLs for Your Setup**

### **CloudFront Domain**
`https://d39ank8zud5pbg.cloudfront.net`

### **Callback URLs (Sign-in redirect URLs)**
These are where Cognito redirects users **after successful login**:

```
https://d39ank8zud5pbg.cloudfront.net/
https://d39ank8zud5pbg.cloudfront.net/auth/callback
```

### **Sign-out URLs (Sign-out redirect URLs)**
These are where Cognito redirects users **after logout**:

```
https://d39ank8zud5pbg.cloudfront.net/
https://d39ank8zud5pbg.cloudfront.net/login
```

## 🔧 **Why These URLs?**

### **Callback URLs Explanation**

#### **1. Root Callback: `https://d39ank8zud5pbg.cloudfront.net/`**
- **Purpose**: Primary callback URL for OAuth flow
- **Used by**: Main login flow, OAuth test pages
- **Handles**: Authorization code processing at the root level
- **Router**: Vue router detects `?code=` parameter and redirects to auth callback handler

#### **2. Auth Callback: `https://d39ank8zud5pbg.cloudfront.net/auth/callback`**
- **Purpose**: Dedicated auth callback route in Vue app
- **Used by**: Vue router's auth callback handler
- **Handles**: Specialized OAuth callback processing
- **Component**: `AuthCallbackView.vue` processes the authentication

### **Sign-out URLs Explanation**

#### **1. Root Logout: `https://d39ank8zud5pbg.cloudfront.net/`**
- **Purpose**: Default logout destination
- **Behavior**: User lands on home page after logout
- **Router**: Will redirect to login if authentication is required

#### **2. Login Page: `https://d39ank8zud5pbg.cloudfront.net/login`**
- **Purpose**: Direct logout to login page
- **Behavior**: User lands directly on login page
- **Use Case**: Clear logout flow for re-authentication

## 📋 **Current Configuration Status**

### **✅ Your Current Callback URLs (CORRECT)**
```
https://d39ank8zud5pbg.cloudfront.net/
https://d39ank8zud5pbg.cloudfront.net/auth/callback
```

### **⚠️ Your Current Logout URLs (NEEDS IMPROVEMENT)**
```
https://d39ank8zud5pbg.cloudfront.net/
```

## 🔧 **Recommended Configuration Update**

### **Keep Callback URLs As-Is** ✅
Your callback URLs are correctly configured and should work perfectly.

### **Update Logout URLs** 📝
Add the login page as an additional logout destination:

**Current:**
```
https://d39ank8zud5pbg.cloudfront.net/
```

**Recommended:**
```
https://d39ank8zud5pbg.cloudfront.net/
https://d39ank8zud5pbg.cloudfront.net/login
```

## 🚀 **Update Command**

Run this command to add the login page as a logout URL:

```bash
aws cognito-idp update-user-pool-client \
  --user-pool-id us-east-1_KePRX24Bn \
  --client-id 1ofgeckef3po4i3us4j1m4chvd \
  --callback-urls "https://d39ank8zud5pbg.cloudfront.net/" "https://d39ank8zud5pbg.cloudfront.net/auth/callback" \
  --logout-urls "https://d39ank8zud5pbg.cloudfront.net/" "https://d39ank8zud5pbg.cloudfront.net/login" \
  --allowed-o-auth-flows "code" \
  --allowed-o-auth-scopes "email" "openid" "profile" \
  --allowed-o-auth-flows-user-pool-client \
  --supported-identity-providers "COGNITO" \
  --region us-east-1
```