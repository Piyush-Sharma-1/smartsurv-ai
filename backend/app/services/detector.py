"""
YOLOv8 Object Detector
Uses the ultralytics library to detect objects in frames.
YOLOv8n (nano) is used by default — fastest, suitable for real-time processing.
"""
from ultralytics import YOLO
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


# COCO class IDs we care about for surveillance
SURVEILLANCE_CLASSES = {
    0:  "person",
    1:  "bicycle",
    2:  "car",
    3:  "motorcycle",
    5:  "bus",
    7:  "truck",
    14: "bird",
    15: "cat",
    16: "dog",
}

# Color per class (BGR for OpenCV)
CLASS_COLORS = {
    "person":     (50, 205, 50),    # lime green
    "car":        (255, 140, 0),    # orange
    "motorcycle": (255, 0, 255),    # magenta
    "bus":        (0, 191, 255),    # deep sky blue
    "truck":      (220, 20, 60),    # crimson
    "bicycle":    (255, 215, 0),    # gold
    "default":    (128, 0, 128),    # purple
}


class ObjectDetector:
    """Wraps YOLOv8 for surveillance-focused detection."""

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.5):
        logger.info(f"Loading YOLO model: {model_name}")
        self.model = YOLO(model_name)   # auto-downloads on first run
        self.confidence = confidence
        logger.info("YOLO model loaded successfully")

    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Run detection on a single frame.
        Returns a list of detection dicts.
        """
        results = self.model(
            frame,
            conf=self.confidence,
            verbose=False,       # suppress ultralytics console spam
            classes=list(SURVEILLANCE_CLASSES.keys()),
        )

        detections: List[Dict] = []
        for result in results:
            for box in result.boxes:
                cls_id  = int(box.cls[0])
                cls_name = SURVEILLANCE_CLASSES.get(cls_id, "unknown")
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])

                detections.append({
                    "bbox":       [x1, y1, x2, y2],   # left, top, right, bottom
                    "confidence": round(conf, 3),
                    "class_id":   cls_id,
                    "class_name": cls_name,
                    "center":     [(x1 + x2) / 2, (y1 + y2) / 2],
                    "width":      x2 - x1,
                    "height":     y2 - y1,
                    "color":      CLASS_COLORS.get(cls_name, CLASS_COLORS["default"]),
                })

        return detections