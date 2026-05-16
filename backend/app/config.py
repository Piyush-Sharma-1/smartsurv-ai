from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # CORS — add your Vercel URL here once deployed
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://smartsurv-ai.vercel.app",   # update after deploy
    ]
    
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    MAX_VIDEO_SIZE_MB: int = 200
    
    # Model settings
    YOLO_MODEL: str = "yolov8n.pt"  # nano=fastest; yolov8s.pt=balanced; yolov8m.pt=best
    DETECTION_CONFIDENCE: float = 0.5
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create directories on import
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)