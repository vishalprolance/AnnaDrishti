"""
Lambda function to get payment metrics across all workflows.
Provides statistics on payment status, delays, and amounts.
Enhanced with production-grade error handling and monitoring.
"""

import json
import os
from datetime import datetime, timedelta
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
PAYMENT_DELAY_THRESHOLD_HOURS = 48


class PaymentMetricsError(Exception):
    """Custom exception for payment metrics errors."""
    pass


def publish_metric(metric_name: str, value: float = 1.0, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='AnnaDrishti/Payments',
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
            
            publish_metric('PaymentMetricsScanSuccess')
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
                    publish_metric('PaymentMetricsScanFailed')
                    raise PaymentMetricsError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('PaymentMetricsScanFailed')
                raise PaymentMetricsError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('PaymentMetricsScanFailed')
            raise PaymentMetricsError(f"Unexpected error scanning workflows: {str(e)}")


def check_payment_delay(workflow: dict) -> bool:
    """Check if payment is delayed beyond threshold."""
    created_at = workflow.get('created_at', '')
    if not created_at:
        return False
    
    try:
        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        current_time = datetime.utcnow().replace(tzinfo=created_time.tzinfo)
        hours_elapsed = (current_time - created_time).total_seconds() / 3600
        
        return hours_elapsed > PAYMENT_DELAY_THRESHOLD_HOURS
    except Exception as e:
        print(f"Error checking payment delay: {str(e)}")
        return False


def calculate_payment_metrics(workflows: List[Dict]) -> Dict:
    """Calculate payment metrics from workflows."""
    metrics = {
        'total_workflows': len(workflows),
        'payment_status_breakdown': {
            'pending': 0,
            'confirmed': 0,
            'failed': 0,
            'delayed': 0,
            'no_payment_info': 0,
        },
        'total_amount_pending': 0,
        'total_amount_confirmed': 0,
        'total_amount_failed': 0,
        'delayed_payments': [],
        'recent_payments': [],
    }
    
    for workflow in workflows:
        payment_info = workflow.get('payment_info', {})
        
        if not payment_info:
            # Check if workflow is old enough to be considered delayed
            is_delayed = check_payment_delay(workflow)
            if is_delayed:
                metrics['payment_status_breakdown']['delayed'] += 1
                metrics['delayed_payments'].append({
                    'workflow_id': workflow.get('workflow_id'),
                    'farmer_name': workflow.get('farmer_input', {}).get('farmer_name', 'Unknown'),
                    'created_at': workflow.get('created_at'),
                    'status': 'no_payment_info',
                })
            else:
                metrics['payment_status_breakdown']['no_payment_info'] += 1
            continue
        
        # Count by status
        status = payment_info.get('status', 'pending')
        metrics['payment_status_breakdown'][status] = metrics['payment_status_breakdown'].get(status, 0) + 1
        
        # Sum amounts by status
        amount = float(payment_info.get('amount', 0)) if payment_info.get('amount') else 0
        
        if status == 'pending':
            metrics['total_amount_pending'] += amount
        elif status == 'confirmed':
            metrics['total_amount_confirmed'] += amount
            # Add to recent payments
            metrics['recent_payments'].append({
                'workflow_id': workflow.get('workflow_id'),
                'farmer_name': workflow.get('farmer_input', {}).get('farmer_name', 'Unknown'),
                'amount': amount,
                'payment_date': payment_info.get('payment_date', ''),
                'transaction_id': payment_info.get('transaction_id', ''),
            })
        elif status == 'failed':
            metrics['total_amount_failed'] += amount
        
        # Check for delayed payments
        if payment_info.get('is_delayed') or (status == 'pending' and check_payment_delay(workflow)):
            metrics['payment_status_breakdown']['delayed'] += 1
            metrics['delayed_payments'].append({
                'workflow_id': workflow.get('workflow_id'),
                'farmer_name': workflow.get('farmer_input', {}).get('farmer_name', 'Unknown'),
                'amount': amount,
                'created_at': workflow.get('created_at'),
                'status': status,
            })
    
    # Sort recent payments by date (most recent first)
    metrics['recent_payments'].sort(key=lambda p: p.get('payment_date', ''), reverse=True)
    metrics['recent_payments'] = metrics['recent_payments'][:10]  # Keep only 10 most recent
    
    # Sort delayed payments by creation date (oldest first)
    metrics['delayed_payments'].sort(key=lambda p: p.get('created_at', ''))
    
    return metrics


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Get payment metrics across all workflows.
    
    Returns statistics on payment status, delays, and amounts.
    """
    start_time = time.time()
    
    try:
        # Scan all workflows
        workflows = scan_workflows_with_retry()
        
        # Calculate metrics
        metrics = calculate_payment_metrics(workflows)
        
        # Convert Decimal to float
        metrics = decimal_to_float(metrics)
        
        # Publish metrics
        publish_metric('PaymentMetricsCalculated')
        publish_metric('DelayedPaymentsCount', len(metrics['delayed_payments']))
        latency = (time.time() - start_time) * 1000
        publish_metric('PaymentMetricsLatency', latency, 'Milliseconds')
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'metrics': metrics,
                'message': f'Payment metrics calculated for {metrics["total_workflows"]} workflows',
            })
        }
        
    except PaymentMetricsError as e:
        publish_metric('PaymentMetricsError')
        print(f"Payment metrics error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Payment metrics error',
                'details': str(e),
                'message': 'Failed to calculate payment metrics',
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
