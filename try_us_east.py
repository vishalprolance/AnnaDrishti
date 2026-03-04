#!/usr/bin/env python3
"""
Try Bedrock in us-east-1 region (sometimes faster approval).
"""

import boto3
import json

def test_region(region):
    """Test Bedrock in a specific region."""
    print(f"\n🌍 Testing region: {region}")
    print("-" * 50)
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user",
                    "content": "Say hello"
                }
            ]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        message = result['content'][0]['text']
        
        print(f"✅ SUCCESS in {region}!")
        print(f"Response: {message}")
        return True
        
    except Exception as e:
        error_str = str(e)
        if 'INVALID_PAYMENT_INSTRUMENT' in error_str:
            print(f"❌ Payment method issue in {region}")
        elif 'use case' in error_str.lower():
            print(f"⏳ Use case form needed in {region}")
        else:
            print(f"❌ Error in {region}: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("  Testing Bedrock in Multiple Regions")
    print("=" * 50)
    
    regions = ['us-east-1', 'us-west-2', 'ap-south-1']
    
    for region in regions:
        if test_region(region):
            print(f"\n🎉 {region} is working!")
            print(f"\nTo use this region, update your Lambda functions:")
            print(f"  Region: {region}")
            break
    else:
        print("\n" + "=" * 50)
        print("❌ All regions have the same issue")
        print("=" * 50)
        print("\n💡 This confirms it's a payment verification issue")
        print("   Please check: https://console.aws.amazon.com/billing/home#/paymentmethods")
