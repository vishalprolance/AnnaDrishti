# Implementation Plan: Satellite Context Provider

## Overview

This implementation plan breaks down the Satellite Context Provider into discrete coding tasks. The system will be built using Python with AWS Lambda for serverless execution, S3 for imagery storage, Timestream for NDVI time-series data, and EventBridge for event-driven workflows. The implementation follows a bottom-up approach, starting with core NDVI calculation logic, then building imagery acquisition, and finally the Context Service API.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Create Python project structure with separate modules for acquisition, processing, and API
  - Set up requirements.txt with dependencies: boto3, numpy, rasterio, hypothesis, pytest
  - Configure AWS SAM or Serverless Framework for Lambda deployment
  - Create shared data models module for NDVIResult, NDVITrajectory, ImageryMetadata
  - _Requirements: All requirements (foundation)_

- [ ] 2. Implement core NDVI calculation logic
  - [ ] 2.1 Implement band extraction from Sentinel-2 GeoTIFF
    - Write `extract_bands(geotiff: GeoTIFF) -> Tuple[np.ndarray, np.ndarray]` function
    - Use rasterio to read Band 4 (red) and Band 8 (NIR) at 10m resolution
    - Handle invalid GeoTIFF format with appropriate exceptions
    - _Requirements: 2.1_
  
  - [ ]* 2.2 Write property test for band extraction
    - **Property 24: Band Extraction Dimensions**
    - **Validates: Requirements 2.1**
  
  - [ ] 2.3 Implement NDVI array calculation
    - Write `compute_ndvi_array(red: np.ndarray, nir: np.ndarray) -> np.ndarray` function
    - Implement formula: (NIR - Red) / (NIR + Red)
    - Handle division by zero by assigning NDVI value of 0
    - _Requirements: 2.2, 2.3_
  
  - [ ]* 2.4 Write property test for NDVI formula correctness
    - **Property 2: NDVI Formula Correctness**
    - **Validates: Requirements 2.2, 2.3**
  
  - [ ] 2.5 Implement spatial masking to plot boundaries
    - Write `mask_to_plot(ndvi_array: np.ndarray, plot_bounds: GeoJSON, geotransform: Tuple) -> np.ndarray` function
    - Use shapely for polygon operations and coordinate transformations
    - Filter pixels to only those within plot boundary polygon
    - _Requirements: 2.4_
  
  - [ ]* 2.6 Write property test for spatial masking
    - **Property 25: Spatial Masking to Plot Boundaries**
    - **Validates: Requirements 2.4**
  
  - [ ] 2.7 Implement mean NDVI calculation
    - Write function to compute mean NDVI across masked pixel array
    - Handle edge case: require minimum 10 pixels for valid calculation
    - _Requirements: 2.5_
  
  - [ ]* 2.8 Write property test for mean NDVI calculation
    - **Property 3: Mean NDVI Calculation**
    - **Validates: Requirements 2.5**

- [ ] 3. Implement NDVI storage and time-series management
  - [ ] 3.1 Create Timestream client and table schema
    - Set up boto3 Timestream client with retry configuration
    - Define table schema: dimensions (plot_id, crop_type, region), measures (ndvi_value, cloud_cover_percent, pixel_count)
    - _Requirements: 2.6, 3.1_
  
  - [ ] 3.2 Implement NDVI time-series storage
    - Write `store_ndvi_timeseries(plot_id: str, ndvi_value: float, timestamp: datetime, metadata: dict) -> None` function
    - Store NDVI with plot identifier, acquisition timestamp, and cloud cover percentage
    - Handle Timestream write failures with exponential backoff retry
    - _Requirements: 2.6, 3.2_
  
  - [ ]* 3.3 Write property test for NDVI storage completeness
    - **Property 4: NDVI Storage Completeness**
    - **Validates: Requirements 2.6**
  
  - [ ] 3.4 Implement NDVI trajectory query
    - Write `get_ndvi_trajectory(plot_id: str, start_date: datetime, end_date: datetime) -> NDVITrajectory` function
    - Query Timestream for NDVI values within date range
    - Return results ordered chronologically by acquisition timestamp
    - _Requirements: 3.3_
  
  - [ ]* 3.5 Write property test for chronological ordering
    - **Property 5: Time-Series Chronological Ordering**
    - **Validates: Requirements 3.3**
  
  - [ ]* 3.6 Write property test for time-series append behavior
    - **Property 6: Time-Series Append Behavior**
    - **Validates: Requirements 3.2**

- [ ] 4. Checkpoint - Ensure core NDVI logic tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Sentinel-2 imagery acquisition service
  - [ ] 5.1 Create Copernicus Hub API client
    - Implement authentication with Copernicus Open Access Hub
    - Write `query_sentinel2_imagery(plot_bounds: GeoJSON, start_date: datetime, end_date: datetime) -> List[SentinelTile]` function
    - Handle API rate limits and implement exponential backoff retry
    - _Requirements: 1.1, 1.2_
  
  - [ ] 5.2 Implement tile selection logic
    - Write `select_best_tile(tiles: List[SentinelTile], max_cloud_cover: float) -> SentinelTile` function
    - Select tile with lowest cloud cover percentage
    - Return None if all tiles exceed max_cloud_cover threshold
    - _Requirements: 1.3_
  
  - [ ]* 5.3 Write property test for tile selection
    - **Property 1: Tile Selection Minimizes Cloud Cover**
    - **Validates: Requirements 1.3**
  
  - [ ] 5.4 Implement imagery download and S3 storage
    - Write `download_sentinel2_imagery(plot_id: str, plot_bounds: GeoJSON) -> ImageryMetadata` function
    - Download GeoTIFF from Copernicus Hub
    - Compress using LZW compression before upload
    - Store in S3 with key format: `raw/{plot_id}/{YYYY-MM-DD}_{tile_id}.tif`
    - _Requirements: 1.1, 1.4, 9.4_
  
  - [ ]* 5.5 Write property test for S3 storage key format
    - **Property 23: S3 Storage Key Format**
    - **Validates: Requirements 1.4**
  
  - [ ]* 5.6 Write property test for GeoTIFF compression
    - **Property 20: GeoTIFF Compression**
    - **Validates: Requirements 9.4**
  
  - [ ] 5.7 Implement data gap recording
    - Write function to record data gaps when no cloud-free imagery is available
    - Store data gap records in DynamoDB with plot_id, timestamp, and reason
    - _Requirements: 1.5, 7.1_
  
  - [ ]* 5.8 Write property test for data gap recording
    - **Property 17: Data Gap Recording**
    - **Validates: Requirements 7.1**

- [ ] 6. Implement NDVI processing Lambda function
  - [ ] 6.1 Create Lambda handler for S3 event trigger
    - Write Lambda handler triggered by S3 event (new imagery upload)
    - Extract plot_id and timestamp from S3 key
    - Retrieve plot boundaries from DynamoDB
    - _Requirements: 2.1, 2.2_
  
  - [ ] 6.2 Wire NDVI calculation pipeline
    - Call extract_bands → compute_ndvi_array → mask_to_plot → compute mean
    - Store result in Timestream using store_ndvi_timeseries
    - Handle errors and log failures to CloudWatch
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [ ]* 6.3 Write integration test for NDVI processing pipeline
    - Test end-to-end flow with sample GeoTIFF fixture
    - Verify NDVI stored in Timestream with correct metadata
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [ ] 7. Implement harvest readiness confirmation logic
  - [ ] 7.1 Implement NDVI trend detection
    - Write function to detect declining, stable, or increasing trends over 14 days
    - Use linear regression or simple slope calculation
    - Handle insufficient data case (fewer than 3 data points)
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [ ]* 7.2 Write property test for harvest readiness trend detection
    - **Property 7: Harvest Readiness Trend Detection**
    - **Validates: Requirements 4.2, 4.3, 4.4**
  
  - [ ] 7.3 Implement confidence level calculation
    - Write function to calculate confidence based on data recency
    - High: 0-5 days, Medium: 5-10 days, Low: 10+ days
    - _Requirements: 4.5_
  
  - [ ]* 7.4 Write property test for confidence level calculation
    - **Property 8: Confidence Level Based on Data Recency**
    - **Validates: Requirements 4.5**
  
  - [ ] 7.5 Implement harvest readiness confirmation function
    - Write `confirm_harvest_readiness(plot_id: str) -> HarvestReadinessResponse` function
    - Query NDVI trajectory for past 30 days
    - Detect trend and calculate confidence level
    - Return structured response with signal, confidence, and data quality
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 7.6 Write property test for query date range
    - **Property 26: Query Date Range for Harvest Readiness**
    - **Validates: Requirements 4.1**

- [ ] 8. Implement regional yield estimation logic
  - [ ] 8.1 Create Market Data Pipeline client
    - Write client to query regional average yields by crop type and region
    - Handle missing data gracefully (return None)
    - _Requirements: 5.2_
  
  - [ ]* 8.2 Write property test for regional yield query parameters
    - **Property 27: Regional Yield Data Query Parameters**
    - **Validates: Requirements 5.2**
  
  - [ ] 8.3 Implement yield adjustment logic
    - Write function to calculate adjustment factor based on mean NDVI
    - +10% when mean NDVI > 0.7, -10% when mean NDVI < 0.5, 0% otherwise
    - _Requirements: 5.3, 5.4_
  
  - [ ] 8.4 Implement yield estimation function
    - Write `estimate_regional_yield(plot_id: str) -> YieldEstimateResponse` function
    - Calculate: plot_area × regional_average × adjustment_factor
    - Include disclaimer: "directional estimate - confirm with farmer"
    - Handle missing regional data gracefully
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 8.5 Write property test for yield estimation formula
    - **Property 9: Yield Estimation Formula**
    - **Validates: Requirements 5.1, 5.3, 5.4**
  
  - [ ]* 8.6 Write property test for yield estimate disclaimer
    - **Property 10: Yield Estimate Disclaimer Presence**
    - **Validates: Requirements 5.5**

- [ ] 9. Checkpoint - Ensure harvest readiness and yield estimation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement crop distress detection logic
  - [ ] 10.1 Implement 30-day moving average calculation
    - Write function to compute NDVI baseline as 30-day moving average
    - Query Timestream for past 30 days of NDVI data
    - _Requirements: 6.1_
  
  - [ ]* 10.2 Write property test for moving average window
    - **Property 28: 30-Day Moving Average Window**
    - **Validates: Requirements 6.1**
  
  - [ ] 10.3 Implement distress detection and recovery logic
    - Write `detect_crop_distress(plot_id: str, current_ndvi: float) -> Optional[DistressAlert]` function
    - Flag distress when current NDVI drops > 0.15 below baseline
    - Clear flag when NDVI recovers to within 0.05 of baseline
    - Store distress state in DynamoDB
    - _Requirements: 6.2, 6.5_
  
  - [ ]* 10.4 Write property test for distress state transitions
    - **Property 11: Distress Detection State Transitions**
    - **Validates: Requirements 6.2, 6.5**
  
  - [ ] 10.5 Implement seasonal distress suppression
    - Write function to check if current date is within harvest season
    - Query crop calendar from DynamoDB by crop type
    - Suppress distress detection during harvest season
    - _Requirements: 6.6_
  
  - [ ]* 10.6 Write property test for seasonal suppression
    - **Property 14: Seasonal Distress Suppression**
    - **Validates: Requirements 6.6**
  
  - [ ] 10.7 Implement distress alert generation
    - Write function to generate DistressAlert with all required fields
    - Include: plot_id, current_ndvi, baseline_ndvi, decline_magnitude, timestamp
    - _Requirements: 6.3_
  
  - [ ]* 10.8 Write property test for distress alert structure
    - **Property 12: Distress Alert Structure**
    - **Validates: Requirements 6.3**
  
  - [ ] 10.9 Implement EventBridge event publishing
    - Write function to publish distress alerts to EventBridge event bus
    - Include event detail with DistressAlert data
    - Handle publishing failures with retry logic
    - _Requirements: 6.4_
  
  - [ ]* 10.10 Write property test for distress event publishing
    - **Property 13: Distress Event Publishing**
    - **Validates: Requirements 6.4**

- [ ] 11. Implement Context Service API endpoints
  - [ ] 11.1 Create API Gateway configuration
    - Define REST API with routes for NDVI queries, harvest readiness, yield estimation
    - Configure Lambda integration for each endpoint
    - Set up CORS and authentication
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  
  - [ ] 11.2 Implement get_current_ndvi endpoint
    - Write Lambda handler for GET /plots/{plot_id}/ndvi
    - Query most recent NDVI from Timestream
    - Include data quality metadata (recency, cloud cover, confidence)
    - Handle missing data gracefully
    - _Requirements: 10.1, 7.2, 7.3, 7.4_
  
  - [ ] 11.3 Implement get_ndvi_trajectory endpoint
    - Write Lambda handler for GET /plots/{plot_id}/ndvi/trajectory
    - Accept start_date and end_date query parameters
    - Return chronologically ordered NDVI time-series
    - _Requirements: 10.2_
  
  - [ ] 11.4 Implement confirm_harvest_readiness endpoint
    - Write Lambda handler for GET /plots/{plot_id}/harvest-readiness
    - Call confirm_harvest_readiness function
    - Return structured response with signal, confidence, and data quality
    - _Requirements: 10.3_
  
  - [ ] 11.5 Implement estimate_regional_yield endpoint
    - Write Lambda handler for GET /plots/{plot_id}/yield-estimate
    - Call estimate_regional_yield function
    - Return structured response with estimate and disclaimer
    - _Requirements: 10.4_
  
  - [ ] 11.6 Implement error response handling
    - Write middleware to catch exceptions and return structured error responses
    - Include error code and human-readable message
    - Return appropriate HTTP status codes (400, 404, 500)
    - _Requirements: 10.6_
  
  - [ ]* 11.7 Write property test for error response structure
    - **Property 22: Error Response Structure**
    - **Validates: Requirements 10.6**
  
  - [ ]* 11.8 Write property test for data quality metadata inclusion
    - **Property 16: Data Recency Metadata Inclusion**
    - **Validates: Requirements 7.3, 10.7**

- [ ] 12. Implement graceful degradation logic
  - [ ] 12.1 Implement staleness indicator logic
    - Write function to classify data recency: "fresh" (0-5 days), "recent" (5-10 days), "stale" (10+ days)
    - Add staleness indicator to all API responses
    - _Requirements: 7.3_
  
  - [ ] 12.2 Implement graceful degradation for missing data
    - Modify API endpoints to return most recent data with staleness indicator during data gaps
    - Return "no data available" when no NDVI data exists for plot
    - Ensure no exceptions block dependent workflows
    - _Requirements: 7.2, 7.4_
  
  - [ ]* 12.3 Write property test for graceful degradation
    - **Property 15: Graceful Degradation for Missing Data**
    - **Validates: Requirements 7.2, 7.4**

- [ ] 13. Implement plot prioritization and batching logic
  - [ ] 13.1 Implement plot prioritization by data gap length
    - Write function to query plots with longest data gaps
    - Sort plots by last_ndvi_update timestamp (oldest first)
    - Process prioritized plots when fresh imagery becomes available
    - _Requirements: 7.6_
  
  - [ ]* 13.2 Write property test for plot prioritization
    - **Property 18: Plot Prioritization by Data Gap Length**
    - **Validates: Requirements 7.6**
  
  - [ ] 13.3 Implement geographic batching for clustered plots
    - Write function to cluster plots by geographic proximity
    - Use spatial indexing (e.g., geohash) to identify clusters
    - Batch imagery downloads for plots within same Sentinel-2 tile
    - _Requirements: 8.4_
  
  - [ ]* 13.4 Write property test for geographic batching
    - **Property 19: Geographic Batching for Clustered Plots**
    - **Validates: Requirements 8.4**

- [ ] 14. Implement plot lifecycle management
  - [ ] 14.1 Implement plot deactivation archival
    - Write function triggered when plot is deactivated
    - Move all associated imagery from S3 Standard to S3 Glacier
    - Archive NDVI time-series data to S3 Glacier
    - _Requirements: 9.5_
  
  - [ ]* 14.2 Write property test for plot deactivation archival
    - **Property 21: Plot Deactivation Triggers Archival**
    - **Validates: Requirements 9.5**

- [ ] 15. Implement EventBridge scheduled imagery acquisition
  - [ ] 15.1 Create EventBridge rule for 5-day schedule
    - Configure EventBridge rule to trigger every 5 days
    - Target Lambda function for imagery acquisition
    - _Requirements: 1.6_
  
  - [ ] 15.2 Implement scheduled acquisition Lambda handler
    - Write Lambda handler to query all active plots
    - Call download_sentinel2_imagery for each plot
    - Implement batching to avoid rate limits
    - Handle failures and record data gaps
    - _Requirements: 1.1, 1.2, 1.5_
  
  - [ ]* 15.3 Write integration test for scheduled acquisition
    - Test Lambda handler with mock EventBridge event
    - Verify imagery downloads triggered for all active plots
    - _Requirements: 1.1, 1.2, 1.6_

- [ ] 16. Checkpoint - Ensure all integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Set up AWS infrastructure with Infrastructure as Code
  - [ ] 17.1 Create CloudFormation or Terraform templates
    - Define S3 buckets with lifecycle policies (Standard → Intelligent-Tiering after 30 days)
    - Define Timestream database and table for NDVI time-series
    - Define DynamoDB tables for plot metadata and data gaps
    - Define Lambda functions with appropriate IAM roles
    - Define API Gateway REST API
    - Define EventBridge rules and event bus
    - _Requirements: 8.5, 9.1, 9.2, 9.3_
  
  - [ ] 17.2 Configure Lambda environment variables
    - Set S3 bucket names, Timestream database/table names, DynamoDB table names
    - Set Copernicus Hub API credentials (from AWS Secrets Manager)
    - Set EventBridge event bus name
    - _Requirements: All requirements (infrastructure)_
  
  - [ ] 17.3 Configure CloudWatch alarms and monitoring
    - Create alarms for Lambda errors, Timestream write failures, S3 upload failures
    - Set up CloudWatch dashboard for NDVI processing metrics
    - Configure SNS notifications for critical alerts
    - _Requirements: All requirements (monitoring)_

- [ ] 18. Final integration and end-to-end testing
  - [ ]* 18.1 Write end-to-end test for complete workflow
    - Test: scheduled acquisition → imagery download → NDVI processing → API query
    - Verify distress detection triggers EventBridge event
    - Verify harvest readiness confirmation returns correct signal
    - Verify yield estimation returns correct estimate
    - _Requirements: All requirements_
  
  - [ ]* 18.2 Write load test for concurrent plot processing
    - Simulate 50 concurrent NDVI calculations
    - Verify system handles load without failures
    - _Requirements: 8.3_
  
  - [ ]* 18.3 Write performance test for API response time
    - Verify get_current_ndvi returns within 3 seconds for cached data
    - _Requirements: 8.1_

- [ ] 19. Final checkpoint - Ensure all tests pass and system is ready for deployment
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows and external service dependencies
- Infrastructure tasks use CloudFormation or Terraform for reproducible deployments
