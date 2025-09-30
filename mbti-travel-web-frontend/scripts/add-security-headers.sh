#!/bin/bash

# CloudFront Security Headers Setup Script
# Adds security headers via CloudFront Functions

DISTRIBUTION_ID="E2OI88972BLL6O"
FUNCTION_NAME="mbti-travel-security-headers"

echo "🔒 Setting up CloudFront security headers..."

# Create the CloudFront Function code
cat > /tmp/security-headers-function.js << 'EOF'
function handler(event) {
    var response = event.response;
    var headers = response.headers;

    // Security Headers
    headers['x-content-type-options'] = { value: 'nosniff' };
    headers['x-frame-options'] = { value: 'DENY' };
    headers['x-xss-protection'] = { value: '1; mode=block' };
    headers['referrer-policy'] = { value: 'strict-origin-when-cross-origin' };
    headers['x-download-options'] = { value: 'noopen' };
    headers['x-permitted-cross-domain-policies'] = { value: 'none' };
    
    // Content Security Policy for HTML files
    if (event.request.uri.endsWith('.html') || event.request.uri === '/' || !event.request.uri.includes('.')) {
        headers['content-security-policy'] = { 
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cognito-idp.us-east-1.amazonaws.com https://*.amazoncognito.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.amazonaws.com https://*.amazoncognito.com https://p4ex20jih1.execute-api.us-east-1.amazonaws.com; frame-ancestors 'none';" 
        };
        headers['strict-transport-security'] = { value: 'max-age=31536000; includeSubDomains' };
        headers['permissions-policy'] = { value: 'geolocation=(), microphone=(), camera=()' };
    }
    
    return response;
}
EOF

echo "📝 Creating CloudFront Function..."

# Create the CloudFront Function
aws cloudfront create-function \
    --name "$FUNCTION_NAME" \
    --function-config Comment="Add security headers to all responses",Runtime=cloudfront-js-1.0 \
    --function-code fileb:///tmp/security-headers-function.js \
    --region us-east-1 2>/dev/null || echo "ℹ️  Function may already exist"

echo "📋 Getting function ARN..."

# Get the function ARN
FUNCTION_ARN=$(aws cloudfront describe-function --name "$FUNCTION_NAME" --region us-east-1 --query 'FunctionSummary.FunctionMetadata.FunctionARN' --output text)

if [ -z "$FUNCTION_ARN" ]; then
    echo "❌ Failed to get function ARN"
    exit 1
fi

echo "✅ Function ARN: $FUNCTION_ARN"

echo "🔄 To complete the setup, you need to:"
echo "1. Go to AWS CloudFront Console"
echo "2. Select distribution: $DISTRIBUTION_ID"
echo "3. Go to Behaviors tab"
echo "4. Edit the Default behavior"
echo "5. Scroll to Function associations"
echo "6. Add Viewer Response function: $FUNCTION_NAME"
echo "7. Save changes"
echo ""
echo "Or run this command to update the distribution:"
echo "aws cloudfront get-distribution-config --id $DISTRIBUTION_ID --query 'DistributionConfig' > /tmp/dist-config.json"
echo "# Edit the config to add function association"
echo "aws cloudfront update-distribution --id $DISTRIBUTION_ID --distribution-config file:///tmp/dist-config.json --if-match \$(aws cloudfront get-distribution-config --id $DISTRIBUTION_ID --query 'ETag' --output text)"

# Clean up
rm -f /tmp/security-headers-function.js

echo "✅ Security headers function created successfully!"
echo "🔄 Distribution update required to activate headers"