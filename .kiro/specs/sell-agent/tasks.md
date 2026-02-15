# Implementation Plan: Sell Agent

## Overview

This implementation plan breaks down the Sell Agent feature into discrete coding tasks. The agent orchestrates the complete selling workflow from farmer intent to confirmed deal using LangGraph for workflow orchestration, Amazon Bedrock for negotiation, and WhatsApp Business API for communication. All tasks build incrementally, with testing integrated throughout to validate correctness early.

## Tasks

- [ ] 1. Set up project structure and core dependencies
  - Create Python project structure with src/sell_agent directory
  - Set up virtual environment and install dependencies: langgraph, boto3 (Bedrock), redis, psycopg2, fastapi, hypothesis (for property testing)
  - Configure environment variables for AWS credentials, database connection, Redis connection, WhatsApp API keys
  - Create configuration module for loading environment-specific settings
  - _Requirements: 9.1, 9.2_

- [ ] 2. Implement data models and session state management
  - [ ] 2.1 Create Pydantic models for all data structures
    - Define Intent, MandiResult, YieldEstimate, AggregationGroup, Offer, NegotiationContext, Deal, Transaction, SellAgentSession models
    - Add validation rules for phone numbers, prices, quantities, coordinates
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 4.1, 5.1, 6.1, 7.1, 8.1_

  - [ ]* 2.2 Write property test for data model validation
    - **Property 7: Net price calculation**
    - **Validates: Requirements 2.3**

  - [ ] 2.3 Implement Redis session manager
    - Create SessionManager class with create, read, update, delete operations
    - Implement 30-minute TTL for sessions
    - Add session state serialization/deserialization
    - _Requirements: 9.2_

  - [ ]* 2.4 Write property test for session state persistence
    - **Property 30: Session state persistence**
    - **Validates: Requirements 9.2**

- [ ] 3. Implement Intent Parser component
  - [ ] 3.1 Create IntentParser class with voice and text parsing
    - Integrate Amazon Transcribe for Hindi voice-to-text
    - Implement IndicBERT-based intent classification (use pre-trained model or mock for MVP)
    - Add entity extraction for crop type and status
    - Implement confidence scoring and clarification logic
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 3.2 Write property tests for intent parsing
    - **Property 1: Voice transcription completeness**
    - **Property 2: Text parsing completeness**
    - **Property 3: Entity extraction accuracy**
    - **Property 4: Clarification on ambiguity**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

  - [ ]* 3.3 Write unit tests for common Hindi phrases
    - Test specific phrases like "Mere tamatar tayyar hain, bech do"
    - Test edge cases: empty input, non-Hindi input, very long input
    - _Requirements: 1.5_

- [ ] 4. Implement Market Scanner component
  - [ ] 4.1 Create MarketScanner class with Agmarknet integration
    - Implement Agmarknet API scraper (or mock API for MVP)
    - Add geospatial query for mandis within radius
    - Implement transport cost calculation based on distance and quantity
    - Add net price calculation: price - (transport_cost / quantity)
    - Implement mandi ranking by net price
    - Add Redis caching with 1-hour TTL
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 4.2 Write property tests for market scanning
    - **Property 5: Mandi query count constraint**
    - **Property 6: Transport cost calculation**
    - **Property 7: Net price calculation**
    - **Property 8: Mandi ranking by net price**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [ ]* 4.3 Write unit test for no mandis found edge case
    - Test behavior when no mandis exist within 100km
    - Verify farmer notification and alternative suggestions
    - _Requirements: 2.5_

  - [ ] 4.4 Implement LightGBM price forecaster (optional for MVP)
    - Train LightGBM model on historical Agmarknet data or use mock predictions
    - Add 48-hour price forecast endpoint
    - _Requirements: 2.1_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Yield Estimator component
  - [ ] 6.1 Create YieldEstimator class with satellite data integration
    - Implement S3 client for Sentinel-2 imagery retrieval
    - Add NDVI calculation from Red and NIR bands (use rasterio or mock for MVP)
    - Implement regional yield estimation: plot_area × regional_avg × ndvi_factor
    - Add confidence scoring based on cloud cover and data staleness
    - Mark all estimates as "assistive only"
    - _Requirements: 3.1, 3.2_

  - [ ]* 6.2 Write property tests for yield estimation
    - **Property 9: Satellite yield estimation**
    - **Property 10: Farmer estimate priority**
    - **Property 11: Dual estimate communication**
    - **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

  - [ ]* 6.3 Write unit test for satellite data unavailable
    - Test graceful degradation when satellite data is missing
    - Verify system proceeds with farmer estimate only
    - _Requirements: 11.2_

- [ ] 7. Implement Aggregation Engine component
  - [ ] 7.1 Create AggregationEngine class with geospatial queries
    - Implement geospatial query for farmers within 10km radius
    - Add filtering by crop compatibility and active selling intent
    - Implement combined quantity calculation (sum of individual quantities)
    - Add shared transport cost calculation (total_cost / num_farmers)
    - Implement cost savings percentage calculation
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 7.2 Write property tests for aggregation
    - **Property 12: Neighbor identification bounds**
    - **Property 13: Aggregation quantity invariant**
    - **Property 14: Shared cost calculation**
    - **Property 15: Aggregation opt-out fallback**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

- [ ] 8. Implement Buyer Matcher component
  - [ ] 8.1 Create BuyerMatcher class with database queries
    - Implement buyer query filtered by crop type and capacity
    - Add distance calculation from farmer location
    - Implement trust score calculation from transaction history
    - Add buyer ranking by trust score and location
    - Limit results to 3-5 buyers
    - _Requirements: 5.1_

  - [ ]* 8.2 Write property test for buyer selection
    - **Property 16: Buyer selection count**
    - **Validates: Requirements 5.1**

- [ ] 9. Implement Negotiation Engine component
  - [ ] 9.1 Create NegotiationEngine class with Bedrock integration
    - Integrate Amazon Bedrock (Claude 3 Haiku) for message generation
    - Implement NegotiationGuardrails class with floor_price enforcement
    - Create template-based offer message generation
    - Implement buyer response parsing for price and terms extraction
    - Add counter-offer generation with guardrails validation
    - Implement 3-round negotiation limit
    - Add 4-hour timeout handling
    - Log all messages to audit trail
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_

  - [ ]* 9.2 Write property tests for negotiation (CRITICAL)
    - **Property 19: Floor price calculation**
    - **Property 20: Floor price enforcement (CRITICAL INVARIANT)**
    - **Property 21: Counter-offer on above-floor offers**
    - **Property 22: Negotiation round limit**
    - **Property 23: Comprehensive audit logging**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.5, 6.6**

  - [ ]* 9.3 Write unit tests for negotiation edge cases
    - Test buyer offers below floor price (should be rejected)
    - Test negotiation timeout after 4 hours
    - Test all buyers unresponsive scenario
    - _Requirements: 5.5, 11.3_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement WhatsApp Client component
  - [ ] 11.1 Create WhatsAppClient class with Business API integration
    - Integrate Gupshup or Twilio WhatsApp Business API
    - Implement send_message method for text messages
    - Implement send_voice_message method for audio
    - Add message template formatting
    - Implement retry with exponential backoff (1s, 2s, 4s)
    - Add webhook handler for incoming messages
    - _Requirements: 5.2, 12.5_

  - [ ]* 11.2 Write property tests for WhatsApp communication
    - **Property 17: Offer message completeness**
    - **Property 34: Exponential backoff retry**
    - **Property 36: Farmer communication language**
    - **Property 37: Buyer communication language preference**
    - **Validates: Requirements 5.3, 11.4, 12.3, 12.4**

- [ ] 12. Implement Confirmation Handler component
  - [ ] 12.1 Create ConfirmationHandler class
    - Implement deal presentation message generation in Hindi
    - Add voice confirmation parsing (detect "Haan" or "Naa")
    - Implement audio recording storage to S3
    - Add confirmation result validation
    - Create transaction record on confirmation
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 12.2 Write property tests for confirmation (CRITICAL)
    - **Property 24: Deal presentation on final offer**
    - **Property 25: No deal finalization without confirmation (CRITICAL INVARIANT)**
    - **Property 26: Deal finalization on valid confirmation**
    - **Validates: Requirements 7.1, 7.3, 7.4**

  - [ ]* 12.3 Write unit test for farmer decline scenario
    - Test workflow branching when farmer says "Naa"
    - Verify return to buyer outreach or market scanning
    - _Requirements: 7.5_

- [ ] 13. Implement Transaction Tracker component
  - [ ] 13.1 Create TransactionTracker class
    - Implement transaction record creation with expected times
    - Add pickup status tracking and farmer prompts
    - Implement payment status monitoring
    - Add delay detection (> 6 hours for payment)
    - Implement alert triggering on delays
    - Add session cleanup on transaction completion
    - _Requirements: 8.1, 8.2, 8.4, 8.5_

  - [ ]* 13.2 Write property tests for transaction tracking
    - **Property 27: Transaction creation completeness**
    - **Property 28: Payment delay alerting**
    - **Property 29: Transaction completion cleanup**
    - **Validates: Requirements 8.1, 8.4, 8.5**

  - [ ]* 13.3 Write unit test for pickup reminder
    - Test time-based pickup reminder at expected pickup time
    - _Requirements: 8.2_

- [ ] 14. Implement Audit Logger component
  - [ ] 14.1 Create AuditLogger class with CloudWatch integration
    - Implement log_state_transition method
    - Add log_negotiation_message method
    - Implement log_farmer_confirmation method
    - Add structured logging with consistent schema
    - Implement audit trail retrieval by transaction ID
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [ ]* 14.2 Write property test for audit logging
    - **Property 23: Comprehensive audit logging** (already tested in 9.2, verify coverage)
    - **Property 33: Audit trail retrieval completeness**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.5**

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Implement LangGraph workflow orchestration
  - [ ] 16.1 Create SellAgentWorkflow class with LangGraph
    - Define workflow state machine: intent → market_scan → yield → surplus_check → aggregate → buyer_outreach → negotiate → confirm → track
    - Implement state transition functions for each step
    - Add conditional branching (e.g., aggregation decline, buyer timeout)
    - Integrate all component classes (IntentParser, MarketScanner, etc.)
    - Implement workflow resumability from session state
    - Add retry logic with 3-attempt limit
    - _Requirements: 9.1, 9.3, 9.4_

  - [ ]* 16.2 Write property tests for workflow orchestration
    - **Property 31: Retry on failure**
    - **Property 32: Workflow resumability**
    - **Validates: Requirements 9.3, 9.4**

- [ ] 17. Implement error handling and graceful degradation
  - [ ] 17.1 Add error handlers for all components
    - Implement circuit breaker for external services
    - Add fallback to cached data when Market Data Pipeline unavailable
    - Implement graceful degradation for satellite data unavailability
    - Add critical error notification to farmers
    - _Requirements: 11.1, 11.2, 11.3, 11.5_

  - [ ]* 17.2 Write unit tests for error scenarios
    - Test Market Data Pipeline unavailable (use cached prices)
    - Test satellite data unavailable (proceed with farmer estimate)
    - Test all buyers unresponsive (suggest mandi sale)
    - Test critical error notification
    - _Requirements: 11.1, 11.2, 11.3, 11.5_

  - [ ]* 17.3 Write property test for critical error notification
    - **Property 35: Critical error notification**
    - **Validates: Requirements 11.5**

- [ ] 18. Implement FastAPI endpoints for workflow control
  - [ ] 18.1 Create FastAPI application with workflow endpoints
    - Add POST /sell-agent/start endpoint to initiate workflow
    - Add GET /sell-agent/session/{session_id} endpoint to retrieve session state
    - Add POST /sell-agent/webhook/whatsapp endpoint for WhatsApp messages
    - Add POST /sell-agent/webhook/payment endpoint for payment updates
    - Add GET /sell-agent/transaction/{transaction_id} endpoint for transaction status
    - Add health check endpoint
    - _Requirements: 9.1_

  - [ ]* 18.2 Write integration tests for API endpoints
    - Test complete workflow via API calls
    - Test webhook handling for WhatsApp and payment
    - Test session retrieval and resumability
    - _Requirements: 9.1, 9.4_

- [ ] 19. Implement database integration
  - [ ] 19.1 Create database client and transaction handling
    - Implement PostgreSQL client with connection pooling
    - Add CRUD operations for farmers, buyers, transactions
    - Implement ACID transaction handling for financial operations
    - Add database migration scripts for schema setup
    - _Requirements: 9.1_

  - [ ]* 19.2 Write unit tests for database operations
    - Test transaction rollback on failure
    - Test concurrent transaction isolation
    - Test foreign key constraint enforcement
    - _Requirements: 9.1_

- [ ] 20. Integration and end-to-end testing
  - [ ] 20.1 Wire all components together in workflow
    - Connect IntentParser → MarketScanner → YieldEstimator → AggregationEngine → BuyerMatcher → NegotiationEngine → ConfirmationHandler → TransactionTracker
    - Ensure session state flows correctly between steps
    - Add logging at each transition point
    - _Requirements: 9.1_

  - [ ]* 20.2 Write end-to-end workflow tests
    - Test happy path: intent → confirmation → tracking
    - Test buyer timeout path: intent → timeout → mandi fallback
    - Test aggregation decline path: intent → decline → individual workflow
    - Test payment delay path: confirmed → pickup → payment delayed → alert
    - _Requirements: 9.1, 9.5_

- [ ] 21. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Deployment preparation
  - [ ] 22.1 Create deployment configuration
    - Create Dockerfile for containerized deployment
    - Add AWS Lambda deployment configuration (if using Lambda)
    - Create CloudFormation or CDK templates for infrastructure
    - Add environment-specific configuration files
    - Document deployment steps
    - _Requirements: 9.1_

  - [ ] 22.2 Set up monitoring and alerting
    - Configure CloudWatch metrics for key performance indicators
    - Set up alerts for floor price violations, deals without confirmation, workflow failures
    - Add dashboard for monitoring workflow completion rate, payment delays, buyer response rate
    - _Requirements: 10.1_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Critical properties (floor price enforcement, no deal without confirmation) require extra validation
- All property tests should use the `hypothesis` library with appropriate strategies
- Integration tests should mock external services (Agmarknet, Sentinel-2, WhatsApp, Bedrock) for deterministic testing
