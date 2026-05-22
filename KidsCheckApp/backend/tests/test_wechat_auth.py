import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from tests.conftest import TestSession
from app.models.models import User, UserRole


@pytest_asyncio.fixture
async def seed_wx_user():
    async with TestSession() as db:
        u = User(username="yeye_wx", password_hash="123456", role=UserRole.grandparent)
        db.add(u)
        await db.commit()
        await db.refresh(u)
        return u


@pytest.mark.asyncio
async def test_wechat_bind_success(seed_wx_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/wechat-bind", json={
            "openid": "test_openid_123",
            "username": "yeye_wx",
            "password": "123456",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "yeye_wx"
    assert data["user"]["role"] == "grandparent"


@pytest.mark.asyncio
async def test_wechat_bind_wrong_password(seed_wx_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/wechat-bind", json={
            "openid": "test_openid_456",
            "username": "yeye_wx",
            "password": "wrong_password",
        })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wechat_bind_then_verify_openid(seed_wx_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/wechat-bind", json={
            "openid": "test_openid_789",
            "username": "yeye_wx",
            "password": "123456",
        })
        assert resp.status_code == 200

    async with TestSession() as db:
        result = await db.execute(select(User).where(User.username == "yeye_wx"))
        user = result.scalar_one()
        assert user.wechat_openid == "test_openid_789"
