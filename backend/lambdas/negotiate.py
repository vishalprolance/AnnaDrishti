"""
Lambda function for AI-powered negotiation using AWS Bedrock.
Generates counter-offers within guardrails using Claude 4.5 Haiku.
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any
import boto3

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Bedrock model configuration
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'global.anthropic.claude-haiku-4-5-20251001-v1:0')

# Negotiation constraints
FLOOR_PRICE = 24.0  # ₹/kg - never go below this
MAX_EXCHANGES = 3  # Maximum negotiation rounds


def invoke_bedrock(prompt: str) -> str:
    """Invoke Bedrock Claude 4.5 Haiku model."""
    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        print(f"Bedrock invocation error: {str(e)}")
        raise


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


def parse_bedrock_response(response_text: str) -> dict:
    """Parse Bedrock response and extract offer."""
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


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Generate negotiation counter-offer using Bedrock.
    
    Expected input:
    {
        "workflow_id": "uuid",
        "buyer_offer": 24.5,  # Optional, for counter-offers
        "exchange_count": 0
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        workflow_id = body.get('workflow_id')
        buyer_offer = body.get('buyer_offer')
        exchange_count = body.get('exchange_count', 0)
        
        if not workflow_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'workflow_id is required'})
            }
        
        # Get workflow from DynamoDB
        response = table.get_item(Key={'workflow_id': workflow_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Workflow not found'})
            }
        
        workflow = response['Item']
        farmer_input = workflow.get('farmer_input', {})
        market_scan = workflow.get('market_scan', {})
        
        # Get market price (best mandi)
        mandis = market_scan.get('mandis', [])
        market_price = max([float(m.get('net_price', 26.0)) for m in mandis]) if mandis else 26.0
        
        # Build context for Bedrock
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
        
        # Invoke Bedrock
        bedrock_response = invoke_bedrock(prompt)
        
        # Parse response
        offer = parse_bedrock_response(bedrock_response)
        
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
        
    except Exception as e:
        print(f"Error in negotiation: {str(e)}")
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
                'error': str(e),
                'message': 'Failed to generate counter-offer',
            })
        }
