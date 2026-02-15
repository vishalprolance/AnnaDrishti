# Requirements Document: Market Data Pipeline

## Introduction

The Market Data Pipeline provides real-time market intelligence for the Anna Drishti platform by scraping mandi (agricultural market) prices from Agmarknet, storing historical data, and generating price forecasts. This system powers the Sell Agent's price intelligence capabilities, enabling farmers and FPOs to make informed selling decisions based on current market conditions and predicted price trends.

## Glossary

- **Agmarknet**: Government of India's agricultural marketing information network that publishes mandi prices
- **Mandi**: Agricultural wholesale market where farmers sell produce
- **FPO**: Farmer Producer Organization
- **Scraper**: Automated system that extracts price data from Agmarknet website
- **Price_Forecaster**: Machine learning model that predicts future mandi prices
- **Price_Cache**: Redis-based temporary storage for frequently accessed price data
- **Data_Store**: Time-series database storing historical mandi price records
- **Pipeline_Scheduler**: EventBridge-based system that triggers scraping jobs
- **API_Service**: REST endpoints for querying prices and forecasts
- **MAPE**: Mean Absolute Percentage Error, a forecast accuracy metric
- **TTL**: Time To Live, duration for which cached data remains valid

## Requirements

### Requirement 1: Scrape Mandi Prices from Agmarknet

**User Story:** As a system operator, I want to automatically scrape mandi prices from Agmarknet, so that the platform has current market data for price intelligence.

#### Acceptance Criteria

1. WHEN the Pipeline_Scheduler triggers a scraping job, THE Scraper SHALL retrieve price data from Agmarknet for all mandis within 100km of the configured FPO location
2. WHEN the Scraper retrieves price data, THE Scraper SHALL extract commodity name, mandi name, arrival quantity, minimum price, maximum price, modal price, and date
3. WHEN Agmarknet returns delayed data, THE Scraper SHALL accept and store prices with timestamps up to 12 hours in the past
4. IF Agmarknet is unavailable or returns errors, THEN THE Scraper SHALL log the failure and retry with exponential backoff up to 3 attempts
5. WHEN a scraping job completes successfully, THE Scraper SHALL store all retrieved records in the Data_Store

### Requirement 2: Schedule Regular Data Collection

**User Story:** As a system operator, I want scraping jobs to run automatically every 6 hours, so that price data remains current without manual intervention.

#### Acceptance Criteria

1. THE Pipeline_Scheduler SHALL trigger the Scraper every 6 hours
2. WHEN a scheduled job starts, THE Pipeline_Scheduler SHALL pass the FPO location and target mandi list to the Scraper
3. IF a scraping job is still running when the next schedule triggers, THEN THE Pipeline_Scheduler SHALL skip the new execution and log a warning
4. WHEN a scraping job fails, THE Pipeline_Scheduler SHALL send an alert notification to system operators

### Requirement 3: Store Historical Price Data

**User Story:** As a data scientist, I want historical mandi prices stored in time-series format, so that I can train accurate forecasting models.

#### Acceptance Criteria

1. WHEN the Scraper retrieves new price records, THE Data_Store SHALL persist them with timestamp, mandi identifier, commodity identifier, arrival quantity, minimum price, maximum price, and modal price
2. THE Data_Store SHALL maintain at least 3 years of historical price data for model training
3. WHEN querying historical data, THE Data_Store SHALL support filtering by mandi, commodity, and date range
4. WHEN storing duplicate records with identical timestamp and mandi-commodity combination, THE Data_Store SHALL update the existing record rather than create a duplicate
5. THE Data_Store SHALL index records by timestamp, mandi identifier, and commodity identifier for efficient querying

### Requirement 4: Train Price Forecasting Model

**User Story:** As a data scientist, I want to train a LightGBM model on historical price data, so that the system can generate accurate price forecasts.

#### Acceptance Criteria

1. WHEN training is initiated, THE Price_Forecaster SHALL retrieve at least 3 years of historical data from the Data_Store
2. THE Price_Forecaster SHALL train a LightGBM model using features including commodity type, mandi location, season, day of week, arrival quantities, and lagged price values
3. WHEN training completes, THE Price_Forecaster SHALL evaluate model performance and achieve MAPE less than 15% on the validation set for 48-hour forecasts
4. WHEN model evaluation passes quality thresholds, THE Price_Forecaster SHALL deploy the trained model to the inference endpoint
5. IF model evaluation fails quality thresholds, THEN THE Price_Forecaster SHALL alert system operators and retain the previous model version

### Requirement 5: Generate Price Forecasts

**User Story:** As a farmer or FPO member, I want 48-hour price forecasts for my crops, so that I can plan optimal selling times.

#### Acceptance Criteria

1. WHEN a forecast is requested for a mandi-commodity pair, THE Price_Forecaster SHALL generate hourly price predictions for the next 48 hours
2. WHEN generating forecasts, THE Price_Forecaster SHALL include confidence intervals indicating prediction uncertainty
3. THE Price_Forecaster SHALL use the most recent historical data available when generating predictions
4. WHEN recent data is missing for a mandi-commodity pair, THE Price_Forecaster SHALL use regional average prices as fallback features
5. WHEN a forecast is generated, THE Price_Forecaster SHALL cache the result in the Price_Cache with 1-hour TTL

### Requirement 6: Cache Frequently Accessed Prices

**User Story:** As a system operator, I want frequently accessed prices cached in Redis, so that the API responds quickly and reduces database load.

#### Acceptance Criteria

1. WHEN a price query is received, THE API_Service SHALL check the Price_Cache before querying the Data_Store
2. WHEN a cache hit occurs, THE API_Service SHALL return the cached data within 100ms
3. THE Price_Cache SHALL store price data with 1-hour TTL
4. WHEN new price data is scraped and stored, THE API_Service SHALL invalidate related cache entries
5. WHEN the Price_Cache is unavailable, THE API_Service SHALL query the Data_Store directly and continue operating

### Requirement 7: Provide Price Query API

**User Story:** As a developer integrating with the platform, I want API endpoints to query current and historical prices, so that I can display market data to users.

#### Acceptance Criteria

1. WHEN a client requests current prices for a mandi and commodity, THE API_Service SHALL return the most recent price record with timestamp, minimum price, maximum price, modal price, and arrival quantity
2. WHEN a client requests historical prices with date range, THE API_Service SHALL return all matching records ordered by timestamp
3. WHEN a client requests prices for multiple commodities, THE API_Service SHALL return results grouped by commodity
4. THE API_Service SHALL validate that requested mandis are within the configured service area
5. IF a requested mandi-commodity combination has no data, THEN THE API_Service SHALL return an empty result with appropriate status code

### Requirement 8: Provide Forecast Query API

**User Story:** As a developer integrating with the platform, I want API endpoints to retrieve price forecasts, so that I can show predicted trends to users.

#### Acceptance Criteria

1. WHEN a client requests a forecast for a mandi and commodity, THE API_Service SHALL return 48-hour predictions with timestamps, predicted prices, and confidence intervals
2. WHEN a cached forecast exists and is less than 1 hour old, THE API_Service SHALL return the cached forecast
3. WHEN no cached forecast exists, THE API_Service SHALL invoke the Price_Forecaster to generate a new forecast
4. THE API_Service SHALL include forecast metadata indicating model version and generation timestamp
5. IF forecast generation fails, THEN THE API_Service SHALL return an error response with appropriate status code and message

### Requirement 9: Handle Data Quality Issues

**User Story:** As a system operator, I want the pipeline to handle missing and delayed data gracefully, so that the system remains reliable despite Agmarknet inconsistencies.

#### Acceptance Criteria

1. WHEN the Scraper encounters missing price fields, THE Scraper SHALL log the incomplete record and continue processing remaining records
2. WHEN price data is delayed by 4-12 hours, THE Scraper SHALL accept and store the data with its original timestamp
3. WHEN a mandi has no new data for more than 24 hours, THE API_Service SHALL flag the data as stale in query responses
4. WHEN training data contains gaps, THE Price_Forecaster SHALL interpolate missing values using forward fill for gaps less than 48 hours
5. WHEN arrival quantity is zero or missing, THE Price_Forecaster SHALL use historical average arrival for that mandi-commodity-season combination

### Requirement 10: Monitor Pipeline Health

**User Story:** As a system operator, I want monitoring and alerts for pipeline failures, so that I can maintain system reliability.

#### Acceptance Criteria

1. WHEN a scraping job fails after all retries, THE Scraper SHALL emit a failure metric and trigger an alert
2. WHEN forecast accuracy degrades below MAPE threshold of 20%, THE Price_Forecaster SHALL trigger a model retraining alert
3. WHEN the Data_Store query latency exceeds 500ms, THE API_Service SHALL emit a performance warning metric
4. WHEN the Price_Cache hit rate falls below 70%, THE API_Service SHALL emit a cache performance warning
5. THE Pipeline_Scheduler SHALL emit metrics for job duration, success rate, and records processed per execution
