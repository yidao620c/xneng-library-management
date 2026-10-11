from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_admin, get_current_user
from ..db.database import get_db
from ..models import Book, Borrow, Message, User
from ..schemas.borrow import BorrowIn, BorrowOut
from ..schemas.common import Page

router = APIRouter(prefix="/borrows", tags=["借阅"])


def _is_overdue(b: Borrow) -> bool:
    return b.status != "returned" and b.due_date < datetime.now()


def _to_out(b: Borrow) -> BorrowOut:
    out = BorrowOut.model_validate(b)
    out.overdue = _is_overdue(b)
    return out


def _apply_filters(query, status: str):
    now = datetime.now()
    if status == "active":
        query = query.filter(Borrow.status != "returned")
    elif status == "borrowed":
        query = query.filter(Borrow.status == "borrowed")
    elif status == "returning":
        query = query.filter(Borrow.status == "returning")
    elif status == "returned":
        query = query.filter(Borrow.status == "returned")
    elif status == "overdue":
        query = query.filter(Borrow.status != "returned", Borrow.due_date < now)
    return query


@router.post("", response_model=BorrowOut)
def create_borrow(
    data: BorrowIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = db.get(Book, data.bookId)
    if book is None:
        raise HTTPException(status_code=404, detail="图书不存在")
    if book.available_copies <= 0:
        raise HTTPException(status_code=400, detail="该书已全部借出，暂时无法借阅")
    active_same = (
        db.query(Borrow)
        .filter(
            Borrow.user_id == user.id,
            Borrow.book_id == book.id,
            Borrow.status != "returned",
        )
        .count()
    )
    if active_same > 0:
        raise HTTPException(status_code=400, detail="您已借阅此书且尚未归还")
    active_count = (
        db.query(Borrow)
        .filter(Borrow.user_id == user.id, Borrow.status != "returned")
        .count()
    )
    limit = settings.MAX_ACTIVE_BORROWS.get(user.role, 5)
    if active_count >= limit:
        role_label = {"user": "普通用户", "vip": "VIP 用户", "admin": "管理员"}.get(user.role, user.role)
        raise HTTPException(
            status_code=400,
            detail=f"已达到 {role_label} 最大在借上限（{limit} 册），请先归还部分图书",
        )

    borrow = Borrow(
        user_id=user.id,
        book_id=book.id,
        status="borrowed",
        borrowed_at=datetime.now(),
        due_date=datetime.now() + timedelta(days=settings.LOAN_DAYS),
    )
    book.available_copies -= 1
    db.add(borrow)
    db.commit()
    db.refresh(borrow)
    return _to_out(borrow)


@router.get("/my", response_model=Page[BorrowOut])
def my_borrows(
    status: str = "",
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Borrow).filter(Borrow.user_id == user.id)
    query = _apply_filters(query, status)
    total = query.count()
    borrows = query.order_by(Borrow.borrowed_at.desc()).offset((page - 1) * size).limit(size).all()
    return Page(items=[_to_out(b) for b in borrows], total=total, page=page, size=size)


@router.get("/my/summary")
def my_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.now()
    base = db.query(Borrow).filter(Borrow.user_id == user.id)
    borrowing = base.filter(Borrow.status != "returned").count()
    overdue = base.filter(Borrow.status != "returned", Borrow.due_date < now).count()
    returned = base.filter(Borrow.status == "returned").count()
    return {"borrowing": borrowing, "overdue": overdue, "returned": returned}


@router.get("", response_model=Page[BorrowOut])
def list_borrows(
    status: str = "",
    keyword: str = "",
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(Borrow)
    query = _apply_filters(query, status)
    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.join(User, Borrow.user_id == User.id).join(Book, Borrow.book_id == Book.id)
        query = query.filter(
            or_(User.username.ilike(like), User.nickname.ilike(like), Book.title.ilike(like))
        )
    total = query.count()
    borrows = query.order_by(Borrow.borrowed_at.desc()).offset((page - 1) * size).limit(size).all()
    return Page(items=[_to_out(b) for b in borrows], total=total, page=page, size=size)


@router.post("/{borrow_id}/return", response_model=BorrowOut)
def request_return(
    borrow_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    borrow = db.get(Borrow, borrow_id)
    if borrow is None:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    if borrow.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="只能操作自己的借阅记录")
    if borrow.status != "borrowed":
        raise HTTPException(status_code=400, detail="该记录当前状态不支持申请归还")
    borrow.status = "returning"
    db.commit()
    db.refresh(borrow)
    return _to_out(borrow)


@router.post("/{borrow_id}/confirm-return", response_model=BorrowOut)
def confirm_return(
    borrow_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    borrow = db.get(Borrow, borrow_id)
    if borrow is None:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    if borrow.status == "returned":
        raise HTTPException(status_code=400, detail="该图书已归还")
    borrow.status = "returned"
    borrow.returned_at = datetime.now()
    book = db.get(Book, borrow.book_id)
    if book:
        book.available_copies = min(book.total_copies, book.available_copies + 1)
    db.commit()
    db.refresh(borrow)
    return _to_out(borrow)


@router.post("/{borrow_id}/remind", response_model=BorrowOut)
def remind_return(
    borrow_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    borrow = db.get(Borrow, borrow_id)
    if borrow is None:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    if borrow.status == "returned":
        raise HTTPException(status_code=400, detail="该图书已归还，无需催还")
    borrow.reminded_at = datetime.now()
    overdue_text = "已逾期" if _is_overdue(borrow) else f"应还日期为 {borrow.due_date:%Y-%m-%d}"
    message = Message(
        title="图书催还通知",
        content=f"管理员提醒：您借阅的《{borrow.book.title}》{overdue_text}，请尽快归还。",
        target_user_id=borrow.user_id,
        created_by=admin.id,
    )
    db.add(message)
    db.commit()
    db.refresh(borrow)
    return _to_out(borrow)
