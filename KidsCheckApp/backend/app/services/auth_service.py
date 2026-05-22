import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.middleware.auth import create_token
from app.config import WX_APP_ID, WX_APP_SECRET


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


async def wechat_login(db: AsyncSession, code: str) -> dict:
    """Exchange wx code for openid, then check if user is bound."""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WX_APP_ID,
        "secret": WX_APP_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
    data = resp.json()
    openid = data.get("openid")
    if not openid:
        return {"error": data.get("errmsg", "WeChat login failed")}

    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalar_one_or_none()
    if user:
        token = create_token(user.id, user.role.value)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "role": user.role.value},
        }
    return {"need_binding": True, "openid": openid}


async def wechat_bind(db: AsyncSession, openid: str, username: str, password: str) -> dict | None:
    """Bind wechat openid to existing account after verifying credentials."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or user.password_hash != password:
        return None
    user.wechat_openid = openid
    await db.flush()
    token = create_token(user.id, user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "role": user.role.value},
    }
