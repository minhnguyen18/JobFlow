from fastapi import FastAPI

from app.api.jobs import router as jobs_router

from app.api.workflows import (
    router as workflows_router
)
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="JobFlow",
    description="Distributed job queue and workflow orchestration engine",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }
from app.api.metrics import (
    router as metrics_router
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_router)

app.include_router(jobs_router)
app.include_router(workflows_router)