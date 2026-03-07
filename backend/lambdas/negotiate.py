"""
Lambda function for AI-powered negotiation using OpenAI GPT-4.
Generates counter-offers within guardrails using GPT-4o-mini.
Enhanced with production-grade error handling, retries, and monitoring.
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any
import boto3
from botocore.exceptions import ClientError
import time
import requests

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
OPENAI_MAX_RETRIES = 2  # Fewer retries for OpenAI (costs money)


class NegotiationError(Exception):
    """Custom exception for negotiation errors."""
    pass


class ValidationError(NegotiationError):
    """Exception for input validation errors."""
    pass


class OpenAIError(NegotiationError):
    """Exception for OpenAI API errors."""
    pass

# OpenAI configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')  # Cost-effective model
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# Negotiation constraints
FLOOR_PRICE = 24.0  # ₹/kg - never go below this
MAX_EXCHANGES = 3  # Maximum negotiation rounds


def publish_metric(metric_name: str, value: float = 1.0, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='AnnaDrishti/Negotiation',
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


def validate_input(body: dict) -> dict:
    """Validate negotiation input data."""
    errors = []
    
    if not body.get('workflow_id'):
        errors.append('workflow_id is required')
    
    buyer_offer = body.get('buyer_offer')
    if buyer_offer is not None:
        try:
            offer = float(buyer_offer)
            if offer <= 0 or offer > 1000:
                errors.append('buyer_offer must be between 0 and 1000 ₹/kg')
        except (ValueError, TypeError):
            errors.append('buyer_offer must be a valid number')
    
    exchange_count = body.get('exchange_count', 0)
    try:
        count = int(exchange_count)
        if count < 0 or count >= MAX_EXCHANGES:
            errors.append(f'exchange_count must be between 0 and {MAX_EXCHANGES - 1}')
    except (ValueError, TypeError):
        errors.append('exchange_count must be a valid integer')
    
    if errors:
        raise ValidationError('; '.join(errors))
    
    return body


def invoke_openai(prompt: str) -> str:
    """Invoke OpenAI GPT-4o-mini API with retry logic."""
    if not OPENAI_API_KEY:
        raise OpenAIError("OpenAI API key not configured")
    
    for attempt in range(OPENAI_MAX_RETRIES):
        try:
            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            }
            
            request_body = {
                'model': OPENAI_MODEL,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a skilled agricultural sales agent negotiating on behalf of Indian farmers. Always respond with valid JSON only.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 500,
                'temperature': 0.7,
            }
            
            response = requests.post(
                OPENAI_API_URL,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                publish_metric('OpenAIInvocationSuccess')
                return response_data['choices'][0]['message']['content']
            elif response.status_code == 429 and attempt < OPENAI_MAX_RETRIES - 1:
                # Rate limit - retry with backoff
                delay = RETRY_DELAY * (2 ** attempt)
                print(f"Rate limited, retrying in {delay}s")
                time.sleep(delay)
                continue
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                publish_metric('OpenAIInvocationFailed')
                raise OpenAIError(f"OpenAI API error ({response.status_code}): {error_msg}")
            
        except requests.exceptions.RequestException as e:
            print(f"OpenAI request error (attempt {attempt + 1}/{OPENAI_MAX_RETRIES}): {str(e)}")
            if attempt < OPENAI_MAX_RETRIES - 1:
                delay = RETRY_DELAY * (2 ** attempt)
                print(f"Retrying in {delay}s")
                time.sleep(delay)
                continue
            else:
                publish_metric('OpenAIInvocationFailed')
                raise OpenAIError(f"Failed to connect to OpenAI: {str(e)}")
        
        except Exception as e:
            print(f"OpenAI invocation error: {str(e)}")
            publish_metric('OpenAIInvocationFailed')
            raise OpenAIError(f"Failed to invoke OpenAI: {str(e)}")


def build_negotiation_prompt(context: dict) -> str:
    """Build prompt for Bedrock negotiation."""
    farmer_name = context.get('farmer_name', 'Farmer')
    crop = context.get('crop_type', 'tomato')
    quantity = context.get('quantity_kg', 2300)
    market_price = context.get('market_price', 26.0)
    floor_price = context.get('floor_price', FLOOR_PRICE)
    buyer_offer = context.get('buyer_offer')
    exchange_count = context.get('exchange_count', 0)
    
    prompt = f"""You are a skilled agricultural sales agent negotiating on behalf of {farmer_name}, an Indian farmer.

Context:
- Crop: {quantity} kg of {crop}
- Market price: ₹{market_price}/kg
- Floor price (minimum acceptable): ₹{floor_price}/kg
- Current negotiation round: {exchange_count + 1} of {MAX_EXCHANGES}

"""
    
    if buyer_offer:
        prompt += f"""Buyer's offer: ₹{buyer_offer}/kg

Your task: Generate a counter-offer that:
1. Is between the floor price (₹{floor_price}/kg) and market price (₹{market_price}/kg)
2. Shows willingness to negotiate but protects farmer's interests
3. Is professional and respectful
4. Includes a brief justification (1 sentence)

"""
    else:
        prompt += f"""Your task: Generate an initial offer that:
1. Starts at or slightly below market price (₹{market_price}/kg)
2. Leaves room for negotiation
3. Is professional and respectful
4. Includes a brief justification (1 sentence)

"""
    
    if exchange_count >= MAX_EXCHANGES - 1:
        prompt += f"\nIMPORTANT: This is the final round. Make your best offer.\n"
    
    prompt += """
Format your response as JSON:
{
  "price": <number>,
  "message": "<negotiation message in English>",
  "reasoning": "<brief internal reasoning>"
}

Respond ONLY with valid JSON, no other text."""
    
    return prompt


def parse_openai_response(response_text: str) -> dict:
    """Parse OpenAI response and extract offer."""
    try:
        # Try to extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            return {
                'price': float(data.get('price', 0)),
                'message': data.get('message', ''),
                'reasoning': data.get('reasoning', '')
            }
        else:
            raise ValueError("No JSON found in response")
            
    except Exception as e:
        print(f"Parse error: {str(e)}")
        print(f"Response: {response_text}")
        # Fallback: return a safe default
        return {
            'price': 0,
            'message': 'Unable to generate offer',
            'reasoning': 'Parse error'
        }


def update_workflow_with_retry(workflow_id: str, negotiation_messages: list) -> None:
    """Update workflow in DynamoDB with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            table.update_item(
                Key={'workflow_id': workflow_id},
                UpdateExpression='SET negotiation_messages = :messages, #status = :status, updated_at = :updated',
                ExpressionAttributeNames={
                    '#status': 'status',
                },
                ExpressionAttributeValues={
                    ':messages': negotiation_messages,
                    ':status': 'negotiating',
                    ':updated': datetime.utcnow().isoformat() + 'Z',
                }
            )
            publish_metric('NegotiationCompleted')
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
                    publish_metric('NegotiationFailed')
                    raise NegotiationError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('NegotiationFailed')
                raise NegotiationError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('NegotiationFailed')
            raise NegotiationError(f"Unexpected error updating workflow: {str(e)}")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Generate negotiation counter-offer using OpenAI GPT-4o-mini.
    
    Expected input:
    {
        "workflow_id": "uuid",
        "buyer_offer": 24.5,  # Optional, for counter-offers
        "exchange_count": 0
    }
    """
    start_time = time.time()
    
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Validate input
        validate_input(body)
        
        workflow_id = body.get('workflow_id')
        buyer_offer = body.get('buyer_offer')
        exchange_count = body.get('exchange_count', 0)
        
        # Get workflow from DynamoDB
        response = table.get_item(Key={'workflow_id': workflow_id})
        if 'Item' not in response:
            raise ValidationError('Workflow not found')
        
        workflow = response['Item']
        farmer_input = workflow.get('farmer_input', {})
        market_scan = workflow.get('market_scan', {})
        
        # Get market price (best mandi)
        mandis = market_scan.get('mandis', [])
        market_price = max([float(m.get('net_price', 26.0)) for m in mandis]) if mandis else 26.0
        
        # Build context for OpenAI
        negotiation_context = {
            'farmer_name': farmer_input.get('farmer_name', 'Farmer'),
            'crop_type': farmer_input.get('crop_type', 'tomato'),
            'quantity_kg': float(farmer_input.get('estimated_quantity', 2300)),
            'market_price': market_price,
            'floor_price': FLOOR_PRICE,
            'buyer_offer': buyer_offer,
            'exchange_count': exchange_count,
        }
        
        # Generate prompt
        prompt = build_negotiation_prompt(negotiation_context)
        
        # Invoke OpenAI
        openai_response = invoke_openai(prompt)
        
        # Parse response
        offer = parse_openai_response(openai_response)
        
        # Safety check: enforce floor price
        if offer['price'] < FLOOR_PRICE:
            offer['price'] = FLOOR_PRICE
            offer['message'] = f"I can offer ₹{FLOOR_PRICE}/kg, which is our minimum acceptable price for this quality {farmer_input.get('crop_type', 'produce')}."
        
        # Safety check: don't exceed market price
        if offer['price'] > market_price:
            offer['price'] = market_price
        
        # Create negotiation message
        negotiation_message = {
            'sender': 'agent',
            'message': offer['message'],
            'price_mentioned': Decimal(str(offer['price'])),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'exchange_count': exchange_count,
        }
        
        # Update workflow in DynamoDB
        negotiation_messages = workflow.get('negotiation_messages', [])
        negotiation_messages.append(negotiation_message)
        
        update_workflow_with_retry(workflow_id, negotiation_messages)
        
        # Publish latency metric
        latency = (time.time() - start_time) * 1000
        publish_metric('NegotiationLatency', latency, 'Milliseconds')
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'offer': {
                    'price': offer['price'],
                    'message': offer['message'],
                },
                'exchange_count': exchange_count + 1,
                'max_exchanges': MAX_EXCHANGES,
                'can_continue': exchange_count + 1 < MAX_EXCHANGES,
                'message': 'Counter-offer generated successfully',
            })
        }
        
    except ValidationError as e:
        publish_metric('ValidationError')
        print(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Validation failed',
                'details': str(e),
                'message': 'Invalid input data',
            })
        }
    
    except OpenAIError as e:
        publish_metric('OpenAIError')
        print(f"OpenAI error: {str(e)}")
        return {
            'statusCode': 503,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'AI service unavailable',
                'details': str(e),
                'message': 'Failed to generate counter-offer',
            })
        }
    
    except NegotiationError as e:
        publish_metric('NegotiationError')
        print(f"Negotiation error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Negotiation error',
                'details': str(e),
                'message': 'Failed to process negotiation',
            })
        }
    
    except Exception as e:
        publish_metric('UnexpectedError')
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'message': 'An unexpected error occurred',
            })
        }
