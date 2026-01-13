""" Shared database utilities for GCS backend """
from dotenv import load_dotenv
import boto3
import os
import uuid
from typing import Dict, Any, List

load_dotenv(dotenv_path="../../.env")

# Initialize DynamoDB connection
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))

def get_all_objects() -> List[Dict[str, Any]]:
    """Retrieve a list of all recorded objects with their classifications and timestamps"""
    response = table.scan()
    items = response.get('Items', [])
    object_list = []
    
    for item in items:
        # Get the first timestamp from positions array
        first_timestamp = None
        positions = item.get('positions', [])
        if positions and len(positions) > 0:
            first_timestamp = positions[0].get('ts')
        
        object_data = {
            "objectID": item['objectID'], 
            "classification": item['class'],
            "timestamp": first_timestamp
        }
        object_list.append(object_data)
    
    return object_list

def delete_object(object_id: str) -> bool:
    """Delete a recorded object from the DynamoDB table by its ID"""
    try:
        table.delete_item(Key={'objectID': object_id})
        return True
    except Exception as e:
        print(f"Error deleting object {object_id}: {e}")
        return False

def record_telemetry_data(data: List[Dict[str, Any]], classification: str = 'Unknown'):
    """Transform recording data into DynamoDB format and store it"""
    if not data or len(data) == 0:
        return

    # Create formatted data for DynamoDB
    formatted_data = {
        'objectID': str(uuid.uuid4()),
        'class': classification,
        'positions': data
    }
    table.put_item(Item=formatted_data)
    data.clear()