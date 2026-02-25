"""
FinWise Teen — API Entry Point
Starts FastAPI with both legacy v1 routes and new v2 FinWise routes.
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.finwise_routes import router as finwise_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="FinWise Teen API",
    description="AI-powered financial planning for young Indians",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
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
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
