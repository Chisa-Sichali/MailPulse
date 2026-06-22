from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_list_and_get_webhook(client: AsyncClient, auth_headers: dict[str, str]):
    create_response = await client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={
            "url": "https://example.com/webhook",
            "name": "Primary webhook",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["url"].startswith("https://example.com/webhook")
    assert created["secret"].startswith("whsec_")
    assert "secret" not in created or created["secret"]  # returned once on create

    list_response = await client.get("/api/v1/webhooks", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert "secret" not in list_response.json()[0]

    webhook_id = created["id"]
    detail_response = await client.get(
        f"/api/v1/webhooks/{webhook_id}",
        headers=auth_headers,
    )
    assert detail_response.status_code == 200


@pytest.mark.asyncio
async def test_rotate_secret_and_update_webhook(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    create_response = await client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={"url": "https://example.com/hook"},
    )
    webhook_id = create_response.json()["id"]

    rotate_response = await client.post(
        f"/api/v1/webhooks/{webhook_id}/rotate-secret",
        headers=auth_headers,
    )
    assert rotate_response.status_code == 200
    assert rotate_response.json()["secret"].startswith("whsec_")

    patch_response = await client.patch(
        f"/api/v1/webhooks/{webhook_id}",
        headers=auth_headers,
        json={"is_enabled": False, "name": "Disabled hook"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["is_enabled"] is False


@pytest.mark.asyncio
async def test_test_webhook_endpoint(client: AsyncClient, auth_headers: dict[str, str]):
    create_response = await client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={"url": "https://example.com/hook"},
    )
    webhook_id = create_response.json()["id"]

    with patch(
        "app.services.webhook.webhook_service.WebhookDispatcher.deliver_test",
        new=AsyncMock(return_value=(200, "ok")),
    ):
        response = await client.post(
            f"/api/v1/webhooks/{webhook_id}/test",
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_webhook_requires_authentication(client: AsyncClient):
    response = await client.get("/api/v1/webhooks")
    assert response.status_code == 401
