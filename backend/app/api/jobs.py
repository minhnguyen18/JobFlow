from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.post("", response_model=JobResponse)
async def create_job(
    data: JobCreate,
    session: AsyncSession = Depends(get_session),
):
    if data.scheduled_at is not None:
        status = "scheduled"
        queued_at = None
    else:
        status = "queued"
        queued_at = datetime.now(timezone.utc)

    job = Job(
        job_type=data.job_type,
        payload=data.payload,
        priority=data.priority,
        max_retries=data.max_retries,
        scheduled_at=data.scheduled_at,
        status=status,
        queued_at=queued_at,
    )

    session.add(job)

    await session.commit()
    await session.refresh(job)

    return job


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Job).order_by(Job.id.desc())
    )

    return result.scalars().all()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Job).where(Job.id == job_id)
    )

    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job