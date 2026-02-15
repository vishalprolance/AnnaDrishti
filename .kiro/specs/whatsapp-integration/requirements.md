# Requirements Document

## Introduction

The WhatsApp Integration feature enables Anna Drishti to communicate with buyers, processors, and farmers via WhatsApp Business API. This integration serves as a critical communication channel for the Sell Agent and Process Agent workflows, handling structured offers, response parsing, notifications, and media attachments. The system supports both Hindi and English messaging with SMS fallback for reliability.

The integration handles high-volume messaging (1000+ messages per day per FPO) with strict delivery guarantees, rate limiting compliance, and comprehensive message tracking. All communications are logged for audit trails and compliance purposes.

## Glossary

- **WhatsApp_Client**: The service that interfaces with WhatsApp Business API (via Gupshup or Twilio)
- **Message_Queue**: AWS SQS queue for outbound message processing
- **Message_Log**: DynamoDB table storing all message records with delivery status
- **Webhook_Handler**: AWS Lambda function processing incoming WhatsApp messages
- **Template**: Pre-approved WhatsApp message template for notifications
- **Delivery_Status**: Message delivery state (queued, sent, delivered, read, failed)
- **Rate_Limiter**: Component enforcing WhatsApp API rate limits (80 messages/second)
- **SMS_Fallback**: Backup SMS delivery via Amazon Pinpoint when WhatsApp fails
- **Media_Attachment**: Image or audio file sent via WhatsApp (stored in S3)
- **Buyer**: Verified entity purchasing produce from farmers
- **Processor**: Micro-food-processing unit converting surplus into value-added products
- **Farmer**: Individual farmer member of an FPO
- **Structured_Offer**: Formatted message containing crop, quantity, quality, location, and price details
- **Response_Parser**: Component extracting structured data from natural language responses

## Requirements

### Requirement 1: WhatsApp Business API Integration

**User Story:** As a system integrator, I want to connect to WhatsApp Business API, so that Anna Drishti can send and receive messages via WhatsApp.

#### Acceptance Criteria

1. THE WhatsApp_Client SHALL connect to WhatsApp Business API via Gupshup or Twilio
2. WHEN a connection is established, THE WhatsApp_Client SHALL authenticate using API credentials from environment variables
3. THE WhatsApp_Client SHALL support sending text messages to valid phone numbers
4. THE WhatsApp_Client SHALL support sending template messages with variable substitution
5. THE WhatsApp_Client SHALL support sending media attachments (images and audio files)
6. WHEN an API error occurs, THE WhatsApp_Client SHALL log the error with request details and error code

### Requirement 2: Buyer Outreach Messages

**User Story:** As a Sell Agent, I want to send structured offers to buyers, so that they can review and respond to purchase opportunities.

#### Acceptance Criteria

1. WHEN a buyer outreach is requested, THE WhatsApp_Client SHALL send a message containing crop type, quantity, quality indicators, location, and price
2. THE WhatsApp_Client SHALL format buyer messages in the buyer's preferred language (Hindi or English)
3. WHEN sending to multiple buyers, THE WhatsApp_Client SHALL send messages sequentially with rate limiting
4. THE WhatsApp_Client SHALL include a unique offer ID in each buyer message for response tracking
5. THE Message_Log SHALL record each buyer outreach message with timestamp, buyer ID, and offer details

### Requirement 3: Buyer Response Parsing

**User Story:** As a Sell Agent, I want to parse buyer responses, so that I can extract price offers and terms from natural language messages.

#### Acceptance Criteria

1. WHEN a buyer response is received, THE Response_Parser SHALL extract price information from the message text
2. THE Response_Parser SHALL extract terms information (payment method, pickup timing) from the message text
3. THE Response_Parser SHALL support parsing responses in both Hindi and English
4. WHEN a response contains a price, THE Response_Parser SHALL normalize it to rupees per kilogram
5. WHEN a response is ambiguous or unparseable, THE Response_Parser SHALL flag it for manual review
6. THE Response_Parser SHALL handle common variations (e.g., "28 rupaye", "₹28/kg", "28 per kg")

### Requirement 4: Processor Communication

**User Story:** As a Process Agent, I want to send capacity offers to processors, so that they can confirm or decline processing opportunities.

#### Acceptance Criteria

1. WHEN a processor outreach is requested, THE WhatsApp_Client SHALL send a message containing crop type, volume, pickup location, and processing requirements
2. THE WhatsApp_Client SHALL format processor messages in the processor's preferred language
3. THE WhatsApp_Client SHALL include expected response timeframe in processor messages
4. THE Message_Log SHALL record each processor outreach message with timestamp and processor ID

### Requirement 5: Processor Response Parsing

**User Story:** As a Process Agent, I want to parse processor responses, so that I can identify confirmations and declines.

#### Acceptance Criteria

1. WHEN a processor response is received, THE Response_Parser SHALL classify it as confirmation, decline, or clarification request
2. THE Response_Parser SHALL extract capacity information from confirmation messages
3. THE Response_Parser SHALL extract decline reasons from decline messages
4. THE Response_Parser SHALL support parsing responses in both Hindi and English
5. WHEN a response requests clarification, THE Response_Parser SHALL extract the specific question or concern

### Requirement 6: Farmer Notifications

**User Story:** As a farmer, I want to receive notifications via WhatsApp, so that I stay informed about deal confirmations, payments, and pickup schedules.

#### Acceptance Criteria

1. WHEN a deal is confirmed, THE WhatsApp_Client SHALL send a notification to the farmer with deal details
2. WHEN a payment is received, THE WhatsApp_Client SHALL send a payment confirmation notification to the farmer
3. WHEN a pickup is scheduled, THE WhatsApp_Client SHALL send a pickup reminder notification to the farmer
4. THE WhatsApp_Client SHALL send all farmer notifications in Hindi
5. THE WhatsApp_Client SHALL use pre-approved message templates for farmer notifications
6. WHEN a farmer notification includes monetary amounts, THE WhatsApp_Client SHALL format them with rupee symbol and proper number formatting

### Requirement 7: Message Templates

**User Story:** As a compliance officer, I want to use pre-approved message templates, so that all notifications comply with WhatsApp Business Policy.

#### Acceptance Criteria

1. THE WhatsApp_Client SHALL store message templates with placeholders for variable content
2. WHEN sending a template message, THE WhatsApp_Client SHALL substitute variables with actual values
3. THE WhatsApp_Client SHALL maintain templates in both Hindi and English
4. THE WhatsApp_Client SHALL validate that all required variables are provided before sending
5. WHEN a template is not found, THE WhatsApp_Client SHALL log an error and not send the message

### Requirement 8: Media Support

**User Story:** As a user, I want to send and receive media attachments, so that I can share quality verification images and voice confirmations.

#### Acceptance Criteria

1. WHEN sending an image, THE WhatsApp_Client SHALL upload it to S3 and send the WhatsApp media message with the S3 URL
2. WHEN sending an audio file, THE WhatsApp_Client SHALL upload it to S3 and send the WhatsApp media message with the S3 URL
3. WHEN receiving a media message, THE Webhook_Handler SHALL download the media file and store it in S3
4. THE Message_Log SHALL record media message references with S3 URLs
5. THE WhatsApp_Client SHALL validate media file size limits (16MB for images, 16MB for audio)
6. WHEN a media file exceeds size limits, THE WhatsApp_Client SHALL reject it and log an error

### Requirement 9: Webhook Handling

**User Story:** As a system operator, I want to process incoming WhatsApp messages, so that buyer and processor responses are captured and routed to the appropriate agents.

#### Acceptance Criteria

1. WHEN a webhook request is received, THE Webhook_Handler SHALL validate the request signature
2. WHEN signature validation fails, THE Webhook_Handler SHALL reject the request with 401 status
3. WHEN a message is received, THE Webhook_Handler SHALL extract sender phone number, message content, and timestamp
4. THE Webhook_Handler SHALL route buyer responses to the Sell Agent workflow
5. THE Webhook_Handler SHALL route processor responses to the Process Agent workflow
6. THE Webhook_Handler SHALL route farmer responses to the appropriate active session
7. THE Webhook_Handler SHALL respond to webhook requests within 2 seconds to avoid timeouts
8. THE Message_Log SHALL record all incoming messages with sender, content, and timestamp

### Requirement 10: Message Delivery Tracking

**User Story:** As a system operator, I want to track message delivery status, so that I can monitor delivery rates and identify failures.

#### Acceptance Criteria

1. WHEN a message is queued, THE Message_Log SHALL record it with status "queued"
2. WHEN a message is sent to WhatsApp API, THE Message_Log SHALL update status to "sent"
3. WHEN a delivery receipt is received, THE Message_Log SHALL update status to "delivered"
4. WHEN a read receipt is received, THE Message_Log SHALL update status to "read"
5. WHEN a message fails, THE Message_Log SHALL update status to "failed" and record the error reason
6. THE Message_Log SHALL record timestamps for each status transition
7. THE WhatsApp_Client SHALL provide a query interface to retrieve message status by message ID

### Requirement 11: Rate Limiting

**User Story:** As a system operator, I want to respect WhatsApp rate limits, so that the API connection remains stable and messages are not rejected.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce a maximum of 80 messages per second per phone number
2. WHEN the rate limit is approached, THE Rate_Limiter SHALL queue messages for delayed sending
3. THE Rate_Limiter SHALL distribute messages evenly across the time window to avoid bursts
4. WHEN a rate limit error is received from WhatsApp API, THE Rate_Limiter SHALL back off and retry
5. THE Rate_Limiter SHALL track message counts per phone number with sliding window
6. THE Rate_Limiter SHALL reset counters every second for accurate rate tracking

### Requirement 12: Retry Logic

**User Story:** As a system operator, I want automatic retry for failed messages, so that transient failures do not result in lost communications.

#### Acceptance Criteria

1. WHEN a message send fails with a transient error, THE WhatsApp_Client SHALL retry up to 3 times
2. THE WhatsApp_Client SHALL use exponential backoff for retries (1 second, 2 seconds, 4 seconds)
3. WHEN all retries are exhausted, THE WhatsApp_Client SHALL trigger SMS fallback
4. THE WhatsApp_Client SHALL not retry messages that fail with permanent errors (invalid phone number, blocked user)
5. THE Message_Log SHALL record all retry attempts with timestamps and error details
6. WHEN a retry succeeds, THE Message_Log SHALL update status to "sent" and clear error information

### Requirement 13: SMS Fallback

**User Story:** As a farmer, I want to receive notifications via SMS when WhatsApp fails, so that I do not miss critical information.

#### Acceptance Criteria

1. WHEN a WhatsApp message fails after all retries, THE SMS_Fallback SHALL send the same content via Amazon Pinpoint SMS
2. THE SMS_Fallback SHALL only activate for farmer notifications (not buyer or processor messages)
3. THE SMS_Fallback SHALL format SMS messages to fit within 160 characters when possible
4. WHEN content exceeds 160 characters, THE SMS_Fallback SHALL send multiple SMS messages
5. THE Message_Log SHALL record SMS fallback attempts with delivery status
6. THE SMS_Fallback SHALL send SMS messages in Hindi for farmer communications

### Requirement 14: Message Queue Processing

**User Story:** As a system operator, I want outbound messages processed via queue, so that message sending is decoupled from business logic and can handle high volumes.

#### Acceptance Criteria

1. WHEN a message send is requested, THE WhatsApp_Client SHALL enqueue it to the Message_Queue
2. THE Message_Queue SHALL process messages in FIFO order within each priority level
3. THE WhatsApp_Client SHALL poll the Message_Queue and send messages with rate limiting
4. WHEN a message is successfully sent, THE WhatsApp_Client SHALL delete it from the Message_Queue
5. WHEN a message fails, THE WhatsApp_Client SHALL update its retry count and re-queue it with delay
6. THE Message_Queue SHALL support priority levels (high for farmer notifications, normal for buyer/processor messages)
7. THE Message_Queue SHALL retain failed messages for 7 days for debugging

### Requirement 15: Message Logging and Audit

**User Story:** As a compliance officer, I want comprehensive message logs, so that all communications are auditable and traceable.

#### Acceptance Criteria

1. THE Message_Log SHALL store all outbound messages with sender, recipient, content, and timestamp
2. THE Message_Log SHALL store all inbound messages with sender, recipient, content, and timestamp
3. THE Message_Log SHALL store delivery status transitions with timestamps
4. THE Message_Log SHALL store media attachment references with S3 URLs
5. THE Message_Log SHALL support querying by phone number, date range, and message type
6. THE Message_Log SHALL retain message records for at least 7 years for compliance
7. THE Message_Log SHALL redact sensitive information (prices, personal details) in query results unless explicitly requested

### Requirement 16: Error Handling and Monitoring

**User Story:** As a system operator, I want comprehensive error handling and monitoring, so that I can identify and resolve issues quickly.

#### Acceptance Criteria

1. WHEN any error occurs, THE WhatsApp_Client SHALL log it to CloudWatch with error type, message, and context
2. THE WhatsApp_Client SHALL emit CloudWatch metrics for message send rate, delivery rate, and error rate
3. WHEN delivery rate falls below 95%, THE WhatsApp_Client SHALL trigger a CloudWatch alarm
4. WHEN error rate exceeds 5%, THE WhatsApp_Client SHALL trigger a CloudWatch alarm
5. THE WhatsApp_Client SHALL provide health check endpoints for monitoring
6. THE Webhook_Handler SHALL log all webhook processing errors with request details

### Requirement 17: Configuration and Deployment

**User Story:** As a DevOps engineer, I want flexible configuration, so that the WhatsApp integration can be deployed to AWS Lambda with environment-specific settings.

#### Acceptance Criteria

1. THE WhatsApp_Client SHALL read API credentials from environment variables
2. THE WhatsApp_Client SHALL read rate limit configuration from environment variables
3. THE WhatsApp_Client SHALL read message template configuration from S3 or environment variables
4. THE Webhook_Handler SHALL be deployable as an AWS Lambda function with API Gateway
5. THE Message_Queue SHALL be implemented using AWS SQS
6. THE Message_Log SHALL be implemented using DynamoDB with appropriate indexes
7. THE WhatsApp_Client SHALL support both Gupshup and Twilio providers via configuration

### Requirement 18: Language Support

**User Story:** As a user, I want messages in my preferred language, so that I can understand communications clearly.

#### Acceptance Criteria

1. THE WhatsApp_Client SHALL support sending messages in Hindi using UTF-8 encoding
2. THE WhatsApp_Client SHALL support sending messages in English
3. THE Response_Parser SHALL parse responses in both Hindi and English
4. THE WhatsApp_Client SHALL select language based on recipient's stored language preference
5. WHEN language preference is not set, THE WhatsApp_Client SHALL default to Hindi for farmers and English for buyers/processors
6. THE WhatsApp_Client SHALL maintain separate message templates for each supported language

### Requirement 19: Performance and Scalability

**User Story:** As a system operator, I want the integration to handle high message volumes, so that it can support 1000+ messages per day per FPO.

#### Acceptance Criteria

1. THE WhatsApp_Client SHALL process at least 1000 messages per day per FPO
2. THE Webhook_Handler SHALL process incoming messages within 2 seconds
3. THE Message_Queue SHALL support at least 10,000 queued messages
4. THE Message_Log SHALL support querying message history within 5 seconds for 95% of queries
5. THE WhatsApp_Client SHALL scale horizontally by processing messages from multiple Lambda instances
6. THE Rate_Limiter SHALL coordinate rate limiting across multiple Lambda instances using DynamoDB

### Requirement 20: Security and Privacy

**User Story:** As a security officer, I want secure message handling, so that user data and communications are protected.

#### Acceptance Criteria

1. THE WhatsApp_Client SHALL validate webhook signatures to prevent unauthorized requests
2. THE WhatsApp_Client SHALL encrypt API credentials at rest using AWS KMS
3. THE Message_Log SHALL encrypt message content at rest using DynamoDB encryption
4. THE WhatsApp_Client SHALL transmit all messages over HTTPS
5. THE WhatsApp_Client SHALL not log sensitive information (API keys, passwords) in plaintext
6. THE Webhook_Handler SHALL implement request throttling to prevent abuse
7. THE WhatsApp_Client SHALL validate phone numbers before sending messages to prevent injection attacks
