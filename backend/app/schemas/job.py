from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    job_type: str
    payload: dict = Field(default_factory=dict)

    priority: int = 5
    max_retries: int = 3

    scheduled_at: datetime | None = None


class JobResponse(BaseModel):
    id: int
    job_type: str
    payload: dict

    result: dict | None

    status: str
    priority: int

    attempt_count: int
    retry_count: int
    max_retries: int

    worker_id: str | None
    last_error: str | None

    scheduled_at: datetime | None
    queued_at: datetime | None
    started_at: datetime | None
    heartbeat_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )