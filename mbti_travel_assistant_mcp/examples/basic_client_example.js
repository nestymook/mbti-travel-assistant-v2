/**
 * Basic Client Example for MBTI Travel Assistant MCP
 * 
 * This example demonstrates how to create a simple client to interact
 * with the MBTI Travel Assistant API for generating 3-day travel itineraries
 * based on MBTI personality types.
 */

const axios = require('axios');

class MBTITravelAssistantClient {
  constructor(baseURL, authTokenProvider) {
    this.baseURL = baseURL;
    this.authTokenProvider = authTokenProvider;
    
    // Create axios instance with default configuration
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 15000, // 15 second timeout for itinerary generation
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
   * Generate 3-day itinerary based on MBTI personality type
   */
  async generateMBTIItinerary(mbtiPersonality, userContext = null) {
    try {
      const request = {
        MBTI_personality: mbtiPersonality
      };
      
      if (userContext) {
        request.user_context = userContext;
      }
      
      const response = await this.client.post('/invocations', request);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to generate itinerary: ${error.message}`);
    }
  }
  
  /**
   * Validate MBTI personality type format
   */
  validateMBTIType(mbtiType) {
    if (!mbtiType || typeof mbtiType !== 'string' || mbtiType.length !== 4) {
      return false;
    }
    
    const validTypes = [
      'INTJ', 'INTP', 'ENTJ', 'ENTP',
      'INFJ', 'INFP', 'ENFJ', 'ENFP', 
      'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
      'ISTP', 'ISFP', 'ESTP', 'ESFP'
    ];
    
    return validTypes.includes(mbtiType.toUpperCase());
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
    
    // Show component health
    if (health.components) {
      console.log('Component Status:');
      Object.entries(health.components).forEach(([component, status]) => {
        console.log(`  ${component}: ${status.status} (${status.response_time_ms}ms)`);
      });
    }
    console.log('');
    
    // Example 2: Generate INFJ itinerary
    console.log('2. Generating 3-day itinerary for INFJ personality...');
    const mbtiType = 'INFJ';
    
    if (!client.validateMBTIType(mbtiType)) {
      throw new Error(`Invalid MBTI type: ${mbtiType}`);
    }
    
    const itinerary = await client.generateMBTIItinerary(mbtiType);
    
    console.log(`✓ 3-day itinerary generated for ${itinerary.metadata.MBTI_personality}`);
    console.log(`Processing time: ${itinerary.metadata.processing_time_ms}ms`);
    console.log(`Tourist spots found: ${itinerary.metadata.total_spots_found}`);
    console.log(`Restaurants found: ${itinerary.metadata.total_restaurants_found}`);
    console.log(`Validation status: ${itinerary.metadata.validation_status}`);
    console.log('');
    
    // Example 3: Show day-by-day breakdown
    console.log('3. Day-by-day itinerary breakdown:');
    Object.entries(itinerary.main_itinerary).forEach(([day, dayData]) => {
      console.log(`\n${day.toUpperCase()}:`);
      
      // Morning
      const morning = dayData.morning_session;
      console.log(`  🌅 Morning: ${morning?.name || 'Not assigned'}`);
      if (morning) {
        console.log(`     ${morning.address}`);
        console.log(`     Category: ${morning.location_category}`);
        console.log(`     MBTI Match: ${morning.MBTI_match ? '✨ Yes' : '❌ No'}`);
      }
      
      // Breakfast
      const breakfast = dayData.breakfast;
      console.log(`  🍳 Breakfast: ${breakfast?.name || 'Not assigned'}`);
      if (breakfast) {
        console.log(`     ${breakfast.address}`);
        console.log(`     Sentiment: ${breakfast.sentiment?.likes || 0} likes, ${breakfast.sentiment?.dislikes || 0} dislikes`);
      }
      
      // Afternoon
      const afternoon = dayData.afternoon_session;
      console.log(`  ☀️ Afternoon: ${afternoon?.name || 'Not assigned'}`);
      if (afternoon) {
        console.log(`     ${afternoon.address}`);
        console.log(`     Category: ${afternoon.location_category}`);
        console.log(`     MBTI Match: ${afternoon.MBTI_match ? '✨ Yes' : '❌ No'}`);
      }
      
      // Lunch
      const lunch = dayData.lunch;
      console.log(`  🍽️ Lunch: ${lunch?.name || 'Not assigned'}`);
      if (lunch) {
        console.log(`     ${lunch.address}`);
      }
      
      // Night
      const night = dayData.night_session;
      console.log(`  🌙 Night: ${night?.name || 'Not assigned'}`);
      if (night) {
        console.log(`     ${night.address}`);
        console.log(`     Category: ${night.location_category}`);
        console.log(`     MBTI Match: ${night.MBTI_match ? '✨ Yes' : '❌ No'}`);
      }
      
      // Dinner
      const dinner = dayData.dinner;
      console.log(`  🍷 Dinner: ${dinner?.name || 'Not assigned'}`);
      if (dinner) {
        console.log(`     ${dinner.address}`);
      }
    });
    
    // Example 4: Show alternative options
    console.log('\n4. Alternative tourist spots available:');
    Object.entries(itinerary.candidate_tourist_spots || {}).forEach(([day, candidates]) => {
      if (candidates && candidates.length > 0) {
        console.log(`\n${day.toUpperCase()} alternatives (showing first 3):`);
        candidates.slice(0, 3).forEach((spot, index) => {
          console.log(`  ${index + 1}. ${spot.name}`);
          console.log(`     ${spot.address}`);
          console.log(`     Category: ${spot.location_category}`);
          console.log(`     MBTI Match: ${spot.MBTI_match ? '✨ Yes' : '❌ No'}`);
        });
      }
    });
    
    // Example 5: Generate itinerary with user preferences
    console.log('\n5. Generating ENFP itinerary with user preferences...');
    const userContext = {
      user_id: 'demo_user',
      preferences: {
        activity_level: 'high',
        cultural_interest: 'moderate',
        social_preference: 'group_activities'
      }
    };
    
    const enfpItinerary = await client.generateMBTIItinerary('ENFP', userContext);
    
    console.log(`✓ Personalized itinerary generated for ${enfpItinerary.metadata.MBTI_personality}`);
    console.log(`Processing time: ${enfpItinerary.metadata.processing_time_ms}ms`);
    
    // Count MBTI matches
    let mbtiMatches = 0;
    let totalSpots = 0;
    
    Object.values(enfpItinerary.main_itinerary).forEach(day => {
      ['morning_session', 'afternoon_session', 'night_session'].forEach(session => {
        if (day[session]) {
          totalSpots++;
          if (day[session].MBTI_match) {
            mbtiMatches++;
          }
        }
      });
    });
    
    console.log(`MBTI Match Rate: ${mbtiMatches}/${totalSpots} (${((mbtiMatches/totalSpots)*100).toFixed(1)}%)`);
    console.log('');
    
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