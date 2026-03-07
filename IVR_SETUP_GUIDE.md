# Phase 2: IVR Implementation with Amazon Connect

## Overview

Build a real phone-based IVR system where farmers can call and provide their information in Hindi/Marathi. The system will:
1. Answer incoming calls
2. Collect farmer information (name, crop, quantity, location)
3. Create workflow in DynamoDB
4. Send SMS with dashboard link

**Timeline**: 3-4 days
**Languages**: Hindi (primary), Marathi (secondary)

---

## Architecture

```
Farmer calls → Amazon Connect → Lex Bot (Hindi) → Lambda (process_ivr_input) → DynamoDB → SMS (SNS)
```

**Components**:
1. **Amazon Connect**: Phone system + IVR flow
2. **Amazon Lex**: Voice recognition (Hindi support)
3. **Lambda**: Process farmer input
4. **SNS**: Send SMS with workflow link
5. **Existing Lambdas**: Market scan, surplus detection, negotiation

---

## Step 1: Set Up Amazon Connect Instance (30 mins)

### 1.1 Create Connect Instance

```bashok 
# Via AWS Console
1. Go to Amazon Connect console
2. Click "Create instance"
3. Choose "Store users in Amazon Connect"
4. Instance alias: "anna-drishti-ivr"
5. Admin: Create new admin user
6. Telephony: Enable incoming calls
7. Data storage: Use defaults
8. Review and create
```

### 1.2 Claim Phone Number

```bash
# In Connect console
1. Go to "Channels" → "Phone numbers"
2. Click "Claim a number"
3. Choose country: India (+91)
4. Type: DID (Direct Inward Dialing)
5. Select available number
6. Description: "Anna Drishti Farmer Hotline"
```

**Note**: Indian phone numbers may require additional verification. Alternative: Use toll-free number or US number for testing.

---

## Step 2: Create Lex Bot for Hindi Voice Input (2 hours)

### 2.1 Create Lex Bot

```bash
# Via AWS Console
1. Go to Amazon Lex V2 console
2. Click "Create bot"
3. Bot name: "AnnaDrishtiFarmerBot"
4. IAM role: Create new role
5. COPPA: No
6. Idle session timeout: 5 minutes
```

### 2.2 Add Hindi Language

```bash
# In bot settings
1. Go to "Languages"
2. Click "Add language"
3. Select: Hindi (hi_IN)
4. Voice: Aditi (female) or Raveena (female)
```

### 2.3 Create Intents

#### Intent 1: GreetFarmer
```
Utterances (Hindi):
- नमस्ते
- हैलो
- मुझे मदद चाहिए

Response:
"नमस्ते! मैं अन्ना दृष्टि हूं। मैं आपकी फसल बेचने में मदद करूंगी। कृपया अपना नाम बताएं।"
```

#### Intent 2: CollectFarmerInfo
```
Slots:
1. farmer_name (AMAZON.Person)
   - Prompt: "आपका नाम क्या है?"
   
2. crop_type (Custom: CropType)
   - Values: टमाटर (tomato), प्याज (onion), मिर्च (chili)
   - Prompt: "आप कौन सी फसल बेचना चाहते हैं?"
   
3. quantity (AMAZON.Number)
   - Prompt: "कितने किलो है?"
   
4. plot_area (AMAZON.Number)
   - Prompt: "आपकी जमीन कितने एकड़ है?"
   
5. location (AMAZON.City)
   - Prompt: "आप कहाँ से हैं?"

Confirmation:
"धन्यवाद {farmer_name}। आपकी {quantity} किलो {crop_type} के लिए हम बाजार में सबसे अच्छी कीमत ढूंढेंगे। क्या यह सही है?"

Fulfillment:
- Lambda function: process_ivr_input
```

---

## Step 3: Create Lambda for IVR Processing (1 hour)

### 3.1 Create Lambda Function

<function_calls>
<invoke name="fsWrite">
<parameter name="path">backend/lambdas/process_ivr_input.py"
Lambda function to process IVR input from Amazon Lex.
Collects farmer information via phone call and creates workflow.
"""

import json
import os
import uuid
from datetime import datetime
from decimal import Decimal
import boto3
from typing import Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Crop name mapping (Hindi to English)
CROP_MAPPING = {
    'टमाटर': 'tomato',
    'tamatar': 'tomato',
    'प्याज': 'onion',
    'pyaj': 'onion',
    'मिर्च': 'chili',
    'mirch': 'chili',
}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Process Lex bot input and create workflow.
    
    Expected Lex event structure:
    {
        "sessionState": {
            "intent": {
                "name": "CollectFarmerInfo",
                "slots": {
                    "farmer_name": {"value": {"interpretedValue": "Ramesh"}},
                    "crop_type": {"value": {"interpretedValue": "टमाटर"}},
                    "quantity": {"value": {"interpretedValue": "2300"}},
                    "plot_area": {"value": {"interpretedValue": "2.1"}},
                    "location": {"value": {"interpretedValue": "Sinnar"}}
                }
            }
        }
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract slots from Lex event
        slots = event['sessionState']['intent']['slots']
        
        # Get slot values
        farmer_name = slots.get('farmer_name', {}).get('value', {}).get('interpretedValue', '')
        crop_type_hindi = slots.get('crop_type', {}).get('value', {}).get('interpretedValue', '')
        quantity = float(slots.get('quantity', {}).get('value', {}).get('interpretedValue', 0))
        plot_area = float(slots.get('plot_area', {}).get('value', {}).get('interpretedValue', 0))
        location = slots.get('location', {}).get('value', {}).get('interpretedValue', '')
        
        # Map crop name to English
        crop_type = CROP_MAPPING.get(crop_type_hindi.lower(), 'tomato')
        
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Get current timestamp
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Create workflow state
        workflow_state = {
            'workflow_id': workflow_id,
            'status': 'pending',
            'source': 'ivr',  # Track that this came from IVR
            'farmer_input': {
                'farmer_name': farmer_name,
                'crop_type': crop_type,
                'plot_area': Decimal(str(plot_area)),
                'estimated_quantity': Decimal(str(quantity)),
                'location': location,
            },
            'market_scan': None,
            'surplus_analysis': None,
            'negotiation_messages': [],
            'negotiation_result': None,
            'blended_income': None,
            'created_at': now,
            'updated_at': now,
            'error': None,
        }
        
        # Store in DynamoDB
        table.put_item(Item=workflow_state)
        
        print(f"Created workflow: {workflow_id}")
        
        # Generate dashboard URL
        dashboard_url = os.environ.get('DASHBOARD_URL', 'https://d2ll18l06rc220.cloudfront.net')
        workflow_url = f"{dashboard_url}?workflow_id={workflow_id}"
        
        # Send SMS with workflow link (if phone number available)
        phone_number = event.get('sessionState', {}).get('sessionAttributes', {}).get('phone_number')
        if phone_number:
            send_sms(phone_number, farmer_name, workflow_url)
        
        # Return Lex response
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'],
                    'state': 'Fulfilled'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': f"धन्यवाद {farmer_name}! हमने आपकी जानकारी ले ली है। हम जल्द ही आपको बाजार की कीमतें बताएंगे। आपका वर्कफ्लो नंबर है: {workflow_id[:8]}"
                }
            ]
        }
        
    except Exception as e:
        print(f"Error processing IVR input: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error response to Lex
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'],
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': 'क्षमा करें, कुछ गलत हो गया। कृपया दोबारा कोशिश करें।'
                }
            ]
        }


def send_sms(phone_number: str, farmer_name: str, workflow_url: str):
    """Send SMS with workflow link to farmer."""
    try:
        message = f"Namaste {farmer_name}! Anna Drishti ne aapki jaankari le li hai. Apna workflow de