#!/usr/bin/env python3
"""
Test script for satellite data API.
Tests fetching Sentinel-2 data and NDVI calculation.
"""

import requests
import json

# API Configuration
API_BASE_URL = "https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo"

def test_get_satellite_data():
    """Test getting satellite data for a workflow."""
    print("\n=== Testing Get Satellite Data ===")
    
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
    
    # Test: Get satellite data
    print("\n2. Fetching satellite data...")
    response = requests.post(
        f"{API_BASE_URL}/satellite",
        json={
            "workflow_id": workflow_id
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get satellite data: {response.text}")
        return
    
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('success'):
        satellite_data = data.get('satellite_data', {})
        print("\n✅ Satellite Data Retrieved:")
        print(f"   Location: {satellite_data.get('location')}")
        print(f"   Data Source: {satellite_data.get('data_source')}")
        print(f"   Last Updated: {satellite_data.get('last_updated')}")
        
        crop_health = satellite_data.get('crop_health', {})
        print(f"\n   Crop Health:")
        print(f"      Score: {crop_health.get('score')}/100")
        print(f"      Status: {crop_health.get('status')}")
        print(f"      Trend: {crop_health.get('trend')}")
        print(f"      Latest NDVI: {crop_health.get('latest_ndvi')}")
        
        ndvi_series = satellite_data.get('ndvi_time_series', [])
        print(f"\n   NDVI Time Series ({len(ndvi_series)} data points):")
        for point in ndvi_series:
            print(f"      {point.get('date')}: NDVI={point.get('ndvi')} ({point.get('status')}) - Cloud: {point.get('cloud_cover')}%")
        
        print(f"\n   Note: {satellite_data.get('note')}")
    else:
        print(f"❌ Failed to get satellite data")


def main():
    """Run all satellite data tests."""
    print("=" * 60)
    print("Satellite Data API Tests")
    print("=" * 60)
    
    try:
        test_get_satellite_data()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
