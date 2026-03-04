#!/usr/bin/env python3
"""
Direct Bedrock test with detailed error handling for Claude 4.5 Haiku.
"""

import boto3
import json

def test_bedrock_detailed():
    """Test Bedrock with detailed error information."""
    print("🔍 Testing Bedrock Access (Detailed)")
    print("=" * 60)
    
    # Try to list models first
    print("\n1. Checking if Claude 4.5 Haiku is available...")
    try:
        bedrock = boto3.client('bedrock', region_name='ap-south-1')
        response = bedrock.list_foundation_models()
        claude_models = [m for m in response['modelSummaries'] if 'claude-haiku-4-5' in m['modelId']]
        print(f"   ✅ Found {len(claude_models)} Claude 4.5 Haiku models")
        for model in claude_models:
            print(f"      - {model['modelId']}: {model.get('modelLifecycle', {}).get('status', 'UNKNOWN')}")
    except Exception as e:
        print(f"   ❌ Error listing models: {e}")
        return False
    
    # Try to invoke the model
    print("\n2. Attempting to invoke Claude 4.5 Haiku...")
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-south-1')
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user",
                    "content": "Say hello in one word"
                }
            ]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='global.anthropic.claude-haiku-4-5-20251001-v1:0',
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        message = result['content'][0]['text']
        
        print(f"   ✅ SUCCESS! Model responded: {message}")
        print("\n" + "=" * 60)
        print("🎉 Bedrock is working! You can now run:")
        print("   python3 test_full_workflow.py")
        print("=" * 60)
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"   ❌ Error: {error_str}")
        print("\n" + "=" * 60)
        print("📋 Error Analysis:")
        print("=" * 60)
        
        if 'INVALID_PAYMENT_INSTRUMENT' in error_str:
            print("\n🔴 Issue: Payment method not verified")
            print("\n💡 Solutions:")
            print("   1. Go to: https://console.aws.amazon.com/billing/home#/paymentmethods")
            print("   2. Check if your card shows 'Verified' status")
            print("   3. If not verified, you may need to:")
            print("      - Check your email for verification link")
            print("      - Wait 5-10 minutes for verification")
            print("      - Try adding a different card")
            print("      - Contact your bank if card is being declined")
            
        elif 'aws-marketplace:Subscribe' in error_str or 'aws-marketplace:ViewSubscriptions' in error_str:
            print("\n🟡 Issue: AWS Marketplace subscription needed")
            print("\n💡 Solution:")
            print("   1. Go to: https://console.aws.amazon.com/bedrock/home?region=ap-south-1#/chat-playground")
            print("   2. Select 'Anthropic' → 'Claude 4.5 Haiku'")
            print("   3. Try to send a message")
            print("   4. Accept any terms/conditions that appear")
            print("   5. Wait 2-3 minutes and try again")
            
        elif 'use case details' in error_str.lower():
            print("\n🟡 Issue: Use case form not submitted")
            print("\n💡 Solution:")
            print("   1. Go to: https://console.aws.amazon.com/bedrock/home?region=ap-south-1#/chat-playground")
            print("   2. Select 'Anthropic' → 'Claude 4.5 Haiku'")
            print("   3. Fill the use case form when prompted")
            print("   4. Wait 5-15 minutes for approval")
            
        else:
            print(f"\n🔴 Unexpected error")
            print(f"\n💡 Try:")
            print("   1. Wait 5 minutes and run this script again")
            print("   2. Check AWS Console → Bedrock for any notifications")
            print("   3. Try using us-east-1 region instead")
        
        return False

if __name__ == "__main__":
    test_bedrock_detailed()
