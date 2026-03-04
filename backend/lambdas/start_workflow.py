"""
Lambda function to start a demo workflow.
Accepts farmer input and creates a workflow in DynamoDB.
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
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)


def convert_to_decimal(obj):
    """Convert floats to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_decimal(item) for item in obj]
    return obj


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Start a new workflow with farmer input.
    
    Expected input:
    {
        "farmer_name": "Ramesh Patil",
        "crop_type": "tomato",
        "plot_area": 2.1,
        "estimated_quantity": 2300,
        "location": "Sinnar, Nashik"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Get current timestamp
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Create workflow state
        workflow_state = {
            'workflow_id': workflow_id,
            'status': 'pending',
            'farmer_input': {
                'farmer_name': body.get('farmer_name', 'Ramesh Patil'),
                'crop_type': body.get('crop_type', 'tomato'),
                'plot_area': Decimal(str(body.get('plot_area', 2.1))),
                'estimated_quantity': Decimal(str(body.get('estimated_quantity', 2300))),
                'location': body.get('location', 'Sinnar, Nashik'),
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
        
        # Generate dashboard URL (will be updated after CloudFront deployment)
        dashboard_url = os.environ.get('DASHBOARD_URL', 'https://placeholder-dashboard-url')
        workflow_url = f"{dashboard_url}?workflow_id={workflow_id}"
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'workflow_id': workflow_id,
                'dashboard_url': workflow_url,
                'message': 'Workflow started successfully',
                'farmer_name': workflow_state['farmer_input']['farmer_name'],
            })
        }
        
    except Exception as e:
        print(f"Error starting workflow: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to start workflow',
            })
        }
