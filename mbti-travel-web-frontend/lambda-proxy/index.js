const https = require('https');

// AgentCore endpoint configuration  
const AGENTCORE_ENDPOINT = 'bedrock-agentcore.us-east-1.amazonaws.com';
const AGENT_ID = 'mbti_travel_assistant_mcp-skv6fd785E';

exports.handler = async (event) => {
    console.log('Lambda proxy received event:', JSON.stringify(event, null, 2));
    
    // CORS headers
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With,X-Request-ID',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Max-Age': '86400'
    };
    
    // Handle preflight OPTIONS request
    if (event.httpMethod === 'OPTIONS') {
        console.log('Handling OPTIONS preflight request');
        return {
            statusCode: 200,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With,X-Request-ID',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Max-Age': '86400',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: 'CORS preflight successful' })
        };
    }
    
    try {
        // Extract JWT token from Authorization header
        const authHeader = event.headers.Authorization || event.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return {
                statusCode: 401,
                headers: corsHeaders,
                body: JSON.stringify({ error: 'Missing or invalid Authorization header' })
            };
        }
        
        const jwtToken = authHeader.substring(7); // Remove 'Bearer ' prefix
        
        // Parse request body
        let requestBody;
        try {
            requestBody = JSON.parse(event.body || '{}');
        } catch (error) {
            return {
                statusCode: 400,
                headers: corsHeaders,
                body: JSON.stringify({ error: 'Invalid JSON in request body' })
            };
        }
        
        // Prepare the request to AgentCore
        const agentCorePayload = JSON.stringify(requestBody);
        
        const options = {
            hostname: AGENTCORE_ENDPOINT,
            port: 443,
            path: `/runtime/${AGENT_ID}/invocations`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(agentCorePayload),
                'Authorization': `Bearer ${jwtToken}`,
                'Accept': 'application/json'
            }
        };
        
        console.log('Making request to AgentCore:', options);
        
        // Make request to AgentCore
        const agentCoreResponse = await new Promise((resolve, reject) => {
            const req = https.request(options, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    console.log('AgentCore response status:', res.statusCode);
                    console.log('AgentCore response headers:', res.headers);
                    console.log('AgentCore response data:', data);
                    
                    resolve({
                        statusCode: res.statusCode,
                        headers: res.headers,
                        body: data
                    });
                });
            });
            
            req.on('error', (error) => {
                console.error('Request to AgentCore failed:', error);
                reject(error);
            });
            
            req.on('timeout', () => {
                console.error('Request to AgentCore timed out');
                req.destroy();
                reject(new Error('Request timeout'));
            });
            
            // Set timeout (3 minutes for long-running agent operations)
            req.setTimeout(180000);
            
            req.write(agentCorePayload);
            req.end();
        });
        
        // Parse AgentCore response
        let responseBody;
        try {
            responseBody = JSON.parse(agentCoreResponse.body);
        } catch (error) {
            console.error('Failed to parse AgentCore response as JSON:', error);
            responseBody = { 
                error: 'Invalid response from AgentCore',
                raw_response: agentCoreResponse.body 
            };
        }
        
        return {
            statusCode: agentCoreResponse.statusCode || 200,
            headers: {
                ...corsHeaders,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(responseBody)
        };
        
    } catch (error) {
        console.error('Lambda proxy error:', error);
        
        return {
            statusCode: 500,
            headers: corsHeaders,
            body: JSON.stringify({
                error: 'Internal server error',
                message: error.message,
                timestamp: new Date().toISOString()
            })
        };
    }
};