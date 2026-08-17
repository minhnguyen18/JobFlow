import asyncio

from app.core.database import engine
from app.models.base import Base

import app.models


async def main():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    print("Database tables created.")


if __name__ == "__main__":
    asyncio.run(main())