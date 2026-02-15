# Implementation Plan: Market Data Pipeline

## Overview

This implementation plan breaks down the Market Data Pipeline into discrete coding tasks. The approach follows a bottom-up strategy: first establishing data models and storage, then building the scraper, followed by the forecasting service, and finally the API layer. Each major component includes property-based tests to validate correctness properties from the design document.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Create directory structure: `src/scraper/`, `src/forecaster/`, `src/api/`, `src/models/`, `src/storage/`, `tests/`
  - Create `requirements.txt` with dependencies: beautifulsoup4, requests, psycopg2-binary, redis, lightgbm, boto3, hypothesis (for property testing)
  - Set up pytest configuration with property-based testing support
  - Create shared configuration module for database, Redis, and AWS settings
  - _Requirements: All (foundational)_

- [ ] 2. Implement data models and storage layer
  - [ ] 2.1 Create core data models
    - Implement `PriceRecord` dataclass with all required fields and validation
    - Implement `Forecast` and `PricePrediction` dataclasses
    - Implement `ScrapeResult` and `ScrapeError` dataclasses
    - Implement `Location` and `MandiInfo` dataclasses with haversine distance calculation
    - _Requirements: 1.2, 3.1, 5.1, 5.2_
  
  - [ ]* 2.2 Write property test for data model validation
    - **Property 2: Complete Field Extraction**
    - **Validates: Requirements 1.2**
  
  - [ ] 2.3 Implement TimescaleDB storage interface
    - Create database connection manager with connection pooling
    - Implement `store_price_records()` with upsert logic (ON CONFLICT UPDATE)
    - Implement `query_prices()` with filtering by mandi, commodity, date range
    - Implement `get_latest_price()` for current price queries
    - Create database migration script for hypertable and indexes
    - _Requirements: 3.1, 3.3, 3.4, 7.1, 7.2_
  
  - [ ]* 2.4 Write property test for storage idempotency
    - **Property 8: Storage Idempotency**
    - **Validates: Requirements 3.4**
  
  - [ ]* 2.5 Write property test for query filtering
    - **Property 7: Query Result Filtering**
    - **Validates: Requirements 3.3**

- [ ] 3. Implement cache layer
  - [ ] 3.1 Create Redis cache interface
    - Implement `get_cached_price()` with error handling
    - Implement `set_cached_price()` with TTL support
    - Implement `get_cached_forecast()` and `set_cached_forecast()`
    - Implement `invalidate_cache_pattern()` for bulk invalidation
    - Add graceful fallback when Redis is unavailable
    - _Requirements: 6.1, 6.3, 6.4, 6.5_
  
  - [ ]* 3.2 Write property test for cache TTL enforcement
    - **Property 15: Cache TTL Enforcement**
    - **Validates: Requirements 6.3**
  
  - [ ]* 3.3 Write property test for graceful cache degradation
    - **Property 17: Graceful Cache Degradation**
    - **Validates: Requirements 6.5**

- [ ] 4. Implement Agmarknet scraper
  - [ ] 4.1 Create HTML parser for Agmarknet
    - Implement `parse_agmarknet_html()` to extract price tables
    - Handle various HTML structures and missing fields
    - Validate extracted data (required fields, price ranges)
    - _Requirements: 1.2, 9.1_
  
  - [ ]* 4.2 Write property test for complete field extraction
    - **Property 2: Complete Field Extraction**
    - **Validates: Requirements 1.2**
  
  - [ ] 4.3 Implement mandi distance filtering
    - Implement haversine distance calculation in `Location` class
    - Implement `get_mandis_within_radius()` to filter mandis by distance
    - _Requirements: 1.1_
  
  - [ ]* 4.4 Write property test for mandi radius filtering
    - **Property 1: Mandi Radius Filtering**
    - **Validates: Requirements 1.1**
  
  - [ ] 4.5 Implement timestamp validation
    - Create `validate_timestamp()` to check if timestamp is within acceptable range (up to 12 hours old)
    - _Requirements: 1.3, 9.2_
  
  - [ ]* 4.6 Write property test for delayed data acceptance
    - **Property 3: Delayed Data Acceptance**
    - **Validates: Requirements 1.3, 9.2**
  
  - [ ] 4.7 Implement retry logic with exponential backoff
    - Create `fetch_with_retry()` wrapper for HTTP requests
    - Implement exponential backoff (2s, 4s, 8s delays)
    - Log each retry attempt and final failure
    - _Requirements: 1.4_
  
  - [ ]* 4.8 Write property test for exponential backoff retry
    - **Property 4: Exponential Backoff Retry**
    - **Validates: Requirements 1.4**
  
  - [ ] 4.9 Implement main scraper function
    - Implement `scrape_mandi_prices()` orchestrating fetch, parse, validate, store
    - Handle partial failures (continue processing on individual record errors)
    - Invalidate cache after successful storage
    - Return `ScrapeResult` with metrics
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1_
  
  - [ ]* 4.10 Write property test for complete data persistence
    - **Property 5: Complete Data Persistence**
    - **Validates: Requirements 1.5, 3.1**
  
  - [ ]* 4.11 Write property test for partial failure resilience
    - **Property 24: Partial Failure Resilience**
    - **Validates: Requirements 9.1**

- [ ] 5. Checkpoint - Ensure scraper tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement forecasting service
  - [ ] 6.1 Implement feature extraction
    - Create `extract_features()` to build feature vector from historical data
    - Extract lagged prices (t-1, t-7, t-14, t-30 days)
    - Calculate rolling averages (7-day, 14-day, 30-day)
    - Extract categorical features (commodity, mandi, season, day of week, month)
    - Handle missing data with regional averages
    - _Requirements: 4.2, 5.3, 5.4, 9.4, 9.5_
  
  - [ ]* 6.2 Write property test for recent data usage
    - **Property 12: Recent Data Usage**
    - **Validates: Requirements 5.3**
  
  - [ ]* 6.3 Write property test for missing data fallback
    - **Property 13: Missing Data Fallback**
    - **Validates: Requirements 5.4**
  
  - [ ]* 6.4 Write property test for gap interpolation
    - **Property 26: Gap Interpolation**
    - **Validates: Requirements 9.4**
  
  - [ ]* 6.5 Write property test for arrival quantity imputation
    - **Property 27: Arrival Quantity Imputation**
    - **Validates: Requirements 9.5**
  
  - [ ] 6.6 Implement model loading and caching
    - Implement `load_model()` to download model artifact from S3
    - Cache loaded model in Lambda global scope for reuse
    - Handle S3 download errors with retry
    - _Requirements: 4.4, 5.1_
  
  - [ ] 6.7 Implement forecast generation
    - Implement `generate_forecast()` to create 48-hour predictions
    - Generate predictions with confidence intervals (quantile regression)
    - Validate confidence interval ordering (lower ≤ predicted ≤ upper)
    - Cache forecast result with 1-hour TTL
    - Return `Forecast` object with metadata
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [ ]* 6.8 Write property test for forecast structure completeness
    - **Property 10: Forecast Structure Completeness**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ]* 6.9 Write property test for confidence interval validity
    - **Property 11: Confidence Interval Validity**
    - **Validates: Requirements 5.2**
  
  - [ ] 6.10 Create Lambda handler for forecast service
    - Implement Lambda handler function
    - Parse event parameters (mandi_id, commodity_id)
    - Invoke `generate_forecast()` and return result
    - Handle errors and return appropriate responses
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7. Implement model training pipeline
  - [ ] 7.1 Create training data preparation script
    - Query 3+ years of historical data from TimescaleDB
    - Implement feature engineering pipeline (same as inference)
    - Split data into train/validation sets (80/20)
    - Handle missing values and outliers
    - _Requirements: 4.1, 4.2, 9.4, 9.5_
  
  - [ ]* 7.2 Write property test for complete feature extraction
    - **Property 9: Complete Feature Extraction**
    - **Validates: Requirements 4.2**
  
  - [ ] 7.3 Create model training script
    - Implement LightGBM training with hyperparameters
    - Train three models: median predictor, lower quantile (0.1), upper quantile (0.9)
    - Evaluate on validation set and calculate MAPE
    - Save model artifacts to S3 if MAPE < 15%
    - Alert if MAPE threshold not met
    - _Requirements: 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 7.4 Write unit tests for training pipeline
    - Test data preparation with sample dataset
    - Test model training and evaluation
    - Test model artifact saving
    - Test alert triggering on quality failure
    - _Requirements: 4.3, 4.4, 4.5_

- [ ] 8. Checkpoint - Ensure forecasting tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement API service
  - [ ] 9.1 Create API request validation
    - Implement parameter validation for all endpoints
    - Validate mandi_id and commodity_id formats
    - Validate date ranges (start < end, not in future)
    - Implement service area validation for mandis
    - _Requirements: 7.4_
  
  - [ ]* 9.2 Write property test for service area validation
    - **Property 21: Service Area Validation**
    - **Validates: Requirements 7.4**
  
  - [ ] 9.3 Implement current price endpoint
    - Create `/api/v1/prices/current` handler
    - Implement cache-first query pattern
    - Call `get_latest_price()` on cache miss
    - Add stale data flagging (> 24 hours old)
    - Return response with all required fields
    - _Requirements: 6.1, 7.1, 9.3_
  
  - [ ]* 9.4 Write property test for cache-first query pattern
    - **Property 14: Cache-First Query Pattern**
    - **Validates: Requirements 6.1**
  
  - [ ]* 9.5 Write property test for current price response completeness
    - **Property 18: Current Price Response Completeness**
    - **Validates: Requirements 7.1**
  
  - [ ]* 9.6 Write property test for stale data flagging
    - **Property 25: Stale Data Flagging**
    - **Validates: Requirements 9.3**
  
  - [ ] 9.7 Implement historical prices endpoint
    - Create `/api/v1/prices/historical` handler
    - Call `query_prices()` with date range filters
    - Order results by timestamp descending
    - Return empty array for no results (not 404)
    - _Requirements: 7.2_
  
  - [ ]* 9.8 Write property test for historical query ordering
    - **Property 19: Historical Query Ordering**
    - **Validates: Requirements 7.2**
  
  - [ ] 9.9 Implement multi-commodity query support
    - Extend endpoints to accept multiple commodity_ids
    - Group results by commodity_id
    - _Requirements: 7.3_
  
  - [ ]* 9.10 Write property test for multi-commodity grouping
    - **Property 20: Multi-Commodity Grouping**
    - **Validates: Requirements 7.3**
  
  - [ ] 9.11 Implement forecast endpoint
    - Create `/api/v1/prices/forecast` handler
    - Check cache for existing forecast (< 1 hour old)
    - Invoke forecast Lambda on cache miss
    - Return forecast with all required metadata
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 9.12 Write property test for cached forecast retrieval
    - **Property 23: Cached Forecast Retrieval**
    - **Validates: Requirements 8.2, 8.3**
  
  - [ ]* 9.13 Write property test for forecast response completeness
    - **Property 22: Forecast Response Completeness**
    - **Validates: Requirements 8.1, 8.4**
  
  - [ ] 9.14 Implement mandis listing endpoint
    - Create `/api/v1/mandis` handler
    - Filter mandis by location and radius
    - Return mandi info with distances
    - _Requirements: 1.1_
  
  - [ ] 9.15 Implement error handling for all endpoints
    - Return 400 for invalid requests with descriptive messages
    - Return 404 for non-existent mandi-commodity pairs
    - Return 503 when database is unavailable
    - Return 500 for unexpected errors with request ID
    - Set appropriate timeouts (5s for queries, 10s for forecasts)
    - _Requirements: 7.5, 8.5_
  
  - [ ] 9.16 Write unit tests for error handling
    - Test invalid request parameters
    - Test missing data scenarios
    - Test service unavailability
    - Test timeout handling
    - _Requirements: 7.5, 8.5_

- [ ] 10. Implement scheduling and monitoring
  - [ ] 10.1 Create EventBridge scheduler configuration
    - Define EventBridge rule for 6-hour schedule
    - Configure rule to trigger scraper Lambda
    - Pass FPO location and mandi list in event payload
    - Implement concurrent execution prevention
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ] 10.2 Write unit test for scheduler event handling
    - Test event payload parsing
    - Test concurrent execution prevention
    - _Requirements: 2.2, 2.3_
  
  - [ ] 10.3 Implement CloudWatch metrics emission
    - Emit scraper metrics: duration, success/failure, records processed
    - Emit API metrics: latency, cache hit rate, error rate
    - Emit forecast metrics: generation time, cache usage
    - _Requirements: 10.1, 10.5_
  
  - [ ]* 10.4 Write property test for metrics emission
    - **Property 28: Metrics Emission**
    - **Validates: Requirements 10.5**
  
  - [ ] 10.5 Implement alerting via SNS
    - Create SNS topic for pipeline alerts
    - Trigger alert on scraper failure after retries
    - Trigger alert on model quality degradation
    - Trigger alert on database unavailability
    - _Requirements: 2.4, 4.5, 10.1_
  
  - [ ]* 10.6 Write property test for alert on scraping failure
    - **Property 6: Alert on Scraping Failure**
    - **Validates: Requirements 2.4, 10.1**
  
  - [ ] 10.7 Create CloudWatch dashboard
    - Add widgets for scraper success rate and duration
    - Add widgets for API latency and error rate
    - Add widgets for cache hit rate
    - Add widgets for forecast generation metrics
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 11. Implement cache invalidation integration
  - [ ] 11.1 Add cache invalidation to scraper
    - After successful data storage, invalidate related cache entries
    - Use pattern matching to invalidate all affected keys
    - _Requirements: 6.4_
  
  - [ ]* 11.2 Write property test for cache invalidation on update
    - **Property 16: Cache Invalidation on Update**
    - **Validates: Requirements 6.4**

- [ ] 12. Create deployment infrastructure
  - [ ] 12.1 Create Lambda deployment packages
    - Package scraper Lambda with dependencies
    - Package forecast Lambda with dependencies and model artifact
    - Package API Lambda with dependencies
    - Configure Lambda settings (memory, timeout, environment variables)
    - _Requirements: All (deployment)_
  
  - [ ] 12.2 Create Terraform/CloudFormation templates
    - Define TimescaleDB RDS instance
    - Define ElastiCache Redis cluster
    - Define Lambda functions and IAM roles
    - Define API Gateway configuration
    - Define EventBridge rule
    - Define SNS topic and subscriptions
    - Define S3 bucket for model artifacts
    - _Requirements: All (infrastructure)_
  
  - [ ] 12.3 Create database migration scripts
    - Create initial schema with hypertable
    - Create indexes for common queries
    - Create continuous aggregates for daily averages
    - Set up data retention policies
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ] 13. Final checkpoint - Integration testing
  - [ ] 13.1 Test end-to-end scraping flow
    - Trigger scraper Lambda manually
    - Verify data appears in TimescaleDB
    - Verify cache invalidation occurs
    - Verify metrics are emitted
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ] 13.2 Test end-to-end forecast flow
    - Request forecast via API
    - Verify forecast generation and caching
    - Verify subsequent request uses cache
    - Verify cache expiration after TTL
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 8.1, 8.2, 8.3_
  
  - [ ] 13.3 Test error recovery scenarios
    - Test scraper with Agmarknet unavailable
    - Test API with database unavailable
    - Test API with Redis unavailable
    - Verify alerts are triggered
    - _Requirements: 1.4, 6.5, 10.1_
  
  - [ ] 13.4 Run property-based tests with high iteration count
    - Run all property tests with 1000 iterations
    - Verify no failures or edge cases discovered
    - _Requirements: All testable properties_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and error conditions
- Integration tests verify end-to-end flows and component interactions
- The implementation follows a bottom-up approach: data layer → scraper → forecaster → API → infrastructure
- Checkpoints ensure incremental validation at major milestones
