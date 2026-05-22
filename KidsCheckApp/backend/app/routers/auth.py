from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.schemas import LoginRequest, TokenResponse, UserResponse, WechatLoginRequest, WechatBindRequest
from app.services import auth_service
from app.services.action_log_service import log_action
from app.middleware.auth import get_current_user
from app.models.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.login(db, req.username, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    await log_action(db, result["user"]["id"], "login")
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse(id=user.id, username=user.username, role=user.role.value)


@router.post("/wechat-login")
async def wechat_login(req: WechatLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.wechat_login(db, req.code)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/wechat-bind")
async def wechat_bind(req: WechatBindRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.wechat_bind(db, req.openid, req.username, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    await log_action(db, result["user"]["id"], "wechat_bind")
    return result
