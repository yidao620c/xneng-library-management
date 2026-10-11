import time
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_admin
from ..db.database import get_db
from ..models import Book, Borrow, Category, Review, User
from ..schemas.book import BookIn, BookOut, BookUpdate, CoverOut
from ..schemas.common import Page

router = APIRouter(prefix="/books", tags=["图书"])


def _rating_map(db: Session, book_ids: list[int]) -> dict[int, tuple[float, int]]:
    if not book_ids:
        return {}
    rows = (
        db.query(Review.book_id, func.avg(Review.rating), func.count(Review.id))
        .filter(Review.book_id.in_(book_ids))
        .group_by(Review.book_id)
        .all()
    )
    return {bid: (round(float(avg) or 0.0, 1), int(cnt)) for bid, avg, cnt in rows}


def _to_out(db: Session, book: Book, ratings: dict[int, tuple[float, int]] | None = None) -> BookOut:
    if ratings is None:
        ratings = _rating_map(db, [book.id])
    avg, count = ratings.get(book.id, (0.0, 0))
    return BookOut(
        id=book.id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        publisher=book.publisher,
        description=book.description,
        categoryId=book.category_id,
        categoryName=book.category.name if book.category else None,
        cover=book.cover,
        tags=[t.strip() for t in book.tags.split(",") if t.strip()],
        totalCopies=book.total_copies,
        availableCopies=book.available_copies,
        ratingAvg=avg,
        ratingCount=count,
        createdAt=book.created_at,
    )


@router.get("", response_model=Page[BookOut])
def list_books(
    keyword: str = "",
    categoryId: int | None = None,
    status: str = "",
    tag: str = "",
    page: int = 1,
    size: int = 12,
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.filter(
            or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like))
        )
    if categoryId:
        query = query.filter(Book.category_id == categoryId)
    if status == "available":
        query = query.filter(Book.available_copies > 0)
    elif status == "unavailable":
        query = query.filter(Book.available_copies == 0)
    if tag:
        query = query.filter(Book.tags.ilike(f"%{tag.strip()}%"))
    total = query.count()
    books = (
        query.order_by(Book.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    ratings = _rating_map(db, [b.id for b in books])
    items = [_to_out(db, b, ratings) for b in books]
    return Page(items=items, total=total, page=page, size=size)


@router.get("/tags", response_model=list[str])
def list_tags(db: Session = Depends(get_db)):
    rows = db.query(Book.tags).filter(Book.tags != "").all()
    tags: list[str] = []
    seen: set[str] = set()
    for (raw,) in rows:
        for t in raw.split(","):
            t = t.strip()
            if t and t not in seen:
                seen.add(t)
                tags.append(t)
    return tags


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="图书不存在")
    return _to_out(db, book)


@router.post("", response_model=BookOut)
def create_book(
    data: BookIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if data.availableCopies > data.totalCopies:
        raise HTTPException(status_code=400, detail="在馆数量不能超过馆藏总量")
    if db.query(Book).filter(Book.isbn == data.isbn.strip()).first():
        raise HTTPException(status_code=400, detail="ISBN 已存在")
    if data.categoryId and db.get(Category, data.categoryId) is None:
        raise HTTPException(status_code=400, detail="分类不存在")
    book = Book(
        title=data.title.strip(),
        author=data.author.strip(),
        isbn=data.isbn.strip(),
        publisher=data.publisher.strip(),
        description=data.description.strip(),
        category_id=data.categoryId,
        tags=data.tags.strip(),
        total_copies=data.totalCopies,
        available_copies=data.availableCopies,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return _to_out(db, book)


@router.put("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="图书不存在")
    if data.availableCopies > data.totalCopies:
        raise HTTPException(status_code=400, detail="在馆数量不能超过馆藏总量")
    dup = db.query(Book).filter(Book.isbn == data.isbn.strip(), Book.id != book_id).first()
    if dup:
        raise HTTPException(status_code=400, detail="ISBN 已存在")
    if data.categoryId and db.get(Category, data.categoryId) is None:
        raise HTTPException(status_code=400, detail="分类不存在")

    # 外借中的册数不能被收回：在馆数下限 = 总量 - 未归还数
    active = (
        db.query(func.count(Borrow.id))
        .filter(Borrow.book_id == book_id, Borrow.status != "returned")
        .scalar() or 0
    )
    min_available = max(0, data.totalCopies - active)
    if data.availableCopies < min_available:
        raise HTTPException(
            status_code=400,
            detail=f"该书有 {active} 册未归还，在馆数量不能低于 {min_available}",
        )

    book.title = data.title.strip()
    book.author = data.author.strip()
    book.isbn = data.isbn.strip()
    book.publisher = data.publisher.strip()
    book.description = data.description.strip()
    book.category_id = data.categoryId
    book.tags = data.tags.strip()
    book.total_copies = data.totalCopies
    book.available_copies = data.availableCopies
    db.commit()
    db.refresh(book)
    return _to_out(db, book)


@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="图书不存在")
    active = (
        db.query(Borrow).filter(Borrow.book_id == book_id, Borrow.status != "returned").count()
    )
    if active > 0:
        raise HTTPException(status_code=400, detail=f"该书有 {active} 条未归还记录，无法删除")
    if book.cover and book.cover.startswith("/uploads/covers/"):
        old = settings.UPLOAD_DIR / Path(book.cover).relative_to("/uploads")
        old.unlink(missing_ok=True)
    db.query(Review).filter(Review.book_id == book_id).delete()
    db.delete(book)
    db.commit()
    return {"detail": "图书已删除"}


COVER_TYPES = {
    "image/webp": "webp",
    "image/png": "png",
    "image/jpeg": "jpg",
}


@router.post("/{book_id}/cover", response_model=CoverOut)
async def upload_cover(
    book_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="图书不存在")
    content_type = (file.content_type or "").lower()
    ext = COVER_TYPES.get(content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="封面仅支持 webp、png、jpeg 格式")
    content = await file.read()
    if len(content) > settings.MAX_COVER_SIZE:
        raise HTTPException(status_code=400, detail="封面大小不能超过 2M")
    if not content:
        raise HTTPException(status_code=400, detail="封面文件为空")

    if book.cover and book.cover.startswith("/uploads/covers/"):
        old = settings.UPLOAD_DIR / Path(book.cover).relative_to("/uploads")
        old.unlink(missing_ok=True)

    filename = f"book_{book.id}_{int(time.time() * 1000)}.{ext}"
    (settings.COVER_DIR / filename).write_bytes(content)
    book.cover = f"/uploads/covers/{filename}"
    db.commit()
    return CoverOut(cover=book.cover)
