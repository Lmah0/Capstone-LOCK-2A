# TABLE SCHEMA LOOKS AS FOLLOWS:
# {
#   "objectID": 1,
#   "class": "vehicle",
#   "positions": [
#     {"ts": "2025-10-16T13:17:00Z", "lat": 51.0447, "lon": -114.0719, "alt": 1045.0, "speed": 20.0, "heading": 90.0},
#     {"ts": "2025-10-16T13:18:00Z", "lat": 51.0448, "lon": -114.07195, "alt": 1045.0, "speed": 21.0, "heading": 90.0},
#     // ...
#   ]
# }
# ---
# All position points for an object are stored in a single item in the table.
# This is to optimize storage and read performance when retrieving the full path of an object.

# This script is used to test inserting and querying data from the DynamoDB table.
# Use this to add test data for development and testing purposes.
import boto3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../../.env")

dynamodb = boto3.resource(
    'dynamodb',
    region_name= os.getenv('AWS_REGION'),
    aws_access_key_id= os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_secret_access_key= os.getenv('AWS_ACCESS_KEY_ID')
)
table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))

def InsertTestData(obj_class):
    object_id = str(uuid.uuid4())

    num_points = 30
    positions = []
    for i in range(num_points):
        ts = datetime.now() + timedelta(minutes=i)
        ts_str = ts.isoformat() + 'Z'
        positions.append({
            'ts': ts_str,
            'lat': Decimal(str(53.0447 + (i * 0.005))),
            'lon': Decimal(str(-110.0719 + (i * 0.002))),
            'alt': Decimal('1089.0'),
            'speed': Decimal(str(11.2 + (i % 10))),
            'heading': Decimal('86.0')
        })

    # Insert one item containing all positions
    item = {
        'objectID': object_id,
        'class': obj_class,
        'positions': positions
    }

    try:
        table.put_item(Item=item)
        print(f"Inserted object {object_id} ({obj_class}) with {num_points} position points.")
    except Exception as e:
        print(f"Error inserting data: {e}")

def QueryTestData(objID):
    try:
        if objID:
            response = table.get_item(Key={'objectID': objID})
            item = response.get('Item')
            if item:
                print(f"Queried object {objID}:")
                print(item)
            else:
                print(f"No data found for objectID {objID}")
        else:
            response = table.scan()
            items = response.get('Items', [])
            print(f"Queried all objects, found {len(items)} items.")
            for item in items:
                print(item)
    except Exception as e:
        print(f"Error querying data: {e}")

if __name__ == "__main__":
    InsertTestData('Unknown')
    # QueryTestData('4d409315-38de-4c39-8b0f-2fb739f8a0d2')