from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.security.encryption import decrypt_secret, encrypt_secret
from app.services.mailbox.imap_connection import ImapConnectionResult


def test_encrypt_decrypt_roundtrip():
    secret = "super-secret-imap-password"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert decrypt_secret(encrypted) == secret


@pytest.mark.asyncio
async def test_create_and_list_mailbox(client: AsyncClient, auth_headers: dict[str, str]):
    create_response = await client.post(
        "/api/v1/mailboxes",
        headers=auth_headers,
        json={
            "email_address": "inbox@example.com",
            "password": "imap-password",
            "imap_host": "imap.example.com",
            "imap_port": 993,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["email_address"] == "inbox@example.com"
    assert created["health_status"] == "unknown"
    assert "password" not in created

    list_response = await client.get("/api/v1/mailboxes", headers=auth_headers)
    assert list_response.status_code == 200
    mailboxes = list_response.json()
    assert mailboxes["limit"] == 50
    assert mailboxes["offset"] == 0
    assert len(mailboxes["items"]) == 1
    assert mailboxes["items"][0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_update_and_delete_mailbox(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    create_response = await client.post(
        "/api/v1/mailboxes",
        headers=auth_headers,
        json={
            "email_address": "update@example.com",
            "password": "imap-password",
            "imap_host": "imap.example.com",
        },
    )
    mailbox_id = create_response.json()["id"]

    get_response = await client.get(
        f"/api/v1/mailboxes/{mailbox_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200

    patch_response = await client.patch(
        f"/api/v1/mailboxes/{mailbox_id}",
        headers=auth_headers,
        json={"is_enabled": False, "imap_host": "imap.updated.com"},
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["is_enabled"] is False
    assert updated["imap_host"] == "imap.updated.com"

    delete_response = await client.delete(
        f"/api/v1/mailboxes/{mailbox_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    missing_response = await client.get(
        f"/api/v1/mailboxes/{mailbox_id}",
        headers=auth_headers,
    )
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_mailbox_returns_conflict(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    payload = {
        "email_address": "dup-mailbox@example.com",
        "password": "imap-password",
        "imap_host": "imap.example.com",
    }
    first = await client.post("/api/v1/mailboxes", headers=auth_headers, json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/mailboxes", headers=auth_headers, json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_mailbox_requires_authentication(client: AsyncClient):
    response = await client.get("/api/v1/mailboxes")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_connection_updates_health_status(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    create_response = await client.post(
        "/api/v1/mailboxes",
        headers=auth_headers,
        json={
            "email_address": "connect@example.com",
            "password": "imap-password",
            "imap_host": "imap.example.com",
        },
    )
    mailbox_id = create_response.json()["id"]

    with patch(
        "app.services.mailbox.mailbox_service.test_imap_connection",
        return_value=ImapConnectionResult(success=True, message="Connection successful"),
    ):
        response = await client.post(
            f"/api/v1/mailboxes/{mailbox_id}/test-connection",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["health_status"] == "healthy"

    with patch(
        "app.services.mailbox.mailbox_service.test_imap_connection",
        return_value=ImapConnectionResult(success=False, message="Invalid credentials"),
    ):
        failure = await client.post(
            f"/api/v1/mailboxes/{mailbox_id}/test-connection",
            headers=auth_headers,
        )

    assert failure.status_code == 200
    failure_body = failure.json()
    assert failure_body["success"] is False
    assert failure_body["health_status"] == "error"
    assert failure_body["mailbox"]["last_error_message"] == "Invalid credentials"
