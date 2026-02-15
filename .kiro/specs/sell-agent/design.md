# Design Document: Sell Agent

## Overview

The Sell Agent is the core value proposition of Anna Drishti - an AI-powered orchestration system that manages the complete selling workflow for farmers from harvest signal to confirmed deal and payment tracking. It operates as a multi-step agent workflow using LangGraph for orchestration, Amazon Bedrock for constrained negotiation, and WhatsApp Business API for communication.

The agent handles:
- Voice/text intent parsing in Hindi
- Real-time market scanning across multiple mandis
- Satellite-assisted yield estimation
- Neighbor aggregation for transport efficiency
- Automated buyer outreach and price negotiation within guardrails
- Explicit farmer confirmation before deal finalization
- Post-transaction pickup and payment tracking

The system is designed to complete the full workflow from intent to confirmation in under 30 minutes (excluding buyer response time), with 100% adherence to price guardrails and mandatory farmer confirmation for all deals.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FARMER INTERFACE                              │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ WhatsApp     │  │ IVR (Amazon    │  │ SMS Alerts       │   │
│  │ (Voice/Text) │  │ Connect/Pinpoint│  │ (Confirmations)  │   │
│  └──────────────┘  └────────────────┘  └──────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│              SELL AGENT ORCHESTRATION (LangGraph)                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ State Machine Flow:                                        │ │
│  │                                                            │ │
│  │  Intent Parse → Market Scan → Yield Estimate →            │ │
│  │  Surplus Check → Neighbor Aggregate → Buyer Outreach →    │ │
│  │  Negotiate → Farmer Confirm → Track Transaction           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Session State (Redis):                                     │ │
│  │ • Current workflow step                                    │ │
│  │ • Farmer context (ID, location, crop, quantity)            │ │
│  │ • Market scan results                                      │ │
│  │ • Aggregation partners                                     │ │
│  │ • Buyer responses and negotiation history                  │ │
│  │ • Best offer pending confirmation                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                      TOOL LAYER                                  │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Intent Parser    │  │ Market Scanner   │  │ Yield        │ │
│  │ (Transcribe +    │  │ (Agmarknet API + │  │ Estimator    │ │
│  │  IndicBERT)      │  │  LightGBM)       │  │ (Sentinel-2) │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Aggregation      │  │ Buyer Matcher    │  │ Negotiation  │ │
│  │ Engine           │  │ (DB Query +      │  │ Engine       │ │
│  │ (Geospatial)     │  │  Trust Score)    │  │ (Bedrock)    │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ WhatsApp Client  │  │ Payment Tracker  │  │ Audit Logger │ │
│  │ (Gupshup/Twilio) │  │ (UPI Webhook)    │  │ (CloudWatch) │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                    DATA & EXTERNAL SERVICES                      │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ PostgreSQL       │  │ Redis            │  │ S3           │ │
│  │ (Farmers, Buyers,│  │ (Sessions,       │  │ (Satellite   │ │
│  │  Transactions)   │  │  Price Cache)    │  │  Imagery)    │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Agmarknet API    │  │ Sentinel-2       │  │ Amazon       │ │
│  │ (Mandi Prices)   │  │ (Copernicus)     │  │ Bedrock      │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Architecture (AWS)

The Sell Agent can be deployed using either AWS Step Functions or AWS Lambda with LangGraph runtime:

**Option A: AWS Step Functions**
- Each workflow step is a Lambda function
- Step Functions orchestrates the state machine
- Redis maintains session state across steps
- Best for: explicit state visualization, long-running workflows (>15 min)

**Option B: Lambda + LangGraph Runtime**
- Single Lambda function runs LangGraph agent
- LangGraph manages internal state transitions
- Redis persists state for resumability
- Best for: faster iteration, complex branching logic

For MVP, we recommend Option B (Lambda + LangGraph) for faster development and easier debugging.

## Components and Interfaces

### 1. Intent Parser

**Purpose:** Parse farmer voice or text input in Hindi to extract structured selling intent.

**Inputs:**
- Voice audio (WhatsApp voice message or IVR recording)
- Text message (WhatsApp text or SMS)
- Farmer ID (from phone number lookup)

**Outputs:**
- Structured intent: `{intent: "sell", crop: string, status: "harvest-ready" | "harvesting" | "planning", urgency: "immediate" | "this-week" | "next-week"}`
- Confidence score (0.0-1.0)
- Clarification needed flag

**Implementation:**
- Amazon Transcribe for Hindi voice-to-text (if voice input)
- IndicBERT fine-tuned model for intent classification
- Entity extraction for crop type using custom vocabulary
- Fallback to structured DTMF menu if confidence < 0.7

**Interface:**
```python
class IntentParser:
    def parse_voice(self, audio_url: str, farmer_id: str) -> Intent:
        """Transcribe and parse voice input"""
        
    def parse_text(self, text: str, farmer_id: str) -> Intent:
        """Parse text input directly"""
        
    def needs_clarification(self, intent: Intent) -> bool:
        """Check if clarification is needed"""
```

### 2. Market Scanner

**Purpose:** Scan nearby mandis for current prices and calculate net prices after transport costs.

**Inputs:**
- Farmer location (lat/lon from farmer profile)
- Crop type
- Estimated quantity
- Search radius (default: 100km)

**Outputs:**
- List of mandis with: name, distance, current price, arrivals, transport cost, net price
- Price trend forecast (48-hour LightGBM prediction)
- Recommended target mandis (top 2-3 by net price)

**Implementation:**
- Query Agmarknet API for last 24-hour prices
- Calculate transport cost: base rate (₹15/km) + quantity factor
- Compute net price: mandi_price - (transport_cost / quantity)
- Run LightGBM model for 48-hour price forecast
- Cache results in Redis with 1-hour TTL

**Interface:**
```python
class MarketScanner:
    def scan_mandis(self, location: Location, crop: str, quantity: float, radius_km: int = 100) -> List[MandiResult]:
        """Scan mandis within radius and calculate net prices"""
        
    def forecast_price(self, mandi_id: str, crop: str, hours_ahead: int = 48) -> PriceForecast:
        """Forecast price trend using LightGBM"""
```

### 3. Yield Estimator

**Purpose:** Provide assistive yield estimation using satellite data (not definitive).

**Inputs:**
- Farmer plot ID
- Crop type
- Current date

**Outputs:**
- Satellite-based yield estimate (tonnes)
- Confidence level (low/medium/high based on cloud cover and data recency)
- NDVI trajectory data
- Data staleness (days since last satellite pass)

**Implementation:**
- Query Sentinel-2 imagery from S3 (pre-downloaded via scheduled Lambda)
- Calculate NDVI from Red and NIR bands
- Compare NDVI trajectory to regional crop stage patterns
- Estimate yield: plot_area × regional_yield_avg × ndvi_factor
- Mark as "assistive only" - farmer's estimate takes precedence

**Interface:**
```python
class YieldEstimator:
    def estimate_yield(self, plot_id: str, crop: str) -> YieldEstimate:
        """Estimate yield from satellite data"""
        
    def get_ndvi_trajectory(self, plot_id: str, days_back: int = 30) -> List[NDVIPoint]:
        """Get NDVI time series for plot"""
```

### 4. Aggregation Engine

**Purpose:** Identify nearby farmers with compatible produce for shared transport.

**Inputs:**
- Farmer ID and location
- Crop type
- Estimated quantity
- Target mandi/buyer location
- Search radius (default: 10km)

**Outputs:**
- List of compatible farmers (2-4 max)
- Combined quantity
- Shared transport cost per farmer
- Cost savings percentage

**Implementation:**
- Geospatial query: farmers within radius with active selling intent
- Filter by crop compatibility (same crop or compatible transport requirements)
- Filter by timing: harvest-ready within same 2-day window
- Calculate shared transport cost: total_cost / num_farmers
- Require explicit confirmation from each farmer

**Interface:**
```python
class AggregationEngine:
    def find_aggregation_partners(self, farmer_id: str, crop: str, quantity: float, target_location: Location) -> AggregationGroup:
        """Find nearby farmers for aggregation"""
        
    def calculate_shared_cost(self, farmers: List[str], total_quantity: float, target_location: Location) -> float:
        """Calculate per-farmer transport cost"""
```

### 5. Buyer Matcher

**Purpose:** Select verified buyers to contact based on crop, location, and trust score.

**Inputs:**
- Crop type
- Quantity
- Farmer/aggregation location
- Target mandi locations (from market scan)

**Outputs:**
- List of 3-5 verified buyers
- Buyer profiles: name, contact, trust score, typical price range, payment terms
- Prioritization order (by trust score and location match)

**Implementation:**
- Query buyers from database filtered by crop type
- Calculate distance from farmer location
- Filter by capacity: buyer's typical purchase volume >= quantity
- Sort by trust score (derived from transaction history)
- Limit to 3-5 buyers to avoid spam

**Interface:**
```python
class BuyerMatcher:
    def match_buyers(self, crop: str, quantity: float, location: Location, max_buyers: int = 5) -> List[Buyer]:
        """Match and rank buyers for outreach"""
        
    def get_trust_score(self, buyer_id: str) -> float:
        """Get buyer reliability score (0.0-1.0)"""
```

### 6. Negotiation Engine

**Purpose:** Conduct price negotiation with buyers via WhatsApp within hard-coded guardrails.

**Inputs:**
- Buyer ID and contact
- Structured offer: crop, quantity, quality, location, pickup timeframe
- Floor price (calculated from production cost and lowest mandi net price)
- Market context (current mandi prices, forecast)

**Outputs:**
- Negotiation transcript (all messages)
- Final offer (if agreement reached)
- Negotiation status: "agreed" | "ongoing" | "failed" | "timeout"

**Implementation:**
- Use Amazon Bedrock (Claude 3 Haiku) with constrained prompts
- Hard constraints enforced in code (not just prompt):
  - Never accept price < floor_price
  - Never commit without farmer confirmation
  - Maximum 3 negotiation rounds
  - Timeout after 4 hours of buyer non-response
- Template-based message generation with variable insertion
- All messages logged to audit trail

**Guardrails:**
```python
class NegotiationGuardrails:
    floor_price: float  # HARD MINIMUM - cannot be overridden
    max_rounds: int = 3
    timeout_hours: int = 4
    
    def validate_offer(self, offer_price: float) -> bool:
        """Ensure offer meets floor price"""
        return offer_price >= self.floor_price
```

**Interface:**
```python
class NegotiationEngine:
    def send_initial_offer(self, buyer: Buyer, offer: Offer, floor_price: float) -> str:
        """Send structured offer to buyer via WhatsApp"""
        
    def handle_buyer_response(self, buyer_id: str, message: str, context: NegotiationContext) -> NegotiationResponse:
        """Process buyer response and generate counter-offer"""
        
    def finalize_negotiation(self, buyer_id: str, agreed_price: float) -> Deal:
        """Create tentative deal (pending farmer confirmation)"""
```

### 7. Confirmation Handler

**Purpose:** Present deal to farmer and obtain explicit voice confirmation.

**Inputs:**
- Farmer ID
- Best deal: buyer, price, quantity, pickup time, payment terms
- Alternative deals (if any)

**Outputs:**
- Confirmation status: "confirmed" | "declined" | "needs-clarification"
- Audio recording reference (for audit)
- Timestamp

**Implementation:**
- Generate Hindi confirmation message with all deal details
- Send via IVR callback or WhatsApp voice message
- Parse farmer response: "Haan" (yes) or "Naa" (no)
- Require explicit affirmative - silence or unclear response = no confirmation
- Store audio reference in S3 and link in transaction record

**Interface:**
```python
class ConfirmationHandler:
    def present_deal(self, farmer_id: str, deal: Deal, alternatives: List[Deal] = None) -> str:
        """Generate and send confirmation request"""
        
    def parse_confirmation(self, audio_url: str) -> ConfirmationResult:
        """Parse farmer's confirmation response"""
        
    def finalize_deal(self, deal_id: str, confirmation: ConfirmationResult) -> Transaction:
        """Create confirmed transaction record"""
```

### 8. Transaction Tracker

**Purpose:** Track pickup completion and payment status post-confirmation.

**Inputs:**
- Transaction ID
- Expected pickup time
- Expected payment time
- Payment method (UPI, bank transfer, cash)

**Outputs:**
- Pickup status: "pending" | "completed" | "delayed"
- Payment status: "pending" | "received" | "delayed" | "failed"
- Alerts triggered (if delays exceed thresholds)

**Implementation:**
- Create transaction record with expected times
- Schedule pickup reminder at expected pickup time
- Prompt farmer to confirm pickup completion
- Monitor payment webhook (for UPI) or manual confirmation
- Trigger alert if payment delayed > 6 hours
- Escalate to FPO coordinator if payment delayed > 24 hours

**Interface:**
```python
class TransactionTracker:
    def create_transaction(self, deal: Deal, confirmation: ConfirmationResult) -> Transaction:
        """Create transaction record with tracking"""
        
    def update_pickup_status(self, transaction_id: str, status: str, timestamp: datetime) -> None:
        """Update pickup status"""
        
    def update_payment_status(self, transaction_id: str, status: str, amount: float, timestamp: datetime) -> None:
        """Update payment status"""
        
    def check_delays(self, transaction_id: str) -> List[Alert]:
        """Check for pickup or payment delays"""
```

## Data Models

### Intent
```python
class Intent:
    intent_type: str  # "sell" | "buy" | "query"
    crop: str
    status: str  # "harvest-ready" | "harvesting" | "planning"
    urgency: str  # "immediate" | "this-week" | "next-week"
    quantity_estimate: Optional[float]  # if provided by farmer
    confidence: float  # 0.0-1.0
    needs_clarification: bool
    raw_text: str
    farmer_id: str
    timestamp: datetime
```

### MandiResult
```python
class MandiResult:
    mandi_id: str
    mandi_name: str
    distance_km: float
    current_price: float  # ₹/kg
    arrivals_today: float  # tonnes
    transport_cost: float  # ₹ total
    net_price: float  # ₹/kg after transport
    price_forecast_48h: Optional[float]
    data_timestamp: datetime
```

### YieldEstimate
```python
class YieldEstimate:
    plot_id: str
    crop: str
    estimated_yield: float  # tonnes
    confidence: str  # "low" | "medium" | "high"
    ndvi_current: float
    ndvi_trajectory: List[float]
    data_staleness_days: int
    is_assistive: bool = True  # Always true - not definitive
    farmer_override: Optional[float]  # Farmer's own estimate
```

### AggregationGroup
```python
class AggregationGroup:
    primary_farmer_id: str
    partner_farmer_ids: List[str]
    crop: str
    total_quantity: float
    individual_quantities: Dict[str, float]
    shared_transport_cost: float
    cost_per_farmer: Dict[str, float]
    savings_percentage: float
    target_location: Location
    all_confirmed: bool
```

### Offer
```python
class Offer:
    crop: str
    quantity: float
    quality_indicators: Dict[str, Any]
    location: Location
    pickup_timeframe: str  # "tomorrow 6 AM" | "within 48 hours"
    floor_price: float
    market_context: str  # "Pune mandi ₹28/kg today"
```

### NegotiationContext
```python
class NegotiationContext:
    buyer_id: str
    offer: Offer
    floor_price: float
    current_round: int
    max_rounds: int
    messages: List[Message]
    best_offer_so_far: Optional[float]
    timeout_at: datetime
```

### Deal
```python
class Deal:
    deal_id: str
    farmer_id: str
    buyer_id: str
    crop: str
    quantity: float
    agreed_price: float  # ₹/kg
    total_value: float  # ₹
    pickup_time: datetime
    payment_terms: str
    payment_method: str
    is_aggregated: bool
    aggregation_group_id: Optional[str]
    status: str  # "tentative" | "confirmed" | "completed" | "cancelled"
    created_at: datetime
```

### Transaction
```python
class Transaction:
    transaction_id: str
    deal_id: str
    farmer_id: str
    buyer_id: str
    crop: str
    quantity: float
    price_per_kg: float
    total_value: float
    confirmation_audio_url: str
    confirmation_timestamp: datetime
    expected_pickup_time: datetime
    actual_pickup_time: Optional[datetime]
    pickup_status: str  # "pending" | "completed" | "delayed"
    expected_payment_time: datetime
    actual_payment_time: Optional[datetime]
    payment_status: str  # "pending" | "received" | "delayed" | "failed"
    payment_amount: Optional[float]
    created_at: datetime
    updated_at: datetime
```

### Session State
```python
class SellAgentSession:
    session_id: str
    farmer_id: str
    current_step: str  # "intent" | "market_scan" | "yield" | "aggregate" | "outreach" | "negotiate" | "confirm" | "track"
    intent: Optional[Intent]
    market_results: Optional[List[MandiResult]]
    yield_estimate: Optional[YieldEstimate]
    aggregation_group: Optional[AggregationGroup]
    contacted_buyers: List[str]
    negotiations: Dict[str, NegotiationContext]
    best_deal: Optional[Deal]
    alternative_deals: List[Deal]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Voice transcription completeness
*For any* Hindi voice input provided by a farmer, the system should transcribe it to text with identifiable content.
**Validates: Requirements 1.1**

### Property 2: Text parsing completeness
*For any* Hindi text input provided by a farmer, the system should parse it and extract intent information.
**Validates: Requirements 1.2**

### Property 3: Entity extraction accuracy
*For any* input containing crop type and readiness signal, the system should extract structured intent data with both crop and status fields populated.
**Validates: Requirements 1.3**

### Property 4: Clarification on ambiguity
*For any* ambiguous or incomplete input (confidence < 0.7), the system should prompt the farmer for clarification rather than proceeding with uncertain intent.
**Validates: Requirements 1.4**

### Property 5: Mandi query count constraint
*For any* confirmed intent with farmer location, the system should query between 4 and 8 mandis within 100km radius.
**Validates: Requirements 2.1**

### Property 6: Transport cost calculation
*For any* mandi at a known distance, the system should calculate transport cost based on distance and quantity.
**Validates: Requirements 2.2**

### Property 7: Net price calculation
*For any* mandi with price P and transport cost T for quantity Q, the net price should equal P - (T / Q).
**Validates: Requirements 2.3**

### Property 8: Mandi ranking by net price
*For any* list of mandi results, the output should be sorted in descending order by net_price.
**Validates: Requirements 2.4**

### Property 9: Satellite yield estimation
*For any* farmer plot with available satellite data, the system should generate a yield estimate marked as assistive (not definitive).
**Validates: Requirements 3.1, 3.2**

### Property 10: Farmer estimate priority
*For any* yield estimation where the farmer provides their own estimate, the farmer's value should be used in all downstream calculations and communications.
**Validates: Requirements 3.4**

### Property 11: Dual estimate communication
*For any* buyer communication where both satellite and farmer estimates exist, both values should be included in the message.
**Validates: Requirements 3.5**

### Property 12: Neighbor identification bounds
*For any* farmer with estimated yield, the system should identify between 2 and 4 farmers within 10km with similar crops and active selling intent.
**Validates: Requirements 4.1, 4.2**

### Property 13: Aggregation quantity invariant
*For any* aggregation group, the combined quantity should equal the sum of individual farmer quantities.
**Validates: Requirements 4.3**

### Property 14: Shared cost calculation
*For any* aggregation group with N farmers and total transport cost T, each farmer's cost should be T / N.
**Validates: Requirements 4.3**

### Property 15: Aggregation opt-out fallback
*For any* aggregation group where at least one farmer declines, the system should proceed with individual selling workflow for all farmers.
**Validates: Requirements 4.5**

### Property 16: Buyer selection count
*For any* completed market scan, the system should select between 3 and 5 verified buyers for outreach.
**Validates: Requirements 5.1**

### Property 17: Offer message completeness
*For any* offer sent to a buyer, the message should contain crop type, quantity, quality indicators, location, and pickup timeframe.
**Validates: Requirements 5.3, 7.2**

### Property 18: Buyer response parsing
*For any* buyer response message, the system should extract price and terms information.
**Validates: Requirements 5.4**

### Property 19: Floor price calculation
*For any* negotiation context with production cost C and mandi net prices [P1, P2, ..., Pn], the floor price should equal max(C, min(P1, P2, ..., Pn)).
**Validates: Requirements 6.1**

### Property 20: Floor price enforcement (CRITICAL INVARIANT)
*For any* negotiation, all accepted offers must have price >= floor_price. The system should never accept a price below the floor price.
**Validates: Requirements 6.2**

### Property 21: Counter-offer on above-floor offers
*For any* buyer offer with price > floor_price and negotiation round < max_rounds, the system should attempt to negotiate higher.
**Validates: Requirements 6.3**

### Property 22: Negotiation round limit
*For any* negotiation that reaches 3 rounds without agreement, the system should present the best offer to the farmer rather than continuing negotiation.
**Validates: Requirements 6.5**

### Property 23: Comprehensive audit logging
*For any* state transition, negotiation message, or farmer confirmation, a corresponding audit log entry should exist with timestamp, actor, and content.
**Validates: Requirements 6.6, 10.1, 10.2, 10.3**

### Property 24: Deal presentation on final offer
*For any* final offer from negotiation, the system should present it to the farmer via WhatsApp with all deal details.
**Validates: Requirements 7.1**

### Property 25: No deal finalization without confirmation (CRITICAL INVARIANT)
*For any* finalized deal, there must exist a farmer confirmation record with audio reference or text content and timestamp.
**Validates: Requirements 7.3**

### Property 26: Deal finalization on valid confirmation
*For any* valid farmer confirmation ("Haan" or equivalent affirmative), the system should finalize the deal and create a transaction record.
**Validates: Requirements 7.4**

### Property 27: Transaction creation completeness
*For any* confirmed deal, a transaction record should be created with expected pickup time and expected payment time populated.
**Validates: Requirements 8.1**

### Property 28: Payment delay alerting
*For any* transaction where actual payment time exceeds expected payment time by more than 6 hours, an alert should be triggered and logged.
**Validates: Requirements 8.4**

### Property 29: Transaction completion cleanup
*For any* transaction marked as complete, the associated session should be closed and the audit trail should be archived.
**Validates: Requirements 8.5**

### Property 30: Session state persistence
*For any* active workflow, a session record should exist in Redis with current step, farmer context, and workflow data.
**Validates: Requirements 9.2**

### Property 31: Retry on failure
*For any* workflow step that fails, the system should retry up to 3 times before escalating to error handling.
**Validates: Requirements 9.3**

### Property 32: Workflow resumability
*For any* interrupted workflow, resuming should continue from the last successfully completed step stored in session state.
**Validates: Requirements 9.4**

### Property 33: Audit trail retrieval completeness
*For any* transaction ID, the system should be able to retrieve the complete audit trail including all state transitions, messages, and confirmations.
**Validates: Requirements 10.5**

### Property 34: Exponential backoff retry
*For any* WhatsApp API failure, the system should retry with exponentially increasing delays (e.g., 1s, 2s, 4s) up to 3 times.
**Validates: Requirements 11.4**

### Property 35: Critical error notification
*For any* critical error that prevents workflow completion, the system should notify the farmer and provide escalation contact information.
**Validates: Requirements 11.5**

### Property 36: Farmer communication language
*For any* message sent to a farmer, the language should be Hindi.
**Validates: Requirements 12.3**

### Property 37: Buyer communication language preference
*For any* message sent to a buyer, the language should match the buyer's stored language preference (Hindi or English).
**Validates: Requirements 12.4**

## Error Handling

### Error Categories

**1. External Service Failures**
- Agmarknet API unavailable → Use cached prices with staleness warning (max 24 hours old)
- Sentinel-2 satellite data unavailable → Proceed with farmer-provided estimate only
- WhatsApp API failure → Retry with exponential backoff (1s, 2s, 4s), then escalate
- Amazon Bedrock timeout → Use template-based fallback message, log incident

**2. Data Quality Issues**
- Ambiguous intent (confidence < 0.7) → Prompt farmer for clarification via structured menu
- Missing farmer location → Request location via WhatsApp or use FPO default location
- No mandis within 100km → Notify farmer, suggest expanding radius or direct processor contact
- No verified buyers available → Fall back to mandi sale recommendation

**3. Workflow Failures**
- All buyers unresponsive (4-hour timeout) → Suggest direct mandi sale with transport options
- Aggregation partner declines → Proceed with individual workflow for all farmers
- Negotiation fails (3 rounds, no agreement) → Present best offer to farmer for decision
- Payment delayed > 24 hours → Escalate to FPO coordinator, mark buyer reliability score

**4. Critical Errors**
- Database connection failure → Retry with exponential backoff, circuit breaker after 3 failures
- Redis session store unavailable → Fall back to stateless operation, warn about no resumability
- Farmer confirmation parsing failure → Request explicit "Haan" or "Naa" via DTMF menu
- Transaction creation failure → Roll back all related operations, notify farmer of technical issue

### Error Recovery Strategies

**Retry with Backoff:**
- Network failures: 3 retries with exponential backoff (1s, 2s, 4s)
- Database deadlocks: 5 retries with jitter to avoid thundering herd
- API rate limits: Respect Retry-After header, queue requests

**Graceful Degradation:**
- Satellite data unavailable → Continue without yield estimate
- Price forecast unavailable → Use current prices only
- Buyer trust scores unavailable → Use all verified buyers equally

**Circuit Breaker:**
- After 3 consecutive failures to external service, open circuit for 60 seconds
- During open circuit, use cached data or skip optional steps
- Half-open state: allow 1 test request after timeout

**Compensation:**
- If deal finalization fails after farmer confirmation → Store confirmation, retry finalization
- If payment tracking fails → Manual reconciliation by FPO coordinator
- If audit log write fails → Queue for async write, alert on persistent failure

## Testing Strategy

### Dual Testing Approach

The Sell Agent requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of intent parsing (e.g., "Mere tamatar tayyar hain")
- Edge cases (no mandis found, all buyers unresponsive, payment delayed)
- Error conditions (API failures, invalid data, timeout scenarios)
- Integration points (WhatsApp API, Bedrock, database transactions)

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs (e.g., floor price enforcement, net price calculation)
- Comprehensive input coverage through randomization (random locations, quantities, prices)
- Invariants that must hold across all executions (e.g., audit logging, no deal without confirmation)

Together, unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

### Property-Based Testing Configuration

**Framework:** Use `hypothesis` (Python) for property-based testing

**Test Configuration:**
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: sell-agent, Property {number}: {property_text}`

**Example Property Test Structure:**
```python
from hypothesis import given, strategies as st

@given(
    mandi_price=st.floats(min_value=1.0, max_value=100.0),
    transport_cost=st.floats(min_value=100.0, max_value=10000.0),
    quantity=st.floats(min_value=100.0, max_value=10000.0)
)
def test_net_price_calculation(mandi_price, transport_cost, quantity):
    """
    Feature: sell-agent, Property 7: Net price calculation
    For any mandi with price P and transport cost T for quantity Q,
    the net price should equal P - (T / Q).
    """
    net_price = calculate_net_price(mandi_price, transport_cost, quantity)
    expected = mandi_price - (transport_cost / quantity)
    assert abs(net_price - expected) < 0.01  # Allow for floating point precision
```

### Critical Properties Requiring Extra Validation

**Property 20: Floor price enforcement**
- This is a CRITICAL INVARIANT that protects farmers from bad deals
- Test with adversarial inputs: prices just below floor, prices far below floor
- Verify enforcement at code level (not just LLM prompt level)
- Include integration tests with actual Bedrock calls

**Property 25: No deal finalization without confirmation**
- This is a CRITICAL INVARIANT that ensures farmer control
- Test all code paths that could finalize deals
- Verify database constraints prevent deals without confirmation records
- Include negative tests: attempt to finalize without confirmation should fail

**Property 23: Comprehensive audit logging**
- Critical for dispute resolution and compliance
- Test that ALL state transitions create audit entries
- Verify audit entries are immutable (append-only)
- Test audit trail retrieval for complex multi-step workflows

### Integration Testing

**End-to-End Workflow Tests:**
1. Happy path: Intent → Market scan → Aggregation → Negotiation → Confirmation → Tracking
2. Buyer timeout path: Intent → Market scan → Buyer outreach → Timeout → Mandi fallback
3. Aggregation decline path: Intent → Aggregation proposed → Partner declines → Individual workflow
4. Payment delay path: Confirmed deal → Pickup complete → Payment delayed → Alert triggered

**External Service Mocking:**
- Mock Agmarknet API with realistic price data
- Mock Sentinel-2 satellite data with NDVI time series
- Mock WhatsApp API for message sending/receiving
- Mock Amazon Bedrock with template-based responses for deterministic testing

**Performance Testing:**
- Workflow completion time: < 30 minutes (excluding buyer response time)
- API response time: < 200ms for reads, < 500ms for writes
- Concurrent sessions: Support 100+ active workflows per FPO
- Database transaction throughput: > 50 transactions/second

### Test Data Generation

**Realistic Test Data:**
- Farmer profiles: 500 farmers across 5 FPOs in Maharashtra
- Mandi prices: 3 years of historical Agmarknet data for tomato, onion, chili
- Buyer profiles: 20 verified buyers with varying trust scores
- Satellite imagery: Pre-downloaded Sentinel-2 tiles for Nashik district

**Synthetic Data for Property Tests:**
- Random farmer locations within Maharashtra bounds
- Random crop types from supported list
- Random quantities (100kg - 10,000kg)
- Random prices (₹5/kg - ₹100/kg)
- Random dates within agricultural seasons

### Monitoring and Observability

**Key Metrics to Track:**
- Workflow completion rate (target: > 95%)
- Average workflow duration (target: < 30 minutes)
- Floor price violation rate (target: 0%)
- Deals finalized without confirmation (target: 0%)
- Payment delay rate (target: < 10%)
- Buyer response rate (target: > 70%)
- Farmer confirmation rate (target: > 80%)

**Alerting Thresholds:**
- Floor price violation: Immediate alert (P0)
- Deal without confirmation: Immediate alert (P0)
- Workflow failure rate > 10%: Alert within 5 minutes (P1)
- Payment delay rate > 20%: Alert within 1 hour (P2)
- External service unavailable > 15 minutes: Alert (P2)
