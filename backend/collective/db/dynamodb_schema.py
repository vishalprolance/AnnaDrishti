"""
DynamoDB schema definitions for real-time inventory management
"""

import boto3
from typing import Dict, Any


def create_collective_inventory_table(table_name: str = "collective_inventory") -> Dict[str, Any]:
    """
    Create DynamoDB table for collective inventory.
    
    Partition key: fpo_id#crop_type (composite)
    
    Attributes:
    - fpo_id: FPO identifier
    - crop_type: Crop type
    - total_quantity_kg: Total quantity
    - available_quantity_kg: Available quantity
    - reserved_quantity_kg: Reserved quantity
    - allocated_quantity_kg: Allocated quantity
    - contributions: List of farmer contributions
    - last_updated: Last update timestamp
    """
    return {
        "TableName": table_name,
        "KeySchema": [
            {"AttributeName": "inventory_key", "KeyType": "HASH"},  # Partition key
        ],
        "AttributeDefinitions": [
            {"AttributeName": "inventory_key", "AttributeType": "S"},  # fpo_id#crop_type
            {"AttributeName": "fpo_id", "AttributeType": "S"},
            {"AttributeName": "last_updated", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "fpo_id-index",
                "KeySchema": [
                    {"AttributeName": "fpo_id", "KeyType": "HASH"},
                    {"AttributeName": "last_updated", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        "BillingMode": "PAY_PER_REQUEST",  # On-demand pricing
        "StreamSpecification": {
            "StreamEnabled": True,
            "StreamViewType": "NEW_AND_OLD_IMAGES",
        },
    }


def create_farmer_contributions_table(table_name: str = "farmer_contributions") -> Dict[str, Any]:
    """
    Create DynamoDB table for farmer contributions.
    
    Partition key: contribution_id
    GSI: farmer_id for querying by farmer
    GSI: fpo_id#crop_type for querying by FPO and crop
    
    Attributes:
    - contribution_id: Unique identifier
    - farmer_id: Farmer identifier
    - farmer_name: Farmer name
    - fpo_id: FPO identifier
    - crop_type: Crop type
    - quantity_kg: Quantity in kg
    - quality_grade: Quality grade (A, B, C)
    - timestamp: Contribution timestamp
    - allocated: Whether allocated
    """
    return {
        "TableName": table_name,
        "KeySchema": [
            {"AttributeName": "contribution_id", "KeyType": "HASH"},  # Partition key
        ],
        "AttributeDefinitions": [
            {"AttributeName": "contribution_id", "AttributeType": "S"},
            {"AttributeName": "farmer_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
            {"AttributeName": "fpo_crop_key", "AttributeType": "S"},  # fpo_id#crop_type
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "farmer_id-index",
                "KeySchema": [
                    {"AttributeName": "farmer_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
            {
                "IndexName": "fpo_crop-index",
                "KeySchema": [
                    {"AttributeName": "fpo_crop_key", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
        ],
        "BillingMode": "PAY_PER_REQUEST",
    }


def create_reservations_table(table_name: str = "reservations") -> Dict[str, Any]:
    """
    Create DynamoDB table for inventory reservations.
    
    Partition key: reservation_id
    GSI: society_id for querying by society
    GSI: delivery_date for querying by date
    
    Attributes:
    - reservation_id: Unique identifier
    - society_id: Society identifier
    - crop_type: Crop type
    - reserved_quantity_kg: Reserved quantity
    - reservation_timestamp: Reservation timestamp
    - delivery_date: Expected delivery date
    - status: Reservation status
    - ttl: Time-to-live for automatic cleanup (30 days)
    """
    return {
        "TableName": table_name,
        "KeySchema": [
            {"AttributeName": "reservation_id", "KeyType": "HASH"},  # Partition key
        ],
        "AttributeDefinitions": [
            {"AttributeName": "reservation_id", "AttributeType": "S"},
            {"AttributeName": "society_id", "AttributeType": "S"},
            {"AttributeName": "delivery_date", "AttributeType": "S"},
            {"AttributeName": "reservation_timestamp", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "society_id-index",
                "KeySchema": [
                    {"AttributeName": "society_id", "KeyType": "HASH"},
                    {"AttributeName": "reservation_timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
            {
                "IndexName": "delivery_date-index",
                "KeySchema": [
                    {"AttributeName": "delivery_date", "KeyType": "HASH"},
                    {"AttributeName": "reservation_timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            },
        ],
        "BillingMode": "PAY_PER_REQUEST",
        "TimeToLiveSpecification": {
            "Enabled": True,
            "AttributeName": "ttl",
        },
    }


def create_tables(region: str = "ap-south-1"):
    """Create all DynamoDB tables for collective selling"""
    dynamodb = boto3.client("dynamodb", region_name=region)
    
    tables = [
        create_collective_inventory_table(),
        create_farmer_contributions_table(),
        create_reservations_table(),
    ]
    
    for table_def in tables:
        try:
            response = dynamodb.create_table(**table_def)
            print(f"Created table: {table_def['TableName']}")
            print(f"Status: {response['TableDescription']['TableStatus']}")
        except dynamodb.exceptions.ResourceInUseException:
            print(f"Table {table_def['TableName']} already exists")
        except Exception as e:
            print(f"Error creating table {table_def['TableName']}: {e}")


def delete_tables(region: str = "ap-south-1"):
    """Delete all DynamoDB tables (for testing/cleanup)"""
    dynamodb = boto3.client("dynamodb", region_name=region)
    
    table_names = [
        "collective_inventory",
        "farmer_contributions",
        "reservations",
    ]
    
    for table_name in table_names:
        try:
            dynamodb.delete_table(TableName=table_name)
            print(f"Deleted table: {table_name}")
        except dynamodb.exceptions.ResourceNotFoundException:
            print(f"Table {table_name} does not exist")
        except Exception as e:
            print(f"Error deleting table {table_name}: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        delete_tables()
    else:
        create_tables()
