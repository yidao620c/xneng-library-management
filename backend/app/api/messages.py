from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.deps import get_current_admin, get_current_user
from ..db.database import get_db
from ..models import Message, MessageRead, User
from ..schemas.common import Page
from ..schemas.message import MessageIn, MessageOut

router = APIRouter(prefix="/messages", tags=["消息"])


def _visible_query(db: Session, user_id: int):
    return db.query(Message).filter(
        or_(Message.target_user_id.is_(None), Message.target_user_id == user_id)
    )


@router.get("", response_model=Page[MessageOut])
def list_messages(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = _visible_query(db, user.id)
    total = query.count()
    messages = (
        query.order_by(Message.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    read_ids = {
        r.message_id
        for r in db.query(MessageRead).filter(MessageRead.user_id == user.id).all()
    }
    items = []
    for m in messages:
        out = MessageOut.model_validate(m)
        out.isRead = m.id in read_ids
        items.append(out)
    return Page(items=items, total=total, page=page, size=size)


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total = _visible_query(db, user.id).count()
    read = (
        db.query(MessageRead)
        .filter(
            MessageRead.user_id == user.id,
            MessageRead.message_id.in_(
                db.query(Message.id).filter(
                    or_(Message.target_user_id.is_(None), Message.target_user_id == user.id)
                )
            ),
        )
        .count()
    )
    return {"unreadCount": max(0, total - read)}


@router.post("/{message_id}/read")
def mark_read(
    message_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    message = db.get(Message, message_id)
    if message is None or (message.target_user_id not in (None, user.id)):
        raise HTTPException(status_code=404, detail="消息不存在")
    exists = (
        db.query(MessageRead)
        .filter(MessageRead.message_id == message_id, MessageRead.user_id == user.id)
        .first()
    )
    if exists is None:
        db.add(MessageRead(message_id=message_id, user_id=user.id, read_at=datetime.now()))
        db.commit()
    return {"detail": "已标记为已读"}


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    read_ids = {
        r.message_id for r in db.query(MessageRead).filter(MessageRead.user_id == user.id).all()
    }
    messages = _visible_query(db, user.id).all()
    for m in messages:
        if m.id not in read_ids:
            db.add(MessageRead(message_id=m.id, user_id=user.id, read_at=datetime.now()))
    db.commit()
    return {"detail": "全部消息已读"}


@router.get("/admin/list", response_model=Page[MessageOut])
def admin_list_messages(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(Message)
    total = query.count()
    messages = (
        query.order_by(Message.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    user_map = {u.id: u.username for u in db.query(User.id, User.username).all()}
    items = []
    for m in messages:
        out = MessageOut.model_validate(m)
        out.targetUsername = (
            "全体用户" if m.target_user_id is None else user_map.get(m.target_user_id, "未知用户")
        )
        items.append(out)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=MessageOut)
def create_message(
    data: MessageIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    if data.targetUserId and db.get(User, data.targetUserId) is None:
        raise HTTPException(status_code=400, detail="目标用户不存在")
    message = Message(
        title=data.title.strip(),
        content=data.content.strip(),
        target_user_id=data.targetUserId,
        created_by=admin.id,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    out = MessageOut.model_validate(message)
    out.isRead = False
    return out


@router.delete("/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    db.query(MessageRead).filter(MessageRead.message_id == message_id).delete()
    db.delete(message)
    db.commit()
    return {"detail": "消息已删除"}
