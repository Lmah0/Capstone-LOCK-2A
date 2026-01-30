import pytest
import json
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import WebSocket
from httpx import ASGITransport
from fastapi.testclient import TestClient
from httpx import AsyncClient
import mock_db # Mock database to avoid real DB calls. Simply tests the logic.
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from server import app, send_data_to_connections

test_telemetry = {
    "timestamp": '2024-10-01T12:00:00Z',
    "latitude": 123.4567,
    "longitude": -123.4567,
    "altitude": 150.0,
    "dlat": 2.0, # Ground X speed (Latitude, positive north)
    "dlon": 3.0, # Ground Y Speed (Longitude, positive east)
    "dalt": 4.0, # Ground Z speed (Altitude, positive down)
    "roll": 2.5,
    "pitch": 1.5,
    "yaw": 0.5,
    "battery_remaining": 75.0,
    "battery_voltage": 12.5
}

# ------------------ Fixtures ------------------
@pytest.fixture
def client():
    """Synchronous test client for FastAPI app with mocked dependencies."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client():
    """Async client for testing async endpoints with mocked dependencies."""
    # Create a test server using httpx.AsyncClient with transport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def mock_flight_computer():
    """Mock flight computer WebSocket for testing flight commands."""
    mock_ws = MagicMock()
    mock_ws.send = AsyncMock()
    return mock_ws

# ------------------ Database Endpoint Tests ------------------
@pytest.mark.asyncio
async def test_get_all_objects_endpoint(async_client):
    """Test /objects endpoint to retrieve all objects."""
    response = await async_client.get("/objects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "id" in data[0]
    assert "class" in data[0]
    assert len(data) == 3


@pytest.mark.asyncio
async def test_delete_object_endpoint(async_client):
    """Test /delete/object/{object_id} endpoint for existing object."""
    response = await async_client.delete("/delete/object/64dbbe66-7117-4f2a-b7db-58a407588682")
    assert response.status_code == 200 # Successful deletion


@pytest.mark.asyncio
async def test_delete_object_endpoint_not_found(async_client):
    """Test /delete/object/{object_id} endpoint for non-existent object."""
    response = await async_client.delete("/delete/object/123")
    assert response.status_code == 500 # Object not found


# ------------------ Record Endpoint Tests ------------------
@pytest.mark.asyncio
async def test_record_endpoint_failure(async_client):
    """Test /record endpoint with invalid data."""
    response = await async_client.post("/record", json={"data": [{"x": 1, "y": 2}]})
    assert response.status_code == 400 # Missing 'data' key


@pytest.mark.asyncio
async def test_record_endpoint_success(async_client):
    """Test /record endpoint with valid data."""
    response = await async_client.post("/record", json={
        "data": [{"timestamp": 1625247600, "latitude": 37.7749, "longitude": -122.4194}]
    })
    assert response.status_code == 200 # Successful recording


@pytest.mark.asyncio
async def test_record_endpoint_missing_data(async_client):
    """Test /record endpoint with missing 'data' key."""
    response = await async_client.post("/record", json={})
    assert response.status_code == 400 # Missing 'data' key


# ------------------ Flight Mode Tests ------------------
@pytest.mark.asyncio
async def test_set_flight_mode_endpoint_with_mocked_fc(async_client):
    """Test /setFlightMode using mocked flight computer communication."""
    with patch('server.send_to_flight_comp') as mock_send:     
        response = await async_client.post("/setFlightMode", json={"mode": "AUTO"})
        assert response.status_code == 200
        
        # Verify the function was called with correct parameters
        mock_send.assert_called_once_with({"command": "set_flight_mode", "mode": "AUTO"})


@pytest.mark.asyncio
async def test_set_flight_mode_endpoint_empty_payload(async_client):
    """Test /setFlightMode with missing mode in payload."""
    response = await async_client.post("/setFlightMode", json={})
    assert response.status_code == 400


# ------------------ Stop Following Test ------------------
@pytest.mark.asyncio
async def test_stop_following_endpoint(async_client):
    """Test /stopFollowing endpoint with mocked flight computer communication."""
    with patch('server.send_to_flight_comp') as mock_send:
        response = await async_client.post("/stopFollowing")
        assert response.status_code == 200
        
        # Verify the function was called with correct parameters
        mock_send.assert_called_once_with({"command": "stop_following"})

# ------------------ Follow Distance Tests ------------------
@pytest.mark.asyncio
async def test_set_follow_distance_endpoint_with_mocked_fc(async_client):
    """Test /setFollowDistance using mocked flight computer communication."""
    with patch('server.send_to_flight_comp') as mock_send:   
        response = await async_client.post("/setFollowDistance", json={"distance": 10})
        assert response.status_code == 200
        
        # Verify the function was called with correct parameters
        mock_send.assert_called_once_with({"command": "set_follow_distance", "distance": 10})

@pytest.mark.asyncio
async def test_set_follow_distance_endpoint_missing_distance(async_client):
    """Test /setFollowDistance with missing distance in payload."""
    response = await async_client.post("/setFollowDistance", json={})
    assert response.status_code == 400


# ------------------ Telemetry Tests ------------------
@pytest.mark.asyncio
async def test_GCS_frontend_telemetry_broadcast():
    """
    TESTS: GCS -> Frontend broadcasting telemetry
    SIMULATES: GCS has received telemetry from flight computer and broadcasts it
    VERIFIES: Telemetry data format and content is preserved through WebSocket transmission
    
    NOTE: This does NOT test Flight Computer → GCS communication.
    """
    # Create mock WebSocket connection (representing React dashboard)
    mock_ws = AsyncMock()
    mock_connections = [mock_ws]
    
    # Test: GCS broadcasts telemetry to frontend (assumes GCS already has the data)
    await send_data_to_connections(test_telemetry, mock_connections)
    
    # Verify the telemetry was sent to WebSocket
    mock_ws.send_text.assert_called_once()
    
    # Verify specific telemetry fields are preserved in transmission
    sent_data = mock_ws.send_text.call_args[0][0]
    parsed_data = json.loads(sent_data) # What frontend receives after parsing
    assert parsed_data["altitude"] == 150.0 
    assert parsed_data["battery_remaining"] == 75.0 