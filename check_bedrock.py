#!/usr/bin/env python3
"""
Quick Bedrock access check for Claude 4.5 Haiku.
"""

import boto3
import json
import time

def check_bedrock():
    """Check if Bedrock is accessible."""
    print("🔍 Checking Bedrock access...")
    print("-" * 50)
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Hello' in one word"
                }
            ]
        }
        
        print("Invoking Claude 4.5 Haiku...")
        response = bedrock.invoke_model(
            modelId='global.anthropic.claude-haiku-4-5-20251001-v1:0',
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        message = result['content'][0]['text']
        
        print(f"\n✅ SUCCESS! Bedrock is working!")
        print(f"Response: {message}")
        print(f"\n🎉 You can now run: python3 test_full_workflow.py")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        
        if 'use case details' in error_msg.lower():
            print(f"\n⏳ Status: Form submitted, waiting for approval")
            print(f"   This usually takes 5-15 minutes")
            print(f"   Try again in a few minutes")
        elif 'INVALID_PAYMENT_INSTRUMENT' in error_msg:
            print(f"\n⏳ Status: Payment method verification needed")
            print(f"   Go to: https://console.aws.amazon.com/billing/home#/paymentmethods")
            print(f"   Check if your card is verified")
        elif 'ResourceNotFoundException' in error_msg:
            print(f"\n⏳ Status: Model not yet available")
            print(f"   Wait 5 more minutes and try again")
        else:
            print(f"\n⚠️  Unexpected error")
            print(f"   Check AWS Console → Bedrock")
        
        return False

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  AWS Bedrock Access Check (Claude 4.5 Haiku)")
    print("=" * 50 + "\n")
    
    success = check_bedrock()
    
    if not success:
        print(f"\n💡 Tip: Run this script again in 5 minutes:")
        print(f"   python3 check_bedrock.py")
    
    print()
