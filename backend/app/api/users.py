import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_admin, get_current_user
from ..db.database import get_db
from ..models import Borrow, Message, MessageRead, Review, User
from ..schemas.common import Page
from ..schemas.user import ProfileUpdate, RoleUpdate, StatusUpdate, UserOut

router = APIRouter(tags=["用户"])


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/users", response_model=Page[UserOut])
def list_users(
    keyword: str = "",
    role: str = "",
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(User.username.ilike(like), User.nickname.ilike(like), User.email.ilike(like))
        )
    if role:
        query = query.filter(User.role == role)
    total = query.count()
    items = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return Page(items=[UserOut.model_validate(u) for u in items], total=total, page=page, size=size)


@router.put("/users/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    user.role = data.role
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/status", response_model=UserOut)
def update_status(
    user_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")
    user.is_active = data.isActive
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    active_borrows = (
        db.query(Borrow)
        .filter(Borrow.user_id == user_id, Borrow.status != "returned")
        .count()
    )
    if active_borrows > 0:
        raise HTTPException(status_code=400, detail="该用户还有未归还的图书，无法删除")
    db.query(Review).filter(Review.user_id == user_id).delete()
    db.query(MessageRead).filter(MessageRead.user_id == user_id).delete()
    db.query(Message).filter(Message.target_user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"detail": "用户已删除"}


@router.put("/profile", response_model=UserOut)
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.nickname = data.nickname.strip()
    user.email = data.email.strip()
    user.phone = data.phone.strip()
    db.commit()
    db.refresh(user)
    return user


AVATAR_TYPES = {
    "image/webp": "webp",
    "image/png": "png",
    "image/jpeg": "jpg",
}


@router.post("/profile/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content_type = (file.content_type or "").lower()
    ext = AVATAR_TYPES.get(content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="头像仅支持 webp、png、jpeg 格式")
    content = await file.read()
    if len(content) > settings.MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="头像大小不能超过 100K")
    if not content:
        raise HTTPException(status_code=400, detail="头像文件为空")

    # 删除旧头像文件
    if user.avatar and user.avatar.startswith("/uploads/avatars/"):
        old = settings.UPLOAD_DIR / Path(user.avatar).relative_to("/uploads")
        old.unlink(missing_ok=True)

    filename = f"user_{user.id}_{int(time.time() * 1000)}.{ext}"
    (settings.AVATAR_DIR / filename).write_bytes(content)
    user.avatar = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(user)
    return user
