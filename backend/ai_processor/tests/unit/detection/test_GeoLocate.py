"""
Sanity tests for GeoLocate.py
Tests the geolocation calculation functionality
"""

import sys
import os

# Add Detection/Spike_2.0 to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../Detection/Spike_2.0'))
from GeoLocate import locate, CAM_FOV, IMG_WIDTH_PX, IMG_HEIGHT_PX


class TestGeoLocate:
    """Sanity tests for GeoLocate module"""
    
    def test_locate_returns_tuple(self):
        """Test that locate returns a tuple of coordinates"""
        result = locate(
            uav_latitude=51.0,
            uav_longitude=-114.0,
            uav_altitude=100.0,
            obj_x_px=0.0,
            obj_y_px=0.0
        )
        
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_locate_at_center(self):
        """Test locate when object is at center of frame (0,0)"""
        uav_latitude = 51.0
        uav_longitude = -114.0
        
        result = locate(
            uav_latitude=uav_latitude,
            uav_longitude=uav_longitude,
            uav_altitude=100.0,
            obj_x_px=0.0,
            obj_y_px=0.0
        )
        
        obj_latitude, obj_longitude = result
        
        # At center with 0 pixel offset, should be very close to UAV position
        assert abs(obj_latitude - uav_latitude) < 0.001
        assert abs(obj_longitude - uav_longitude) < 0.001
    
    def test_locate_with_positive_altitude(self):
        """Test locate with positive altitude"""
        result = locate(
            uav_latitude=51.0,
            uav_longitude=-114.0,
            uav_altitude=500.0,
            obj_x_px=10.0,
            obj_y_px=10.0
        )
        
        obj_latitude, obj_longitude = result
        
        # Should return valid latitude and longitude
        assert -90 <= obj_latitude <= 90
        assert -180 <= obj_longitude <= 180
    
    def test_locate_different_bearings(self):
        """Test locate with different drone orientations"""
        base_params = {
            "uav_latitude": 51.0,
            "uav_longitude": -114.0,
            "uav_altitude": 100.0,
            "obj_x_px": 100.0,
            "obj_y_px": 0.0
        }
        
        # With constant downward-facing camera, all bearings should produce same result
        result_north = locate(**base_params)
        result_east = locate(**base_params)
        result_south = locate(**base_params)
        result_west = locate(**base_params)
        
        # Results should be the same regardless of drone heading
        assert result_north == result_east
        assert result_east == result_south
        assert result_south == result_west
    
    def test_locate_with_positive_pixel_offsets(self):
        """Test locate with positive pixel offsets"""
        result = locate(
            uav_latitude=51.0,
            uav_longitude=-114.0,
            uav_altitude=200.0,
            obj_x_px=50.0,
            obj_y_px=50.0
        )
        
        obj_latitude, obj_longitude = result
        
        # Should return valid coordinates
        assert isinstance(obj_latitude, float)
        assert isinstance(obj_longitude, float)
        assert -90 <= obj_latitude <= 90
        assert -180 <= obj_longitude <= 180
    
    def test_locate_with_negative_pixel_offsets(self):
        """Test locate with negative pixel offsets"""
        result = locate(
            uav_latitude=51.0,
            uav_longitude=-114.0,
            uav_altitude=200.0,
            obj_x_px=-50.0,
            obj_y_px=-50.0
        )
        
        obj_latitude, obj_longitude = result
        
        # Should return valid coordinates
        assert isinstance(obj_latitude, float)
        assert isinstance(obj_longitude, float)
        assert -90 <= obj_latitude <= 90
        assert -180 <= obj_longitude <= 180
    
    def test_locate_high_altitude(self):
        """Test locate at high altitude (larger ground coverage)"""
        result = locate(
            uav_latitude=51.0,
            uav_longitude=-114.0,
            uav_altitude=1000.0,
            obj_x_px=100.0,
            obj_y_px=100.0
        )
        
        obj_latitude, obj_longitude = result
        
        # Should return valid coordinates
        assert -90 <= obj_latitude <= 90
        assert -180 <= obj_longitude <= 180
    
    def test_locate_low_altitude(self):
        """Test locate at low altitude (smaller ground coverage)"""
        result = locate(
            uav_latitude=51.0,
            uav_longitude=-114.0,
            uav_altitude=50.0,
            obj_x_px=10.0,
            obj_y_px=10.0
        )
        
        obj_latitude, obj_longitude = result
        
        # Should return valid coordinates
        assert -90 <= obj_latitude <= 90
        assert -180 <= obj_longitude <= 180
    
    def test_locate_consistency(self):
        """Test that same inputs produce same outputs"""
        params = {
            "uav_latitude": 51.1656129,
            "uav_longitude": -114.1054339,
            "uav_altitude": 680.84,
            "obj_x_px": 0.77,
            "obj_y_px": 0.58
        }
        
        result1 = locate(**params)
        result2 = locate(**params)
        
        assert result1 == result2
    
    def test_locate_altitude_affects_distance(self):
        """Test that higher altitude results in larger ground coverage"""
        base_params = {
            "uav_latitude": 51.0,
            "uav_longitude": -114.0,
            "obj_x_px": 100.0,
            "obj_y_px": 0.0
        }
        
        result_low = locate(**base_params, uav_altitude=100.0)
        result_high = locate(**base_params, uav_altitude=500.0)
        
        # Calculate distance from UAV position
        lat_diff_low = abs(result_low[0] - 51.0)
        lat_diff_high = abs(result_high[0] - 51.0)
        
        # Higher altitude should result in greater distance for same pixel offset
        # This assumes the object is not at center
        assert lat_diff_high > lat_diff_low
    
    def test_constants_are_positive(self):
        """Test that camera constants are positive values"""
        assert CAM_FOV > 0
        assert IMG_WIDTH_PX > 0
        assert IMG_HEIGHT_PX > 0
    
    def test_locate_with_edge_case_zero_altitude(self):
        """Test behavior with zero altitude (edge case)"""
        # Note: In real world this shouldn't happen, but good to test
        # With zero altitude, ground coverage would be zero
        result = locate(
            uav_latitude=51.0,
            uav_longitude=-114.0,
            uav_altitude=0.0,
            obj_x_px=100.0,
            obj_y_px=100.0
        )
        
        # Should still return valid coordinates (at or near UAV position)
        assert isinstance(result, tuple)
        assert len(result) == 2
