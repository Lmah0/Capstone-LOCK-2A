from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8765"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
connections = set()

@app.websocket("/ws/gcs")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the connection
    await websocket.accept()
    connections.add(websocket)
    print(f"Client connected. Total connections: {len(connections)}")
    
    try:
        # Keep connection alive
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            print(f"Received: {data}")
            
            # Echo back to confirm connection
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(connections)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8766, reload=True)
