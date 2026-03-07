#!/usr/bin/env python3
"""
Test script for payment tracking APIs.
Tests update payment status and get payment metrics endpoints.
"""

import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo"

def test_update_payment():
    """Test updating payment status for a workflow."""
    print("\n=== Testing Update Payment ===")
    
    # First, create a test workflow
    print("\n1. Creating test workflow...")
    workflow_response = requests.post(
        f"{API_BASE_URL}/workflow/start",
        json={
            "farmer_name": "Ramesh Patil",
            "crop_type": "tomato",
            "plot_area": 2.5,
            "estimated_quantity": 500,
            "location": "Nashik"
        }
    )
    
    if workflow_response.status_code != 200:
        print(f"❌ Failed to create workflow: {workflow_response.text}")
        return
    
    workflow_data = workflow_response.json()
    workflow_id = workflow_data.get('workflow_id')
    print(f"✅ Created workflow: {workflow_id}")
    
    # Test 1: Update payment to pending
    print("\n2. Updating payment to pending...")
    response = requests.post(
        f"{API_BASE_URL}/payments/update",
        json={
            "workflow_id": workflow_id,
            "payment_status": "pending",
            "payment_amount": 62350.0,
            "payment_method": "bank_transfer",
            "transaction_id": "TXN123456",
            "payment_date": datetime.utcnow().isoformat() + "Z"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Payment updated to pending")
    else:
        print(f"❌ Failed to update payment: {response.text}")
        return
    
    # Test 2: Update payment to confirmed
    print("\n3. Updating payment to confirmed...")
    response = requests.post(
        f"{API_BASE_URL}/payments/update",
        json={
            "workflow_id": workflow_id,
            "payment_status": "confirmed",
            "payment_amount": 62350.0,
            "payment_method": "bank_transfer",
            "transaction_id": "TXN123456",
            "payment_date": datetime.utcnow().isoformat() + "Z"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Payment updated to confirmed")
    else:
        print(f"❌ Failed to update payment: {response.text}")
    
    # Test 3: Invalid status
    print("\n4. Testing invalid payment status...")
    response = requests.post(
        f"{API_BASE_URL}/payments/update",
        json={
            "workflow_id": workflow_id,
            "payment_status": "invalid_status",
            "payment_amount": 62350.0
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 400:
        print("✅ Validation error handled correctly")
    else:
        print(f"❌ Expected 400 status code, got {response.status_code}")
    
    # Test 4: Missing workflow_id
    print("\n5. Testing missing workflow_id...")
    response = requests.post(
        f"{API_BASE_URL}/payments/update",
        json={
            "payment_status": "confirmed",
            "payment_amount": 62350.0
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 400:
        print("✅ Validation error handled correctly")
    else:
        print(f"❌ Expected 400 status code, got {response.status_code}")


def test_get_payment_metrics():
    """Test getting payment metrics across all workflows."""
    print("\n\n=== Testing Get Payment Metrics ===")
    
    response = requests.get(f"{API_BASE_URL}/payments/metrics")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get payment metrics: {response.text}")
        return
    
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('success'):
        metrics = data.get('metrics', {})
        print("\n✅ Payment Metrics Retrieved:")
        print(f"   Total Workflows: {metrics.get('total_workflows')}")
        print(f"   Payment Status Breakdown:")
        for status, count in metrics.get('payment_status_breakdown', {}).items():
            print(f"      {status}: {count}")
        print(f"   Total Amount Pending: ₹{metrics.get('total_amount_pending', 0):,.2f}")
        print(f"   Total Amount Confirmed: ₹{metrics.get('total_amount_confirmed', 0):,.2f}")
        print(f"   Total Amount Failed: ₹{metrics.get('total_amount_failed', 0):,.2f}")
        print(f"   Delayed Payments: {len(metrics.get('delayed_payments', []))}")
        print(f"   Recent Payments: {len(metrics.get('recent_payments', []))}")
    else:
        print(f"❌ Failed to get payment metrics")


def main():
    """Run all payment tracking tests."""
    print("=" * 60)
    print("Payment Tracking API Tests")
    print("=" * 60)
    
    try:
        test_update_payment()
        test_get_payment_metrics()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
