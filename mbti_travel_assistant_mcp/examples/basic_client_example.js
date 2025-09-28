/**
 * Basic Client Example for MBTI Travel Assistant MCP
 * 
 * This example demonstrates how to create a simple client to interact
 * with the MBTI Travel Assistant API for restaurant recommendations.
 */

const axios = require('axios');

class MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider) {
    this.baseURL = baseURL;
    this.authTokenProvider = authTokenProvider;
    
    // Create axios instance with default configuration
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 10000, // 10 second timeout
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'MBTITravelApp-Example/1.0.0'
      }
    });
    
    this.setupInterceptors();
  }
  
  setupInterceptors() {
    // Request interceptor to add authentication
    this.client.interceptors.request.use(async (config) => {
      try {
        const token = await this.authTokenProvider();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (error) {
        console.error('Failed to get auth token:', error.message);
      }
      return config;
    });
    
    // Response interceptor for logging
    this.client.interceptors.response.use(
      (response) => {
        console.log(`✓ API call successful: ${response.config.method?.toUpperCase()} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error(`✗ API call failed: ${error.config?.method?.toUpperCase()} ${error.config?.url}`);
        console.error(`Error: ${error.response?.status} - ${error.response?.data?.error?.message || error.message}`);
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Get restaurant recommendation based on district and meal time
   */
  async getRestaurantRecommendation(district, mealTime) {
    try {
      const response = await this.client.post('/invocations', {
        district: district,
        meal_time: mealTime
      });
      
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get recommendation: ${error.message}`);
    }
  }
  
  /**
   * Search restaurants using natural language query
   */
  async searchWithNaturalLanguage(query) {
    try {
      const response = await this.client.post('/invocations', {
        natural_language_query: query
      });
      
      return response.data;
    } catch (error) {
      throw new Error(`Natural language search failed: ${error.message}`);
    }
  }
  
  /**
   * Get health status of the service
   */
  async getHealthStatus() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }
}

// Example usage
async function main() {
  // Mock JWT token provider (replace with your actual implementation)
  const getAuthToken = async () => {
    // In a real application, this would:
    // 1. Check if current token is still valid
    // 2. Refresh token if needed
    // 3. Return valid JWT token
    return process.env.JWT_TOKEN || 'your-jwt-token-here';
  };
  
  // Create client instance
  const client = new MBTITravelAssistantClient(
    process.env.API_BASE_URL || 'https://your-agentcore-endpoint.amazonaws.com',
    getAuthToken
  );
  
  console.log('🚀 Starting MBTI Travel Assistant Example\n');
  
  try {
    // Example 1: Check service health
    console.log('1. Checking service health...');
    const health = await client.getHealthStatus();
    console.log(`Service status: ${health.status}`);
    console.log(`Environment: ${health.environment}`);
    console.log('');
    
    // Example 2: Get recommendation by district and meal time
    console.log('2. Getting breakfast recommendations in Central district...');
    const recommendation1 = await client.getRestaurantRecommendation('Central district', 'breakfast');
    
    if (recommendation1.recommendation) {
      console.log(`✓ Recommended: ${recommendation1.recommendation.name}`);
      console.log(`  Address: ${recommendation1.recommendation.address}`);
      console.log(`  Sentiment: ${recommendation1.recommendation.sentiment.positive_percentage.toFixed(1)}% positive`);
      console.log(`  Price Range: ${recommendation1.recommendation.price_range}`);
    }
    
    console.log(`Found ${recommendation1.candidates.length} alternative options`);
    console.log(`Processing time: ${recommendation1.metadata.processing_time_ms}ms`);
    console.log('');
    
    // Example 3: Natural language search
    console.log('3. Searching with natural language query...');
    const query = "Find me a good Italian restaurant for dinner in Causeway Bay";
    const recommendation2 = await client.searchWithNaturalLanguage(query);
    
    if (recommendation2.recommendation) {
      console.log(`✓ Recommended: ${recommendation2.recommendation.name}`);
      console.log(`  District: ${recommendation2.recommendation.district}`);
      console.log(`  Cuisine: ${recommendation2.recommendation.metadata?.cuisine_type || 'Not specified'}`);
    }
    
    console.log(`Query: "${query}"`);
    console.log(`Found ${recommendation2.candidates.length} alternatives`);
    console.log('');
    
    // Example 4: Show candidate restaurants
    console.log('4. Top 3 candidate restaurants:');
    const topCandidates = recommendation2.candidates.slice(0, 3);
    topCandidates.forEach((restaurant, index) => {
      console.log(`  ${index + 1}. ${restaurant.name}`);
      console.log(`     ${restaurant.address}`);
      console.log(`     ${restaurant.sentiment.positive_percentage.toFixed(1)}% positive (${restaurant.sentiment.total_responses} reviews)`);
      console.log('');
    });
    
  } catch (error) {
    console.error('❌ Example failed:', error.message);
    
    // Show error details if available
    if (error.response?.data?.error) {
      const errorInfo = error.response.data.error;
      console.error(`Error Type: ${errorInfo.error_type}`);
      console.error(`Error Code: ${errorInfo.error_code}`);
      
      if (errorInfo.suggested_actions) {
        console.error('Suggested Actions:');
        errorInfo.suggested_actions.forEach(action => {
          console.error(`  - ${action}`);
        });
      }
    }
  }
}

// Run the example
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { MBTITravelAssistantClient };