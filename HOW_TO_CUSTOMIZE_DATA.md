# How to Customize Data - Quick Guide

## Overview

This guide shows you how to customize the dummy data in your Anna Drishti system.

---

## 1. Change Satellite Location

### Current Locations
The system supports these locations:
- Nashik (default)
- Sinnar
- Pune
- Mumbai
- Nagpur
- Aurangabad
- Delhi
- Bangalore
- Hyderabad
- Kolkata

### Add New Location

**File**: `backend/lambdas/get_satellite_data.py`

**Step 1**: Find the location_coords dictionary (around line 100):
```python
location_coords = {
    'nashik': {'lat': 19.9975, 'lon': 73.7898},
    'sinnar': {'lat': 19.8500, 'lon': 73.9833},
    # ... more locations
}
```

**Step 2**: Add your location:
```python
location_coords = {
    'nashik': {'lat': 19.9975, 'lon': 73.7898},
    'sinnar': {'lat': 19.8500, 'lon': 73.9833},
    'your_city': {'lat': YOUR_LATITUDE, 'lon': YOUR_LONGITUDE},  # ADD THIS
}
```

**Step 3**: Deploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

**Step 4**: Test:
- Go to dashboard
- Start workflow with location = "your_city"
- Satellite data will use your coordinates

---

## 2. Change Market Prices

### Current Prices
The system has mock prices for tomato, onion, and chili.

### Update Prices

**File**: `backend/lambdas/scan_market.py`

**Step 1**: Find MOCK_PRICES dictionary (around line 30):
```python
MOCK_PRICES = {
    'tomato': {
        'Sinnar': {'price': 26.0, 'arrivals': 18.5},
        'Nashik': {'price': 25.0, 'arrivals': 22.0},
        'Pune': {'price': 28.0, 'arrivals': 45.0},
        'Mumbai': {'price': 32.0, 'arrivals': 120.0},
    },
    # ... more crops
}
```

**Step 2**: Update prices:
```python
MOCK_PRICES = {
    'tomato': {
        'Sinnar': {'price': 30.0, 'arrivals': 20.0},  # CHANGE PRICE
        'Nashik': {'price': 28.0, 'arrivals': 25.0},  # CHANGE PRICE
        # ...
    },
}
```

**Step 3**: Add new crop:
```python
MOCK_PRICES = {
    'tomato': { ... },
    'onion': { ... },
    'potato': {  # ADD NEW CROP
        'Sinnar': {'price': 15.0, 'arrivals': 30.0},
        'Nashik': {'price': 14.0, 'arrivals': 35.0},
        'Pune': {'price': 16.0, 'arrivals': 50.0},
        'Mumbai': {'price': 18.0, 'arrivals': 100.0},
    },
}
```

**Step 4**: Deploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

---

## 3. Change Processor Information

### Current Processors
The system has 2 mock processors.

### Update Processors

**File**: `backend/lambdas/detect_surplus.py`

**Step 1**: Find PROCESSORS list (around line 30):
```python
PROCESSORS = [
    {
        'name': 'Sai Agro Processing',
        'capacity_tonnes': Decimal('5.0'),
        'rate_per_kg': Decimal('32.0'),
        'location': 'Sinnar Industrial Area',
    },
    {
        'name': 'Krishi Processing Co.',
        'capacity_tonnes': Decimal('2.0'),
        'rate_per_kg': Decimal('38.0'),
        'location': 'Nashik MIDC',
    },
]
```

**Step 2**: Update or add processors:
```python
PROCESSORS = [
    {
        'name': 'Your Processor Name',
        'capacity_tonnes': Decimal('10.0'),  # CHANGE CAPACITY
        'rate_per_kg': Decimal('35.0'),      # CHANGE RATE
        'location': 'Your Location',         # CHANGE LOCATION
    },
    # ADD MORE PROCESSORS
]
```

**Step 3**: Deploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

---

## 4. Change Surplus Thresholds

### Current Thresholds
- Mandi capacity: 22 tonnes
- Surplus threshold: 3 tonnes

### Update Thresholds

**File**: `backend/lambdas/detect_surplus.py`

**Step 1**: Find threshold constants (around line 40):
```python
# Mandi capacity threshold (tonnes)
MANDI_CAPACITY_THRESHOLD = 22.0

# Surplus threshold for processing diversion (tonnes)
SURPLUS_THRESHOLD = 3.0
```

**Step 2**: Change values:
```python
MANDI_CAPACITY_THRESHOLD = 30.0  # CHANGE TO YOUR VALUE
SURPLUS_THRESHOLD = 5.0          # CHANGE TO YOUR VALUE
```

**Step 3**: Deploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

---

## 5. Change AI Negotiation Settings

### Current Settings
- Floor price: ₹24/kg
- Max exchanges: 3 rounds
- Model: GPT-4o-mini

### Update Settings

**File**: `backend/lambdas/negotiate.py`

**Step 1**: Find negotiation constants (around line 40):
```python
# Negotiation constraints
FLOOR_PRICE = 24.0  # ₹/kg - never go below this
MAX_EXCHANGES = 3   # Maximum negotiation rounds
```

**Step 2**: Change values:
```python
FLOOR_PRICE = 20.0  # CHANGE FLOOR PRICE
MAX_EXCHANGES = 5   # CHANGE MAX ROUNDS
```

**Step 3**: Change AI model (optional):

**File**: `infrastructure/lib/demo-stack.ts`

Find the negotiate Lambda environment variables (around line 150):
```typescript
environment: {
  WORKFLOW_TABLE_NAME: workflowTable.tableName,
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
  OPENAI_MODEL: 'gpt-4o-mini',  // CHANGE MODEL HERE
},
```

Options:
- `gpt-4o-mini` - Cheapest, fast (current)
- `gpt-4o` - Higher quality, more expensive
- `gpt-3.5-turbo` - Cheaper, lower quality

**Step 4**: Deploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

---

## 6. Change Transport Costs

### Current Costs
Transport costs based on distance:
- Sinnar (15 km): ₹0.5/kg
- Nashik (30 km): ₹1.0/kg
- Pune (180 km): ₹3.0/kg
- Mumbai (250 km): ₹5.0/kg

### Update Costs

**File**: `backend/lambdas/scan_market.py`

**Step 1**: Find TRANSPORT_COSTS dictionary (around line 25):
```python
TRANSPORT_COSTS = {
    'Sinnar': 0.5,   # 15 km
    'Nashik': 1.0,   # 30 km
    'Pune': 3.0,     # 180 km
    'Mumbai': 5.0,   # 250 km
}
```

**Step 2**: Change costs:
```python
TRANSPORT_COSTS = {
    'Sinnar': 0.3,   # CHANGE COST
    'Nashik': 0.8,   # CHANGE COST
    'Pune': 2.5,     # CHANGE COST
    'Mumbai': 4.0,   # CHANGE COST
}
```

**Step 3**: Deploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

---

## 7. Change Satellite NDVI Simulation

### Current Simulation
NDVI grows from 0.3 to 0.75 over 30 days (simulating crop growth).

### Update Simulation

**File**: `backend/lambdas/get_satellite_data.py`

**Step 1**: Find calculate_ndvi_mock function (around line 120):
```python
# Simulate NDVI increasing over time (crop growing)
# Start at 0.3 (early growth), increase to 0.75 (mature crop)
ndvi_value = 0.3 + (i * 0.075)
```

**Step 2**: Change growth pattern:
```python
# Option 1: Faster growth
ndvi_value = 0.4 + (i * 0.1)  # 0.4 → 0.9

# Option 2: Slower growth
ndvi_value = 0.2 + (i * 0.05)  # 0.2 → 0.5

# Option 3: Declining (crop stress)
ndvi_value = 0.8 - (i * 0.05)  # 0.8 → 0.5
```

**Step 3**: Deploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

---

## Quick Deployment Script

Create a file `deploy.sh`:

```bash
#!/bin/bash

echo "Deploying Anna Drishti with updated data..."

cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack --require-approval never

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "Dashboard: https://d2ll18l06rc220.cloudfront.net"
else
    echo "❌ Deployment failed"
    exit 1
fi
```

Make it executable:
```bash
chmod +x deploy.sh
```

Run it:
```bash
./deploy.sh
```

---

## Testing Your Changes

### Test Market Prices
```bash
python3 test_api.py
# Check market_scan section for updated prices
```

### Test Satellite Location
1. Go to dashboard: https://d2ll18l06rc220.cloudfront.net
2. Start workflow with your new location
3. Check satellite data section for coordinates

### Test Processors
1. Start workflow with large quantity (>30,000 kg)
2. Check surplus panel for updated processor info

### Test AI Negotiation
```bash
python3 test_full_workflow.py
# Check negotiation rounds for updated floor price/max exchanges
```

---

## Summary

**To customize data**:
1. Edit the relevant Lambda function file
2. Change the constants/dictionaries
3. Deploy with `npx cdk deploy AnnaDrishtiDemoStack`
4. Test your changes

**Files to edit**:
- `backend/lambdas/scan_market.py` - Market prices, transport costs
- `backend/lambdas/detect_surplus.py` - Processors, thresholds
- `backend/lambdas/negotiate.py` - AI negotiation settings
- `backend/lambdas/get_satellite_data.py` - Satellite locations, NDVI

**Deployment time**: ~2 minutes

**No code restart needed**: Lambda functions update automatically

---

**Last Updated**: March 7, 2026  
**Status**: Ready to customize ✅
