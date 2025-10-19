"""
Minimal AI Engine Service for debugging
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Legal India AI Engine - Minimal",
    description="Minimal AI service for debugging",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track service start time
SERVICE_START_TIME = datetime.now()

@app.get("/health")
async def health_check():
    """Simple health check"""
    uptime = (datetime.now() - SERVICE_START_TIME).total_seconds()
    
    return {
        "status": "ok",
        "uptime_seconds": uptime,
        "service": "ai-engine-minimal",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Legal India AI Engine - Minimal",
        "version": "1.0.0",
        "status": "running",
        "message": "Minimal service for debugging"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
