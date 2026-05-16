"""
Anomaly Detection Engine
Analyzes motion and behavior patterns to flag suspicious activity.

Detects:
  1. RUNNING        — speed exceeds threshold
  2. LOITERING      — person stays in small area for too long
  3. CROWD_SURGE    — too many people detected simultaneously
  4. MASS_MOVEMENT  — large portion of frame in motion (optical flow)
  5. DIRECTION_CHANGE — sharp directional reversal
"""
import cv2
import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


# Anomaly severity levels
SEVERITY = {
    "LOW":    {"label": "Low",    "color": (0, 255, 255)},   # cyan
    "MEDIUM": {"label": "Medium", "color": (0, 165, 255)},   # orange
    "HIGH":   {"label": "High",   "color": (0, 0, 255)},     # red
}


class AnomalyDetector:
    def __init__(
        self,
        speed_threshold: float = 15.0,       # px/frame — above = running
        loiter_frames: int = 80,              # frames before loitering alert
        loiter_area_px: float = 40.0,         # max displacement = "not moving"
        crowd_count: int = 8,                 # people to trigger crowd alert
        direction_angle: float = 110.0,       # degrees of turn = direction change
        motion_ratio: float = 0.35,           # fraction of frame moving = mass movement
    ):
        self.speed_threshold   = speed_threshold
        self.loiter_frames     = loiter_frames
        self.loiter_area_px    = loiter_area_px
        self.crowd_count       = crowd_count
        self.direction_angle   = direction_angle
        self.motion_ratio      = motion_ratio

        # Per-track state
        self.track_speeds:    Dict[int, deque] = defaultdict(lambda: deque(maxlen=15))
        self.track_positions: Dict[int, deque] = defaultdict(lambda: deque(maxlen=120))
        self.track_frame_cnt: Dict[int, int]   = defaultdict(int)

        # Background subtractor for mass motion detection
        self.bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False
        )

        self.frame_count  = 0
        self.anomaly_log: List[Dict] = []

    # ──────────────────────────────────────────────────────────────────
    def analyze(self, frame: np.ndarray, tracked_objects: List[Dict]) -> Dict:
        """Main entry point — call once per frame."""
        self.frame_count += 1
        anomalies: List[Dict] = []

        # Update per-track state
        for obj in tracked_objects:
            tid = obj["track_id"]
            vel = obj.get("velocity", {})
            self.track_speeds[tid].append(vel.get("speed", 0.0))
            self.track_positions[tid].append(obj["center"])
            if obj["class_name"] == "person":
                self.track_frame_cnt[tid] += 1

        # ── 1. Running ────────────────────────────────────────────────
        for obj in tracked_objects:
            if obj["class_name"] != "person":
                continue
            tid = obj["track_id"]
            speeds = list(self.track_speeds[tid])
            if len(speeds) >= 5:
                avg = np.mean(speeds[-5:])
                if avg > self.speed_threshold:
                    anomalies.append(self._make(
                        "RUNNING", "MEDIUM", tid,
                        f"Person #{tid} running — speed {avg:.1f} px/frame",
                        obj["center"]
                    ))

        # ── 2. Loitering ──────────────────────────────────────────────
        for obj in tracked_objects:
            if obj["class_name"] != "person":
                continue
            tid = obj["track_id"]
            frames_here = self.track_frame_cnt[tid]
            if frames_here > self.loiter_frames:
                positions = list(self.track_positions[tid])
                if len(positions) >= 20:
                    arr = np.array(positions[-20:])
                    spread = np.max(np.std(arr, axis=0))
                    if spread < self.loiter_area_px:
                        anomalies.append(self._make(
                            "LOITERING", "HIGH", tid,
                            f"Person #{tid} loitering ({frames_here} frames, "
                            f"area spread {spread:.1f}px)",
                            obj["center"]
                        ))

        # ── 3. Crowd surge ────────────────────────────────────────────
        people = [o for o in tracked_objects if o["class_name"] == "person"]
        if len(people) >= self.crowd_count:
            anomalies.append(self._make(
                "CROWD_SURGE", "HIGH", None,
                f"High crowd density — {len(people)} people in frame",
                None
            ))

        # ── 4. Direction change ───────────────────────────────────────
        for obj in tracked_objects:
            if obj["class_name"] != "person":
                continue
            result = self._check_direction(obj["track_id"])
            if result:
                result["location"] = obj["center"]
                anomalies.append(result)

        # ── 5. Mass movement (background subtraction) ─────────────────
        fg_mask    = self.bg_sub.apply(frame)
        motion_pct = float(np.sum(fg_mask > 0)) / fg_mask.size
        if motion_pct > self.motion_ratio:
            anomalies.append(self._make(
                "MASS_MOVEMENT", "HIGH", None,
                f"Mass movement detected ({motion_pct:.1%} of frame in motion)",
                None
            ))

        # Log unique anomalies (don't spam the same type every frame)
        for a in anomalies:
            # Deduplicate: only log same type+track if last log was 30+ frames ago
            recent = [
                x for x in self.anomaly_log[-20:]
                if x["type"] == a["type"] and x["track_id"] == a["track_id"]
            ]
            if not recent or (self.frame_count - recent[-1]["frame"]) > 30:
                self.anomaly_log.append(a)

        return {
            "frame":          self.frame_count,
            "anomalies":      anomalies,
            "people_count":   len(people),
            "motion_score":   round(motion_pct, 4),
            "total_tracks":   len(tracked_objects),
        }

    # ──────────────────────────────────────────────────────────────────
    def _check_direction(self, tid: int) -> Optional[Dict]:
        positions = list(self.track_positions[tid])
        if len(positions) < 12:
            return None

        recent_dir = np.array(positions[-1]) - np.array(positions[-4])
        older_dir  = np.array(positions[-7]) - np.array(positions[-10])

        if np.linalg.norm(recent_dir) < 2 or np.linalg.norm(older_dir) < 2:
            return None

        cos_theta = np.dot(recent_dir, older_dir) / (
            np.linalg.norm(recent_dir) * np.linalg.norm(older_dir)
        )
        angle = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))

        if angle > self.direction_angle:
            return self._make(
                "DIRECTION_CHANGE", "LOW", tid,
                f"Person #{tid} sudden direction change ({angle:.0f}°)",
                None
            )
        return None

    def _make(
        self,
        atype: str,
        severity: str,
        track_id: Optional[int],
        description: str,
        location: Optional[List[float]],
    ) -> Dict:
        return {
            "type":        atype,
            "severity":    severity,
            "track_id":    track_id,
            "description": description,
            "location":    location,
            "frame":       self.frame_count,
        }

    def get_summary(self) -> Dict:
        by_type: Dict[str, int] = defaultdict(int)
        for a in self.anomaly_log:
            by_type[a["type"]] += 1
        
        by_severity: Dict[str, int] = defaultdict(int)
        for a in self.anomaly_log:
            by_severity[a["severity"]] += 1

        return {
            "total_anomalies": len(self.anomaly_log),
            "by_type":         dict(by_type),
            "by_severity":     dict(by_severity),
            "anomaly_log":     self.anomaly_log[-100:],  # Last 100 entries
        }

    def reset(self):
        self.track_speeds.clear()
        self.track_positions.clear()
        self.track_frame_cnt.clear()
        self.frame_count = 0
        self.anomaly_log = []
        self.bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False
        )