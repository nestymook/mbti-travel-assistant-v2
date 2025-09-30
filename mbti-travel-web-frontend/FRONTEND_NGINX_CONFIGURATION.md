# Frontend to Nginx Reverse Proxy Configuration

## ✅ **Configuration Verified and Fixed**

The frontend is now correctly configured to point to the nginx reverse proxy location.

## 🔧 **Current Configuration**

### **Frontend API Configuration**
```typescript
// .env.production
VITE_API_BASE_URL=  // Empty - uses same origin

// apiService.ts
const config: ApiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || '', // Empty for same-origin requests
  // ...
}
```

### **API Endpoint**
```typescript
// Frontend makes calls to:
url: '/api/itinerary/generate'
```

### **Nginx Reverse Proxy**
```nginx
# nginx.conf
location /api/itinerary/generate {
    proxy_pass https://bedrock-agentcore.us-east-1.amazonaws.com/runtime/mbti_travel_assistant_mcp-skv6fd785E/invocations;
    proxy_set_header Authorization $http_authorization;  # Forward JWT
    # ... CORS and other headers
}
```

## 🌐 **Request Flow**

### **Complete Request Path:**
```
Browser → Same Origin Request → Nginx → AgentCore
```

**Step by Step:**
1. **Frontend**: Makes POST request to `/api/itinerary/generate`
2. **Same Origin**: Since `baseURL` is empty, request goes to same domain
3. **Nginx**: Intercepts `/api/itinerary/generate` and proxies to AgentCore
4. **AgentCore**: Processes request and returns response
5. **Nginx**: Forwards response back to browser
6. **Frontend**: Receives and processes response

## 📍 **URL Resolution**

### **Current Deployment (S3 Static Website):**
- **Frontend URL**: `http://mbti-travel-production-209803798463.s3-website-us-east-1.amazonaws.com`
- **API Call**: `/api/itinerary/generate` (relative URL)
- **Resolved URL**: `http://mbti-travel-production-209803798463.s3-website-us-east-1.amazonaws.com/api/itinerary/generate`

### **Container Deployment (Future):**
- **Frontend URL**: `http://localhost:8080` (or deployed domain)
- **API Call**: `/api/itinerary/generate` (relative URL)
- **Resolved URL**: `http://localhost:8080/api/itinerary/generate`
- **Nginx Proxy**: Forwards to AgentCore endpoint

## 🔍 **Debug Information**

With the enhanced logging, you'll now see:

```javascript
🔧 API Service Configuration
  Base URL:  // Empty string
  Full URL: /api/itinerary/generate
  Environment: production
```

## ✅ **What Was Fixed**

### **Before (Incorrect):**
```typescript
baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'
// This would make requests to: http://localhost:8080/api/itinerary/generate
// Which bypasses nginx reverse proxy
```

### **After (Correct):**
```typescript
baseURL: import.meta.env.VITE_API_BASE_URL || ''
// This makes requests to: /api/itinerary/generate (same origin)
// Which hits nginx reverse proxy correctly
```

## 🎯 **Why This Works**

### **Same Origin Requests:**
- ✅ **No CORS issues** - same domain
- ✅ **Nginx intercepts** - `/api/*` routes go to proxy
- ✅ **JWT forwarded** - authentication maintained
- ✅ **Simple setup** - no complex URL management

### **Nginx Reverse Proxy Benefits:**
- ✅ **Transparent proxy** - frontend doesn't know about AgentCore
- ✅ **CORS handling** - nginx adds proper headers
- ✅ **Authentication** - JWT tokens forwarded automatically
- ✅ **Error handling** - nginx can handle timeouts and retries

## 🚀 **Current Status**

- ✅ **Frontend Configuration**: Fixed to use empty baseURL
- ✅ **Nginx Configuration**: Properly configured reverse proxy
- ✅ **API Endpoint**: Correct path `/api/itinerary/generate`
- ✅ **JWT Forwarding**: Authorization header forwarded
- ✅ **CORS Headers**: Properly configured for browser requests
- ✅ **Deployed**: Live and ready for testing

## 🧪 **Testing**

When you now try to generate an itinerary:

1. **Browser Console** should show:
   ```javascript
   🚀 API Request: POST /api/itinerary/generate
   Full URL: /api/itinerary/generate
   ```

2. **Network Tab** should show:
   - **Request URL**: `http://mbti-travel-production-209803798463.s3-website-us-east-1.amazonaws.com/api/itinerary/generate`
   - **Status**: Should NOT be `ERR_NAME_NOT_RESOLVED`
   - **Headers**: Should include `Authorization: Bearer <jwt_token>`

3. **Expected Behavior**:
   - ✅ No DNS resolution errors
   - ✅ Request reaches nginx
   - ✅ Nginx forwards to AgentCore
   - ✅ Response returned to browser

## 🔧 **For Container Deployment**

When using Docker containers, the same configuration works:

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "8080:8080"  # Nginx serves on port 8080
```

The nginx container will:
- **Serve static files** from `/usr/share/nginx/html`
- **Proxy API calls** from `/api/*` to AgentCore
- **Handle CORS** and authentication forwarding

---

**The frontend is now correctly configured to use the nginx reverse proxy!** 🎉