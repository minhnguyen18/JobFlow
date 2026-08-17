from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.job import Job
from app.models.job_dependency import JobDependency
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate
from app.services.dag import validate_dag


router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
)


@router.post("")
async def create_workflow(
    data: WorkflowCreate,
    session: AsyncSession = Depends(get_session),
):

    try:
        validate_dag(data.steps)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    workflow = Workflow(
        name=data.name,
        definition=data.model_dump(),
        status="running",
        started_at=datetime.now(timezone.utc),
    )

    session.add(workflow)

    await session.flush()

    jobs_by_step = {}

    for step in data.steps:

        status = (
            "queued"
            if len(step.depends_on) == 0
            else "blocked"
        )

        job = Job(
            workflow_id=workflow.id,
            step_key=step.id,
            job_type=step.job_type,
            payload=step.payload,
            priority=step.priority,
            max_retries=step.max_retries,
            status=status,
            queued_at=(
                datetime.now(timezone.utc)
                if status == "queued"
                else None
            ),
        )

        session.add(job)

        await session.flush()

        jobs_by_step[step.id] = job

    for step in data.steps:

        child_job = jobs_by_step[step.id]

        for parent_step_id in step.depends_on:

            parent_job = jobs_by_step[
                parent_step_id
            ]

            dependency = JobDependency(
                job_id=child_job.id,
                depends_on_job_id=parent_job.id,
            )

            session.add(dependency)

    await session.commit()

    return {
        "workflow_id": workflow.id,
        "status": workflow.status,
    }