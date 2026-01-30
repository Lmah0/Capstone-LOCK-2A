"""
Sanity tests for AIEngine.py
Tests basic functionality and edge cases for the TrackingEngine class
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

root = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root))
from backend.gcs.ai.AIEngine import TrackingEngine, TrackingConfig, ProcessingState

class TestTrackingEngine:
    """Sanity tests for TrackingEngine class"""
    
    @pytest.fixture
    def mock_model_path(self):
        """Fixture for model path"""
        return "mock_model.pt"
    
    @pytest.fixture
    def sample_frame(self):
        """Create a sample frame for testing"""
        return np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
    
    @pytest.fixture
    def sample_bbox(self):
        """Sample bounding box (x, y, w, h)"""
        return (100, 100, 50, 50)
    
    @patch('backend.gcs.ai.AIEngine.YOLO')
    def test_init(self, mock_yolo):
        """Test TrackingEngine initialization"""
        mock_model = Mock()
        mock_yolo.return_value = mock_model

        engine = TrackingEngine()

        assert engine.is_tracking == False
        assert engine.tracked_bbox is None
        assert engine.tracked_class is None
        assert engine.tracker is None
        mock_yolo.assert_called_once()
    
    @patch('backend.gcs.ai.AIEngine.YOLO')
    def test_detect_objects_with_valid_frame(self, mock_yolo, sample_frame):
        """Test detect_objects with valid frame"""
        mock_model_instance = Mock()
        mock_result = Mock()
        mock_model_instance.predict.return_value = [mock_result]
        mock_yolo.return_value = mock_model_instance
        
        engine = TrackingEngine()
        result = engine.detect_objects(sample_frame)
        
        assert result == mock_result
        mock_model_instance.predict.assert_called_once()
    
    @patch('backend.gcs.ai.AIEngine.YOLO')
    def test_detect_objects_with_none_frame(self, mock_yolo):
        """Test detect_objects with None frame"""
        mock_model = Mock()
        mock_yolo.return_value = mock_model

        engine = TrackingEngine()
        result = engine.detect_objects(None)

        assert result is None
        mock_model.predict.assert_not_called()
    
    @patch('backend.gcs.ai.AIEngine.YOLO')
    def test_detect_objects_with_empty_frame(self, mock_yolo):
        """Test detect_objects with empty frame"""
        mock_model = Mock()
        mock_yolo.return_value = mock_model

        engine = TrackingEngine()
        result = engine.detect_objects(None)

        assert result is None
        mock_model.predict.assert_not_called()
    
    @patch("backend.gcs.ai.AIEngine.YOLO")
    @patch("backend.gcs.ai.AIEngine.TrackingEngine._load_vittrack")
    @patch("backend.gcs.ai.AIEngine.cv2.TrackerCSRT.create")
    def test_start_tracking_uses_vittrack_when_available(self, mock_csrt_create, mock_load_vittrack, mock_yolo, sample_frame, sample_bbox):
        mock_yolo.return_value = Mock()
        vit_tracker = Mock()
        mock_load_vittrack.return_value = vit_tracker

        engine = TrackingEngine()
        engine.tracker_type = "vittrack"

        engine.start_tracking(sample_frame, sample_bbox, class_id=1)

        mock_load_vittrack.assert_called_once()
        mock_csrt_create.assert_not_called()
        vit_tracker.init.assert_called_once()

    @patch("backend.gcs.ai.AIEngine.YOLO")
    @patch("backend.gcs.ai.AIEngine.TrackingEngine._load_vittrack")
    @patch("backend.gcs.ai.AIEngine.cv2.TrackerCSRT.create")
    def test_start_tracking_falls_back_to_csrt(self, mock_csrt_create, mock_load_vittrack, mock_yolo, sample_frame, sample_bbox):
        mock_yolo.return_value = Mock()

        mock_load_vittrack.return_value = None
        csrt_tracker = Mock()
        mock_csrt_create.return_value = csrt_tracker

        engine = TrackingEngine()
        engine.tracker_type = "vittrack"

        engine.start_tracking(sample_frame, sample_bbox, class_id=2)

        mock_load_vittrack.assert_called_once()
        mock_csrt_create.assert_called_once()
        csrt_tracker.init.assert_called_once()
        assert engine.tracker_type == "csrt"

    @patch('backend.gcs.ai.AIEngine.YOLO')
    @patch('backend.gcs.ai.AIEngine.cv2.TrackerCSRT.create')
    def test_start_tracking(self, mock_tracker, mock_yolo, sample_frame, sample_bbox):
        """Test start_tracking initializes correctly"""
        mock_yolo.return_value = Mock()
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance
        
        engine = TrackingEngine()
        engine.tracker_type = "csrt" # Force use csrt over vittrack
        class_id = 0
        engine.start_tracking(sample_frame, sample_bbox, class_id)
        
        assert engine.is_tracking == True
        assert engine.tracked_bbox == sample_bbox
        assert engine.tracked_class == class_id
        mock_tracker_instance.init.assert_called_once_with(sample_frame, sample_bbox)
