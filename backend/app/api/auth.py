from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_user
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ..db.database import get_db
from ..models import User
from ..schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut
from ..schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


def _token_payload(user: User) -> dict:
    return {
        "accessToken": create_access_token(user.id),
        "refreshToken": create_refresh_token(user.id),
        "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserOut.model_validate(user).model_dump(mode="json"),
    }


@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == data.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被注册")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname.strip() or data.username,
        email=data.email,
        phone=data.phone,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_payload(user)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    return _token_payload(user)


@router.post("/refresh", response_model=TokenOut)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    payload = decode_token(data.refreshToken, "refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="刷新凭证无效或已过期，请重新登录")
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="刷新凭证无效，请重新登录")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="账号不存在或已禁用")
    return _token_payload(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
