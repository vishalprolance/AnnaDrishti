# Design Document: Satellite Context Provider

## Overview

The Satellite Context Provider is an assistive system component that provides directional crop health and yield context using Sentinel-2 satellite imagery. The system performs NDVI (Normalized Difference Vegetation Index) temporal analysis to support three primary use cases:

1. **Harvest Readiness Confirmation**: Validates farmer signals against NDVI trajectory patterns
2. **Regional Yield Estimation**: Provides directional yield estimates (not plot-precise measurements)
3. **Crop Distress Detection**: Identifies NDVI anomalies for insurance assistance

The design emphasizes graceful degradation, acknowledging that satellite data is assistive context only and the system must function when data is unavailable due to cloud cover or other limitations.

### Key Design Principles

- **Assistive, Not Definitive**: All satellite-derived insights are labeled as context, not ground truth
- **Graceful Degradation**: System continues to function when satellite data is unavailable
- **Data Quality Transparency**: All responses include metadata about data recency and confidence
- **Scalability**: Designed to handle 500+ farmer plots with weekly NDVI updates
- **Cost Efficiency**: Intelligent storage lifecycle management to minimize AWS costs

## Architecture

The Satellite Context Provider follows a serverless event-driven architecture on AWS:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Satellite Context Provider                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Imagery    │      │     NDVI     │      │   Context    │  │
│  │  Acquisition │─────▶│  Processing  │─────▶│   Service    │  │
│  │   Service    │      │   Service    │      │     API      │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                      │                      │          │
│         ▼                      ▼                      ▼          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  S3 Imagery  │      │  Timestream  │      │ EventBridge  │  │
│  │   Storage    │      │  NDVI Time-  │      │   Events     │  │
│  │              │      │    Series    │      │              │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         ▲                                              │
         │                                              ▼
┌────────────────┐                          ┌──────────────────────┐
│  Copernicus    │                          │  Dependent Systems   │
│  Open Access   │                          │  - Sell Agent        │
│     Hub        │                          │  - Process Agent     │
│  (Sentinel-2)  │                          │  - Insurance Assist  │
└────────────────┘                          └──────────────────────┘
```

### Component Responsibilities

**Imagery Acquisition Service**:
- Scheduled downloads from Copernicus Hub (EventBridge trigger every 5 days)
- Cloud cover filtering and tile selection
- GeoTIFF storage in S3 with compression
- Handles API rate limits and retries

**NDVI Processing Service**:
- Extracts red (Band 4) and NIR (Band 8) from Sentinel-2 imagery
- Calculates NDVI: (NIR - Red) / (NIR + Red)
- Computes mean NDVI for plot boundaries
- Stores time-series data in Timestream
- Triggers distress detection analysis

**Context Service API**:
- REST API for NDVI queries, harvest readiness, yield estimation
- Implements graceful degradation logic
- Adds data quality metadata to all responses
- Publishes crop distress events to EventBridge

## Components and Interfaces

### 1. Imagery Acquisition Service

**Implementation**: AWS Lambda function triggered by EventBridge schedule

**Core Functions**:

```python
def download_sentinel2_imagery(plot_id: str, plot_bounds: GeoJSON) -> ImageryMetadata:
    """
    Downloads Sentinel-2 imagery for a plot from Copernicus Hub.
    
    Args:
        plot_id: Unique identifier for the farmer's plot
        plot_bounds: GeoJSON polygon defining plot boundaries
        
    Returns:
        ImageryMetadata containing S3 location, acquisition timestamp, cloud cover %
        
    Raises:
        NoImageryAvailableError: When no cloud-free imagery exists within 10 days
    """
    pass

def select_best_tile(tiles: List[SentinelTile], max_cloud_cover: float = 20.0) -> SentinelTile:
    """
    Selects the tile with lowest cloud cover from available options.
    
    Args:
        tiles: List of available Sentinel-2 tiles covering the plot
        max_cloud_cover: Maximum acceptable cloud cover percentage
        
    Returns:
        SentinelTile with lowest cloud cover, or None if all exceed threshold
    """
    pass

def store_imagery_s3(imagery: GeoTIFF, plot_id: str, timestamp: datetime) -> str:
    """
    Compresses and stores GeoTIFF imagery in S3.
    
    Args:
        imagery: GeoTIFF raster data
        plot_id: Plot identifier for S3 key construction
        timestamp: Acquisition timestamp for S3 key construction
        
    Returns:
        S3 URI of stored imagery
    """
    pass
```

**Data Structures**:

```python
@dataclass
class ImageryMetadata:
    plot_id: str
    s3_uri: str
    acquisition_timestamp: datetime
    cloud_cover_percent: float
    tile_id: str
    
@dataclass
class SentinelTile:
    tile_id: str
    acquisition_date: datetime
    cloud_cover_percent: float
    download_url: str
```

### 2. NDVI Processing Service

**Implementation**: AWS Lambda function triggered by S3 event (new imagery upload)

**Core Functions**:

```python
def calculate_ndvi(imagery_s3_uri: str, plot_bounds: GeoJSON) -> NDVIResult:
    """
    Calculates mean NDVI for a plot from Sentinel-2 imagery.
    
    Args:
        imagery_s3_uri: S3 location of GeoTIFF imagery
        plot_bounds: GeoJSON polygon defining plot boundaries
        
    Returns:
        NDVIResult containing mean NDVI, pixel count, and metadata
    """
    pass

def extract_bands(geotiff: GeoTIFF) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extracts red (Band 4) and NIR (Band 8) from Sentinel-2 GeoTIFF.
    
    Args:
        geotiff: Sentinel-2 GeoTIFF raster data
        
    Returns:
        Tuple of (red_band, nir_band) as numpy arrays
    """
    pass

def compute_ndvi_array(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Computes NDVI array from red and NIR bands.
    
    Formula: (NIR - Red) / (NIR + Red)
    Handles division by zero by assigning 0.
    
    Args:
        red: Red band pixel values
        nir: Near-infrared band pixel values
        
    Returns:
        NDVI array with same shape as input bands
    """
    pass

def mask_to_plot(ndvi_array: np.ndarray, plot_bounds: GeoJSON, 
                 geotransform: Tuple) -> np.ndarray:
    """
    Masks NDVI array to pixels within plot boundaries.
    
    Args:
        ndvi_array: Full NDVI raster array
        plot_bounds: GeoJSON polygon defining plot boundaries
        geotransform: GDAL geotransform for coordinate mapping
        
    Returns:
        Masked NDVI array containing only pixels within plot
    """
    pass

def store_ndvi_timeseries(plot_id: str, ndvi_value: float, 
                          timestamp: datetime, metadata: dict) -> None:
    """
    Stores NDVI value in Timestream time-series database.
    
    Args:
        plot_id: Plot identifier
        ndvi_value: Mean NDVI value for the plot
        timestamp: Acquisition timestamp
        metadata: Additional metadata (cloud cover, pixel count, etc.)
    """
    pass
```

**Data Structures**:

```python
@dataclass
class NDVIResult:
    plot_id: str
    mean_ndvi: float
    pixel_count: int
    acquisition_timestamp: datetime
    cloud_cover_percent: float
    
@dataclass
class NDVITrajectory:
    plot_id: str
    values: List[NDVIDataPoint]
    
@dataclass
class NDVIDataPoint:
    timestamp: datetime
    ndvi: float
    cloud_cover_percent: float
```

### 3. Context Service API

**Implementation**: AWS Lambda function behind API Gateway

**Core Functions**:

```python
def get_current_ndvi(plot_id: str) -> NDVIResponse:
    """
    Retrieves most recent NDVI value for a plot.
    
    Args:
        plot_id: Plot identifier
        
    Returns:
        NDVIResponse with NDVI value and data quality metadata
    """
    pass

def get_ndvi_trajectory(plot_id: str, start_date: datetime, 
                        end_date: datetime) -> NDVITrajectoryResponse:
    """
    Retrieves NDVI time-series for a plot within date range.
    
    Args:
        plot_id: Plot identifier
        start_date: Start of date range
        end_date: End of date range
        
    Returns:
        NDVITrajectoryResponse with time-series data and metadata
    """
    pass

def confirm_harvest_readiness(plot_id: str) -> HarvestReadinessResponse:
    """
    Validates harvest readiness signal against NDVI trajectory.
    
    Args:
        plot_id: Plot identifier
        
    Returns:
        HarvestReadinessResponse with confirmation signal and confidence level
    """
    pass

def estimate_regional_yield(plot_id: str) -> YieldEstimateResponse:
    """
    Provides directional yield estimate based on plot area and regional averages.
    
    Args:
        plot_id: Plot identifier
        
    Returns:
        YieldEstimateResponse with estimate and disclaimer metadata
    """
    pass

def detect_crop_distress(plot_id: str, current_ndvi: float) -> Optional[DistressAlert]:
    """
    Detects NDVI anomalies indicating potential crop damage.
    
    Args:
        plot_id: Plot identifier
        current_ndvi: Most recent NDVI value
        
    Returns:
        DistressAlert if anomaly detected, None otherwise
    """
    pass
```

**API Response Structures**:

```python
@dataclass
class NDVIResponse:
    plot_id: str
    ndvi: float
    acquisition_timestamp: datetime
    data_quality: DataQuality
    
@dataclass
class DataQuality:
    recency: str  # "fresh" (0-5 days), "recent" (5-10 days), "stale" (10+ days)
    cloud_cover_percent: float
    confidence_level: str  # "high", "medium", "low"
    
@dataclass
class HarvestReadinessResponse:
    plot_id: str
    signal: str  # "consistent", "not_consistent", "insufficient_data"
    confidence_level: str
    ndvi_trend: str  # "declining", "stable", "increasing"
    data_quality: DataQuality
    
@dataclass
class YieldEstimateResponse:
    plot_id: str
    estimated_yield_tons: float
    disclaimer: str  # "directional estimate - confirm with farmer"
    regional_average_tons_per_hectare: float
    adjustment_factor: float  # +/- 10% based on NDVI
    data_quality: DataQuality
    
@dataclass
class DistressAlert:
    plot_id: str
    current_ndvi: float
    baseline_ndvi: float
    decline_magnitude: float
    acquisition_timestamp: datetime
    alert_severity: str  # "moderate", "severe"
```

## Data Models

### Timestream Schema for NDVI Time-Series

```python
# Timestream table: ndvi_timeseries
# Dimensions: plot_id, crop_type, region
# Measures: ndvi_value, cloud_cover_percent, pixel_count

@dataclass
class TimestreamRecord:
    time: datetime  # Acquisition timestamp
    plot_id: str  # Dimension
    crop_type: str  # Dimension
    region: str  # Dimension
    ndvi_value: float  # Measure
    cloud_cover_percent: float  # Measure
    pixel_count: int  # Measure
```

### S3 Storage Structure

```
s3://anna-drishti-satellite-imagery/
├── raw/
│   ├── {plot_id}/
│   │   ├── {YYYY-MM-DD}_{tile_id}.tif
│   │   └── {YYYY-MM-DD}_{tile_id}.tif.metadata.json
├── processed/
│   ├── {plot_id}/
│   │   ├── {YYYY-MM-DD}_ndvi.tif
│   │   └── {YYYY-MM-DD}_ndvi.json
```

### DynamoDB Schema for Plot Metadata

```python
@dataclass
class PlotMetadata:
    plot_id: str  # Partition key
    farmer_id: str
    crop_type: str
    region: str
    plot_area_hectares: float
    boundaries: GeoJSON  # Polygon coordinates
    created_at: datetime
    last_ndvi_update: datetime
    active: bool
```

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Tile Selection Minimizes Cloud Cover

*For any* set of available Sentinel-2 tiles covering a plot, the selected tile should have the lowest cloud cover percentage among all tiles in the set.

**Validates: Requirements 1.3**

### Property 2: NDVI Formula Correctness

*For any* pair of red and NIR band pixel values, the calculated NDVI should equal (NIR - Red) / (NIR + Red), with division by zero handled by returning 0.

**Validates: Requirements 2.2, 2.3**

### Property 3: Mean NDVI Calculation

*For any* set of NDVI pixel values within a plot boundary, the computed mean NDVI should equal the sum of all pixel values divided by the pixel count.

**Validates: Requirements 2.5**

### Property 4: NDVI Storage Completeness

*For any* completed NDVI calculation, the stored record should contain plot identifier, mean NDVI value, acquisition timestamp, and cloud cover percentage.

**Validates: Requirements 2.6**

### Property 5: Time-Series Chronological Ordering

*For any* NDVI trajectory query, the returned data points should be ordered by acquisition timestamp in ascending chronological order.

**Validates: Requirements 3.3**

### Property 6: Time-Series Append Behavior

*For any* new NDVI calculation, the value should appear in the plot's trajectory with its acquisition timestamp after the append operation completes.

**Validates: Requirements 3.2**

### Property 7: Harvest Readiness Trend Detection

*For any* NDVI trajectory over the past 14 days, the harvest readiness signal should be "consistent" when NDVI shows a declining trend, "not consistent" when NDVI shows an increasing or stable trend, and "insufficient data" when fewer than 3 data points exist.

**Validates: Requirements 4.2, 4.3, 4.4**

### Property 8: Confidence Level Based on Data Recency

*For any* NDVI data point, the confidence level should be "high" when data is 0-5 days old, "medium" when 5-10 days old, and "low" when older than 10 days.

**Validates: Requirements 4.5**

### Property 9: Yield Estimation Formula

*For any* plot with area A hectares and regional average yield R tons/hectare, the estimated yield should equal A × R × adjustment_factor, where adjustment_factor is 1.1 when mean NDVI > 0.7, 0.9 when mean NDVI < 0.5, and 1.0 otherwise.

**Validates: Requirements 5.1, 5.3, 5.4**

### Property 10: Yield Estimate Disclaimer Presence

*For any* yield estimate response, the disclaimer field should contain the text "directional estimate - confirm with farmer".

**Validates: Requirements 5.5**

### Property 11: Distress Detection State Transitions

*For any* plot with a 30-day NDVI baseline, a distress flag should be set when current NDVI drops more than 0.15 units below baseline, and cleared when NDVI recovers to within 0.05 units of baseline.

**Validates: Requirements 6.2, 6.5**

### Property 12: Distress Alert Structure

*For any* crop distress event, the generated alert should contain plot identifier, current NDVI, baseline NDVI, decline magnitude, and acquisition timestamp.

**Validates: Requirements 6.3**

### Property 13: Distress Event Publishing

*For any* detected crop distress, an event notification should be published to the Insurance_Assist event bus.

**Validates: Requirements 6.4**

### Property 14: Seasonal Distress Suppression

*For any* plot during harvest season dates (based on crop calendar), NDVI declines should not trigger distress flags regardless of magnitude.

**Validates: Requirements 6.6**

### Property 15: Graceful Degradation for Missing Data

*For any* NDVI query when no data exists for a plot, the response should indicate "no data available" without raising exceptions, and when data exists but is stale, the response should return the most recent value with staleness metadata.

**Validates: Requirements 7.2, 7.4**

### Property 16: Data Recency Metadata Inclusion

*For any* API response containing NDVI data, the response should include data quality metadata with recency classification ("fresh", "recent", or "stale"), cloud cover percentage, and confidence level.

**Validates: Requirements 7.3, 10.7**

### Property 17: Data Gap Recording

*For any* imagery acquisition failure due to cloud cover or unavailability, a data gap record should be created containing timestamp and reason.

**Validates: Requirements 7.1**

### Property 18: Plot Prioritization by Data Gap Length

*For any* set of plots awaiting processing after fresh imagery becomes available, plots with longer data gaps should be processed before plots with shorter gaps.

**Validates: Requirements 7.6**

### Property 19: Geographic Batching for Clustered Plots

*For any* set of plots within a geographic clustering threshold, imagery downloads should be batched into a single Copernicus Hub query rather than individual queries.

**Validates: Requirements 8.4**

### Property 20: GeoTIFF Compression

*For any* imagery uploaded to S3, the file should be compressed using LZW compression algorithm.

**Validates: Requirements 9.4**

### Property 21: Plot Deactivation Triggers Archival

*For any* plot that is deactivated, all associated imagery and NDVI data should be moved to S3 Glacier storage class.

**Validates: Requirements 9.5**

### Property 22: Error Response Structure

*For any* API request that fails, the error response should contain an error code field and a human-readable error message field.

**Validates: Requirements 10.6**

### Property 23: S3 Storage Key Format

*For any* downloaded imagery, the S3 storage key should contain the plot identifier and acquisition timestamp in the path.

**Validates: Requirements 1.4**

### Property 24: Band Extraction Dimensions

*For any* valid Sentinel-2 GeoTIFF, extracting Band 4 (red) and Band 8 (NIR) should return two arrays with identical dimensions at 10m resolution.

**Validates: Requirements 2.1**

### Property 25: Spatial Masking to Plot Boundaries

*For any* NDVI array and plot boundary polygon, the masked result should contain only pixels whose coordinates fall within the polygon boundaries.

**Validates: Requirements 2.4**

### Property 26: Query Date Range for Harvest Readiness

*For any* harvest readiness request, the NDVI trajectory query should span exactly 30 days prior to the request timestamp.

**Validates: Requirements 4.1**

### Property 27: Regional Yield Data Query Parameters

*For any* yield estimation request, the query to Market_Data_Pipeline should include the plot's crop type and geographic region as parameters.

**Validates: Requirements 5.2**

### Property 28: 30-Day Moving Average Window

*For any* distress detection calculation, the baseline NDVI should be computed as the moving average over exactly the past 30 days.

**Validates: Requirements 6.1**

## Error Handling

The Satellite Context Provider implements comprehensive error handling to ensure graceful degradation:

### Imagery Acquisition Errors

**Cloud Cover Exceeds Threshold**:
- Record data gap with timestamp and cloud cover percentage
- Continue scheduled downloads without blocking
- Return stale data with staleness indicator when queried

**Copernicus Hub API Unavailable**:
- Implement exponential backoff retry (3 attempts)
- Log failure and record data gap
- Alert monitoring system after 3 consecutive failures

**Network Timeouts**:
- Retry with exponential backoff (max 3 attempts)
- Fall back to cached imagery if available
- Record partial download failures for investigation

### NDVI Processing Errors

**Invalid GeoTIFF Format**:
- Log error with imagery S3 URI
- Skip processing and mark imagery as invalid
- Alert monitoring system for manual investigation

**Plot Boundary Outside Imagery Extent**:
- Return error response indicating boundary mismatch
- Suggest imagery tile that covers the plot
- Do not block other plot processing

**Insufficient Pixels in Plot Boundary**:
- Require minimum 10 pixels for valid NDVI calculation
- Return error if pixel count < 10
- Log warning for plots with small areas

### API Request Errors

**Plot Not Found**:
- Return 404 with error code `PLOT_NOT_FOUND`
- Include message: "Plot {plot_id} does not exist"

**No NDVI Data Available**:
- Return 200 with `no_data_available` indicator
- Include message explaining data gap reason
- Do not block dependent workflows

**Regional Yield Data Unavailable**:
- Return 200 with `insufficient_data_for_estimation` indicator
- Include message explaining missing regional data
- Suggest manual yield estimation

**Invalid Date Range**:
- Return 400 with error code `INVALID_DATE_RANGE`
- Include message explaining valid date range constraints

### Storage Errors

**S3 Upload Failure**:
- Retry upload with exponential backoff (3 attempts)
- Store imagery locally temporarily
- Alert monitoring system after 3 failures

**Timestream Write Failure**:
- Retry write with exponential backoff (3 attempts)
- Queue failed writes for batch retry
- Alert monitoring system after 3 failures

## Testing Strategy

The Satellite Context Provider will be tested using a dual approach combining unit tests and property-based tests using the Hypothesis framework for Python.

### Property-Based Testing with Hypothesis

Property-based tests will validate universal correctness properties across randomly generated inputs. Each property test will run a minimum of 100 iterations to ensure comprehensive coverage.

**Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(
    red=st.floats(min_value=0, max_value=1),
    nir=st.floats(min_value=0, max_value=1)
)
def test_ndvi_formula_correctness(red, nir):
    """
    Feature: satellite-context-provider, Property 2: NDVI Formula Correctness
    
    For any pair of red and NIR band pixel values, the calculated NDVI 
    should equal (NIR - Red) / (NIR + Red), with division by zero handled 
    by returning 0.
    """
    result = compute_ndvi_array(
        np.array([red]), 
        np.array([nir])
    )
    
    if nir + red == 0:
        assert result[0] == 0
    else:
        expected = (nir - red) / (nir + red)
        assert abs(result[0] - expected) < 1e-6
```

**Property Test Coverage**:
- Property 1: Tile selection (generate random tile sets)
- Property 2: NDVI formula (generate random red/NIR values)
- Property 3: Mean calculation (generate random pixel arrays)
- Property 7: Harvest readiness (generate random NDVI trajectories)
- Property 9: Yield estimation (generate random plot areas and NDVI values)
- Property 11: Distress detection (generate random NDVI sequences)
- Property 15: Graceful degradation (generate missing data scenarios)
- Property 18: Prioritization (generate random plot sets with varying gap lengths)

**Custom Hypothesis Strategies**:
```python
# Strategy for generating valid NDVI trajectories
@st.composite
def ndvi_trajectory(draw):
    length = draw(st.integers(min_value=3, max_value=30))
    timestamps = sorted([
        draw(st.datetimes(
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        ))
        for _ in range(length)
    ])
    ndvi_values = [
        draw(st.floats(min_value=0, max_value=1))
        for _ in range(length)
    ]
    return NDVITrajectory(
        plot_id=draw(st.text(min_size=1, max_size=20)),
        values=[
            NDVIDataPoint(ts, ndvi, draw(st.floats(0, 100)))
            for ts, ndvi in zip(timestamps, ndvi_values)
        ]
    )

# Strategy for generating plot boundaries
@st.composite
def plot_boundary(draw):
    # Generate random polygon with 4-8 vertices
    num_vertices = draw(st.integers(min_value=4, max_value=8))
    center_lat = draw(st.floats(min_value=-90, max_value=90))
    center_lon = draw(st.floats(min_value=-180, max_value=180))
    
    vertices = []
    for _ in range(num_vertices):
        lat_offset = draw(st.floats(min_value=-0.01, max_value=0.01))
        lon_offset = draw(st.floats(min_value=-0.01, max_value=0.01))
        vertices.append([center_lon + lon_offset, center_lat + lat_offset])
    
    # Close the polygon
    vertices.append(vertices[0])
    
    return {
        "type": "Polygon",
        "coordinates": [vertices]
    }
```

### Unit Testing

Unit tests will focus on specific examples, edge cases, and integration points:

**Imagery Acquisition Tests**:
- Test Copernicus Hub API integration with mock responses
- Test cloud cover filtering with specific threshold values
- Test S3 upload with mock boto3 client
- Test retry logic with simulated failures

**NDVI Processing Tests**:
- Test band extraction with sample Sentinel-2 GeoTIFF
- Test NDVI calculation with known red/NIR values
- Test spatial masking with specific plot boundaries
- Test edge case: empty plot (no pixels)
- Test edge case: plot boundary outside imagery extent

**Context API Tests**:
- Test harvest readiness with specific declining trajectory
- Test harvest readiness with specific increasing trajectory
- Test yield estimation with known plot area and regional average
- Test distress detection with specific NDVI drop
- Test graceful degradation with missing data

**Error Handling Tests**:
- Test invalid GeoTIFF format handling
- Test network timeout retry logic
- Test S3 upload failure recovery
- Test Timestream write failure recovery

**Integration Tests**:
- Test end-to-end flow: download → process → store → query
- Test EventBridge event publishing for distress alerts
- Test Market_Data_Pipeline integration for regional yields
- Test API Gateway integration with Lambda functions

### Test Data

**Sample Sentinel-2 Imagery**:
- Store small sample GeoTIFF tiles (100x100 pixels) in test fixtures
- Include tiles with varying cloud cover percentages
- Include tiles with known NDVI patterns (healthy crops, stressed crops)

**Mock Plot Data**:
- Create test plots with various sizes (0.5 - 10 hectares)
- Include plots in different geographic regions
- Include plots with different crop types

**Mock NDVI Trajectories**:
- Healthy crop trajectory (NDVI 0.3 → 0.8 → 0.6)
- Stressed crop trajectory (NDVI 0.7 → 0.4 → 0.3)
- Stable crop trajectory (NDVI 0.6 → 0.6 → 0.6)
- Sparse data trajectory (3 points over 30 days)

### Testing Checklist

- [ ] All 28 correctness properties implemented as Hypothesis tests
- [ ] Each property test runs minimum 100 iterations
- [ ] Custom Hypothesis strategies for NDVI trajectories and plot boundaries
- [ ] Unit tests for all error handling paths
- [ ] Integration tests for external service dependencies
- [ ] Mock data fixtures for Sentinel-2 imagery
- [ ] Performance tests for 3-second response time requirement
- [ ] Load tests for 50 concurrent plot processing
- [ ] End-to-end tests for complete workflows
