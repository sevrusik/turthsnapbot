"""
FraudLens FastAPI Application

Consumer API for TruthSnap Bot
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FraudLens Consumer API",
    description="AI-generated image detection for consumers",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from backend.api.routes import consumer

app.include_router(consumer.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "FraudLens Consumer API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/api/v1/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
