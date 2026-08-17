import asyncio

from sqlalchemy import text

from app.core.database import SessionLocal


async def enqueue_due_jobs():

    query = text("""
        UPDATE jobs

        SET
            status = 'queued',
            queued_at = NOW(),
            updated_at = NOW()

        WHERE
            status = 'scheduled'
            AND scheduled_at <= NOW()

        RETURNING id;
    """)

    async with SessionLocal() as session:

        result = await session.execute(query)

        rows = result.fetchall()

        await session.commit()

        return [
            row[0]
            for row in rows
        ]


async def main():

    print("Scheduler started")

    while True:

        job_ids = await enqueue_due_jobs()

        for job_id in job_ids:
            print(
                f"Scheduler queued Job {job_id}"
            )

        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())