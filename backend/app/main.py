"""
FastAPI application entrypoint.
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import video, analysis

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SmartSurv AI",
    description="Computer Vision Surveillance Analytics API",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file serving for processed videos ───────────────────────────
os.makedirs("outputs", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# ── Routers ───────────────────────────────────────────────────────────
app.include_router(video.router,    prefix="/api/video",    tags=["Video"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])


@app.get("/")
def root():
    return {"service": "SmartSurv AI API", "status": "running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}