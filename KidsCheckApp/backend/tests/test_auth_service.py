"""Tests for auth_service functions."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import auth_service


@pytest.mark.asyncio
async def test_login_success(db: AsyncSession, seed_data):
    """Test successful login."""
    result = await auth_service.login(db, "baba", "123456")
    assert result is not None
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    assert result["user"]["username"] == "baba"
    assert result["user"]["role"] == "parent"


@pytest.mark.asyncio
async def test_login_wrong_password(db: AsyncSession, seed_data):
    """Test login with wrong password."""
    result = await auth_service.login(db, "baba", "wrong")
    assert result is None


@pytest.mark.asyncio
async def test_login_nonexistent_user(db: AsyncSession, seed_data):
    """Test login with non-existent user."""
    result = await auth_service.login(db, "nonexistent", "123456")
    assert result is None


@pytest.mark.asyncio
async def test_login_grandparent(db: AsyncSession, seed_data):
    """Test grandparent login."""
    result = await auth_service.login(db, "yeye", "123456")
    assert result is not None
    assert result["user"]["role"] == "grandparent"
