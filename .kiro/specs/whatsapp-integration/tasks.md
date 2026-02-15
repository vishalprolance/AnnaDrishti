# Implementation Plan: WhatsApp Integration

## Overview

This implementation plan breaks down the WhatsApp Integration feature into discrete coding tasks. The implementation uses Python with AWS Lambda, SQS, DynamoDB, and S3. The approach is incremental: build core components first, add message handling, implement retry/fallback logic, and finally add monitoring and security features.

## Tasks

- [ ] 1. Set up project structure and core dependencies
  - Create Python project with virtual environment
  - Install dependencies: boto3, requests, hypothesis, pytest
  - Set up directory structure: src/, tests/, templates/
  - Create requirements.txt and setup.py
  - Configure pytest for unit and property-based tests
  - _Requirements: 17.1, 17.2, 17.3_

- [ ] 2. Implement WhatsApp API client abstraction
  - [ ] 2.1 Create base WhatsAppClient interface
    - Define abstract methods: send_text(), send_template(), send_media(), validate_webhook()
    - _Requirements: 1.1, 1.2_
  
  - [ ] 2.2 Implement Gupshup adapter
    - Implement send_text() for Gupshup API
    - Implement send_template() with Gupshup template format
    - Implement send_media() with Gupshup media endpoints
    - Implement webhook signature validation for Gupshup
    - _Requirements: 1.3, 1.4, 1.5, 9.1_
  
  - [ ] 2.3 Implement Twilio adapter
    - Implement send_text() for Twilio API
    - Implement send_template() with Twilio Content API
    - Implement send_media() with Twilio media endpoints
    - Implement webhook signature validation for Twilio
    - _Requirements: 1.3, 1.4, 1.5, 9.1, 17.7_
  
  - [ ]* 2.4 Write property tests for WhatsApp client
    - **Property 1: Text message sending** - For any valid phone number and text content, send should succeed
    - **Property 3: Media message sending** - For any valid media file under 16MB, send should succeed
    - **Property 30: Media size validation** - For any media file, size should be validated against 16MB limit
    - **Property 31: Oversized media rejection** - For any file exceeding 16MB, should reject with error
    - **Validates: Requirements 1.3, 1.5, 8.5, 8.6**
  
  - [ ]* 2.5 Write unit tests for provider adapters
    - Test Gupshup API call formatting
    - Test Twilio API call formatting
    - Test error handling for both providers
    - _Requirements: 1.6_

- [ ] 3. Implement message data models
  - [ ] 3.1 Create OutboundMessage, InboundMessage, MessageLog models
    - Define Pydantic models with validation
    - Add serialization/deserialization methods
    - _Requirements: 2.1, 9.3_
  
  - [ ] 3.2 Create SendResult, BuyerResponse, ProcessorResponse models
    - Define response models with confidence scores
    - Add validation for required fields
    - _Requirements: 3.1, 5.1_
  
  - [ ]* 3.3 Write unit tests for data models
    - Test model validation
    - Test serialization round-trip
    - Test edge cases (empty fields, special characters)
    - _Requirements: 9.3_

- [ ] 4. Implement template manager
  - [ ] 4.1 Create TemplateManager class
    - Load templates from S3 on initialization
    - Implement render() method with variable substitution
    - Implement validate() method to check required variables
    - Cache templates in memory
    - _Requirements: 7.1, 7.2, 7.4_
  
  - [ ] 4.2 Create message templates
    - Create buyer_offer_hi.json and buyer_offer_en.json
    - Create processor_offer_hi.json and processor_offer_en.json
    - Create deal_confirmation_hi.json
    - Create payment_received_hi.json
    - Create pickup_reminder_hi.json
    - _Requirements: 6.1, 6.2, 6.3, 7.3_
  
  - [ ]* 4.3 Write property tests for template manager
    - **Property 2: Template variable substitution** - For any template with all required variables, substitution should succeed
    - **Property 26: Template variable validation** - For any template with missing variables, validation should fail
    - **Validates: Requirements 1.4, 7.2, 7.4**
  
  - [ ]* 4.4 Write unit tests for template manager
    - Test template loading from S3
    - Test variable substitution with Hindi and English
    - Test missing template handling
    - Test missing variable detection
    - _Requirements: 7.5_

- [ ] 5. Implement response parser
  - [ ] 5.1 Create ResponseParser class
    - Implement parse_buyer_response() with regex patterns
    - Implement parse_processor_response() with classification logic
    - Implement parse_farmer_response() for confirmations
    - Implement extract_price() with normalization
    - Implement extract_terms() for payment and timing
    - _Requirements: 3.1, 3.2, 3.4, 5.1, 5.2, 5.3_
  
  - [ ] 5.2 Add language detection
    - Detect Hindi (Devanagari) vs English (Latin) characters
    - Apply language-specific parsing rules
    - _Requirements: 3.3_
  
  - [ ]* 5.3 Write property tests for response parser
    - **Property 10: Price extraction from responses** - For any price format, should normalize to ₹/kg
    - **Property 11: Terms extraction** - For any response with terms, should extract them
    - **Property 12: Multilingual response parsing** - For any Hindi or English response, should parse
    - **Property 13: Ambiguous response flagging** - For any low-confidence parse, should flag for review
    - **Property 16: Processor response classification** - For any processor response, should classify correctly
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 5.1**
  
  - [ ]* 5.4 Write unit tests for response parser
    - Test specific price formats ("28", "₹28/kg", "28 rupaye")
    - Test Hindi confirmation keywords ("Haan", "Theek hai")
    - Test English confirmation keywords ("Yes", "OK", "Confirm")
    - Test decline keywords in both languages
    - Test edge cases (empty messages, special characters)
    - _Requirements: 3.6, 5.5_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Run all unit tests and property tests
  - Verify core components work independently
  - Ask the user if questions arise

- [ ] 7. Implement message logger (DynamoDB)
  - [ ] 7.1 Create MessageLogger class
    - Implement log_outbound() to write to DynamoDB
    - Implement log_inbound() to write to DynamoDB
    - Implement update_status() for status transitions
    - Implement query_by_phone() using partition key
    - Implement query_by_status() using GSI
    - Add TTL calculation (7 years from creation)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 15.1, 15.2, 15.5_
  
  - [ ] 7.2 Create DynamoDB table schema
    - Define table with recipient_phone (partition key) and timestamp (sort key)
    - Create GSI: message_id-index
    - Create GSI: status-timestamp-index
    - Configure TTL attribute
    - _Requirements: 17.6_
  
  - [ ]* 7.3 Write property tests for message logger
    - **Property 9: Outbound message logging** - For any outbound message, log entry should exist
    - **Property 38: Inbound message logging** - For any inbound message, log entry should exist
    - **Property 39: Message status transitions** - For any message, status should follow valid sequence
    - **Property 40: Failed message status** - For any failed message, status should be "failed" with error
    - **Property 41: Message status query** - For any message ID, should retrieve status
    - **Property 61: Status transition timestamps** - For any status change, timestamp should be recorded
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 15.1, 15.2, 15.3**
  
  - [ ]* 7.4 Write unit tests for message logger
    - Test DynamoDB write operations
    - Test query operations with various filters
    - Test TTL calculation
    - Test error handling for DynamoDB failures
    - _Requirements: 15.6, 15.7_

- [ ] 8. Implement rate limiter (DynamoDB)
  - [ ] 8.1 Create RateLimiter class
    - Implement check_and_increment() with atomic DynamoDB update
    - Implement get_wait_time() to calculate delay
    - Use conditional writes for atomic counter increment
    - Set TTL to 1 second for automatic reset
    - _Requirements: 11.1, 11.5, 11.6_
  
  - [ ] 8.2 Create DynamoDB table schema for rate limits
    - Define table with phone_number (partition key)
    - Configure TTL attribute (1 second)
    - _Requirements: 17.6, 19.6_
  
  - [ ]* 8.3 Write property tests for rate limiter
    - **Property 42: Rate limit enforcement** - For any phone number, rate should not exceed 80/sec
    - **Property 43: Rate limit queueing** - For any burst, excess should be queued
    - **Property 44: Rate limit error backoff** - For any rate limit error, should back off
    - **Validates: Requirements 11.1, 11.2, 11.4**
  
  - [ ]* 8.4 Write unit tests for rate limiter
    - Test atomic increment operations
    - Test TTL expiration behavior
    - Test distributed rate limiting across multiple instances
    - Test graceful degradation when DynamoDB unavailable
    - _Requirements: 11.3_

- [ ] 9. Implement message queue manager (SQS)
  - [ ] 9.1 Create MessageQueueManager class
    - Implement enqueue() to add messages to SQS FIFO queue
    - Implement dequeue() to poll messages with batch size 10
    - Implement delete() to remove processed messages
    - Implement requeue_with_delay() for failed messages
    - Add priority handling (high vs normal)
    - _Requirements: 14.1, 14.2, 14.4, 14.5, 14.6_
  
  - [ ] 9.2 Create SQS queues
    - Create whatsapp-messages.fifo queue
    - Create whatsapp-messages-dlq.fifo dead letter queue
    - Configure visibility timeout (30 seconds)
    - Configure message retention (7 days for DLQ)
    - _Requirements: 17.5, 14.7_
  
  - [ ]* 9.3 Write property tests for queue manager
    - **Property 56: Message enqueue** - For any send request, should enqueue
    - **Property 57: FIFO ordering** - For any messages at same priority, should process in order
    - **Property 58: Successful send deletion** - For any successful send, should delete from queue
    - **Property 59: Failed message requeue** - For any failed message, should requeue with retry count
    - **Property 60: Priority assignment** - For any farmer message, priority should be high
    - **Validates: Requirements 14.1, 14.2, 14.4, 14.5, 14.6**
  
  - [ ]* 9.4 Write unit tests for queue manager
    - Test FIFO ordering guarantees
    - Test priority handling
    - Test dead letter queue behavior
    - Test batch processing
    - _Requirements: 14.3_

- [ ] 10. Implement retry manager
  - [ ] 10.1 Create RetryManager class
    - Implement should_retry() to check error type
    - Implement get_delay() for exponential backoff (1s, 2s, 4s)
    - Implement is_permanent_error() to detect non-retryable errors
    - _Requirements: 12.1, 12.2, 12.4_
  
  - [ ]* 10.2 Write property tests for retry manager
    - **Property 45: Transient error retry limit** - For any transient error, max 3 retries
    - **Property 46: Exponential backoff delays** - For any retry sequence, delays should be 1s, 2s, 4s
    - **Property 48: Permanent error no-retry** - For any permanent error, no retry should occur
    - **Validates: Requirements 12.1, 12.2, 12.4**
  
  - [ ]* 10.3 Write unit tests for retry manager
    - Test permanent error detection (invalid phone, blocked user)
    - Test transient error detection (timeout, server error)
    - Test exponential backoff calculation
    - _Requirements: 12.3_

- [ ] 11. Implement SMS fallback handler (Amazon Pinpoint)
  - [ ] 11.1 Create SMSFallbackHandler class
    - Implement send_sms() using Amazon Pinpoint
    - Implement truncate_message() to fit 160 characters
    - Implement split_message() for multi-part SMS
    - Add farmer-only restriction check
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [ ]* 11.2 Write property tests for SMS fallback
    - **Property 47: SMS fallback after retry exhaustion** - For any farmer message failing 3 times, SMS should trigger
    - **Property 52: SMS farmer-only restriction** - For any non-farmer failure, no SMS
    - **Property 53: SMS 160-character optimization** - For any message fitting 160 chars, single SMS
    - **Property 54: SMS multi-part splitting** - For any long message, should split into multiple SMS
    - **Property 55: SMS fallback logging** - For any SMS fallback, log entry should exist
    - **Validates: Requirements 12.3, 13.1, 13.2, 13.3, 13.4, 13.5**
  
  - [ ]* 11.3 Write unit tests for SMS fallback
    - Test message truncation logic
    - Test multi-part SMS splitting
    - Test Hindi UTF-8 encoding
    - Test Pinpoint API error handling
    - _Requirements: 13.6_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Run all unit tests and property tests
  - Verify message flow components work together
  - Ask the user if questions arise

- [ ] 13. Implement message sender Lambda function
  - [ ] 13.1 Create message sender Lambda handler
    - Implement lambda_handler() to process SQS events
    - Poll queue and process messages in batches
    - Apply rate limiting before sending
    - Send messages via WhatsApp client
    - Handle retries with exponential backoff
    - Trigger SMS fallback on exhausted retries
    - Log all messages to DynamoDB
    - Delete successful messages from queue
    - Requeue failed messages with delay
    - _Requirements: 2.1, 2.2, 2.3, 11.1, 12.1, 12.2, 12.3_
  
  - [ ] 13.2 Add structured offer formatting
    - Format buyer offers with crop, quantity, quality, location, price
    - Format processor offers with crop, volume, pickup location
    - Include unique offer IDs
    - Apply language preference
    - _Requirements: 2.1, 2.4, 4.1_
  
  - [ ] 13.3 Add farmer notification formatting
    - Format deal confirmations in Hindi
    - Format payment confirmations in Hindi
    - Format pickup reminders in Hindi
    - Use templates with variable substitution
    - Format monetary amounts with rupee symbol
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 13.4 Write property tests for message sender
    - **Property 5: Buyer offer completeness** - For any buyer outreach, message should contain all required fields
    - **Property 6: Language preference matching** - For any recipient with preference, should use that language
    - **Property 7: Rate-limited sequential sending** - For any multiple recipients, should send with rate limiting
    - **Property 8: Unique offer ID inclusion** - For any offer message, should contain unique ID
    - **Property 14: Processor offer completeness** - For any processor outreach, message should contain all fields
    - **Property 20: Farmer deal confirmation** - For any confirmed deal, notification should be sent
    - **Property 23: Farmer notification language** - For any farmer notification, language should be Hindi
    - **Property 24: Template usage** - For any farmer notification, should use template
    - **Property 25: Monetary amount formatting** - For any amount, should format with rupee symbol
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 4.1, 6.1, 6.4, 6.5, 6.6**
  
  - [ ]* 13.5 Write unit tests for message sender
    - Test batch processing from SQS
    - Test rate limiting integration
    - Test retry logic integration
    - Test SMS fallback trigger
    - Test error logging
    - _Requirements: 1.6, 16.1_

- [ ] 14. Implement webhook handler Lambda function
  - [ ] 14.1 Create webhook handler Lambda
    - Implement lambda_handler() for API Gateway events
    - Validate webhook signature (HMAC-SHA256)
    - Reject invalid signatures with 401
    - Extract message data (sender, content, timestamp)
    - Download media files and upload to S3
    - Route messages by sender type (buyer/processor/farmer)
    - Log all incoming messages to DynamoDB
    - Respond within 2 seconds
    - _Requirements: 9.1, 9.2, 9.3, 9.8_
  
  - [ ] 14.2 Implement message routing logic
    - Query database to identify sender type
    - Route buyer responses to Sell Agent workflow (via EventBridge or direct invoke)
    - Route processor responses to Process Agent workflow
    - Route farmer responses to active session lookup
    - _Requirements: 9.4, 9.5, 9.6_
  
  - [ ] 14.3 Add media handling
    - Download media from WhatsApp API
    - Upload to S3 with organized key structure
    - Store S3 URLs in message log
    - _Requirements: 8.3, 8.4_
  
  - [ ]* 14.4 Write property tests for webhook handler
    - **Property 32: Webhook signature validation** - For any webhook, signature validation should occur
    - **Property 33: Invalid signature rejection** - For any invalid signature, should return 401
    - **Property 34: Message field extraction** - For any incoming message, should extract all fields
    - **Property 35: Buyer response routing** - For any buyer message, should route to Sell Agent
    - **Property 36: Processor response routing** - For any processor message, should route to Process Agent
    - **Property 37: Farmer response routing** - For any farmer message, should route to session
    - **Property 28: Incoming media S3 storage** - For any incoming media, should store in S3
    - **Property 29: Media reference logging** - For any media message, log should contain S3 URLs
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 8.3, 8.4**
  
  - [ ]* 14.5 Write unit tests for webhook handler
    - Test signature validation with valid and invalid signatures
    - Test malformed payload handling
    - Test unknown sender handling
    - Test media download and S3 upload
    - Test response time (should be < 2 seconds)
    - _Requirements: 16.6_

- [ ] 15. Implement language and formatting utilities
  - [ ] 15.1 Create language selection logic
    - Implement get_language() to determine recipient language
    - Default to Hindi for farmers, English for buyers/processors
    - Support explicit language preference override
    - _Requirements: 18.4, 18.5_
  
  - [ ] 15.2 Create formatting utilities
    - Implement format_price() for rupee symbol and number formatting
    - Implement format_date() for Hindi and English
    - Implement format_quantity() with units
    - _Requirements: 6.6_
  
  - [ ]* 15.3 Write property tests for language utilities
    - **Property 65: Default language selection** - For any recipient without preference, should use default based on type
    - **Property 66: Hindi UTF-8 encoding** - For any Hindi message, should use UTF-8
    - **Validates: Requirements 18.1, 18.5**
  
  - [ ]* 15.4 Write unit tests for formatting
    - Test price formatting with various amounts
    - Test date formatting in Hindi and English
    - Test quantity formatting with different units
    - _Requirements: 18.2_

- [ ] 16. Implement security and validation
  - [ ] 16.1 Add phone number validation
    - Implement validate_phone() for Indian mobile format
    - Reject invalid phone numbers before sending
    - Prevent injection attacks
    - _Requirements: 20.7_
  
  - [ ] 16.2 Add sensitive data protection
    - Implement redact_sensitive() for log entries
    - Hash message content in logs (SHA-256)
    - Never log API keys or passwords in plaintext
    - _Requirements: 15.7, 20.5_
  
  - [ ] 16.3 Add request throttling for webhooks
    - Implement rate limiting for webhook endpoint
    - Limit to 1000 requests per second
    - Return 429 for exceeded limits
    - _Requirements: 20.6_
  
  - [ ]* 16.4 Write property tests for security
    - **Property 63: Sensitive data redaction** - For any query without permission, should redact sensitive data
    - **Property 67: Sensitive info logging protection** - For any log entry, no plaintext sensitive info
    - **Property 68: Request throttling** - For any burst of requests, throttling should apply
    - **Property 69: Phone validation before send** - For any send attempt, phone should be validated
    - **Validates: Requirements 15.7, 20.5, 20.6, 20.7**
  
  - [ ]* 16.5 Write unit tests for security
    - Test phone number validation with valid and invalid formats
    - Test sensitive data redaction in various contexts
    - Test webhook throttling behavior
    - Test injection attack prevention
    - _Requirements: 20.1, 20.2, 20.3, 20.4_

- [ ] 17. Implement error handling and logging
  - [ ] 17.1 Add CloudWatch logging
    - Configure structured JSON logging
    - Add correlation IDs for request tracing
    - Implement log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Log all errors with context
    - _Requirements: 16.1_
  
  - [ ] 17.2 Add CloudWatch metrics
    - Emit message send rate metric
    - Emit delivery rate metric
    - Emit error rate metric
    - Emit webhook processing time metric
    - _Requirements: 16.2_
  
  - [ ] 17.3 Configure CloudWatch alarms
    - Create alarm for delivery rate < 95%
    - Create alarm for error rate > 5%
    - Create alarm for queue depth > 1000
    - _Requirements: 16.3, 16.4_
  
  - [ ]* 17.4 Write property tests for error handling
    - **Property 4: API error logging** - For any API error, log entry should exist
    - **Property 49: Retry attempt logging** - For any retry, log entry should exist
    - **Property 50: Successful retry status update** - For any successful retry, status should be "sent"
    - **Property 64: Webhook error logging** - For any webhook error, log entry should exist
    - **Validates: Requirements 1.6, 12.5, 12.6, 16.6**
  
  - [ ]* 17.5 Write unit tests for logging
    - Test structured log format
    - Test correlation ID propagation
    - Test metric emission
    - Test alarm triggering conditions
    - _Requirements: 16.5_

- [ ] 18. Create deployment configuration
  - [ ] 18.1 Create Lambda deployment packages
    - Package message sender Lambda with dependencies
    - Package webhook handler Lambda with dependencies
    - Package SMS fallback Lambda with dependencies
    - Create Lambda layer for shared dependencies
    - _Requirements: 17.4_
  
  - [ ] 18.2 Create infrastructure as code (Terraform or CloudFormation)
    - Define Lambda functions with environment variables
    - Define SQS queues (FIFO and DLQ)
    - Define DynamoDB tables with indexes and TTL
    - Define S3 buckets with encryption
    - Define API Gateway with webhook endpoint
    - Define IAM roles and policies (least privilege)
    - Define CloudWatch log groups and alarms
    - _Requirements: 17.1, 17.2, 17.3, 17.5, 17.6_
  
  - [ ] 18.3 Create environment-specific configurations
    - Development: Gupshup sandbox, reduced rate limits
    - Staging: Gupshup production, test phone numbers
    - Production: Gupshup with Twilio backup, full rate limits
    - _Requirements: 17.7_
  
  - [ ]* 18.4 Write integration tests
    - Test end-to-end message flow (enqueue → send → log)
    - Test webhook → routing → response flow
    - Test retry → SMS fallback flow
    - Test rate limiting across multiple Lambda instances
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6_

- [ ] 19. Final checkpoint - Ensure all tests pass
  - Run all unit tests (target >80% coverage)
  - Run all property tests (100% of 69 properties)
  - Run integration tests
  - Verify deployment configuration
  - Ask the user if questions arise

- [ ] 20. Create documentation
  - [ ] 20.1 Create API documentation
    - Document WhatsApp client interface
    - Document message formats and templates
    - Document webhook payload format
    - Document error codes and responses
  
  - [ ] 20.2 Create deployment guide
    - Document AWS resource setup
    - Document environment variable configuration
    - Document WhatsApp Business API setup (Gupshup/Twilio)
    - Document monitoring and alerting setup
  
  - [ ] 20.3 Create operational runbook
    - Document common issues and resolutions
    - Document monitoring dashboards
    - Document escalation procedures
    - Document backup and recovery procedures

## Notes

- Tasks marked with `*` are optional test-related sub-tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties (69 total)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- Checkpoints ensure incremental validation at key milestones
- All Lambda functions should be tested locally before deployment
- Use LocalStack or moto for local AWS service mocking during development
