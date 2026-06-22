import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_and_me(client: AsyncClient):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "securepass123",
            "full_name": "Test User",
        },
    )
    assert register_response.status_code == 201
    tokens = register_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200
    user = me_response.json()
    assert user["email"] == "user@example.com"
    assert user["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_login_with_registered_user(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "securepass123"},
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "securepass123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "securepass123"},
    )
    old_refresh = register_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert new_tokens["refresh_token"] != old_refresh


@pytest.mark.asyncio
async def test_duplicate_registration_returns_conflict(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "securepass123"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
