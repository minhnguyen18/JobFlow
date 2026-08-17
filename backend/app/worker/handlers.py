import asyncio
from datetime import datetime, timedelta, timezone

async def add_numbers(payload: dict) -> dict:
    a = payload["a"]
    b = payload["b"]

    return {
        "answer": a + b
    }


async def sleep_job(payload: dict) -> dict:
    seconds = payload.get("seconds", 5)

    await asyncio.sleep(seconds)

    return {
        "slept_for": seconds
    }


async def always_fail(payload: dict) -> dict:
    raise RuntimeError(
        "Intentional failure for testing"
    )


async def unstable_job(payload: dict) -> dict:
    attempt = payload.get("_attempt", 1)
    fail_until = payload.get("fail_until", 2)

    if attempt <= fail_until:
        raise RuntimeError(
            f"Intentional failure on attempt {attempt}"
        )

    return {
        "message": "Eventually succeeded"
    }


HANDLERS = {
    "add_numbers": add_numbers,
    "sleep": sleep_job,
    "always_fail": always_fail,
    "unstable": unstable_job,
}

