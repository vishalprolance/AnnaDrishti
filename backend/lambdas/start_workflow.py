"""
Lambda function to start a demo workflow.
Accepts farmer input and creates a workflow in DynamoDB.
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
cloudwatch = boto3.client('cloudwatch')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


class WorkflowError(Exception):
    """Custom exception for workflow errors."""
    pass


class ValidationError(WorkflowError):
    """Exception for input validation errors."""
    pass


def publish_metric(metric_name: str, value: float = 1.0, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='AnnaDrishti/Workflows',
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


def validate_farmer_input(body: dict) -> dict:
    """Validate farmer input data."""
    errors = []
    
    # Required fields
    if not body.get('farmer_name'):
        errors.append('farmer_name is required')
    
    if not body.get('crop_type'):
        errors.append('crop_type is required')
    
    # Numeric validations
    try:
        plot_area = float(body.get('plot_area', 0))
        if plot_area <= 0 or plot_area > 100:
            errors.append('plot_area must be between 0 and 100 acres')
    except (ValueError, TypeError):
        errors.append('plot_area must be a valid number')
    
    try:
        quantity = float(body.get('estimated_quantity', 0))
        if quantity <= 0 or quantity > 1000000:
            errors.append('estimated_quantity must be between 0 and 1,000,000 kg')
    except (ValueError, TypeError):
        errors.append('estimated_quantity must be a valid number')
    
    if errors:
        raise ValidationError('; '.join(errors))
    
    return body


def convert_to_decimal(obj):
    """Convert floats to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_decimal(item) for item in obj]
    return obj


def store_workflow_with_retry(workflow_state: dict) -> None:
    """Store workflow in DynamoDB with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            table.put_item(Item=workflow_state)
            publish_metric('WorkflowCreated')
            return
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ProvisionedThroughputExceededException':
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    print(f"Throughput exceeded, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    continue
                else:
                    publish_metric('WorkflowCreationFailed')
                    raise WorkflowError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('WorkflowCreationFailed')
                raise WorkflowError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('WorkflowCreationFailed')
            raise WorkflowError(f"Unexpected error storing workflow: {str(e)}")


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
    start_time = time.time()
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Validate input
        validate_farmer_input(body)
        
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Get current timestamp
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Create workflow state
        workflow_state = {
            'workflow_id': workflow_id,
            'status': 'pending',
            'farmer_input': {
                'farmer_name': body.get('farmer_name'),
                'crop_type': body.get('crop_type'),
                'plot_area': Decimal(str(body.get('plot_area'))),
                'estimated_quantity': Decimal(str(body.get('estimated_quantity'))),
                'location': body.get('location', ''),
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
        
        # Generate dashboard URL
        dashboard_url = os.environ.get('DASHBOARD_URL', 'https://d2ll18l06rc220.cloudfront.net')
        workflow_url = f"{dashboard_url}?workflow_id={workflow_id}"
        
        # Publish latency metric
        latency = (time.time() - start_time) * 1000  # milliseconds
        publish_metric('WorkflowCreationLatency', latency, 'Milliseconds')
        
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
    
    except WorkflowError as e:
        publish_metric('WorkflowError')
        print(f"Workflow error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Workflow error',
                'details': str(e),
                'message': 'Failed to create workflow',
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
