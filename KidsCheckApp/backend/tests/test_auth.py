"""Tests for authentication: login, token validation, RBAC."""
import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_data):
    resp = await client.post("/api/auth/login", json={"username": "baba", "password": "123456"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "baba"
    assert data["user"]["role"] == "parent"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, seed_data):
    resp = await client.post("/api/auth/login", json={"username": "baba", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, seed_data):
    resp = await client.post("/api/auth/login", json={"username": "nobody", "password": "123456"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, parent_token):
    resp = await client.get("/api/auth/me", headers=auth_header(parent_token))
    assert resp.status_code == 200
    assert resp.json()["role"] == "parent"


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    resp = await client.get("/api/auth/me", headers=auth_header("invalid.token.here"))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_token(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_rbac_parent_only_endpoint(client: AsyncClient, grandparent_token):
    """Grandparent cannot access parent-only endpoints like creating templates."""
    resp = await client.post(
        "/api/templates/1",
        json={"weekday": 1, "title": "test", "type": "written", "points": 5},
        headers=auth_header(grandparent_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_rbac_parent_allowed(client: AsyncClient, parent_token, seed_data):
    """Parent can create templates."""
    child_id = seed_data["luobo"].id
    resp = await client.post(
        f"/api/templates/{child_id}",
        json={"weekday": 1, "title": "数学口算", "type": "written", "description": "2页", "points": 5},
        headers=auth_header(parent_token),
    )
    assert resp.status_code == 200
