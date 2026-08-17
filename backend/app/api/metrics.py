from fastapi import APIRouter

from sqlalchemy import text

from app.core.database import SessionLocal


router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
)


@router.get("")
async def metrics():

    query = text("""
        SELECT

            COUNT(*) FILTER (
                WHERE status = 'queued'
            ) AS queued,

            COUNT(*) FILTER (
                WHERE status = 'running'
            ) AS running,

            COUNT(*) FILTER (
                WHERE status = 'scheduled'
            ) AS scheduled,

            COUNT(*) FILTER (
                WHERE status = 'succeeded'
            ) AS succeeded,

            COUNT(*) FILTER (
                WHERE status = 'dead'
            ) AS dead,

            COUNT(*) FILTER (
                WHERE status = 'blocked'
            ) AS blocked

        FROM jobs;
    """)

    async with SessionLocal() as session:

        result = await session.execute(query)

        return dict(
            result.mappings().one()
        )