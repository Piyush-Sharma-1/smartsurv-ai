"""
DeepSORT Multi-Object Tracker
Maintains consistent IDs for each object across video frames.

DeepSORT works by combining:
  1. Kalman Filter: predicts where an object will be next frame
  2. Appearance descriptor (Re-ID): checks if a detected box 
     looks like a tracked object from before
  3. Hungarian Algorithm: optimally assigns detections to tracks
"""
from deep_sort_realtime.deepsort_tracker import DeepSort
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ObjectTracker:
    """Wraps DeepSORT with history tracking for trail visualization."""

    def __init__(self, max_age: int = 30, n_init: int = 3):
        """
        max_age: frames to keep a track alive without a detection match
        n_init:  consecutive frames needed before track is confirmed
        """
        self.max_age = max_age
        self.n_init  = n_init
        self._init_tracker()
        
        # Stores position history per track: {track_id: [(x, y), ...]}
        self.track_history: Dict[int, List] = {}
        # Stores class per track: {track_id: class_name}
        self.track_classes: Dict[int, str] = {}

    def _init_tracker(self):
        self.tracker = DeepSort(
            max_age=self.max_age,
            n_init=self.n_init,
            max_cosine_distance=0.3,
            nn_budget=None,
        )

    def update(self, detections: List[Dict], frame: np.ndarray) -> List[Dict]:
        """
        Feed detections into DeepSORT, get back confirmed tracks with IDs.
        
        DeepSORT input format: ([x, y, w, h], confidence, class_name)
        """
        # Convert our detection format → DeepSORT format
        ds_input = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            w = x2 - x1
            h = y2 - y1
            ds_input.append(([x1, y1, w, h], det["confidence"], det["class_name"]))

        # Run tracker
        tracks = self.tracker.update_tracks(ds_input, frame=frame)

        tracked_objects: List[Dict] = []
        for track in tracks:
            if not track.is_confirmed():
                continue

            tid  = track.track_id
            ltrb = track.to_ltrb()       # left, top, right, bottom
            x1, y1, x2, y2 = ltrb
            center = [(x1 + x2) / 2, (y1 + y2) / 2]
            cls_name = track.det_class or "unknown"

            # Store class
            self.track_classes[tid] = cls_name

            # Update history
            if tid not in self.track_history:
                self.track_history[tid] = []
            self.track_history[tid].append(center)
            # Keep last 40 positions for trail
            if len(self.track_history[tid]) > 40:
                self.track_history[tid].pop(0)

            velocity = self._compute_velocity(tid)

            tracked_objects.append({
                "track_id":   tid,
                "bbox":       [x1, y1, x2, y2],
                "center":     center,
                "class_name": cls_name,
                "history":    list(self.track_history[tid]),
                "velocity":   velocity,
                "confidence": track.det_conf if track.det_conf else 0.0,
            })

        return tracked_objects

    def _compute_velocity(self, track_id: int) -> Dict:
        """Compute frame-to-frame velocity from last 2 positions."""
        history = self.track_history.get(track_id, [])
        if len(history) < 2:
            return {"dx": 0.0, "dy": 0.0, "speed": 0.0}
        
        dx = history[-1][0] - history[-2][0]
        dy = history[-1][1] - history[-2][1]
        speed = float(np.sqrt(dx**2 + dy**2))
        return {"dx": float(dx), "dy": float(dy), "speed": round(speed, 2)}

    def reset(self):
        """Full reset — call at the start of each new video."""
        self._init_tracker()
        self.track_history.clear()
        self.track_classes.clear()