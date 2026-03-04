# Hybrid Implementation Plan: Anna Drishti

## Overview

This is a **3-phase hybrid approach** that balances hackathon demo needs with long-term production goals:

- **Phase 1 (48 hours)**: Hackathon MVP - Win the demo
- **Phase 2 (2 weeks)**: Post-Hackathon Enhancements - Real integrations
- **Phase 3 (3 months)**: Production System - Full specs implementation

Each phase builds on the previous one, preserving all work.

---

# PHASE 1: HACKATHON MVP (48 Hours)

**Goal**: Win the hackathon with a working demo
**Scope**: ~50 tasks, minimal but impressive
**Testing**: Manual only, no automated tests

## Day 1: Core Infrastructure (Hours 1-24)

### Hour 1-4: AWS Setup & Project Structure

- [x] 1.1 Set up AWS account and configure CLI
  - Create AWS account (if needed)
  - Install and configure AWS CLI
  - Set up IAM user with admin permissions
  - Configure AWS credentials locally

- [x] 1.2 Initialize project structure
  - Create monorepo structure: `/backend`, `/dashboard`, `/infrastructure`
  - Initialize Python project for backend (Python 3.11)
  - Initialize React + TypeScript project for dashboard (Vite)
  - Create `.env` files for configuration

- [x] 1.3 Set up AWS CDK for infrastructure
  - Install AWS CDK
  - Initialize CDK app in `/infrastructure`
  - Create stacks: `DemoStack`, `DashboardStack`
  - Configure CDK context for demo environment

### Hour 5-8: DynamoDB & Basic Lambda

- [x] 2.1 Create DynamoDB table
  - Define `demo_workflows` table schema
  - Set up partition key: `workflow_id`
  - Add GSI for querying by status
  - Deploy table via CDK

- [x] 2.2 Create Lambda layer for shared code
  - Package common dependencies: boto3, requests
  - Create data models: `FarmerInput`, `MarketData`, `SurplusAnalysis`
  - Deploy layer via CDK

- [x] 2.3 Implement farmer input API
  - Create Lambda function: `start_demo_workflow`
  - Accept POST request with farmer data
  - Generate workflow_id
  - Store in DynamoDB
  - Return workflow_id and dashboard URL

### Hour 9-12: Market Data Scanner

- [x] 3.1 Implement Agmarknet scraper
  - Create Lambda function: `scan_market_data`
  - Implement HTTP request to Agmarknet API
  - Parse HTML response (BeautifulSoup)
  - Extract prices for 4 mandis: Sinnar, Nashik, Pune, Mumbai
  - Calculate net-to-farmer price (price - transport cost)

- [x] 3.2 Add caching and fallback
  - Store fetched prices in DynamoDB with TTL
  - Implement fallback to cached data if API fails
  - Add "data_source" field: "live" or "cached"

- [x] 3.3 Test market scanner
  - Manual test with real Agmarknet API
  - Verify fallback works when API is unreachable
  - Check price calculations are correct

### Hour 13-16: Mock Satellite Data

- [x] 4.1 Create static NDVI data
  - Create JSON file with pre-loaded NDVI trajectory
  - Include 5 data points showing declining trend (0.68 → 0.52)
  - Add metadata: trend, harvest_readiness, confidence

- [x] 4.2 Implement satellite context Lambda
  - Create Lambda function: `get_satellite_context`
  - Load static NDVI data from S3 or embedded JSON
  - Return formatted response with "simulated" label

### Hour 17-20: Surplus Detection Logic

- [x] 5.1 Implement surplus detector
  - Create Lambda function: `detect_surplus`
  - Calculate total FPO volume (sum of all farmer inputs)
  - Compare against mandi capacity threshold (22 tonnes)
  - If surplus > 3 tonnes, recommend processing diversion

- [x] 5.2 Add processor capacity data
  - Create static processor list: Sai Agro (5T @ ₹32/kg), Krishi Proc (2T @ ₹38/kg)
  - Calculate recommended split: fresh vs processing
  - Return structured `SurplusAnalysis` response

### Hour 21-24: Step Functions Workflow

- [x] 6.1 Define Step Functions state machine
  - Create state machine: `AnnaDrishtiDemoWorkflow`
  - Add states: ParseInput → ScanMarket → GetSatellite → DetectSurplus → SelectBuyer
  - Configure error handling and retries
  - Deploy via CDK

- [x] 6.2 Wire Lambda functions to states
  - Connect each Lambda to corresponding state
  - Configure input/output transformations
  - Add EventBridge event publishing for dashboard updates

- [x] 6.3 Test workflow end-to-end
  - Trigger workflow with test farmer input
  - Verify each state executes successfully
  - Check DynamoDB for stored results

## Day 2: AI Negotiation & Dashboard (Hours 25-48)

### Hour 25-32: WhatsApp + Bedrock Integration

- [x] 7.1 Set up WhatsApp Business API
  - Create WhatsApp Business account (or use sandbox)
  - Get API credentials from Twilio/Gupshup
  - Configure webhook URL (API Gateway)
  - Test sending/receiving messages

- [x] 7.2 Implement WhatsApp message sender
  - Create Lambda function: `send_whatsapp_message`
  - Use WhatsApp Business API to send messages
  - Store sent messages in DynamoDB
  - Return message ID

- [x] 7.3 Implement WhatsApp webhook handler
  - Create Lambda function: `handle_whatsapp_webhook`
  - Parse incoming message payload
  - Extract buyer response and price
  - Store in DynamoDB
  - Trigger Step Functions continuation

- [x] 7.4 Set up AWS Bedrock
  - Enable Bedrock in AWS console
  - Request access to Claude 3 Haiku model
  - Test model invocation with sample prompt
  - Configure IAM permissions

- [x] 7.5 Implement negotiation logic
  - Create Lambda function: `negotiate_with_buyer`
  - Build prompt with context: offer, buyer response, market price
  - Add hard constraints: floor price, max 3 exchanges
  - Invoke Bedrock Claude 3 Haiku
  - Parse response and extract counter-offer
  - Safety check: ensure price >= floor

- [x] 7.6 Add negotiation to workflow
  - Add state: `NegotiateWithBuyer` (with wait for callback)
  - Configure task token for async WhatsApp response
  - Add state: `CalculateBlendedIncome`
  - Add state: `PresentForConfirmation`

- [x] 7.7 Test negotiation end-to-end
  - Trigger workflow
  - Send WhatsApp message to team phone
  - Respond as buyer
  - Verify Bedrock generates counter-offer
  - Check final deal is stored correctly

### Hour 33-40: Real-Time Dashboard

- [x] 8.1 Set up React dashboard project
  - Initialize Vite + React + TypeScript
  - Install dependencies: React Query, Recharts, Tailwind CSS
  - Create basic layout: header, activity stream, negotiation panel

- [x] 8.2 Implement WebSocket connection
  - Create API Gateway WebSocket API
  - Create Lambda: `websocket_connect`, `websocket_disconnect`
  - Implement connection management in DynamoDB
  - Test WebSocket connection from React

- [x] 8.3 Implement EventBridge → WebSocket bridge
  - Create EventBridge rule for workflow events
  - Create Lambda: `publish_to_websocket`
  - Send events to all connected WebSocket clients
  - Test event flow: workflow → EventBridge → WebSocket → dashboard

- [x] 8.4 Build activity stream component
  - Create `ActivityStream` component
  - Display list of agent actions with timestamps
  - Color code by agent type: blue (Sell), green (Process)
  - Add "LIVE" or "SIMULATED" badges
  - Auto-scroll to latest action

- [x] 8.5 Build negotiation chat component
  - Create `NegotiationChat` component
  - Display messages in chat interface
  - Show agent messages (left) and buyer messages (right)
  - Highlight final agreed price

- [x] 8.6 Build surplus detection panel
  - Create `SurplusPanel` component
  - Display total volume, mandi capacity, surplus
  - Show recommended split: fresh vs processing
  - List processors with capacity and rates

- [x] 8.7 Build income comparison card
  - Create `IncomeComparison` component
  - Display: nearest mandi income vs Anna Drishti income
  - Show difference in large green text
  - Add breakdown: fresh + processing

### Hour 41-44: Processing Impact Visualization

- [x] 9.1 Build processing impact component
  - Create `ProcessingImpactViz` component
  - Implement scenario toggle: "Without" vs "With" Anna Drishti
  - Use Recharts for bar chart (14 farmer incomes)
  - Add Sankey diagram for supply flow

- [x] 9.2 Add pre-computed scenario data
  - Define scenarios in JSON: without (₹2.1cr) vs with (₹3.4cr)
  - Calculate per-farmer incomes for each scenario
  - Add supply flow data: total → mandi/processing

- [x] 9.3 Implement scenario animation
  - Animate transition between scenarios
  - Highlight income difference in green
  - Add explanatory text for each scenario

### Hour 45-46: Game Theory Simulation

- [x] 10.1 Build game theory component
  - Create `GameTheorySimulation` component
  - Use Mapbox GL JS for farmer map (500 dots)
  - Implement mode toggle: "Uncoordinated" vs "Coordinated"
  - Color dots by crop type

- [x] 10.2 Add pre-computed farmer allocations
  - Generate 500 farmer positions (Nashik region)
  - Uncoordinated: 80% tomato (red), 20% moong (green)
  - Coordinated: 40% tomato, 25% moong, 20% chili, 15% greens
  - Calculate collective incomes for each mode

- [x] 10.3 Add outcome display
  - Show collective income for each mode
  - Highlight difference: +₹1.3 crore
  - Add label: "Pre-computed simulation - Phase 2 feature"

### Hour 47-48: Demo Polish & Testing

- [x] 11.1 Implement reset button
  - Create API endpoint: POST /api/demo/reset
  - Clear DynamoDB tables
  - Stop running Step Functions executions
  - Publish reset event to dashboard

- [x] 11.2 Add offline mode
  - Create environment variable: DEMO_OFFLINE_MODE
  - Use cached market data when offline
  - Simulate WhatsApp messages in UI only
  - Test full demo without internet

- [x] 11.3 Deploy to AWS
  - Deploy backend via CDK: `cdk deploy DemoStack`
  - Build dashboard: `npm run build`
  - Deploy dashboard via CDK: `cdk deploy DashboardStack`
  - Get CloudFront URL

- [x] 11.4 End-to-end demo rehearsal
  - Run through full demo script (4 minutes)
  - Test reset button
  - Test offline mode
  - Fix any bugs
  - Practice presenter narration

- [x] 11.5 Prepare backup plan
  - Record video of working demo (in case live fails)
  - Prepare slides with screenshots
  - Have team member ready to act as buyer
  - Test on venue WiFi (if possible)

---

# PHASE 2: POST-HACKATHON ENHANCEMENTS (2 Weeks)

**Goal**: Replace simulations with real integrations
**Scope**: ~30 tasks
**Testing**: Basic unit tests

## Week 1: Real IVR & Satellite Integration

- [ ] 12. Replace web form with real IVR
  - Set up Amazon Connect instance
  - Configure Hindi language support
  - Create IVR flow with Lex bot
  - Integrate with Step Functions
  - Test with real phone calls

- [ ] 13. Integrate real Sentinel-2 API
  - Set up Copernicus Hub account
  - Implement imagery download Lambda
  - Add NDVI calculation (rasterio + numpy)
  - Store results in Timestream
  - Replace mock data with real API calls

- [ ] 14. Add basic authentication
  - Set up AWS Cognito user pool
  - Add login page to dashboard
  - Protect API endpoints with JWT
  - Add FPO coordinator role

## Week 2: Enhanced Dashboard & Error Handling

- [ ] 15. Build farmer portfolio view
  - Add farmer list page
  - Add farmer detail page with plots
  - Display transaction history
  - Add search functionality

- [ ] 16. Add payment tracking
  - Create payment status tracker
  - Flag delayed payments (>48 hours)
  - Display payment metrics

- [ ] 17. Implement error handling
  - Add try-catch blocks to all Lambdas
  - Implement exponential backoff retries
  - Add CloudWatch alarms for failures
  - Create error dashboard

- [ ] 18. Add basic unit tests
  - Write tests for market scanner
  - Write tests for surplus detector
  - Write tests for negotiation logic
  - Achieve 50% code coverage

---

# PHASE 3: PRODUCTION SYSTEM (3 Months)

**Goal**: Implement full specs for 1 FPO pilot (500 farmers)
**Scope**: All remaining tasks from full specs (~700 tasks)
**Testing**: Comprehensive (unit + property-based + integration + E2E)

## Month 1: Backend Foundation

- [ ] 19. Implement full Backend Foundation & Data Layer spec
  - Execute all tasks from `.kiro/specs/backend-foundation-data-layer/tasks.md`
  - Set up production RDS PostgreSQL
  - Implement proper data models
  - Add comprehensive error handling
  - Write property-based tests

- [ ] 20. Implement full Market Data Pipeline spec
  - Execute all tasks from `.kiro/specs/market-data-pipeline/tasks.md`
  - Add price forecasting (LightGBM)
  - Implement scheduled scraping
  - Add data quality checks

## Month 2: Agent Systems

- [ ] 21. Implement full Sell Agent spec
  - Execute all tasks from `.kiro/specs/sell-agent/tasks.md`
  - Add multi-buyer coordination
  - Implement aggregation logic
  - Add confirmation workflows
  - Write property-based tests

- [ ] 22. Implement full Process Agent spec
  - Execute all tasks from `.kiro/specs/process-agent/tasks.md`
  - Add processor onboarding
  - Implement quality grading
  - Add logistics coordination

- [ ] 23. Implement full Voice Interface spec
  - Execute all tasks from `.kiro/specs/voice-interface-ivr/tasks.md`
  - Add multi-language support (Hindi, Marathi)
  - Implement DTMF fallback
  - Add voice biometrics

- [ ] 24. Implement full WhatsApp Integration spec
  - Execute all tasks from `.kiro/specs/whatsapp-integration/tasks.md`
  - Add rich media support
  - Implement message templates
  - Add conversation state management

## Month 3: Advanced Features & Dashboard

- [ ] 25. Implement full Satellite Context Provider spec
  - Execute all tasks from `.kiro/specs/satellite-context-provider/tasks.md`
  - Add automated imagery downloads
  - Implement crop distress detection
  - Add harvest readiness confirmation

- [ ] 26. Implement full FPO Dashboard spec
  - Execute all tasks from `.kiro/specs/fpo-dashboard/tasks.md`
  - Build all feature modules
  - Add analytics and reporting
  - Implement accessibility features
  - Write E2E tests with Playwright

- [ ] 27. Production deployment
  - Set up multi-AZ RDS
  - Configure auto-scaling for Lambdas
  - Set up CloudWatch dashboards
  - Implement backup and disaster recovery
  - Add monitoring and alerting

- [ ] 28. Pilot launch with 1 FPO
  - Onboard 500 farmers
  - Train FPO coordinator
  - Run pilot for 1 harvest season
  - Collect feedback and iterate

---

## Task Prioritization Rules

**Phase 1 (Hackathon):**
- ✅ Focus: Demo impact over completeness
- ✅ Skip: All automated tests, production error handling
- ✅ Simulate: Satellite data, processor capacity, multi-farmer coordination
- ✅ Real: Bedrock negotiation, Agmarknet prices, WhatsApp messages

**Phase 2 (Post-Hackathon):**
- ✅ Focus: Replace simulations with real integrations
- ✅ Add: Basic authentication, error handling, unit tests
- ✅ Skip: Property-based tests, advanced features

**Phase 3 (Production):**
- ✅ Focus: Full spec implementation
- ✅ Add: All remaining features, comprehensive testing, production infrastructure
- ✅ Goal: Ready for 1 FPO pilot (500 farmers)

## Success Criteria by Phase

**Phase 1 Success:**
- ✅ Demo completes in 4 minutes without errors
- ✅ Live Bedrock negotiation works on stage
- ✅ Judges see AWS services in console
- ✅ Processing math is clear and compelling
- ✅ Win the hackathon!

**Phase 2 Success:**
- ✅ Real IVR calls work
- ✅ Real satellite data integrated
- ✅ Dashboard has authentication
- ✅ Basic error handling prevents crashes
- ✅ 50% code coverage with unit tests

**Phase 3 Success:**
- ✅ All 8 specs fully implemented
- ✅ 500 farmers onboarded to 1 FPO
- ✅ System handles 50+ concurrent transactions
- ✅ 90%+ uptime over 1 harvest season
- ✅ Measurable income improvement for farmers

## Notes

- Each phase preserves all work from previous phases
- Phase 1 code is refactored (not rewritten) in Phase 2/3
- Full specs in `.kiro/specs/` remain the source of truth for Phase 3
- Optional tasks (marked with `*` in full specs) can be skipped even in Phase 3
- Property-based tests are valuable but not required for pilot launch
