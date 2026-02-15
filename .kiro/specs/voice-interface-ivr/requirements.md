# Requirements Document

## Introduction

The Voice Interface (IVR) enables farmers to interact with Anna Drishti using any phone via voice commands in Hindi. This feature provides an accessible, low-barrier entry point for farmers who may have limited literacy or smartphone access. The IVR system handles inbound calls from farmers signaling harvest intent and outbound calls for deal confirmations, using speech-to-text, intent classification, and text-to-speech technologies with DTMF fallback for reliability.

The system integrates with the Sell Agent workflow to enable complete selling transactions via voice, and with the Process Agent for surplus management inquiries. It supports multi-step conversational flows with session management, ensuring farmers can complete complex interactions over multiple calls if needed.

## Glossary

- **IVR_System**: The Interactive Voice Response system that handles phone-based interactions with farmers
- **STT_Engine**: Speech-to-Text engine (Amazon Transcribe) that converts Hindi voice to text
- **TTS_Engine**: Text-to-Speech engine (Amazon Polly with Aditi voice) that converts text to Hindi voice
- **Intent_Classifier**: Component that determines farmer intent from transcribed text (IndicBERT or rule-based)
- **DTMF_Menu**: Dual-Tone Multi-Frequency menu system for keypad-based navigation
- **Session_Manager**: Component that maintains conversation state across call steps
- **Call_Flow_Handler**: Lambda function that orchestrates IVR logic and integrations
- **Toll_Free_Number**: Dedicated phone number farmers call to access the system
- **Confidence_Score**: Numerical measure (0.0-1.0) of transcription or classification accuracy
- **Entity_Extractor**: Component that identifies specific data (crop type, quantity) from transcribed text
- **Sell_Agent**: The AI workflow that manages the complete selling process from intent to payment
- **Process_Agent**: The AI workflow that manages surplus processing and value addition

## Requirements

### Requirement 1: Toll-Free Number Setup and Call Routing

**User Story:** As a farmer, I want to call a toll-free number, so that I can interact with Anna Drishti without incurring call charges.

#### Acceptance Criteria

1. THE IVR_System SHALL provide a toll-free number accessible from any phone in India
2. WHEN a farmer calls the toll-free number, THE IVR_System SHALL answer within 3 rings
3. WHEN a call is answered, THE IVR_System SHALL play a Hindi greeting message identifying the service
4. THE IVR_System SHALL identify the caller's phone number and look up the associated farmer profile
5. WHEN the caller's phone number is not registered, THE IVR_System SHALL prompt for registration or transfer to coordinator
6. THE IVR_System SHALL support at least 100 concurrent inbound calls
7. WHEN call volume exceeds capacity, THE IVR_System SHALL play a busy message and request callback

### Requirement 2: Hindi Voice Recognition

**User Story:** As a farmer, I want to speak in Hindi, so that I can communicate naturally without language barriers.

#### Acceptance Criteria

1. WHEN a farmer speaks in Hindi, THE STT_Engine SHALL transcribe the audio to text
2. THE STT_Engine SHALL support common Hindi agricultural phrases and vocabulary
3. THE STT_Engine SHALL achieve transcription accuracy greater than 80% for common phrases
4. WHEN transcription is complete, THE STT_Engine SHALL return the text with a confidence score
5. THE STT_Engine SHALL handle regional Hindi accents and variations
6. WHEN audio quality is poor, THE STT_Engine SHALL indicate low confidence rather than producing incorrect transcription
7. THE STT_Engine SHALL process voice input within 3 seconds of speech completion

### Requirement 3: Intent Classification and Entity Extraction

**User Story:** As a system, I want to understand farmer intent from voice input, so that I can route them to the appropriate workflow.

#### Acceptance Criteria

1. WHEN transcribed text is received, THE Intent_Classifier SHALL determine the farmer's intent
2. THE Intent_Classifier SHALL support intents: "sell", "process", "query-price", "query-scheme", "confirm-deal"
3. THE Intent_Classifier SHALL achieve classification accuracy greater than 85%
4. WHEN intent is "sell", THE Entity_Extractor SHALL extract crop type, quantity estimate, and urgency
5. WHEN intent is "process", THE Entity_Extractor SHALL extract crop type and surplus quantity
6. THE Intent_Classifier SHALL return a confidence score with each classification
7. WHEN confidence score is below 0.7, THE IVR_System SHALL fall back to DTMF menu
8. THE Entity_Extractor SHALL handle variations in crop names and Hindi spellings

### Requirement 4: Text-to-Speech Response Generation

**User Story:** As a farmer, I want to hear responses in natural Hindi, so that I can understand the system's messages clearly.

#### Acceptance Criteria

1. WHEN the system needs to respond, THE TTS_Engine SHALL convert text to Hindi speech
2. THE TTS_Engine SHALL use Amazon Polly's Aditi voice for natural-sounding Hindi
3. THE TTS_Engine SHALL speak at a moderate pace suitable for phone conversations
4. THE TTS_Engine SHALL pronounce numbers, prices, and quantities correctly in Hindi
5. THE TTS_Engine SHALL handle mixed Hindi-English text for technical terms
6. WHEN generating speech, THE TTS_Engine SHALL complete within 2 seconds for messages up to 100 words
7. THE TTS_Engine SHALL support SSML tags for pauses, emphasis, and pronunciation control

### Requirement 5: DTMF Fallback Menu

**User Story:** As a farmer with poor network connectivity, I want to use keypad options, so that I can interact with the system when voice recognition fails.

#### Acceptance Criteria

1. WHEN voice confidence is below 0.7, THE IVR_System SHALL present a DTMF menu
2. THE DTMF_Menu SHALL offer options: 1 for sell, 2 for process, 3 for price query, 9 for coordinator
3. WHEN a farmer presses a key, THE IVR_System SHALL capture the DTMF input within 1 second
4. THE DTMF_Menu SHALL support multi-level navigation for crop selection and quantity input
5. WHEN no input is received for 10 seconds, THE DTMF_Menu SHALL repeat the options once
6. WHEN no input is received after repeat, THE IVR_System SHALL transfer to coordinator or end call
7. THE DTMF_Menu SHALL allow farmers to return to the previous menu level by pressing *

### Requirement 6: Session Management for Multi-Step Interactions

**User Story:** As a farmer, I want the system to remember my conversation context, so that I don't have to repeat information if the call is interrupted.

#### Acceptance Criteria

1. WHEN a call starts, THE Session_Manager SHALL create a session record with unique session ID
2. THE Session_Manager SHALL store session state including current step, farmer ID, and collected data
3. THE Session_Manager SHALL set a time-to-live of 30 minutes for each session
4. WHEN a farmer calls back within 30 minutes, THE Session_Manager SHALL resume from the last completed step
5. WHEN session data is updated, THE Session_Manager SHALL persist changes to Redis immediately
6. WHEN a session expires, THE Session_Manager SHALL automatically remove the session data
7. THE Session_Manager SHALL support concurrent sessions for the same farmer across different intents

### Requirement 7: Integration with Sell Agent Workflow

**User Story:** As a farmer, I want to complete the entire selling process via voice, so that I can sell my produce without using a smartphone.

#### Acceptance Criteria

1. WHEN intent is "sell", THE IVR_System SHALL initiate the Sell Agent workflow
2. THE IVR_System SHALL pass extracted entities (crop, quantity, urgency) to the Sell Agent
3. WHEN the Sell Agent requires clarification, THE IVR_System SHALL prompt the farmer via voice
4. WHEN the Sell Agent completes market scanning, THE IVR_System SHALL present top 2 mandi options via voice
5. WHEN the Sell Agent finds aggregation partners, THE IVR_System SHALL explain the opportunity and request confirmation
6. WHEN the Sell Agent receives a buyer offer, THE IVR_System SHALL call the farmer for deal confirmation
7. THE IVR_System SHALL record farmer confirmation audio and pass reference to Sell Agent

### Requirement 8: Integration with Process Agent Workflow

**User Story:** As a farmer with surplus produce, I want to inquire about processing options via voice, so that I can explore value addition opportunities.

#### Acceptance Criteria

1. WHEN intent is "process", THE IVR_System SHALL initiate the Process Agent workflow
2. THE IVR_System SHALL pass extracted entities (crop, surplus quantity) to the Process Agent
3. WHEN the Process Agent identifies processing options, THE IVR_System SHALL present them via voice
4. WHEN the Process Agent calculates processing costs, THE IVR_System SHALL explain the breakdown in Hindi
5. THE IVR_System SHALL allow farmers to request callback from processor via voice confirmation

### Requirement 9: Outbound Confirmation Calls

**User Story:** As a farmer, I want to receive calls for important confirmations, so that I don't miss deal opportunities.

#### Acceptance Criteria

1. WHEN the Sell Agent has a deal pending confirmation, THE IVR_System SHALL initiate an outbound call
2. THE IVR_System SHALL attempt outbound calls up to 3 times with 15-minute intervals
3. WHEN the farmer answers, THE IVR_System SHALL present deal details via TTS in Hindi
4. THE IVR_System SHALL include: buyer name, price per kg, total quantity, pickup time, payment terms
5. WHEN presenting the deal, THE IVR_System SHALL request explicit confirmation via voice or DTMF
6. THE IVR_System SHALL accept "Haan" (yes) or DTMF 1 as confirmation
7. THE IVR_System SHALL accept "Naa" (no) or DTMF 2 as rejection
8. WHEN confirmation is ambiguous, THE IVR_System SHALL request clarification via DTMF menu
9. THE IVR_System SHALL record the confirmation audio and store reference in S3
10. WHEN the farmer doesn't answer after 3 attempts, THE IVR_System SHALL notify via SMS and WhatsApp

### Requirement 10: Call Duration and Efficiency

**User Story:** As a farmer, I want interactions to be quick and efficient, so that I don't spend excessive time on calls.

#### Acceptance Criteria

1. THE IVR_System SHALL complete simple transactions (price query) within 1 minute
2. THE IVR_System SHALL complete sell intent capture within 3 minutes
3. THE IVR_System SHALL complete deal confirmation calls within 2 minutes
4. WHEN a call exceeds 10 minutes, THE IVR_System SHALL offer to transfer to coordinator
5. THE IVR_System SHALL minimize repeated prompts and confirmations
6. THE IVR_System SHALL allow farmers to interrupt TTS playback by speaking or pressing keys

### Requirement 11: Call Quality and Reliability

**User Story:** As a farmer, I want clear audio quality and reliable connections, so that I can communicate effectively.

#### Acceptance Criteria

1. THE IVR_System SHALL maintain audio quality with minimal latency (< 300ms)
2. WHEN network quality degrades, THE IVR_System SHALL automatically fall back to DTMF menu
3. THE IVR_System SHALL detect call drops and mark sessions for resumption
4. WHEN a call drops, THE IVR_System SHALL send SMS with callback number and session reference
5. THE IVR_System SHALL support call recording for quality assurance and dispute resolution
6. THE IVR_System SHALL store call recordings in S3 with 90-day retention
7. WHEN audio is unclear, THE IVR_System SHALL request farmer to repeat rather than guessing

### Requirement 12: Analytics and Monitoring

**User Story:** As an FPO coordinator, I want to track IVR usage and performance, so that I can identify issues and improve the system.

#### Acceptance Criteria

1. THE IVR_System SHALL log all calls with: farmer ID, duration, intent, completion status, timestamp
2. THE IVR_System SHALL track voice recognition accuracy per call
3. THE IVR_System SHALL track DTMF fallback rate
4. THE IVR_System SHALL track call completion rate (successful intent handling)
5. THE IVR_System SHALL track average call duration by intent type
6. THE IVR_System SHALL provide daily summary reports of call volume and success rates
7. WHEN voice recognition accuracy drops below 70%, THE IVR_System SHALL trigger an alert

### Requirement 13: Error Handling and Graceful Degradation

**User Story:** As a farmer, I want the system to handle errors gracefully, so that I can still complete my task even when technical issues occur.

#### Acceptance Criteria

1. WHEN the STT_Engine fails, THE IVR_System SHALL fall back to DTMF menu immediately
2. WHEN the TTS_Engine fails, THE IVR_System SHALL use pre-recorded audio messages
3. WHEN the Intent_Classifier fails, THE IVR_System SHALL present the main DTMF menu
4. WHEN Redis session store is unavailable, THE IVR_System SHALL operate in stateless mode with reduced functionality
5. WHEN the Sell Agent API is unavailable, THE IVR_System SHALL inform the farmer and offer coordinator callback
6. WHEN database connection fails, THE IVR_System SHALL retry 3 times with exponential backoff
7. WHEN all retries fail, THE IVR_System SHALL apologize in Hindi and provide coordinator contact number

### Requirement 14: Security and Privacy

**User Story:** As a farmer, I want my conversations to be secure and private, so that my business information is protected.

#### Acceptance Criteria

1. THE IVR_System SHALL encrypt all call recordings at rest using AES-256
2. THE IVR_System SHALL encrypt call data in transit using TLS 1.2 or higher
3. THE IVR_System SHALL authenticate farmers by phone number before accessing sensitive information
4. WHEN accessing transaction history, THE IVR_System SHALL require additional PIN verification
5. THE IVR_System SHALL not store credit card or bank account numbers in call recordings
6. THE IVR_System SHALL comply with Indian telecom regulations for call recording and consent
7. THE IVR_System SHALL allow farmers to request deletion of their call recordings

### Requirement 15: Scalability and Performance

**User Story:** As a system administrator, I want the IVR to scale efficiently, so that it can handle peak call volumes during harvest season.

#### Acceptance Criteria

1. THE IVR_System SHALL support 100 concurrent calls per FPO
2. THE IVR_System SHALL scale automatically when concurrent calls exceed 80% of capacity
3. THE IVR_System SHALL maintain response times under 3 seconds for STT processing under peak load
4. THE IVR_System SHALL maintain response times under 2 seconds for TTS generation under peak load
5. THE Call_Flow_Handler SHALL execute within Lambda timeout limits (15 minutes maximum)
6. THE IVR_System SHALL handle at least 1000 calls per day per FPO
7. WHEN scaling events occur, THE IVR_System SHALL log metrics for capacity planning

