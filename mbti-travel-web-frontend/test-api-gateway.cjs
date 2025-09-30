#!/usr/bin/env node

const https = require('https');

// Test the API Gateway endpoint
const testPayload = {
    "MBTI_personality": "INFJ",
    "user_context": {
        "user_id": "test-user",
        "preferences": {
            "budget": "medium",
            "interests": ["culture", "food", "sightseeing"],
            "includeRestaurants": true,
            "includeTouristSpots": true
        }
    },
    "start_date": "2025-09-30",
    "special_requirements": "Test request from API Gateway"
};

const postData = JSON.stringify(testPayload);

const options = {
    hostname: 'p4ex20jih1.execute-api.us-east-1.amazonaws.com',
    port: 443,
    path: '/prod/generate-itinerary',
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'Authorization': 'Bearer test-token-for-testing'
    }
};

console.log('Testing API Gateway endpoint...');
console.log('URL:', `https://${options.hostname}${options.path}`);

const req = https.request(options, (res) => {
    console.log(`Status: ${res.statusCode}`);
    console.log(`Headers:`, res.headers);
    
    let data = '';
    res.on('data', (chunk) => {
        data += chunk;
    });
    
    res.on('end', () => {
        console.log('Response:', data);
        try {
            const jsonResponse = JSON.parse(data);
            console.log('Parsed Response:', JSON.stringify(jsonResponse, null, 2));
        } catch (error) {
            console.log('Raw Response (not JSON):', data);
        }
    });
});

req.on('error', (error) => {
    console.error('Request failed:', error);
});

req.write(postData);
req.end();