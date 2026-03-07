#!/bin/bash

# Deploy Anna Drishti with OpenAI API Key
# Usage: ./deploy_with_openai.sh

echo "=========================================="
echo "Anna Drishti - OpenAI Deployment"
echo "=========================================="
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is not set"
    echo ""
    echo "Please set your OpenAI API key:"
    echo "  export OPENAI_API_KEY=\"sk-your-api-key-here\""
    echo ""
    echo "Get your API key from: https://platform.openai.com/api-keys"
    exit 1
fi

echo "✅ OPENAI_API_KEY is set"
echo ""

# Deploy Lambda
echo "Deploying Lambda with OpenAI integration..."
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack --require-approval never

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Deployment successful!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Test AI negotiation: python3 ../test_full_workflow.py"
    echo "2. Monitor usage: https://platform.openai.com/usage"
    echo "3. Check logs: aws logs tail /aws/lambda/anna-drishti-negotiate --follow"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Deployment failed"
    echo "=========================================="
    echo ""
    echo "Check the error messages above"
    exit 1
fi
