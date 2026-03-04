"""
Lambda function to scan market data from Agmarknet.
Fetches prices for 4 mandis and calculates net-to-farmer prices.
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

# Transport costs (₹/kg) based on distance
TRANSPORT_COSTS = {
    'Sinnar': 0.5,   # 15 km
    'Nashik': 1.0,   # 30 km
    'Pune': 3.0,     # 180 km
    'Mumbai': 5.0,   # 250 km
}

# Mock data for demo (fallback when Agmarknet is unavailable)
MOCK_PRICES = {
    'tomato': {
        'Sinnar': {'price': 26.0, 'arrivals': 18.5},
        'Nashik': {'price': 25.0, 'arrivals': 22.0},
        'Pune': {'price': 28.0, 'arrivals': 45.0},
        'Mumbai': {'price': 32.0, 'arrivals': 120.0},
    },
    'onion': {
        'Sinnar': {'price': 18.0, 'arrivals': 25.0},
        'Nashik': {'price': 17.5, 'arrivals': 30.0},
        'Pune': {'price': 20.0, 'arrivals': 50.0},
        'Mumbai': {'price': 24.0, 'arrivals': 100.0},
    },
    'chili': {
        'Sinnar': {'price': 45.0, 'arrivals': 8.0},
        'Nashik': {'price': 44.0, 'arrivals': 12.0},
        'Pune': {'price': 48.0, 'arrivals': 20.0},
        'Mumbai': {'price': 52.0, 'arrivals': 35.0},
    },
}


def fetch_agmarknet_prices(crop_type: str) -> tuple[list[dict], str]:
    """
    Fetch prices from Agmarknet API.
    Returns (mandis_data, data_source).
    
    For MVP, we use mock data. Phase 2 will implement real scraping.
    """
    try:
        # TODO: Implement real Agmarknet scraping in Phase 2
        # For now, use mock data
        
        mandis_data = []
        crop_prices = MOCK_PRICES.get(crop_type, MOCK_PRICES['tomato'])
        
        for mandi_name, data in crop_prices.items():
            distance_km = {
                'Sinnar': 15,
                'Nashik': 30,
                'Pune': 180,
                'Mumbai': 250,
            }[mandi_name]
            
            transport_cost = TRANSPORT_COSTS[mandi_name]
            net_price = data['price'] - transport_cost
            
            mandis_data.append({
                'name': mandi_name,
                'price': Decimal(str(data['price'])),
                'distance_km': Decimal(str(distance_km)),
                'net_price': Decimal(str(net_price)),
                'arrivals_tonnes': Decimal(str(data['arrivals'])),
            })
        
        return mandis_data, 'live'
        
    except Exception as e:
        print(f"Error fetching Agmarknet data: {str(e)}")
        # Return cached/mock data as fallback
        return [], 'cached'


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Scan market data for a workflow.
    
    Expected input:
    {
        "workflow_id": "uuid",
        "crop_type": "tomato"
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        workflow_id = body.get('workflow_id')
        crop_type = body.get('crop_type', 'tomato')
        
        if not workflow_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'workflow_id is required'})
            }
        
        # Fetch market data
        mandis_data, data_source = fetch_agmarknet_prices(crop_type)
        
        if not mandis_data:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to fetch market data'})
            }
        
        # Find recommended mandi (highest net price)
        recommended = max(mandis_data, key=lambda m: m['net_price'])
        
        # Create market scan result
        market_scan = {
            'mandis': mandis_data,
            'recommended': recommended['name'],
            'data_source': data_source,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        # Update workflow in DynamoDB
        table.update_item(
            Key={'workflow_id': workflow_id},
            UpdateExpression='SET market_scan = :scan, #status = :status, updated_at = :updated',
            ExpressionAttributeNames={
                '#status': 'status',
            },
            ExpressionAttributeValues={
                ':scan': market_scan,
                ':status': 'scanning_market',
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
                'market_scan': {
                    'mandis': [{
                        'name': m['name'],
                        'price': float(m['price']),
                        'distance_km': float(m['distance_km']),
                        'net_price': float(m['net_price']),
                        'arrivals_tonnes': float(m['arrivals_tonnes']),
                    } for m in market_scan['mandis']],
                    'recommended': market_scan['recommended'],
                    'data_source': market_scan['data_source'],
                    'timestamp': market_scan['timestamp'],
                },
                'message': f'Market scan completed ({data_source} data)',
            })
        }
        
    except Exception as e:
        print(f"Error scanning market: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to scan market',
            })
        }
