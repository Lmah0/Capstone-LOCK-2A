# SOT.py
from ultralytics import YOLO 

class ObjectTracker:
    def __init__(self, model_name="yolo11n.pt", show=False): 
        self.model_name = model_name
        self.detection_model = YOLO(self.model_name)
        self.show_internal = show
        self.frame_count = 0
        self.total_processing_time = 0.0
        self.target_id = None 

    def update(self, frame):
        """
        Run the YOLO tracking model on a frame and return detections, 
        including a persistent 'id' for each object.
        """
        detections = []

        results_list = self.detection_model.track(
            frame, 
            persist=True, # Critical for maintaining object identity
            verbose=False, 
            show=self.show_internal
        )

        if not results_list:
            return detections
        
        results = results_list[0] 

        # Note: If no detections are present, results.boxes might be None.
        if (not hasattr(results, "boxes") or 
            results.boxes is None or 
            results.boxes.data.shape[0] == 0):
            return detections

        # Extract all necessary attributes
        boxes = results.boxes.xyxy 
        classes = results.boxes.cls

        # Extract track IDs. If tracking fails (e.g., first frame), .id might be None.
        track_ids = results.boxes.id.int().tolist() if results.boxes.id is not None else []

        # Build the detections list
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box) 
            w, h = x2 - x1, y2 - y1
            cx, cy = x1 + w / 2, y1 + h / 2
            
            class_id = int(classes[i]) if len(classes) > i else -1
            track_id = track_ids[i] if len(track_ids) > i else -1
            
            detections.append({
                "bbox": (x1, y1, w, h),
                "center": (cx, cy),
                "cls": class_id,
                "id": track_id # New persistent ID for tracking
            })

        return detections