#!/bin/bash

echo "=================================================="
echo "  AWS Bedrock - Enable Claude 3 Haiku"
echo "=================================================="
echo ""
echo "📋 Steps to enable Bedrock:"
echo ""
echo "1. Open Bedrock Playground:"
echo "   https://ap-south-1.console.aws.amazon.com/bedrock/home?region=ap-south-1#/chat-playground"
echo ""
echo "2. Select Model:"
echo "   - Provider: Anthropic"
echo "   - Model: Claude 3 Haiku"
echo ""
echo "3. Send a test message (anything)"
echo ""
echo "4. Fill the use case form when prompted:"
echo "   - Use case: Agricultural technology"
echo "   - Description: AI negotiation for Indian farmers"
echo "   - Company: Your name"
echo "   - Email: Your email"
echo ""
echo "5. Submit and wait (~5-15 minutes)"
echo ""
echo "=================================================="
echo ""
read -p "Press Enter when you've submitted the form..."
echo ""
echo "Testing Bedrock access..."
echo ""

# Test with a simple API call
python3 -c "
import boto3
import json

try:
    bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
    
    request_body = {
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 100,
        'messages': [{
            'role': 'user',
            'content': 'Say hello in one word'
        }]
    }
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps(request_body)
    )
    
    result = json.loads(response['body'].read())
    print('✅ Bedrock is working!')
    print(f'Response: {result[\"content\"][0][\"text\"]}')
    print('')
    print('🎉 You can now run: python3 test_full_workflow.py')
    
except Exception as e:
    print(f'❌ Error: {str(e)}')
    print('')
    if 'use case details' in str(e).lower():
        print('⏳ Use case form not yet submitted or approved')
        print('   Go to the Bedrock Playground link above')
    elif 'ResourceNotFoundException' in str(e):
        print('⏳ Model not yet available in this region')
        print('   Try again in 5 minutes')
    else:
        print('⏳ Wait a few more minutes and try again')
"
