"""
FinWise Teen — API Entry Point
Starts FastAPI with both legacy v1 routes and new v2 FinWise routes.
"""

import time
import logging
import uvicorn
from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.api.finwise_routes import router as finwise_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="FinWise Teen API",
    description="AI-powered financial planning for young Indians",
    version="2.0.0",
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Duration: {duration:.2f}s")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





# FinWise Teen routes (v2)
app.include_router(finwise_router)


@app.get("/")
async def root():
    return {
        "app": "FinWise Teen",
        "version": "2.0",
        "docs": "/docs",
        "api_v2": "/api/v2",
    }

if __name__ == "__main__":
    uvicorn.run(
        "run_api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
