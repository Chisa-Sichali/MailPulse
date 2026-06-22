import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.database.models.email_event import EmailEvent, EmailEventStatus


async def _seed_event(session_factory, *, user_id: uuid.UUID, mailbox_id: uuid.UUID) -> uuid.UUID:
    async with session_factory() as session:
        event = EmailEvent(
            mailbox_id=mailbox_id,
            message_id="<event-1@example.com>",
            imap_uid="101",
            sender_email="sender@example.com",
            sender_name="Sender",
            recipients=["inbox@example.com"],
            subject="Test subject",
            text_body="Body",
            html_body="",
            attachments_metadata=[],
            status=EmailEventStatus.FAILED.value,
            attempt_count=1,
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event.id


@pytest.mark.asyncio
async def test_list_and_get_events(client: AsyncClient, auth_headers: dict[str, str], db_engine):
    mailbox_response = await client.post(
        "/api/v1/mailboxes",
        headers=auth_headers,
        json={
            "email_address": "events@example.com",
            "password": "imap-password",
            "imap_host": "imap.example.com",
        },
    )
    mailbox_id = uuid.UUID(mailbox_response.json()["id"])

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    event_id = await _seed_event(
        session_factory,
        user_id=uuid.uuid4(),
        mailbox_id=mailbox_id,
    )

    list_response = await client.get("/api/v1/events", headers=auth_headers)
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["limit"] == 50
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(event_id)

    detail_response = await client.get(f"/api/v1/events/{event_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == EmailEventStatus.FAILED.value


@pytest.mark.asyncio
async def test_retry_event_queues_processing_job(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_engine,
):
    mailbox_response = await client.post(
        "/api/v1/mailboxes",
        headers=auth_headers,
        json={
            "email_address": "retry@example.com",
            "password": "imap-password",
            "imap_host": "imap.example.com",
        },
    )
    mailbox_id = uuid.UUID(mailbox_response.json()["id"])

    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    event_id = await _seed_event(
        session_factory,
        user_id=uuid.uuid4(),
        mailbox_id=mailbox_id,
    )

    with patch(
        "app.core.queue.enqueue_process_email",
        new=AsyncMock(return_value="job-123"),
    ) as mock_enqueue:
        response = await client.post(
            f"/api/v1/events/{event_id}/retry",
            headers=auth_headers,
        )

    assert response.status_code == 202
    mock_enqueue.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_email_check_queues_monitor_sweep(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("CRON_SECRET_KEY", "test-cron-secret")
    get_settings.cache_clear()

    with patch(
        "app.api.v1.legacy.routes.enqueue_monitor_sweep",
        new=AsyncMock(return_value="monitor-job-1"),
    ):
        response = await client.post(
            "/api/v1/run-email-check",
            headers={"Authorization": "Bearer test-cron-secret"},
        )

    get_settings.cache_clear()
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
