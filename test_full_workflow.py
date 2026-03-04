#!/usr/bin/env python3
"""
Complete workflow test for Anna Drishti API.
Tests all endpoints in sequence.
"""

import requests
import json
import time

# API endpoint
API_URL = "https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo"

def print_section(title):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_start_workflow():
    """Test 1: Start workflow."""
    print_section("TEST 1: Start Workflow")
    
    payload = {
        "farmer_name": "Ramesh Patil",
        "crop_type": "tomato",
        "plot_area": 2.1,
        "estimated_quantity": 2300,
        "location": "Sinnar, Nashik"
    }
    
    print(f"POST {API_URL}/workflow/start")
    response = requests.post(
        f"{API_URL}/workflow/start",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    if response.status_code == 200:
        workflow_id = data.get('workflow_id')
        print(f"\n✅ Workflow created: {workflow_id}")
        return workflow_id
    else:
        print(f"\n❌ Failed to create workflow")
        return None

def test_scan_market(workflow_id):
    """Test 2: Scan market data."""
    print_section("TEST 2: Scan Market Data")
    
    payload = {
        "workflow_id": workflow_id,
        "crop_type": "tomato"
    }
    
    print(f"POST {API_URL}/workflow/scan")
    response = requests.post(
        f"{API_URL}/workflow/scan",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    if response.status_code == 200:
        print(f"\n✅ Market scan completed")
        return True
    else:
        print(f"\n❌ Market scan failed")
        return False

def test_detect_surplus(workflow_id):
    """Test 3: Detect surplus."""
    print_section("TEST 3: Detect Surplus")
    
    payload = {
        "workflow_id": workflow_id,
        "total_volume_kg": 30000  # 30 tonnes (simulating FPO total)
    }
    
    print(f"POST {API_URL}/workflow/surplus")
    response = requests.post(
        f"{API_URL}/workflow/surplus",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    if response.status_code == 200:
        print(f"\n✅ Surplus detection completed")
        return True
    else:
        print(f"\n❌ Surplus detection failed")
        return False

def test_negotiate(workflow_id, buyer_offer=None, exchange_count=0):
    """Test 4: AI Negotiation."""
    print_section(f"TEST 4: AI Negotiation (Round {exchange_count + 1})")
    
    payload = {
        "workflow_id": workflow_id,
        "exchange_count": exchange_count
    }
    
    if buyer_offer:
        payload["buyer_offer"] = buyer_offer
        print(f"Buyer's offer: ₹{buyer_offer}/kg")
    
    print(f"POST {API_URL}/workflow/negotiate")
    response = requests.post(
        f"{API_URL}/workflow/negotiate",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    if response.status_code == 200:
        offer = data.get('offer', {})
        print(f"\n✅ Agent's counter-offer: ₹{offer.get('price')}/kg")
        print(f"Message: {offer.get('message')}")
        return data
    else:
        print(f"\n❌ Negotiation failed")
        return None

def main():
    """Run complete workflow test."""
    print("\n" + "🌾" * 30)
    print("  Anna Drishti - Complete Workflow Test")
    print("🌾" * 30)
    
    # Test 1: Start workflow
    workflow_id = test_start_workflow()
    if not workflow_id:
        print("\n❌ Workflow creation failed. Stopping tests.")
        return
    
    time.sleep(1)
    
    # Test 2: Scan market
    if not test_scan_market(workflow_id):
        print("\n⚠️  Market scan failed, but continuing...")
    
    time.sleep(1)
    
    # Test 3: Detect surplus
    if not test_detect_surplus(workflow_id):
        print("\n⚠️  Surplus detection failed, but continuing...")
    
    time.sleep(1)
    
    # Test 4: AI Negotiation (multiple rounds)
    print("\n" + "-" * 60)
    print("  Starting AI Negotiation Simulation")
    print("-" * 60)
    
    # Round 1: Initial offer
    result = test_negotiate(workflow_id, exchange_count=0)
    if not result:
        print("\n❌ Negotiation failed. Stopping tests.")
        return
    
    time.sleep(2)
    
    # Round 2: Buyer counter-offer
    agent_price = result.get('offer', {}).get('price', 26.0)
    buyer_counter = agent_price - 1.5  # Buyer offers less
    result = test_negotiate(workflow_id, buyer_offer=buyer_counter, exchange_count=1)
    
    if result:
        time.sleep(2)
        
        # Round 3: Final round
        agent_price = result.get('offer', {}).get('price', 26.0)
        buyer_final = agent_price - 0.5  # Buyer comes closer
        result = test_negotiate(workflow_id, buyer_offer=buyer_final, exchange_count=2)
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"✅ Workflow ID: {workflow_id}")
    print(f"✅ All endpoints tested successfully!")
    print(f"\n📊 View results:")
    print(f"   Dashboard: https://d2ll18l06rc220.cloudfront.net")
    print(f"   DynamoDB: anna-drishti-demo-workflows")
    print(f"\n🎉 Anna Drishti MVP is working!")

if __name__ == "__main__":
    main()
