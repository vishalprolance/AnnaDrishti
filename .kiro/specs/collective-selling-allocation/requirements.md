# Requirements Document: Collective Selling & Allocation

## Introduction

Anna Drishti is transforming from an individual farmer marketplace into an operating system for collective selling. The system pools farmer produce into collective FPO inventory and allocates it across multiple channels using priority-based logic. This enables small farmers to operate as one organized supply engine, delivering stable retail supply to societies, value capture through processing partners, and optimized fallback through mandi channels.

## Glossary

- **FPO**: Farmer Producer Organization - the collective entity that pools farmer produce
- **Society**: Residential apartment community that orders produce on a recurring schedule
- **Collective_Inventory**: Aggregated produce pool from multiple farmers managed at FPO level
- **Allocation_Engine**: System component that distributes inventory across channels based on priority
- **Processing_Partner**: Industrial buyer with pre-agreed rates for surplus produce
- **Blended_Realization**: Average price per kg achieved across all sales channels
- **Reservation**: Locked quantity for society demand before allocation begins
- **Mandi**: Traditional wholesale market for agricultural produce
- **Contribution**: Individual farmer's produce added to collective inventory
- **Channel**: Sales destination (society, processing partner, or mandi/buyer)

## Requirements

### Requirement 1: Collective Inventory Management

**User Story:** As an FPO coordinator, I want to pool farmer produce into collective inventory, so that we can manage supply as one coordinated unit instead of fragmented individual lots.

#### Acceptance Criteria

1. WHEN a farmer adds produce to the system, THE Collective_Inventory SHALL aggregate it with existing FPO inventory for that crop type
2. WHEN inventory is aggregated, THE System SHALL maintain a record of each farmer's individual contribution including farmer ID, crop type, quantity, quality grade, and timestamp
3. THE System SHALL provide real-time inventory totals by crop type across all farmers
4. WHEN querying inventory, THE System SHALL return both aggregate totals and per-farmer breakdowns
5. WHEN a farmer's contribution is recorded, THE System SHALL validate that quantity is positive and crop type is recognized

### Requirement 2: Society Registration and Profile Management

**User Story:** As a society administrator, I want to register my community and set delivery preferences, so that we receive consistent farm-fresh produce on our preferred schedule.

#### Acceptance Criteria

1. WHEN a society registers, THE System SHALL capture society name, location, contact details, and delivery address
2. WHEN setting preferences, THE Society_Profile SHALL store delivery frequency (once weekly, twice weekly, or weekend-only)
3. WHEN setting preferences, THE Society_Profile SHALL store preferred delivery day and time window
4. WHEN setting preferences, THE Society_Profile SHALL store crop preferences and typical quantity ranges
5. THE System SHALL validate that delivery frequency is one of the allowed values
6. WHEN a society profile is created, THE System SHALL assign a unique society identifier

### Requirement 3: Demand Prediction and Reservation

**User Story:** As an FPO coordinator, I want the system to predict society demand and reserve inventory, so that we fulfill committed orders before allocating to other channels.

#### Acceptance Criteria

1. WHEN a society has historical order data, THE Prediction_Engine SHALL calculate expected demand for the next delivery cycle based on past patterns
2. WHEN demand is predicted, THE System SHALL reserve the predicted quantity from collective inventory before allocation begins
3. WHEN reservation occurs, THE System SHALL mark reserved quantity as unavailable for other channels
4. IF predicted demand exceeds available inventory, THEN THE System SHALL reserve all available inventory and flag the shortage
5. WHEN a society places an actual order, THE System SHALL replace the predicted reservation with the confirmed order quantity
6. THE System SHALL maintain reservation records with society ID, crop type, quantity, and reservation timestamp

### Requirement 4: Priority-Based Allocation Engine

**User Story:** As an FPO coordinator, I want inventory allocated across channels by priority, so that we maximize value while fulfilling commitments.

#### Acceptance Criteria

1. WHEN allocation begins, THE Allocation_Engine SHALL first allocate to society reservations (Priority 1)
2. WHEN society demand is fulfilled, THE Allocation_Engine SHALL allocate surplus to processing partners (Priority 2)
3. WHEN processing capacity is filled, THE Allocation_Engine SHALL allocate remaining inventory to mandi/buyers (Priority 3)
4. THE Allocation_Engine SHALL respect processing partner capacity constraints when allocating to Priority 2
5. THE Allocation_Engine SHALL respect quality requirements for each channel when allocating
6. WHEN allocation is complete, THE System SHALL record allocation details including channel, quantity, and expected price for each allocation
7. IF inventory is insufficient for all society reservations, THEN THE System SHALL allocate proportionally and flag unfulfilled reservations

### Requirement 5: Processing Partner Management

**User Story:** As an FPO coordinator, I want to manage processing partner relationships, so that we can route surplus produce to value-added channels at pre-agreed rates.

#### Acceptance Criteria

1. WHEN a processing partner is registered, THE System SHALL capture partner name, contact details, and processing facility location
2. WHEN setting partner terms, THE System SHALL store pre-agreed rates by crop type
3. WHEN setting partner terms, THE System SHALL store daily or weekly capacity limits by crop type
4. WHEN setting partner terms, THE System SHALL store quality requirements and pickup schedule
5. THE System SHALL validate that rates are positive and capacity limits are non-negative
6. WHEN a processing partner is created, THE System SHALL assign a unique partner identifier

### Requirement 6: Blended Realization Calculation

**User Story:** As a farmer, I want to see my income breakdown across all channels, so that I understand how collective selling improves my returns compared to single-channel selling.

#### Acceptance Criteria

1. WHEN allocation is complete, THE System SHALL calculate blended realization as total revenue divided by total quantity sold
2. WHEN calculating farmer income, THE System SHALL multiply each farmer's contribution by the blended realization rate
3. THE System SHALL provide a breakdown showing quantity and revenue by channel (society, processing, mandi)
4. THE System SHALL calculate and display the difference between blended realization and best single-channel price
5. WHEN displaying realization, THE System SHALL show per-kg rates for each channel alongside quantities allocated
6. THE System SHALL maintain historical realization data for trend analysis

### Requirement 7: Allocation Execution and Tracking

**User Story:** As an FPO coordinator, I want to execute allocation and track fulfillment, so that I can coordinate logistics and ensure timely delivery.

#### Acceptance Criteria

1. WHEN allocation is executed, THE System SHALL generate delivery orders for each society with allocated quantity and delivery details
2. WHEN allocation is executed, THE System SHALL generate pickup orders for processing partners with allocated quantity and pickup schedule
3. WHEN allocation is executed, THE System SHALL generate mandi dispatch orders with allocated quantity and destination
4. THE System SHALL track fulfillment status for each order (pending, in-transit, delivered, completed)
5. WHEN an order is fulfilled, THE System SHALL update inventory to reflect the dispatched quantity
6. THE System SHALL prevent double-allocation by marking allocated inventory as committed

### Requirement 8: Dashboard and Reporting

**User Story:** As an FPO coordinator, I want visual dashboards and reports, so that I can monitor collective operations and make informed decisions.

#### Acceptance Criteria

1. THE Dashboard SHALL display current collective inventory totals by crop type
2. THE Dashboard SHALL display upcoming society delivery schedule with reserved quantities
3. THE Dashboard SHALL visualize allocation flow across channels using a Sankey diagram
4. THE Dashboard SHALL display blended realization metrics with channel-wise breakdown
5. THE Dashboard SHALL display per-farmer contribution and income tracking
6. WHEN viewing reports, THE System SHALL allow filtering by date range, crop type, and channel
7. THE Dashboard SHALL display alerts for inventory shortages and unfulfilled reservations

### Requirement 9: Data Integrity and Validation

**User Story:** As a system administrator, I want data validation and integrity checks, so that the system maintains accurate and consistent records.

#### Acceptance Criteria

1. WHEN inventory is updated, THE System SHALL ensure total allocated quantity does not exceed available inventory
2. WHEN calculating realization, THE System SHALL validate that all prices and quantities are non-negative
3. THE System SHALL prevent deletion of farmer contributions that have been allocated
4. THE System SHALL maintain referential integrity between allocations and inventory records
5. WHEN concurrent updates occur, THE System SHALL use transaction isolation to prevent race conditions
6. THE System SHALL log all inventory and allocation changes with timestamp and user identifier

### Requirement 10: Integration with Existing Agents

**User Story:** As a system architect, I want seamless integration with existing Sell Agent and Process Agent, so that collective selling enhances rather than replaces current functionality.

#### Acceptance Criteria

1. WHEN Sell_Agent receives farmer produce information, THE System SHALL route it to Collective_Inventory
2. WHEN Process_Agent handles processing partner interactions, THE System SHALL use allocation data from Allocation_Engine
3. THE System SHALL expose APIs for inventory queries, allocation execution, and realization reporting
4. THE System SHALL maintain backward compatibility with existing farmer and buyer workflows
5. WHEN integration errors occur, THE System SHALL log errors and continue operating with degraded functionality
