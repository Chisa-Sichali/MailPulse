from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session_factory


@asynccontextmanager
async def worker_session():
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
