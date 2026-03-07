"""
Lambda function to detect surplus and recommend processing diversion.
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

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


class SurplusDetectionError(Exception):
    """Custom exception for surplus detection errors."""
    pass


class ValidationError(SurplusDetectionError):
    """Exception for input validation errors."""
    pass

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


def publish_metric(metric_name: str, value: float = 1.0, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='AnnaDrishti/SurplusDetection',
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
    """Validate surplus detection input data."""
    errors = []
    
    if not body.get('workflow_id'):
        errors.append('workflow_id is required')
    
    try:
        total_volume = float(body.get('total_volume_kg', 0))
        if total_volume <= 0 or total_volume > 10000000:  # 10,000 tonnes max
            errors.append('total_volume_kg must be between 0 and 10,000,000 kg')
    except (ValueError, TypeError):
        errors.append('total_volume_kg must be a valid number')
    
    if errors:
        raise ValidationError('; '.join(errors))
    
    return body


def update_workflow_with_retry(workflow_id: str, surplus_analysis: dict) -> None:
    """Update workflow in DynamoDB with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
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
            publish_metric('SurplusDetectionCompleted')
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
                    publish_metric('SurplusDetectionFailed')
                    raise SurplusDetectionError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('SurplusDetectionFailed')
                raise SurplusDetectionError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('SurplusDetectionFailed')
            raise SurplusDetectionError(f"Unexpected error updating workflow: {str(e)}")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Detect surplus and recommend processing diversion.
    
    Expected input:
    {
        "workflow_id": "uuid",
        "total_volume_kg": 30000
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
        total_volume_kg = float(body.get('total_volume_kg', 0))
        
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
            publish_metric('SurplusDetected')
        else:
            # All goes to fresh market
            recommended_fresh_kg = total_volume_kg
            recommended_processing_kg = 0
            publish_metric('NoSurplusDetected')
        
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
        
        # Update workflow in DynamoDB with retry logic
        update_workflow_with_retry(workflow_id, surplus_analysis)
        
        # Publish latency metric
        latency = (time.time() - start_time) * 1000
        publish_metric('SurplusDetectionLatency', latency, 'Milliseconds')
        
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
    
    except SurplusDetectionError as e:
        publish_metric('SurplusDetectionError')
        print(f"Surplus detection error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Surplus detection error',
                'details': str(e),
                'message': 'Failed to detect surplus',
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
