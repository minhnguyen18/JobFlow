from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobDependency(Base):

    __tablename__ = "job_dependencies"

    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    depends_on_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )