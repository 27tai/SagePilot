"""
FastAPI application entry point.

Start the server:
    uvicorn app.main:app --reload --port 8000

Start the Temporal worker (separate terminal):
    python -m app.temporal.worker
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.workflows import router as workflows_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SagePilot Workflow Engine",
    description="Visual workflow automation engine backed by Temporal.",
    version="0.1.0",
)

# Allow all origins during development — tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "sagepilot-backend"}


@app.get("/api/node-types")
async def node_types() -> dict:
    """Return all registered node types — useful for the frontend palette."""
    from app.nodes.registry import NODE_REGISTRY
    return {
        "node_types": list(NODE_REGISTRY.keys()),
    }
