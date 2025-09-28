/**
 * Error Handling Example for MBTI Travel Assistant MCP
 * 
 * This example demonstrates comprehensive error handling patterns
 * for different types of errors that can occur when using the API.
 */

const axios = require('axios');

class APIError extends Error {
  constructor(message, type, code, suggestedActions = []) {
    super(message);
    this.name = 'APIError';
    this.type = type;
    this.code = code;
    this.suggestedActions = suggestedActions;
  }
}

class MBTIClientWithErrorHandling {
  constructor(baseURL, authTokenProvider) {
    this.baseURL = baseURL;
    this.authTokenProvider = authTokenProvider;
    
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'MBTITravelApp-ErrorHandling/1.0.0'
      }
    });
    
    this.setupInterceptors();
  }
  
  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        try {
          const token = await this.authTokenProvider();
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch (error) {
          throw new APIError(
            'Failed to obtain authentication token',
            'authentication_error',
            'AUTH_TOKEN_FAILED',
            ['Check authentication configuration', 'Verify token provider']
          );
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        return Promise.reject(this.handleError(error));
      }
    );
  }
  
  handleError(error) {
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data;
      const errorInfo = errorData.error || {};
      
      return new APIError(
        errorInfo.message || `HTTP ${error.response.status} Error`,
        errorInfo.error_type || 'server_error',
        errorInfo.error_code || `HTTP_${error.response.status}`,
        errorInfo.suggested_actions || []
      );
    } else if (error.request) {
      // Network error - no response received
      return new APIError(
        'Network error - unable to reach the service',
        'network_error',
        'NETWORK_ERROR',
        [
          'Check your internet connection',
          'Verify the service URL is correct',
          'Try again in a few moments'
        ]
      );
    } else {
      // Request configuration error
      return new APIError(
        error.message || 'Request configuration error',
        'client_error',
        'CLIENT_ERROR',
        ['Check request parameters', 'Verify client configuration']
      );
    }
  }
  
  async getRestaurantRecommendationSafely(request) {
    try {
      const response = await this.client.post('/invocations', request);
      return {
        success: true,
        data: response.data,
        error: null
      };
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error
      };
    }
  }
  
  async getRestaurantRecommendationWithRetry(request, maxRetries = 3) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await this.client.post('/invocations', request);
        return response.data;
      } catch (error) {
        lastError = error;
        
        // Don't retry on client errors (4xx) except rate limiting
        if (error.response?.status >= 400 && 
            error.response?.status < 500 && 
            error.response?.status !== 429) {
          throw error;
        }
        
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
          console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
          await this.sleep(delay);
        }
      }
    }
    
    throw lastError;
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Example error handling scenarios
async function demonstrateErrorHandling() {
  const client = new MBTIClientWithErrorHandling(
    process.env.API_BASE_URL || 'https://your-endpoint.amazonaws.com',
    async () => process.env.JWT_TOKEN || 'test-token'
  );
  
  console.log('🔧 Demonstrating Error Handling Patterns\n');
  
  // Scenario 1: Validation Error
  console.log('1. Testing validation error...');
  try {
    const result = await client.getRestaurantRecommendationSafely({
      meal_time: 'invalid_meal_time'
    });
    
    if (!result.success) {
      console.log(`❌ Validation Error: ${result.error.message}`);
      console.log(`   Type: ${result.error.type}`);
      console.log(`   Code: ${result.error.code}`);
      console.log('   Suggested Actions:');
      result.error.suggestedActions.forEach(action => {
        console.log(`   - ${action}`);
      });
    }
  } catch (error) {
    console.error('Unexpected error:', error.message);
  }
  console.log('');
  
  // Scenario 2: Authentication Error
  console.log('2. Testing authentication error...');
  const clientWithBadAuth = new MBTIClientWithErrorHandling(
    process.env.API_BASE_URL || 'https://your-endpoint.amazonaws.com',
    async () => 'invalid-token'
  );
  
  try {
    const result = await clientWithBadAuth.getRestaurantRecommendationSafely({
      district: 'Central district',
      meal_time: 'breakfast'
    });
    
    if (!result.success) {
      console.log(`❌ Authentication Error: ${result.error.message}`);
      console.log(`   Type: ${result.error.type}`);
      console.log(`   Code: ${result.error.code}`);
    }
  } catch (error) {
    console.error('Unexpected error:', error.message);
  }
  console.log('');
  
  // Scenario 3: Network Error
  console.log('3. Testing network error...');
  const clientWithBadURL = new MBTIClientWithErrorHandling(
    'https://non-existent-endpoint.example.com',
    async () => 'valid-token'
  );
  
  try {
    const result = await clientWithBadURL.getRestaurantRecommendationSafely({
      district: 'Central district',
      meal_time: 'breakfast'
    });
    
    if (!result.success) {
      console.log(`❌ Network Error: ${result.error.message}`);
      console.log(`   Type: ${result.error.type}`);
      console.log(`   Code: ${result.error.code}`);
      console.log('   Suggested Actions:');
      result.error.suggestedActions.forEach(action => {
        console.log(`   - ${action}`);
      });
    }
  } catch (error) {
    console.error('Unexpected error:', error.message);
  }
  console.log('');
  
  // Scenario 4: Retry Logic
  console.log('4. Testing retry logic...');
  try {
    // This will likely fail, but demonstrates retry logic
    const result = await client.getRestaurantRecommendationWithRetry({
      district: 'Central district',
      meal_time: 'breakfast'
    }, 2);
    
    console.log('✓ Request succeeded after retries');
  } catch (error) {
    console.log(`❌ Request failed after all retries: ${error.message}`);
    console.log(`   Type: ${error.type}`);
    console.log(`   Code: ${error.code}`);
  }
  console.log('');
  
  // Scenario 5: Graceful Degradation
  console.log('5. Demonstrating graceful degradation...');
  await demonstrateGracefulDegradation(client);
}

async function demonstrateGracefulDegradation(client) {
  const fallbackRecommendations = [
    {
      id: 'fallback_001',
      name: 'Local Favorite Restaurant',
      address: 'Popular dining area',
      district: 'Central district',
      meal_type: ['breakfast', 'lunch', 'dinner'],
      sentiment: { likes: 80, dislikes: 10, neutral: 10, total_responses: 100, positive_percentage: 90 },
      price_range: '$$',
      operating_hours: { monday: ['07:00-22:00'] },
      location_category: 'urban',
      metadata: { note: 'Fallback recommendation' }
    }
  ];
  
  try {
    const result = await client.getRestaurantRecommendationSafely({
      district: 'Central district',
      meal_time: 'breakfast'
    });
    
    if (result.success) {
      console.log('✓ API call successful, using live data');
      console.log(`  Recommended: ${result.data.recommendation?.name || 'None'}`);
    } else {
      console.log('❌ API call failed, using fallback data');
      console.log(`  Error: ${result.error.message}`);
      console.log('  Providing cached/fallback recommendations:');
      
      fallbackRecommendations.forEach(restaurant => {
        console.log(`  - ${restaurant.name} (${restaurant.district})`);
      });
      
      // In a real application, you might:
      // 1. Return cached data from previous successful calls
      // 2. Show a limited set of popular restaurants
      // 3. Display an offline message with basic recommendations
    }
  } catch (error) {
    console.error('Unexpected error in graceful degradation:', error.message);
  }
}

// Error handling utilities
class ErrorReporter {
  static logError(error, context = {}) {
    const errorReport = {
      timestamp: new Date().toISOString(),
      message: error.message,
      type: error.type || 'unknown',
      code: error.code || 'UNKNOWN',
      context: context,
      stack: error.stack
    };
    
    console.error('Error Report:', JSON.stringify(errorReport, null, 2));
    
    // In a real application, you might:
    // 1. Send error reports to monitoring service (e.g., Sentry, CloudWatch)
    // 2. Store errors in a database for analysis
    // 3. Alert development team for critical errors
  }
  
  static shouldRetry(error) {
    // Don't retry on client errors (4xx) except rate limiting
    if (error.response?.status >= 400 && error.response?.status < 500) {
      return error.response.status === 429; // Only retry on rate limiting
    }
    
    // Retry on server errors (5xx) and network errors
    return true;
  }
  
  static getRetryDelay(attempt, error) {
    // Use server-provided retry-after if available
    if (error.response?.headers['retry-after']) {
      return parseInt(error.response.headers['retry-after']) * 1000;
    }
    
    // Exponential backoff with jitter
    const baseDelay = 1000; // 1 second
    const maxDelay = 30000; // 30 seconds
    const exponentialDelay = Math.min(baseDelay * Math.pow(2, attempt - 1), maxDelay);
    
    // Add jitter (±25%)
    const jitter = exponentialDelay * 0.25 * (Math.random() * 2 - 1);
    return Math.max(0, exponentialDelay + jitter);
  }
}

// Run the demonstration
if (require.main === module) {
  demonstrateErrorHandling().catch(error => {
    ErrorReporter.logError(error, { scenario: 'error_handling_demo' });
  });
}

module.exports = { 
  MBTIClientWithErrorHandling, 
  APIError, 
  ErrorReporter 
};