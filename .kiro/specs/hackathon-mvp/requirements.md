# Hackathon MVP Requirements

## Introduction

This is a **48-hour hackathon MVP** designed to win by demonstrating the core Anna Drishti value proposition: AI agents that negotiate sales and prevent market crashes through processing diversion. This spec focuses on **demo impact over production readiness**.

## Strategic Focus: What Wins Hackathons

1. **Live Demo Magic** - Real AI negotiation happening on stage
2. **Emotional Resonance** - Show the ₹26,400 income difference for one farmer
3. **Technical Depth** - Prove the LLM negotiation + processing math works
4. **Visual Impact** - Dashboard showing agent actions in real-time
5. **Honest Scope** - Clearly label what's simulated vs. real

## Core Demo Flow (12 Minutes)

```
Minute 0-2: Problem setup (farmer distress, agency gap)
Minute 2-7: LIVE DEMO - Sell Agent negotiation
Minute 7-9: Processing Pivot visualization
Minute 9-10: Game Theory simulation
Minute 10-12: Roadmap + close
```

## MVP Requirements

### Requirement 1: Simulated Farmer Input

**User Story:** As a demo presenter, I want to trigger a farmer harvest signal via web form, so that I can initiate the agent workflow on stage.

#### Acceptance Criteria

1. WHEN I submit a web form with farmer name, crop type, and quantity, THE system SHALL trigger the Sell Agent workflow
2. THE form SHALL pre-populate with realistic Nashik farmer data (tomato, 2.1 acres)
3. THE system SHALL display the farmer input on the dashboard immediately

### Requirement 2: Live Market Data Scan

**User Story:** As the Sell Agent, I want to fetch real Agmarknet prices, so that the demo shows actual market data.

#### Acceptance Criteria

1. WHEN the workflow starts, THE Sell Agent SHALL query Agmarknet API for tomato prices in Maharashtra
2. THE system SHALL display prices for 4 mandis: Sinnar, Nashik, Pune, Mumbai
3. IF Agmarknet API fails, THEN THE system SHALL use cached prices from yesterday with a "cached data" indicator
4. THE system SHALL calculate net-to-farmer price (price - transport cost)

### Requirement 3: Mock Satellite Context

**User Story:** As the Sell Agent, I want to display NDVI context, so that judges see the satellite integration concept.

#### Acceptance Criteria

1. WHEN displaying farmer context, THE system SHALL show a pre-loaded NDVI chart for the plot
2. THE chart SHALL show declining NDVI trend (0.68 → 0.52) consistent with harvest readiness
3. THE system SHALL label this as "Satellite Context (Sentinel-2 simulation)"
4. THE yield estimate SHALL be calculated as: plot_area × regional_average (no NDVI adjustment for MVP)

### Requirement 4: Processing Surplus Detection

**User Story:** As the Process Agent, I want to detect surplus conditions, so that I can recommend processing diversion.

#### Acceptance Criteria

1. WHEN total FPO harvest volume exceeds 25 tonnes, THE Process Agent SHALL flag surplus risk
2. THE system SHALL calculate: FPO_total_volume = sum of all farmer inputs in current session
3. THE system SHALL display: "Surplus Detected: 30T harvest, 22T mandi capacity → 8T to processing"
4. THE system SHALL show pre-configured processor capacity: Sai Agro (5T @ ₹32/kg), Krishi Proc (2T @ ₹38/kg)

### Requirement 5: Live WhatsApp Negotiation

**User Story:** As the Sell Agent, I want to conduct a real WhatsApp negotiation with a human buyer, so that judges see the AI in action.

#### Acceptance Criteria

1. WHEN the agent identifies the best buyer, THE system SHALL send a WhatsApp message to a team member's phone (acting as buyer)
2. THE message SHALL follow the template: "Namaste [Buyer]. [Quantity] [Crop] available, [Location], [Date]. ₹[Price] minimum. Interested?"
3. WHEN the buyer responds, THE system SHALL use Bedrock Claude 3 Haiku to generate a counter-offer within guardrails
4. THE negotiation SHALL be visible on the dashboard in real-time
5. THE system SHALL enforce floor price = ₹24/kg (never go below)
6. THE negotiation SHALL conclude after 2-3 message exchanges

### Requirement 6: Farmer Confirmation Flow

**User Story:** As the Sell Agent, I want to present the deal to the farmer for confirmation, so that the demo shows human-in-the-loop control.

#### Acceptance Criteria

1. WHEN negotiation concludes, THE system SHALL display a confirmation screen with deal details
2. THE presenter SHALL click "Farmer Confirms (Haan)" button to approve the deal
3. THE system SHALL calculate blended income: (fresh_quantity × fresh_price) + (processing_quantity × processing_price)
4. THE system SHALL display income comparison: "Nearest mandi: ₹36,800 vs Anna Drishti: ₹63,200 (+₹26,400)"

### Requirement 7: Real-Time Dashboard

**User Story:** As a demo presenter, I want a visual dashboard showing agent actions, so that judges can follow the workflow.

#### Acceptance Criteria

1. THE dashboard SHALL display an activity stream showing each agent action with timestamp
2. THE dashboard SHALL show: Market Scan → Surplus Detection → Buyer Outreach → Negotiation → Confirmation
3. THE dashboard SHALL use color coding: blue for Sell Agent, green for Process Agent
4. THE dashboard SHALL display the current negotiation messages in a chat-like interface
5. THE dashboard SHALL show a "Processing Diversion" panel with surplus math

### Requirement 8: Processing Pivot Visualization

**User Story:** As a demo presenter, I want to show the counter-factual scenario, so that judges understand the crash prevention value.

#### Acceptance Criteria

1. THE system SHALL display two side-by-side scenarios:
   - Scenario A: "Without Anna Drishti" - 30T hits mandis → price crashes to ₹12/kg
   - Scenario B: "With Anna Drishti" - 7T diverted to processing → price holds at ₹25/kg
2. THE visualization SHALL show 14 farmer income bars (red vs green)
3. THE system SHALL calculate collective income difference: ₹2.1 crore vs ₹3.4 crore
4. THE visualization SHALL be triggered by clicking "Show Processing Impact" button

### Requirement 9: Game Theory Simulation

**User Story:** As a demo presenter, I want to show the pre-season planning simulation, so that judges see the intellectual depth.

#### Acceptance Criteria

1. THE system SHALL display a map with 500 farmer dots
2. WHEN clicking "Uncoordinated Planning", THE dots SHALL turn 80% red (tomato) and show price crash
3. WHEN clicking "Anna Drishti Coordination", THE dots SHALL diversify (40% tomato, 25% moong, 20% chili, 15% greens)
4. THE system SHALL display income comparison: ₹2.1 crore (uncoordinated) vs ₹3.4 crore (coordinated)
5. THE system SHALL label this as "Pre-computed simulation - Phase 2 feature"

### Requirement 10: AWS Service Integration

**User Story:** As a hackathon judge, I want to see AWS services in use, so that I can evaluate technical implementation.

#### Acceptance Criteria

1. THE system SHALL use AWS Bedrock (Claude 3 Haiku) for negotiation message generation
2. THE system SHALL use AWS Lambda for Sell Agent and Process Agent logic
3. THE system SHALL use AWS Step Functions to orchestrate the workflow (visible in AWS console)
4. THE system SHALL use AWS DynamoDB for storing farmer inputs and transaction state
5. THE system SHALL use AWS API Gateway for WhatsApp webhook integration
6. THE dashboard SHALL be deployed on AWS S3 + CloudFront

### Requirement 11: Demo Reliability

**User Story:** As a demo presenter, I want the system to work reliably on stage, so that the demo doesn't fail.

#### Acceptance Criteria

1. THE system SHALL have a "Reset Demo" button that clears all state and starts fresh
2. THE system SHALL work offline with cached Agmarknet data if internet fails
3. THE WhatsApp integration SHALL have a fallback to simulated messages if WhatsApp API is down
4. THE system SHALL complete the full workflow in under 4 minutes
5. THE system SHALL log all actions to CloudWatch for post-demo debugging

### Requirement 12: Honest Labeling

**User Story:** As a demo presenter, I want to clearly label what's simulated, so that judges trust our credibility.

#### Acceptance Criteria

1. THE dashboard SHALL display badges: "LIVE" (Bedrock negotiation, Agmarknet prices), "SIMULATED" (satellite data, processor capacity)
2. THE presenter script SHALL explicitly state: "Satellite imagery is pre-downloaded; production system pulls from Copernicus every 5 days"
3. THE game theory visualization SHALL be labeled: "Pre-computed simulation - demonstrates Phase 2 capability"
4. THE system SHALL display a "Tech Stack" panel showing which AWS services are actually running

## Out of Scope for MVP

- Real IVR integration (use web form instead)
- Real satellite API calls (use pre-loaded NDVI charts)
- Multi-farmer coordination (demo with 1 farmer, show visualization for 500)
- Payment tracking (end demo at confirmation)
- FPO coordinator authentication (public dashboard)
- Error handling beyond basic fallbacks
- Property-based testing (manual testing only)
- Production database schema (use simple DynamoDB tables)

## Success Criteria

**The demo wins if:**
1. ✅ Live Bedrock negotiation works on stage (judges see AI in action)
2. ✅ Processing math is clear and compelling (₹1.3 crore collective benefit)
3. ✅ Technical depth is evident (Step Functions, Lambda, Bedrock visible in AWS console)
4. ✅ Emotional story lands (₹26,400 difference for one farmer)
5. ✅ Honest scope builds credibility (clear about what's simulated)

**The demo fails if:**
1. ❌ WhatsApp negotiation doesn't work (have backup plan)
2. ❌ Dashboard doesn't update in real-time (judges lose the thread)
3. ❌ Processing math is confusing (practice the explanation)
4. ❌ We claim capabilities we don't have (judges see through it)
