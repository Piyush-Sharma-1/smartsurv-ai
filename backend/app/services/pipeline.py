"""
Full Surveillance Pipeline
Connects Detector → Tracker → Anomaly Detector → Annotated Video
"""
import cv2
import numpy as np
import time
import logging
from typing import Dict, Callable, Optional

from app.services.detector import ObjectDetector, CLASS_COLORS
from app.services.tracker import ObjectTracker
from app.services.anomaly import AnomalyDetector, SEVERITY

logger = logging.getLogger(__name__)

ANOMALY_BG = {
    "LOW":    (40, 40, 0),
    "MEDIUM": (0, 60, 100),
    "HIGH":   (0, 0, 120),
}


class SurveillancePipeline:
    """
    Orchestrates the full pipeline on a video file.
    Creates an annotated output video and returns analysis results.
    """

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.5):
        self.detector = ObjectDetector(model_name=model_name, confidence=confidence)
        self.tracker  = ObjectTracker(max_age=30, n_init=3)
        self.anomaly  = AnomalyDetector()

    # ──────────────────────────────────────────────────────────────────
    def process_video(
        self,
        input_path:  str,
        output_path: str,
        progress_cb: Optional[Callable[[float, int], None]] = None,
    ) -> Dict:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {input_path}")

        fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Reset all services for fresh video
        self.tracker.reset()
        self.anomaly.reset()

        frame_results = []
        frame_count   = 0
        t0            = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # ─── Core pipeline ────────────────────────────────────────
            detections     = self.detector.detect(frame)
            tracked        = self.tracker.update(detections, frame)
            analysis       = self.anomaly.analyze(frame, tracked)

            # ─── Annotate ─────────────────────────────────────────────
            annotated = self._draw(frame, tracked, analysis)
            out.write(annotated)

            # ─── Store per-frame summary ──────────────────────────────
            frame_results.append({
                "frame":         frame_count,
                "detections":    len(detections),
                "tracks":        len(tracked),
                "people_count":  analysis["people_count"],
                "motion_score":  analysis["motion_score"],
                "anomaly_count": len(analysis["anomalies"]),
            })

            # ─── Progress callback ────────────────────────────────────
            if progress_cb and frame_count % 15 == 0:
                pct = (frame_count / total_frames * 100) if total_frames > 0 else 0
                progress_cb(round(pct, 1), frame_count)

        cap.release()
        out.release()

        elapsed = time.time() - t0
        summary = self.anomaly.get_summary()

        return {
            "total_frames":    frame_count,
            "fps":             round(fps, 2),
            "resolution":      f"{width}x{height}",
            "duration_sec":    round(frame_count / fps, 2) if fps else 0,
            "processing_time": round(elapsed, 2),
            "proc_fps":        round(frame_count / elapsed, 2) if elapsed > 0 else 0,
            "summary":         summary,
            "frame_results":   frame_results,
        }

    # ──────────────────────────────────────────────────────────────────
    def _draw(
        self,
        frame:    np.ndarray,
        tracked:  list,
        analysis: Dict,
    ) -> np.ndarray:
        ann = frame.copy()
        h, w = frame.shape[:2]

        # ── Draw trails and boxes ──────────────────────────────────────
        for obj in tracked:
            x1, y1, x2, y2 = [int(v) for v in obj["bbox"]]
            tid    = obj["track_id"]
            cls    = obj.get("class_name", "?")
            speed  = obj.get("velocity", {}).get("speed", 0)
            color  = CLASS_COLORS.get(cls, CLASS_COLORS["default"])

            # Trail
            history = obj.get("history", [])
            for i in range(1, len(history)):
                alpha = i / len(history)
                tc = tuple(int(c * alpha) for c in color)
                p1 = (int(history[i-1][0]), int(history[i-1][1]))
                p2 = (int(history[i][0]),   int(history[i][1]))
                cv2.line(ann, p1, p2, tc, 2)

            # Bounding box
            cv2.rectangle(ann, (x1, y1), (x2, y2), color, 2)

            # Label background
            label = f"#{tid} {cls} {speed:.0f}px/f"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(ann, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(ann, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        # ── Stats overlay (top-right) ─────────────────────────────────
        stats = [
            f"People:  {analysis['people_count']}",
            f"Tracks:  {analysis['total_tracks']}",
            f"Motion:  {analysis['motion_score']:.1%}",
            f"Frame:   {analysis['frame']}",
        ]
        for i, stat in enumerate(stats):
            y = 28 + i * 26
            cv2.rectangle(ann, (w - 190, y - 18), (w - 4, y + 6), (0, 0, 0, 160), -1)
            cv2.putText(ann, stat, (w - 186, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # ── Anomaly alerts (bottom-left) ──────────────────────────────
        anomalies = analysis.get("anomalies", [])
        for i, a in enumerate(anomalies[:4]):
            sev    = a.get("severity", "LOW")
            color  = SEVERITY[sev]["color"]
            bg     = ANOMALY_BG.get(sev, (0, 0, 0))
            text   = f"[{sev}] {a['type']}: {a['description'][:55]}"
            y      = h - 20 - i * 28
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(ann, (4, y - th - 4), (tw + 14, y + 6), bg, -1)
            cv2.rectangle(ann, (4, y - th - 4), (tw + 14, y + 6), color, 1)
            cv2.putText(ann, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return ann


