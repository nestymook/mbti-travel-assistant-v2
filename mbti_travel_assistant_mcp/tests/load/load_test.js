// K6 Load Testing Script for MBTI Travel Assistant MCP
// This script tests the performance and scalability of the MBTI Travel Assistant

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 20 },   // Ramp up to 20 users
    { duration: '5m', target: 20 },   // Stay at 20 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<10000'], // 95% of requests must complete below 10s
    http_req_failed: ['rate<0.1'],      // Error rate must be below 10%
    errors: ['rate<0.1'],               // Custom error rate must be below 10%
  },
};

// Test data - different MBTI personality types
const mbtiTypes = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
];

// Base URL from environment or default
const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8080';

// Headers
const headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

// Test setup
export function setup() {
  console.log(`Starting load test against: ${BASE_URL}`);
  
  // Health check before starting tests
  const healthResponse = http.get(`${BASE_URL}/health`);
  if (healthResponse.status !== 200) {
    throw new Error(`Health check failed: ${healthResponse.status}`);
  }
  
  console.log('Health check passed, starting load test...');
  return { baseUrl: BASE_URL };
}

// Main test function
export default function(data) {
  // Select random MBTI type
  const mbtiType = mbtiTypes[Math.floor(Math.random() * mbtiTypes.length)];
  
  // Test payload
  const payload = JSON.stringify({
    MBTI_personality: mbtiType
  });
  
  // Make request
  const startTime = Date.now();
  const response = http.post(`${data.baseUrl}/invocations`, payload, { headers });
  const endTime = Date.now();
  
  // Record custom metrics
  const duration = endTime - startTime;
  responseTime.add(duration);
  
  // Check response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 10s': (r) => r.timings.duration < 10000,
    'has main_itinerary': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.main_itinerary !== undefined;
      } catch (e) {
        return false;
      }
    },
    'has candidate_tourist_spots': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.candidate_tourist_spots !== undefined;
      } catch (e) {
        return false;
      }
    },
    'has candidate_restaurants': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.candidate_restaurants !== undefined;
      } catch (e) {
        return false;
      }
    },
    'has metadata': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.metadata !== undefined;
      } catch (e) {
        return false;
      }
    }
  });
  
  // Record errors
  if (!success) {
    errorRate.add(1);
    console.log(`Request failed for ${mbtiType}: ${response.status} - ${response.body}`);
  } else {
    errorRate.add(0);
  }
  
  // Log successful responses periodically
  if (success && Math.random() < 0.1) { // 10% of successful requests
    try {
      const body = JSON.parse(response.body);
      console.log(`Successful request for ${mbtiType}: ${duration}ms, spots: ${body.metadata?.total_spots_found || 'unknown'}`);
    } catch (e) {
      console.log(`Successful request for ${mbtiType}: ${duration}ms (could not parse response)`);
    }
  }
  
  // Think time between requests
  sleep(Math.random() * 2 + 1); // 1-3 seconds
}

// Test scenarios for different load patterns
export const scenarios = {
  // Constant load scenario
  constant_load: {
    executor: 'constant-vus',
    vus: 5,
    duration: '5m',
    tags: { scenario: 'constant' },
  },
  
  // Spike testing scenario
  spike_test: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '30s', target: 50 }, // Spike to 50 users
      { duration: '1m', target: 50 },  // Stay at 50 users
      { duration: '30s', target: 0 },  // Drop to 0 users
    ],
    tags: { scenario: 'spike' },
  },
  
  // Stress testing scenario
  stress_test: {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '2m', target: 10 },  // Ramp up
      { duration: '5m', target: 10 },  // Stay at normal load
      { duration: '2m', target: 30 },  // Ramp up to stress level
      { duration: '5m', target: 30 },  // Stay at stress level
      { duration: '2m', target: 50 },  // Ramp up to breaking point
      { duration: '5m', target: 50 },  // Stay at breaking point
      { duration: '2m', target: 0 },   // Ramp down
    ],
    tags: { scenario: 'stress' },
  }
};

// Test teardown
export function teardown(data) {
  console.log('Load test completed');
  
  // Final health check
  const healthResponse = http.get(`${data.baseUrl}/health`);
  if (healthResponse.status === 200) {
    console.log('Service is still healthy after load test');
  } else {
    console.log(`Service health check failed after load test: ${healthResponse.status}`);
  }
}

// Handle summary data
export function handleSummary(data) {
  return {
    '/results/load_test_summary.json': JSON.stringify(data, null, 2),
    '/results/load_test_summary.txt': textSummary(data, { indent: ' ', enableColors: false }),
  };
}

// Helper function to create text summary
function textSummary(data, options = {}) {
  const indent = options.indent || '';
  const summary = [];
  
  summary.push(`${indent}Load Test Summary`);
  summary.push(`${indent}================`);
  summary.push(`${indent}Test Duration: ${data.state.testRunDurationMs}ms`);
  summary.push(`${indent}Total Requests: ${data.metrics.http_reqs.values.count}`);
  summary.push(`${indent}Failed Requests: ${data.metrics.http_req_failed.values.passes}`);
  summary.push(`${indent}Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%`);
  summary.push(`${indent}Average Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms`);
  summary.push(`${indent}95th Percentile Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms`);
  summary.push(`${indent}Max Response Time: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms`);
  summary.push(`${indent}Requests per Second: ${data.metrics.http_reqs.values.rate.toFixed(2)}`);
  
  if (data.metrics.errors) {
    summary.push(`${indent}Custom Error Rate: ${(data.metrics.errors.values.rate * 100).toFixed(2)}%`);
  }
  
  return summary.join('\n');
}