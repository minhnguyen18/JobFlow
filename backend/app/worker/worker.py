import asyncio
import socket
import uuid
import json

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.database import SessionLocal
from app.worker.handlers import HANDLERS


WORKER_ID = (
    f"{socket.gethostname()}-"
    f"{uuid.uuid4().hex[:8]}"
)


async def claim_job():
    query = text("""
        WITH next_job AS (
            SELECT id
            FROM jobs
            WHERE status = 'queued'
            ORDER BY
                priority DESC,
                queued_at ASC,
                id ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )

        UPDATE jobs AS j
        SET
            status = 'running',
            worker_id = :worker_id,
            started_at = NOW(),
            heartbeat_at = NOW(),
            attempt_count = j.attempt_count + 1,
            updated_at = NOW()

        FROM next_job

        WHERE j.id = next_job.id

        RETURNING
            j.id,
            j.job_type,
            j.payload,
            j.priority,
            j.attempt_count,
            j.retry_count,
            j.max_retries,
            j.worker_id;
    """)

    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                query,
                {"worker_id": WORKER_ID},
            )

            row = result.mappings().first()

            if row is None:
                return None

            return dict(row)


async def complete_job(job_id: int, result_data: dict):
    import json

    query = text("""
        UPDATE jobs
        SET
            status = 'succeeded',
            result = CAST(:result AS JSONB),
            completed_at = NOW(),
            heartbeat_at = NULL,
            worker_id = NULL,
            updated_at = NOW()

        WHERE
            id = :job_id
            AND worker_id = :worker_id
            AND status = 'running';
    """)

    async with SessionLocal() as session:
        await session.execute(
            query,
            {
                "job_id": job_id,
                "worker_id": WORKER_ID,
                "result": json.dumps(result_data),
            },
        )

        await session.commit()


async def fail_job(job: dict, error: Exception):
    retry_count = job["retry_count"]
    max_retries = job["max_retries"]

    async with SessionLocal() as session:

        if retry_count < max_retries:
            delay = min(
                5 * (2 ** retry_count),
                300,
            )

            next_retry = (
                datetime.now(timezone.utc)
                + timedelta(seconds=delay)
            )

            query = text("""
                UPDATE jobs
                SET
                    status = 'scheduled',
                    retry_count = retry_count + 1,
                    scheduled_at = :scheduled_at,
                    last_error = :error,
                    heartbeat_at = NULL,
                    worker_id = NULL,
                    updated_at = NOW()

                WHERE
                    id = :job_id
                    AND worker_id = :worker_id;
            """)

            await session.execute(
                query,
                {
                    "job_id": job["id"],
                    "worker_id": WORKER_ID,
                    "scheduled_at": next_retry,
                    "error": str(error),
                },
            )

            print(
                f"[{WORKER_ID}] "
                f"Job {job['id']} failed. "
                f"Retry in {delay}s"
            )

        else:
            query = text("""
                UPDATE jobs
                SET
                    status = 'dead',
                    completed_at = NOW(),
                    last_error = :error,
                    heartbeat_at = NULL,
                    worker_id = NULL,
                    updated_at = NOW()

                WHERE
                    id = :job_id
                    AND worker_id = :worker_id;
            """)

            await session.execute(
                query,
                {
                    "job_id": job["id"],
                    "worker_id": WORKER_ID,
                    "error": str(error),
                },
            )

            print(
                f"[{WORKER_ID}] "
                f"Job {job['id']} moved to dead letter"
            )

        await session.commit()


async def heartbeat_loop(job_id: int):
    try:
        while True:
            await asyncio.sleep(3)

            query = text("""
                UPDATE jobs
                SET
                    heartbeat_at = NOW(),
                    updated_at = NOW()

                WHERE
                    id = :job_id
                    AND worker_id = :worker_id
                    AND status = 'running';
            """)

            async with SessionLocal() as session:
                await session.execute(
                    query,
                    {
                        "job_id": job_id,
                        "worker_id": WORKER_ID,
                    },
                )

                await session.commit()

    except asyncio.CancelledError:
        return


async def execute_job(job: dict):
    job_id = job["id"]
    job_type = job["job_type"]

    handler = HANDLERS.get(job_type)

    if handler is None:
        await fail_job(
            job,
            RuntimeError(
                f"Unknown job type: {job_type}"
            ),
        )

        return

    print(
        f"[{WORKER_ID}] "
        f"Executing Job {job_id} "
        f"type={job_type}"
    )

    heartbeat_task = asyncio.create_task(
        heartbeat_loop(job_id)
    )

    try:
        payload = dict(job["payload"])

        payload["_attempt"] = job["attempt_count"]

        result = await handler(payload)

        await complete_job(
            job_id,
            result,
        )

        print(
            f"[{WORKER_ID}] "
            f"Job {job_id} succeeded"
        )

    except Exception as exc:
        await fail_job(
            job,
            exc,
        )

    finally:
        heartbeat_task.cancel()

        try:
            await heartbeat_task

        except asyncio.CancelledError:
            pass


async def worker_slot(slot_number: int):
    print(
        f"[{WORKER_ID}] "
        f"Slot {slot_number} started"
    )

    while True:
        job = await claim_job()

        if job is None:
            await asyncio.sleep(0.5)
            continue

        await execute_job(job)


async def main():
    concurrency = 4

    print(
        f"Worker started: {WORKER_ID}"
    )

    print(
        f"Concurrency: {concurrency}"
    )

    slots = [
        worker_slot(i)
        for i in range(1, concurrency + 1)
    ]

    await asyncio.gather(*slots)


if __name__ == "__main__":
    asyncio.run(main())