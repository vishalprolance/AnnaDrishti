# Implementation Plan: Process Agent

## Overview

This implementation plan breaks down the Process Agent feature into discrete coding tasks that build incrementally. The Process Agent is deployed as an AWS Lambda function that detects surplus conditions, optimizes allocation between fresh market and processing using MILP, and coordinates with processors and the Sell Agent.

The implementation follows a layered approach: data models → core components → optimization → communication → integration → deployment. Each task builds on previous work, with testing integrated throughout to validate functionality early.

## Tasks

- [ ] 1. Set up project structure and data models
  - Create Lambda function directory structure with layers for OR-Tools
  - Define all data model classes (AggregatedVolume, SurplusDetection, ProcessorMatch, AllocationPlan, Contract, etc.)
  - Set up PostgreSQL schema for processors and contracts
  - Set up DynamoDB schema for allocation state
  - Configure environment variables and AWS SDK clients
  - _Requirements: 1.1, 2.1, 7.2, 20.1, 20.2, 20.5_

- [ ]* 1.1 Write unit tests for data model validation
  - Test data model serialization/deserialization
  - Test field validation and constraints
  - _Requirements: 1.1, 7.2_

- [ ] 2. Implement Volume Aggregator component
  - [ ] 2.1 Implement FPO volume aggregation logic
    - Query farmer harvest signals from database
    - Filter by FPO, crop type, and harvest readiness status
    - Sum quantities across farmers
    - Create harvest timing distribution
    - _Requirements: 1.1, 1.6_
  
  - [ ]* 2.2 Write property test for volume aggregation
    - **Property 1: Volume Aggregation Invariant**
    - **Validates: Requirements 1.1**
  
  - [ ] 2.3 Implement Redis caching for aggregated volumes
    - Cache results with 1-hour TTL
    - Implement cache invalidation on new farmer signals
    - _Requirements: 1.6_

- [ ] 3. Implement Absorption Calculator component
  - [ ] 3.1 Implement historical capacity calculation
    - Query Market Data Pipeline for mandi arrivals
    - Calculate rolling 90-day average
    - Apply seasonal adjustment factors
    - Compute safe threshold
    - _Requirements: 1.2, 1.3, 16.1, 16.2, 16.3_
  
  - [ ]* 3.2 Write property test for safe threshold calculation
    - **Property 2: Safe Threshold Calculation**
    - **Validates: Requirements 1.3**
  
  - [ ]* 3.3 Write property test for rolling average
    - **Property 35: Rolling Average Capacity**
    - **Validates: Requirements 16.2**
  
  - [ ] 3.4 Implement fallback to cached data when pipeline unavailable
    - Use cached absorption capacity with staleness warning
    - Log data source and staleness
    - _Requirements: 16.4, 16.6_

- [ ] 4. Implement Surplus Detector component
  - [ ] 4.1 Implement surplus detection logic
    - Compare aggregated volume to safe threshold
    - Calculate surplus amount and percentage
    - Assess crash risk level (low/medium/high)
    - Recommend processing diversion amount
    - _Requirements: 1.4, 1.5_
  
  - [ ]* 4.2 Write property test for surplus detection trigger
    - **Property 3: Surplus Detection Trigger**
    - **Validates: Requirements 1.4**
  
  - [ ]* 4.3 Write unit tests for crash risk assessment
    - Test low/medium/high risk thresholds
    - Test edge cases at boundaries
    - _Requirements: 1.4_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Processor Matcher component
  - [ ] 6.1 Implement processor query and filtering
    - Query processor database by crop type
    - Check available capacity from cache or database
    - Calculate distance from FPO to processor
    - Filter by minimum batch size feasibility
    - Sort by capacity, distance, and rate
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 6.2 Write property test for crop type filtering
    - **Property 4: Crop Type Filtering**
    - **Validates: Requirements 2.2**
  
  - [ ]* 6.3 Write property test for zero capacity exclusion
    - **Property 5: Zero Capacity Exclusion**
    - **Validates: Requirements 2.5**
  
  - [ ] 6.4 Implement net rate calculation with transport costs
    - Calculate transport cost based on distance and quantity
    - Compute net processing rate after transport
    - _Requirements: 11.1, 11.2_
  
  - [ ]* 6.5 Write property test for net processing price calculation
    - **Property 25: Net Processing Price Calculation**
    - **Validates: Requirements 11.2**
  
  - [ ] 6.6 Implement processor capacity caching in Redis
    - Cache capacity data with 24-hour TTL
    - _Requirements: 2.6, 18.4_
  
  - [ ]* 6.7 Write property test for capacity caching
    - **Property 41: Capacity Data Caching**
    - **Validates: Requirements 2.6, 18.4**

- [ ] 7. Implement MILP Optimizer component
  - [ ] 7.1 Set up OR-Tools MILP solver
    - Configure CP-SAT solver with 5-second timeout
    - Define decision variables for farmer-destination allocation
    - _Requirements: 3.1, 3.5_
  
  - [ ] 7.2 Implement objective function
    - Maximize total FPO revenue across all allocations
    - Include transport costs in revenue calculation
    - _Requirements: 3.2, 11.3_
  
  - [ ] 7.3 Implement MILP constraints
    - Fresh market total ≤ safe threshold
    - Processor allocations ≤ processor capacity
    - Processor allocations ≥ minimum batch size (if allocated)
    - Each farmer allocated to exactly one destination
    - Quality matching constraints
    - Farmer preference constraints
    - _Requirements: 3.3, 3.4, 9.2, 10.2, 17.4_
  
  - [ ]* 7.4 Write property test for MILP constraint satisfaction
    - **Property 6: MILP Constraint Satisfaction**
    - **Validates: Requirements 3.3, 3.4, 9.2, 17.4**
  
  - [ ]* 7.5 Write property test for minimum batch size enforcement
    - **Property 21: Minimum Batch Size Enforcement**
    - **Validates: Requirements 9.2**
  
  - [ ]* 7.6 Write property test for quality matching
    - **Property 23: Quality Matching**
    - **Validates: Requirements 10.2**
  
  - [ ] 7.4 Implement processing diversion preference
    - When multiple optimal solutions exist, prefer higher processing volume
    - _Requirements: 3.6_
  
  - [ ]* 7.8 Write property test for processing diversion preference
    - **Property 8: Processing Diversion Preference**
    - **Validates: Requirements 3.6**
  
  - [ ] 7.9 Implement fallback rule-based allocation
    - Proportional distribution when MILP fails or times out
    - _Requirements: 19.1_
  
  - [ ]* 7.10 Write property test for MILP solver fallback
    - **Property 43: MILP Solver Fallback**
    - **Validates: Requirements 19.1**
  
  - [ ]* 7.11 Write property test for optimization performance
    - **Property 7: Optimization Performance**
    - **Validates: Requirements 3.5**

- [ ] 8. Implement Revenue Calculator component
  - [ ] 8.1 Implement blended price calculation
    - Calculate weighted average price across allocations
    - Handle split allocations (fresh + processing)
    - _Requirements: 4.1_
  
  - [ ]* 8.2 Write property test for blended price calculation
    - **Property 9: Blended Price Calculation**
    - **Validates: Requirements 4.1**
  
  - [ ] 8.3 Implement revenue and benefit calculations
    - Calculate total expected revenue per farmer
    - Calculate counterfactual crash scenario revenue
    - Compute benefit vs crash scenario
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [ ]* 8.4 Write property test for revenue calculation
    - **Property 10: Revenue Calculation**
    - **Validates: Requirements 4.2**
  
  - [ ]* 8.5 Write property test for benefit calculation
    - **Property 11: Benefit Calculation**
    - **Validates: Requirements 4.4**
  
  - [ ] 8.6 Implement FPO-level metrics aggregation
    - Aggregate revenue metrics across all farmers
    - Calculate average blended price
    - Verify price protection achieved
    - _Requirements: 4.5_
  
  - [ ] 8.7 Implement currency formatting
    - Format all currency values with ₹ symbol and thousand separators
    - _Requirements: 4.6_
  
  - [ ]* 8.8 Write property test for currency formatting
    - **Property 12: Currency Formatting**
    - **Validates: Requirements 4.6**

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement Processor Communicator component
  - [ ] 10.1 Set up WhatsApp Business API client
    - Configure Gupshup or Twilio WhatsApp API
    - Implement message sending with retry logic
    - _Requirements: 5.1_
  
  - [ ] 10.2 Implement processor message generation
    - Generate structured messages in Hindi and English
    - Include all required fields: crop, quantity, quality, pickup time, location, rate
    - Format based on processor language preference
    - _Requirements: 5.2, 5.3_
  
  - [ ]* 10.3 Write property test for processor message completeness
    - **Property 13: Processor Message Completeness**
    - **Validates: Requirements 5.2, 10.4**
  
  - [ ]* 10.4 Write property test for language preference matching
    - **Property 14: Language Preference Matching**
    - **Validates: Requirements 5.3**
  
  - [ ] 10.5 Implement processor response parsing
    - Parse confirmation, decline, and counter-offer responses
    - Handle timeout after 4 hours
    - _Requirements: 5.4, 5.5_
  
  - [ ]* 10.6 Write property test for reallocation trigger on decline
    - **Property 15: Reallocation Trigger on Decline**
    - **Validates: Requirements 5.5, 12.1**
  
  - [ ] 10.7 Implement WhatsApp rate limiting
    - Respect API rate limits
    - Queue messages if rate limit exceeded
    - _Requirements: 18.6_
  
  - [ ]* 10.8 Write property test for WhatsApp rate limiting
    - **Property 42: WhatsApp Rate Limiting**
    - **Validates: Requirements 18.6**
  
  - [ ] 10.9 Implement exponential backoff retry and SMS fallback
    - Retry WhatsApp with exponential backoff (1s, 2s, 4s)
    - Fall back to SMS if WhatsApp fails
    - _Requirements: 19.3_
  
  - [ ]* 10.10 Write property test for exponential backoff retry
    - **Property 45: Exponential Backoff Retry**
    - **Validates: Requirements 19.3**

- [ ] 11. Implement Sell Agent Coordinator component
  - [ ] 11.1 Implement EventBridge event publishing
    - Publish allocation plan to Sell Agent
    - Include farmer routing instructions
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 11.2 Write property test for allocation notification
    - **Property 16: Allocation Notification**
    - **Validates: Requirements 6.2**
  
  - [ ] 11.3 Implement safe volume update
    - Calculate updated fresh market safe volume after diversion
    - Notify Sell Agent of updated safe volume
    - _Requirements: 6.5_
  
  - [ ]* 11.4 Write property test for safe volume update
    - **Property 17: Safe Volume Update**
    - **Validates: Requirements 6.5**
  
  - [ ] 11.5 Implement coordination signal for farmer confirmations
    - Notify Sell Agent when all processor confirmations received
    - _Requirements: 6.6_

- [ ] 12. Implement Contract Tracker component
  - [ ] 12.1 Implement contract creation
    - Create processing contract record in PostgreSQL
    - Store all required fields
    - _Requirements: 7.1, 7.2_
  
  - [ ]* 12.2 Write property test for contract creation on confirmation
    - **Property 18: Contract Creation on Confirmation**
    - **Validates: Requirements 7.1**
  
  - [ ]* 12.3 Write property test for contract data completeness
    - **Property 19: Contract Data Completeness**
    - **Validates: Requirements 7.2**
  
  - [ ] 12.4 Implement contract status tracking
    - Track status transitions: pending → pickup_scheduled → picked_up → payment_pending → completed
    - Support different payment terms for processing
    - _Requirements: 7.3, 7.4, 7.5_
  
  - [ ] 12.5 Implement payment tracking
    - Track payment received events
    - Alert on payment delays
    - _Requirements: 7.5_
  
  - [ ] 12.6 Implement contract report generation
    - Generate reports for FPO coordinator
    - Filter by date range and status
    - _Requirements: 7.6_

- [ ] 13. Implement reallocation logic
  - [ ] 13.1 Implement reallocation trigger
    - Detect processor decline or timeout
    - Trigger MILP re-optimization
    - _Requirements: 12.1, 12.2_
  
  - [ ]* 13.2 Write property test for reallocation exclusion
    - **Property 28: Reallocation Exclusion**
    - **Validates: Requirements 12.2**
  
  - [ ] 13.3 Implement alternative processor allocation
    - Attempt to allocate declined volume to other processors
    - Fall back to fresh market if no alternatives
    - _Requirements: 12.3, 12.4_
  
  - [ ] 13.4 Implement farmer notification on allocation change
    - Send SMS to affected farmers
    - _Requirements: 12.5_
  
  - [ ]* 13.5 Write property test for reallocation performance
    - **Property 29: Reallocation Performance**
    - **Validates: Requirements 12.6**

- [ ] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Implement multi-crop surplus handling
  - [ ] 15.1 Implement independent crop detection
    - Run surplus detection separately for each crop type
    - _Requirements: 14.1_
  
  - [ ]* 15.2 Write property test for independent crop detection
    - **Property 30: Independent Crop Detection**
    - **Validates: Requirements 14.1**
  
  - [ ] 15.3 Implement independent crop optimization
    - Run MILP optimization separately for each crop
    - _Requirements: 14.2_
  
  - [ ] 15.4 Implement processor communication coordination
    - Aggregate multiple crop offers into single message per processor
    - _Requirements: 14.3, 14.4_
  
  - [ ]* 15.5 Write property test for message aggregation
    - **Property 31: Message Aggregation for Multi-Crop**
    - **Validates: Requirements 14.4**
  
  - [ ] 15.6 Implement crash risk prioritization
    - Prioritize crops with higher crash risk for processing
    - _Requirements: 14.5_
  
  - [ ]* 15.7 Write property test for crash risk prioritization
    - **Property 32: Crash Risk Prioritization**
    - **Validates: Requirements 14.5**
  
  - [ ] 15.8 Implement multi-crop dashboard data
    - Provide FPO coordinator with multi-crop surplus status
    - _Requirements: 14.6_

- [ ] 16. Implement farmer preference support
  - [ ] 16.1 Implement preference storage and retrieval
    - Store farmer processing preferences in database
    - Support: "accept processing", "fresh market only", "processing only if premium"
    - _Requirements: 17.1_
  
  - [ ] 16.2 Implement preference-based filtering
    - Exclude "fresh market only" farmers from processing allocation
    - Apply conditional logic for "processing only if premium"
    - _Requirements: 17.2, 17.3_
  
  - [ ]* 16.3 Write property test for farmer preference respect
    - **Property 37: Farmer Preference Respect**
    - **Validates: Requirements 17.2**
  
  - [ ]* 16.4 Write property test for premium-only conditional allocation
    - **Property 38: Premium-Only Conditional Allocation**
    - **Validates: Requirements 17.3**
  
  - [ ] 16.5 Implement preference update via IVR/WhatsApp
    - Allow farmers to update preferences at any time
    - _Requirements: 17.6_
  
  - [ ] 16.6 Implement alert on insufficient diversion due to opt-outs
    - Alert FPO coordinator when opt-outs reduce effectiveness
    - _Requirements: 17.5_

- [ ] 17. Implement price protection validation
  - [ ] 17.1 Implement price calculation with and without diversion
    - Calculate expected fresh market price with processing diversion
    - Calculate crash scenario price without diversion
    - _Requirements: 8.1, 8.2_
  
  - [ ] 17.2 Implement price protection validation
    - Verify fresh market price within 10% of forecasted stable price
    - _Requirements: 8.3_
  
  - [ ]* 17.3 Write property test for price protection validation
    - **Property 20: Price Protection Validation**
    - **Validates: Requirements 8.3**
  
  - [ ] 17.4 Implement alert on insufficient price protection
    - Alert FPO coordinator when diversion insufficient
    - _Requirements: 8.4_
  
  - [ ] 17.5 Implement price protection metrics logging
    - Log pre/post diversion supply and prices
    - _Requirements: 8.5_
  
  - [ ] 17.6 Implement actual vs predicted price tracking
    - Track actual post-transaction prices
    - Compare to predictions for model improvement
    - _Requirements: 8.6_

- [ ] 18. Implement audit logging
  - [ ] 18.1 Implement comprehensive audit logger
    - Log all surplus detection events
    - Log all MILP optimization runs
    - Log all processor communications
    - Log all allocation changes
    - Include timestamps and full context
    - _Requirements: 5.6, 9.6, 10.5, 15.1, 15.2, 15.3, 15.4, 16.6, 19.5_
  
  - [ ]* 18.2 Write property test for comprehensive audit logging
    - **Property 33: Comprehensive Audit Logging**
    - **Validates: Requirements 5.6, 9.6, 10.5, 15.1, 15.2, 15.3, 15.4, 16.6, 19.5**
  
  - [ ] 18.3 Implement audit log retention policy
    - Configure CloudWatch Logs retention for 7 years
    - _Requirements: 15.6_
  
  - [ ]* 18.4 Write property test for audit log retention
    - **Property 34: Audit Log Retention**
    - **Validates: Requirements 15.6**
  
  - [ ] 18.5 Implement audit trail query interface
    - Provide query API for FPO coordinators
    - Filter by date range, crop, farmer, event type
    - _Requirements: 15.5_

- [ ] 19. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Implement performance optimizations
  - [ ] 20.1 Implement concurrent FPO processing
    - Support multiple FPOs triggering surplus detection simultaneously
    - Use async processing where possible
    - _Requirements: 18.3_
  
  - [ ]* 20.2 Write property test for concurrent FPO processing
    - **Property 40: Concurrent FPO Processing**
    - **Validates: Requirements 18.3**
  
  - [ ] 20.3 Optimize database queries with connection pooling
    - Configure connection pool size
    - Implement connection reuse
    - _Requirements: 18.5_
  
  - [ ] 20.4 Implement performance monitoring
    - Track surplus detection time
    - Track MILP optimization time
    - Track reallocation time
    - Alert on performance degradation
    - _Requirements: 18.1, 18.2_
  
  - [ ]* 20.5 Write property test for surplus detection performance
    - **Property 39: Surplus Detection Performance**
    - **Validates: Requirements 18.1**

- [ ] 21. Implement error handling and graceful degradation
  - [ ] 21.1 Implement circuit breaker for external services
    - Circuit breaker for processor database
    - Circuit breaker for Market Data Pipeline
    - Circuit breaker for WhatsApp API
    - _Requirements: 19.6_
  
  - [ ] 21.2 Implement graceful degradation on service failures
    - Use cached data when services unavailable
    - Route to fresh market when processor database unavailable
    - _Requirements: 19.2, 19.4_
  
  - [ ]* 21.3 Write property test for graceful degradation
    - **Property 44: Graceful Degradation on Service Failure**
    - **Validates: Requirements 19.2, 19.4**
  
  - [ ] 21.4 Implement comprehensive error logging
    - Log all errors with full context
    - Include stack traces for debugging
    - _Requirements: 19.5_

- [ ] 22. Implement Lambda deployment configuration
  - [ ] 22.1 Create Lambda deployment package
    - Package Python code with dependencies
    - Create OR-Tools Lambda Layer
    - Configure Lambda function with 3GB memory and 15-minute timeout
    - _Requirements: 20.1, 20.2, 20.4_
  
  - [ ]* 22.2 Write property test for Lambda execution timeout
    - **Property 46: Lambda Execution Timeout**
    - **Validates: Requirements 20.4**
  
  - [ ] 22.3 Configure EventBridge triggers
    - Set up trigger from Sell Agent events
    - Set up scheduled trigger for periodic surplus check
    - _Requirements: 20.3_
  
  - [ ] 22.4 Configure VPC and security
    - Attach Lambda to VPC for RDS access
    - Configure security groups
    - Set up IAM roles and permissions
    - _Requirements: 20.1_
  
  - [ ] 22.5 Configure environment variables
    - Database connection strings
    - API keys (WhatsApp, Market Data Pipeline)
    - Configuration thresholds (safe threshold percentage, timeout values)
    - _Requirements: 20.5_
  
  - [ ] 22.6 Set up CloudWatch monitoring
    - Configure CloudWatch Logs
    - Set up CloudWatch metrics and alarms
    - _Requirements: 20.6_

- [ ] 23. Integration testing and end-to-end validation
  - [ ]* 23.1 Write integration tests for EventBridge integration
    - Test event publishing to Sell Agent
    - Test event consumption from Sell Agent
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 23.2 Write integration tests for WhatsApp communication
    - Test message sending to processors
    - Test response parsing
    - _Requirements: 5.1, 5.4_
  
  - [ ]* 23.3 Write integration tests for database operations
    - Test processor query and capacity updates
    - Test contract creation and tracking
    - _Requirements: 2.1, 7.1_
  
  - [ ]* 23.4 Write integration tests for Market Data Pipeline
    - Test absorption capacity query
    - Test fallback to cached data
    - _Requirements: 16.1, 16.4_
  
  - [ ] 23.5 Write end-to-end test for complete workflow
    - Test full flow: surplus detection → optimization → processor communication → confirmation → contract creation
    - _Requirements: All requirements_

- [ ] 24. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate external service interactions
- The implementation uses Python 3.11 as specified in the design
- OR-Tools MILP solver is packaged as a Lambda Layer for deployment
- All processor communication uses WhatsApp Business API with SMS fallback
- The system is designed to complete surplus detection and allocation within 15 seconds
