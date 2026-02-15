# Requirements Document: Sell Agent

## Introduction

The Sell Agent is the core value proposition of Anna Drishti - an AI-powered agent that orchestrates the complete selling workflow for farmers. It finds the best buyers, negotiates optimal prices within guardrails, and ensures transparent, auditable transactions from harvest signal to confirmed deal and payment tracking.

## Glossary

- **Sell_Agent**: The AI orchestration system that manages the complete selling workflow
- **Farmer**: The agricultural producer who wants to sell their harvest
- **Buyer**: A verified purchaser of agricultural produce (trader, processor, or retailer)
- **Mandi**: A regulated agricultural market where produce is traded
- **Net_Price**: The effective price after subtracting transport costs from mandi price
- **Floor_Price**: The minimum acceptable price, calculated as max(production cost, lowest mandi net price)
- **Guardrails**: Hard-coded constraints that limit negotiation parameters
- **Intent**: The farmer's expressed desire to sell produce, captured via voice or text
- **Deal**: A negotiated agreement between farmer and buyer with confirmed price and terms
- **Audit_Trail**: A complete log of all state transitions and negotiation messages
- **Session**: A Redis-backed state container for multi-step workflow execution
- **Aggregation**: Combining produce from multiple nearby farmers for shared transport

## Requirements

### Requirement 1: Intent Understanding

**User Story:** As a farmer, I want to express my selling intent in Hindi via voice or text, so that the agent understands what I want to sell.

#### Acceptance Criteria

1. WHEN a farmer provides voice input in Hindi, THE Sell_Agent SHALL transcribe it to text
2. WHEN a farmer provides text input in Hindi, THE Sell_Agent SHALL parse it directly
3. WHEN the input contains crop type and readiness signal, THE Sell_Agent SHALL extract structured intent data
4. WHEN the input is ambiguous or incomplete, THE Sell_Agent SHALL prompt the farmer for clarification
5. THE Sell_Agent SHALL support common Hindi phrases for selling intent (e.g., "Mere tamatar tayyar hain, bech do")

### Requirement 2: Market Scanning

**User Story:** As a farmer, I want the agent to scan nearby mandis and calculate net prices, so that I know the best market opportunities.

#### Acceptance Criteria

1. WHEN intent is confirmed, THE Sell_Agent SHALL query 4-8 mandis within 100km radius
2. WHEN mandi prices are retrieved, THE Sell_Agent SHALL calculate transport costs for each mandi
3. WHEN transport costs are calculated, THE Sell_Agent SHALL compute Net_Price for each mandi
4. THE Sell_Agent SHALL rank mandis by Net_Price in descending order
5. WHEN no mandis are found within 100km, THE Sell_Agent SHALL notify the farmer and suggest alternatives

### Requirement 3: Yield Estimation

**User Story:** As a farmer, I want the agent to estimate my yield using satellite data, so that buyers have accurate quantity information.

#### Acceptance Criteria

1. WHEN the farmer's location is known, THE Sell_Agent SHALL query satellite data for the farm plot
2. WHEN satellite data is available, THE Sell_Agent SHALL generate a yield estimate
3. THE Sell_Agent SHALL present the yield estimate as assistive information, not definitive
4. WHEN the farmer provides their own yield estimate, THE Sell_Agent SHALL use the farmer's value
5. THE Sell_Agent SHALL include both satellite estimate and farmer estimate in buyer communications

### Requirement 4: Neighbor Aggregation

**User Story:** As a farmer, I want the agent to aggregate my produce with nearby farmers, so that we can share transport costs and get better deals.

#### Acceptance Criteria

1. WHEN yield is estimated, THE Sell_Agent SHALL identify 2-4 farmers within 10km with similar crops
2. WHEN nearby farmers are identified, THE Sell_Agent SHALL check if they have active selling intent
3. WHEN aggregation is possible, THE Sell_Agent SHALL calculate combined quantity and shared transport cost
4. THE Sell_Agent SHALL present aggregation opportunity to all participating farmers for approval
5. WHEN any farmer declines aggregation, THE Sell_Agent SHALL proceed with individual selling workflow

### Requirement 5: Buyer Outreach

**User Story:** As a farmer, I want the agent to contact verified buyers with structured offers, so that I can get competitive bids.

#### Acceptance Criteria

1. WHEN market scanning is complete, THE Sell_Agent SHALL select 3-5 verified buyers
2. WHEN buyers are selected, THE Sell_Agent SHALL send structured offers via WhatsApp Business API
3. THE Sell_Agent SHALL include crop type, quantity, quality indicators, location, and pickup timeframe in offers
4. WHEN a buyer responds, THE Sell_Agent SHALL parse the response and extract price and terms
5. WHEN no buyer responds within 4 hours, THE Sell_Agent SHALL notify the farmer and suggest next steps

### Requirement 6: Price Negotiation

**User Story:** As a farmer, I want the agent to negotiate the best price within safe limits, so that I get fair value without risk.

#### Acceptance Criteria

1. WHEN a buyer makes an offer, THE Sell_Agent SHALL calculate Floor_Price as max(production cost, lowest mandi Net_Price)
2. WHEN negotiating, THE Sell_Agent SHALL never accept a price below Floor_Price
3. WHEN a buyer's offer is above Floor_Price, THE Sell_Agent SHALL attempt to negotiate higher
4. THE Sell_Agent SHALL use Amazon Bedrock (Claude 3 Haiku) for negotiation with hard-coded guardrails
5. WHEN negotiation reaches 3 rounds without agreement, THE Sell_Agent SHALL present the best offer to the farmer
6. THE Sell_Agent SHALL log all negotiation messages to Audit_Trail

### Requirement 7: Deal Confirmation

**User Story:** As a farmer, I want to explicitly confirm any deal before it's finalized, so that I maintain control over my transactions.

#### Acceptance Criteria

1. WHEN negotiation produces a final offer, THE Sell_Agent SHALL present it to the farmer via WhatsApp
2. THE Sell_Agent SHALL include price, quantity, buyer name, pickup time, and payment terms in the presentation
3. THE Sell_Agent SHALL never finalize a deal without explicit farmer confirmation
4. WHEN the farmer provides voice confirmation in Hindi (e.g., "Haan"), THE Sell_Agent SHALL finalize the deal
5. WHEN the farmer declines, THE Sell_Agent SHALL return to buyer outreach or market scanning

### Requirement 8: Post-Transaction Tracking

**User Story:** As a farmer, I want the agent to track pickup and payment status, so that I'm alerted to any delays or issues.

#### Acceptance Criteria

1. WHEN a deal is confirmed, THE Sell_Agent SHALL create a transaction record with expected pickup and payment times
2. WHEN pickup time is reached, THE Sell_Agent SHALL prompt the farmer to confirm pickup completion
3. WHEN payment is expected, THE Sell_Agent SHALL monitor payment status
4. WHEN payment is delayed by more than 6 hours, THE Sell_Agent SHALL alert the farmer and log the delay
5. WHEN the transaction is complete, THE Sell_Agent SHALL close the session and archive the Audit_Trail

### Requirement 9: Workflow Orchestration

**User Story:** As a system operator, I want the agent to manage multi-step workflows reliably, so that farmers experience a seamless selling process.

#### Acceptance Criteria

1. THE Sell_Agent SHALL use LangGraph to orchestrate the workflow from intent to confirmation
2. THE Sell_Agent SHALL maintain Session state in Redis for all active workflows
3. WHEN a workflow step fails, THE Sell_Agent SHALL retry up to 3 times before escalating
4. WHEN a workflow is interrupted, THE Sell_Agent SHALL resume from the last successful state
5. THE Sell_Agent SHALL complete the full workflow from intent to confirmation in under 30 minutes (excluding buyer response time)

### Requirement 10: Audit and Compliance

**User Story:** As a system operator, I want complete audit trails for all transactions, so that we can ensure transparency and resolve disputes.

#### Acceptance Criteria

1. THE Sell_Agent SHALL log every state transition to Audit_Trail with timestamp and actor
2. THE Sell_Agent SHALL log all negotiation messages with buyer ID, message content, and timestamp
3. THE Sell_Agent SHALL log all farmer confirmations with voice transcription or text content
4. THE Sell_Agent SHALL store Audit_Trail records for at least 2 years
5. WHEN a dispute occurs, THE Sell_Agent SHALL provide complete Audit_Trail for the transaction

### Requirement 11: Error Handling and Graceful Degradation

**User Story:** As a farmer, I want the agent to handle errors gracefully, so that I'm not left without options when something goes wrong.

#### Acceptance Criteria

1. WHEN the Market Data Pipeline is unavailable, THE Sell_Agent SHALL use cached mandi prices with staleness warning
2. WHEN satellite data is unavailable, THE Sell_Agent SHALL proceed with farmer-provided yield estimate only
3. WHEN all buyers are unresponsive, THE Sell_Agent SHALL suggest direct mandi sale with transport options
4. WHEN WhatsApp API fails, THE Sell_Agent SHALL retry with exponential backoff up to 3 times
5. WHEN a critical error occurs, THE Sell_Agent SHALL notify the farmer and provide manual escalation contact

### Requirement 12: Communication Protocols

**User Story:** As a farmer, I want to communicate with the agent in my preferred language and channel, so that I can easily participate in the selling process.

#### Acceptance Criteria

1. THE Sell_Agent SHALL support Hindi voice input via WhatsApp voice messages
2. THE Sell_Agent SHALL support Hindi text input via WhatsApp text messages
3. THE Sell_Agent SHALL respond to farmers in Hindi via WhatsApp
4. WHEN communicating with buyers, THE Sell_Agent SHALL use structured English or Hindi based on buyer preference
5. THE Sell_Agent SHALL use WhatsApp Business API (Gupshup or Twilio) for all communications
