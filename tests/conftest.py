import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.database.models import Base
from app.database.session import get_db_session
from app.main import create_app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse_test",
)


async def _ensure_test_database_exists() -> None:
    """Create the test database if it does not exist yet.

    The fixtures below only create/drop the *schema* (``Base.metadata``), so
    the database itself has to be there first. Doing it here means ``pytest``
    works on a fresh checkout with nothing more than::

        docker compose up -d postgres

    instead of failing every test with
    ``InvalidCatalogNameError: database "mailpulse_test" does not exist``.
    """
    url = make_url(TEST_DATABASE_URL)
    target_db = url.database
    if not target_db:
        return

    # Postgres has no "CREATE DATABASE IF NOT EXISTS", so connect to the
    # maintenance database, check, then create.
    admin_engine = create_async_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target_db},
            )
            if exists is None:
                # A database name cannot be a bound parameter. `target_db`
                # comes from our own configuration, not from user input.
                await conn.exec_driver_sql(f'CREATE DATABASE "{target_db}"')
    finally:
        await admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _test_database() -> None:
    """Session-scoped, so it runs once before any test that needs the DB."""
    asyncio.run(_ensure_test_database_exists())


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "mailbox-user@example.com",
            "password": "securepass123",
            "full_name": "Mailbox User",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
