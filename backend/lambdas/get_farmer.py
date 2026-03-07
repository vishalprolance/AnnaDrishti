"""
Lambda function to get a specific farmer's details and all their workflows.
Enhanced with production-grade error handling and monitoring.
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List
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


class FarmerDetailError(Exception):
    """Custom exception for farmer detail errors."""
    pass


class ValidationError(FarmerDetailError):
    """Exception for input validation errors."""
    pass


def publish_metric(metric_name: str, value: float = 1.0, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='AnnaDrishti/FarmerPortfolio',
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


def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


def scan_farmer_workflows_with_retry(farmer_name: str) -> List[Dict]:
    """Scan all workflows for a specific farmer with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            workflows = []
            last_evaluated_key = None
            
            while True:
                scan_kwargs = {
                    'FilterExpression': 'farmer_input.farmer_name = :name',
                    'ExpressionAttributeValues': {':name': farmer_name}
                }
                
                if last_evaluated_key:
                    scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
                
                response = table.scan(**scan_kwargs)
                workflows.extend(response.get('Items', []))
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            publish_metric('FarmerWorkflowsScanSuccess')
            return workflows
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ProvisionedThroughputExceededException':
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    print(f"Throughput exceeded, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    continue
                else:
                    publish_metric('FarmerWorkflowsScanFailed')
                    raise FarmerDetailError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('FarmerWorkflowsScanFailed')
                raise FarmerDetailError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('FarmerWorkflowsScanFailed')
            raise FarmerDetailError(f"Unexpected error scanning workflows: {str(e)}")


def calculate_farmer_statistics(workflows: List[Dict]) -> Dict:
    """Calculate statistics for a farmer's workflows."""
    if not workflows:
        return {
            'total_workflows': 0,
            'total_quantity_kg': 0,
            'total_plots': 0,
            'crops': [],
            'locations': [],
            'status_breakdown': {},
            'total_income': 0,
        }
    
    total_quantity = 0
    crops = set()
    locations = set()
    status_counts = {}
    total_income = 0
    
    for workflow in workflows:
        farmer_input = workflow.get('farmer_input', {})
        
        # Quantity
        quantity = float(farmer_input.get('estimated_quantity', 0))
        total_quantity += quantity
        
        # Crops
        crop = farmer_input.get('crop_type', '')
        if crop:
            crops.add(crop)
        
        # Locations
        location = farmer_input.get('location', '')
        if location:
            locations.add(location)
        
        # Status
        status = workflow.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Income (if negotiation completed)
        negotiation_result = workflow.get('negotiation_result')
        if negotiation_result:
            final_price = float(negotiation_result.get('final_price', 0))
            total_income += final_price * quantity
    
    return {
        'total_workflows': len(workflows),
        'total_quantity_kg': total_quantity,
        'total_plots': len(workflows),  # Each workflow = 1 plot
        'crops': list(crops),
        'locations': list(locations),
        'status_breakdown': status_counts,
        'total_income': total_income,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Get a specific farmer's details and all their workflows.
    
    Path parameters:
    - farmer_name: Name of the farmer (required)
    
    Query parameters:
    - include_workflows: Include full workflow details (default: true)
    """
    start_time = time.time()
    
    try:
        # Parse path parameters
        path_params = event.get('pathParameters') or {}
        farmer_name = path_params.get('farmer_name', '')
        
        # URL decode the farmer name (API Gateway doesn't auto-decode)
        from urllib.parse import unquote
        farmer_name = unquote(farmer_name)
        
        if not farmer_name:
            raise ValidationError('farmer_name is required')
        
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        include_workflows = query_params.get('include_workflows', 'true').lower() == 'true'
        
        # Get all workflows for this farmer
        workflows = scan_farmer_workflows_with_retry(farmer_name)
        
        if not workflows:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Farmer not found',
                    'message': f'No workflows found for farmer: {farmer_name}',
                })
            }
        
        # Calculate statistics
        statistics = calculate_farmer_statistics(workflows)
        
        # Sort workflows by date (most recent first)
        workflows.sort(key=lambda w: w.get('created_at', ''), reverse=True)
        
        # Prepare response
        response_data = {
            'farmer_name': farmer_name,
            'statistics': statistics,
        }
        
        if include_workflows:
            response_data['workflows'] = decimal_to_float(workflows)
        else:
            # Just include workflow IDs and basic info
            response_data['workflow_summaries'] = [
                {
                    'workflow_id': w.get('workflow_id'),
                    'status': w.get('status'),
                    'created_at': w.get('created_at'),
                    'crop_type': w.get('farmer_input', {}).get('crop_type'),
                    'quantity_kg': float(w.get('farmer_input', {}).get('estimated_quantity', 0)),
                }
                for w in workflows
            ]
        
        # Convert Decimal to float
        response_data = decimal_to_float(response_data)
        
        # Publish metrics
        publish_metric('FarmerDetailRetrieved')
        latency = (time.time() - start_time) * 1000
        publish_metric('GetFarmerLatency', latency, 'Milliseconds')
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'farmer': response_data,
                'message': f'Found {len(workflows)} workflows for {farmer_name}',
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
    
    except FarmerDetailError as e:
        publish_metric('FarmerDetailError')
        print(f"Farmer detail error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Farmer detail error',
                'details': str(e),
                'message': 'Failed to get farmer details',
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
