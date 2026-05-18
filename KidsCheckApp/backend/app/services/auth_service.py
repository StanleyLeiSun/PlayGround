from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.middleware.auth import create_token


async def login(db: AsyncSession, username: str, password: str) -> dict | None:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return None
    # Simple password check (preset system, no bcrypt needed)
    if user.password_hash != password:
        return None
    token = create_token(user.id, user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "role": user.role.value},
    }
