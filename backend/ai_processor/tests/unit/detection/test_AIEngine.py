"""
Sanity tests for AIEngine.py
Tests basic functionality and edge cases for the TrackingEngine class
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add Detection/Spike_2.0 to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../Detection/Spike_2.0'))
from AIEngine import TrackingEngine


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
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_init(self, mock_tracker, mock_yolo, mock_model_path):
        """Test TrackingEngine initialization"""
        engine = TrackingEngine(mock_model_path)
        
        assert engine.is_tracking == False
        assert engine.tracked_bbox is None
        assert engine.tracked_class is None
        assert engine.detection_history == []
        assert engine.status_message == ""
        mock_yolo.assert_called_once_with(mock_model_path)
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_detect_objects_with_valid_frame(self, mock_tracker, mock_yolo, mock_model_path, sample_frame):
        """Test detect_objects with valid frame"""
        mock_model_instance = Mock()
        mock_result = Mock()
        mock_model_instance.predict.return_value = [mock_result]
        mock_yolo.return_value = mock_model_instance
        
        engine = TrackingEngine(mock_model_path)
        result = engine.detect_objects(sample_frame)
        
        assert result == mock_result
        mock_model_instance.predict.assert_called_once()
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_detect_objects_with_none_frame(self, mock_tracker, mock_yolo, mock_model_path):
        """Test detect_objects with None frame"""
        engine = TrackingEngine(mock_model_path)
        result = engine.detect_objects(None)
        
        assert result is None
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_detect_objects_with_empty_frame(self, mock_tracker, mock_yolo, mock_model_path):
        """Test detect_objects with empty frame"""
        engine = TrackingEngine(mock_model_path)
        empty_frame = np.array([])
        result = engine.detect_objects(empty_frame)
        
        assert result is None
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_start_tracking(self, mock_tracker, mock_yolo, mock_model_path, sample_frame, sample_bbox):
        """Test start_tracking initializes correctly"""
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance
        
        engine = TrackingEngine(mock_model_path)
        class_id = 0
        engine.start_tracking(sample_frame, sample_bbox, class_id)
        
        assert engine.is_tracking == True
        assert engine.tracked_bbox == sample_bbox
        assert engine.tracked_class == class_id
        assert engine.detection_history == []
        mock_tracker_instance.init.assert_called_once_with(sample_frame, sample_bbox)
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_update_when_not_tracking(self, mock_tracker, mock_yolo, mock_model_path, sample_frame):
        """Test update returns False when not tracking"""
        engine = TrackingEngine(mock_model_path)
        success, bbox = engine.update(sample_frame, 1)
        
        assert success == False
        assert bbox is None
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_update_when_tracker_succeeds(self, mock_tracker, mock_yolo, mock_model_path, sample_frame, sample_bbox):
        """Test update when tracker successfully tracks"""
        mock_tracker_instance = Mock()
        mock_tracker_instance.update.return_value = (True, sample_bbox)
        mock_tracker.return_value = mock_tracker_instance
        
        engine = TrackingEngine(mock_model_path)
        engine.is_tracking = True
        engine.tracked_bbox = sample_bbox
        
        success, bbox = engine.update(sample_frame, 1)
        
        assert success == True
        assert bbox == sample_bbox
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_update_when_tracker_fails(self, mock_tracker, mock_yolo, mock_model_path, sample_frame):
        """Test update when tracker fails"""
        mock_tracker_instance = Mock()
        mock_tracker_instance.update.return_value = (False, None)
        mock_tracker.return_value = mock_tracker_instance
        
        engine = TrackingEngine(mock_model_path)
        engine.is_tracking = True
        
        success, bbox = engine.update(sample_frame, 1)
        
        assert success == False
        assert bbox is None
        assert engine.is_tracking == False
    
    def test_calculate_iou_perfect_overlap(self):
        """Test IoU calculation with perfect overlap"""
        box1 = (100, 100, 50, 50)
        box2 = (100, 100, 50, 50)
        
        iou = TrackingEngine.calculate_iou(box1, box2)
        assert iou == 1.0
    
    def test_calculate_iou_no_overlap(self):
        """Test IoU calculation with no overlap"""
        box1 = (0, 0, 50, 50)
        box2 = (100, 100, 50, 50)
        
        iou = TrackingEngine.calculate_iou(box1, box2)
        assert iou == 0.0
    
    def test_calculate_iou_partial_overlap(self):
        """Test IoU calculation with partial overlap"""
        box1 = (0, 0, 100, 100)
        box2 = (50, 50, 100, 100)
        
        iou = TrackingEngine.calculate_iou(box1, box2)
        # 50*50 = 2500 intersection, 100*100 + 100*100 - 2500 = 17500 union
        # IoU = 2500 / 17500 = 0.142857...
        assert 0.14 < iou < 0.15
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_get_tracker_confidence(self, mock_tracker, mock_yolo, mock_model_path, sample_frame, sample_bbox):
        """Test get_tracker_confidence returns a valid value"""
        mock_tracker_instance = Mock()
        mock_tracker_instance.getTrackingResponse.return_value = np.array([0.8, 0.9, 0.7])
        mock_tracker.return_value = mock_tracker_instance
        
        engine = TrackingEngine(mock_model_path)
        confidence = engine.get_tracker_confidence(mock_tracker_instance, sample_frame, sample_bbox)
        
        assert confidence == 0.9
    
    @patch('AIEngine.YOLO')
    @patch('AIEngine.cv2.legacy.TrackerCSRT_create')
    def test_get_tracker_confidence_fallback(self, mock_tracker, mock_yolo, mock_model_path, sample_frame, sample_bbox):
        """Test get_tracker_confidence fallback when method fails"""
        from AIEngine import TRACKER_CONFIDENCE_THRESHOLD
        
        mock_tracker_instance = Mock()
        mock_tracker_instance.getTrackingResponse.side_effect = Exception("Method not available")
        mock_tracker.return_value = mock_tracker_instance
        
        engine = TrackingEngine(mock_model_path)
        confidence = engine.get_tracker_confidence(mock_tracker_instance, sample_frame, sample_bbox)
        
        assert confidence == TRACKER_CONFIDENCE_THRESHOLD
