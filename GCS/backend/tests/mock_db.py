import sys
import types

# Create the mock module
mock_db = types.ModuleType("GCS.backend.database")
# Mock database functions
mock_db._objects = [
        {"id": "64dbbe66-7117-4f2a-b7db-58a407588682", "class": "person"},
        {"id": "a3f5c8e2-9f4b-4d2e-8c3a-2b1e5f6d7c8e", "class": "vehicle"},
        {"id": "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f90", "class": "Unknown"}
    ]
mock_db.get_all_objects = lambda: mock_db._objects
mock_db.delete_object = lambda object_id: True if any(obj["id"] == object_id for obj in mock_db._objects) else False
mock_db.record_telemetry_data = lambda data, classification=None: None

# Inject the mock into sys.modules for both import paths
sys.modules["GCS.backend.database"] = mock_db
sys.modules["database"] = mock_db  # For the server's direct import