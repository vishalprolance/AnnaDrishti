"""
Lambda function to fetch Sentinel-2 satellite data and calculate NDVI.
Provides crop health indicators for verification and credibility.
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
s3 = boto3.client('s3')
table_name = os.environ.get('WORKFLOW_TABLE_NAME', 'anna-drishti-demo-workflows')
table = dynamodb.Table(table_name)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
SENTINEL_BUCKET = 'sentinel-s2-l2a'  # AWS Open Data bucket


class SatelliteError(Exception):
    """Custom exception for satellite data errors."""
    pass


class ValidationError(SatelliteError):
    """Exception for input validation errors."""
    pass


def publish_metric(metric_name: str, value: float = 1.0, unit: str = 'Count'):
    """Publish custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace='AnnaDrishti/Satellite',
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


def validate_input(body: dict) -> dict:
    """Validate satellite data request."""
    errors = []
    
    if not body.get('workflow_id'):
        errors.append('workflow_id is required')
    
    if errors:
        raise ValidationError('; '.join(errors))
    
    return body


def get_workflow_location(workflow_id: str) -> tuple:
    """Get farm location from workflow."""
    try:
        response = table.get_item(Key={'workflow_id': workflow_id})
        if 'Item' not in response:
            raise ValidationError('Workflow not found')
        
        workflow = response['Item']
        location = workflow.get('farmer_input', {}).get('location', '')
        
        # Map location to approximate coordinates (for demo)
        # In production, use geocoding API
        location_coords = {
            'nashik': {'lat': 19.9975, 'lon': 73.7898},
            'sinnar': {'lat': 19.8500, 'lon': 73.9833},
            'pune': {'lat': 18.5204, 'lon': 73.8567},
            'mumbai': {'lat': 19.0760, 'lon': 72.8777},
            'nagpur': {'lat': 21.1458, 'lon': 79.0882},
            'aurangabad': {'lat': 19.8762, 'lon': 75.3433},
            'delhi': {'lat': 28.7041, 'lon': 77.1025},
            'bangalore': {'lat': 12.9716, 'lon': 77.5946},
            'hyderabad': {'lat': 17.3850, 'lon': 78.4867},
            'kolkata': {'lat': 22.5726, 'lon': 88.3639},
        }
        
        coords = location_coords.get(location.lower(), location_coords['nashik'])
        return coords['lat'], coords['lon']
        
    except ClientError as e:
        raise SatelliteError(f"Failed to get workflow: {str(e)}")


def calculate_ndvi_mock(lat: float, lon: float) -> List[Dict]:
    """
    Calculate NDVI (Normalized Difference Vegetation Index) for crop health.
    
    For MVP, returns mock data. In production, this would:
    1. Query Sentinel-2 S3 bucket for imagery
    2. Download NIR and Red bands
    3. Calculate NDVI = (NIR - Red) / (NIR + Red)
    4. Return time series data
    
    NDVI ranges:
    - 0.8-1.0: Very healthy vegetation
    - 0.6-0.8: Healthy vegetation
    - 0.4-0.6: Moderate vegetation
    - 0.2-0.4: Sparse vegetation
    - 0.0-0.2: Bare soil/no vegetation
    """
    
    # Generate mock NDVI data for last 30 days
    ndvi_data = []
    base_date = datetime.utcnow()
    
    # Simulate crop growth cycle
    for i in range(6):  # 6 data points (every 5 days)
        date = base_date - timedelta(days=i * 5)
        
        # Simulate NDVI increasing over time (crop growing)
        # Start at 0.3 (early growth), increase to 0.75 (mature crop)
        ndvi_value = 0.3 + (i * 0.075)
        
        # Add some variation
        import random
        ndvi_value += random.uniform(-0.05, 0.05)
        ndvi_value = max(0.0, min(1.0, ndvi_value))  # Clamp to [0, 1]
        
        # Determine health status
        if ndvi_value >= 0.7:
            status = 'excellent'
            color = '#22c55e'  # green
        elif ndvi_value >= 0.5:
            status = 'good'
            color = '#84cc16'  # lime
        elif ndvi_value >= 0.3:
            status = 'moderate'
            color = '#eab308'  # yellow
        else:
            status = 'poor'
            color = '#ef4444'  # red
        
        ndvi_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'ndvi': Decimal(str(round(ndvi_value, 3))),  # Convert to Decimal
            'status': status,
            'color': color,
            'cloud_cover': random.randint(0, 30),  # % cloud cover
        })
    
    # Reverse to show oldest first
    ndvi_data.reverse()
    
    return ndvi_data


def calculate_crop_health_score(ndvi_data: List[Dict]) -> Dict:
    """Calculate overall crop health score from NDVI data."""
    if not ndvi_data:
        return {
            'score': 0,
            'status': 'unknown',
            'trend': 'stable',
        }
    
    # Get latest NDVI (convert Decimal to float)
    latest_ndvi = float(ndvi_data[-1]['ndvi'])
    
    # Calculate trend (comparing last 2 data points)
    if len(ndvi_data) >= 2:
        prev_ndvi = float(ndvi_data[-2]['ndvi'])
        ndvi_change = latest_ndvi - prev_ndvi
        
        if ndvi_change > 0.05:
            trend = 'improving'
        elif ndvi_change < -0.05:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'stable'
    
    # Convert NDVI to 0-100 score
    score = int(latest_ndvi * 100)
    
    # Determine status
    if score >= 70:
        status = 'excellent'
    elif score >= 50:
        status = 'good'
    elif score >= 30:
        status = 'moderate'
    else:
        status = 'poor'
    
    return {
        'score': score,
        'status': status,
        'trend': trend,
        'latest_ndvi': Decimal(str(latest_ndvi)),  # Convert to Decimal
    }


def update_workflow_satellite_data(workflow_id: str, satellite_data: dict) -> None:
    """Update workflow with satellite data."""
    for attempt in range(MAX_RETRIES):
        try:
            table.update_item(
                Key={'workflow_id': workflow_id},
                UpdateExpression='SET satellite_data = :data, updated_at = :updated',
                ExpressionAttributeValues={
                    ':data': satellite_data,
                    ':updated': datetime.utcnow().isoformat() + 'Z',
                }
            )
            publish_metric('SatelliteDataUpdated')
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
                    publish_metric('SatelliteDataUpdateFailed')
                    raise SatelliteError(f"DynamoDB throughput exceeded after {MAX_RETRIES} retries")
            else:
                publish_metric('SatelliteDataUpdateFailed')
                raise SatelliteError(f"DynamoDB error: {error_code} - {str(e)}")
        except Exception as e:
            publish_metric('SatelliteDataUpdateFailed')
            raise SatelliteError(f"Unexpected error updating satellite data: {str(e)}")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Fetch Sentinel-2 satellite data and calculate NDVI for crop health.
    
    Expected input:
    {
        "workflow_id": "uuid"
    }
    
    Returns:
    {
        "success": true,
        "satellite_data": {
            "location": {"lat": 19.9975, "lon": 73.7898},
            "ndvi_time_series": [...],
            "crop_health": {
                "score": 75,
                "status": "excellent",
                "trend": "improving"
            },
            "last_updated": "2026-03-05T20:00:00Z"
        }
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
        
        # Get farm location
        lat, lon = get_workflow_location(workflow_id)
        publish_metric('LocationResolved')
        
        # Calculate NDVI (mock data for MVP)
        ndvi_data = calculate_ndvi_mock(lat, lon)
        publish_metric('NDVICalculated')
        
        # Calculate crop health score
        crop_health = calculate_crop_health_score(ndvi_data)
        publish_metric('CropHealthCalculated')
        
        # Prepare satellite data
        satellite_data = {
            'location': {
                'lat': Decimal(str(lat)),  # Convert to Decimal
                'lon': Decimal(str(lon)),  # Convert to Decimal
            },
            'ndvi_time_series': ndvi_data,
            'crop_health': crop_health,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'data_source': 'Sentinel-2 (simulated for MVP)',
            'note': 'Satellite data provides crop health trends for verification, not precise yield estimates (±30-40% accuracy)',
        }
        
        # Update workflow with satellite data
        update_workflow_satellite_data(workflow_id, satellite_data)
        
        # Publish latency metric
        latency = (time.time() - start_time) * 1000
        publish_metric('SatelliteDataLatency', latency, 'Milliseconds')
        
        # Convert Decimal to float for JSON response
        satellite_data_json = decimal_to_float(satellite_data)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'satellite_data': satellite_data_json,
                'message': 'Satellite data retrieved successfully',
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
    
    except SatelliteError as e:
        publish_metric('SatelliteError')
        print(f"Satellite error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Satellite error',
                'details': str(e),
                'message': 'Failed to retrieve satellite data',
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
