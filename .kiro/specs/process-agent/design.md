# Design Document: Process Agent

## Overview

The Process Agent is the core differentiator of Anna Drishti - an AI-powered system that prevents market crashes by detecting surplus conditions and orchestrating processing diversion before prices collapse. It operates as an event-driven component that integrates with the Sell Agent to provide comprehensive surplus management for FPOs.

The agent handles:
- Real-time surplus detection by aggregating harvest signals across FPO members
- Processor capacity querying from pre-onboarded partners
- MILP-based optimization to calculate optimal allocation between fresh market and processing
- Revenue blending calculations to demonstrate farmer benefits
- WhatsApp-based processor communication and confirmation
- Coordination with Sell Agent for integrated workflow execution
- Separate tracking of processing contracts with different payment terms

The system is designed to complete surplus detection and allocation within 15 seconds, with MILP optimization completing in under 5 seconds for up to 50 farmers. It prevents fresh market crashes by maintaining prices within 10% of forecasted stable prices through strategic processing diversion.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRIGGER LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Sell Agent (Market Scan) → Surplus Signal                │  │
│  │ EventBridge Schedule → Periodic Surplus Check            │  │
│  │ Farmer Harvest Signal → Volume Aggregation Update        │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│              PROCESS AGENT CORE (AWS Lambda)                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Execution Flow:                                            │ │
│  │                                                            │ │
│  │  Aggregate Volumes → Check Absorption → Detect Surplus →  │ │
│  │  Query Processors → MILP Optimize → Calculate Blending →  │ │
│  │  Send Offers → Track Responses → Coordinate with Sell     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ State Management (DynamoDB):                               │ │
│  │ • Surplus detection events                                 │ │
│  │ • Processor capacity snapshots                             │ │
│  │ • Allocation plans (pending/confirmed)                     │ │
│  │ • Processor response tracking                              │ │
│  │ • Reallocation triggers                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                      TOOL LAYER                                  │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Volume           │  │ Absorption       │  │ Processor    │ │
│  │ Aggregator       │  │ Calculator       │  │ Matcher      │ │
│  │ (FPO harvest     │  │ (Market Data     │  │ (DB Query +  │ │
│  │  signals)        │  │  Pipeline)       │  │  Capacity)   │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ MILP Optimizer   │  │ Revenue          │  │ WhatsApp     │ │
│  │ (OR-Tools        │  │ Calculator       │  │ Client       │ │
│  │  Lambda Layer)   │  │ (Blending)       │  │ (Gupshup)    │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Sell Agent       │  │ Contract         │  │ Audit Logger │ │
│  │ Coordinator      │  │ Tracker          │  │ (CloudWatch) │ │
│  │ (EventBridge)    │  │ (PostgreSQL)     │  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                    DATA & EXTERNAL SERVICES                      │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ PostgreSQL       │  │ DynamoDB         │  │ ElastiCache  │ │
│  │ (Processors,     │  │ (Allocation      │  │ Redis        │ │
│  │  Contracts)      │  │  State)          │  │ (Capacity    │ │
│  │                  │  │                  │  │  Cache)      │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Market Data      │  │ WhatsApp         │  │ EventBridge  │ │
│  │ Pipeline         │  │ Business API     │  │ (Events)     │ │
│  │ (Absorption)     │  │ (Gupshup/Twilio) │  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Architecture (AWS)

The Process Agent is deployed as an AWS Lambda function with the following components:

**Lambda Configuration:**
- Runtime: Python 3.11
- Memory: 3GB (required for OR-Tools MILP solver)
- Timeout: 15 minutes (to handle complex optimizations and processor response waiting)
- Layers: OR-Tools Python library, NumPy, SciPy
- VPC: Attached to private subnet for RDS access
- Environment Variables: Database connection, API keys, configuration thresholds

**Trigger Sources:**
- EventBridge event from Sell Agent (surplus signal)
- EventBridge scheduled rule (periodic surplus check every 6 hours)
- API Gateway webhook (processor response callback)

**Data Storage:**
- PostgreSQL (RDS): Processor profiles, processing contracts, farmer allocations
- DynamoDB: Allocation state, processor responses, reallocation triggers
- ElastiCache Redis: Processor capacity cache (24-hour TTL)
- CloudWatch Logs: Audit trail, execution logs, error tracking

## Components and Interfaces

### 1. Volume Aggregator

**Purpose:** Aggregate harvest signals from farmers at the FPO level to calculate total volume by crop type.

**Inputs:**
- Farmer harvest signals (from IVR/WhatsApp via Sell Agent)
- FPO ID
- Crop type
- Time window (default: next 7 days)

**Outputs:**
- Aggregated volume by crop type
- List of farmers contributing to volume
- Individual farmer quantities
- Harvest timing distribution

**Implementation:**
- Query farmer harvest signals from database filtered by FPO and crop
- Filter by harvest readiness status: "harvest-ready" or "harvesting"
- Sum quantities across all farmers
- Group by expected harvest date to create timing distribution
- Cache results in Redis with 1-hour TTL

**Interface:**
```python
class VolumeAggregator:
    def aggregate_fpo_volume(self, fpo_id: str, crop: str, days_ahead: int = 7) -> AggregatedVolume:
        """Aggregate harvest volumes across FPO members"""
        
    def get_farmer_contributions(self, fpo_id: str, crop: str) -> List[FarmerContribution]:
        """Get individual farmer quantities contributing to total"""
        
    def get_harvest_timing(self, fpo_id: str, crop: str) -> Dict[date, float]:
        """Get volume distribution by expected harvest date"""
```

### 2. Absorption Calculator

**Purpose:** Calculate historical mandi absorption capacity to determine safe volume thresholds.

**Inputs:**
- Target mandi IDs (from Sell Agent market scan)
- Crop type
- Historical period (default: 90 days)
- Seasonal adjustment factors

**Outputs:**
- Historical average daily arrivals per mandi
- Combined absorption capacity across target mandis
- Safe threshold (configurable percentage, default 80%)
- Seasonal adjustment factor
- Data staleness indicator

**Implementation:**
- Query Market Data Pipeline for historical mandi arrivals
- Calculate rolling 90-day average arrivals by mandi and crop
- Apply seasonal adjustment based on festival calendar and weather patterns
- Compute safe threshold as percentage of historical capacity
- Flag data staleness if most recent data is >24 hours old

**Interface:**
```python
class AbsorptionCalculator:
    def calculate_capacity(self, mandi_ids: List[str], crop: str, days_back: int = 90) -> AbsorptionCapacity:
        """Calculate historical absorption capacity"""
        
    def get_safe_threshold(self, capacity: AbsorptionCapacity, threshold_pct: float = 0.8) -> float:
        """Calculate safe volume threshold"""
        
    def apply_seasonal_adjustment(self, capacity: float, date: datetime) -> float:
        """Apply seasonal factors to capacity estimate"""
```

### 3. Surplus Detector

**Purpose:** Detect when FPO volume exceeds safe mandi capacity and trigger processing diversion.

**Inputs:**
- Aggregated FPO volume
- Mandi absorption capacity
- Safe threshold percentage
- Crash risk parameters

**Outputs:**
- Surplus detected flag (boolean)
- Surplus amount (tonnes)
- Percentage over threshold
- Crash risk level (low/medium/high)
- Recommended processing diversion amount

**Implementation:**
- Compare aggregated volume to safe threshold
- Calculate surplus as: volume - safe_threshold
- Compute percentage over threshold
- Assess crash risk based on percentage over threshold:
  - Low: 0-20% over threshold
  - Medium: 20-40% over threshold
  - High: >40% over threshold
- Recommend processing diversion to bring volume to safe threshold

**Interface:**
```python
class SurplusDetector:
    def detect_surplus(self, volume: float, capacity: AbsorptionCapacity, threshold_pct: float = 0.8) -> SurplusDetection:
        """Detect if volume exceeds safe capacity"""
        
    def calculate_crash_risk(self, surplus_pct: float) -> str:
        """Assess crash risk level"""
        
    def recommend_diversion(self, surplus: float, capacity: float) -> float:
        """Calculate recommended processing diversion amount"""
```

### 4. Processor Matcher

**Purpose:** Query and match available processors based on crop type, capacity, and location.

**Inputs:**
- Crop type
- Required capacity (surplus amount)
- FPO location
- Quality requirements

**Outputs:**
- List of matched processors
- Available capacity per processor
- Contract rates
- Distance from FPO
- Quality requirements
- Minimum batch sizes

**Implementation:**
- Query processor database filtered by crop type compatibility
- Check available capacity from cache (Redis) or database
- Calculate distance from FPO to processor facility
- Filter by minimum batch size feasibility
- Sort by: available capacity (desc), distance (asc), contract rate (desc)
- Limit to top 5 processors

**Interface:**
```python
class ProcessorMatcher:
    def match_processors(self, crop: str, required_capacity: float, fpo_location: Location) -> List[ProcessorMatch]:
        """Find and rank processors for surplus allocation"""
        
    def check_capacity(self, processor_id: str) -> float:
        """Get current available capacity for processor"""
        
    def calculate_net_rate(self, processor: Processor, fpo_location: Location, quantity: float) -> float:
        """Calculate net processing rate after transport costs"""
```

### 5. MILP Optimizer

**Purpose:** Calculate optimal allocation between fresh market and processing to maximize total FPO revenue.

**Inputs:**
- List of farmers with quantities
- Fresh market price (from Sell Agent)
- Crash price (estimated price if no diversion)
- List of processors with capacity and rates
- Safe fresh market threshold
- Constraints (batch sizes, quality, transport)

**Outputs:**
- Allocation plan: farmer → destination (fresh market or processor)
- Quantities per allocation
- Expected revenue per farmer
- Total FPO revenue
- Objective function value

**Implementation:**
- Use OR-Tools CP-SAT solver for MILP optimization
- Define decision variables: x[farmer][destination] (binary or continuous)
- Objective function: maximize Σ(quantity × price) across all allocations
- Constraints:
  - Fresh market total ≤ safe threshold
  - Processor allocations ≤ processor capacity
  - Processor allocations ≥ minimum batch size (if allocated)
  - Each farmer allocated to exactly one destination
  - Quality matching constraints
- Solve with 5-second timeout
- Fall back to proportional allocation if solver fails

**Interface:**
```python
class MILPOptimizer:
    def optimize_allocation(
        self,
        farmers: List[Farmer],
        fresh_price: float,
        crash_price: float,
        processors: List[Processor],
        safe_threshold: float,
        constraints: AllocationConstraints
    ) -> AllocationPlan:
        """Calculate optimal allocation using MILP"""
        
    def validate_solution(self, plan: AllocationPlan, constraints: AllocationConstraints) -> bool:
        """Verify solution satisfies all constraints"""
        
    def fallback_allocation(self, farmers: List[Farmer], processors: List[Processor]) -> AllocationPlan:
        """Rule-based allocation if MILP fails"""
```

### 6. Revenue Calculator

**Purpose:** Calculate blended prices and demonstrate farmer benefits from coordinated approach.

**Inputs:**
- Allocation plan
- Fresh market price
- Processing prices by processor
- Crash scenario price (counterfactual)

**Outputs:**
- Blended price per farmer
- Total revenue per farmer
- Breakdown: fresh vs processing revenue
- Benefit compared to crash scenario
- FPO-level aggregated metrics

**Implementation:**
- For each farmer, calculate:
  - Fresh revenue: fresh_quantity × fresh_price
  - Processing revenue: processing_quantity × processing_rate
  - Total revenue: fresh_revenue + processing_revenue
  - Blended price: total_revenue / total_quantity
- Calculate counterfactual: total_quantity × crash_price
- Compute benefit: total_revenue - counterfactual_revenue
- Aggregate across FPO for collective metrics

**Interface:**
```python
class RevenueCalculator:
    def calculate_blended_price(self, farmer: Farmer, allocation: Allocation, prices: PriceContext) -> float:
        """Calculate weighted average price across allocations"""
        
    def calculate_benefit(self, farmer: Farmer, allocation: Allocation, crash_price: float) -> float:
        """Calculate benefit vs crash scenario"""
        
    def calculate_fpo_metrics(self, allocations: List[Allocation], prices: PriceContext) -> FPOMetrics:
        """Aggregate revenue metrics across FPO"""
```

### 7. Processor Communicator

**Purpose:** Send allocation offers to processors via WhatsApp and track responses.

**Inputs:**
- Processor contact (WhatsApp number)
- Allocation details (crop, quantity, quality, pickup time)
- Contract rate
- FPO location
- Processor language preference

**Outputs:**
- Message sent confirmation
- Processor response (confirm/decline/counter)
- Response timestamp
- Communication log entry

**Implementation:**
- Generate structured message in processor's preferred language
- Include: crop type, quantity, quality indicators, pickup timeframe, location, rate
- Send via WhatsApp Business API (Gupshup or Twilio)
- Set 4-hour response timeout
- Parse processor response for confirmation keywords
- Log all communications to audit trail
- Trigger reallocation if declined or timeout

**Interface:**
```python
class ProcessorCommunicator:
    def send_allocation_offer(self, processor: Processor, allocation: Allocation, context: AllocationContext) -> str:
        """Send WhatsApp offer to processor"""
        
    def parse_response(self, processor_id: str, message: str) -> ProcessorResponse:
        """Parse processor response message"""
        
    def handle_timeout(self, processor_id: str, allocation_id: str) -> None:
        """Handle processor non-response after 4 hours"""
```

### 8. Sell Agent Coordinator

**Purpose:** Coordinate with Sell Agent to integrate processing allocation into farmer workflows.

**Inputs:**
- Allocation plan
- Processor confirmations
- Fresh market safe volume

**Outputs:**
- Farmer routing instructions (fresh market vs processing)
- Updated safe volume for fresh market
- Coordination events for Sell Agent

**Implementation:**
- Publish allocation plan to EventBridge for Sell Agent consumption
- Include farmer IDs, destinations, quantities, expected prices
- Update fresh market safe volume after processing diversion
- Notify Sell Agent when all processor confirmations received
- Coordinate timing: Sell Agent waits for Process Agent before farmer confirmations

**Interface:**
```python
class SellAgentCoordinator:
    def publish_allocation(self, plan: AllocationPlan) -> None:
        """Publish allocation plan to Sell Agent via EventBridge"""
        
    def update_safe_volume(self, fresh_market_volume: float) -> None:
        """Update fresh market safe volume after diversion"""
        
    def notify_ready_for_confirmation(self, allocation_id: str) -> None:
        """Signal Sell Agent to proceed with farmer confirmations"""
```

### 9. Contract Tracker

**Purpose:** Track processing contracts separately from fresh market transactions.

**Inputs:**
- Farmer confirmation
- Processor confirmation
- Allocation details
- Payment terms

**Outputs:**
- Processing contract record
- Pickup schedule
- Payment tracking
- Contract status updates

**Implementation:**
- Create contract record in PostgreSQL
- Store: farmer ID, processor ID, crop, quantity, rate, pickup time, payment terms
- Track status: pending → pickup_scheduled → picked_up → payment_pending → completed
- Support different payment terms (7-15 days typical for processing)
- Generate contract reports for FPO coordinator
- Alert on payment delays

**Interface:**
```python
class ContractTracker:
    def create_contract(self, farmer_id: str, processor_id: str, allocation: Allocation) -> Contract:
        """Create processing contract record"""
        
    def update_status(self, contract_id: str, status: str, timestamp: datetime) -> None:
        """Update contract status"""
        
    def track_payment(self, contract_id: str, amount: float, timestamp: datetime) -> None:
        """Record payment received"""
        
    def generate_report(self, fpo_id: str, date_range: DateRange) -> ContractReport:
        """Generate processing contract report for FPO"""
```

## Data Models

### AggregatedVolume
```python
class AggregatedVolume:
    fpo_id: str
    crop: str
    total_volume: float  # tonnes
    farmer_count: int
    farmer_contributions: List[FarmerContribution]
    harvest_timing: Dict[date, float]  # date → volume
    calculated_at: datetime
```

### FarmerContribution
```python
class FarmerContribution:
    farmer_id: str
    quantity: float  # tonnes
    quality_indicators: Dict[str, Any]
    expected_harvest_date: date
    processing_preference: str  # "accept" | "fresh_only" | "premium_only"
```

### AbsorptionCapacity
```python
class AbsorptionCapacity:
    mandi_ids: List[str]
    crop: str
    historical_avg_daily: float  # tonnes/day
    combined_weekly_capacity: float  # tonnes/week
    seasonal_adjustment_factor: float
    safe_threshold: float  # tonnes
    data_staleness_hours: int
    calculated_at: datetime
```

### SurplusDetection
```python
class SurplusDetection:
    surplus_detected: bool
    fpo_volume: float  # tonnes
    safe_threshold: float  # tonnes
    surplus_amount: float  # tonnes
    surplus_percentage: float  # percentage over threshold
    crash_risk_level: str  # "low" | "medium" | "high"
    recommended_diversion: float  # tonnes
    detected_at: datetime
```

### ProcessorMatch
```python
class ProcessorMatch:
    processor_id: str
    processor_name: str
    processing_type: str  # "paste" | "dried" | "powder" | "frozen"
    available_capacity: float  # tonnes/week
    contract_rate_min: float  # ₹/kg
    contract_rate_max: float  # ₹/kg
    distance_km: float
    transport_cost: float  # ₹ total
    net_rate: float  # ₹/kg after transport
    minimum_batch_size: float  # tonnes
    quality_requirements: Dict[str, Any]
    location: Location
```

### AllocationPlan
```python
class AllocationPlan:
    allocation_id: str
    fpo_id: str
    crop: str
    total_volume: float
    fresh_market_volume: float
    processing_volume: float
    farmer_allocations: List[FarmerAllocation]
    processor_allocations: List[ProcessorAllocation]
    expected_total_revenue: float
    objective_value: float  # MILP objective
    created_at: datetime
    status: str  # "pending" | "confirmed" | "executing" | "completed"
```

### FarmerAllocation
```python
class FarmerAllocation:
    farmer_id: str
    destination_type: str  # "fresh_market" | "processor"
    destination_id: Optional[str]  # processor_id if processing
    quantity: float  # tonnes
    expected_price: float  # ₹/kg
    expected_revenue: float  # ₹
    blended_price: float  # ₹/kg (if split allocation)
    benefit_vs_crash: float  # ₹
```

### ProcessorAllocation
```python
class ProcessorAllocation:
    processor_id: str
    processor_name: str
    total_quantity: float  # tonnes
    farmer_ids: List[str]
    contract_rate: float  # ₹/kg
    pickup_time: datetime
    location: Location
    quality_requirements: Dict[str, Any]
    status: str  # "pending" | "confirmed" | "declined" | "timeout"
    response_time: Optional[datetime]
```

### ProcessorResponse
```python
class ProcessorResponse:
    processor_id: str
    allocation_id: str
    response_type: str  # "confirm" | "decline" | "counter" | "timeout"
    confirmed_quantity: Optional[float]
    counter_rate: Optional[float]
    message: str
    timestamp: datetime
```

### Contract
```python
class Contract:
    contract_id: str
    farmer_id: str
    processor_id: str
    crop: str
    quantity: float  # tonnes
    agreed_rate: float  # ₹/kg
    total_value: float  # ₹
    pickup_time: datetime
    expected_payment_time: datetime
    payment_terms: str  # "7 days" | "15 days" | "on delivery"
    status: str  # "pending" | "pickup_scheduled" | "picked_up" | "payment_pending" | "completed"
    created_at: datetime
    updated_at: datetime
```

### AllocationConstraints
```python
class AllocationConstraints:
    safe_fresh_threshold: float  # tonnes
    processor_capacities: Dict[str, float]  # processor_id → capacity
    minimum_batch_sizes: Dict[str, float]  # processor_id → min batch
    quality_requirements: Dict[str, Dict[str, Any]]  # processor_id → requirements
    transport_costs: Dict[str, float]  # processor_id → cost
    farmer_preferences: Dict[str, str]  # farmer_id → preference
```

### PriceContext
```python
class PriceContext:
    fresh_market_price: float  # ₹/kg (stable price with diversion)
    crash_price: float  # ₹/kg (price without diversion)
    processor_rates: Dict[str, float]  # processor_id → rate
    transport_costs: Dict[str, float]  # processor_id → cost
```

### FPOMetrics
```python
class FPOMetrics:
    fpo_id: str
    total_farmers: int
    total_volume: float  # tonnes
    fresh_market_farmers: int
    processing_farmers: int
    total_revenue: float  # ₹
    avg_revenue_per_farmer: float  # ₹
    total_benefit_vs_crash: float  # ₹
    avg_blended_price: float  # ₹/kg
    price_protection_achieved: bool  # fresh price within 10% of forecast
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Volume Aggregation Invariant
*For any* set of farmers with individual quantities, the aggregated FPO volume should equal the sum of all individual farmer quantities.
**Validates: Requirements 1.1**

### Property 2: Safe Threshold Calculation
*For any* historical absorption capacity C and threshold percentage P, the safe threshold should equal C × P.
**Validates: Requirements 1.3**

### Property 3: Surplus Detection Trigger
*For any* aggregated volume V and safe threshold T where V > T, a surplus alert should be triggered.
**Validates: Requirements 1.4**

### Property 4: Crop Type Filtering
*For any* surplus detection with crop C, only processors compatible with crop C should be returned in the query results.
**Validates: Requirements 2.2**

### Property 5: Zero Capacity Exclusion
*For any* processor with available capacity = 0, that processor should not appear in allocation candidates.
**Validates: Requirements 2.5**

### Property 6: MILP Constraint Satisfaction
*For any* allocation solution produced by the MILP optimizer, all constraints must be satisfied: fresh market volume ≤ safe threshold, processor allocations ≤ processor capacity, processor allocations ≥ minimum batch size (if allocated), and quality requirements met.
**Validates: Requirements 3.3, 3.4, 9.2, 17.4**

### Property 7: Optimization Performance
*For any* optimization problem with up to 50 farmers and 5 processors, the MILP solver should complete within 5 seconds.
**Validates: Requirements 3.5**

### Property 8: Processing Diversion Preference
*For any* two allocation solutions with equal total revenue, the solution with higher processing volume should be preferred.
**Validates: Requirements 3.6**

### Property 9: Blended Price Calculation
*For any* farmer allocation with fresh quantity Qf at price Pf and processing quantity Qp at price Pp, the blended price should equal (Qf × Pf + Qp × Pp) / (Qf + Qp).
**Validates: Requirements 4.1**

### Property 10: Revenue Calculation
*For any* farmer allocation, total expected revenue should equal the sum of (quantity × price) across all allocation destinations.
**Validates: Requirements 4.2**

### Property 11: Benefit Calculation
*For any* farmer with blended revenue R and crash scenario revenue C, the benefit should equal R - C.
**Validates: Requirements 4.4**

### Property 12: Currency Formatting
*For any* currency value displayed to users, it should be formatted with ₹ symbol and appropriate thousand separators (e.g., ₹63,200).
**Validates: Requirements 4.6**

### Property 13: Processor Message Completeness
*For any* WhatsApp message sent to a processor, it should contain: crop type, total quantity offered, quality indicators, pickup timeframe, FPO location, and contract rate.
**Validates: Requirements 5.2, 10.4**

### Property 14: Language Preference Matching
*For any* processor with language preference L (Hindi or English), messages sent to that processor should be in language L.
**Validates: Requirements 5.3**

### Property 15: Reallocation Trigger on Decline
*For any* processor that declines an allocation or does not respond within 4 hours, reallocation should be triggered.
**Validates: Requirements 5.5, 12.1**

### Property 16: Allocation Notification
*For any* completed allocation plan, the Sell Agent should receive farmer assignment notifications.
**Validates: Requirements 6.2**

### Property 17: Safe Volume Update
*For any* processing diversion of volume D from fresh market, the updated safe volume provided to Sell Agent should reflect the reduction.
**Validates: Requirements 6.5**

### Property 18: Contract Creation on Confirmation
*For any* farmer confirmation of processing allocation, a processing contract record should be created.
**Validates: Requirements 7.1**

### Property 19: Contract Data Completeness
*For any* processing contract record, it should contain: farmer ID, processor ID, crop type, quantity, agreed rate, pickup time, expected payment time, and payment terms.
**Validates: Requirements 7.2**

### Property 20: Price Protection Validation
*For any* allocation with processing diversion, the expected fresh market price should be within 10% of the forecasted stable price.
**Validates: Requirements 8.3**

### Property 21: Minimum Batch Size Enforcement
*For any* processor allocation in the solution, the allocated quantity should be greater than or equal to that processor's minimum batch size.
**Validates: Requirements 9.2**

### Property 22: Batch Size Exclusion
*For any* processor with minimum batch size M and available surplus S where S < M, that processor should not receive any allocation.
**Validates: Requirements 9.3**

### Property 23: Quality Matching
*For any* farmer allocated to a processor, the farmer's quality indicators should meet or exceed the processor's quality requirements.
**Validates: Requirements 10.2**

### Property 24: Quality-Based Exclusion
*For any* farmer whose quality indicators do not meet a processor's requirements, that farmer should not be allocated to that processor.
**Validates: Requirements 10.3**

### Property 25: Net Processing Price Calculation
*For any* processor with contract rate R, transport cost T, and quantity Q, the net processing price should equal R - (T / Q).
**Validates: Requirements 11.2**

### Property 26: Profitability Filter
*For any* processor where net processing price is less than fresh market price, no allocation should be made to that processor.
**Validates: Requirements 11.4**

### Property 27: Shared Transport Cost
*For any* multiple farmers allocated to the same processor, the transport cost should be divided among them proportionally.
**Validates: Requirements 11.5**

### Property 28: Reallocation Exclusion
*For any* reallocation triggered by processor decline, the MILP optimization should exclude the declined processor from consideration.
**Validates: Requirements 12.2**

### Property 29: Reallocation Performance
*For any* reallocation event, the reallocation process should complete within 2 minutes.
**Validates: Requirements 12.6**

### Property 30: Independent Crop Detection
*For any* FPO with multiple crop types, surplus detection should run independently for each crop type.
**Validates: Requirements 14.1**

### Property 31: Message Aggregation for Multi-Crop
*For any* processor receiving allocations for multiple crop types, all crop offers should be aggregated into a single WhatsApp message.
**Validates: Requirements 14.4**

### Property 32: Crash Risk Prioritization
*For any* multiple crops with surplus, crops with higher crash risk (higher percentage over threshold) should be prioritized for processing allocation.
**Validates: Requirements 14.5**

### Property 33: Comprehensive Audit Logging
*For any* system event (surplus detection, optimization run, processor communication, allocation change), a corresponding audit log entry should exist with timestamp and full context.
**Validates: Requirements 5.6, 9.6, 10.5, 15.1, 15.2, 15.3, 15.4, 16.6, 19.5**

### Property 34: Audit Log Retention
*For any* audit log entry, it should be retained for at least 7 years.
**Validates: Requirements 15.6**

### Property 35: Rolling Average Capacity
*For any* absorption capacity calculation, it should use a rolling 90-day average of mandi arrivals.
**Validates: Requirements 16.2**

### Property 36: Seasonal Adjustment Application
*For any* absorption capacity calculation, seasonal adjustment factors should be applied based on the date.
**Validates: Requirements 16.3**

### Property 37: Farmer Preference Respect
*For any* farmer with "fresh market only" preference, that farmer should not be allocated to processing.
**Validates: Requirements 17.2**

### Property 38: Premium-Only Conditional Allocation
*For any* farmer with "processing only if premium" preference, allocation to processing should only occur if processing rate exceeds fresh market net price.
**Validates: Requirements 17.3**

### Property 39: Surplus Detection Performance
*For any* FPO with up to 500 farmers, surplus detection should complete within 10 seconds.
**Validates: Requirements 18.1**

### Property 40: Concurrent FPO Processing
*For any* multiple FPOs triggering surplus detection simultaneously, the system should process them concurrently without interference.
**Validates: Requirements 18.3**

### Property 41: Capacity Data Caching
*For any* processor capacity query, the result should be cached and reused within a 24-hour window.
**Validates: Requirements 2.6, 18.4**

### Property 42: WhatsApp Rate Limiting
*For any* sequence of WhatsApp API calls, the rate should not exceed the configured rate limit.
**Validates: Requirements 18.6**

### Property 43: MILP Solver Fallback
*For any* MILP optimization that fails to find a solution within timeout, the system should fall back to rule-based proportional allocation.
**Validates: Requirements 19.1**

### Property 44: Graceful Degradation on Service Failure
*For any* external service failure (processor database, Market Data Pipeline, WhatsApp API), the system should use cached data or fallback mechanisms and continue operation with appropriate warnings.
**Validates: Requirements 19.2, 19.4**

### Property 45: Exponential Backoff Retry
*For any* WhatsApp API failure, the system should retry with exponentially increasing delays before falling back to SMS.
**Validates: Requirements 19.3**

### Property 46: Lambda Execution Timeout
*For any* Process Agent execution, it should complete within the Lambda timeout limit of 15 minutes.
**Validates: Requirements 20.4**

## Error Handling

### Error Categories

**1. Optimization Failures**
- MILP solver timeout (>5 seconds) → Fall back to rule-based proportional allocation
- No feasible solution found → Relax constraints incrementally (quality, then batch size, then transport)
- Infeasible constraints → Alert FPO coordinator, route all to fresh market

**2. External Service Failures**
- Processor database unavailable → Use cached capacity data (max 24 hours old), alert coordinator
- Market Data Pipeline unavailable → Use cached absorption capacity with staleness warning
- WhatsApp API failure → Retry with exponential backoff (1s, 2s, 4s), fall back to SMS
- EventBridge delivery failure → Retry with dead-letter queue for manual intervention

**3. Data Quality Issues**
- Missing processor capacity → Exclude processor from allocation, log warning
- Stale market data (>24 hours) → Proceed with warning flag, increase safety margin
- Invalid farmer quality indicators → Exclude from processing allocation, route to fresh market
- Conflicting farmer preferences → Default to most conservative (fresh market only)

**4. Coordination Failures**
- Sell Agent not responding → Timeout after 30 seconds, proceed with allocation
- Processor response parsing failure → Request explicit confirmation via structured menu
- Multiple processor declines → Expand fresh market allocation, alert coordinator
- Reallocation loop (>3 iterations) → Break loop, route remaining to fresh market

**5. Performance Issues**
- Optimization taking >5 seconds → Terminate and use fallback allocation
- Concurrent FPO processing causing resource contention → Queue requests with priority
- Database connection pool exhausted → Retry with exponential backoff, circuit breaker after 3 failures
- Memory limit exceeded in Lambda → Reduce problem size by splitting into batches

### Error Recovery Strategies

**Retry with Backoff:**
- Network failures: 3 retries with exponential backoff (1s, 2s, 4s)
- Database deadlocks: 5 retries with jitter to avoid thundering herd
- API rate limits: Respect Retry-After header, queue requests

**Graceful Degradation:**
- Processor database unavailable → Use cached data, route to fresh market if cache expired
- MILP solver fails → Use rule-based allocation (proportional distribution)
- Quality matching unavailable → Skip quality constraints, include warning in processor message

**Circuit Breaker:**
- After 3 consecutive failures to external service, open circuit for 60 seconds
- During open circuit, use cached data or skip optional steps
- Half-open state: allow 1 test request after timeout

**Compensation:**
- If processor confirmation fails after allocation → Store allocation, retry confirmation
- If contract creation fails → Queue for async creation, alert coordinator
- If audit log write fails → Queue for async write, alert on persistent failure

## Testing Strategy

The Process Agent requires a dual testing approach combining unit tests for specific scenarios and property-based tests for universal correctness guarantees.

### Unit Testing

Unit tests focus on specific examples, edge cases, and integration points:

**Surplus Detection:**
- Test surplus detection with exact threshold boundary (volume = threshold)
- Test surplus detection with volume slightly over threshold (101% of threshold)
- Test surplus detection with multiple crops simultaneously
- Test surplus detection with stale market data

**MILP Optimization:**
- Test optimization with single farmer, single processor
- Test optimization with multiple farmers, capacity constraints binding
- Test optimization with minimum batch size constraints
- Test optimization with quality mismatches
- Test optimization with transport costs making processing unprofitable
- Test optimization fallback when solver times out

**Processor Communication:**
- Test WhatsApp message formatting in Hindi and English
- Test processor response parsing for various confirmation formats
- Test timeout handling after 4 hours
- Test reallocation trigger on decline

**Integration:**
- Test EventBridge event publishing to Sell Agent
- Test coordination with Sell Agent for farmer confirmations
- Test Market Data Pipeline integration for absorption capacity
- Test contract creation in PostgreSQL

**Error Handling:**
- Test graceful degradation when processor database unavailable
- Test fallback to cached data when Market Data Pipeline fails
- Test SMS fallback when WhatsApp API fails
- Test circuit breaker behavior after repeated failures

### Property-Based Testing

Property tests verify universal properties across all inputs using randomized test generation. Each property test should run a minimum of 100 iterations.

**Configuration:**
- Use `hypothesis` library for Python property-based testing
- Configure 100 iterations per property test
- Tag each test with feature name and property number
- Generate random but realistic test data (farmers, processors, prices, capacities)

**Property Test Examples:**

**Property 1: Volume Aggregation Invariant**
```python
@given(farmers=st.lists(st.builds(Farmer, quantity=st.floats(min_value=0.1, max_value=10.0)), min_size=1, max_size=50))
def test_volume_aggregation_invariant(farmers):
    """Feature: process-agent, Property 1: Volume aggregation equals sum of individual quantities"""
    aggregator = VolumeAggregator()
    result = aggregator.aggregate_fpo_volume(farmers)
    expected_total = sum(f.quantity for f in farmers)
    assert abs(result.total_volume - expected_total) < 0.01  # floating point tolerance
```

**Property 6: MILP Constraint Satisfaction**
```python
@given(
    farmers=st.lists(st.builds(Farmer), min_size=5, max_size=50),
    processors=st.lists(st.builds(Processor), min_size=1, max_size=5),
    safe_threshold=st.floats(min_value=10.0, max_value=100.0)
)
def test_milp_constraint_satisfaction(farmers, processors, safe_threshold):
    """Feature: process-agent, Property 6: All MILP constraints satisfied"""
    optimizer = MILPOptimizer()
    plan = optimizer.optimize_allocation(farmers, processors, safe_threshold)
    
    # Verify fresh market constraint
    fresh_volume = sum(a.quantity for a in plan.farmer_allocations if a.destination_type == "fresh_market")
    assert fresh_volume <= safe_threshold
    
    # Verify processor capacity constraints
    for proc_alloc in plan.processor_allocations:
        processor = next(p for p in processors if p.id == proc_alloc.processor_id)
        assert proc_alloc.total_quantity <= processor.available_capacity
        
    # Verify minimum batch size constraints
    for proc_alloc in plan.processor_allocations:
        processor = next(p for p in processors if p.id == proc_alloc.processor_id)
        assert proc_alloc.total_quantity >= processor.minimum_batch_size
```

**Property 9: Blended Price Calculation**
```python
@given(
    fresh_quantity=st.floats(min_value=0.0, max_value=10.0),
    fresh_price=st.floats(min_value=10.0, max_value=50.0),
    processing_quantity=st.floats(min_value=0.0, max_value=10.0),
    processing_price=st.floats(min_value=20.0, max_value=60.0)
)
def test_blended_price_calculation(fresh_quantity, fresh_price, processing_quantity, processing_price):
    """Feature: process-agent, Property 9: Blended price formula correctness"""
    assume(fresh_quantity + processing_quantity > 0)  # avoid division by zero
    
    calculator = RevenueCalculator()
    allocation = Allocation(fresh_quantity, fresh_price, processing_quantity, processing_price)
    blended = calculator.calculate_blended_price(allocation)
    
    expected = (fresh_quantity * fresh_price + processing_quantity * processing_price) / (fresh_quantity + processing_quantity)
    assert abs(blended - expected) < 0.01
```

**Property 33: Comprehensive Audit Logging**
```python
@given(
    event_type=st.sampled_from(["surplus_detection", "optimization", "processor_communication", "allocation_change"]),
    event_data=st.dictionaries(st.text(), st.text())
)
def test_comprehensive_audit_logging(event_type, event_data):
    """Feature: process-agent, Property 33: All events logged with timestamp"""
    logger = AuditLogger()
    
    # Trigger event
    if event_type == "surplus_detection":
        detector = SurplusDetector()
        detector.detect_surplus(event_data)
    # ... other event types
    
    # Verify log entry exists
    logs = logger.query_logs(event_type=event_type)
    assert len(logs) > 0
    assert logs[-1].timestamp is not None
    assert logs[-1].event_type == event_type
```

**Property 43: MILP Solver Fallback**
```python
@given(
    farmers=st.lists(st.builds(Farmer), min_size=5, max_size=50),
    processors=st.lists(st.builds(Processor), min_size=1, max_size=5)
)
def test_milp_solver_fallback(farmers, processors):
    """Feature: process-agent, Property 43: Fallback allocation when MILP fails"""
    optimizer = MILPOptimizer(timeout=0.001)  # Force timeout
    
    plan = optimizer.optimize_allocation(farmers, processors, safe_threshold=50.0)
    
    # Should still return a valid allocation plan (from fallback)
    assert plan is not None
    assert len(plan.farmer_allocations) == len(farmers)
    assert plan.status == "fallback_allocation"
```

### Testing Coverage Goals

- Unit test coverage: >85% of code paths
- Property test coverage: All 46 correctness properties implemented as property tests
- Integration test coverage: All external service integrations (EventBridge, WhatsApp, Database)
- Performance test coverage: All performance requirements (optimization time, detection time, reallocation time)
- Error handling test coverage: All error scenarios and fallback paths

### Test Data Generation

For property-based tests, generate realistic test data:

**Farmers:**
- Quantity: 0.5-10 tonnes (typical smallholder range)
- Quality indicators: Grade A/B/C, defect rate 0-20%
- Preferences: 70% accept processing, 20% fresh only, 10% premium only

**Processors:**
- Capacity: 2-20 tonnes/week
- Minimum batch: 1-5 tonnes
- Contract rates: ₹25-45/kg (higher than typical fresh market)
- Quality requirements: Grade B+ minimum, defect rate <10%

**Market Conditions:**
- Fresh market price: ₹15-35/kg
- Crash price: 40-60% of fresh market price
- Safe threshold: 15-50 tonnes
- Surplus: 0-200% over threshold

### Continuous Testing

- Run unit tests on every commit (CI/CD pipeline)
- Run property tests nightly (longer execution time)
- Run integration tests on staging environment before production deployment
- Run performance tests weekly to detect regressions
- Monitor production metrics and compare to test predictions
