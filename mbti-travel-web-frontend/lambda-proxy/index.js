const { BedrockAgentCoreClient, InvokeAgentRuntimeCommand } = require('@aws-sdk/client-bedrock-agentcore');

// AgentCore configuration
const AGENT_RUNTIME_ARN = 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_assistant_mcp-skv6fd785E';
const AWS_REGION = 'us-east-1';

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
        
        // Create BedrockAgentCore client with SigV4 authentication
        const client = new BedrockAgentCoreClient({
            region: AWS_REGION
        });
        
        // Generate a session ID (must be 33+ characters)
        const runtimeSessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2)}-${Math.random().toString(36).substring(2)}`;
        
        // Prepare the input text from request body
        const inputText = JSON.stringify(requestBody);
        
        // Create payload as Uint8Array
        const payload = new TextEncoder().encode(inputText);
        
        console.log('Making request to AgentCore with SigV4:', {
            agentRuntimeArn: AGENT_RUNTIME_ARN,
            runtimeSessionId: runtimeSessionId,
            payloadSize: payload.length,
            inputPreview: inputText.substring(0, 200) + '...'
        });
        
        // Create the invoke command input
        const input = {
            runtimeSessionId: runtimeSessionId,
            agentRuntimeArn: AGENT_RUNTIME_ARN,
            qualifier: "DEFAULT",
            payload: payload
        };
        
        // Create and send the command
        const command = new InvokeAgentRuntimeCommand(input);
        const response = await client.send(command);
        
        console.log('AgentCore response received');
        
        // Transform the response to string
        const textResponse = await response.response.transformToString();
        
        console.log('AgentCore response data:', textResponse);
        
        // Parse the response
        let responseBody;
        try {
            responseBody = JSON.parse(textResponse);
        } catch (error) {
            console.error('Failed to parse AgentCore response as JSON:', error);
            responseBody = { 
                error: 'Invalid response from AgentCore',
                raw_response: textResponse 
            };
        }
        
        return {
            statusCode: 200,
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