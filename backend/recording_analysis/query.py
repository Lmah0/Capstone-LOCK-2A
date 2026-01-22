from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from dotenv import load_dotenv
import os
import uvicorn
from typing import List, Dict, Any

load_dotenv(dotenv_path="../../.env")
app = FastAPI()

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{os.getenv('RECORDING_ANALYSIS_FRONTEND_PORT')}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dynamodb = boto3.resource(
    'dynamodb',
    region_name= os.getenv('AWS_REGION'),
    aws_access_key_id= os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY')
)
table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))

@app.get("/object/{object_id}")
async def get_object_data(object_id: str):
    try:
        response = table.get_item(Key={'objectID': object_id})
        item = response.get('Item')     
        if item:
            telemetry_data = []        
            for position in item.get('positions', []):
                telemetry_point = {
                    "timestamp": position.get('ts'),
                    "latitude": float(position.get('lat', 0)),
                    "longitude": float(position.get('lon', 0)),
                    "altitude": float(position.get('alt', 0)),
                    "speed": float(position.get('speed', 0)),
                    "heading": float(position.get('heading', 0))
                }
                telemetry_data.append(telemetry_point)
            
            return { "class": item.get('class'), "telemetryData": telemetry_data }
        else:
            raise HTTPException(status_code=404, detail=f"Object with ID {object_id} not found")
            
    except Exception as e:
        print(f"Error querying data: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.get("/all_objects")
async def get_all_objects()-> List[Dict[str, Any]]:
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


if __name__ == "__main__":
    uvicorn.run("query:app", host="0.0.0.0", port=int(os.getenv('RECORDING_ANALYSIS_BACKEND_PORT')), reload=True)