"""
Lambda function to list all farmers with their workflows.
Groups workflows by farmer name and provides summary statistics.
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
from collections import defaultdict

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


class FarmerListError(Exception):
    """Custom exception for farmer list errors."""
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


def scan_workflows_with_retry() -> List[Dict]:
    """Scan all workflows from DynamoDB with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            workflows = []
            last_evaluated_key = None
            
            while True:
                if last_evaluated_key:
                    response = table.scan(ExclusiveStartKey=last_evaluated_key)
                else:
                    response = table.scan()
                
                workflows.extend(response.get('Items', []))
                
                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break
            
            publish_metric('WorkflowsScanSuccess')
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
                    publish_metric('WorkflowsScanFailed')
                    raise FarmerListError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('WorkflowsScanFailed')
                raise FarmerListError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('WorkflowsScanFailed')
            raise FarmerListError(f"Unexpected error scanning workflows: {str(e)}")


def group_workflows_by_farmer(workflows: List[Dict]) -> List[Dict]:
    """Group workflows by farmer name and calculate statistics."""
    farmer_map = defaultdict(lambda: {
        'workflows': [],
        'total_quantity': 0,
        'total_plots': 0,
        'crops': set(),
        'locations': set(),
        'latest_workflow': None,
    })
    
    for workflow in workflows:
        farmer_input = workflow.get('farmer_input', {})
        farmer_name = farmer_input.get('farmer_name', 'Unknown')
        
        # Add workflow to farmer
        farmer_map[farmer_name]['workflows'].append(workflow)
        
        # Update statistics
        quantity = float(farmer_input.get('estimated_quantity', 0))
        farmer_map[farmer_name]['total_quantity'] += quantity
        farmer_map[farmer_name]['total_plots'] += 1
        
        crop = farmer_input.get('crop_type', '')
        if crop:
            farmer_map[farmer_name]['crops'].add(crop)
        
        location = farmer_input.get('location', '')
        if location:
            farmer_map[farmer_name]['locations'].add(location)
        
        # Track latest workflow
        created_at = workflow.get('created_at', '')
        if not farmer_map[farmer_name]['latest_workflow'] or created_at > farmer_map[farmer_name]['latest_workflow'].get('created_at', ''):
            farmer_map[farmer_name]['latest_workflow'] = workflow
    
    # Convert to list format
    farmers = []
    for farmer_name, data in farmer_map.items():
        farmers.append({
            'farmer_name': farmer_name,
            'total_workflows': len(data['workflows']),
            'total_quantity_kg': data['total_quantity'],
            'total_plots': data['total_plots'],
            'crops': list(data['crops']),
            'locations': list(data['locations']),
            'latest_workflow_id': data['latest_workflow'].get('workflow_id', '') if data['latest_workflow'] else '',
            'latest_workflow_date': data['latest_workflow'].get('created_at', '') if data['latest_workflow'] else '',
            'latest_status': data['latest_workflow'].get('status', '') if data['latest_workflow'] else '',
        })
    
    # Sort by latest workflow date (most recent first)
    farmers.sort(key=lambda f: f['latest_workflow_date'], reverse=True)
    
    return farmers


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    List all farmers with their workflow statistics.
    
    Query parameters:
    - search: Filter by farmer name (optional)
    - crop: Filter by crop type (optional)
    - location: Filter by location (optional)
    """
    start_time = time.time()
    
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        search_term = query_params.get('search', '').lower()
        crop_filter = query_params.get('crop', '').lower()
        location_filter = query_params.get('location', '').lower()
        
        # Scan all workflows
        workflows = scan_workflows_with_retry()
        
        # Group by farmer
        farmers = group_workflows_by_farmer(workflows)
        
        # Apply filters
        if search_term:
            farmers = [f for f in farmers if search_term in f['farmer_name'].lower()]
        
        if crop_filter:
            farmers = [f for f in farmers if crop_filter in [c.lower() for c in f['crops']]]
        
        if location_filter:
            farmers = [f for f in farmers if location_filter in [l.lower() for l in f['locations']]]
        
        # Convert Decimal to float
        farmers = decimal_to_float(farmers)
        
        # Publish metrics
        publish_metric('FarmersListed', len(farmers))
        latency = (time.time() - start_time) * 1000
        publish_metric('ListFarmersLatency', latency, 'Milliseconds')
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'farmers': farmers,
                'total_count': len(farmers),
                'message': f'Found {len(farmers)} farmers',
            })
        }
        
    except FarmerListError as e:
        publish_metric('FarmerListError')
        print(f"Farmer list error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Farmer list error',
                'details': str(e),
                'message': 'Failed to list farmers',
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
