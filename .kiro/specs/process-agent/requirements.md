# Requirements Document

## Introduction

The Process Agent is the core differentiator of Anna Drishti - an AI-powered system that prevents market crashes by detecting surplus conditions at the FPO level and orchestrating diversion of excess produce to processing facilities before prices collapse. When the combined harvest volume from an FPO exceeds what nearby mandis can absorb at stable prices, the Process Agent calculates the optimal split between fresh market and processing, matches surplus with pre-onboarded micro-processing partners, and coordinates the diversion to maintain stable fresh market prices for all farmers.

The system operates as part of the Anna Drishti platform, integrating with the Sell Agent to provide a comprehensive selling and surplus management solution. It uses Mixed Integer Linear Programming (MILP) optimization to maximize total FPO revenue while preventing fresh market crashes, and communicates with processors via WhatsApp Business API.

## Glossary

- **FPO**: Farmer Producer Organization - a collective of farmers registered as a legal entity
- **Process_Agent**: The AI system that detects surplus and orchestrates processing diversion
- **Processor**: A micro-food-processing unit that converts surplus produce into value-added products (paste, dried, powder)
- **Surplus**: When FPO combined harvest volume exceeds historical mandi absorption capacity at stable prices
- **Mandi**: Agricultural wholesale market where farmers sell produce
- **Absorption_Capacity**: Historical volume that a mandi can handle without significant price drops
- **MILP_Solver**: Mixed Integer Linear Programming optimization engine (OR-Tools) for allocation decisions
- **Blended_Price**: Weighted average price across fresh market and processing sales
- **Sell_Agent**: The companion AI system that handles individual farmer selling workflows
- **Crash_Price**: Significant price drop (typically 30-40%) when supply exceeds demand
- **Processing_Contract**: Pre-negotiated agreement with processor specifying rates, capacity, and quality requirements
- **Diversion**: Routing produce to processing instead of fresh market to prevent oversupply

## Requirements

### Requirement 1: Surplus Detection at FPO Level

**User Story:** As an FPO coordinator, I want the system to detect when our combined harvest volume will exceed safe mandi capacity, so that we can prevent price crashes before they happen.

#### Acceptance Criteria

1. WHEN farmers signal harvest readiness via IVR or WhatsApp, THE Process_Agent SHALL aggregate reported volumes by crop type at the FPO level
2. WHEN aggregated volume is calculated, THE Process_Agent SHALL query historical mandi absorption capacity for the target mandis
3. THE Process_Agent SHALL calculate a safe threshold as a configurable percentage of historical absorption capacity (default 80%)
4. WHEN aggregated FPO volume exceeds the safe threshold, THE Process_Agent SHALL trigger a surplus alert
5. THE Process_Agent SHALL include in the surplus alert: crop type, total FPO volume, historical absorption capacity, and percentage over threshold
6. THE Process_Agent SHALL update surplus detection calculations as new farmers signal harvest readiness

### Requirement 2: Processor Capacity Query

**User Story:** As a system component, I want to query available processing capacity from pre-onboarded partners, so that I can determine how much surplus can be diverted.

#### Acceptance Criteria

1. THE Process_Agent SHALL maintain a database of pre-onboarded processors with capacity, processing types, and contract rates
2. WHEN surplus is detected, THE Process_Agent SHALL query processors filtered by crop type compatibility
3. THE Process_Agent SHALL retrieve for each processor: available weekly capacity, processing type, contract rate range, quality requirements, and location
4. THE Process_Agent SHALL calculate distance from FPO location to each processor facility
5. WHEN a processor has zero available capacity, THE Process_Agent SHALL exclude that processor from allocation consideration
6. THE Process_Agent SHALL cache processor capacity data with a time-to-live of 24 hours

### Requirement 3: Optimal Allocation Using MILP

**User Story:** As an optimization system, I want to calculate the optimal split between fresh market and processing, so that total FPO revenue is maximized while preventing fresh market crashes.

#### Acceptance Criteria

1. THE Process_Agent SHALL use OR-Tools MILP solver to calculate optimal allocation
2. THE Process_Agent SHALL define the objective function as: maximize total FPO revenue across all farmers
3. THE Process_Agent SHALL enforce constraints: processor capacity limits, minimum batch sizes, quality requirements, and transport feasibility
4. THE Process_Agent SHALL ensure fresh market allocation does not exceed safe mandi absorption threshold
5. THE Process_Agent SHALL complete optimization calculation within 5 seconds for up to 50 farmers
6. WHEN multiple optimal solutions exist, THE Process_Agent SHALL prefer solutions that maximize processing diversion (to provide maximum price protection)
7. THE Process_Agent SHALL output allocation plan specifying: farmers assigned to fresh market, farmers assigned to each processor, quantities for each allocation, and expected prices

### Requirement 4: Revenue Blending Calculation

**User Story:** As a farmer, I want to see the blended price that accounts for both fresh market and processing sales, so that I understand the benefit of the coordinated approach.

#### Acceptance Criteria

1. WHEN allocation is determined, THE Process_Agent SHALL calculate blended price for each farmer as: (fresh_quantity × fresh_price + processing_quantity × processing_price) / total_quantity
2. THE Process_Agent SHALL calculate total expected revenue for each farmer based on their allocation
3. THE Process_Agent SHALL calculate the counterfactual scenario: expected revenue if all FPO volume went to fresh market at crash price
4. THE Process_Agent SHALL compute the benefit amount as: blended_revenue - crash_scenario_revenue
5. THE Process_Agent SHALL present to each farmer: blended price per kg, total expected revenue, breakdown by fresh vs processing, and benefit compared to crash scenario
6. THE Process_Agent SHALL format all currency values in Indian Rupees with appropriate thousand separators

### Requirement 5: Processor Communication via WhatsApp

**User Story:** As a processor partner, I want to receive volume offers via WhatsApp with all necessary details, so that I can quickly confirm or decline capacity.

#### Acceptance Criteria

1. WHEN allocation plan is finalized, THE Process_Agent SHALL send WhatsApp messages to assigned processors
2. THE Process_Agent SHALL include in each message: crop type, total quantity offered, quality indicators, pickup timeframe, FPO location, and contract rate
3. THE Process_Agent SHALL format messages in the processor's preferred language (Hindi or English based on processor profile)
4. WHEN a processor responds with confirmation, THE Process_Agent SHALL parse the response and mark allocation as confirmed
5. WHEN a processor declines or does not respond within 4 hours, THE Process_Agent SHALL trigger reallocation to find alternative processors or adjust fresh market allocation
6. THE Process_Agent SHALL log all processor communications to the audit trail with timestamps

### Requirement 6: Coordination with Sell Agent

**User Story:** As a system integrator, I want the Process Agent to coordinate with the Sell Agent, so that farmers receive integrated workflow guidance for both fresh and processing sales.

#### Acceptance Criteria

1. WHEN the Sell Agent detects potential surplus during market scanning, THE Sell_Agent SHALL trigger the Process_Agent for surplus analysis
2. WHEN the Process Agent completes allocation, THE Process_Agent SHALL notify the Sell_Agent with allocation assignments for each farmer
3. THE Sell_Agent SHALL route farmers assigned to fresh market through the standard buyer outreach and negotiation workflow
4. THE Sell_Agent SHALL route farmers assigned to processing through the processor confirmation and pickup coordination workflow
5. THE Process_Agent SHALL provide the Sell_Agent with updated fresh market safe volume after processing diversion
6. WHEN all allocations are confirmed, THE Process_Agent SHALL update the Sell_Agent to proceed with farmer confirmations

### Requirement 7: Processing Contract Tracking

**User Story:** As an FPO coordinator, I want processing contracts tracked separately from fresh market sales, so that I can manage different payment terms and pickup schedules.

#### Acceptance Criteria

1. WHEN a farmer confirms processing allocation, THE Process_Agent SHALL create a processing contract record
2. THE Process_Agent SHALL store in the contract: farmer ID, processor ID, crop type, quantity, agreed rate, pickup time, expected payment time, and payment terms
3. THE Process_Agent SHALL track processing contracts separately from fresh market transactions in the database
4. THE Process_Agent SHALL support different payment terms for processing (typically 7-15 days) versus fresh market (same day)
5. WHEN pickup is completed, THE Process_Agent SHALL update contract status and trigger payment tracking
6. THE Process_Agent SHALL generate processing contract reports for FPO coordinator review

### Requirement 8: Crash Prevention Validation

**User Story:** As a system validator, I want to verify that processing diversion maintains fresh market prices within acceptable ranges, so that the core value proposition is delivered.

#### Acceptance Criteria

1. THE Process_Agent SHALL calculate expected fresh market price with processing diversion
2. THE Process_Agent SHALL calculate expected fresh market price without processing diversion (crash scenario)
3. THE Process_Agent SHALL ensure fresh market price with diversion is within 10% of the forecasted stable price
4. WHEN processing diversion is insufficient to prevent crash, THE Process_Agent SHALL alert the FPO coordinator with recommendations
5. THE Process_Agent SHALL log price protection metrics: pre-diversion supply, post-diversion supply, expected price with diversion, expected price without diversion
6. THE Process_Agent SHALL track actual post-transaction prices and compare to predictions for model improvement

### Requirement 9: Minimum Batch Size Enforcement

**User Story:** As a processor partner, I want the system to respect my minimum batch size requirements, so that I receive economically viable volumes.

#### Acceptance Criteria

1. THE Process_Agent SHALL retrieve minimum batch size from each processor's profile
2. THE Process_Agent SHALL enforce in MILP constraints that any allocation to a processor meets or exceeds minimum batch size
3. WHEN total available surplus is less than any processor's minimum batch size, THE Process_Agent SHALL not allocate to that processor
4. THE Process_Agent SHALL prefer aggregating multiple farmers to meet minimum batch sizes over splitting small quantities
5. WHEN no processor can accept the available surplus due to batch size constraints, THE Process_Agent SHALL route all volume to fresh market with expanded mandi targeting
6. THE Process_Agent SHALL log batch size constraint violations for processor relationship management

### Requirement 10: Quality Requirements Matching

**User Story:** As a processor partner, I want to receive produce that meets my quality standards, so that I can maintain processing output quality.

#### Acceptance Criteria

1. THE Process_Agent SHALL store quality requirements for each processor (grade, size, ripeness, defect tolerance)
2. WHEN allocating farmers to processors, THE Process_Agent SHALL match farmer produce quality indicators to processor requirements
3. THE Process_Agent SHALL exclude farmers from processor allocation when quality indicators do not meet processor standards
4. THE Process_Agent SHALL include quality indicators in WhatsApp messages to processors for verification
5. WHEN processor rejects produce at pickup due to quality issues, THE Process_Agent SHALL log the rejection and update farmer quality profile
6. THE Process_Agent SHALL provide quality matching transparency: show farmers which processors they qualify for based on quality

### Requirement 11: Transport Cost Optimization

**User Story:** As an FPO coordinator, I want transport costs to processing facilities factored into allocation decisions, so that net farmer revenue is maximized.

#### Acceptance Criteria

1. THE Process_Agent SHALL calculate transport cost from FPO location to each processor facility
2. THE Process_Agent SHALL compute net processing price as: contract_rate - (transport_cost / quantity)
3. THE Process_Agent SHALL include transport costs in the MILP objective function
4. WHEN transport cost makes processing unprofitable compared to fresh market, THE Process_Agent SHALL not allocate to that processor
5. THE Process_Agent SHALL support shared transport when multiple farmers are allocated to the same processor
6. THE Process_Agent SHALL present transport cost breakdown to farmers in the allocation explanation

### Requirement 12: Reallocation on Processor Decline

**User Story:** As a system operator, I want automatic reallocation when a processor declines capacity, so that surplus diversion continues without manual intervention.

#### Acceptance Criteria

1. WHEN a processor declines an allocation within 4 hours, THE Process_Agent SHALL trigger reallocation
2. THE Process_Agent SHALL re-run MILP optimization excluding the declined processor
3. THE Process_Agent SHALL attempt to allocate declined volume to alternative processors with available capacity
4. WHEN no alternative processors are available, THE Process_Agent SHALL increase fresh market allocation and recalculate safe volume thresholds
5. THE Process_Agent SHALL notify affected farmers of allocation changes via SMS
6. THE Process_Agent SHALL complete reallocation within 2 minutes to maintain workflow momentum

### Requirement 13: Seasonal Processing Capacity Planning

**User Story:** As an FPO coordinator, I want visibility into processor capacity across the season, so that I can plan harvest timing and processor partnerships.

#### Acceptance Criteria

1. THE Process_Agent SHALL maintain a seasonal capacity calendar for each processor
2. THE Process_Agent SHALL allow processors to update their available capacity by week via WhatsApp or web interface
3. THE Process_Agent SHALL provide FPO coordinators with a dashboard showing: processor capacity by week, historical utilization, and projected FPO harvest volume
4. WHEN processor capacity is consistently insufficient, THE Process_Agent SHALL alert the FPO coordinator to onboard additional processors
5. THE Process_Agent SHALL support capacity reservations: processors can reserve capacity for specific FPOs in advance
6. THE Process_Agent SHALL track capacity utilization metrics for processor relationship management

### Requirement 14: Multi-Crop Surplus Handling

**User Story:** As an FPO with diverse crops, I want the system to handle surplus detection and processing allocation across multiple crop types simultaneously, so that all farmers benefit from coordinated surplus management.

#### Acceptance Criteria

1. THE Process_Agent SHALL detect surplus independently for each crop type
2. THE Process_Agent SHALL run MILP optimization separately for each crop with surplus
3. THE Process_Agent SHALL coordinate processor communications across multiple crops to avoid overwhelming processor partners
4. WHEN a processor handles multiple crop types, THE Process_Agent SHALL aggregate communications into a single message
5. THE Process_Agent SHALL prioritize crops with highest crash risk (largest percentage over safe threshold) for processing allocation
6. THE Process_Agent SHALL provide FPO coordinators with a multi-crop surplus dashboard showing status across all active crops

### Requirement 15: Audit Trail and Transparency

**User Story:** As an FPO coordinator, I want complete audit trails of all allocation decisions and processor communications, so that I can verify system actions and resolve disputes.

#### Acceptance Criteria

1. THE Process_Agent SHALL log all surplus detection events with: timestamp, crop, FPO volume, safe threshold, and surplus percentage
2. THE Process_Agent SHALL log all MILP optimization runs with: input parameters, constraints, objective function value, and solution
3. THE Process_Agent SHALL log all processor communications with: message content, timestamp, processor response, and response time
4. THE Process_Agent SHALL log all allocation changes with: reason for change, affected farmers, and new allocation
5. THE Process_Agent SHALL provide audit trail query interface for FPO coordinators filtered by date range, crop, and farmer
6. THE Process_Agent SHALL retain audit logs for at least 7 years for compliance and dispute resolution

### Requirement 16: Integration with Market Data Pipeline

**User Story:** As a system component, I want to use historical mandi absorption data from the Market Data Pipeline, so that surplus detection is based on accurate market capacity estimates.

#### Acceptance Criteria

1. THE Process_Agent SHALL query the Market Data Pipeline for historical mandi absorption capacity by crop and mandi
2. THE Process_Agent SHALL use a rolling 90-day average of mandi arrivals as the baseline absorption capacity
3. THE Process_Agent SHALL adjust absorption capacity based on seasonal patterns (festival demand, weather events)
4. WHEN Market Data Pipeline data is unavailable, THE Process_Agent SHALL use cached data with staleness warning
5. THE Process_Agent SHALL update absorption capacity estimates weekly based on latest market data
6. THE Process_Agent SHALL log data source and staleness for all absorption capacity calculations

### Requirement 17: Farmer Opt-Out Support

**User Story:** As a farmer, I want the ability to opt out of processing allocation if I prefer to sell only to fresh market, so that I maintain control over my selling decisions.

#### Acceptance Criteria

1. THE Process_Agent SHALL allow farmers to set processing preferences in their profile: "accept processing", "fresh market only", or "processing only if premium"
2. WHEN a farmer has "fresh market only" preference, THE Process_Agent SHALL exclude that farmer from processing allocation
3. WHEN a farmer has "processing only if premium" preference, THE Process_Agent SHALL only allocate to processing if processing rate exceeds fresh market net price
4. THE Process_Agent SHALL respect farmer preferences in MILP constraints
5. WHEN farmer opt-outs reduce processing diversion below effective threshold, THE Process_Agent SHALL alert FPO coordinator
6. THE Process_Agent SHALL allow farmers to update preferences via IVR or WhatsApp at any time

### Requirement 18: Performance and Scalability

**User Story:** As a system administrator, I want the Process Agent to scale efficiently, so that it can handle multiple FPOs with hundreds of farmers each.

#### Acceptance Criteria

1. THE Process_Agent SHALL complete surplus detection for 500 farmers within 10 seconds
2. THE Process_Agent SHALL complete MILP optimization for 50 farmers and 5 processors within 5 seconds
3. THE Process_Agent SHALL support concurrent processing of surplus detection for multiple FPOs
4. THE Process_Agent SHALL cache processor capacity data to reduce database queries
5. THE Process_Agent SHALL use connection pooling for database access with configurable pool size
6. THE Process_Agent SHALL implement rate limiting for WhatsApp API calls to avoid exceeding quotas

### Requirement 19: Error Handling and Graceful Degradation

**User Story:** As a system operator, I want robust error handling, so that the system continues to function even when components fail.

#### Acceptance Criteria

1. WHEN MILP solver fails to find a solution within timeout, THE Process_Agent SHALL fall back to rule-based allocation (proportional distribution)
2. WHEN processor database is unavailable, THE Process_Agent SHALL route all volume to fresh market and alert FPO coordinator
3. WHEN WhatsApp API fails, THE Process_Agent SHALL retry with exponential backoff and fall back to SMS if WhatsApp remains unavailable
4. WHEN Market Data Pipeline is unavailable, THE Process_Agent SHALL use cached absorption capacity with staleness warning
5. THE Process_Agent SHALL log all errors with full context for debugging
6. THE Process_Agent SHALL implement circuit breaker pattern for external service calls

### Requirement 20: Deployment on AWS Lambda

**User Story:** As a DevOps engineer, I want the Process Agent deployed on AWS Lambda with OR-Tools layer, so that it scales automatically and minimizes infrastructure costs.

#### Acceptance Criteria

1. THE Process_Agent SHALL be packaged as an AWS Lambda function with Python 3.11 runtime
2. THE Process_Agent SHALL use a Lambda Layer containing OR-Tools and dependencies
3. THE Process_Agent SHALL be triggered by events from the Sell Agent via EventBridge
4. THE Process_Agent SHALL complete execution within Lambda timeout limits (15 minutes maximum)
5. THE Process_Agent SHALL use environment variables for configuration (database connection, API keys, thresholds)
6. THE Process_Agent SHALL integrate with CloudWatch for logging and monitoring
