# MBTI Travel Assistant MCP - Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting information for common issues encountered when using the MBTI Travel Assistant MCP API. It includes diagnostic steps, solutions, and preventive measures.

## Quick Diagnostic Checklist

Before diving into specific issues, run through this quick checklist:

1. **Service Health**: Check if the service is running
   ```bash
   curl -X GET https://your-endpoint.amazonaws.com/health
   ```

2. **Authentication**: Verify your JWT token is valid
   ```bash
   # Decode JWT token (without verification)
   echo "YOUR_JWT_TOKEN" | cut -d. -f2 | base64 -d | jq .
   ```

3. **Network Connectivity**: Test basic connectivity
   ```bash
   ping your-endpoint.amazonaws.com
   ```

4. **Request Format**: Validate your request payload
   ```bash
   echo '{"district": "Central district", "meal_time": "breakfast"}' | jq .
   ```

## Common Issues and Solutions

### 1. Authentication Errors

#### Issue: 401 Unauthorized - "AUTH_FAILED"

**Symptoms:**
- HTTP 401 responses
- Error message: "JWT token validation failed"
- Error code: "AUTH_FAILED"

**Common Causes:**
- Expired JWT token
- Invalid token signature
- Malformed Authorization header
- Incorrect Cognito configuration

**Solutions:**

1. **Check Token Expiration:**
   ```javascript
   // JavaScript example
   function isTokenExpired(token) {
     try {
       const payload = JSON.parse(atob(token.split('.')[1]));
       return Date.now() >= payload.exp * 1000;
     } catch (e) {
       return true;
     }
   }
   ```

2. **Verify Authorization Header Format:**
   ```bash
   # Correct format
   Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
   
   # Common mistakes
   Authorization: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...  # Missing "Bearer "
   Authorization: Bearer: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...  # Extra colon
   ```

3. **Refresh Token Logic:**
   ```python
   # Python example
   async def get_valid_token(self):
       if self.is_token_expired():
           await self.refresh_token()
       return self.access_token
   ```

4. **Validate Cognito Configuration:**
   ```bash
   # Check Cognito User Pool configuration
   aws cognito-idp describe-user-pool --user-pool-id YOUR_POOL_ID
   ```

#### Issue: 401 Unauthorized - "AUTH_MISSING"

**Symptoms:**
- HTTP 401 responses
- Error message: "Authentication token is required"
- Error code: "AUTH_MISSING"

**Solutions:**
1. Ensure Authorization header is included in all requests
2. Check if authentication is required in your environment
3. Verify token is being passed correctly through your HTTP client

### 2. Validation Errors

#### Issue: 400 Bad Request - "VALIDATION_FAILED"

**Symptoms:**
- HTTP 400 responses
- Error message describing validation failure
- Error code: "VALIDATION_FAILED"

**Common Validation Issues:**

1. **Missing Required Parameters:**
   ```json
   // ❌ Invalid - no search parameters
   {
     "user_context": {"user_id": "123"}
   }
   
   // ✅ Valid - has district
   {
     "district": "Central district",
     "user_context": {"user_id": "123"}
   }
   ```

2. **Invalid Meal Time:**
   ```json
   // ❌ Invalid meal time
   {
     "district": "Central district",
     "meal_time": "brunch"
   }
   
   // ✅ Valid meal times
   {
     "district": "Central district",
     "meal_time": "breakfast"  // or "lunch", "dinner"
   }
   ```

3. **Empty or Invalid District:**
   ```json
   // ❌ Empty district
   {
     "district": "",
     "meal_time": "breakfast"
   }
   
   // ✅ Valid district
   {
     "district": "Central district",
     "meal_time": "breakfast"
   }
   ```

**Solutions:**
1. Validate input parameters before sending requests
2. Use the suggested actions from error responses
3. Implement client-side validation

### 3. Service Unavailability

#### Issue: 503 Service Unavailable - "MCP_SERVICE_UNAVAILABLE"

**Symptoms:**
- HTTP 503 responses
- Error message: "restaurant-search-mcp: Connection timeout"
- Error code: "MCP_SERVICE_UNAVAILABLE"

**Diagnostic Steps:**

1. **Check Service Health:**
   ```bash
   curl -X GET https://your-endpoint.amazonaws.com/health | jq '.components'
   ```

2. **Verify MCP Server Status:**
   ```bash
   # Check if MCP servers are responding
   curl -X POST https://search-mcp-endpoint.com/health
   curl -X POST https://reasoning-mcp-endpoint.com/health
   ```

3. **Check Network Connectivity:**
   ```bash
   # Test connectivity to MCP servers
   telnet search-mcp-endpoint.com 443
   telnet reasoning-mcp-endpoint.com 443
   ```

**Solutions:**

1. **Implement Retry Logic:**
   ```javascript
   async function makeRequestWithRetry(requestFn, maxRetries = 3) {
     for (let attempt = 1; attempt <= maxRetries; attempt++) {
       try {
         return await requestFn();
       } catch (error) {
         if (attempt === maxRetries) throw error;
         
         const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
         await new Promise(resolve => setTimeout(resolve, delay));
       }
     }
   }
   ```

2. **Circuit Breaker Pattern:**
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
   ```

3. **Graceful Degradation:**
   ```javascript
   async function getRecommendationWithFallback(request) {
     try {
       return await apiClient.getRecommendation(request);
     } catch (error) {
       if (error.code === 'MCP_SERVICE_UNAVAILABLE') {
         return getCachedRecommendation(request) || getDefaultRecommendation();
       }
       throw error;
     }
   }
   ```

### 4. Rate Limiting

#### Issue: 429 Too Many Requests - "RATE_LIMIT_EXCEEDED"

**Symptoms:**
- HTTP 429 responses
- Error message: "Rate limit exceeded: 100 requests per minute"
- Error code: "RATE_LIMIT_EXCEEDED"

**Solutions:**

1. **Implement Exponential Backoff:**
   ```python
   import asyncio
   import random
   
   async def make_request_with_backoff(request_func, max_retries=5):
       for attempt in range(max_retries):
           try:
               return await request_func()
           except RateLimitError as e:
               if attempt == max_retries - 1:
                   raise
               
               # Exponential backoff with jitter
               delay = min(2 ** attempt + random.uniform(0, 1), 60)
               await asyncio.sleep(delay)
   ```

2. **Request Queuing:**
   ```javascript
   class RequestQueue {
     constructor(maxConcurrent = 5, delayBetweenRequests = 200) {
       this.maxConcurrent = maxConcurrent;
       this.delayBetweenRequests = delayBetweenRequests;
       this.queue = [];
       this.activeRequests = 0;
     }
     
     async enqueue(requestFn) {
       return new Promise((resolve, reject) => {
         this.queue.push({ requestFn, resolve, reject });
         this.processQueue();
       });
     }
     
     async processQueue() {
       if (this.activeRequests >= this.maxConcurrent || this.queue.length === 0) {
         return;
       }
       
       const { requestFn, resolve, reject } = this.queue.shift();
       this.activeRequests++;
       
       try {
         const result = await requestFn();
         resolve(result);
       } catch (error) {
         reject(error);
       } finally {
         this.activeRequests--;
         setTimeout(() => this.processQueue(), this.delayBetweenRequests);
       }
     }
   }
   ```

3. **Caching Strategy:**
   ```javascript
   class CachedAPIClient {
     constructor(client, cacheTTL = 5 * 60 * 1000) {
       this.client = client;
       this.cache = new Map();
       this.cacheTTL = cacheTTL;
     }
     
     generateCacheKey(request) {
       return JSON.stringify(request);
     }
     
     async getRecommendation(request) {
       const cacheKey = this.generateCacheKey(request);
       const cached = this.cache.get(cacheKey);
       
       if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
         return cached.data;
       }
       
       const result = await this.client.getRecommendation(request);
       this.cache.set(cacheKey, { data: result, timestamp: Date.now() });
       
       return result;
     }
   }
   ```

### 5. Timeout Issues

#### Issue: 504 Gateway Timeout - "MCP_TIMEOUT"

**Symptoms:**
- HTTP 504 responses
- Error message: "MCP server request timeout"
- Error code: "MCP_TIMEOUT"
- Long response times (>5 seconds)

**Diagnostic Steps:**

1. **Check Response Times:**
   ```bash
   # Test response time
   curl -w "Response time: %{time_total}s\n" \
        -X POST https://your-endpoint.amazonaws.com/invocations \
        -H "Authorization: Bearer YOUR_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"district": "Central district", "meal_time": "breakfast"}'
   ```

2. **Monitor Service Health:**
   ```bash
   # Check component response times
   curl -X GET https://your-endpoint.amazonaws.com/health | jq '.components'
   ```

**Solutions:**

1. **Adjust Client Timeouts:**
   ```javascript
   const client = axios.create({
     timeout: 15000, // 15 seconds
     headers: { 'Content-Type': 'application/json' }
   });
   ```

2. **Implement Timeout Handling:**
   ```python
   import asyncio
   
   async def make_request_with_timeout(request_func, timeout=10):
       try:
           return await asyncio.wait_for(request_func(), timeout=timeout)
       except asyncio.TimeoutError:
           raise TimeoutError(f"Request timed out after {timeout} seconds")
   ```

3. **Use Streaming for Long Operations:**
   ```javascript
   // For long-running requests, consider streaming responses
   const response = await fetch('/invocations', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify(request)
   });
   
   const reader = response.body.getReader();
   // Process streaming response
   ```

### 6. Response Format Issues

#### Issue: Malformed JSON Response

**Symptoms:**
- JSON parsing errors
- Unexpected response structure
- Missing required fields

**Diagnostic Steps:**

1. **Validate Response Structure:**
   ```javascript
   function validateResponse(response) {
     const required = ['recommendation', 'candidates', 'metadata'];
     const missing = required.filter(field => !(field in response));
     
     if (missing.length > 0) {
       throw new Error(`Missing required fields: ${missing.join(', ')}`);
     }
     
     if (response.candidates && response.candidates.length > 19) {
       console.warn('Candidates list exceeds expected maximum of 19');
     }
     
     return true;
   }
   ```

2. **Check Content-Type Headers:**
   ```bash
   curl -I https://your-endpoint.amazonaws.com/invocations
   # Should return: Content-Type: application/json
   ```

**Solutions:**

1. **Robust Response Parsing:**
   ```javascript
   async function parseResponse(response) {
     try {
       const data = await response.json();
       validateResponse(data);
       return data;
     } catch (error) {
       console.error('Response parsing failed:', error);
       throw new Error('Invalid response format');
     }
   }
   ```

2. **Fallback Response Handling:**
   ```python
   def handle_response(response):
       try:
           data = response.json()
           
           # Ensure required fields exist
           if 'recommendation' not in data:
               data['recommendation'] = None
           if 'candidates' not in data:
               data['candidates'] = []
           if 'metadata' not in data:
               data['metadata'] = {'total_found': 0, 'processing_time_ms': 0}
               
           return data
       except json.JSONDecodeError:
           return {
               'recommendation': None,
               'candidates': [],
               'metadata': {'total_found': 0, 'processing_time_ms': 0},
               'error': {'message': 'Invalid response format'}
           }
   ```

## Performance Issues

### Slow Response Times

**Symptoms:**
- Response times > 5 seconds
- Timeouts on client side
- Poor user experience

**Diagnostic Steps:**

1. **Measure Response Times:**
   ```bash
   # Measure different components
   time curl -X POST https://your-endpoint.amazonaws.com/invocations \
        -H "Authorization: Bearer YOUR_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"district": "Central district", "meal_time": "breakfast"}'
   ```

2. **Check Cache Hit Rates:**
   ```javascript
   // Monitor cache performance
   const response = await client.getRecommendation(request);
   console.log('Cache hit:', response.metadata.cache_hit);
   console.log('Processing time:', response.metadata.processing_time_ms);
   ```

**Solutions:**

1. **Implement Client-Side Caching:**
   ```javascript
   class PerformantClient {
     constructor(baseClient) {
       this.baseClient = baseClient;
       this.cache = new Map();
       this.pendingRequests = new Map();
     }
     
     async getRecommendation(request) {
       const key = this.getCacheKey(request);
       
       // Return cached result if available
       if (this.cache.has(key)) {
         return this.cache.get(key);
       }
       
       // Deduplicate concurrent requests
       if (this.pendingRequests.has(key)) {
         return this.pendingRequests.get(key);
       }
       
       // Make request
       const promise = this.baseClient.getRecommendation(request);
       this.pendingRequests.set(key, promise);
       
       try {
         const result = await promise;
         this.cache.set(key, result);
         return result;
       } finally {
         this.pendingRequests.delete(key);
       }
     }
   }
   ```

2. **Request Optimization:**
   ```javascript
   // Batch similar requests
   class BatchingClient {
     constructor(baseClient, batchSize = 5, batchTimeout = 100) {
       this.baseClient = baseClient;
       this.batchSize = batchSize;
       this.batchTimeout = batchTimeout;
       this.pendingRequests = [];
       this.batchTimer = null;
     }
     
     async getRecommendation(request) {
       return new Promise((resolve, reject) => {
         this.pendingRequests.push({ request, resolve, reject });
         
         if (this.pendingRequests.length >= this.batchSize) {
           this.processBatch();
         } else {
           this.scheduleBatch();
         }
       });
     }
   }
   ```

## Monitoring and Debugging

### Enable Debug Logging

1. **Client-Side Logging:**
   ```javascript
   const client = axios.create({
     baseURL: 'https://your-endpoint.amazonaws.com'
   });
   
   // Request logging
   client.interceptors.request.use(request => {
     console.log('API Request:', {
       method: request.method,
       url: request.url,
       headers: request.headers,
       data: request.data
     });
     return request;
   });
   
   // Response logging
   client.interceptors.response.use(
     response => {
       console.log('API Response:', {
         status: response.status,
         headers: response.headers,
         data: response.data
       });
       return response;
     },
     error => {
       console.error('API Error:', {
         status: error.response?.status,
         data: error.response?.data,
         message: error.message
       });
       return Promise.reject(error);
     }
   );
   ```

2. **Server-Side Monitoring:**
   ```bash
   # Check CloudWatch logs
   aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/mbti-travel-assistant"
   
   # Tail logs in real-time
   aws logs tail /aws/lambda/mbti-travel-assistant --follow
   ```

### Health Check Monitoring

```bash
#!/bin/bash
# health-check-monitor.sh

ENDPOINT="https://your-endpoint.amazonaws.com"
ALERT_EMAIL="admin@yourcompany.com"

while true; do
  HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$ENDPOINT/health")
  
  if [ "$HEALTH_STATUS" != "200" ]; then
    echo "$(date): Health check failed with status $HEALTH_STATUS"
    
    # Send alert (replace with your alerting mechanism)
    echo "MBTI Travel Assistant health check failed" | mail -s "Service Alert" "$ALERT_EMAIL"
  else
    echo "$(date): Health check passed"
  fi
  
  sleep 60  # Check every minute
done
```

## Prevention Strategies

### 1. Implement Circuit Breakers

```javascript
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000) {
    this.threshold = threshold;
    this.timeout = timeout;
    this.failureCount = 0;
    this.lastFailureTime = null;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
  }
  
  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }
    
    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }
  
  onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
    }
  }
}
```

### 2. Implement Proper Error Handling

```python
class APIClient:
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 1,
            'status_forcelist': [500, 502, 503, 504]
        }
    
    async def make_request(self, request):
        for attempt in range(self.retry_config['max_retries']):
            try:
                response = await self._execute_request(request)
                return response
            except Exception as e:
                if attempt == self.retry_config['max_retries'] - 1:
                    raise
                
                if self._should_retry(e):
                    delay = self.retry_config['backoff_factor'] * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
    
    def _should_retry(self, error):
        # Implement retry logic based on error type
        return hasattr(error, 'status_code') and error.status_code in [500, 502, 503, 504]
```

### 3. Monitor Key Metrics

```javascript
class MetricsCollector {
  constructor() {
    this.metrics = {
      requestCount: 0,
      errorCount: 0,
      totalResponseTime: 0,
      cacheHits: 0
    };
  }
  
  recordRequest(responseTime, success, cacheHit) {
    this.metrics.requestCount++;
    this.metrics.totalResponseTime += responseTime;
    
    if (!success) {
      this.metrics.errorCount++;
    }
    
    if (cacheHit) {
      this.metrics.cacheHits++;
    }
  }
  
  getMetrics() {
    return {
      ...this.metrics,
      averageResponseTime: this.metrics.totalResponseTime / this.metrics.requestCount,
      errorRate: this.metrics.errorCount / this.metrics.requestCount,
      cacheHitRate: this.metrics.cacheHits / this.metrics.requestCount
    };
  }
}
```

## Getting Help

### Support Channels

1. **Documentation**: Review API documentation and usage examples
2. **Health Endpoint**: Check service status at `/health`
3. **Logs**: Review CloudWatch logs for detailed error information
4. **Monitoring**: Check service metrics and dashboards

### Reporting Issues

When reporting issues, include:

1. **Request Details:**
   - Full request payload
   - Headers (excluding sensitive tokens)
   - Timestamp of the request

2. **Response Details:**
   - HTTP status code
   - Response body
   - Response headers

3. **Environment Information:**
   - Client library version
   - Programming language/runtime
   - Network configuration

4. **Error Context:**
   - Steps to reproduce
   - Frequency of occurrence
   - Impact on your application

### Emergency Contacts

For critical issues affecting production systems:

1. Check service status page
2. Review recent deployments or changes
3. Implement fallback mechanisms
4. Contact support with detailed incident information

---

This troubleshooting guide should help you diagnose and resolve most common issues with the MBTI Travel Assistant MCP API. Keep this guide updated as new issues and solutions are discovered.