# Design Document: WhatsApp Integration

## Overview

The WhatsApp Integration provides a robust, scalable communication layer for Anna Drishti, enabling structured messaging with buyers, processors, and farmers via WhatsApp Business API. The system handles high-volume messaging (1000+ messages/day per FPO) with comprehensive delivery tracking, intelligent retry logic, and SMS fallback for reliability.

Key capabilities:
- Structured offer messages to buyers and processors with response parsing
- Farmer notifications in Hindi with template support
- Media handling (images for quality verification, audio for confirmations)
- Webhook processing for incoming messages with <2s response time
- Rate limiting compliance (80 messages/second per number)
- Exponential backoff retry with SMS fallback
- Comprehensive audit logging and delivery tracking

The system is deployed on AWS Lambda with SQS for message queuing, DynamoDB for message logs, and S3 for media storage. It supports both Gupshup and Twilio as WhatsApp Business API providers.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                              │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ WhatsApp     │  │ Buyers/        │  │ Farmers          │   │
│  │ Business API │  │ Processors     │  │                  │   │
│  │ (Gupshup/    │  │ (WhatsApp)     │  │ (WhatsApp/SMS)   │   │
│  │  Twilio)     │  │                │  │                  │   │
│  └──────────────┘  └────────────────┘  └──────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTPS Webhooks
                           │ (Incoming Messages)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WEBHOOK HANDLER (Lambda)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • Signature validation                                     │ │
│  │ • Message extraction (text, media, sender)                 │ │
│  │ • Routing (buyer → Sell Agent, processor → Process Agent)  │ │
│  │ • Response within 2 seconds                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Route to Agent Workflows
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              AGENT WORKFLOWS (Sell/Process Agents)               │
│  • Buyer response parsing                                        │
│  • Processor response parsing                                    │
│  • Farmer response handling                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Send Message Requests
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE SENDER (Lambda)                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Message Enqueue:                                           │ │
│  │ • Validate recipient and content                           │ │
│  │ • Apply priority (high for farmers, normal for others)     │ │
│  │ • Enqueue to SQS                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Message Processing:                                        │ │
│  │ • Poll SQS queue                                           │ │
│  │ • Rate limiting (80 msg/sec per number)                    │ │
│  │ • Template variable substitution                           │ │
│  │ • Media upload to S3 (if applicable)                       │ │
│  │ • Send via WhatsApp API                                    │ │
│  │ • Retry with exponential backoff on failure                │ │
│  │ • SMS fallback for farmer messages                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ API Calls
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WHATSAPP API CLIENT                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Provider Abstraction:                                      │ │
│  │ • Gupshup adapter                                          │ │
│  │ • Twilio adapter                                           │ │
│  │ • Unified interface for send/receive                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Store Logs & Status
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                    │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ SQS              │  │ DynamoDB         │  │ S3           │ │
│  │ (Message Queue)  │  │ (Message Logs)   │  │ (Media)      │ │
│  │                  │  │                  │  │              │ │
│  │ • FIFO ordering  │  │ • Message records│  │ • Images     │ │
│  │ • Priority       │  │ • Delivery status│  │ • Audio      │ │
│  │ • Retry tracking │  │ • Audit trail    │  │ • Templates  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ CloudWatch       │  │ Amazon Pinpoint  │                    │
│  │ (Logs/Metrics)   │  │ (SMS Fallback)   │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Message Flow Diagrams

**Outbound Message Flow:**
```
Agent Request → Validate → Enqueue (SQS) → Rate Limit Check → 
Template Substitution → Send (WhatsApp API) → Log Status (DynamoDB)
                                    ↓ (on failure)
                            Retry (exponential backoff)
                                    ↓ (after 3 retries)
                            SMS Fallback (farmers only)
```

**Inbound Message Flow:**
```
WhatsApp Webhook → Validate Signature → Extract Message → 
Route by Sender Type → Parse Response → Update Agent Workflow → 
Log Message (DynamoDB)
```

## Components and Interfaces

### 1. WhatsApp API Client

**Purpose:** Abstract interface to WhatsApp Business API providers (Gupshup/Twilio).

**Inputs:**
- Message content (text or template with variables)
- Recipient phone number
- Message type (text, template, media)
- Media URL (for image/audio messages)
- Priority level

**Outputs:**
- Message ID (from WhatsApp API)
- Send status (success/failure)
- Error details (if failed)

**Implementation:**
- Provider abstraction layer with Gupshup and Twilio adapters
- Unified interface: `send_text()`, `send_template()`, `send_media()`
- Automatic provider selection based on configuration
- Connection pooling for HTTP requests
- Timeout handling (10 seconds per request)

**Interface:**
```python
class WhatsAppClient:
    def __init__(self, provider: str, api_key: str, phone_number: str):
        """Initialize client with provider (gupshup/twilio)"""
        
    def send_text(self, to: str, message: str) -> SendResult:
        """Send plain text message"""
        
    def send_template(self, to: str, template_name: str, variables: Dict[str, str], language: str) -> SendResult:
        """Send template message with variable substitution"""
        
    def send_media(self, to: str, media_url: str, media_type: str, caption: str = None) -> SendResult:
        """Send image or audio message"""
        
    def validate_webhook(self, signature: str, payload: str) -> bool:
        """Validate incoming webhook signature"""
```

### 2. Message Queue Manager

**Purpose:** Manage outbound message queue with priority and rate limiting.

**Inputs:**
- Message send request (recipient, content, priority)
- Rate limit configuration (messages per second)

**Outputs:**
- Queue position
- Estimated send time
- Enqueue status

**Implementation:**
- AWS SQS FIFO queue for ordering guarantees
- Two priority levels: high (farmer notifications), normal (buyer/processor)
- Message attributes: recipient, content, template_name, variables, priority, retry_count
- Visibility timeout: 30 seconds (for processing)
- Dead letter queue for failed messages after 3 retries
- Batch processing (up to 10 messages per poll)

**Interface:**
```python
class MessageQueueManager:
    def enqueue(self, message: OutboundMessage, priority: str = "normal") -> str:
        """Add message to queue, return queue message ID"""
        
    def dequeue(self, max_messages: int = 10) -> List[QueuedMessage]:
        """Poll queue for messages to send"""
        
    def delete(self, queue_message_id: str) -> None:
        """Remove message from queue after successful send"""
        
    def requeue_with_delay(self, queue_message_id: str, delay_seconds: int) -> None:
        """Re-queue failed message with delay for retry"""
```

### 3. Rate Limiter

**Purpose:** Enforce WhatsApp API rate limits (80 messages/second per phone number).

**Inputs:**
- Phone number (sender)
- Current timestamp

**Outputs:**
- Can send now (boolean)
- Wait time (seconds) if rate limited

**Implementation:**
- DynamoDB table: `rate_limits` with phone_number as partition key
- Sliding window counter: track message count in current second
- Atomic increment using DynamoDB conditional writes
- Reset counter every second using TTL
- Distributed rate limiting across multiple Lambda instances
- Graceful degradation: if DynamoDB unavailable, allow sends (fail open)

**Interface:**
```python
class RateLimiter:
    def __init__(self, max_per_second: int = 80):
        """Initialize with rate limit"""
        
    def check_and_increment(self, phone_number: str) -> RateLimitResult:
        """Check if send allowed, increment counter if yes"""
        
    def get_wait_time(self, phone_number: str) -> float:
        """Get seconds to wait before next send"""
```

### 4. Message Logger

**Purpose:** Store all message records with delivery status for audit and tracking.

**Inputs:**
- Message details (sender, recipient, content, type)
- Delivery status updates
- Error information

**Outputs:**
- Message record with full history
- Query results (by phone, date range, status)

**Implementation:**
- DynamoDB table: `message_logs`
- Partition key: `recipient_phone` (for efficient queries by user)
- Sort key: `timestamp` (for chronological ordering)
- Attributes: message_id, sender_phone, content_hash (not full content for privacy), template_name, status, error_reason, media_urls, retry_count, created_at, updated_at
- GSI: `message_id-index` for lookup by WhatsApp message ID
- GSI: `status-timestamp-index` for queries by delivery status
- Status transitions logged as separate items for audit trail
- TTL: 7 years (2555 days) for compliance

**Interface:**
```python
class MessageLogger:
    def log_outbound(self, message: OutboundMessage, status: str) -> str:
        """Log outbound message, return log ID"""
        
    def log_inbound(self, sender: str, recipient: str, content: str, media_urls: List[str] = None) -> str:
        """Log inbound message, return log ID"""
        
    def update_status(self, log_id: str, status: str, error_reason: str = None) -> None:
        """Update message delivery status"""
        
    def query_by_phone(self, phone: str, start_date: datetime, end_date: datetime) -> List[MessageLog]:
        """Query messages for a phone number"""
        
    def query_by_status(self, status: str, start_date: datetime, end_date: datetime) -> List[MessageLog]:
        """Query messages by delivery status"""
```

### 5. Template Manager

**Purpose:** Manage pre-approved WhatsApp message templates with variable substitution.

**Inputs:**
- Template name
- Language (Hindi/English)
- Variables (key-value pairs)

**Outputs:**
- Rendered message text
- Template validation result

**Implementation:**
- Templates stored in S3 as JSON files (one per language)
- Template format: `{"name": "deal_confirmation", "text": "आपका सौदा पक्का हो गया है। फसल: {crop}, मात्रा: {quantity} किलो, कीमत: ₹{price}/किलो", "variables": ["crop", "quantity", "price"]}`
- Load templates at Lambda cold start, cache in memory
- Variable substitution using string formatting
- Validation: ensure all required variables provided
- Fallback: if template not found, use generic message

**Templates:**
- `buyer_offer_hi` / `buyer_offer_en`: Structured offer to buyer
- `processor_offer_hi` / `processor_offer_en`: Capacity offer to processor
- `deal_confirmation_hi`: Deal confirmation to farmer
- `payment_received_hi`: Payment confirmation to farmer
- `pickup_reminder_hi`: Pickup reminder to farmer

**Interface:**
```python
class TemplateManager:
    def __init__(self, s3_bucket: str, s3_prefix: str):
        """Initialize and load templates from S3"""
        
    def render(self, template_name: str, language: str, variables: Dict[str, str]) -> str:
        """Render template with variables"""
        
    def validate(self, template_name: str, variables: Dict[str, str]) -> bool:
        """Check if all required variables provided"""
        
    def list_templates(self, language: str = None) -> List[str]:
        """List available templates"""
```

### 6. Response Parser

**Purpose:** Extract structured data from natural language buyer/processor responses.

**Inputs:**
- Message text (Hindi or English)
- Context (offer ID, expected response type)

**Outputs:**
- Parsed data (price, terms, confirmation/decline)
- Confidence score
- Ambiguity flag

**Implementation:**
- Regex patterns for common response formats
- Number extraction: "28", "28 rupaye", "₹28", "28/kg"
- Confirmation keywords: "Haan", "Yes", "OK", "Theek hai", "Confirm"
- Decline keywords: "Naa", "No", "Nahi", "Decline", "Cancel"
- Terms extraction: "UPI", "cash", "bank transfer", "tomorrow", "2 days"
- Language detection using character set (Devanagari vs Latin)
- Fallback: if confidence < 0.7, flag for manual review

**Interface:**
```python
class ResponseParser:
    def parse_buyer_response(self, message: str, offer_id: str) -> BuyerResponse:
        """Parse buyer response for price and terms"""
        
    def parse_processor_response(self, message: str, offer_id: str) -> ProcessorResponse:
        """Parse processor response for confirmation/decline"""
        
    def parse_farmer_response(self, message: str, context: str) -> FarmerResponse:
        """Parse farmer response (confirmation, question, etc)"""
        
    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text (₹/kg)"""
        
    def extract_terms(self, text: str) -> Dict[str, str]:
        """Extract payment and timing terms"""
```

### 7. Webhook Handler

**Purpose:** Process incoming WhatsApp messages and route to appropriate workflows.

**Inputs:**
- Webhook payload (from WhatsApp API)
- Signature (for validation)

**Outputs:**
- HTTP 200 response (within 2 seconds)
- Routed message to agent workflow

**Implementation:**
- AWS Lambda function triggered by API Gateway
- Signature validation using HMAC-SHA256
- Extract message data: sender, recipient, content, media URLs, timestamp
- Identify sender type: buyer (from buyer DB), processor (from processor DB), farmer (default)
- Route to appropriate handler:
  - Buyer → Sell Agent negotiation workflow
  - Processor → Process Agent workflow
  - Farmer → Active session lookup
- Download media files from WhatsApp and upload to S3
- Log all incoming messages to DynamoDB
- Respond within 2 seconds to avoid timeout

**Interface:**
```python
class WebhookHandler:
    def handle_webhook(self, event: Dict, context: Dict) -> Dict:
        """Lambda handler for webhook requests"""
        
    def validate_signature(self, signature: str, payload: str) -> bool:
        """Validate webhook signature"""
        
    def extract_message(self, payload: Dict) -> InboundMessage:
        """Extract message data from webhook payload"""
        
    def route_message(self, message: InboundMessage) -> None:
        """Route message to appropriate workflow"""
        
    def download_media(self, media_url: str) -> str:
        """Download media from WhatsApp, upload to S3, return S3 URL"""
```

### 8. SMS Fallback Handler

**Purpose:** Send SMS via Amazon Pinpoint when WhatsApp delivery fails.

**Inputs:**
- Message content
- Recipient phone number
- Original WhatsApp message ID (for tracking)

**Outputs:**
- SMS send status
- SMS message ID

**Implementation:**
- Amazon Pinpoint SMS client
- Only for farmer notifications (not buyer/processor)
- Message truncation: fit within 160 characters if possible
- Multi-part SMS: split longer messages across multiple SMS
- Hindi SMS encoding: UTF-8 support
- Log SMS attempts to DynamoDB with reference to original WhatsApp message

**Interface:**
```python
class SMSFallbackHandler:
    def __init__(self, pinpoint_client, origination_number: str):
        """Initialize with Pinpoint client"""
        
    def send_sms(self, to: str, message: str, original_message_id: str) -> SMSResult:
        """Send SMS fallback"""
        
    def truncate_message(self, message: str, max_length: int = 160) -> str:
        """Truncate message to fit SMS limit"""
        
    def split_message(self, message: str) -> List[str]:
        """Split long message into multiple SMS"""
```

### 9. Retry Manager

**Purpose:** Handle retry logic with exponential backoff for failed messages.

**Inputs:**
- Failed message details
- Current retry count
- Error type (transient vs permanent)

**Outputs:**
- Retry decision (retry/fallback/abandon)
- Delay duration (seconds)

**Implementation:**
- Exponential backoff: 1s, 2s, 4s (3 retries max)
- Permanent error detection: invalid phone number, blocked user, policy violation
- Transient error detection: network timeout, rate limit, server error
- Skip retry for permanent errors
- Trigger SMS fallback after 3 failed retries (farmers only)
- Log all retry attempts with error details

**Interface:**
```python
class RetryManager:
    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """Determine if message should be retried"""
        
    def get_delay(self, retry_count: int) -> int:
        """Calculate exponential backoff delay"""
        
    def is_permanent_error(self, error: Exception) -> bool:
        """Check if error is permanent (no retry)"""
```

## Data Models

### OutboundMessage
```python
class OutboundMessage:
    recipient_phone: str
    message_type: str  # "text" | "template" | "media"
    content: Optional[str]  # For text messages
    template_name: Optional[str]  # For template messages
    template_variables: Optional[Dict[str, str]]
    language: str  # "hi" | "en"
    media_url: Optional[str]  # S3 URL for media
    media_type: Optional[str]  # "image" | "audio"
    priority: str  # "high" | "normal"
    context: Dict[str, Any]  # Offer ID, session ID, etc.
    created_at: datetime
```

### InboundMessage
```python
class InboundMessage:
    sender_phone: str
    recipient_phone: str
    message_type: str  # "text" | "media"
    content: Optional[str]
    media_urls: List[str]  # S3 URLs after download
    timestamp: datetime
    whatsapp_message_id: str
```

### MessageLog
```python
class MessageLog:
    log_id: str  # UUID
    message_id: Optional[str]  # WhatsApp message ID
    direction: str  # "outbound" | "inbound"
    sender_phone: str
    recipient_phone: str
    content_hash: str  # SHA256 hash for privacy
    template_name: Optional[str]
    status: str  # "queued" | "sent" | "delivered" | "read" | "failed"
    error_reason: Optional[str]
    media_urls: List[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    ttl: int  # Unix timestamp for DynamoDB TTL (7 years)
```

### SendResult
```python
class SendResult:
    success: bool
    message_id: Optional[str]
    error: Optional[str]
    error_type: Optional[str]  # "transient" | "permanent"
```

### BuyerResponse
```python
class BuyerResponse:
    offer_id: str
    response_type: str  # "price_offer" | "decline" | "question"
    price: Optional[float]  # ₹/kg
    terms: Dict[str, str]  # payment_method, pickup_time, etc.
    confidence: float  # 0.0-1.0
    needs_clarification: bool
    raw_text: str
```

### ProcessorResponse
```python
class ProcessorResponse:
    offer_id: str
    response_type: str  # "confirm" | "decline" | "clarification"
    capacity: Optional[float]  # tonnes
    decline_reason: Optional[str]
    clarification_question: Optional[str]
    confidence: float
    raw_text: str
```

### FarmerResponse
```python
class FarmerResponse:
    session_id: str
    response_type: str  # "confirmation" | "decline" | "question"
    confirmation: Optional[bool]
    question: Optional[str]
    confidence: float
    raw_text: str
```

### RateLimitResult
```python
class RateLimitResult:
    allowed: bool
    current_count: int
    limit: int
    wait_seconds: float
```

### SMSResult
```python
class SMSResult:
    success: bool
    message_id: Optional[str]
    parts_sent: int  # Number of SMS parts
    error: Optional[str]
```

### QueuedMessage
```python
class QueuedMessage:
    queue_message_id: str  # SQS message ID
    receipt_handle: str  # For deletion
    message: OutboundMessage
    retry_count: int
    enqueued_at: datetime
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.


### Property Reflection

After analyzing all acceptance criteria, I identified several areas of redundancy:

1. **Language support properties (3.3, 5.4, 18.3)**: All refer to parsing responses in Hindi and English - can be combined into one comprehensive property
2. **Template variable substitution (1.4, 7.2)**: Both test the same behavior - combine into one
3. **Media logging (8.4, 15.4)**: Duplicate requirement - use single property
4. **Webhook signature validation (9.1, 20.1)**: Same requirement - single property
5. **Message logging properties**: Several properties about logging can be grouped by message direction (inbound/outbound) rather than having separate properties for each field
6. **Status transition properties (10.1-10.6)**: Can be combined into a single comprehensive property about status transitions
7. **Media upload properties (8.1, 8.2)**: Both test S3 upload before sending - combine into one

After reflection, I've consolidated 80+ testable criteria into 45 unique, non-redundant properties.

### Property 1: Text message sending
*For any* valid phone number and text content, the WhatsApp client should successfully send the message.
**Validates: Requirements 1.3**

### Property 2: Template variable substitution
*For any* template message with all required variables provided, the system should substitute variables and send the message.
**Validates: Requirements 1.4, 7.2**

### Property 3: Media message sending
*For any* valid media file (image or audio) under 16MB, the system should send it via WhatsApp.
**Validates: Requirements 1.5**

### Property 4: API error logging
*For any* WhatsApp API error, a corresponding log entry should exist with error details and request context.
**Validates: Requirements 1.6, 16.1**

### Property 5: Buyer offer message completeness
*For any* buyer outreach request, the sent message should contain crop type, quantity, quality indicators, location, and price.
**Validates: Requirements 2.1**

### Property 6: Language preference matching
*For any* recipient with a stored language preference, messages should be sent in that language.
**Validates: Requirements 2.2, 4.2, 18.4**

### Property 7: Rate-limited sequential sending
*For any* set of messages to multiple recipients, they should be sent sequentially with rate limiting applied.
**Validates: Requirements 2.3**

### Property 8: Unique offer ID inclusion
*For any* buyer or processor outreach message, it should contain a unique offer ID.
**Validates: Requirements 2.4**

### Property 9: Outbound message logging
*For any* outbound message, a log entry should exist with timestamp, recipient, and message details.
**Validates: Requirements 2.5, 4.4, 15.1**

### Property 10: Price extraction from responses
*For any* buyer response containing price information in various formats ("28", "₹28/kg", "28 rupaye"), the parser should extract and normalize it to ₹/kg.
**Validates: Requirements 3.1, 3.4, 3.6**

### Property 11: Terms extraction from responses
*For any* response containing payment or timing terms, the parser should extract them.
**Validates: Requirements 3.2**

### Property 12: Multilingual response parsing
*For any* response in Hindi or English, the parser should successfully extract structured information.
**Validates: Requirements 3.3, 5.4, 18.3**

### Property 13: Ambiguous response flagging
*For any* response with confidence score below 0.7, the system should flag it for manual review.
**Validates: Requirements 3.5**

### Property 14: Processor offer message completeness
*For any* processor outreach request, the sent message should contain crop type, volume, pickup location, and processing requirements.
**Validates: Requirements 4.1**

### Property 15: Response timeframe inclusion
*For any* processor outreach message, it should include an expected response timeframe.
**Validates: Requirements 4.3**

### Property 16: Processor response classification
*For any* processor response, the parser should classify it as confirmation, decline, or clarification request.
**Validates: Requirements 5.1**

### Property 17: Capacity extraction from confirmations
*For any* processor confirmation message, capacity information should be extracted if present.
**Validates: Requirements 5.2**

### Property 18: Decline reason extraction
*For any* processor decline message, the decline reason should be extracted if present.
**Validates: Requirements 5.3**

### Property 19: Clarification question extraction
*For any* response requesting clarification, the specific question or concern should be extracted.
**Validates: Requirements 5.5**

### Property 20: Farmer deal confirmation notification
*For any* confirmed deal, a notification should be sent to the farmer with all deal details.
**Validates: Requirements 6.1**

### Property 21: Farmer payment notification
*For any* payment received event, a payment confirmation notification should be sent to the farmer.
**Validates: Requirements 6.2**

### Property 22: Farmer pickup reminder
*For any* scheduled pickup, a pickup reminder notification should be sent to the farmer.
**Validates: Requirements 6.3**

### Property 23: Farmer notification language
*For any* farmer notification, the language should be Hindi.
**Validates: Requirements 6.4, 13.6**

### Property 24: Template usage for farmer notifications
*For any* farmer notification, a pre-approved template should be used.
**Validates: Requirements 6.5**

### Property 25: Monetary amount formatting
*For any* notification containing monetary amounts, they should be formatted with rupee symbol and proper number formatting.
**Validates: Requirements 6.6**

### Property 26: Template variable validation
*For any* template send attempt, if required variables are missing, the send should fail validation.
**Validates: Requirements 7.4**

### Property 27: Media S3 upload before sending
*For any* media message (image or audio), the file should be uploaded to S3 before the WhatsApp message is sent.
**Validates: Requirements 8.1, 8.2**

### Property 28: Incoming media S3 storage
*For any* incoming media message, the media file should be downloaded and stored in S3.
**Validates: Requirements 8.3**

### Property 29: Media reference logging
*For any* media message (inbound or outbound), the log should contain S3 URLs.
**Validates: Requirements 8.4, 15.4**

### Property 30: Media size validation
*For any* media file, size should be validated against the 16MB limit before sending.
**Validates: Requirements 8.5**

### Property 31: Oversized media rejection
*For any* media file exceeding 16MB, the system should reject it and log an error.
**Validates: Requirements 8.6**

### Property 32: Webhook signature validation
*For any* incoming webhook request, signature validation should occur before processing.
**Validates: Requirements 9.1, 20.1**

### Property 33: Invalid signature rejection
*For any* webhook request with invalid signature, the response should be 401 Unauthorized.
**Validates: Requirements 9.2**

### Property 34: Incoming message field extraction
*For any* incoming message, the system should extract sender phone number, message content, and timestamp.
**Validates: Requirements 9.3**

### Property 35: Buyer response routing
*For any* message from a buyer, it should be routed to the Sell Agent workflow.
**Validates: Requirements 9.4**

### Property 36: Processor response routing
*For any* message from a processor, it should be routed to the Process Agent workflow.
**Validates: Requirements 9.5**

### Property 37: Farmer response routing
*For any* message from a farmer, it should be routed to the appropriate active session.
**Validates: Requirements 9.6**

### Property 38: Inbound message logging
*For any* incoming message, a log entry should exist with sender, content, and timestamp.
**Validates: Requirements 9.8, 15.2**

### Property 39: Message status transitions
*For any* message, status transitions should follow the sequence: queued → sent → delivered → read, with each transition logged with timestamp.
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.6**

### Property 40: Failed message status and error logging
*For any* failed message, the status should be "failed" and the error reason should be recorded.
**Validates: Requirements 10.5**

### Property 41: Message status query
*For any* message ID, the system should be able to retrieve the current status and history.
**Validates: Requirements 10.7**

### Property 42: Rate limit enforcement
*For any* phone number, the message send rate should not exceed 80 messages per second.
**Validates: Requirements 11.1**

### Property 43: Rate limit queueing
*For any* burst of messages exceeding rate limit, excess messages should be queued for delayed sending.
**Validates: Requirements 11.2**

### Property 44: Rate limit error backoff
*For any* rate limit error from WhatsApp API, the system should back off and retry.
**Validates: Requirements 11.4**

### Property 45: Transient error retry limit
*For any* message failing with transient error, retry count should not exceed 3.
**Validates: Requirements 12.1**

### Property 46: Exponential backoff delays
*For any* retry sequence, delays should follow exponential pattern: 1s, 2s, 4s.
**Validates: Requirements 12.2**

### Property 47: SMS fallback after retry exhaustion
*For any* farmer message that fails after 3 retries, SMS fallback should be triggered.
**Validates: Requirements 12.3**

### Property 48: Permanent error no-retry
*For any* message failing with permanent error (invalid phone, blocked user), no retry should occur.
**Validates: Requirements 12.4**

### Property 49: Retry attempt logging
*For any* retry attempt, a log entry should exist with timestamp and error details.
**Validates: Requirements 12.5**

### Property 50: Successful retry status update
*For any* successful retry, message status should be "sent" with error information cleared.
**Validates: Requirements 12.6**

### Property 51: WhatsApp failure SMS fallback
*For any* farmer notification that fails WhatsApp delivery after all retries, the same content should be sent via SMS.
**Validates: Requirements 13.1**

### Property 52: SMS fallback farmer-only restriction
*For any* non-farmer message failure, SMS fallback should not be triggered.
**Validates: Requirements 13.2**

### Property 53: SMS 160-character optimization
*For any* SMS message where content fits within 160 characters, it should be sent as a single SMS.
**Validates: Requirements 13.3**

### Property 54: SMS multi-part splitting
*For any* SMS content exceeding 160 characters, it should be split into multiple SMS messages.
**Validates: Requirements 13.4**

### Property 55: SMS fallback logging
*For any* SMS fallback attempt, a log entry should exist with delivery status.
**Validates: Requirements 13.5**

### Property 56: Message enqueue on send request
*For any* message send request, the message should be enqueued to the message queue.
**Validates: Requirements 14.1**

### Property 57: FIFO ordering within priority
*For any* set of messages at the same priority level, they should be processed in FIFO order.
**Validates: Requirements 14.2**

### Property 58: Successful send queue deletion
*For any* successfully sent message, it should be deleted from the queue.
**Validates: Requirements 14.4**

### Property 59: Failed message requeue with retry count
*For any* failed message, it should be re-queued with incremented retry count and delay.
**Validates: Requirements 14.5**

### Property 60: Priority level assignment
*For any* farmer notification, priority should be "high"; for buyer/processor messages, priority should be "normal".
**Validates: Requirements 14.6**

### Property 61: Status transition timestamp recording
*For any* message status change, a timestamp should be recorded.
**Validates: Requirements 15.3**

### Property 62: Message log query support
*For any* valid query parameters (phone number, date range, message type), matching results should be returned.
**Validates: Requirements 15.5**

### Property 63: Sensitive data redaction
*For any* message log query without explicit permission, sensitive information should be redacted.
**Validates: Requirements 15.7**

### Property 64: Webhook error logging
*For any* webhook processing error, a log entry should exist with request details.
**Validates: Requirements 16.6**

### Property 65: Default language selection
*For any* recipient without language preference, the system should default to Hindi for farmers and English for buyers/processors.
**Validates: Requirements 18.5**

### Property 66: Hindi UTF-8 encoding
*For any* Hindi message, it should be sent with UTF-8 encoding.
**Validates: Requirements 18.1**

### Property 67: Sensitive information logging protection
*For any* log entry, sensitive information (API keys, passwords) should not appear in plaintext.
**Validates: Requirements 20.5**

### Property 68: Request throttling
*For any* burst of webhook requests, throttling should be applied to prevent abuse.
**Validates: Requirements 20.6**

### Property 69: Phone number validation before send
*For any* message send attempt, phone number validation should occur before sending.
**Validates: Requirements 20.7**

## Error Handling

### Error Categories

**1. WhatsApp API Errors**
- **Rate limit exceeded**: Back off and retry with exponential delay
- **Invalid phone number**: Mark as permanent error, do not retry, log for correction
- **Blocked user**: Mark as permanent error, do not retry, notify sender
- **Network timeout**: Retry up to 3 times with exponential backoff
- **Server error (5xx)**: Retry up to 3 times with exponential backoff
- **Authentication failure**: Alert operations team, check credentials

**2. Message Processing Errors**
- **Template not found**: Log error, do not send message, alert operations
- **Missing template variables**: Reject message, return validation error to caller
- **Media file too large**: Reject message, return error to caller
- **Media upload to S3 fails**: Retry upload 3 times, then fail message send
- **Invalid message format**: Reject message, return validation error

**3. Webhook Processing Errors**
- **Invalid signature**: Reject with 401, log suspicious request
- **Malformed payload**: Reject with 400, log for investigation
- **Unknown sender**: Accept message, log as unrouted for manual review
- **Parsing failure**: Accept message, flag for manual review, respond 200 to WhatsApp

**4. Queue and Storage Errors**
- **SQS unavailable**: Retry enqueue 3 times, then fail request with error
- **DynamoDB write failure**: Retry 3 times with exponential backoff
- **DynamoDB read failure**: Retry 3 times, then return cached data if available
- **S3 upload failure**: Retry 3 times, then fail message send

**5. Rate Limiting Errors**
- **DynamoDB rate limit check failure**: Fail open (allow send) to avoid blocking
- **Distributed counter inconsistency**: Use best-effort rate limiting
- **Rate limit exceeded**: Queue message for delayed sending

### Error Recovery Strategies

**Retry with Exponential Backoff:**
- Transient errors: 3 retries with delays of 1s, 2s, 4s
- Network timeouts: 3 retries with delays of 2s, 4s, 8s
- Database deadlocks: 5 retries with jitter to avoid thundering herd

**SMS Fallback:**
- Activated only for farmer notifications after WhatsApp exhausts retries
- Preserves message content with truncation if needed
- Logs fallback attempt for monitoring

**Circuit Breaker:**
- After 10 consecutive failures to WhatsApp API, open circuit for 60 seconds
- During open circuit, queue all messages for later sending
- Half-open state: allow 1 test message after timeout

**Graceful Degradation:**
- Rate limiter unavailable → Allow sends (fail open)
- Template not found → Use fallback generic message
- Media upload fails → Send text-only message with error note

**Dead Letter Queue:**
- Messages failing after 3 retries moved to DLQ
- DLQ retention: 7 days for manual investigation
- Alert operations team when DLQ depth > 100

## Testing Strategy

### Dual Testing Approach

The WhatsApp Integration will use both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of message formatting (e.g., buyer offer with specific crop/price)
- Edge cases (empty messages, special characters, boundary values)
- Error conditions (invalid phone numbers, missing templates, oversized media)
- Integration points (webhook signature validation, S3 upload, DynamoDB writes)
- Provider-specific behavior (Gupshup vs Twilio differences)

**Property-Based Tests** focus on:
- Universal properties across all inputs (e.g., "for any valid phone number, send succeeds")
- Message parsing correctness (e.g., "for any price format, normalization produces ₹/kg")
- Rate limiting behavior (e.g., "for any burst, rate never exceeds 80/sec")
- Retry logic (e.g., "for any transient error, retries follow exponential backoff")
- Status transitions (e.g., "for any message, status follows valid state machine")

### Property-Based Testing Configuration

**Framework**: Use `hypothesis` (Python) for property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test references its design document property
- Tag format: `# Feature: whatsapp-integration, Property {number}: {property_text}`

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

@given(
    phone=st.from_regex(r'\+91[6-9]\d{9}', fullmatch=True),
    message=st.text(min_size=1, max_size=1000)
)
def test_property_1_text_message_sending(phone, message):
    """
    Feature: whatsapp-integration, Property 1: Text message sending
    For any valid phone number and text content, the WhatsApp client 
    should successfully send the message.
    """
    client = WhatsAppClient(provider="gupshup", api_key=TEST_API_KEY)
    result = client.send_text(to=phone, message=message)
    assert result.success is True
    assert result.message_id is not None
```

### Test Coverage Goals

- Unit test coverage: >80% of code
- Property test coverage: 100% of correctness properties (69 properties)
- Integration test coverage: All external service interactions
- End-to-end test coverage: Complete message flows (outbound, inbound, fallback)

### Testing Priorities

**High Priority** (must test before deployment):
1. Message sending and delivery tracking (Properties 1-9)
2. Response parsing accuracy (Properties 10-19)
3. Rate limiting enforcement (Properties 42-44)
4. Retry and fallback logic (Properties 45-55)
5. Webhook signature validation (Properties 32-33)

**Medium Priority** (test during development):
6. Template management (Properties 24-26)
7. Media handling (Properties 27-31)
8. Message routing (Properties 35-37)
9. Queue management (Properties 56-60)
10. Logging and audit (Properties 38-41, 61-64)

**Lower Priority** (test for completeness):
11. Language selection (Properties 6, 23, 65-66)
12. Security features (Properties 67-69)

### Mock and Test Data

**Mocked Services**:
- WhatsApp API (Gupshup/Twilio): Use mock responses for different scenarios
- AWS SQS: Use LocalStack or moto for local testing
- AWS DynamoDB: Use LocalStack or moto for local testing
- AWS S3: Use LocalStack or moto for local testing
- Amazon Pinpoint: Mock SMS sending

**Test Data Generators**:
- Phone numbers: Indian mobile format (+91 followed by 10 digits starting with 6-9)
- Messages: Hindi and English text with various lengths
- Prices: Various formats ("28", "₹28/kg", "28 rupaye per kg")
- Templates: Sample templates with different variable counts
- Media files: Sample images and audio files of various sizes

## Deployment Architecture

### AWS Lambda Functions

**1. Message Sender Lambda**
- **Trigger**: SQS queue (Message_Queue)
- **Batch size**: 10 messages
- **Timeout**: 30 seconds
- **Memory**: 512 MB
- **Concurrency**: 10 (to handle rate limiting across instances)
- **Environment variables**: WHATSAPP_PROVIDER, API_KEY, PHONE_NUMBER, RATE_LIMIT

**2. Webhook Handler Lambda**
- **Trigger**: API Gateway (POST /webhook)
- **Timeout**: 5 seconds (must respond within 2 seconds)
- **Memory**: 256 MB
- **Concurrency**: 50 (handle high webhook volume)
- **Environment variables**: WEBHOOK_SECRET, DYNAMODB_TABLE, S3_BUCKET

**3. SMS Fallback Lambda**
- **Trigger**: SQS queue (SMS_Fallback_Queue)
- **Timeout**: 10 seconds
- **Memory**: 256 MB
- **Concurrency**: 5
- **Environment variables**: PINPOINT_ORIGINATION_NUMBER

### AWS Resources

**SQS Queues**:
- `whatsapp-messages.fifo`: Main message queue (FIFO for ordering)
- `whatsapp-messages-dlq.fifo`: Dead letter queue for failed messages
- `sms-fallback`: SMS fallback queue (standard queue)

**DynamoDB Tables**:
- `message_logs`: Message audit trail
  - Partition key: `recipient_phone` (String)
  - Sort key: `timestamp` (Number)
  - GSI: `message_id-index` (message_id as partition key)
  - GSI: `status-timestamp-index` (status as partition key, timestamp as sort key)
  - TTL attribute: `ttl` (7 years)
- `rate_limits`: Rate limiting counters
  - Partition key: `phone_number` (String)
  - TTL attribute: `ttl` (1 second)

**S3 Buckets**:
- `whatsapp-media-{env}`: Media file storage (images, audio)
- `whatsapp-templates-{env}`: Message template storage

**API Gateway**:
- REST API: `/webhook` endpoint for incoming WhatsApp messages
- Request validation: Signature verification
- Throttling: 1000 requests per second

**CloudWatch**:
- Log groups: `/aws/lambda/message-sender`, `/aws/lambda/webhook-handler`
- Metrics: MessageSendRate, DeliveryRate, ErrorRate
- Alarms: DeliveryRateLow (<95%), ErrorRateHigh (>5%)

### Environment Configuration

**Development**:
- Provider: Gupshup sandbox
- Rate limit: 10 messages/second (sandbox limit)
- SMS fallback: Disabled

**Staging**:
- Provider: Gupshup production
- Rate limit: 80 messages/second
- SMS fallback: Enabled with test phone numbers

**Production**:
- Provider: Gupshup production (with Twilio as backup)
- Rate limit: 80 messages/second
- SMS fallback: Enabled for all farmers
- Multi-region: Primary in ap-south-1 (Mumbai), backup in ap-southeast-1 (Singapore)

## Security Considerations

**API Credentials**:
- Stored in AWS Secrets Manager
- Rotated every 90 days
- Accessed via IAM role (no hardcoded keys)

**Webhook Security**:
- HMAC-SHA256 signature validation
- Request throttling (1000 req/sec)
- IP whitelist (WhatsApp API IPs only)

**Data Encryption**:
- At rest: DynamoDB encryption, S3 encryption (AES-256)
- In transit: TLS 1.2+ for all API calls
- Message content: Hashed in logs (SHA-256)

**Access Control**:
- Lambda execution roles: Least privilege IAM policies
- DynamoDB: Fine-grained access control
- S3: Bucket policies restricting access to Lambda roles only

**Audit and Compliance**:
- All messages logged for 7 years
- CloudTrail enabled for all API calls
- Regular security audits and penetration testing

## Monitoring and Observability

**Key Metrics**:
- Message send rate (messages/second)
- Delivery rate (delivered / sent)
- Error rate (failed / total)
- Webhook processing time (p50, p95, p99)
- Queue depth (messages waiting)
- SMS fallback rate (SMS sent / WhatsApp failed)

**Dashboards**:
- Real-time message flow visualization
- Delivery rate trends (hourly, daily)
- Error breakdown by type
- Rate limiting effectiveness

**Alerts**:
- Delivery rate < 95% (critical)
- Error rate > 5% (warning)
- Queue depth > 1000 (warning)
- Webhook processing time > 2s (warning)
- SMS fallback rate > 10% (warning)

**Logging**:
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs for request tracing
- PII redaction in logs
