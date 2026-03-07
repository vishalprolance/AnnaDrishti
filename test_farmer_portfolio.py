"""
Test script for Farmer Portfolio APIs.
"""

import requests
import json

# API Base URL
API_URL = "https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo"

def test_list_farmers():
    """Test GET /farmers endpoint."""
    print("\n=== Testing List Farmers ===")
    
    response = requests.get(f"{API_URL}/farmers")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_list_farmers_with_search():
    """Test GET /farmers with search parameter."""
    print("\n=== Testing List Farmers with Search ===")
    
    response = requests.get(f"{API_URL}/farmers?search=Ramesh")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_get_farmer(farmer_name):
    """Test GET /farmers/{farmer_name} endpoint."""
    print(f"\n=== Testing Get Farmer: {farmer_name} ===")
    
    # URL encode the farmer name
    from urllib.parse import quote
    encoded_name = quote(farmer_name)
    
    response = requests.get(f"{API_URL}/farmers/{encoded_name}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


def test_get_farmer_without_workflows(farmer_name):
    """Test GET /farmers/{farmer_name} without full workflow details."""
    print(f"\n=== Testing Get Farmer (Summary Only): {farmer_name} ===")
    
    # URL encode the farmer name
    from urllib.parse import quote
    encoded_name = quote(farmer_name)
    
    response = requests.get(f"{API_URL}/farmers/{encoded_name}?include_workflows=false")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.json()


if __name__ == "__main__":
    print("Testing Farmer Portfolio APIs...")
    print(f"API URL: {API_URL}")
    
    # Test list farmers
    farmers_response = test_list_farmers()
    
    # Test search
    test_list_farmers_with_search()
    
    # Test get specific farmer (if any farmers exist)
    if farmers_response.get('success') and farmers_response.get('farmers'):
        first_farmer = farmers_response['farmers'][0]
        farmer_name = first_farmer['farmer_name']
        
        # Test get farmer with full details
        test_get_farmer(farmer_name)
        
        # Test get farmer summary only
        test_get_farmer_without_workflows(farmer_name)
    else:
        print("\nNo farmers found. Create some workflows first using /workflow/start")
    
    print("\n=== All Tests Complete ===")
