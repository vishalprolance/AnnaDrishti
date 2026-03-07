"""
Lambda function to update payment status for a workflow.
Tracks payment confirmation, amount, and timestamp.
Enhanced with production-grade error handling and monitoring.
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
sns = boto3.client('sns')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
PAYMENT_DELAY_THRESHOLD_HOURS = 48  # Flag payments delayed > 48 hours


class PaymentError(Exception):
    """Custom exception for payment errors."""
    pass


class ValidationError(PaymentError):
    """Exception for input validation errors."""
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


def validate_payment_data(body: dict) -> dict:
    """Validate payment update data."""
    errors = []
    
    if not body.get('workflow_id'):
        errors.append('workflow_id is required')
    
    payment_status = body.get('payment_status', '').lower()
    valid_statuses = ['pending', 'confirmed', 'failed', 'delayed']
    if payment_status and payment_status not in valid_statuses:
        errors.append(f'payment_status must be one of: {", ".join(valid_statuses)}')
    
    if body.get('payment_amount'):
        try:
            amount = float(body.get('payment_amount'))
            if amount <= 0:
                errors.append('payment_amount must be greater than 0')
        except (ValueError, TypeError):
            errors.append('payment_amount must be a valid number')
    
    if errors:
        raise ValidationError('; '.join(errors))
    
    return body


def update_payment_with_retry(workflow_id: str, payment_data: dict) -> None:
    """Update payment information in DynamoDB with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            table.update_item(
                Key={'workflow_id': workflow_id},
                UpdateExpression='SET payment_info = :payment, updated_at = :updated',
                ExpressionAttributeValues={
                    ':payment': payment_data,
                    ':updated': datetime.utcnow().isoformat() + 'Z',
                }
            )
            publish_metric('PaymentUpdated')
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
                    publish_metric('PaymentUpdateFailed')
                    raise PaymentError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('PaymentUpdateFailed')
                raise PaymentError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('PaymentUpdateFailed')
            raise PaymentError(f"Unexpected error updating payment: {str(e)}")


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


def send_payment_alert(workflow_id: str, farmer_name: str, amount: float):
    """Send SNS alert for delayed payment."""
    try:
        message = (
            f"Payment Alert: Payment for workflow {workflow_id[:8]} "
            f"to farmer {farmer_name} (₹{amount:,.2f}) is delayed beyond 48 hours."
        )
        
        # In production, this would send to an SNS topic
        # For now, just log it
        print(f"Payment alert: {message}")
        publish_metric('PaymentAlertSent')
        
    except Exception as e:
        print(f"Failed to send payment alert: {str(e)}")
        publish_metric('PaymentAlertFailed')


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Update payment status for a workflow.
    
    Expected input:
    {
        "workflow_id": "uuid",
        "payment_status": "confirmed|pending|failed|delayed",
        "payment_amount": 62350.0,
        "payment_method": "bank_transfer",
        "transaction_id": "TXN123456",
        "payment_date": "2026-03-05T12:00:00Z"
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
        validate_payment_data(body)
        
        workflow_id = body.get('workflow_id')
        
        # Get existing workflow to check for delays
        response = table.get_item(Key={'workflow_id': workflow_id})
        if 'Item' not in response:
            raise ValidationError('Workflow not found')
        
        workflow = response['Item']
        
        # Check if payment is delayed
        is_delayed = check_payment_delay(workflow)
        
        # Create payment data
        payment_data = {
            'status': body.get('payment_status', 'pending'),
            'amount': Decimal(str(body.get('payment_amount', 0))) if body.get('payment_amount') else None,
            'method': body.get('payment_method', ''),
            'transaction_id': body.get('transaction_id', ''),
            'payment_date': body.get('payment_date', ''),
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'is_delayed': is_delayed,
        }
        
        # Update payment in DynamoDB
        update_payment_with_retry(workflow_id, payment_data)
        
        # Send alert if payment is delayed and status is still pending
        if is_delayed and payment_data['status'] == 'pending':
            farmer_name = workflow.get('farmer_input', {}).get('farmer_name', 'Unknown')
            amount = float(payment_data['amount']) if payment_data['amount'] else 0
            send_payment_alert(workflow_id, farmer_name, amount)
            publish_metric('DelayedPayment')
        
        # Publish status-specific metrics
        if payment_data['status'] == 'confirmed':
            publish_metric('PaymentConfirmed')
        elif payment_data['status'] == 'failed':
            publish_metric('PaymentFailed')
        
        # Publish latency metric
        latency = (time.time() - start_time) * 1000
        publish_metric('PaymentUpdateLatency', latency, 'Milliseconds')
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'payment_info': {
                    'status': payment_data['status'],
                    'amount': float(payment_data['amount']) if payment_data['amount'] else None,
                    'is_delayed': payment_data['is_delayed'],
                    'updated_at': payment_data['updated_at'],
                },
                'message': 'Payment status updated successfully',
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
    
    except PaymentError as e:
        publish_metric('PaymentError')
        print(f"Payment error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Payment error',
                'details': str(e),
                'message': 'Failed to update payment',
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
