"""
Analysis result endpoints — serve processed data for charts/tables.
"""
from fastapi import APIRouter, HTTPException
from app.routers.video import job_store

router = APIRouter()


@router.get("/results/{job_id}")
async def get_results(job_id: str):
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    job = job_store[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, f"Job status is '{job['status']}', not yet completed")
    return job["results"]


@router.get("/anomalies/{job_id}")
async def get_anomalies(job_id: str):
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    job = job_store[job_id]
    if not job.get("results"):
        raise HTTPException(400, "No results yet")
    return job["results"]["summary"]


@router.get("/frames/{job_id}")
async def get_frame_data(job_id: str, limit: int = 500):
    """Return per-frame data for time-series charts."""
    if job_id not in job_store:
        raise HTTPException(404, "Job not found")
    results = job_store[job_id].get("results", {})
    frames  = results.get("frame_results", [])
    # Downsample if too many frames
    if len(frames) > limit:
        step = len(frames) // limit
        frames = frames[::step]
    return {"frames": frames, "total": len(frames)}