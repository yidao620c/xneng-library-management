from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.deps import get_current_admin
from ..db.database import get_db
from ..models import Book, Borrow, Message, Review, User

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    now = datetime.now()
    total_books = db.query(func.count(Book.id)).scalar() or 0
    total_copies = db.query(func.coalesce(func.sum(Book.total_copies), 0)).scalar() or 0
    available_copies = db.query(func.coalesce(func.sum(Book.available_copies), 0)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    borrowing = (
        db.query(func.count(Borrow.id)).filter(Borrow.status != "returned").scalar() or 0
    )
    overdue = (
        db.query(func.count(Borrow.id))
        .filter(Borrow.status != "returned", Borrow.due_date < now)
        .scalar()
        or 0
    )
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    return {
        "totalBooks": total_books,
        "totalCopies": total_copies,
        "availableCopies": available_copies,
        "totalUsers": total_users,
        "totalReviews": total_reviews,
        "borrowing": borrowing,
        "overdue": overdue,
        "totalMessages": total_messages,
    }


def _bucket_start(dt: datetime, granularity: str) -> datetime:
    if granularity == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if granularity == "week":
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return start - timedelta(days=start.weekday())
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _next_bucket(dt: datetime, granularity: str) -> datetime:
    if granularity == "day":
        return dt + timedelta(days=1)
    if granularity == "week":
        return dt + timedelta(weeks=1)
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1)
    return dt.replace(month=dt.month + 1)


@router.get("/borrow-trend")
def borrow_trend(
    granularity: str = "day",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if granularity not in ("day", "week", "month"):
        granularity = "day"
    span = {"day": 30, "week": 12, "month": 12}[granularity]

    now = datetime.now()
    if granularity == "day":
        first = (now - timedelta(days=span - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif granularity == "week":
        this_week = _bucket_start(now, "week")
        first = this_week - timedelta(weeks=span - 1)
    else:
        first = _bucket_start(now, "month")
        for _ in range(span - 1):
            first = _bucket_start(first - timedelta(days=1), "month")

    rows = db.query(Borrow.borrowed_at).filter(Borrow.borrowed_at >= first).all()
    counts: dict[datetime, int] = {}
    for (borrowed_at,) in rows:
        key = _bucket_start(borrowed_at, granularity)
        counts[key] = counts.get(key, 0) + 1

    items = []
    cursor = first
    while cursor <= _bucket_start(now, granularity):
        label = cursor.strftime("%Y-%m-%d")
        if granularity == "week":
            label = cursor.strftime("%Y年第%W周")
        elif granularity == "month":
            label = cursor.strftime("%Y-%m")
        items.append({"label": label, "count": counts.get(cursor, 0)})
        cursor = _next_bucket(cursor, granularity)
    return {"granularity": granularity, "span": span, "items": items}
