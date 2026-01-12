# Unit Tests for Detection Module

This directory contains unit tests for the Detection module components.

## Test Files

- `test_AIEngine.py` - Sanity tests for the TrackingEngine class in AIEngine.py
- `test_GeoLocate.py` - Sanity tests for the geolocation calculation module

## Running the Tests

### Prerequisites

Install pytest and required dependencies:

```bash
pip install pytest pytest-cov
pip install opencv-python numpy ultralytics geographiclib
```

### Run All Tests

From the project root directory:

```bash
# Run all tests in this directory
pytest tests/unit/detection/

```

### Run Specific Test Files

```bash
# Test AIEngine only
pytest tests/unit/detection/test_AIEngine.py -v

# Test GeoLocate only
pytest tests/unit/detection/test_GeoLocate.py -v
```

### Run Specific Test Cases

```bash
# Run a specific test class
pytest tests/unit/detection/test_AIEngine.py::TestTrackingEngine -v

# Run a specific test method
pytest tests/unit/detection/test_AIEngine.py::TestTrackingEngine::test_calculate_iou_perfect_overlap -v
```
