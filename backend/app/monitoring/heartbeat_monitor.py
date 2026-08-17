import asyncio

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.database import SessionLocal


HEARTBEAT_TIMEOUT_SECONDS = 10


async def recover_stale_jobs():

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(
            seconds=HEARTBEAT_TIMEOUT_SECONDS
        )
    )

    query = text("""
        UPDATE jobs

        SET
            status = 'queued',
            worker_id = NULL,
            heartbeat_at = NULL,
            started_at = NULL,
            queued_at = NOW(),
            last_error = 'Worker heartbeat expired; job requeued',
            updated_at = NOW()

        WHERE
            status = 'running'
            AND heartbeat_at < :cutoff

        RETURNING id;
    """)

    async with SessionLocal() as session:

        result = await session.execute(
            query,
            {
                "cutoff": cutoff
            },
        )

        rows = result.fetchall()

        await session.commit()

        return [
            row[0]
            for row in rows
        ]


async def main():

    print("Heartbeat monitor started")

    while True:

        recovered = await recover_stale_jobs()

        for job_id in recovered:

            print(
                f"Recovered abandoned "
                f"Job {job_id}"
            )

        await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())