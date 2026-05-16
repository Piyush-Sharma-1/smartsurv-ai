"""
Video processing API endpoints.

POST /api/video/upload   — Upload video, start background processing
GET  /api/video/status/{job_id} — Poll for job status + results
GET  /api/video/jobs     — List all jobs
"""
import os
import uuid
import logging
from typing import Dict
from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.services.pipeline import SurveillancePipeline
from app.config import settings

logger  = logging.getLogger(__name__)
router  = APIRouter()
pipeline = SurveillancePipeline(
    model_name=settings.YOLO_MODEL,
    confidence=settings.DETECTION_CONFIDENCE,
)

# In-memory job store (use Redis in production)
job_store: Dict[str, Dict] = {}


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a video file and kick off background processing."""
    # Validate
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(400, f"Invalid file type: {file.content_type}. Upload a video file.")

    job_id      = str(uuid.uuid4())
    filename    = Path(file.filename).name if file.filename else "video.mp4"
    upload_path = os.path.join(settings.UPLOAD_DIR, f"{job_id}_{filename}")
    output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_annotated.mp4")

    # Save uploaded bytes
    async with aiofiles.open(upload_path, "wb") as f:
        content = await file.read()
        if len(content) > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise HTTPException(413, f"Video exceeds {settings.MAX_VIDEO_SIZE_MB}MB limit")
        await f.write(content)

    job_store[job_id] = {
        "job_id":       job_id,
        "status":       "queued",
        "progress":     0.0,
        "filename":     filename,
        "upload_path":  upload_path,
        "output_path":  output_path,
        "results":      None,
        "error":        None,
    }

    background_tasks.add_task(_process_task, job_id, upload_path, output_path)
    return {"job_id": job_id, "status": "queued", "filename": filename}


def _process_task(job_id: str, input_path: str, output_path: str):
    """Background task — runs the full ML pipeline."""
    try:
        job_store[job_id]["status"] = "processing"
        logger.info(f"[{job_id}] Starting pipeline on {input_path}")

        def cb(pct: float, frame: int):
            job_store[job_id]["progress"]      = pct
            job_store[job_id]["current_frame"] = frame

        results = pipeline.process_video(input_path, output_path, cb)

        job_store[job_id].update({
            "status":   "completed",
            "progress": 100.0,
            "results":  results,
        })
        logger.info(f"[{job_id}] Completed. {results['total_frames']} frames processed.")

    except Exception as exc:
        logger.exception(f"[{job_id}] Pipeline failed")
        job_store[job_id].update({"status": "failed", "error": str(exc)})


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """Poll this endpoint to check job progress."""
    if job_id not in job_store:
        raise HTTPException(404, f"Job {job_id} not found")

    job = dict(job_store[job_id])
    job.pop("upload_path", None)  # don't expose server paths

    if job["status"] == "completed":
        out_name = os.path.basename(job["output_path"])
        job["video_url"] = f"/outputs/{out_name}"

    return job


@router.get("/jobs")
async def list_jobs():
    """Return all jobs (status summary)."""
    return [
        {
            "job_id":   jid,
            "status":   j["status"],
            "progress": j.get("progress", 0),
            "filename": j.get("filename", ""),
        }
        for jid, j in job_store.items()
    ]