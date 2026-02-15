# Implementation Plan: Voice Interface (IVR)

## Overview

This implementation plan breaks down the Voice Interface (IVR) feature into discrete coding tasks. The IVR system enables farmers to interact with Anna Drishti via phone using Hindi voice commands, with DTMF fallback for reliability. The implementation uses Python with AWS Lambda for call flow logic, Amazon Connect for call handling, Amazon Transcribe for STT, Amazon Polly for TTS, and Redis for session management.

The tasks are organized to build incrementally: core infrastructure first, then speech processing, then workflow integration, and finally testing and monitoring.

## Tasks

- [ ] 1. Set up project structure and core infrastructure
  - Create directory structure for IVR Lambda functions
  - Set up Python virtual environment with dependencies (boto3, redis, requests)
  - Configure AWS Lambda deployment scripts
  - Create configuration files for environment variables (Amazon Connect, Redis, API endpoints)
  - Set up logging configuration with CloudWatch integration
  - _Requirements: 1.1, 15.5_

- [ ] 2. Implement session management
  - [ ] 2.1 Create session data models and Redis client
    - Define IVRSession data class with all required fields
    - Implement Redis connection with connection pooling
    - Create session key generation (format: `ivr:session:{session_id}`)
    - _Requirements: 6.1, 6.2_

  - [ ]* 2.2 Write property test for session creation
    - **Property 11: Session creation with required fields**
    - **Validates: Requirements 6.1, 6.2**

  - [ ] 2.3 Implement SessionManager class
    - Implement create_session() with unique ID generation and TTL setting
    - Implement get_session() with Redis lookup
    - Implement update_session() with TTL reset
    - Implement close_session() for cleanup
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 2.4 Write property tests for session operations
    - **Property 12: Session TTL initialization**
    - **Property 13: Session resumption**
    - **Property 14: Session persistence**
    - **Property 15: Concurrent session support**
    - **Validates: Requirements 6.3, 6.4, 6.5, 6.7**

  - [ ]* 2.5 Write unit tests for session edge cases
    - Test session expiry handling
    - Test Redis connection failures
    - Test concurrent session creation for same farmer
    - _Requirements: 6.6, 13.4_

- [ ] 3. Implement speech-to-text processing
  - [ ] 3.1 Create SpeechToTextProcessor class
    - Implement transcribe_audio() using Amazon Transcribe
    - Configure Hindi language (hi-IN) and custom vocabulary
    - Parse transcription results and extract confidence scores
    - Handle transcription failures gracefully
    - _Requirements: 2.1, 2.4, 2.7_

  - [ ]* 3.2 Write property tests for STT
    - **Property 2: Hindi audio transcription**
    - **Property 3: Transcription confidence score**
    - **Validates: Requirements 2.1, 2.4**

  - [ ] 3.3 Create custom vocabulary for agricultural terms
    - Define crop names in Hindi (टमाटर, प्याज, मिर्च, आलू)
    - Define action verbs (बेचना, तैयार, कटाई)
    - Define quantity terms (क्विंटल, किलो, टन)
    - Upload custom vocabulary to Amazon Transcribe
    - _Requirements: 2.2_

  - [ ]* 3.4 Write unit tests for STT edge cases
    - Test poor audio quality handling
    - Test transcription timeout
    - Test service unavailability fallback
    - _Requirements: 2.6, 13.1_

- [ ] 4. Implement intent classification and entity extraction
  - [ ] 4.1 Create IntentClassifier class with rule-based patterns
    - Define intent patterns for sell, process, query-price, help
    - Define crop patterns with Hindi name variations
    - Implement classify_intent() with keyword matching
    - Implement extract_entities() for each intent type
    - Calculate confidence scores based on pattern matches
    - _Requirements: 3.1, 3.4, 3.5, 3.6_

  - [ ]* 4.2 Write property tests for intent classification
    - **Property 4: Intent classification**
    - **Property 5: Entity extraction for sell intent**
    - **Property 6: Entity extraction for process intent**
    - **Property 7: DTMF fallback on low confidence**
    - **Validates: Requirements 3.1, 3.4, 3.5, 3.6, 3.7**

  - [ ]* 4.3 Write unit tests for intent classification examples
    - Test specific Hindi phrases: "Mere tamatar tayyar hain"
    - Test ambiguous inputs
    - Test entity extraction accuracy
    - _Requirements: 3.1, 3.4, 3.5_

- [ ] 5. Implement text-to-speech generation
  - [ ] 5.1 Create TextToSpeechGenerator class
    - Implement generate_speech() using Amazon Polly with Aditi voice
    - Configure speech rate and language settings
    - Handle mixed Hindi-English text
    - Cache frequently used phrases in Redis
    - _Requirements: 4.1, 4.4_

  - [ ] 5.2 Create SSML templates for common prompts
    - Create template for price announcements
    - Create template for deal confirmations
    - Create template for menu prompts
    - Implement generate_from_template() with variable substitution
    - _Requirements: 4.1, 4.7_

  - [ ]* 5.3 Write property tests for TTS
    - **Property 8: Text-to-speech conversion**
    - **Property 9: Number pronunciation in TTS**
    - **Validates: Requirements 4.1, 4.4**

  - [ ]* 5.4 Write unit tests for TTS edge cases
    - Test TTS service failure fallback
    - Test SSML template rendering
    - Test caching behavior
    - _Requirements: 13.2_

- [ ] 6. Implement DTMF menu system
  - [ ] 6.1 Define menu structure and create Menu data models
    - Define main menu with options (1=sell, 2=process, 3=price, 9=coordinator)
    - Define sell submenu for crop selection
    - Define quantity input menu
    - Create Menu and MenuOption data classes
    - _Requirements: 5.2, 5.4_

  - [ ] 6.2 Create DTMFMenuHandler class
    - Implement get_menu() to retrieve menu definitions
    - Implement handle_input() to process DTMF digits
    - Implement build_prompt() to generate menu audio
    - Support * for back navigation and # for confirmation
    - _Requirements: 5.2, 5.7_

  - [ ]* 6.3 Write property test for DTMF navigation
    - **Property 10: DTMF menu navigation**
    - **Validates: Requirements 5.7**

  - [ ]* 6.4 Write unit tests for DTMF menu flows
    - Test main menu navigation
    - Test submenu navigation
    - Test invalid input handling
    - Test timeout behavior
    - _Requirements: 5.2, 5.5, 5.6_

- [ ] 7. Checkpoint - Ensure core components work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement call handler and orchestration
  - [ ] 8.1 Create CallHandler class
    - Implement handle_call_start() to initialize session and play greeting
    - Implement handle_voice_input() to process transcribed audio
    - Implement handle_dtmf_input() to process keypad input
    - Implement handle_call_end() to cleanup and log
    - Generate CallResponse objects for Amazon Connect
    - _Requirements: 1.3, 1.4_

  - [ ]* 8.2 Write property tests for call handling
    - **Property 1: Farmer profile lookup**
    - **Property 34: Call drop session marking**
    - **Property 35: Call drop SMS notification**
    - **Validates: Requirements 1.4, 11.3, 11.4**

  - [ ] 8.3 Implement call routing logic
    - Route to appropriate handler based on intent
    - Handle low-confidence fallback to DTMF
    - Handle service failures with graceful degradation
    - _Requirements: 3.7, 13.1, 13.2, 13.3_

  - [ ]* 8.4 Write property tests for error handling
    - **Property 37: Repeat request on unclear audio**
    - **Property 40: Service failure DTMF fallback**
    - **Property 41: TTS failure fallback**
    - **Validates: Requirements 11.7, 13.1, 13.2, 13.3**

  - [ ]* 8.5 Write unit tests for call flow scenarios
    - Test happy path: voice input → intent → workflow
    - Test DTMF fallback path
    - Test error recovery paths
    - _Requirements: 3.7, 13.1, 13.2, 13.3_

- [ ] 9. Implement workflow integration
  - [ ] 9.1 Create WorkflowIntegrator class
    - Implement initiate_sell_workflow() to call Sell Agent API
    - Implement initiate_process_workflow() to call Process Agent API
    - Implement get_workflow_status() to poll workflow progress
    - Implement handle_workflow_callback() for workflow events
    - Handle API failures with retry and fallback
    - _Requirements: 7.1, 7.2, 8.1, 8.2, 13.5_

  - [ ]* 9.2 Write property tests for workflow integration
    - **Property 16: Sell Agent invocation with entities**
    - **Property 22: Process Agent invocation with entities**
    - **Property 42: Sell Agent API failure handling**
    - **Validates: Requirements 7.1, 7.2, 8.1, 8.2, 13.5**

  - [ ] 9.3 Implement workflow response handlers
    - Handle market scan results presentation
    - Handle aggregation opportunity presentation
    - Handle processing options presentation
    - Handle cost breakdown presentation
    - _Requirements: 7.4, 7.5, 8.3, 8.4_

  - [ ]* 9.4 Write property tests for workflow responses
    - **Property 17: Sell Agent clarification prompting**
    - **Property 18: Market results presentation**
    - **Property 19: Aggregation opportunity presentation**
    - **Property 23: Processing options presentation**
    - **Property 24: Processing cost breakdown presentation**
    - **Property 25: Processor callback request**
    - **Validates: Requirements 7.3, 7.4, 7.5, 8.3, 8.4, 8.5**

  - [ ]* 9.5 Write unit tests for workflow integration
    - Test API request formatting
    - Test API response parsing
    - Test retry logic with exponential backoff
    - Test circuit breaker behavior
    - _Requirements: 13.5, 13.6, 13.7_

- [ ] 10. Implement confirmation handling
  - [ ] 10.1 Create ConfirmationHandler class
    - Implement present_deal() to generate confirmation prompt with all deal details
    - Implement parse_confirmation_response() to parse voice/DTMF responses
    - Implement record_confirmation() to store audio in S3
    - Handle ambiguous responses with DTMF fallback
    - _Requirements: 7.7, 9.5, 9.8, 9.9_

  - [ ]* 10.2 Write property tests for confirmation handling
    - **Property 21: Confirmation audio recording**
    - **Property 29: Explicit confirmation request**
    - **Property 30: Confirmation and rejection parsing**
    - **Property 31: Ambiguous confirmation fallback**
    - **Property 32: Confirmation audio storage**
    - **Validates: Requirements 7.7, 9.5, 9.6, 9.7, 9.8, 9.9**

  - [ ]* 10.3 Write unit tests for confirmation parsing
    - Test Hindi affirmative phrases: "Haan", "Theek hai", "Ji haan"
    - Test Hindi negative phrases: "Naa", "Nahi"
    - Test DTMF inputs: 1 for yes, 2 for no
    - Test ambiguous responses
    - _Requirements: 9.6, 9.7, 9.8_

- [ ] 11. Implement outbound call management
  - [ ] 11.1 Create OutboundCallManager class
    - Implement initiate_call() using Amazon Connect outbound API
    - Implement schedule_retry() with 15-minute intervals
    - Implement send_fallback_notification() for SMS/WhatsApp
    - Track call attempts in DynamoDB
    - Respect calling hours (8 AM - 8 PM)
    - _Requirements: 9.1, 9.2, 9.10_

  - [ ]* 11.2 Write property tests for outbound calls
    - **Property 20: Outbound call for buyer offer**
    - **Property 26: Outbound call initiation for pending deal**
    - **Property 27: Outbound call retry logic**
    - **Property 28: Deal details presentation with all fields**
    - **Property 33: Fallback notification after failed attempts**
    - **Validates: Requirements 7.6, 9.1, 9.2, 9.3, 9.4, 9.10**

  - [ ]* 11.3 Write unit tests for outbound call scenarios
    - Test successful call flow
    - Test retry logic
    - Test fallback to SMS/WhatsApp
    - Test calling hours enforcement
    - _Requirements: 9.1, 9.2, 9.10_

- [ ] 12. Checkpoint - Ensure workflow integration works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement analytics and logging
  - [ ] 13.1 Create AnalyticsTracker class
    - Implement log_call() to write call logs to DynamoDB
    - Implement emit_metric() to send CloudWatch metrics
    - Implement generate_daily_report() for summary reports
    - Track all required metrics (call volume, duration, accuracy, completion rate)
    - _Requirements: 12.1, 12.2_

  - [ ]* 13.2 Write property tests for analytics
    - **Property 38: Comprehensive call logging**
    - **Property 39: Voice recognition accuracy tracking**
    - **Property 48: Scaling event logging**
    - **Validates: Requirements 12.1, 12.2, 15.7**

  - [ ] 13.3 Set up CloudWatch dashboards and alarms
    - Create dashboard for key metrics (call volume, accuracy, completion rate)
    - Configure alarms for critical thresholds (accuracy < 70%, completion < 80%)
    - Set up SNS notifications for alerts
    - _Requirements: 12.7_

  - [ ]* 13.4 Write unit tests for analytics
    - Test call log structure
    - Test metric emission
    - Test daily report generation
    - _Requirements: 12.1, 12.2_

- [ ] 14. Implement security and data protection
  - [ ] 14.1 Implement call recording with encryption
    - Configure S3 bucket with AES-256 encryption
    - Implement upload_recording() with encryption verification
    - Set 90-day lifecycle policy for recordings
    - Store recording references in multiple places (session, transaction, audit log)
    - _Requirements: 11.6, 14.1_

  - [ ]* 14.2 Write property tests for security
    - **Property 36: Call recording storage with encryption**
    - **Property 45: Farmer authentication for sensitive data**
    - **Property 46: PIN verification for transaction history**
    - **Property 47: Sensitive data exclusion from recordings**
    - **Validates: Requirements 11.6, 14.1, 14.3, 14.4, 14.5**

  - [ ] 14.3 Implement authentication and authorization
    - Implement phone number authentication
    - Implement PIN verification for transaction history
    - Add PII detection to prevent storing sensitive data in recordings
    - _Requirements: 14.3, 14.4, 14.5_

  - [ ]* 14.4 Write unit tests for security features
    - Test authentication flows
    - Test PIN verification
    - Test PII detection and masking
    - Test encryption verification
    - _Requirements: 14.3, 14.4, 14.5_

- [ ] 15. Implement error handling and retry logic
  - [ ] 15.1 Create error handling utilities
    - Implement exponential backoff retry decorator
    - Implement circuit breaker for external services
    - Create error response templates in Hindi
    - Implement fallback message generation
    - _Requirements: 13.6, 13.7_

  - [ ]* 15.2 Write property tests for error handling
    - **Property 43: Database retry with exponential backoff**
    - **Property 44: Exhausted retry fallback message**
    - **Validates: Requirements 13.6, 13.7**

  - [ ]* 15.3 Write unit tests for error scenarios
    - Test retry logic with various failure patterns
    - Test circuit breaker state transitions
    - Test fallback message generation
    - Test graceful degradation paths
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

- [ ] 16. Create Amazon Connect contact flows
  - [ ] 16.1 Design and implement inbound call flow
    - Create contact flow for inbound calls
    - Configure call routing to Lambda functions
    - Set up voice input collection
    - Set up DTMF input collection
    - Configure call recording
    - _Requirements: 1.2, 1.3_

  - [ ] 16.2 Design and implement outbound call flow
    - Create contact flow for outbound calls
    - Configure deal confirmation prompts
    - Set up confirmation response collection
    - Handle no-answer and busy scenarios
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 16.3 Configure Amazon Connect instance
    - Set up toll-free number
    - Configure hours of operation
    - Set up call queues and routing profiles
    - Configure Lambda function integrations
    - _Requirements: 1.1, 1.6_

- [ ] 17. Integration and end-to-end testing
  - [ ]* 17.1 Write integration tests for complete call flows
    - Test inbound call → voice intent → Sell Agent → confirmation
    - Test inbound call → DTMF menu → Process Agent → callback
    - Test outbound call → deal presentation → confirmation
    - Test error recovery flows
    - Test call drop and resume flows
    - _Requirements: 1.1, 7.1, 8.1, 9.1_

  - [ ]* 17.2 Write integration tests with mocked AWS services
    - Mock Amazon Connect call events
    - Mock Amazon Transcribe responses
    - Mock Amazon Polly responses
    - Mock Sell Agent API
    - Mock Process Agent API
    - _Requirements: 2.1, 4.1, 7.1, 8.1_

  - [ ] 17.3 Set up local testing environment
    - Create Docker Compose setup with Redis
    - Create mock AWS service endpoints
    - Set up test data (farmers, crops, deals)
    - Create test scripts for manual testing
    - _Requirements: All_

- [ ] 18. Deployment and infrastructure setup
  - [ ] 18.1 Create AWS Lambda deployment packages
    - Package Lambda functions with dependencies
    - Create Lambda layers for shared code
    - Configure Lambda environment variables
    - Set up Lambda execution roles and permissions
    - _Requirements: 15.5_

  - [ ] 18.2 Set up infrastructure with Terraform/CloudFormation
    - Define Lambda functions
    - Define DynamoDB tables for call logs and attempts
    - Define S3 bucket for recordings
    - Define Redis cluster (ElastiCache)
    - Define IAM roles and policies
    - _Requirements: 1.1, 11.6, 12.1_

  - [ ] 18.3 Configure monitoring and alerting
    - Set up CloudWatch log groups
    - Configure CloudWatch metrics
    - Create CloudWatch dashboards
    - Set up SNS topics for alerts
    - Configure alarm thresholds
    - _Requirements: 12.7_

- [ ] 19. Final checkpoint - Ensure complete system works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Documentation and handoff
  - [ ] 20.1 Create operational documentation
    - Document deployment procedures
    - Document monitoring and alerting setup
    - Document troubleshooting guides
    - Document escalation procedures
    - _Requirements: All_

  - [ ] 20.2 Create developer documentation
    - Document API interfaces
    - Document data models
    - Document configuration options
    - Document testing procedures
    - _Requirements: All_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- The implementation uses Python with AWS services (Lambda, Connect, Transcribe, Polly, S3, DynamoDB, Redis)
- Amazon Connect contact flows are configured separately from Lambda code
- All Hindi text and audio should be tested with native speakers for accuracy

