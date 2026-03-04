#!/usr/bin/env python3
"""
Simple test script for Anna Drishti API.
"""

import requests
import json

# API endpoint from CDK deployment
API_URL = "https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo"

def test_start_workflow():
    """Test starting a workflow."""
    print("Testing: Start Workflow")
    print("-" * 50)
    
    payload = {
        "farmer_name": "Ramesh Patil",
        "crop_type": "tomato",
        "plot_area": 2.1,
        "estimated_quantity": 2300,
        "location": "Sinnar, Nashik"
    }
    
    print(f"Endpoint: {API_URL}/workflow/start")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    response = requests.post(
        f"{API_URL}/workflow/start",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        workflow_id = data.get('workflow_id')
        print(f"\n✅ Workflow started successfully!")
        print(f"Workflow ID: {workflow_id}")
        print(f"Dashboard URL: https://d2ll18l06rc220.cloudfront.net")
        return workflow_id
    else:
        print(f"\n❌ Failed to start workflow")
        return None

def main():
    print("=" * 50)
    print("Anna Drishti API Test")
    print("=" * 50)
    print()
    
    # Test 1: Start workflow
    workflow_id = test_start_workflow()
    
    if workflow_id:
        print(f"\n✅ All tests passed!")
        print(f"\nNext steps:")
        print(f"1. Visit dashboard: https://d2ll18l06rc220.cloudfront.net")
        print(f"2. Check DynamoDB table: anna-drishti-demo-workflows")
        print(f"3. View workflow: {workflow_id}")
    else:
        print(f"\n❌ Tests failed")

if __name__ == "__main__":
    main()
