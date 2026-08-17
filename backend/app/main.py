from fastapi import FastAPI

from app.api.jobs import router as jobs_router


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


app.include_router(jobs_router)