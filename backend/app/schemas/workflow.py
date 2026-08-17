from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):

    id: str

    job_type: str

    payload: dict = Field(
        default_factory=dict
    )

    priority: int = 5

    max_retries: int = 3

    depends_on: list[str] = Field(
        default_factory=list
    )


class WorkflowCreate(BaseModel):

    name: str

    steps: list[WorkflowStep]