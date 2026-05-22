"""Create all database tables.

Usage:
    python -m scripts.init_db
"""
from __future__ import annotations

import asyncio

from app.database.models import Base
from app.database.session import engine


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())