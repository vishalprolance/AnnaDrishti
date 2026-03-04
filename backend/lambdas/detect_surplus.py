"""
Lambda function to detect surplus and recommend processing diversion.
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any
import boto3

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Mock processor data for demo
PROCESSORS = [
    {
        'name': 'Sai Agro Processing',
        'capacity_tonnes': Decimal('5.0'),
        'rate_per_kg': Decimal('32.0'),
        'location': 'Sinnar Industrial Area',
    },
    {
        'name': 'Krishi Processing Co.',
        'capacity_tonnes': Decimal('2.0'),
        'rate_per_kg': Decimal('38.0'),
        'location': 'Nashik MIDC',
    },
]

# Mandi capacity threshold (tonnes)
MANDI_CAPACITY_THRESHOLD = 22.0

# Surplus threshold for processing diversion (tonnes)
SURPLUS_THRESHOLD = 3.0


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Detect surplus and recommend processing diversion.
    
    Expected input:
    {
        "workflow_id": "uuid",
        "total_volume_kg": 30000
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        workflow_id = body.get('workflow_id')
        total_volume_kg = float(body.get('total_volume_kg', 0))
        
        if not workflow_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'workflow_id is required'})
            }
        
        # Convert to tonnes
        total_volume_tonnes = total_volume_kg / 1000.0
        mandi_capacity_tonnes = MANDI_CAPACITY_THRESHOLD
        surplus_tonnes = max(0, total_volume_tonnes - mandi_capacity_tonnes)
        
        # Check if surplus exceeds threshold
        has_surplus = surplus_tonnes >= SURPLUS_THRESHOLD
        
        # Calculate recommended split
        if has_surplus:
            # Divert surplus to processing
            recommended_processing_kg = surplus_tonnes * 1000
            recommended_fresh_kg = total_volume_kg - recommended_processing_kg
        else:
            # All goes to fresh market
            recommended_fresh_kg = total_volume_kg
            recommended_processing_kg = 0
        
        # Create surplus analysis
        surplus_analysis = {
            'total_volume_kg': Decimal(str(total_volume_kg)),
            'mandi_capacity_kg': Decimal(str(mandi_capacity_tonnes * 1000)),
            'surplus_kg': Decimal(str(surplus_tonnes * 1000)),
            'has_surplus': has_surplus,
            'recommended_fresh_kg': Decimal(str(recommended_fresh_kg)),
            'recommended_processing_kg': Decimal(str(recommended_processing_kg)),
            'processors': PROCESSORS,
        }
        
        # Update workflow in DynamoDB
        table.update_item(
            Key={'workflow_id': workflow_id},
            UpdateExpression='SET surplus_analysis = :analysis, #status = :status, updated_at = :updated',
            ExpressionAttributeNames={
                '#status': 'status',
            },
            ExpressionAttributeValues={
                ':analysis': surplus_analysis,
                ':status': 'detecting_surplus',
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
                'surplus_analysis': {
                    'total_volume_kg': float(surplus_analysis['total_volume_kg']),
                    'mandi_capacity_kg': float(surplus_analysis['mandi_capacity_kg']),
                    'surplus_kg': float(surplus_analysis['surplus_kg']),
                    'has_surplus': surplus_analysis['has_surplus'],
                    'recommended_fresh_kg': float(surplus_analysis['recommended_fresh_kg']),
                    'recommended_processing_kg': float(surplus_analysis['recommended_processing_kg']),
                    'processors': [{
                        'name': p['name'],
                        'capacity_tonnes': float(p['capacity_tonnes']),
                        'rate_per_kg': float(p['rate_per_kg']),
                        'location': p['location'],
                    } for p in surplus_analysis['processors']],
                },
                'message': f'Surplus detection completed: {"Surplus detected" if has_surplus else "No surplus"}',
            })
        }
        
    except Exception as e:
        print(f"Error detecting surplus: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to detect surplus',
            })
        }
