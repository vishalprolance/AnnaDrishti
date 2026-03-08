# Implementation Plan: Collective Selling & Allocation

## Overview

This implementation plan breaks down the Collective Selling & Allocation feature into discrete coding tasks. The system transforms Anna Drishti from individual farmer optimization to FPO-level collective operations with priority-based allocation across societies, processing partners, and mandis. The implementation uses Python with AWS Lambda, PostgreSQL for relational data, DynamoDB for real-time inventory, and React for the dashboard.

The tasks are organized to build incrementally: data models and storage first, then inventory aggregation, demand prediction, allocation engine, and finally dashboard visualization.

## Tasks

- [x] 1. Set up project structure and data models
  - Create Python project structure with modules: inventory/, allocation/, society/, processing/
  - Set up requirements.txt with dependencies: boto3, psycopg2, hypothesis, pytest, fastapi
  - Create shared data models module for all entities
  - Configure AWS SAM or Serverless Framework for Lambda deployment
  - _Requirements: All requirements (foundation)_

- [x] 2. Implement database schema
  - [x] 2.1 Create PostgreSQL schema for relational data
    - Define tables: societies, processing_partners, demand_predictions, allocations
    - Define foreign key relationships and indexes
    - Create migration scripts
    - _Requirements: 2.1, 5.1_
  
  - [x] 2.2 Create DynamoDB schema for real-time inventory
    - Define table: collective_inventory with partition key (fpo_id, crop_type)
    - Define table: farmer_contributions with GSI for farmer_id
    - Define table: reservations with GSI for society_id and delivery_date
    - Configure TTL for historical data
    - _Requirements: 1.1, 1.2, 3.3_
  
  - [x] 2.3 Create database access layer
    - Implement InventoryRepository with CRUD operations
    - Implement SocietyRepository with CRUD operations
    - Implement AllocationRepository with CRUD operations
    - Add connection pooling and error handling
    - _Requirements: All requirements_

- [-] 3. Implement collective inventory management
  - [x] 3.1 Create FarmerContribution data model
    - Define FarmerContribution class with validation
    - Implement serialization/deserialization methods
    - Add quality grade validation (A, B, C)
    - _Requirements: 1.2_
  
  - [x] 3.2 Implement inventory aggregation logic
    - Create aggregate_farmer_contribution() function
    - Use DynamoDB atomic counters for real-time updates
    - Maintain contribution list in DynamoDB
    - Update total_quantity, available_quantity
    - _Requirements: 1.1, 1.3_
  
  - [x] 3.3 Write property test for contribution aggregation
    - **Property 2: Contribution Aggregation**
    - **Validates: Requirements 1.1**
  
  - [x] 3.4 Implement inventory query API
    - Create GET /api/inventory/{fpo_id}/{crop_type} endpoint
    - Return aggregate totals and per-farmer breakdowns
    - Add filtering by date range
    - _Requirements: 1.4_
  
  - [x] 3.5 Write property test for inventory conservation
    - **Property 1: Inventory Conservation**
    - **Validates: Requirements 1.1, 1.3**
  
  - [x] 3.6 Write unit tests for inventory aggregation
    - Test contribution validation
    - Test concurrent updates
    - Test error handling
    - _Requirements: 1.5_

- [-] 4. Implement society management
  - [x] 4.1 Create SocietyProfile data model
    - Define SocietyProfile class with validation
    - Validate delivery frequency enum
    - Validate contact details format
    - _Requirements: 2.1, 2.5_
  
  - [x] 4.2 Implement society registration API
    - Create POST /api/societies endpoint
    - Validate input data
    - Generate unique society_id
    - Store in PostgreSQL
    - _Requirements: 2.1, 2.6_
  
  - [x] 4.3 Implement society profile management API
    - Create GET /api/societies/{society_id} endpoint
    - Create PUT /api/societies/{society_id} endpoint
    - Create DELETE /api/societies/{society_id} endpoint
    - _Requirements: 2.2, 2.3, 2.4_
  
  - [x] 4.4 Write unit tests for society management
    - Test registration validation
    - Test profile updates
    - Test delivery frequency validation
    - _Requirements: 2.5_

- [-] 5. Implement demand prediction engine
  - [x] 5.1 Create DemandPrediction data model
    - Define DemandPrediction class with validation
    - Validate confidence score bounds (0.0 to 1.0)
    - Validate predicted quantity is non-negative
    - _Requirements: 3.1_
  
  - [x] 5.2 Implement historical order tracking
    - Create order_history table in PostgreSQL
    - Implement query_historical_orders() function
    - Add 90-day lookback window
    - _Requirements: 3.1_
  
  - [x] 5.3 Implement demand prediction algorithm
    - Create predict_society_demand() function
    - Implement exponential weighted moving average
    - Calculate confidence based on consistency
    - Handle insufficient data case
    - _Requirements: 3.1_
  
  - [x] 5.4 Write property test for demand prediction bounds
    - **Property 8: Demand Prediction Bounds**
    - **Validates: Requirements 3.1**
  
  - [x] 5.5 Implement reservation system
    - Create reserve_inventory() function
    - Mark reserved quantity as unavailable
    - Store reservation in DynamoDB
    - Handle insufficient inventory case
    - _Requirements: 3.2, 3.3, 3.4_
  
  - [x] 5.6 Implement reservation confirmation
    - Create confirm_reservation() function
    - Replace predicted reservation with confirmed order
    - Update reservation status
    - _Requirements: 3.5_
  
  - [x] 5.7 Write unit tests for demand prediction
    - Test EWMA calculation
    - Test confidence calculation
    - Test insufficient data handling
    - Test reservation logic
    - _Requirements: 3.6_

- [x] 6. Checkpoint - Ensure core data models work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement processing partner management
  - [x] 7.1 Create ProcessingPartner data model
    - Define ProcessingPartner class with validation
    - Validate rates are positive
    - Validate capacity limits are non-negative
    - _Requirements: 5.1, 5.5_
  
  - [x] 7.2 Implement partner registration API
    - Create POST /api/processing-partners endpoint
    - Validate input data
    - Generate unique partner_id
    - Store in PostgreSQL
    - _Requirements: 5.1, 5.6_
  
  - [x] 7.3 Implement partner management API
    - Create GET /api/processing-partners/{partner_id} endpoint
    - Create PUT /api/processing-partners/{partner_id} endpoint
    - Create DELETE /api/processing-partners/{partner_id} endpoint
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [x] 7.4 Write unit tests for partner management
    - Test registration validation
    - Test rate and capacity validation
    - Test partner updates
    - _Requirements: 5.5_

- [x] 8. Implement priority-based allocation engine
  - [x] 8.1 Create Allocation and ChannelAllocation data models
    - Define Allocation class with validation
    - Define ChannelAllocation class with validation
    - Validate priority values (1, 2, 3)
    - _Requirements: 4.1_
  
  - [x] 8.2 Implement Priority 1: Society allocation
    - Query active reservations for allocation date
    - Sort reservations by timestamp
    - Allocate to societies in timestamp order
    - Flag unfulfilled reservations if insufficient inventory
    - _Requirements: 4.1, 4.7_
  
  - [x] 8.3 Write property test for reservation fulfillment
    - **Property 4: Reservation Fulfillment**
    - **Validates: Requirements 4.1, 4.7**
  
  - [x] 8.4 Write property test for reservation timestamp ordering
    - **Property 10: Reservation Timestamp Ordering**
    - **Validates: Requirements 4.1**
  
  - [x] 8.5 Implement Priority 2: Processing partner allocation
    - Query processing partners for crop type
    - Sort partners by rate (highest first)
    - Allocate up to partner capacity
    - Respect quality requirements
    - _Requirements: 4.2, 4.5_
  
  - [x] 8.6 Write property test for processing capacity constraint
    - **Property 9: Processing Capacity Constraint**
    - **Validates: Requirements 4.2, 4.5**
  
  - [x] 8.7 Implement Priority 3: Mandi allocation
    - Query best mandi price for crop type
    - Allocate remaining inventory to mandi
    - _Requirements: 4.3_
  
  - [x] 8.8 Implement allocation orchestration
    - Create allocate_inventory() function
    - Execute Priority 1, 2, 3 in sequence
    - Calculate blended realization
    - Update inventory allocated_quantity
    - Store allocation in PostgreSQL
    - _Requirements: 4.1, 4.2, 4.3, 4.6_
  
  - [x] 8.9 Write property test for priority ordering
    - **Property 3: Priority Ordering**
    - **Validates: Requirements 4.1, 4.2, 4.3**
  
  - [x] 8.10 Write property test for no over-allocation
    - **Property 5: No Over-Allocation**
    - **Validates: Requirements 4.1**
  
  - [x] 8.11 Write unit tests for allocation engine
    - Test allocation with sufficient inventory
    - Test allocation with insufficient inventory
    - Test allocation with no reservations
    - Test allocation with no processing partners
    - _Requirements: 4.7_

- [x] 9. Implement blended realization calculation
  - [x] 9.1 Implement blended realization formula
    - Calculate total revenue across all channels
    - Calculate total quantity across all channels
    - Compute blended_realization = total_revenue / total_quantity
    - _Requirements: 6.1_
  
  - [x] 9.2 Write property test for blended realization accuracy
    - **Property 6: Blended Realization Accuracy**
    - **Validates: Requirements 6.1**
  
  - [x] 9.3 Implement farmer income calculation
    - Create calculate_farmer_income() function
    - Calculate farmer's share of total revenue
    - Generate channel-wise breakdown
    - Compare to best single-channel price
    - _Requirements: 6.2, 6.3, 6.4_
  
  - [x] 9.4 Write property test for farmer income conservation
    - **Property 7: Farmer Income Conservation**
    - **Validates: Requirements 6.2**
  
  - [x] 9.5 Implement realization reporting API
    - Create GET /api/allocations/{allocation_id}/realization endpoint
    - Return blended realization and channel breakdown
    - Return per-farmer income details
    - _Requirements: 6.3, 6.5_
  
  - [x] 9.6 Write unit tests for realization calculation
    - Test blended realization with multiple channels
    - Test farmer income with multiple farmers
    - Test channel breakdown accuracy
    - Test comparison to single-channel
    - _Requirements: 6.6_

- [x] 10. Checkpoint - Ensure allocation engine works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement allocation execution and tracking
  - [x] 11.1 Implement delivery order generation
    - Create generate_delivery_orders() function
    - Generate orders for each society allocation
    - Include delivery details and schedule
    - Store orders in PostgreSQL
    - _Requirements: 7.1_
  
  - [x] 11.2 Implement pickup order generation
    - Create generate_pickup_orders() function
    - Generate orders for each processing partner allocation
    - Include pickup schedule and location
    - Store orders in PostgreSQL
    - _Requirements: 7.2_
  
  - [x] 11.3 Implement mandi dispatch order generation
    - Create generate_dispatch_orders() function
    - Generate orders for mandi allocations
    - Include destination and transport details
    - Store orders in PostgreSQL
    - _Requirements: 7.3_
  
  - [x] 11.4 Implement fulfillment tracking
    - Create update_fulfillment_status() function
    - Track status transitions (pending → in_transit → delivered → completed)
    - Update inventory on fulfillment
    - Prevent double-allocation
    - _Requirements: 7.4, 7.5, 7.6_
  
  - [x] 11.5 Write unit tests for order generation
    - Test delivery order generation
    - Test pickup order generation
    - Test dispatch order generation
    - Test fulfillment tracking
    - _Requirements: 7.1, 7.2, 7.3_

- [-] 12. Implemen                  t data integrity and validation
  - [x] 12.1 Implement inventory validation
    - Validate total allocated <= available inventory
    - Validate all prices and quantities are non-negative
    - Prevent deletion of allocated contributions
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [x] 12.2 Implement transaction isolation
    - Use PostgreSQL transactions for allocation
    - Use DynamoDB conditional writes for inventory updates
    - Handle concurrent update conflicts
    - _Requirements: 9.5_
  
  - [x] 12.3 Implement audit logging
    - Log all inventory changes with timestamp and user
    - Log all allocation decisions
    - Log all fulfillment updates
    - Store logs in CloudWatch
    - _Requirements: 9.6_
  
  - [x] 12.4 Write unit tests for data integrity
    - Test validation rules
    - Test transaction rollback
    - Test concurrent update handling
    - Test audit log completeness
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 13. Implement integration with existing agents
  - [x] 13.1 Create integration with Sell Agent
    - Expose API for Sell Agent to route farmer produce
    - Create POST /api/inventory/contributions endpoint
    - Expose API for Sell Agent to query allocation data
    - Create GET /api/allocations/mandi endpoint
    - _Requirements: 10.1, 10.2_
  
  - [x] 13.2 Create integration with Process Agent
    - Expose API for Process Agent to query allocations
    - Create GET /api/allocations/processing endpoint
    - Expose API for Process Agent to update fulfillment
    - Create PUT /api/allocations/{id}/fulfillment endpoint
    - _Requirements: 10.2_
  
  - [x] 13.3 Implement backward compatibility
    - Maintain existing farmer workflow APIs
    - Maintain existing buyer workflow APIs
    - Add feature flag for collective mode
    - _Requirements: 10.4_
  
  - [x] 13.4 Implement error handling and degradation
    - Handle integration errors gracefully
    - Log errors to CloudWatch
    - Continue operating with degraded functionality
    - _Requirements: 10.5_
  
  - [x] 13.5 Write integration tests
    - Test Sell Agent integration
    - Test Process Agent integration
    - Test backward compatibility
    - Test error handling
    - _Requirements: 10.3_

- [x] 14. Checkpoint - Ensure integrations work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement dashboard: Collective inventory view
  - [x] 15.1 Create CollectiveInventoryView component
    - Display current inventory totals by crop type
    - Show available, reserved, and allocated quantities
    - Display per-farmer contribution breakdown
    - Add real-time updates via WebSocket
    - _Requirements: 8.1_
  
  - [x] 15.2 Create InventoryCard component
    - Display crop type, total quantity, and status
    - Use color coding for inventory levels
    - Show last updated timestamp
    - _Requirements: 8.1_
  
  - [x] 15.3 Write unit tests for inventory view
    - Test inventory display
    - Test real-time updates
    - Test per-farmer breakdown
    - _Requirements: 8.1_

- [x] 16. Implement dashboard: Society delivery schedule
  - [x] 16.1 Create SocietyScheduleView component
    - Display upcoming deliveries in calendar format
    - Show reserved quantities by society
    - Display delivery day and time window
    - Add filtering by date range
    - _Requirements: 8.2_
  
  - [x] 16.2 Create DeliveryCard component
    - Display society name, crop type, quantity
    - Show delivery date and status
    - Add action buttons for confirmation
    - _Requirements: 8.2_
  
  - [x] 16.3 Write unit tests for schedule view
    - Test calendar rendering
    - Test filtering
    - Test delivery card display
    - _Requirements: 8.2_

- [x] 17. Implement dashboard: Allocation flow visualization
  - [x] 17.1 Create AllocationFlowView component
    - Implement Sankey diagram using Recharts
    - Show flow from collective inventory to channels
    - Display quantities and percentages
    - Add interactive tooltips
    - _Requirements: 8.3_
  
  - [x] 17.2 Create allocation flow data transformation
    - Transform allocation data to Sankey format
    - Calculate node positions and link widths
    - Add color coding by channel type
    - _Requirements: 8.3_
  
  - [x] 17.3 Write unit tests for flow visualization
    - Test data transformation
    - Test Sankey rendering
    - Test interactive tooltips
    - _Requirements: 8.3_

- [x] 18. Implement dashboard: Blended realization metrics
  - [x] 18.1 Create RealizationMetricsView component
    - Display blended realization rate
    - Show channel-wise breakdown (society, processing, mandi)
    - Display comparison to best single-channel
    - Add trend chart for historical data
    - _Requirements: 8.4_
  
  - [x] 18.2 Create ChannelBreakdownCard component
    - Display channel name, quantity, revenue, rate
    - Use color coding by channel type
    - Show percentage of total
    - _Requirements: 8.4_
  
  - [x] 18.3 Write unit tests for realization metrics
    - Test metrics display
    - Test channel breakdown
    - Test trend chart
    - _Requirements: 8.4_

- [-] 19. Implement dashboard: Per-farmer tracking
  - [x] 19.1 Create FarmerContributionView component
    - Display list of farmers with contributions
    - Show contribution quantity and income
    - Display blended realization per farmer
    - Add search and filtering
    - _Requirements: 8.5_
  
  - [x] 19.2 Create FarmerIncomeCard component
    - Display farmer name, contribution, income
    - Show channel-wise breakdown
    - Display improvement vs single-channel
    - _Requirements: 8.5_
  
  - [x] 19.3 Write unit tests for farmer tracking
    - Test farmer list display
    - Test income calculation
    - Test search and filtering
    - _Requirements: 8.5_

- [x] 20. Implement dashboard: Alerts and reporting
  - [x] 20.1 Create AlertsView component
    - Display inventory shortage alerts
    - Display unfulfilled reservation alerts
    - Show alert priority and timestamp
    - Add action buttons for resolution
    - _Requirements: 8.7_
  
  - [x] 20.2 Create ReportsView component
    - Add date range filtering
    - Add crop type filtering
    - Add channel filtering
    - Generate CSV export
    - _Requirements: 8.6_
  
  - [x] 20.3 Write unit tests for alerts and reporting
    - Test alert display
    - Test filtering
    - Test CSV export
    - _Requirements: 8.6, 8.7_

- [x] 21. Checkpoint - Ensure dashboard works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 22. Implement API endpoints
  - [x] 22.1 Create FastAPI application
    - Set up FastAPI app with CORS
    - Configure authentication middleware
    - Add request logging
    - Add error handling
    - _Requirements: 10.3_
  
  - [x] 22.2 Implement inventory endpoints
    - POST /api/inventory/contributions
    - GET /api/inventory/{fpo_id}/{crop_type}
    - GET /api/inventory/{fpo_id}/summary
    - _Requirements: 1.1, 1.4_
  
  - [x] 22.3 Implement society endpoints
    - POST /api/societies
    - GET /api/societies/{society_id}
    - PUT /api/societies/{society_id}
    - DELETE /api/societies/{society_id}
    - GET /api/societies
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [x] 22.4 Implement processing partner endpoints
    - POST /api/processing-partners
    - GET /api/processing-partners/{partner_id}
    - PUT /api/processing-partners/{partner_id}
    - DELETE /api/processing-partners/{partner_id}
    - GET /api/processing-partners
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x] 22.5 Implement allocation endpoints
    - POST /api/allocations
    - GET /api/allocations/{allocation_id}
    - GET /api/allocations/{fpo_id}/history
    - GET /api/allocations/{allocation_id}/realization
    - PUT /api/allocations/{allocation_id}/fulfillment
    - _Requirements: 4.1, 6.3, 7.4_
  
  - [x] 22.6 Implement demand prediction endpoints
    - POST /api/demand/predict
    - POST /api/demand/reserve
    - PUT /api/demand/confirm
    - GET /api/demand/reservations
    - _Requirements: 3.1, 3.2, 3.5_
  
  - [x] 22.7 Write API integration tests
    - Test all endpoints with valid inputs
    - Test error handling
    - Test authentication
    - Test CORS
    - _Requirements: 10.3_

- [x] 23. Deploy infrastructure
  - [x] 23.1 Create AWS CDK stacks
    - Define Lambda functions for all APIs
    - Define PostgreSQL RDS instance
    - Define DynamoDB tables
    - Define API Gateway
    - Define IAM roles and policies
    - _Requirements: All requirements_
  
  - [x] 23.2 Configure environment variables
    - Set database connection strings
    - Set AWS region and credentials
    - Set feature flags
    - _Requirements: All requirements_
  
  - [x] 23.3 Set up monitoring and alerting
    - Configure CloudWatch dashboards
    - Set up alarms for errors and latency
    - Configure SNS notifications
    - _Requirements: All requirements_
  
  - [x] 23.4 Deploy to staging environment
    - Deploy CDK stacks
    - Run smoke tests
    - Verify all endpoints work
    - _Requirements: All requirements_

- [ ] 24. Final checkpoint - End-to-end verification
  - Run full test suite (unit + property + integration)
  - Verify all 10 correctness properties pass
  - Test with realistic data (500 farmers, 50 societies, 10 partners)
  - Verify allocation completes in < 5 seconds
  - Test dashboard with real backend
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each property test references a specific correctness property from the design document
- Checkpoints ensure incremental validation and early error detection
- Property tests use Hypothesis with minimum 100 iterations per test
- Integration tests use mocked AWS services for local development
- All tests should pass before proceeding to deployment
- The implementation integrates with existing Sell Agent and Process Agent
- Dashboard uses React 18, TypeScript, and Recharts for visualization

