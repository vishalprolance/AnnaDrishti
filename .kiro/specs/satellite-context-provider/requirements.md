# Requirements Document

## Introduction

The Satellite Context Provider is an assistive component that provides directional crop health and yield context using Sentinel-2 satellite imagery for the Anna Drishti agricultural platform. It performs NDVI (Normalized Difference Vegetation Index) temporal analysis to support crop stage confirmation, regional yield estimation, and crop distress detection for insurance assistance. The system is designed to provide context that assists decision-making while acknowledging inherent limitations in satellite-based measurements.

## Glossary

- **Satellite_Context_Provider**: The system component that retrieves, processes, and analyzes Sentinel-2 satellite imagery to provide crop health context
- **NDVI**: Normalized Difference Vegetation Index, a measure of vegetation health calculated from red and near-infrared spectral bands
- **Sentinel-2**: European Space Agency satellite constellation providing 10m resolution multispectral imagery with 5-day revisit cycle
- **Plot**: A farmer's agricultural field with defined geographic boundaries
- **NDVI_Trajectory**: Time-series sequence of NDVI values for a plot showing vegetation health trends
- **Crop_Distress**: Anomalous decline in NDVI values indicating potential crop damage or stress
- **Regional_Yield_Estimate**: Directional yield prediction based on plot area multiplied by regional average yields (not plot-precise)
- **Harvest_Readiness**: Crop stage where NDVI trajectory indicates maturity suitable for harvesting
- **Cloud_Cover**: Atmospheric conditions that prevent satellite imagery acquisition, creating data gaps
- **Graceful_Degradation**: System behavior that maintains functionality when satellite data is unavailable
- **Sell_Agent**: System component that manages crop sale workflows and requires harvest-readiness context
- **Process_Agent**: System component that manages post-harvest processing workflows
- **Insurance_Assist**: System component that handles crop insurance claims and requires distress detection alerts
- **GeoTIFF**: Georeferenced raster image format used for satellite imagery storage
- **Copernicus_Hub**: European Space Agency's open access platform for Sentinel satellite data

## Requirements

### Requirement 1: Sentinel-2 Imagery Acquisition

**User Story:** As the Satellite Context Provider, I want to retrieve Sentinel-2 imagery for farmer plots, so that I can perform NDVI analysis for crop health monitoring.

#### Acceptance Criteria

1. WHEN a plot location is registered, THE Satellite_Context_Provider SHALL retrieve Sentinel-2 imagery covering that plot's geographic boundaries
2. WHEN imagery is requested, THE Satellite_Context_Provider SHALL query the Copernicus_Hub for the most recent cloud-free imagery within the past 10 days
3. WHEN multiple imagery tiles are available, THE Satellite_Context_Provider SHALL select the tile with the lowest cloud cover percentage
4. WHEN imagery is downloaded, THE Satellite_Context_Provider SHALL store it in S3 as GeoTIFF format with plot identifier and acquisition timestamp
5. IF no cloud-free imagery is available within 10 days, THEN THE Satellite_Context_Provider SHALL record the data gap and continue without blocking workflows
6. THE Satellite_Context_Provider SHALL schedule imagery downloads every 5 days to align with Sentinel-2 revisit cycle

### Requirement 2: NDVI Calculation

**User Story:** As the Satellite Context Provider, I want to calculate NDVI from Sentinel-2 imagery, so that I can quantify vegetation health for each plot.

#### Acceptance Criteria

1. WHEN Sentinel-2 imagery is retrieved, THE Satellite_Context_Provider SHALL extract the red band (Band 4) and near-infrared band (Band 8) at 10m resolution
2. THE Satellite_Context_Provider SHALL calculate NDVI using the formula: (NIR - Red) / (NIR + Red)
3. WHEN calculating NDVI, THE Satellite_Context_Provider SHALL handle division by zero by assigning NDVI value of 0
4. THE Satellite_Context_Provider SHALL extract NDVI values for pixels within the plot's geographic boundaries
5. THE Satellite_Context_Provider SHALL compute the mean NDVI value across all pixels within the plot
6. WHEN NDVI calculation completes, THE Satellite_Context_Provider SHALL store the mean NDVI value with plot identifier, acquisition timestamp, and cloud cover percentage

### Requirement 3: NDVI Temporal Analysis

**User Story:** As the Satellite Context Provider, I want to track NDVI values over time, so that I can identify vegetation health trends and crop stage transitions.

#### Acceptance Criteria

1. THE Satellite_Context_Provider SHALL maintain a time-series of NDVI values for each plot spanning the current growing season
2. WHEN a new NDVI value is calculated, THE Satellite_Context_Provider SHALL append it to the plot's NDVI_Trajectory with acquisition timestamp
3. WHEN queried for NDVI trends, THE Satellite_Context_Provider SHALL return NDVI values ordered chronologically with timestamps
4. THE Satellite_Context_Provider SHALL retain NDVI time-series data for the current growing season plus 90 days
5. WHEN the retention period expires, THE Satellite_Context_Provider SHALL archive historical NDVI data to S3 Glacier

### Requirement 4: Harvest Readiness Confirmation

**User Story:** As the Sell Agent, I want to validate farmer harvest-readiness signals against NDVI trajectory patterns, so that I can confirm crop maturity before initiating sale workflows.

#### Acceptance Criteria

1. WHEN a farmer signals harvest readiness, THE Satellite_Context_Provider SHALL retrieve the plot's NDVI_Trajectory for the past 30 days
2. WHEN NDVI_Trajectory shows a declining trend over the past 14 days, THE Satellite_Context_Provider SHALL return a "consistent with harvest readiness" signal
3. WHEN NDVI_Trajectory shows an increasing or stable trend, THE Satellite_Context_Provider SHALL return a "not consistent with harvest readiness" signal
4. IF insufficient NDVI data exists (fewer than 3 data points in 30 days), THEN THE Satellite_Context_Provider SHALL return "insufficient data" without blocking the workflow
5. THE Satellite_Context_Provider SHALL include the confidence level based on data recency (high if latest data is within 5 days, medium if 5-10 days, low if older than 10 days)

### Requirement 5: Regional Yield Estimation

**User Story:** As the Sell Agent, I want directional yield estimates for farmer plots, so that I can provide context for sale quantity negotiations.

#### Acceptance Criteria

1. WHEN a yield estimate is requested, THE Satellite_Context_Provider SHALL calculate it as: plot area (hectares) × regional average yield (tons/hectare)
2. THE Satellite_Context_Provider SHALL retrieve regional average yield values from the Market_Data_Pipeline for the plot's crop type and geographic region
3. WHEN NDVI_Trajectory indicates above-average vegetation health (mean NDVI > 0.7), THE Satellite_Context_Provider SHALL apply a +10% adjustment to the regional average
4. WHEN NDVI_Trajectory indicates below-average vegetation health (mean NDVI < 0.5), THE Satellite_Context_Provider SHALL apply a -10% adjustment to the regional average
5. THE Satellite_Context_Provider SHALL label all yield estimates as "directional estimate - confirm with farmer" to indicate they are not plot-precise measurements
6. IF regional average yield data is unavailable, THEN THE Satellite_Context_Provider SHALL return "insufficient data for estimation" without blocking workflows

### Requirement 6: Crop Distress Detection

**User Story:** As the Insurance Assist component, I want to detect NDVI anomalies indicating crop damage, so that I can proactively alert farmers about potential insurance claims.

#### Acceptance Criteria

1. WHEN a new NDVI value is calculated, THE Satellite_Context_Provider SHALL compare it to the plot's 30-day NDVI moving average
2. IF the new NDVI value is more than 0.15 units below the moving average, THEN THE Satellite_Context_Provider SHALL flag the plot for potential crop distress
3. WHEN crop distress is flagged, THE Satellite_Context_Provider SHALL generate an alert containing: plot identifier, current NDVI, baseline NDVI, decline magnitude, and acquisition timestamp
4. THE Satellite_Context_Provider SHALL send crop distress alerts to the Insurance_Assist component via event notification
5. WHEN NDVI recovers to within 0.05 units of the baseline, THE Satellite_Context_Provider SHALL clear the distress flag and send a recovery notification
6. THE Satellite_Context_Provider SHALL not flag distress during expected NDVI decline periods (harvest season based on crop calendar)

### Requirement 7: Graceful Degradation for Missing Data

**User Story:** As the Satellite Context Provider, I want to handle cloud cover and data gaps gracefully, so that the system continues to function when satellite imagery is unavailable.

#### Acceptance Criteria

1. WHEN satellite imagery is unavailable due to cloud cover, THE Satellite_Context_Provider SHALL record the data gap with timestamp and reason
2. WHEN queried for NDVI context during a data gap, THE Satellite_Context_Provider SHALL return the most recent available NDVI value with a staleness indicator
3. THE Satellite_Context_Provider SHALL include data recency metadata in all responses: "fresh" (0-5 days), "recent" (5-10 days), "stale" (10+ days)
4. WHEN no NDVI data exists for a plot, THE Satellite_Context_Provider SHALL return "no data available" without blocking dependent workflows
5. THE Satellite_Context_Provider SHALL continue to attempt imagery downloads during data gaps according to the scheduled 5-day cycle
6. WHEN fresh imagery becomes available after a data gap, THE Satellite_Context_Provider SHALL prioritize processing plots with the longest data gaps

### Requirement 8: Performance and Scalability

**User Story:** As the system administrator, I want the Satellite Context Provider to handle 500+ farmer plots efficiently, so that all farmers receive timely crop health context.

#### Acceptance Criteria

1. WHEN NDVI context is requested, THE Satellite_Context_Provider SHALL return results within 3 seconds for cached data
2. WHEN NDVI calculation is triggered, THE Satellite_Context_Provider SHALL process a single plot's imagery within 30 seconds
3. THE Satellite_Context_Provider SHALL support concurrent NDVI calculations for up to 50 plots simultaneously
4. THE Satellite_Context_Provider SHALL batch imagery downloads to process multiple plots in a single Copernicus_Hub query when plots are geographically clustered
5. WHEN storage exceeds 80% capacity, THE Satellite_Context_Provider SHALL transition imagery older than 30 days to S3 Glacier storage class

### Requirement 9: Data Storage and Lifecycle Management

**User Story:** As the system administrator, I want efficient storage management for satellite imagery, so that storage costs remain sustainable as the system scales.

#### Acceptance Criteria

1. THE Satellite_Context_Provider SHALL store raw Sentinel-2 GeoTIFF imagery in S3 Standard storage class
2. THE Satellite_Context_Provider SHALL transition imagery to S3 Intelligent-Tiering after 30 days
3. THE Satellite_Context_Provider SHALL store NDVI time-series data in a time-series database (Timestream or RDS) for fast query access
4. THE Satellite_Context_Provider SHALL compress GeoTIFF imagery using LZW compression before S3 upload
5. WHEN a plot is deactivated, THE Satellite_Context_Provider SHALL archive all associated imagery and NDVI data to S3 Glacier within 7 days

### Requirement 10: Integration with Dependent Systems

**User Story:** As a system integrator, I want the Satellite Context Provider to expose clear APIs for dependent components, so that Sell Agent, Process Agent, and Insurance Assist can consume crop health context.

#### Acceptance Criteria

1. THE Satellite_Context_Provider SHALL expose a REST API endpoint for retrieving current NDVI values by plot identifier
2. THE Satellite_Context_Provider SHALL expose a REST API endpoint for retrieving NDVI_Trajectory time-series by plot identifier and date range
3. THE Satellite_Context_Provider SHALL expose a REST API endpoint for harvest readiness confirmation by plot identifier
4. THE Satellite_Context_Provider SHALL expose a REST API endpoint for regional yield estimation by plot identifier
5. THE Satellite_Context_Provider SHALL publish crop distress alerts to an EventBridge event bus for Insurance_Assist subscription
6. WHEN API requests fail, THE Satellite_Context_Provider SHALL return structured error responses with error codes and human-readable messages
7. THE Satellite_Context_Provider SHALL include data quality metadata in all API responses: recency, cloud cover percentage, and confidence level
