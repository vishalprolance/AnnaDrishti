"""
Lambda function to process IVR input from Amazon Lex.
Collects farmer information via phone call and creates workflow.
Enhanced with production-grade error handling, retries, and monitoring.
"""

import json
import os
import uuid
from datetime import datetime
from decimal import Decimal
import boto3
from typing import Any
from botocore.exceptions import ClientError
import time

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


class IVRError(Exception):
    """Custom exception for IVR errors."""
    pass


class ValidationError(IVRError):
    """Exception for input validation errors."""
    pass


# Crop name mapping (Hindi/Marathi to English)
CROP_MAPPING = {
    'टमाटर': 'tomato',
    'tamatar': 'tomato',
    'टोमॅटो': 'tomato',
    'प्याज': 'onion',
    'pyaj': 'onion',
    'कांदा': 'onion',
    'मिर्च': 'chili',
    'mirch': 'chili',
    'मिरची': 'chili',
}


def publish_metric(metric_name: str, value: float = 1.0, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='AnnaDrishti/IVR',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    except Exception as e:
        print(f"Failed to publish metric {metric_name}: {str(e)}")


def validate_slots(slots: dict) -> dict:
    """Validate Lex slot values."""
    errors = []
    
    # Extract slot values
    farmer_name = slots.get('farmer_name', {}).get('value', {}).get('interpretedValue', '')
    crop_type = slots.get('crop_type', {}).get('value', {}).get('interpretedValue', '')
    quantity = slots.get('quantity', {}).get('value', {}).get('interpretedValue', '')
    plot_area = slots.get('plot_area', {}).get('value', {}).get('interpretedValue', '')
    location = slots.get('location', {}).get('value', {}).get('interpretedValue', '')
    
    # Validate required fields
    if not farmer_name:
        errors.append('farmer_name is required')
    
    if not crop_type:
        errors.append('crop_type is required')
    
    # Validate numeric fields
    try:
        qty = float(quantity)
        if qty <= 0 or qty > 1000000:
            errors.append('quantity must be between 0 and 1,000,000 kg')
    except (ValueError, TypeError):
        errors.append('quantity must be a valid number')
    
    try:
        area = float(plot_area)
        if area <= 0 or area > 100:
            errors.append('plot_area must be between 0 and 100 acres')
    except (ValueError, TypeError):
        errors.append('plot_area must be a valid number')
    
    if errors:
        raise ValidationError('; '.join(errors))
    
    return {
        'farmer_name': farmer_name,
        'crop_type': crop_type,
        'quantity': float(quantity),
        'plot_area': float(plot_area),
        'location': location or 'Unknown'
    }


def store_workflow_with_retry(workflow_state: dict) -> None:
    """Store workflow in DynamoDB with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            table.put_item(Item=workflow_state)
            publish_metric('IVRWorkflowCreated')
            return
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ProvisionedThroughputExceededException':
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    print(f"Throughput exceeded, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    continue
                else:
                    publish_metric('IVRWorkflowCreationFailed')
                    raise IVRError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('IVRWorkflowCreationFailed')
                raise IVRError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('IVRWorkflowCreationFailed')
            raise IVRError(f"Unexpected error storing workflow: {str(e)}")


def send_sms(phone_number: str, farmer_name: str, workflow_id: str):
    """Send SMS with workflow link to farmer."""
    try:
        dashboard_url = os.environ.get('DASHBOARD_URL', 'https://d2ll18l06rc220.cloudfront.net')
        workflow_url = f"{dashboard_url}?workflow_id={workflow_id}"
        
        # SMS message in Hindi (Romanized for SMS compatibility)
        message = (
            f"Namaste {farmer_name}! "
            f"Anna Drishti ne aapki jaankari le li hai. "
            f"Apna workflow dekhne ke liye: {workflow_url} "
            f"Workflow ID: {workflow_id[:8]}"
        )
        
        sns.publish(
            PhoneNumber=phone_number,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                    'DataType': 'String',
                    'StringValue': 'ANNADRI'
                },
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
        
        publish_metric('SMSSent')
        print(f"SMS sent to {phone_number}")
        
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        publish_metric('SMSFailed')
        # Don't fail the workflow if SMS fails


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
            },
            "sessionAttributes": {
                "phone_number": "+919876543210"
            }
        }
    }
    """
    
    start_time = time.time()
    print(f"Received IVR event: {json.dumps(event)}")
    
    try:
        # Extract slots from Lex event
        slots = event['sessionState']['intent']['slots']
        
        # Validate slots
        validated_data = validate_slots(slots)
        
        # Map crop name to English
        crop_type_input = validated_data['crop_type'].lower()
        crop_type = CROP_MAPPING.get(crop_type_input, crop_type_input)
        
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
                'farmer_name': validated_data['farmer_name'],
                'crop_type': crop_type,
                'plot_area': Decimal(str(validated_data['plot_area'])),
                'estimated_quantity': Decimal(str(validated_data['quantity'])),
                'location': validated_data['location'],
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
        
        # Store in DynamoDB with retry logic
        store_workflow_with_retry(workflow_state)
        
        print(f"Created IVR workflow: {workflow_id}")
        
        # Send SMS with workflow link (if phone number available)
        phone_number = event.get('sessionState', {}).get('sessionAttributes', {}).get('phone_number')
        if phone_number:
            send_sms(phone_number, validated_data['farmer_name'], workflow_id)
        
        # Publish latency metric
        latency = (time.time() - start_time) * 1000
        publish_metric('IVRProcessingLatency', latency, 'Milliseconds')
        
        # Return Lex response (success)
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'],
                    'state': 'Fulfilled'
                },
                'sessionAttributes': event.get('sessionState', {}).get('sessionAttributes', {})
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': (
                        f"धन्यवाद {validated_data['farmer_name']}! "
                        f"हमने आपकी जानकारी ले ली है। "
                        f"हम जल्द ही आपको बाजार की कीमतें बताएंगे। "
                        f"आपका वर्कफ्लो नंबर है: {workflow_id[:8]}"
                    )
                }
            ]
        }
        
    except ValidationError as e:
        publish_metric('ValidationError')
        print(f"Validation error: {str(e)}")
        
        # Return Lex response (validation error)
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
                    'content': 'क्षमा करें, आपकी जानकारी में कुछ गलती है। कृपया दोबारा कोशिश करें।'
                }
            ]
        }
    
    except IVRError as e:
        publish_metric('IVRError')
        print(f"IVR error: {str(e)}")
        
        # Return Lex response (IVR error)
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
                    'content': 'क्षमा करें, कुछ तकनीकी समस्या है। कृपया कुछ देर बाद कोशिश करें।'
                }
            ]
        }
    
    except Exception as e:
        publish_metric('UnexpectedError')
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return Lex response (unexpected error)
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event.get('sessionState', {}).get('intent', {}).get('name', 'CollectFarmerInfo'),
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
