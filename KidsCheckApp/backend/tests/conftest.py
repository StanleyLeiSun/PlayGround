import asyncio
from datetime import date, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.models import (
    User, UserRole, Child, TaskTemplate, TaskType, TaskStatus,
    DailyTask, PointAccount, Reward, ConditionalTask, CheckInPhoto,
    ActionLog, RewardRedemption, RedemptionStatus,
)
from app.middleware.auth import create_token

TEST_DB_URL = "sqlite+aiosqlite:///./test_kidscheck.db"
engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def committed_db():
    """A DB session that commits on context exit, so data is visible to API calls."""
    async with TestSession() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture
async def seed_data():
    """Seed preset users, children, and point accounts."""
    async with TestSession() as db:
        users = {}
        for uname, role in [
            ("baba", UserRole.parent), ("mama", UserRole.parent),
            ("yeye", UserRole.grandparent), ("nainai", UserRole.grandparent),
            ("laoye", UserRole.grandparent), ("laolao", UserRole.grandparent),
        ]:
            u = User(username=uname, password_hash="123456", role=role)
            db.add(u)
            users[uname] = u

        luobo = Child(name="萝卜", nickname="萝卜", age=8)
        candou = Child(name="蚕豆", nickname="蚕豆", age=5)
        db.add(luobo)
        db.add(candou)
        await db.flush()

        pa1 = PointAccount(child_id=luobo.id, balance=0)
        pa2 = PointAccount(child_id=candou.id, balance=0)
        db.add(pa1)
        db.add(pa2)
        await db.commit()

        return {
            "users": users,
            "luobo": luobo,
            "candou": candou,
        }


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def parent_token(seed_data):
    parent = seed_data["users"]["baba"]
    return create_token(parent.id, parent.role.value)


@pytest_asyncio.fixture
async def grandparent_token(seed_data):
    gp = seed_data["users"]["yeye"]
    return create_token(gp.id, gp.role.value)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
