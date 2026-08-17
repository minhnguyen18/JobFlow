from sqlalchemy import text

from app.core.database import SessionLocal


async def unlock_dependent_jobs(
    completed_job_id: int,
):

    query = text("""
        UPDATE jobs AS child

        SET
            status = 'queued',
            queued_at = NOW(),
            updated_at = NOW()

        WHERE
            child.status = 'blocked'

            AND EXISTS (
                SELECT 1
                FROM job_dependencies d

                WHERE
                    d.job_id = child.id
                    AND d.depends_on_job_id = :completed_job_id
            )

            AND NOT EXISTS (

                SELECT 1

                FROM job_dependencies d

                JOIN jobs parent
                    ON parent.id =
                       d.depends_on_job_id

                WHERE
                    d.job_id = child.id
                    AND parent.status != 'succeeded'
            )

        RETURNING child.id;
    """)

    async with SessionLocal() as session:

        result = await session.execute(
            query,
            {
                "completed_job_id":
                    completed_job_id
            },
        )

        rows = result.fetchall()

        await session.commit()

        return [
            row[0]
            for row in rows
        ]
    async def update_workflow_status(
    workflow_id: int | None,
    ):

        if workflow_id is None:
            return

    query = text("""
        SELECT
            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE status = 'succeeded'
            ) AS succeeded,

            COUNT(*) FILTER (
                WHERE status = 'dead'
            ) AS dead

        FROM jobs

        WHERE workflow_id = :workflow_id;
    """)

    async with SessionLocal() as session:

        result = await session.execute(
            query,
            {
                "workflow_id": workflow_id
            },
        )

        row = result.mappings().one()

        if row["dead"] > 0:

            await session.execute(
                text("""
                    UPDATE workflows

                    SET
                        status = 'failed',
                        completed_at = NOW()

                    WHERE id = :workflow_id;
                """),
                {
                    "workflow_id":
                        workflow_id
                },
            )

        elif (
            row["total"] > 0
            and row["total"] == row["succeeded"]
        ):

            await session.execute(
                text("""
                    UPDATE workflows

                    SET
                        status = 'succeeded',
                        completed_at = NOW()

                    WHERE id = :workflow_id;
                """),
                {
                    "workflow_id":
                        workflow_id
                },
            )

        await session.commit()