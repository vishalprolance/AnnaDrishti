# Real vs Dummy Data Analysis - Current Status

## Summary

**Overall**: 60% Real Data, 40% Dummy Data

When you click "Start Demo Workflow", here's what happens:

---

## Component-by-Component Analysis

### ✅ 1. Start Workflow (100% REAL)
**Status**: REAL DATA ✅

**What Happens**:
- User inputs farmer name, crop type, plot area, quantity, location
- Creates workflow in DynamoDB with unique ID
- Stores all user input as-is (no dummy data)

**Data Source**: User input → DynamoDB

**Dummy Data**: NONE

---

### ⚠️ 2. Market Scan (100% DUMMY)
**Status**: DUMMY DATA ❌

**What Happens**:
- Uses hardcoded mock prices for 4 mandis (Sinnar, Nashik, Pune, Mumbai)
- Mock data defined in `MOCK_PRICES` dictionary
- Transport costs are calculated (real logic, dummy prices)

**Current Mock Data**:
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

**Why Dummy**: Agmarknet scraping not implemented yet (Phase 2 task)

**How to Make Real**: Implement Agmarknet web scraping or API integration

---

### ⚠️ 3. Surplus Detection (50% REAL, 50% DUMMY)
**Status**: MIXED DATA ⚠️

**What Happens**:
- **REAL**: Surplus calculation logic (total volume - mandi capacity)
- **REAL**: Threshold checks (22 tonnes mandi capacity, 3 tonnes surplus threshold)
- **DUMMY**: Processor information (names, rates, locations)

**Current Mock Processors**:
```python
PROCESSORS = [
    {
        'name': 'Sai Agro Processing',
        'capacity_tonnes': 5.0,
        'rate_per_kg': 32.0,
        'location': 'Sinnar Industrial Area',
    },
    {
        'name': 'Krishi Processing Co.',
        'capacity_tonnes': 2.0,
        'rate_per_kg': 38.0,
        'location': 'Nashik MIDC',
    },
]
```

**Why Dummy**: No processor database yet

**How to Make Real**: Create processor database or integrate with FPO processor registry

---

### ✅ 4. AI Negotiation (100% REAL)
**Status**: REAL DATA ✅

**What Happens**:
- Uses OpenAI GPT-4o-mini API
- Generates real AI responses based on context
- Enforces real guardrails (floor price, max exchanges)
- Stores negotiation messages in DynamoDB

**Data Source**: OpenAI API → DynamoDB

**Dummy Data**: NONE

---

### ⚠️ 5. Satellite Data (100% DUMMY)
**Status**: DUMMY DATA ❌

**What Happens**:
- **DUMMY**: NDVI values (simulated crop growth cycle)
- **REAL**: Location mapping (Nashik, Pune, Mumbai, etc.)
- **REAL**: NDVI calculation logic (would work with real data)
- **REAL**: Crop health score calculation

**Current Mock NDVI**:
```python
# Simulates crop growth: 0.3 → 0.75 over 30 days
ndvi_value = 0.3 + (i * 0.075)
```

**Why Dummy**: Sentinel-2 imagery download not implemented yet

**How to Make Real**: 
1. Query Sentinel-2 S3 bucket (s3://sentinel-s2-l2a/)
2. Download NIR and Red bands
3. Calculate real NDVI = (NIR - Red) / (NIR + Red)

---

### ✅ 6. Farmer Portfolio (100% REAL)
**Status**: REAL DATA ✅

**What Happens**:
- Queries DynamoDB for all workflows
- Groups by farmer name
- Calculates real statistics (total workflows, quantity, income)
- Filters and searches work on real data

**Data Source**: DynamoDB

**Dummy Data**: NONE

---

### ✅ 7. Payment Tracking (100% REAL)
**Status**: REAL DATA ✅

**What Happens**:
- Updates payment status in DynamoDB
- Calculates real payment metrics
- Detects real payment delays (>48 hours)
- Tracks real transaction IDs

**Data Source**: DynamoDB

**Dummy Data**: NONE

---

## Summary Table

| Component | Real Data | Dummy Data | Status |
|-----------|-----------|------------|--------|
| Start Workflow | 100% | 0% | ✅ REAL |
| Market Scan | 0% | 100% | ❌ DUMMY |
| Surplus Detection | 50% | 50% | ⚠️ MIXED |
| AI Negotiation | 100% | 0% | ✅ REAL |
| Satellite Data | 0% | 100% | ❌ DUMMY |
| Farmer Portfolio | 100% | 0% | ✅ REAL |
| Payment Tracking | 100% | 0% | ✅ REAL |

**Overall**: 60% Real, 40% Dummy

---

## When You Click "Start Demo Workflow"

### Step 1: User Input (REAL)
- You enter: Farmer name, crop, plot area, quantity, location
- **Result**: Real data stored in DynamoDB ✅

### Step 2: Market Scan (DUMMY)
- System fetches: Mock prices from hardcoded dictionary
- **Result**: Dummy market prices ❌
- **Shows**: Sinnar ₹26/kg, Nashik ₹25/kg, Pune ₹28/kg, Mumbai ₹32/kg

### Step 3: Surplus Detection (MIXED)
- System calculates: Real surplus logic with your quantity
- System shows: Dummy processor information
- **Result**: Real calculation, dummy processors ⚠️

### Step 4: AI Negotiation (REAL)
- System generates: Real AI responses from OpenAI
- **Result**: Real AI negotiation ✅
- **Shows**: Professional, contextual negotiation messages

### Step 5: Satellite Data (DUMMY)
- System generates: Mock NDVI values
- **Result**: Dummy satellite data ❌
- **Shows**: Simulated crop health (0.3 → 0.75 NDVI)

---

## How to Change Satellite Location

### Current Location Mapping

The satellite data uses location from your workflow input. Here's how it maps:

**File**: `backend/lambdas/get_satellite_data.py`

**Current Mapping**:
```python
location_coords = {
    'nashik': {'lat': 19.9975, 'lon': 73.7898},
    'pune': {'lat': 18.5204, 'lon': 73.8567},
    'mumbai': {'lat': 19.0760, 'lon': 72.8777},
    'nagpur': {'lat': 21.1458, 'lon': 79.0882},
    'aurangabad': {'lat': 19.8762, 'lon': 75.3433},
}
```

### Option 1: Add New Location (Recommended)

Add your location to the dictionary:

```python
location_coords = {
    'nashik': {'lat': 19.9975, 'lon': 73.7898},
    'pune': {'lat': 18.5204, 'lon': 73.8567},
    'mumbai': {'lat': 19.0760, 'lon': 72.8777},
    'nagpur': {'lat': 21.1458, 'lon': 79.0882},
    'aurangabad': {'lat': 19.8762, 'lon': 75.3433},
    'sinnar': {'lat': 19.8500, 'lon': 73.9833},  # ADD YOUR LOCATION
}
```

Then redeploy:
```bash
cd infrastructure
npx cdk deploy AnnaDrishtiDemoStack
```

### Option 2: Change Default Location

Change the default fallback location:

```python
coords = location_coords.get(location.lower(), location_coords['nashik'])
# Change to:
coords = location_coords.get(location.lower(), {'lat': YOUR_LAT, 'lon': YOUR_LON})
```

### Option 3: Use Geocoding API (Production)

For production, use a geocoding API to convert location names to coordinates:

```python
def geocode_location(location: str) -> tuple:
    """Convert location name to coordinates using geocoding API."""
    # Use Google Maps Geocoding API, Mapbox, or similar
    # For now, use mock mapping
    pass
```

---

## How to Make Data Real (Production Roadmap)

### 1. Market Scan → Real Agmarknet Data

**Current**: Mock prices  
**Target**: Real Agmarknet scraping

**Implementation**:
```python
def fetch_agmarknet_prices(crop_type: str) -> tuple[list[dict], str]:
    """Fetch real prices from Agmarknet."""
    import requests
    from bs4 import BeautifulSoup
    
    # Scrape Agmarknet website
    url = f"https://agmarknet.gov.in/..."
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Parse prices
    # ...
    
    return mandis_data, 'live'
```

**Effort**: 1-2 days  
**Cost**: FREE (Agmarknet is public)

---

### 2. Surplus Detection → Real Processor Database

**Current**: Mock processors  
**Target**: Real processor registry

**Implementation**:
- Create DynamoDB table for processors
- Add processor registration API
- Query real processors by location and capacity

**Effort**: 1 day  
**Cost**: $1-2/month (DynamoDB)

---

### 3. Satellite Data → Real Sentinel-2 Imagery

**Current**: Mock NDVI  
**Target**: Real Sentinel-2 data from AWS Open Data

**Implementation**:
```python
def fetch_sentinel2_imagery(lat: float, lon: float, date: str) -> dict:
    """Fetch real Sentinel-2 imagery from S3."""
    import rasterio
    
    # Query Sentinel-2 S3 bucket
    bucket = 'sentinel-s2-l2a'
    # Find tile for lat/lon
    # Download NIR and Red bands
    # Calculate NDVI
    
    return ndvi_data
```

**Effort**: 2-3 days  
**Cost**: FREE (Sentinel-2 is public) + $1-5/month (S3 transfer)

---

## Cost Comparison

### Current (MVP)
- **AWS**: $13/month (DynamoDB, Lambda, API Gateway, CloudFront)
- **OpenAI**: $1.50/month (500 negotiations/day)
- **Total**: $14.50/month

### Production (All Real Data)
- **AWS**: $15/month (+ processor DB, + Sentinel-2 processing)
- **OpenAI**: $1.50/month
- **Agmarknet**: FREE (public data)
- **Sentinel-2**: FREE (public data)
- **Total**: $16.50/month

**Difference**: +$2/month for real data ✅

---

## Recommendations

### Immediate (This Week)
1. ✅ Keep current setup (60% real is good for MVP)
2. ✅ AI negotiation is real and working
3. ✅ Payment tracking is real and working
4. ✅ Farmer portfolio is real and working

### Short-term (Next 2 Weeks)
1. Implement Agmarknet scraping (1-2 days)
2. Create processor database (1 day)
3. Add more location mappings for satellite data

### Long-term (Production)
1. Implement real Sentinel-2 imagery (2-3 days)
2. Add geocoding API for location mapping
3. Create processor registration system

---

## Summary

**When you click "Start Demo Workflow"**:
- ✅ Your input is REAL (stored in DynamoDB)
- ❌ Market prices are DUMMY (hardcoded)
- ⚠️ Surplus calculation is REAL, processors are DUMMY
- ✅ AI negotiation is REAL (OpenAI)
- ❌ Satellite data is DUMMY (simulated NDVI)
- ✅ Payment tracking is REAL (DynamoDB)
- ✅ Farmer portfolio is REAL (DynamoDB)

**Overall**: 60% real data, 40% dummy data

**Good enough for**: MVP, hackathon demo, proof of concept

**Not good enough for**: Production deployment (need real market prices and satellite data)

---

**Last Updated**: March 7, 2026  
**Status**: MVP with 60% real data ✅
