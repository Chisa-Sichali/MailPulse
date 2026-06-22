from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10,
)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

def get_session_factory():
    return async_session_factory

async def get_db_session():
    async with async_session_factory() as session:
        yield session

def get_engine():
    return engine

async def dispose_engine():
    await engine.dispose()
