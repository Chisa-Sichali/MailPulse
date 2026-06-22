import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.models.email_event import EmailEvent, EmailEventStatus
from app.database.models.mailbox import Mailbox, MailboxHealthStatus


async def _seed_analytics_data(session_factory, *, user_id: uuid.UUID) -> None:
    async with session_factory() as session:
        mailbox = Mailbox(
            user_id=user_id,
            email_address="analytics@example.com",
            imap_username="analytics@example.com",
            imap_host="imap.example.com",
            imap_port=993,
            encrypted_password="enc",
            health_status=MailboxHealthStatus.HEALTHY.value,
        )
        session.add(mailbox)
        await session.flush()

        event = EmailEvent(
            mailbox_id=mailbox.id,
            message_id="<analytics@example.com>",
            sender_email="sender@example.com",
            sender_name="Sender",
            recipients=["analytics@example.com"],
            subject="Analytics test",
            status=EmailEventStatus.PROCESSED.value,
        )
        session.add(event)
        await session.commit()


@pytest.mark.asyncio
async def test_analytics_overview(client: AsyncClient, auth_headers: dict[str, str], db_engine):
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == 200
    user_id = uuid.UUID(me.json()["id"])

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    await _seed_analytics_data(session_factory, user_id=user_id)

    response = await client.get("/api/v1/analytics/overview?days=7", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["emails_processed_total"] >= 1
    assert body["period_days"] == 7


@pytest.mark.asyncio
async def test_analytics_top_senders(client: AsyncClient, auth_headers: dict[str, str], db_engine):
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = uuid.UUID(me.json()["id"])

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    await _seed_analytics_data(session_factory, user_id=user_id)

    response = await client.get("/api/v1/analytics/top-senders", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_system_health_endpoint(client: AsyncClient):
    response = await client.get("/health/system")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"healthy", "degraded"}
    assert "checks" in body
