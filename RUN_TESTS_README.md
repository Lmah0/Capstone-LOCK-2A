# Unit Tests for GCS Frontend, Endpoints & Recording Analysis

This directory contains unit tests covering the frontend, frontend-related endpoints, and AI / detection components.

## Test Files
AI/Detection components test
- `test_AIEngine.py` - Sanity tests for the TrackingEngine class in AIEngine.py
- `test_GeoLocate.py` - Sanity tests for the geolocation calculation module

GCS endpoint tests
- `test_endpoints.py` - Sanity tests for the gcs server endpoints

GCS tests
- `HUD.test.jsx`
- `InfoDashBoard.test.jsx`

Recording-Analysis tests
- `dashboard.test.jsx`
- `map.test.jsx`

### Run All Tests

Ensure you have the correct dependencies installed.

From the project root directory:

```bash
# Run all AI tests
pytest backend/gcs/tests/ai_tests -v

# Run all endpoint tests
pytest backend/gcs/tests/gcs_tests -v

# Run all frontend gcs tests
npm test --prefix frontend/gcs -- --watchAll=false --passWithNoTests

# Run all frontend recording-analysis tests
npm test --prefix frontend/recording_analysis -- --watchAll=false --passWithNoTests
```

### Run Specific Test Files

```bash
# Test AIEngine only
pytest backend/gcs/tests/ai_tests/test_AIEngine.py -v

# Test GeoLocate only
pytest backend/gcs/tests/ai_tests/test_GeoLocate.py -v

# Test GCS endpoints only
pytest backend/gcs/tests/gcs_tests/test_endpoints.py -v
```

### Run Specific Test Cases

```bash
# Run a specific test class
pytest backend/gcs/tests/ai_tests/test_GeoLocate.py::TestGeoLocate -v

# Run a specific test method
pytest backend/gcs/tests/ai_tests/test_AIEngine.py::TestTrackingEngine::test_init -v
```